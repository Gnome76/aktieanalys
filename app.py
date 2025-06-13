import streamlit as st
import sqlite3
import pandas as pd

# --- Hjälpfunktioner för säker konvertering ---
def safe_float(val):
    try:
        if val is None:
            return 0.0
        return float(val)
    except (TypeError, ValueError):
        return 0.0

def safe_str(val):
    try:
        if val is None:
            return ""
        return str(val).strip()
    except Exception:
        return ""

# --- Databasinställningar ---
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

# --- CRUD-funktioner ---
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

def uppdatera_bolag(bolag_id, bolag, kurs, pe, ps, vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar):
    c.execute('''UPDATE bolag SET
                 bolag=?, nuvarande_kurs=?, pe1=?, pe2=?, pe3=?, pe4=?, ps1=?, ps2=?, ps3=?, ps4=?, 
                 vinst_ar=?, vinst_nasta_ar=?, oms_i_ar=?, oms_nasta_ar=?
                 WHERE id=?''',
              (bolag, kurs, pe[0], pe[1], pe[2], pe[3], ps[0], ps[1], ps[2], ps[3], vinst_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar, bolag_id))
    conn.commit()

def radera_bolag(bolag_id):
    c.execute("DELETE FROM bolag WHERE id=?", (bolag_id,))
    conn.commit()

# --- Beräkningsfunktioner ---
def berakna_genomsnitt(lista):
    rensad = [x for x in lista if x > 0]
    return sum(rensad) / len(rensad) if rensad else 0

def berakna_targetkurs(kurs, pe_list, ps_list, vinst_ar, vinst_nasta_ar):
    pe_avg = berakna_genomsnitt(pe_list)
    ps_avg = berakna_genomsnitt(ps_list)

    # Targetkurs baserat på P/E
    target_pe_i_ar = pe_avg * vinst_ar if pe_avg > 0 else 0
    target_pe_nasta_ar = pe_avg * vinst_nasta_ar if pe_avg > 0 else 0

    # Targetkurs baserat på P/S
    target_ps_i_ar = ps_avg * vinst_ar if ps_avg > 0 else 0
    target_ps_nasta_ar = ps_avg * vinst_nasta_ar if ps_avg > 0 else 0

    # Genomsnitt av P/E och P/S targetkurser
    target_avg_i_ar = (target_pe_i_ar + target_ps_i_ar) / 2 if target_pe_i_ar > 0 and target_ps_i_ar > 0 else max(target_pe_i_ar, target_ps_i_ar)
    target_avg_nasta_ar = (target_pe_nasta_ar + target_ps_nasta_ar) / 2 if target_pe_nasta_ar > 0 and target_ps_nasta_ar > 0 else max(target_pe_nasta_ar, target_ps_nasta_ar)

    return {
        'target_pe_i_ar': target_pe_i_ar,
        'target_pe_nasta_ar': target_pe_nasta_ar,
        'target_ps_i_ar': target_ps_i_ar,
        'target_ps_nasta_ar': target_ps_nasta_ar,
        'target_avg_i_ar': target_avg_i_ar,
        'target_avg_nasta_ar': target_avg_nasta_ar
    }

def berakna_undervardering(nuvarande_kurs, target_kurs):
    if target_kurs == 0:
        return 0
    diff = target_kurs - nuvarande_kurs
    procent = (diff / nuvarande_kurs) * 100
    return procent

# --- UI/Streamlit app ---
st.title("📈 Enkel Aktieanalysapp")

# --- Lägg till nytt bolag ---
st.header("➕ Lägg till nytt bolag")

with st.form("add_form", clear_on_submit=True):
    bolag = st.text_input("Bolagsnamn")
    kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")

    st.markdown("**P/E de 4 senaste:**")
    pe = [st.number_input(f"P/E år {i+1}", min_value=0.0, format="%.2f", key=f"pe_add_{i}") for i in range(4)]

    st.markdown("**P/S de 4 senaste:**")
    ps = [st.number_input(f"P/S år {i+1}", min_value=0.0, format="%.2f", key=f"ps_add_{i}") for i in range(4)]

    vinst_i_ar = st.number_input("Vinstprognos i år", min_value=0.0, format="%.2f")
    vinst_nasta_ar = st.number_input("Vinstprognos nästa år", min_value=0.0, format="%.2f")
    oms_i_ar = st.number_input("Omsättningstillväxt i år (%)", min_value=0.0, format="%.2f")
    oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år (%)", min_value=0.0, format="%.2f")

    submit = st.form_submit_button("💾 Lägg till bolag")

    if submit:
        bolag_clean = safe_str(bolag).capitalize()
        if bolag_clean == "":
            st.warning("Ange ett bolagsnamn!")
        else:
            lyckades = lagg_till_bolag(bolag_clean, kurs, pe, ps, vinst_i_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar)
            if lyckades:
                st.success(f"✅ Bolag {bolag_clean} tillagt!")
            else:
                st.error("Bolaget finns redan!")

