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

    # Новый способ извлечения даты и времени рождения
    date_str = bdata.findtext("date") if bdata is not None else None
    time_str = bdata.findtext("time") if bdata is not None else None
    if date_str and time_str:
        birth_dt = f"{date_str} {time_str}"
    elif date_str:
        birth_dt = date_str
    else:
        birth_dt = None

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

...
