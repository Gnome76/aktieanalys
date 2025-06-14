import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "bolag.db"

# === MIGRERA NY KOLUMN ===
def migrera_ny_kolumn():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE bolag ADD COLUMN senast_andrad TEXT")
        st.success("Kolumn 'senast_andrad' tillagd.")
    except sqlite3.OperationalError as e:
        st.info("Kolumnen finns redan eller fel inträffade.")
    conn.commit()
    conn.close()

# === INITIERA DATABAS ===
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
            insatt_datum TEXT,
            senast_andrad TEXT
        )
    """)
    conn.commit()
    conn.close()

def spara_bolag(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

    target_genomsnitt_ars = (target_pe_ars + target_ps_ars) / 2 if target_pe_ars and target_ps_ars else None
    target_genomsnitt_nastaar = (target_pe_nastaar + target_ps_nastaar) / 2 if target_pe_nastaar and target_ps_nastaar else None

    undervardering_genomsnitt_ars = (target_genomsnitt_ars / nuvarande_kurs) - 1 if nuvarande_kurs and target_genomsnitt_ars else None
    undervardering_genomsnitt_nastaar = (target_genomsnitt_nastaar / nuvarande_kurs) - 1 if nuvarande_kurs and target_genomsnitt_nastaar else None

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
    st.title("📈 Aktieanalysapp")
    init_db()

    # === KNAPP: MIGRERA NY KOLUMN ===
    if st.button("🔧 Migrera ny kolumn (senast_andrad)"):
        migrera_ny_kolumn()

    # === FORMULÄR: LÄGG TILL BOLAG ===
    with st.form("form_lagg_till", clear_on_submit=True):
        st.subheader("➕ Lägg till nytt bolag")
        namn = st.text_input("Bolagsnamn (unika)")
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0)
        pe1 = st.number_input("P/E (år 1)", min_value=0.0)
        pe2 = st.number_input("P/E (år 2)", min_value=0.0)
        pe3 = st.number_input("P/E (år 3)", min_value=0.0)
        pe4 = st.number_input("P/E (år 4)", min_value=0.0)
        ps1 = st.number_input("P/S (år 1)", min_value=0.0)
        ps2 = st.number_input("P/S (år 2)", min_value=0.0)
        ps3 = st.number_input("P/S (år 3)", min_value=0.0)
        ps4 = st.number_input("P/S (år 4)", min_value=0.0)
        vinst_arsprognos = st.number_input("Vinst prognos i år")
        vinst_nastaar = st.number_input("Vinst prognos nästa år")
        omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt i år (%)")
        omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)")

        submit = st.form_submit_button("Spara bolag")
        if submit:
            if namn.strip() == "":
                st.error("Bolagsnamn krävs.")
            else:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                data = (
                    namn.strip(), nuvarande_kurs,
                    pe1, pe2, pe3, pe4,
                    ps1, ps2, ps3, ps4,
                    vinst_arsprognos, vinst_nastaar,
                    omsattningstillvaxt_arsprognos, omsattningstillvaxt_nastaar,
                    now, now
                )
                spara_bolag(data)
                st.success(f"Bolaget '{namn}' sparades!")

    # === HÄMTA OCH VISA ===
    bolag = hamta_alla_bolag()
    if bolag:
        df = pd.DataFrame(bolag, columns=[
            "namn", "nuvarande_kurs",
            "pe1", "pe2", "pe3", "pe4",
            "ps1", "ps2", "ps3", "ps4",
            "vinst_arsprognos", "vinst_nastaar",
            "omsattningstillvaxt_arsprognos", "omsattningstillvaxt_nastaar",
            "insatt_datum", "senast_andrad"
        ])

        # === VISA UNDERVÄRDERADE BOLAG ===
        resultat = []
        for _, row in df.iterrows():
            res = berakna_targetkurs(
                [row.pe1, row.pe2, row.pe3, row.pe4],
                [row.ps1, row.ps2, row.ps3, row.ps4],
                row.vinst_arsprognos, row.vinst_nastaar, row.nuvarande_kurs
            )
            resultat.append(res)

        df_target = pd.DataFrame(resultat)
        df_display = pd.concat([df.reset_index(drop=True), df_target], axis=1)

        st.subheader("📊 Undervärderade bolag (≥30%)")
        undervarderade = df_display[
            (df_display["undervardering_genomsnitt_ars"] >= 0.3) |
            (df_display["undervardering_genomsnitt_nastaar"] >= 0.3)
        ].sort_values(by=["undervardering_genomsnitt_ars", "undervardering_genomsnitt_nastaar"], ascending=False)

        if undervarderade.empty:
            st.info("Inga bolag är minst 30 % undervärderade.")
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

            bolag = undervarderade.iloc[st.session_state.idx]
            st.markdown(f"### {bolag['namn']}")
            st.write(f"**Nuvarande kurs:** {bolag['nuvarande_kurs']:.2f} kr")
            st.write(f"**Targetkurs år:** {bolag['target_genomsnitt_ars']:.2f} kr")
            st.write(f"**Undervärdering år:** {bolag['undervardering_genomsnitt_ars']:.0%}")
            st.write(f"**Köpvärd upp till (år):** {bolag['kopvard_ars']:.2f} kr")
            st.caption(f"{st.session_state.idx + 1} av {total}")

        # === TA BORT: BOKSTAVSORDNING ===
        st.subheader("🗑️ Ta bort bolag")
        namn_radera = st.selectbox("Välj bolag (A–Ö)", df["namn"])
        if st.button("Radera valt bolag"):
            ta_bort_bolag(namn_radera)
            st.success(f"Bolag '{namn_radera}' raderat.")
            st.experimental_rerun()

        # === TA BORT: EFTER DATUM ===
        df_datum = df.sort_values("insatt_datum")
        options_datum = df_datum.apply(lambda r: f"{r['namn']} ({r['insatt_datum']})", axis=1).tolist()
        namn_map = dict(zip(options_datum, df_datum["namn"]))
        val_datum = st.selectbox("Eller välj bolag efter insatt datum", options_datum)
        if st.button("Radera valt (datumordning)"):
            ta_bort_bolag(namn_map[val_datum])
            st.success(f"Bolag '{namn_map[val_datum]}' raderat.")
            st.experimental_rerun()

        # === REDIGERA BOLAG ===
        st.subheader("✏️ Redigera bolag")
        val = st.selectbox("Välj bolag att redigera", df["namn"])
        bolag_rad = df[df["namn"] == val].iloc[0]
        with st.form("form_redigera"):
            kurs = st.number_input("Nuvarande kurs", value=bolag_rad["nuvarande_kurs"])
            pe1 = st.number_input("P/E (år 1)", value=bolag_rad["pe1"])
            ps1 = st.number_input("P/S (år 1)", value=bolag_rad["ps1"])
            vinst = st.number_input("Vinst prognos i år", value=bolag_rad["vinst_arsprognos"])
            tillvaxt = st.number_input("Omsättningstillväxt (%)", value=bolag_rad["omsattningstillvaxt_arsprognos"])
            spara = st.form_submit_button("Spara ändringar")
            if spara:
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                df.loc[df["namn"] == val, ["nuvarande_kurs", "pe1", "ps1", "vinst_arsprognos", "omsattningstillvaxt_arsprognos", "senast_andrad"]] = \
                    [kurs, pe1, ps1, vinst, tillvaxt, now]
                updated_row = df[df["namn"] == val].iloc[0]
                spara_bolag(tuple(updated_row))
                st.success(f"Bolaget '{val}' uppdaterades.")
                st.experimental_rerun()

    else:
        st.info("Inga bolag sparade ännu.")

if __name__ == "__main__":
    main()
