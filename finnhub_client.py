import finnhub
import streamlit as st

finnhub_client = finnhub.Client(
    api_key=st.secrets["FINNHUB_API_KEY"]
)

def haal_fundamentals_op(ticker):

    try:

        data = finnhub_client.company_basic_financials(
            ticker,
            "all"
        )

        metrics = data.get("metric", {})

        return {
            "pe": metrics.get("peNormalizedAnnual"),
            "peg": metrics.get("pegAnnual"),
            "roe": metrics.get("roeRfy"),
            "net_margin": metrics.get("netMarginAnnual"),
            "revenue_growth": metrics.get("revenueGrowth3Y"),
            "eps_growth": metrics.get("epsGrowth3Y")
        }

    except Exception:
        return {}
