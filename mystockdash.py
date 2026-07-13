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
ORIGINAL_INVESTMENT = 700000.0  # FSS=292600; SBITO=407400; Hardcode your actual deposited amount here

# User input for cash on hand
# User input for cash on hand (allows math expressions)
# 1. Initialize session state for the input if it doesn't exist yet
if 'line_input' not in st.session_state:
    st.session_state.line_input = "0"

# 2. Callback function that calculates the math when you press Enter
def calculate_line():
    try:
        raw_val = st.session_state.line_input
        # Evaluate the math expression
        calc_val = float(eval(raw_val))
        # Format it cleanly (removes .0 if it's a whole number)
        if calc_val.is_integer():
            st.session_state.line_input = str(int(calc_val))
        else:
            st.session_state.line_input = str(calc_val)
    except Exception:
        # If there's an error (like typing a letter), do nothing here. 
        # The main code block below will catch it and show the error message.
        pass

# 3. User input linked to the session state and the callback
line_available_str = st.text_input(
    "Line Available (Cash in account in THB)", 
    key="line_input", 
    on_change=calculate_line
)

# 4. Final safety check and assignment for the rest of your dashboard
try:
    # Since the callback runs first, this will now usually just be converting "3000" to float
    line_available = float(eval(line_available_str))
except Exception:
    st.error("Invalid math expression. Please enter numbers and operators like 1000 + 2000")
    line_available = 0.0


# 1. Define your portfolio
MY_PORTFOLIO = {
    "ADVANC.BK": {"shares": 100, "buy_price": 370.96},
#    "AOT.BK": {"shares": 1300, "buy_price": 64.34},
    "KBANK.BK": {"shares": 400, "buy_price": 231.39},
    "IVL.BK": {"shares": 2500, "buy_price": 23.13},
    "PTTGC.BK": {"shares": 1500, "buy_price": 34.39},
    "WHA.BK": {"shares": 10800, "buy_price": 5.46},
    "KTB.BK": {"shares": 1700, "buy_price": 40.64},
    "PTT.BK": {"shares": 6200, "buy_price": 36.02},
#    "CPF.BK": {"shares": 1500, "buy_price": 22.32},
    "BCP.BK": {"shares": 2000, "buy_price": 36.53}
#    "SCB.BK": {"shares": 500, "buy_price": 142.02},
    "GULF.BK": {"shares": 1100, "buy_price": 63.56}
    
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

# Determine colors and arrows for Profit/Loss
pl_color = "#09ab3b" if real_pl >= 0 else "#ff2b2b"
pl_arrow = "↑" if real_pl >= 0 else "↓"

# Build a custom HTML card to guarantee the entire box is shaded
custom_card = f"""
<div style="background-color: rgba(0, 150, 255, 0.08); border: 1px solid rgba(0, 150, 255, 0.3); border-radius: 0.5rem; padding: 1.5rem; margin-bottom: 1rem;">
<h3 style="margin-top: 0; margin-bottom: 1rem; font-family: sans-serif;">True Portfolio Performance</h3>
<div style="display: flex; flex-wrap: wrap; gap: 1rem;">
<div style="flex: 1; min-width: 200px;">
<p style="margin: 0; font-size: 0.875rem; opacity: 0.7;">Real Total Value (Stocks + Cash)</p>
<h2 style="margin: 0.25rem 0 0 0; font-weight: 400;">{real_total_value:,.2f} THB</h2>
</div>
<div style="flex: 1; min-width: 200px;">
<p style="margin: 0; font-size: 0.875rem; opacity: 0.7;">Original Investment</p>
<h2 style="margin: 0.25rem 0 0 0; font-weight: 400;">{ORIGINAL_INVESTMENT:,.2f} THB</h2>
</div>
<div style="flex: 1; min-width: 200px;">
<div style="display: flex; align-items: center; gap: 0.5rem;">
<p style="margin: 0; font-size: 0.875rem; opacity: 0.7;">Real P/L</p>
<span style="color: {pl_color}; font-weight: bold; font-size: 0.9rem;">{pl_arrow} {real_pl_pct:.2f}%</span>
</div>
<h2 style="margin: 0.25rem 0 0 0; font-weight: 400;">{real_pl:,.2f} THB</h2>
</div>
</div>
</div>
"""

# Render the custom card
st.markdown(custom_card, unsafe_allow_html=True)


# --- BOTTOM ROW: STOCK ONLY PERFORMANCE ---
st.subheader("Stock Holdings Performance")

# 1. Calculate the values and colors for the Stock P/L
stock_pl = total_val - total_cost
stock_pl_pct = (stock_pl / total_cost) * 100 if total_cost != 0 else 0
stock_pl_color = "#09ab3b" if stock_pl >= 0 else "#ff2b2b"
stock_pl_arrow = "↑" if stock_pl >= 0 else "↓"

# 2. Build the transparent HTML layout
stock_card = f"""
<div style="margin-bottom: 1rem; padding: 0.5rem 0;">
<div style="display: flex; flex-wrap: wrap; gap: 1rem;">
<div style="flex: 1; min-width: 200px;">
<p style="margin: 0; font-size: 0.875rem; opacity: 0.7;">Total Stock Value</p>
<h2 style="margin: 0.25rem 0 0 0; font-weight: 400;">{total_val:,.2f} THB</h2>
</div>
<div style="flex: 1; min-width: 200px;">
<p style="margin: 0; font-size: 0.875rem; opacity: 0.7;">Total Stock Cost</p>
<h2 style="margin: 0.25rem 0 0 0; font-weight: 400;">{total_cost:,.2f} THB</h2>
</div>
<div style="flex: 1; min-width: 200px;">
<div style="display: flex; align-items: center; gap: 0.5rem;">
<p style="margin: 0; font-size: 0.875rem; opacity: 0.7;">Stock P/L</p>
<span style="color: {stock_pl_color}; font-weight: bold; font-size: 0.9rem;">{stock_pl_arrow} {stock_pl_pct:.2f}%</span>
</div>
<h2 style="margin: 0.25rem 0 0 0; font-weight: 400;">{stock_pl:,.2f} THB</h2>
</div>
</div>
</div>
"""

# 3. Render it to the screen
st.markdown(stock_card, unsafe_allow_html=True)


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

st.plotly_chart(fig, use_container_width=True, key=f"chart_{sort_option}", config={'displayModeBar': False})
