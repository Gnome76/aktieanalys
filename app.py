import os

# Radera databasen en gång för att fixa kolumnproblemet
if os.path.exists("aktier.db"):
    os.remove("aktier.db")
import streamlit as st
import sqlite3
import pandas as pd

# --- Databasanslutning ---
conn = sqlite3.connect("aktier.db", check_same_thread=False)
c = conn.cursor()

# --- Skapa tabell (radera och återskapa för att rätta struktur) ---
def skapa_tabell():
    c.execute("DROP TABLE IF EXISTS bolag")  # Bara första gången du kör detta
    c.execute('''
        CREATE TABLE bolag (
            bolag TEXT PRIMARY KEY,
            nuvarande_kurs REAL,
            pe1 REAL, pe2 REAL, pe3 REAL, pe4 REAL,
            ps1 REAL, ps2 REAL, ps3 REAL, ps4 REAL,
            vinst_ar REAL, vinst_nasta_ar REAL,
            oms_i_ar REAL, oms_nasta_ar REAL
        )
    ''')
    conn.commit()

skapa_tabell()

# --- Funktion för att rensa alla bolag (men inte databasen) ---
def rensa_tabell():
    c.execute("DELETE FROM bolag")
    conn.commit()

# --- Hämta bolag från databasen ---
def hamta_bolag():
    return pd.read_sql("SELECT * FROM bolag ORDER BY bolag", conn)

# --- Lägg till eller uppdatera bolag ---
def lagg_till_eller_uppdatera_bolag(data):
    try:
        c.execute('''
            INSERT OR REPLACE INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit()
        return True, None
    except sqlite3.Error as e:
        return False, str(e)

# --- Beräkningar ---
def genomsnitt(lista):
    return sum(lista) / len(lista)

def targetkurs_pe(pe_avg, vinst):
    return pe_avg * vinst if vinst else 0

def targetkurs_ps(ps_avg, oms_tillv):
    return ps_avg * (1 + oms_tillv / 100)

def undervardering(target, current):
    if current == 0:
        return 0
    return ((target - current) / current) * 100

# --- UI ---
st.title("📈 Aktieanalys")

with st.form("aktieform", clear_on_submit=True):
    st.subheader("Lägg till eller uppdatera bolag")

    bolag = st.text_input("Bolagsnamn").strip().capitalize()
    kurs = st.number_input("Nuvarande kurs", min_value=0.0)

    st.markdown("**P/E 4 senaste år:**")
    pe = [st.number_input(f"P/E år {i+1}", min_value=0.0, key=f"pe{i}") for i in range(4)]

    st.markdown("**P/S 4 senaste år:**")
    ps = [st.number_input(f"P/S år {i+1}", min_value=0.0, key=f"ps{i}") for i in range(4)]

    vinst_ar = st.number_input("Vinst i år", min_value=0.0)
    vinst_nasta_ar = st.number_input("Vinst nästa år", min_value=0.0)
    oms_i_ar = st.number_input("Omsättningstillväxt i år (%)", min_value=0.0)
    oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år (%)", min_value=0.0)

    if st.form_submit_button("💾 Spara bolag"):
        if bolag:
            data = (
                bolag, kurs,
                *pe, *ps,
                vinst_ar, vinst_nasta_ar,
                oms_i_ar, oms_nasta_ar
            )
            success, error = lagg_till_eller_uppdatera_bolag(data)
            if success:
                st.success(f"{bolag} sparades.")
            else:
                st.error(f"Fel i databasen: {error}")
        else:
            st.warning("Ange bolagsnamn.")

# --- Visa bolag och analys ---
st.subheader("📊 Analys av bolag")
df = hamta_bolag()

if df.empty:
    st.info("Inga bolag sparade ännu.")
else:
    resultat = []

    for _, row in df.iterrows():
        pe_avg = genomsnitt([row['pe1'], row['pe2'], row['pe3'], row['pe4']])
        ps_avg = genomsnitt([row['ps1'], row['ps2'], row['ps3'], row['ps4']])
        vinstsnitt = genomsnitt([row['vinst_ar'], row['vinst_nasta_ar']])
        oms_snitt = genomsnitt([row['oms_i_ar'], row['oms_nasta_ar']])

        target_pe = targetkurs_pe(pe_avg, vinstsnitt)
        target_ps = targetkurs_ps(ps_avg, oms_snitt)
        target_avg = genomsnitt([target_pe, target_ps])

        underv = undervardering(target_avg, row['nuvarande_kurs'])

        resultat.append({
            "Bolag": row['bolag'],
            "Nuvarande kurs": row['nuvarande_kurs'],
            "Target P/E": round(target_pe, 2),
            "Target P/S": round(target_ps, 2),
            "Target Snitt": round(target_avg, 2),
            "Undervärdering (%)": round(underv, 2)
        })

    result_df = pd.DataFrame(resultat)

    st.markdown("### Filtrering:")
    visa_alla = st.checkbox("Visa alla bolag", value=True)
    visa_undervarderade = st.checkbox("Visa endast undervärderade (minst 30%)")

    if visa_undervarderade:
        result_df = result_df[result_df["Undervärdering (%)"] >= 30]
        result_df = result_df.sort_values(by="Undervärdering (%)", ascending=False)

    if visa_alla or visa_undervarderade:
        st.dataframe(result_df, use_container_width=True)

# --- Töm alla bolag (frivillig funktion) ---
st.markdown("---")
if st.button("🗑 Rensa alla bolag i databasen"):
    rensa_tabell()
    st.success("Alla bolag raderades från databasen.")
