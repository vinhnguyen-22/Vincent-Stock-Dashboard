import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Set page configuration
st.set_page_config(layout="wide", page_title="HPG Financial Analysis Dashboard")


# Load data
@st.cache_data
def load_data():
    bs_df = pd.read_csv("BS.csv", index_col=0)
    cf_df = pd.read_csv("CF.csv", index_col=0)
    is_df = pd.read_csv("IS.csv", index_col=0)

    # Convert yearReport to int for proper sorting
    bs_df["yearReport"] = bs_df["yearReport"].astype(int)
    cf_df["yearReport"] = cf_df["yearReport"].astype(int)
    is_df["yearReport"] = is_df["yearReport"].astype(int)

    # Sort by year in descending order
    bs_df = bs_df.sort_values("yearReport", ascending=False)
    cf_df = cf_df.sort_values("yearReport", ascending=False)
    is_df = is_df.sort_values("yearReport", ascending=False)

    return bs_df, cf_df, is_df


bs_df, cf_df, is_df = load_data()


# Utility function to format numbers as billions VND
def format_billions(value):
    if isinstance(value, (int, float)):
        return f"{value/1e9:.2f} Tỷ VND"
    return value


# Utility function to calculate YoY growth
def calc_yoy_growth(current, previous):
    if previous == 0:
        return float("inf")
    return (current - previous) / previous * 100


# Main title
st.title("HPG Financial Analysis Dashboard")
st.write("Phân tích tình hình tài chính của Hòa Phát (HPG)")

# Create tabs for different analysis views
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "Tổng quan",
        "Phân tích tăng trưởng",
        "Phân tích biên lợi nhuận",
        "Phân tích tài sản và nợ",
        "Đánh giá chỉ số",
        "Phân tích DUPONT",
    ]
)

