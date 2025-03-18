from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from vnstock import Vnstock

from src.config import PROCESSED_DATA_DIR


def get_port_price(symbols, start_date, end_date):

    result = pd.DataFrame()

    for s in symbols:
        stock = Vnstock().stock(symbol=s, source="TCBS")
        df = stock.quote.history(start=start_date, end=end_date, interval="1D")
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
            "DailyReturn": port_ret.mean(),
            "DailyRisk": port_ret.std(),
            "AnnualReturn": port_annual_ret,
            "AnnualRisk": port_annual_risk,
            "Sharpe Ratio": sharpe_ratio,
        }
    )
    return result


def calculate_optimal_portfolio(symbols, price, port, no_of_port=1000, risk_free_rate=0.05,nav = 100.00):
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
        expected_ret[i] = np.sum(port["AnnualReturn"] * weight_random)
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
            "Tối Ưu": weight[max_sharpe_index, :].round(decimals=2)*nav ,
            "Tấn Công": weight[max_return_index, :].round(decimals=2)*nav,
            "Phòng Thủ": weight[min_risk_index, :].round(decimals=2)*nav ,
        }
    )
    
    optimal_portfolio.set_index("Stock",inplace=True)

    return optimal_portfolio


def plot_optimal_portfolio_chart(optimal_portfolio):
    # Định dạng lại dữ liệu
    categories = ["Tối Ưu", "Tấn Công", "Phòng Thủ"]
    optimal_portfolio.reset_index(inplace=True)
    ma_co_phieu = optimal_portfolio["Stock"].tolist()
    data = optimal_portfolio[categories].values.T  # Chuyển ma trận để lấy danh mục làm trục x

    total_values = np.sum(data, axis=1, keepdims=True)
    ratios = (data / total_values) * 100  # Chuyển đổi sang tỷ lệ %

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

    # Hiển thị với Streamlit
    st.plotly_chart(fig)


def main(
    input_path: Path = PROCESSED_DATA_DIR / "dataset.csv",
    output_path: Path = PROCESSED_DATA_DIR / "features.csv",
    # -----------------------------------------
):

    pass


if __name__ == "__main__":
    main()
