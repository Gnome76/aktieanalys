import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

# --- Databas setup ---

conn = sqlite3.connect("aktier.db", check_same_thread=False)
c = conn.cursor()

# Skapa tabell om den inte finns
c.execute('''
CREATE TABLE IF NOT EXISTS bolag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bolag TEXT UNIQUE,
    nuvarande_kurs REAL,
    pe1 REAL, pe2 REAL, pe3 REAL, pe4 REAL,
    ps1 REAL, ps2 REAL, ps3 REAL, ps4 REAL,
    vinst_ar REAL,
    vinst_nasta_ar REAL,
    oms_i_ar REAL,
    oms_nasta_ar REAL
)
''')
conn.commit()

# --- Funktioner ---

def hamta_data():
    df = pd.read_sql_query("SELECT * FROM bolag ORDER BY bolag COLLATE NOCASE ASC", conn)
    return df

def lagg_till_bolag(bolag, kurs, pe, ps, vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar):
    try:
        c.execute('''
        INSERT INTO bolag (bolag, nuvarande_kurs, pe1, pe2, pe3, pe4,
                          ps1, ps2, ps3, ps4,
                          vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (bolag, kurs, *pe, *ps, vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar))
        conn.commit()
        return True, f"✅ {bolag} tillagd!"
    except sqlite3.IntegrityError:
        return False, "⚠️ Bolaget finns redan!"

def radera_bolag(bolag):
    c.execute("DELETE FROM bolag WHERE bolag = ?", (bolag,))
    conn.commit()

def beräkna_target(df):
    df = df.copy()
    df['PE snitt'] = df[['pe1', 'pe2', 'pe3', 'pe4']].mean(axis=1)
    df['PS snitt'] = df[['ps1', 'ps2', 'ps3', 'ps4']].mean(axis=1)
    df['Vinst snitt'] = df[['vinst_ar', 'vinst_nasta_ar']].mean(axis=1)
    df['Oms snitt'] = df[['oms_i_ar', 'oms_nasta_ar']].mean(axis=1)

    df['Target P/E'] = df['PE snitt'] * df['Vinst snitt']
    df['Target P/S'] = df['PS snitt'] * df['Oms snitt']
    df['Target genomsnitt'] = (df['Target P/E'] + df['Target P/S']) / 2

    df['Undervärdering %'] = ((df['Target genomsnitt'] - df['nuvarande_kurs']) / df['nuvarande_kurs']) * 100
    return df

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Bolag')
    writer.save()
    processed_data = output.getvalue()
    return processed_data

# --- Streamlit UI ---

st.set_page_config(page_title="Aktieanalys med DB", page_icon="📈", layout="centered")
st.title("📈 Aktieanalys med Databas")

# 1. Lägg till nytt bolag
with st.expander("➕ Lägg till nytt bolag"):
    with st.form("add_company_form"):
        bolag = st.text_input("Bolagsnamn")
        kurs = st.number_input("Nuvarande kurs", min_value=0.0)

        pe = [st.number_input(f"P/E {i+1}", min_value=0.0, key=f"pe{i}") for i in range(4)]
        ps = [st.number_input(f"P/S {i+1}", min_value=0.0, key=f"ps{i}") for i in range(4)]

        vinst_i_ar = st.number_input("Vinstprognos i år", min_value=0.0)
        vinst_nasta_ar = st.number_input("Vinstprognos nästa år", min_value=0.0)
        oms_i_ar = st.number_input("Omsättningstillväxt i år", min_value=0.0)
        oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år", min_value=0.0)

        submitted = st.form_submit_button("💾 Spara bolag")
        if submitted:
            if bolag.strip() == "":
                st.warning("Skriv in ett bolagsnamn!")
            else:
                ok, msg = lagg_till_bolag(bolag.strip().capitalize(), kurs, pe, ps, vinst_i_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

# 2. Hämta och visa data med beräkningar
df = hamta_data()
if df.empty:
    st.info("Inga bolag tillagda ännu.")
else:
    df_calc = beräkna_target(df)

    # 3. Sök/filter på bolagsnamn
    sök = st.text_input("🔍 Filtrera bolag (sök på namn)").lower()
    if sök:
        df_calc = df_calc[df_calc['bolag'].str.lower().str.contains(sök)]

    # 4. Lista med möjlighet att ta bort bolag
    st.subheader("📋 Bolag och värdering")
    for _, row in df_calc.iterrows():
        undervärdering = row['Undervärdering %']
        if undervärdering >= 30:
            färg = "🟢"
        elif undervärdering > 0:
            färg = "⚪️"
        else:
            färg = "🔴"

        st.markdown(f"""
        <div style="border:1px solid #ccc; border-radius:8px; padding:12px; margin-bottom:10px;">
        <h3 style="margin-bottom:5px;">{row['bolag']} {färg}</h3>
        <p><b>Nuvarande kurs:</b> {row['nuvarande_kurs']:.2f} kr</p>
        <p>🧮 <b>Target baserat på P/E:</b> {row['Target P/E']:.2f} kr</p>
        <p>🧮 <b>Target baserat på P/S:</b> {row['Target P/S']:.2f} kr</p>
        <p>🟨 <b>Genomsnittlig targetkurs (P/E + P/S / 2):</b> <strong>{row['Target genomsnitt']:.2f} kr</strong></p>
        <p>📉 <b>Undervärdering:</b> {undervärdering:.1f} %</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"🗑️ Ta bort {row['bolag']}", key=f"del_{row['bolag']}"):
            radera_bolag(row['bolag'])
            st.experimental_rerun()

    # 5. Visa undervärderade bolag (≥ 30%)
    undervarderade = df_calc[df_calc['Undervärdering %'] >= 30].sort_values('Undervärdering %', ascending=False)
    if not undervarderade.empty:
        st.subheader("🟢 Mest undervärderade bolag (≥ 30%)")
        for _, row in undervarderade.iterrows():
            st.markdown(f"**{row['bolag']}** – {row['Undervärdering %']:.1f}% undervärderad, mål: {row['Target genomsnitt']:.2f} kr")

    else:
        st.info("Inga bolag är just nu undervärderade med ≥ 30%.")

    # 6. Exportfunktion
    st.subheader("📤 Exportera data")
    export_format = st.selectbox("Välj exportformat", options=["Excel (.xlsx)", "CSV (.csv)"])
    if st.button("Exportera"):
        if export_format == "Excel (.xlsx)":
            data = to_excel(df_calc)
            st.download_button(label="Ladda ner Excel-fil", data=data, file_name="aktieanalys.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            csv = df_calc.to_csv(index=False).encode('utf-8')
            st.download_button(label="Ladda ner CSV-fil", data=csv, file_name="aktieanalys.csv", mime="text/csv")
