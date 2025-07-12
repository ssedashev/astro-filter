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
biography_tree = {}

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
    place = bdata.findtext("place") if bdata is not None else None
    if date_str and time_str:
        birth_dt = f"{date_str}, {time_str}"
    elif date_str:
        birth_dt = date_str
    else:
        birth_dt = ""

    birth_place = place or ""

    sun_sign_raw = positions.get("sun_sign") if positions is not None else None
    sun_sign = translate_sign(sun_sign_raw)
    moon_sign_raw = positions.get("moon_sign") if positions is not None else None
    moon_sign = translate_sign(moon_sign_raw)
    asc_sign_raw = positions.get("asc_sign") if positions is not None else None
    asc_sign = translate_sign(asc_sign_raw)

    research_data = entry.find("research_data")
    raw_categories = []
    tree_path = []
    if research_data is not None:
        cats = research_data.find("categories")
        if cats is not None:
            for cat in cats.findall("category"):
                if cat.text:
                    parts = cat.text.strip().split(" > ")
                    tree_path.append(parts)
                    raw_categories.append(cat.text.strip())

    category_label = raw_categories[0] if raw_categories else "Без категории"
    category_translation[category_label] = category_translation.get(category_label, category_label)

    entries.append({
        "Имя": name,
        "Дата и место рождения": f"{birth_dt}, {birth_place}".strip(', '),
        "Рейтинг Роддена": rodden,
        "Знак Солнца": sun_sign,
        "Знак Луны": moon_sign,
        "Знак Асцендента": asc_sign,
        "Категории": tree_path,
        "Описание": bio
    })

# Построение дерева категорий
import collections

def build_tree(paths):
    tree = collections.defaultdict(dict)
    for path in paths:
        current = tree
        for part in path:
            current = current.setdefault(part, {})
    return tree

df = pd.DataFrame(entries)
biography_tree = build_tree([cat for entry in entries for cat in entry["Категории"]])

st.title("Фильтр по базе AstroDatabank")

col1, col2, col3 = st.columns(3)
with col1:
    selected_rodden = st.selectbox("Рейтинг Роддена", options=["Любой"] + sorted(df["Рейтинг Роддена"].dropna().unique().tolist()), index=(sorted(df["Рейтинг Роддена"].dropna().unique().tolist()).index("AA") + 1 if "AA" in df["Рейтинг Роддена"].values else 0))
    selected_sun_sign = st.selectbox("Знак Солнца", options=sign_options)
with col2:
    selected_moon_sign = st.selectbox("Знак Луны", options=sign_options)
with col3:
    selected_asc_sign = st.selectbox("Знак Асцендента", options=sign_options)

# Триуровневый фильтр биографии
bio1 = st.selectbox("Биография: Уровень 1", ["Любой"] + sorted(biography_tree.keys()))
bio2 = st.selectbox("Биография: Уровень 2", ["Любой"] + (sorted(biography_tree.get(bio1, {}).keys()) if bio1 != "Любой" else []))
bio3 = st.selectbox("Биография: Уровень 3", ["Любой"] + (sorted(biography_tree.get(bio1, {}).get(bio2, {}).keys()) if bio2 != "Любой" else []))

# Фильтрация
filtered_df = df.copy()
if selected_rodden != "Любой":
    filtered_df = filtered_df[filtered_df["Рейтинг Роддена"] == selected_rodden]
if selected_sun_sign != "Любой":
    filtered_df = filtered_df[filtered_df["Знак Солнца"] == selected_sun_sign]
if selected_moon_sign != "Любой":
    filtered_df = filtered_df[filtered_df["Знак Луны"] == selected_moon_sign]
if selected_asc_sign != "Любой":
    filtered_df = filtered_df[filtered_df["Знак Асцендента"] == selected_asc_sign]

if bio1 != "Любой":
    filtered_df = filtered_df[filtered_df["Категории"].apply(lambda cats: any(cat[:1] == [bio1] for cat in cats))]
if bio2 != "Любой":
    filtered_df = filtered_df[filtered_df["Категории"].apply(lambda cats: any(cat[:2] == [bio1, bio2] for cat in cats))]
if bio3 != "Любой":
    filtered_df = filtered_df[filtered_df["Категории"].apply(lambda cats: any(cat[:3] == [bio1, bio2, bio3] for cat in cats))]

st.write(f"Найдено записей: {len(filtered_df)}")

left, right = st.columns([2, 3])

with left:
    selected_name = st.radio("Выберите человека:", filtered_df["Имя"].tolist())

with right:
    person = filtered_df[filtered_df["Имя"] == selected_name].iloc[0]
    st.markdown(f"### {person['Имя']}")
    st.markdown(f"**Дата и место рождения:** {person['Дата и место рождения']}")
    st.markdown(f"**Знак Солнца:** {person['Знак Солнца']}")
    st.markdown(f"**Знак Луны:** {person['Знак Луны']}")
    st.markdown(f"**Знак Асцендента:** {person['Знак Асцендента']}")
    st.markdown(f"**Описание:**\n{person['Описание']}")
