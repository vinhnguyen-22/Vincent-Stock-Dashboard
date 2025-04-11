from contextlib import suppress
from datetime import datetime, timedelta
from math import sqrt

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_tags import st_tags
from vnstock import Vnstock

from src.company_profile import calculate_quant_metrics, calculate_stock_metrics
from src.features import (
    fetch_and_plot_ownership,
    fetch_cashflow_data,
    fetch_cashflow_market,
    get_fund_data,
    plot_cashflow_analysis,
    plot_pie_fund,
)
from src.filter import (
    filter_by_ownerratio,
    filter_by_pricing_stock,
    filter_by_quantitative,
    filter_components,
    filter_stocks_by_industry,
)
from src.optimize_portfolio import display_portfolio_analysis
from src.plots import (
    get_firm_pricing,
    get_stock_price,
    plot_close_price_and_ratio,
    plot_firm_pricing,
    plot_foreign_trading,
    plot_proprietary_trading,
)

load_dotenv()
period = 7


def configure_streamlit():
    """Configure Streamlit app settings."""
    st.set_page_config(
        page_title="Vincent App",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://www.extremelycoolapp.com/help",
            "Report a bug": "https://www.extremelycoolapp.com/bug",
            "About": "# This is a header. This is an *extremely* cool app!",
        },
    )


def get_sidebar_inputs():
    """Get user inputs from the sidebar."""
    with st.sidebar:
        st.header("📃 Chọn trang")
        page = st.radio(
            "",
            [
                "📈 Phân Tích Cổ Phiếu",
                "🎲 Phân Tích Định Lượng",
                "🌍 Tổng Quan Thị Trường",
                "🔍 Bộ Lọc Cổ Phiếu",
                "💰 Phân Tích Dòng Tiền",
                "🗂 Phân Bổ Danh Mục",
                "🧐 Danh Mục Tham Khảo",
            ],
        )
        stock = st.text_input("Nhập mã cổ phiếu", "FPT")

        start_date = st.date_input("Chọn ngày bắt đầu", datetime(2025, 1, 1))
        end_option = st.checkbox("Nhập ngày kết thúc")

        if page != "Tổng Quan Thị Trường" and not end_option:
            time_range = st.selectbox(
                "Chọn khoảng thời gian", ["Tuần", "Tháng", "Qúy", "Năm"], index=1
            )
            end_date = datetime.today()
            if time_range == "Tuần":
                period = 7
                start_date = end_date - timedelta(weeks=1)
            elif time_range == "Tháng":
                period = 30
                start_date = end_date - timedelta(days=30)
            elif time_range == "Qúy":
                period = 90
                start_date = end_date - timedelta(days=90)
            elif time_range == "Năm":
                period = 365
                start_date = end_date - timedelta(days=365)
        else:
            end_date = st.date_input("Chọn ngày kết thúc", start_date + timedelta(days=30))
            period = (end_date - start_date).days

        # Initialize session state for industries and selections

        return stock, start_date, end_date, period, page


def display_cashflow_analysis(stock, df_price, period):
    plot_cashflow_analysis(df_price, stock, period)


