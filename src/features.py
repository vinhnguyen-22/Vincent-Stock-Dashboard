from datetime import datetime, timedelta
from multiprocessing import Pool, cpu_count

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots
from vnstock import Vnstock

from src.llm_model import analysis_with_ai

HEADERS = {
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
}

API_URL_CASHFLOW = "https://api-finfo.vndirect.com.vn/v4/cashflow_analysis/latest"
API_URL_FUND = "https://api-finfo.vndirect.com.vn/v4/fund_ratios"
API_URL_OWNERSHIP = "https://api2.simplize.vn/api/company/ownership/ownership-breakdown"


@st.cache_data(ttl=3600)
def get_company_plan(stock, year):
    """Lấy thông tin chi tiết của quỹ từ API"""
    try:
        url = f"https://api-finfo.vndirect.com.vn/v4/company_forecast?q=code:{stock}~fiscalYear:gte:{year}&sort=fiscalYear"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data["data"])
        else:
            st.error(f"Lỗi khi lấy thông tin cổ phiếu {stock}: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"Không thể kết nối đến API: {str(e)}")
        return {}


def fetch_single_date(params):
    date, stock = params
    api_url = f"{API_URL_CASHFLOW}?order=time&where=code:{stock}~period:1D&filter=date:{date}"
    try:
        res = requests.get(url=api_url, headers=HEADERS)
        res.raise_for_status()
        data = res.json()
        return data["data"]
    except requests.exceptions.RequestException as e:
        print(f"Request failed for date {date}:", e)
        return []


def fetch_cashflow_data(stock, period=30):
    today = datetime.now()
    start_date = today - timedelta(days=period)
    dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(period + 1)]
    params = [(date, stock) for date in dates]

    with Pool(cpu_count()) as pool:
        results = pool.map(fetch_single_date, params)

    all_data = []
    for result in results:
        all_data.extend(result)

    return pd.DataFrame(all_data) if all_data else None


def plot_price_chart(df):
    try:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["time"], y=df["close"], mode="lines", name="Close Price"))
        fig.update_layout(
            title="Stock Price Chart",
            xaxis_title="Time",
            yaxis_title="Close Price",
            template="plotly_white",
        )
        st.plotly_chart(fig)
    except Exception as e:
        st.write("No data available:", e)


def calculate_relative_values(row):
    total = (
        row["topActiveBuyVal"]
        + row["midActiveBuyVal"]
        + row["botActiveBuyVal"]
        + row["topActiveSellVal"]
        + row["midActiveSellVal"]
        + row["botActiveSellVal"]
    )

    return pd.Series(
        {
            "Shark buy": row["topActiveBuyVal"] if total else 0,
            "Wolf buy": row["midActiveBuyVal"] if total else 0,
            "Sheep buy": row["botActiveBuyVal"] if total else 0,
            "Shark sell": row["topActiveSellVal"] if total else 0,
            "Wolf sell": row["midActiveSellVal"] if total else 0,
            "Sheep sell": row["botActiveSellVal"] if total else 0,
        }
    )


def process_chunk(chunk):
    return chunk.apply(calculate_relative_values, axis=1)


# === Các hàm phân tích bổ sung ===


