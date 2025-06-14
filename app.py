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
            insatt_datum TEXT,
            senast_andrad TEXT
        )
    """)
    conn.commit()
    conn.close()

def spara_bolag(data, is_update=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if is_update:
        # Uppdatera existerande rad och sätt senast_andrad till nu
        c.execute("""
            UPDATE bolag SET
                nuvarande_kurs = ?,
                pe1 = ?, pe2 = ?, pe3 = ?, pe4 = ?,
                ps1 = ?, ps2 = ?, ps3 = ?, ps4 = ?,
                vinst_arsprognos = ?,
                vinst_nastaar = ?,
                omsattningstillvaxt_arsprognos = ?,
                omsattningstillvaxt_nastaar = ?,
                senast_andrad = ?
            WHERE namn = ?
        """, (
            data['nuvarande_kurs'],
            data['pe1'], data['pe2'], data['pe3'], data['pe4'],
            data['ps1'], data['ps2'], data['ps3'], data['ps4'],
            data['vinst_arsprognos'],
            data['vinst_nastaar'],
            data['omsattningstillvaxt_arsprognos'],
            data['omsattningstillvaxt_nastaar'],
            datetime.now().isoformat(timespec='seconds'),
            data['namn']
        ))
    else:
        # Lägg till ny rad med insatt_datum och senast_andrad satt till nu
        c.execute("""
            INSERT INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['namn'],
            data['nuvarande_kurs'],
            data['pe1'], data['pe2'], data['pe3'], data['pe4'],
            data['ps1'], data['ps2'], data['ps3'], data['ps4'],
            data['vinst_arsprognos'],
            data['vinst_nastaar'],
            data['omsattningstillvaxt_arsprognos'],
            data['omsattningstillvaxt_nastaar'],
            datetime.now().isoformat(timespec='seconds'),
            datetime.now().isoformat(timespec='seconds'),
        ))
    conn.commit()
    conn.close()

def hamta_alla_bolag():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT namn, nuvarande_kurs,
               pe1, pe2, pe3, pe4,
               ps1, ps2, ps3, ps4,
               vinst_arsprognos, vinst_nastaar,
               omsattningstillvaxt_arsprognos, omsattningstillvaxt_nastaar,
               insatt_datum, senast_andrad
        FROM bolag ORDER BY namn COLLATE NOCASE ASC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def hamta_bolag_sorterat_på_datum():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT namn, insatt_datum
        FROM bolag ORDER BY datetime(insatt_datum) ASC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def ta_bort_bolag(namn):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn = ?", (namn,))
    conn.commit()
    conn.close()

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
    st.title("Aktieanalys – Spara, redigera, ta bort och analysera bolag")
    init_db()

    # --- Lägg till nytt bolag ---
    with st.expander("Lägg till nytt bolag"):
        with st.form("form_lagg_till_bolag", clear_on_submit=True):
            namn = st.text_input("Bolagsnamn (unik)").strip()
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
                if namn == "":
                    st.error("Bolagsnamn måste anges.")
                else:
                    alla_bolag = hamta_alla_bolag()
                    namn_i_db = [b[0] for b in alla_bolag]
                    if namn in namn_i_db:
                        st.error("Bolaget finns redan. Använd redigeringsfunktionen istället.")
                    else:
                        data = {
                            'namn': namn,
                            'nuvarande_kurs': nuvarande_kurs,
                            'pe1': pe1,
                            'pe2': pe2,
                            'pe3': pe3,
                            'pe4': pe4,
                            'ps1': ps1,
                            'ps2': ps2,
                            'ps3': ps3,
                            'ps4': ps4,
                            'vinst_arsprognos': vinst_arsprognos,
                            'vinst_nastaar': vinst_nastaar,
                            'omsattningstillvaxt_arsprognos': omsattningstillvaxt_arsprognos,
                            'omsattningstillvaxt_nastaar': omsattningstillvaxt_nastaar,
                        }
                        spara_bolag(data)
                        st.success(f"Bolaget '{namn}' har lagts till.")

    # --- Redigera bolag ---
    st.header("Redigera sparade bolag")
    alla_bolag = hamta_alla_bolag()
    if not alla_bolag:
        st.info("Inga bolag sparade än.")
    else:
        namn_lista = [b[0] for b in alla_bolag]
        valt_bolag = st.selectbox("Välj bolag att redigera", namn_lista)
        if valt_bolag:
            # Hämta data för valt bolag
            vald_data = next((b for b in alla_bolag if b[0] == valt_bolag), None)
            if vald_data:
                # packa ut data
                (namn, nuvarande_kurs, pe1, pe2, pe3, pe4, ps1, ps2, ps3, ps4,
                 vinst_arsprognos, vinst_nastaar, omsattningstillvaxt_arsprognos,
                 omsattningstillvaxt_nastaar, insatt_datum, senast_andrad) = vald_data

                with st.form("form_redigera_bolag"):
                    nuvarande_kurs_new = st.number_input("Nuvarande kurs", value=nuvarande_kurs, format="%.2f")
                    pe1_new = st.number_input("P/E (år 1)", value=pe1, format="%.2f")
                    pe2_new = st.number_input("P/E (år 2)", value=pe2, format="%.2f")
                    pe3_new = st.number_input("P/E (år 3)", value=pe3, format="%.2f")
                    pe4_new = st.number_input("P/E (år 4)", value=pe4, format="%.2f")
                    ps1_new = st.number_input("P/S (år 1)", value=ps1, format="%.2f")
                    ps2_new = st.number_input("P/S (år 2)", value=ps2, format="%.2f")
                    ps3_new = st.number_input("P/S (år 3)", value=ps3, format="%.2f")
                    ps4_new = st.number_input("P/S (år 4)", value=ps4, format="%.2f")
                    vinst_arsprognos_new = st.number_input("Vinst prognos i år", value=vinst_arsprognos, format="%.2f")
                    vinst_nastaar_new = st.number_input("Vinst prognos
