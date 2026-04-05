import streamlit as st
from finance_utils import run_portfolio_analysis, get_stock_data, llm
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="AI Financial Advisor", layout="wide")

st.title("💼 AI Financial Advisor")

# ---------------- Tabs ----------------
tab1, tab2, tab3 = st.tabs([
    "📁 Portfolio Analyzer",
    "📈 Stock Analyzer",
    "💬 Chatbot"
])


# -------- PORTFOLIO --------
with tab1:
    st.subheader("Portfolio Analysis")

    # 1. User Guidance
    st.markdown("""
    **📝 How to enter your portfolio:**
    Type the stock ticker symbol followed by the total invested amount in rupees. Separate multiple entries with a space.
    *(Example: `TCS 100000 HDFCBANK 200000 INFY 50000`)*
    """)

    user_input = st.text_area(
        "Enter Portfolio",
        placeholder="TCS 100000 HDFCBANK 200000",
        label_visibility="collapsed"
    )

    if st.button("Analyze Portfolio"):
        if user_input:
            result = run_portfolio_analysis(user_input)

            st.success("Analysis Complete")

            col1, col2 = st.columns(2)

            # Format as Percentage
            col1.metric("Annualized Return", f"{result['portfolio_return'] * 252:.2%}")
            col2.metric("Annualized Risk (Vol)", f"{result['portfolio_risk'] * (252**0.5):.2%}")

            st.write("### 🍰 Asset Allocation")
            # Convert weights dict to DataFrame for Plotly
            df_weights = pd.DataFrame(list(result["weights"].items()), columns=['Stock', 'Weight'])
            fig = px.pie(df_weights, values='Weight', names='Stock', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)

            st.write("### 💡 AI Strategic Advice")
            st.info(result["analysis"])

    st.markdown("---")
    
    # 2. Methodology Information
    with st.expander("ℹ️ How are Returns and Risk calculated?"):
        st.write("""
        * **Data Source:** We pull the most recent 5-year historical daily closing prices using Yahoo Finance (`yfinance`).
        * **Expected Return:** Calculated using the weighted average of the annualized historical daily returns for each asset in your portfolio.
        * **Portfolio Risk:** Represents the annualized volatility. We use a covariance matrix to calculate this, which means we don't just look at individual            stock risk, but also how your selected stocks move in relation to one another.
        """)
        
    # 3. Disclaimer
    st.caption("⚠️ **Disclaimer:** The insights and metrics provided by this AI Financial Advisor are based on historical data and generative AI models. This     tool is strictly for educational and informational purposes and does not constitute professional financial advice. Always consult with a certified   financial planner before making investment decisions.")

# -------- STOCK --------
with tab2:
    st.subheader("📈 Stock Analysis & Technicals")

    ticker = st.text_input("Enter Stock Ticker (e.g. TCS, INFY, RELIANCE)", placeholder="TCS")

    if st.button("Analyze Stock"):
        if ticker:
            # Clean up the ticker string
            clean_ticker = ticker.strip().upper()
            if ".NS" not in clean_ticker:
                clean_ticker += ".NS"

            with st.spinner(f"Fetching market data for {clean_ticker}..."):
                data = get_stock_data(clean_ticker)

            if not data.empty:
                # 1. Calculate Key Metrics (using the last 252 trading days for a 1-year view)
                data_1y = data.tail(252)
                
                latest_price = data_1y["Close"].iloc[-1]
                prev_price = data_1y["Close"].iloc[-2]
                daily_change = (latest_price - prev_price) / prev_price
                
                high_52w = data_1y["High"].max()
                low_52w = data_1y["Low"].min()

                # 2. Display Metrics in a clean row
                st.write("### 📊 Key Metrics")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Latest Price", f"₹{latest_price:,.2f}", f"{daily_change:.2%}")
                c2.metric("52-Week High", f"₹{high_52w:,.2f}")
                c3.metric("52-Week Low", f"₹{low_52w:,.2f}")
                c4.metric("Distance to High", f"{(latest_price/high_52w)-1:.2%}")

                # 3. Professional Candlestick Chart
                st.write("### 🕯️ Price Action (1 Year)")
                fig = go.Figure(data=[go.Candlestick(
                    x=data_1y.index,
                    open=data_1y['Open'],
                    high=data_1y['High'],
                    low=data_1y['Low'],
                    close=data_1y['Close'],
                    name=clean_ticker
                )])
                
                # Make it look sleek and hide the bulky bottom slider
                fig.update_layout(
                    template="plotly_dark",
                    margin=dict(l=0, r=0, t=0, b=0),
                    xaxis_rangeslider_visible=False 
                )
                st.plotly_chart(fig, use_container_width=True)

                # 4. Upgraded AI Technical Prompt
                prompt = f"""
                You are a technical equity analyst.
                Analyze the Indian stock {clean_ticker} based on this recent data:
                - Latest Price: ₹{latest_price:.2f}
                - Daily Change: {daily_change:.2%}
                - 52-Week High: ₹{high_52w:.2f}
                - 52-Week Low: ₹{low_52w:.2f}

                Provide a concise response containing:
                1. A brief assessment of its current trading position relative to its 52-week range.
                2. Potential psychological support and resistance levels based on these highs/lows.
                3. A short, professional technical outlook.
                """
                
                with st.spinner("Generating AI Technical Analysis..."):
                    response = llm.invoke(prompt)

                st.write("### 🤖 AI Technical Insights")
                st.info(response.content)
            else:
                st.error("Could not fetch data. Please check the ticker symbol.")

# -------- CHAT --------
with tab3:
    st.subheader("Finance Chatbot")

    # 1. Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 2. Display ALL chat messages from history first
    for role, text in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(text)

    # 3. Get user input at the bottom of the UI
    user_q = st.chat_input("Ask anything about finance...")

    if user_q:
        # Save user message to history silently
        st.session_state.chat_history.append(("human", user_q))

        # Get AI response and save to history silently
        with st.spinner("Analyzing..."):
            response = llm.invoke(st.session_state.chat_history)
        st.session_state.chat_history.append(("ai", response.content))

        # Force a quick page refresh to redraw the UI in the correct order
        st.rerun()