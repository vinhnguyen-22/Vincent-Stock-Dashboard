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
    df_price = get_stock_price(stock, "2015-01-01", end_date.strftime("%Y-%m-%d"))
    df_index = get_stock_price("VNINDEX", "2015-01-01", end_date.strftime("%Y-%m-%d"))
    rf = 0.0267
    df_data = df_price.merge(df_index[['time', 'close']].rename(columns={'close': 'close_index'}), on='time', how='inner')
    df_data.set_index('time', inplace=True)
    # Calculate returns
    ret_stock = np.log(df_data["close"] / df_data["close"].shift(1)).dropna()
    ret_index = np.log(df_data["close_index"] / df_data["close_index"].shift(1)).dropna()
    
    # Calculate risk metrics
    annual_return = (ret_stock.mean() * 252) if len(ret_stock) > 0 else 0
    annual_std = (ret_stock.std() * sqrt(252)) if len(ret_stock) > 0 else 0
    sharpe_ratio = (annual_return - rf) / annual_std if annual_std != 0 else 0
    beta = ret_stock.cov(ret_index) / ret_index.var()
    beta_adj = 0.67 * beta + 0.33 * 1
   
    current_price = df_data.iloc[-1]["close"]
    peak = df_data["close"].cummax()
    drawdown = (df_data["close"] - peak) / peak * 100
    max_drawdown = drawdown.min()
    sortino = (annual_return - rf) / (ret_stock[ret_stock < 0].std() * sqrt(252))
    VaR = quantile(ret_stock, 0.05) *100

    n_years = (df_data.index[-1] - df_data.index[0]).days / 365
    cagr = (df_data.iloc[-1]["close"]/ df_data["close"][0]) ** (1/n_years) - 1

    metrics = pd.DataFrame({
        "Thông Số": [
            "Giá hiện tại",
            "Tỷ xuất sinh lời hàng năm", 
            "Tăng trưởng kép hàng năm",
            "Độ biến động hàng năm",
            "Tỷ lệ Sharpe",
            "Tỷ lệ Sortino",    
            "Beta",
            "Max drawdown",
            "VaR" 
        ],
        "Giá Trị": [
            f"{int(current_price*1000):,} VND",
            f"{annual_return*100:.2f}%", 
            f"{cagr*100:.2f}%",
            f"{annual_std*100:.2f}%",
            f"{sharpe_ratio:.2f}",
            f"{sortino:.2f}",
            f"{beta_adj:.2f}",
            f"{max_drawdown:.2f}%",
            f"{VaR:.2f}%"
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