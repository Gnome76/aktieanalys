def main():
    st.title("Aktieinnehav - Spara och analysera")

    init_db()

    # Formulär för att lägga till nytt bolag
    with st.form("form_lagg_till_bolag", clear_on_submit=True):
        namn = st.text_input("Bolagsnamn (unik)")
        nuvarande_kurs = st.number_input("Nuvarande kurs", min_value=0.0, format="%.2f")
        pe1 = st.number_input("P/E (år 1)", min_value=0.0, format="%.2f")
        pe2 = st.number_input("P/E (år 2)", min_value=0.0, format="%.2f")
        pe3 = st.number_input("P/E (år 3)", min_value=0.0, format="%.2f")
        pe4 = st.number_input("P/E (år 4)", min_value=0.0, format="%.2f")
        ps1 = st.number_input("P/S (år 1)", min_value=0.0, format="%.2f")
        ps2 = st.number_input("P/S (år 2)", min_value=0.0, format="%.2f")
        ps3 = st.number_input("P/S (år 3)", min_value=0.0, format="%.2f")
        ps4 = st.number_input("P/S (år 4)", min_value=0.0, format="%.2f")
        vinst_arsprognos = st.number_input("Vinst prognos i år", format="%.2f")
        vinst_nastaar = st.number_input("Vinst prognos nästa år", format="%.2f")
        omsattningstillvaxt_arsprognos = st.number_input("Omsättningstillväxt i år (%)", format="%.2f")
        omsattningstillvaxt_nastaar = st.number_input("Omsättningstillväxt nästa år (%)", format="%.2f")

        lagg_till = st.form_submit_button("Lägg till bolag")

        if lagg_till:
            if namn.strip() == "":
                st.error("Bolagsnamn måste anges.")
            else:
                data = (
                    namn.strip(),
                    nuvarande_kurs,
                    pe1, pe2, pe3, pe4,
                    ps1, ps2, ps3, ps4,
                    vinst_arsprognos,
                    vinst_nastaar,
                    omsattningstillvaxt_arsprognos,
                    omsattningstillvaxt_nastaar,
                )
                spara_bolag(data)
                st.success(f"Bolag '{namn}' sparat!")
                st.rerun()

    # Visa sparade bolag
    bolag = hamta_alla_bolag()
    if bolag:
        df = pd.DataFrame(
            bolag,
            columns=[
                "namn",
                "nuvarande_kurs",
                "pe1", "pe2", "pe3", "pe4",
                "ps1", "ps2", "ps3", "ps4",
                "vinst_arsprognos",
                "vinst_nastaar",
                "omsattningstillvaxt_arsprognos",
                "omsattningstillvaxt_nastaar"
            ],
        )

        # Sökfunktion
        sok_text = st.text_input("Sök bolag (namn)")
        if sok_text:
            df = df[df["namn"].str.contains(sok_text, case=False, na=False)]

        # Beräkna target och undervärdering
        target_lista = []
        for _, row in df.iterrows():
            resultat = berakna_targetkurs(
                [row.pe1, row.pe2, row.pe3, row.pe4],
                [row.ps1, row.ps2, row.ps3, row.ps4],
                row.vinst_arsprognos,
                row.vinst_nastaar,
                row.nuvarande_kurs,
            )
            target_lista.append(resultat)

        df_target = pd.DataFrame(target_lista)
        df_display = pd.concat([df.reset_index(drop=True), df_target], axis=1)

        st.subheader("Alla sparade bolag")
        st.dataframe(df_display[[
            "namn",
            "nuvarande_kurs",
            "target_pe_ars",
            "target_pe_nastaar",
            "target_ps_ars",
            "target_ps_nastaar",
            "target_genomsnitt_ars",
            "target_genomsnitt_nastaar",
            "undervardering_pe_ars",
            "undervardering_pe_nastaar",
            "undervardering_genomsnitt_ars",
            "undervardering_genomsnitt_nastaar",
        ]].style.format({
            "nuvarande_kurs": "{:.2f}",
            "target_pe_ars": "{:.2f}",
            "target_pe_nastaar": "{:.2f}",
            "target_ps_ars": "{:.2f}",
            "target_ps_nastaar": "{:.2f}",
            "target_genomsnitt_ars": "{:.2f}",
            "target_genomsnitt_nastaar": "{:.2f}",
            "undervardering_pe_ars": "{:.0%}",
            "undervardering_pe_nastaar": "{:.0%}",
            "undervardering_genomsnitt_ars": "{:.0%}",
            "undervardering_genomsnitt_nastaar": "{:.0%}",
        }))

        # Filter för undervärderade bolag minst 30%
        if st.checkbox("Visa bara bolag minst 30% undervärderade (genomsnitt target år i år)"):
            undervarderade = df_display[
                (df_display["undervardering_genomsnitt_ars"] >= 0.3)
                | (df_display["undervardering_genomsnitt_nastaar"] >= 0.3)
            ]

            undervarderade = undervarderade.sort_values(
                by=["undervardering_genomsnitt_ars", "undervardering_genomsnitt_nastaar"], ascending=False
            )

            if not undervarderade.empty:
                st.subheader("Undervärderade bolag (≥30%)")
                st.dataframe(undervarderade[[
                    "namn",
                    "nuvarande_kurs",
                    "target_genomsnitt_ars",
                    "target_genomsnitt_nastaar",
                    "undervardering_genomsnitt_ars",
                    "undervardering_genomsnitt_nastaar"
                ]].style.format({
                    "nuvarande_kurs": "{:.2f}",
                    "target_genomsnitt_ars": "{:.2f}",
                    "target_genomsnitt_nastaar": "{:.2f}",
                    "undervardering_genomsnitt_ars": "{:.0%}",
                    "undervardering_genomsnitt_nastaar": "{:.0%}",
                }))
            else:
                st.info("Inga bolag är minst 30% undervärderade just nu.")

        # Ta bort bolag - dropdown och knapp
        st.subheader("Ta bort bolag")
        namn_radera = st.selectbox("Välj bolag att ta bort", options=df["namn"])
        if st.button("Ta bort valt bolag"):
            ta_bort_bolag(namn_radera)
            st.success(f"Bolag '{namn_radera}' borttaget.")
            st.rerun()

    else:
        st.info("Inga bolag sparade ännu.")
