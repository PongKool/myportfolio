import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import plotly.express as px
import time

st.set_page_config(page_title="My Portfolio", layout="wide")
st.title("📊 Personal Stock Portfolio")

# --- Add this button for refreshing ---
if st.button("Refresh Data"):
    st.cache_data.clear()  # This wipes the cache and forces a new download
    st.rerun()             # This reloads the page to show new data

st.caption(f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}")


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
col1, col2, col3 = st.columns(3)
col1.metric("Total Value", f"{total_val:,.2f} THB")
col2.metric("Total Cost", f"{total_cost:,.2f} THB")
# Color the P&L metric red/green based on value
col3.metric("Profit/Loss", f"{(total_val - total_cost):,.2f} THB", 
            delta=f"{((total_val - total_cost)/total_cost)*100:.2f}%")

def color_profit_loss(val):
    if isinstance(val, (int, float)):
        color = 'green' if val >= 0 else 'red'
        return f'color: {color}'
    return ''

st.subheader("Portfolio Breakdown")

st.dataframe(
    df.style.format({
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
    chart_df = chart_df.sort_values(by="Ticker", ascending=True)
elif sort_option == "Ticker: Z-A":
    chart_df = chart_df.sort_values(by="Ticker", ascending=False)
elif sort_option == "Value: Low to High":
    chart_df = chart_df.sort_values(by="Value", ascending=True)
elif sort_option == "Value: High to Low":
    chart_df = chart_df.sort_values(by="Value", ascending=False)

# 4. FIXED: Swap x and y axes - Tickers on Y-axis, Value on X-axis (horizontal bar chart)
fig = px.bar(
    chart_df, 
    y="Ticker",           # Changed from x to y
    x="Value",            # Changed from y to x
    orientation="h",      # Added horizontal orientation
    title="Portfolio Value by Asset",
    labels={"Value": "Value (THB)", "Ticker": "Stock Ticker"},
    color="Value",
    color_continuous_scale="Viridis"
)

# Maintain the order by setting category order for Y-axis
fig.update_yaxes(categoryorder="array", categoryarray=chart_df["Ticker"].tolist())

st.plotly_chart(fig, use_container_width=True, key=f"chart_{sort_option}")