def display_trading_analysis(stock, df_price, df_index, start_date, end_date):
    """Display trading analysis for the selected stock."""
    df_pricing = get_firm_pricing(stock, "2024-01-01")

    col_1, col_2 = st.columns(2)
    with col_1:
        st.subheader("ĐỊNH GIÁ CỔ PHIẾU")
        calculate_stock_metrics(df_price, df_index, df_pricing)
    with col_2:
        st.subheader("THÔNG TIN CỔ PHIẾU")
        company = Vnstock().stock(symbol=stock, source="TCBS").company
        profile = company.profile()
        profile.set_index("company_name", inplace=True)
        st.dataframe(
            profile.T,
            use_container_width=True,
        )

    st.divider()
    col_1, col_2 = st.columns(2)
    with col_1:
        st.subheader("CƠ CẤU CỔ ĐÔNG")
        fetch_and_plot_ownership(stock)
    with col_2:
        st.subheader("ĐỊNH GIÁ TỪ CÁC CTCK")
        plot_firm_pricing(df_pricing)

    st.divider()
    st.subheader("GIAO DỊCH CỦA TỔ CHỨC VÀ NƯỚC NGOÀI")
    col_1, col_2 = st.columns(2)
    with col_1:
        plot_proprietary_trading(
            stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
    with col_2:
        plot_foreign_trading(stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    st.divider()
    st.subheader("TƯƠNG QUAN GIAO DỊCH NƯỚC NGOÀI VÀ GIÁ CỔ PHIẾU")
    plot_close_price_and_ratio(
        df_price, stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    )
    with st.popover("Hướng dẫn"):
        st.write("Update sau")


def display_overview_market():
    """Display market overview."""
    start = st.date_input("Chọn ngày: ", datetime(2025, 1, 1))
    df = get_fund_data(start.strftime("%Y-%m-%d"))
    plot_pie_fund(df)
    exchange = st.selectbox(
        "Chọn sàn giao dịch",
        options=[
            "HOSE",
            "HNX",
            "UPCOM",
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
        Vnstock().stock("ACB", source="VCI").listing.symbols_by_group(exchange).tolist()
    )
    layer = st.selectbox("Chọn tầng nhà đầu tư để hiển thị:", options=["Top", "Mid", "Bot"])
    layer_key_map = {"Top": "netTopVal", "Mid": "netMidVal", "Bot": "netBotVal"}
    layer_key = layer_key_map[layer]
    all_data = pd.DataFrame()
    for ticker in stock_by_exchange:
        df_cf = fetch_cashflow_market(ticker, layer_key)
        if not df_cf.empty:
            all_data = pd.concat([all_data, df_cf], ignore_index=True)

    if all_data.empty:
        st.warning("Không có dữ liệu hợp lệ cho các mã đã nhập.")
    else:
        # --- Vẽ biểu đồ ---
        fig = go.Figure()
        for ticker in stock_by_exchange:
            df_plot = all_data[all_data["ticker"] == ticker]
            fig.add_trace(
                go.Scatter(
                    x=df_plot["ticker"], y=df_plot["netVal"], mode="lines+markers", name=ticker
                )
            )

        fig.update_layout(
            title=f"So sánh dòng tiền {layer} nhà đầu tư theo thời gian",
            xaxis_title="Thời gian",
            yaxis_title="Giá trị mua ròng (triệu VND)",
            legend_title="Mã cổ phiếu",
            height=600,
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Bảng dữ liệu ---
        with st.expander("📋 Xem dữ liệu chi tiết"):
            st.dataframe(all_data)


def display_quant_analysis(stock, end_date):
    """Display market overview."""
    years = st.selectbox("Chọn số năm phân tích: ", [5, 7, 10], index=0)
    quant_metric = calculate_quant_metrics(stock, end_date, years)


def display_filter_stock(end_date):
    """Display market overview."""
    stocks = filter_components()
    filter_by_ownerratio(stocks, end_date)

    filter_by_pricing_stock(stocks, end_date)
    stocks = st_tags(
        label="Nhập mã chứng khoán ở đây",
        text="Press enter to add more",
        value=["ACB", "FPT", "HPG"],
        suggestions=["ACB", "FPT", "MBB", "HPG"],
        maxtags=5,
        key="stocks_quant",
    )
    years = st.selectbox("Chọn số năm phân tích: ", [5, 7, 10], index=0)
    filter_by_quantitative(stocks, end_date, years)


def main():
    """Main function to run the Streamlit app."""
    configure_streamlit()
    stock, start_date, end_date, period, page = get_sidebar_inputs()
    st.title(f"Vincent App - {page}")
    st.divider()
    st.info(
        """
            Thông báo cập nhật 05/04/2025:
            - Cập nhật chức năng bộ loc cổ phiếu.
            - Cập nhật biểu đồ phân tích định lượng.
            - Chức năng tổng quan thị trường đang trong quá trình phát triển.
            """
    )

    if stock:
        df_price = get_stock_price(
            stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
        df_index = get_stock_price(
            "VNINDEX", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
        if page == "💰 Phân Tích Dòng Tiền":
            display_cashflow_analysis(stock, df_price, period)
        elif page == "🌍 Tổng Quan Thị Trường":
            display_overview_market()
        elif page == "🎲 Phân Tích Định Lượng":
            display_quant_analysis(stock, end_date)
        elif page == "🗂 Phân Bổ Danh Mục":
            display_portfolio_analysis()
        elif page == "🔍 Bộ Lọc Cổ Phiếu":
            display_filter_stock(end_date)
        else:
            display_trading_analysis(stock, df_price, df_index, start_date, end_date)


if __name__ == "__main__":
    main()