def plot_volume_price_analysis(df_stacked):
    """Phân tích mối tương quan giữa khối lượng và giá"""
    fig = make_subplots(
        rows=3,
        cols=1,
        subplot_titles=("Giá cổ phiếu", "Tổng khối lượng giao dịch", "Tỷ lệ BUY/SELL"),
        vertical_spacing=0.08,
        specs=[[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": False}]],
    )

    # Price chart
    fig.add_trace(
        go.Scatter(
            x=df_stacked["date"],
            y=df_stacked["close"],
            name="Giá đóng cửa",
            line=dict(color="blue"),
        ),
        row=1,
        col=1,
    )

    # Volume chart
    df_stacked["total_volume"] = df_stacked["BUY"] + abs(df_stacked["SELL"])
    fig.add_trace(
        go.Bar(
            x=df_stacked["date"],
            y=df_stacked["total_volume"],
            name="Tổng khối lượng",
            marker_color="orange",
        ),
        row=2,
        col=1,
    )

    # Buy/Sell ratio
    df_stacked["buy_sell_ratio"] = df_stacked["BUY"] / (abs(df_stacked["SELL"]) + 0.001)
    fig.add_trace(
        go.Scatter(
            x=df_stacked["date"],
            y=df_stacked["buy_sell_ratio"],
            name="Tỷ lệ BUY/SELL",
            line=dict(color="green"),
        ),
        row=3,
        col=1,
    )

    fig.update_layout(height=800, title_text="Phân tích Khối lượng - Giá")
    return fig


def plot_investor_sentiment_heatmap(df_stacked):
    """Tạo heatmap thể hiện tâm lý nhà đầu tư"""
    # Chuẩn bị dữ liệu
    sentiment_data = df_stacked[
        ["date", "Shark buy", "Wolf buy", "Sheep buy", "Shark sell", "Wolf sell", "Sheep sell"]
    ].copy()

    # Tính net buying cho từng nhóm
    sentiment_data["Shark Net"] = sentiment_data["Shark buy"] - abs(sentiment_data["Shark sell"])
    sentiment_data["Wolf Net"] = sentiment_data["Wolf buy"] - abs(sentiment_data["Wolf sell"])
    sentiment_data["Sheep Net"] = sentiment_data["Sheep buy"] - abs(sentiment_data["Sheep sell"])

    # Tạo ma trận cho heatmap
    heatmap_data = sentiment_data[["Shark Net", "Wolf Net", "Sheep Net"]].T

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values,
            x=[d.strftime("%m-%d") for d in sentiment_data["date"]],
            y=["Shark", "Wolf", "Sheep"],
            colorscale="RdYlGn",
            zmid=0,
            text=np.round(heatmap_data.values, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
        )
    )

    fig.update_layout(
        title="Heatmap Tâm lý Nhà đầu tư (Net Buying)",
        xaxis_title="Ngày",
        yaxis_title="Nhóm nhà đầu tư",
        height=400,
    )
    return fig


def plot_candlestick_with_volume(df_stacked):
    """Biểu đồ nến kết hợp với khối lượng giao dịch"""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Biểu đồ nến", "Phân tích khối lượng theo nhóm"),
        row_width=[0.2, 0.7],
    )

    # Tạo dữ liệu OHLC giả lập (vì chỉ có close price)
    df_stacked["open"] = df_stacked["close"].shift(1).fillna(df_stacked["close"])
    df_stacked["high"] = df_stacked[["open", "close"]].max(axis=1) * 1.002
    df_stacked["low"] = df_stacked[["open", "close"]].min(axis=1) * 0.998

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df_stacked["date"],
            open=df_stacked["open"],
            high=df_stacked["high"],
            low=df_stacked["low"],
            close=df_stacked["close"],
            name="OHLC",
        ),
        row=1,
        col=1,
    )

    # Volume by investor type
    fig.add_trace(
        go.Bar(
            x=df_stacked["date"],
            y=df_stacked["Shark buy"],
            name="Shark Buy",
            marker_color="darkgreen",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=df_stacked["date"],
            y=df_stacked["Wolf buy"],
            name="Wolf Buy",
            marker_color="lightgreen",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=df_stacked["date"],
            y=-abs(df_stacked["Shark sell"]),
            name="Shark Sell",
            marker_color="darkred",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=df_stacked["date"],
            y=-abs(df_stacked["Wolf sell"]),
            name="Wolf Sell",
            marker_color="lightcoral",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(height=700, title_text="Biểu đồ nến kết hợp Khối lượng")
    fig.update_xaxes(rangeslider_visible=False)

    return fig


def plot_correlation_analysis(df_stacked):
    """Phân tích tương quan giữa các yếu tố"""
    # Tính toán các chỉ số bổ sung
    df_analysis = df_stacked.copy()
    df_analysis["price_change"] = df_analysis["close"].pct_change()
    df_analysis["shark_dominance"] = (
        df_analysis["Shark buy"] + abs(df_analysis["Shark sell"])
    ) / (df_analysis["BUY"] + abs(df_analysis["SELL"]))
    df_analysis["market_sentiment"] = df_analysis["BUY"] - abs(df_analysis["SELL"])

    # Ma trận tương quan
    corr_cols = ["close", "BUY", "SELL", "price_change", "shark_dominance", "market_sentiment"]
    corr_matrix = df_analysis[corr_cols].corr()

    fig = go.Figure(
        data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_cols,
            y=corr_cols,
            colorscale="RdBu",
            zmid=0,
            text=np.round(corr_matrix.values, 2),
            texttemplate="%{text}",
            textfont={"size": 12},
        )
    )

    fig.update_layout(title="Ma trận Tương quan các Yếu tố", height=500, width=500)
    return fig


def plot_moving_averages_analysis(df_stacked):
    """Phân tích đường trung bình động"""
    df_ma = df_stacked.copy()

    # Tính các đường MA
    df_ma["MA_5"] = df_ma["close"].rolling(window=5).mean()
    df_ma["MA_10"] = df_ma["close"].rolling(window=10).mean()
    df_ma["MA_20"] = df_ma["close"].rolling(window=20).mean()

    # Tính MA cho BUY/SELL
    df_ma["BUY_MA_5"] = df_ma["BUY"].rolling(window=5).mean()
    df_ma["SELL_MA_5"] = df_ma["SELL"].rolling(window=5).mean()

    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=("Giá và Đường trung bình động", "Xu hướng BUY/SELL MA"),
        vertical_spacing=0.1,
    )

    # Price and MA
    fig.add_trace(
        go.Scatter(
            x=df_ma["date"], y=df_ma["close"], name="Giá", line=dict(color="cyan", width=2)
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=df_ma["date"], y=df_ma["MA_5"], name="MA5", line=dict(color="red", width=1)),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_ma["date"], y=df_ma["MA_10"], name="MA10", line=dict(color="blue", width=1)
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_ma["date"], y=df_ma["MA_20"], name="MA20", line=dict(color="green", width=1)
        ),
        row=1,
        col=1,
    )

    # BUY/SELL MA
    fig.add_trace(
        go.Scatter(
            x=df_ma["date"], y=df_ma["BUY_MA_5"], name="BUY MA5", line=dict(color="darkgreen")
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_ma["date"], y=df_ma["SELL_MA_5"], name="SELL MA5", line=dict(color="darkred")
        ),
        row=2,
        col=1,
    )

    fig.update_layout(height=600, title_text="Phân tích Đường trung bình động")
    return fig


