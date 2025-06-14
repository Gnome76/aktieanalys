import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

DB_PATH = "aktieanalys.db"

# --- Databasfunktioner ---

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS bolag (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        namn TEXT UNIQUE,
        kurs REAL,
        vinst_nastaar REAL,
        pe1 REAL,
        pe2 REAL,
        ps1 REAL,
        ps2 REAL,
        omsattningstillvaxt1 REAL,
        omsattningstillvaxt2 REAL,
        aktuellt_pe REAL,
        aktuellt_ps REAL,
        insatt_datum TEXT,
        senast_andrad TEXT
    )
    ''')
    conn.commit()
    conn.close()

def hamta_alla_bolag():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM bolag ORDER BY namn')
    rows = c.fetchall()
    conn.close()
    columns = ['id','namn','kurs','vinst_nastaar','pe1','pe2','ps1','ps2','omsattningstillvaxt1','omsattningstillvaxt2','aktuellt_pe','aktuellt_ps','insatt_datum','senast_andrad']
    df = pd.DataFrame(rows, columns=columns)
    return df

def lagg_till_eller_uppdatera_bolag(namn, kurs, vinst_nastaar, pe1, pe2, ps1, ps2, oms1, oms2, aktuellt_pe, aktuellt_ps):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM bolag WHERE namn=?', (namn,))
    res = c.fetchone()
    if res:
        # Uppdatera befintligt bolag, uppdatera insatt_datum vid redigering
        c.execute('''
            UPDATE bolag SET kurs=?, vinst_nastaar=?, pe1=?, pe2=?, ps1=?, ps2=?, omsattningstillvaxt1=?, omsattningstillvaxt2=?,
            aktuellt_pe=?, aktuellt_ps=?, insatt_datum=?, senast_andrad=?
            WHERE namn=?
        ''', (kurs, vinst_nastaar, pe1, pe2, ps1, ps2, oms1, oms2, aktuellt_pe, aktuellt_ps, now, now, namn))
    else:
        # Nytt bolag
        c.execute('''
            INSERT INTO bolag (namn,kurs,vinst_nastaar,pe1,pe2,ps1,ps2,omsattningstillvaxt1,omsattningstillvaxt2,aktuellt_pe,aktuellt_ps,insatt_datum,senast_andrad)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (namn,kurs,vinst_nastaar,pe1,pe2,ps1,ps2,oms1,oms2,aktuellt_pe,aktuellt_ps,now,now))
    conn.commit()
    conn.close()

def ta_bort_bolag(namn):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM bolag WHERE namn=?', (namn,))
    conn.commit()
    conn.close()

# --- Targetkursberäkning ---

def berakna_targetkurs_pe(vinst_nastaar, pe1, pe2):
    if vinst_nastaar is None or pe1 is None or pe2 is None:
        return None
    return vinst_nastaar * ((pe1 + pe2) / 2)

def berakna_targetkurs_ps(ps1, ps2, oms1, oms2, kurs):
    # enligt önskemål: medelvärde av ps1 och ps2 * medelvärde av omsättningstillväxt1 och 2 * kurs
    if None in (ps1, ps2, oms1, oms2, kurs):
        return None
    medel_ps = (ps1 + ps2) / 2
    medel_oms = (oms1 + oms2) / 2
    return medel_ps * medel_oms * kurs

# --- UI och applogik ---

