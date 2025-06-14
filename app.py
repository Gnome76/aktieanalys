import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "bolag.db"

# Initiera databasen
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bolag (
            namn TEXT PRIMARY KEY,
            nuvarande_kurs REAL,
            pe1 REAL, pe2 REAL, pe3 REAL, pe4 REAL,
            ps1 REAL, ps2 REAL, ps3 REAL, ps4 REAL,
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
    genomsnitt_pe = sum(pe) / len(pe)
    genomsnitt_ps = sum(ps) / len(ps)

    target_pe_ars = genomsnitt_pe * vinst_ars if vinst_ars else None
    target_pe_nastaar = genomsnitt_pe * vinst_nastaar if vinst_nastaar else None
    target_ps_ars = genomsnitt_ps * vinst_ars if vinst_ars else None
    target_ps_nastaar = genomsnitt_ps * vinst_nastaar if vinst_nastaar else None

    target_genomsnitt_ars = ((target_pe_ars + target_ps_ars) / 2) if target_pe_ars and target_ps_ars else None
    target_genomsnitt_nastaar = ((target_pe_nastaar + target_ps_nastaar) / 2) if target_pe_nastaar and target_ps_nastaar else None

    undervardering_ars = ((target_genomsnitt_ars / kurs) - 1) if target_genomsnitt_ars and kurs else None
    undervardering_nastaar = ((target_genomsnitt_nastaar / kurs) - 1) if target_genomsnitt_nastaar and kurs else None

    kopvard_ars = target_genomsnitt_ars * 0.7 if target_genomsnitt_ars else None
    kopvard_nastaar = target_genomsnitt_nastaar * 0.7 if target_genomsnitt_nastaar else None

    return {
        "target_genomsnitt_ars": target_genomsnitt_ars,
        "target_genomsnitt_nastaar": target_genomsnitt_nastaar,
        "undervardering_genomsnitt_ars": undervardering_ars,
        "undervardering_genomsnitt_nastaar": undervardering_nastaar,
        "kopvard_ars": kopvard_ars,
        "kopvard_nastaar": kopvard_nastaar
    }

def main():
    st.title("Aktieinnehav – Spara och analysera")
    init_db()

    with st.form("form_lagg_till", clear_on_submit=True):
        namn = st.text_input("Bolagsnamn (unika)")
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")
        pe1 = st.number_input("P/E 1", min_value=0.0, format="%.2f")
        pe2 = st.number_input("P/E 2", min_value=0.0, format="%.2f")
        pe3 = st.number_input("P/E 3", min_value=0.0, format="%.2f")
        pe4 = st.number_input("P/E 4", min_value=0.0, format="%.2f")
        ps1 = st.number_input("P/S 1", min_value=0.0, format="%.2f")
        ps2 = st.number_input("P/S 2", min_value=0.0, format="%.2f")
        ps3 = st.number_input("P/S 3", min_value=0.0, format="%.2f")
        ps4 = st.number_input("P/S 4", min_value=0.0, format="%.2f")
        vinst_arsprognos = st.number_input("Vinst prognos i år", format="%.2f")
        vinst_nastaar = st.number_input("Vinst prognos nästa år", format="%.2f")
        tillvaxt_ars = st.number_input("Omsättningstillväxt i år (%)", format="%.2f")
        tillvaxt_nasta = st.number_input("Omsättningstillväxt nästa år (%)", format="%.2f")

        if st.form_submit_button("Lägg till bolag"):
            if namn.strip() == "":
                st.error("Bolagsnamn krävs.")
            else:
                data = (
                    namn.strip(), nuvarande_kurs,
                    pe1, pe2, pe3, pe4,
                    ps1, ps2, ps3, ps4,
                    vinst_arsprognos, vinst_nastaar,
                    tillvaxt_ars, tillvaxt_nasta,
                    datetime.now().isoformat()
                )
                spara_bolag(data)
                st.success(f"Bolag '{namn}' sparat.")

    bolag = hamta_alla_bolag()
    if not bolag:
        st.info("Inga bolag sparade ännu.")
        return

    df = pd.DataFrame(
        bolag,
        columns=[
            "namn", "nuvarande_kurs",
            "pe1", "pe2", "pe3", "pe4",
            "ps1", "ps2", "ps3", "ps4",
            "vinst_arsprognos", "vinst_nastaar",
            "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
            "insatt_datum"
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

    st.subheader("📊 Välj bolag")
    val = st.selectbox("Välj ett bolag", df_display["namn"])
    valt_rad = df_display[df_display["namn"] == val].iloc[0]

    st.markdown(f"### {val}")
    st.write(f"**Nuvarande kurs:** {valt_rad['nuvarande_kurs']:.2f} kr")
    st.write(f"**Targetkurs år:** {valt_rad['target_genomsnitt_ars']:.2f} kr" if pd.notna(valt_rad['target_genomsnitt_ars']) else "**Targetkurs år:** saknas")
    st.write(f"**Targetkurs nästa år:** {valt_rad['target_genomsnitt_nastaar']:.2f} kr" if pd.notna(valt_rad['target_genomsnitt_nastaar']) else "**Targetkurs nästa år:** saknas")
    st.write(f"**Undervärdering i år:** {valt_rad['undervardering_genomsnitt_ars']:.0%}" if pd.notna(valt_rad['undervardering_genomsnitt_ars']) else "**Undervärdering i år:** saknas")
    st.write(f"**Undervärdering nästa år:** {valt_rad['undervardering_genomsnitt_nastaar']:.0%}" if pd.notna(valt_rad['undervardering_genomsnitt_nastaar']) else "**Undervärdering nästa år:** saknas")
    st.write(f"**Köpvärd upp till (i år):** {valt_rad['kopvard_ars']:.2f} kr" if pd.notna(valt_rad['kopvard_ars']) else "**Köpvärd upp till (i år):** saknas")
    st.write(f"**Köpvärd upp till (nästa år):** {valt_rad['kopvard_nastaar']:.2f} kr" if pd.notna(valt_rad['kopvard_nastaar']) else "**Köpvärd upp till (nästa år):** saknas")

    st.subheader("🔥 Mest undervärderade bolag (> 0 %)")
    visning = df_display[
        (df_display["undervardering_genomsnitt_ars"] > 0) |
        (df_display["undervardering_genomsnitt_nastaar"] > 0)
    ].copy()

    visning["max_undervardering"] = visning[["undervardering_genomsnitt_ars", "undervardering_genomsnitt_nastaar"]].max(axis=1)
    visning = visning.sort_values("max_undervardering", ascending=False)

    if visning.empty:
        st.info("Inga bolag med positiv undervärdering.")
    else:
        for _, rad in visning.iterrows():
            st.write(f"**{rad['namn']}** – {rad['max_undervardering']:.0%} undervärderad")

    st.subheader("🗑️ Ta bort bolag")
    namn_att_ta_bort = st.selectbox("Välj bolag att ta bort", df_display["namn"])
    if st.button("Radera bolag"):
        ta_bort_bolag(namn_att_ta_bort)
        st.success(f"Bolag '{namn_att_ta_bort}' har raderats.")

if __name__ == "__main__":
    main()
