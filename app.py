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

def berakna_targetkurs_och_undervardering(r):
    # Genomsnitt P/E och P/S från år 1-4
    pe_values = [r["pe1"], r["pe2"], r["pe3"], r["pe4"]]
    ps_values = [r["ps1"], r["ps2"], r["ps3"], r["ps4"]]

    # Räkna ut medelvärde, ignorera 0 eller None
    pe_values = [v for v in pe_values if v and v > 0]
    ps_values = [v for v in ps_values if v and v > 0]

    pe_avg = sum(pe_values)/len(pe_values) if pe_values else None
    ps_avg = sum(ps_values)/len(ps_values) if ps_values else None

    # Targetkurs baserad på vinstprognos och omsättning samt P/E och P/S
    # Vi använder genomsnitt P/E och P/S på vinst_arsprognos och omsättningstillväxt_arsprognos som proxies
    # Vi antar targetkurs baserad på högst av P/E eller P/S mål (om båda finns)
    target_pe = pe_avg * r["vinst_arsprognos"] if pe_avg and r["vinst_arsprognos"] else None
    target_ps = ps_avg * r["omsattningstillvaxt_arsprognos"] if ps_avg and r["omsattningstillvaxt_arsprognos"] else None

    # Targetkurs: ta max av target_pe och target_ps om båda finns, annars det som finns
    targetkurs = None
    if target_pe and target_ps:
        targetkurs = max(target_pe, target_ps)
    elif target_pe:
        targetkurs = target_pe
    elif target_ps:
        targetkurs = target_ps

    undervardering = None
    if targetkurs and r["nuvarande_kurs"] and r["nuvarande_kurs"] > 0:
        undervardering = (targetkurs - r["nuvarande_kurs"]) / targetkurs * 100

    return pe_avg, ps_avg, targetkurs, undervardering

def main():
    st.title("Aktieinnehav - Spara, redigera och bläddra undervärderade bolag")

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

    # Lägg till beräkningar i df
    if not df.empty:
        df["pe_avg"] = df.apply(lambda r: pd.Series(berakna_targetkurs_och_undervardering(r))[0], axis=1)
        df["ps_avg"] = df.apply(lambda r: pd.Series(berakna_targetkurs_och_undervardering(r))[1], axis=1)
        df["targetkurs"] = df.apply(lambda r: pd.Series(berakna_targetkurs_och_undervardering(r))[2], axis=1)
        df["undervardering_pct"] = df.apply(lambda r: pd.Series(berakna_targetkurs_och_undervardering(r))[3], axis=1)

    # Filter: visa endast undervärderade (minst 30%)
    visa_undervarderade_endast = st.checkbox("Visa endast minst 30% undervärderade bolag", value=False)

    if visa_undervarderade_endast and not df.empty:
        df_undervarderade = df[(df["undervardering_pct"] != None) & (df["undervardering_pct"] >= 30)]
    else:
        df_undervarderade = df

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

    # Bläddra mellan undervärderade bolag
    st.header("Bläddra bland undervärderade bolag")

    undervard_df = df_undervarderade.sort_values(by="undervardering_pct", ascending=False) if not df_undervarderade.empty else pd.DataFrame()

    if undervard_df.empty:
        st.info("Inga undervärderade bolag att visa.")
    else:
        # Session state för index
        if "undervard_index" not in st.session_state:
            st.session_state.undervard_index = 0

        col1, col2, col3 = st.columns([1,3,1])

        with col1:
            if st.button("Föregående"):
                if st.session_state.undervard_index > 0:
                    st.session_state.undervard_index -= 1

        with col3:
            if st.button("Nästa"):
                if st.session_state.undervard_index < len(undervard_df) - 1:
                    st.session_state.undervard_index += 1

        bolag_visas = undervard_df.iloc[st.session_state.undervard_index]

        st.markdown(f"### {bolag_visas['namn']}")
        st.write(f"- Nuvarande kurs: {bolag_visas['nuvarande_kurs']:.2f} SEK")
        st.write(f"- Genomsnitt P/E (år 1-4): {bolag_visas['pe_avg']:.2f}" if bolag_visas['pe_avg'] else "- Genomsnitt P/E: Ej tillgängligt")
        st.write(f"- Genomsnitt P/S (år 1-4): {bolag_visas['ps_avg']:.2f}" if bolag_visas['ps_avg'] else "- Genomsnitt P/S: Ej tillgängligt")
        st.write(f"- Targetkurs: {bolag_visas['targetkurs']:.2f} SEK" if bolag_visas['targetkurs'] else "- Targetkurs: Ej beräknad")
        st.write(f"- Undervärdering: {bolag_visas['undervardering_pct']:.2f} %")
        st.write(f"- Vinst prognos i år: {bolag_visas['vinst_arsprognos']}")
        st.write(f"- Omsättningstillväxt i år (%): {bolag_visas['omsattningstillvaxt_arsprognos']}")

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

if __name__ == "__main__":
    main()
