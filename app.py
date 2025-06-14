import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "bolag.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bolag (
            namn TEXT PRIMARY KEY,
            nuvarande_kurs REAL,
            pe1 REAL,
            pe2 REAL,
            pe3 REAL,
            pe4 REAL,
            ps1 REAL,
            ps2 REAL,
            ps3 REAL,
            ps4 REAL,
            vinst_arsprognos REAL,
            vinst_nastaar REAL,
            omsattningstillvaxt_arsprognos REAL,
            omsattningstillvaxt_nastaar REAL,
            insatt_datum TEXT
        )
    """)
    conn.commit()
    conn.close()

def spara_bolag(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

def hamta_alla_bolag():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM bolag")
    rows = c.fetchall()
    conn.close()
    return rows

def ta_bort_bolag(namn):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn = ?", (namn,))
    conn.commit()
    conn.close()

def berakna_targetkurs_pe(row):
    pe_values = [row['pe1'], row['pe2'], row['pe3'], row['pe4']]
    pe_values = [v for v in pe_values if v and v > 0]
    if not pe_values:
        return None
    pe_genomsnitt = sum(pe_values) / len(pe_values)
    return pe_genomsnitt * row['vinst_nastaar']

def berakna_targetkurs_ps(row):
    ps_values = [row['ps1'], row['ps2'], row['ps3'], row['ps4']]
    ps_values = [v for v in ps_values if v and v > 0]
    if not ps_values:
        return None
    ps_genomsnitt = sum(ps_values) / len(ps_values)
    return ps_genomsnitt * row['vinst_nastaar']

def las_in_data():
    bolag_lista = hamta_alla_bolag()
    if not bolag_lista:
        return pd.DataFrame()
    df = pd.DataFrame(
        bolag_lista,
        columns=[
            "namn", "nuvarande_kurs",
            "pe1", "pe2", "pe3", "pe4",
            "ps1", "ps2", "ps3", "ps4",
            "vinst_arsprognos", "vinst_nastaar",
            "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
            "insatt_datum"
        ]
    )
    num_cols = ["nuvarande_kurs", "pe1", "pe2", "pe3", "pe4", "ps1", "ps2", "ps3", "ps4",
                "vinst_arsprognos", "vinst_nastaar", "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar"]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df['target_pe'] = df.apply(berakna_targetkurs_pe, axis=1)
    df['target_ps'] = df.apply(berakna_targetkurs_ps, axis=1)

    df['undervarde_pe'] = ((df['target_pe'] - df['nuvarande_kurs']) / df['target_pe']) * 100
    df['undervarde_ps'] = ((df['target_ps'] - df['nuvarande_kurs']) / df['target_ps']) * 100

    df['undervarde_pe'] = df['undervarde_pe'].fillna(0)
    df['undervarde_ps'] = df['undervarde_ps'].fillna(0)

    df['min_target'] = df[['target_pe', 'target_ps']].min(axis=1)
    df['undervarde_min'] = ((df['min_target'] - df['nuvarande_kurs']) / df['min_target']) * 100
    df['undervarde_min'] = df['undervarde_min'].fillna(0)

    return df

def main():
    st.title("Aktieanalys med undervärdering (P/E och P/S) och bläddring")

    init_db()

    if 'reload_trigger' not in st.session_state:
        st.session_state.reload_trigger = 0
    if 'index_undervarde' not in st.session_state:
        st.session_state.index_undervarde = 0

    df = las_in_data()
    df_undervarde = df[df['undervarde_min'] > 0].copy().sort_values(by='undervarde_min', ascending=False)

    st.header("Lägg till eller redigera bolag")

    val_av_bolag = st.selectbox(
        "Välj bolag att redigera (eller tomt för nytt):",
        options=[""] + (df["namn"].tolist() if not df.empty else [])
    )

    if val_av_bolag:
        vald_rad = df[df["namn"] == val_av_bolag].iloc[0]
        namn = val_av_bolag
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, value=float(vald_rad["nuvarande_kurs"]), format="%.2f", key="edit_kurs")
        pe1 = st.number_input("P/E (år 1)", min_value=0.0, value=float(vald_rad["pe1"]), format="%.2f", key="edit_pe1")
        pe2 = st.number_input("P/E (år 2)", min_value=0.0, value=float(vald_rad["pe2"]), format="%.2f", key="edit_pe2")
        pe3 = st.number_input("P/E (år 3)", min_value=0.0, value=float(vald_rad["pe3"]), format="%.2f", key="edit_pe3")
        pe4 = st.number_input("P/E (år 4)", min_value=0.0, value=float(vald_rad["pe4"]), format="%.2f", key="edit_pe4")
        ps1 = st.number_input("P/S (år 1)", min_value=0.0, value=float(vald_rad["ps1"]), format="%.2f", key="edit_ps1")
        ps2 = st.number_input("P/S (år 2)", min_value=0.0, value=float(vald_rad["ps2"]), format="%.2f", key="edit_ps2")
        ps3 = st.number_input("P/S (år 3)", min_value=0.0, value=float(vald_rad["ps3"]), format="%.2f", key="edit_ps3")
        ps4 = st.number_input("P/S (år 4)", min_value=0.0, value=float(vald_rad["ps4"]), format="%.2f", key="edit_ps4")
        vinst_arsprognos = st.number_input("Vinst prognos i år", value=float(vald_rad["vinst_arsprognos"]), format="%.2f", key="edit_vinst_i_ar")
        vinst_nastaar = st.number_input("Vinst prognos nästa år", value=float(vald_rad["vinst_nastaar"]), format="%.2f", key="edit_vinst_nasta_ar")
        omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt i år (%)", value=float(vald_rad["omsattningstillvaxt_arsprognos"]), format="%.2f", key="edit_omsatt_i_ar")
        omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)", value=float(vald_rad["omsattningstillvaxt_nastaar"]), format="%.2f", key="edit_omsatt_nasta_ar")

        if st.button("Spara ändringar"):
            data = (
                namn,
                nuvarande_kurs,
                pe1, pe2, pe3, pe4,
                ps1, ps2, ps3, ps4,
                vinst_arsprognos,
                vinst_nastaar,
                omsattningstillvaxt_arsprognos,
                omsattningstillvaxt_nastaar,
                datetime.now().isoformat()
            )
            spara_bolag(data)
            st.success(f"Bolag '{namn}' uppdaterat!")
            st.session_state.reload_trigger += 1

    else:
        with st.form("form_lagg_till_bolag", clear_on_submit=True):
            namn = st.text_input("Bolagsnamn (unik)")
            nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")
            pe1 = st.number_input("P/E (år 1)", min_value=0.0, format="%.2f")
            pe2 = st.number_input("P/E (år 2)", min_value=0.0, format="%.2f")
            pe3 = st.number_input("P/E (år 3)", min_value=0.0, format="%.2f")
            pe4 = st.number_input("P/E (år 4)", min_value=0.0, format="%.2f")
            ps1 = st.number_input("P/S (år 1)", min_value=0.0, format="%.2f")
            ps2 = st.number_input("P/S (år 2)", min_value=0.0, format="%.2f")
            ps3 = st.number_input("P/S (år 3)", min_value=0.0, format="%.2f")
            ps4 = st.number_input("P/S (år 4)", min_value=0.0, format="%.2f")
            vinst_arsprognos = st.number_input("Vinst prognos i år", format="%.2f")
            vinst_nastaar = st.number_input("Vinst prognos nästa år", format="%.2f")
            omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt i år (%)", format="%.2f")
            omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)", format="%.2f")

            lagg_till = st.form_submit_button("Lägg till bolag")

            if lagg_till:
                if namn.strip() == "":
                    st.error("Bolagsnamn måste anges.")
                else:
                    data = (
                        namn.strip(),
                        nuvarande_kurs,
                        pe1, pe2, pe3, pe4,
                        ps1, ps2, ps3, ps4,
                        vinst_arsprognos,
                        vinst_nastaar,
                        omsattningstillvaxt_arsprognos,
                        omsattningstillvaxt_nastaar,
                        datetime.now().isoformat()
                    )
                    spara_bolag(data)
                    st.success(f"Bolag '{namn}' sparat!")
                    st.session_state.reload_trigger += 1

    if st.session_state.reload_trigger > 0:
        df = las_in_data()
        df_undervarde = df[df['undervarde_min'] > 0].copy().sort_values(by='undervarde_min', ascending=False)
        st.session_state.reload_trigger = 0

    st.header("Undervärderade bolag (mer än 0%) - bläddra")

    if df_undervarde.empty:
        st.info("Inga undervärderade bolag att visa.")
        return

    idx = st.session_state.index_undervarde
    bolag = df_undervarde.iloc[idx]

    st.subheader(f"{bolag['namn']}")
    st.write(f"Nuvarande kurs: {bolag['nuvarande_kurs']:.2f} kr")
    st.write(f"Target P/E: {bolag['target_pe']:.2f} kr")
    st.write(f"Target P/S: {bolag['target_ps']:.2f} kr")
    st.write(f"Undervärdering (min): {bolag['undervarde_min']:.1f} %")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Föregående"):
            if st.session_state.index_undervarde > 0:
                st.session_state.index_undervarde -= 1
    with col2:
        st.write(f"{idx + 1} / {len(df_undervarde)}")
    with col3:
        if st.button("Nästa"):
            if st.session_state.index_undervarde < len(df_undervarde) - 1:
                st.session_state.index_undervarde += 1

    st.header("Ta bort bolag")
    namn_ta_bort = st.selectbox("Välj bolag att ta bort", options=[""] + df["namn"].tolist() if not df.empty else [])
    if namn_ta_bort:
        if st.button("Ta bort valt bolag"):
            ta_bort_bolag(namn_ta_bort)
            st.success(f"Bolag '{namn_ta_bort}' borttaget.")
            st.session_state.reload_trigger += 1

if __name__ == "__main__":
    main()
