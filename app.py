import streamlit as st
import pandas as pd
from datetime import datetime
import os

DB_FILE = "aktier.csv"

# Ladda data eller skapa tom df med rätt kolumner
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Säkerställ att kolumn insatt_datum finns
        if "insatt_datum" not in df.columns:
            df["insatt_datum"] = ""
    else:
        df = pd.DataFrame(columns=[
            "namn", "inkop", "target", "pe1", "pe2", "ps1", "ps2", 
            "ev_ebit", "p_bok", "skuldsattning", "insatt_datum"
        ])
    return df

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def main():
    st.title("Aktieanalysapp med redigering")

    df = load_data()

    menu = st.sidebar.radio("Välj funktion:", ["Visa bolag", "Lägg till bolag", "Redigera bolag", "Ta bort bolag"])

    if menu == "Visa bolag":
        st.subheader("Alla bolag")
        if df.empty:
            st.info("Inga bolag i databasen.")
        else:
            st.dataframe(df.sort_values("namn"))

    elif menu == "Lägg till bolag":
        st.subheader("Lägg till nytt bolag")
        with st.form("add_form"):
            namn = st.text_input("Bolagsnamn")
            inkop = st.number_input("Inköpspris", min_value=0.0, format="%.2f")
            target = st.number_input("Targetpris", min_value=0.0, format="%.2f")
            pe1 = st.number_input("P/E (år 1)", min_value=0.0, format="%.2f")
            pe2 = st.number_input("P/E (år 2)", min_value=0.0, format="%.2f")
            ps1 = st.number_input("P/S (år 1)", min_value=0.0, format="%.2f")
            ps2 = st.number_input("P/S (år 2)", min_value=0.0, format="%.2f")
            ev_ebit = st.number_input("EV/EBIT", min_value=0.0, format="%.2f")
            p_bok = st.number_input("P/Bok", min_value=0.0, format="%.2f")
            skuldsattning = st.number_input("Skuldsättning", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Spara bolag")

            if submitted:
                if namn.strip() == "":
                    st.error("Bolagsnamn får inte vara tomt.")
                elif namn in df["namn"].values:
                    st.error("Bolaget finns redan. Använd redigera istället.")
                else:
                    ny_rad = {
                        "namn": namn.strip(),
                        "inkop": inkop,
                        "target": target,
                        "pe1": pe1,
                        "pe2": pe2,
                        "ps1": ps1,
                        "ps2": ps2,
                        "ev_ebit": ev_ebit,
                        "p_bok": p_bok,
                        "skuldsattning": skuldsattning,
                        "insatt_datum": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                    df = df.append(ny_rad, ignore_index=True)
                    save_data(df)
                    st.success(f"Bolag '{namn}' sparat.")

    elif menu == "Redigera bolag":
        st.subheader("Redigera befintligt bolag")
        if df.empty:
            st.info("Inga bolag att redigera.")
        else:
            valt_bolag = st.selectbox("Välj bolag att redigera", df["namn"].sort_values())
            if valt_bolag:
                bolagsrad = df[df["namn"] == valt_bolag].iloc[0]

                with st.form("edit_form"):
                    inkop = st.number_input("Inköpspris", value=float(bolagsrad["inkop"]), format="%.2f")
                    target = st.number_input("Targetpris", value=float(bolagsrad["target"]), format="%.2f")
                    pe1 = st.number_input("P/E (år 1)", value=float(bolagsrad["pe1"]), format="%.2f")
                    pe2 = st.number_input("P/E (år 2)", value=float(bolagsrad["pe2"]), format="%.2f")
                    ps1 = st.number_input("P/S (år 1)", value=float(bolagsrad["ps1"]), format="%.2f")
                    ps2 = st.number_input("P/S (år 2)", value=float(bolagsrad["ps2"]), format="%.2f")
                    ev_ebit = st.number_input("EV/EBIT", value=float(bolagsrad["ev_ebit"]), format="%.2f")
                    p_bok = st.number_input("P/Bok", value=float(bolagsrad["p_bok"]), format="%.2f")
                    skuldsattning = st.number_input("Skuldsättning", value=float(bolagsrad["skuldsattning"]), format="%.2f")
                    submitted = st.form_submit_button("Spara ändringar")

                    if submitted:
                        idx = df.index[df["namn"] == valt_bolag][0]
                        df.at[idx, "inkop"] = inkop
                        df.at[idx, "target"] = target
                        df.at[idx, "pe1"] = pe1
                        df.at[idx, "pe2"] = pe2
                        df.at[idx, "ps1"] = ps1
                        df.at[idx, "ps2"] = ps2
                        df.at[idx, "ev_ebit"] = ev_ebit
                        df.at[idx, "p_bok"] = p_bok
                        df.at[idx, "skuldsattning"] = skuldsattning
                        # Uppdatera datumet vid redigering
                        df.at[idx, "insatt_datum"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        save_data(df)
                        st.success(f"Bolag '{valt_bolag}' uppdaterat.")

    elif menu == "Ta bort bolag":
        st.subheader("Ta bort bolag")
        if df.empty:
            st.info("Inga bolag att ta bort.")
        else:
            # Två rullistor: Alfabetisk och efter insättningsdatum (äldsta först)
            st.markdown("### Välj bolag att ta bort (alfabetisk ordning)")
            valt_bolag_alf = st.selectbox("Bolag (A-Ö)", df["namn"].sort_values())

            st.markdown("### Välj bolag att ta bort (datumordning, äldsta först)")
            df_sorted = df.sort_values("insatt_datum")
            options_datum = df_sorted.apply(lambda r: f"{r['namn']} (insatt: {r['insatt_datum']})", axis=1).tolist()
            valt_bolag_datum = st.selectbox("Bolag (datum)", options_datum)

            # Ta bort från alfabetisk lista
            if st.button("Ta bort valt bolag (alfabetisk)"):
                df = df[df["namn"] != valt_bolag_alf]
                save_data(df)
                st.success(f"Bolaget '{valt_bolag_alf}' är borttaget.")

            # Ta bort från datumlista
            if st.button("Ta bort valt bolag (datum)"):
                # Extrahera namn från texten i datumlistan
                namn = valt_bolag_datum.split(" (")[0]
                df = df[df["namn"] != namn]
                save_data(df)
                st.success(f"Bolaget '{namn}' är borttaget.")

if __name__ == "__main__":
    main()
