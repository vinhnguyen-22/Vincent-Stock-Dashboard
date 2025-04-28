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

from src.features import (
    fetch_and_plot_ownership,
    fetch_cashflow_data,
    fetch_cashflow_market,
    get_company_plan,
    get_fund_data,
    plot_cashflow_analysis,
    plot_pie_fund,
)
from src.filter import (
    filter_by_ownerratio,
    filter_by_pricing_stock,
    filter_by_quantitative,
    filter_components,
    filter_stocks_by_industry,
)
from src.fund import display_fund_data
from src.market_overview import overview_market
from src.optimize_portfolio import display_portfolio_analysis
from src.plots import (
    get_firm_pricing,
    get_stock_price,
    plot_close_price_and_ratio,
    plot_firm_pricing,
    plot_foreign_trading,
    plot_proprietary_trading,
)
from src.quant_profile import calculate_quant_metrics, calculate_stock_metrics

load_dotenv()
period = 7


def configure_streamlit():
    """Configure Streamlit app settings."""
    st.set_page_config(
        page_title="Vincent App",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://www.extremelycoolapp.com/help",
            "Report a bug": "https://www.extremelycoolapp.com/bug",
            "About": "# This is a header. This is an *extremely* cool app!",
        },
    )


def get_sidebar_inputs():
    """Get user inputs from the sidebar."""
    with st.sidebar:
        st.header("📃 Chọn trang")
        page = st.radio(
            "",
            [
                "📈 Phân Tích Cổ Phiếu",
                "🌍 Tổng Quan Thị Trường",
                "🔍 Bộ Lọc Cổ Phiếu",
                "💰 Phân Tích Dòng Tiền",
                "💲 Đầu Tư Quỹ Mở",
                "🎲 Phân Tích Định Lượng",
                "🗂 Phân Bổ Danh Mục",
                "🧐 Danh Mục Tham Khảo",
            ],
        )
        stock = st.text_input("Nhập mã cổ phiếu", "FPT")

        start_date = st.date_input("Chọn ngày bắt đầu", datetime(2025, 1, 1))
        end_option = st.checkbox("Nhập ngày kết thúc")

        if page != "Tổng Quan Thị Trường" and not end_option:
            time_range = st.selectbox(
                "Chọn khoảng thời gian", ["Tuần", "Tháng", "Qúy", "Năm"], index=1
            )
            end_date = datetime.today()
            if time_range == "Tuần":
                period = 7
                start_date = end_date - timedelta(weeks=1)
            elif time_range == "Tháng":
                period = 30
                start_date = end_date - timedelta(days=30)
            elif time_range == "Qúy":
                period = 90
                start_date = end_date - timedelta(days=90)
            elif time_range == "Năm":
                period = 365
                start_date = end_date - timedelta(days=365)
        else:
            end_date = st.date_input("Chọn ngày kết thúc", start_date + timedelta(days=30))
            period = (end_date - start_date).days

        # Initialize session state for industries and selections

        return stock, start_date, end_date, period, page


def display_cashflow_analysis(stock, df_price, period):
    plot_cashflow_analysis(df_price, stock, period)


