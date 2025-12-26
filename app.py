import streamlit as st
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib.chart import Chart
from geopy.geocoders import Nominatim

# Настройка стилей в вашей палитре
st.markdown(f"""
    <style>
    .stApp {{
        background-color: #fde2e4; /* Самый светлый розовый из палитры */
    }}
    h1, h2, h3 {{
        color: #737b69; /* Темный оливковый для заголовков */
    }}
    .stButton>button {{
        background-color: #a6817b; /* Пыльная роза для кнопки */
        color: white;
        border-radius: 20px;
        border: none;
    }}
    .result-card {{
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #9ba192; /* Шалфейный акцент */
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

st.title("✨ Звездный путеводитель малыша")
st.subheader("Узнайте точное положение планет вашего ребенка")

# Поля ввода
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Дата рождения")
        time = st.time_input("Точное время")
    with col2:
        city_name = st.text_input("Город рождения (на английском, например: Tel Aviv)")

if st.button("Рассчитать карту"):
    try:
        # 1. Получаем координаты города
        geolocator = Nominatim(user_agent="astro_kids_app")
        location = geolocator.geocode(city_name)
        
        if location:
            lat = location.latitude
            lon = location.longitude
            
            # 2. Настройка данных для расчета
            # Формат даты для flatlib: YYYY/MM/DD
            date_str = date.strftime('%Y/%m/%d')
            time_str = time.strftime('%H:%M')
            
            dt = Datetime(date_str, time_str, '+00:00') # В идеале нужно добавить расчет таймзоны
            pos = GeoPos(lat, lon)
            chart = Chart(dt, pos, hsys='Placidus') # Система домов Плацидус
            
            st.success(f"Карта построена для: {city_name}")
            
            # 3. Вывод результатов (только данные, без трактовок)
            planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']
            
            for p_id in planets:
                planet = chart.get(p_id)
                # Получаем дом
                house = chart.houses.getHouse(planet.lon)
                
                st.markdown(f"""
                <div class="result-card">
                    <b>{p_id} ({"Солнце" if p_id=='Sun' else "Луна" if p_id=='Moon' else "Марс" if p_id=='Mars' else p_id})</b>: 
                    {round(planet.lon % 30, 2)}° {planet.sign} в {house} доме
                </div>
                """, unsafe_allow_html=True)
            
            st.info("Хотите полную расшифровку талантов и предназначения? Пишите мне в Директ!")
        else:
            st.error("Город не найден. Попробуйте написать на английском.")
    except Exception as e:
        st.error(f"Произошла ошибка при расчете. Проверьте данные.")
