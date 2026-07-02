import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.express as px
import time
from datetime import datetime as dt
import pytz

st.set_page_config(page_title="My Portfolio", layout="wide")
st.title("📊 Personal Stock Portfolio")

# --- Add this button for refreshing ---
if st.button("Refresh Data"):
    st.cache_data.clear()  # This wipes the cache and forces a new download
    st.rerun()             # This reloads the page to show new data

# Get Thailand timezone and current time
thailand_tz = pytz.timezone('Asia/Bangkok')
thailand_time = dt.now(thailand_tz).strftime('%H:%M:%S')
st.caption(f"Last updated: {thailand_time} (Bangkok)")

# --- PORTFOLIO SETTINGS ---
st.markdown("### Portfolio Settings")
ORIGINAL_INVESTMENT = 600000.0  # Hardcode your actual deposited amount here

# User input for cash on hand
line_available = st.number_input("Line Available (Cash in account in THB)", min_value=0.0, value=0.0, step=1000.0)
# st.divider() # Adds a clean visual line to separate settings from the dashboard


# 1. Define your portfolio
MY_PORTFOLIO = {
    "ADVANC.BK": {"shares": 200, "buy_price": 362.61},
    "AOT.BK": {"shares": 1300, "buy_price": 63.82},
    "KBANK.BK": {"shares": 500, "buy_price": 206.75},
    "IVL.BK": {"shares": 1200, "buy_price": 22.74},
    "BDMS.BK": {"shares": 3000, "buy_price": 18.62},
    "KTB.BK": {"shares": 1000, "buy_price": 36.53},
    "PTT.BK": {"shares": 4700, "buy_price": 35.77},
    "SCB.BK": {"shares": 900, "buy_price": 142.63}
}

# 2. Caching function with retry logic and delays
@st.cache_data(ttl=3600)
def fetch_prices(tickers):
    prices = {}
    for idx, ticker in enumerate(tickers):
        try:
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(period="1d")
            
            if not data.empty:
                prices[ticker] = float(data['Close'].iloc[-1])
            else:
                prices[ticker] = None
            
            # Add delay between requests to avoid rate limiting
            if idx < len(tickers) - 1:
                time.sleep(0.5)
                
        except Exception as e:
            st.warning(f"Could not fetch data for {ticker}: {str(e)}")
            prices[ticker] = None
    
    return prices

# 3. Data Processing
tickers = list(MY_PORTFOLIO.keys())
prices = fetch_prices(tickers) 

rows = []
total_val = 0
total_cost = 0

for ticker, info in MY_PORTFOLIO.items():
    price = prices.get(ticker) 
    
    if price is None or pd.isna(price):
        continue
    
    shares = info["shares"]
    val = price * shares
    cost = info["buy_price"] * shares
    profit_loss = val - cost
    pct_pl = (profit_loss / cost) * 100 if cost != 0 else 0
    
    rows.append({
        "Ticker": ticker, 
        "Display Ticker": ticker.replace(".BK", ""),  # Remove .BK for display
        "Shares": shares,
        "Current Price": price,
        "Value": val, 
        "P&L": profit_loss, 
        "%P&L": pct_pl
    })

    total_val += val
    total_cost += cost

# Convert to DataFrame
df = pd.DataFrame(rows)
df.index = df.index + 1

# 4. Display Visual Improvements

# --- NEW CALCULATIONS ---
real_total_value = total_val + line_available
real_pl = real_total_value - ORIGINAL_INVESTMENT
real_pl_pct = (real_pl / ORIGINAL_INVESTMENT) * 100 if ORIGINAL_INVESTMENT != 0 else 0

# --- TOP ROW: OVERALL REAL PERFORMANCE ---

# --- TOP ROW: OVERALL REAL PERFORMANCE ---

