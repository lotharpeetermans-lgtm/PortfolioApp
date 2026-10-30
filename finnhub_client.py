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

        pe = metrics.get("peNormalizedAnnual")

        revenue_growth = (
            metrics.get("revenueGrowth3Y")
            or metrics.get("revenueGrowth5Y")
        )

        eps_growth = (
            metrics.get("epsGrowth3Y")
            or metrics.get("epsGrowth5Y")
            or metrics.get("epsGrowthQuarterlyYoy")
        )

        roe = metrics.get("roeRfy")

        net_margin = metrics.get("netMarginAnnual")

        # Eigen PEG-berekening
        peg = None

        if (
            pe is not None
            and eps_growth is not None
            and eps_growth > 0
        ):
            peg = round(
                pe / eps_growth,
                2
            )

        return {
            "pe": pe,
            "peg": peg,
            "roe": roe,
            "net_margin": net_margin,
            "revenue_growth": revenue_growth,
            "eps_growth": eps_growth
        }

    except Exception as e:

        return {
            "error": str(e)
        }