def plot_advanced_indicators(df_stacked):
    """Các chỉ báo kỹ thuật nâng cao"""
    df_indicators = df_stacked.copy()

    # RSI tự tạo đơn giản
    delta = df_indicators["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df_indicators["RSI"] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    df_indicators["BB_middle"] = df_indicators["close"].rolling(window=20).mean()
    bb_std = df_indicators["close"].rolling(window=20).std()
    df_indicators["BB_upper"] = df_indicators["BB_middle"] + (bb_std * 2)
    df_indicators["BB_lower"] = df_indicators["BB_middle"] - (bb_std * 2)

    # Money Flow Index (MFI) simplified
    df_indicators["typical_price"] = df_indicators["close"]
    df_indicators["money_flow"] = df_indicators["typical_price"] * df_indicators["BUY"]
    df_indicators["MFI"] = df_indicators["money_flow"].rolling(window=14).mean()

    fig = make_subplots(
        rows=4,
        cols=1,
        subplot_titles=("Giá và Bollinger Bands", "RSI", "Money Flow Index", "Volume Oscillator"),
        vertical_spacing=0.08,
    )

    # Bollinger Bands
    fig.add_trace(
        go.Scatter(
            x=df_indicators["date"], y=df_indicators["close"], name="Giá", line=dict(color="cyan")
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_indicators["date"],
            y=df_indicators["BB_upper"],
            name="BB Upper",
            line=dict(color="red", dash="dash"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_indicators["date"],
            y=df_indicators["BB_lower"],
            name="BB Lower",
            line=dict(color="red", dash="dash"),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_indicators["date"],
            y=df_indicators["BB_middle"],
            name="BB Middle",
            line=dict(color="blue"),
        ),
        row=1,
        col=1,
    )

    # RSI
    fig.add_trace(
        go.Scatter(
            x=df_indicators["date"], y=df_indicators["RSI"], name="RSI", line=dict(color="purple")
        ),
        row=2,
        col=1,
    )
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # MFI
    fig.add_trace(
        go.Scatter(
            x=df_indicators["date"], y=df_indicators["MFI"], name="MFI", line=dict(color="orange")
        ),
        row=3,
        col=1,
    )

    # Volume Oscillator
    df_indicators["volume_osc"] = df_indicators["BUY"] - abs(df_indicators["SELL"])
    fig.add_trace(
        go.Bar(
            x=df_indicators["date"],
            y=df_indicators["volume_osc"],
            name="Volume Oscillator",
            marker_color="teal",
        ),
        row=4,
        col=1,
    )

    fig.update_layout(height=1000, title_text="Các Chỉ báo Kỹ thuật Nâng cao")
    return fig


# === Hàm xử lý chart với nhiều tab ===
def plot_cashflow_analysis(df_price, stock, period):
    st.subheader("📊 Phân Tích Tỷ Lệ Mua Bán Chủ Động")

    # --- Load data ---
    df = fetch_cashflow_data(stock, period)
    if df is None or df.empty:
        st.warning("No data available")
        return

    # Chia nhỏ để xử lý song song
    chunks = np.array_split(df, cpu_count())
    with Pool(cpu_count()) as pool:
        results = pool.map(process_chunk, chunks)

    df_relative = pd.concat(results).reset_index(drop=True)

    # Ghép lại với cột date
    df_relative["date"] = pd.to_datetime(df["date"])
    df_price["time"] = pd.to_datetime(df_price["time"])
    df_stacked = df_relative.merge(
        df_price[["time", "close"]], left_on="date", right_on="time", how="left"
    )

    # Gom nhóm BUY / SELL
    df_stacked["BUY"] = df_stacked[["Shark buy", "Wolf buy", "Sheep buy"]].sum(axis=1)
    df_stacked["SELL"] = df_stacked[["Shark sell", "Wolf sell", "Sheep sell"]].sum(axis=1)

    # --- Tabs mở rộng ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
        [
            "Tổng quan BUY vs SELL",
            "Chi tiết Shark/Wolf/Sheep",
            "Khối lượng - Giá",
            "Heatmap Tâm lý",
            "Biểu đồ Nến",
            "Ma trận Tương quan",
            "Đường MA",
            "Chỉ báo Kỹ thuật",
        ]
    )

    # --- Chart 1: BUY vs SELL ---
    with tab1:
        fig1 = go.Figure()
        fig1.add_trace(
            go.Bar(x=df_stacked["date"], y=df_stacked["BUY"], name="BUY", marker_color="green")
        )
        fig1.add_trace(
            go.Bar(x=df_stacked["date"], y=df_stacked["SELL"], name="SELL", marker_color="red")
        )

        fig1.add_trace(
            go.Scatter(
                x=df_stacked["date"],
                y=df_stacked["close"],
                name="Close Price",
                yaxis="y2",
                line=dict(color="blue"),
            )
        )

        fig1.update_layout(
            barmode="relative",
            title="Tỷ trọng BUY vs SELL",
            yaxis=dict(title="Tỷ lệ giao dịch (%)", tickformat=".0%"),
            yaxis2=dict(title="Close Price", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
            height=500,
        )

        st.plotly_chart(fig1, use_container_width=True)

    # --- Chart 2: Shark/Wolf/Sheep ---
    with tab2:
        fig2 = go.Figure()
        colors_buy = ["darkgreen", "limegreen", "yellowgreen"]
        colors_sell = ["darkred", "orangered", "gold"]

        for col, color in zip(["Shark buy", "Wolf buy", "Sheep buy"], colors_buy):
            fig2.add_trace(
                go.Bar(x=df_stacked["date"], y=df_stacked[col], name=col, marker_color=color)
            )

        for col, color in zip(["Shark sell", "Wolf sell", "Sheep sell"], colors_sell):
            fig2.add_trace(
                go.Bar(x=df_stacked["date"], y=df_stacked[col], name=col, marker_color=color)
            )

        fig2.add_trace(
            go.Scatter(
                x=df_stacked["date"],
                y=df_stacked["close"],
                name="Close Price",
                yaxis="y2",
                line=dict(color="blue"),
            )
        )

        fig2.update_layout(
            barmode="relative",
            title="Chi tiết Shark/Wolf/Sheep",
            yaxis=dict(title="Tỷ lệ giao dịch (%)", tickformat=".0%"),
            yaxis2=dict(title="Close Price", overlaying="y", side="right"),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
            height=500,
        )
        st.plotly_chart(fig2, use_container_width=True)

        # Bảng thống kê nhanh
        top_shark = df_stacked.nlargest(5, "Shark buy")[["date", "Shark buy", "close"]]
        top_sheep = df_stacked.nlargest(5, "Sheep sell")[["date", "Sheep sell", "close"]]

        st.write("🐋 **Top ngày Shark mua ròng mạnh nhất**")
        st.dataframe(top_shark)

        st.write("🐑 **Top ngày Sheep bán tháo mạnh nhất**")
        st.dataframe(top_sheep)

    # --- Tab 3: Volume-Price Analysis ---
    with tab3:
        fig3 = plot_volume_price_analysis(df_stacked)
        st.plotly_chart(fig3, use_container_width=True)

        # Thống kê tương quan
        correlation = df_stacked[["close", "BUY", "SELL"]].corr()
        st.write("**Ma trận tương quan đơn giản:**")
        st.dataframe(correlation)

    # --- Tab 4: Sentiment Heatmap ---
    with tab4:
        fig4 = plot_investor_sentiment_heatmap(df_stacked)
        st.plotly_chart(fig4, use_container_width=True)

        # Thông tin bổ sung
        st.write("**Giải thích màu sắc:**")
        st.write("🟩 Xanh lá: Net buying (Tích cực)")
        st.write("🟥 Đỏ: Net selling (Tiêu cực)")
        st.write("🟡 Vàng: Trung tính")

    # --- Tab 5: Candlestick with Volume ---
    with tab5:
        fig5 = plot_candlestick_with_volume(df_stacked)
        st.plotly_chart(fig5, use_container_width=True)

    # --- Tab 6: Correlation Analysis ---
    with tab6:
        col1, col2 = st.columns(2)
        with col1:
            fig6 = plot_correlation_analysis(df_stacked)
            st.plotly_chart(fig6, use_container_width=True)

        with col2:
            # Scatter plot quan trọng
            fig_scatter = px.scatter(
                df_stacked, x="BUY", y="close", title="Mối quan hệ BUY vs Giá", trendline="ols"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    # --- Tab 7: Moving Averages ---
    with tab7:
        fig7 = plot_moving_averages_analysis(df_stacked)
        st.plotly_chart(fig7, use_container_width=True)

    # --- Tab 8: Advanced Technical Indicators ---
    with tab8:
        fig8 = plot_advanced_indicators(df_stacked)
        st.plotly_chart(fig8, use_container_width=True)

    # --- Highlight sự kiện rule-based ---
    events = []
    for idx, row in df_stacked.iterrows():
        if row["Shark buy"] > 0.6:
            events.append((row["date"], "Shark mua ròng > 60%"))
        if row["Sheep sell"] > 0.4:
            events.append((row["date"], "Sheep bán tháo > 40%"))

    # --- Phân tích AI ---
    st.subheader("🤖 Phân tích AI")
    prompt = f"""
    Dưới đây là dữ liệu giao dịch của {stock} trong {period} ngày qua.
    Sự kiện rule-based phát hiện: {', '.join([t for _, t in events])}.
    
    Hãy phân tích:
    1. Xu hướng tổng thể của cổ phiếu
    2. Mối liên hệ giữa hành vi Shark/Wolf/Sheep và biến động giá
    3. Các tín hiệu mua/bán tiềm năng
    4. Đánh giá rủi ro và cơ hội
    
    Dữ liệu bao gồm: giá đóng cửa, tỷ lệ mua/bán của các nhóm nhà đầu tư.
    """

    try:
        res = analysis_with_ai(df_stacked, prompt)
        st.success(res)
    except Exception as e:
        st.error(f"Lỗi khi phân tích AI: {str(e)}")
        st.info("Có thể phân tích thủ công dựa trên các biểu đồ trên.")


def get_fund_data(start_date):
    api_url = (
        f"{API_URL_FUND}?q=reportDate:gte:{start_date}~ratioCode:IFC_HOLDING_COUNT_CR&size=1000"
    )
    try:
        res = requests.get(url=api_url, headers=HEADERS)
        res.raise_for_status()
        data = res.json()
        df = pd.DataFrame(data["data"])
        df.rename(columns={"reportDate": "time"}, inplace=True)
        df["time"] = pd.to_datetime(df["time"])
        return df
    except requests.exceptions.RequestException as e:
        print("Yêu cầu không thành công:", e)
        return None


def fetch_cashflow_market(ticker, date=None):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    try:
        url = (
            f"https://api-finfo.vndirect.com.vn/v4/cashflow_analysis/latest?"
            f"order=time&where=code:{ticker}~period:1D&filter=date:{date}"
        )
        res = requests.get(url, headers=HEADERS, verify=False, timeout=10)
        res.raise_for_status()
        data = res.json()

        if "data" not in data or not isinstance(data["data"], list):
            print(f"[{ticker}] API trả về không đúng format (không có 'data').")
            return pd.DataFrame()

        df = pd.DataFrame(data["data"])
        if df.empty:
            print(f"[{ticker}] Không có dữ liệu cashflow ngày {date}.")
            return pd.DataFrame()

        if "date" in df.columns and "time" in df.columns:
            df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"])
        else:
            print(f"[{ticker}] DataFrame thiếu cột 'date' hoặc 'time'.")
            return pd.DataFrame()
        return df

    except Exception as e:
        print(f"Lỗi khi fetch_cashflow_market({ticker}, {date}): {e}")
        return pd.DataFrame()


def plot_pie_fund(df):
    st.subheader("Biểu đồ phân bổ quỹ")

    col1, col2 = st.columns(2)

    with col1:
        years = sorted(df["time"].dt.year.unique(), reverse=True)
        selected_year = st.selectbox("Chọn năm", years, index=0)
        filtered_df = df[df["time"].dt.year == selected_year]

    with col2:
        months = sorted(df["time"].dt.month.unique(), reverse=True)
        selected_month = st.selectbox("Chọn tháng", months, index=0)
        filtered_df = filtered_df[filtered_df["time"].dt.month == selected_month]

    df_top10 = filtered_df.nlargest(10, "value").sort_values(by="value", ascending=False)
    fig = go.Figure(
        data=[
            go.Pie(
                labels=df_top10["code"],
                values=df_top10["value"],
                hole=0.5,
                textinfo="label+value",
            )
        ]
    )
    fig.update_layout(title="TOP 10 Cổ PHIẾU CÁC QUỸ ĐẦU TƯ ĐANG NẮM GIỮ", showlegend=False)
    st.plotly_chart(fig)


def fetch_and_plot_ownership(symbol):
    url = f"{API_URL_OWNERSHIP}/{symbol}"
    response = requests.get(url)

    if response.status_code != 200:
        st.error("Không lấy được dữ liệu từ API.")
        return

    data = response.json().get("data", [])
    if not data:
        st.error("Dữ liệu không hợp lệ hoặc không có dữ liệu.")
        return

    records = [
        {
            "Investor Type": child["investorType"],
            "Parent": parent["investorType"],
            "Percentage": child["pctOfSharesOutHeldTier"],
        }
        for parent in data
        for child in parent.get("children", [])
    ]

    df = pd.DataFrame(records)
    fig = px.sunburst(
        df,
        path=["Parent", "Investor Type"],
        values="Percentage",
        color="Parent",
        color_discrete_sequence=px.colors.qualitative.Set1,
    )

    fig.update_traces(textinfo="label+percent entry", insidetextorientation="radial")
    fig.update_layout(legend_title_text="Investor Types")

    st.plotly_chart(fig)


# === Thêm các hàm phân tích bổ sung ===


def plot_market_breadth_analysis(df_stacked):
    """Phân tích độ rộng thị trường và momentum"""
    df_breadth = df_stacked.copy()

    # Tính toán các chỉ số breadth
    df_breadth["price_momentum"] = df_breadth["close"].pct_change(periods=5)
    df_breadth["volume_momentum"] = (df_breadth["BUY"] + abs(df_breadth["SELL"])).pct_change(
        periods=3
    )
    df_breadth["shark_momentum"] = df_breadth["Shark buy"].pct_change(periods=3)

    # Advance/Decline ratio
    df_breadth["advance_decline"] = np.where(
        df_breadth["close"] > df_breadth["close"].shift(1), 1, -1
    )
    df_breadth["ad_cumulative"] = df_breadth["advance_decline"].cumsum()

    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=(
            "Price Momentum (5 ngày)",
            "Volume Momentum (3 ngày)",
            "Shark Momentum",
            "Advance/Decline Cumulative",
            "Momentum Comparison",
            "Market Strength Index",
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    # Price momentum
    fig.add_trace(
        go.Scatter(
            x=df_breadth["date"],
            y=df_breadth["price_momentum"],
            name="Price Momentum",
            line=dict(color="blue"),
        ),
        row=1,
        col=1,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)

    # Volume momentum
    fig.add_trace(
        go.Scatter(
            x=df_breadth["date"],
            y=df_breadth["volume_momentum"],
            name="Volume Momentum",
            line=dict(color="orange"),
        ),
        row=1,
        col=2,
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=2)

    # Shark momentum
    fig.add_trace(
        go.Bar(
            x=df_breadth["date"],
            y=df_breadth["shark_momentum"],
            name="Shark Momentum",
            marker_color="green",
        ),
        row=2,
        col=1,
    )

    # A/D Cumulative
    fig.add_trace(
        go.Scatter(
            x=df_breadth["date"],
            y=df_breadth["ad_cumulative"],
            name="A/D Cumulative",
            line=dict(color="purple"),
        ),
        row=2,
        col=2,
    )

    # Momentum comparison
    fig.add_trace(
        go.Scatter(
            x=df_breadth["date"],
            y=df_breadth["price_momentum"],
            name="Price",
            line=dict(color="blue"),
        ),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_breadth["date"],
            y=df_breadth["volume_momentum"],
            name="Volume",
            line=dict(color="orange"),
        ),
        row=3,
        col=1,
    )

    # Market strength index (custom)
    df_breadth["market_strength"] = (
        df_breadth["price_momentum"].fillna(0) * 0.4
        + df_breadth["volume_momentum"].fillna(0) * 0.3
        + df_breadth["shark_momentum"].fillna(0) * 0.3
    )

    fig.add_trace(
        go.Bar(
            x=df_breadth["date"],
            y=df_breadth["market_strength"],
            name="Market Strength",
            marker_color=np.where(df_breadth["market_strength"] > 0, "green", "red"),
        ),
        row=3,
        col=2,
    )

    fig.update_layout(height=800, title_text="Phân tích Độ rộng Thị trường và Momentum")
    return fig


def plot_risk_analysis(df_stacked):
    """Phân tích rủi ro và volatility"""
    df_risk = df_stacked.copy()

    # Tính toán các chỉ số rủi ro
    df_risk["daily_return"] = df_risk["close"].pct_change()
    df_risk["volatility_10d"] = df_risk["daily_return"].rolling(window=10).std() * np.sqrt(252)
    df_risk["volatility_20d"] = df_risk["daily_return"].rolling(window=20).std() * np.sqrt(252)

    # VaR (Value at Risk) 95% và 99%
    df_risk["var_95"] = df_risk["daily_return"].rolling(window=20).quantile(0.05)
    df_risk["var_99"] = df_risk["daily_return"].rolling(window=20).quantile(0.01)

    # Drawdown
    df_risk["peak"] = df_risk["close"].cummax()
    df_risk["drawdown"] = (df_risk["close"] - df_risk["peak"]) / df_risk["peak"]

    # Risk-adjusted returns (Sharpe ratio approximation)
    risk_free_rate = 0.05 / 252  # 5% annual risk-free rate
    df_risk["excess_return"] = df_risk["daily_return"] - risk_free_rate
    df_risk["sharpe_10d"] = (
        df_risk["excess_return"].rolling(window=10).mean()
        / df_risk["daily_return"].rolling(window=10).std()
    )

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Volatility Analysis",
            "Value at Risk (VaR)",
            "Drawdown Analysis",
            "Risk-Adjusted Returns",
        ),
        vertical_spacing=0.15,
    )

    # Volatility
    fig.add_trace(
        go.Scatter(
            x=df_risk["date"], y=df_risk["volatility_10d"], name="Vol 10D", line=dict(color="red")
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_risk["date"],
            y=df_risk["volatility_20d"],
            name="Vol 20D",
            line=dict(color="orange"),
        ),
        row=1,
        col=1,
    )

    # VaR
    fig.add_trace(
        go.Scatter(
            x=df_risk["date"], y=df_risk["var_95"], name="VaR 95%", line=dict(color="blue")
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=df_risk["date"], y=df_risk["var_99"], name="VaR 99%", line=dict(color="darkblue")
        ),
        row=1,
        col=2,
    )

    # Drawdown
    fig.add_trace(
        go.Scatter(
            x=df_risk["date"],
            y=df_risk["drawdown"],
            fill="tonexty",
            name="Drawdown",
            line=dict(color="red"),
            fillcolor="rgba(255,0,0,0.3)",
        ),
        row=2,
        col=1,
    )

    # Sharpe ratio
    fig.add_trace(
        go.Scatter(
            x=df_risk["date"], y=df_risk["sharpe_10d"], name="Sharpe 10D", line=dict(color="green")
        ),
        row=2,
        col=2,
    )
    fig.add_hline(y=1, line_dash="dash", line_color="gray", row=2, col=2)
    fig.add_hline(y=2, line_dash="dash", line_color="green", row=2, col=2)

    fig.update_layout(height=600, title_text="Phân tích Rủi ro và Volatility")
    return fig


def plot_liquidity_analysis(df_stacked):
    """Phân tích thanh khoản thị trường"""
    df_liquidity = df_stacked.copy()

    # Tính toán các chỉ số thanh khoản
    df_liquidity["total_value"] = df_liquidity["BUY"] + abs(df_liquidity["SELL"])
    df_liquidity["liquidity_ratio"] = df_liquidity["total_value"] / df_liquidity["close"]
    df_liquidity["bid_ask_spread"] = (
        abs(df_liquidity["BUY"] - abs(df_liquidity["SELL"])) / df_liquidity["total_value"]
    )

    # Amihud illiquidity measure (simplified)
    df_liquidity["price_impact"] = (
        abs(df_liquidity["close"].pct_change()) / df_liquidity["total_value"]
    )
    df_liquidity["amihud_illiquidity"] = df_liquidity["price_impact"].rolling(window=5).mean()

    # Market efficiency measure
    df_liquidity["price_reversal"] = df_liquidity["close"].pct_change() * df_liquidity[
        "close"
    ].pct_change().shift(1)

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Thanh khoản vs Giá",
            "Bid-Ask Spread",
            "Amihud Illiquidity Measure",
            "Price Reversal Pattern",
        ),
        vertical_spacing=0.15,
    )

    # Liquidity vs Price
    fig.add_trace(
        go.Scatter(
            x=df_liquidity["date"],
            y=df_liquidity["liquidity_ratio"],
            name="Liquidity Ratio",
            line=dict(color="blue"),
        ),
        row=1,
        col=1,
    )

    # Bid-Ask Spread
    fig.add_trace(
        go.Scatter(
            x=df_liquidity["date"],
            y=df_liquidity["bid_ask_spread"],
            name="Spread",
            line=dict(color="red"),
        ),
        row=1,
        col=2,
    )

    # Amihud Illiquidity
    fig.add_trace(
        go.Scatter(
            x=df_liquidity["date"],
            y=df_liquidity["amihud_illiquidity"],
            name="Illiquidity",
            line=dict(color="orange"),
        ),
        row=2,
        col=1,
    )

    # Price Reversal
    fig.add_trace(
        go.Bar(
            x=df_liquidity["date"],
            y=df_liquidity["price_reversal"],
            name="Price Reversal",
            marker_color=np.where(df_liquidity["price_reversal"] > 0, "red", "green"),
        ),
        row=2,
        col=2,
    )

    fig.update_layout(height=600, title_text="Phân tích Thanh khoản Thị trường")
    return fig


