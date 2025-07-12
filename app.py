import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

st.set_page_config(page_title="AstroData Filter", layout="wide")

@st.cache_data
def load_xml():
    with open("astrodata.xml", "r", encoding="utf-8") as f:
        tree = ET.parse(f)
    return tree.getroot()

root = load_xml()

def extract_degree(degmin):
    try:
        deg = degmin.split("\u00b0")[0]
        return int(deg)
    except:
        return None

sign_translate = {
    'ari': 'Овен', 'tau': 'Телец', 'gem': 'Близнецы', 'can': 'Рак',
    'leo': 'Лев', 'vir': 'Дева', 'lib': 'Весы', 'sco': 'Скорпион',
    'sag': 'Стрелец', 'cap': 'Козерог', 'aqu': 'Водолей', 'pis': 'Рыбы'
}

reverse_sign_translate = {v: k for k, v in sign_translate.items()}

sign_options = ["Любой"] + list(sign_translate.values())
degree_min, degree_max = 1, 30

def translate_sign(sign):
    if not sign:
        return ""
    if "/" in sign:
        parts = sign.split("/")
        return "/".join([sign_translate.get(p, p) for p in parts])
    return sign_translate.get(sign, sign)

entries = []
category_translation = {}

for entry in root.findall("adb_entry"):
    aid = entry.get("adb_id")
    public_data = entry.find("public_data")
    bdata = public_data.find("bdata") if public_data is not None else None
    positions = bdata.find("positions") if bdata is not None else None

    rodden = public_data.findtext("roddenrating")
    name = public_data.findtext("name")
    bio = public_data.findtext("bio") or ""

    date_str = bdata.findtext("date") if bdata is not None else None
    time_str = bdata.findtext("time") if bdata is not None else None
    if date_str and time_str:
        birth_dt = f"{date_str} {time_str}"
    elif date_str:
        birth_dt = date_str
    else:
        birth_dt = ""

    sun_sign_raw = positions.get("sun_sign") if positions is not None else None
    sun_sign = translate_sign(sun_sign_raw)
    sun_deg = extract_degree(positions.get("sun_degmin")) if positions is not None else None
    moon_sign_raw = positions.get("moon_sign") if positions is not None else None
    moon_sign = translate_sign(moon_sign_raw)
    moon_deg = extract_degree(positions.get("moon_degmin")) if positions is not None else None
    asc_sign_raw = positions.get("asc_sign") if positions is not None else None
    asc_sign = translate_sign(asc_sign_raw)
    asc_deg = extract_degree(positions.get("asc_degmin")) if positions is not None else None

    research_data = entry.find("research_data")
    raw_categories = []
    if research_data is not None:
        cats = research_data.find("categories")
        if cats is not None:
            for cat in cats.findall("category"):
                if cat.text:
                    raw_categories.append(cat.text.strip())

    category_label = raw_categories[0] if raw_categories else "Без категории"
    category_translation[category_label] = category_translation.get(category_label, category_label)

    entries.append({
        "Имя": name,
        "Дата рождения": birth_dt,
        "Рейтинг Роддена": rodden,
        "Знак Солнца": sun_sign,
        "Градус Солнца": sun_deg,
        "Знак Луны": moon_sign,
        "Градус Луны": moon_deg,
        "Знак Асцендента": asc_sign,
        "Градус Асцендента": asc_deg,
        "Категория": category_label,
        "Описание": bio
    })

df = pd.DataFrame(entries)

st.title("Фильтр по базе AstroDatabank")

col1, col2, col3 = st.columns(3)
with col1:
    selected_rodden = st.selectbox("Рейтинг Роддена", options=["Любой"] + sorted(df["Рейтинг Роддена"].dropna().unique().tolist()), index=(sorted(df["Рейтинг Роддена"].dropna().unique().tolist()).index("AA") + 1 if "AA" in df["Рейтинг Роддена"].values else 0))
    selected_sun_sign = st.selectbox("Знак Солнца", options=sign_options)
    selected_sun_deg_range = st.slider("Градус Солнца", min_value=degree_min, max_value=degree_max, value=(degree_min, degree_max))
with col2:
    selected_moon_sign = st.selectbox("Знак Луны", options=sign_options)
    selected_moon_deg_range = st.slider("Градус Луны", min_value=degree_min, max_value=degree_max, value=(degree_min, degree_max))
with col3:
    selected_asc_sign = st.selectbox("Знак Асцендента", options=sign_options)
    selected_asc_deg_range = st.slider("Градус Асцендента", min_value=degree_min, max_value=degree_max, value=(degree_min, degree_max))
    selected_category = st.selectbox("Категория", options=["Любая"] + sorted(df["Категория"].dropna().unique()))

# Фильтрация
filtered_df = df.copy()
if selected_rodden != "Любой":
    filtered_df = filtered_df[filtered_df["Рейтинг Роддена"] == selected_rodden]
if selected_sun_sign != "Любой":
    filtered_df = filtered_df[filtered_df["Знак Солнца"] == selected_sun_sign]
filtered_df = filtered_df[filtered_df["Градус Солнца"].between(*selected_sun_deg_range)]
if selected_moon_sign != "Любой":
    filtered_df = filtered_df[filtered_df["Знак Луны"] == selected_moon_sign]
filtered_df = filtered_df[filtered_df["Градус Луны"].between(*selected_moon_deg_range)]
if selected_asc_sign != "Любой":
    filtered_df = filtered_df[filtered_df["Знак Асцендента"] == selected_asc_sign]
filtered_df = filtered_df[filtered_df["Градус Асцендента"].between(*selected_asc_deg_range)]
if selected_category != "Любая":
    filtered_df = filtered_df[filtered_df["Категория"] == selected_category]

st.write(f"Найдено записей: {len(filtered_df)}")

for i, row in filtered_df.iterrows():
    with st.expander(f"{row['Имя']} ({row['Дата рождения']})"):
        st.markdown(f"**Категория:** {row['Категория']}  ")
        st.markdown(f"**Описание:** {row['Описание']}")
