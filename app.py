import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

DB_FILE = "bolag.db"

# Initiera databas
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bolag (
            namn TEXT PRIMARY KEY,
            aktiekurs REAL,
            vinst1 REAL,
            vinst2 REAL,
            pe1 REAL,
            pe2 REAL,
            ps1 REAL,
            ps2 REAL,
            targetkurs_pe REAL,
            targetkurs_ps REAL,
            uppsida_pe REAL,
            uppsida_ps REAL,
            insatt_datum TEXT
        )
    """)
    conn.commit()
    conn.close()

# Spara nytt eller redigerat bolag
def spara_bolag(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["namn"],
        data["aktiekurs"],
        data["vinst1"],
        data["vinst2"],
        data["pe1"],
        data["pe2"],
        data["ps1"],
        data["ps2"],
        data["targetkurs_pe"],
        data["targetkurs_ps"],
        data["uppsida_pe"],
        data["uppsida_ps"],
        data["insatt_datum"]
    ))
    conn.commit()
    conn.close()

# Ladda alla bolag
def ladda_bolag():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM bolag", conn)
    conn.close()
    return df

# Ta bort bolag
def ta_bort_bolag(namn):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn=?", (namn,))
    conn.commit()
    conn.close()

def main():
    st.title("📊 Aktieanalys")

    # UI-refresh fix utan rerun
    if st.session_state.get("nysparad"):
        st.session_state["nysparad"] = False
        st.experimental_set_query_params(updated=datetime.now().isoformat())

    init_db()
    df = ladda_bolag()

    st.header("➕ Lägg till eller redigera bolag")
    namn = st.text_input("Bolagsnamn")

    aktiekurs = st.number_input("Aktiekurs", min_value=0.0)
    vinst1 = st.number_input("Vinst per aktie år 1", min_value=0.0)
    vinst2 = st.number_input("Vinst per aktie år 2", min_value=0.0)
    pe1 = st.number_input("P/E (år 1)", min_value=0.0)
    pe2 = st.number_input("P/E (år 2)", min_value=0.0)
    ps1 = st.number_input("P/S (år 1)", min_value=0.0)
    ps2 = st.number_input("P/S (år 2)", min_value=0.0)

    if st.button("Spara bolag"):
        if namn == "":
            st.warning("Ange ett bolagsnamn.")
        else:
            target_pe = vinst2 * pe2
            target_ps = vinst2 * ps2
            uppsida_pe = ((target_pe - aktiekurs) / aktiekurs) * 100 if aktiekurs else 0
            uppsida_ps = ((target_ps - aktiekurs) / aktiekurs) * 100 if aktiekurs else 0

            data = {
                "namn": namn,
                "aktiekurs": aktiekurs,
                "vinst1": vinst1,
                "vinst2": vinst2,
                "pe1": pe1,
                "pe2": pe2,
                "ps1": ps1,
                "ps2": ps2,
                "targetkurs_pe": round(target_pe, 2),
                "targetkurs_ps": round(target_ps, 2),
                "uppsida_pe": round(uppsida_pe, 2),
                "uppsida_ps": round(uppsida_ps, 2),
                "insatt_datum": datetime.now().strftime("%Y-%m-%d %H:%M")
            }

            spara_bolag(data)
            st.success(f"Bolag '{namn}' sparat.")
            st.session_state["nysparad"] = True

    st.header("📋 Alla bolag")
    if df.empty:
        st.info("Inga bolag sparade ännu.")
    else:
        df_sorted = df.sort_values(by="uppsida_pe", ascending=False)
        for index, row in df_sorted.iterrows():
            with st.expander(f"{row['namn']} (Uppsida P/E: {row['uppsida_pe']}%)"):
                st.write(f"Aktiekurs: {row['aktiekurs']} kr")
                st.write(f"Vinst år 1: {row['vinst1']}, år 2: {row['vinst2']}")
                st.write(f"P/E år 1: {row['pe1']}, år 2: {row['pe2']}")
                st.write(f"P/S år 1: {row['ps1']}, år 2: {row['ps2']}")
                st.write(f"Targetkurs P/E: {row['targetkurs_pe']}")
                st.write(f"Targetkurs P/S: {row['targetkurs_ps']}")
                st.write(f"Uppsida P/E: {row['uppsida_pe']}%")
                st.write(f"Uppsida P/S: {row['uppsida_ps']}%")
                st.write(f"Senast ändrad: {row['insatt_datum']}")

    st.header("🗑️ Ta bort bolag")
    namn_lista = df["namn"].tolist()
    if namn_lista:
        valt_bolag = st.selectbox("Välj bolag att ta bort", namn_lista)
        if st.button("Radera bolag"):
            ta_bort_bolag(valt_bolag)
            st.success(f"Bolaget '{valt_bolag}' är borttaget.")
            st.session_state["nysparad"] = True
    else:
        st.info("Inga bolag att ta bort.")

if __name__ == "__main__":
    main()