def plot_smart_money_flow(df_stacked):
    """Phân tích dòng tiền thông minh"""
    df_smart = df_stacked.copy()

    # Smart Money Index (SMI)
    df_smart["smart_money"] = df_smart["Shark buy"] - abs(df_smart["Shark sell"])
    df_smart["dumb_money"] = df_smart["Sheep buy"] - abs(df_smart["Sheep sell"])
    df_smart["smart_money_index"] = df_smart["smart_money"].cumsum()
    df_smart["dumb_money_index"] = df_smart["dumb_money"].cumsum()

    # Money Flow Pressure
    df_smart["buying_pressure"] = (df_smart["Shark buy"] + df_smart["Wolf buy"]) / df_smart["BUY"]
    df_smart["selling_pressure"] = (df_smart["Shark sell"] + df_smart["Wolf sell"]) / abs(
        df_smart["SELL"]
    )

    # Smart Money Divergence
    df_smart["price_ma"] = df_smart["close"].rolling(window=10).mean()
    df_smart["smart_money_ma"] = df_smart["smart_money"].rolling(window=10).mean()

    # Tính toán divergence
    price_trend = np.where(df_smart["close"] > df_smart["price_ma"], 1, -1)
    smart_trend = np.where(df_smart["smart_money"] > df_smart["smart_money_ma"], 1, -1)
    df_smart["divergence"] = price_trend - smart_trend

    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=(
            "Smart Money vs Dumb Money Index",
            "Buying vs Selling Pressure",
            "Smart Money Divergence",
            "Cumulative Money Flow",
            "Daily Smart Money Flow",
            "Money Flow Histogram",
        ),
        vertical_spacing=0.1,
        horizontal_spacing=0.08,
    )

    # SMI vs DMI
    fig.add_trace(
        go.Scatter(
            x=df_smart["date"],
            y=df_smart["smart_money_index"],
            name="Smart Money Index",
            line=dict(color="green", width=2),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df_smart["date"],
            y=df_smart["dumb_money_index"],
            name="Dumb Money Index",
            line=dict(color="red", width=2),
        ),
        row=1,
        col=1,
    )

    # Pressure
    fig.add_trace(
        go.Bar(
            x=df_smart["date"],
            y=df_smart["buying_pressure"],
            name="Buying Pressure",
            marker_color="green",
            opacity=0.7,
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Bar(
            x=df_smart["date"],
            y=df_smart["selling_pressure"],
            name="Selling Pressure",
            marker_color="red",
            opacity=0.7,
        ),
        row=1,
        col=2,
    )

    # Divergence
    colors = ["red" if x != 0 else "gray" for x in df_smart["divergence"]]
    fig.add_trace(
        go.Bar(
            x=df_smart["date"], y=df_smart["divergence"], name="Divergence", marker_color=colors
        ),
        row=2,
        col=1,
    )

    # Cumulative flow
    fig.add_trace(
        go.Scatter(
            x=df_smart["date"],
            y=df_smart["smart_money_index"],
            name="Smart Money",
            line=dict(color="blue"),
        ),
        row=2,
        col=2,
    )
    fig.add_trace(
        go.Scatter(
            x=df_smart["date"],
            y=df_smart["close"],
            name="Price",
            yaxis="y2",
            line=dict(color="cyan"),
        ),
        row=2,
        col=2,
    )

    # Daily flow
    fig.add_trace(
        go.Bar(
            x=df_smart["date"],
            y=df_smart["smart_money"],
            name="Daily Smart Money",
            marker_color=np.where(df_smart["smart_money"] > 0, "green", "red"),
        ),
        row=3,
        col=1,
    )

    # Histogram
    fig.add_trace(
        go.Histogram(
            x=df_smart["smart_money"],
            name="Distribution",
            nbinsx=20,
            marker_color="blue",
            opacity=0.7,
        ),
        row=3,
        col=2,
    )

    fig.update_layout(height=900, title_text="Phân tích Dòng tiền Thông minh")
    return fig
