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
            vinst_arsprognos REAL, vinst_nastaar REAL,
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
    c.execute("INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
    conn.commit()
    conn.close()

def hamta_alla_bolag():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM bolag", conn)
    conn.close()
    return df

def ta_bort_bolag(namn):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn = ?", (namn,))
    conn.commit()
    conn.close()

def berakna_vardering(df):
    df["pe_snitt"] = df[["pe1", "pe2", "pe3", "pe4"]].mean(axis=1)
    df["ps_snitt"] = df[["ps1", "ps2", "ps3", "ps4"]].mean(axis=1)
    df["target_pe"] = df["pe_snitt"] * df["vinst_nastaar"]
    df["target_ps"] = df["ps_snitt"] * df["vinst_nastaar"]  # Antag omsättning ≈ vinst
    df["target_genomsnitt"] = (df["target_pe"] + df["target_ps"]) / 2
    df["undervarde_min"] = ((df["target_genomsnitt"] - df["nuvarande_kurs"]) / df["nuvarande_kurs"]) * 100
    return df

def main():
    st.set_page_config(page_title="Aktieanalys", layout="centered")
    st.title("📊 Aktieanalys & Undervärdering")
    init_db()

    df = hamta_alla_bolag()
    if not df.empty:
        df = berakna_vardering(df)

    st.header("➕ Lägg till / Redigera bolag")
    medval = st.selectbox("Välj bolag att redigera", [""] + df["namn"].tolist() if not df.empty else [""])

    if medval:
        valt = df[df["namn"] == medval].iloc[0]
        namn = valt["namn"]
        nuvarande_kurs = st.number_input("Nuvarande kurs", value=float(valt["nuvarande_kurs"]))
        pe = [st.number_input(f"P/E år {i+1}", value=float(valt[f"pe{i+1}"])) for i in range(4)]
        ps = [st.number_input(f"P/S år {i+1}", value=float(valt[f"ps{i+1}"])) for i in range(4)]
        vinst_arsprognos = st.number_input("Vinst prognos i år", value=float(valt["vinst_arsprognos"]))
        vinst_nastaar = st.number_input("Vinst nästa år", value=float(valt["vinst_nastaar"]))
        oms_i_ar = st.number_input("Omsättningstillväxt i år (%)", value=float(valt["omsattningstillvaxt_arsprognos"]))
        oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år (%)", value=float(valt["omsattningstillvaxt_nastaar"]))

        if st.button("💾 Spara ändringar"):
            spara_bolag((
                namn, nuvarande_kurs, *pe, *ps,
                vinst_arsprognos, vinst_nastaar,
                oms_i_ar, oms_nasta_ar,
                datetime.now().isoformat()
            ))
            st.success(f"{namn} uppdaterat.")
            st.session_state["refresh"] = True
            st.stop()
    else:
        with st.form("nytt_bolag"):
            namn = st.text_input("Bolagsnamn")
            nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0)
            pe = [st.number_input(f"P/E år {i+1}", min_value=0.0) for i in range(4)]
            ps = [st.number_input(f"P/S år {i+1}", min_value=0.0) for i in range(4)]
            vinst_arsprognos = st.number_input("Vinst prognos i år", min_value=0.0)
            vinst_nastaar = st.number_input("Vinst nästa år", min_value=0.0)
            oms_i_ar = st.number_input("Omsättningstillväxt i år (%)", value=0.0)
            oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år (%)", value=0.0)

            if st.form_submit_button("➕ Lägg till"):
                if namn.strip():
                    spara_bolag((
                        namn.strip(), nuvarande_kurs, *pe, *ps,
                        vinst_arsprognos, vinst_nastaar,
                        oms_i_ar, oms_nasta_ar,
                        datetime.now().isoformat()
                    ))
                    st.success(f"{namn} tillagt.")
                    st.session_state["refresh"] = True
                    st.stop()
                else:
                    st.error("Bolagsnamn krävs.")

    if not df.empty:
        st.header("📉 Undervärderade bolag")

        df_undervarde = df[df["undervarde_min"] > 0].sort_values(by="undervarde_min", ascending=False).reset_index(drop=True)
        if not df_undervarde.empty:
            if "index" not in st.session_state:
                st.session_state["index"] = 0

            antal = len(df_undervarde)
            idx = st.session_state["index"]
            bolag = df_undervarde.iloc[idx]

            st.subheader(f"{bolag['namn']} ({idx+1} av {antal})")
            st.metric("Nuvarande kurs", f"{bolag['nuvarande_kurs']:.2f} kr")
            st.metric("Targetkurs P/E", f"{bolag['target_pe']:.2f} kr")
            st.metric("Targetkurs P/S", f"{bolag['target_ps']:.2f} kr")
            st.metric("Genomsnittlig targetkurs", f"{bolag['target_genomsnitt']:.2f} kr")
            st.metric("Undervärdering", f"{bolag['undervarde_min']:.1f} %")
            if bolag["undervarde_min"] > 30:
                st.success("✅ Bolaget är över 30 % undervärderat!")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Föregående", disabled=idx == 0):
                    st.session_state["index"] -= 1
                    st.stop()
            with col2:
                if st.button("➡️ Nästa", disabled=idx == antal - 1):
                    st.session_state["index"] += 1
                    st.stop()
        else:
            st.info("Inga undervärderade bolag hittades.")

        st.header("🗑️ Ta bort bolag")
        val = st.selectbox("Välj bolag", [""] + df["namn"].tolist())
        if val and st.button(f"Ta bort '{val}'"):
            ta_bort_bolag(val)
            st.success(f"{val} borttaget.")
            st.session_state["refresh"] = True
            st.stop()
    else:
        st.info("Inga bolag i databasen ännu.")

if __name__ == "__main__":
    main()
