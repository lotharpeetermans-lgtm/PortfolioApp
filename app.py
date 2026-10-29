import streamlit as st
import pandas as pd
import yfinance as yf
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

from finnhub_client import finnhub_client

def score_range(
    waarde,
    grens1,
    grens2,
    grens3,
    punten_max=10
):

    if waarde >= grens3:
        return punten_max

    elif waarde >= grens2:
        return round(
            punten_max * 0.75,
            1
        )

    elif waarde >= grens1:
        return round(
            punten_max * 0.4,
            1
        )

    return 0

# ===================================
# PAGINA
# ===================================

st.set_page_config(
    page_title="Beyond Beleggingen",
    page_icon="📈",
    layout="wide"
)

# ===================================
# SESSION STATE
# ===================================

if "koopkansen_refresh" not in st.session_state:

    st.session_state.koopkansen_refresh = 0

# ===================================
# LOGIN
# ===================================

if "user_id" not in st.session_state:

    st.title("📈 Beyond Beleggingen")

    col1, col2 = st.columns([8, 1])
    
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

    st.session_state.koopkansen_refresh += 1

    st.rerun()

st.caption(
    f"🕒 Laatst vernieuwd: "
    f"{datetime.now().strftime('%H:%M:%S')}"
)

# ===================================
# WERELDWIJDE KOOPKANSEN
# ===================================

wereld_tickers = [

    # Mega Caps
    "MSFT", "AAPL", "NVDA", "GOOGL", "AMZN",
    "META", "TSLA", "AVGO", "LLY",

    # Technologie
    "AMD", "QCOM", "INTC", "CRM", "ADBE",
    "NOW", "PLTR", "SNOW", "UBER", "SHOP",

    # Chips
    "ASML", "TSM", "AMAT", "LRCX", "MU",
    "KLAC", "NXPI", "ON", "MRVL",

    # Financieel
    "V", "MA", "JPM", "BAC", "GS",
    "MS", "BLK", "SCHW", "AXP",

    # Gezondheidszorg
    "JNJ", "ABBV", "MRK", "PFE",
    "ABT", "ISRG", "TMO", "DHR",

    # Industrie
    "CAT", "GE", "HON", "DE",
    "RTX", "LMT", "ETN", "PH",

    # Consument
    "PG", "KO", "PEP", "MCD",
    "HD", "COST", "NKE", "SBUX",

    # Energie
    "XOM", "CVX", "SLB", "COP",

    # Europa
    "SAP", "SIE.DE",
    "MC.PA", "RMS.PA",
    "OR.PA", "AIR.PA",

    # ETF's
    "SPY", "VOO", "QQQ", "VTI",
    "SCHD", "DGRO", "VIG",
    "XLK", "XLF", "XLE",
    "SOXX", "SMH",

    # Wereld ETF's
    "IWDA.AS",
    "VWCE.DE",
    "VWRL.AS",
    "EUNL.DE",

    # Dividend
    "VHYL.AS",
    "HDV",
    "DVY",
    "NOBL"
]

def bereken_trend_score(
    koers,
    hist
):

    ma50 = (
        hist["Close"]
        .tail(50)
        .mean()
    )

    ma200 = (
        hist["Close"]
        .tail(200)
        .mean()
    )

    score = 0

    if koers > ma50:

        score += 10

    if koers > ma200:

        score += 10

    if ma50 > ma200:

        score += 10

    return score

def bereken_momentum_score(
    rendement_6m,
    rendement_12m
):

    score = 0

    # 6 maanden

    if rendement_6m > 100:
        score += 15

    elif rendement_6m > 50:
        score += 12

    elif rendement_6m > 20:
        score += 10

    elif rendement_6m > 0:
        score += 5

    # 12 maanden

    if rendement_12m > 50:
        score += 15

    elif rendement_12m > 25:
        score += 12

    elif rendement_12m > 10:
        score += 8

    elif rendement_12m > 0:
        score += 4

    return score



def bereken_relatieve_sterkte_score(
    koers,
    hist
):

    jaarhoog = hist["High"].max()
    jaarlaag = hist["Low"].min()

    if jaarhoog == jaarlaag:
        return 0

    positie = (
        (koers - jaarlaag)
        /
        (jaarhoog - jaarlaag)
    ) * 100

    if positie > 80:
        return 20
    elif positie > 60:
        return 15
    elif positie > 40:
        return 10
    elif positie > 20:
        return 5

    return 0

def bereken_terugval_score(
    koers,
    hist
):

    jaarhoog = hist["High"].max()

    korting = (
        (jaarhoog - koers)
        / jaarhoog
    ) * 100

    if 10 <= korting <= 20:
        return 20
    elif 20 < korting <= 30:
        return 15
    elif 30 < korting <= 40:
        return 10
    elif korting > 40:
        return 5

    return 0

def haal_fundamentals_op(ticker):

    return {
        "pe": None,
        "peg": None,
        "roe": None,
        "net_margin": None,
        "revenue_growth": None,
        "eps_growth": None
    }
def bereken_fundamentele_score(data):

    score = 0

    pe = data.get("pe")
    peg = data.get("peg")
    roe = data.get("roe")
    revenue_growth = data.get("revenue_growth")
    eps_growth = data.get("eps_growth")

    # PEG

    if peg:

        if peg < 1:
            score += 15

        elif peg < 2:
            score += 10

    # ROE

    if roe:

        if roe > 20:
            score += 15

        elif roe > 10:
            score += 10

    # Omzetgroei

    if revenue_growth:

        if revenue_growth > 20:
            score += 10

        elif revenue_growth > 10:
            score += 5

    # Winstgroei

    if eps_growth:

        if eps_growth > 20:
            score += 10

        elif eps_growth > 10:
            score += 5

    return score

