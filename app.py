import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io

DB_NAME = "bolag.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS bolag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            namn TEXT UNIQUE,
            nuvarande_kurs REAL,
            pe_1 REAL,
            pe_2 REAL,
            pe_3 REAL,
            pe_4 REAL,
            ps_1 REAL,
            ps_2 REAL,
            ps_3 REAL,
            ps_4 REAL,
            vinst_prognos_1 REAL,
            vinst_prognos_2 REAL,
            oms_tillv_1 REAL,
            oms_tillv_2 REAL,
            sparad_tid TEXT
        )
    """)
    conn.commit()
    conn.close()

def spara_bolag(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO bolag (
            namn, nuvarande_kurs,
            pe_1, pe_2, pe_3, pe_4,
            ps_1, ps_2, ps_3, ps_4,
            vinst_prognos_1, vinst_prognos_2,
            oms_tillv_1, oms_tillv_2,
            sparad_tid
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, data)
    conn.commit()
    conn.close()

def ta_bort_bolag(namn):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn = ?", (namn,))
    conn.commit()
    conn.close()

def hamta_alla_bolag():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM bolag ORDER BY namn ASC")
    rows = c.fetchall()
    conn.close()
    return rows

def berakna_targetkurs(data):
    # data = dict med nyckeltal för ett bolag
    pe_varden = [data["pe_1"], data["pe_2"], data["pe_3"], data["pe_4"]]
    ps_varden = [data["ps_1"], data["ps_2"], data["ps_3"], data["ps_4"]]

    avg_pe = sum(pe_varden) / len(pe_varden)
    avg_ps = sum(ps_varden) / len(ps_varden)

    # Target kurs p/e = avg_pe * vinstprognos_2 (nästa år)
    target_pe = avg_pe * data["vinst_prognos_2"]
    # Target kurs p/s = avg_ps * oms_tillv_2 (nästa år)
    # OBS! Omsättningstillväxt är i procent, behöver omvandlas till multipel
    # Här tolkar vi omsättningstillväxt som procentuell tillväxt, för enkelhet: 
    # använd omsättningstillväxt + 1 som multipel för p/s
    oms_mult = 1 + (data["oms_tillv_2"] / 100)
    target_ps = avg_ps * oms_mult

    target_genomsnitt = (target_pe + target_ps) / 2

    return target_pe, target_ps, target_genomsnitt

def main():
    st.set_page_config(page_title="Aktieanalys", layout="wide")
    st.title("Aktieanalys - Lägg till och analysera bolag")

    init_db()

    with st.form("ny_bolag_form"):
        st.subheader("Lägg till nytt bolag")
        namn = st.text_input("Bolagsnamn").strip()
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")
        pe_1 = st.number_input("P/E (år 1)", min_value=0.0, format="%.2f")
        pe_2 = st.number_input("P/E (år 2)", min_value=0.0, format="%.2f")
        pe_3 = st.number_input("P/E (år 3)", min_value=0.0, format="%.2f")
        pe_4 = st.number_input("P/E (år 4)", min_value=0.0, format="%.2f")
        ps_1 = st.number_input("P/S (år 1)", min_value=0.0, format="%.2f")
        ps_2 = st.number_input("P/S (år 2)", min_value=0.0, format="%.2f")
        ps_3 = st.number_input("P/S (år 3)", min_value=0.0, format="%.2f")
        ps_4 = st.number_input("P/S (år 4)", min_value=0.0, format="%.2f")
        vinst_prognos_1 = st.number_input("Vinstprognos i år", format="%.2f")
        vinst_prognos_2 = st.number_input("Vinstprognos nästa år", format="%.2f")
        oms_tillv_1 = st.number_input("Omsättningstillväxt i år (%)", format="%.2f")
        oms_tillv_2 = st.number_input("Omsättningstillväxt nästa år (%)", format="%.2f")

        skickaknapp = st.form_submit_button("Spara bolag")

        if skickaknapp:
            if namn == "":
                st.error("Ange bolagsnamn!")
            else:
                data = (
                    namn, nuvarande_kurs,
                    pe_1, pe_2, pe_3, pe_4,
                    ps_1, ps_2, ps_3, ps_4,
                    vinst_prognos_1, vinst_prognos_2,
                    oms_tillv_1, oms_tillv_2,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                spara_bolag(data)
                st.success(f"Bolaget {namn} sparat!")
                st.experimental_rerun()

    # Hämta alla bolag
    bolag = hamta_alla_bolag()
    if not bolag:
        st.info("Inga bolag sparade ännu.")
        return

    # Konvertera till DataFrame för enklare hantering
    df = pd.DataFrame(bolag, columns=[
        "id", "namn", "nuvarande_kurs",
        "pe_1", "pe_2", "pe_3", "pe_4",
        "ps_1", "ps_2", "ps_3", "ps_4",
        "vinst_prognos_1", "vinst_prognos_2",
        "oms_tillv_1", "oms_tillv_2",
        "sparad_tid"
    ])

    # Beräkna targetkurser och undervärdering
    def calc(row):
        data = row.to_dict()
        tp, tps, tgen = berakna_targetkurs(data)
        undervard_pe = (tp - data["nuvarande_kurs"]) / data["nuvarande_kurs"] * 100 if data["nuvarande_kurs"] else 0
        undervard_ps = (tps - data["nuvarande_kurs"]) / data["nuvarande_kurs"] * 100 if data["nuvarande_kurs"] else 0
        undervard_gen = (tgen - data["nuvarande_kurs"]) / data["nuvarande_kurs"] * 100 if data["nuvarande_kurs"] else 0
        return pd.Series({
            "target_pe": tp,
            "target_ps": tps,
            "target_genomsnitt": tgen,
            "undervard_pe_pct": undervard_pe,
            "undervard_ps_pct": undervard_ps,
            "undervard_gen_pct": undervard_gen
        })

    df_targets = df.apply(calc, axis=1)
    df = pd.concat([df, df_targets], axis=1)

    # Sökfilter
    search_text = st.text_input("Sök bolag")
    if search_text:
        df = df[df["namn"].str.contains(search_text, case=False)]

    # Filter undervärderade (minst 30%)
    visa_endast_undervard = st.checkbox("Visa endast bolag minst 30% undervärderade (genomsnitt)")
    if visa_endast_undervard:
        df = df[df["undervard_gen_pct"] >= 30]
        df = df.sort_values(by="undervard_gen_pct", ascending=False)

    # Visa tabell med snyggare format
    def format_percent(x):
        return f"{x:.1f}%" if pd.notnull(x) else ""

    df_display = df[[
        "namn", "nuvarande_kurs",
        "target_pe", "target_ps", "target_genomsnitt",
        "undervard_pe_pct", "undervard_ps_pct", "undervard_gen_pct",
        "sparad_tid"
    ]].copy()

    df_display["nuvarande_kurs"] = df_display["nuvarande_kurs"].map("{:.2f}".format)
    df_display["target_pe"] = df_display["target_pe"].map("{:.2f}".format)
    df_display["target_ps"] = df_display["target_ps"].map("{:.2f}".format)
    df_display["target_genomsnitt"] = df_display["target_genomsnitt"].map("{:.2f}".format)
    df_display["undervard_pe_pct"] = df_display["undervard_pe_pct"].map(format_percent)
    df_display["undervard_ps_pct"] = df_display["undervard_ps_pct"].map(format_percent)
    df_display["undervard_gen_pct"] = df_display["undervard_gen_pct"].map(format_percent)

    st.subheader("Sparade bolag")
    st.dataframe(df_display, use_container_width=True)

    # Ta bort bolag
    st.subheader("Ta bort bolag")
    bolag_namn = df["namn"].tolist()
    val = st.selectbox("Välj bolag att ta bort", options=bolag_namn)
    if st.button("Ta bort valt bolag"):
        if st.confirm("Är du säker på att du vill ta bort bolaget?"):
            ta_bort_bolag(val)
            st.success(f"Bolaget {val} är borttaget.")
            st.experimental_rerun()

    # Visa statistik
    st.markdown("---")
    st.subheader("Statistik")
    st.write(f"Antal bolag totalt: {len(df)}")
    undervardade_antal = len(df[df["undervard_gen_pct"] >= 30])
    st.write(f"Antal bolag minst 30% undervärderade: {undervardade_antal}")
    if undervardade_antal > 0:
        medel_undervard = df[df["undervard_gen_pct"] >= 30]["undervard_gen_pct"].mean()
        st.write(f"Genomsnittlig undervärdering (bland dessa): {medel_undervard:.1f}%")

    # Visa senaste uppdateringstid
    senaste_tid = df["sparad_tid"].max()
    st.write(f"Senaste uppdatering: {senaste_tid}")

    # Exportera till CSV
    csv_buffer = io.StringIO()
    df_display.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    st.download
