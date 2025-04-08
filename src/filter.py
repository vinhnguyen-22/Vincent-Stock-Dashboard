from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from vnstock import Vnstock

from src.optimize_portfolio import get_port, get_port_price
from src.plots import foreigner_trading_stock, get_firm_pricing, get_stock_price

HEADERS = {
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
}


def fetch_api_data(url, payload, headers):
    """Fetch data from API and return as a DataFrame."""
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return pd.DataFrame(response.json().get("data", []))
    else:
        st.error(f"API request failed with status code {response.status_code}")
        return None


def get_stock_data_from_api(market_cap_min, net_bought_val_avg_20d_min):
    """Retrieve stock data based on market cap and net bought value."""
    url = "https://screener-api.vndirect.com.vn/search_data"
    payload = {
        "fields": "code,companyNameVi,floor,priceCr,quarterReportDate,annualReportDate,marketCapCr,netForBoughtValAvgCr20d",
        "filters": [
            {"dbFilterCode": "marketCapCr", "condition": "GT", "value": market_cap_min},
            {
                "dbFilterCode": "netForBoughtValAvgCr20d",
                "condition": "GT",
                "value": net_bought_val_avg_20d_min,
            },
        ],
        "sort": "code:asc",
    }
    return fetch_api_data(url, payload, {"Content-Type": "application/json"})


def filter_stocks(end_date, market_cap=50, net_bought_val=1):
    """Filter stocks based on foreign ownership."""
    if st.button("Lọc cổ phiếu có tỷ trọng sở hữu nước ngoài cao nhất"):
        market_cap_min = market_cap * 1e12
        net_bought_val_avg_20d_min = net_bought_val * 1e9
        df = get_stock_data_from_api(market_cap_min, net_bought_val_avg_20d_min)

        if df is None or df.empty:
            st.warning("No data found.")
            return None

        start_date = end_date - timedelta(days=30)
        stocks_data = {}

        for symbol in df["code"]:
            foreign = foreigner_trading_stock(
                symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )
            if foreign:
                curr, total = foreign["currentRoom"], foreign["totalRoom"]
                ownership_ratio = round((total - curr) / total * 100, 2)
                stocks_data[symbol] = ownership_ratio

        sorted_stocks = pd.DataFrame.from_dict(
            stocks_data, orient="index", columns=["Ownership Ratio"]
        ).sort_values(by="Ownership Ratio", ascending=False)
        st.dataframe(sorted_stocks)
        return sorted_stocks


def get_industry_data(level=1, higher_level_code=0):
    """Retrieve industry data from API."""
    base_url = "https://api-finfo.vndirect.com.vn/v4/industry_classification"
    params = [f"industryLevel:{level}"]
    if higher_level_code:
        params.append(f"higherLevelCode:{higher_level_code}")
    url = f"{base_url}?q=" + "~".join(params)

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return pd.DataFrame(response.json().get("data", []))
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed: {e}")
        return None


def filter_stocks_by_industry():
    """Filter stocks by industry hierarchy."""
    industries_l1 = st.session_state.get("industries_l1") or get_industry_data(1)
    st.session_state["industries_l1"] = industries_l1

    industry_l1_name = st.selectbox("Chọn ngành cấp 1", industries_l1["vietnameseName"].tolist())
    if not industry_l1_name:
        return None

    industry_l1_code = industries_l1.loc[
        industries_l1["vietnameseName"] == industry_l1_name, "industryCode"
    ].iloc[0]
    industries_l2 = st.session_state.get("industries_l2") or get_industry_data(2, industry_l1_code)
    st.session_state["industries_l2"] = industries_l2

    industry_l2_name = st.selectbox("Chọn ngành cấp 2", industries_l2["vietnameseName"].tolist())
    if not industry_l2_name:
        return None

    industry_l2_code = industries_l2.loc[
        industries_l2["vietnameseName"] == industry_l2_name, "industryCode"
    ].iloc[0]
    industries_l3 = st.session_state.get("industries_l3") or get_industry_data(3, industry_l2_code)
    st.session_state["industries_l3"] = industries_l3

    industry_l3_name = st.selectbox("Chọn ngành cấp 3", industries_l3["vietnameseName"].tolist())
    if not industry_l3_name:
        return None

    stocks = industries_l3.loc[
        industries_l3["vietnameseName"] == industry_l3_name, "codeList"
    ].iloc[0]
    return stocks.split(",")


def filter_by_pricing_stock(end_date):
    """Filter stocks based on pricing and safety margin."""
    stocks = filter_stocks_by_industry()
    if not stocks:
        st.warning("No stocks selected.")
        return

    start_date = end_date - timedelta(days=90)
    data = []

    if st.button("Lọc cổ phiếu theo định giá"):
        for stock in stocks:
            df_pricing = get_firm_pricing(stock, start_date.strftime("%Y-%m-%d"))
            if df_pricing is not None and not df_pricing.empty:
                target_price = df_pricing["targetPrice"].astype(float).mean()
                close_price = get_stock_price(
                    stock,
                    (end_date - timedelta(days=3)).strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )
                if not close_price.empty:
                    close_price_value = close_price["close"].iloc[-1]
                    safety_margin = round(
                        (target_price - close_price_value) / target_price * 100, 2
                    )
                    data.append(
                        {
                            "Stock": stock,
                            "Target Price": target_price,
                            "Close Price": close_price_value,
                            "Safety Margin": safety_margin,
                        }
                    )

        if data:
            df_safety = pd.DataFrame(data).sort_values(by="Safety Margin", ascending=False)
            st.dataframe(df_safety)
        else:
            st.warning("No pricing data available.")


def plot_correlation_and_yield(stocks, start_date, end_date):
    """Plot correlation matrix and yield curve for selected stocks."""
    df_stocks = get_port_price(
        stocks, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    )
    returns = df_stocks.pct_change()
    cumulative_returns = (1 + returns).cumprod()

    # Yield curve plot
    fig_yield = go.Figure()
    colors = px.colors.qualitative.Set3
    for i, stock in enumerate(stocks):
        fig_yield.add_trace(
            go.Scatter(
                x=df_stocks.index,
                y=cumulative_returns[stock],
                name=stock,
                mode="lines",
                line=dict(color=colors[i % len(colors)]),
            )
        )

    fig_yield.update_layout(
        title="So sánh lợi suất",
        xaxis_title="Thời gian",
        yaxis_title="Lợi suất tích lũy",
        template="plotly_white",
    )

    # Correlation heatmap
    correlation_matrix = returns.corr().round(2)
    fig_corr = go.Figure(
        data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.columns,
            colorscale="RdYlBu",
            zmid=0,
        )
    )

    fig_corr.update_layout(title="Ma trận tương quan giữa các cổ phiếu", template="plotly_white")

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_corr, use_container_width=True)
    with col2:
        st.plotly_chart(fig_yield, use_container_width=True)


def filter_by_quantitative(end_date):
    """Filter stocks using quantitative analysis."""
    stocks = ["ACB", "BID", "CTG", "MBB", "VPB", "VNINDEX"]
    start_date = end_date - timedelta(days=365 * 5)
    plot_correlation_and_yield(stocks, start_date, end_date)