def display_trading_analysis(stock, df_price, df_index, start_date, end_date):
    """Display trading analysis for the selected stock."""
    df_pricing = get_firm_pricing(stock, "2024-01-01")

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

    def format_number(num, suffix=""):
        """Format large numbers to K, M, B, T"""
        if num >= 1_000_000_000:
            formatted = f"{num / 1_000_000_000:,.0f}"
            return f"{formatted} Tỷ {suffix}"
        elif num >= 1_000_000:
            formatted = f"{num / 1_000_000:,.0f}"
            return f"{formatted} Triệu {suffix}"
        elif num >= 1_000:
            formatted = f"{num / 1_000:,.0f}"
            return f"{formatted} Ngàn {suffix}"
        else:
            formatted = f"{num:,.0f}"
            return f"{formatted} {suffix}"

    st.header("Tổng quan công ty")
    calculate_stock_metrics(stock, df_price, df_index, df_pricing)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(
            label="Kế Hoạch Doanh Thu",
            value=format_number(latest_data["netRevenueEst"]),
            delta=f"{latest_data['% Doanh Thu Kế Hoạch']:.2f}% Kế hoạch.",
        )

    with col2:
        st.metric(
            label="Kế Hoạch Lợi Nhuận Sau Thuế",
            value=format_number(latest_data["profitAftTaxEst"]),
            delta=f"{latest_data['% Lợi nhuận kế hoạch']:.2f}% Kế hoạch",
        )
    with col3:
        # Calculate YoY growth for net revenue
        if len(df) >= 2:
            prev_year = int(latest_year) - 1
            filtered_df = df[df["fiscalYear"] == prev_year]
            if not filtered_df.empty:
                prev_year_data = filtered_df.iloc[0]
                yoy_growth = (
                    (latest_data["netRevenueVal"] / prev_year_data["netRevenueVal"]) - 1
                ) * 100
                st.metric(
                    label="YoY Net Revenue Growth",
                    value=f"{yoy_growth:.2f}%",
                    delta=f"{yoy_growth:.2f}%",
                )
            else:
                st.metric(label="YoY Net Revenue Growth", value="N/A")
        else:
            st.metric(label="YoY Net Revenue Growth", value="N/A")
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

    def create_comparison_plot(filtered_df, metric_type):
        """
        Create a reusable comparison plot for financial metrics.

        Args:
            filtered_df: DataFrame with financial data
            metric_type: 'revenue' or 'profit' to determine which metrics to plot
        """
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

    col_1, col_2 = st.columns(2)

    # Create plots using the reusable function
    fig1 = create_comparison_plot(filtered_df, "revenue")
    fig2 = create_comparison_plot(filtered_df, "profit")

    with col_1:
        st.plotly_chart(fig1, use_container_width=True)
    with col_2:
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("THÔNG TIN CỔ PHIẾU")
    company = Vnstock().stock(symbol=stock, source="TCBS").company
    profile = company.profile()
    profile.set_index("company_name", inplace=True)
    st.dataframe(
        profile.T,
        use_container_width=True,
    )

    st.divider()
    col_1, col_2 = st.columns(2)
    with col_1:
        st.subheader("CƠ CẤU CỔ ĐÔNG")
        fetch_and_plot_ownership(stock)
    with col_2:
        st.subheader("ĐỊNH GIÁ TỪ CÁC CTCK")
        plot_firm_pricing(df_pricing)

    st.divider()
    st.subheader("GIAO DỊCH CỦA TỔ CHỨC VÀ NƯỚC NGOÀI")
    col_1, col_2 = st.columns(2)
    with col_1:
        plot_proprietary_trading(
            stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
    with col_2:
        plot_foreign_trading(stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    st.divider()
    st.subheader("TƯƠNG QUAN GIAO DỊCH NƯỚC NGOÀI VÀ GIÁ CỔ PHIẾU")
    plot_close_price_and_ratio(
        df_price, stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
    )
    with st.popover("Hướng dẫn"):
        st.write("Update sau")


def display_overview_market():
    """Display market overview."""
    overview_market()
    st.divider()
    start = st.date_input("Chọn ngày: ", datetime(2025, 1, 1))
    df = get_fund_data(start.strftime("%Y-%m-%d"))
    plot_pie_fund(df)


def display_quant_analysis(stock, end_date):
    """Display market overview."""
    years = st.selectbox("Chọn số năm phân tích: ", [5, 7, 10], index=0)
    quant_metric = calculate_quant_metrics(stock, end_date, years)


def display_filter_stock(end_date):
    """Display market overview."""
    stocks = filter_components()
    filter_by_ownerratio(stocks, end_date)

    filter_by_pricing_stock(stocks, end_date)
    st.write(", ".join(stocks))
    if stocks:

        stocks_tag = st_tags(
            label="Nhập mã chứng khoán ở đây",
            text="Press enter to add more",
            value=stocks,
            suggestions=stocks,
            key="stocks_quant",
        )
        years = st.selectbox("Chọn số năm phân tích: ", [5, 7, 10], index=0)
        filter_by_quantitative(stocks_tag, end_date, years)


def main():
    """Main function to run the Streamlit app."""
    configure_streamlit()
    stock, start_date, end_date, period, page = get_sidebar_inputs()
    st.title(f"Vincent App - {page}")
    st.divider()
    st.info(
        """
            Thông báo cập nhật 25/04/2025:
            - Cập nhật chức năn theo dõi kế hoạch kinh doanh
            - cập nhật chức năng phân tích mua bán chủ động
            """
    )

    if stock:
        df_price = get_stock_price(
            stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
        df_index = get_stock_price(
            "VNINDEX", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        )
        if page == "💰 Phân Tích Dòng Tiền":
            display_cashflow_analysis(stock, df_price, period)
        elif page == "🌍 Tổng Quan Thị Trường":
            display_overview_market()
        elif page == "🎲 Phân Tích Định Lượng":
            display_quant_analysis(stock, end_date)
        elif page == "🗂 Phân Bổ Danh Mục":
            display_portfolio_analysis()
        elif page == "🔍 Bộ Lọc Cổ Phiếu":
            display_filter_stock(end_date)
        elif page == "📈 Phân Tích Cổ Phiếu":
            display_trading_analysis(stock, df_price, df_index, start_date, end_date)
        elif page == "💲 Đầu Tư Quỹ Mở":
            display_fund_data()
        else:
            display_overview_market()


if __name__ == "__main__":
    main()
