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
def lagg_till_bolag(...): # oförändrad
    ...

def uppdatera_bolag(bolag, kurs, pe, ps, vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar):
    c.execute('''UPDATE bolag SET
        nuvarande_kurs=?, pe1=?, pe2=?, pe3=?, pe4=?,
        ps1=?, ps2=?, ps3=?, ps4=?,
        vinst_ar=?, vinst_nasta_ar=?, oms_i_ar=?, oms_nasta_ar=?
        WHERE bolag=?''',
        (kurs, pe[0], pe[1], pe[2], pe[3], ps[0], ps[1], ps[2], ps[3],
         vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar, bolag))
    conn.commit()

def hamta_allt():
    ...

def hamta_bolag_data(bolag):
    c.execute("SELECT * FROM bolag WHERE bolag=?", (bolag,))
    return c.fetchone()

# --- Beräkningar ---
def berakna_genomsnitt(...): ...
def berakna_targetkurs(...): ...
def berakna_undervardering(...): ...

# --- Streamlit App ---
st.title("📈 Enkel Aktieanalysapp")

st.header("🛠 Lägg till eller uppdatera bolag")

bolag_lista = [row[0] for row in c.execute("SELECT bolag FROM bolag").fetchall()]
redigeringsbolag = st.selectbox("Välj bolag att redigera (eller lämna tomt för nytt)", [""] + bolag_lista)

if redigeringsbolag:
    data = hamta_bolag_data(redigeringsbolag)
    kurs_init = data[2]
    pe_init = data[3:7]
    ps_init = data[7:11]
    vinst_ar_init = data[11]
    vinst_nasta_ar_init = data[12]
    oms_i_ar_init = data[13]
    oms_nasta_ar_init = data[14]
else:
    kurs_init = 0.0
    pe_init = [0.0]*4
    ps_init = [0.0]*4
    vinst_ar_init = 0.0
    vinst_nasta_ar_init = 0.0
    oms_i_ar_init = 0.0
    oms_nasta_ar_init = 0.0

with st.form("form", clear_on_submit=not redigeringsbolag):
    bolag_input = st.text_input("Bolagsnamn", value=redigeringsbolag)
    kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f", value=kurs_init)

    st.markdown("**P/E de 4 senaste åren:**")
    pe = [st.number_input(f"P/E år {i+1}", min_value=0.0, format="%.2f", value=pe_init[i], key=f"pe_{i}") for i in range(4)]

    st.markdown("**P/S de 4 senaste åren:**")
    ps = [st.number_input(f"P/S år {i+1}", min_value=0.0, format="%.2f", value=ps_init[i], key=f"ps_{i}") for i in range(4)]

    vinst_i_ar = st.number_input("Vinstprognos i år", min_value=0.0, format="%.2f", value=vinst_ar_init)
    vinst_nasta_ar = st.number_input("Vinstprognos nästa år", min_value=0.0, format="%.2f", value=vinst_nasta_ar_init)
    oms_i_ar = st.number_input("Omsättningstillväxt i år (%)", min_value=0.0, format="%.2f", value=oms_i_ar_init)
    oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år (%)", min_value=0.0, format="%.2f", value=oms_nasta_ar_init)

    submit = st.form_submit_button("💾 Spara")

    if submit:
        namn = bolag_input.strip().capitalize()
        if redigeringsbolag:
            uppdatera_bolag(namn, kurs, pe, ps, vinst_i_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar)
            st.success(f"✅ '{namn}' uppdaterades!")
        else:
            if lagg_till_bolag(namn, kurs, pe, ps, vinst_i_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar):
                st.success(f"✅ Bolag '{namn}' tillagt!")
            else:
                st.error("❌ Bolaget finns redan!")

# --- Visa & filtrera ---
df = hamta_allt()

st.header("📂 Bolagsöversikt")

if df.empty:
    st.info("Inga bolag sparade ännu.")
else:
    visa_alla = st.checkbox("🔍 Visa alla bolag")
    visa_undervard = st.checkbox("📉 Visa endast undervärderade (≥30%)")

    data_lista = []
    for _, row in df.iterrows():
        pe_list = [row['pe1'], row['pe2'], row['pe3'], row['pe4']]
        ps_list = [row['ps1'], row['ps2'], row['ps3'], row['ps4']]
        target_pe, target_ps, target_avg = berakna_targetkurs(pe_list, ps_list, row['vinst_ar'])
        undervardering = berakna_undervardering(row['nuvarande_kurs'], target_avg)
        data_lista.append({
            'Bolag': row['bolag'],
            'Nuvarande kurs': row['nuvarande_kurs'],
            'Target P/E': target_pe,
            'Target P/S': target_ps,
            'Target Genomsnitt': target_avg,
            'Undervärdering (%)': undervardering
        })

    df_visning = pd.DataFrame(data_lista)

    if visa_undervard:
        df_visning = df_visning[df_visning['Undervärdering (%)'] >= 30]
        df_visning = df_visning.sort_values(by='Undervärdering (%)', ascending=False)

    if visa_alla or visa_undervard:
        for col in ['Nuvarande kurs', 'Target P/E', 'Target P/S', 'Target Genomsnitt']:
            df_visning[col] = df_visning[col].map('{:.2f}'.format)
        df_visning['Undervärdering (%)'] = df_visning['Undervärdering (%)'].map('{:.2f} %'.format)
        st.dataframe(df_visning, use_container_width=True)
