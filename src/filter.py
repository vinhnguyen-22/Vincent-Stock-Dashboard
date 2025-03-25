from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from numpy import mean
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from streamlit_tags import st_tags
import requests

from src.features import plot_cashflow_analysis, plot_price_chart
from src.optimize_portfolio import (
    calculate_optimal_portfolio,
    get_port,
    get_port_price,
    plot_optimal_portfolio_chart,
)
from src.plots import (
    foreigner_trading_stock,
    get_stock_price,
    plot_close_price_and_ratio,
    plot_firm_pricing,
    plot_foreign_trading,
    plot_proprietary_trading,
)



def filter_stocks(end,market_cap=50, net_bought_val=1):
    market_cap_min = market_cap*1000000000000
    net_bought_val_avg_20d_min = net_bought_val *1000000000
    url = "https://screener-api.vndirect.com.vn/search_data"
    payload = {
        "fields": "code,companyNameVi,floor,priceCr,quarterReportDate,annualReportDate,marketCapCr,netForBoughtValAvgCr20d",
        "filters": [
            {"dbFilterCode": "marketCapCr", "condition": "GT", "value": market_cap_min},
            {"dbFilterCode": "netForBoughtValAvgCr20d", "condition": "GT", "value": net_bought_val_avg_20d_min}
        ],
        "sort": "code:asc"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["data"])
    else:
        return {"error": f"Request failed with status code {response.status_code}"}

    symbols = df["code"]
    start = end - timedelta(days=7)
    stocks = pd.DataFrame()
    for symbol in symbols:
        foreign = foreigner_trading_stock(symbol, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        curr = foreign["currentRoom"]
        total = foreign["totalRoom"]
        rs = round((total - curr) / total, 6) * 100
        stocks[symbol] = rs
    stocks.sort_index(axis=0, ascending=False, inplace=True)
    pct_change = round(stocks.pct_change() * 100, 1)
    use_pct_change = st.radio("Tốc độ tăng trưởng tỷ lệ sở hữu", [False, True], index=0)
    if use_pct_change:
        stocks = pct_change
    stocks_sorted = stocks.loc[:, stocks.iloc[-1].sort_values(ascending=False).index].T
    stocks_sorted.index.name = "Code"
    value_columns  = stocks_sorted.columns
    stocks_sorted['lines'] = stocks_sorted[value_columns].values.tolist()
    return stocks_sorted

def main():
    pass

if __name__ == "__main__":
    main()
