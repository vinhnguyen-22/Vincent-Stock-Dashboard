from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import seaborn as sb
import streamlit as st
from vnstock import Vnstock

headers = {
    # "X-Request-Id": id,
    "pgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
}


def cf_analysis(stock, period):
    try:
        today = datetime.now()
        start_date = today - timedelta(days=period)
        all_data = []

        for i in range(period + 1):
            date = start_date + timedelta(days=i)
            date = date.strftime("%Y-%m-%d")
            api_url = f"https://api-finfo.vndirect.com.vn/v4/cashflow_analysis/latest?order=time&where=code:{stock}~period:1D&filter=date:{date}"
            res = requests.get(url=api_url, headers=headers)
            res.raise_for_status()
            data = res.json()
            all_data.extend(data["data"])
        df = pd.DataFrame(all_data)
        return df
    except requests.exceptions.RequestException as e:
        print("Yêu cầu không thành công:", e)
        return None


def plot_cashflow_analysis(stock, period):
    # Extract the relevant columns for the bar chart
    buy_columns = ["topActiveBuyPct", "midActiveBuyPct", "botActiveBuyPct"]
    sell_columns = ["topActiveSellPct", "midActiveSellPct", "botActiveSellPct"]
    df = cf_analysis(stock, period)
    # Create a new DataFrame for the bar chart
    df_stacked = df[["date"] + buy_columns + sell_columns]

    # Create the figure
    fig = go.Figure()

    # Define colors for sell orders with gradient effect
    sell_colors = ["red", "coral", "yellow"]
    buy_colors = ["green", "lightgreen", "yellowgreen"]

    # Plot buy orders
    for col, color in zip(buy_columns, buy_colors):
        fig.add_trace(
            go.Bar(x=df_stacked["date"], y=df_stacked[col], name=col, marker_color=color)
        )

    # Plot sell orders
    for col, color in zip(sell_columns, sell_colors):
        fig.add_trace(
            go.Bar(
                x=df_stacked["date"],
                y=df_stacked[col],
                name=col,
                marker_color=color,
            )
        )

    # Update layout
    fig.update_layout(
        barmode="stack",
        title="Thống kê lệnh mua bán chủ động",
        xaxis_title="",
        yaxis_title="",
        legend_title="Order Type",
    )

    st.plotly_chart(fig, use_container_width=True)


def main():
    # ---- REPLACE THIS WITH YOUR OWN CODE ----
    pass


if __name__ == "__main__":
    main()
