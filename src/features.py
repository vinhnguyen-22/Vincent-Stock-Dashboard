from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

HEADERS = {
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
}


def fetch_cashflow_data(stock, period):
    today = datetime.now()
    start_date = today - timedelta(days=period)
    all_data = []

    for i in range(period + 1):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        api_url = f"https://api-finfo.vndirect.com.vn/v4/cashflow_analysis/latest?order=time&where=code:{stock}~period:1D&filter=date:{date}"
        try:
            res = requests.get(url=api_url, headers=HEADERS)
            res.raise_for_status()
            data = res.json()
            all_data.extend(data["data"])
        except requests.exceptions.RequestException as e:
            print("Request failed:", e)
            return None

    return pd.DataFrame(all_data)


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


def plot_cashflow_analysis(stock, period):
    st.write(
        """
        | Loại Nhà Đầu Tư   | Đặc Điểm Chính | Chủ Thể |
        |------------------|-----------------|------|
        | **Shark** | Nhà đầu tư lớn, có khả năng thao túng thị trường, đầu tư dài hạn hoặc tạo sóng giá. | Quỹ đầu tư lớn, ngân hàng đầu tư, tỷ phú tài chính. |
        | **Wolf** | Nhà đầu tư có kinh nghiệm, linh hoạt, giao dịch dựa trên phân tích kỹ thuật và tin tức. | Trader chuyên nghiệp, quỹ đầu cơ nhỏ. |
        | **Sheep** | Nhà đầu tư nhỏ lẻ, dễ bị ảnh hưởng bởi tâm lý đám đông, ít chiến lược. | Nhà đầu tư F0, người mới tham gia thị trường. |
        """
    )
    df = fetch_cashflow_data(stock, period)
    if df is None:
        st.write("No data available")
        return

    df.rename(
        columns={
            "topActiveBuyVal": "Shark buy",
            "midActiveBuyVal": "Wolf buy",
            "botActiveBuyVal": "Sheep buy",
            "topActiveSellVal": "Shark sell",
            "midActiveSellVal": "Wolf sell",
            "botActiveSellVal": "Sheep sell",
        },
        inplace=True,
    )

    buy_columns = ["Shark buy", "Wolf buy", "Sheep buy"]
    sell_columns = ["Shark sell", "Wolf sell", "Sheep sell"]
    df_stacked = df[["date"] + buy_columns + sell_columns]

    fig = go.Figure()

    buy_colors = ["green", "lightgreen", "yellowgreen"]
    sell_colors = ["red", "coral", "yellow"]

    for col, color in zip(buy_columns, buy_colors):
        fig.add_trace(
            go.Bar(x=df_stacked["date"], y=df_stacked[col], name=col, marker_color=color)
        )

    for col, color in zip(sell_columns, sell_colors):
        fig.add_trace(
            go.Bar(x=df_stacked["date"], y=df_stacked[col], name=col, marker_color=color)
        )

    fig.update_layout(
        barmode="stack",
        title="Phân Tích Mua Bán Chủ Động",
        xaxis_title="",
        yaxis_title="",
        legend_title="Order Type",
    )

    st.plotly_chart(fig, use_container_width=True)


def main():
    stock = "VIC"
    period = 30
    plot_cashflow_analysis(stock, period)


if __name__ == "__main__":
    main()
