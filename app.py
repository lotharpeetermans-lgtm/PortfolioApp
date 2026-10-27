import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
from streamlit_calendar import calendar
import json

from auth import (
    registreer_gebruiker,
    login_user
)

from transactions import (
    voeg_transactie_toe,
    haal_transacties_op,
    bereken_posities,
    verrijk_posities_met_koersen,
    verwijder_transactie
)


# ===================================
# PAGINA
# ===================================

st.set_page_config(
    page_title="Beyond Beleggingen",
    page_icon="📈",
    layout="wide"
)

if "user_id" not in st.session_state:

    st.title("📈 Beyond Beleggingen")

    col1, col2 = st.columns([8, 1])

    with col2:

        if st.button("🚪 Uitloggen"):

            st.session_state.clear()

            st.rerun()
    
    login_tab, register_tab = st.tabs(
        [
            "🔐 Inloggen",
            "📝 Registreren"
        ]
    )

    with login_tab:

        email = st.text_input(
            "E-mail",
            key="login_email"
        )

        wachtwoord = st.text_input(
            "Wachtwoord",
            type="password",
            key="login_password"
        )

        if st.button("🔓 Inloggen"):

            gebruiker = login_user(
                email,
                wachtwoord
            )

            if gebruiker:

                st.session_state.user_id = gebruiker["id"]
                st.session_state.user_name = gebruiker["naam"]

                st.success(
                    f"Welkom {gebruiker['naam']}!"
                )

                st.rerun()

            else:

                st.error(
                    "Onjuiste login."
                )

    with register_tab:

        naam = st.text_input(
            "Naam",
            key="register_naam"
        )

        email = st.text_input(
            "E-mail",
            key="register_email"
        )

        wachtwoord = st.text_input(
            "Wachtwoord",
            type="password",
            key="register_password"
        )

        if st.button("📝 Account aanmaken"):

            try:

                registreer_gebruiker(
                    naam,
                    email,
                    wachtwoord
                )

                st.success(
                    "Account aangemaakt. Je kan nu inloggen."
                )

            except Exception as e:

                st.error(
                    f"Fout: {e}"
                )

    st.stop()

with st.expander("📥 Bolero import (optioneel)"):

    uploaded_file = st.file_uploader(
        "Upload je Bolero-export",
        type=["xlsx"]
    )

if uploaded_file is not None:

    df = pd.read_excel(
        uploaded_file
    )

else:

    df = pd.DataFrame()

st.title("📈 Beyond Beleggingen")

if st.button("🔄 Portefeuille verversen"):

    st.cache_data.clear()

    st.rerun()

st.caption(
    f"🕒 Laatst vernieuwd: "
    f"{datetime.now().strftime('%H:%M:%S')}"
)

if uploaded_file is not None:

    st.caption(
        f"📂 Actieve export: {uploaded_file.name}"
    )

else:

    st.caption(
        "📂 Geen Bolero-export geladen"
    )

# ===================================
# TABS
# ===================================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "💰 Portefeuillebeheer",
        "📊 Dashboard",
        "💼 Posities",
        "📈 Analyse",
        "🤖 Koopkansen",
        "⚙️ Instellingen"
    ]
)

# ===================================
# TAB 1 - PORTEFEUILLEBEHEER
# ===================================

with tab1:

    st.subheader("🛒 Nieuwe transactie")

    datum = st.date_input(
        "Datum"
    )

    ticker = st.text_input(
        "Ticker"
    )

    transactie_type = st.selectbox(
        "Type",
        [
            "KOOP",
            "VERKOOP"
        ]
    )

    aantal = st.number_input(
        "Aantal",
        min_value=0.0,
        step=1.0
    )

    prijs = st.number_input(
        "Prijs",
        min_value=0.0
    )

    kosten = st.number_input(
        "Kosten",
        min_value=0.0
    )

    if st.button("💾 Transactie opslaan"):

        voeg_transactie_toe(
            st.session_state.user_id,
            str(datum),
            ticker.upper(),
            transactie_type,
            aantal,
            prijs,
            kosten
        )

        st.success(
            "✅ Transactie opgeslagen."
        )

        st.rerun()

    st.divider()

    st.subheader("📋 Transactiehistoriek")

    response = haal_transacties_op(
    st.session_state.user_id
)

if response.data:

    historiek_df = pd.DataFrame(
        response.data
    )

    historiek_df = historiek_df.sort_values(
        "datum",
        ascending=False
    )

    for _, row in historiek_df.iterrows():

        col1, col2, col3, col4, col5, col6, col7 = st.columns(
            [2, 2, 2, 2, 2, 2, 1]
        )

        col1.write(row["datum"])
        col2.write(row["ticker"])
        col3.write(row["type"])
        col4.write(row["aantal"])
        col5.write(f"€ {row['prijs']}")
        col6.write(f"€ {row['kosten']}")

        if col7.button(
            "🗑️",
            key=f"delete_{row['id']}"
        ):

            verwijder_transactie(
                row["id"]
            )

            st.success(
                "Transactie verwijderd."
            )

            st.rerun()

