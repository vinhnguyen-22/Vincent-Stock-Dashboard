from ast import Or
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

from src.plots import (
    get_firm_pricing,
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


with st.sidebar:
    stock = st.text_input("Nhập mã cổ phiếu", "HPG")
    start_date = st.date_input("Chọn ngày bắt đầu", datetime(2025, 1, 1))
    end_option = st.checkbox("Nhập ngày kết thúc")
    if end_option == False:
        time_range = st.selectbox("Chọn khoảng thời gian", ["Tuần", "Tháng", "Năm"], index=1)
        end_date = datetime.today()
        if time_range == "Tuần":
            start_date = end_date - timedelta(weeks=1)
        elif time_range == "Tháng":
            start_date = end_date - timedelta(days=30)
        elif time_range == "Năm":
            start_date = end_date - timedelta(days=365)
    else:
        end_date = st.date_input("Chọn ngày kết thúc", start_date + pd.Timedelta(days=30))

st.title("Phân tích giao dịch nước ngoài cổ phiếu " + stock)

col_1, col_2 = st.columns(2)

if stock:
    plot_foreign_trading(stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    with col_1:
        plot_proprietary_trading(
            stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
    with col_1:
        st.dataframe(get_firm_pricing(stock, start_date.strftime("%Y-%m-%d")))
    with col_2:
        plot_firm_pricing(stock, start_date.strftime("%Y-%m-%d"))

if st.button("Refresh"):
    st.caching.clear_cache()
    st.experimental_rerun()
