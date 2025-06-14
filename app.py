import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "bolag.db"

# Initiera databasen och skapa tabell om den inte finns
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
            omsattningstillvaxt_nastaar REAL
            -- Notera: datum_inlagd läggs till via migrering
        )
    """)
    conn.commit()
    conn.close()

# Uppgradera befintlig databas med kolumn datum_inlagd om den saknas
def uppgradera_databas_med_datum():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Kolla om kolumnen datum_inlagd finns
    c.execute("PRAGMA table_info(bolag)")
    kolumner = [info[1] for info in c.fetchall()]
    if "datum_inlagd" not in kolumner:
        c.execute("ALTER TABLE bolag ADD COLUMN datum_inlagd TEXT")
        # Sätt dagens datum som standard för befintliga rader
        idag = datetime.today().strftime("%Y-%m-%d")
        c.execute("UPDATE bolag SET datum_inlagd = ?", (idag,))
        conn.commit()

    conn.close()

def spara_bolag(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Kolla om bolaget redan finns för att kunna behålla datum_inlagd
    c.execute("SELECT datum_inlagd FROM bolag WHERE namn = ?", (data[0],))
    rad = c.fetchone()
    if rad:
        datum_inlagd = rad[0]
    else:
        datum_inlagd = datetime.today().strftime("%Y-%m-%d")

    c.execute("""
        INSERT OR REPLACE INTO bolag (
            namn, nuvarande_kurs,
            pe1, pe2, pe3, pe4,
            ps1, ps2, ps3, ps4,
            vinst_arsprognos, vinst_nastaar,
            omsattningstillvaxt_arsprognos, omsattningstillvaxt_nastaar,
            datum_inlagd
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data + (datum_inlagd,))
    conn.commit()
    conn.close()

def hamta_alla_bolag():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT namn, nuvarande_kurs,
               pe1, pe2, pe3, pe4,
               ps1, ps2, ps3, ps4,
               vinst_arsprognos, vinst_nastaar,
               omsattningstillvaxt_arsprognos, omsattningstillvaxt_nastaar,
               datum_inlagd
        FROM bolag
        ORDER BY namn COLLATE NOCASE ASC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def hamta_bolag_sorterat_pa_datum():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT namn, nuvarande_kurs,
               pe1, pe2, pe3, pe4,
               ps1, ps2, ps3, ps4,
               vinst_arsprognos, vinst_nastaar,
               omsattningstillvaxt_arsprognos, omsattningstillvaxt_nastaar,
               datum_inlagd
        FROM bolag
        ORDER BY datum_inlagd ASC, namn COLLATE NOCASE ASC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def ta_bort_bolag(namn):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn = ?", (namn,))
    conn.commit()
    conn.close()

# Beräkna targetkurser och undervärdering
def berakna_targetkurs(pe_vardena, ps_vardena, vinst_arsprognos, vinst_nastaar, nuvarande_kurs):
    genomsnitt_pe = sum(pe_vardena) / len(pe_vardena)
    genomsnitt_ps = sum(ps_vardena) / len(ps_vardena)

    target_pe_ars = genomsnitt_pe * vinst_arsprognos if vinst_arsprognos else None
    target_pe_nastaar = genomsnitt_pe * vinst_nastaar if vinst_nastaar else None
    target_ps_ars = genomsnitt_ps * vinst_arsprognos if vinst_arsprognos else None
    target_ps_nastaar = genomsnitt_ps * vinst_nastaar if vinst_nastaar else None

    target_genomsnitt_ars = None
    target_genomsnitt_nastaar = None
    if target_pe_ars and target_ps_ars:
        target_genomsnitt_ars = (target_pe_ars + target_ps_ars) / 2
    if target_pe_nastaar and target_ps_nastaar:
        target_genomsnitt_nastaar = (target_pe_nastaar + target_ps_nastaar) / 2

    undervardering_genomsnitt_ars = None
    undervardering_genomsnitt_nastaar = None

    if nuvarande_kurs and target_genomsnitt_ars:
        undervardering_genomsnitt_ars = (target_genomsnitt_ars / nuvarande_kurs) - 1
    if nuvarande_kurs and target_genomsnitt_nastaar:
        undervardering_genomsnitt_nastaar = (target_genomsnitt_nastaar / nuvarande_kurs) - 1

    kopvard_ars = target_genomsnitt_ars * 0.7 if target_genomsnitt_ars else None
    kopvard_nastaar = target_genomsnitt_nastaar * 0.7 if target_genomsnitt_nastaar else None

    return {
        "target_genomsnitt_ars": target_genomsnitt_ars,
        "target_genomsnitt_nastaar": target_genomsnitt_nastaar,
        "undervardering_genomsnitt_ars": undervardering_genomsnitt_ars,
        "undervardering_genomsnitt_nastaar": undervardering_genomsnitt_nastaar,
        "kopvard_ars": kopvard_ars,
        "kopvard_nastaar": kopvard_nastaar
    }

