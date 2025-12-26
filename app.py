import streamlit as st
import swisseph as swe
from datetime import datetime
import pytz
import re
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# Настройка дизайна (твоя палитра)
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
    label { color: #737b69 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("✨ Звёздный калькулятор ✨")
st.write("### Положение планет в карте вашего ребенка")

col1, col2 = st.columns(2)
with col1:
    d = st.date_input("Дата рождения", format="DD/MM/YYYY", min_value=datetime(1900, 1, 1))
    t_input = st.text_input("Время (напишите, например: 22:22)", value="22:22")
with col2:
    city_input = st.text_input("Город на английском (например: Tel Aviv)", value="Tel Aviv")

if st.button("Рассчитать карту"):
    # Очистка времени: оставляем только цифры и двоеточие, берем первые 5 символов
    clean_time = re.sub(r'[^0-9:]', '', t_input).strip()
    if len(clean_time) > 5: clean_time = clean_time[:5]
    
    try:
        with st.spinner('Связываюсь со звездами...'):
            # 1. Поиск города
            geolocator = Nominatim(user_agent="katy_astro_final_app")
            location = geolocator.geocode(city_input, timeout=15)
            
            if not location:
                st.error("Город не найден. Напишите, пожалуйста, на английском.")
            else:
                # 2. Поиск часового пояса
                tf = TimezoneFinder()
                tz_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
                timezone = pytz.timezone(tz_name)
                
                # Парсинг времени
                time_obj = datetime.strptime(clean_time, "%H:%M")
                local_dt = timezone.localize(datetime(d.year, d.month, d.day, time_obj.hour, time_obj.minute))
                utc_dt = local_dt.astimezone(pytz.utc)
                
                # 3. Астрономический расчет
                jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60)
                cusps, ascmc = swe.houses(jd, location.latitude, location.longitude, b'P')
                
                planets = {
                    "Солнце": swe.SUN, "Луна": swe.MOON, "Меркурий": swe.MERCURY, 
                    "Венера": swe.VENUS, "Марс": swe.MARS, "Юпитер": swe.JUPITER, "Сатурн": swe.SATURN
                }
                zodiac = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

                st.success(f"Расчет готов для {city_input}")
                
                for name, p_id in planets.items():
                    res, flag = swe.calc_ut(jd, p_id)
                    lon = res[0] # Берем только долготу из результата
                    
                    sign_idx = int(lon / 30)
                    deg = int(lon % 30)
                    
                    # Поиск дома
                    p_house = 0
                    for i in range(1, 13):
                        c1 = cusps[i]
                        c2 = cusps[i+1] if i < 12 else cusps[1]
                        if c1 < c2:
                            if c1 <= lon < c2: p_house = i; break
                        else: # Если дом пересекает 0° Овна
                            if lon >= c1 or lon < c2: p_house = i; break

                    st.markdown(f"""
                    <div class="result-card">
                        <b>{name}</b>: {deg}° {zodiac[sign_idx]} в {p_house} доме
                    </div>
                    """, unsafe_allow_html=True)
    except ValueError:
        st.error("Проверьте формат времени. Должно быть ЧЧ:ММ (например, 22:22)")
    except Exception as e:
        st.error("Сервис поиска городов временно перегружен. Попробуйте нажать кнопку еще раз через 10 секунд.")
