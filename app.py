import streamlit as st
import sqlite3
import pandas as pd

# --- Hjälpfunktioner ---
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

def berakna_targetkurs(kurs, pe_list, ps_list, vinst_ar, vinst_nasta_ar):
    pe_avg = berakna_genomsnitt(pe_list)
    ps_avg = berakna_genomsnitt(ps_list)

    target_pe_i_ar = pe_avg * vinst_ar if pe_avg > 0 else 0
    target_pe_nasta_ar = pe_avg * vinst_nasta_ar if pe_avg > 0 else 0

    target_ps_i_ar = ps_avg * vinst_ar if ps_avg > 0 else 0
    target_ps_nasta_ar = ps_avg * vinst_nasta_ar if ps_avg > 0 else 0

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

# --- Appen ---
st.title("📈 Enkel Aktieanalysapp")

# Lägg till bolag
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

# Visa sparade bolag
st.header("📊 Undervärderade bolag med minst 30% undervärdering")

df = hamta_allt()

if df.empty:
    st.info("Inga bolag sparade ännu.")
else:
    resultat = []
    for i, row in df.iterrows():
        pe_list = [row['pe1'], row['pe2'], row['pe3'], row['pe4']]
        ps_list = [row['ps1'], row['ps2'], row['ps3'], row['ps4']]

        target = berakna_targetkurs(row['nuvarande_kurs'], pe_list, ps_list, row['vinst_ar'], row['vinst_nasta_ar'])
        undervardering_avg = berakna_undervardering(row['nuvarande_kurs'], target['target_avg_i_ar'])

        if undervardering_avg >= 30:
            resultat.append({
                'Bolag': row['bolag'],
                'Nuvarande kurs': row['nuvarande_kurs'],
                'Target P/E i år': target['target_pe_i_ar'],
                'Target P/S i år': target['target_ps_i_ar'],
                'Target Genomsnitt i år': target['target_avg_i_ar'],
                'Undervärdering (%)': undervardering_avg,
            })

    if not resultat:
        st.info("Inga bolag är undervärderade med minst 30%.")
    else:
        # Sortera efter undervärdering största först
        resultat = sorted(resultat, key=lambda x: x['Undervärdering (%)'], reverse=True)

        # Bygg tabell i markdown med lite färg för undervärdering
        st.markdown(
            """
            <style>
                .table-container {
                    max-width: 900px;
                    overflow-x: auto;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                    font-family: Arial, sans-serif;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: center;
                }
                th {
                    background-color: #004080;
                    color: white;
                }
                tr:nth-child(even){background-color: #f2f2f2;}
                tr:hover {background-color: #ddd;}
                .green {
                    background-color: #d4edda;
                    color: #155724;
                    font-weight: bold;
                }
            </style>
            """, unsafe_allow_html=True
        )

        rows_md = ""
        for bolag in resultat:
            underv = bolag['Undervärdering (%)']
            underv_class = "green" if underv >= 30 else ""
            rows_md += f"""
            <tr class="{underv_class}">
                <td>{bolag['Bolag']}</td>
                <td>{bolag['Nuvarande kurs']:.2f}</td>
                <td>{bolag['Target P/E i år']:.2f}</td>
                <td>{bolag['Target P/S i år']:.2f}</td>
                <td>{bolag['Target Genomsnitt i år']:.2f}</td>
                <td>{underv:.2f} %</td>
            </tr>
            """

        st.markdown(f"""
        <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Bolag</th>
                    <th>Nuvarande kurs</th>
                    <th>Target P/E i år</th>
                    <th>Target P/S i år</th>
                    <th>Target Genomsnitt i år</th>
                    <th>Undervärdering (%)</th>
                </tr>
            </thead>
            <tbody>
                {rows_md}
            </tbody>
        </table>
        </div>
        """, unsafe_allow_html=True)
