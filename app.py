import streamlit as st
import swisseph as swe
from datetime import datetime
import pytz
import re
from timezonefinder import TimezoneFinder
from PIL import Image, ImageDraw, ImageFont
import io
import geonamescache

# --- ДИЗАЙН (Твоя палитра: Шалфей и Роза) ---
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
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- БАЗА ГОРОДОВ (ОФФЛАЙН) ---
gc = geonamescache.GeonamesCache()
def get_city_data(name):
    cities = gc.get_cities()
    for c_id in cities:
        if cities[c_id]['name'].lower() == name.lower():
            return cities[c_id]
    return None

# --- ГЕНЕРАЦИЯ КАРТИНКИ (W=750) ---
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
    draw.text((W/2, 115), f"{date_str}  {time_str}", fill="#a6817b", font=f_title, anchor="mm")
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

# --- ИНТЕРФЕЙС ---
st.title("✨ Звёздный калькулятор ✨")
user_name = st.text_input("Имя ребенка", value="Мишель")

col1, col2 = st.columns(2)
with col1:
    city_in = st.text_input("Город на английском", value="Tel Aviv")
    d = st.date_input("Дата рождения", format="DD/MM/YYYY", min_value=datetime(1900, 1, 1))
with col2:
    t_in = st.text_input("Время (ЧЧ:ММ)", value="22:22")

if st.button("Рассчитать и сохранить карту"):
    # Чистим время
    t_clean = re.sub(r'[^0-9:]', '', t_in.replace('.', ':')).strip()[:5]
    if len(t_clean) < 5 and ':' in t_clean:
        h, m = t_clean.split(':')
        t_clean = f"{h.zfill(2)}:{m.zfill(2)}"

    try:
        with st.spinner('Анализирую небо...'):
            city = get_city_data(city_in)
            if city:
                tf = TimezoneFinder()
                tz = pytz.timezone(tf.timezone_at(lng=city['longitude'], lat=city['latitude']))
                
                # Локальное время (то, что ввел юзер)
                local_dt = tz.localize(datetime(d.year, d.month, d.day, int(t_clean[:2]), int(t_clean[3:])))
                # Время UTC (для расчетов)
                utc_dt = local_dt.astimezone(pytz.utc)
                
                jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60)
                cusps, ascmc = swe.houses(jd, city['latitude'], city['longitude'], b'P')
                zod = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
                
                def get_h(lon, c):
                    for i in range(1, 12):
                        if (c[i] < c[i+1] and c[i] <= lon < c[i+1]) or (c[i] > c[i+1] and (lon >= c[i] or lon < c[i+1])): return i
                    return 12

                asc_txt = f"Асцендент: {int(ascmc[0]%30)}° {zod[int(ascmc[0]/30)]}"
                st.markdown(f'<div class="asc-card">🌟 {asc_txt}</div>', unsafe_allow_html=True)

                all_results = []
                # Планеты
                for n, pid in {"Солнце": 0, "Луна": 1, "Меркурий": 2, "Венера": 3, "Марс": 4, "Юпитер": 5, "Сатурн": 6}.items():
                    lon = swe.calc_ut(jd, pid)[0][0]
                    h = get_h(lon, cusps)
                    line = f"{n}: {int(lon%30)}° {zod[int(lon/30)]} в {h} доме"
                    all_results.append(line)
                    st.markdown(f'<div class="result-card"><b>{line}</b></div>', unsafe_allow_html=True)

                # Узлы
                rahu = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
                rh = get_h(rahu, cusps)
                all_results.append(f"Сев. Узел (Раху): {int(rahu%30)}° {zod[int(rahu/30)]} в {rh} доме")
                ketu = (rahu + 180) % 360
                kh = (rh + 6) % 12 or 12
                all_results.append(f"Южн. Узел (Кету): {int(ketu%30)}° {zod[int(ketu/30)]} в {kh} доме")
                
                for item in all_results[7:]:
                    st.markdown(f'<div class="result-card" style="border-left-color: #a6817b;"><b>{item}</b></div>', unsafe_allow_html=True)

                img_bin = create_final_img(user_name, d.strftime("%d.%m.%Y"), t_clean, asc_txt, all_results)
                st.download_button("📸 Скачать именную карту", img_bin, f"{user_name}_astro.png", "image/png")
            else:
                st.error("Город не найден в оффлайн-базе. Проверьте English.")
    except Exception as e:
        st.error(f"Проверьте время! Оно должно быть как 22:22.")
