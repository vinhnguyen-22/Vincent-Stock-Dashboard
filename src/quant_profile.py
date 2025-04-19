from datetime import datetime, timedelta
from math import sqrt

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from duckdb import df
from numpy import quantile
from scipy.stats import norm
from vnstock import Vnstock

from src.plots import get_stock_price


def calculate_returns(df_data):
    """Calculate log returns for stock and index"""
    ret_stock = np.log(df_data["close"] / df_data["close"].shift(1)).dropna()
    ret_index = np.log(df_data["close_index"] / df_data["close_index"].shift(1)).dropna()
    return ret_stock, ret_index


def calculate_extended_metrics(returns):
    from math import sqrt

    import numpy as np

    ann_return = returns.mean() * 252
    ann_std = returns.std() * sqrt(252)
    sharpe = ann_return / ann_std if ann_std > 0 else 0

    downside_std = returns[returns < 0].std() * sqrt(252) if len(returns[returns < 0]) > 0 else 1
    sortino = ann_return / downside_std if downside_std > 0 else 0

    cumulative = (1 + returns).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    max_drawdown = drawdown.min()

    calmar = ann_return / abs(max_drawdown) if max_drawdown != 0 else 0

    var_95 = returns.quantile(0.05)

    return {
        "Annual Return": ann_return,
        "Annual Std": ann_std,
        "Sharpe Ratio": sharpe,
        "Sortino Ratio": sortino,
        "Max Drawdown": max_drawdown,
        "Calmar Ratio": calmar,
        "VaR (95%)": var_95,
    }


def calculate_risk_metrics(returns):
    """Calculate risk metrics: annual return, std, Sharpe ratio, and Sortino ratio"""
    annual_return = returns.mean() * 252
    annual_std = returns.std() * sqrt(252)

    # Sharpe ratio (assuming risk-free rate = 0 for simplicity)
    sharpe_ratio = annual_return / annual_std if annual_std != 0 else 0

    # Sortino ratio (considering only negative returns)
    negative_returns = returns[returns < 0]
    downside_std = negative_returns.std() * sqrt(252) if len(negative_returns) > 0 else 1
    sortino = annual_return / downside_std if downside_std != 0 else 0

    return annual_return, annual_std, sharpe_ratio, sortino


def calculate_beta(ret_stock, ret_index):
    """Calculate beta coefficient using covariance method"""
    covariance = np.cov(ret_stock, ret_index)[0][1]
    variance = np.var(ret_index)
    beta = covariance / variance if variance != 0 else 1
    return beta


def calculate_drawdown_metrics(df_data, column="close"):
    """Calculate maximum drawdown and its duration"""
    peak = df_data[column].expanding().max()
    drawdown = ((df_data[column] - peak) / peak) * 100
    max_drawdown = drawdown.min()

    # Calculate drawdown duration
    is_drawdown = drawdown < 0
    drawdown_start = is_drawdown.ne(is_drawdown.shift()).cumsum()
    drawdown_duration = is_drawdown.groupby(drawdown_start).cumsum()
    max_duration = drawdown_duration.max()

    return max_drawdown, max_duration


def plot_drawdown(df_data):
    """Plot drawdown chart using Plotly"""
    df_data = df_data[~df_data.index.duplicated(keep="first")]

    peak = df_data["close"].cummax()
    drawdown = (df_data["close"] - peak) / peak * 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_data.index, y=drawdown, fill="tozeroy", name="Drawdown"))
    fig.update_layout(
        title="Biểu đồ Drawdown",
        xaxis_title="Thời gian",
        yaxis_title="Drawdown (%)",
    )
    return fig


def plot_returns_distribution(ret_stock):
    """Plot returns distribution using Plotly"""

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=ret_stock, nbinsx=50, name="Returns"))
    fig.update_layout(title="Phân phối lợi nhuận", xaxis_title="Lợi nhuận", yaxis_title="Tần suất")
    return fig


def calculate_quant_metrics(stock, end_date, years):
    # Get analysis period from user
    start_date = end_date - timedelta(days=365 * years)

    # Get and merge price data
    df_price = get_stock_price(
        stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), interval="1D"
    )
    df_index = get_stock_price(
        "VNINDEX", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), interval="1D"
    )
    df_data = df_price.merge(
        df_index[["time", "close"]].rename(columns={"close": "close_index"}),
        on="time",
        how="inner",
    )
    df_data.set_index("time", inplace=True)

    # Calculate all metrics
    ret_stock, ret_index = calculate_returns(df_data)
    annual_return, annual_std, sharpe_ratio, sortino = calculate_risk_metrics(ret_stock)
    beta_adj = calculate_beta(ret_stock, ret_index)
    max_drawdown, max_duration = calculate_drawdown_metrics(df_data)
    # Calculate CAGR and VaR
    n_years = np.ceil((df_data.index[-1] - df_data.index[0]).days / 365)
    cagr = (df_data.iloc[-1]["close"] / df_data["close"][0]) ** (1 / n_years) - 1
    VaR = quantile(ret_stock, 0.05) * 100
    current_price = df_data.iloc[-1]["close"]

    # Create metrics dataframe
    metrics_df = pd.DataFrame(
        {
            "Chỉ số": [
                "Giá hiện tại",
                "Lợi nhuận trung bình năm",
                "Độ biến động trung bình năm",
                "Tăng trưởng kép hàng năm (CAGR)",
                "Tỷ lệ Sharpe",
                "Tỷ lệ Sortino",
                "Beta",
                "Max Drawdown",
                "Max Drawdown Duration",
                "VaR",
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
                f"{max_duration:.0f} ngày",
                f"{VaR:.2f}%",
            ],
        }
    )

    # Create tabs for visualization
    tab1, tab2, tab3 = st.tabs(["Chỉ số", "Drawdown", "Phân phối"])

    with tab1:
        st.dataframe(metrics_df.set_index("Chỉ số"), use_container_width=True)
    with tab2:
        st.plotly_chart(plot_drawdown(df_data), use_container_width=True)
    with tab3:
        st.plotly_chart(plot_returns_distribution(ret_stock), use_container_width=True)

    return metrics_df


def calculate_stock_metrics(df_price, df_index, df_pricing):
    # Constants
    TARGET_YEAR = 2025
    SAFETY_MARGIN_THRESHOLD = 0.3

    try:
        # Data preparation
        df_price.set_index("time", inplace=True)

        # Calculate target and current prices
        target_price = round(
            df_pricing[pd.to_datetime(df_pricing["reportDate"]).dt.year == TARGET_YEAR][
                "targetPrice"
            ].mean(),
            2,
        )
        current_price = df_price.iloc[-1]["close"]

        # Calculate safety margin and recommendation
        safety_margin = (target_price - current_price) / target_price
        recommendation = (
            "Mua"
            if safety_margin > SAFETY_MARGIN_THRESHOLD
            else "Nắm giữ" if safety_margin > 0 else "Bán"
        )

        # Create metrics dataframe
        metrics = pd.DataFrame(
            {
                "Thông Số": ["Định giá", "Giá hiện tại", "Khuyến nghị", "Biên an toàn"],
                "Giá Trị": [
                    f"{int(target_price*1000):,} VND",
                    f"{int(current_price*1000):,} VND",
                    recommendation,
                    f"{safety_margin*100:.2f}%",
                ],
            }
        )
        return st.dataframe(metrics.set_index("Thông Số"), use_container_width=True)
    except:
        return st.write("Không có dữ liệu")
