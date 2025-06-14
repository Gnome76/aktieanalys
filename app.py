import streamlit as st
import sqlite3
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
            insatt_datum TEXT,
            senast_andrad TEXT
        )
    """)
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
               insatt_datum, senast_andrad
        FROM bolag ORDER BY namn COLLATE NOCASE ASC
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def spara_bolag(data, redigera=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if redigera:
        c.execute("""
            UPDATE bolag SET
                nuvarande_kurs = ?,
                pe1 = ?, pe2 = ?, pe3 = ?, pe4 = ?,
                ps1 = ?, ps2 = ?, ps3 = ?, ps4 = ?,
                vinst_arsprognos = ?,
                vinst_nastaar = ?,
                omsattningstillvaxt_arsprognos = ?,
                omsattningstillvaxt_nastaar = ?,
                senast_andrad = ?
            WHERE namn = ?
        """, (
            data["nuvarande_kurs"],
            data["pe1"], data["pe2"], data["pe3"], data["pe4"],
            data["ps1"], data["ps2"], data["ps3"], data["ps4"],
            data["vinst_arsprognos"],
            data["vinst_nastaar"],
            data["omsattningstillvaxt_arsprognos"],
            data["omsattningstillvaxt_nastaar"],
            data["senast_andrad"],
            data["namn"]
        ))
    else:
        c.execute("""
            INSERT INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["namn"],
            data["nuvarande_kurs"],
            data["pe1"], data["pe2"], data["pe3"], data["pe4"],
            data["ps1"], data["ps2"], data["ps3"], data["ps4"],
            data["vinst_arsprognos"],
            data["vinst_nastaar"],
            data["omsattningstillvaxt_arsprognos"],
            data["omsattningstillvaxt_nastaar"],
            data["insatt_datum"],
            data["senast_andrad"]
        ))
    conn.commit()
    conn.close()

def ta_bort_bolag(namn):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn = ?", (namn,))
    conn.commit()
    conn.close()

