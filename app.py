import streamlit as st
import swisseph as swe
from datetime import datetime
from geopy.geocoders import Nominatim

# Твоя красивая палитра (шалфей и роза)
st.markdown("""
    <style>
    .stApp { background-color: #fde2e4; }
    h1, h2, h3 { color: #737b69; text-align: center; font-family: 'Arial'; }
    .stButton>button { 
        background-color: #a6817b; color: white; 
        border-radius: 20px; width: 100%; border: none; height: 3em;
    }
    .result-card {
        background-color: #ffffff; padding: 15px;
        border-radius: 12px; border-left: 5px solid #9ba192;
        margin-bottom: 10px; color: #4a4a4a; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("✨ Звездный путеводитель")
st.write("### Узнайте таланты вашего малыша по звездам")

# Ввод данных
col1, col2 = st.columns(2)
with col1:
    d = st.date_input("Дата рождения")
    t = st.time_input("Время рождения")
with col2:
    city = st.text_input("Город (на английском, например: Tel Aviv)")

if st.button("Рассчитать планеты"):
    try:
        geolocator = Nominatim(user_agent="katy_astro_app")
        loc = geolocator.geocode(city)
        if loc:
            # Расчет Юлианской даты (математика для звезд)
            jd = swe.julday(d.year, d.month, d.day, t.hour + t.minute/60)
            
            planets = {
                "Солнце (Личность)": swe.SUN, 
                "Луна (Эмоции)": swe.MOON, 
                "Меркурий (Интеллект)": swe.MERCURY, 
                "Венера (Социализация)": swe.VENUS, 
                "Марс (Энергия)": swe.MARS
            }
            zodiac = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", 
                      "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

            st.success(f"Расчет выполнен для города: {city}")
            
            for name, p_id in planets.items():
                res = swe.calc_ut(jd, p_id)[0]
                sign_idx = int(res / 30)
                deg = round(res % 30, 2)
                
                st.markdown(f"""
                <div class="result-card">
                    <b>{name}</b>: {deg}° {zodiac[sign_idx]}
                </div>
                """, unsafe_allow_html=True)
            
            st.info("💡 Это базовые данные. За полной расшифровкой талантов и домов пишите мне в Директ!")
        else:
            st.error("Город не найден. Попробуйте написать название на английском.")
    except Exception as e:
        st.error("Что-то пошло не так. Проверьте правильность введенных данных.")
