from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pyparsing import col
from regex import D
from streamlit_tags import st_tags
from vnstock import Vnstock

from src.config import PROCESSED_DATA_DIR
from src.tcbs_stock_data import TCBSStockData


def get_port_price(symbols, start_date, end_date):
    result = pd.DataFrame()
    for s in symbols:
        tcbs = TCBSStockData(rate_limit_pause=0)
        df = tcbs.get_stock_data_by_date_range(s, start_date=start_date, end_date=end_date)
        if result.empty:
            result["time"] = df["time"]
        result[s] = df["close"]
    result.set_index("time", inplace=True)
    return result


def get_port(price, N=252):
    port_ret = np.log(price / price.shift(1))
    port_annual_risk = np.sqrt(port_ret.std() * sqrt(N))
    port_annual_ret = ((1 + port_ret.mean()) ** N) - 1
    sharpe_ratio = port_annual_ret / port_annual_risk
    result = pd.DataFrame(
        {
            "% DailyReturn": port_ret.mean() * 100,
            "% DailyRisk": port_ret.std() * 100,
            "% AnnualReturn": port_annual_ret * 100,
            "% AnnualRisk": port_annual_risk * 100,
            "Sharpe Ratio": sharpe_ratio,
        }
    )
    return result


def calculate_optimal_portfolio(
    symbols, price, port, no_of_port=1000, risk_free_rate=0.05, nav=100.00
):
    num_stocks = len(symbols)
    weight = np.zeros((no_of_port, num_stocks))
    expected_ret = np.zeros(no_of_port)
    expected_vol = np.zeros(no_of_port)
    sharpe_ratio = np.zeros(no_of_port)

    port_ret = np.log(price / price.shift(1))

    for i in range(no_of_port):
        weight_random = np.random.random(num_stocks)
        weight_random /= np.sum(weight_random)
        weight[i, :] = weight_random
        expected_ret[i] = np.sum(port["% AnnualReturn"] * weight_random)
        expected_vol[i] = np.sqrt(
            np.dot(weight_random.T, np.dot(port_ret.cov() * 252, weight_random))
        )
        sharpe_ratio[i] = (expected_ret[i] - risk_free_rate) / expected_vol[i]

    max_sharpe_index = sharpe_ratio.argmax()
    max_return_index = expected_ret.argmax()
    min_risk_index = expected_vol.argmin()

    optimal_portfolio = pd.DataFrame(
        {
            "Stock": symbols,
            "Tối Ưu": weight[max_sharpe_index, :].round(decimals=2) * nav,
            "Tấn Công": weight[max_return_index, :].round(decimals=2) * nav,
            "Phòng Thủ": weight[min_risk_index, :].round(decimals=2) * nav,
        }
    )

    optimal_portfolio.set_index("Stock", inplace=True)

    return optimal_portfolio


def plot_optimal_portfolio_chart(optimal_portfolio):
    categories = ["Tối Ưu", "Tấn Công", "Phòng Thủ"]
    optimal_portfolio.reset_index(inplace=True)
    ma_co_phieu = optimal_portfolio["Stock"].tolist()
    data = optimal_portfolio[categories].values.T
    total_values = np.sum(data, axis=1, keepdims=True)
    ratios = (data / total_values) * 100

    fig = go.Figure()

    for idx, ma in enumerate(ma_co_phieu):
        fig.add_trace(
            go.Bar(
                x=categories,
                y=ratios[:, idx],
                name=ma,
                text=[f"{ma} - ({val:.1f}%)" if val > 0 else "" for val in ratios[:, idx]],
                textposition="inside",
            )
        )
    fig.update_layout(
        barmode="stack",
        title="Biểu đồ cột chồng theo danh mục với tỷ trọng từng mã cổ phiếu",
        xaxis_title="Danh mục",
        yaxis_title="Tỷ trọng (%)",
        yaxis=dict(range=[0, 100]),
        legend_title="Stock",
    )
    st.plotly_chart(fig)


def display_portfolio_analysis():
    col1, col2 = st.columns([1, 2])
    with col1:
        stocks = st_tags(
            label="Nhập mã chứng khoán ở đây",
            text="Press enter to add more",
            value=["ACB", "CTG", "FPT", "MBB", "HPG"],
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
        optimal_portfolio = calculate_optimal_portfolio(stocks, price, port, nav=nav)
        st.dataframe(optimal_portfolio, use_container_width=True)
        plot_optimal_portfolio_chart(optimal_portfolio)

    with col2:
        df_portfolio = pd.DataFrame(
            {
                "Danh mục": ["Tối Ưu", "Tấn Công", "Phòng Thủ"],
                "Mô tả": [
                    "Danh mục tối ưu hóa lợi nhuận và rủi ro",
                    "Danh mục tập trung vào lợi nhuận cao",
                    "Danh mục tập trung vào rủi ro thấp",
                ],
            }
        )
        st.dataframe(df_portfolio.set_index("Danh mục"), use_container_width=True)


def main():
    pass


if __name__ == "__main__":
    main()
