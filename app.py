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
    st.title("Aktieanalys - Lägg till, redigera och visa undervärderade bolag")

    if "refresh" not in st.session_state:
        st.session_state["refresh"] = False
    if "current_idx" not in st.session_state:
        st.session_state["current_idx"] = 0
    if "visa_endast_undervarde" not in st.session_state:
        st.session_state["visa_endast_undervarde"] = True

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

    st.header("Lägg till nytt bolag eller redigera befintligt")
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
            st.session_state["refresh"] = True
            st.stop()
        if st.button("Ta bort bolag"):
            ta_bort_bolag(namn)
            st.success(f"Bolag '{namn}' borttaget!")
            st.session_state["refresh"] = True
            st.stop()
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
                    st.session_state["refresh"] = True
                    st.stop()

    if df.empty:
        st.info("Inga bolag sparade än.")
        return

    # Beräkna targetkurser
    df["targetkurs_pe"] = df["vinst_nastaar"] * ((df["pe1"] + df["pe2"]) / 2)
    df["targetkurs_ps"] = df["nuvarande_kurs"] / df["ps1"].replace(0, 1)

    df["undervarde_pe"] = (df["targetkurs_pe"] - df["nuvarande_kurs"]) / df["targetkurs_pe"] * 100
    df["undervarde_ps"] = (df["targetkurs_ps"] - df["nuvarande_kurs"]) / df["targetkurs_ps"] * 100
    df["undervarde_min"] = df[["undervarde_pe", "undervarde_ps"]].min(axis=1)

    visa_endast = st.checkbox("Visa endast bolag minst 30% undervärderade", value=st.session_state["visa_endast_undervarde"])
    st.session_state["visa_endast_undervarde"] = visa_endast

    if visa_endast:
        df_undervarde = df[df["undervarde_min"] >= 30].copy().sort_values(by="undervarde_min", ascending=False)
    else:
        df_undervarde = df.sort_values(by="namn")

    if df_undervarde.empty:
        st.warning("Inga undervärderade bolag att visa.")
        return

    idx = st.session_state["current_idx"]
    if idx >= len(df_undervarde):
        idx = 0
        st.session_state["current_idx"] = 0
    if idx < 0:
        idx = len(df_undervarde) - 1
        st.session_state["current_idx"] = idx

    bolag = df_undervarde.iloc[idx]

    st.header(f"Bolag {idx+1} av {len(df_undervarde)}: {bolag['namn']}")

    st.write(f"**Nuvarande kurs:** {bolag['nuvarande_kurs']:.2f} SEK")
    st.write(f"**Targetkurs P/E (år 1-2 medel):** {bolag['targetkurs_pe']:.2f} SEK")
    st.write(f"**Targetkurs P/S (år 1):** {bolag['targetkurs_ps']:.2f} SEK")
    st.write(f"**Undervärdering (min av P/E och P/S):** {bolag['undervarde_min']:.2f} %")

    st.write("---")
    st.write(f"P/E: {bolag['pe1']:.2f}, {bolag['pe2']:.2f}, {bolag['pe3']:.2f}, {bolag['pe4']:.2f}")
    st.write(f"P/S: {bolag['ps1']:.2f}, {bolag['ps2']:.2f}, {bolag['ps3']:.2f}, {bolag['ps4']:.2f}")
    st.write(f"Vinst prognos i år: {bolag['vinst_arsprognos']:.2f}")
    st.write(f"Vinst prognos nästa år: {bolag['vinst_nastaar']:.2f}")
    st.write(f"Omsättningstillväxt i år (%): {bolag['omsattningstillvaxt_arsprognos']:.2f}")
    st.write(f"Omsättningstillväxt nästa år (%): {bolag['omsattningstillvaxt_nastaar']:.2f}")
    st.write(f"Inmatad senast: {bolag['insatt_datum']}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Föregående"):
            st.session_state["current_idx"] = (st.session_state["current_idx"] - 1) % len(df_undervarde)
            st.stop()
    with col2:
        if st.button("Nästa"):
            st.session_state["current_idx"] = (st.session_state["current_idx"] + 1) % len(df_undervarde)
            st.stop()

if __name__ == "__main__":
    main()
