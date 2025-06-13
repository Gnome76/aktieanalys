import streamlit as st
import sqlite3

# --- Databasfunktioner ---

DB_NAME = "aktier.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS bolag (
        bolag TEXT PRIMARY KEY,
        nuvarande_kurs REAL,
        pe1 REAL, pe2 REAL, pe3 REAL, pe4 REAL,
        ps1 REAL, ps2 REAL, ps3 REAL, ps4 REAL,
        vinst_ar REAL,
        vinst_nasta_ar REAL,
        oms_i_ar REAL,
        oms_nasta_ar REAL
    )
    ''')
    conn.commit()
    conn.close()

def add_or_update_bolag(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
    INSERT INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(bolag) DO UPDATE SET
        nuvarande_kurs=excluded.nuvarande_kurs,
        pe1=excluded.pe1,
        pe2=excluded.pe2,
        pe3=excluded.pe3,
        pe4=excluded.pe4,
        ps1=excluded.ps1,
        ps2=excluded.ps2,
        ps3=excluded.ps3,
        ps4=excluded.ps4,
        vinst_ar=excluded.vinst_ar,
        vinst_nasta_ar=excluded.vinst_nasta_ar,
        oms_i_ar=excluded.oms_i_ar,
        oms_nasta_ar=excluded.oms_nasta_ar
    ''', data)
    conn.commit()
    conn.close()

def get_all_bolag():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM bolag ORDER BY bolag')
    rows = c.fetchall()
    conn.close()
    return rows

def delete_bolag(bolagsnamn):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM bolag WHERE bolag=?', (bolagsnamn,))
    conn.commit()
    conn.close()

# --- Beräkningar ---

def genomsnitt(values):
    vals = [v for v in values if v is not None]
    return sum(vals)/len(vals) if vals else None

def targetkurs_pe(pe_values, vinst):
    pe_avg = genomsnitt(pe_values)
    if pe_avg is None or vinst is None:
        return None
    return pe_avg * vinst

def targetkurs_ps(ps_values, oms):
    ps_avg = genomsnitt(ps_values)
    if ps_avg is None or oms is None:
        return None
    return ps_avg * oms

# --- Streamlit UI ---

st.title("Aktieanalys med databashantering")

init_db()

# --- Lägg till eller redigera bolag ---
with st.form("form_lagg_till"):
    st.subheader("Lägg till eller uppdatera bolag")

    bolag = st.text_input("Bolagsnamn (unik identifierare)").strip()
    nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")
    
    pe1 = st.number_input("P/E år -4", min_value=0.0, format="%.2f")
    pe2 = st.number_input("P/E år -3", min_value=0.0, format="%.2f")
    pe3 = st.number_input("P/E år -2", min_value=0.0, format="%.2f")
    pe4 = st.number_input("P/E år -1", min_value=0.0, format="%.2f")
    
    ps1 = st.number_input("P/S år -4", min_value=0.0, format="%.2f")
    ps2 = st.number_input("P/S år -3", min_value=0.0, format="%.2f")
    ps3 = st.number_input("P/S år -2", min_value=0.0, format="%.2f")
    ps4 = st.number_input("P/S år -1", min_value=0.0, format="%.2f")

    vinst_ar = st.number_input("Vinst prognos i år", format="%.2f")
    vinst_nasta_ar = st.number_input("Vinst prognos nästa år", format="%.2f")

    oms_i_ar = st.number_input("Omsättningstillväxt i år", format="%.2f")
    oms_nasta_ar = st.number_input("Omsättningstillväxt nästa år", format="%.2f")

    submitted = st.form_submit_button("Spara bolag")

    if submitted:
        if bolag == "":
            st.error("Du måste ange bolagsnamn!")
        else:
            data = (
                bolag,
                nuvarande_kurs,
                pe1, pe2, pe3, pe4,
                ps1, ps2, ps3, ps4,
                vinst_ar,
                vinst_nasta_ar,
                oms_i_ar,
                oms_nasta_ar
            )
            add_or_update_bolag(data)
            st.success(f"Bolaget '{bolag}' sparat/uppdaterat!")
            st.experimental_rerun()

# --- Visa bolag ---

st.markdown("---")
st.subheader("Alla bolag i databasen")

alla_bolag = get_all_bolag()

if not alla_bolag:
    st.info("Inga bolag sparade ännu.")