def main():
    st.title("Aktieanalys – Lägg till, redigera & ta bort bolag")
    init_db()

    menu = st.sidebar.radio("Välj funktion", ["Lägg till nytt bolag", "Redigera bolag", "Ta bort bolag", "Visa alla bolag"])

    if menu == "Lägg till nytt bolag":
        st.header("Lägg till nytt bolag")

        namn = st.text_input("Bolagsnamn (unik)")
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")
        pe1 = st.number_input("PE 1", format="%.2f")
        pe2 = st.number_input("PE 2", format="%.2f")
        pe3 = st.number_input("PE 3", format="%.2f")
        pe4 = st.number_input("PE 4", format="%.2f")
        ps1 = st.number_input("PS 1", format="%.2f")
        ps2 = st.number_input("PS 2", format="%.2f")
        ps3 = st.number_input("PS 3", format="%.2f")
        ps4 = st.number_input("PS 4", format="%.2f")
        vinst_arsprognos = st.number_input("Vinst årsprognos", format="%.2f")
        vinst_nastaar = st.number_input("Vinst nästa år", format="%.2f")
        omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt årsprognos (%)", format="%.2f")
        omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)", format="%.2f")

        if st.button("Spara nytt bolag"):
            if namn.strip() == "":
                st.error("Ange ett bolagsnamn!")
            else:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data = {
                    "namn": namn.strip(),
                    "nuvarande_kurs": nuvarande_kurs,
                    "pe1": pe1,
                    "pe2": pe2,
                    "pe3": pe3,
                    "pe4": pe4,
                    "ps1": ps1,
                    "ps2": ps2,
                    "ps3": ps3,
                    "ps4": ps4,
                    "vinst_arsprognos": vinst_arsprognos,
                    "vinst_nastaar": vinst_nastaar,
                    "omsattningstillvaxt_arsprognos": omsattningstillvaxt_arsprognos,
                    "omsattningstillvaxt_nastaar": omsattningstillvaxt_nastaar,
                    "insatt_datum": now,
                    "senast_andrad": now
                }
                spara_bolag(data, redigera=False)
                st.success(f"Bolaget '{namn}' sparat!")

    elif menu == "Redigera bolag":
        st.header("Redigera befintligt bolag")
        bolag = hamta_alla_bolag()
        if not bolag:
            st.info("Inga bolag att redigera.")
            return

        bolag_namn_lista = [b[0] for b in bolag]
        valt_bolag = st.selectbox("Välj bolag att redigera", bolag_namn_lista)

        # Hämta bolagets data
        valt_data = next((b for b in bolag if b[0] == valt_bolag), None)
        if valt_data:
            nuvarande_kurs = st.number_input("Nuvarande kurs", value=valt_data[1], format="%.2f")
            pe1 = st.number_input("PE 1", value=valt_data[2], format="%.2f")
            pe2 = st.number_input("PE 2", value=valt_data[3], format="%.2f")
            pe3 = st.number_input("PE 3", value=valt_data[4], format="%.2f")
            pe4 = st.number_input("PE 4", value=valt_data[5], format="%.2f")
            ps1 = st.number_input("PS 1", value=valt_data[6], format="%.2f")
            ps2 = st.number_input("PS 2", value=valt_data[7], format="%.2f")
            ps3 = st.number_input("PS 3", value=valt_data[8], format="%.2f")
            ps4 = st.number_input("PS 4", value=valt_data[9], format="%.2f")
            vinst_arsprognos = st.number_input("Vinst årsprognos", value=valt_data[10], format="%.2f")
            vinst_nastaar = st.number_input("Vinst nästa år", value=valt_data[11], format="%.2f")
            omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt årsprognos (%)", value=valt_data[12], format="%.2f")
            omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)", value=valt_data[13], format="%.2f")

            if st.button("Spara ändringar"):
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                data = {
                    "namn": valt_bolag,
                    "nuvarande_kurs": nuvarande_kurs,
                    "pe1": pe1,
                    "pe2": pe2,
                    "pe3": pe3,
                    "pe4": pe4,
                    "ps1": ps1,
                    "ps2": ps2,
                    "ps3": ps3,
                    "ps4": ps4,
                    "vinst_arsprognos": vinst_arsprognos,
                    "vinst_nastaar": vinst_nastaar,
                    "omsattningstillvaxt_arsprognos": omsattningstillvaxt_arsprognos,
                    "omsattningstillvaxt_nastaar": omsattningstillvaxt_nastaar,
                    "insatt_datum": valt_data[14],  # Bevara ursprungligt datum
                    "senast_andrad": now
                }
                spara_bolag(data, redigera=True)
                st.success(f"Bolaget '{valt_bolag}' uppdaterat!")

    elif menu == "Ta bort bolag":
        st.header("Ta bort bolag")
        bolag = hamta_alla_bolag()
        if not bolag:
            st.info("Inga bolag att ta bort.")
            return

        bolag_namn_lista = [f"{b[0]} (insatt: {b[14]})" for b in bolag]
        # Vi visar både namn och datum för bättre info i dropdown

        valt_str = st.selectbox("Välj bolag att ta bort", bolag_namn_lista)

        # Extrahera namnet från strängen (till vänster om första mellanslag + '(')
        valt_bolag = valt_str.split(" (")[0]

        if st.button(f"Ta bort bolaget '{valt_bolag}'"):
            ta_bort_bolag(valt_bolag)
            st.success(f"Bolaget '{valt_bolag}' har tagits bort.")

    elif menu == "Visa alla bolag":
        st.header("Alla sparade bolag")
        bolag = hamta_alla_bolag()
        if not bolag:
            st.info("Inga bolag sparade.")
            return
        for b in bolag:
            st.write(f"**{b[0]}** — Kurs: {b[1]:.2f}, Insatt: {b[14]}, Senast ändrad: {b[15]}")

if __name__ == "__main__":
    main()
