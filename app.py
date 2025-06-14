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

def berakna_target(df):
    df["pe_snitt"] = df[["pe1", "pe2", "pe3", "pe4"]].mean(axis=1)
    df["ps_snitt"] = df[["ps1", "ps2", "ps3", "ps4"]].mean(axis=1)
    df["target_pe"] = df["vinst_nastaar"] * df["pe_snitt"]
    df["target_ps"] = df["ps_snitt"] * df["vinst_nastaar"]  # Antag omsättning ≈ vinst för enkelhet
    df["target_genomsnitt"] = (df["target_pe"] + df["target_ps"]) / 2
    df["undervarde_min"] = ((df["target_genomsnitt"] - df["nuvarande_kurs"]) / df["nuvarande_kurs"]) * 100
    return df

def main():
    st.set_page_config(page_title="Aktieanalys", layout="centered")
    st.title("📈 Aktieinnehav & Analys")
    init_db()

    bolag_lista = hamta_alla_bolag()
    df = pd.DataFrame(bolag_lista, columns=[
        "namn", "nuvarande_kurs", "pe1", "pe2", "pe3", "pe4",
        "ps1", "ps2", "ps3", "ps4",
        "vinst_arsprognos", "vinst_nastaar",
        "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
        "insatt_datum"
    ])

    st.header("Lägg till eller redigera bolag")
    val = st.selectbox("Välj bolag att redigera:", [""] + df["namn"].tolist())

    if val:
        bolag = df[df["namn"] == val].iloc[0]
        namn = val
        nuvarande_kurs = st.number_input("Nuvarande kurs", value=float(bolag["nuvarande_kurs"]))
        pe1 = st.number_input("P/E år 1", value=float(bolag["pe1"]))
        pe2 = st.number_input("P/E år 2", value=float(bolag["pe2"]))
        pe3 = st.number_input("P/E år 3", value=float(bolag["pe3"]))
        pe4 = st.number_input("P/E år 4", value=float(bolag["pe4"]))
        ps1 = st.number_input("P/S år 1", value=float(bolag["ps1"]))
        ps2 = st.number_input("P/S år 2", value=float(bolag["ps2"]))
        ps3 = st.number_input("P/S år 3", value=float(bolag["ps3"]))
        ps4 = st.number_input("P/S år 4", value=float(bolag["ps4"]))
        vinst_arsprognos = st.number_input("Vinst prognos i år", value=float(bolag["vinst_arsprognos"]))
        vinst_nastaar = st.number_input("Vinst nästa år", value=float(bolag["vinst_nastaar"]))
        oms_i_ar = st.number_input("Omsättningstillväxt i år", value=float(bolag["omsattningstillvaxt_arsprognos"]))
        oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år", value=float(bolag["omsattningstillvaxt_nastaar"]))

        if st.button("💾 Spara ändringar"):
            spara_bolag((
                namn, nuvarande_kurs, pe1, pe2, pe3, pe4,
                ps1, ps2, ps3, ps4,
                vinst_arsprognos, vinst_nastaar,
                oms_i_ar, oms_nasta_ar,
                datetime.now().isoformat()
            ))
            st.success(f"{namn} sparades.")
            st.session_state["refresh"] = True
            st.stop()
    else:
        with st.form("nytt_bolag"):
            namn = st.text_input("Bolagsnamn (unik)")
            nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0)
            pe1 = st.number_input("P/E år 1", min_value=0.0)
            pe2 = st.number_input("P/E år 2", min_value=0.0)
            pe3 = st.number_input("P/E år 3", min_value=0.0)
            pe4 = st.number_input("P/E år 4", min_value=0.0)
            ps1 = st.number_input("P/S år 1", min_value=0.0)
            ps2 = st.number_input("P/S år 2", min_value=0.0)
            ps3 = st.number_input("P/S år 3", min_value=0.0)
            ps4 = st.number_input("P/S år 4", min_value=0.0)
            vinst_arsprognos = st.number_input("Vinst i år", min_value=0.0)
            vinst_nastaar = st.number_input("Vinst nästa år", min_value=0.0)
            oms_i_ar = st.number_input("Omsättningstillväxt i år (%)", value=0.0)
            oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år (%)", value=0.0)

            if st.form_submit_button("➕ Lägg till bolag"):
                if namn.strip() == "":
                    st.error("Namn måste anges.")
                else:
                    spara_bolag((
                        namn.strip(), nuvarande_kurs, pe1, pe2, pe3, pe4,
                        ps1, ps2, ps3, ps4,
                        vinst_arsprognos, vinst_nastaar,
                        oms_i_ar, oms_nasta_ar,
                        datetime.now().isoformat()
                    ))
                    st.success(f"{namn} tillagt!")
                    st.session_state["refresh"] = True
                    st.stop()

    if not df.empty:
        df = berakna_target(df)
        df_undervarde = df[df["undervarde_min"] > 0].sort_values(by="undervarde_min", ascending=False).reset_index(drop=True)

        st.header("📉 Undervärderade bolag")
        if not df_undervarde.empty:
            if "bolag_index" not in st.session_state:
                st.session_state["bolag_index"] = 0

            antal = len(df_undervarde)
            i = st.session_state["bolag_index"]

            valt = df_undervarde.iloc[i]

            st.subheader(f"{valt['namn']} ({i+1} av {antal})")
            st.write(f"📌 **Nuvarande kurs:** {valt['nuvarande_kurs']:.2f} kr")
            st.write(f"🎯 **Targetkurs P/E:** {valt['target_pe']:.2f} kr")
            st.write(f"🎯 **Targetkurs P/S:** {valt['target_ps']:.2f} kr")
            st.write(f"🎯 **Genomsnittlig target:** {valt['target_genomsnitt']:.2f} kr")
            st.write(f"📉 **Undervärdering:** {valt['undervarde_min']:.1f}%")
            if valt["undervarde_min"] > 30:
                st.success("✅ Över 30 % undervärderad!")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ Föregående", disabled=i == 0):
                    st.session_state["bolag_index"] -= 1
                    st.stop()
            with col2:
                if st.button("➡️ Nästa", disabled=i == antal - 1):
                    st.session_state["bolag_index"] += 1
                    st.stop()

        else:
            st.info("Inga undervärderade bolag hittades.")

        st.header("🗑️ Ta bort bolag")
        namn_att_ta_bort = st.selectbox("Välj bolag att ta bort", options=[""] + df["namn"].tolist())
        if namn_att_ta_bort:
            if st.button(f"Ta bort '{namn_att_ta_bort}'"):
                ta_bort_bolag(namn_att_ta_bort)
                st.success(f"{namn_att_ta_bort} borttaget!")
                st.session_state["refresh"] = True
                st.stop()
    else:
        st.info("Inga bolag tillagda än.")

if __name__ == "__main__":
    main()
