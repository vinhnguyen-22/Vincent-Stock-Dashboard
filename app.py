from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from streamlit_tags import st_tags
from vnstock import Vnstock

from src.features import (
    fetch_and_plot_ownership,
    get_fund_data,
    plot_cashflow_analysis,
    plot_pie_fund,
    plot_price_chart,
)
from src.llm_model import analysis_with_ai
from src.optimize_portfolio import (
    calculate_optimal_portfolio,
    get_port,
    get_port_price,
    plot_optimal_portfolio_chart,
)
from src.plots import (
    get_stock_price,
    plot_close_price_and_ratio,
    plot_firm_pricing,
    plot_foreign_trading,
    plot_proprietary_trading,
)

load_dotenv()


def display_info_stock():
    pass


def configure_streamlit():
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
    with st.sidebar:
        st.header("📃 Chọn trang")
        page = st.radio(
            "",
            [
                "Phân Tích Giao Dịch",
                "Tổng Quan Thị Trường",
                "Phân Tích Dòng Tiền",
                "Phân Bổ Danh Mục",
            ],
        )
        stock = st.text_input("Nhập mã cổ phiếu", "FPT")
        start_date = st.date_input("Chọn ngày bắt đầu", datetime(2025, 1, 1))
        end_option = st.checkbox("Nhập ngày kết thúc")
        if page != "Tổng Quan Thị Trường" and not end_option:
            time_range = st.selectbox("Chọn khoảng thời gian", ["Tuần", "Tháng","Qúy", "Năm"], index=1)
            end_date = datetime.today()
            if time_range == "Tuần":
                start_date = end_date - timedelta(weeks=1)
            elif time_range == "Tháng":
                start_date = end_date - timedelta(days=30)
            elif time_range == "Qúy":
                start_date = end_date - timedelta(days=90)
            elif time_range == "Năm":
                start_date = end_date - timedelta(days=365)
        else:
            end_date = st.date_input("Chọn ngày kết thúc", start_date + timedelta(days=30))

    return stock, start_date, end_date, page


def display_cashflow_analysis(stock, df_price, start_date, end_date):
    st.title(f"Phân tích dòng tiền cổ phiếu {stock}")
    plot_cashflow_analysis(df_price, stock, (end_date - start_date).days)


def display_portfolio_analysis():
    st.title("Phân Bổ Tỷ Trọng Danh Mục Đầu Tư")
    df_portfolio = pd.DataFrame({
        "Danh mục": ["Tối Ưu", "Tấn Công", "Phòng Thủ"],
        "Mô tả": [
            "Danh mục tối ưu hóa lợi nhuận và rủi ro",
            "Danh mục tập trung vào lợi nhuận cao",
            "Danh mục tập trung vào rủi ro thấp"
        ]
    })
    
    st.dataframe(df_portfolio.set_index("Danh mục"), use_container_width=True)
    stocks = st_tags(
                label="Nhập mã chứng khoán ở đây",
                text="Press enter to add more",
                value=[],
                suggestions=["ACB", "FPT", "MBB", "HPG"],
                maxtags=5,
                key="aljnf",
            )
    nav = st.text_input("Nhập NAV", value=100000000.00, max_chars=20)
    try:
        nav = float(nav)
        st.write("{:,.2f}".format(nav))
    except ValueError:
        st.error("Vui lòng nhập một số hợp lệ cho NAV")
    
    if stocks and st.button("Kết Quả"):
        price = get_port_price(stocks, "2015-01-01", "2025-01-01")
        port = get_port(price=price)
        st.dataframe(port, use_container_width=True)
        optimal_portfolio = calculate_optimal_portfolio(stocks, price, port,nav=nav)
        st.dataframe(optimal_portfolio, use_container_width=True)
        plot_optimal_portfolio_chart(optimal_portfolio)


def display_trading_analysis(stock, df_price, start_date, end_date):
    st.title(f"PHÂN TÍCH GIAO DỊCH CỔ PHIẾU {stock}")
    st.subheader("THÔNG TIN CỔ PHIẾU")

    company = Vnstock().stock(symbol=stock, source="TCBS").company
    st.dataframe(company.profile().T, use_container_width=True, height=300)

    col_1, col_2 = st.columns(2)
    with col_1:
        st.subheader("Cơ Cấu Cổ Đông")
        fetch_and_plot_ownership(stock)
    with col_2:
        st.subheader("ĐỊNH GIÁ TỪ CÁC CÔNG TY CHỨNG KHOÁN")
        plot_firm_pricing(stock, "2024-01-01")

    st.subheader("GIAO DỊCH CỦA TỔ CHỨC VÀ NƯỚC NGOÀI")
    col_1, col_2 = st.columns(2)
    with col_1:
        plot_proprietary_trading(
            stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
    with col_2:
        plot_foreign_trading(stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    st.subheader("TƯƠNG QUAN GIAO DỊCH NƯỚC NGOÀI VÀ GIÁ CỔ PHIẾU")
    plot_close_price_and_ratio(
        df_price, stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    )


def main():
    configure_streamlit()
    stock, start_date, end_date, page = get_sidebar_inputs()

    if stock:
        df_price = get_stock_price(
            stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
     
        if page == "Phân Tích Dòng Tiền":
            display_cashflow_analysis(stock, df_price, start_date, end_date)
        elif page == "Tổng Quan Thị Trường":
            df = get_fund_data(start_date.strftime("%Y-%m-%d"))
            plot_pie_fund(df)
            pass
        elif page == "Phân Bổ Danh Mục":
            
            display_portfolio_analysis()
        else:
            display_trading_analysis(stock, df_price, start_date, end_date)
            # st.subheader("Nhận định từ DeepSeek")


if __name__ == "__main__":
    main()
