import streamlit as st
import sqlite3
import pandas as pd

DB_FILE = "bolag.db"

# Initiera databas
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bolag (
            namn TEXT PRIMARY KEY,
            nuvarande_kurs REAL,
            pe1 REAL, pe2 REAL, pe3 REAL, pe4 REAL,
            ps1 REAL, ps2 REAL, ps3 REAL, ps4 REAL,
            vinst_i_ar REAL, vinst_nasta_ar REAL,
            oms_i_ar REAL, oms_nasta_ar REAL
        )
    ''')
    conn.commit()
    conn.close()

# Lägg till eller uppdatera bolag
def add_or_update_bolag(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(namn) DO UPDATE SET
            nuvarande_kurs=excluded.nuvarande_kurs,
            pe1=excluded.pe1, pe2=excluded.pe2, pe3=excluded.pe3, pe4=excluded.pe4,
            ps1=excluded.ps1, ps2=excluded.ps2, ps3=excluded.ps3, ps4=excluded.ps4,
            vinst_i_ar=excluded.vinst_i_ar, vinst_nasta_ar=excluded.vinst_nasta_ar,
            oms_i_ar=excluded.oms_i_ar, oms_nasta_ar=excluded.oms_nasta_ar
    ''', data)
    conn.commit()
    conn.close()

# Hämta alla bolag
def get_all_bolag():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM bolag ORDER BY namn")
    rows = c.fetchall()
    conn.close()
    return rows

# Huvudfunktion
def main():
    st.title("📊 Aktieanalys")

    init_db()

    st.subheader("➕ Lägg till / uppdatera bolag")

    alla_bolag = get_all_bolag()
    bolagsnamn_lista = [row[0] for row in alla_bolag]

    valt_bolag = st.selectbox("🔄 Välj bolag att redigera (eller lämna tomt för nytt):", [""] + bolagsnamn_lista)

    if valt_bolag and valt_bolag != "":
        data = next(row for row in alla_bolag if row[0] == valt_bolag)
        (
            bolag, nuvarande_kurs,
            pe1, pe2, pe3, pe4,
            ps1, ps2, ps3, ps4,
            vinst_ar, vinst_nasta_ar,
            oms_i_ar, oms_nasta_ar
        ) = data
    else:
        bolag = ""
        nuvarande_kurs = pe1 = pe2 = pe3 = pe4 = ps1 = ps2 = ps3 = ps4 = 0.0
        vinst_ar = vinst_nasta_ar = oms_i_ar = oms_nasta_ar = 0.0

    with st.form("form_lagg_till"):
        bolag_input = st.text_input("Bolagsnamn", bolag)
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f", value=nuvarande_kurs)
        pe1 = st.number_input("P/E -4 år", value=pe1)
        pe2 = st.number_input("P/E -3 år", value=pe2)
        pe3 = st.number_input("P/E -2 år", value=pe3)
        pe4 = st.number_input("P/E -1 år", value=pe4)
        ps1 = st.number_input("P/S -4 år", value=ps1)
        ps2 = st.number_input("P/S -3 år", value=ps2)
        ps3 = st.number_input("P/S -2 år", value=ps3)
        ps4 = st.number_input("P/S -1 år", value=ps4)
        vinst_ar = st.number_input("Vinst i år", value=vinst_ar)
        vinst_nasta_ar = st.number_input("Vinst nästa år", value=vinst_nasta_ar)
        oms_i_ar = st.number_input("Omsättning i år", value=oms_i_ar)
        oms_nasta_ar = st.number_input("Omsättning nästa år", value=oms_nasta_ar)

        if st.form_submit_button("💾 Spara bolag"):
            if bolag_input.strip() == "":
                st.error("⚠️ Du måste ange bolagsnamn.")
            else:
                data = (
                    bolag_input.strip(), nuvarande_kurs,
                    pe1, pe2, pe3, pe4,
                    ps1, ps2, ps3, ps4,
                    vinst_ar, vinst_nasta_ar,
                    oms_i_ar, oms_nasta_ar
                )
                add_or_update_bolag(data)
                st.success(f"✅ '{bolag_input}' har sparats eller uppdaterats!")
                st.session_state.clear()  # 👈 Bytt från rerun till clear

    st.subheader("📈 Analyserade bolag")

    rows = get_all_bolag()
    if not rows:
        st.info("Inga bolag inlagda ännu.")
        return

    df = pd.DataFrame(rows, columns=[
        "Bolag", "Nuvarande kurs",
        "P/E 1", "P/E 2", "P/E 3", "P/E 4",
        "P/S 1", "P/S 2", "P/S 3", "P/S 4",
        "Vinst i år", "Vinst nästa år",
        "Omsättning i år", "Omsättning nästa år"
    ])

    df["P/E snitt"] = df[["P/E 1", "P/E 2", "P/E 3", "P/E 4"]].mean(axis=1)
    df["P/S snitt"] = df[["P/S 1", "P/S 2", "P/S 3", "P/S 4"]].mean(axis=1)

    df["Target P/E"] = df["P/E snitt"] * df["Vinst nästa år"]
    df["Target P/S"] = df["P/S snitt"] * df["Omsättning nästa år"]
    df["Target snitt"] = (df["Target P/E"] + df["Target P/S"]) / 2

    df["Undervärdering (%)"] = ((df["Target snitt"] - df["Nuvarande kurs"]) / df["Nuvarande kurs"]) * 100

    visa_alla = st.checkbox("✅ Visa alla bolag")
    visa_undervard = st.checkbox("📉 Visa endast undervärderade ≥ 30%")

    df_display = df.copy()

    if visa_undervard:
        df_display = df_display[df_display["Undervärdering (%)"] >= 30]
        df_display = df_display.sort_values(by="Undervärdering (%)", ascending=False)

    if not df_display.empty:
        df_display = df_display[[
            "Bolag", "Nuvarande kurs",
            "Target P/E", "Target P/S", "Target snitt", "Undervärdering (%)"
        ]]
        df_display["Undervärdering (%)"] = df_display["Undervärdering (%)"].map(lambda x: f"{x:.1f}%")
        st.dataframe(df_display.set_index("Bolag"), use_container_width=True)
    else:
        st.warning("🚫 Inga bolag matchar kriterierna.")

if __name__ == "__main__":
    main()
