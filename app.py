import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime

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

st.title("📈 Beyond Beleggingen")

if st.button("🔄 Portefeuille verversen"):

    st.cache_data.clear()

    st.rerun()

st.caption(
    f"🕒 Laatst vernieuwd: "
    f"{datetime.now().strftime('%H:%M:%S')}"
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

    st.divider()

    st.dataframe(
        posities_df[
            [
                "Ticker",
                "Aantal",
                "Koers",
                "Marktwaarde",
                "Winst/Verlies",
                "Rendement %"
            ]
        ],
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

    st.subheader("📈 Analyse")

    posities_df = bereken_posities(
        st.session_state.user_id
    )

    posities_df = verrijk_posities_met_koersen(
        posities_df
    )

    if posities_df.empty:

        st.info(
            "Geen analyse beschikbaar."
        )

    else:

        winnaars = (
            posities_df
            .sort_values(
                "Rendement %",
                ascending=False
            )
            .head(5)
        )

        verliezers = (
            posities_df
            .sort_values(
                "Rendement %",
                ascending=True
            )
            .head(5)
        )

        st.subheader("🏆 Top winnaars")

        st.dataframe(
            winnaars[
                [
                    "Ticker",
                    "Rendement %",
                    "Winst/Verlies"
                ]
            ],
            hide_index=True,
            use_container_width=True
        )

        st.subheader("📉 Top verliezers")

        st.dataframe(
            verliezers[
                [
                    "Ticker",
                    "Rendement %",
                    "Winst/Verlies"
                ]
            ],
            hide_index=True,
            use_container_width=True
        )
# ===================================
# TAB 5 - ADVIES
# ===================================

with tab5:

    st.subheader(
        "🏆 Top 10 Wereldwijde Koopkansen"
    )

    if not wereld_koopkansen.empty:

        st.data_editor(
            wereld_koopkansen[
                [
                    "Ticker",
                    "Sector",
                    "Analistenadvies",
                    "Analisten",
                    "Koers",
                    "Koersdoel",
                    "Potentieel %",
                    "Koopscore"
                ]
            ],
            disabled=True,
            hide_index=True,
            use_container_width=True
        )

    else:

        st.info(
            "Momenteel geen koopkansen beschikbaar."
        )

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
