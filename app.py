import streamlit as st
import swisseph as swe
from datetime import datetime
import pytz
import re
from timezonefinder import TimezoneFinder
from PIL import Image, ImageDraw, ImageFont
import io
import geonamescache
import pycountry

# --- СТИЛИЗАЦИЯ ---
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
        border-radius: 12px; border: 3px solid #737b69;
        margin-bottom: 20px; color: #737b69; text-align: center; font-weight: bold;
    }
    label { color: #737b69 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- БАЗА ГОРОДОВ И СТРАН ---
gc = geonamescache.GeonamesCache()
countries = sorted([c.name for c in pycountry.countries])

def find_city_pro(city_name, country_name):
    try:
        country_code = pycountry.countries.get(name=country_name).alpha_2
        cities = gc.get_cities()
        found = []
        for c_id in cities:
            c = cities[c_id]
            if c['name'].lower() == city_name.lower() and c['countrycode'] == country_code:
                found.append(c)
        return found[0] if found else None
    except:
        return None

# --- РИСОВАНИЕ КАРТИНКИ ---
def create_final_img(name, date_str, time_str, asc_info, data_list):
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

    draw.text((W/2, 60), name, fill="#737b69", font=f_title, anchor="mm")
    draw.text((W/2, 115), f"{date_str} {time_str}", fill="#a6817b", font=f_title, anchor="mm")
    draw.text((W/2, 175), "Расчет положения планет в натальной карте", fill="#737b69", font=f_sub, anchor="mm")
    draw.rectangle([50, 240, W-50, 320], fill="#f0f2ed", outline="#737b69", width=4)
    draw.text((W/2, 280), asc_info, fill="#737b69", font=f_asc, anchor="mm")

    y = 360
    for i, item in enumerate(data_list):
        color = "#9ba192" if i < 7 else "#a6817b"
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
user_name = st.text_input("Имя ребенка", value="Мишель")

col1, col2 = st.columns(2)
with col1:
    country_in = st.selectbox("Страна", countries, index=countries.index("Israel") if "Israel" in countries else 0)
    city_in = st.text_input("Город на английском", value="Tel Aviv")
with col2:
    d = st.date_input("Дата рождения", format="DD/MM/YYYY")
    t_in = st.text_input("Время рождения (ЧЧ:ММ)", value="12:00")

if st.button("Рассчитать и сохранить"):
    # Гибкая очистка времени
    t_nums = re.findall(r'\d+', t_in)
    if len(t_nums) >= 2:
        h, m = int(t_nums[0]), int(t_nums[1])
        t_clean = f"{h:02d}:{m:02d}"
    else:
        st.error("Пожалуйста, введите время цифрами (например, 12:30)")
        st.stop()

    try:
        with st.spinner('Сверяюсь со звездами...'):
            city = find_city_pro(city_in, country_in)
            if not city:
                st.error(f"Город '{city_in}' не найден в стране {country_in}. Проверьте английское написание.")
            else:
                tf = TimezoneFinder()
                tz = pytz.timezone(tf.timezone_at(lng=city['longitude'], lat=city['latitude']))
                dt_local = tz.localize(datetime(d.year, d.month, d.day, h, m))
                dt_utc = dt_local.astimezone(pytz.utc)
                
                jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour + dt_utc.minute/60)
                cusps, ascmc = swe.houses(jd, city['latitude'], city['longitude'], b'P')
                zod = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

                def find_h(lon, c):
                    for i in range(1, 12):
                        if (c[i] < c[i+1] and c[i] <= lon < c[i+1]) or (c[i] > c[i+1] and (lon >= c[i] or lon < c[i+1])): return i
                    return 12

                asc_txt = f"Асцендент: {int(ascmc[0]%30)}° {zod[int(ascmc[0]/30)]}"
                st.markdown(f'<div class="asc-card">🌟 {asc_txt}</div>', unsafe_allow_html=True)

                res_list = []
                planets = {"Солнце": 0, "Луна": 1, "Меркурий": 2, "Венера": 3, "Марс": 4, "Юпитер": 5, "Сатурн": 6}
                
                for name, pid in planets.items():
                    lon = swe.calc_ut(jd, pid)[0][0]
                    h_num = find_h(lon, cusps)
                    line = f"{name}: {int(lon%30)}° {zod[int(lon/30)]} в {h_num} доме"
                    res_list.append(line)
                    st.markdown(f'<div class="result-card"><b>{line}</b></div>', unsafe_allow_html=True)

                rahu = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
                rh = find_h(rahu, cusps)
                res_list.append(f"Сев. Узел (Раху): {int(rahu%30)}° {zod[int(rahu/30)]} в {rh} доме")
                ketu = (rahu + 180) % 360
                kh = (rh + 6) % 12 or 12
                res_list.append(f"Южн. Узел (Кету): {int(ketu%30)}° {zod[int(ketu/30)]} в {kh} доме")
                
                for item in res_list[7:]:
                    st.markdown(f'<div class="result-card" style="border-left-color: #a6817b;"><b>{item}</b></div>', unsafe_allow_html=True)

                img = create_final_img(user_name, d.strftime("%d.%m.%Y"), t_clean, asc_txt, res_list)
                st.download_button("📸 Сохранить карту в галерею", img, f"{user_name}_astro.png", "image/png")
    except Exception as e:
        st.error(f"Произошла ошибка при расчете. Попробуйте еще раз.")
