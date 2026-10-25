import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import glob
import os
from datetime import datetime
from streamlit_calendar import calendar

# ===================================
# PAGINA
# ===================================

st.set_page_config(
    page_title="Mijn Beleggingsdashboard",
    page_icon="📈",
    layout="wide"
)

bestanden = glob.glob("exports/*.xlsx")

if not bestanden:
    st.error("Geen Excel-bestanden gevonden in exports.")
    st.stop()

nieuwste_bestand = max(
    bestanden,
    key=os.path.getmtime
)

st.title("📈 Mijn Beleggingsdashboard")

if st.button("🔄 Portefeuille verversen"):
    st.cache_data.clear()
    st.rerun()

st.caption(
    f"🕒 Laatst vernieuwd: {datetime.now().strftime('%H:%M:%S')}"
)

st.caption(
    f"📂 Actieve export: {os.path.basename(nieuwste_bestand)}"
)

# ===================================
# BOLERO BESTAND INLEZEN
# ===================================

try:

    raw = pd.read_excel(
        nieuwste_bestand,
        header=None,
        engine="openpyxl"
    )

    header_row = None

    for idx, row in raw.iterrows():

        if row.astype(str).str.contains(
            "ISIN",
            case=False,
            na=False
        ).any():

            header_row = idx
            break

    if header_row is None:
        st.error("Geen geldige Bolero-export gevonden.")
        st.stop()

    headers = raw.iloc[header_row]

    geldige_kolommen = headers.dropna().index

    df = raw.iloc[
        header_row + 1:,
        geldige_kolommen
    ].copy()

    df.columns = headers.dropna().values

    df = df.dropna(how="all")

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    df["Type"] = (
        df["Type"]
        .astype(str)
        .str.strip()
    )

    df = df[
        df["Type"].str.contains(
            "Aandelen|ETF",
            case=False,
            na=False
        )
    ]

    df.reset_index(drop=True, inplace=True)

except Exception as e:

    st.error(f"Fout bij inlezen Excel: {e}")
    st.stop()

# ===================================
# NUMERIEKE KOLOMMEN
# ===================================

numerieke_kolommen = [
    "Waarde in EUR",
    "Rendement %",
    "Totale aankoopwaarde",
    "Gem. aankoopkoers",
    "Koers",
    "Wijziging (%)"
]

for kolom in numerieke_kolommen:

    if kolom in df.columns:

        df[kolom] = pd.to_numeric(
            df[kolom],
            errors="coerce"
        )

# ===================================
# ISIN -> TICKER
# ===================================

tickers = {

    # Aandelen

    "BE0974293251": "ABI.BR",
    "NL0010832176": "ARGX.BR",
    "US0231351067": "AMZN",
    "US0320951017": "APH",
    "US67066G1040": "NVDA",
    "US68389X1054": "ORCL",
    "US5738741041": "MRVL",
    "US8740541094": "TTWO",
    "US92840M1027": "VST",
"FR0013233012": "IVA.PA",      
"US15675D1037": "CBRS",        
"US21873S1087": "CRWV",        
"KYG4124C1096": "GRAB",        
"US5949181045": "MSFT",
"NL0010391025": "PHARM.AS",
"US69608A1088": "PLTR",  
"US84615Q1031": "SPCX",

    # ETF's

    "IE00B8FHGS14": "MVOL.L",
    "IE00B4L5Y983": "IWDA.AS",
    "IE00B4ND3602": "IGLN.L",
    "IE00BKM4GZ66": "EMIM.L",
    "IE00BYZK4552": "RBOT.L",
    "LU1781541252": "LCUJ.DE",
    "IE00BCBJG560": "WOSC.AS",
    "IE00B3RBWM25": "VWRL.AS",
    "IE000VAHT5T0": "VALL.AS",
    "IE00B3WJKG14": "IUIT.L",
}

# ===================================
# REALTIME KOERSEN
# ===================================

df["Realtime koers"] = np.nan
df["Dag %"] = np.nan
df["Realtime rendement %"] = np.nan

