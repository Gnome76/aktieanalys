import streamlit as st
import sqlite3
import pandas as pd
import os

# För att garantera att databasfilen sparas på korrekt plats på Streamlit Cloud
DB_NAME = os.path.join(".", "bolag.db")

# Initiera databasen
def init_db():
    try:
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
    except Exception as e:
        st.error(f"Fel vid initiering av databas: {e}")

def spara_bolag(data):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Fel vid sparande: {e}")

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

    undervardering_genomsnitt_ars = (target_genomsnitt_ars / nuvarande_kurs) - 1 if target_genomsnitt_ars and nuvarande_kurs else None
    undervardering_genomsnitt_nastaar = (target_genomsnitt_nastaar / nuvarande_kurs) - 1 if target_genomsnitt_nastaar and nuvarande_kurs else None

    return {
        "target_genomsnitt_ars": target_genomsnitt_ars,
        "target_genomsnitt_nastaar": target_genomsnitt_nastaar,
        "undervardering_genomsnitt_ars": undervardering_genomsnitt_ars,
        "undervardering_genomsnitt_nastaar": undervardering_genomsnitt_nastaar,
    }

def main():
    st.title("📈 Aktieanalys - Köpvärda bolag")

    init_db()

    # Formulär för att lägga till nytt bolag
    with st.form("form_lagg_till_bolag"):
        namn = st.text_input("Bolagsnamn (unika)")
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0)
        pe1 = st.number_input("P/E (år 1)", min_value=0.0)
        pe2 = st.number_input("P/E (år 2)", min_value=0.0)
        pe3 = st.number_input("P/E (år 3)", min_value=0.0)
        pe4 = st.number_input("P/E (år 4)", min_value=0.0)
        ps1 = st.number_input("P/S (år 1)", min_value=0.0)
        ps2 = st.number_input("P/S (år 2)", min_value=0.0)
        ps3 = st.number_input("P/S (år 3)", min_value=0.0)
        ps4 = st.number_input("P/S (år 4)", min_value=0.0)
        vinst_arsprognos = st.number_input("Vinst prognos i år", min_value=0.0)
        vinst_nastaar = st.number_input("Vinst prognos nästa år", min_value=0.0)
        omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt i år (%)", min_value=0.0)
        omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)", min_value=0.0)

        if st.form_submit_button("💾 Spara bolag"):
            if namn.strip() == "":
                st.error("Bolagsnamn krävs.")
            else:
                data = (
                    namn.strip(), nuvarande_kurs,
                    pe1, pe2, pe3, pe4,
                    ps1, ps2, ps3, ps4,
                    vinst_arsprognos, vinst_nastaar,
                    omsattningstillvaxt_arsprognos, omsattningstillvaxt_nastaar,
                )
                spara_bolag(data)
                st.success(f"Bolag '{namn}' sparat!")
                st.rerun()

    # Hämta och visa alla bolag
    bolag = hamta_alla_bolag()
    if bolag:
        df = pd.DataFrame(bolag, columns=[
            "namn", "nuvarande_kurs",
            "pe1", "pe2", "pe3", "pe4",
            "ps1", "ps2", "ps3", "ps4",
            "vinst_arsprognos", "vinst_nastaar",
            "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar"
        ])

        target_data = []
        for _, row in df.iterrows():
            resultat = berakna_targetkurs(
                [row.pe1, row.pe2, row.pe3, row.pe4],
                [row.ps1, row.ps2, row.ps3, row.ps4],
                row.vinst_arsprognos,
                row.vinst_nastaar,
                row.nuvarande_kurs,
            )
            target_data.append(resultat)

        df_target = pd.DataFrame(target_data)
        df_display = pd.concat([df, df_target], axis=1)

        st.subheader("📊 Alla bolag")
        st.dataframe(df_display[[
            "namn", "nuvarande_kurs",
            "target_genomsnitt_ars", "target_genomsnitt_nastaar",
            "undervardering_genomsnitt_ars", "undervardering_genomsnitt_nastaar"
        ]].style.format({
            "nuvarande_kurs": "{:.2f}",
            "target_genomsnitt_ars": "{:.2f}",
            "target_genomsnitt_nastaar": "{:.2f}",
            "undervardering_genomsnitt_ars": "{:.0%}",
            "undervardering_genomsnitt_nastaar": "{:.0%}",
        }))

        if st.checkbox("✅ Visa endast bolag undervärderade ≥ 30%"):
            filtrerat = df_display[
                (df_display["undervardering_genomsnitt_ars"] >= 0.3)
                | (df_display["undervardering_genomsnitt_nastaar"] >= 0.3)
            ].sort_values(by="undervardering_genomsnitt_ars", ascending=False)

            if not filtrerat.empty:
                st.subheader("💎 Köpvärda bolag")
                st.dataframe(filtrerat[[
                    "namn", "nuvarande_kurs",
                    "target_genomsnitt_ars", "target_genomsnitt_nastaar",
                    "undervardering_genomsnitt_ars", "undervardering_genomsnitt_nastaar"
                ]].style.format({
                    "nuvarande_kurs": "{:.2f}",
                    "target_genomsnitt_ars": "{:.2f}",
                    "target_genomsnitt_nastaar": "{:.2f}",
                    "undervardering_genomsnitt_ars": "{:.0%}",
                    "undervardering_genomsnitt_nastaar": "{:.0%}",
                }))
            else:
                st.info("Inga undervärderade bolag hittades.")

        # Ta bort bolag
        st.subheader("🗑️ Ta bort bolag")
        val = st.selectbox("Välj bolag", options=df["namn"])
        if st.button("Ta bort"):
            ta_bort_bolag(val)
            st.success(f"Bolag '{val}' borttaget.")
            st.rerun()

    else:
        st.info("Inga bolag sparade ännu.")

if __name__ == "__main__":
    main()