else:
    # Filterknapp
    filter_undervarderade = st.checkbox("Visa endast bolag undervärderade minst 30%")

    # Beräkna targetkurser och undervärdering
    bolag_data = []
    for row in alla_bolag:
        (
            bolag, kurs, pe1, pe2, pe3, pe4,
            ps1, ps2, ps3, ps4,
            vinst_ar, vinst_nasta_ar,
            oms_i_ar, oms_nasta_ar
        ) = row

        pe_vals = [pe1, pe2, pe3, pe4]
        ps_vals = [ps1, ps2, ps3, ps4]

        # Targetkurser
        target_pe_ar = targetkurs_pe(pe_vals, vinst_ar)
        target_pe_nasta_ar = targetkurs_pe(pe_vals, vinst_nasta_ar)
        target_ps_ar = targetkurs_ps(ps_vals, oms_i_ar)
        target_ps_nasta_ar = targetkurs_ps(ps_vals, oms_nasta_ar)

        # Genomsnitt targetkurs (PE + PS)
        targets = [t for t in [target_pe_ar, target_pe_nasta_ar, target_ps_ar, target_ps_nasta_ar] if t is not None]
        target_genomsnitt = sum(targets)/len(targets) if targets else None

        # Undervärdering % utifrån target_genomsnitt
        if target_genomsnitt is not None:
            undervardering_pct = (target_genomsnitt - kurs) / kurs * 100
        else:
            undervardering_pct = None

        bolag_data.append({
            "bolag": bolag,
            "kurs": kurs,
            "target_pe_ar": target_pe_ar,
            "target_pe_nasta_ar": target_pe_nasta_ar,
            "target_ps_ar": target_ps_ar,
            "target_ps_nasta_ar": target_ps_nasta_ar,
            "target_genomsnitt": target_genomsnitt,
            "undervardering_pct": undervardering_pct
        })

    # Filtrera undervärderade minst 30%
    if filter_undervarderade:
        bolag_data = [b for b in bolag_data if b["undervardering_pct"] is not None and b["undervardering_pct"] >= 30]
        bolag_data = sorted(bolag_data, key=lambda x: x["undervardering_pct"], reverse=True)

    # Visa i tabell med snygg styling
    import pandas as pd
    df = pd.DataFrame(bolag_data)
    if not df.empty:
        # Format tal med två decimaler
        df_display = df.copy()
        df_display["kurs"] = df_display["kurs"].map("{:.2f}".format)
        df_display["target_pe_ar"] = df_display["target_pe_ar"].map(lambda x: f"{x:.2f}" if x else "-")
        df_display["target_pe_nasta_ar"] = df_display["target_pe_nasta_ar"].map(lambda x: f"{x:.2f}" if x else "-")
        df_display["target_ps_ar"] = df_display["target_ps_ar"].map(lambda x: f"{x:.2f}" if x else "-")
        df_display["target_ps_nasta_ar"] = df_display["target_ps_nasta_ar"].map(lambda x: f"{x:.2f}" if x else "-")
        df_display["target_genomsnitt"] = df_display["target_genomsnitt"].map(lambda x: f"{x:.2f}" if x else "-")
        df_display["undervardering_pct"] = df_display["undervardering_pct"].map(lambda x: f"{x:.1f}%" if x else "-")

        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Inga bolag att visa med valt filter.")

# --- Redigera eller ta bort bolag ---

st.markdown("---")
st.subheader("Redigera eller ta bort bolag")

alla_bolag_namn = [b[0] for b in alla_bolag]

val_bolag = st.selectbox("Välj bolag att redigera eller ta bort", options=alla_bolag_namn)

if val_bolag:
    # Hämta bolagets data
    val_data = next(b for b in alla_bolag if b[0] == val_bolag)

    with st.form("form_redigera"):
        st.write(f"Redigera data för: **{val_bolag}**")

        nuvarande_kurs_e = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f", value=val_data[1])
        pe1_e = st.number_input("P/E år -4", min_value=0.0, format="%.2f", value=val_data[2])
        pe2_e = st.number_input("P/E år -3", min_value=0.0, format="%.2f", value=val_data[3])
        pe3_e = st.number_input("P/E år -2", min_value=0.0, format="%.2f", value=val_data[4])
        pe4_e = st.number_input("P/E år -1", min_value=0.0, format="%.2f", value=val_data[5])

        ps1_e = st.number_input("P/S år -4", min_value=0.0, format="%.2f", value=val_data[6])
        ps2_e = st.number_input("P/S år -3", min_value=0.0, format="%.2f", value=val_data[7])
        ps3_e = st.number_input("P/S år -2", min_value=0.0, format="%.2f", value=val_data[8])
        ps4_e = st.number_input("P/S år -1", min_value=0.0, format="%.2f", value=val_data[9])

        vinst_ar_e = st.number_input("Vinst prognos i år", format="%.2f", value=val_data[10])
        vinst_nasta_ar_e = st.number_input("Vinst prognos nästa år", format="%.2f", value=val_data[11])

        oms_i_ar_e = st.number_input("Omsättningstillväxt i år", format="%.2f", value=val_data[12])
        oms_nasta_ar_e = st.number_input("Omsättningstillväxt nästa år", format="%.2f", value=val_data[13])

        uppdatera = st.form_submit_button("Uppdatera bolag")
        ta_bort = st.form_submit_button("Ta bort bolag")

        if uppdatera:
            ny_data = (
                val_bolag,
                nuvarande_kurs_e,
                pe1_e, pe2_e, pe3_e, pe4_e,
                ps
