import streamlit as st
import swisseph as swe
from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# Стилизация
st.markdown("""
    <style>
    .stApp { background-color: #fde2e4; }
    h1, h3 { color: #737b69; text-align: center; }
    .stButton>button { 
        background-color: #a6817b; color: white; 
        border-radius: 20px; width: 100%; border: none; height: 3.5em; font-weight: bold;
    }
    .result-card {
        background-color: #ffffff; padding: 15px;
        border-radius: 12px; border-left: 5px solid #9ba192;
        margin-bottom: 10px; color: #4a4a4a;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("✨ Звёздный калькулятор ✨")

# Поля ввода
d = st.date_input("Дата рождения", format="DD/MM/YYYY", min_value=datetime(1900, 1, 1))
# ВВОД ВРЕМЕНИ ТЕКСТОМ
t_str = st.text_input("Время (например, 22:22)", value="12:00")
city = st.text_input("Город на английском (например: Tel Aviv)")

if st.button("Рассчитать карту"):
    try:
        # 1. Гео-данные и Часовой пояс
        geolocator = Nominatim(user_agent="katy_astro_helper")
        location = geolocator.geocode(city)
        
        if location:
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            timezone = pytz.timezone(tz_name)
            
            # Парсим время
            time_obj = datetime.strptime(t_str, "%H:%M")
            local_dt = timezone.localize(datetime(d.year, d.month, d.day, time_obj.hour, time_obj.minute))
            utc_dt = local_dt.astimezone(pytz.utc)
            
            # 2. Расчет Юлианской даты
            jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60)
            
            # 3. Расчет Домов (Placidus)
            cusps, ascmc = swe.houses(jd, location.latitude, location.longitude, b'P')
            
            planets = {
                "Солнце": swe.SUN, "Луна": swe.MOON, "Меркурий": swe.MERCURY, 
                "Венера": swe.VENUS, "Марс": swe.MARS, "Юпитер": swe.JUPITER, "Сатурн": swe.SATURN
            }
            zodiac = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

            st.success(f"Расчет готов для {city} (Пояс: {tz_name})")
            
            for name, p_id in planets.items():
                res = swe.calc_ut(jd, p_id)[0]
                sign_idx = int(res / 30)
                deg = int(res % 30)
                
                # Определяем дом планеты
                p_house = 0
                for i in range(12):
                    if i < 11:
                        if cusps[i] <= res < cusps[i+1]: p_house = i + 1
                    else:
                        if res >= cusps[11] or res < cusps[0]: p_house = 12

                st.markdown(f"""
                <div class="result-card">
                    <b>{name}</b>: {deg}° {zodiac[sign_idx]} в {p_house} доме
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error("Город не найден. Напиши латиницей, например: Tel Aviv")
    except Exception as e:
        st.error(f"Проверь формат времени (должно быть 22:22). Ошибка: {e}")
