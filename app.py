import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "bolag.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bolag (
            namn TEXT PRIMARY KEY,
            nuvarande_kurs REAL,
            pe_1 REAL,
            pe_2 REAL,
            pe_3 REAL,
            pe_4 REAL,
            ps_1 REAL,
            ps_2 REAL,
            ps_3 REAL,
            ps_4 REAL,
            vinst_prognos_1 REAL,
            vinst_prognos_2 REAL,
            oms_tillv_1 REAL,
            oms_tillv_2 REAL,
            sparad_tid TEXT
        )
    """)
    conn.commit()
    conn.close()

def spara_bolag(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

def hamta_bolag():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM bolag")
    rader = c.fetchall()
    conn.close()
    kolumner = ["namn","nuvarande_kurs","pe_1","pe_2","pe_3","pe_4",
                "ps_1","ps_2","ps_3","ps_4","vinst_prognos_1","vinst_prognos_2",
                "oms_tillv_1","oms_tillv_2","sparad_tid"]
    df = pd.DataFrame(rader, columns=kolumner)
    return df

def radera_bolag(namn):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn=?", (namn,))
    conn.commit()
    conn.close()

def berakna_targetkurs(df):
    if df.empty:
        return df
    df = df.copy()
    df["pe_medel"] = df[["pe_1","pe_2","pe_3","pe_4"]].mean(axis=1)
    df["ps_medel"] = df[["ps_1","ps_2","ps_3","ps_4"]].mean(axis=1)

    df["target_pe"] = df["pe_medel"] * df["vinst_prognos_1"]
    df["target_ps"] = df["ps_medel"] * (1 + df["oms_tillv_1"] / 100) * df["nuvarande_kurs"]

    df["target_genomsnitt"] = (df["target_pe"] + df["target_ps"]) / 2

    df["undervardering_genomsnitt"] = (df["target_genomsnitt"] - df["nuvarande_kurs"]) / df["target_genomsnitt"] * 100
    return df

def main():
    st.title("Aktieanalys - Enkel sparare")

    init_db()

    with st.form("nytt_bolag"):
        namn = st.text_input("Bolagsnamn").strip()
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")
        pe_1 = st.number_input("P/E år 1", format="%.2f")
        pe_2 = st.number_input("P/E år 2", format="%.2f")
        pe_3 = st.number_input("P/E år 3", format="%.2f")
        pe_4 = st.number_input("P/E år 4", format="%.2f")
        ps_1 = st.number_input("P/S år 1", format="%.2f")
        ps_2 = st.number_input("P/S år 2", format="%.2f")
        ps_3 = st.number_input("P/S år 3", format="%.2f")
        ps_4 = st.number_input("P/S år 4", format="%.2f")
        vinst_prognos_1 = st.number_input("Vinstprognos år 1", format="%.2f")
        vinst_prognos_2 = st.number_input("Vinstprognos år 2", format="%.2f")
        oms_tillv_1 = st.number_input("Omsättningstillväxt år 1 (%)", format="%.2f")
        oms_tillv_2 = st.number_input("Omsättningstillväxt år 2 (%)", format="%.2f")

        submit = st.form_submit_button("Spara bolag")

        if submit:
            if namn == "":
                st.warning("Ange ett bolagsnamn!")
            else:
                sparad_tid = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data = (namn, nuvarande_kurs, pe_1, pe_2, pe_3, pe_4,
                        ps_1, ps_2, ps_3, ps_4, vinst_prognos_1, vinst_prognos_2,
                        oms_tillv_1, oms_tillv_2, sparad_tid)
                spara_bolag(data)
                st.success(f"Bolaget {namn} sparat!")
                st.experimental_rerun()

    df = hamta_bolag()
    df = berakna_targetkurs(df)

    st.subheader("Alla bolag")
    if df.empty:
        st.info("Inga bolag sparade.")
    else:
        df_display = df.sort_values("namn")
        for idx, row in df_display.iterrows():
            col1, col2, col3 = st.columns([3,2,1])
            col1.markdown(f"**{row['namn']}**")
            col2.write(f"Kurs: {row['nuvarande_kurs']:.2f} kr")
            col3.button("Ta bort", key=f"radera_{row['namn']}", on_click=radera_bolag, args=(row['namn'],), help="Ta bort detta bolag")
            st.write(f"Targetkurs genomsnitt: {row['target_genomsnitt']:.2f} kr, Undervärdering: {row['undervardering_genomsnitt']:.1f}%")
            st.markdown("---")

    if st.button("Visa endast bolag minst 30% undervärderade"):
        df_undervard = df[df["undervardering_genomsnitt"] >= 30]
        if df_undervard.empty:
            st.info("Inga bolag minst 30% undervärderade.")
        else:
            df_undervard = df_undervard.sort_values("undervardering_genomsnitt", ascending=False)
            st.subheader("Undervärderade bolag (minst 30%)")
            for idx, row in df_undervard.iterrows():
                st.write(f"**{row['namn']}** — Kurs: {row['nuvarande_kurs']:.2f} kr — Target: {row['target_genomsnitt']:.2f} kr — Undervärdering: {row['undervardering_genomsnitt']:.1f}%")
                st.markdown("---")

if __name__ == "__main__":
    main()
