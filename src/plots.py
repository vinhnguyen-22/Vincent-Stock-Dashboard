import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from vnstock import Vnstock

from src.tcbs_stock_data import TCBSStockData

cookies = {
    "vnds-uuid": "4408bacf-3ab6-44f4-a8bf-e1f775a4cfd1",
    "vnds-uuid-d": "1692352399674",
    "hubspotutk": "edd567b45c7010c2aed97945c1b01fdc",
    "_fbp": "fb.2.1701411065088.1101377913",
    "_ga_6ZM759CRYX": "GS1.1.1704686095.1.0.1704686095.0.0.0",
    "_ga_TK3KB287ZD": "GS1.3.1707143244.5.0.1707143244.0.0.0",
    "_gcl_au": "1.1.263873144.1707654508",
    "_gid": "GA1.3.164983510.1708877431",
    "token-id": "efeff96d-85d0-4aaf-a207-7a3b41a28a36",
    "accessToken": "eyJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJpc3N1ZXIiLCJzdWIiOiJzdWJqZWN0IiwiYXVkIjpbImF1ZGllbmNlIiwiaW9zIiwib25saW5lIiwidHJhZGVhcGkiLCJhdXRoIl0sImV4cCI6MTcwOTE3OTIxOCwibmJmIjoxNzA5MTUwMTE4LCJpYXQiOjE3MDkxNTA0MTgsImFsbG93U2hhcmluZ1Byb2ZpbGUiOiIiLCJyb2xlcyI6IltdIiwiYWNjb3VudFR5cGUiOm51bGwsInZfdXNlcklkIjoiMjAzNjAxMTU0Mjg1OTc2OSIsInVzZXJJZCI6Im51bGwiLCJ2ZXJzaW9uIjoiVjIiLCJjdXN0b21lck5hbWUiOiJOR1VZ4buETiBUSEFOSCBWSU5IIiwidHJhZGluZ0V4cCI6MCwiaWRnSWQiOm51bGwsInBob25lIjoiMDM0NDQ4ODc2MSIsImN1c3RvbWVySWQiOiIwMTAxMDE4MTA4IiwicmV0aXJlZEFjY291bnRzIjpudWxsLCJ1c2VyVHlwZSI6ImFjdGl2ZSIsImVtYWlsIjoidmluaG5ndXllbmFkMjJAZ21haWwuY29tIiwidXNlcm5hbWUiOiIwMzQ0NDg4NzYxIiwic3RhdHVzIjoiTm90IHVzZWQifQ.I1oE8MnO4gRl8bPlYC628UWNA3nWPtQHKNn4oy8A3v1GANzcX04vf1L7YlbxDusommU-KeXDRhk13iLOGNKenHuzs5kw5jw3D-SeDLPbzSDBINH92GLqNjTkOXUlCtBQWOgYEHhydbkjc51uUko13WaBG7zBWJybU_8jAD8-_ZcwnK-P0tOYiUZzJlhhkyxzfTu0uWsS8Vhm4wqqYEcvlFYgSdsQtkAjrgmRGgYA6pqiENAIz6kR0446H4tgcnCb-6qk_jS0_8Z9r-oYsebEAoNAz-DJGxTMQptqqQkeHHW6zJxNVdGaKdEK0MiQpcgQtjM-p6tKy06gc7eePcDIQA",
    "myUsername": "0344488761",
    "dlink-token": "04316f66e1c93a274e0190901c1151b369f4znTj",
    "__hstc": "2186287.edd567b45c7010c2aed97945c1b01fdc.1692644903520.1709053591695.1709152493953.45",
    "__hssrc": "1",
    "_ga_E9VQ08SM6F": "GS1.1.1709150433.81.1.1709152929.6.0.0",
    "__hssc": "2186287.2.1709152493953",
    "_ga_6VJHGNJJ3F": "GS1.1.1709152472.92.1.1709153529.60.0.0",
    "_ga_188NCLS7Q4": "GS1.1.1709152731.110.1.1709153536.56.0.0",
    "_ga_B4ERGR30NH": "GS1.1.1709152731.107.1.1709153536.56.0.0",
    "_ga_M0QV5JMKN5": "GS1.1.1709152731.107.1.1709153536.56.0.0",
    "_ga_FX88YC793Q": "GS1.1.1709150424.288.1.1709153538.60.0.0",
    "_ga": "GA1.3.952483946.1692352396",
}

id = "28890077D4314EC785FC981FFFA55075"  # @param {type:"string"}
headers = {
    "X-Request-Id": id,
    "pgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
}


def get_firm_pricing(symbol, start_date):
    api_url = f"https://api-finfo.vndirect.com.vn/v4/recommendations?q=code:{symbol}~reportDate:gte:{start_date}&size=100&sort=reportDate:DESC"
    try:
        res = requests.get(url=api_url, headers=headers, cookies=cookies)
        res.raise_for_status()
        data = res.json()
        return pd.DataFrame(data["data"])
    except requests.exceptions.RequestException as e:
        st.write("Yêu cầu không thành công:")
        return None


