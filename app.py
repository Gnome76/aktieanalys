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
        pe1=excluded.pe1, pe2=excluded.pe2, pe3=excluded.pe3, pe4=excluded.pe4,
        ps1=excluded.ps1, ps2=excluded.ps2, ps3=excluded.ps3, ps4=excluded.ps4,
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
    st.title("📊 Aktieanalys App")

    init_db()

    if "form_data" not in st.session_state:
        st.session_state.form_data = {
            "bolag": "", "nuvarande_kurs": 0.0,
            "pe1": 0.0, "pe2": 0.0, "pe3": 0.0, "pe4": 0.0,
            "ps1": 0.0, "ps2": 0.0, "ps3": 0.0, "ps4": 0.0,
            "vinst_ar": 0.0, "vinst_nasta_ar": 0.0,
            "oms_i_ar": 0.0, "oms_nasta_ar": 0.0
        }

    with st.form("form_lagg_till"):
        st.subheader("➕ Lägg till / uppdatera bolag")

        bolag = st.text_input("Bolagsnamn", st.session_state.form_data["bolag"])
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f", value=st.session_state.form_data["nuvarande_kurs"])
        pe1 = st.number_input("P/E -4 år", value=st.session_state.form_data["pe1"])
        pe2 = st.number_input("P/E -3 år", value=st.session_state.form_data["pe2"])
        pe3 = st.number_input("P/E -2 år", value=st.session_state.form_data["pe3"])
        pe4 = st.number_input("P/E -1 år", value=st.session_state.form_data["pe4"])
        ps1 = st.number_input("P/S -4 år", value=st.session_state.form_data["ps1"])
        ps2 = st.number_input("P/S -3 år", value=st.session_state.form_data["ps2"])
        ps3 = st.number_input("P/S -2 år", value=st.session_state.form_data["ps3"])
        ps4 = st.number_input("P/S -1 år", value=st.session_state.form_data["ps4"])
        vinst_ar = st.number_input("Vinst i år", value=st.session_state.form_data["vinst_ar"])
        vinst_nasta_ar = st.number_input("Vinst nästa år", value=st.session_state.form_data["vinst_nasta_ar"])
        oms_i_ar = st.number_input("Omsättning i år", value=st.session_state.form_data["oms_i_ar"])
        oms_nasta_ar = st.number_input("Omsättning nästa år", value=st.session_state.form_data["oms_nasta_ar"])

        if st.form_submit_button("💾 Spara bolag"):
            if bolag.strip() == "":
                st.error("⚠️ Du måste ange bolagsnamn.")
            else:
                data = (
                    bolag.strip(), nuvarande_kurs,
                    pe1, pe2, pe3, pe4,
                    ps1, ps2, ps3, ps4,
                    vinst_ar, vinst_nasta_ar,
                    oms_i_ar, oms_nasta_ar
                )
                add_or_update_bolag(data)
                st.success(f"✅ '{bolag}' sparat/uppdaterat!")
                st.session_state.form_data = {k: 0.0 for k in st.session_state.form_data}
                st.session_state.form_data["bolag"] = ""

    st.markdown("---")
    st.subheader("📋 Bolagsdata och värdering")

    alla_bolag = get_all_bolag()

    if not alla_bolag:
        st.info("Inga bolag sparade ännu.")
    else:
        filter_undervarderade = st.checkbox("🔍 Visa endast undervärderade (>30%)", value=False)

        bolag_data = []
        for row in alla_bolag:
            (bolag, kurs, pe1, pe2, pe3, pe4, ps1, ps2, ps3, ps4,
             vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar) = row

            pe_vals = [pe1, pe2, pe3, pe4]
            ps_vals = [ps1, ps2, ps3, ps4]

            target_pe = targetkurs_pe(pe_vals, vinst_ar)
            target_ps = targetkurs_ps(ps_vals, oms_i_ar)

            targets = [t for t in [target_pe, target_ps] if t]
            target_avg = sum(targets)/len(targets) if targets else None

            undervardering_pct = None
            if target_avg and kurs > 0:
                undervardering_pct = (target_avg - kurs) / kurs * 100

            bolag_data.append({
                "Bolag": bolag,
                "Nuvarande kurs": kurs,
                "Target P/E": round(target_pe, 2) if target_pe else None,
                "Target P/S": round(target_ps, 2) if target_ps else None,
                "Genomsnittlig targetkurs": round(target_avg, 2) if target_avg else None,
                "Undervärdering %": round(undervardering_pct, 1) if undervardering_pct else None
            })

        df = pd.DataFrame(bolag_data)

        if filter_undervarderade:
            df = df[df["Undervärdering %"] >= 30].sort_values("Undervärdering %", ascending=False)

        if df.empty:
            st.info("Inga bolag matchar filtret.")
        else:
            st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()
