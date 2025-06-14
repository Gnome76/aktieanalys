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
    st.title("Aktieinnehav - Spara och redigera bolag")

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

    st.header("Redigera befintligt bolag eller lägg till nytt")

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

    # Visa lista över bolag
    st.header("Sparade bolag")
    if not df.empty:
        st.dataframe(df.drop(columns=["insatt_datum"]))
        namn_att_ta_bort = st.selectbox("Välj bolag att ta bort", options=[""] + df["namn"].tolist())
        if namn_att_ta_bort != "":
            if st.button(f"Ta bort '{namn_att_ta_bort}'"):
                ta_bort_bolag(namn_att_ta_bort)
                st.success(f"Bolag '{namn_att_ta_bort}' borttaget!")
    else:
        st.info("Inga bolag sparade ännu.")

    # --------------------
    # Bläddra mellan undervärderade bolag
    st.header("Undervärderade bolag (nuvarande kurs < P/E år 1)")

    # Filtrera undervärderade bolag
    undervard_df = df[df["nuvarande_kurs"] < df["pe1"]] if not df.empty else pd.DataFrame()

    if undervard_df.empty:
        st.info("Inga undervärderade bolag just nu.")
    else:
        if "undervard_index" not in st.session_state:
            st.session_state.undervard_index = 0

        # Knapp för föregående och nästa
        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            if st.button("⬅ Föregående"):
                if st.session_state.undervard_index > 0:
                    st.session_state.undervard_index -= 1
        with col3:
            if st.button("Nästa ➡"):
                if st.session_state.undervard_index < len(undervard_df) - 1:
                    st.session_state.undervard_index += 1

        # Visa valt undervärderat bolag
        current_bolag = undervard_df.iloc[st.session_state.undervard_index]

        st.subheader(f"{current_bolag['namn']} ({st.session_state.undervard_index + 1} av {len(undervard_df)})")
        st.write(f"Nuvarande kurs: {current_bolag['nuvarande_kurs']:.2f}")
        st.write(f"P/E år 1: {current_bolag['pe1']:.2f}")
        st.write(f"P/E år 2: {current_bolag['pe2']:.2f}")
        st.write(f"P/E år 3: {current_bolag['pe3']:.2f}")
        st.write(f"P/E år 4: {current_bolag['pe4']:.2f}")
        st.write(f"P/S år 1: {current_bolag['ps1']:.2f}")
        st.write(f"P/S år 2: {current_bolag['ps2']:.2f}")
        st.write(f"P/S år 3: {current_bolag['ps3']:.2f}")
        st.write(f"P/S år 4: {current_bolag['ps4']:.2f}")
        st.write(f"Vinst prognos i år: {current_bolag['vinst_arsprognos']:.2f}")
        st.write(f"Vinst prognos nästa år: {current_bolag['vinst_nastaar']:.2f}")
        st.write(f"Omsättningstillväxt i år (%): {current_bolag['omsattningstillvaxt_arsprognos']:.2f}")
        st.write(f"Omsättningstillväxt nästa år (%): {current_bolag['omsattningstillvaxt_nastaar']:.2f}")

if __name__ == "__main__":
    main()
