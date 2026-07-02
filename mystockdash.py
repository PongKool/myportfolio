import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="My Portfolio", layout="wide")
st.title("📊 Personal Stock Portfolio")

# 1. Define your portfolio
MY_PORTFOLIO = {
    "ADVANC.BK": {"shares": 200, "buy_price": 362.61},
    "AOT.BK": {"shares": 1300, "buy_price": 63.82},
    "KBANK.BK": {"shares": 500, "buy_price": 206.75}, # Added comma
    "PRM.BK": {"shares": 3100, "buy_price": 8.88},
    "BDMS.BK": {"shares": 3000, "buy_price": 18.62},
    "KTB.BK": {"shares": 1000, "buy_price": 36.53},  # Added comma
    "PTT.BK": {"shares": 3700, "buy_price": 35.79},
    "SCB.BK": {"shares": 900, "buy_price": 142.63},
    "TRUE.BK": {"shares": 1700, "buy_price": 12.83}
}

# 2. Caching function
@st.cache_data(ttl=600)
def fetch_prices(tickers):
    return yf.download(tickers, period="1d", group_by='ticker')['Close'].iloc[-1]

# 3. Data Processing
tickers = list(MY_PORTFOLIO.keys())
prices = fetch_prices(tickers)

# Calculate metrics
rows = []
total_val = 0
total_cost = 0

for ticker, info in MY_PORTFOLIO.items():
    price = prices.get(ticker, 0)
    val = price * info["shares"]
    cost = info["buy_price"] * info["shares"]
    rows.append({"Ticker": ticker, "Value": val, "P&L": val - cost})
    total_val += val
    total_cost += cost

# 4. Display
col1, col2, col3 = st.columns(3)
col1.metric("Total Value", f"{total_val:,.2f} THB")
col2.metric("Total Cost", f"{total_cost:,.2f} THB")
col3.metric("Profit/Loss", f"{(total_val - total_cost):,.2f} THB")

st.table(pd.DataFrame(rows))
