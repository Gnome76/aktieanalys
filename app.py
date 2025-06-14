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
    st.title("Aktieinnehav – Spara, visa och redigera")

    init_db()

    # Hämta alla bolag i en DataFrame
    bolag_lista = hamta_alla_bolag()
    if bolag_lista:
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
        )
    else:
        df = pd.DataFrame(columns=[
            "namn", "nuvarande_kurs",
            "pe1", "pe2", "pe3", "pe4",
            "ps1", "ps2", "ps3", "ps4",
            "vinst_arsprognos", "vinst_nastaar",
            "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
            "insatt_datum"
        ])

    st.header("➕ Lägg till nytt bolag")
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
            elif namn.strip() in df["namn"].values:
                st.error("Bolaget finns redan. Använd redigeringsfunktionen.")
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

    st.header("✏️ Redigera befintligt bolag")
    if not df.empty:
        valt_bolag = st.selectbox("Välj bolag att redigera", df["namn"].tolist())

        if valt_bolag:
            vald_rad = df[df["namn"] == valt_bolag].iloc[0]

            with st.form("form_redigera_bolag"):
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

                spara = st.form_submit_button("Spara ändringar")

                if spara:
                    data = (
                        valt_bolag,
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
                    st.success(f"Bolag '{valt_bolag}' uppdaterat!")
                    st.experimental_rerun()
    else:
        st.info("Inga bolag sparade ännu för att redigera.")

    # Visa bolag sorterat på undervärdering (över 0%), mest undervärderade först
    st.header("Undervärderade bolag (över 0%) - sorterade mest undervärderade först")
    if not df.empty:
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

        # Beräkna max undervärdering av år eller nästa år för sortering
        df_display["max_undervardering"] = df_display[
            ["undervardering_genomsnitt_ars", "undervardering_genomsnitt_nastaar"]
        ].max(axis=1)

        undervarderade = df_display[
            (df_display["max_undervardering"] > 0)
        ].sort_values(by="max_undervardering", ascending=False).reset_index(drop=True)

        if undervarderade.empty:
            st.info("Inga bolag är undervärderade just nu.")
        else:
            for i, bolag in undervarderade.iterrows():
                st.markdown(f"### {bolag['namn']}")
                st.write(f"**Nuvarande kurs:** {bolag['nuvarande_kurs']:.2f} kr")
                tg_ars = bolag['target_genomsnitt_ars']
                tg_nastaar = bolag['target_genomsnitt_nastaar']
                st.write(f"**Targetkurs år:** {tg_ars:.2f} kr" if tg_ars else "**Targetkurs år:** -")
                st.write(f"**Targetkurs nästa år:** {tg_nastaar:.2f} kr" if tg_nastaar else "**Targetkurs nästa år:** -")
                uv_ars = bolag['undervardering_genomsnitt_ars']
                uv_nastaar = bolag['undervardering_genomsnitt_nastaar']
                st.write(f"**Undervärdering i år:** {uv_ars:.0%}" if uv_ars else "**Undervärdering i år:** -")
                st.write(f"**Undervärdering nästa år:** {uv_nastaar:.0%}" if uv_nastaar else "**Undervärdering nästa år:** -")
                st.write(f"**Köpvärd upp till (i år):** {bolag['kopvard_ars']:.2f} kr" if bolag['kopvard_ars'] else "**Köpvärd upp till (i år):** -")
                st.write(f"**Köpvärd upp till (nästa år):** {bolag['kopvard_nastaar']:.2f} kr" if bolag['kopvard_nastaar'] else "**Köpvärd upp till (nästa år):** -")
                st.markdown("---")
    else:
        st.info("Inga bolag sparade ännu.")

    # Ta bort bolag
    st.header("🗑️ Ta bort bolag")
    if not df.empty:
        namn_radera = st.selectbox("Välj bolag att ta bort",