def main():
    st.title("Aktieanalysapp")

    # Initiera session_state-variabler
    if "current_idx" not in st.session_state:
        st.session_state["current_idx"] = 0
    if "visa_endast_undervarde" not in st.session_state:
        st.session_state["visa_endast_undervarde"] = True
    if "refresh" not in st.session_state:
        st.session_state["refresh"] = False

    # Hantera refresh-flagga för att ersätta st.experimental_rerun
    if st.session_state["refresh"]:
        st.session_state["refresh"] = False
        st.stop()

    init_db()
    df = hamta_alla_bolag()

    # Filtera enligt checkbox
    st.checkbox("Visa endast minst 30% undervärderade bolag", value=st.session_state["visa_endast_undervarde"], key="visa_endast_undervarde")
    if st.session_state["visa_endast_undervarde"]:
        # Undervärderade: targetkurs_pe > kurs * 1.3 eller targetkurs_ps > kurs * 1.3 (minst 30% undervärderade)
        df["target_pe"] = df.apply(lambda r: berakna_targetkurs_pe(r["vinst_nastaar"], r["pe1"], r["pe2"]), axis=1)
        df["target_ps"] = df.apply(lambda r: berakna_targetkurs_ps(r["ps1"], r["ps2"], r["omsattningstillvaxt1"], r["omsattningstillvaxt2"], r["kurs"]), axis=1)
        df = df[
            ((df["target_pe"] > df["kurs"] * 1.3) | (df["target_ps"] > df["kurs"] * 1.3))
            & df["kurs"].notnull()
        ]
        df = df.reset_index(drop=True)

    if df.empty:
        st.warning("Inga bolag att visa.")
        return

    # Indexbegränsning
    if st.session_state["current_idx"] >= len(df):
        st.session_state["current_idx"] = 0

    current = df.iloc[st.session_state["current_idx"]]

    # Visa bolagsinfo
    st.subheader(f"{current['namn']}")
    st.write(f"Kurs: {current['kurs']}")
    st.write(f"Vinst näst år: {current['vinst_nastaar']}")
    st.write(f"P/E år 1: {current['pe1']}, P/E år 2: {current['pe2']}")
    st.write(f"P/S år 1: {current['ps1']}, P/S år 2: {current['ps2']}")
    st.write(f"Omsättningstillväxt år 1: {current['omsattningstillvaxt1']}, år 2: {current['omsattningstillvaxt2']}")
    st.write(f"Aktuellt P/E: {current['aktuellt_pe']}")
    st.write(f"Aktuellt P/S: {current['aktuellt_ps']}")
    st.write(f"Insatt: {current['insatt_datum']}")
    st.write(f"Senast ändrad: {current['senast_andrad']}")

    target_pe = berakna_targetkurs_pe(current["vinst_nastaar"], current["pe1"], current["pe2"])
    target_ps = berakna_targetkurs_ps(current["ps1"], current["ps2"], current["omsattningstillvaxt1"], current["omsattningstillvaxt2"], current["kurs"])
    st.write(f"Targetkurs (P/E): {target_pe if target_pe is not None else 'N/A'}")
    st.write(f"Targetkurs (P/S): {target_ps if target_ps is not None else 'N/A'}")

    # Navigering
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Föregående"):
            if st.session_state["current_idx"] > 0:
                st.session_state["current_idx"] -= 1
                st.session_state["refresh"] = True
                st.stop()
    with col2:
        if st.button("Nästa"):
            if st.session_state["current_idx"] < len(df) - 1:
                st.session_state["current_idx"] += 1
                st.session_state["refresh"] = True
                st.stop()

    st.markdown("---")

    # Formulär för att lägga till / uppdatera bolag
    with st.form("lagg_till_form"):
        st.subheader("Lägg till / Uppdatera bolag")

        namn = st.text_input("Namn", value=current["namn"] if current is not None else "")
        kurs = st.number_input("Kurs", value=float(current["kurs"]) if current["kurs"] is not None else 0.0, format="%.2f")
        vinst_nastaar = st.number_input("Vinst näst år", value=float(current["vinst_nastaar"]) if current["vinst_nastaar"] is not None else 0.0, format="%.2f")
        pe1 = st.number_input("P/E år 1", value=float(current["pe1"]) if current["pe1"] is not None else 0.0, format="%.2f")
        pe2 = st.number_input("P/E år 2", value=float(current["pe2"]) if current["pe2"] is not None else 0.0, format="%.2f")
        ps1 = st.number_input("P/S år 1", value=float(current["ps1"]) if current["ps1"] is not None else 0.0, format="%.2f")
        ps2 = st.number_input("P/S år 2", value=float(current["ps2"]) if current["ps2"] is not None else 0.0, format="%.2f")
        oms1 = st.number_input("Omsättningstillväxt år 1", value=float(current["omsattningstillvaxt1"]) if current["omsattningstillvaxt1"] is not None else 0.0, format="%.2f")
        oms2 = st.number_input("Omsättningstillväxt år 2", value=float(current["omsattningstillvaxt2"]) if current["omsattningstillvaxt2"] is not None else 0.0, format="%.2f")
        aktuellt_pe = st.number_input("Aktuellt P/E", value=float(current["aktuellt_pe"]) if current["aktuellt_pe"] is not None else 0.0, format="%.2f")
        aktuellt_ps = st.number_input("Aktuellt P/S", value=float(current["aktuellt_ps"]) if current["aktuellt_ps"] is not None else 0.0, format="%.2f")

        submit = st.form_submit_button("Spara")

        if submit:
            if not namn.strip():
                st.error("Namn måste anges!")
            else:
                lagg_till_eller_uppdatera_bolag(
                    namn.strip(),
                    kurs,
                    vinst_nastaar,
                    pe1,
                    pe2,
                    ps1,
                    ps2,
                    oms1,
                    oms2,
                    aktuellt_pe,
                    aktuellt_ps
                )
                st.success(f"Bolaget '{namn}' sparat/uppdaterat.")
                st.session_state["refresh"] = True
                st.stop()

    st.markdown("---")

    # Ta bort bolag
    with st.form("tabort_form"):
        st.subheader("Ta bort bolag")
        namn_ta_bort = st.text_input("Namn på bolag att ta bort")
        ta_bort_knapp = st.form_submit_button("Ta bort")
        if ta_bort_knapp:
            if not namn_ta_bort.strip():
                st.error("Ange ett bolagsnamn att ta bort!")
            else:
                ta_bort_bolag(namn_ta_bort.strip())
                st.success(f"Bolaget '{namn_ta_bort}' borttaget.")
                st.session_state["refresh"] = True
                st.stop()

if __name__ == "__main__":
    main()