def bereken_beyond_score(
    ticker
):

    try:

        aandeel = yf.Ticker(ticker)

        hist = aandeel.history(
            period="1y"
        )

        if hist.empty:
            return None

        koers = float(
            hist["Close"].iloc[-1]
        )

        fundamentals = haal_fundamentals_op(
            ticker
        )

        fundamenteel = 0

        jaarhoog = (
            hist["High"]
            .max()
        )

        jaarlaag = (
            hist["Low"]
            .min()
        )

        if len(hist) < 126:
            return None

        koers_6m = hist["Close"].iloc[-126]
        koers_12m = hist["Close"].iloc[0]
        
        rendement_6m = (
            (koers - koers_6m)
            / koers_6m
        ) * 100

        rendement_12m = (
            (koers - koers_12m)
            / koers_12m
        ) * 100

        afstand_tot_hoog = (
            (jaarhoog - koers)
            / jaarhoog
        ) * 100

        trend = (
            bereken_trend_score(
                koers,
                hist
            )
        )

        momentum = (
            bereken_momentum_score(
                rendement_6m,
                rendement_12m
            )
        )        

        sterkte = (
            bereken_relatieve_sterkte_score(
                koers,
                hist
            )
        )

        terugval = (
            bereken_terugval_score(
                koers,
                hist
            )
        )

        totaal = (
            trend +
            momentum +
            sterkte +
            terugval +
            fundamenteel
        )

        if totaal >= 80:

            label = "🔥 Top koopkans"

        elif totaal >= 65:

            label = "✅ Koopwaardig"

        elif totaal >= 50:

            label = "👀 Interessant"

        else:

            label = "⚠️ Opvolgen"

        return {

            "Ticker": ticker,

            "Beyond Score": totaal,

            "Label": label,

            "Trend": trend,

            "Momentum": momentum,

            "Sterkte": sterkte,

            "Terugval": terugval,

            "Koers": round(
                koers,
                2
            ),

            "6M Rendement": round(
                rendement_6m,
                2
            ),

            "12M Rendement": round(
                rendement_12m,
                2
            ),

            "52W Hoog": round(
                jaarhoog,
                2
            ),

            "52W Laag": round(
                jaarlaag,
                2
            ),

            "Afstand tot Hoog": round(
                afstand_tot_hoog,
                2
            )
        }

    except Exception as e:
        st.error(f"{ticker}: {e}")
        return None

@st.cache_data(
    ttl=3600,
    show_spinner="Wereldwijde koopkansen berekenen..."
)
def bereken_wereldwijde_koopkansen(
    refresh_key=0
):

    resultaten = []

    for ticker in wereld_tickers:

        resultaat = (
            bereken_beyond_score(
                ticker
            )
        )

        if resultaat:

            resultaten.append(
                resultaat
            )

    if not resultaten:

        return pd.DataFrame()

    return (
        pd.DataFrame(
            resultaten
        )
        .sort_values(
            "Beyond Score",
            ascending=False
        )
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
# TAB 2 - DASHBOARD
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

        st.info(
            "Geen posities aanwezig."
        )

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

        st.subheader(
            "📋 Overzicht posities"
        )

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
# TAB 4 - ANALYSE
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

        st.subheader("🏆 Top 5 winnaars")

        st.dataframe(
            winnaars[
                [
                    "Ticker",
                    "Aantal",
                    "Rendement %",
                    "Winst/Verlies"
                ]
            ],
            hide_index=True,
            use_container_width=True
        )

        st.divider()

        st.subheader("📉 Top 5 verliezers")

        st.dataframe(
            verliezers[
                [
                    "Ticker",
                    "Aantal",
                    "Rendement %",
                    "Winst/Verlies"
                ]
            ],
            hide_index=True,
            use_container_width=True
        )

        st.divider()

        st.subheader("📊 Rendement per positie")

        grafiek_df = (
            posities_df
            .set_index("Ticker")
        )

        st.bar_chart(
            grafiek_df["Rendement %"]
        )
# ===================================
# TAB 5 - KOOPKANSEN
# ===================================

with tab5:
    
    st.subheader(
        "🏆 Beste Koopkansen Wereldwijd"
    )

    wereld_koopkansen = (
        bereken_wereldwijde_koopkansen(
            st.session_state.koopkansen_refresh
        )
    )

    if wereld_koopkansen.empty:

        st.info(
            "Geen koopkansen gevonden."
        )

    else:

        st.metric(
            "Aantal gescreende aandelen/ETF's",
            len(wereld_koopkansen)
        )

        st.divider()

        st.dataframe(
            wereld_koopkansen[
                [
                    "Ticker",
                    "Beyond Score",
                    "Label",
                    "Trend",
                    "Momentum",
                    "Sterkte",
                    "Terugval",
                    "Koers",
                    "6M Rendement",
                    "12M Rendement",
                    "52W Hoog",
                    "52W Laag",
                    "Afstand tot Hoog",
                ]
            ],
            hide_index=True,
            use_container_width=True
        )

        st.divider()

        st.subheader(
            "🔥 Top 10 Koopkansen"
        )
        
        st.dataframe(
            wereld_koopkansen[
                [
                    "Ticker",
                    "Beyond Score",
                    "Label"
                ]
            ].head(10),
            hide_index=True,
            use_container_width=True
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
