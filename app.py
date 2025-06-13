import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO

# --- Databas setup ---

conn = sqlite3.connect("aktier.db", check_same_thread=False)
c = conn.cursor()

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

def uppdatera_bolag(bolag_id, bolag, kurs, pe, ps, vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar):
    c.execute('''
    UPDATE bolag SET
        bolag = ?,
        nuvarande_kurs = ?,
        pe1 = ?, pe2 = ?, pe3 = ?, pe4 = ?,
        ps1 = ?, ps2 = ?, ps3 = ?, ps4 = ?,
        vinst_ar = ?,
        vinst_nasta_ar = ?,
        oms_i_ar = ?,
        oms_nasta_ar = ?
    WHERE id = ?
    ''', (bolag, kurs, *pe, *ps, vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar, bolag_id))
    conn.commit()

def safe_float(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0

def berakna_target(df):
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

# --- Streamlit UI ---

st.set_page_config(page_title="Aktieanalys med DB", page_icon="📈", layout="centered")
st.title("📈 Aktieanalys med Databas")

# Lägg till nytt bolag
with st.expander("➕ Lägg till nytt bolag"):
    with st.form("add_form", clear_on_submit=True):
        bolag = st.text_input("Bolagsnamn")
        kurs = st.number_input("Nuvarande kurs", min_value=0.0)

        pe = [st.number_input(f"P/E {i+1}", min_value=0.0) for i in range(4)]
        ps = [st.number_input(f"P/S {i+1}", min_value=0.0) for i in range(4)]

        vinst_i_ar = st.number_input("Vinstprognos i år", min_value=0.0)
        vinst_nasta_ar = st.number_input("Vinstprognos nästa år", min_value=0.0)
        oms_i_ar = st.number_input("Omsättningstillväxt i år", min_value=0.0)
        oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år", min_value=0.0)

        submit = st.form_submit_button("💾 Spara bolag")

        if submit:
            if bolag.strip() == "":
                st.warning("Ange ett bolagsnamn!")
            else:
                ok, msg = lagg_till_bolag(bolag.strip().capitalize(), kurs, pe, ps, vinst_i_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

# Hämta data
df = hamta_data()

# Redigera bolag
st.subheader("✏️ Redigera sparade bolag")

if not df.empty:
    val = st.selectbox("Välj bolag att redigera", df['bolag'].tolist())

    if val:
        bolag_data = df[df['bolag'] == val].iloc[0]

        with st.form("edit_form"):
            bolag_id = bolag_data['id']
            bolag = st.text_input("Bolagsnamn", value=bolag_data['bolag'], key="edit_bolag")
            kurs = st.number_input("Nuvarande kurs", min_value=0.0, value=safe_float(bolag_data['nuvarande_kurs']), key="edit_kurs")

            pe = [
                st.number_input(f"P/E {i+1}", min_value=0.0, value=safe_float(bolag_data[f'pe{i+1}']), key=f"edit_pe{i}_input")
                for i in range(4)
            ]
            ps = [
                st.number_input(f"P/S {i+1}", min_value=0.0, value=safe_float(bolag_data[f'ps{i+1}']), key=f"edit_ps{i}_input")
                for i in range(4)
            ]

            vinst_i_ar = st.number_input("Vinstprognos i år", min_value=0.0, value=safe_float(bolag_data['vinst_ar']), key="edit_vinst_ar")
            vinst_nasta_ar = st.number_input("Vinstprognos nästa år", min_value=0.0, value=safe_float(bolag_data['vinst_nasta_ar']), key="edit_vinst_nasta_ar")
            oms_i_ar = st.number_input("Omsättningstillväxt i år", min_value=0.0, value=safe_float(bolag_data['oms_i_ar']), key="edit_oms_i_ar")
            oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år", min_value=0.0, value=safe_float(bolag_data['oms_nasta_ar']), key="edit_oms_nasta_ar")

            uppdatera = st.form_submit_button("💾 Uppdatera bolag")

            if uppdatera:
                uppdatera_bolag(bolag_id, bolag.strip().capitalize(), kurs, pe, ps, vinst_i_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar)
                st.success(f"✅ {bolag} uppdaterat!")
                st.experimental_rerun()
else:
    st.info("Inga bolag att visa/redigera ännu.")

# Visa alla bolag med beräkningar och filter

if not df.empty:
    df_calc = berakna_target(df)

    sök = st.text_input("🔍 Filtrera bolag (sök på namn)").lower()
    if sök:
        df_calc = df_calc[df_calc['bolag'].str.lower().str.contains(sök)]

    # Filtrera undervärderade minst 30%
    undervärderade = df_calc[df_calc['Undervärdering %'] >= 30].sort_values(by='Undervärdering %', ascending=False)

    st.subheader("📋 Bolag och värdering")

    if not undervärderade.empty:
        st.markdown("### Undervärderade bolag (minst 30%)")
        for _, row in undervärderade.iterrows():
            st.markdown(f"""
            <div style="border:1px solid #aaa; border-radius:10px; padding:10px; margin-bottom:10px;">
            <b>{row['bolag']}</b><br>
            Nuvarande kurs: {row['nuvarande_kurs']:.2f} SEK<br>
            Target kurs P/E: {row['Target P/E']:.2f} SEK<br>
            Target kurs P/S: {row['Target P/S']:.2f} SEK<br>
            <b>Target kurs genomsnitt: {row['Target genomsnitt']:.2f} SEK</b><br>
            Undervärdering: {row['Undervärdering %']:.2f} %
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Inga bolag är undervärderade med minst 30%.")

    st.markdown("---")
    st.markdown("### Alla bolag:")

    for _, row in df_calc.iterrows():
        st.markdown(f"""
        <div style="border:1px solid #ddd; border-radius:8px; padding:8px; margin-bottom:8px;">
        <b>{row['bolag']}</b> - Kurs: {row['nuvarande_kurs']:.2f} SEK - 
        Target P/E: {row['Target P/E']:.2f} SEK, Target P/S: {row['Target P/S']:.2f} SEK, 
        Genomsnitt Target: {row['Target genomsnitt']:.2f} SEK, 
        Undervärdering: {row['Undervärdering %']:.2f} %
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Inga bolag att visa.")
