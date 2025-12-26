import streamlit as st
import swisseph as swe
from datetime import datetime
import pytz
import re
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- НАСТРОЙКИ ОФОРМЛЕНИЯ САЙТА ---
st.markdown("""
    <style>
    .stApp { background-color: #fde2e4; }
    h1, h3 { color: #737b69; text-align: center; font-family: 'Arial', sans-serif; }
    .stButton>button { 
        background-color: #a6817b; color: white; 
        border-radius: 20px; width: 100%; border: none; height: 3.5em; font-weight: bold; font-size: 16px;
    }
    .result-card {
        background-color: #ffffff; padding: 15px;
        border-radius: 12px; border-left: 5px solid #9ba192;
        margin-bottom: 10px; color: #4a4a4a; font-family: 'Arial', sans-serif;
    }
    .asc-card {
        background-color: #f0f2ed; padding: 15px;
        border-radius: 12px; border: 2px solid #737b69;
        margin-bottom: 20px; color: #737b69; text-align: center; font-weight: bold; font-family: 'Arial', sans-serif;
    }
    /* Скрываем лишние элементы Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- ФУНКЦИЯ СОЗДАНИЯ КРАСИВОЙ КАРТИНКИ ---
def create_beautiful_image(name, date_str, asc_info, planets_data, nodes_data):
    # 1. Настройка холста и шрифтов
    W, H = 600, 1100
    img = Image.new('RGB', (W, H), color='#fde2e4')
    draw = ImageDraw.Draw(img)

    try:
        # Пытаемся загрузить стандартные красивые шрифты сервера
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 42)
        font_subtitle = ImageFont.truetype("DejaVuSans.ttf", 26)
        font_text = ImageFont.truetype("DejaVuSans.ttf", 28)
        font_asc = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
    except IOError:
        # Если не вышло, берем стандартный (на всякий случай)
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_asc = ImageFont.load_default()

    # Цвета из твоей палитры
    sage_color = "#737b69"
    rose_dark_color = "#a6817b"
    text_color = "#4a4a4a"
    bg_card_color = "#ffffff"
    
    # 2. Рисуем Заголовки
    draw.text((W/2, 60), f"{name}", fill=sage_color, font=font_title, anchor="mm")
    draw.text((W/2, 110), f"{date_str}", fill=rose_dark_color, font=font_title, anchor="mm")
    draw.text((W/2, 160), "Натальная карта малыша", fill=sage_color, font=font_subtitle, anchor="mm")

    # 3. Рисуем Асцендент (в рамочке)
    asc_y = 210
    draw.rectangle([40, asc_y, W-40, asc_y+70], fill="#f0f2ed", outline=sage_color, width=3)
    draw.text((W/2, asc_y+35), asc_info, fill=sage_color, font=font_asc, anchor="mm")

    # 4. Рисуем Список планет
    y_pos = 310
    # Объединяем планеты и узлы для картинки
    full_list = planets_data + nodes_data
    
    for item in full_list:
        # Белая карточка для каждой строчки
        draw.rectangle([40, y_pos, W-40, y_pos+60], fill=bg_card_color)
        # Шалфейная полоска слева
        draw.rectangle([40, y_pos, 50, y_pos+60], fill="#9ba192")
        # Текст
        draw.text((65, y_pos+15), item, fill=text_color, font=font_text)
        y_pos += 75

    # Футер
    draw.text((W/2, H-40), "Создано в звезнном калькуляторе @katy.astro.kids", fill=sage_color, font=font_subtitle, anchor="mm")
    
    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()


# --- ОСНОВНОЙ ИНТЕРФЕЙС ---
st.title("✨ Звёздный калькулятор ✨")

child_name = st.text_input("Имя малыша", value="Мой ребенок")

col1, col2 = st.columns(2)
with col1:
    d = st.date_input("Дата рождения", format="DD/MM/YYYY", min_value=datetime(1900, 1, 1))
    t_input = st.text_input("Время (например: 22:22)", value="12:00")
with col2:
    city_input = st.text_input("Город (английскими, например: Moscow)", value="Moscow")

# --- ЛОГИКА РАСЧЕТА ---
if st.button("Рассчитать и создать красивую карту"):
    clean_time = re.sub(r'[^0-9:]', '', t_input).strip()[:5]
    
    try:
        with st.spinner('Звезды выстраиваются в рисунок...'):
            # 1. Геолокация и время
            geolocator = Nominatim(user_agent="katy_astro_fixed_v2")
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

                # --- ФОРМИРУЕМ ДАННЫЕ ---
                
                # Асцендент
                asc_raw = ascmc[0]
                asc_txt = f"Асцендент: {int(asc_raw%30)}° {zodiac[int(asc_raw/30)]}"
                
                # Планеты
                planets_list_screen = [] # Для экрана
                planets_list_img = []    # Для картинки
                
                planets_db = {
                    "Солнце": swe.SUN, "Луна": swe.MOON, "Меркурий": swe.MERCURY, 
                    "Венера": swe.VENUS, "Марс": swe.MARS, "Юпитер": swe.JUPITER, 
                    "Сатурн": swe.SATURN
                }

                for name, p_id in planets_db.items():
                    lon = swe.calc_ut(jd, p_id)[0][0]
                    p_house = 0
                    for i in range(1, 13):
                        c1, c2 = cusps[i], cusps[i+1] if i < 12 else cusps[1]
                        if (c1 < c2 and c1 <= lon < c2) or (c1 > c2 and (lon >= c1 or lon < c2)):
                            p_house = i; break
                    
                    res_line = f"{name}: {int(lon%30)}° {zodiac[int(lon/30)]} в {p_house} доме"
                    planets_list_screen.append(res_line)
                    planets_list_img.append(res_line)

                # Узлы (Раху и Кету)
                nodes_list_screen = []
                nodes_list_img = []
                
                rahu_lon = swe.calc_ut(jd, swe.MEAN_NODE)[0][0]
                r_house = 0
                for i in range(1, 13):
                    c1, c2 = cusps[i], cusps[i+1] if i < 12 else cusps[1]
                    if (c1 < c2 and c1 <= rahu_lon < c2) or (c1 > c2 and (rahu_lon >= c1 or rahu_lon < c2)):
                        r_house = i; break
                rahu_line = f"Северный Узел (Раху): {int(rahu_lon%30)}° {zodiac[int(rahu_lon/30)]} в {r_house} доме"
                nodes_list_screen.append(rahu_line)
                nodes_list_img.append(rahu_line)

                # Кету (напротив Раху)
                ketu_lon = (rahu_lon + 180) % 360
                k_house = (r_house + 6) % 12 if (r_house + 6) % 12 != 0 else 12
                ketu_line = f"Южный Узел (Кету): {int(ketu_lon%30)}° {zodiac[int(ketu_lon/30)]} в {k_house} доме"
                nodes_list_screen.append(ketu_line)
                nodes_list_img.append(ketu_line)

                # --- ВЫВОД НА ЭКРАН (ТЕПЕРЬ ВСЕ ЕСТЬ!) ---
                st.markdown(f'<div class="asc-card">🌟 <b>{asc_txt}</b></div>', unsafe_allow_html=True)
                for item in planets_list_screen:
                    st.markdown(f'<div class="result-card"><b>{item}</b></div>', unsafe_allow_html=True)
                for item in nodes_list_screen:
                     st.markdown(f'<div class="result-card" style="border-left-color: #a6817b;"><b>{item}</b></div>', unsafe_allow_html=True)

                # --- ГЕНЕРАЦИЯ КРАСИВОЙ КАРТИНКИ ---
                date_str = d.strftime("%d.%m.%Y")
                img_data = create_beautiful_image(child_name, date_str, asc_txt, planets_list_img, nodes_list_img)
                
                st.download_button(
                    label="📸 Скачать красивую карту в галерею",
                    data=img_data,
                    file_name=f"{child_name}_astro_card.png",
                    mime="image/png"
                )
                
            else:
                st.error("Город не найден. Проверьте написание на английском.")
    except Exception as e:
        st.error(f"Ошибка в данных. Проверьте время (ЧЧ:ММ). Детали: {e}")
