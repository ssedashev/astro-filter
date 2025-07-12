import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

st.set_page_config(page_title="AstroData Filter", layout="wide")

# --- Загрузка XML-файла из репозитория ---
@st.cache_data
def load_xml():
    with open("astrodata.xml", "r", encoding="utf-8") as f:
        tree = ET.parse(f)
    return tree.getroot()

root = load_xml()

# --- Вспомогательная функция ---
def extract_degree(degmin):
    try:
        deg = degmin.split("\u00b0")[0]
        return int(deg)
    except:
        return None

# --- Сбор основной информации из каждого adb_entry ---
entries = []
categories_map = {
    'спортсмен': ['Sports'],
    'актёр': ['Actor', 'TV', 'Entertainment : Live Stage'],
    'писатель': ['Writer', 'Autobiographer', 'Journalist', 'Poet', 'Fiction']
}

for entry in root.findall("adb_entry"):
    aid = entry.get("adb_id")
    public_data = entry.find("public_data")
    bdata = public_data.find("bdata") if public_data is not None else None
    positions = bdata.find("positions") if bdata is not None else None

    rodden = public_data.findtext("roddenrating")
    sun_sign = positions.get("sun_sign") if positions is not None else None
    sun_deg = extract_degree(positions.get("sun_degmin")) if positions is not None else None
    moon_sign = positions.get("moon_sign") if positions is not None else None
    moon_deg = extract_degree(positions.get("moon_degmin")) if positions is not None else None
    asc_sign = positions.get("asc_sign") if positions is not None else None
    asc_deg = extract_degree(positions.get("asc_degmin")) if positions is not None else None

    # категории (если есть)
    research_data = entry.find("research_data")
    raw_categories = []
    if research_data is not None:
        cats = research_data.find("categories")
        if cats is not None:
            for cat in cats.findall("category"):
                if cat.text:
                    raw_categories.append(cat.text.strip())

    entries.append({
        "adb_id": aid,
        "rodden": rodden,
        "sun_sign": sun_sign,
        "sun_deg": sun_deg,
        "moon_sign": moon_sign,
        "moon_deg": moon_deg,
        "asc_sign": asc_sign,
        "asc_deg": asc_deg,
        "categories_raw": raw_categories
    })

# --- Преобразование в DataFrame ---
df = pd.DataFrame(entries)

# --- Преобразование категорий в текстовую метку (спортсмен, актёр, писатель) ---
def label_category(cat_list):
    if not cat_list:
        return None
    for label, keys in categories_map.items():
        if any(any(k.lower() in c.lower() for k in keys) for c in cat_list):
            return label
    return None

df["main_category"] = df["categories_raw"].apply(label_category)

# --- Интерфейс ---
st.title("Фильтр по базе AstroDatabank")

col1, col2, col3 = st.columns(3)
with col1:
    rodden_opt = st.selectbox("Рейтинг Роддена", sorted(df["rodden"].dropna().unique()))
    sun_sign_opt = st.selectbox("Знак Солнца", sorted(df["sun_sign"].dropna().unique()))
    sun_deg_opt = st.slider("Градус Солнца", 0, 29, 0)
with col2:
    moon_sign_opt = st.selectbox("Знак Луны", sorted(df["moon_sign"].dropna().unique()))
    moon_deg_opt = st.slider("Градус Луны", 0, 29, 0)
    category_opt = st.selectbox("Категория", ["спортсмен", "актёр", "писатель"])
with col3:
    asc_sign_opt = st.selectbox("Знак Асцендента", sorted(df["asc_sign"].dropna().unique()))
    asc_deg_opt = st.slider("Градус Асцендента", 0, 29, 0)

# --- Фильтрация ---
filtered = df[
    (df["rodden"] == rodden_opt) &
    (df["sun_sign"] == sun_sign_opt) & (df["sun_deg"] == sun_deg_opt) &
    (df["moon_sign"] == moon_sign_opt) & (df["moon_deg"] == moon_deg_opt) &
    (df["asc_sign"] == asc_sign_opt) & (df["asc_deg"] == asc_deg_opt) &
    (df["main_category"] == category_opt)
]

# --- Результат ---
st.subheader("Результаты фильтрации")
st.dataframe(filtered[["adb_id", "rodden", "sun_sign", "sun_deg", "moon_sign", "moon_deg", "asc_sign", "asc_deg", "main_category"]])
