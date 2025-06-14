import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

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
    rows = c.fetchall()
    conn.close()
    kolumner = ["namn","nuvarande_kurs","pe_1","pe_2","pe_3","pe_4",
                "ps_1","ps_2","ps_3","ps_4","vinst_prognos_1","vinst_prognos_2",
                "oms_tillv_1","oms_tillv_2","sparad_tid"]
    df = pd.DataFrame(rows, columns=kolumner)
    return df

def radera_bolag(namn):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn=?", (namn,))
    conn.commit()
    conn.close()

def berakna_targetkurs(df):
    # Medel P/E och P/S
    df["pe_medel"] = df[["pe_1","pe_2","pe_3","pe_4"]].mean(axis=1)
    df["ps_medel"] = df[["ps_1","ps_2","ps_3","ps_4"]].mean(axis=1)

    # Targetkurs p/e = medel P/E * vinst prognos i år
    df["target_pe"] = df["pe_medel"] * df["vinst_prognos_1"]
    # Targetkurs p/s = medel P/S * omsättningstillväxt i år (procent → som faktor) * nuvarande kurs (för rimlighet)
    # Men vi måste räkna ut targetkurs p/s annorlunda, vanligt är omsättning * P/S, men vi har inte omsättning direkt, så vi använder vinst prognos som proxy.
    # För att hålla det enkelt: targetkurs p/s = medel P/S * (1 + omsättningstillväxt i år i dec) * nuvarande kurs (ungefär)
    df["target_ps"] = df["ps_medel"] * (1 + df["oms_tillv_1"] / 100) * df["nuvarande_kurs"]

    # Genomsnitt av target p/e och p/s
    df["target_genomsnitt"] = (df["target_pe"] + df["target_ps"]) / 2

    # Beräkna undervärdering i procent (positivt = undervärderad)
    df["undervardering_pe"] = (df["target_pe"] - df["nuvarande_kurs"]) / df["target_pe"] * 100
    df["undervardering_ps"] = (df["target_ps"] - df["nuvarande_kurs"]) / df["target_ps"] * 100
    df["undervardering_genomsnitt"] = (df["target_genomsnitt"] - df["nuvarande_kurs"]) / df["target_genomsnitt"] * 100

    return df

def visa_bolag_tabell(df):
    # Formatering för snygg display
    if df.empty:
        st.info("Inga bolag sparade.")
        return

    display_df = df.copy()
    display_df = display_df.sort_values("namn")
    display_df["nuvarande_kurs"] = display_df["nuvarande_kurs"].map(lambda x: f"{x:.2f}")
    display_df["target_pe"] = display_df["target_pe"].map(lambda x: f"{x:.2f}")
    display_df["target_ps"] = display_df["target_ps"].map(lambda x: f"{x:.2f}")
    display_df["target_genomsnitt"] = display_df["target_genomsnitt"].map(lambda x: f"{x:.2f}")
    display_df["undervardering_pe"] = display_df["undervardering_pe"].map(lambda x: f"{x:.1f}%")
    display_df["undervardering_ps"] = display_df["undervardering_ps"].map(lambda x: f"{x:.1f}%")
    display_df["undervardering_genomsnitt"] = display_df["undervardering_genomsnitt"].map(lambda x: f"{x:.1f}%")

    cols_to_show = ["namn", "nuvarande_kurs", "target_pe", "undervardering_pe",
                    "target_ps", "undervardering_ps", "target_genomsnitt", "undervardering_genomsnitt"]
    st.dataframe(display_df[cols_to_show], use_container_width=True)

def visa_undervarderade(df):
    df_undervard = df[df["undervardering_genomsnitt"] >= 30].copy()
    if df_undervard.empty:
        st.info("Inga bolag är minst 30% undervärderade.")
        return

    df_undervard = df_undervard.sort_values("undervardering_genomsnitt", ascending=False)

    df_undervard_display = df_undervard.copy()
    df_undervard_display["nuvarande_kurs"] = df_undervard_display["nuvarande_kurs"].map(lambda x: f"{x:.2f}")
    df_undervard_display["target_pe"] = df_undervard_display["target_pe"].map(lambda x: f"{x:.2f}")
    df_undervard_display["target_ps"] = df_undervard_display["target_ps"].map(lambda x: f"{x:.2f}")
    df_undervard_display["target_genomsnitt"] = df_undervard_display["target_genomsnitt"].map(lambda x: f"{x:.2f}")
    df_undervard_display["undervardering_pe"] = df_undervard_display["undervardering_pe"].map(lambda x: f"{x:.1f}%")
    df_undervard_display["undervardering_ps"] = df_undervard_display["undervardering_ps"].map(lambda x: f"{x:.1f}%")
    df_undervard_display["undervardering_genomsnitt"] = df_undervard_display["undervardering_genomsnitt"].map(lambda x: f"{x:.1f}%")

    cols_to_show = ["namn", "nuvarande_kurs", "target_pe", "undervardering_pe",
                    "target_ps", "undervardering_ps", "target_genomsnitt", "undervardering_genomsnitt"]
    st.dataframe(df_undervard_display[cols_to_show], use_container_width=True)

def main():
    st.title("Aktieanalys - Spara & analysera bolag")

    init_db()

    with st.form("nytt_bolag_form"):
        st.subheader("Lägg till nytt bolag")
        namn = st.text_input("Bolagsnamn").strip()
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")
        pe_1 = st.number_input("P/E (år 1)", format="%.2f")
        pe_2 = st.number_input("P/E (år 2)", format="%.2f")
        pe_3 = st.number_input("P/E (år 3)", format="%.2f")
        pe_4 = st.number_input("P/E (år 4)", format="%.2f")
        ps_1 = st.number_input("P/S (år 1)", format="%.2f")
        ps_2 = st.number_input("P/S (år 2)", format="%.2f")
        ps_3 = st.number_input("P/S (år 3)", format="%.2f")
        ps_4 = st.number_input("P/S (år 4)", format="%.2f")
        vinst_prognos_1 = st.number_input("Vinstprognos i år", format="%.2f")
        v
