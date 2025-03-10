from ast import Or
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

from src.features import plot_cashflow_analysis
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

    page = st.sidebar.radio("Chọn trang", ["Phân tích giao dịch", "Dòng tiền"])

if page == "Dòng tiền":
    st.title("Phân tích dòng tiền cổ phiếu " + stock)

else:
    st.title("Phân tích giao dịch nước ngoài cổ phiếu " + stock)
    col_1, col_2 = st.columns(2)

    if stock:

        with col_1:
            plot_proprietary_trading(
                stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )
        with col_2:
            # plot_firm_pricing(stock, start_date.strftime("%Y-%m-%d"))
            plot_foreign_trading(
                stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )
        plot_close_price_and_ratio(
            stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
        plot_cashflow_analysis(stock, period)
