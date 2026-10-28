import finnhub
import streamlit as st

client = finnhub.Client(
    api_key=st.secrets["FINNHUB_API_KEY"]
)
