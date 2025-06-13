import streamlit as st
import pandas as pd

st.title("📊 Aktieanalys – Enkel nyckeltalsapp")

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

# Visa alla bolag
if not st.session_state.data.empty:
    st.subheader("📋 Sparade bolag")
    st.dataframe(st.session_state.data)
else:
    st.info("Inga bolag tillagda ännu.")
