from datetime import datetime, timedelta
from math import sqrt
from tabnanny import check

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots
from streamlit_tags import st_tags
from vnstock import Vnstock

from src.optimize_portfolio import get_port, get_port_price
from src.plots import foreigner_trading_stock, get_firm_pricing, get_stock_price
from src.quant_profile import calculate_extended_metrics

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


def filter_components():
    """Filter stocks based on user input."""
    st.subheader("🔍 Lọc cổ phiếu theo tiêu chí")

    stock_sets = []  # Mỗi tiêu chí lọc tạo ra một tập hợp mã cổ phiếu

    # Lọc theo sàn giao dịch
    exchange = st.selectbox(
        "Chọn sàn giao dịch",
        options=[
            # "HOSE",
            # "HNX",
            # "UPCOM",
            "VN30",
            "VN100",
            "HNX30",
            "VNMidCap",
            "VNSmallCap",
            "VNAllShare",
            "HNXCon",
            "HNXFin",
            "HNXLCap",
            "HNXMSCap",
            "HNXMan",
        ],
        index=0,
    )
    stock_by_exchange = (
        Vnstock().stock("ACB", source="TCBS").listing.symbols_by_group(exchange).tolist()
    )

    stock_sets.append(set(stock_by_exchange))
    # Lọc theo ngành nghề
    if st.checkbox("Ngành nghề", value=True):
        stock_by_industry = filter_stocks_by_industry()
        if stock_by_industry:
            stock_sets.append(set(stock_by_industry))
    # Lọc theo vốn hóa và GTNN
    if st.checkbox("Lọc cổ phiếu theo vốn hóa và GTNN mua ròng", value=True):
        st.info(
            "Chọn các tiêu chí để lọc cổ phiếu. Các cổ phiếu sẽ được lọc dựa trên vốn hóa thị trường và GTNN mua ròng 20 ngày."
        )

        market_cap = st.slider(
            "Vốn Hóa Thị Trường (nghìn tỷ): ", min_value=1, max_value=500, value=1, step=10
        )
        net_bought_val = st.slider(
            "GTNN mua ròng 20 ngày (tỷ): ", min_value=1, max_value=200, value=5
        )

        market_cap_min = market_cap * 1e12
        net_bought_val_avg_20d_min = net_bought_val * 1e9

        stock_by_filter = get_stock_data_from_api(market_cap_min, net_bought_val_avg_20d_min)

        if stock_by_filter is not None and not stock_by_filter.empty:
            stock_sets.append(set(stock_by_filter["code"].tolist()))

    # Kết hợp kết quả lọc
    if stock_sets:
        filtered_stocks = set.intersection(*stock_sets)  # lấy giao của tất cả tập con
    else:
        filtered_stocks = set()
    return list(filtered_stocks)


def filter_by_ownerratio(stocks, end_date):
    """Filter stocks based on foreign ownership ratio and show trend."""

    start_date = end_date - timedelta(days=30)
    stocks_data = {}

    for symbol in stocks:
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


def filter_stocks_by_industry():
    # Lấy dữ liệu ngành từ API
    stock = Vnstock().stock("ACB", source="TCBS")
    df = stock.listing.symbols_by_industries()

    # UI chọn ngành cấp 1
    nganh1 = st.selectbox("Chọn ngành cấp 1", sorted(df["icb_name2"].unique()))
    df_nganh1 = df[df["icb_name2"] == nganh1]

    # Hiện danh sách cổ phiếu ngay khi chỉ chọn ngành cấp 1
    filtered = df_nganh1

    # UI chọn ngành cấp 2 (tuỳ chọn)
    nganh2 = st.selectbox(
        "Chọn ngành cấp 2 (tùy chọn)",
        options=["(Tất cả)"] + sorted(df_nganh1["icb_name3"].unique()),
    )

    if nganh2 != "(Tất cả)":
        df_nganh2 = df_nganh1[df_nganh1["icb_name3"] == nganh2]
        filtered = df_nganh2

        # UI chọn ngành cấp 3 (tuỳ chọn)
        nganh3 = st.selectbox(
            "Chọn ngành cấp 3 (tùy chọn)",
            options=["(Tất cả)"] + sorted(df_nganh2["icb_name4"].unique()),
        )

        if nganh3 != "(Tất cả)":
            filtered = df_nganh2[df_nganh2["icb_name4"] == nganh3]

    return filtered["symbol"].tolist()


def filter_by_pricing_stock(stocks, end_date):
    """Filter stocks based on pricing and safety margin."""
    start_date = end_date - timedelta(days=90)
    data = []

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
                safety_margin = (target_price - close_price_value) / target_price * 100
                data.append(
                    {
                        "Stock": stock,
                        "Target Price": f"{target_price * 1000:,.0f}",
                        "Close Price": f"{close_price_value * 1000:,.0f}",
                        "Safety Margin": round(safety_margin, 2),
                    }
                )
    if data:
        df_safety = pd.DataFrame(data).sort_values(by="Safety Margin", ascending=False)
        st.dataframe(
            df_safety.style.background_gradient(
                subset=["Safety Margin"],
                cmap="RdYlGn",
                vmin=-50,
                vmax=50,
            ),
            use_container_width=True,
        )
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
def get_risk_weights(profile="Cân bằng"):
    if profile == "Phòng thủ":
        return {
            "Annual Return": 0.1,
            "Sharpe Ratio": 0.15,
            "Sortino Ratio": 0.15,
            "Annual Std": 0.2,
            "VaR (95%)": 0.2,
            "Max Drawdown": 0.1,
            "Calmar Ratio": 0.1,
        }
    elif profile == "Cân bằng":
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
    )
    fig.update_layout(title="So sánh Risk Metrics giữa các cổ phiếu", height=600)
    return fig


# === Main analyzer ===
def run_quant_analyzer(stocks, start_date, end_date, risk_profile="Cân bằng"):

    weights = get_risk_weights(risk_profile)
    df_stocks = get_port_price(
        stocks, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), interval="W"
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
        st.dataframe(
            rank_df.style.background_gradient(
                cmap="Blues_r", vmin=1, vmax=len(rank_df), axis=None
            ),
            use_container_width=True,
            height=400,
        )

    best_stock = metrics_df.index[0]
    st.success(
        f"✅ Theo phân tích định lượng với khẩu vị {risk_profile}, nên ưu tiên đầu tư vào: **{best_stock}**"
    )

    return metrics_df


def filter_by_quantitative(stocks, end_date, years, risk_profile):
    """Filter stocks using quantitative analysis."""
    if st.button("So sánh các cổ phiếu "):
        start_date = end_date - timedelta(days=365 * years)
        run_quant_analyzer(stocks, start_date, end_date, risk_profile)
