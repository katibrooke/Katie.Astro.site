import streamlit as st
import swisseph as swe
from datetime import datetime
import pytz
import re
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from PIL import Image, ImageDraw, ImageFont
import io

# Настройка дизайна
st.markdown("""
    <style>
    .stApp { background-color: #fde2e4; }
    h1, h3 { color: #737b69; text-align: center; font-family: 'Arial'; }
    .stButton>button { 
        background-color: #a6817b; color: white; 
        border-radius: 20px; width: 100%; border: none; height: 3.5em; font-weight: bold;
    }
    .result-card {
        background-color: #ffffff; padding: 15px;
        border-radius: 12px; border-left: 5px solid #9ba192;
        margin-bottom: 10px; color: #4a4a4a;
    }
    .asc-card {
        background-color: #f0f2ed; padding: 15px;
        border-radius: 12px; border: 2px solid #737b69;
        margin-bottom: 20px; color: #737b69; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

def create_image(data_list, asc_info):
    # Создаем холст (вертикальный для сторис)
    img = Image.new('RGB', (600, 900), color='#fde2e4')
    d = ImageDraw.Draw(img)
    
    # Заголовок
    d.text((300, 50), "Звездный калькулятор", fill="#737b69", anchor="mm")
    d.text((300, 100), asc_info, fill="#a6817b", anchor="mm")
    
    # Рисуем планеты
    y_pos = 180
    for item in data_list:
        # Фон карточки
        d.rectangle([50, y_pos, 550, y_pos + 60], fill="white", outline="#9ba192")
        d.text((70, y_pos + 20), item, fill="#4a4a4a")
        y_pos += 80
        
    d.text((300, 850), "Создано в @katy.astro.kids", fill="#737b69", anchor="mm")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

st.title("✨ Звёздный калькулятор ✨")

col1, col2 = st.columns(2)
with col1:
    d = st.date_input("Дата рождения", format="DD/MM/YYYY", min_value=datetime(1900, 1, 1))
    t_input = st.text_input("Время (например: 22:22)", value="22:22")
with col2:
    city_input = st.text_input("Город на английском (например: Tel Aviv)", value="Tel Aviv")

if st.button("Рассчитать карту"):
    clean_time = re.sub(r'[^0-9:]', '', t_input).strip()[:5]
    
    try:
        with st.spinner('Считываю энергию планет...'):
            geolocator = Nominatim(user_agent="katy_astro_v4")
            location = geolocator.geocode(city_input, timeout=15)
            
            if location:
                tf = TimezoneFinder()
                tz_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
                timezone = pytz.timezone(tz_name)
                local_dt = timezone.localize(datetime(d.year, d.month, d.day, int(clean_time[:2]), int(clean_time[3:])))
                utc_dt = local_dt.astimezone(pytz.utc)
                
                jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60)
                cusps, ascmc = swe.houses(jd, location.latitude, location.longitude, b'P')
                zodiac = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

                # Асцендент
                asc_txt = f"Асцендент: {int(ascmc[0]%30)}° {zodiac[int(ascmc[0]/30)]}"
                st.markdown(f'<div class="asc-card">🌟 <b>{asc_txt}</b></div>', unsafe_allow_html=True)

                results_for_img = []
                planets = {"Солнце": 0, "Луна": 1, "Меркурий": 2, "Венера": 3, "Марс": 4, "Юпитер": 5, "Сатурн": 6}
                
                for name, p_id in planets.items():
                    lon = swe.calc_ut(jd, p_id)[0][0]
                    p_house = 1 # Упрощенный поиск дома для примера
                    for i in range(1, 13):
                        c1, c2 = cusps[i], cusps[i+1] if i < 12 else cusps[1]
                        if (c1 < c2 and c1 <= lon < c2) or (c1 > c2 and (lon >= c1 or lon < c2)):
                            p_house = i; break
                    
                    line = f"{name}: {int(lon%30)}° {zodiac[int(lon/30)]} в {p_house} доме"
                    results_for_img.append(line)
                    st.markdown(f'<div class="result-card"><b>{name}</b></div>', unsafe_allow_html=True)

                # КНОПКА СКАЧИВАНИЯ
                img_data = create_image(results_for_img, asc_txt)
                st.download_button(
                    label="📸 Сохранить результат в галерею",
                    data=img_data,
                    file_name=f"astro_map_{d}.png",
                    mime="image/png"
                )
    except Exception as e:
        st.error("Проверьте данные.")
