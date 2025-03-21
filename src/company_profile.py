from datetime import datetime, timedelta
from math import sqrt
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from vnstock import Vnstock
import pandas as pd

def calculate_stock_metrics(df_price, df_index, df_pricing):
    # Calculate returns
    ret_stock = df_price["close"].pct_change().dropna()
    ret_index = df_index["close"].pct_change().dropna()
    
    # Calculate risk metrics
    annual_return = (ret_stock.mean() * 252) if len(ret_stock) > 0 else 0
    annual_std = (ret_stock.std() * sqrt(252)) if len(ret_stock) > 0 else 0
    sharpe_ratio = annual_return / annual_std if annual_std != 0 else 0
    beta = ret_stock.cov(ret_index) / ret_index.var()
    
    # Calculate pricing metrics
    target_price = round(df_pricing["avgTargetPrice"].mean(), 2)
    current_price = df_price['close'][0]
    safety_margin = target_price/current_price - 1
    recommendation = "Mua" if safety_margin > 0.2 else "Bán"
    
    # Create metrics dataframe
    metrics = pd.DataFrame({
        "Thông Số": [
            "Định giá", 
            "Giá hiện tại",
            "Khuyến nghị",
            "Biên an toàn",
            "Tỷ xuất sinh lời hàng năm", 
            "Độ biến động hàng năm",
            "Tỷ lệ Sharpe",
            "Beta"
        ],
        "Giá Trị": [
            target_price,
            current_price,
            recommendation,
            f"{safety_margin*100:.2f}%",
            f"{annual_return*100:.2f}%", 
            f"{annual_std*100:.2f}%",
            f"{sharpe_ratio:.2f}",
            f"{beta:.2f}"
        ]
    })
    
    return metrics