# --- Visa sparade bolag med beräkningar ---
st.header("📊 Sparade bolag och värdering")

df = hamta_allt()

if df.empty:
    st.info("Inga bolag sparade ännu.")
else:
    # Lägg till beräkningar till DataFrame
    resultat = []
    for i, row in df.iterrows():
        pe_list = [row['pe1'], row['pe2'], row['pe3'], row['pe4']]
        ps_list = [row['ps1'], row['ps2'], row['ps3'], row['ps4']]

        target = berakna_targetkurs(row['nuvarande_kurs'], pe_list, ps_list, row['vinst_ar'], row['vinst_nasta_ar'])
        undervardering_avg = berakna_undervardering(row['nuvarande_kurs'], target['target_avg_i_ar'])

        resultat.append({
            'bolag': row['bolag'],
            'kurs': row['nuvarande_kurs'],
            'target_pe_i_ar': target['target_pe_i_ar'],
            'target_ps_i_ar': target['target_ps_i_ar'],
            'target_avg_i_ar': target['target_avg_i_ar'],
            'undervardering_%': undervardering_avg,
            'id': row['id']
        })

    df_result = pd.DataFrame(resultat)

    # Sortera efter undervärdering (största först)
    df_result = df_result.sort_values(by='undervardering_%', ascending=False)

    # Filter för minst 30% undervärdering
    filter_undervarderade = st.checkbox("Visa endast bolag med minst 30% undervärdering", value=False)

    if filter_undervarderade:
        df_result = df_result[df_result['undervardering_%'] >= 30]

    # Visa tabell
    st.dataframe(df_result.style.format({
        'kurs': "{:.2f}",
        'target_pe_i_ar': "{:.2f}",
        'target_ps_i_ar': "{:.2f}",
        'target_avg_i_ar': "{:.2f}",
        'undervardering_%': "{:.2f} %"
    }), height=300)

# --- Redigera bolag ---
st.header("✏️ Redigera sparade bolag")

if not df.empty:
    val = st.selectbox("Välj bolag att redigera", df['bolag'].tolist())

    if val:
        bolag_data = df[df['bolag'] == val].iloc[0]

        with st.form("edit_form"):
            bolag_id = bolag_data['id']
            bolag = st.text_input("Bolagsnamn", value=safe_str(bolag_data['bolag']), key="edit_bolag")
            kurs = st.number_input("Nuvarande kurs", min_value=0.0, value=safe_float(bolag_data['nuvarande_kurs']), key="edit_kurs")

            pe = [
                st.number_input(f"P/E år {i+1}", min_value=0.0, value=safe_float(bolag_data[f'pe{i+1}']), key=f"edit_pe{i+1}")
                for i in range(4)
            ]
            ps = [
                st.number_input(f"P/S år {i+1}", min_value=0.0, value=safe_float(bolag_data[f'ps{i+1}']), key=f"edit_ps{i+1}")
                for i in range(4)
            ]

            vinst_i_ar = st.number_input("Vinstprognos i år", min_value=0.0, value=safe_float(bolag_data['vinst_ar']), key="edit_vinst_i_ar")
            vinst_nasta_ar = st.number_input("Vinstprognos nästa år", min_value=0.0, value=safe_float(bolag_data['vinst_nasta_ar']), key="edit_vinst_nasta_ar")
            oms_i_ar = st.number_input("Omsättningstillväxt i år (%)", min_value=0.0, value=safe_float(bolag_data['oms_i_ar']), key="edit_oms_i_ar")
            oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år (%)", min_value=0.0, value=safe_float(bolag_data['oms_nasta_ar']), key="edit_oms_nasta_ar")

            uppdatera = st.form_submit_button("💾 Uppdatera bolag")

            if uppdatera:
                bolag_clean = safe_str(bolag).capitalize()
                if bolag_clean == "":
                    st.warning("Ange ett bolagsnamn!")
                else:
                    uppdatera_bolag(bolag_id, bolag_clean, kurs, pe, ps, vinst_i_ar, vinst_nasta_ar, oms_i_ar, oms_nasta_ar)
                    st.success(f"✅ {bolag_clean} uppdaterat!")
                    st.experimental_rerun()
else:
    st.info("Inga bolag att visa/redigera ännu.")