else:

    st.info(
        "Nog geen transacties aanwezig."
    )

# ===================================
# TAB 2
# ===================================

with tab2:

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Portefeuillewaarde",
        f"€ {totale_waarde:,.2f}"
    )

    col2.metric(
        "Resultaat",
        f"€ {totale_winst:,.2f}",
        f"{totale_winst_pct:+.2f}%"
    )

    col3.metric(
        "Inleg",
        f"€ {netto_inleg:,.2f}"
    )

    col4.metric(
        "Aandelen",
        aantal_aandelen
    )

    col5.metric(
        "ETF's",
        aantal_etfs
    )

    st.divider()

    st.subheader("🩺 Portefeuille Health Check")

    if grootste_positie["Gewicht %"] > 15:
        st.warning(
            f"Grootste positie: {grootste_positie['Naam']} "
            f"({grootste_positie['Gewicht %']:.2f}%)"
        )
    else:
        st.success(
            f"Grootste positie: {grootste_positie['Naam']} "
            f"({grootste_positie['Gewicht %']:.2f}%)"
        )

    if technologie_pct > 50:
        st.warning(
            f"Technologie weegt {technologie_pct:.2f}% van de portefeuille"
        )
    else:
        st.success(
            f"Technologie weegt {technologie_pct:.2f}% van de portefeuille"
        )

    st.info(
        f"ETF-aandeel portefeuille: {etf_pct:.2f}%"
    )

    st.success(
        f"Beste wereldwijde koopkans momenteel: {beste_koopkans}"
    )

    st.info(
        f"Verwacht dividend per jaar: "
        f"€ {df['Verwacht dividend €/jaar'].sum():,.2f}"
    )

    st.divider()

    st.subheader("🏆 Top 10 grootste posities")

    top10_posities = (
        df.sort_values(
            "Waarde in EUR",
            ascending=False
        )
        .head(10)
    )

    st.dataframe(
        formatteer_tabel(
            top10_posities[
                [
                    "Naam",
                    "Aantal",
                    "Gewicht %",
                    "Waarde in EUR",
                     "Winst/Verlies €",
                    "Realtime rendement %"
                ]
            ]
            .style.map(
                kleur,
                subset=[
                    "Winst/Verlies €",
                     "Realtime rendement %"
                ]
            )
        ),
        hide_index=True,
        use_container_width=True
    )

# ===================================
# TAB 3
# ===================================

with tab3:

    st.subheader("💼 Actuele Posities")

    posities_df = bereken_posities(
        st.session_state.user_id
    )

    posities_df = (
        verrijk_posities_met_koersen(
            posities_df
    )
)

    if posities_df.empty:

        st.info(
            "Nog geen open posities."
        )

    else:

        st.dataframe(
    posities_df.style.format(
        {
            "Gem. aankoopprijs":
                "€ {:.2f}",
            "Kostbasis":
                "€ {:.2f}",
            "Koers":
                "€ {:.2f}",
            "Marktwaarde":
                "€ {:.2f}",
            "Winst/Verlies":
                "€ {:.2f}",
            "Rendement %":
                "{:.2f}%"
        }
    ),
    hide_index=True,
    use_container_width=True
)

# ===================================
# TAB 4
# ===================================

