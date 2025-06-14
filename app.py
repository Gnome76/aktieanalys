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

def safe_float(x):
    try:
        return float(x)
    except:
        return None

def berakna_targetkurs_pe(pe_list, vinst_nastaar):
    targetkurser = []
    for pe in pe_list:
        if pe is not None and vinst_nastaar is not None:
            targetkurser.append(pe * vinst_nastaar)
    return sum(targetkurser) / len(targetkurser) if targetkurser else None

def berakna_targetkurs_ps(ps_list, omsattning_nastaar):
    targetkurser = []
    for ps in ps_list:
        if ps is not None and omsattning_nastaar is not None:
            targetkurser.append(ps * omsattning_nastaar * 10)  # 10 är en dummy omsättning för beräkning
    return sum(targetkurser) / len(targetkurser) if targetkurser else None

def main():
    st.title("Aktieanalys: Lägg till, redigera, ta bort och visa undervärderade bolag")

    init_db()

    # --- Hämta bolag från DB ---
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

    # --- Lägg till / redigera bolag ---
    st.header("Lägg till eller redigera bolag")

    val_av_bolag = st.selectbox(
        "Välj bolag att redigera (eller tomt för nytt):",
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

        if st.button("Ta bort bolag"):
            ta_bort_bolag(namn)
            st.success(f"Bolag '{namn}' borttaget!")
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

    # --- Uppdatera df efter ev ändringar ---
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

    if df.empty:
        st.info("Inga bolag sparade ännu.")
        return

    # --- Beräkna undervärdering ---
    undervarde_records = []
    for _, row in df.iterrows():
        nuv_kurs = safe_float(row["nuvarande_kurs"])
        vinst_nastaar = safe_float(row["vinst_nastaar"])
        oms_nastaar = safe_float(row["omsattningstillvaxt_nastaar"])
        pe_list = [safe_float(row[c]) for c in ["pe1","pe2","pe3","pe4"]]
        ps_list = [safe_float(row[c]) for c in ["ps1","ps2","ps3","ps4"]]

        target_pe = berakna_targetkurs_pe(pe_list, vinst_nastaar)
        target_ps = berakna_targetkurs_ps(ps_list, oms_nastaar)

        target_list = [t for t in [target_pe, target_ps] if t is not None]
        targetkurs = min(target_list) if target_list else None

        if targetkurs and nuv_kurs:
            undervarde_pct = (targetkurs - nuv_kurs) / targetkurs * 100
        else:
            undervarde_pct = None

        undervarde_records.append({
            "namn": row["namn"],
            "nuvarande_kurs": nuv_kurs,
            "targetkurs_pe": target_pe,
            "targetkurs_ps": target_ps,
            "targetkurs": targetkurs,
            "undervarde_pct": undervarde_pct
        })

    df_undervarde = pd.DataFrame(undervarde_records)
    df_undervarde = df_undervarde.dropna(subset=["undervarde_pct"])

    # --- Filter undervärderade ---
    visa_allt = st.checkbox("Visa alla bolag (annars minst 30 % undervärderade)", value=False)
    if not visa_allt:
        df_undervarde = df_undervarde[df_undervarde["undervarde_pct"] >= 30]

    if df_undervarde.empty:
        st.warning("Inga bolag uppfyller kriterierna.")
        return

    # --- Sortera på undervärdering ---
    df_undervarde = df_undervarde.sort_values(by="undervarde_pct", ascending=False).reset_index(drop=True)

    # --- Bläddra mellan bolag ---
    st.header("Visa undervärderade bolag")
    if "index" not in st.session_state:
        st.session_state.index = 0

    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.button("Föregående"):
            if st.session_state.index > 0:
                st.session_state.index -= 1
    with col3:
        if st.button("Nästa"):
            if st.session_state.index < len(df_undervarde) - 1:
                st.session_state.index += 1

    bolag = df_undervarde.iloc[st.session_state.index]

    st.subheader(f"{bolag['namn']} ({bolag['undervarde_pct']:.1f}% undervärderad)")
    st.write(f"Nuvarande kurs: {bolag['nuvarande_kurs']:.2f} SEK")
    st.write(f"Targetkurs (lägsta av P/E och P/S): {bolag['targetkurs']:.2f} SEK")
    st.write(f"Targetkurs (P/E): {bolag['targetkurs_pe'] if bolag['targetkurs_pe'] else 'N/A'}")
    st.write(f"Targetkurs (P/S): {bolag['targetkurs_ps'] if bolag['targetkurs_ps'] else 'N/A'}")

if __name__ == "__main__":
    main()
