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
            pe1 REAL,
            pe2 REAL,
            pe3 REAL,
            pe4 REAL,
            ps1 REAL,
            ps2 REAL,
            ps3 REAL,
            ps4 REAL,
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

def main():
    st.title("Aktieinnehav - Spara, redigera och analysera bolag")

    init_db()

    bolag_lista = hamta_alla_bolag()
    df = pd.DataFrame(
        bolag_lista,
        columns=[
            "namn", "nuvarande_kurs",
            "pe1", "pe2", "pe3", "pe4",
            "ps1", "ps2", "ps3", "ps4",
            "vinst_arsprognos", "vinst_nastaar",
            "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
            "insatt_datum"
        ]
    ) if bolag_lista else pd.DataFrame()

    st.header("Lägg till eller redigera bolag")

    val_av_bolag = st.selectbox(
        "Välj bolag att redigera (eller välj tomt för nytt):",
        options=[""] + (df["namn"].tolist() if not df.empty else [])
    )

    if val_av_bolag:
        vald_rad = df[df["namn"] == val_av_bolag].iloc[0]
        namn = val_av_bolag
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, value=float(vald_rad["nuvarande_kurs"]), format="%.2f")
        pe1 = st.number_input("P/E (år 1)", min_value=0.0, value=float(vald_rad["pe1"]), format="%.2f")
        pe2 = st.number_input("P/E (år 2)", min_value=0.0, value=float(vald_rad["pe2"]), format="%.2f")
        pe3 = st.number_input("P/E (år 3)", min_value=0.0, value=float(vald_rad["pe3"]), format="%.2f")
        pe4 = st.number_input("P/E (år 4)", min_value=0.0, value=float(vald_rad["pe4"]), format="%.2f")
        ps1 = st.number_input("P/S (år 1)", min_value=0.0, value=float(vald_rad["ps1"]), format="%.2f")
        ps2 = st.number_input("P/S (år 2)", min_value=0.0, value=float(vald_rad["ps2"]), format="%.2f")
        ps3 = st.number_input("P/S (år 3)", min_value=0.0, value=float(vald_rad["ps3"]), format="%.2f")
        ps4 = st.number_input("P/S (år 4)", min_value=0.0, value=float(vald_rad["ps4"]), format="%.2f")
        vinst_arsprognos = st.number_input("Vinst prognos i år", value=float(vald_rad["vinst_arsprognos"]), format="%.2f")
        vinst_nastaar = st.number_input("Vinst prognos nästa år", value=float(vald_rad["vinst_nastaar"]), format="%.2f")
        omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt i år (%)", value=float(vald_rad["omsattningstillvaxt_arsprognos"]), format="%.2f")
        omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)", value=float(vald_rad["omsattningstillvaxt_nastaar"]), format="%.2f")

        if st.button("Spara ändringar"):
            data = (
                namn,
                nuvarande_kurs,
                pe1, pe2, pe3, pe4,
                ps1, ps2, ps3, ps4,
                vinst_arsprognos,
                vinst_nastaar,
                omsattningstillvaxt_arsprognos,
                omsattningstillvaxt_nastaar,
                datetime.now().isoformat()
            )
            spara_bolag(data)
            st.success(f"Bolag '{namn}' uppdaterat!")
            st.experimental_rerun()
    else:
        with st.form("form_lagg_till_bolag", clear_on_submit=True):
            namn = st.text_input("Bolagsnamn (unik)")
            nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")
            pe1 = st.number_input("P/E (år 1)", min_value=0.0, format="%.2f")
            pe2 = st.number_input("P/E (år 2)", min_value=0.0, format="%.2f")
            pe3 = st.number_input("P/E (år 3)", min_value=0.0, format="%.2f")
            pe4 = st.number_input("P/E (år 4)", min_value=0.0, format="%.2f")
            ps1 = st.number_input("P/S (år 1)", min_value=0.0, format="%.2f")
            ps2 = st.number_input("P/S (år 2)", min_value=0.0, format="%.2f")
            ps3 = st.number_input("P/S (år 3)", min_value=0.0, format="%.2f")
            ps4 = st.number_input("P/S (år 4)", min_value=0.0, format="%.2f")
            vinst_arsprognos = st.number_input("Vinst prognos i år", format="%.2f")
            vinst_nastaar = st.number_input("Vinst prognos nästa år", format="%.2f")
            omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt i år (%)", format="%.2f")
            omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)", format="%.2f")

            lagg_till = st.form_submit_button("Lägg till bolag")

            if lagg_till:
                if namn.strip() == "":
                    st.error("Bolagsnamn måste anges.")
                else:
                    data = (
                        namn.strip(),
                        nuvarande_kurs,
                        pe1, pe2, pe3, pe4,
                        ps1, ps2, ps3, ps4,
                        vinst_arsprognos,
                        vinst_nastaar,
                        omsattningstillvaxt_arsprognos,
                        omsattningstillvaxt_nastaar,
                        datetime.now().isoformat()
                    )
                    spara_bolag(data)
                    st.success(f"Bolag '{namn}' sparat!")
                    st.experimental_rerun()

    # Beräkna targetkurser och undervärdering
    if not df.empty:
        df["target_pe"] = df["vinst_nastaar"] * df["pe1"]
        df["target_ps"] = df["nuvarande_kurs"] / (df["ps1"] if df["ps1"].all() else 1)
        # Targetkurs baserat på P/S, bättre att räkna omsättning * ps, men saknar omsättningsdata här
        # Vi använder därför P/S på nuvarande kurs som approx. (annars behövs omsättning i DB)

        df["target_ps"] = df["nuvarande_kurs"] * (df["ps1"] if df["ps1"].all() else 1)  # förenklad formel

        # Beräkna undervärdering separat för PE och PS (positiv = undervärderad)
        df["undervarde_pe"] = (df["target_pe"] - df["nuvarande_kurs"]) / df["target_pe"] * 100
        df["undervarde_ps"] = (df["target_ps"] - df["nuvarande_kurs"]) / df["target_ps"] * 100

        # Ta minsta undervärdering (mest konservativ)
        df["undervarde_min"] = df[["undervarde_pe", "undervarde_ps"]].min(axis=1)

        df_undervarde = df[df["undervarde_min"] > 0].copy().sort_values(by="undervarde_min", ascending=False)

        st.header("Undervärderade bolag (>0%) - bläddra mellan dem")

        if df_undervarde.empty:
            st.info("Inga undervärderade bolag just nu.")
        else:
            if "index_undervarde" not in st.session_state:
                st.session_state.index_undervarde = 0

            def prev_bolag():
                if st.session_state.index_undervarde > 0:
                    st.session_state.index_undervarde -= 1

            def next_bolag():
                if st.session_state.index_undervarde < len(df_undervarde) - 1:
                    st.session_state.index_undervarde += 1

            col1, col2, col3 = st.columns([1,6,1])
            with col1:
                st.button("⬅️ Föregående", on_click=prev_bolag)
            with col3:
                st.button("Nästa ➡️", on_click=next_bolag)

            idx = st.session_state.index_undervarde
            rad = df_undervarde.iloc[idx]

            st.subheader(f"{rad['namn']} ({idx+1} av {len(df_undervarde)})")
            st.write(f"Nuvarande kurs: {rad['nuvarande_kurs']:.2f} kr")
            st.write(f"Targetkurs (P/E): {rad['target_pe']:.2f} kr")
            st.write(f"Targetkurs (P/S): {rad['target_ps']:.2f} kr")
            st.write(f"Undervärdering (min av P/E och P/S): {rad['undervarde_min']:.2f} %")
            st.write(f"Undervärdering (P/E): {rad['undervarde_pe']:.2f} %")
            st.write(f"Undervärdering (P/S): {rad['undervarde_ps']:.2f} %")
            st.write(f"P/E år 1: {rad['pe1']:.2f}")
            st.write(f"P/S år 1: {rad['ps1']:.2f}")
            st.write(f"Vinst prognos nästa år: {rad['vinst_nastaar']:.2f}")

    else:
        st.info("Inga bolag sparade ännu.")

    st.header("Ta bort bolag")
    if not df.empty:
        namn_att_ta_bort = st.selectbox("Välj bolag att ta bort", options=[""] + df["namn"].tolist())
        if namn_att_ta_bort != "":
            if st.button(f"Ta bort '{namn_att_ta_bort}'"):
                ta_bort_bolag(namn_att_ta_bort)
                st.success(f"Bolag '{namn_att_ta_bort}' borttaget!")
                st.experimental_rerun()
    else:
        st.info("Inga bolag att ta bort.")

if __name__ == "__main__":
    main()
