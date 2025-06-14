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
            aktuellt_pe REAL DEFAULT 0,
            aktuellt_ps REAL DEFAULT 0,
            insatt_datum TEXT
        )
    """)
    conn.commit()

    c.execute("PRAGMA table_info(bolag)")
    columns = [info[1] for info in c.fetchall()]
    if "aktuellt_pe" not in columns:
        c.execute("ALTER TABLE bolag ADD COLUMN aktuellt_pe REAL DEFAULT 0")
    if "aktuellt_ps" not in columns:
        c.execute("ALTER TABLE bolag ADD COLUMN aktuellt_ps REAL DEFAULT 0")
    conn.commit()
    conn.close()

def spara_bolag(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

    if "current_idx" not in st.session_state:
        st.session_state["current_idx"] = 0
    if "visa_endast_undervarde" not in st.session_state:
        st.session_state["visa_endast_undervarde"] = True
    if "refresh" not in st.session_state:
        st.session_state["refresh"] = False

    init_db()
    bolag_lista = hamta_alla_bolag()

    if not bolag_lista:
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(bolag_lista, columns=[
            "namn", "nuvarande_kurs",
            "pe1", "pe2", "pe3", "pe4",
            "ps1", "ps2", "ps3", "ps4",
            "vinst_arsprognos", "vinst_nastaar",
            "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
            "aktuellt_pe", "aktuellt_ps",
            "insatt_datum"
        ])

    # Filter checkbox
    visa_filter = st.checkbox("Visa endast undervärderade bolag (minst 30 %)", value=st.session_state["visa_endast_undervarde"])
    st.session_state["visa_endast_undervarde"] = visa_filter

    # Beräkna targetkurser och undervärdering
    def berakna_targetkurs(row):
        try:
            target_pe = row["vinst_nastaar"] * ((row["pe1"] + row["pe2"]) / 2)
            # P/S medel * genomsnittlig omsättningstillväxt * nuvarande kurs
            ps_medel = (row["ps1"] + row["ps2"]) / 2
            omsattningstillvaxt_medel = (row["omsattningstillvaxt_arsprognos"] + row["omsattningstillvaxt_nastaar"]) / 2 / 100  # procent till decimaltal
            target_ps = ps_medel * omsattningstillvaxt_medel * row["nuvarande_kurs"]
            return pd.Series([target_pe, target_ps])
        except Exception:
            return pd.Series([None, None])

    if not df.empty:
        df[["targetkurs_pe", "targetkurs_ps"]] = df.apply(berakna_targetkurs, axis=1)
        # Räkna undervärdering som skillnad mellan target och aktuellt värde
        df["undervarde_pe"] = (df["targetkurs_pe"] - df["nuvarande_kurs"]) / df["nuvarande_kurs"] * 100
        df["undervarde_ps"] = (df["targetkurs_ps"] - df["nuvarande_kurs"]) / df["nuvarande_kurs"] * 100

        if visa_filter:
            # Visa bolag som är minst 30% undervärderade på antingen P/E eller P/S
            df = df[(df["undervarde_pe"] >= 30) | (df["undervarde_ps"] >= 30)]
            df = df.reset_index(drop=True)
        else:
            df = df.reset_index(drop=True)

    st.header("Navigera bland bolag")

    if df.empty:
        st.info("Inga bolag att visa.")
    else:
        idx = st.session_state["current_idx"]
        if idx < 0:
            idx = 0
        if idx >= len(df):
            idx = len(df) - 1
        st.session_state["current_idx"] = idx

        bolag = df.iloc[idx]

        st.subheader(f"Bolag {idx+1} av {len(df)}: {bolag['namn']}")

        # Visa nyckeltal
        st.write(f"**Nuvarande kurs:** {bolag['nuvarande_kurs']:.2f}")
        st.write(f"**Aktuellt P/E:** {bolag['aktuellt_pe']:.2f}")
        st.write(f"**Aktuellt P/S:** {bolag['aktuellt_ps']:.2f}")
        st.write(f"**Targetkurs P/E:** {bolag['targetkurs_pe']:.2f}")
        st.write(f"**Targetkurs P/S:** {bolag['targetkurs_ps']:.2f}")
        st.write(f"**Undervärdering P/E (%):** {bolag['undervarde_pe']:.2f}")
        st.write(f"**Undervärdering P/S (%):** {bolag['undervarde_ps']:.2f}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Föregående"):
                if idx > 0:
                    st.session_state["current_idx"] = idx - 1
                    st.experimental_rerun()
        with col2:
            if st.button("Nästa"):
                if idx < len(df) - 1:
                    st.session_state["current_idx"] = idx + 1
                    st.experimental_rerun()
        with col3:
            if st.button("Uppdatera vy"):
                st.experimental_rerun()

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
        aktuellt_pe = st.number_input("Aktuellt P/E", min_value=0.0, value=float(vald_rad["aktuellt_pe"]), format="%.2f")
        aktuellt_ps = st.number_input("Aktuellt P/S", min_value=0.0, value=float(vald_rad["aktuellt_ps"]), format="%.2f")

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
                aktuellt_pe,
                aktuellt_ps,
                datetime.now().isoformat()
            )
            spara_bolag(data)
            st.success(f"Bolag '{namn}' uppdaterat!")
            st.session_state["refresh"] = True
            st.experimental_rerun()

        if st.button("Ta bort bolag"):
            ta_bort_bolag(namn)
            st.success(f"Bolag '{namn}' borttaget!")
            st.session_state["refresh"] = True
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
            aktuellt_pe = st.number_input("Aktuellt P/E", min_value=0.0, format="%.2f")
            aktuellt_ps = st.number_input("Aktuellt P/S", min_value=0.0, format="%.2f")

            skickaknapp = st.form_submit_button("Lägg till bolag")
            if skickaknapp:
                if namn.strip() == "":
                    st.error("Bolagsnamn kan inte vara tomt.")
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
                        aktuellt_pe,
                        aktuellt_ps,
                        datetime.now().isoformat()
                    )
                    spara_bolag(data)
                    st.success(f"Bolag '{namn}' tillagt!")
                    st.session_state["refresh"] = True
                    st.experimental_rerun()

if __name__ == "__main__":
    main()
