import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "aktier.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS bolag (
        bolag TEXT PRIMARY KEY,
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
    conn.close()

def add_or_update_bolag(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
    INSERT INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(bolag) DO UPDATE SET
        nuvarande_kurs=excluded.nuvarande_kurs,
        pe1=excluded.pe1,
        pe2=excluded.pe2,
        pe3=excluded.pe3,
        pe4=excluded.pe4,
        ps1=excluded.ps1,
        ps2=excluded.ps2,
        ps3=excluded.ps3,
        ps4=excluded.ps4,
        vinst_ar=excluded.vinst_ar,
        vinst_nasta_ar=excluded.vinst_nasta_ar,
        oms_i_ar=excluded.oms_i_ar,
        oms_nasta_ar=excluded.oms_nasta_ar
    ''', data)
    conn.commit()
    conn.close()

def get_all_bolag():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM bolag ORDER BY bolag')
    rows = c.fetchall()
    conn.close()
    return rows

def genomsnitt(values):
    vals = [v for v in values if v is not None and v > 0]
    return sum(vals)/len(vals) if vals else None

def targetkurs_pe(pe_values, vinst):
    pe_avg = genomsnitt(pe_values)
    if pe_avg is None or vinst is None or vinst <= 0:
        return None
    return pe_avg * vinst

def targetkurs_ps(ps_values, oms):
    ps_avg = genomsnitt(ps_values)
    if ps_avg is None or oms is None or oms <= 0:
        return None
    return ps_avg * oms

def main():
    st.title("Aktieanalys med databashantering")

    init_db()

    # Session state för formulärdata
    if "form_data" not in st.session_state:
        st.session_state.form_data = {
            "bolag": "",
            "nuvarande_kurs": 0.0,
            "pe1": 0.0,
            "pe2": 0.0,
            "pe3": 0.0,
            "pe4": 0.0,
            "ps1": 0.0,
            "ps2": 0.0,
            "ps3": 0.0,
            "ps4": 0.0,
            "vinst_ar": 0.0,
            "vinst_nasta_ar": 0.0,
            "oms_i_ar": 0.0,
            "oms_nasta_ar": 0.0
        }

    with st.form("form_lagg_till"):
        st.subheader("Lägg till eller uppdatera bolag")

        bolag = st.text_input("Bolagsnamn (unik identifierare)", st.session_state.form_data["bolag"])
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f", value=st.session_state.form_data["nuvarande_kurs"])

        pe1 = st.number_input("P/E år -4", min_value=0.0, format="%.2f", value=st.session_state.form_data["pe1"])
        pe2 = st.number_input("P/E år -3", min_value=0.0, format="%.2f", value=st.session_state.form_data["pe2"])
        pe3 = st.number_input("P/E år -2", min_value=0.0, format="%.2f", value=st.session_state.form_data["pe3"])
        pe4 = st.number_input("P/E år -1", min_value=0.0, format="%.2f", value=st.session_state.form_data["pe4"])

        ps1 = st.number_input("P/S år -4", min_value=0.0, format="%.2f", value=st.session_state.form_data["ps1"])
        ps2 = st.number_input("P/S år -3", min_value=0.0, format="%.2f", value=st.session_state.form_data["ps2"])
        ps3 = st.number_input("P/S år -2", min_value=0.0, format="%.2f", value=st.session_state.form_data["ps3"])
        ps4 = st.number_input("P/S år -1", min_value=0.0, format="%.2f", value=st.session_state.form_data["ps4"])

        vinst_ar = st.number_input("Vinst prognos i år", format="%.2f", value=st.session_state.form_data["vinst_ar"])
        vinst_nasta_ar = st.number_input("Vinst prognos nästa år", format="%.2f", value=st.session_state.form_data["vinst_nasta_ar"])

        oms_i_ar = st.number_input("Omsättningstillväxt i år", format="%.2f", value=st.session_state.form_data["oms_i_ar"])
        oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år", format="%.2f", value=st.session_state.form_data["oms_nasta_ar"])

        submitted = st.form_submit_button("Spara bolag")

        if submitted:
            if bolag.strip() == "":
                st.error("Du måste ange bolagsnamn!")
            else:
                data = (
                    bolag.strip(),
                    nuvarande_kurs,
                    pe1, pe2, pe3, pe4,
                    ps1, ps2, ps3, ps4,
                    vinst_ar,
                    vinst_nasta_ar,
                    oms_i_ar,
                    oms_nasta_ar
                )
                add_or_update_bolag(data)
                st.success(f"Bolaget '{bolag}' sparat/uppdaterat!")

                # Nollställ formulärfält
                st.session_state.form_data = {
                    "bolag": "",
                    "nuvarande_kurs": 0.0,
                    "pe1": 0.0,
                    "pe2": 0.0,
                    "pe3": 0.0,
                    "pe4": 0.0,
                    "ps1": 0.0,
                    "ps2": 0.0,
                    "ps3": 0.0,
                    "ps4": 0.0,
                    "vinst_ar": 0.0,
                    "vinst_nasta_ar": 0.0,
                    "oms_i_ar": 0.0,
                    "oms_nasta_ar": 0.0
                }

    st.markdown("---")
    st.subheader("Bolagslista och värdering")

    alla_bolag = get_all_bolag()

    if not alla_bolag:
        st.info("Inga bolag sparade ännu.")
        return

    filter_undervarderade = st.checkbox("Visa endast bolag undervärderade med minst 30%")

    bolag_data = []
    for row in alla_bolag:
        (
            bolag, kurs, pe1, pe2, pe3, pe4,
            ps1, ps2, ps3, ps4,
            vinst_ar, vinst_nasta_ar,
            oms_i_ar, oms_nasta_ar
        ) = row

        pe_vals = [pe1, pe2, pe3, pe4]
        ps_vals = [ps1, ps2, ps3, ps4]

        target_pe_ar = targetkurs_pe(pe_vals, vinst_ar)
        target_pe_nasta_ar = targetkurs_pe(pe_vals, vinst_nasta_ar)
        target_ps_ar = targetkurs_ps(ps_vals, oms_i_ar)
        target_ps_nasta_ar = targetkurs_ps(ps_vals, oms_nasta_ar)

        # Genomsnitt av P/E- och P/S-targetkurser för i år och nästa år (de som finns)
        targets = [t for t in [target_pe_ar, target_pe_nasta_ar, target_ps_ar, target_ps_nasta_ar] if t is not None]
        target_genomsnitt = sum(targets)/len(targets) if targets else None

        undervardering_pct = None
        if target_genomsnitt is not None and kurs > 0:
            undervardering_pct = (target_genomsnitt - kurs) / kurs * 100

        bolag_data.append({
            "Bolag": bolag,
            "Nuvarande kurs": kurs,
            "Target P/E i år": target_pe_ar,
            "Target P/E nästa år": target_pe_nasta_ar,
            "Target P/S i år": target_ps_ar,
            "Target P/S nästa år": target_ps_nasta_ar,
            "Genomsnittlig targetkurs": target_genomsnitt,
            "Undervärdering %": undervardering_pct
        })

    # Filtrera undervärderade om kryssrutan är satt
    if filter_undervarderade:
        bolag_data = [b for b in bolag_data if b["Undervärdering %"] is not None and b["Undervärdering %"] >= 30]

    # Sortera
