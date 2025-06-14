import streamlit as st
import sqlite3
from datetime import datetime

DB_PATH = "aktier.db"

# --- Databashantering ---

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Skapa tabell med insatt_datum och senast_andrad om den inte finns
    c.execute("""
    CREATE TABLE IF NOT EXISTS bolag (
        namn TEXT PRIMARY KEY,
        pe1 REAL,
        pe2 REAL,
        ps1 REAL,
        ps2 REAL,
        ev_ebitda REAL,
        ev_sales REAL,
        roic REAL,
        soliditet REAL,
        nettoskuld REAL,
        utdelning REAL,
        insatt_datum TEXT,
        senast_andrad TEXT
    )
    """)
    conn.commit()
    conn.close()

def hamta_alla_bolag():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM bolag")
    data = c.fetchall()
    conn.close()
    return data

def spara_bolag(namn, pe1, pe2, ps1, ps2, ev_ebitda, ev_sales, roic, soliditet, nettoskuld, utdelning, insatt_datum=None, senast_andrad=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Kolla om bolaget redan finns
    c.execute("SELECT namn FROM bolag WHERE namn=?", (namn,))
    exists = c.fetchone()
    if exists:
        # Uppdatera bolag och senast_andrad
        c.execute("""
        UPDATE bolag SET
            pe1=?, pe2=?, ps1=?, ps2=?, ev_ebitda=?, ev_sales=?, roic=?, soliditet=?, nettoskuld=?, utdelning=?, senast_andrad=?
        WHERE namn=?
        """, (pe1, pe2, ps1, ps2, ev_ebitda, ev_sales, roic, soliditet, nettoskuld, utdelning, now, namn))
    else:
        # Nytt bolag, insatt_datum sätts nu om inte angivet
        if insatt_datum is None:
            insatt_datum = now
        if senast_andrad is None:
            senast_andrad = now
        c.execute("""
        INSERT INTO bolag (namn, pe1, pe2, ps1, ps2, ev_ebitda, ev_sales, roic, soliditet, nettoskuld, utdelning, insatt_datum, senast_andrad)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (namn, pe1, pe2, ps1, ps2, ev_ebitda, ev_sales, roic, soliditet, nettoskuld, utdelning, insatt_datum, senast_andrad))
    conn.commit()
    conn.close()

def ta_bort_bolag(namn):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM bolag WHERE namn=?", (namn,))
    conn.commit()
    conn.close()

# --- Hjälpfunktioner ---

def format_bolag_med_datum(row):
    # Exempel: "Bolagsnamn (Insatt: 2024-06-14 13:22)"
    namn = row[0]
    insatt = row[11]
    return f"{namn} (Insatt: {insatt})" if insatt else namn

# --- Appens UI och logik ---

def main():
    st.title("Aktieanalysapp")

    init_db()

    meny = st.sidebar.radio("Välj funktion", ["Visa bolag", "Lägg till/uppdatera bolag", "Redigera bolag", "Ta bort bolag"])

    # --- Visa bolag ---
    if meny == "Visa bolag":
        bolag = hamta_alla_bolag()
        if not bolag:
            st.info("Inga bolag sparade än.")
        else:
            for b in bolag:
                st.write(f"**{b[0]}** | P/E år 1: {b[1]} | P/E år 2: {b[2]} | P/S år 1: {b[3]} | P/S år 2: {b[4]} | Insatt: {b[11]} | Senast ändrad: {b[12]}")

    # --- Lägg till / uppdatera bolag ---
    elif meny == "Lägg till/uppdatera bolag":
        with st.form("nytt_bolag_form"):
            namn = st.text_input("Bolagsnamn").strip().upper()
            pe1 = st.number_input("P/E (år 1)", min_value=0.0, format="%.2f")
            pe2 = st.number_input("P/E (år 2)", min_value=0.0, format="%.2f")
            ps1 = st.number_input("P/S (år 1)", min_value=0.0, format="%.2f")
            ps2 = st.number_input("P/S (år 2)", min_value=0.0, format="%.2f")
            ev_ebitda = st.number_input("EV/EBITDA", min_value=0.0, format="%.2f")
            ev_sales = st.number_input("EV/Sales", min_value=0.0, format="%.2f")
            roic = st.number_input("ROIC (%)", min_value=0.0, format="%.2f")
            soliditet = st.number_input("Soliditet (%)", min_value=0.0, max_value=100.0, format="%.2f")
            nettoskuld = st.number_input("Nettoskuld", format="%.2f")
            utdelning = st.number_input("Utdelning (%)", min_value=0.0, max_value=100.0, format="%.2f")
            skickaknapp = st.form_submit_button("Spara bolag")

            if skickaknapp:
                if namn == "":
                    st.warning("Bolagsnamn måste anges.")
                else:
                    spara_bolag(namn, pe1, pe2, ps1, ps2, ev_ebitda, ev_sales, roic, soliditet, nettoskuld, utdelning)
                    st.success(f"Bolaget '{namn}' sparat/uppdaterat!")

    # --- Redigera bolag ---
    elif meny == "Redigera bolag":
        alla_bolag = hamta_alla_bolag()
        if not alla_bolag:
            st.info("Inga bolag sparade än.")
            return
        
        namn_lista = [b[0] for b in alla_bolag]
        
        # Hantera valt bolag i session_state och fallback
        if 'valt_bolag' not in st.session_state or st.session_state.valt_bolag not in namn_lista:
            st.session_state.valt_bolag = namn_lista[0]

        valt_bolag = st.selectbox("Välj bolag att redigera", namn_lista, index=namn_lista.index(st.session_state.valt_bolag))
        st.session_state.valt_bolag = valt_bolag

        # Hämta data för valt bolag
        vald_data = next((b for b in alla_bolag if b[0] == valt_bolag), None)
        if vald_data:
            pe1, pe2, ps1, ps2, ev_ebitda, ev_sales, roic, soliditet, nettoskuld, utdelning, insatt_datum, senast_andrad = \
                vald_data[1], vald_data[2], vald_data[3], vald_data[4], vald_data[5], vald_data[6], vald_data[7], vald_data[8], vald_data[9], vald_data[10], vald_data[11], vald_data[12]

            with st.form("redigera_bolag_form"):
                pe1_new = st.number_input("P/E (år 1)", value=pe1, format="%.2f")
                pe2_new = st.number_input("P/E (år 2)", value=pe2, format="%.2f")
                ps1_new = st.number_input("P/S (år 1)", value=ps1, format="%.2f")
                ps2_new = st.number_input("P/S (år 2)", value=ps2, format="%.2f")
                ev_ebitda_new = st.number_input("EV/EBITDA", value=ev_ebitda, format="%.2f")
                ev_sales_new = st.number_input("EV/Sales", value=ev_sales, format="%.2f")
                roic_new = st.number_input("ROIC (%)", value=roic, format="%.2f")
                soliditet_new = st.number_input("Soliditet (%)", value=soliditet, format="%.2f")
                nettoskuld_new = st.number_input("Nettoskuld", value=nettoskuld, format="%.2f")
                utdelning_new = st.number_input("Utdelning (%)", value=utdelning, format="%.2f")
                skickaknapp = st.form_submit_button("Uppdatera bolag")

                if skickaknapp:
                    spara_bolag(valt_bolag, pe1_new, pe2_new, ps1_new, ps2_new, ev_ebitda_new, ev_sales_new, roic_new, soliditet_new, nettoskuld_new, utdelning_new, insatt_datum=insatt_datum)
                    st.success(f"Bolaget '{valt_bolag}' uppdaterat!")

    # --- Ta bort bolag ---
    elif meny == "Ta bort bolag":
        alla_bolag = hamta_alla_bolag()
        if not alla_bolag:
            st.info("Inga bolag sparade än.")
            return

        # Lista för bokstavsordning
        namn_lista = sorted([b[0] for b in alla_bolag])
        # Lista för datumordning (äldsta först)
        datum_lista = sorted(alla_bolag, key=lambda x: x[11] or "9999-99-99 99:99:99")
        datum_str_list = [format_bolag_med_datum(b) for b in datum_lista]

        col1, col2 = st.columns(2)

        with col1:
            st.write("Ta bort bolag (bokstavsordning):")
            valt_bokstavs = st.selectbox("Välj bolag att ta bort", namn_lista, key="ta_bort_bokstav")
            if st.button(f"Ta bort {valt_bokstavs}", key="btn_bokstav"):
                ta_bort_bolag(valt_bokstavs)
                st.success(f"Bolaget '{valt_bokstavs}' är borttaget.")
                # Rensa valt bolag för att inte krascha
                if 'valt_bolag' in st.session_state and st.session_state.valt_bolag == valt_bokstavs:
                    del st.session_state.valt_bolag
                st.experimental_rerun()

        with col2:
            st.write("Ta bort bolag (datumordning):")
            valt_datum = st.selectbox("Välj bolag att ta bort", datum_str_list, key="ta_bort_datum")
            if st.button(f"Ta bort {valt_datum}", key="btn_datum"):
                # Extrahera bolagsnamnet ur strängen, t.ex. "ABB (Insatt: 2023-06-14 12:00)"
                namn_att_ta_bort = valt_datum.split(" (")[0]
                ta_bort_bolag(namn_att_ta_bort)
                st.success(f"Bolaget '{namn_att_ta_bort}' är borttaget.")
                if 'valt_bolag' in st.session_state and st.session_state.valt_bolag == namn_att_ta_bort:
                    del st.session_state.valt_bolag
                st.experimental_rerun()


if __name__ == "__main__":
    main()
