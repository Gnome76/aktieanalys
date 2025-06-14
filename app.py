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
    # Vi saknar omsättning i data, men antar omsättning kan approx vinst_nastaar / vinstmarginal
    # Då vi inte har omsättning, vi använder vinst_nastaar som proxy, eller sätt ps_genomsnitt * (vinst_nastaar) som target?
    # Det är en förenkling. Annars behövs omsättning i databas.
    # Här använder vi vinst_nastaar * ps_genomsnitt som approximation.
    return ps_genomsnitt * row['vinst_nastaar']  

def main():
    st.title("Aktieanalys med undervärdering (P/E och P/S) och bläddring")

    init_db()

    # Läs in bolag
    bolag_lista = hamta_alla_bolag()
    if not bolag_lista:
        df = pd.DataFrame()
    else:
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

        # Konvertera numeriska kolumner till float
        for col in ["nuvarande_kurs", "pe1", "pe2", "pe3", "pe4", "ps1", "ps2", "ps3", "ps4",
                    "vinst_arsprognos", "vinst_nastaar",
                    "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Beräkna targetkurser
        df['target_pe'] = df.apply(berakna_targetkurs_pe, axis=1)
        df['target_ps'] = df.apply(berakna_targetkurs_ps, axis=1)

        # Beräkna undervärdering % (positiv betyder undervärderad)
        df['undervarde_pe'] = ((df['target_pe'] - df['nuvarande_kurs']) / df['target_pe']) * 100
        df['undervarde_ps'] = ((df['target_ps'] - df['nuvarande_kurs']) / df['target_ps']) * 100

        # Sätt undervärdering till 0 där target saknas för att undvika NaN
        df['undervarde_pe'] = df['undervarde_pe'].fillna(0)
        df['undervarde_ps'] = df['undervarde_ps'].fillna(0)

        # Välj mest konservativa (lägsta targetkurs) och undervärdering från den
        df['min_target'] = df[['target_pe', 'target_ps']].min(axis=1)
        df['undervarde_min'] = ((df['min_target'] - df['nuvarande_kurs']) / df['min_target']) * 100
        df['undervarde_min'] = df['undervarde_min'].fillna(0)

        # Filtrera undervärderade bolag (mer än 0%)
        df_undervarde = df[df['undervarde_min'] > 0].copy()

        # Sortera från mest undervärderad till minst
        df_undervarde.sort_values(by='undervarde_min', ascending=False, inplace=True)

    st.header("Lägg till eller redigera bolag")

    # --- Redigera / Lägg till bolag ---
    val_av_bolag = st.selectbox(
        "Välj bolag att redigera (eller tomt för nytt):",
        options=[""] + (df["namn"].tolist() if not df.empty else [])
    )

    if val_av_bolag:
        vald_rad = df[df["namn"] == val_av_bolag].iloc[0]
        namn = val_av_bolag
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, value=float(vald_rad["nuvarande_kurs"]), format="%.2f")
        pe1 = st.number_input("P/E (år 1)", min_value=0.0, value=float(vald_rad["pe1"]), format="%.2f")
        pe2 = st.number_input("P/E (år 2)", min_value=0.0, value=float(vald_rad["pe2"]), format="%.2f")
        pe3 = st.number_input("P/E (år 3)", min_value=0.0, value=float(vald_rad["pe3"]), format="%.2f")
        pe4 = st.number_input("P/E (år 4)", min_value=0.0, value=float(vald_rad["pe4"]), format="%.2f")
        ps1 = st.number_input("P/S (år 1)", min_value=0.0, value=float(vald_rad["ps1"]), format="%.2f")
        ps2 = st.number_input("P/S (år 2)", min_value=0.0, value=float(vald_rad["ps2"]), format="%.2f")
        ps3 = st.number_input("P/S (år 3)", min_value=0.0, value=float(vald_rad["ps3"]), format="%.2f")
        ps4 = st.number_input("P/S (år 4)", min_value=0.0, value=float(vald_rad["ps4"]), format="%.2f")
        vinst_arsprognos = st.number_input("Vinst prognos i år", value=float(vald_rad["vinst_arsprognos"]), format="%.2f")
        vinst_nastaar = st.number_input("Vinst prognos nästa år", value=float(vald_rad["vinst_nastaar"]), format="%.2f")
        omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt i år (%)", value=float(vald_rad["omsattningstillvaxt_arsprognos"]), format="%.2f")
        omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)", value=float(vald_rad["omsattningstillvaxt_nastaar"]), format="%.2f")

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
            st.experimental_rerun()

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
                    st.experimental_rerun()

    # Bläddra bland undervärderade bolag
    st.header("Undervärderade bolag (mer än 0%) - bläddra")

    if df.empty or df_undervarde.empty:
        st.info("Inga bolag sparade eller inga undervärderade bolag just nu.")
        return

    if 'index_undervarde' not in st.session_state:
        st.session_state['index_undervarde'] = 0

    col1, col2, col3 = st.columns([1,2,1])

    with col1:
        if st.button("Föregående"):
            st.session_state['index_undervarde'] = max(0, st.session_state['index_undervarde'] - 1)

    with col2:
        idx = st.session_state['index_undervarde']
        row = df_undervarde.iloc[idx]
        st.markdown(f"### {row['namn']}")
        st.write(f"**Nuvarande kurs:** {row['nuvarande_kurs']:.2f} kr")
        st.write(f"**Targetkurs P/E:** {row['target_pe']:.2f} kr")
        st.write(f"**Undervärdering P/E:** {row['undervarde_pe']:.2f} %")
        st.write(f"**Targetkurs P/S:** {row['target_ps']:.2f} kr")
        st.write(f"**Undervärdering P/S:** {row['undervarde_ps']:.2f} %")
        st.write(f"**Konservativ mål (lägst target):** {row['min_target']:.2f} kr")
        st.write(f"**Undervärdering konservativ:** {row['undervarde_min']:.2f} %")

    with col3:
        if st.button("Nästa"):
            st.session_state['index_undervarde'] = min(len(df_undervarde) - 1, st.session_state['index_undervarde'] + 1)

    # Ta bort bolag
    st.header("Ta bort bolag")
    namn_att_ta_bort = st.selectbox("Välj bolag att ta bort", options=[""] + (df["namn"].tolist() if not df.empty else []))
    if namn_att_ta_bort != "":
        if st.button(f"Ta bort '{namn_att_ta_bort}'"):
            ta_bort_bolag(namn_att_ta_bort)
            st.success(f"Bolag '{namn_att_ta_bort}' borttaget!")
            st.experimental_rerun()

if __name__ == "__main__":
    main()
