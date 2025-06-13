import streamlit as st
import pandas as pd

st.title("📊 Aktieanalys – Enkel värderingsmodell")

# Lagra data i session state
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        'Bolag', 'Nuvarande kurs', 'P/E1', 'P/E2', 'P/E3', 'P/E4',
        'P/S1', 'P/S2', 'P/S3', 'P/S4',
        'Vinst i år', 'Vinst nästa år',
        'Omsättningstillväxt i år', 'Omsättningstillväxt nästa år'
    ])

# Formulär för att lägga till bolag
with st.form("add_company"):
    st.subheader("➕ Lägg till nytt bolag")
    bolag = st.text_input("Bolagsnamn")
    kurs = st.number_input("Nuvarande kurs", min_value=0.0)

    pe = [st.number_input(f"P/E {i+1}", min_value=0.0, key=f"pe{i}") for i in range(4)]
    ps = [st.number_input(f"P/S {i+1}", min_value=0.0, key=f"ps{i}") for i in range(4)]

    vinst_i_ar = st.number_input("Vinstprognos i år", min_value=0.0)
    vinst_nasta_ar = st.number_input("Vinstprognos nästa år", min_value=0.0)
    oms_i_ar = st.number_input("Omsättningstillväxt i år", min_value=0.0)
    oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år", min_value=0.0)

    submitted = st.form_submit_button("Spara bolag")
    if submitted and bolag:
        ny_rad = pd.DataFrame([[
            bolag.strip().capitalize(), kurs, *pe, *ps,
            vinst_i_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar
        ]], columns=st.session_state.data.columns)

        st.session_state.data = pd.concat([st.session_state.data, ny_rad])
        st.session_state.data = st.session_state.data.sort_values("Bolag").reset_index(drop=True)
        st.success(f"{bolag} har lagts till!")

# Beräkna targetkurser
def beräkna_target(df):
    df = df.copy()
    df['PE snitt'] = df[['P/E1', 'P/E2', 'P/E3', 'P/E4']].mean(axis=1)
    df['PS snitt'] = df[['P/S1', 'P/S2', 'P/S3', 'P/S4']].mean(axis=1)
    df['Vinst snitt'] = df[['Vinst i år', 'Vinst nästa år']].mean(axis=1)
    df['Oms snitt'] = df[['Omsättningstillväxt i år', 'Omsättningstillväxt nästa år']].mean(axis=1)

    df['Target P/E'] = df['PE snitt'] * df['Vinst snitt']
    df['Target P/S'] = df['PS snitt'] * df['Oms snitt']
    df['Target genomsnitt'] = (df['Target P/E'] + df['Target P/S']) / 2

    df['Undervärdering %'] = ((df['Target genomsnitt'] - df['Nuvarande kurs']) / df['Nuvarande kurs']) * 100
    return df

# Visa bolag med beräkningar
if not st.session_state.data.empty:
    df = beräkna_target(st.session_state.data)

    st.subheader("📈 Översikt – Alla bolag")
    st.dataframe(df[['Bolag', 'Nuvarande kurs', 'Target P/E', 'Target P/S', 'Target genomsnitt', 'Undervärdering %']])

    st.subheader("🟢 Undervärderade bolag (≥ 30%)")
    undervarderade = df[df['Undervärdering %'] >= 30].sort_values('Undervärdering %', ascending=False)
    st.dataframe(undervarderade[['Bolag', 'Nuvarande kurs', 'Target genomsnitt', 'Undervärdering %']])
else:
    st.info("Inga bolag tillagda ännu.")
