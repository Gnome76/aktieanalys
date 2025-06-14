import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "bolag.db"

# Initiera databasen och skapa tabell om den inte finns
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
            omsattningstillvaxt_nastaar REAL
        )
    """)
    conn.commit()
    conn.close()

def spara_bolag(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

def ta_bort_bolag(namn):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn = ?", (namn,))
    conn.commit()
    conn.close()

# Beräkna targetkurser och undervärdering
def berakna_targetkurs(pe_vardena, ps_vardena, vinst_arsprognos, vinst_nastaar, nuvarande_kurs):
    genomsnitt_pe = sum(pe_vardena) / len(pe_vardena)
    genomsnitt_ps = sum(ps_vardena) / len(ps_vardena)

    target_pe_ars = genomsnitt_pe * vinst_arsprognos if vinst_arsprognos and genomsnitt_pe else None
    target_pe_nastaar = genomsnitt_pe * vinst_nastaar if vinst_nastaar and genomsnitt_pe else None

    target_ps_ars = genomsnitt_ps * vinst_arsprognos if vinst_arsprognos and genomsnitt_ps else None
    target_ps_nastaar = genomsnitt_ps * vinst_nastaar if vinst_nastaar and genomsnitt_ps else None

    target_genomsnitt_ars = (target_pe_ars + target_ps_ars) / 2 if target_pe_ars and target_ps_ars else None
    target_genomsnitt_nastaar = (target_pe_nastaar + target_ps_nastaar) / 2 if target_pe_nastaar and target_ps_nastaar else None

    undervardering_ars = (target_pe_ars / nuvarande_kurs) - 1 if nuvarande_kurs and target_pe_ars else None
    undervardering_nastaar = (target_pe_nastaar / nuvarande_kurs) - 1 if nuvarande_kurs and target_pe_nastaar else None
    undervardering_genomsnitt_ars = (target_genomsnitt_ars / nuvarande_kurs) - 1 if nuvarande_kurs and target_genomsnitt_ars else None
    undervardering_genomsnitt_nastaar = (target_genomsnitt_nastaar / nuvarande_kurs) - 1 if nuvarande_kurs and target_genomsnitt_nastaar else None

    return {
        "target_pe_ars": target_pe_ars,
        "target_pe_nastaar": target_pe_nastaar,
        "target_ps_ars": target_ps_ars,
        "target_ps_nastaar": target_ps_nastaar,
        "target_genomsnitt_ars": target_genomsnitt_ars,
        "target_genomsnitt_nastaar": target_genomsnitt_nastaar,
        "undervardering_pe_ars": undervardering_ars,
        "undervardering_pe_nastaar": undervardering_nastaar,
        "undervardering_genomsnitt_ars": undervardering_genomsnitt_ars,
        "undervardering_genomsnitt_nastaar": undervardering_genomsnitt_nastaar,
    }

def main():
    st.title("Aktieinnehav - Spara och analysera")

    init_db()

    # Formulär för att lägga till nytt bolag
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
                )
                spara_bolag(data)
                st.success(f"Bolag '{namn}' sparat!")
                st.experimental_rerun()

    # Visa sparade bolag
    bolag = hamta_alla_bolag()
    if bolag:
        df = pd.DataFrame(
            bolag,
            columns=[
                "namn",
                "nuvarande_kurs",
                "pe1", "pe2", "pe3", "pe4",
                "ps1", "ps2", "ps3", "ps4",
                "vinst_arsprognos",
                "vinst_nastaar",
                "omsattningstillvaxt_arsprognos",
                "omsattningstillvaxt_nastaar"
            ],
        )

        # Beräkna target och undervärdering
        target_lista = []
        for _, row in df.iterrows():
            resultat = berakna_targetkurs(
                [row.pe1, row.pe2, row.pe3, row.pe4],
                [row.ps1, row.ps2, row.ps3, row.ps4],
                row.vinst_arsprognos,
                row.vinst_nastaar,
                row.nuvarande_kurs,
            )
            target_lista.append(resultat)

        df_target = pd.DataFrame(target_lista)
        df_display = pd.concat([df.reset_index(drop=True), df_target], axis=1)

        st.subheader("Alla sparade bolag")
        st.dataframe(df_display[[
            "namn",
            "nuvarande_kurs",
            "target_pe_ars",
            "target_pe_nastaar",
            "target_ps_ars",
            "target_ps_nastaar",
            "target_genomsnitt_ars",
            "target_genomsnitt_nastaar",
            "undervardering_pe_ars",
            "undervardering_pe_nastaar",
            "undervardering_genomsnitt_ars",
            "undervardering_genomsnitt_nastaar",
        ]].style.format({
            "nuvarande_kurs": "{:.2f}",
            "target_pe_ars": "{:.2f}",
            "target_pe_nastaar": "{:.2f}",
            "target_ps_ars": "{:.2f}",
            "target_ps_nastaar": "{:.2f}",
            "target_genomsnitt_ars": "{:.2f}",
            "target_genomsnitt_nastaar": "{:.2f}",
            "undervardering_pe_ars": "{:.0%}",
            "undervardering_pe_nastaar": "{:.0%}",
            "undervardering_genomsnitt_ars": "{:.0%}",
            "undervardering_genomsnitt_nastaar": "{:.0%}",
        }))

        if st.checkbox("Visa bara bolag minst 30 % undervärderade (genomsnitt i år)"):
            df_filter = df_display[df_display["undervardering_genomsnitt_ars"] >= 0.3]
            st.subheader("Undervärderade bolag")
            st.dataframe(
                df_filter[
                    [
                        "namn",
                        "nuvarande_k
