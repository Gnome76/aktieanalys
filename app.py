import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "aktier.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bolag (
            namn TEXT PRIMARY KEY,
            kurs REAL,
            vinst1 REAL,
            vinst2 REAL,
            ps1 REAL,
            ps2 REAL,
            pe1 REAL,
            pe2 REAL,
            tillvaxt REAL,
            insatt_datum TEXT
        )
    ''')
    conn.commit()
    conn.close()

def hamta_bolag():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM bolag", conn)
    conn.close()
    return df

def spara_bolag(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO bolag 
        (namn, kurs, vinst1, vinst2, ps1, ps2, pe1, pe2, tillvaxt, insatt_datum)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data["namn"], data["kurs"], data["vinst1"], data["vinst2"],
        data["ps1"], data["ps2"], data["pe1"], data["pe2"],
        data["tillvaxt"], data["insatt_datum"]
    ))
    conn.commit()
    conn.close()

def ta_bort_bolag(namn):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn = ?", (namn,))
    conn.commit()
    conn.close()

def main():
    st.title("Aktieanalys")

    init_db()
    df = hamta_bolag()

    st.header("Lägg till eller redigera bolag")
    namn = st.text_input("Bolagsnamn").strip()
    kurs = st.number_input("Aktiekurs", value=0.0)
    vinst1 = st.number_input("Vinst/aktie (år 1)", value=0.0)
    vinst2 = st.number_input("Vinst/aktie (år 2)", value=0.0)
    ps1 = st.number_input("P/S (år 1)", value=0.0)
    ps2 = st.number_input("P/S (år 2)", value=0.0)
    pe1 = st.number_input("P/E (år 1)", value=0.0)
    pe2 = st.number_input("P/E (år 2)", value=0.0)
    tillvaxt = st.number_input("Tillväxt %", value=0.0)

    if st.button("Spara bolag"):
        if namn == "":
            st.warning("Bolagsnamn krävs.")
        else:
            data = {
                "namn": namn,
                "kurs": kurs,
                "vinst1": vinst1,
                "vinst2": vinst2,
                "ps1": ps1,
                "ps2": ps2,
                "pe1": pe1,
                "pe2": pe2,
                "tillvaxt": tillvaxt,
                "insatt_datum": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            spara_bolag(data)
            st.success(f"Bolag '{namn}' sparat.")
            st.experimental_rerun()

    st.header("Sparade bolag")
    if df.empty:
        st.info("Inga bolag sparade ännu.")
    else:
        st.dataframe(df)

    st.header("Ta bort bolag")
    val_namn = st.selectbox("Välj bolag att ta bort", df["namn"].sort_values().tolist())
    if st.button("Ta bort valt bolag"):
        ta_bort_bolag(val_namn)
        st.success(f"Bolaget '{val_namn}' är borttaget.")
        st.experimental_rerun()

if __name__ == "__main__":
    main()
