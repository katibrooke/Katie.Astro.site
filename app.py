import streamlit as st
import swisseph as swe
from datetime import datetime
import pytz
import re
from timezonefinder import TimezoneFinder
from PIL import Image, ImageDraw, ImageFont
import io
import geonamescache

# --- ОФОРМЛЕНИЕ (Твоя палитра) ---
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

# --- РАБОТА С БАЗОЙ ГОРОДОВ (ОФФЛАЙН) ---
gc = geonamescache.GeonamesCache()

def find_city_offline(city_name):
    cities = gc.get_cities()
    found_cities = []
    # Ищем город в базе (без учета регистра)
    for city_id in cities:
        city = cities[city_id]
        if city['name'].lower() == city_name.lower():
            found_cities.append(city)
    return found_cities

# --- ГЕНЕРАЦИЯ КАРТИНКИ ---
def create_final_img(name, date_str, asc_info, planets_data, nodes_data):
    W, H = 750, 1150
    img = Image.new('RGB', (W, H), color='#fde2e4')
    draw = ImageDraw.Draw(img)
    try:
        f_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 46)
        f_text = ImageFont.truetype("DejaVuSans.ttf", 28)
    except:
        f_title = f_text = ImageFont.load_default()

    draw.text((W/2, 70), name, fill="#737b69", font=f_title, anchor="mm")
    draw.text((W/2, 130), date_str, fill="#a6817b", font=f_title, anchor="mm")
    draw.text((W/2, 190), "Расчет положения планет в натальной карте", fill="#737b69", font=f_text, anchor="mm")
    draw.rectangle([50, 250, W-50, 330], fill="#f0f2ed", outline="#737b69", width=4)
    draw.text((W/2, 290), asc_info, fill="#737b69", font=f_title, anchor="mm")
    y = 370
    for i, item in enumerate(planets_data + nodes_data):
        color = "#9ba192" if i < len(planets_data) else "#a6817b"
        draw.rectangle([50, y, W-50, y+65], fill="white")
        draw.rectangle([50, y, 65, y+65], fill=color)
        draw.text((80, y+18), item, fill="#4a4a4a", font=f_text)
        y += 80
    draw.text((W/2, H-50), "Создано в @katy.astro.kids", fill="#737b69", font=f_text, anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- САЙТ ---
st.title("✨ Звёздный калькулятор ✨")
child_name = st.text_input("Имя", value="Мишель")

col1, col2 = st.columns(2)
with col1:
    city_in = st.text_input("Город на английском (например: Kazan)", value="Kazan")
    d = st.date_input("Дата рождения", format="DD/MM/YYYY", min_value=datetime(1900, 1, 1))
with col2:
    t_in = st.text_input("Время (например: 22:22)", value="22:22")

# Кнопка расчета
if st.button("Рассчитать карту"):
    t_clean = re.sub(r'[^0-9:]', '', t_in).strip()[:5]
    try:
        with st.spinner('Поиск города в базе...'):
            found = find_city_offline(city_in)
            
            if not found:
                st.error(f"Город '{city_in}' не найден в базе. Проверьте написание (English).")
            else:
                # Если найдено несколько городов с таким именем, берем первый (самый крупный)
                best_city = found[0]
                lat, lon = best_city['latitude'], best_city['longitude']
                
                tf = TimezoneFinder()
                tz = pytz.timezone(tf.timezone_at(lng=lon, lat=lat))
                dt = tz.localize(datetime(d.year, d.month, d.day, int(t_clean[:2]), int(t_clean[3:])))
                utc_dt = dt.astimezone(pytz.utc)
                
                jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60)
                cusps, ascmc = swe.houses(jd, lat, lon, b'P')
                zod = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
                
                def get_h(lon_p, c):
                    for i in range(1, 12):
                        if (c[i] < c[i+1] and c[i] <= lon_p < c[i+1]) or (c[i] > c[i+1] and (lon_p >= c[i] or lon_p < c[i+1])): return i
                    return 12

                asc_txt = f"Асцендент: {int(ascmc[0]%30)}° {zod[int(ascmc[0]/30)]}"
                st.markdown(f'<div class="asc-card">🌟 {asc_txt}</div>', unsafe_allow_html=True)

                p_list, n_list = [], []
                # Планеты
                for n, p_id in {"Солнце": 0, "Луна": 1, "Меркурий": 2, "Венера": 3, "Марс": 4, "Юпитер": 5, "Сатурн": 6}.items():
                    lon_p = swe.calc_ut(jd, p_id)[0][0]
                    h = get_h(lon_p, cusps)
                    line = f"{n}: {int(lon_p%30)}° {zod[int(lon_p/30)]} в {h} доме"
                    p_list.append(line)
                    st.markdown(f'<div class="result-card"><b>{line}</b></div>', unsafe_allow_html=True)

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
    except Exception as e:
        st.error(f"Проверьте формат времени (22:22).")
