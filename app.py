from contextlib import suppress
from datetime import datetime, timedelta
from dis import dis
from math import e, sqrt

import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_tags import st_tags
from vnstock import Vnstock

from src.features import (
    fetch_and_plot_ownership,
    get_fund_data,
    plot_cashflow_analysis,
    plot_pie_fund,
)
from src.filter import (
    filter_by_ownerratio,
    filter_by_pricing_stock,
    filter_by_quantitative,
    filter_components,
)
from src.fund import display_fund_data
from src.market_overview import overview_market
from src.optimize_portfolio import display_portfolio_analysis
from src.plots import (
    get_firm_pricing,
    get_stock_price,
    plot_close_price_and_ratio,
    plot_firm_pricing,
    plot_foreign_trading,
    plot_proprietary_trading,
)
from src.quant_profile import calculate_quant_metrics
from src.stock_health import display_dupont_analysis, display_stock_score
from src.stock_profile import company_profile

load_dotenv()
period = 7

old_request = requests.Session.request


def new_request(self, *args, **kwargs):
    kwargs["verify"] = False
    return old_request(self, *args, **kwargs)


requests.Session.request = new_request


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
        st.image(
            "./logo.png",
            width=200,
        )

        st.header("📃 Chọn trang")
        page = st.radio(
            "",
            [
                "📈 Phân Tích Cổ Phiếu",
                "📃 Phân Tích Cơ Bản Cổ Phiếu",
                "🌍 Tổng Quan Thị Trường",
                "🔍 Bộ Lọc Cổ Phiếu",
                "💰 Phân Tích Dòng Tiền",
                "💲 Đầu Tư Quỹ Mở",
                "🎲 Phân Tích Định Lượng",
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
    st.header("📈 PHÂN TÍCH CỔ PHIẾU " + stock)
    st.subheader("THÔNG TIN CỔ PHIẾU")
    df_pricing = get_firm_pricing(stock, "2024-01-01")
    company_profile(stock, df_price, df_pricing, start_date, end_date)

    company = Vnstock().stock(symbol=stock, source="TCBS").company
    profile = company.profile()
    profile.set_index("company_name", inplace=True)

    profile = profile.drop("symbol", axis=1)
    tabs = st.tabs(profile.columns.tolist())
    for tab, column in zip(tabs, profile.columns):
        with tab:
            st.write(profile[column].iloc[0])

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
    col_1, col_2 = st.columns([2, 1])
    with col_1:
        plot_foreign_trading(stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    with col_2:
        plot_proprietary_trading(
            stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
    st.divider()
    st.subheader("TƯƠNG QUAN GIAO DỊCH NƯỚC NGOÀI VÀ GIÁ CỔ PHIẾU")
    plot_close_price_and_ratio(
        df_price, stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    )
    with st.popover("Hướng dẫn"):
        st.write("Update sau")


def display_overview_market():
    """Display market overview."""
    overview_market()
    st.divider()
    start = st.date_input("Chọn ngày: ", datetime(2025, 1, 1))
    df = get_fund_data(start.strftime("%Y-%m-%d"))
    plot_pie_fund(df)


def display_quant_analysis(stock, end_date):
    """Display market overview."""
    years = st.selectbox("Chọn số năm phân tích: ", [5, 7, 10], index=0)
    quant_metric = calculate_quant_metrics(stock, end_date, years)


def display_filter_stock(end_date):
    """Display market overview."""
    stocks = filter_components()
    tabs = st.tabs(
        [
            "Lọc cổ phiếu theo % NN sở hữu",
            "Lọc cổ phiếu theo định giá",
            "Lọc theo định lượng",
        ]
    )
    with tabs[0]:
        filter_by_ownerratio(stocks, end_date)
    with tabs[1]:
        filter_by_pricing_stock(stocks, end_date)
    with tabs[2]:
        st.write(", ".join(stocks))
        if stocks is not None:
            stocks_tag = st_tags(
                label="Nhập mã chứng khoán ở đây",
                text="Press enter to add more",
                value=stocks,
                suggestions=stocks,
                key="stocks_quant",
            )
            years = st.selectbox("Chọn số năm phân tích: ", [5, 7, 10], index=0)
            risk_profile = st.selectbox(
                "🎯 Khẩu vị đầu tư của bạn là gì?", ["Phòng thủ", "Cân bằng", "Rủi ro"]
            )

            filter_by_quantitative(stocks_tag, end_date, years, risk_profile)


def main():
    """Main function to run the Streamlit app."""
    configure_streamlit()
    stock, start_date, end_date, period, page = get_sidebar_inputs()
    st.title(f"Vincent App - {page}")
    st.divider()
    st.info(
        """
            Thông báo cập nhật 25/04/2025:
            - Cập nhật chức năn theo dõi kế hoạch kinh doanh
            - cập nhật chức năng phân tích mua bán chủ động
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
        elif page == "📈 Phân Tích Cổ Phiếu":
            display_trading_analysis(stock, df_price, df_index, start_date, end_date)
        elif page == "📃 Phân Tích Cơ Bản Cổ Phiếu":
            display_stock_score(stock)
            st.divider()
            display_dupont_analysis(stock)
        elif page == "💲 Đầu Tư Quỹ Mở":
            display_fund_data()
        else:
            display_overview_market()


if __name__ == "__main__":
    main()
