import streamlit as st
import swisseph as swe
from datetime import datetime
import pytz
import re
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from PIL import Image, ImageDraw, ImageFont
import io
import pycountry

# --- 1. ПОЛНЫЙ СПИСОК СТРАН МИРА ---
all_countries = sorted([country.name for country in pycountry.countries])

# --- ДИЗАЙН ---
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

# --- ФУНКЦИЯ РИСОВАНИЯ КАРТИНКИ ---
def create_final_img(name, date_str, time_str, asc_info, data_list):
    W, H = 750, 1150
    img = Image.new('RGB', (W, H), color='#fde2e4')
    draw = ImageDraw.Draw(img)
    try:
        f_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
        f_text = ImageFont.truetype("DejaVuSans.ttf", 28)
    except:
        f_title = f_text = ImageFont.load_default()

    draw.text((W/2, 60), name, fill="#737b69", font=f_title, anchor="mm")
    draw.text((W/2, 115), f"{date_str} {time_str}", fill="#a6817b", font=f_title, anchor="mm")
    draw.text((W/2, 175), "Расчет положения планет", fill="#737b69", font=f_text, anchor="mm")
    draw.rectangle([50, 240, W-50, 320], fill="#f0f2ed", outline="#737b69", width=4)
    draw.text((W/2, 280), asc_info, fill="#737b69", font=f_title, anchor="mm")
    y = 360
    for i, item in enumerate(data_list):
        color = "#9ba192" if i < 7 else "#a6817b"
        draw.rectangle([50, y, W-50, y+65], fill="white")
        draw.rectangle([50, y, 65, y+65], fill=color)
        draw.text((80, y+18), item, fill="#4a4a4a", font=f_text)
        y += 80
    draw.text((W/2, H-50), "Создано в @katy.astro.kids", fill="#737b69", font=f_text, anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- ИНТЕРФЕЙС САЙТА ---
st.title("✨ Звёздный калькулятор ✨")
user_name = st.text_input("Имя", value="Мишель")

col1, col2 = st.columns(2)
with col1:
    # ТЕПЕРЬ ТУТ ВСЕ СТРАНЫ МИРА
    country = st.selectbox("1. Выберите страну", all_countries, index=all_countries.index("Moldova") if "Moldova" in all_countries else 0)
    city_query = st.text_input("2. Введите город (на английском)", value="Chisinau")
with col2:
    d = st.date_input("Дата рождения", value=datetime(2011, 9, 26), min_value=datetime(1900,1,1))
    t_in = st.text_input("Время (ЧЧ:ММ)", value="22:22")

# --- ЛОГИКА ПОИСКА ГОРОДА ---
if "found_locs" not in st.session_state:
    st.session_state.found_locs = None

if st.button("🔍 Найти город в этой стране"):
    with st.spinner('Ищу город в международной базе...'):
        geolocator = Nominatim(user_agent="katy_astro_global_v1")
        try:
            # Ищем город строго внутри выбранной страны
            locs = geolocator.geocode(f"{city_query}, {country}", exactly_one=False, limit=5, timeout=15)
            if locs:
                st.session_state.found_locs = {loc.address: loc for loc in locs}
            else:
                st.error(f"Город '{city_query}' не найден в стране {country}. Попробуйте уточнить название.")
                st.session_state.found_locs = None
        except:
            st.error("Сервис временно перегружен, попробуйте еще раз через 2 секунды.")

# Выбор конкретного адреса из найденных
selected_location = None
if st.session_state.found_locs:
    choice = st.selectbox("3. Подтвердите ваш город из списка:", list(st.session_state.found_locs.keys()))
    selected_location = st.session_state.found_locs[choice]
    st.success(f"Выбрано: {selected_location.address}")

# --- РАСЧЕТ ---
if selected_location:
    if st.button("🔮 Рассчитать натальную карту"):
        t_clean = re.sub(r'[^0-9:]', '', t_in.replace('.', ':')).strip()[:5]
        try:
            with st.spinner('Звезды выстраиваются в рисунок...'):
                lat, lon = selected_location.latitude, selected_location.longitude
                tf = TimezoneFinder()
                tz = pytz.timezone(tf.timezone_at(lng=lon, lat=lat))
                dt_local = tz.localize(datetime(d.year, d.month, d.day, int(t_clean[:2]), int(t_clean[3:])))
                utc_dt = dt_local.astimezone(pytz.utc)
                
                jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60)
                cusps, ascmc = swe.houses(jd, lat, lon, b'P')
                zod = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

                def get_h(lon_p, c):
                    for i in range(1, 12):
                        if (c[i] < c[i+1] and c[i] <= lon_p < c[i+1]) or (c[i] > c[i+1] and (lon_p >= c[i] or lon_p < c[i+1])): return i
                    return 12

                asc_txt = f"Асцендент: {int(ascmc[0]%30)}° {zod[int(ascmc[0]/30)]}"
                st.markdown(f'<div class="asc-card">🌟 {asc_txt}</div>', unsafe_allow_html=True)

                res_list = []
                # Планеты
                for n, pid in {"Солнце": 0, "Луна": 1, "Меркурий": 2, "Венера": 3, "Марс": 4, "Юпитер": 5, "Сатурн": 6}.items():
                    lon_p = swe.calc_ut(jd, pid)[0][0]
                    h = get_h(lon_p, cusps)
                    line = f"{n}: {int(lon_p%30)}° {zod[int(lon_p/30)]} в {h} доме"
                    res_list.append(line)
                    st.markdown(f'<div class="result-card"><b>{line}</b></div>', unsafe_allow_html=True)

                # Узлы
                rahu = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
                rh = get_h(rahu, cusps)
                res_list.append(f"Сев. Узел (Раху): {int(rahu%30)}° {zod[int(rahu/30)]} в {rh} доме")
                ketu = (rahu + 180) % 360
                kh = (rh + 6) % 12 or 12
                res_list.append(f"Южн. Узел (Кету): {int(ketu%30)}° {zod[int(ketu/30)]} в {kh} доме")
                
                for item in res_list[7:]:
                    st.markdown(f'<div class="result-card" style="border-left-color: #a6817b;"><b>{item}</b></div>', unsafe_allow_html=True)

                img = create_final_img(user_name, d.strftime("%d.%m.%Y"), t_clean, asc_txt, res_list)
                st.download_button("📸 Сохранить карту в галерею", img, f"{user_name}_astro.png", "image/png")
        except:
            st.error("Проверьте время! Оно должно быть в формате 22:22")
