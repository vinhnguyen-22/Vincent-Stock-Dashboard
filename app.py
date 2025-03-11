from ast import Or
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st
from streamlit_tags import st_tags

from src.features import plot_cashflow_analysis
from src.optimize_portfolio import (
    calculate_optimal_portfolio,
    get_port,
    get_port_price,
    plot_optimal_portfolio_chart,
)
from src.plots import (
    get_firm_pricing,
    plot_close_price_and_ratio,
    plot_firm_pricing,
    plot_foreign_trading,
    plot_proprietary_trading,
)

# Giao diện Streamlit
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


period = 0
with st.sidebar:
    stock = st.text_input("Nhập mã cổ phiếu", "HPG")
    start_date = st.date_input("Chọn ngày bắt đầu", datetime(2025, 1, 1))
    end_option = st.checkbox("Nhập ngày kết thúc")
    if end_option == False:
        time_range = st.selectbox("Chọn khoảng thời gian", ["Tuần", "Tháng", "Năm"], index=1)
        end_date = datetime.today()
        if time_range == "Tuần":
            period = 7
            start_date = end_date - timedelta(weeks=1)
        elif time_range == "Tháng":
            period = 30
            start_date = end_date - timedelta(days=30)
        elif time_range == "Năm":
            period = 365
            start_date = end_date - timedelta(days=365)
    else:
        end_date = st.date_input("Chọn ngày kết thúc", start_date + pd.Timedelta(days=30))

    st.header("📃 Chọn trang")
    page = st.sidebar.radio("", ["Phân tích giao dịch", "Dòng tiền", "Danh mục cổ phiếu"])

if page == "Dòng tiền":
    st.title("Phân tích dòng tiền cổ phiếu " + stock)
    plot_cashflow_analysis(stock, period)
elif page == "Danh mục cổ phiếu":
    st.title("Danh mục cổ phiếu")

    stocks = st_tags(
        label="Nhập mã chứng khoán ở đây",
        text="Press enter to add more",
        value=[],
        suggestions=["ACB", "FPT", "MBB", "HPG"],
        maxtags=5,
        key="aljnf",
    )
    if stocks and st.button("Tính toán"):
        price = get_port_price(stocks, "2015-01-01", "2025-01-01")
        port = get_port(price=price)
        st.dataframe(port)
    if st.button("Tối Ưu"):
        price = get_port_price(stocks, "2015-01-01", "2025-01-01")
        port = get_port(price=price)
        optimal_portfolio = calculate_optimal_portfolio(stocks, price, port)
        st.dataframe(optimal_portfolio)

        # Call the function to plot the chart
        plot_optimal_portfolio_chart(optimal_portfolio)

else:
    # col_1, col_2 = st.columns(2)
    st.title("Phân tích giao dịch nước ngoài cổ phiếu " + stock)
    if stock:

        # with col_1:
        #     plot_proprietary_trading(
        #         stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        #     )
        # with col_2:
        plot_firm_pricing(stock, "2024-01-01")
        plot_foreign_trading(stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        plot_close_price_and_ratio(
            stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
