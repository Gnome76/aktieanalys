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
    c.execute("INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
    conn.commit()
    conn.close()

def hamta_alla_bolag():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM bolag")
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

    target_genomsnitt_ars = (target_pe_ars + target_ps_ars) / 2 if target_pe_ars and target_ps_ars else None
    target_genomsnitt_nastaar = (target_pe_nastaar + target_ps_nastaar) / 2 if target_pe_nastaar and target_ps_nastaar else None

    undervardering_genomsnitt_ars = (target_genomsnitt_ars / nuvarande_kurs - 1) if target_genomsnitt_ars and nuvarande_kurs else None
    undervardering_genomsnitt_nastaar = (target_genomsnitt_nastaar / nuvarande_kurs - 1) if target_genomsnitt_nastaar and nuvarande_kurs else None

    kopvard_ars = target_genomsnitt_ars * 0.7 if target_genomsnitt_ars else None
    kopvard_nastaar = target_genomsnitt_nastaar * 0.7 if target_genomsnitt_nastaar else None

    genomsnitt_undervardering = None
    if undervardering_genomsnitt_ars and undervardering_genomsnitt_nastaar:
        genomsnitt_undervardering = (undervardering_genomsnitt_ars + undervardering_genomsnitt_nastaar) / 2
    elif undervardering_genomsnitt_ars:
        genomsnitt_undervardering = undervardering_genomsnitt_ars
    elif undervardering_genomsnitt_nastaar:
        genomsnitt_undervardering = undervardering_genomsnitt_nastaar

    return {
        "target_genomsnitt_ars": target_genomsnitt_ars,
        "target_genomsnitt_nastaar": target_genomsnitt_nastaar,
        "undervardering_genomsnitt_ars": undervardering_genomsnitt_ars,
        "undervardering_genomsnitt_nastaar": undervardering_genomsnitt_nastaar,
        "kopvard_ars": kopvard_ars,
        "kopvard_nastaar": kopvard_nastaar,
        "undervardering": genomsnitt_undervardering
    }

def main():
    st.title("📊 Aktieanalys – Undervärderade bolag")
    init_db()

    # Hämta bolag
    alla_bolag = hamta_alla_bolag()
    df = pd.DataFrame(alla_bolag, columns=[
        "namn", "nuvarande_kurs",
        "pe1", "pe2", "pe3", "pe4",
        "ps1", "ps2", "ps3", "ps4",
        "vinst_arsprognos", "vinst_nastaar",
        "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
        "insatt_datum"
    ])

    valt_bolag = None
    if not df.empty:
        namn_lista = df["namn"].sort_values().tolist()
        valt_namn = st.selectbox("📌 Välj bolag att visa/redigera", options=[""] + namn_lista)
        if valt_namn:
            valt_bolag = df[df["namn"] == valt_namn].iloc[0]

    st.subheader("➕ Lägg till eller uppdatera bolag")
    with st.form("lagg_till_bolag"):
        namn = st.text_input("Bolagsnamn", value=valt_bolag["namn"] if valt_bolag is not None else "")
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f", value=valt_bolag["nuvarande_kurs"] if valt_bolag is not None else 0.0)
        pe1 = st.number_input("P/E år 1", min_value=0.0, format="%.2f", value=valt_bolag["pe1"] if valt_bolag is not None else 0.0)
        pe2 = st.number_input("P/E år 2", min_value=0.0, format="%.2f", value=valt_bolag["pe2"] if valt_bolag is not None else 0.0)
        pe3 = st.number_input("P/E år 3", min_value=0.0, format="%.2f", value=valt_bolag["pe3"] if valt_bolag is not None else 0.0)
        pe4 = st.number_input("P/E år 4", min_value=0.0, format="%.2f", value=valt_bolag["pe4"] if valt_bolag is not None else 0.0)
        ps1 = st.number_input("P/S år 1", min_value=0.0, format="%.2f", value=valt_bolag["ps1"] if valt_bolag is not None else 0.0)
        ps2 = st.number_input("P/S år 2", min_value=0.0, format="%.2f", value=valt_bolag["ps2"] if valt_bolag is not None else 0.0)
        ps3 = st.number_input("P/S år 3", min_value=0.0, format="%.2f", value=valt_bolag["ps3"] if valt_bolag is not None else 0.0)
        ps4 = st.number_input("P/S år 4", min_value=0.0, format="%.2f", value=valt_bolag["ps4"] if valt_bolag is not None else 0.0)
        vinst_arsprognos = st.number_input("Vinstprognos i år", format="%.2f", value=valt_bolag["vinst_arsprognos"] if valt_bolag is not None else 0.0)
        vinst_nastaar = st.number_input("Vinstprognos nästa år", format="%.2f", value=valt_bolag["vinst_nastaar"] if valt_bolag is not None else 0.0)
        omsattning_i_ar = st.number_input("Omsättningstillväxt i år (%)", format="%.2f", value=valt_bolag["omsattningstillvaxt_arsprognos"] if valt_bolag is not None else 0.0)
        omsattning_nasta_ar = st.number_input("Omsättningstillväxt nästa år (%)", format="%.2f", value=valt_bolag["omsattningstillvaxt_nastaar"] if valt_bolag is not None else 0.0)

        submit = st.form_submit_button("💾 Spara bolag")
        if submit:
            if namn.strip() == "":
                st.error("Bolagsnamn måste anges.")
            else:
                spara_bolag((
                    namn.strip(),
                    nuvarande_kurs,
                    pe1, pe2, pe3, pe4,
                    ps1, ps2, ps3, ps4,
                    vinst_arsprognos,
                    vinst_nastaar,
                    omsattning_i_ar,
                    omsattning_nasta_ar,
                    datetime.now().isoformat()
                ))
                st.success(f"Bolag '{namn}' har sparats.")

    if not df.empty:
        st.subheader("📉 Mest undervärderade bolag (> 0 %)")

        resultat = []
        for _, row in df.iterrows():
            r = berakna_targetkurs(
                [row.pe1, row.pe2, row.pe3, row.pe4],
                [row.ps1, row.ps2, row.ps3, row.ps4],
                row.vinst_arsprognos,
                row.vinst_nastaar,
                row.nuvarande_kurs
            )
            resultat.append(r)

        df_target = pd.DataFrame(resultat)
        bolag_df = pd.concat([df.reset_index(drop=True), df_target], axis=1)

        bolag_df = bolag_df[bolag_df["undervardering"] > 0]
        bolag_df = bolag_df.sort_values("undervardering", ascending=False).reset_index(drop=True)

        if bolag_df.empty:
            st.info("Inga bolag är undervärderade.")
        else:
            for _, rad in bolag_df.iterrows():
                st.markdown(f"### {rad['namn']}")
                st.write(f"**Undervärdering (snitt):** {rad['undervardering']:.0%}")
                st.write(f"Nuvarande kurs: {rad['nuvarande_kurs']} kr")
                st.write(f"Targetkurs i år: {rad['target_genomsnitt_ars']:.2f} kr")
                st.write(f"Targetkurs nästa år: {rad['target_genomsnitt_nastaar']:.2f} kr")
                st.divider()

if __name__ == "__main__":
    main()
