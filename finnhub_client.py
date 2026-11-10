import streamlit as st
import finnhub

finnhub_client = finnhub.Client(
    api_key=st.secrets["FINNHUB_API_KEY"]
)

@st.cache_data(ttl=86400)
def haal_fundamentals_op(ticker):

    try:
        data = finnhub_client.company_basic_financials(
            ticker,
            "all"
        )

        metrics = data.get("metric", {})

        return {
            "pe": metrics.get("peTTM"),
            "peg": metrics.get("pegAnnual"),
            "roe": metrics.get("roeTTM"),
            "revenue_growth": metrics.get("revenueGrowthTTMYoy"),
            "eps_growth": metrics.get("epsGrowthTTMYoy")
        }

    except:
        return {}
