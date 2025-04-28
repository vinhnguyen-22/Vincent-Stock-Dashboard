from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from vnstock import Vnstock

from src.features import fetch_cashflow_market


def overview_market():
    df = pd.DataFrame()
    date = datetime.now().strftime("%Y-%m-%d")
    date = st.date_input("Chọn ngày", date)
    exchange = st.selectbox(
        "Chọn sàn giao dịch",
        options=[
            # "HOSE",
            # "HNX",
            # "UPCOM",
            "VN30",
            "VN100",
            "HNX30",
            "VNMidCap",
            "VNSmallCap",
            "VNAllShare",
            "HNXCon",
            "HNXFin",
            "HNXLCap",
            "HNXMSCap",
            "HNXMan",
        ],
        index=0,
    )
    stock_by_exchange = (
        Vnstock().stock("ACB", source="VCI").listing.symbols_by_group(exchange).tolist()
    )
    df = pd.DataFrame()
    for ticker in stock_by_exchange:
        df_cf = fetch_cashflow_market(ticker, date)
        if not df_cf.empty:
            df = pd.concat([df, df_cf], ignore_index=True)

    # Add title and description
    st.markdown(
        """
        Dashboard phân tích hoạt động giao dịch, cung cấp thông tin chi tiết về khối lượng giao dịch, hành vi của người mua/người bán và xác định các xu hướng thị trường quan trọng.
        """
    )

    # Create tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Khối lượng giao dịch",
            "Buy/Sell Balance",
            "Giá trị ròng theo danh mục",
            "Mức độ tập trung giao dịch",
        ]
    )

    with tab1:
        st.header("PHÂN TÍCH KHỐI LƯỢNG GIAO DỊCH")

        # Sort by total value
        volume_df = df.sort_values(by="totalVal", ascending=False).head(10)

        # Plot total trading value for top 10 stocks
        fig = px.bar(
            volume_df,
            x="code",
            y="totalVal",
            title="Top 10 Cổ Phiếu theo Khối Lượng Giao Dịch",
            text_auto=".2s",
            color="totalVal",
            color_continuous_scale="Viridis",
            labels={"totalVal": "Total Trading Value", "code": "Stock Code"},
        )
        fig.update_layout(xaxis_title="Stock Code", yaxis_title="Total Value")
        st.plotly_chart(fig, use_container_width=True)

        # Key insights
        st.subheader("Key Insights - Khối Lượng Giao Dịch")
        col1, col2 = st.columns(2)

        with col1:
            top_stock = volume_df.iloc[0]["code"]
            top_value = volume_df.iloc[0]["totalVal"]
            st.metric("Khối Lượng Giao Dịch cao nhất", f"{top_stock}", f"{top_value:,.0f}")

            # Calculate market concentration (% of total volume by top 5 stocks)
            total_market = df["totalVal"].sum()
            top5_share = volume_df.head(5)["totalVal"].sum() / total_market * 100
            st.metric("Top 5 thị phần", f"{top5_share:.2f}%")

        with col2:
            average_volume = df["totalVal"].mean()
            st.metric("Khối Lượng Giao Dịch Trung Bình", f"{average_volume:,.0f}")

    with tab2:
        st.header("Phân Tích Mua/Bán")

        # Calculate total buy and sell values for each stock
        df["totalBuyVal"] = df["topActiveBuyVal"] + df["midActiveBuyVal"] + df["botActiveBuyVal"]
        df["totalSellVal"] = (
            df["topActiveSellVal"] + df["midActiveSellVal"] + df["botActiveSellVal"]
        )
        df["buyProportion"] = df["totalBuyVal"] / (df["totalBuyVal"] + df["totalSellVal"]) * 100

        # Create a figure with buy/sell ratio
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add total values
        buy_sell_df = df.sort_values(by="totalVal", ascending=False)

        # Add bars for buy and sell values
        fig.add_trace(
            go.Bar(
                x=buy_sell_df["code"],
                y=buy_sell_df["totalBuyVal"],
                name="Total Buy Value",
                marker_color="green",
                opacity=0.7,
            )
        )

        fig.add_trace(
            go.Bar(
                x=buy_sell_df["code"],
                y=buy_sell_df["totalSellVal"],
                name="Total Sell Value",
                marker_color="red",
                opacity=0.7,
            )
        )

        # Add line for buy proportion
        fig.add_trace(
            go.Scatter(
                x=buy_sell_df["code"],
                y=buy_sell_df["buyProportion"],
                mode="lines+markers",
                name="Buy Proportion (%)",
                marker=dict(size=8, color="blue"),
                line=dict(width=2),
            ),
            secondary_y=True,
        )

        # Add 50% line to show equal buy/sell
        fig.add_trace(
            go.Scatter(
                x=buy_sell_df["code"],
                y=[50] * len(buy_sell_df),
                mode="lines",
                name="Equal Buy/Sell (50%)",
                line=dict(color="orange", width=1, dash="dash"),
            ),
            secondary_y=True,
        )

        # Update layout
        fig.update_layout(
            title_text="Buy vs. Sell Values by Stock",
            barmode="group",
            xaxis_title="Stock Code",
            yaxis_title="Value",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        fig.update_yaxes(title_text="Value", secondary_y=False)
        fig.update_yaxes(title_text="Buy Proportion (%)", secondary_y=True)

        st.plotly_chart(fig, use_container_width=True)

        # Identify stocks with highest buy and sell pressure
        st.subheader("Notable Buy/Sell Pressure")
        col1, col2 = st.columns(2)

        with col1:
            # Stocks with highest buy pressure
            buy_pressure_df = df.sort_values(by="buyProportion", ascending=False).head(5)
            st.write("Highest Buy Pressure (% of total activity)")

            for i, row in buy_pressure_df.iterrows():
                st.markdown(f"**{row['code']}**: {row['buyProportion']:.2f}%")

        with col2:
            # Stocks with highest sell pressure
            sell_pressure_df = df.sort_values(by="buyProportion", ascending=True).head(5)
            st.write("Highest Sell Pressure (% of total activity)")

            for i, row in sell_pressure_df.iterrows():
                st.markdown(f"**{row['code']}**: {(100-row['buyProportion']):.2f}%")

    with tab3:
        st.header("Net Value Analysis by Trader Category")

        # Calculate net values
        df["netVal"] = df["netTopVal"] + df["netMidVal"] + df["netBotVal"]

        # Sort by absolute net value
        net_df = df.sort_values(by="netVal", key=abs, ascending=False)

        # Create figure for net values
        fig = px.bar(
            net_df.head(10),
            x="code",
            y=["netTopVal", "netMidVal", "netBotVal"],
            title="Net Buy/Sell Value by Trader Category (Top/Mid/Bot)",
            labels={"value": "Net Value", "code": "Stock Code", "variable": "Trader Category"},
            color_discrete_map={
                "netTopVal": "#1f77b4",
                "netMidVal": "#ff7f0e",
                "netBotVal": "#2ca02c",
            },
            barmode="group",
        )

        fig.update_layout(
            xaxis_title="Stock Code",
            yaxis_title="Net Value (Buy - Sell)",
            legend_title="Trader Category",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        # Add a horizontal line at y=0
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=0,
            x1=len(net_df.head(10)) - 0.5,
            y1=0,
            line=dict(color="black", width=1, dash="dash"),
        )

        st.plotly_chart(fig, use_container_width=True)

        # Show stocks with highest positive and negative net values
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Cổ phiếu mua ròng mạnh nhất")
            positive_net = df.sort_values(by="netVal", ascending=False).head(5)

            for i, row in positive_net.iterrows():
                st.markdown(f"**{row['code']}**: {row['netVal']:,.0f}")

        with col2:
            st.subheader("Cổ phiếu bán ròng mạnh nhất")
            negative_net = df.sort_values(by="netVal", ascending=True).head(5)

            for i, row in negative_net.iterrows():
                st.markdown(f"**{row['code']}**: {row['netVal']:,.0f}")

        # Show a summary of Top Trader activity
        st.subheader("Top Trader Activity Analysis")

        # Calculate aggregates
        top_trader_net = df["netTopVal"].sum()
        mid_trader_net = df["netMidVal"].sum()
        bot_trader_net = df["netBotVal"].sum()

        fig = px.bar(
            x=["Top Traders", "Mid Traders", "Bot Traders"],
            y=[top_trader_net, mid_trader_net, bot_trader_net],
            title="Net Activity by Trader Category (Market-wide)",
            labels={"x": "Trader Category", "y": "Net Value"},
            color=["Top Traders", "Mid Traders", "Bot Traders"],
            text_auto=".2s",
        )

        fig.update_layout(xaxis_title="Trader Category", yaxis_title="Net Value")

        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.header("Phân Tích Mức Độ Tập Trung Giao Dịch")

        # Create analyses for all trader types
        trader_types = ["Top", "Mid", "Bot"]

        for trader_type in trader_types:
            st.subheader(f"Phân tích nhóm {trader_type}")

            # Dynamic column names based on trader type
            buy_col = f"{trader_type.lower()}ActiveBuyVal"
            sell_col = f"{trader_type.lower()}ActiveSellVal"
            net_col = f"net{trader_type}Val"

            # Calculate concentration metrics
            df[f"{trader_type.lower()}BuySellRatio"] = df[buy_col] / df[sell_col]
            df[f"{trader_type.lower()}BuyConcentration"] = df[buy_col] / df["totalVal"] * 100
            df[f"{trader_type.lower()}SellConcentration"] = df[sell_col] / df["totalVal"] * 100

            # Create a scatter plot of concentration metrics
            fig = px.scatter(
                df,
                x=f"{trader_type.lower()}BuyConcentration",
                y=f"{trader_type.lower()}SellConcentration",
                size="totalVal",
                color=net_col,
                hover_name="code",
                text="code",
                title=f"Phân tích lựa chọn các nhà giao dịch {trader_type}",
                labels={
                    f"{trader_type.lower()}BuyConcentration": f"{trader_type} Trader Buy Concentration (%)",
                    f"{trader_type.lower()}SellConcentration": f"{trader_type} Trader Sell Concentration (%)",
                    "totalVal": "Total Trading Value",
                    net_col: f"Net {trader_type} Trader Value",
                },
                color_continuous_scale="RdYlGn",
                range_color=[-df[net_col].abs().max(), df[net_col].abs().max()],
            )

            # Add 45-degree line (equal buy/sell concentration)
            max_val = max(
                df[f"{trader_type.lower()}BuyConcentration"].max(),
                df[f"{trader_type.lower()}SellConcentration"].max(),
            )
            fig.add_trace(
                go.Scatter(
                    x=[0, max_val],
                    y=[0, max_val],
                    mode="lines",
                    line=dict(color="orange", width=1, dash="dash"),
                    name="Equal Concentration",
                )
            )

            fig.update_traces(
                textposition="top center", marker=dict(line=dict(width=1, color="DarkSlateGrey"))
            )

            fig.update_layout(
                xaxis_title=f"{trader_type} Trader Buy Concentration (%)",
                yaxis_title=f"{trader_type} Trader Sell Concentration (%)",
            )

            st.plotly_chart(fig, use_container_width=True)

            # Key observations
            col1, col2 = st.columns(2)

            with col1:
                # Calculate average trader concentration
                avg_buy = df[f"{trader_type.lower()}BuyConcentration"].mean()
                avg_sell = df[f"{trader_type.lower()}SellConcentration"].mean()

                st.metric(f"Tỷ trọng mua trung bình của nhóm {trader_type}", f"{avg_buy:.2f}%")
                st.metric(f"Tỷ trọng bán trung bình của nhóm {trader_type}", f"{avg_sell:.2f}%")

                # Find most imbalanced stock
                most_imbalanced = df.sort_values(
                    by=f"{trader_type.lower()}BuySellRatio", ascending=False
                ).iloc[0]
                st.metric(
                    f"Cổ phiếu mất cân bằng nhất của nhóm {trader_type}",
                    f"{most_imbalanced['code']}",
                    f"Tỷ lệ Mua/Bán: {most_imbalanced[f'{trader_type.lower()}BuySellRatio']:.2f}",
                )

            with col2:
                # Stocks with highest trader buy and sell participation
                highest_buy = df.sort_values(
                    by=f"{trader_type.lower()}BuyConcentration", ascending=False
                ).iloc[0]
                highest_sell = df.sort_values(
                    by=f"{trader_type.lower()}SellConcentration", ascending=False
                ).iloc[0]

                st.metric(
                    f"Cổ phiếu được mua nhiều nhất bởi {trader_type} Trader",
                    f"{highest_buy['code']}",
                    f"{highest_buy[f'{trader_type.lower()}BuyConcentration']:.2f}%",
                )

                st.metric(
                    f"Cổ phiếu bị bán nhiều nhất của {trader_type} Trader",
                    f"{highest_sell['code']}",
                    f"{highest_sell[f'{trader_type.lower()}SellConcentration']:.2f}%",
                )
