from ast import Or
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

from src.plots import plot_foreign_trading

# Giao diện Streamlit
st.title("Phân tích giao dịch nước ngoài")

stock = st.text_input("Nhập mã cổ phiếu", "VCB")
start_date = st.date_input("Chọn ngày bắt đầu", datetime(2025, 1, 1))
end_option = st.checkbox("Nhập ngày kết thúc")


if end_option == False:
    time_range = st.radio("Chọn khoảng thời gian", ["Tuần", "Tháng", "Năm"], index=1)
    end_date = datetime.today()
    if time_range == "Tuần":
        start_date = end_date - timedelta(weeks=1)
    elif time_range == "Tháng":
        start_date = end_date - timedelta(days=30)
    elif time_range == "Năm":
        start_date = end_date - timedelta(days=365)
else:
    end_date = st.date_input("Chọn ngày kết thúc", start_date + pd.Timedelta(days=30))


if st.button("Hiển thị biểu đồ") or stock:
    plot_foreign_trading(stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
