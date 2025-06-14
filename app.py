import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "bolag.db"

# --- Skapa tabellen om den inte finns ---
def skapa_databas():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bolag (
            namn TEXT PRIMARY KEY,
            kurs REAL,
            pe1 REAL, pe2 REAL, pe3 REAL, pe4 REAL,
            ps1 REAL, ps2 REAL, ps3 REAL, ps4 REAL,
            vinst_ar REAL, vinst_nasta_ar REAL,
            oms_ar REAL, oms_nasta_ar REAL
        )
    """)
    conn.commit()
    conn.close()

# --- Spara bolag till databasen ---
def spara_bolag(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO bolag (
            namn, kurs,
            pe1, pe2, pe3, pe4,
            ps1, ps2, ps3, ps4,
            vinst_ar, vinst_nasta_ar,
            oms_ar, oms_nasta_ar
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

# --- Hämta alla bolag ---
def hamta_bolag():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM bolag", conn)
    conn.close()
    return df

# --- Ta bort bolag ---
def radera_bolag(namn):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn = ?", (namn,))
    conn.commit()
    conn.close()

# --- Räkna ut targetkurser ---
def berakna_target(df):
    df = df.copy()
    df["pe_snitt"] = df[["pe1", "pe2", "pe3", "pe4"]].mean(axis=1)
    df["ps_snitt"] = df[["ps1", "ps2", "ps3", "ps4"]].mean(axis=1)

    df["vinst_snitt"] = (df["vinst_ar"] + df["vinst_nasta_ar"]) / 2
    df["oms_snitt"] = (df["oms_ar"] + df["oms_nasta_ar"]) / 2

    df["target_pe"] = df["pe_snitt"] * df["vinst_snitt"]
    df["target_ps"] = df["ps_snitt"] * df["oms_snitt"]
    df["target_genomsnitt"] = (df["target_pe"] + df["target_ps"]) / 2

    df["undervardering_pct"] = ((df["target_genomsnitt"] - df["kurs"]) / df["kurs"]) * 100

    return df

# --- Huvudfunktion för Streamlit-appen ---
def main():
    st.set_page_config(page_title="Aktieanalys", layout="wide")
    skapa_databas()

    st.title("📈 Aktieanalys – Enkelt & Effektivt")

    with st.form("bolagsformulär"):
        st.subheader("➕ Lägg till nytt bolag")
        namn = st.text_input("Bolagsnamn")
        kurs = st.number_input("Nuvarande kurs", step=0.1)

        pe1 = st.number_input("P/E år 1")
        pe2 = st.number_input("P/E år 2")
        pe3 = st.number_input("P/E år 3")
        pe4 = st.number_input("P/E år 4")

        ps1 = st.number_input("P/S år 1")
        ps2 = st.number_input("P/S år 2")
        ps3 = st.number_input("P/S år 3")
        ps4 = st.number_input("P/S år 4")

        vinst_ar = st.number_input("Vinst prognos i år")
        vinst_nasta_ar = st.number_input("Vinst prognos nästa år")

        oms_ar = st.number_input("Omsättningstillväxt i år")
        oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år")

        sparaknapp = st.form_submit_button("💾 Spara bolag")

        if sparaknapp and namn:
            data = (namn, kurs, pe1, pe2, pe3, pe4, ps1, ps2, ps3, ps4,
                    vinst_ar, vinst_nasta_ar, oms_ar, oms_nasta_ar)
            spara_bolag(data)
            st.success(f"{namn} har sparats.")
            st.experimental_rerun()

    st.subheader("📋 Alla bolag (i bokstavsordning)")
    df = hamta_bolag()

    if not df.empty:
        df = berakna_target(df)
        df_sorted = df.sort_values("namn")

        # Visa alla bolag
        st.dataframe(df_sorted[[
            "namn", "kurs", "target_pe", "target_ps", "target_genomsnitt", "undervardering_pct"
        ]].rename(columns={
            "namn": "Bolag",
            "kurs": "Nuvarande kurs",
            "target_pe": "Target P/E",
            "target_ps": "Target P/S",
            "target_genomsnitt": "Target Snitt",
            "undervardering_pct": "Undervärdering (%)"
        }).style.format({
            "Nuvarande kurs": "{:.2f}",
            "Target P/E": "{:.2f}",
            "Target P/S": "{:.2f}",
            "Target Snitt": "{:.2f}",
            "Undervärdering (%)": "{:.1f}%"
        }), use_container_width=True)

        # Filtrera undervärderade
        if st.button("🔍 Visa undervärderade (>30%)"):
            under_df = df[df["undervardering_pct"] >= 30]
            under_df = under_df.sort_values("undervardering_pct", ascending=False)

            if under_df.empty:
                st.info("Inga bolag är undervärderade med minst 30%.")
            else:
                st.subheader("📉 Undervärderade bolag (>30%)")
                st.dataframe(under_df[[
                    "namn", "kurs", "target_pe", "target_ps", "target_genomsnitt", "undervardering_pct"
                ]].rename(columns={
                    "namn": "Bolag",
                    "kurs": "Nuvarande kurs",
                    "target_pe": "Target P/E",
                    "target_ps": "Target P/S",
                    "target_genomsnitt": "Target Snitt",
                    "undervardering_pct": "Undervärdering (%)"
                }).style.format({
                    "Nuvarande kurs": "{:.2f}",
                    "Target P/E": "{:.2f}",
                    "Target P/S": "{:.2f}",
                    "Target Snitt": "{:.2f}",
                    "Undervärdering (%)": "{:.1f}%"
                }), use_container_width=True)

        # Radera funktion
        st.subheader("🗑️ Radera bolag")
        namn_lista = df_sorted["namn"].tolist()
        valt_bolag = st.selectbox("Välj bolag att radera", namn_lista)
        if st.button("Ta bort bolag"):
            radera_bolag(valt_bolag)
            st.warning(f"{valt_bolag} har tagits bort.")
            st.experimental_rerun()
    else:
        st.info("Inga bolag sparade ännu.")

if __name__ == "__main__":
    main()
