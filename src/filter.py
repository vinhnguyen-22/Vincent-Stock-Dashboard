from datetime import datetime, timedelta
from math import sqrt

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots
from streamlit_tags import st_tags
from vnstock import Vnstock

from src.company_profile import (
    calculate_drawdown_metrics,
    calculate_extended_metrics,
    calculate_quant_metrics,
    calculate_risk_metrics,
    plot_drawdown,
)
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
    """Filter stocks based on foreign ownership ratio and show trend."""

    if st.button("Lọc cổ phiếu có tỷ trọng sở hữu nước ngoài cao nhất"):
        market_cap_min = market_cap * 1e12
        net_bought_val_avg_20d_min = net_bought_val * 1e9

        df = get_stock_data_from_api(market_cap_min, net_bought_val_avg_20d_min)

        if df is None or df.empty:
            st.warning("Không tìm thấy dữ liệu.")
            return None

        start_date = end_date - timedelta(days=30)
        stocks_data = {}

        for symbol in df["code"]:
            foreign = foreigner_trading_stock(
                symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            ).sort_index(ascending=False)
            foreign.ffill(inplace=True)

            if foreign is not None and not foreign.empty:
                try:
                    curr = foreign["currentRoom"].iloc[-1]
                    total = foreign["totalRoom"].iloc[-1]
                    if total > 0:
                        ownership_ratio = round((total - curr) / total * 100, 2)

                        trend_series = (
                            (foreign["totalRoom"] - foreign["currentRoom"])
                            / foreign["totalRoom"]
                            * 100
                        ).fillna(0)
                        trend = [round(val, 2) for val in trend_series.tolist()]

                        stocks_data[symbol] = {"Ownership Ratio": ownership_ratio, "lines": trend}
                except Exception as e:
                    st.error(f"Lỗi xử lý dữ liệu cho mã {symbol}: {e}")

        if not stocks_data:
            st.warning("Không có cổ phiếu nào phù hợp.")
            return None

        df_result = (
            pd.DataFrame.from_dict(stocks_data, orient="index")
            .sort_values(by="Ownership Ratio", ascending=False)
            .reset_index()
            .rename(columns={"index": "Mã cổ phiếu"})
        )

        st.data_editor(
            df_result,
            column_config={
                "lines": st.column_config.LineChartColumn(
                    "Xu hướng sở hữu (%) 30 ngày",
                    width="medium",
                )
            },
            use_container_width=True,
        )

        return df_result


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
    """Filter stocks by industry hierarchy with caching and error handling."""

    def get_cached_industry_data(level, parent_code=0, force_refresh=False):
        """Get industry data with caching in session state."""
        cache_key = f"industries_l{level}"
        if force_refresh or st.session_state.get(cache_key) is None:
            data = get_industry_data(level, parent_code)
            st.session_state[cache_key] = data
        return st.session_state[cache_key]

    def select_industry_level(level, data, label, parent_code=0):
        """Handle industry selection for a specific level."""
        if data is None or data.empty:
            st.error(f"No data available for {label}")
            return None, None

        selected = st.selectbox(label, data["vietnameseName"].tolist())
        if not selected:
            return None, None

        industry_code = data.loc[data["vietnameseName"] == selected, "industryCode"].iloc[0]
        return selected, industry_code

    # Level 1 selection
    industries_l1 = get_cached_industry_data(1)
    name_l1, code_l1 = select_industry_level(1, industries_l1, "Chọn ngành cấp 1")
    if not code_l1:
        return None

    # Level 2 selection
    industries_l2 = get_cached_industry_data(2, code_l1, True)
    name_l2, code_l2 = select_industry_level(2, industries_l2, "Chọn ngành cấp 2", code_l1)
    if not code_l2:
        return None

    # Level 3 selection
    industries_l3 = get_cached_industry_data(3, code_l2, True)
    name_l3, _ = select_industry_level(3, industries_l3, "Chọn ngành cấp 3", code_l2)
    if not name_l3:
        return None

    # Get stock list
    stocks = industries_l3.loc[industries_l3["vietnameseName"] == name_l3, "codeList"].iloc[0]
    return stocks.split(",")


def filter_by_pricing_stock(stocks, end_date):
    """Filter stocks based on pricing and safety margin."""
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


def plot_risk_metrics_radar(metrics_df):
    df_radar = metrics_df.copy().reset_index().rename(columns={"index": "Stock"})
    df_melted = df_radar.melt(id_vars=["Stock"], var_name="Metric", value_name="Value")

    fig = px.line_polar(
        df_melted,
        r="Value",
        theta="Metric",
        color="Stock",
        line_close=True,
        markers=True,
        template="plotly_dark",
    )

    fig.update_layout(
        title="So sánh Risk Metrics giữa các cổ phiếu",
        polar=dict(radialaxis=dict(showticklabels=True, ticks="outside")),
        legend_title_text="Mã cổ phiếu",
        height=600,
    )

    return fig


# === Risk profile weights ===
def get_risk_weights(profile="Moderate"):
    if profile == "Conservative":
        return {
            "Annual Return": 0.1,
            "Sharpe Ratio": 0.15,
            "Sortino Ratio": 0.15,
            "Annual Std": 0.2,
            "VaR (95%)": 0.2,
            "Max Drawdown": 0.1,
            "Calmar Ratio": 0.1,
        }
    elif profile == "Aggressive":
        return {
            "Annual Return": 0.25,
            "Sharpe Ratio": 0.2,
            "Sortino Ratio": 0.2,
            "Annual Std": 0.1,
            "VaR (95%)": 0.1,
            "Max Drawdown": 0.05,
            "Calmar Ratio": 0.1,
        }
    else:
        return {
            "Annual Return": 0.15,
            "Sharpe Ratio": 0.15,
            "Sortino Ratio": 0.1,
            "Annual Std": 0.15,
            "VaR (95%)": 0.15,
            "Max Drawdown": 0.15,
            "Calmar Ratio": 0.15,
        }