def foreigner_trading_stock(stock, start, end):
    api_url = f"https://api-finfo.vndirect.com.vn/v4/foreigns?sort=tradingDate&q=code:{stock}~tradingDate:gte:{start}~tradingDate:lte:{end}&size=365"
    try:
        res = requests.get(url=api_url, headers=headers)
        res.raise_for_status()
        data = res.json()
        df = pd.DataFrame(data["data"])
        df.rename(columns={"tradingDate": "time"}, inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        st.write("Yêu cầu không thành công:")
        return None


def proprietary_trading_stock(stock, start, end):
    api_url = f"https://api-finfo.vndirect.com.vn/v4/proprietary_trading?q=code:{stock}~date:lte:{end}~date:gte:{start}&sort=date:desc&size=20"
    try:
        res = requests.get(url=api_url, headers=headers)
        res.raise_for_status()
        data = res.json()
        df = pd.DataFrame(data["data"])
        df.rename(columns={"date": "time"}, inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        st.write("Yêu cầu không thành công:")
        return None


def plot_firm_pricing(df):
    try:
        fig = px.scatter(
            df,
            x="reportDate",
            y="targetPrice",
            color="firm",
            labels={
                "reportDate": "Ngày báo cáo",
                "targetPrice": "Giá mục tiêu",
                "firm": "Công ty chứng khoán",
            },
            text=df.apply(lambda row: f"{row['firm']} - {row['targetPrice']}", axis=1),
        )
        fig.update_traces(
            textposition="top center",
        )
        fig.update_layout(showlegend=False)

        st.plotly_chart(
            fig,
            use_container_width=True,
        )
    except:
        st.write("Không có dữ liệu")


def plot_foreign_trading(stock, start_date, end_date):
    try:
        df = pd.DataFrame(foreigner_trading_stock(stock, start_date, end_date))
        df["time"] = pd.to_datetime(df["time"])
        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=df["time"],
                y=df["netVal"],
                name="Net Value",
                marker_color=df["netVal"].apply(lambda x: "lightgreen" if x >= 0 else "coral"),
            )
        )
        # Biểu đồ đường cho sở hữu nước ngoài
        ratio = (df["totalRoom"] - df["currentRoom"]) / df["totalRoom"]
        fig.add_trace(
            go.Scatter(
                x=df["time"],
                y=round(ratio, 2) * 100,
                mode="lines",
                name="(%) Sở hữu nước ngoài",
                line=dict(color="blue"),
                yaxis="y2",
            )
        )

        # Cấu hình layout
        fig.update_layout(
            title_text=f"Thống kê giao dịch và sở hữu nước ngoài cổ phiếu " + stock,
            xaxis_title="",
            yaxis_title="Giá trị giao dịch",
            yaxis2=dict(title="Foreigner ownership", overlaying="y", side="right", range=[0, 100]),
            template="plotly_white",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(l=40, r=40, t=40, b=40),
        )

        st.plotly_chart(fig)
    except:
        st.write("Không có dữ liệu")


def plot_proprietary_trading(stock, start_date, end_date):
    try:
        df = pd.DataFrame(proprietary_trading_stock(stock, start=start_date, end=end_date))
        df["time"] = pd.to_datetime(df["time"])

        fig = go.Figure()

        # Biểu đồ cột cho giá trị mua bán
        fig.add_trace(
            go.Bar(
                x=df["time"],
                y=df["netVal"],
                name="Net Value",
                marker_color=df["netVal"].apply(lambda x: "lightgreen" if x >= 0 else "coral"),
            )
        )

        # Cấu hình layout
        fig.update_layout(
            title_text=f"Thống kê giao dịch và sở hữu nhà đầu tư tổ chức cổ phiếu  " + stock,
            xaxis_title="",
            yaxis_title="Giá trị giao dịch",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            hovermode="x unified",
            margin=dict(l=40, r=40, t=40, b=40),
        )

        st.plotly_chart(fig)
    except:
        st.write("Không có dữ liệu")


def get_stock_data_with_ratio(df_price, symbol, start_date, end_date):
    foreign = foreigner_trading_stock(symbol, start=start_date, end=end_date)
    foreign["time"] = pd.to_datetime(foreign["time"])
    merged_df = pd.merge(df_price, foreign, on="time", how="right")
    merged_df.ffill(inplace=True)
    merged_df.dropna(subset=["currentRoom"], inplace=True)
    merged_df["ratio"] = (merged_df["totalRoom"] - merged_df["currentRoom"]) / merged_df[
        "totalRoom"
    ]
    result_df = merged_df[["time", "volume", "close", "ratio"]]
    return result_df


def get_stock_price(symbol, start_date, end_date, interval="1D"):
    tcbs = TCBSStockData(rate_limit_pause=0)
    df = tcbs.get_stock_data_by_date_range(symbol, start_date=start_date, end_date=end_date)
    df["time"] = pd.to_datetime(df["time"])
    df["close"] = df["close"].astype(float) / 1000
    return df


def plot_close_price_and_ratio(df_price, symbol, start_date, end_date):
    try:

        result = get_stock_data_with_ratio(df_price, symbol, start_date, end_date)

        fig = go.Figure()

        # Add the close price trace
        fig.add_trace(
            go.Scatter(
                x=result["time"],
                y=result["close"],
                mode="lines+markers",
                name="Close Price",
                marker=dict(size=6, symbol="cross"),
            )
        )

        # Add the ratio trace
        fig.add_trace(
            go.Scatter(
                x=result["time"],
                y=round(result["ratio"] * 100, 2),
                mode="lines+markers",
                name="Sở hữu nước ngoài (%)",
                yaxis="y2",
                marker=dict(size=6, symbol="circle"),
            )
        )

        # Update layout for dual y-axes
        fig.update_layout(
            title_text=f"Tương quan giá và tỷ lệ sở hữu nước ngoài cổ phiếu {symbol}",
            xaxis_title="",
            yaxis_title="Giá cổ phiếu",
            yaxis2=dict(title="Tỷ lệ sở hữu nước ngoài", overlaying="y", side="right"),
            template="plotly_white",
            hovermode="x unified",
            margin=dict(l=40, r=40, t=40, b=40),
        )

        st.plotly_chart(fig)
    except:
        st.write("Không có dữ liệu")


def main():
    pass


if __name__ == "__main__":
    main()