for index, row in df.iterrows():

    try:

        instrument_type = str(
            row["Type"]
        ).strip()

        # ==========================
        # AANDELEN
        # ==========================

        if instrument_type == "Aandelen":

            isin = str(
                row["ISIN"]
            ).strip().upper()

            if isin not in tickers:
                continue

            ticker = yf.Ticker(
                tickers[isin]
            )

            hist = ticker.history(
                period="2d"
            )

            if len(hist) < 2:
                continue

            koers = float(
                hist["Close"].iloc[-1]
            )

            vorige = float(
                hist["Close"].iloc[-2]
            )

            aankoopprijs = pd.to_numeric(
                row["Gem. aankoopkoers"],
                errors="coerce"
            )

            if (
                pd.isna(aankoopprijs)
                or aankoopprijs <= 0
            ):
                continue

            dag_pct = (
                (koers - vorige)
                / vorige
            ) * 100

            realtime_rendement = (
                (koers - aankoopprijs)
                / aankoopprijs
            ) * 100

            df.at[
                index,
                "Realtime koers"
            ] = round(
                koers,
                2
            )

            df.at[
                index,
                "Dag %"
            ] = round(
                dag_pct,
                2
            )

            df.at[
                index,
                "Realtime rendement %"
            ] = round(
                realtime_rendement,
                2
            )

        # ==========================
        # ETF'S
        # ==========================

        else:

            koers = pd.to_numeric(
                row["Koers"],
                errors="coerce"
            )

            dag_pct = pd.to_numeric(
                row["Wijziging (%)"],
                errors="coerce"
            )

            aankoopprijs = pd.to_numeric(
                row["Gem. aankoopkoers"],
                errors="coerce"
            )

            if pd.notna(koers):

                df.at[index, "Realtime koers"] = round(
                    koers,
                    2
                )

            if pd.notna(dag_pct):

                df.at[index, "Dag %"] = round(
                    dag_pct,
                    2
                )

            if (
                pd.notna(koers)
                and pd.notna(aankoopprijs)
                and aankoopprijs > 0
            ):

                realtime_rendement = (
                    (koers - aankoopprijs)
                    / aankoopprijs
                ) * 100

                df.at[
                    index,
                    "Realtime rendement %"
                ] = round(
                    realtime_rendement,
                    2
                )

    except Exception:
        pass

df["Ticker"] = (
    df["ISIN"]
    .astype(str)
    .str.strip()
    .map(tickers)
)

# EUR/USD wisselkoers

try:

    eurusd = yf.Ticker("EURUSD=X")

    wisselkoers = float(
        eurusd.history(period="1d")["Close"].iloc[-1]
    )

except Exception:

    wisselkoers = 1.15

# ===================================
# BEREKENINGEN
# ===================================

df["Winst/Verlies €"] = np.where(
    df["Ticker"].str.contains(
        r"\.(AS|BR|PA|DE|L)$",
        na=False
    ),
    (
        (df["Realtime koers"]
         - df["Gem. aankoopkoers"])
        * df["Aantal"]
    ),
    (
        (df["Realtime koers"]
         - df["Gem. aankoopkoers"])
        * df["Aantal"]
    ) / wisselkoers
)

df["Winst/Verlies €"] = pd.to_numeric(
    df["Winst/Verlies €"],
    errors="coerce"
).round(2)


totale_waarde = df["Waarde in EUR"].sum()

df["Gewicht %"] = (
    df["Waarde in EUR"]
    / totale_waarde
    * 100
).round(2)

df["Gewicht %"] = (
    df["Waarde in EUR"]
    / totale_waarde
    * 100
).round(1)

netto_inleg = 23500

totale_winst = totale_waarde - netto_inleg

totale_winst_pct = (
    totale_winst
    / netto_inleg
) * 100

aantal_posities = len(df)

aantal_aandelen = len(
    df[
        df["Type"]
        .str.contains(
            "Aandelen",
            na=False
        )
    ]
)

aantal_etfs = len(
    df[
        df["Type"]
        .str.contains(
            "ETF",
            na=False
        )
    ]
)

# ===================================
# WERELDWIJDE KOOPKANSEN
# ===================================

