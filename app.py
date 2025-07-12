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

def translate_sign(sign):
    if not sign:
        return ""
    if "/" in sign:
        parts = sign.split("/")
        return "/".join([sign_translate.get(p, p) for p in parts])
    return sign_translate.get(sign, sign)

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
    name = public_data.findtext("name")
    birth_dt = public_data.findtext("birth_dt")
    sun_sign = positions.get("sun_sign") if positions is not None else None
    sun_deg = extract_degree(positions.get("sun_degmin")) if positions is not None else None
    moon_sign = positions.get("moon_sign") if positions is not None else None
    moon_deg = extract_degree(positions.get("moon_degmin")) if positions is not None else None
    asc_sign = positions.get("asc_sign") if positions is not None else None
    asc_deg = extract_degree(positions.get("asc_degmin")) if positions is not None else None

    research_data = entry.find("research_data")
    raw_categories = []
    if research_data is not None:
        cats = research_data.find("categories")
        if cats is not None:
            for cat in cats.findall("category"):
                if cat.text:
                    raw_categories.append(cat.text.strip())

    entries.append({
        "name": name,
        "birth_dt": birth_dt,
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

df = pd.DataFrame(entries)

def label_category(cat_list):
    if not cat_list:
        return None
    for label, keys in categories_map.items():
        if any(any(k.lower() in c.lower() for k in keys) for c in cat_list):
            return label
    return None

df["main_category"] = df["categories_raw"].apply(label_category)

st.title("Фильтр по базе AstroDatabank")

sign_options = ['Любой'] + sorted(df["sun_sign"].dropna().unique())
sign_display = {'Любой': 'Любой'}
sign_display.update({k: translate_sign(k) for k in df["sun_sign"].dropna().unique()})

col1, col2, col3 = st.columns(3)
with col1:
    rodden_opt = st.selectbox("Рейтинг Роддена", ['Любой'] + sorted(df["rodden"].dropna().unique()))
    sun_sign_opt = st.selectbox("Знак Солнца", options=sign_options, format_func=lambda x: sign_display.get(x, x))
    sun_deg_opt = st.slider("Градусы Солнца", 0, 29, (0, 29))
with col2:
    moon_sign_opt = st.selectbox("Знак Луны", options=sign_options, format_func=lambda x: sign_display.get(x, x))
    moon_deg_opt = st.slider("Градусы Луны", 0, 29, (0, 29))
    category_opt = st.selectbox("Категория", ['Любой', 'спортсмен', 'актёр', 'писатель'])
with col3:
    asc_sign_opt = st.selectbox("Знак Асцендента", options=sign_options, format_func=lambda x: sign_display.get(x, x))
    asc_deg_opt = st.slider("Градусы Асцендента", 0, 29, (0, 29))

filtered = df.copy()
if rodden_opt != 'Любой':
    filtered = filtered[filtered["rodden"] == rodden_opt]
if sun_sign_opt != 'Любой':
    filtered = filtered[(filtered["sun_sign"] == sun_sign_opt) &
                        (filtered["sun_deg"] >= sun_deg_opt[0]) & (filtered["sun_deg"] <= sun_deg_opt[1])]
if moon_sign_opt != 'Любой':
    filtered = filtered[(filtered["moon_sign"] == moon_sign_opt) &
                        (filtered["moon_deg"] >= moon_deg_opt[0]) & (filtered["moon_deg"] <= moon_deg_opt[1])]
if asc_sign_opt != 'Любой':
    filtered = filtered[(filtered["asc_sign"] == asc_sign_opt) &
                        (filtered["asc_deg"] >= asc_deg_opt[0]) & (filtered["asc_deg"] <= asc_deg_opt[1])]
if category_opt != 'Любой':
    filtered = filtered[filtered["main_category"] == category_opt]

st.subheader(f"Результаты фильтрации: найдено {len(filtered)} записей")

# Перевод знаков перед отображением:
filtered_disp = filtered.copy()
for col in ["sun_sign", "moon_sign", "asc_sign"]:
    filtered_disp[col] = filtered_disp[col].apply(translate_sign)

filtered_disp = filtered_disp.rename(columns={
    "name": "Имя",
    "birth_dt": "Дата рождения",
    "rodden": "Рейтинг Роддена",
    "sun_sign": "Знак Солнца",
    "sun_deg": "Градус Солнца",
    "moon_sign": "Знак Луны",
    "moon_deg": "Градус Луны",
    "asc_sign": "Знак Асцендента",
    "asc_deg": "Градус Асцендента",
    "main_category": "Категория"
})

st.dataframe(filtered_disp[["Имя", "Дата рождения", "Рейтинг Роддена", "Знак Солнца", "Градус Солнца",
                            "Знак Луны", "Градус Луны", "Знак Асцендента", "Градус Асцендента", "Категория"]])
