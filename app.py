import streamlit as st
import swisseph as swe
from datetime import datetime
import pytz
import re
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from PIL import Image, ImageDraw, ImageFont
import io

# --- УСКОРЕННЫЙ ПОИСК ГОРОДА ---
@st.cache_data(ttl=86400) # Кэш на сутки
def get_location_pro(city, country):
    try:
        # Уникальный агент для стабильной работы
        geolocator = Nominatim(user_agent="katy_astro_unique_search_v2")
        query = f"{city}, {country}"
        return geolocator.geocode(query, timeout=30)
    except:
        return None

@st.cache_data(ttl=86400)
def get_tz_pro(lat, lon):
    tf = TimezoneFinder()
    return tf.timezone_at(lng=lon, lat=lat)

# --- ДИЗАЙН ---
st.markdown("""
    <style>
    .stApp { background-color: #fde2e4; }
    h1, h3 { color: #737b69; text-align: center; font-family: 'Arial', sans-serif; }
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
        border-radius: 12px; border: 3px solid #737b69;
        margin-bottom: 20px; color: #737b69; text-align: center; font-weight: bold;
    }
    label { color: #737b69 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- КАРТИНКА ---
def create_map_image(name, date_str, asc_info, planets_data, nodes_data):
    W, H = 750, 1150
    img = Image.new('RGB', (W, H), color='#fde2e4')
    draw = ImageDraw.Draw(img)
    try:
        f_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
        f_sub = ImageFont.truetype("DejaVuSans.ttf", 26)
        f_text = ImageFont.truetype("DejaVuSans.ttf", 28)
        f_asc = ImageFont.truetype("DejaVuSans-Bold.ttf", 32)
    except:
        f_title = f_sub = f_text = f_asc = ImageFont.load_default()

    draw.text((W/2, 70), name, fill="#737b69", font=f_title, anchor="mm")
    draw.text((W/2, 130), date_str, fill="#a6817b", font=f_title, anchor="mm")
    draw.text((W/2, 190), "Расчет положения планет в натальной карте", fill="#737b69", font=f_sub, anchor="mm")
    draw.rectangle([50, 250, W-50, 330], fill="#f0f2ed", outline="#737b69", width=4)
    draw.text((W/2, 290), asc_info, fill="#737b69", font=f_asc, anchor="mm")
    y = 370
    for i, item in enumerate(planets_data + nodes_data):
        color = "#9ba192" if i < len(planets_data) else "#a6817b"
        draw.rectangle([50, y, W-50, y+65], fill="white")
        draw.rectangle([50, y, 65, y+65], fill=color)
        draw.text((80, y+18), item, fill="#4a4a4a", font=f_text)
        y += 80
    draw.text((W/2, H-50), "Создано в @katy.astro.kids", fill="#737b69", font=f_sub, anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- САЙТ ---
st.title("✨ Звёздный калькулятор ✨")
name_val = st.text_input("Имя ребенка", value="Мишель")

col1, col2 = st.columns(2)
with col1:
    country_in = st.selectbox("Страна (на английском)", 
                             ["Israel", "Russia", "USA", "Germany", "France", "Ukraine", "Kazakhstan", "Other"])
    if country_in == "Other":
        country_in = st.text_input("Введите название страны на английском")
    
    city_in = st.text_input("Город на английском (например: Kazan)", value="Tel Aviv")

with col2:
    d = st.date_input("Дата рождения", format="DD/MM/YYYY", min_value=datetime(1900, 1, 1))
    t_in = st.text_input("Время (ЧЧ:ММ)", value="12:00")

if st.button("Рассчитать карту"):
    t_clean = re.sub(r'[^0-9:]', '', t_in).strip()[:5]
    try:
        with st.spinner('Связываюсь со звездами...'):
            loc = get_location_pro(city_in, country_in)
            if loc:
                tz_name = get_tz_pro(loc.latitude, loc.longitude)
                timezone = pytz.timezone(tz_name)
                
                # Математика
                time_parts = t_clean.split(':')
                dt = timezone.localize(datetime(d.year, d.month, d.day, int(time_parts[0]), int(time_parts[1])))
                utc_dt = dt.astimezone(pytz.utc)
                jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60)
                cusps, ascmc = swe.houses(jd, loc.latitude, loc.longitude, b'P')
                zod = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
                
                def get_h(lon, c):
                    for i in range(1, 12):
                        if c[i] < c[i+1]:
                            if c[i] <= lon < c[i+1]: return i
                        else:
                            if lon >= c[i] or lon < c[i+1]: return i
                    return 12

                asc_t = f"Асцендент: {int(ascmc[0]%30)}° {zod[int(ascmc[0]/30)]}"
                st.markdown(f'<div class="asc-card">🌟 {asc_t}</div>', unsafe_allow_html=True)

                p_res, n_res = [], []
                for n, id in {"Солнце": 0, "Луна": 1, "Меркурий": 2, "Венера": 3, "Марс": 4, "Юпитер": 5, "Сатурн": 6}.items():
                    lon = swe.calc_ut(jd, id)[0][0]
                    h = get_h(lon, cusps)
                    line = f"{n}: {int(lon%30)}° {zod[int(lon/30)]} в {h} доме"
                    p_res.append(line)
                    st.markdown(f'<div class="result-card"><b>{line}</b></div>', unsafe_allow_html=True)

                rahu = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
                rh = get_h(rahu, cusps)
                n_res.append(f"Сев. Узел (Раху): {int(rahu%30)}° {zod[int(rahu/30)]} в {rh} доме")
                ketu = (rahu + 180) % 360
                kh = (rh + 6) % 12 or 12
                n_res.append(f"Южн. Узел (Кету): {int(ketu%30)}° {zod[int(ketu/30)]} в {kh} доме")
                
                for item in n_res:
                    st.markdown(f'<div class="result-card" style="border-left-color: #a6817b;"><b>{item}</b></div>', unsafe_allow_html=True)

                img = create_map_image(name_val, d.strftime("%d.%m.%Y"), asc_t, p_res, n_res)
                st.download_button("📸 Сохранить карту в галерею", img, f"{name_val}_astro.png", "image/png")
            else:
                st.error(f"Город '{city_in}' в стране '{country_in}' не найден. Попробуйте уточнить страну.")
    except Exception as e:
        st.error("Техническая ошибка. Пожалуйста, проверьте формат времени.")
