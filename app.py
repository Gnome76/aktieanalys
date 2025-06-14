import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "bolag.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
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
    conn.commit()
    conn.close()

def spara_bolag(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
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

def berakna_targetkurs(pe_vardena, ps_vardena, vinst_arsprognos, vinst_nastaar, nuvarande_kurs):
    genomsnitt_pe = sum(pe_vardena) / len(pe_vardena)
    genomsnitt_ps = sum(ps_vardena) / len(ps_vardena)

    target_pe_ars = genomsnitt_pe * vinst_arsprognos if vinst_arsprognos and genomsnitt_pe else None
    target_pe_nastaar = genomsnitt_pe * vinst_nastaar if vinst_nastaar and genomsnitt_pe else None
    target_ps_ars = genomsnitt_ps * vinst_arsprognos if vinst_arsprognos and genomsnitt_ps else None
    target_ps_nastaar = genomsnitt_ps * vinst_nastaar if vinst_nastaar and genomsnitt_ps else None

    target_genomsnitt_ars = (target_pe_ars + target_ps_ars) / 2 if target_pe_ars and target_ps_ars else None
    target_genomsnitt_nastaar = (target_pe_nastaar + target_ps_nastaar) / 2 if target_pe_nastaar and target_ps_nastaar else None

    undervardering_pe_ars = (target_pe_ars / nuvarande_kurs) - 1 if target_pe_ars and nuvarande_kurs else None
    undervardering_pe_nastaar = (target_pe_nastaar / nuvarande_kurs) - 1 if target_pe_nastaar and nuvarande_kurs else None
    undervardering_genomsnitt_ars = (target_genomsnitt_ars / nuvarande_kurs) - 1 if target_genomsnitt_ars and nuvarande_kurs else None
    undervardering_genomsnitt_nastaar = (target_genomsnitt_nastaar / nuvarande_kurs) - 1 if target_genomsnitt_nastaar and nuvarande_kurs else None

    kopvard_upp_till_ars = target_genomsnitt_ars * 0.7 if target_genomsnitt_ars else None
    kopvard_upp_till_nastaar = target_genomsnitt_nastaar * 0.7 if target_genomsnitt_nastaar else None

    return {
        "target_genomsnitt_ars": target_genomsnitt_ars,
        "target_genomsnitt_nastaar": target_genomsnitt_nastaar,
        "undervardering_genomsnitt_ars": undervardering_genomsnitt_ars,
        "undervardering_genomsnitt_nastaar": undervardering_genomsnitt_nastaar,
        "kopvard_upp_till_ars": kopvard_upp_till_ars,
        "kopvard_upp_till_nastaar": kopvard_upp_till_nastaar
    }

def main():
    st.title("Aktieinnehav – Köpvärda bolag")

    init_db()

    # Formulär: Lägg till nytt bolag
    with st.form("form_lagg_till", clear_on_submit=True):
        namn = st.text_input("Bolagsnamn (unik)")
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")
        pe1 = st.number_input("P/E (år 1)", min_value=0.0)
        pe2 = st.number_input("P/E (år 2)", min_value=0.0)
        pe3 = st.number_input("P/E (år 3)", min_value=0.0)
        pe4 = st.number_input("P/E (år 4)", min_value=0.0)
        ps1 = st.number_input("P/S (år 1)", min_value=0.0)
        ps2 = st.number_input("P/S (år 2)", min_value=0.0)
        ps3 = st.number_input("P/S (år 3)", min_value=0.0)
        ps4 = st.number_input("P/S (år 4)", min_value=0.0)
        vinst_arsprognos = st.number_input("Vinstprognos i år", format="%.2f")
        vinst_nastaar = st.number_input("Vinstprognos nästa år", format="%.2f")
        omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt i år (%)", format="%.2f")
        omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)", format="%.2f")

        if st.form_submit_button("Lägg till bolag"):
            if namn.strip() == "":
                st.error("Bolagsnamn krävs.")
            else:
                data = (
                    namn.strip(), nuvarande_kurs, pe1, pe2, pe3, pe4,
                    ps1, ps2, ps3, ps4, vinst_arsprognos, vinst_nastaar,
                    omsattningstillvaxt_arsprognos, omsattningstillvaxt_nastaar
                )
                spara_bolag(data)
                st.success(f"{namn} sparat.")
                st.experimental_set_query_params(refresh="1")  # Force refresh workaround

    bolag = hamta_alla_bolag()
    if bolag:
        df = pd.DataFrame(bolag, columns=[
            "namn", "nuvarande_kurs", "pe1", "pe2", "pe3", "pe4",
            "ps1", "ps2", "ps3", "ps4", "vinst_arsprognos",
            "vinst_nastaar", "omsattningstillvaxt_arsprognos",
            "omsattningstillvaxt_nastaar"
        ])

        resultat = []
        for _, row in df.iterrows():
            resultat.append(berakna_targetkurs(
                [row.pe1, row.pe2, row.pe3, row.pe4],
                [row.ps1, row.ps2, row.ps3, row.ps4],
                row.vinst_arsprognos, row.vinst_nastaar,
                row.nuvarande_kurs
            ))

        df_resultat = pd.concat([df.reset_index(drop=True), pd.DataFrame(resultat)], axis=1)

        undervarderade = df_resultat[
            (df_resultat["undervardering_genomsnitt_ars"] >= 0.3) |
            (df_resultat["undervardering_genomsnitt_nastaar"] >= 0.3)
        ].sort_values(by=["undervardering_genomsnitt_ars", "undervardering_genomsnitt_nastaar"], ascending=False)

        st.subheader("📉 Undervärderade bolag (≥30%)")

        if undervarderade.empty:
            st.info("Inga undervärderade bolag just nu.")
        else:
            index = st.session_state.get("undervarderad_index", 0)

            bolag = undervarderade.iloc[index]
            st.markdown(f"### {bolag['namn']}")
            st.metric("Nuvarande kurs", f"{bolag['nuvarande_kurs']:.2f} kr")
            st.metric("Target i år", f"{bolag['target_genomsnitt_ars']:.2f} kr")
            st.metric("Target nästa år", f"{bolag['target_genomsnitt_nastaar']:.2f} kr")
            st.metric("Köpvärd upp till (i år)", f"{bolag['kopvard_upp_till_ars']:.2f} kr")
            st.metric("Köpvärd upp till (nästa år)", f"{bolag['kopvard_upp_till_nastaar']:.2f} kr")
            st.metric("Undervärdering i år", f"{bolag['undervardering_genomsnitt_ars']:.0%}")
            st.metric("Undervärdering nästa år", f"{bolag['undervardering_genomsnitt_nastaar']:.0%}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Föregående") and index > 0:
                    st.session_state.undervarderad_index = index - 1
            with col2:
                if st.button("Nästa ➡️") and index < len(undervarderade) - 1:
                    st.session_state.undervarderad_index = index + 1

    else:
        st.info("Inga bolag sparade än.")

if __name__ == "__main__":
    main()
