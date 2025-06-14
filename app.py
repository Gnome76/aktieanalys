import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

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

def berakna_targetkurs(pe, ps, vinst_ars, vinst_nastaar, kurs):
    # Kontrollera att vi har giltiga värden
    def medelvärde(lst):
        lst = [v for v in lst if v and v > 0]
        return sum(lst)/len(lst) if lst else None

    gen_pe = medelvärde(pe)
    gen_ps = medelvärde(ps)

    target_pe_ars = gen_pe * vinst_ars if gen_pe and vinst_ars else None
    target_pe_nastaar = gen_pe * vinst_nastaar if gen_pe and vinst_nastaar else None
    target_ps_ars = gen_ps * vinst_ars if gen_ps and vinst_ars else None
    target_ps_nastaar = gen_ps * vinst_nastaar if gen_ps and vinst_nastaar else None

    target_ars = None
    target_nastaar = None
    if target_pe_ars and target_ps_ars:
        target_ars = (target_pe_ars + target_ps_ars) / 2
    elif target_pe_ars:
        target_ars = target_pe_ars
    elif target_ps_ars:
        target_ars = target_ps_ars

    if target_pe_nastaar and target_ps_nastaar:
        target_nastaar = (target_pe_nastaar + target_ps_nastaar) / 2
    elif target_pe_nastaar:
        target_nastaar = target_pe_nastaar
    elif target_ps_nastaar:
        target_nastaar = target_ps_nastaar

    undervard_ars = (target_ars / kurs - 1) if target_ars and kurs else None
    undervard_nastaar = (target_nastaar / kurs -1) if target_nastaar and kurs else None

    kopvard_ars = target_ars * 0.7 if target_ars else None
    kopvard_nastaar = target_nastaar * 0.7 if target_nastaar else None

    return {
        "target_ars": target_ars,
        "target_nastaar": target_nastaar,
        "undervard_ars": undervard_ars,
        "undervard_nastaar": undervard_nastaar,
        "kopvard_ars": kopvard_ars,
        "kopvard_nastaar": kopvard_nastaar,
    }

def main():
    st.title("Aktieanalysapp med SQLite")

    init_db()

    # Initiera index i session_state för navigering
    if "index" not in st.session_state:
        st.session_state.index = 0

    # --- Form för att lägga till bolag ---
    with st.form("add_form", clear_on_submit=True):
        st.subheader("Lägg till / uppdatera bolag")

        namn = st.text_input("Bolagsnamn")
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")
        pe1 = st.number_input("P/E år 1", min_value=0.0, format="%.2f")
        pe2 = st.number_input("P/E år 2", min_value=0.0, format="%.2f")
        pe3 = st.number_input("P/E år 3", min_value=0.0, format="%.2f")
        pe4 = st.number_input("P/E år 4", min_value=0.0, format="%.2f")
        ps1 = st.number_input("P/S år 1", min_value=0.0, format="%.2f")
        ps2 = st.number_input("P/S år 2", min_value=0.0, format="%.2f")
        ps3 = st.number_input("P/S år 3", min_value=0.0, format="%.2f")
        ps4 = st.number_input("P/S år 4", min_value=0.0, format="%.2f")
        vinst_arsprognos = st.number_input("Vinst prognos i år", format="%.2f")
        vinst_nastaar = st.number_input("Vinst prognos nästa år", format="%.2f")
        oms_ars = st.number_input("Omsättningstillväxt i år (%)", format="%.2f")
        oms_nasta = st.number_input("Omsättningstillväxt nästa år (%)", format="%.2f")

        submit = st.form_submit_button("Spara bolag")

        if submit:
            if not namn.strip():
                st.error("Ange bolagsnamn!")
            else:
                data = (
                    namn.strip(),
                    nuvarande_kurs,
                    pe1, pe2, pe3, pe4,
                    ps1, ps2, ps3, ps4,
                    vinst_arsprognos,
                    vinst_nastaar,
                    oms_ars,
                    oms_nasta,
                    datetime.now().isoformat()
                )
                spara_bolag(data)
                st.success(f"Bolag '{namn}' sparat!")
                # Rensa fält via rerun (clear_on_submit=True rensar automatiskt num_inputs)

    # --- Ta bort bolag ---
    st.subheader("Ta bort bolag")
    alla_bolag = hamta_alla_bolag()
    namn_lista = [b[0] for b in alla_bolag]

    if namn_lista:
        ta_bort = st.selectbox("Välj bolag att ta bort", namn_lista)
        if st.button("Ta bort valt bolag"):
            ta_bort_bolag(ta_bort)
            st.success(f"Bolag '{ta_bort}' borttaget!")
            st.session_state.index = 0  # reset index

    else:
        st.info("Inga bolag sparade än.")

    # --- Visa undervärderade bolag ---
    st.subheader("Visa undervärderade bolag (≥30%)")

    if alla_bolag:
        df = pd.DataFrame(
            alla_bolag,
            columns=[
                "namn", "nuvarande_kurs",
                "pe1", "pe2", "pe3", "pe4",
                "ps1", "ps2", "ps3", "ps4",
                "vinst_arsprognos", "vinst_nastaar",
                "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
                "insatt_datum"
            ]
        )

        berakningar = []
        for _, row in df.iterrows():
            res = berakna_targetkurs(
                [row.pe1, row.pe2, row.pe3, row.pe4],
                [row.ps1, row.ps2, row.ps3, row.ps4],
                row.vinst_arsprognos,
                row.vinst_nastaar,
                row.nuvarande_kurs
            )
            berakningar.append(res)

        df_beraknad = pd.DataFrame(berakningar)
        df = pd.concat([df.reset_index(drop=True), df_beraknad], axis=1)

        undervard = df[
            ((df.undervard_ars >= 0.3) | (df.undervard_nastaar >= 0.3))
        ].reset_index(drop=True)

        if undervard.empty:
            st.info("Inga bolag är minst 30% undervärderade just nu.")
            return

        # Navigation
        col1, col2, col3 = st.columns([1,3,1])
        with col1:
            if st.button("⬅️ Föregående"):
                if st.session_state.index > 0:
                    st.session_state.index -= 1
        with col3:
            if st.button("Nästa ➡️"):
                if st.session_state.index < len(undervard)-1:
                    st.session_state.index += 1

        bolag = undervard.iloc[st.session_state.index]

        st.markdown(f"## {bolag.namn}")
        st.write(f"Nuvarande kurs: **{bolag.nuvarande_kurs:.2f}**")
        st.write(f"Targetkurs år 1 (genomsnitt P/E & P/S): **{bolag.target_ars:.2f}**")
        st.write(f"Targetkurs år 2 (genomsnitt P/E & P/S): **{bolag.target_nastaar:.2f}**")
        st.write(f"Undervärdering år 1: **{bolag.undervard_ars:.1%}**")
        st.write(f"Undervärdering år 2: **{bolag.undervard_nastaar:.1%}**")
        st.write(f"Köpvärd år 1 (70% av target): **{bolag.kopvard_ars:.2f}**")
        st.write(f"Köpvärd år 2 (70% av target): **{bolag.kopvard_nastaar:.2f}**")

    else:
        st.info("Inga bolag sparade än.")

if __name__ == "__main__":
    main()
