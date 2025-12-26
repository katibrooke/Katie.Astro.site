import streamlit as st
import swisseph as swe
from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# Настройка эстетики (твоя палитра)
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
st.write("### Узнайте положение планет в карте вашего ребенка")

# Поля ввода
col1, col2 = st.columns(2)
with col1:
    d = st.date_input("Дата рождения", format="DD/MM/YYYY", min_value=datetime(1900, 1, 1))
    # ВВОД ВРЕМЕНИ ВРУЧНУЮ (ТЕКСТОМ)
    t_str = st.text_input("Время (например, 22:22)", value="22:22")
with col2:
    city = st.text_input("Город на английском (например: Tel Aviv)", value="Tel Aviv")

if st.button("Рассчитать карту"):
    try:
        # 1. Поиск города и часового пояса
        geolocator = Nominatim(user_agent="katy_astro_brand")
        location = geolocator.geocode(city, timeout=10)
        
        if location:
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            timezone = pytz.timezone(tz_name)
            
            # Очистка и проверка формата времени
            t_str = t_str.strip().replace('.', ':').replace(' ', '')
            time_obj = datetime.strptime(t_str, "%H:%M")
            
            local_dt = timezone.localize(datetime(d.year, d.month, d.day, time_obj.hour, time_obj.minute))
            utc_dt = local_dt.astimezone(pytz.utc)
            
            # 2. Расчет Юлианской даты
            jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, utc_dt.hour + utc_dt.minute/60)
            
            # 3. Расчет Домов (Система Плацидус)
            # В pyswisseph cusps возвращает 13 элементов, индекс 1-12 — это дома
            cusps, ascmc = swe.houses(jd, location.latitude, location.longitude, b'P')
            
            planets = {
                "Солнце": swe.SUN, "Луна": swe.MOON, "Меркурий": swe.MERCURY, 
                "Венера": swe.VENUS, "Марс": swe.MARS, "Юпитер": swe.JUPITER, "Сатурн": swe.SATURN
            }
            zodiac = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

            st.success(f"Расчет готов для {city}")
            
            for name, p_id in planets.items():
                # Исправлено: берем только первый элемент результата (долготу)
                res_data, flag = swe.calc_ut(jd, p_id)
                lon = res_data[0]
                
                sign_idx = int(lon / 30)
                deg = int(lon % 30)
                
                # Поиск дома планеты
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
            
            st.info("💡 Это базовый расчет. За полной расшифровкой талантов и натальной карты пишите мне в Директ!")
        else:
            st.error("Город не найден. Напишите название на английском (например: Tel Aviv).")
    except ValueError:
        st.error("Ошибка в формате времени. Напишите, например, 22:22")
    except Exception as e:
        st.error("Произошла ошибка при расчете. Попробуйте еще раз.")
