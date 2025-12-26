import streamlit as st
import swisseph as swe
from datetime import datetime
import pytz
import re
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from PIL import Image, ImageDraw, ImageFont
import io
import time

# --- НАСТРОЙКА ПОИСКА (БЕЗ РУЧНЫХ КООРДИНАТ) ---
@st.cache_data(ttl=86400)
def get_location_smart(query):
    # Используем уникальный агент, чтобы сервер нас не блокировал
    geolocator = Nominatim(user_agent="katy_astro_pro_v7")
    try:
        # Первая попытка
        loc = geolocator.geocode(query, timeout=15)
        if loc: return loc
        # Если не нашел, пробуем только первое слово (на случай если ввели лишнее)
        loc = geolocator.geocode(query.split(',')[0], timeout=15)
        return loc
    except:
        return None

# --- ОФОРМЛЕНИЕ ---
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

# --- ГЕНЕРАЦИЯ КАРТИНКИ (ШИРИНА 750) ---
def create_final_img(name, date_str, asc_info, planets_data, nodes_data):
    W, H = 750, 1150
    img = Image.new('RGB', (W, H), color='#fde2e4')
    draw = ImageDraw.Draw(img)
    try:
        f_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
        f_sub = ImageFont.truetype("DejaVuSans.ttf", 28)
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
    full_list = planets_data + nodes_data
    for i, item in enumerate(full_list):
        bar = "#9ba192" if i < len(planets_data) else "#a6817b"
        draw.rectangle([50, y, W-50, y+65], fill="white")
        draw.rectangle([50, y, 65, y+65], fill=bar)
        draw.text((80, y+18), item, fill="#4a4a4a", font=f_text)
        y += 80
    
    draw.text((W/2, H-50), "Создано в @katy.astro.kids", fill="#737b69", font=f_sub, anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- ИНТЕРФЕЙС ---
st.title("✨ Звёздный калькулятор ✨")
child_name = st.text_input("Имя", value="Мишель")

col1, col2 = st.columns(2)
with col1:
    # ОДНО ПОЛЕ ДЛЯ ВСЕГО
    place_in = st.text_input("Город и страна (English)", value="Kazan, Russia")
with col2:
    d = st.date_input("Дата рождения", format="DD/MM/YYYY", min_value=datetime(1900, 1, 1))
    t_in = st.text_input("Время (ЧЧ:ММ)", value="22:22")

if st.button("Рассчитать карту"):
    t_clean = re.sub(r'[^0-9:]', '', t_in).strip()[:5]
    try:
        with st.spinner('Считываю энергию звезд...'):
            loc = get_location_smart(place_in)
            if loc:
                tf = TimezoneFinder()
                tz = pytz.timezone(tf.timezone_at(lng=loc.longitude, lat=loc.latitude))
                dt = tz.localize(datetime(d.year, d.month, d.day, int(t_clean[:2]), int(t_clean[3:])))
                jd = swe.julday(dt.astimezone(pytz.utc).year, dt.astimezone(pytz.utc).month, dt.astimezone(pytz.utc).day, dt.astimezone(pytz.utc).hour + dt.astimezone(pytz.utc).minute/60)
                
                cusps, ascmc = swe.houses(jd, loc.latitude, loc.longitude, b'P')
                zod = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
                
                def get_h(lon, c):
                    for i in range(1, 12):
                        if (c[i] < c[i+1] and c[i] <= lon < c[i+1]) or (c[i] > c[i+1] and (lon >= c[i] or lon < c[i+1])): return i
                    return 12

                asc_txt = f"Асцендент: {int(ascmc[0]%30)}° {zod[int(ascmc[0]/30)]}"
                st.markdown(f'<div class="asc-card">🌟 {asc_txt}</div>', unsafe_allow_html=True)

                p_list, n_list = [], []
                # Планеты
                for n, id in {"Солнце": 0, "Луна": 1, "Меркурий": 2, "Венера": 3, "Марс": 4, "Юпитер": 5, "Сатурн": 6}.items():
                    lon = swe.calc_ut(jd, id)[0][0]
                    h = get_h(lon, cusps)
                    p_list.append(f"{n}: {int(lon%30)}° {zod[int(lon/30)]} в {h} доме")
                    st.markdown(f'<div class="result-card"><b>{p_list[-1]}</b></div>', unsafe_allow_html=True)

                # Узлы
                rahu = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
                rh = get_h(rahu, cusps)
                n_list.append(f"Сев. Узел (Раху): {int(rahu%30)}° {zod[int(rahu/30)]} в {rh} доме")
                ketu = (rahu + 180) % 360
                kh = (rh + 6) % 12 or 12
                n_list.append(f"Южн. Узел (Кету): {int(ketu%30)}° {zod[int(ketu/30)]} в {kh} доме")
                
                for item in n_list:
                    st.markdown(f'<div class="result-card" style="border-left-color: #a6817b;"><b>{item}</b></div>', unsafe_allow_html=True)

                img_bin = create_final_img(child_name, d.strftime("%d.%m.%Y"), asc_txt, p_list, n_list)
                st.download_button("📸 Скачать карту в галерею", img_bin, f"{child_name}_astro.png", "image/png")
            else:
                st.error("Город не найден. Попробуйте написать 'Kazan, Russia' или 'Ashdod, Israel'.")
    except Exception as e:
        st.error("Техническая ошибка. Проверьте формат времени (ЧЧ:ММ).")
