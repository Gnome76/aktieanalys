import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

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
            omsattningstillvaxt_nastaar REAL,
            insatt_datum TEXT
        )
    """)
    conn.commit()
    conn.close()

def spara_bolag(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

def berakna_target_och_undervarde(df):
    df["pe_target"] = (df["vinst_nastaar"] * ((df["pe1"] + df["pe2"] + df["pe3"] + df["pe4"]) / 4)).round(2)
    df["ps_target"] = (df["vinst_nastaar"] * ((df["ps1"] + df["ps2"] + df["ps3"] + df["ps4"]) / 4)).round(2)
    df["target_snitt"] = ((df["pe_target"] + df["ps_target"]) / 2).round(2)
    df["undervarde_min"] = ((df["target_snitt"] - df["nuvarande_kurs"]) / df["nuvarande_kurs"] * 100).round(2)
    return df

def main():
    st.set_page_config(page_title="Aktieanalys", layout="wide")
    st.title("📊 Aktieanalys med undervärderingsbläddring")
    init_db()

    bolag_lista = hamta_alla_bolag()
    df = pd.DataFrame(bolag_lista, columns=[
        "namn", "nuvarande_kurs",
        "pe1", "pe2", "pe3", "pe4",
        "ps1", "ps2", "ps3", "ps4",
        "vinst_arsprognos", "vinst_nastaar",
        "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
        "insatt_datum"
    ]) if bolag_lista else pd.DataFrame()

    if not df.empty:
        df = berakna_target_och_undervarde(df)

    st.header("➕ Lägg till eller redigera bolag")

    val_av_bolag = st.selectbox(
        "Välj bolag att redigera (eller lämna tomt för nytt):",
        options=[""] + df["namn"].tolist() if not df.empty else [""]
    )

    if val_av_bolag:
        bol = df[df["namn"] == val_av_bolag].iloc[0]
        namn = val_av_bolag
    else:
        bol = None
        namn = st.text_input("Bolagsnamn (unik)")

    nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, value=float(bol["nuvarande_kurs"]) if bol is not None else 0.0)
    pe1 = st.number_input("P/E år 1", value=float(bol["pe1"]) if bol is not None else 0.0)
    pe2 = st.number_input("P/E år 2", value=float(bol["pe2"]) if bol is not None else 0.0)
    pe3 = st.number_input("P/E år 3", value=float(bol["pe3"]) if bol is not None else 0.0)
    pe4 = st.number_input("P/E år 4", value=float(bol["pe4"]) if bol is not None else 0.0)
    ps1 = st.number_input("P/S år 1", value=float(bol["ps1"]) if bol is not None else 0.0)
    ps2 = st.number_input("P/S år 2", value=float(bol["ps2"]) if bol is not None else 0.0)
    ps3 = st.number_input("P/S år 3", value=float(bol["ps3"]) if bol is not None else 0.0)
    ps4 = st.number_input("P/S år 4", value=float(bol["ps4"]) if bol is not None else 0.0)
    vinst_arsprognos = st.number_input("Vinstprognos i år", value=float(bol["vinst_arsprognos"]) if bol is not None else 0.0)
    vinst_nastaar = st.number_input("Vinstprognos nästa år", value=float(bol["vinst_nastaar"]) if bol is not None else 0.0)
    omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt i år (%)", value=float(bol["omsattningstillvaxt_arsprognos"]) if bol is not None else 0.0)
    omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)", value=float(bol["omsattningstillvaxt_nastaar"]) if bol is not None else 0.0)

    if st.button("💾 Spara bolag"):
        if namn.strip() == "":
            st.error("Bolagsnamn krävs.")
        else:
            data = (
                namn.strip(), nuvarande_kurs,
                pe1, pe2, pe3, pe4,
                ps1, ps2, ps3, ps4,
                vinst_arsprognos, vinst_nastaar,
                omsattningstillvaxt_arsprognos, omsattningstillvaxt_nastaar,
                datetime.now().isoformat()
            )
            spara_bolag(data)
            st.success(f"'{namn}' har sparats.")
            st.session_state["refresh"] = True
            st.stop()

    st.header("🗑️ Ta bort bolag")
    if not df.empty:
        namn_att_ta_bort = st.selectbox("Välj bolag att ta bort", options=[""] + df["namn"].tolist())
        if namn_att_ta_bort and st.button(f"❌ Ta bort {namn_att_ta_bort}"):
            ta_bort_bolag(namn_att_ta_bort)
            st.success(f"'{namn_att_ta_bort}' har tagits bort.")
            st.session_state["refresh"] = True
            st.stop()

    st.header("📈 Undervärderade bolag (> 0%)")
    if not df.empty:
        df_undervarde = df[df["undervarde_min"] > 0].sort_values(by="undervarde_min", ascending=False).reset_index(drop=True)

        if not df_undervarde.empty:
            if "index" not in st.session_state or st.session_state["index"] >= len(df_undervarde):
                st.session_state["index"] = 0

            bolag = df_undervarde.iloc[st.session_state["index"]]

            st.subheader(f"🔍 {bolag['namn']}")
            st.write(f"📉 Nuvarande kurs: **{bolag['nuvarande_kurs']} kr**")
            st.write(f"🎯 Targetkurs P/E: **{bolag['pe_target']} kr**")
            st.write(f"🎯 Targetkurs P/S: **{bolag['ps_target']} kr**")
            st.write(f"📊 Snitt-target: **{bolag['target_snitt']} kr**")
            st.write(f"💰 Undervärdering: **{bolag['undervarde_min']} %**")
            st.write(f"📌 Köpvärd om target uppnås: {round(bolag['target_snitt'] * 0.7, 2)} kr")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Föregående") and st.session_state["index"] > 0:
                    st.session_state["index"] -= 1
                    st.experimental_rerun()
            with col2:
                if st.button("➡️ Nästa") and st.session_state["index"] < len(df_undervarde) - 1:
                    st.session_state["index"] += 1
                    st.experimental_rerun()
        else:
            st.info("Inga undervärderade bolag hittades.")
    else:
        st.info("Inga bolag har lagts till ännu.")

if __name__ == "__main__":
    main()
