import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "aktier.db"

# --- Initiera databasen ---
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

# --- Lägg till eller uppdatera bolag ---
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

# --- Hämta alla bolag ---
def get_all_bolag():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM bolag ORDER BY bolag')
    rows = c.fetchall()
    conn.close()
    return rows

# --- Ta bort bolag ---
def delete_bolag(bolagsnamn):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM bolag WHERE bolag=?', (bolagsnamn,))
    conn.commit()
    conn.close()

# --- Beräkningar ---
def genomsnitt(values):
    vals = [v for v in values if v is not None]
    return sum(vals)/len(vals) if vals else None

def targetkurs_pe(pe_values, vinst):
    pe_avg = genomsnitt(pe_values)
    if pe_avg is None or vinst is None:
        return None
    return pe_avg * vinst

def targetkurs_ps(ps_values, oms):
    ps_avg = genomsnitt(ps_values)
    if ps_avg is None or oms is None:
        return None
    return ps_avg * oms

# --- Streamlit-app ---
def main():
    st.title("Aktieanalys med databashantering")

    init_db()

    # --- Form för nytt bolag ---
    with st.form("form_lagg_till"):
        st.subheader("Lägg till eller uppdatera bolag")

        bolag = st.text_input("Bolagsnamn (unik identifierare)").strip()
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")

        pe1 = st.number_input("P/E år -4", min_value=0.0, format="%.2f")
        pe2 = st.number_input("P/E år -3", min_value=0.0, format="%.2f")
        pe3 = st.number_input("P/E år -2", min_value=0.0, format="%.2f")
        pe4 = st.number_input("P/E år -1", min_value=0.0, format="%.2f")

        ps1 = st.number_input("P/S år -4", min_value=0.0, format="%.2f")
        ps2 = st.number_input("P/S år -3", min_value=0.0, format="%.2f")
        ps3 = st.number_input("P/S år -2", min_value=0.0, format="%.2f")
        ps4 = st.number_input("P/S år -1", min_value=0.0, format="%.2f")

        vinst_ar = st.number_input("Vinst prognos i år", format="%.2f")
        vinst_nasta_ar = st.number_input("Vinst prognos nästa år", format="%.2f")

        oms_i_ar = st.number_input("Omsättningstillväxt i år", format="%.2f")
        oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år", format="%.2f")

        submitted = st.form_submit_button("Spara bolag")

        if submitted:
            if bolag == "":
                st.error("Du måste ange bolagsnamn!")
            else:
                data = (
                    bolag,
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
                st.experimental_rerun()

    # --- Visa bolag ---
    st.markdown("---")
    st.subheader("Alla bolag i databasen")

    alla_bolag = get_all_bolag()

    if not alla_bolag:
        st.info("Inga bolag sparade ännu.")
    else:
        filter_undervarderade = st.checkbox("Visa endast bolag undervärderade minst 30%")

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

            targets = [t for t in [target_pe_ar, target_pe_nasta_ar, target_ps_ar, target_ps_nasta_ar] if t is not None]
            target_genomsnitt = sum(targets)/len(targets) if targets else None

            undervardering_pct = None
            if target_genomsnitt is not None:
                undervardering_pct = (target_genomsnitt - kurs) / kurs * 100

            bolag_data.append({
                "bolag": bolag,
                "kurs": kurs,
                "target_pe_ar": target_pe_ar,
                "target_pe_nasta_ar": target_pe_nasta_ar,
                "target_ps_ar": target_ps_ar,
                "target_ps_nasta_ar": target_ps_nasta_ar,
                "target_genomsnitt": target_genomsnitt,
                "undervardering_pct": undervardering_pct
            })

        if filter_undervarderade:
            bolag_data = [b for b in bolag_data if b["undervardering_pct"] is not None and b["undervardering_pct"] >= 30]
            bolag_data = sorted(bolag_data, key=lambda x: x["undervardering_pct"], reverse=True)

        df = pd.DataFrame(bolag_data)
        if not df.empty:
            df_display = df.copy()
            df_display["kurs"] = df_display["kurs"].map("{:.2f}".format)
            df_display["target_pe_ar"] = df_display["target_pe_ar"].map(lambda x: f"{x:.2f}" if x else "-")
            df_display["target_pe_nasta_ar"] = df_display["target_pe_nasta_ar"].map(lambda x: f"{x:.2f}" if x else "-")
            df_display["target_ps_ar"] = df_display["target_ps_ar"].map(lambda x: f"{x:.2f}" if x else "-")
            df_display["target_ps_nasta_ar"] = df_display["target_ps_nasta_ar"].map(lambda x: f"{x:.2f}" if x else "-")
            df_display["target_genomsnitt"] = df_display["target_genomsnitt"].map(lambda x: f"{x:.2f}" if x else "-")
            df_display["undervardering_pct"] = df_display["undervardering_pct"].map(lambda x: f"{x:.1f}%" if
