import streamlit as st
import pandas as pd

st.set_page_config(page_title="Aktieanalys", page_icon="📈", layout="centered")

st.title("📈 Aktieanalys – Nyckeltal & Värdering")

# Lagra data i session state
if 'data' not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=[
        'Bolag', 'Nuvarande kurs', 'P/E1', 'P/E2', 'P/E3', 'P/E4',
        'P/S1', 'P/S2', 'P/S3', 'P/S4',
        'Vinst i år', 'Vinst nästa år',
        'Omsättningstillväxt i år', 'Omsättningstillväxt nästa år'
    ])

# Formulär för att lägga till bolag
with st.expander("➕ Lägg till nytt bolag"):
    with st.form("add_company"):
        bolag = st.text_input("Bolagsnamn")
        kurs = st.number_input("Nuvarande kurs", min_value=0.0)

        pe = [st.number_input(f"P/E {i+1}", min_value=0.0, key=f"pe{i}") for i in range(4)]
        ps = [st.number_input(f"P/S {i+1}", min_value=0.0, key=f"ps{i}") for i in range(4)]

        vinst_i_ar = st.number_input("Vinstprognos i år", min_value=0.0)
        vinst_nasta_ar = st.number_input("Vinstprognos nästa år", min_value=0.0)
        oms_i_ar = st.number_input("Omsättningstillväxt i år", min_value=0.0)
        oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år", min_value=0.0)

        submitted = st.form_submit_button("💾 Spara bolag")
        if submitted and bolag:
            ny_rad = pd.DataFrame([[
                bolag.strip().capitalize(), kurs, *pe, *ps,
                vinst_i_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar
            ]], columns=st.session_state.data.columns)

            st.session_state.data = pd.concat([st.session_state.data, ny_rad])
            st.session_state.data = st.session_state.data.sort_values("Bolag").reset_index(drop=True)
            st.success(f"✅ {bolag} har lagts till!")

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

# Visa bolag
if not st.session_state.data.empty:
    df = beräkna_target(st.session_state.data)

    st.subheader("📋 Alla bolag")
    for index, row in df.iterrows():
        färg = "🟢" if row["Undervärdering %"] >= 30 else "⚪️" if row["Undervärdering %"] > 0 else "🔴"
        st.markdown(f"""
        ### {row['Bolag']} {färg}
        - **Nuvarande kurs:** {row['Nuvarande kurs']:.2f} kr
        - **Target P/E-kurs:** {row['Target P/E']:.2f} kr
        - **Target P/S-kurs:** {row['Target P/S']:.2f} kr
        - **Snitt-target:** {row['Target genomsnitt']:.2f} kr
        - **Undervärdering:** {row['Undervärdering %']:.1f} %
        """, unsafe_allow_html=True)

    # Lista undervärderade bolag
    undervarderade = df[df['Undervärdering %'] >= 30].sort_values('Undervärdering %', ascending=False)

    if not undervarderade.empty:
        st.subheader("🟢 Mest undervärderade bolag (≥ 30%)")
        for _, row in undervarderade.iterrows():
            st.markdown(f"**{row['Bolag']}** – {row['Undervärdering %']:.1f}% undervärderad, mål: {row['Target genomsnitt']:.2f} kr")
    else:
        st.info("Inga bolag är just nu undervärderade med ≥ 30%.")

else:
    st.info("Inga bolag tillagda ännu.")