wereld_tickers = [

    # AI & Software
    "NVDA","MSFT","GOOGL","AMZN","META",
    "PLTR","CRM","NOW","ADBE","ORCL",
    "SNOW","DDOG","CRWD","PANW","MDB",
    "NET","TEAM","ZS","OKTA",

    # Chips
    "AMD","AVGO","TSM","ASML","ARM",
    "QCOM","MU","MRVL","ANET","INTC",

    # Financieel
    "V","MA","JPM","GS","BLK",
    "MS","AXP","SCHW","KKR","BX",

    # Gezondheid
    "LLY","NVO","UNH","ABBV","TMO",
    "DHR","ISRG","VRTX","REGN","BSX",

    # Industrie
    "GE","GEV","ETN","PH","TT",
    "PWR","NXT","CAT","DE","HON",

    # Energie
    "VST","CEG","SMR","CCJ","NEE",
    "XOM","CVX","COP","SLB","OKE",

    # Consument
    "COST","WMT","MELI","NFLX","BKNG",
    "ABNB","UBER","SPOT","TSLA","RACE",

    # Europa
    "SAP","MC.PA","SU.PA",
    "RMS.PA","AIR.PA","BN.PA",
    "NOVO-B.CO","DSV.CO","PRX.AS",

    # ETF's
    "SPY","QQQ","VOO","VGT","SOXX",
    "IWM","SMH","SCHG","XLK","IGV"
]

koopkansen = []

for ticker in wereld_tickers:

    try:

        info = yf.Ticker(ticker).info

        advies = info.get("recommendationKey")
        koersdoel = info.get("targetMeanPrice")
        koers = info.get("currentPrice")

        if koers is None:
            koers = info.get("regularMarketPrice")

        analisten = info.get(
            "numberOfAnalystOpinions"
        )

        sector = info.get("sector")

        if (
            koersdoel is None
            or koers is None
            or koers <= 0
        ):
            continue

        potentieel = round(
            ((koersdoel - koers) / koers) * 100,
            1
        )

        if advies == "strong_buy":
            score = 100
            advies_txt = "🟢 Sterk kopen"

        elif advies == "buy":
            score = 75
            advies_txt = "🟢 Kopen"

        elif advies == "hold":
            score = 40
            advies_txt = "🟡 Houden"

        else:
            score = 0
            advies_txt = "🔴 Verkopen"

        score += potentieel

        if analisten is not None:
            score += min(analisten, 50) / 5

        koopkansen.append({
            "Ticker": ticker,
            "Sector": sector,
            "Analistenadvies": advies_txt,
            "Analisten": analisten,
            "Koers": koers,
            "Koersdoel": koersdoel,
            "Potentieel %": potentieel,
            "Koopscore": round(score, 1),
            "Yahoo": f"https://finance.yahoo.com/quote/{ticker}/analysis"
        })

    except Exception:
        pass

wereld_koopkansen = pd.DataFrame(
    koopkansen
)

if (
    not wereld_koopkansen.empty
    and "Koopscore" in wereld_koopkansen.columns
):

    wereld_koopkansen = (
        wereld_koopkansen
        .sort_values(
            "Koopscore",
            ascending=False
        )
        .head(10)
    )

    beste_koopkans = wereld_koopkansen.iloc[0]["Ticker"]

else:

    beste_koopkans = "Geen data"

# ===================================
# AUTOMATISCH ADVIES
# ===================================

def bepaal_advies(rendement):

    if pd.isna(rendement):
        return "⚪ Geen data"

    elif rendement < -20:
        return "🟢 Sterk bijkopen"

    elif rendement < -10:
        return "🟢 Bijkopen"

    elif rendement < 20:
        return "🟡 Houden"

    elif rendement < 50:
        return "🔵 Afbouwen"

    else:
        return "🔴 Winst nemen"

def haal_analistenadvies(ticker):

    try:

        if pd.isna(ticker):
            return "⚪ Geen data"

        advies = yf.Ticker(ticker).info.get(
            "recommendationKey"
        )

        if advies == "strong_buy":
            return "🟢 Sterk kopen"

        elif advies == "buy":
            return "🟢 Kopen"

        elif advies == "hold":
            return "🟡 Houden"

        elif advies in [
            "underperform",
            "sell",
            "strong_sell"
        ]:
            return "🔴 Verkopen"

        return "⚪ Geen advies"

    except Exception:
        return "⚪ Geen advies"

def haal_koersdoel(ticker):

    try:

        if pd.isna(ticker):
            return np.nan

        return yf.Ticker(ticker).info.get(
            "targetMeanPrice"
        )

    except:
        return np.nan

