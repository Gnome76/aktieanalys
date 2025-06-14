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

def spara_bolag(data, redigera=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if redigera:
        c.execute("""
            UPDATE bolag SET
                nuvarande_kurs = ?,
                pe1 = ?,
                pe2 = ?,
                pe3 = ?,
                pe4 = ?,
                ps1 = ?,
                ps2 = ?,
                ps3 = ?,
                ps4 = ?,
                vinst_arsprognos = ?,
                vinst_nastaar = ?,
                omsattningstillvaxt_arsprognos = ?,
                omsattningstillvaxt_nastaar = ?,
                senast_andrad = ?
            WHERE namn = ?
        """, (
            data["nuvarande_kurs"],
            data["pe1"], data["pe2"], data["pe3"], data["pe4"],
            data["ps1"], data["ps2"], data["ps3"], data["ps4"],
            data["vinst_arsprognos"],
            data["vinst_nastaar"],
            data["omsattningstillvaxt_arsprognos"],
            data["omsattningstillvaxt_nastaar"],
            data["senast_andrad"],
            data["namn"]
        ))
    else:
        c.execute("""
            INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["namn"],
            data["nuvarande_kurs"],
            data["pe1"], data["pe2"], data["pe3"], data["pe4"],
            data["ps1"], data["ps2"], data["ps3"], data["ps4"],
            data["vinst_arsprognos"],
            data["vinst_nastaar"],
            data["omsattningstillvaxt_arsprognos"],
            data["omsattningstillvaxt_nastaar"],
            data["insatt_datum"],
            data["senast_andrad"]
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
    st.title("Aktieinnehav – Spara, redigera och analysera")
    init_db()

    # Lägg till nytt bolag
    st.header("Lägg till nytt bolag")
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
            if not namn.strip():
                st.error("Bolagsnamn måste anges.")
            else:
                nu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data = {
                    "namn": namn.strip(),
                    "nuvarande_kurs": nuvarande_kurs,
                    "pe1": pe1, "pe2": pe2, "pe3": pe3, "pe4": pe4,
                   
