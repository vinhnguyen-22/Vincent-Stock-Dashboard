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
    N = 252
    rf = 0.0267
    years = st.selectbox("Chọn khoảng thời gian phân tích", [5, 7, 10], index=0)
    start_date = end_date - timedelta(days=365*years)
    df_price = get_stock_price(stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), interval="1D")
    df_index = get_stock_price("VNINDEX", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), interval="1D")
    df_data = df_price.merge(df_index[['time', 'close']].rename(columns={'close': 'close_index'}), on='time', how='inner')
    df_data.set_index('time', inplace=True)
    # Calculate returns
    ret_stock = np.log(df_data["close"] / df_data["close"].shift(1)).dropna()
    ret_index = np.log(df_data["close_index"] / df_data["close_index"].shift(1)).dropna()
    
    # Calculate risk metrics
    annual_return = (ret_stock.mean() * N) if len(ret_stock) > 0 else 0
    annual_std = (ret_stock.std() * sqrt(N)) if len(ret_stock) > 0 else 0
    sharpe_ratio = (annual_return - rf) / annual_std if annual_std != 0 else 0
    beta = ret_stock.cov(ret_index) / ret_index.var()
    beta_adj = 0.67 * beta + 0.33 * 1
    current_price = df_data.iloc[-1]["close"]
    peak = df_data["close"].cummax()
    drawdown = (df_data["close"] - peak) / peak * 100
    max_drawdown = drawdown.min()
    sortino = (annual_return - rf) / (ret_stock[ret_stock < 0].std() * sqrt(N))
    VaR = quantile(ret_stock, 0.05) *100

    n_years = np.ceil((df_data.index[-1] - df_data.index[0]).days / 365)
    st.write(n_years)
    cagr = (df_data.iloc[-1]["close"]/ df_data["close"][0]) ** (1/n_years) - 1

    metrics = pd.DataFrame({
        "Thông Số": [
            "Giá hiện tại",
            "Lợi nhuận trung bình năm", 
            "Độ biến động trung bình năm",
            "Tăng trưởng kép hàng năm (CAGR)",
            "Tỷ lệ Sharpe",
            "Tỷ lệ Sortino",    
            "Beta",
            "Max drawdown",
            "VaR" 
        ],
        "Giá Trị": [
            f"{int(current_price*1000):,} VND",
            f"{annual_return*100:.2f}%", 
            f"{annual_std*100:.2f}%",
            f"{cagr*100:.2f}%",
            f"{sharpe_ratio:.2f}",
            f"{sortino:.2f}",
            f"{beta_adj:.2f}",
            f"{max_drawdown:.2f}%",
            f"{VaR:.2f}%"
        ],
        "Đánh giá": [
            "",
            "GOOD" if annual_return > 0.15 else "BAD",
            "GOOD" if cagr > 0.15 else "BAD", 
            "GOOD" if annual_std < 0.25 else "BAD",
            "GOOD" if sharpe_ratio > 1 else "BAD",
            "GOOD" if sortino > 1 else "BAD",
            "GOOD" if 0.8 <= beta_adj <= 1.2 else "BAD",
            "GOOD" if max_drawdown > -30 else "BAD",
            "GOOD" if VaR > -2 else "BAD"
        ]
    })
    
    return metrics

def calculate_stock_metrics(df_price, df_index, df_pricing):
    df_price.set_index('time', inplace=True)
    target_price = round(df_pricing[pd.to_datetime(df_pricing['reportDate']).dt.year == 2025]['targetPrice'].mean(), 2)
    current_price = df_price.iloc[-1]["close"]
    safety_margin = ((target_price -current_price)/target_price)
    recommendation = "Mua" if safety_margin > 0.3 else "Nắm giữ" if safety_margin > 0 else "Bán"
    metrics = pd.DataFrame({
        "Thông Số": [
            "Định giá", 
            "Giá hiện tại",
            "Khuyến nghị",
            "Biên an toàn",
        ],
        "Giá Trị": [
            f"{int(target_price*1000):,} VND",
            f"{int(current_price*1000):,} VND",
            recommendation,
            f"{safety_margin*100:.2f}%",
            
        ]
    })
    
    return metrics