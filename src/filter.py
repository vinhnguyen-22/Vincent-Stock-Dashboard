from datetime import datetime, timedelta

import matplotlib.pyplot as plt
from numpy import mean
import pandas as pd
import streamlit as st
from streamlit_tags import st_tags
import requests
from src.plots import (
    foreigner_trading_stock,
    get_firm_pricing,
    get_stock_price,
)
from vnstock import Vnstock



HEADERS = {
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
}
def get_stock_data_from_api(market_cap_min, net_bought_val_avg_20d_min):
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
        return pd.DataFrame(data["data"])
    else:
        return {"error": f"Request failed with status code {response.status_code}"}

def filter_stocks(end, market_cap=50, net_bought_val=1):
    if 'stocks_data' not in st.session_state:
        st.session_state.stocks_data = None

    stocks_sorted = None
    if st.button("Danh sách cổ phiếu có tỷ trọng sở hữu nước ngoài cao nhất"):
        market_cap_min = market_cap*1000000000000
        net_bought_val_avg_20d_min = net_bought_val *1000000000
        
        df = get_stock_data_from_api(market_cap_min, net_bought_val_avg_20d_min)
        if isinstance(df, dict) and "error" in df:
            return df

        symbols = df["code"]
        start = end - timedelta(days=30)
        stocks = pd.DataFrame()
        
        for symbol in symbols:
            foreign = foreigner_trading_stock(symbol, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
            curr = foreign["currentRoom"]
            total = foreign["totalRoom"]
            rs = round((total - curr) / total, 6) * 100
            stocks[symbol] = rs
        stocks.sort_index(axis=0, ascending=False, inplace=True)
        st.session_state.stocks_data = stocks

        if st.session_state.stocks_data is not None:
            use_pct_change = st.checkbox("Tốc độ tăng trưởng tỷ lệ sở hữu", value=False)
            stocks = st.session_state.stocks_data
            if use_pct_change:
                stocks = round(stocks.pct_change() * 100, 1).fillna(0)
            if not stocks.empty:
                stocks_sorted = stocks.loc[:, stocks.iloc[-1].sort_values(ascending=False).index].T
            else:
                if all(col in stocks_sorted.columns for col in value_columns):
                    stocks_sorted['lines'] = stocks_sorted[value_columns].values.tolist()
                else:
                    st.warning("Some columns in value_columns do not exist in stocks_sorted.")
                    stocks_sorted = None
            stocks_sorted.index.name = "Code"
            value_columns = stocks_sorted.columns
            stocks_sorted['lines'] = stocks_sorted[value_columns].values.tolist()
        
        return stocks_sorted


def get_stock_by_industry(level=1, higher_level_code=0):
    """Get stock data by industry."""
    base_url = "https://api-finfo.vndirect.com.vn/v4/industry_classification"
    params = [f"industryLevel:{level}"]
    if higher_level_code != 0:
        params.append(f"higherLevelCode:{higher_level_code}")
    
    api_url = f"{base_url}?q=" + "~".join(params)
    try:
        res = requests.get(url=api_url, headers=HEADERS)
        res.raise_for_status()
        data = res.json()
        return pd.DataFrame(data["data"])
    except requests.exceptions.RequestException as e:
        st.write("Yêu cầu không thành công:")
        return None

def filter_stocks_by_industry():
    if 'industries_l1' not in st.session_state:
        st.session_state.industries_l1 = get_stock_by_industry(1)
    if 'industry_l1_name' not in st.session_state:
        st.session_state.industry_l1_name = None
    if 'industry_l2_name' not in st.session_state:
        st.session_state.industry_l2_name = None
    if 'industry_l3_name' not in st.session_state:
        st.session_state.industry_l3_name = None

    # Level 1 industry selection
    industry_l1_name = st.selectbox(
        "Chọn ngành cấp 1",
        options=st.session_state.industries_l1["vietnameseName"].tolist(),
        key="industry_level_1"
    )

    # Level 2 industry selection
    if industry_l1_name:
        if 'industries_l2' not in st.session_state or st.session_state.industry_l1_name != industry_l1_name:
            industry_l1_code = st.session_state.industries_l1[
                st.session_state.industries_l1["vietnameseName"] == industry_l1_name
            ]["industryCode"].iloc[0]
            st.session_state.industries_l2 = get_stock_by_industry(2, higher_level_code=industry_l1_code)
            st.session_state.industry_l1_name = industry_l1_name

        industry_l2_name = st.selectbox(
            "Chọn ngành cấp 2",
            options=st.session_state.industries_l2["vietnameseName"].tolist(),
            key="industry_level_2"
        )

        # Level 3 industry selection
        if industry_l2_name:
            if 'industries_l3' not in st.session_state or st.session_state.industry_l2_name != industry_l2_name:
                industry_l2_code = st.session_state.industries_l2[
                    st.session_state.industries_l2["vietnameseName"] == industry_l2_name
                ]["industryCode"].iloc[0]
                st.session_state.industries_l3 = get_stock_by_industry(3, higher_level_code=industry_l2_code)
                st.session_state.industry_l2_name = industry_l2_name

            industry_l3_name = st.selectbox(
                "Chọn ngành cấp 3",
                options=st.session_state.industries_l3["vietnameseName"].tolist(),
                key="industry_level_3"
            )

            # Display stock list
            if industry_l3_name:
                stocks = st.session_state.industries_l3[
                    st.session_state.industries_l3["vietnameseName"] == industry_l3_name
                ]["codeList"].iloc[0]
                stocks = stocks.split(",")
    return stocks


def filter_stock_by_icb():
     # Lấy dữ liệu ngành từ API
    stock = Vnstock().stock("ACB" ,source='VCI')
    df = stock.listing.symbols_by_industries()

    # UI chọn ngành cấp 1
    nganh1 = st.selectbox("Chọn ngành cấp 1", sorted(df['icb_name2'].unique()))
    df_nganh1 = df[df['icb_name2'] == nganh1]

    # Hiện danh sách cổ phiếu ngay khi chỉ chọn ngành cấp 1
    filtered = df_nganh1

    # UI chọn ngành cấp 2 (tuỳ chọn)
    nganh2 = st.selectbox(
        "Chọn ngành cấp 2 (tùy chọn)", 
        options=["(Tất cả)"] + sorted(df_nganh1['icb_name3'].unique())
    )

    if nganh2 != "(Tất cả)":
        df_nganh2 = df_nganh1[df_nganh1['icb_name3'] == nganh2]
        filtered = df_nganh2

        # UI chọn ngành cấp 3 (tuỳ chọn)
        nganh3 = st.selectbox(
            "Chọn ngành cấp 3 (tùy chọn)", 
            options=["(Tất cả)"] + sorted(df_nganh2['icb_name4'].unique())
        )

        if nganh3 != "(Tất cả)":
            filtered = df_nganh2[df_nganh2['icb_name4'] == nganh3]

    return filtered


def filter_by_pricing_stock(end_date):
    """Filter stocks by pricing."""

    if 'pricing' not in st.session_state:
        st.session_state.pricing = None
    stocks = filter_stock_by_icb()["symbol"]
    start_date = end_date - timedelta(days=90)
    df_safety = pd.DataFrame()
    if st.button("Lọc cổ phiếu theo định giá"):
        data = []
        for stock in stocks:
            df_pricing = get_firm_pricing(stock, start_date.strftime("%Y-%m-%d"))
            if df_pricing is not None and not df_pricing.empty:
                target_pricing = df_pricing["targetPrice"].astype(float).mean()
                close_price = get_stock_price(stock, (end_date - timedelta(days=3)).strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
                
                if not close_price.empty:
                    data.append({
                        "stock": stock,
                        "Định giá": round(target_pricing, 2),
                        "Giá đóng cửa": round(close_price["close"].iloc[-1], 2),
                        "Biên an toàn": round((target_pricing - close_price["close"].iloc[-1]) / target_pricing * 100, 2)
                    })
        
        if data:
            df_safety = pd.DataFrame(data)
            df_safety = df_safety.sort_values(by='Biên an toàn', ascending=False)
            st.dataframe(df_safety)
        else:
            st.warning("Không tìm thấy dữ liệu định giá phù hợp")
            