import finnhub
import streamlit as st

finnhub_client = finnhub.Client(
    api_key=st.secrets["FINNHUB_API_KEY"]
)

def haal_fundamentals_op(
    ticker
):

    try:

        data = finnhub_client.company_basic_financials(
            ticker,
            "all"
        )

        return data

    except Exception:

        return {}
