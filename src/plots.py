from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st
from tqdm import tqdm

from src.config import FIGURES_DIR, PROCESSED_DATA_DIR

headers = {
    "pgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
}


def foreigner_trading_stock(stock, start, end):
    api_url = f"https://api-finfo.vndirect.com.vn/v4/foreigns?sort=tradingDate&q=code:{stock}~tradingDate:gte:{start}~tradingDate:lte:{end}&size=365"
    try:
        response = requests.get(url=api_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data["data"])
        df.rename(columns={"tradingDate": "time"}, inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        print("Yêu cầu không thành công:", e)
        return None


def plot_foreign_trading(stock, start_date, end_date):
    """
    Hàm để vẽ biểu đồ phân tích dữ liệu giao dịch.
    :param data: Dictionary chứa dữ liệu giao dịch
    """
    df = pd.DataFrame(foreigner_trading_stock(stock, start=start_date, end=end_date))
    df["time"] = pd.to_datetime(df["time"])

    # Vẽ biểu đồ miền cho BuyVal và SellVal, kết hợp biểu đồ đường cho currentRoom / totalRoom
    fig, ax1 = plt.subplots(figsize=(12, 6))
    fig.subplots_adjust(bottom=0.2)

    # Biểu đồ miền
    ax1.fill_between(df["time"], df["buyVal"], label="Buy Value", color="green", alpha=0.6)
    ax1.fill_between(df["time"], -df["sellVal"], label="Sell Value", color="red", alpha=0.6)
    ax1.set_xlabel("")
    ax1.set_ylabel("")
    ax1.set_title(
        "Thống kê giao dịch và sở hữu nước ngoài với cổ phiếu " + stock,
        fontdict={"fontweight": "bold"},
    )
    # ax1.legend(loc="upper left")
    ax1.tick_params(axis="x", rotation=45)

    # Trục y thứ hai cho biểu đồ đường
    ax2 = ax1.twinx()
    ratio = -df["currentRoom"] / df["totalRoom"]
    ax2.plot(df["time"], ratio, label="Sở hữu nước ngoài", color="blue")
    ax2.set_ylabel("foreigner ownership")
    fig.legend(loc="lower center", ncol=3)
    plt.grid()
    st.pyplot(fig)


def main(
    input_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    output_path: Path = FIGURES_DIR / "plot.png",
):
    pass


if __name__ == "__main__":
    main()