# === Extended risk metrics ===
def calculate_extended_metrics(returns):
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


# === Radar chart ===
def plot_risk_metrics_radar(metrics_df):
    df_radar = metrics_df.copy().reset_index().rename(columns={"index": "Stock"})
    df_melted = df_radar.melt(id_vars=["Stock"], var_name="Metric", value_name="Value")
    fig = px.line_polar(
        df_melted,
        r="Value",
        theta="Metric",
        color="Stock",
        line_close=True,
        markers=True,
        template="plotly_dark",
    )
    fig.update_layout(title="So sánh Risk Metrics giữa các cổ phiếu", height=600)
    return fig


# === Main analyzer ===
def run_quant_analyzer(stocks, start_date, end_date, risk_profile="Moderate"):

    weights = get_risk_weights(risk_profile)
    df_stocks = get_port_price(
        stocks, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    )
    df_stocks = df_stocks[~df_stocks.index.duplicated(keep="first")]
    returns = np.log(df_stocks / df_stocks.shift(1)).dropna()

    metrics = {col: calculate_extended_metrics(returns[col]) for col in returns.columns}
    metrics_df = pd.DataFrame(metrics).T.round(4)

    norm_df = (metrics_df - metrics_df.min()) / (metrics_df.max() - metrics_df.min())
    reverse_metrics = ["Annual Std", "Max Drawdown", "VaR (95%)"]
    for col in reverse_metrics:
        if col in norm_df.columns:
            norm_df[col] = 1 - norm_df[col]

    score = sum(norm_df[col] * w for col, w in weights.items() if col in norm_df.columns)
    metrics_df["Score"] = score.round(4)
    metrics_df = metrics_df.sort_values(by="Score", ascending=False)

    st.subheader("📌 Radar Chart: So sánh đa chỉ số")
    st.plotly_chart(
        plot_risk_metrics_radar(metrics_df.drop(columns=["Score"])), use_container_width=True
    )

    rank_df = metrics_df.drop(columns=["Score"]).copy()
    for col in rank_df.columns:
        asc = col in reverse_metrics
        rank_df[col] = rank_df[col].rank(ascending=asc)

    fig_rank = px.imshow(
        rank_df,
        color_continuous_scale="blues",
        text_auto=True,
        labels=dict(x="Chỉ số", y="Mã cổ phiếu", color="Thứ hạng"),
        title="Thứ hạng (1 = tốt nhất)",
    )
    cumulative_returns = (1 + returns).cumprod()
    fig_yield = go.Figure()
    colors = px.colors.qualitative.Set3
    for i, stock in enumerate(stocks):
        fig_yield.add_trace(
            go.Scatter(
                x=cumulative_returns.index,
                y=cumulative_returns[stock],
                name=stock,
                mode="lines",
                line=dict(color=colors[i % len(colors)]),
            )
        )
    fig_yield.update_layout(
        title="📈 So sánh lợi suất tích lũy",
        xaxis_title="Thời gian",
        yaxis_title="Lợi suất",
        template="plotly_white",
    )

    correlation_matrix = returns.corr().round(2)
    fig_corr = go.Figure(
        data=go.Heatmap(
            z=correlation_matrix.values,
            x=correlation_matrix.columns,
            y=correlation_matrix.columns,
            colorscale="RdYlBu",
            zmid=0,
            text=correlation_matrix.values,
            texttemplate="%{text:.2f}",
        )
    )
    fig_corr.update_layout(
        title="🔗 Ma trận tương quan giữa các cổ phiếu", template="plotly_white"
    )

    tab1, tab2, tab3 = st.tabs(["Tương quan", "Lợi suất", "Thứ hạng"])
    with tab1:
        st.plotly_chart(fig_corr, use_container_width=True)
    with tab2:
        st.plotly_chart(fig_yield, use_container_width=True)
    with tab3:
        st.plotly_chart(fig_rank, use_container_width=True)

    best_stock = metrics_df.index[0]
    st.success(
        f"✅ Theo phân tích định lượng với khẩu vị {risk_profile}, nên ưu tiên đầu tư vào: **{best_stock}**"
    )

    return metrics_df


def filter_by_quantitative(stocks, end_date, years):
    """Filter stocks using quantitative analysis."""
    risk_profile = st.selectbox(
        "🎯 Khẩu vị đầu tư của bạn là gì?", ["Conservative", "Moderate", "Aggressive"]
    )
    st.info(
        {
            "Conservative": "Bạn ưu tiên an toàn vốn và ổn định hơn là lợi nhuận cao.",
            "Moderate": "Bạn muốn cân bằng giữa rủi ro và hiệu suất đầu tư.",
            "Aggressive": "Bạn chấp nhận rủi ro cao để tìm kiếm tăng trưởng dài hạn.",
        }[risk_profile]
    )
    if st.button("So sánh các cổ phiếu "):
        start_date = end_date - timedelta(days=365 * years)
        run_quant_analyzer(stocks, start_date, end_date, risk_profile)
