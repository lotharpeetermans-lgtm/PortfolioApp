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

    st.subheader("📊 Dashboard")

    posities_df = bereken_posities(
        st.session_state.user_id
    )

    posities_df = verrijk_posities_met_koersen(
        posities_df
    )

    if posities_df.empty:

        st.info("Geen posities aanwezig.")

    else:

        totale_kostbasis = (
            posities_df["Kostbasis"].sum()
        )

        totale_marktwaarde = (
            posities_df["Marktwaarde"].sum()
        )

        totale_winst = (
            posities_df["Winst/Verlies"].sum()
        )

        rendement = (
            (totale_winst / totale_kostbasis) * 100
            if totale_kostbasis > 0
            else 0
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "Marktwaarde",
            f"€ {totale_marktwaarde:,.2f}"
        )

        col2.metric(
            "Kostbasis",
            f"€ {totale_kostbasis:,.2f}"
        )

        col3.metric(
            "Winst/Verlies",
            f"€ {totale_winst:,.2f}"
        )

        col4.metric(
            "Rendement",
            f"{rendement:.2f}%"
        )

        col5.metric(
            "Posities",
            len(posities_df)
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

    st.subheader("📈 Analyse")

    posities_df = bereken_posities(
        st.session_state.user_id
    )

    posities_df = verrijk_posities_met_koersen(
        posities_df
    )

    if posities_df.empty:

        st.info("Geen analyse beschikbaar.")

    else:

        winnaars = (
            posities_df.sort_values(
                "Rendement %",
                ascending=False
            )
            .head(5)
        )

        verliezers = (
            posities_df.sort_values(
                "Rendement %",
                ascending=True
            )
            .head(5)
        )

        st.subheader("🏆 Top winnaars")

        st.dataframe(
            winnaars,
            hide_index=True,
            use_container_width=True
        )

        st.subheader("📉 Top verliezers")

        st.dataframe(
            verliezers,
            hide_index=True,
            use_container_width=True
        )
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
