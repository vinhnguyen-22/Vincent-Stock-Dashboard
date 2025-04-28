from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

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
        print(url)
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


def fetch_cashflow_data(stock, period=30):
    today = datetime.now()
    start_date = today - timedelta(days=period)
    all_data = []

    for i in range(period + 1):
        date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        api_url = f"{API_URL_CASHFLOW}?order=time&where=code:{stock}~period:1D&filter=date:{date}"
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


def plot_cashflow_analysis(df_price, stock, period):
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
    df_stacked["date"] = pd.to_datetime(df_stacked["date"])

    df_stacked = df_stacked.merge(
        df_price[["time", "close"]], left_on="date", right_on="time", how="left"
    )
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

    fig.add_trace(
        go.Scatter(
            x=df_stacked["date"],
            y=df_stacked["close"],
            name="Close Price",
            yaxis="y2",
            line=dict(color="blue"),
        )
    )
    fig.update_layout(
        barmode="stack",
        title="Phân Tích Mua Bán Chủ Động",
        xaxis_title="",
        yaxis_title="",
        legend_title="Order Type",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        yaxis2=dict(title="Close Price", overlaying="y", side="right"),
    )

    st.plotly_chart(fig, use_container_width=True)
    res = analysis_with_ai(
        df_stacked,
        f"Dưới đây là dữ liệu giá và giao dịch chủ động của cổ phiếu {stock} hãy phân tích dữ liệu này",
    )
    st.write(res)


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


@st.cache_data(ttl=600)
def fetch_cashflow_market(ticker, date=datetime.now().strftime("%Y-%m-%d")):
    url = f"https://api-finfo.vndirect.com.vn/v4/cashflow_analysis/latest?order=time&where=code:{ticker}~period:1D&filter=date:{date}"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    data = res.json()
    df = pd.DataFrame(data["data"])
    if df.empty:
        return df
    df["datetime"] = pd.to_datetime(df["date"] + " " + df["time"])
    return df


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
