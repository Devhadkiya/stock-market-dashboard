import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide"
)

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .metric-card {
        background: #1c1c2e;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #2d2d44;
    }
    .positive { color: #00ff88; }
    .negative { color: #ff4444; }
    h1 { color: #00ff88; }
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.title("📈 Real-Time Stock Market Dashboard")
st.markdown("Live stock data powered by Yahoo Finance")

# ---------- SIDEBAR ----------
st.sidebar.header("Settings")

# Stock selector
popular_stocks = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA',
                  'META', 'NVDA', 'NFLX', 'AMD', 'INTC']

selected_stocks = st.sidebar.multiselect(
    "Select Stocks",
    options=popular_stocks,
    default=['AAPL', 'MSFT', 'NVDA']
)

# Time period
period = st.sidebar.selectbox(
    "Time Period",
    options=['1mo', '3mo', '6mo', '1y', '2y', '5y'],
    index=3
)

# Moving averages
show_ma20  = st.sidebar.checkbox("Show MA20",  value=True)
show_ma50  = st.sidebar.checkbox("Show MA50",  value=True)
show_ma200 = st.sidebar.checkbox("Show MA200", value=False)

# Auto refresh
refresh = st.sidebar.selectbox(
    "Auto Refresh",
    options=['Off', '30s', '60s', '5min'],
    index=2
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Built by Dev Hadakiya**")
st.sidebar.markdown("Data Science Portfolio Project")

if not selected_stocks:
    st.warning("Please select at least one stock from the sidebar!")
    st.stop()

# ---------- FETCH DATA ----------
@st.cache_data(ttl=60)
def get_stock_data(ticker, period):
    stock = yf.Ticker(ticker)
    df    = stock.history(period=period)
    info  = stock.info
    return df, info

# ---------- RSI CALCULATION ----------
def calc_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.where(delta > 0, 0).rolling(period).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))

# ---------- MAIN STOCK (first selected) ----------
main_ticker = selected_stocks[0]
df, info = get_stock_data(main_ticker, period)

# ---------- KPI CARDS ----------
curr_price  = df['Close'].iloc[-1]
prev_price  = df['Close'].iloc[-2]
change      = curr_price - prev_price
change_pct  = (change / prev_price) * 100
high_52w    = df['High'].max()
low_52w     = df['Low'].min()
avg_vol     = df['Volume'].mean()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Current Price", f"${curr_price:.2f}",
              f"{change:+.2f} ({change_pct:+.2f}%)")
with col2:
    st.metric("52W High", f"${high_52w:.2f}")
with col3:
    st.metric("52W Low",  f"${low_52w:.2f}")
with col4:
    st.metric("Avg Volume", f"{avg_vol/1e6:.1f}M")
with col5:
    mkt_cap = info.get('marketCap', 0)
    st.metric("Market Cap", f"${mkt_cap/1e9:.1f}B" if mkt_cap else "N/A")

st.markdown("---")

# ---------- CANDLESTICK + VOLUME CHART ----------
st.subheader(f"📊 {main_ticker} — Price Chart")

# Calculate MAs
df['MA20']  = df['Close'].rolling(20).mean()
df['MA50']  = df['Close'].rolling(50).mean()
df['MA200'] = df['Close'].rolling(200).mean()

fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    row_heights=[0.6, 0.2, 0.2],
    vertical_spacing=0.03
)

# Candlestick
fig.add_trace(go.Candlestick(
    x=df.index, open=df['Open'], high=df['High'],
    low=df['Low'], close=df['Close'],
    name=main_ticker,
    increasing_line_color='#00ff88',
    decreasing_line_color='#ff4444'
), row=1, col=1)

# Moving averages
if show_ma20:
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'],
        name='MA20', line=dict(color='#f39c12', width=1.5)), row=1, col=1)
if show_ma50:
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'],
        name='MA50', line=dict(color='#3498db', width=1.5)), row=1, col=1)
if show_ma200:
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'],
        name='MA200', line=dict(color='#9b59b6', width=1.5)), row=1, col=1)

# Volume bars
colors = ['#00ff88' if c >= o else '#ff4444'
          for c, o in zip(df['Close'], df['Open'])]
fig.add_trace(go.Bar(
    x=df.index, y=df['Volume'],
    name='Volume', marker_color=colors, opacity=0.7
), row=2, col=1)

# RSI
rsi = calc_rsi(df['Close'])
fig.add_trace(go.Scatter(
    x=df.index, y=rsi,
    name='RSI', line=dict(color='#e74c3c', width=1.5)
), row=3, col=1)
fig.add_hline(y=70, line_dash='dash', line_color='red',   opacity=0.5, row=3, col=1)
fig.add_hline(y=30, line_dash='dash', line_color='green', opacity=0.5, row=3, col=1)

fig.update_layout(
    template='plotly_dark',
    height=700,
    showlegend=True,
    xaxis_rangeslider_visible=False,
    paper_bgcolor='#0e1117',
    plot_bgcolor='#0e1117'
)
fig.update_yaxes(title_text="Price ($)", row=1, col=1)
fig.update_yaxes(title_text="Volume",   row=2, col=1)
fig.update_yaxes(title_text="RSI",      row=3, col=1)

st.plotly_chart(fig, use_container_width=True)

# ---------- MULTI STOCK COMPARISON ----------
if len(selected_stocks) > 1:
    st.markdown("---")
    st.subheader("📊 Multi-Stock Price Comparison (Normalised)")

    fig2 = go.Figure()
    colors_list = ['#00ff88', '#3498db', '#f39c12',
                   '#e74c3c', '#9b59b6', '#1abc9c']

    for i, ticker in enumerate(selected_stocks):
        d, _ = get_stock_data(ticker, period)
        normalized = (d['Close'] / d['Close'].iloc[0]) * 100
        fig2.add_trace(go.Scatter(
            x=d.index, y=normalized,
            name=ticker,
            line=dict(color=colors_list[i % len(colors_list)], width=2)
        ))

    fig2.update_layout(
        template='plotly_dark',
        height=400,
        yaxis_title="Normalised Price (Base=100)",
        paper_bgcolor='#0e1117',
        plot_bgcolor='#0e1117'
    )
    st.plotly_chart(fig2, use_container_width=True)

# ---------- STOCK SUMMARY TABLE ----------
st.markdown("---")
st.subheader("📋 Stock Summary")

summary_data = []
for ticker in selected_stocks:
    d, inf = get_stock_data(ticker, period)
    cp  = d['Close'].iloc[-1]
    pp  = d['Close'].iloc[-2]
    chg = ((cp - pp) / pp) * 100
    summary_data.append({
        'Ticker':        ticker,
        'Price':         f"${cp:.2f}",
        'Change %':      f"{chg:+.2f}%",
        '52W High':      f"${d['High'].max():.2f}",
        '52W Low':       f"${d['Low'].min():.2f}",
        'Avg Volume':    f"{d['Volume'].mean()/1e6:.1f}M",
    })

st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

# ---------- AUTO REFRESH ----------
if refresh != 'Off':
    import time
    intervals = {'30s': 30, '60s': 60, '5min': 300}
    time.sleep(intervals[refresh])
    st.rerun()

st.markdown("---")
st.caption("Data source: Yahoo Finance | Built with Streamlit & Plotly")