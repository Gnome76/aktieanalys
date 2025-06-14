import streamlit as st
import sqlite3
import pandas as pd

DB_NAME = "aktier_v2.db"  # ändrat!

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Skapa om tabellen helt (dödar tidigare data)
    c.execute("DROP TABLE IF EXISTS bolag")
    c.execute("""
        CREATE TABLE IF NOT EXISTS bolag (
            namn TEXT PRIMARY KEY,
            kurs REAL,
            pe1 REAL, pe2 REAL, pe3 REAL, pe4 REAL,
            ps1 REAL, ps2 REAL, ps3 REAL, ps4 REAL,
            vinst_ar REAL, vinst_nasta_ar REAL,
            oms_ar REAL, oms_nasta_ar REAL
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

def hamta_bolag():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM bolag ORDER BY namn", conn)
    conn.close()
    return df

def ta_bort_bolag(namn):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn = ?", (namn,))
    conn.commit()
    conn.close()

def berakna_targetkurser(df):
    df["pe_snitt"] = df[["pe1", "pe2", "pe3", "pe4"]].mean(axis=1)
    df["ps_snitt"] = df[["ps1", "ps2", "ps3", "ps4"]].mean(axis=1)

    df["target_pe"] = df["pe_snitt"] * df["vinst_nasta_ar"]
    df["target_ps"] = df["ps_snitt"] * df["oms_nasta_ar"]
    df["target_snitt"] = (df["target_pe"] + df["target_ps"]) / 2

    df["undervardering_pct"] = ((df["target_snitt"] - df["kurs"]) / df["kurs"]) * 100
    return df

def main():
    st.set_page_config(page_title="Aktieanalys", layout="centered")
    init_db()

    st.title("📈 Aktieanalys – Enkel och Stilren")

    with st.form("nytt_bolag"):
        st.subheader("➕ Lägg till bolag")
        namn = st.text_input("Bolagsnamn")
        kurs = st.number_input("Nuvarande kurs", min_value=0.01, format="%.2f")
        pe1 = st.number_input("P/E -4 år")
        pe2 = st.number_input("P/E -3 år")
        pe3 = st.number_input("P/E -2 år")
        pe4 = st.number_input("P/E -1 år")
        ps1 = st.number_input("P/S -4 år")
        ps2 = st.number_input("P/S -3 år")
        ps3 = st.number_input("P/S -2 år")
        ps4 = st.number_input("P/S -1 år")
        vinst_ar = st.number_input("Vinst i år")
        vinst_nasta_ar = st.number_input("Vinst nästa år")
        oms_ar = st.number_input("Omsättning i år")
        oms_nasta_ar = st.number_input("Omsättning nästa år")

        if st.form_submit_button("💾 Spara bolag"):
            if namn.strip() == "":
                st.warning("⚠️ Ange bolagsnamn.")
            else:
                data = (namn.strip(), kurs, pe1, pe2, pe3, pe4,
                        ps1, ps2, ps3, ps4,
                        vinst_ar, vinst_nasta_ar,
                        oms_ar, oms_nasta_ar)
                spara_bolag(data)
                st.success(f"✅ {namn} sparat!")

    st.markdown("---")
    st.subheader("📃 Alla bolag")

    df = hamta_bolag()

    if df.empty:
        st.info("Inga bolag sparade ännu.")
    else:
        df = berakna_targetkurser(df)

        visa_undervarderade = st.checkbox("🔍 Visa endast bolag med minst 30 % undervärdering", value=False)

        if visa_undervarderade:
            df = df[df["undervardering_pct"] >= 30]
            df = df.sort_values("undervardering_pct", ascending=False)

        for _, row in df.iterrows():
            with st.expander(f"📌 {row['namn']}"):
                st.write(f"**Nuvarande kurs:** {row['kurs']:.2f} kr")
                st.write(f"**Targetkurs (P/E):** {row['target_pe']:.2f} kr")
                st.write(f"**Targetkurs (P/S):** {row['target_ps']:.2f} kr")
                st.write(f"**Targetkurs (snitt):** {row['target_snitt']:.2f} kr")
                st.write(f"📉 **Undervärdering:** {row['undervardering_pct']:.1f}%")

                if st.button(f"🗑️ Ta bort {row['namn']}", key=row['namn']):
                    ta_bort_bolag(row['namn'])
                    st.experimental_rerun()

if __name__ == "__main__":
    main()