with tab4:

    st.subheader("🏆 Top 5 winnaars (%)")

    winnaars = (
        df.sort_values(
            "Realtime rendement %",
            ascending=False
        )
        [[
            "Naam",
            "Aantal",
            "Realtime rendement %",
            "Winst/Verlies €"
        ]]
        .head(5)
    )

    st.dataframe(
        formatteer_tabel(
            winnaars.style.map(
                kleur,
                subset=[
                    "Realtime rendement %",
                    "Winst/Verlies €"
                ]
            )
        ),
        hide_index=True,
        use_container_width=True
    )

    st.subheader("📉 Top 5 verliezers (%)")

    verliezers = (
        df.sort_values(
            "Realtime rendement %",
            ascending=True
        )
        [[
            "Naam",
            "Aantal",
            "Realtime rendement %",
            "Winst/Verlies €"
        ]]
        .head(5)
    )

    st.dataframe(
        formatteer_tabel(
            verliezers.style.map(
                kleur,
                subset=[
                    "Realtime rendement %",
                    "Winst/Verlies €"
                ]
            )
        ),
        hide_index=True,
        use_container_width=True
    )

    st.divider()

    st.subheader("🏭 Sectorverdeling")

    sectoren = (
        df.groupby("Sector")["Waarde in EUR"]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    st.bar_chart(sectoren)

    st.divider()

    st.subheader("📊 Yahoo Analyses")

    keuze = st.selectbox(
        "Kies een aandeel of ETF",
        df["Naam"].sort_values().unique()
    )

    ticker = df.loc[
        df["Naam"] == keuze,
        "Ticker"
    ].iloc[0]

    if pd.notna(ticker):

        st.link_button(
           "📈 Open Yahoo Analyse",
           f"https://finance.yahoo.com/quote/{ticker}/analysis"
    )

        st.link_button(
           "💰 Open Yahoo Financiële gegevens",
           f"https://finance.yahoo.com/quote/{ticker}/financials"
    )

        st.link_button(
           "📊 Open Yahoo Statistieken",
           f"https://finance.yahoo.com/quote/{ticker}/key-statistics"
    )

    st.divider()

    st.subheader("🌍 Spreiding portefeuille")

    spreiding_type = (
        df.groupby("Type")["Waarde in EUR"]
        .sum()
    )

    st.bar_chart(spreiding_type)

# ===================================
# EARNINGS DATA
# ===================================

earnings_data = {

    # Eigen portefeuille

    "MSFT": "2026-10-28",
    "AMZN": "2026-10-29",
    "PLTR": "2026-11-02",
    "PHARM.AS": "2026-11-05",
    "NVDA": "2026-11-17",
    "ORCL": "2026-12-09",
    "ARGX.BR": "2027-02-25",

    # Koopkansen

    "GOOGL": "2026-10-28",
    "META": "2026-10-28",
    "AMD": "2026-11-03",
    "CRM": "2026-12-02",
    "AVGO": "2026-12-10",
    "ADBE": "2026-12-09",
    "ASML": "2027-01-27"
}

# ===================================
# TAB 5 - ADVIES
# ===================================

with tab5:

    # ==============================
    # KOMENDE EARNINGS
    # ==============================

    st.subheader("📅 Komende Earnings")

    earnings_tabel = pd.DataFrame(
        [
            {"Ticker": ticker, "Datum": datum}
            for ticker, datum in earnings_data.items()
        ]
    )

    st.dataframe(
        earnings_tabel.sort_values("Datum"),
        hide_index=True,
        use_container_width=True
    )

    st.divider()

    # ==============================
    # TOP 10 KOOPKANSEN
    # ==============================

    st.subheader("🏆 Top 10 Wereldwijde Koopkansen")

    if not wereld_koopkansen.empty:

        wereld_koopkansen_tabel = wereld_koopkansen[
            [
                "Ticker",
                "Sector",
                "Analistenadvies",
                "Analisten",
                "Koers",
                "Koersdoel",
                "Potentieel %",
                "Koopscore",
                "Yahoo"
            ]
        ]

        st.data_editor(
            wereld_koopkansen_tabel,
            column_config={
                "Yahoo": st.column_config.LinkColumn(
                    "📊 Yahoo Analyse",
                    display_text="📈"
                )
            },
            disabled=True,
            hide_index=True,
            use_container_width=True
        )

    else:

        st.info(
            "Momenteel geen koopkansen beschikbaar."
        )

    st.divider()

    # ==============================
    # ONBEKENDE ISIN'S
    # ==============================

    st.subheader("⚠️ Onbekende ISIN's")

    onbekende_df = df[
        ~df["ISIN"]
        .astype(str)
        .str.strip()
        .isin(tickers.keys())
    ][["Naam", "ISIN"]].drop_duplicates()

    if onbekende_df.empty:

        st.success(
            "✅ Alle ISIN's hebben een ticker."
        )

    else:

        st.warning(
            "Nieuwe aandelen/ETF's gevonden zonder ticker."
        )

        st.dataframe(
            onbekende_df,
            hide_index=True,
            use_container_width=True
        )

        st.download_button(
            "⬇️ Download onbekende ISIN's",
            onbekende_df.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="onbekende_isins.csv",
            mime="text/csv"
        )

    st.divider()

    # ==============================
    # ISIN-DATABASE
    # ==============================

    st.subheader("📚 ISIN-database")

    ticker_df = pd.DataFrame(
        [
            {
                "ISIN": isin,
                "Ticker": ticker
            }
            for isin, ticker in tickers.items()
        ]
    )

    if not ticker_df.empty:

        st.dataframe(
            ticker_df.sort_values("Ticker"),
            hide_index=True,
            use_container_width=True
        )

    st.divider()

# ===================================
# TAB 6 - INSTELLINGEN
# ===================================

with tab6:

    st.subheader("⚙️ Instellingen")

    st.info(
        "Gebruikersinstellingen volgen binnenkort."
    )

    st.divider()

    if st.button(
        "🚪 Uitloggen",
        key="logout_settings"
    ):

        st.session_state.clear()

        st.rerun()
