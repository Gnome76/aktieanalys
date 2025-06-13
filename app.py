def main():
    init_db()
    st.title("📊 Aktieanalys – Enkel version")

    st.subheader("➕ Lägg till nytt bolag")

    with st.form("nytt_bolag_form"):
        bolag = st.text_input("Bolagsnamn")
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")
        pe1 = st.number_input("P/E -4 år")
        pe2 = st.number_input("P/E -3 år")
        pe3 = st.number_input("P/E -2 år")
        pe4 = st.number_input("P/E -1 år")
        ps1 = st.number_input("P/S -4 år")
        ps2 = st.number_input("P/S -3 år")
        ps3 = st.number_input("P/S -2 år")
        ps4 = st.number_input("P/S -1 år")
        vinst_ar = st.number_input("Vinst i år")
        vinst_nasta_ar = st.number_input("Vinst nästa år")
        oms_i_ar = st.number_input("Omsättning i år")
        oms_nasta_ar = st.number_input("Omsättning nästa år")

        submit = st.form_submit_button("💾 Spara bolag")
        if submit:
            if bolag.strip() == "":
                st.error("⚠️ Ange bolagsnamn.")
            else:
                data = (
                    bolag.strip(), nuvarande_kurs,
                    pe1, pe2, pe3, pe4,
                    ps1, ps2, ps3, ps4,
                    vinst_ar, vinst_nasta_ar,
                    oms_i_ar, oms_nasta_ar
                )
                add_or_update_bolag(data)
                st.success(f"✅ '{bolag}' har sparats!")

    st.subheader("📈 Alla bolag")

    rows = get_all_bolag()
    if rows:
        df = pd.DataFrame(rows, columns=[
            "Bolag", "Nuvarande kurs",
            "P/E 1", "P/E 2", "P/E 3", "P/E 4",
            "P/S 1", "P/S 2", "P/S 3", "P/S 4",
            "Vinst i år", "Vinst nästa år",
            "Omsättning i år", "Omsättning nästa år"
        ])

        df["P/E snitt"] = df[["P/E 1", "P/E 2", "P/E 3", "P/E 4"]].mean(axis=1)
        df["P/S snitt"] = df[["P/S 1", "P/S 2", "P/S 3", "P/S 4"]].mean(axis=1)
        df["Target P/E"] = df["P/E snitt"] * df["Vinst nästa år"]
        df["Target P/S"] = df["P/S snitt"] * df["Omsättning nästa år"]
        df["Target snitt"] = (df["Target P/E"] + df["Target P/S"]) / 2
        df["Undervärdering (%)"] = ((df["Target snitt"] - df["Nuvarande kurs"]) / df["Nuvarande kurs"]) * 100

        st.dataframe(df[[
            "Bolag", "Nuvarande kurs", "Target P/E", "Target P/S", "Target snitt", "Undervärdering (%)"
        ]].set_index("Bolag"), use_container_width=True)
    else:
        st.info("Inga bolag sparade ännu.")