def main():
    st.title("Aktieinnehav – Spara och analysera")
    init_db()
    uppgradera_databas_med_datum()

    # Formulär för att lägga till nytt bolag
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
                )
                spara_bolag(data)
                st.success(f"Bolag '{namn}' sparat!")
                # Uppdatera sidan
                st.experimental_rerun()

    bolag = hamta_alla_bolag()
    if bolag:
        df = pd.DataFrame(
            bolag,
            columns=[
                "namn", "nuvarande_kurs",
                "pe1", "pe2", "pe3", "pe4",
                "ps1", "ps2", "ps3", "ps4",
                "vinst_arsprognos", "vinst_nastaar",
                "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
                "datum_inlagd"
            ]
        )

        resultats = []
        for _, row in df.iterrows():
            res = berakna_targetkurs(
                [row.pe1, row.pe2, row.pe3, row.pe4],
                [row.ps1, row.ps2, row.ps3, row.ps4],
                row.vinst_arsprognos,
                row.vinst_nastaar,
                row.nuvarande_kurs,
            )
            resultats.append(res)

        df_target = pd.DataFrame(resultats)
        df_display = pd.concat([df.reset_index(drop=True), df_target], axis=1)

        st.subheader("Undervärderade bolag (≥30%)")
        undervarderade = df_display[
            (df_display["undervardering_genomsnitt_ars"] >= 0.3) |
            (df_display["undervardering_genomsnitt_nastaar"] >= 0.3)
        ].sort_values(
            by=["undervardering_genomsnitt_ars", "undervardering_genomsnitt_nastaar"],
            ascending=False
        ).reset_index(drop=True)

        if undervarderade.empty:
            st.info("Inga bolag är minst 30 % undervärderade just nu.")
        else:
            st.session_state.idx = st.session_state.get("idx", 0)
            total = len(undervarderade)

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("⬅️ Föregående") and st.session_state.idx > 0:
                    st.session_state.idx -= 1
            with col3:
                if st.button("Nästa ➡️") and st.session_state.idx < total - 1:
                    st.session_state.idx += 1

            bolag_visat = undervarderade.iloc[st.session_state.idx]

            st.markdown(f"### {bolag_visat['namn']}")
            st.write(f"**Nuvarande kurs:** {bolag_visat['nuvarande_kurs']:.2f} kr")
            st.write(f"**Targetkurs år:** {bolag_visat['target_genomsnitt_ars']:.2f} kr")
            st.write(f"**Targetkurs nästa år:** {bolag_visat['target_genomsnitt_nastaar']:.2f} kr")
            st.write(f"**Undervärdering i år:** {bolag_visat['undervardering_genomsnitt_ars']:.0%}")
            st.write(f"**Undervärdering nästa år:** {bolag_visat['undervardering_genomsnitt_nastaar']:.0%}")
            st.write(f"**Köpvärd upp till (i år):** {bolag_visat['kopvard_ars']:.2f} kr")
            st.write(f"**Köpvärd upp till (nästa år):** {bolag_visat['kopvard_nastaar']:.2f} kr")
            st.caption(f"Bolag {st.session_state.idx + 1} av {total}")

        # Ta bort bolag
        st.subheader("Ta bort bolag")

        # Hämta bolag sorterade på namn (bokstavsordning)
        bolag_namn = df["namn"].tolist()

        # Hämta bolag sorterade på datum (äldsta först) med datum som sträng
        bolag_datum = hamta_bolag_sorterat_pa_datum()
        df_datum = pd.DataFrame(
            bolag_datum,
            columns=[
                "namn", "nuvarande_kurs",
                "pe1", "pe2", "pe3", "pe4",
                "ps1", "ps2", "ps3", "ps4",
                "vinst_arsprognos", "vinst_nastaar",
                "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
                "datum_inlagd"
            ]
        )

        # Visa två rullistor
        st.write("**Välj bolag att ta bort (bokstavsordning):**")
        namn_radera_alfabet = st.selectbox("Bolag (A-Ö)", options=bolag_namn, key="radera_alfabet")

        st.write("**Välj bolag att ta bort (datumordning):**")
        # Visa både namn och datum i selectboxen, t.ex. "Bolagsnamn (YYYY-MM-DD)"
        namn_datum_list = df_datum.apply(lambda r: f"{r.namn} ({r.datum_inlagd})", axis=1).tolist()
        valt_namn_datum = st.selectbox("Bolag (Äldsta först)", options=namn_datum_list, key="radera_datum")

        # Knappar för borttagning
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("Ta bort valt bolag (bokstavsordning)"):
                ta_bort_bolag(namn_radera_alfabet)
                st.success(f"Bolag '{namn_radera_alfabet}' borttaget.")
                st.experimental_rerun()

        with col_del2:
            if st.button("Ta bort valt bolag (datumordning)"):
                # Extrahera namn från strängen "Bolagsnamn (YYYY-MM-DD)"
                namn_att_ta_bort = valt_namn_datum.split(" (")[0]
                ta_bort_bolag(namn_att_ta_bort)
                st.success(f"Bolag '{namn_att_ta_bort}' borttaget.")
                st.experimental_rerun()

    else:
        st.info("Inga bolag sparade ännu.")

if __name__ == "__main__":
    main()
