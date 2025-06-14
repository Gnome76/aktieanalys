import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "bolag.db"

# Initiera databasen
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bolag (
                namn TEXT PRIMARY KEY,
                nuvarande_kurs REAL,
                pe1 REAL, pe2 REAL, pe3 REAL, pe4 REAL,
                ps1 REAL, ps2 REAL, ps3 REAL, ps4 REAL,
                vinst_arsprognos REAL,
                vinst_nastaar REAL,
                omsattningstillvaxt_arsprognos REAL,
                omsattningstillvaxt_nastaar REAL
            )
        """)

def spara_bolag(data):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

def hamta_alla_bolag():
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query("SELECT * FROM bolag ORDER BY namn COLLATE NOCASE", conn)

def ta_bort_bolag(namn):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM bolag WHERE namn = ?", (namn,))

# Beräkning
def berakna_targetkurs(pe_vardena, ps_vardena, vinst_arsprognos, vinst_nastaar, nuvarande_kurs):
    genomsnitt_pe = sum(pe_vardena) / len(pe_vardena)
    genomsnitt_ps = sum(ps_vardena) / len(ps_vardena)

    target_pe_ars = genomsnitt_pe * vinst_arsprognos if vinst_arsprognos else None
    target_pe_nastaar = genomsnitt_pe * vinst_nastaar if vinst_nastaar else None
    target_ps_ars = genomsnitt_ps * vinst_arsprognos if vinst_arsprognos else None
    target_ps_nastaar = genomsnitt_ps * vinst_nastaar if vinst_nastaar else None

    target_genomsnitt_ars = (target_pe_ars + target_ps_ars) / 2 if target_pe_ars and target_ps_ars else None
    target_genomsnitt_nastaar = (target_pe_nastaar + target_ps_nastaar) / 2 if target_pe_nastaar and target_ps_nastaar else None

    undervardering_genomsnitt_ars = ((target_genomsnitt_ars / nuvarande_kurs) - 1) if target_genomsnitt_ars else None
    undervardering_genomsnitt_nastaar = ((target_genomsnitt_nastaar / nuvarande_kurs) - 1) if target_genomsnitt_nastaar else None

    # Köpvärd upp till 30 % under target
    kopvard_ars = target_genomsnitt_ars * 0.7 if target_genomsnitt_ars else None
    kopvard_nastaar = target_genomsnitt_nastaar * 0.7 if target_genomsnitt_nastaar else None

    return {
        "target_genomsnitt_ars": target_genomsnitt_ars,
        "target_genomsnitt_nastaar": target_genomsnitt_nastaar,
        "undervardering_genomsnitt_ars": undervardering_genomsnitt_ars,
        "undervardering_genomsnitt_nastaar": undervardering_genomsnitt_nastaar,
        "kopvard_ars": kopvard_ars,
        "kopvard_nastaar": kopvard_nastaar,
    }

# App
def main():
    st.set_page_config(page_title="Aktieanalys", layout="wide")
    init_db()

    st.title("📈 Aktieanalys")

    with st.form("form_lagg_till_bolag", clear_on_submit=True):
        namn = st.text_input("Bolagsnamn")
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0)
        pe1 = st.number_input("P/E år 1", min_value=0.0)
        pe2 = st.number_input("P/E år 2", min_value=0.0)
        pe3 = st.number_input("P/E år 3", min_value=0.0)
        pe4 = st.number_input("P/E år 4", min_value=0.0)
        ps1 = st.number_input("P/S år 1", min_value=0.0)
        ps2 = st.number_input("P/S år 2", min_value=0.0)
        ps3 = st.number_input("P/S år 3", min_value=0.0)
        ps4 = st.number_input("P/S år 4", min_value=0.0)
        vinst_arsprognos = st.number_input("Vinst prognos i år")
        vinst_nastaar = st.number_input("Vinst prognos nästa år")
        omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt i år (%)")
        omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)")

        if st.form_submit_button("Lägg till bolag"):
            if namn.strip():
                data = (
                    namn.strip(), nuvarande_kurs,
                    pe1, pe2, pe3, pe4,
                    ps1, ps2, ps3, ps4,
                    vinst_arsprognos, vinst_nastaar,
                    omsattningstillvaxt_arsprognos, omsattningstillvaxt_nastaar,
                )
                spara_bolag(data)
                st.toast("Bolaget har sparats.")
                st.query_params.clear()
                st.experimental_rerun()
            else:
                st.error("Bolagsnamn krävs.")

    df = hamta_alla_bolag()
    if df.empty:
        st.info("Inga bolag sparade ännu.")
        return

    # Beräkna target och undervärdering
    targetdata = df.apply(
        lambda row: berakna_targetkurs(
            [row.pe1, row.pe2, row.pe3, row.pe4],
            [row.ps1, row.ps2, row.ps3, row.ps4],
            row.vinst_arsprognos,
            row.vinst_nastaar,
            row.nuvarande_kurs,
        ),
        axis=1,
        result_type="expand",
    )
    df = pd.concat([df, targetdata], axis=1)

    visa_endast_undervard = st.checkbox("Visa endast undervärderade (≥30%)", value=False)

    if visa_endast_undervard:
        df = df[
            (df["undervardering_genomsnitt_ars"] >= 0.3) |
            (df["undervardering_genomsnitt_nastaar"] >= 0.3)
        ]
        df = df.sort_values(by=["undervardering_genomsnitt_ars"], ascending=False)

    st.subheader("📋 Bolagsdata")
    st.dataframe(df[[
        "namn", "nuvarande_kurs",
        "target_genomsnitt_ars", "target_genomsnitt_nastaar",
        "undervardering_genomsnitt_ars", "undervardering_genomsnitt_nastaar",
        "kopvard_ars", "kopvard_nastaar"
    ]].style.format({
        "nuvarande_kurs": "{:.2f}",
        "target_genomsnitt_ars": "{:.2f}",
        "target_genomsnitt_nastaar": "{:.2f}",
        "undervardering_genomsnitt_ars": "{:.0%}",
        "undervardering_genomsnitt_nastaar": "{:.0%}",
        "kopvard_ars": "{:.2f}",
        "kopvard_nastaar": "{:.2f}",
    }), use_container_width=True)

    st.subheader("🗑️ Ta bort bolag")
    val_bort = st.selectbox("Välj bolag att ta bort", options=df["namn"].unique())
    if st.button("Ta bort valt bolag"):
        ta_bort_bolag(val_bort)
        st.success(f"Bolag '{val_bort}' har tagits bort.")
        st.query_params.clear()
        st.experimental_rerun()

if __name__ == "__main__":
    main()
