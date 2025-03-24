from datetime import datetime, timedelta
from math import sqrt
from duckdb import df
import matplotlib.pyplot as plt
from numpy import quantile
import pandas as pd
import streamlit as st
from vnstock import Vnstock
import pandas as pd
from scipy.stats import norm
import numpy as np

from src.plots import get_stock_price
def calculate_quant_metrics(stock, end_date):
    # Constants
    TRADING_DAYS = 252
    RISK_FREE_RATE = 0.0267
    BETA_ADJUSTMENT = 0.67
    
    # Get time period from user
    years = st.selectbox("Chọn số năm phân tích: ", [5, 7, 10], index=0)
    start_date = end_date - timedelta(days=365*years)
    
    # Get price data
    df_price = get_stock_price(stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), interval="1D")
    df_index = get_stock_price("VNINDEX", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), interval="1D")
    df_data = df_price.merge(df_index[['time', 'close']].rename(columns={'close': 'close_index'}), on='time', how='inner')
    df_data.set_index('time', inplace=True)
    
    # Calculate returns
    ret_stock = np.log(df_data["close"] / df_data["close"].shift(1)).dropna()
    ret_index = np.log(df_data["close_index"] / df_data["close_index"].shift(1)).dropna()
    
    # Calculate risk metrics
    annual_return = (ret_stock.mean() * TRADING_DAYS) if len(ret_stock) > 0 else 0
    annual_std = (ret_stock.std() * sqrt(TRADING_DAYS)) if len(ret_stock) > 0 else 0
    sharpe_ratio = (annual_return - RISK_FREE_RATE) / annual_std if annual_std != 0 else 0
    
    # Calculate beta
    beta = np.cov(ret_stock, ret_index)[0][1] / np.var(ret_index)
    beta_adj = BETA_ADJUSTMENT * beta + (1 - BETA_ADJUSTMENT) * 1
    
    # Calculate drawdown and VaR
    current_price = df_data.iloc[-1]["close"]
    peak = df_data["close"].cummax()
    drawdown = (df_data["close"] - peak) / peak * 100
    max_drawdown = drawdown.min()
    sortino = (annual_return - RISK_FREE_RATE) / (ret_stock[ret_stock < 0].std() * sqrt(TRADING_DAYS))
    VaR = quantile(ret_stock, 0.05) * 100
    
    # Calculate CAGR
    n_years = np.ceil((df_data.index[-1] - df_data.index[0]).days / 365)
    cagr = (df_data.iloc[-1]["close"] / df_data["close"][0]) ** (1/n_years) - 1
    
    # Calculate maximum drawdown duration
    durations = []
    current_duration = 0
    
    for dd in drawdown:
        if dd < 0:
            current_duration += 1
        elif current_duration > 0:
            durations.append(current_duration)
            current_duration = 0
    if current_duration > 0:
        durations.append(current_duration)
        
    max_duration = max(durations) if durations else 0
    
    # Create metrics dataframe
    metrics = pd.DataFrame({
        "Chỉ số": ["Giá hiện tại", "Lợi nhuận trung bình năm", "Độ biến động trung bình năm",
                   "Tăng trưởng kép hàng năm (CAGR)", "Tỷ lệ Sharpe", "Tỷ lệ Sortino",    
                   "Beta", "Max Drawdown","Max Drawdown Duration", "VaR"],
        "Giá Trị": [f"{int(current_price*1000):,} VND", f"{annual_return*100:.2f}%", 
                    f"{annual_std*100:.2f}%", f"{cagr*100:.2f}%", f"{sharpe_ratio:.2f}",
                    f"{sortino:.2f}", f"{beta_adj:.2f}", f"{max_drawdown:.2f}%", f"{max_duration:.0f} ngày", f"{VaR:.2f}%"],
       
    })
    
    return metrics

def calculate_stock_metrics(df_price, df_index, df_pricing):
    # Constants
    TARGET_YEAR = 2025
    SAFETY_MARGIN_THRESHOLD = 0.3
    
    # Data preparation
    df_price.set_index('time', inplace=True)
    
    # Calculate target and current prices
    target_price = round(df_pricing[pd.to_datetime(df_pricing['reportDate']).dt.year == TARGET_YEAR]['targetPrice'].mean(), 2)
    current_price = df_price.iloc[-1]["close"]
    
    # Calculate safety margin and recommendation
    safety_margin = (target_price - current_price) / target_price
    recommendation = (
        "Mua" if safety_margin > SAFETY_MARGIN_THRESHOLD 
        else "Nắm giữ" if safety_margin > 0 
        else "Bán"
    )
    
    # Create metrics dataframe
    metrics = pd.DataFrame({
        "Thông Số": ["Định giá", "Giá hiện tại", "Khuyến nghị", "Biên an toàn"],
        "Giá Trị": [
            f"{int(target_price*1000):,} VND",
            f"{int(current_price*1000):,} VND",
            recommendation,
            f"{safety_margin*100:.2f}%"
        ]
    })
    
    return metrics