# 1. Inject CSS to shade the ENTIRE container using our 'blue-tag'
st.markdown("""
<style>
/* Target the massive bordered wrapper that contains our blue tags */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.blue-tag) {
    background-color: rgba(0, 150, 255, 0.08) !important;
    border: 1px solid rgba(0, 150, 255, 0.4) !important;
}

/* Force Streamlit's inner layout blocks to be transparent so the shade shows through */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.blue-tag) [data-testid="stVerticalBlock"] {
    background-color: transparent !important;
}

/* Remove the individual card borders so they blend smoothly into the big box */
div[data-testid="stColumn"]:has(.blue-tag) div[data-testid="stMetric"] {
    background-color: transparent !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

with st.container(border=True):
    st.subheader("True Portfolio Performance")
    col1, col2, col3 = st.columns(3)
    
    # Drop a hidden tag directly inside each column we want to shade
    col1.markdown('<span class="blue-tag"></span>', unsafe_allow_html=True)
    col1.metric("Real Total Value (Stocks + Cash)", f"{real_total_value:,.2f} THB")
    
    col2.markdown('<span class="blue-tag"></span>', unsafe_allow_html=True)
    col2.metric("Original Investment", f"{ORIGINAL_INVESTMENT:,.2f} THB")
    
    col3.markdown('<span class="blue-tag"></span>', unsafe_allow_html=True)
    col3.metric("Real P/L", f"{real_pl:,.2f} THB", delta=f"{real_pl_pct:.2f}%")

st.markdown("<br>", unsafe_allow_html=True) # Adds a little spacing


# --- BOTTOM ROW: STOCK ONLY PERFORMANCE ---
st.subheader("Stock Holdings Performance")
col4, col5, col6 = st.columns(3)
col4.metric("Total Stock Value", f"{total_val:,.2f} THB")
col5.metric("Total Stock Cost", f"{total_cost:,.2f} THB")
col6.metric("Stock P/L", f"{(total_val - total_cost):,.2f} THB", delta=f"{((total_val - total_cost)/total_cost)*100:.2f}%")

def color_profit_loss(val):
    if isinstance(val, (int, float)):
        color = 'green' if val >= 0 else 'red'
        return f'color: {color}'
    return ''

st.subheader("Portfolio Breakdown")

st.dataframe(
    df[["Display Ticker", "Shares", "Current Price", "Value", "P&L", "%P&L"]].style.format({
        "Current Price": "{:,.2f}",
        "Value": "{:,.2f}",
        "P&L": "{:,.2f}",
        "%P&L": "{:,.2f}%"
    }).map(color_profit_loss, subset=['P&L', '%P&L']),
    use_container_width=True
)

# Optional: Add a quick visualization with sorting options
st.subheader("Asset Allocation")

sort_option = st.selectbox(
    "Sort Asset Allocation by:",
    ("Ticker: A-Z", "Ticker: Z-A", "Value: Low to High", "Value: High to Low"),
    index=0 
)

# 1. Create a clean copy for the chart
chart_df = df.copy() 

# 2. Convert Value to numeric to ensure clean sorting
chart_df['Value'] = pd.to_numeric(chart_df['Value'], errors='coerce')
chart_df = chart_df.dropna(subset=['Value'])

# 3. Sort based on the selection - RESET INDEX to avoid confusion
chart_df = chart_df.reset_index(drop=True)

if sort_option == "Ticker: A-Z":
    chart_df = chart_df.sort_values(by="Display Ticker", ascending=True)
elif sort_option == "Ticker: Z-A":
    chart_df = chart_df.sort_values(by="Display Ticker", ascending=False)
elif sort_option == "Value: Low to High":
    chart_df = chart_df.sort_values(by="Value", ascending=True)
elif sort_option == "Value: High to Low":
    chart_df = chart_df.sort_values(by="Value", ascending=False)

# 4. Horizontal bar chart with display tickers on Y-axis
fig = px.bar(
    chart_df, 
    y="Display Ticker",
    x="Value",
    orientation="h",
    title="Portfolio Value by Asset",
    labels={"Value": "Value (THB)", "Display Ticker": "Stock Ticker"},
    color="Value",
    color_continuous_scale="Viridis"
)

# FIXED: For horizontal charts, reverse the categoryarray so items display in the correct order
ticker_order = chart_df["Display Ticker"].tolist()[::-1]
fig.update_yaxes(categoryorder="array", categoryarray=ticker_order)

st.plotly_chart(fig, use_container_width=True, key=f"chart_{sort_option}")