def haal_sector(ticker):

    try:

        info = yf.Ticker(ticker).info

        sector = info.get("sector")

        if sector:
            return sector

        quote_type = info.get("quoteType")

        if quote_type == "ETF":
            return "ETF"

        return "Onbekend"

    except:
        return "Onbekend"

def haal_dividendrendement(ticker):

    try:

        info = yf.Ticker(ticker).info

        dividend = info.get(
            "trailingAnnualDividendRate"
        )

        koers = info.get(
            "currentPrice"
        )

        if koers is None:
            koers = info.get(
                "regularMarketPrice"
            )

        if (
            dividend is None
            or koers is None
            or koers <= 0
        ):
            return 0

        return round(
            (dividend / koers) * 100,
            2
        )

    except:
        return 0

def haal_earnings_datum(ticker):

    try:

        tk = yf.Ticker(ticker)

        kalender = tk.calendar

        if kalender is not None and not kalender.empty:

            datum = kalender.iloc[0, 0]

            return pd.to_datetime(
                datum
            ).strftime("%Y-%m-%d")

        return None

    except:
        return None

# ===================================
# OPMAAK POSITIEF / NEGATIEF
# ===================================

def kleur(val):

    if "Sterk bijkopen" in str(val):
        return (
            "background-color:#0d3b1e;"
            "color:#00ff88;"
            "font-weight:bold"
        )

    elif "Bijkopen" in str(val):
        return (
            "background-color:#1b5e20;"
            "color:white;"
            "font-weight:bold"
        )

    elif "Houden" in str(val):
        return (
            "background-color:#f9a825;"
            "color:black;"
            "font-weight:bold"
        )

    elif "Afbouwen" in str(val):
        return (
            "background-color:#1565c0;"
            "color:white;"
            "font-weight:bold"
        )

    elif "Winst nemen" in str(val):
        return (
            "background-color:#b71c1c;"
            "color:white;"
            "font-weight:bold"
        )

    return ""

# ===================================
# KLEUR ADVIES
# ===================================

def kleur_advies(val):

    if "Sterk bijkopen" in str(val):
        return "background-color:#0d3b1e;color:#00ff88;font-weight:bold"

    elif "Bijkopen" in str(val):
        return "background-color:#1b5e20;color:white;font-weight:bold"

    elif "Houden" in str(val):
        return "background-color:#f9a825;color:black;font-weight:bold"

    elif "Afbouwen" in str(val):
        return "background-color:#1565c0;color:white;font-weight:bold"

    elif "Winst nemen" in str(val):
        return "background-color:#b71c1c;color:white;font-weight:bold"
    
    elif "Sterk kopen" in str(val):
        return "background-color:#0d3b1e;color:#00ff88;font-weight:bold"

    elif "Kopen" in str(val):
        return "background-color:#1b5e20;color:white;font-weight:bold"

    elif "Verkopen" in str(val):
         return "background-color:#b71c1c;color:white;font-weight:bold"

    return ""

# ===================================
# ADVIESKOLOM
# ===================================


df["Analistenadvies"] = df["Ticker"].apply(
    haal_analistenadvies
)

df["Koersdoel"] = df["Ticker"].apply(
    haal_koersdoel
)

df["Sector"] = df["Ticker"].apply(
    haal_sector
)

df["Sector"] = df["Ticker"].apply(
    haal_sector
)

grootste_positie = df.loc[
    df["Gewicht %"].idxmax()
]

technologie_pct = (
    df.loc[
        df["Sector"] == "Technology",
        "Waarde in EUR"
    ].sum()
    / totale_waarde
    * 100
)

etf_pct = (
    df.loc[
        df["Type"].str.contains(
            "ETF",
            na=False
        ),
        "Waarde in EUR"
    ].sum()
    / totale_waarde
    * 100
)

df["Dividendrendement %"] = df["Ticker"].apply(
    haal_dividendrendement
)

df["Verwacht dividend €/jaar"] = (
    df["Waarde in EUR"]
    * df["Dividendrendement %"]
    / 100
).round(2)

if not wereld_koopkansen.empty:
    beste_koopkans = wereld_koopkansen.iloc[0]["Ticker"]
else:
    beste_koopkans = "Geen data"

df["Potentieel %"] = (
    (
        df["Koersdoel"]
        - df["Realtime koers"]
    )
    / df["Realtime koers"]
    * 100
).round(1)

