import streamlit as st
from finance_utils import run_portfolio_analysis, get_stock_data
import pandas as pd

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

    user_input = st.text_area(
        "Enter Portfolio",
        placeholder="TCS 100000 HDFCBANK 200000"
    )

    if st.button("Analyze Portfolio"):
        if user_input:
            result = run_portfolio_analysis(user_input)

            st.success("Analysis Complete")

            col1, col2 = st.columns(2)

            col1.metric("Return", result["portfolio_return"])
            col2.metric("Risk", result["portfolio_risk"])

            st.write("### Weights")
            st.write(result["weights"])
            
            st.write("### AI Insights")
            st.write(result["analysis"])

# -------- STOCK --------
with tab2:
    st.subheader("Stock Analysis")

    ticker = st.text_input("Enter Stock (e.g. TCS, INFY)")

    if st.button("Analyze Stock"):
        if ticker:
            if ".NS" not in ticker:
                ticker += ".NS"

            data = get_stock_data(ticker)

            if not data.empty:
                st.line_chart(data["Close"])

                latest_price = data["Close"].iloc[-1]
                avg_price = data["Close"].mean()

                prompt = f"""
                Analyze this stock:
                Latest Price: {latest_price}
                Average Price: {avg_price}
                """

                response = llm.invoke(prompt)

                st.write("### AI Analysis")
                st.write(response.content)

# -------- CHAT --------
chat_history = []

with tab3:
    st.subheader("Finance Chatbot")

    user_q = st.text_input("Ask anything about finance")

    if st.button("Ask"):
        if user_q:
            chat_history.append(("human", user_q))

            response = llm.invoke(chat_history)

            chat_history.append(("ai", response.content))

            st.write(response.content)
