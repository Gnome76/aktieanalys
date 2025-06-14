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
    c.execute("SELECT * FROM bolag ORDER BY namn COLLATE NOCASE ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def berakna_targetkurs(pe_vardena, ps_vardena, vinst_arsprognos, vinst_nastaar, nuvarande_kurs):
    genomsnitt_pe = sum(pe_vardena) / len(pe_vardena)
    genomsnitt_ps = sum(ps_vardena) / len(ps_vardena)

    target_pe_ars = genomsnitt_pe * vinst_arsprognos if vinst_arsprognos else None
    target_pe_nastaar = genomsnitt_pe * vinst_nastaar if vinst_nastaar else None
    target_ps_ars = genomsnitt_ps * vinst_arsprognos if vinst_arsprognos else None
    target_ps_nastaar = genomsnitt_ps * vinst_nastaar if vinst_nastaar else None

    target_genomsnitt_ars = None
    target_genomsnitt_nastaar = None
    if target_pe_ars and target_ps_ars:
        target_genomsnitt_ars = (target_pe_ars + target_ps_ars) / 2
    if target_pe_nastaar and target_ps_nastaar:
        target_genomsnitt_nastaar = (target_pe_nastaar + target_ps_nastaar) / 2

    undervardering_genomsnitt_ars = None
    undervardering_genomsnitt_nastaar = None

    if nuvarande_kurs and target_genomsnitt_ars:
        undervardering_genomsnitt_ars = (target_genomsnitt_ars / nuvarande_kurs) - 1
    if nuvarande_kurs and target_genomsnitt_nastaar:
        undervardering_genomsnitt_nastaar = (target_genomsnitt_nastaar / nuvarande_kurs) - 1

    kopvard_ars = target_genomsnitt_ars * 0.7 if target_genomsnitt_ars else None
    kopvard_nastaar = target_genomsnitt_nastaar * 0.7 if target_genomsnitt_nastaar else None

    return {
        "target_genomsnitt_ars": target_genomsnitt_ars,
        "target_genomsnitt_nastaar": target_genomsnitt_nastaar,
        "undervardering_genomsnitt_ars": undervardering_genomsnitt_ars,
        "undervardering_genomsnitt_nastaar": undervardering_genomsnitt_nastaar,
        "kopvard_ars": kopvard_ars,
        "kopvard_nastaar": kopvard_nastaar
    }

def main():
    st.title("Aktieinnehav – Spara och analysera")
    init_db()

    # Initiera session_state med tomma värden för att slippa 0.00 i input-fälten
    if "namn" not in st.session_state:
        st.session_state.namn = ""
    if "nuvarande_kurs" not in st.session_state:
        st.session_state.nuvarande_kurs = None
    for key in ["pe1","pe2","pe3","pe4","ps1","ps2","ps3","ps4",
                "vinst_arsprognos","vinst_nastaar","omsattningstillvaxt_arsprognos","omsattningstillvaxt_nastaar"]:
        if key not in st.session_state:
            st.session_state[key] = None

    with st.form("form_lagg_till_bolag", clear_on_submit=False):
        namn = st.text_input("Bolagsnamn (unik)", key="namn")
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f", key="nuvarande_kurs", value=st.session_state.nuvarande_kurs if st.session_state.nuvarande_kurs is not None else 0.0)
        pe1 = st.number_input("P/E (år 1)", min_value=0.0, format="%.2f", key="pe1", value=st.session_state.pe1 if st.session_state.pe1 is not None else 0.0)
        pe2 = st.number_input("P/E (år 2)", min_value=0.0, format="%.2f", key="pe2", value=st.session_state.pe2 if st.session_state.pe2 is not None else 0.0)
        pe3 = st.number_input("P/E (år 3)", min_value=0.0, format="%.2f", key="pe3", value=st.session_state.pe3 if st.session_state.pe3 is not None else 0.0)
        pe4 = st.number_input("P/E (år 4)", min_value=0.0, format="%.2f", key="pe4", value=st.session_state.pe4 if st.session_state.pe4 is not None else 0.0)
        ps1 = st.number_input("P/S (år 1)", min_value=0.0, format="%.2f", key="ps1", value=st.session_state.ps1 if st.session_state.ps1 is not None else 0.0)
        ps2 = st.number_input("P/S (år 2)", min_value=0.0, format="%.2f", key="ps2", value=st.session_state.ps2 if st.session_state.ps2 is not None else 0.0)
        ps3 = st.number_input("P/S (år 3)", min_value=0.0, format="%.2f", key="ps3", value=st.session_state.ps3 if st.session_state.ps3 is not None else 0.0)
        ps4 = st.number_input("P/S (år 4)", min_value=0.0, format="%.2f", key="ps4", value=st.session_state.ps4 if st.session_state.ps4 is not None else 0.0)
        vinst_arsprognos = st.number_input("Vinst prognos i år", format="%.2f", key="vinst_arsprognos", value=st.session_state.vinst_arsprognos if st.session_state.vinst_arsprognos is not None else 0.0)
        vinst_nastaar = st.number_input("Vinst prognos nästa år", format="%.2f", key="vinst_nastaar", value=st.session_state.vinst_nastaar if st.session_state.vinst_nastaar is not None else 0.0)
        omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt i år (%)", format="%.2f", key="omsattningstillvaxt_arsprognos", value=st.session_state.omsattningstillvaxt_arsprognos if st.session_state.omsattningstillvaxt_arsprognos is not None else 0.0)
        omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)", format="%.2f", key="omsattningstillvaxt_nastaar", value=st.session_state.omsattningstillvaxt_nastaar if st.session_state.omsattningstillvaxt_nastaar is not None else 0.0)

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

                # Töm alla fält (så det inte står 0.00 eller gamla värden kvar)
                st.session_state.namn = ""
                st.session_state.nuvarande_kurs = None
                st.session_state.pe1 = None
                st.session_state.pe2 = None
                st.session_state.pe3 = None
                st.session_state.pe4 = None
                st.session_state.ps1 = None
                st.session_state.ps2 = None
                st.session_state.ps3 = None
                st.session_state.ps4 = None
                st.session_state.vinst_arsprognos = None
                st.session_state.vinst_nastaar = None
                st.session_state.omsattningstillvaxt_arsprognos = None
                st.session_state.omsattningstillvaxt_nastaar = None

    bolag = hamta_alla_bolag()
    if bolag:
        df = pd.DataFrame(
            bolag,
            columns=[
                "namn", "nuvarande_kurs",
                "pe1", "pe2", "pe3", "pe4",
                "ps1", "ps2", "ps3", "ps4",
                "vinst_arsprognos", "vinst_nastaar",
                "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
                "insatt_datum"
            ]
        )
        st.write("### Sparade bolag")
        st.dataframe(df)

if __name__ == "__main__":
    main()
