import pandas as pd
import numpy as np
import yfinance as yf

from langchain_groq import ChatGroq

import streamlit as st

api_key = st.secrets["GROQ_API_KEY"]

llm = ChatGroq(
    api_key=api_key,
    model="llama-3.3-70b-versatile"
)
from langchain_core.prompts import PromptTemplate

portfolio_template = """
You are a financial advisor.

Portfolio Details:
Weights: {weights}
Expected Return: {portfolio_return}
Risk (Volatility): {portfolio_risk}

Give:
1. Portfolio assessment
2. Risk level
3. Diversification suggestions
4. Improvement recommendations
"""

portfolio_prompt = PromptTemplate(
    input_variables=["weights", "portfolio_return", "portfolio_risk"],
    template=portfolio_template
)

portfolio_chain = portfolio_prompt | llm

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y")
    return data

def parse_portfolio(text):
    portfolio = {}
    
    # Replace commas with spaces
    text = text.replace(",", " ")
    
    parts = text.split()
    
    # Process in pairs (stock, value)
    i = 0
    while i < len(parts) - 1:
        
        stock = parts[i].strip()
        value = parts[i+1].replace("₹", "").replace(",", "")
        
        try:
            value = float(value)
        except:
            i += 1
            continue
        
        # Clean ticker
        stock = stock.replace(":", "").replace(",", "")
        
        # Add .NS if missing
        if ".NS" not in stock:
            stock = stock + ".NS"
        
        portfolio[stock] = value
        
        i += 2
    
    return portfolio
def get_portfolio_data(portfolio):
    data = {}
    
    for stock in portfolio:
        try:
            df = get_stock_data(stock)
            
            if df.empty:
                print(f"Skipping {stock} (no data)")
                continue
            
            data[stock] = df
        
        except:
            print(f"Error fetching {stock}")
    
    return data

def calculate_portfolio_metrics(data, portfolio):
    
    total_value = sum(portfolio.values())
    
    weights = {}
    returns = {}
    returns_df = pd.DataFrame()
    
    for stock in data:
        df = data[stock].copy()
        
        df['returns'] = df['Close'].pct_change()
        
        avg_return = df['returns'].mean()
        
        returns[stock] = avg_return
        weights[stock] = portfolio[stock] / total_value
        
        returns_df[stock] = df['returns']
    
    returns_df = returns_df.dropna()
    
    # Portfolio Return
    portfolio_return = sum(weights[s] * returns[s] for s in returns)
    
    # Portfolio Risk (CORRECT WAY)
    cov_matrix = returns_df.cov()
    
    weights_array = np.array([weights[s] for s in returns_df.columns])
    
    portfolio_risk = np.sqrt(
        np.dot(weights_array.T, np.dot(cov_matrix, weights_array))
    )
    
    return portfolio_return, portfolio_risk, weights

def analyze_portfolio(chain, portfolio_return, portfolio_risk, weights):
    
    response = chain.invoke({
        "weights": weights,
        "portfolio_return": portfolio_return,
        "portfolio_risk": portfolio_risk
    })
    
    return response.content

def run_portfolio_analysis(user_input_text):
    
    portfolio = parse_portfolio(user_input_text)
    
    data = get_portfolio_data(portfolio)
    
    portfolio_return, portfolio_risk, weights = calculate_portfolio_metrics(data, portfolio)
    
    analysis = analyze_portfolio(
        portfolio_chain,
        portfolio_return,
        portfolio_risk,
        weights
    )
    
    return {
        "portfolio_return": portfolio_return,
        "portfolio_risk": portfolio_risk,
        "weights": weights,
        "analysis": analysis
    }
