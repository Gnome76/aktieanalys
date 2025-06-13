import streamlit as st
import sqlite3
import pandas as pd

# --- Databas ---
conn = sqlite3.connect('aktier.db', check_same_thread=False)
c = conn.cursor()

def skapa_tabell():
    c.execute('''CREATE TABLE IF NOT EXISTS bolag (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bolag TEXT UNIQUE,
        nuvarande_kurs REAL,
        pe1 REAL, pe2 REAL, pe3 REAL, pe4 REAL,
        ps1 REAL, ps2 REAL, ps3 REAL, ps4 REAL,
        vinst_ar REAL,
        vinst_nasta_ar REAL,
        oms_i_ar REAL,
        oms_nasta_ar REAL
    )''')
    conn.commit()

skapa_tabell()

# --- CRUD ---
def lagg_till_bolag(bolag, kurs, pe, ps, vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar):
    try:
        c.execute('''INSERT INTO bolag 
                     (bolag, nuvarande_kurs, pe1, pe2, pe3, pe4, ps1, ps2, ps3, ps4, vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (bolag, kurs, pe[0], pe[1], pe[2], pe[3], ps[0], ps[1], ps[2], ps[3], vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def hamta_allt():
    df = pd.read_sql_query("SELECT * FROM bolag ORDER BY bolag COLLATE NOCASE ASC", conn)
    return df

# --- Beräkningar ---
def berakna_genomsnitt(lista):
    rensad = [x for x in lista if x > 0]
    return sum(rensad) / len(rensad) if rensad else 0

def berakna_targetkurs(pe_list, ps_list, vinst_ar):
    pe_avg = berakna_genomsnitt(pe_list)
    ps_avg = berakna_genomsnitt(ps_list)

    target_pe = pe_avg * vinst_ar if pe_avg > 0 else 0
    target_ps = ps_avg * vinst_ar if ps_avg > 0 else 0

    target_avg = (target_pe + target_ps) / 2 if target_pe > 0 and target_ps > 0 else max(target_pe, target_ps)

    return target_pe, target_ps, target_avg

def berakna_undervardering(nuvarande_kurs, target_kurs):
    if target_kurs == 0:
        return 0
    diff = target_kurs - nuvarande_kurs
    procent = (diff / nuvarande_kurs) * 100
    return procent

# --- Appen ---
st.title("📈 Enkel Aktieanalysapp")

# Lägg till bolag
st.header("➕ Lägg till nytt bolag")
with st.form("add_form", clear_on_submit=True):
    bolag = st.text_input("Bolagsnamn")
    kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")

    st.markdown("**P/E de 4 senaste åren:**")
    pe = [st.number_input(f"P/E år {i+1}", min_value=0.0, format="%.2f", key=f"pe_add_{i}") for i in range(4)]

    st.markdown("**P/S de 4 senaste åren:**")
    ps = [st.number_input(f"P/S år {i+1}", min_value=0.0, format="%.2f", key=f"ps_add_{i}") for i in range(4)]

    vinst_i_ar = st.number_input("Vinstprognos i år", min_value=0.0, format="%.2f")
    vinst_nasta_ar = st.number_input("Vinstprognos nästa år", min_value=0.0, format="%.2f")
    oms_i_ar = st.number_input("Omsättningstillväxt i år (%)", min_value=0.0, format="%.2f")
    oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år (%)", min_value=0.0, format="%.2f")

    submit = st.form_submit_button("💾 Lägg till bolag")

    if submit:
        bolag_clean = bolag.strip().capitalize()
        if bolag_clean == "":
            st.warning("Ange ett bolagsnamn!")
        else:
            lyckades = lagg_till_bolag(bolag_clean, kurs, pe, ps, vinst_i_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar)
            if lyckades:
                st.success(f"✅ Bolag '{bolag_clean}' tillagt!")
            else:
                st.error("Bolaget finns redan!")

# Visa undervärderade bolag med minst 30% undervärdering
st.header("📊 Bolag undervärderade med minst 30%")

df = hamta_allt()

if df.empty:
    st.info("Inga bolag sparade ännu.")
else:
    data_lista = []
    for i, row in df.iterrows():
        pe_list = [row['pe1'], row['pe2'], row['pe3'], row['pe4']]
        ps_list = [row['ps1'], row['ps2'], row['ps3'], row['ps4']]

        target_pe_i_ar, target_ps_i_ar, target_avg_i_ar = berakna_targetkurs(pe_list, ps_list, row['vinst_ar'])
        undervardering = berakna_undervardering(row['nuvarande_kurs'], target_avg_i_ar)

        if undervardering >= 30:
            data_lista.append({
                'Bolag': row['bolag'],
                'Nuvarande kurs': row['nuvarande_kurs'],
                'Target P/E i år': target_pe_i_ar,
                'Target P/S i år': target_ps_i_ar,
                'Target Genomsnitt i år': target_avg_i_ar,
                'Undervärdering (%)': undervardering
            })

    if not data_lista:
        st.info("Inga bolag är undervärderade med minst 30%.")
    else:
        df_visning = pd.DataFrame(data_lista)
        df_visning = df_visning.sort_values(by='Undervärdering (%)', ascending=False)

        # Formatera flyttal med 2 decimaler
        df_visning['Nuvarande kurs'] = df_visning['Nuvarande kurs'].map('{:.2f}'.format)
        df_visning['Target P/E i år'] = df_visning['Target P/E i år'].map('{:.2f}'.format)
        df_visning['Target P/S i år'] = df_visning['Target P/S i år'].map('{:.2f}'.format)
        df_visning['Target Genomsnitt i år'] = df_visning['Target Genomsnitt i år'].map('{:.2f}'.format)
        df_visning['Undervärdering (%)'] = df_visning['Undervärdering (%)'].map('{:.2f} %'.format)

        st.dataframe(df_visning, use_container_width=True)
