from contextlib import suppress
from datetime import datetime, timedelta
from dis import dis
from math import e, sqrt

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv
from numpy import empty
from streamlit_tags import st_tags
from vnstock import Vnstock

from src.features import get_company_plan


def create_comparison_plot(filtered_df, metric_type):
    metrics = {
        "revenue": {
            "est_col": "netRevenueEst",
            "val_col": "netRevenueVal",
            "pct_col": "% Doanh Thu Kế Hoạch",
            "est_name": "Estimate Net Revenue",
            "val_name": "Actual Net Revenue",
            "title": "Net Revenue: Actual vs Estimated (Billions VND)",
        },
        "profit": {
            "est_col": "profitAftTaxEst",
            "val_col": "profitAftTaxVal",
            "pct_col": "% Lợi nhuận kế hoạch",
            "est_name": "Estimate Profit Revenue",
            "val_name": "Actual Profit After Tax",
            "title": "Profit After Tax: Actual vs Estimated (Billions VND)",
        },
    }

    m = metrics[metric_type]
    fig = go.Figure()

    # Add estimate bar
    fig.add_trace(
        go.Bar(x=filtered_df["fiscalYear"], y=filtered_df[m["est_col"]], name=m["est_name"])
    )

    # Add actual bar
    fig.add_trace(
        go.Bar(x=filtered_df["fiscalYear"], y=filtered_df[m["val_col"]], name=m["val_name"])
    )

    # Add percentage line
    fig.add_trace(
        go.Scatter(
            x=filtered_df["fiscalYear"],
            y=filtered_df[m["pct_col"]],
            name=m["est_name"],
            yaxis="y2",
            mode="lines+markers+text",
            text=filtered_df[m["pct_col"]].round(2).astype(str) + "%",
            textposition="top center",
            line=dict(color="rgba(246, 78, 139, 0.8)", width=3),
        )
    )

    # Update layout
    fig.update_layout(
        title=m["title"],
        xaxis_title="Fiscal Year",
        yaxis_title="Amount (Billions VND)",
        hovermode="x unified",
        yaxis2=dict(title="% Kế hoạch", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def calculate_stock_metrics(stock, df_price, df_pricing):
    # Constants
    TARGET_YEAR = 2025
    SAFETY_MARGIN_THRESHOLD = 0.3

    try:
        # Data preparation
        df_price.set_index("time", inplace=True)

        # Calculate target and current prices
        target_price = round(
            df_pricing[pd.to_datetime(df_pricing["reportDate"]).dt.year == TARGET_YEAR][
                "targetPrice"
            ].mean(),
            2,
        )
        current_price = df_price.iloc[-1]["close"]

        # Calculate safety margin and recommendation
        safety_margin = (target_price - current_price) / target_price
        recommendation = (
            "Mua"
            if safety_margin > SAFETY_MARGIN_THRESHOLD
            else "Nắm giữ" if safety_margin > 0 else "Bán"
        )

        # Create metrics dataframe
        col = st.columns(4)
        with col[0]:
            st.metric("Giá hiện tại", f"{int(current_price*1000):,} VND", border=True)
        with col[1]:
            st.metric("Định giá", f"{int(target_price*1000):,} VND", border=True)
        with col[2]:
            st.metric("Biên an toàn", f"{safety_margin*100:.2f}%", border=True)
        with col[3]:
            st.metric("Khuyến nghị", recommendation, border=True)

    except:
        return st.write("Không có dữ liệu")


def format_number(num, suffix=""):
    """Format large numbers to K, M, B, T"""
    if num >= 1000000000:
        formatted = f"{num / 1000000000:,.0f}"
        return f"{formatted} Tỷ {suffix}"
    elif num >= 1000000:
        formatted = f"{num / 1000000:,.0f}"
        return f"{formatted} Triệu {suffix}"
    elif num >= 1000:
        formatted = f"{num / 1000:,.0f}"
        return f"{formatted} Ngàn {suffix}"
    else:
        formatted = f"{num:,.0f}"
        return f"{formatted} {suffix}"


def IS_company(stock):
    vn_stock = Vnstock().stock(symbol=stock, source="TCBS")
    IS = vn_stock.finance.income_statement(period="quarter", lang="en").head(8)

    # Chọn các cột cần thiết
    IS = IS[
        [
            "yearReport",
            "lengthReport",
            "Revenue (Bn. VND)",
            "Attribute to parent company (Bn. VND)",
        ]
    ]
    IS = IS.sort_values(by=["yearReport", "lengthReport"], ascending=[True, True])

    # Tạo cột kỳ để dễ xử lý
    IS["Kỳ"] = "Q" + IS["lengthReport"].astype(str) + "/" + IS["yearReport"].astype(str)

    # Tìm quý gần nhất
    latest_row = IS.iloc[-1]
    latest_quarter = latest_row["lengthReport"]
    latest_year = latest_row["yearReport"]
    latest_kỳ = latest_row["Kỳ"]
    latest_revenue = latest_row["Revenue (Bn. VND)"]
    latest_profit = latest_row["Attribute to parent company (Bn. VND)"]

    # Tìm cùng kỳ năm trước
    prev_year = latest_year - 1
    prev_row = IS[(IS["lengthReport"] == latest_quarter) & (IS["yearReport"] == prev_year)]

    if not prev_row.empty:
        prev_revenue = prev_row.iloc[0]["Revenue (Bn. VND)"]
        prev_profit = prev_row.iloc[0]["Attribute to parent company (Bn. VND)"]

        delta_rev_pct = (latest_revenue - prev_revenue) / prev_revenue * 100
        delta_profit_pct = (latest_profit - prev_profit) / prev_profit * 100

        # Hiển thị song song 2 chỉ số
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label=f"Doanh thu {latest_kỳ} vs Q{latest_quarter}/{prev_year}",
                value=format_number(latest_revenue),
                border=True,
                delta=f"{delta_rev_pct:.2f}% so với cùng kỳ",
            )

        with col2:
            st.metric(
                label=f"LNST (CĐ mẹ) {latest_kỳ} vs Q{latest_quarter}/{prev_year}",
                value=format_number(latest_profit),
                border=True,
                delta=f"{delta_profit_pct:.2f}% so với cùng kỳ",
            )
    else:
        st.warning("Không có dữ liệu cho cùng kỳ quý trước!")


def company_profile(stock, df_price, df_pricing, start_date, end_date):
    df = get_company_plan(stock, 2015)
    if "netRevenueVal" and "netRevenueEst" not in df.columns:
        df["netRevenueVal"] = 100
        df["netRevenueEst"] = 100

    df = df.sort_values("fiscalYear")
    df["% Doanh Thu Kế Hoạch"] = df["netRevenueVal"] / df["netRevenueEst"] * 100
    df["% Lợi nhuận kế hoạch"] = df["profitAftTaxVal"] / df["profitAftTaxEst"] * 100
    df.dropna(subset="% Doanh Thu Kế Hoạch", inplace=True)
    df.dropna(subset="% Lợi nhuận kế hoạch", inplace=True)
    latest_year = df["fiscalYear"].iloc[-1]
    latest_data = df[df["fiscalYear"] == latest_year].iloc[0]

    calculate_stock_metrics(stock, df_price, df_pricing)
    col_1, col_2 = st.columns(2)

    with col_1:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="Kế Hoạch Doanh Thu",
                value=format_number(latest_data["netRevenueEst"]),
                border=True,
                delta=f"{latest_data['% Doanh Thu Kế Hoạch']:.2f}% Kế hoạch.",
            )

        with col2:
            st.metric(
                label="Kế Hoạch Lợi Nhuận Sau Thuế",
                value=format_number(latest_data["profitAftTaxEst"]),
                border=True,
                delta=f"{latest_data['% Lợi nhuận kế hoạch']:.2f}% Kế hoạch",
            )
    with col_2:
        IS_company(stock)

    st.sidebar.header("Filter Options")
    year_range = st.sidebar.slider(
        "Select Year Range",
        min_value=int(df["fiscalYear"].min()),
        max_value=int(df["fiscalYear"].max()),
        value=(int(df["fiscalYear"].min()), int(df["fiscalYear"].max())),
    )

    # Filter data based on selected years
    filtered_df = df[
        (df["fiscalYear"].astype(int) >= year_range[0])
        & (df["fiscalYear"].astype(int) <= year_range[1])
    ]

    col_1, col_2 = st.columns(2)

    # Create plots using the reusable function
    fig1 = create_comparison_plot(filtered_df, "revenue")
    fig2 = create_comparison_plot(filtered_df, "profit")

    with col_1:
        st.plotly_chart(fig1, use_container_width=True)
    with col_2:
        st.plotly_chart(fig2, use_container_width=True)
