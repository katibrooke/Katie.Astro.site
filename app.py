import streamlit as st
import swisseph as swe
from datetime import datetime
import pytz
import re
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# Красивое оформление (твоя палитра: шалфей и роза)
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
        margin-bottom: 10px; color: #4a4a4a; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .asc-card {
        background-color: #f0f2ed; padding: 15px;
        border-radius: 12px; border: 2px solid #737b69;
        margin-bottom: 20px; color: #737b69; text-align: center;
    }
    label { color: #737b69 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("✨ Звёздный калькулятор ✨")
st.write("### Положение планет в карте вашего ребенка")

# Поля ввода
col1, col2 = st.columns(2)
with col1:
    d = st.date_input("Дата рождения", format="DD/MM/YYYY", min_value=datetime(1900, 1, 1))
    t_input = st.text_input("Время (напишите, например: 22:22)", value="22:22")
with col2:
    city_input = st.text_input("Город на английском (например: Tel Aviv)", value="Tel Aviv")

if st.button("Рассчитать карту"):
    # Очистка времени от лишних знаков
    clean_time = re.sub(r'[^0-9:]', '', t_input).strip()
    if len(clean_time) > 5: clean_time = clean_time[:5]
    
    try:
        with st.spinner('Считываю энергию планет...'):
            geolocator = Nominatim(user_agent="katy_astro_final_v3")
            location = geolocator.geocode(city_input, timeout=15)
            
            if location:
                tf = TimezoneFinder()
                tz_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
                timezone = pytz.timezone(tz_name)
                
                time_obj = datetime.strptime(clean_time, "%H:%M")
                local_dt = timezone.localize(datetime(d.year, d.month, d.day, time_obj.hour, time_obj.minute))
                utc_dt = local_dt.astimezone(pytz.utc)
                
                jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60)
                cusps, ascmc = swe.houses(jd, location.latitude, location.longitude, b'P')
                
                zodiac = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

                # 1. СНАЧАЛА АСЦЕНДЕНТ (Точка входа)
                asc_lon = ascmc[0]
                asc_sign = zodiac[int(asc_lon / 30)]
                asc_deg = int(asc_lon % 30)
                st.markdown(f"""<div class="asc-card">🌟 <b>Асцендент (Восходящий знак)</b>: {asc_deg}° {asc_sign}</div>""", unsafe_allow_html=True)

                # 2. ЗАТЕМ ПЛАНЕТЫ
                planets = {
                    "Солнце": swe.SUN, "Луна": swe.MOON, "Меркурий": swe.MERCURY, 
                    "Венера": swe.VENUS, "Марс": swe.MARS, "Юпитер": swe.JUPITER, "Сатурн": swe.SATURN
                }
                
                for name, p_id in planets.items():
                    res, flag = swe.calc_ut(jd, p_id)
                    lon = res[0]
                    sign_idx = int(lon / 30)
                    deg = int(lon % 30)
                    
                    # Поиск дома
                    p_house = 0
                    for i in range(1, 13):
                        c1, c2 = cusps[i], cusps[i+1] if i < 12 else cusps[1]
                        if (c1 < c2 and c1 <= lon < c2) or (c1 > c2 and (lon >= c1 or lon < c2)):
                            p_house = i; break
                    
                    st.markdown(f"""<div class="result-card"><b>{name}</b>: {deg}° {zodiac[sign_idx]} в {p_house} доме</div>""", unsafe_allow_html=True)

                # 3. В КОНЦЕ УЗЛЫ (Кармический путь)
                rahu_res, _ = swe.calc_ut(jd, swe.MEAN_NODE)
                r_lon = rahu_res[0]
                r_sign = zodiac[int(r_lon / 30)]
                r_deg = int(r_lon % 30)
                
                # Дома для узлов
                for i in range(1, 13):
                    c1, c2 = cusps[i], cusps[i+1] if i < 12 else cusps[1]
                    if (c1 < c2 and c1 <= r_lon < c2) or (c1 > c2 and (r_lon >= c1 or r_lon < c2)):
                        r_house = i; break

                st.markdown(f"""<div class="result-card"><b>Северный Узел (Раху)</b>: {r_deg}° {r_sign} в {r_house} доме</div>""", unsafe_allow_html=True)

                # Южный узел всегда напротив
                k_lon = (r_lon + 180) % 360
                k_sign = zodiac[int(k_lon / 30)]
                k_deg = int(k_lon % 30)
                k_house = (r_house + 6) % 12
                if k_house == 0: k_house = 12
                
                st.markdown(f"""<div class="result-card"><b>Южный Узел (Кету)</b>: {k_deg}° {k_sign} в {k_house} доме</div>""", unsafe_allow_html=True)

                st.info("💡 Это базовая карта. За подробным разбором талантов ребенка пишите мне в Директ!")
            else:
                st.error("Город не найден. Напишите, пожалуйста, на английском.")
    except Exception as e:
        st.error("Проверьте формат времени (например, 22:22).")