def koopscore(row):

    score = 0

    advies = str(row["Analistenadvies"])

    if "Sterk kopen" in advies:
        score += 100

    elif "Kopen" in advies:
        score += 75

    elif "Houden" in advies:
        score += 40

    if pd.notna(row["Potentieel %"]):
        score += row["Potentieel %"]

    return round(score, 1)

df["Koopscore"] = df.apply(
    koopscore,
    axis=1
)

# ===================================
# TABELFORMATTERING
# ===================================

def formatteer_tabel(df_style):

    return (
        df_style
        .format({
            "Waarde in EUR": "€ {:.2f}",
            "Totale aankoopwaarde": "€ {:.2f}",
            "Gem. aankoopkoers": "{:.2f}",
            "Koers": "{:.2f}",
            "Realtime koers": "{:.2f}",
            "Dag %": "{:.2f} %",
            "Gewicht %": "{:.2f} %",
            "Rendement %": "{:.2f} %",
            "Realtime rendement %": "{:.2f} %",
            "Winst/Verlies €": "€ {:.2f}",
            "Dividendrendement %": "{:.2f} %",
            "Verwacht dividend €/jaar": "€ {:.2f}",
            "Koersdoel": "{:.2f}",
            "Potentieel %": "{:.1f} %",
            "Koopscore": "{:.1f}"
        })
    )
# ===================================
# TABS
# ===================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Overzicht",
        "💼 Portefeuille",
        "📈 Analyse",
        "🤖 Advies"
    ]
)

# ===================================
# TAB 1
# ===================================

with tab1:

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
# TAB 2
# ===================================

with tab2:

    aandelen_tab, etf_tab = st.tabs(
        [
            "📈 Aandelen",
            "📊 ETF's"
        ]
    )

    with aandelen_tab:

        aandelen = df[
            df["Type"].str.contains(
                "Aandelen",
                na=False
            )
        ].copy()

        kolommen_aandelen = [
            "Naam",
            "Waarde in EUR",
            "Aantal",
            "Gem. aankoopkoers",
            "Realtime koers",
            "Dag %",
            "Realtime rendement %",
            "Winst/Verlies €",
            "Analistenadvies",
            "Koersdoel",
            "Potentieel %",
        ]

        st.dataframe(
            formatteer_tabel(
                aandelen[kolommen_aandelen]
                .style.map(
                    kleur,
                    subset=[
                        "Dag %",
                        "Realtime rendement %",
                        "Winst/Verlies €",
                        "Potentieel %"
                    ]
                )
                .map(
                    kleur_advies,
                    subset=[
                        "Analistenadvies"
                    ]
                )
            ),
            hide_index=True,
            use_container_width=True
        )

    with etf_tab:

        etfs = df[
            df["Type"].str.contains(
                "ETF",
                na=False
            )
        ]

        kolommen_etfs = [
            "Naam",
            "Waarde in EUR",
            "Aantal",
            "Gem. aankoopkoers",
            "Koers",
            "Dag %",
            "Realtime rendement %",
            "Winst/Verlies €",
            "Analistenadvies",
            "Koersdoel",
            "Potentieel %",
        ]

        st.dataframe(
            formatteer_tabel(
                etfs[kolommen_etfs]
                .style.map(
                    kleur,
                    subset=[
                        "Dag %",
                        "Realtime rendement %",
                        "Winst/Verlies €",
                        "Potentieel %"
                    ]
                )
            ),
            hide_index=True,
            use_container_width=True
        )

    # ===================================
    # DIVIDENDOVERZICHT
    # ===================================

    st.divider()

    st.subheader("💰 Dividendoverzicht")

    totaal_dividend = df[
        "Verwacht dividend €/jaar"
    ].sum()

    st.metric(
        "Verwacht dividend per jaar",
        f"€ {totaal_dividend:,.2f}"
    )

    dividend_tabel = (
        df[
            [
                "Naam",
                "Waarde in EUR",
                "Dividendrendement %",
                "Verwacht dividend €/jaar"
            ]
        ]
        .sort_values(
            "Verwacht dividend €/jaar",
            ascending=False
        )
    )

    st.dataframe(
        formatteer_tabel(
            dividend_tabel.style
        ),
        hide_index=True,
        use_container_width=True
    )

# ===================================
# TAB 3
# ===================================

with tab3:

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
# TAB 4 - ADVIES
# ===================================

with tab4:

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