with tab1:
    st.header("Tổng quan tài chính HPG")

    # Key metrics for overview
    col1, col2, col3 = st.columns(3)

    latest_year = bs_df["yearReport"].iloc[0]
    previous_year = bs_df["yearReport"].iloc[1]

    # Extract latest financial data
    latest_revenue = is_df[is_df["yearReport"] == latest_year]["Revenue (Bn. VND)"].values[0]
    prev_revenue = is_df[is_df["yearReport"] == previous_year]["Revenue (Bn. VND)"].values[0]

    latest_profit = is_df[is_df["yearReport"] == latest_year]["Net Profit For the Year"].values[0]
    prev_profit = is_df[is_df["yearReport"] == previous_year]["Net Profit For the Year"].values[0]

    latest_assets = bs_df[bs_df["yearReport"] == latest_year]["TOTAL ASSETS (Bn. VND)"].values[0]
    prev_assets = bs_df[bs_df["yearReport"] == previous_year]["TOTAL ASSETS (Bn. VND)"].values[0]

    # Calculate YoY growth
    revenue_growth = calc_yoy_growth(latest_revenue, prev_revenue)
    profit_growth = calc_yoy_growth(latest_profit, prev_profit)
    assets_growth = calc_yoy_growth(latest_assets, prev_assets)

    # Display key metrics with YoY growth
    with col1:
        st.metric("Doanh thu", format_billions(latest_revenue), f"{revenue_growth:.2f}%")

    with col2:
        st.metric("Lợi nhuận ròng", format_billions(latest_profit), f"{profit_growth:.2f}%")

    with col3:
        st.metric("Tổng tài sản", format_billions(latest_assets), f"{assets_growth:.2f}%")

    # Revenue and profit trend over years
    st.subheader("Doanh thu và lợi nhuận qua các năm")

    # Prepare data for line chart
    yearly_data = pd.DataFrame(
        {
            "Năm": is_df["yearReport"],
            "Doanh thu": is_df["Revenue (Bn. VND)"]
            / 1e9,  # Convert to billions for easier reading
            "Lợi nhuận ròng": is_df["Net Profit For the Year"] / 1e9,
        }
    )

    # Create line chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(x=yearly_data["Năm"], y=yearly_data["Doanh thu"], name="Doanh thu (Tỷ VND)"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=yearly_data["Năm"],
            y=yearly_data["Lợi nhuận ròng"],
            name="Lợi nhuận ròng (Tỷ VND)",
            line=dict(color="red"),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title_text="Doanh thu và lợi nhuận ròng qua các năm",
        xaxis=dict(title="Năm", tickmode="linear"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_yaxes(title_text="Doanh thu (Tỷ VND)", secondary_y=False)
    fig.update_yaxes(title_text="Lợi nhuận ròng (Tỷ VND)", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

    # Asset and liability composition
    st.subheader("Cơ cấu tài sản và nợ (Năm gần nhất)")

    col1, col2 = st.columns(2)

    with col1:
        # Assets composition pie chart
        latest_bs = bs_df[bs_df["yearReport"] == latest_year].iloc[0]

        asset_data = {
            "Loại": [
                "Tiền và tương đương tiền",
                "Đầu tư ngắn hạn",
                "Phải thu",
                "Hàng tồn kho",
                "Tài sản cố định",
                "Tài sản dài hạn khác",
            ],
            "Giá trị (Tỷ VND)": [
                latest_bs["Cash and cash equivalents (Bn. VND)"] / 1e9,
                latest_bs["Short-term investments (Bn. VND)"] / 1e9,
                latest_bs["Accounts receivable (Bn. VND)"] / 1e9,
                latest_bs["Net Inventories"] / 1e9,
                latest_bs["Fixed assets (Bn. VND)"] / 1e9,
                (latest_bs["LONG-TERM ASSETS (Bn. VND)"] - latest_bs["Fixed assets (Bn. VND)"])
                / 1e9,
            ],
        }

        asset_df = pd.DataFrame(asset_data)

        fig_assets = px.pie(
            asset_df,
            values="Giá trị (Tỷ VND)",
            names="Loại",
            title=f"Cơ cấu tài sản năm {latest_year}",
        )

        fig_assets.update_traces(textposition="inside", textinfo="percent+label")

        st.plotly_chart(fig_assets, use_container_width=True)

    with col2:
        # Liabilities and equity composition
        liabilities_equity_data = {
            "Loại": ["Nợ ngắn hạn", "Nợ dài hạn", "Vốn chủ sở hữu"],
            "Giá trị (Tỷ VND)": [
                latest_bs["Current liabilities (Bn. VND)"] / 1e9,
                latest_bs["Long-term liabilities (Bn. VND)"] / 1e9,
                latest_bs["OWNER'S EQUITY(Bn.VND)"] / 1e9,
            ],
        }

        liabilities_equity_df = pd.DataFrame(liabilities_equity_data)

        fig_liabilities = px.pie(
            liabilities_equity_df,
            values="Giá trị (Tỷ VND)",
            names="Loại",
            title=f"Cơ cấu nợ và vốn chủ sở hữu năm {latest_year}",
        )

        fig_liabilities.update_traces(textposition="inside", textinfo="percent+label")

        st.plotly_chart(fig_liabilities, use_container_width=True)

with tab2:
    st.header("Phân tích tăng trưởng")

    # Prepare growth data
    years = bs_df["yearReport"].unique()
    years.sort()

    if len(years) >= 2:
        growth_data = []

        for i in range(1, len(years)):
            current_year = years[i]
            prev_year = years[i - 1]

            current_is = is_df[is_df["yearReport"] == current_year].iloc[0]
            prev_is = is_df[is_df["yearReport"] == prev_year].iloc[0]

            current_bs = bs_df[bs_df["yearReport"] == current_year].iloc[0]
            prev_bs = bs_df[bs_df["yearReport"] == prev_year].iloc[0]

            growth_data.append(
                {
                    "Năm": current_year,
                    "Tăng trưởng doanh thu (%)": calc_yoy_growth(
                        current_is["Revenue (Bn. VND)"], prev_is["Revenue (Bn. VND)"]
                    ),
                    "Tăng trưởng lợi nhuận (%)": calc_yoy_growth(
                        current_is["Net Profit For the Year"], prev_is["Net Profit For the Year"]
                    ),
                    "Tăng trưởng tài sản (%)": calc_yoy_growth(
                        current_bs["TOTAL ASSETS (Bn. VND)"], prev_bs["TOTAL ASSETS (Bn. VND)"]
                    ),
                    "Tăng trưởng vốn CSH (%)": calc_yoy_growth(
                        current_bs["OWNER'S EQUITY(Bn.VND)"], prev_bs["OWNER'S EQUITY(Bn.VND)"]
                    ),
                }
            )

        growth_df = pd.DataFrame(growth_data)

        # Create a multi-line chart for growth metrics
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=growth_df["Năm"],
                y=growth_df["Tăng trưởng doanh thu (%)"],
                mode="lines+markers",
                name="Tăng trưởng doanh thu (%)",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=growth_df["Năm"],
                y=growth_df["Tăng trưởng lợi nhuận (%)"],
                mode="lines+markers",
                name="Tăng trưởng lợi nhuận (%)",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=growth_df["Năm"],
                y=growth_df["Tăng trưởng tài sản (%)"],
                mode="lines+markers",
                name="Tăng trưởng tài sản (%)",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=growth_df["Năm"],
                y=growth_df["Tăng trưởng vốn CSH (%)"],
                mode="lines+markers",
                name="Tăng trưởng vốn CSH (%)",
            )
        )

        fig.update_layout(
            title="Tỷ lệ tăng trưởng các chỉ số tài chính qua các năm",
            xaxis_title="Năm",
            yaxis_title="Tăng trưởng (%)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        st.plotly_chart(fig, use_container_width=True)

        # Growth table
        st.subheader("Bảng tăng trưởng chi tiết")
        st.dataframe(
            growth_df.style.format(
                {
                    "Tăng trưởng doanh thu (%)": "{:.2f}%",
                    "Tăng trưởng lợi nhuận (%)": "{:.2f}%",
                    "Tăng trưởng tài sản (%)": "{:.2f}%",
                    "Tăng trưởng vốn CSH (%)": "{:.2f}%",
                }
            )
        )

    # Revenue breakdown analysis
    st.subheader("Phân tích doanh thu và chi phí")

    # Prepare data for stacked bar chart
    yearly_revenue_cost = []

    for year in years:
        year_is = is_df[is_df["yearReport"] == year].iloc[0]

        yearly_revenue_cost.append(
            {
                "Năm": year,
                "Doanh thu thuần": year_is["Net Sales"] / 1e9,
                "Giá vốn hàng bán": year_is["Cost of Sales"]
                / abs(1e9),  # Make positive for visualization
                "Chi phí tài chính": year_is["Financial Expenses"] / abs(1e9),
                "Chi phí bán hàng": year_is["Selling Expenses"] / abs(1e9),
                "Chi phí quản lý": year_is["General & Admin Expenses"] / abs(1e9),
            }
        )

    rev_cost_df = pd.DataFrame(yearly_revenue_cost)

    # Stacked bar chart for revenue and costs
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=rev_cost_df["Năm"],
            y=rev_cost_df["Doanh thu thuần"],
            name="Doanh thu thuần",
            marker_color="green",
        )
    )

    # Create a secondary y-axis figure for cost breakdown
    fig_costs = go.Figure()

    fig_costs.add_trace(
        go.Bar(
            x=rev_cost_df["Năm"],
            y=rev_cost_df["Giá vốn hàng bán"],
            name="Giá vốn hàng bán",
            marker_color="red",
        )
    )

    fig_costs.add_trace(
        go.Bar(
            x=rev_cost_df["Năm"],
            y=rev_cost_df["Chi phí tài chính"],
            name="Chi phí tài chính",
            marker_color="orange",
        )
    )

    fig_costs.add_trace(
        go.Bar(
            x=rev_cost_df["Năm"],
            y=rev_cost_df["Chi phí bán hàng"],
            name="Chi phí bán hàng",
            marker_color="blue",
        )
    )

    fig_costs.add_trace(
        go.Bar(
            x=rev_cost_df["Năm"],
            y=rev_cost_df["Chi phí quản lý"],
            name="Chi phí quản lý",
            marker_color="purple",
        )
    )

    fig_costs.update_layout(
        barmode="stack",
        title="Cơ cấu chi phí theo năm",
        xaxis_title="Năm",
        yaxis_title="Giá trị (Tỷ VND)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    col1, col2 = st.columns(2)

    with col1:
        fig.update_layout(
            title="Doanh thu thuần theo năm",
            xaxis_title="Năm",
            yaxis_title="Doanh thu thuần (Tỷ VND)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.plotly_chart(fig_costs, use_container_width=True)

with tab3:
    st.header("Phân tích biên lợi nhuận")

    # Calculate profit margins
    profit_margins = []

    for year in years:
        year_is = is_df[is_df["yearReport"] == year].iloc[0]

        if year_is["Net Sales"] != 0:  # Avoid division by zero
            gross_margin = (year_is["Gross Profit"] / year_is["Net Sales"]) * 100
            operating_margin = (year_is["Operating Profit/Loss"] / year_is["Net Sales"]) * 100
            net_margin = (year_is["Net Profit For the Year"] / year_is["Net Sales"]) * 100

            profit_margins.append(
                {
                    "Năm": year,
                    "Biên lợi nhuận gộp (%)": gross_margin,
                    "Biên lợi nhuận hoạt động (%)": operating_margin,
                    "Biên lợi nhuận ròng (%)": net_margin,
                }
            )

    margins_df = pd.DataFrame(profit_margins)

    # Create line chart for profit margins
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=margins_df["Năm"],
            y=margins_df["Biên lợi nhuận gộp (%)"],
            mode="lines+markers",
            name="Biên lợi nhuận gộp (%)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=margins_df["Năm"],
            y=margins_df["Biên lợi nhuận hoạt động (%)"],
            mode="lines+markers",
            name="Biên lợi nhuận hoạt động (%)",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=margins_df["Năm"],
            y=margins_df["Biên lợi nhuận ròng (%)"],
            mode="lines+markers",
            name="Biên lợi nhuận ròng (%)",
        )
    )

    fig.update_layout(
        title="Biên lợi nhuận qua các năm",
        xaxis_title="Năm",
        yaxis_title="Biên lợi nhuận (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Profit margins table
    st.subheader("Bảng biên lợi nhuận chi tiết")
    st.dataframe(
        margins_df.style.format(
            {
                "Biên lợi nhuận gộp (%)": "{:.2f}%",
                "Biên lợi nhuận hoạt động (%)": "{:.2f}%",
                "Biên lợi nhuận ròng (%)": "{:.2f}%",
            }
        )
    )

    # ROA and ROE analysis
    st.subheader("Phân tích hiệu quả sử dụng tài sản và vốn")

    # Calculate ROA and ROE
    roa_roe = []

    for year in years:
        year_is = is_df[is_df["yearReport"] == year].iloc[0]
        year_bs = bs_df[bs_df["yearReport"] == year].iloc[0]

        net_profit = year_is["Net Profit For the Year"]
        total_assets = year_bs["TOTAL ASSETS (Bn. VND)"]
        equity = year_bs["OWNER'S EQUITY(Bn.VND)"]

        if total_assets != 0 and equity != 0:
            roa = (net_profit / total_assets) * 100
            roe = (net_profit / equity) * 100

            roa_roe.append({"Năm": year, "ROA (%)": roa, "ROE (%)": roe})

    roa_roe_df = pd.DataFrame(roa_roe)

    # Create line chart for ROA and ROE
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=roa_roe_df["Năm"], y=roa_roe_df["ROA (%)"], mode="lines+markers", name="ROA (%)"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=roa_roe_df["Năm"], y=roa_roe_df["ROE (%)"], mode="lines+markers", name="ROE (%)"
        )
    )

    fig.update_layout(
        title="ROA và ROE qua các năm",
        xaxis_title="Năm",
        yaxis_title="Tỷ lệ (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Phân tích tài sản và nợ")

    # Asset and Liability trend
    st.subheader("Xu hướng tài sản và nợ")

    # Prepare data for asset and liability trends
    asset_liability_trend = []

    for year in years:
        year_bs = bs_df[bs_df["yearReport"] == year].iloc[0]

        asset_liability_trend.append(
            {
                "Năm": year,
                "Tổng tài sản": year_bs["TOTAL ASSETS (Bn. VND)"] / 1e9,
                "Tài sản ngắn hạn": year_bs["CURRENT ASSETS (Bn. VND)"] / 1e9,
                "Tài sản dài hạn": year_bs["LONG-TERM ASSETS (Bn. VND)"] / 1e9,
                "Tổng nợ": year_bs["LIABILITIES (Bn. VND)"] / 1e9,
                "Nợ ngắn hạn": year_bs["Current liabilities (Bn. VND)"] / 1e9,
                "Nợ dài hạn": year_bs["Long-term liabilities (Bn. VND)"] / 1e9,
                "Vốn chủ sở hữu": year_bs["OWNER'S EQUITY(Bn.VND)"] / 1e9,
            }
        )

    trend_df = pd.DataFrame(asset_liability_trend)

    # Create area chart for assets
    fig1 = go.Figure()

    fig1.add_trace(
        go.Scatter(
            x=trend_df["Năm"],
            y=trend_df["Tài sản ngắn hạn"],
            name="Tài sản ngắn hạn",
            stackgroup="assets",
        )
    )

    fig1.add_trace(
        go.Scatter(
            x=trend_df["Năm"],
            y=trend_df["Tài sản dài hạn"],
            name="Tài sản dài hạn",
            stackgroup="assets",
        )
    )

    fig1.update_layout(
        title="Cơ cấu tài sản qua các năm",
        xaxis_title="Năm",
        yaxis_title="Giá trị (Tỷ VND)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig1, use_container_width=True)

    # Create area chart for liabilities and equity
    fig2 = go.Figure()

    fig2.add_trace(
        go.Scatter(
            x=trend_df["Năm"],
            y=trend_df["Nợ ngắn hạn"],
            name="Nợ ngắn hạn",
            stackgroup="liab_equity",
        )
    )

    fig2.add_trace(
        go.Scatter(
            x=trend_df["Năm"],
            y=trend_df["Nợ dài hạn"],
            name="Nợ dài hạn",
            stackgroup="liab_equity",
        )
    )

    fig2.add_trace(
        go.Scatter(
            x=trend_df["Năm"],
            y=trend_df["Vốn chủ sở hữu"],
            name="Vốn chủ sở hữu",
            stackgroup="liab_equity",
        )
    )

    fig2.update_layout(
        title="Cơ cấu nợ và vốn chủ sở hữu qua các năm",
        xaxis_title="Năm",
        yaxis_title="Giá trị (Tỷ VND)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Debt ratios
    st.subheader("Phân tích tỷ lệ nợ và khả năng thanh toán")

    # Calculate debt ratios
    debt_ratios = []

    for year in years:
        year_bs = bs_df[bs_df["yearReport"] == year].iloc[0]

        total_assets = year_bs["TOTAL ASSETS (Bn. VND)"]
        total_liabilities = year_bs["LIABILITIES (Bn. VND)"]
        current_assets = year_bs["CURRENT ASSETS (Bn. VND)"]
        current_liabilities = year_bs["Current liabilities (Bn. VND)"]

        if total_assets != 0 and current_liabilities != 0:
            debt_ratio = (total_liabilities / total_assets) * 100
            current_ratio = current_assets / current_liabilities
            quick_ratio = (current_assets - year_bs["Net Inventories"]) / current_liabilities

            debt_ratios.append(
                {
                    "Năm": year,
                    "Tỷ lệ nợ/tài sản (%)": debt_ratio,
                    "Tỷ lệ thanh toán hiện hành": current_ratio,
                    "Tỷ lệ thanh toán nhanh": quick_ratio,
                }
            )

    debt_ratios_df = pd.DataFrame(debt_ratios)

    # Create two subplot figures
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add debt ratio on primary y-axis
    fig.add_trace(
        go.Scatter(
            x=debt_ratios_df["Năm"],
            y=debt_ratios_df["Tỷ lệ nợ/tài sản (%)"],
            mode="lines+markers",
            name="Tỷ lệ nợ/tài sản (%)",
        ),
        secondary_y=False,
    )

    # Add liquidity ratios on secondary y-axis
    fig.add_trace(
        go.Scatter(
            x=debt_ratios_df["Năm"],
            y=debt_ratios_df["Tỷ lệ thanh toán hiện hành"],
            mode="lines+markers",
            name="Tỷ lệ thanh toán hiện hành",
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=debt_ratios_df["Năm"],
            y=debt_ratios_df["Tỷ lệ thanh toán nhanh"],
            mode="lines+markers",
            name="Tỷ lệ thanh toán nhanh",
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title="Tỷ lệ nợ và khả năng thanh toán",
        xaxis_title="Năm",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig.update_yaxes(title_text="Tỷ lệ nợ/tài sản (%)", secondary_y=False)
    fig.update_yaxes(title_text="Tỷ lệ thanh toán", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.header("Đánh giá chỉ số tài chính")

    # Get latest year data
    latest_year = bs_df["yearReport"].iloc[0]
    latest_bs = bs_df[bs_df["yearReport"] == latest_year].iloc[0]
    latest_is = is_df[is_df["yearReport"] == latest_year].iloc[0]
    latest_cf = cf_df[cf_df["yearReport"] == latest_year].iloc[0]

    # Previous year data
    prev_year = bs_df["yearReport"].iloc[1]
    prev_bs = bs_df[bs_df["yearReport"] == prev_year].iloc[0]
    prev_is = is_df[is_df["yearReport"] == prev_year].iloc[0]

    # Calculate key metrics
with tab5:
    st.header("Đánh giá chỉ số tài chính")

    # Get latest year data
    latest_year = bs_df["yearReport"].iloc[0]
    latest_bs = bs_df[bs_df["yearReport"] == latest_year].iloc[0]
    latest_is = is_df[is_df["yearReport"] == latest_year].iloc[0]
    latest_cf = cf_df[cf_df["yearReport"] == latest_year].iloc[0]

    # Previous year data
    prev_year = bs_df["yearReport"].iloc[1]
    prev_bs = bs_df[bs_df["yearReport"] == prev_year].iloc[0]
    prev_is = is_df[is_df["yearReport"] == prev_year].iloc[0]

    # Calculate key metrics
    revenue_growth = calc_yoy_growth(latest_is["Revenue (Bn. VND)"], prev_is["Revenue (Bn. VND)"])
    profit_growth = calc_yoy_growth(
        latest_is["Net Profit For the Year"], prev_is["Net Profit For the Year"]
    )

    # Calculate profitability ratios
    gross_margin = (latest_is["Gross Profit"] / latest_is["Net Sales"]) * 100
    net_margin = (latest_is["Net Profit For the Year"] / latest_is["Net Sales"]) * 100

    # Calculate ROA and ROE
    roa = (latest_is["Net Profit For the Year"] / latest_bs["TOTAL ASSETS (Bn. VND)"]) * 100
    roe = (latest_is["Net Profit For the Year"] / latest_bs["OWNER'S EQUITY(Bn.VND)"]) * 100

    # Calculate liquidity ratios
    current_ratio = (
        latest_bs["CURRENT ASSETS (Bn. VND)"] / latest_bs["Current liabilities (Bn. VND)"]
    )
    quick_ratio = (
        latest_bs["CURRENT ASSETS (Bn. VND)"] - latest_bs["Net Inventories"]
    ) / latest_bs["Current liabilities (Bn. VND)"]

    # Calculate debt ratios
    debt_ratio = (latest_bs["LIABILITIES (Bn. VND)"] / latest_bs["TOTAL ASSETS (Bn. VND)"]) * 100
    debt_to_equity = latest_bs["LIABILITIES (Bn. VND)"] / latest_bs["OWNER'S EQUITY(Bn.VND)"]

    # Calculate cash flow metrics
    operating_cash_flow_to_revenue = (
        latest_cf["Net cash inflows/outflows from operating activities"]
        / latest_is["Revenue (Bn. VND)"]
    )

    # Calculate efficiency ratios (if available)
    # Inventory turnover
    if "Cost of Sales" in is_df.columns:
        inventory_turnover = abs(latest_is["Cost of Sales"]) / latest_bs["Net Inventories"]
    else:
        inventory_turnover = None

    # Receivables turnover
    if "Net Sales" in is_df.columns and "Accounts receivable (Bn. VND)" in bs_df.columns:
        receivables_turnover = latest_is["Net Sales"] / latest_bs["Accounts receivable (Bn. VND)"]
    else:
        receivables_turnover = None

    # Create assessment function
    def assess_metric(
        value, threshold_poor, threshold_average, threshold_good, higher_is_better=True
    ):
        if higher_is_better:
            if value >= threshold_good:
                return "Tốt", "green"
            elif value >= threshold_average:
                return "Trung bình", "orange"
            else:
                return "Kém", "red"
        else:
            if value <= threshold_good:
                return "Tốt", "green"
            elif value <= threshold_average:
                return "Trung bình", "orange"
            else:
                return "Kém", "red"

    # Create metrics dictionary with assessment criteria
    metrics = {
        "Tăng trưởng doanh thu (%)": {
            "value": revenue_growth,
            "thresholds": (5, 15, 25),  # poor, average, good
            "higher_is_better": True,
            "explanation": "Tăng trưởng doanh thu là chỉ số đo lường mức độ tăng trưởng của doanh thu so với kỳ trước. Tăng trưởng doanh thu cao thể hiện khả năng mở rộng thị phần và tăng năng lực bán hàng. Tốt khi > 15%.",
        },
        "Tăng trưởng lợi nhuận (%)": {
            "value": profit_growth,
            "thresholds": (5, 15, 30),
            "higher_is_better": True,
            "explanation": "Tăng trưởng lợi nhuận đo lường mức độ tăng của lợi nhuận ròng so với kỳ trước. Tăng trưởng lợi nhuận cao thể hiện khả năng cải thiện hiệu quả hoạt động. Tốt khi > 15%.",
        },
        "Biên lợi nhuận gộp (%)": {
            "value": gross_margin,
            "thresholds": (15, 25, 35),
            "higher_is_better": True,
            "explanation": "Biên lợi nhuận gộp cho biết phần trăm doanh thu còn lại sau khi trừ giá vốn hàng bán. Chỉ số này cao cho thấy công ty có khả năng kiểm soát chi phí sản xuất tốt. Tốt khi > 25%.",
        },
        "Biên lợi nhuận ròng (%)": {
            "value": net_margin,
            "thresholds": (5, 10, 15),
            "higher_is_better": True,
            "explanation": "Biên lợi nhuận ròng cho biết phần trăm doanh thu được chuyển thành lợi nhuận sau thuế. Tốt khi > 10%.",
        },
        "ROA (%)": {
            "value": roa,
            "thresholds": (3, 8, 12),
            "higher_is_better": True,
            "explanation": "Tỷ suất sinh lời trên tổng tài sản (ROA) đo lường hiệu quả sử dụng tài sản để tạo ra lợi nhuận. Tốt khi > 8%.",
        },
        "ROE (%)": {
            "value": roe,
            "thresholds": (10, 15, 20),
            "higher_is_better": True,
            "explanation": "Tỷ suất sinh lời trên vốn chủ sở hữu (ROE) đo lường hiệu quả sử dụng vốn chủ sở hữu để tạo ra lợi nhuận. Tốt khi > 15%.",
        },
        "Tỷ lệ thanh toán hiện hành": {
            "value": current_ratio,
            "thresholds": (1, 1.5, 2),
            "higher_is_better": True,
            "explanation": "Tỷ lệ thanh toán hiện hành đo lường khả năng thanh toán các khoản nợ ngắn hạn bằng tài sản ngắn hạn. Tốt khi > 1.5.",
        },
        "Tỷ lệ thanh toán nhanh": {
            "value": quick_ratio,
            "thresholds": (0.5, 0.8, 1),
            "higher_is_better": True,
            "explanation": "Tỷ lệ thanh toán nhanh đo lường khả năng thanh toán nợ ngắn hạn bằng các tài sản có tính thanh khoản cao (không tính hàng tồn kho). Tốt khi > 0.8.",
        },
        "Tỷ lệ nợ trên tài sản (%)": {
            "value": debt_ratio,
            "thresholds": (60, 40, 30),
            "higher_is_better": False,
            "explanation": "Tỷ lệ nợ trên tài sản cho biết phần trăm tài sản được tài trợ bởi nợ. Chỉ số này thấp cho thấy rủi ro tài chính thấp. Tốt khi < 40%.",
        },
        "Tỷ lệ nợ trên vốn chủ sở hữu": {
            "value": debt_to_equity,
            "thresholds": (2, 1, 0.5),
            "higher_is_better": False,
            "explanation": "Tỷ lệ nợ trên vốn chủ sở hữu đo lường mức độ sử dụng đòn bẩy tài chính. Chỉ số này thấp thể hiện rủi ro tài chính thấp. Tốt khi < 1.",
        },
        "Dòng tiền từ hoạt động kinh doanh trên doanh thu": {
            "value": operating_cash_flow_to_revenue,
            "thresholds": (0.05, 0.1, 0.15),
            "higher_is_better": True,
            "explanation": "Tỷ lệ dòng tiền từ hoạt động kinh doanh trên doanh thu đo lường khả năng chuyển đổi doanh thu thành tiền mặt. Tốt khi > 0.1.",
        },
    }

    # Add inventory and receivables turnover if available
    if inventory_turnover is not None:
        metrics["Vòng quay hàng tồn kho"] = {
            "value": inventory_turnover,
            "thresholds": (3, 6, 10),
            "higher_is_better": True,
            "explanation": "Vòng quay hàng tồn kho đo lường số lần công ty bán hết và thay thế hàng tồn kho trong kỳ. Chỉ số cao thể hiện quản lý tồn kho hiệu quả. Tốt khi > 6.",
        }

    if receivables_turnover is not None:
        metrics["Vòng quay khoản phải thu"] = {
            "value": receivables_turnover,
            "thresholds": (4, 8, 12),
            "higher_is_better": True,
            "explanation": "Vòng quay khoản phải thu đo lường hiệu quả trong việc thu hồi các khoản phải thu. Chỉ số cao cho thấy khả năng thu hồi nợ tốt. Tốt khi > 8.",
        }

    # Create assessment table
    assessment_data = []

    for metric_name, metric_info in metrics.items():
        assessment, color = assess_metric(
            metric_info["value"],
            metric_info["thresholds"][0],
            metric_info["thresholds"][1],
            metric_info["thresholds"][2],
            metric_info["higher_is_better"],
        )

        assessment_data.append(
            {
                "Chỉ số": metric_name,
                "Giá trị": metric_info["value"],
                "Đánh giá": assessment,
                "Màu": color,
                "Giải thích": metric_info["explanation"],
            }
        )

    assessment_df = pd.DataFrame(assessment_data)

    # Display assessment table with colors
    st.subheader(f"Bảng đánh giá chỉ số tài chính năm {latest_year}")

    # Format the metrics for display
    display_df = assessment_df.copy()

    # Format values based on metric type
    for i, row in display_df.iterrows():
        if "(%)" in row["Chỉ số"] or row["Chỉ số"] in [
            "ROA (%)",
            "ROE (%)",
            "Tỷ lệ nợ trên tài sản (%)",
        ]:
            display_df.at[i, "Giá trị"] = f"{row['Giá trị']:.2f}%"
        elif row["Chỉ số"] in [
            "Tỷ lệ thanh toán hiện hành",
            "Tỷ lệ thanh toán nhanh",
            "Tỷ lệ nợ trên vốn chủ sở hữu",
        ]:
            display_df.at[i, "Giá trị"] = f"{row['Giá trị']:.2f}"
        elif row["Chỉ số"] in ["Vòng quay hàng tồn kho", "Vòng quay khoản phải thu"]:
            display_df.at[i, "Giá trị"] = f"{row['Giá trị']:.2f} lần"
        else:
            display_df.at[i, "Giá trị"] = f"{row['Giá trị']:.2f}"

    # Use st.dataframe to display the table
    st.dataframe(
        display_df[["Chỉ số", "Giá trị", "Đánh giá", "Giải thích"]],
        column_config={
            "Chỉ số": st.column_config.TextColumn("Chỉ số"),
            "Giá trị": st.column_config.TextColumn("Giá trị"),
            "Đánh giá": st.column_config.TextColumn("Đánh giá"),
            "Giải thích": st.column_config.TextColumn("Giải thích", width="large"),
        },
        hide_index=True,
        use_container_width=True,
    )

    # Create visualization for assessment
    st.subheader("Biểu đồ radar - Đánh giá tổng quan các chỉ số tài chính")

    # Prepare data for radar chart - normalize values
    radar_metrics = {
        "Tăng trưởng": revenue_growth / 30 * 100,  # Normalize to 0-100 scale
        "Lợi nhuận": net_margin / 15 * 100,
        "ROA": roa / 12 * 100,
        "ROE": roe / 20 * 100,
        "Thanh khoản": current_ratio / 2 * 100,
        "Cấu trúc vốn": (1 - debt_ratio / 100) * 100,  # Lower debt ratio is better
        "Dòng tiền": operating_cash_flow_to_revenue / 0.15 * 100,
    }

    # Cap values at 100 (100%)
    for key in radar_metrics:
        radar_metrics[key] = min(radar_metrics[key], 100)

    # Create radar chart
    categories = list(radar_metrics.keys())
    values = list(radar_metrics.values())

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(r=values, theta=categories, fill="toself", name=f"Năm {latest_year}")
    )

    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)

    st.plotly_chart(fig, use_container_width=True)

    # Summary assessment
    st.subheader("Tổng hợp đánh giá")

    # Count ratings
    ratings = assessment_df["Đánh giá"].value_counts()
    good_count = ratings.get("Tốt", 0)
    avg_count = ratings.get("Trung bình", 0)
    poor_count = ratings.get("Kém", 0)

    # Calculate overall score (3 points for good, 2 for average, 1 for poor)
    total_metrics = len(assessment_df)
    overall_score = (good_count * 3 + avg_count * 2 + poor_count * 1) / (total_metrics * 3) * 100

    # Display donut chart of ratings distribution
    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Tốt", "Trung bình", "Kém"],
                values=[good_count, avg_count, poor_count],
                hole=0.3,
                marker_colors=["green", "orange", "red"],
            )
        ]
    )

    fig.update_layout(title="Phân phối đánh giá các chỉ số")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Overall assessment text
        if overall_score >= 80:
            assessment_text = "Tình hình tài chính rất tốt"
            emoji = "🌟"
        elif overall_score >= 60:
            assessment_text = "Tình hình tài chính tốt"
            emoji = "✅"
        elif overall_score >= 40:
            assessment_text = "Tình hình tài chính trung bình"
            emoji = "⚠️"
        else:
            assessment_text = "Tình hình tài chính yếu"
            emoji = "❌"

        st.markdown(
            f"""
        ## Đánh giá tổng thể {emoji}
        
        **Điểm số tổng thể: {overall_score:.1f}%**
        
        **Kết luận: {assessment_text}**
        
        ### Điểm mạnh:
        """
        )

        # Get strengths (good metrics)
        strengths = assessment_df[assessment_df["Đánh giá"] == "Tốt"]["Chỉ số"].tolist()
        if strengths:
            for strength in strengths:
                st.markdown(f"- {strength}")
        else:
            st.markdown("- Không có điểm mạnh nổi bật")

        st.markdown("### Điểm yếu cần cải thiện:")

        # Get weaknesses (poor metrics)
        weaknesses = assessment_df[assessment_df["Đánh giá"] == "Kém"]["Chỉ số"].tolist()
        if weaknesses:
            for weakness in weaknesses:
                st.markdown(f"- {weakness}")
        else:
            st.markdown("- Không có điểm yếu đáng kể")

    # Add cash flow analysis
    st.header("Phân tích dòng tiền")

    # Prepare cash flow data
    cash_flow_data = []

    for year in years:
        year_cf = cf_df[cf_df["yearReport"] == year].iloc[0]

        cash_flow_data.append(
            {
                "Năm": year,
                "Dòng tiền từ hoạt động kinh doanh": year_cf[
                    "Net cash inflows/outflows from operating activities"
                ]
                / 1e9,
                "Dòng tiền từ hoạt động đầu tư": year_cf[
                    "Net Cash Flows from Investing Activities"
                ]
                / 1e9,
                "Dòng tiền từ hoạt động tài chính": year_cf["Cash flows from financial activities"]
                / 1e9,
                "Tăng/giảm tiền thuần": year_cf[
                    "Net increase/decrease in cash and cash equivalents"
                ]
                / 1e9,
            }
        )

    cf_df_plot = pd.DataFrame(cash_flow_data)

    # Create cash flow waterfall chart for latest year
    latest_cf = cf_df_plot[cf_df_plot["Năm"] == latest_year].iloc[0]

    waterfall_data = {
        "Chỉ số": [
            "Tiền đầu kỳ",
            "Hoạt động kinh doanh",
            "Hoạt động đầu tư",
            "Hoạt động tài chính",
            "Tiền cuối kỳ",
        ],
        "Giá trị": [
            latest_cf["Tăng/giảm tiền thuần"]
            - latest_cf["Dòng tiền từ hoạt động kinh doanh"]
            - latest_cf["Dòng tiền từ hoạt động đầu tư"]
            - latest_cf["Dòng tiền từ hoạt động tài chính"],
            latest_cf["Dòng tiền từ hoạt động kinh doanh"],
            latest_cf["Dòng tiền từ hoạt động đầu tư"],
            latest_cf["Dòng tiền từ hoạt động tài chính"],
            latest_cf["Tăng/giảm tiền thuần"]
            + (
                latest_cf["Tăng/giảm tiền thuần"]
                - latest_cf["Dòng tiền từ hoạt động kinh doanh"]
                - latest_cf["Dòng tiền từ hoạt động đầu tư"]
                - latest_cf["Dòng tiền từ hoạt động tài chính"]
            ),
        ],
    }

    waterfall_df = pd.DataFrame(waterfall_data)

    # Create waterfall chart
    fig = go.Figure(
        go.Waterfall(
            name="Dòng tiền năm " + str(latest_year),
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "total"],
            x=waterfall_df["Chỉ số"],
            textposition="outside",
            text=waterfall_df["Giá trị"].round(2),
            y=waterfall_df["Giá trị"],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
        )
    )

    fig.update_layout(title=f"Phân tích dòng tiền năm {latest_year} (Tỷ VND)", showlegend=False)

    st.plotly_chart(fig, use_container_width=True)

    # Create cash flow trend chart
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=cf_df_plot["Năm"],
            y=cf_df_plot["Dòng tiền từ hoạt động kinh doanh"],
            name="HĐ kinh doanh",
            marker_color="green",
        )
    )

    fig.add_trace(
        go.Bar(
            x=cf_df_plot["Năm"],
            y=cf_df_plot["Dòng tiền từ hoạt động đầu tư"],
            name="HĐ đầu tư",
            marker_color="red",
        )
    )

    fig.add_trace(
        go.Bar(
            x=cf_df_plot["Năm"],
            y=cf_df_plot["Dòng tiền từ hoạt động tài chính"],
            name="HĐ tài chính",
            marker_color="blue",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=cf_df_plot["Năm"],
            y=cf_df_plot["Tăng/giảm tiền thuần"],
            name="Tăng/giảm tiền thuần",
            marker_color="black",
            mode="lines+markers",
        )
    )

    fig.update_layout(
        title="Xu hướng dòng tiền qua các năm",
        xaxis_title="Năm",
        yaxis_title="Tỷ VND",
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)
# Thêm tab phân tích DuPont
with tab6:
    st.header("Phân tích DuPont")

    # Tạo dataframe để lưu dữ liệu phân tích DuPont
    dupont_data = []

    for year in years:
        # Lấy dữ liệu cho năm hiện tại
        current_bs = bs_df[bs_df["yearReport"] == year].iloc[0]
        current_is = is_df[is_df["yearReport"] == year].iloc[0]

        # Tính toán các thành phần phân tích DuPont
        net_profit_margin = current_is["Net Profit For the Year"] / current_is["Net Sales"]
        asset_turnover = current_is["Net Sales"] / current_bs["TOTAL ASSETS (Bn. VND)"]
        equity_multiplier = (
            current_bs["TOTAL ASSETS (Bn. VND)"] / current_bs["OWNER'S EQUITY(Bn.VND)"]
        )

        # ROA và ROE
        roa = net_profit_margin * asset_turnover
        roe = roa * equity_multiplier

        # Phân tích DuPont mở rộng (5 thành phần)
        tax_burden = (
            current_is["Net Profit For the Year"] / current_is["Profit before tax"]
        )  # Gánh nặng thuế
        interest_burden = current_is["Profit before tax"] / (
            current_is["Profit before tax"] + abs(current_is["Interest Expenses"])
        )  # Gánh nặng lãi vay
        operating_margin = (
            current_is["Profit before tax"] + abs(current_is["Interest Expenses"])
        ) / current_is[
            "Net Sales"
        ]  # Biên lợi nhuận hoạt động

        dupont_data.append(
            {
                "Năm": year,
                "Biên lợi nhuận ròng": net_profit_margin,
                "Hiệu suất sử dụng tài sản": asset_turnover,
                "Đòn bẩy tài chính": equity_multiplier,
                "ROA": roa,
                "ROE": roe,
                "Gánh nặng thuế": tax_burden,
                "Gánh nặng lãi vay": interest_burden,
                "Biên lợi nhuận hoạt động": operating_margin,
            }
        )

    dupont_df = pd.DataFrame(dupont_data)

    # Hiển thị 2 bảng: DuPont cơ bản và DuPont mở rộng
    st.subheader("1. Phân tích DuPont cơ bản")

    basic_dupont = dupont_df.copy()

    # Format các cột phần trăm
    for col in ["Biên lợi nhuận ròng", "ROA", "ROE"]:
        basic_dupont[col] = basic_dupont[col].apply(lambda x: f"{x*100:.2f}%")

    # Format các cột tỷ số
    for col in ["Hiệu suất sử dụng tài sản", "Đòn bẩy tài chính"]:
        basic_dupont[col] = basic_dupont[col].apply(lambda x: f"{x:.2f}")

    st.dataframe(
        basic_dupont[
            [
                "Năm",
                "Biên lợi nhuận ròng",
                "Hiệu suất sử dụng tài sản",
                "Đòn bẩy tài chính",
                "ROA",
                "ROE",
            ]
        ],
        column_config={
            "Năm": st.column_config.TextColumn("Năm"),
            "Biên lợi nhuận ròng": st.column_config.TextColumn("Biên lợi nhuận ròng"),
            "Hiệu suất sử dụng tài sản": st.column_config.TextColumn("Hiệu suất sử dụng tài sản"),
            "Đòn bẩy tài chính": st.column_config.TextColumn("Đòn bẩy tài chính"),
            "ROA": st.column_config.TextColumn("ROA"),
            "ROE": st.column_config.TextColumn("ROE"),
        },
        hide_index=True,
        use_container_width=True,
    )

    # Thêm phần giải thích DuPont cơ bản
    with st.expander("Giải thích phân tích DuPont cơ bản"):
        st.markdown(
            """
        ### Phân tích DuPont cơ bản
        Phân tích DuPont chia ROE thành 3 thành phần chính:
        
        **ROE = Biên lợi nhuận ròng × Hiệu suất sử dụng tài sản × Đòn bẩy tài chính**
        
        - **Biên lợi nhuận ròng** = Lợi nhuận ròng / Doanh thu thuần
          - Đo lường khả năng sinh lời từ doanh thu
          - Cao hơn thể hiện hiệu quả kiểm soát chi phí tốt
        
        - **Hiệu suất sử dụng tài sản** = Doanh thu thuần / Tổng tài sản
          - Đo lường hiệu quả sử dụng tài sản để tạo doanh thu
          - Cao hơn thể hiện sử dụng tài sản hiệu quả
        
        - **Đòn bẩy tài chính** = Tổng tài sản / Vốn chủ sở hữu
          - Đo lường mức độ sử dụng nợ để tài trợ cho tài sản
          - Cao hơn thể hiện sử dụng nhiều nợ hơn, tiềm ẩn nhiều rủi ro hơn nhưng có thể giúp tăng ROE
        """
        )

    # Hiển thị phân tích DuPont mở rộng
    st.subheader("2. Phân tích DuPont mở rộng")

    extended_dupont = dupont_df.copy()

    # Format các cột phần trăm
    for col in [
        "Biên lợi nhuận ròng",
        "ROA",
        "ROE",
        "Gánh nặng thuế",
        "Gánh nặng lãi vay",
        "Biên lợi nhuận hoạt động",
    ]:
        extended_dupont[col] = extended_dupont[col].apply(lambda x: f"{x*100:.2f}%")

    # Format các cột tỷ số
    for col in ["Hiệu suất sử dụng tài sản", "Đòn bẩy tài chính"]:
        extended_dupont[col] = extended_dupont[col].apply(lambda x: f"{x:.2f}")

    st.dataframe(
        extended_dupont[
            [
                "Năm",
                "Gánh nặng thuế",
                "Gánh nặng lãi vay",
                "Biên lợi nhuận hoạt động",
                "Hiệu suất sử dụng tài sản",
                "Đòn bẩy tài chính",
                "ROE",
            ]
        ],
        column_config={
            "Năm": st.column_config.TextColumn("Năm"),
            "Gánh nặng thuế": st.column_config.TextColumn("Gánh nặng thuế"),
            "Gánh nặng lãi vay": st.column_config.TextColumn("Gánh nặng lãi vay"),
            "Biên lợi nhuận hoạt động": st.column_config.TextColumn("Biên LN hoạt động"),
            "Hiệu suất sử dụng tài sản": st.column_config.TextColumn("Hiệu suất TS"),
            "Đòn bẩy tài chính": st.column_config.TextColumn("Đòn bẩy TC"),
            "ROE": st.column_config.TextColumn("ROE"),
        },
        hide_index=True,
        use_container_width=True,
    )

    # Thêm phần giải thích DuPont mở rộng
    with st.expander("Giải thích phân tích DuPont mở rộng"):
        st.markdown(
            """
        ### Phân tích DuPont mở rộng
        Phân tích DuPont mở rộng chia ROE thành 5 thành phần:
        
        **ROE = Gánh nặng thuế × Gánh nặng lãi vay × Biên lợi nhuận hoạt động × Hiệu suất sử dụng tài sản × Đòn bẩy tài chính**
        
        - **Gánh nặng thuế** = Lợi nhuận ròng / Lợi nhuận trước thuế
          - Tỷ lệ lợi nhuận còn lại sau khi nộp thuế
          - Cao hơn thể hiện gánh nặng thuế thấp hơn (có lợi)
        
        - **Gánh nặng lãi vay** = Lợi nhuận trước thuế / (Lợi nhuận trước thuế + Chi phí lãi vay)
          - Tỷ lệ lợi nhuận còn lại sau khi trả lãi vay
          - Cao hơn thể hiện gánh nặng lãi vay thấp hơn (có lợi)
        
        - **Biên lợi nhuận hoạt động** = (Lợi nhuận trước thuế + Chi phí lãi vay) / Doanh thu thuần
          - Đo lường lợi nhuận từ hoạt động kinh doanh chính trước chi phí tài chính và thuế
          - Cao hơn thể hiện hiệu quả hoạt động kinh doanh tốt hơn
        """
        )

    # Biểu đồ xu hướng ROE và các thành phần
    st.subheader("3. Biểu đồ phân tích xu hướng DuPont")

    # Chuyển đổi dữ liệu về float để vẽ biểu đồ
    numeric_dupont_df = dupont_df.copy()

    # Tạo biểu đồ ROE và các thành phần
    fig1 = go.Figure()

    # Thêm đường ROE
    fig1.add_trace(
        go.Scatter(
            x=numeric_dupont_df["Năm"],
            y=numeric_dupont_df["ROE"] * 100,
            mode="lines+markers",
            name="ROE (%)",
            line=dict(color="blue", width=3),
        )
    )

    # Thêm đường ROA
    fig1.add_trace(
        go.Scatter(
            x=numeric_dupont_df["Năm"],
            y=numeric_dupont_df["ROA"] * 100,
            mode="lines+markers",
            name="ROA (%)",
            line=dict(color="green", width=2),
        )
    )

    # Cập nhật layout
    fig1.update_layout(
        title="Xu hướng ROE và ROA qua các năm",
        xaxis_title="Năm",
        yaxis_title="%",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig1, use_container_width=True)

    # Tạo biểu đồ cho các thành phần cơ bản của DuPont
    fig2 = go.Figure()

    # Đòn bẩy tài chính (sử dụng trục y thứ hai)
    fig2.add_trace(
        go.Scatter(
            x=numeric_dupont_df["Năm"],
            y=numeric_dupont_df["Đòn bẩy tài chính"],
            mode="lines+markers",
            name="Đòn bẩy tài chính",
            line=dict(color="red", width=2),
            yaxis="y2",
        )
    )

    # Hiệu suất sử dụng tài sản (sử dụng trục y thứ hai)
    fig2.add_trace(
        go.Scatter(
            x=numeric_dupont_df["Năm"],
            y=numeric_dupont_df["Hiệu suất sử dụng tài sản"],
            mode="lines+markers",
            name="Hiệu suất sử dụng tài sản",
            line=dict(color="purple", width=2),
            yaxis="y2",
        )
    )

    # Biên lợi nhuận ròng (sử dụng trục y thứ nhất)
    fig2.add_trace(
        go.Scatter(
            x=numeric_dupont_df["Năm"],
            y=numeric_dupont_df["Biên lợi nhuận ròng"] * 100,
            mode="lines+markers",
            name="Biên lợi nhuận ròng (%)",
            line=dict(color="orange", width=2),
            yaxis="y",
        )
    )

    # Cập nhật layout với hai trục y
    fig2.update_layout(
        title="Các thành phần cơ bản của phân tích DuPont",
        xaxis_title="Năm",
        yaxis=dict(
            title="Biên lợi nhuận (%)",
            tickfont=dict(color="orange"),
        ),
        yaxis2=dict(
            title="Tỷ số",
            tickfont=dict(color="red"),
            anchor="x",
            overlaying="y",
            side="right",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Tạo biểu đồ cho các thành phần mở rộng của DuPont
    fig3 = go.Figure()

    # Gánh nặng thuế
    fig3.add_trace(
        go.Scatter(
            x=numeric_dupont_df["Năm"],
            y=numeric_dupont_df["Gánh nặng thuế"] * 100,
            mode="lines+markers",
            name="Gánh nặng thuế (%)",
            line=dict(color="green", width=2),
        )
    )

    # Gánh nặng lãi vay
    fig3.add_trace(
        go.Scatter(
            x=numeric_dupont_df["Năm"],
            y=numeric_dupont_df["Gánh nặng lãi vay"] * 100,
            mode="lines+markers",
            name="Gánh nặng lãi vay (%)",
            line=dict(color="blue", width=2),
        )
    )

    # Biên lợi nhuận hoạt động
    fig3.add_trace(
        go.Scatter(
            x=numeric_dupont_df["Năm"],
            y=numeric_dupont_df["Biên lợi nhuận hoạt động"] * 100,
            mode="lines+markers",
            name="Biên lợi nhuận hoạt động (%)",
            line=dict(color="purple", width=2),
        )
    )

    # Cập nhật layout
    fig3.update_layout(
        title="Các thành phần bổ sung trong phân tích DuPont mở rộng",
        xaxis_title="Năm",
        yaxis_title="%",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig3, use_container_width=True)

    # Phân tích sự thay đổi của ROE qua các năm
    st.subheader("4. Phân tích thay đổi ROE")

    # Chọn năm để phân tích
    years_list = sorted(dupont_df["Năm"].unique(), reverse=True)

    if len(years_list) > 1:
        col1, col2 = st.columns(2)

        with col1:
            selected_year = st.selectbox("Chọn năm phân tích:", years_list[:-1])

        with col2:
            # Chọn năm trước đó để so sánh
            prev_year_index = years_list.index(selected_year) + 1
            if prev_year_index < len(years_list):
                prev_year = years_list[prev_year_index]
                st.text(f"So sánh với năm: {prev_year}")

        # Lấy dữ liệu ROE và các thành phần cho 2 năm đã chọn
        current_year_data = dupont_df[dupont_df["Năm"] == selected_year].iloc[0]
        prev_year_data = dupont_df[dupont_df["Năm"] == prev_year].iloc[0]

        # Phân tích sự thay đổi ROE
        roe_current = current_year_data["ROE"]
        roe_prev = prev_year_data["ROE"]
        roe_change = roe_current - roe_prev
        roe_change_percent = (roe_change / abs(roe_prev)) * 100 if roe_prev != 0 else 0

        # Tính toán ảnh hưởng của từng thành phần đến sự thay đổi ROE
        # Cho DuPont cơ bản: ROE = NPM * AT * EM
        npm_current = current_year_data["Biên lợi nhuận ròng"]
        npm_prev = prev_year_data["Biên lợi nhuận ròng"]

        at_current = current_year_data["Hiệu suất sử dụng tài sản"]
        at_prev = prev_year_data["Hiệu suất sử dụng tài sản"]

        em_current = current_year_data["Đòn bẩy tài chính"]
        em_prev = prev_year_data["Đòn bẩy tài chính"]

        # Ảnh hưởng của biên lợi nhuận ròng
        effect_npm = (npm_current - npm_prev) * at_prev * em_prev

        # Ảnh hưởng của hiệu suất sử dụng tài sản
        effect_at = npm_current * (at_current - at_prev) * em_prev

        # Ảnh hưởng của đòn bẩy tài chính
        effect_em = npm_current * at_current * (em_current - em_prev)

        # Tổng các ảnh hưởng (có thể có chênh lệch nhỏ do làm tròn)
        total_effect = effect_npm + effect_at + effect_em

        # Tạo biểu đồ waterfall cho sự thay đổi ROE
        waterfall_data = {
            "Chỉ số": [
                "ROE " + str(prev_year),
                "Biên LN ròng",
                "Hiệu suất TS",
                "Đòn bẩy TC",
                "ROE " + str(selected_year),
            ],
            "Giá trị": [
                roe_prev * 100,
                effect_npm * 100,
                effect_at * 100,
                effect_em * 100,
                roe_current * 100,
            ],
        }

        waterfall_df = pd.DataFrame(waterfall_data)

        # Tạo biểu đồ waterfall
        fig_waterfall = go.Figure(
            go.Waterfall(
                name="Phân tích thay đổi ROE",
                orientation="v",
                measure=["absolute", "relative", "relative", "relative", "total"],
                x=waterfall_df["Chỉ số"],
                textposition="outside",
                text=[f"{val:.2f}%" for val in waterfall_df["Giá trị"]],
                y=waterfall_df["Giá trị"],
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            )
        )

        fig_waterfall.update_layout(
            title=f"Phân tích thay đổi ROE từ năm {prev_year} đến năm {selected_year}",
            showlegend=False,
        )

        st.plotly_chart(fig_waterfall, use_container_width=True)

        # Hiển thị bảng phân tích
        st.markdown(
            f"""
        ### Phân tích sự thay đổi ROE từ {prev_year} đến {selected_year}
        
        - ROE năm {prev_year}: **{roe_prev*100:.2f}%**
        - ROE năm {selected_year}: **{roe_current*100:.2f}%**
        - Thay đổi: **{roe_change*100:.2f}%** ({roe_change_percent:.2f}%)
        
        #### Ảnh hưởng của từng thành phần:
        
        1. **Biên lợi nhuận ròng**: {effect_npm*100:.2f}% ({effect_npm/roe_change*100:.2f}% tổng thay đổi)
        2. **Hiệu suất sử dụng tài sản**: {effect_at*100:.2f}% ({effect_at/roe_change*100:.2f}% tổng thay đổi)
        3. **Đòn bẩy tài chính**: {effect_em*100:.2f}% ({effect_em/roe_change*100:.2f}% tổng thay đổi)
        
        > Lưu ý: Có thể có chênh lệch nhỏ do làm tròn số. Tổng ảnh hưởng: {total_effect*100:.2f}%, ROE thay đổi thực tế: {roe_change*100:.2f}%.
        """
        )

    # Nhận xét và đánh giá DuPont
    st.subheader("5. Nhận xét và đánh giá")

    # Lấy dữ liệu năm gần nhất và năm liền trước
    latest_year = dupont_df["Năm"].iloc[0]
    prev_year = dupont_df["Năm"].iloc[1] if len(dupont_df) > 1 else None

    latest_data = dupont_df[dupont_df["Năm"] == latest_year].iloc[0]
    prev_data = dupont_df[dupont_df["Năm"] == prev_year].iloc[0] if prev_year else None

    # Tính toán % thay đổi của các thành phần
    if prev_year:
        roe_change_pct = (
            ((latest_data["ROE"] - prev_data["ROE"]) / abs(prev_data["ROE"])) * 100
            if prev_data["ROE"] != 0
            else 0
        )
        npm_change_pct = (
            (
                (latest_data["Biên lợi nhuận ròng"] - prev_data["Biên lợi nhuận ròng"])
                / abs(prev_data["Biên lợi nhuận ròng"])
            )
            * 100
            if prev_data["Biên lợi nhuận ròng"] != 0
            else 0
        )
        at_change_pct = (
            (
                (latest_data["Hiệu suất sử dụng tài sản"] - prev_data["Hiệu suất sử dụng tài sản"])
                / abs(prev_data["Hiệu suất sử dụng tài sản"])
            )
            * 100
            if prev_data["Hiệu suất sử dụng tài sản"] != 0
            else 0
        )
        em_change_pct = (
            (
                (latest_data["Đòn bẩy tài chính"] - prev_data["Đòn bẩy tài chính"])
                / abs(prev_data["Đòn bẩy tài chính"])
            )
            * 100
            if prev_data["Đòn bẩy tài chính"] != 0
            else 0
        )

    # Tạo đánh giá tự động
    assessment = ""
    if prev_year:
        # Đánh giá ROE
        if roe_change_pct > 10:
            assessment += f"- **ROE tăng mạnh ({roe_change_pct:.2f}%)**: ROE năm {latest_year} là {latest_data['ROE']*100:.2f}%, tăng đáng kể so với năm {prev_year} ({prev_data['ROE']*100:.2f}%). "
        elif roe_change_pct > 0:
            assessment += f"- **ROE tăng nhẹ ({roe_change_pct:.2f}%)**: ROE năm {latest_year} là {latest_data['ROE']*100:.2f}%, tăng nhẹ so với năm {prev_year} ({prev_data['ROE']*100:.2f}%). "
        elif roe_change_pct > -10:
            assessment += f"- **ROE giảm nhẹ ({roe_change_pct:.2f}%)**: ROE năm {latest_year} là {latest_data['ROE']*100:.2f}%, giảm nhẹ so với năm {prev_year} ({prev_data['ROE']*100:.2f}%). "
        else:
            assessment += f"- **ROE giảm mạnh ({roe_change_pct:.2f}%)**: ROE năm {latest_year} là {latest_data['ROE']*100:.2f}%, giảm đáng kể so với năm {prev_year} ({prev_data['ROE']*100:.2f}%). "

        # Đánh giá các thành phần DuPont
        assessment += "\n\n"

        # Biên lợi nhuận ròng
        if npm_change_pct > 10:
            assessment += f"- **Biên lợi nhuận ròng tăng mạnh ({npm_change_pct:.2f}%)**: từ {prev_data['Biên lợi nhuận ròng']*100:.2f}% lên {latest_data['Biên lợi nhuận ròng']*100:.2f}%, cho thấy công ty đã cải thiện đáng kể khả năng kiểm soát chi phí và tăng hiệu quả hoạt động.\n\n"
        elif npm_change_pct > 0:
            assessment += f"- **Biên lợi nhuận ròng tăng nhẹ ({npm_change_pct:.2f}%)**: từ {prev_data['Biên lợi nhuận ròng']*100:.2f}% lên {latest_data['Biên lợi nhuận ròng']*100:.2f}%, cho thấy công ty duy trì được hiệu quả kiểm soát chi phí.\n\n"
        elif npm_change_pct > -10:
            assessment += f"- **Biên lợi nhuận ròng giảm nhẹ ({npm_change_pct:.2f}%)**: từ {prev_data['Biên lợi nhuận ròng']*100:.2f}% xuống {latest_data['Biên lợi nhuận ròng']*100:.2f}%, cho thấy có áp lực nhẹ về chi phí hoặc giá bán.\n\n"
        else:
            assessment += f"- **Biên lợi nhuận ròng giảm mạnh ({npm_change_pct:.2f}%)**: từ {prev_data['Biên lợi nhuận ròng']*100:.2f}% xuống {latest_data['Biên lợi nhuận ròng']*100:.2f}%, cho thấy áp lực lớn về chi phí hoặc sự sụt giảm của giá bán.\n\n"

        # Hiệu suất sử dụng tài sản
        if at_change_pct > 10:
            assessment += f"- **Hiệu suất sử dụng tài sản tăng mạnh ({at_change_pct:.2f}%)**: từ {prev_data['Hiệu suất sử dụng tài sản']:.2f} lên {latest_data['Hiệu suất sử dụng tài sản']:.2f}, cho thấy công ty sử dụng tài sản hiệu quả hơn để tạo doanh thu.\n\n"
        elif at_change_pct > 0:
            assessment += f"- **Hiệu suất sử dụng tài sản tăng nhẹ ({at_change_pct:.2f}%)**: từ {prev_data['Hiệu suất sử dụng tài sản']:.2f} lên {latest_data['Hiệu suất sử dụng tài sản']:.2f}, cho thấy công ty duy trì được hiệu quả sử dụng tài sản.\n\n"
        elif at_change_pct > -10:
            assessment += f"- **Hiệu suất sử dụng tài sản giảm nhẹ ({at_change_pct:.2f}%)**: từ {prev_data['Hiệu suất sử dụng tài sản']:.2f} xuống {latest_data['Hiệu suất sử dụng tài sản']:.2f}, cho thấy hiệu quả sử dụng tài sản có phần suy giảm.\n\n"
        else:
            assessment += f"- **Hiệu suất sử dụng tài sản giảm mạnh ({at_change_pct:.2f}%)**: từ {prev_data['Hiệu suất sử dụng tài sản']:.2f} xuống {latest_data['Hiệu suất sử dụng tài sản']:.2f}, cho thấy công ty đang gặp khó khăn trong việc tạo doanh thu từ tài sản hiện có.\n\n"

        # Đòn bẩy tài chính
        if em_change_pct > 10:
            assessment += f"- **Đòn bẩy tài chính tăng mạnh ({em_change_pct:.2f}%)**: từ {prev_data['Đòn bẩy tài chính']:.2f} lên {latest_data['Đòn bẩy tài chính']:.2f}, cho thấy công ty đã tăng sử dụng nợ để tài trợ cho tài sản, điều này có thể làm tăng ROE nhưng cũng làm tăng rủi ro tài chính.\n\n"
        elif em_change_pct > 0:
            assessment += f"- **Đòn bẩy tài chính tăng nhẹ ({em_change_pct:.2f}%)**: từ {prev_data['Đòn bẩy tài chính']:.2f} lên {latest_data['Đòn bẩy tài chính']:.2f}, cho thấy công ty có sự điều chỉnh nhẹ trong cơ cấu vốn theo hướng tăng nợ.\n\n"
        elif em_change_pct > -10:
            assessment += f"- **Đòn bẩy tài chính giảm nhẹ ({em_change_pct:.2f}%)**: từ {prev_data['Đòn bẩy tài chính']:.2f} xuống {latest_data['Đòn bẩy tài chính']:.2f}, cho thấy công ty giảm nhẹ tỷ lệ nợ, có thể để giảm rủi ro tài chính.\n\n"
        else:
            assessment += f"- **Đòn bẩy tài chính giảm mạnh ({em_change_pct:.2f}%)**: từ {prev_data['Đòn bẩy tài chính']:.2f} xuống {latest_data['Đòn bẩy tài chính']:.2f}, cho thấy công ty đã giảm đáng kể việc sử dụng nợ, điều này làm giảm rủi ro tài chính nhưng cũng có thể ảnh hưởng đến ROE.\n\n"
    else:
        # Trường hợp chỉ có dữ liệu của 1 năm
        assessment += f"- **ROE năm {latest_year}**: {latest_data['ROE']*100:.2f}%\n\n"
        assessment += (
            f"- **Biên lợi nhuận ròng**: {latest_data['Biên lợi nhuận ròng']*100:.2f}%\n\n"
        )
        assessment += (
            f"- **Hiệu suất sử dụng tài sản**: {latest_data['Hiệu suất sử dụng tài sản']:.2f}\n\n"
        )
        assessment += f"- **Đòn bẩy tài chính**: {latest_data['Đòn bẩy tài chính']:.2f}\n\n"

    # Thêm đánh giá về ROE so với ngành (giả định)
    assessment += "### Kết luận\n\n"

    if latest_data["ROE"] > 0.15:
        assessment += "- **ROE cao**: Công ty có ROE > 15%, thể hiện khả năng sinh lời từ vốn chủ sở hữu ở mức tốt, có thể cao hơn trung bình ngành.\n\n"
    elif latest_data["ROE"] > 0.10:
        assessment += "- **ROE khá**: Công ty có ROE trong khoảng 10-15%, thể hiện khả năng sinh lời từ vốn chủ sở hữu ở mức khá, tương đương trung bình ngành.\n\n"
    elif latest_data["ROE"] > 0.05:
        assessment += "- **ROE trung bình**: Công ty có ROE trong khoảng 5-10%, thể hiện khả năng sinh lời từ vốn chủ sở hữu ở mức trung bình, có thể thấp hơn trung bình ngành.\n\n"
    else:
        assessment += "- **ROE thấp**: Công ty có ROE < 5%, thể hiện khả năng sinh lời từ vốn chủ sở hữu ở mức thấp, có thể đáng kể thấp hơn trung bình ngành.\n\n"

    # Thêm gợi ý cải thiện ROE
    assessment += "### Gợi ý cải thiện ROE\n\n"

    # Gợi ý dựa trên biên lợi nhuận ròng
    if latest_data["Biên lợi nhuận ròng"] < 0.05:
        assessment += "- **Cải thiện biên lợi nhuận ròng**: Xem xét kiểm soát chặt chẽ chi phí, tăng giá bán hoặc tối ưu hóa cơ cấu sản phẩm/dịch vụ với biên lợi nhuận cao hơn.\n\n"

    # Gợi ý dựa trên hiệu suất sử dụng tài sản
    if latest_data["Hiệu suất sử dụng tài sản"] < 0.8:
        assessment += "- **Cải thiện hiệu suất sử dụng tài sản**: Xem xét việc tăng doanh thu trên cùng một lượng tài sản, hoặc giảm/thanh lý các tài sản không hiệu quả.\n\n"

    # Gợi ý dựa trên đòn bẩy tài chính
    if latest_data["Đòn bẩy tài chính"] < 1.5:
        assessment += "- **Xem xét cơ cấu vốn**: Có thể cân nhắc tăng đòn bẩy tài chính nếu chi phí vốn vay thấp hơn ROA, tuy nhiên cần cân nhắc rủi ro tài chính.\n\n"
    elif latest_data["Đòn bẩy tài chính"] > 3:
        assessment += "- **Cần thận trọng với đòn bẩy tài chính cao**: Đòn bẩy tài chính cao có thể làm tăng ROE nhưng cũng làm tăng rủi ro tài chính, đặc biệt trong điều kiện kinh tế không ổn định.\n\n"

    st.markdown(assessment)

    # Thêm bảng so sánh ngành (giả định)
    st.subheader("6. So sánh với trung bình ngành (tham khảo)")

    # Dữ liệu trung bình ngành (giả định)
    industry_avg = {
        "ROE": 0.12,
        "Biên lợi nhuận ròng": 0.08,
        "Hiệu suất sử dụng tài sản": 0.9,
        "Đòn bẩy tài chính": 1.7,
    }

    # Tạo DataFrame so sánh
    comparison_data = {
        "Chỉ số": ["ROE", "Biên lợi nhuận ròng", "Hiệu suất sử dụng tài sản", "Đòn bẩy tài chính"],
        "Công ty": [
            f"{latest_data['ROE']*100:.2f}%",
            f"{latest_data['Biên lợi nhuận ròng']*100:.2f}%",
            f"{latest_data['Hiệu suất sử dụng tài sản']:.2f}",
            f"{latest_data['Đòn bẩy tài chính']:.2f}",
        ],
        "Trung bình ngành": [
            f"{industry_avg['ROE']*100:.2f}%",
            f"{industry_avg['Biên lợi nhuận ròng']*100:.2f}%",
            f"{industry_avg['Hiệu suất sử dụng tài sản']:.2f}",
            f"{industry_avg['Đòn bẩy tài chính']:.2f}",
        ],
        "So với ngành": [
            f"{(latest_data['ROE']/industry_avg['ROE']-1)*100:.2f}%",
            f"{(latest_data['Biên lợi nhuận ròng']/industry_avg['Biên lợi nhuận ròng']-1)*100:.2f}%",
            f"{(latest_data['Hiệu suất sử dụng tài sản']/industry_avg['Hiệu suất sử dụng tài sản']-1)*100:.2f}%",
            f"{(latest_data['Đòn bẩy tài chính']/industry_avg['Đòn bẩy tài chính']-1)*100:.2f}%",
        ],
    }

    comparison_df = pd.DataFrame(comparison_data)

    st.dataframe(
        comparison_df,
        column_config={
            "Chỉ số": st.column_config.TextColumn("Chỉ số"),
            "Công ty": st.column_config.TextColumn("Công ty"),
            "Trung bình ngành": st.column_config.TextColumn("Trung bình ngành"),
            "So với ngành": st.column_config.TextColumn("% So với ngành"),
        },
        hide_index=True,
        use_container_width=True,
    )

    st.markdown(
        """
    > **Lưu ý**: Dữ liệu trung bình ngành là giả định để minh họa. Cần sử dụng dữ liệu ngành thực tế để có đánh giá chính xác.
    """
    )
