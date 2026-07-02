import streamlit as st
import yfinance as yf
import pandas as pd
import datetime # Make sure this is imported at the top of your file

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

# 2. Caching function
@st.cache_data(ttl=600)
def fetch_prices(tickers):
    # Use threads=True for faster/more reliable downloads
    data = yf.download(tickers, period="1d", group_by='ticker', threads=True)
    
    prices = {}
    for ticker in tickers:
        try:
            # Access the specific ticker column, then the 'Close' price
            ticker_data = data[ticker]
            price = ticker_data['Close'].iloc[-1]
            prices[ticker] = float(price)
        except:
            prices[ticker] = None
    return prices

# 3. Data Processing
tickers = list(MY_PORTFOLIO.keys())
# --- ADD THIS LINE BELOW ---
prices = fetch_prices(tickers) 
# ---------------------------

rows = []
total_val = 0
total_cost = 0

for ticker, info in MY_PORTFOLIO.items():
    price = prices.get(ticker) # Remove the ', 0' default temporarily
    
    # Debug: Print the price to the console/UI if it's missing
    if price is None or pd.isna(price):
        st.write(f"Debug: {ticker} returned no price!")
        continue
        
    shares = info["shares"]
    val = price * shares
    cost = info["buy_price"] * shares
    profit_loss = val - cost
    pct_pl = (profit_loss / cost) * 100 if cost != 0 else 0
    
rows.append({
        "Ticker": ticker, 
        "Shares": shares,
        "Current Price": price,  # <--- ADD THIS LINE
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

# Use st.dataframe for interactivity (sorting, formatting)
# --- Replace from line 75 down to 82 with this: ---

def color_profit_loss(val):
    if isinstance(val, (int, float)):
        color = 'green' if val >= 0 else 'red'
        return f'color: {color}'
    return ''

st.subheader("Portfolio Breakdown")

st.dataframe(
    df.style.format({
        "Current Price": "{:,.2f}", # <--- ADD THIS LINE
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

# 3. Sort based on the selection
if sort_option == "Ticker: A-Z":
    chart_df = chart_df.sort_values(by="Ticker", ascending=True)
elif sort_option == "Ticker: Z-A":
    chart_df = chart_df.sort_values(by="Ticker", ascending=False)
elif sort_option == "Value: Low to High":
    chart_df = chart_df.sort_values(by="Value", ascending=True)
elif sort_option == "Value: High to Low":
    chart_df = chart_df.sort_values(by="Value", ascending=False)

# 4. Set the Ticker as the index ONLY for the chart display
st.bar_chart(chart_df.set_index("Ticker")["Value"])
