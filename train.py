import json

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

# Set page configuration
st.set_page_config(page_title="VHC Financial Analysis Dashboard", page_icon="📊", layout="wide")
HEADERS = {
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
}


@st.cache_data(ttl=3600)
def get_company_plan(stock, year):
    """Lấy thông tin chi tiết của quỹ từ API"""
    try:
        url = f"https://api-finfo.vndirect.com.vn/v4/company_forecast?q=code:{stock}~fiscalYear:gte:{year}&sort=fiscalYear"
        print(url)
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data["data"])
        else:
            st.error(f"Lỗi khi lấy thông tin cổ phiếu {stock}: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"Không thể kết nối đến API: {str(e)}")
        return {}


# Function to load data
@st.cache_data
def load_data():
    # In a real app, you would load from the API
    # Here we're loading the data from the sample provided
    df = get_company_plan("HPG", 2020)
    # Convert fiscal year to string for better display
    df["fiscalYear"] = df["fiscalYear"].astype(str)
    # Sort by fiscal year
    df = df.sort_values("fiscalYear")

    # Convert values to billions for better readability
    for col in [
        "netRevenueEst",
        "netRevenueVal",
        "profitAftTaxEst",
        "profitAftTaxVal",
        "totalRevenueEst",
        "totalRevenueVal",
    ]:
        df[f"{col}_B"] = df[col]

    return df


# Load data
df = load_data()

# Create the dashboard
st.title("VHC Financial Analysis Dashboard")

# Overview section
st.header("Company Overview")
col1, col2, col3 = st.columns(3)

# Calculate metrics for the latest year
latest_year = df["fiscalYear"].iloc[-1]
latest_data = df[df["fiscalYear"] == latest_year].iloc[0]


# Format large numbers
def format_number(num, suffix=""):
    """Format large numbers to K, M, B, T"""
    if num >= 1_000_000_000_000:
        return f"{num / 1_000_000_000_000:.2f}T {suffix}"
    elif num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.2f}B {suffix}"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M {suffix}"
    elif num >= 1_000:
        return f"{num / 1_000:.2f}K {suffix}"
    else:
        return f"{num:.2f} {suffix}"


with col1:
    st.metric(
        label="Net Revenue (Latest Year)",
        value=format_number(latest_data["netRevenueVal"]),
        delta=f"{latest_data['netRevenueRate'] - 100:.2f}% vs Est.",
    )

with col2:
    st.metric(
        label="Profit After Tax (Latest Year)",
        value=format_number(latest_data["profitAftTaxVal"]),
        delta=f"{latest_data['profitAftTaxRate'] - 100:.2f}% vs Est.",
    )

with col3:
    # Calculate YoY growth for net revenue
    if len(df) >= 2:
        prev_year = str(int(float(latest_year)) - 1)
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

# Time period selector
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

# Tab layout for different analyses
tab1, tab2, tab3, tab4 = st.tabs(
    ["Revenue Analysis", "Profit Analysis", "Forecasting Accuracy", "Data Table"]
)

with tab1:
    st.subheader("Revenue Analysis")

    # Revenue trend chart
    fig1 = go.Figure()

    fig1.add_trace(
        go.Bar(
            x=filtered_df["fiscalYear"],
            y=filtered_df["netRevenueVal_B"],
            name="Actual Net Revenue",
            marker_color="rgb(26, 118, 255)",
        )
    )

    fig1.add_trace(
        go.Scatter(
            x=filtered_df["fiscalYear"],
            y=filtered_df["netRevenueEst_B"],
            mode="lines+markers",
            name="Estimated Net Revenue",
            line=dict(color="rgba(246, 78, 139, 0.8)", width=3),
        )
    )

    fig1.update_layout(
        title="Net Revenue: Actual vs Estimated (Billions VND)",
        xaxis_title="Fiscal Year",
        yaxis_title="Amount (Billions VND)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig1, use_container_width=True)

    # Revenue growth rate chart
    col1, col2 = st.columns(2)

    with col1:
        # Calculate YoY growth rates
        filtered_df["yoy_growth"] = filtered_df["netRevenueVal"].pct_change() * 100

        fig_growth = px.bar(
            filtered_df,
            x="fiscalYear",
            y="yoy_growth",
            title="Year-over-Year Net Revenue Growth (%)",
            labels={"yoy_growth": "YoY Growth (%)", "fiscalYear": "Fiscal Year"},
            color="yoy_growth",
            color_continuous_scale=px.colors.diverging.RdBu,
            color_continuous_midpoint=0,
        )

        fig_growth.update_layout(hovermode="x unified")
        st.plotly_chart(fig_growth, use_container_width=True)

    with col2:
        # Revenue composition
        fig_comp = go.Figure()

        fig_comp.add_trace(
            go.Bar(
                x=filtered_df["fiscalYear"],
                y=filtered_df["netRevenueVal_B"],
                name="Net Revenue",
                marker_color="rgba(26, 118, 255, 0.8)",
            )
        )

        fig_comp.add_trace(
            go.Bar(
                x=filtered_df["fiscalYear"],
                y=(filtered_df["totalRevenueVal_B"] - filtered_df["netRevenueVal_B"]),
                name="Other Revenue",
                marker_color="rgba(55, 83, 109, 0.7)",
            )
        )

        fig_comp.update_layout(
            title="Revenue Composition (Billions VND)",
            xaxis_title="Fiscal Year",
            yaxis_title="Amount (Billions VND)",
            barmode="stack",
            hovermode="x unified",
        )

        st.plotly_chart(fig_comp, use_container_width=True)

with tab2:
    st.subheader("Profit Analysis")

    # Profit trend chart
    fig2 = go.Figure()

    fig2.add_trace(
        go.Bar(
            x=filtered_df["fiscalYear"],
            y=filtered_df["profitAftTaxVal_B"],
            name="Actual Profit After Tax",
            marker_color="rgb(46, 184, 46)",
        )
    )

    fig2.add_trace(
        go.Scatter(
            x=filtered_df["fiscalYear"],
            y=filtered_df["profitAftTaxEst_B"],
            mode="lines+markers",
            name="Estimated Profit After Tax",
            line=dict(color="rgba(246, 78, 139, 0.8)", width=3),
        )
    )

    fig2.update_layout(
        title="Profit After Tax: Actual vs Estimated (Billions VND)",
        xaxis_title="Fiscal Year",
        yaxis_title="Amount (Billions VND)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Profit metrics
    col1, col2 = st.columns(2)

    with col1:
        # Calculate profit margin
        filtered_df["profit_margin"] = (
            filtered_df["profitAftTaxVal"] / filtered_df["netRevenueVal"]
        ) * 100

        fig_margin = px.line(
            filtered_df,
            x="fiscalYear",
            y="profit_margin",
            title="Profit Margin (%)",
            labels={"profit_margin": "Profit Margin (%)", "fiscalYear": "Fiscal Year"},
            markers=True,
            line_shape="spline",
        )

        fig_margin.update_traces(line=dict(width=3, color="rgba(46, 184, 46, 0.8)"))
        fig_margin.update_layout(hovermode="x unified")
        st.plotly_chart(fig_margin, use_container_width=True)

    with col2:
        # Calculate YoY profit growth
        filtered_df["profit_yoy_growth"] = filtered_df["profitAftTaxVal"].pct_change() * 100

        fig_profit_growth = px.bar(
            filtered_df,
            x="fiscalYear",
            y="profit_yoy_growth",
            title="Year-over-Year Profit Growth (%)",
            labels={"profit_yoy_growth": "YoY Growth (%)", "fiscalYear": "Fiscal Year"},
            color="profit_yoy_growth",
            color_continuous_scale=px.colors.diverging.RdBu,
            color_continuous_midpoint=0,
        )

        fig_profit_growth.update_layout(hovermode="x unified")
        st.plotly_chart(fig_profit_growth, use_container_width=True)

with tab3:
    st.subheader("Forecasting Accuracy Analysis")

    # Create a figure with 2 subplots
    fig3 = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=("Revenue Forecast Accuracy (%)", "Profit Forecast Accuracy (%)"),
        vertical_spacing=0.1,
    )

    # Add revenue rate trace
    fig3.add_trace(
        go.Scatter(
            x=filtered_df["fiscalYear"],
            y=filtered_df["netRevenueRate"],
            mode="lines+markers",
            name="Revenue Forecast Accuracy",
            line=dict(color="rgba(26, 118, 255, 0.8)", width=3),
        ),
        row=1,
        col=1,
    )

    # Add profit rate trace
    fig3.add_trace(
        go.Scatter(
            x=filtered_df["fiscalYear"],
            y=filtered_df["profitAftTaxRate"],
            mode="lines+markers",
            name="Profit Forecast Accuracy",
            line=dict(color="rgba(46, 184, 46, 0.8)", width=3),
        ),
        row=2,
        col=1,
    )

    # Add horizontal lines at 100%
    fig3.add_hline(
        y=100,
        line_dash="dash",
        line_color="gray",
        annotation_text="Perfect Forecast",
        annotation_position="bottom right",
        row=1,
        col=1,
    )

    fig3.add_hline(
        y=100,
        line_dash="dash",
        line_color="gray",
        annotation_text="Perfect Forecast",
        annotation_position="bottom right",
        row=2,
        col=1,
    )

    # Update layout
    fig3.update_layout(
        height=800,
        title_text="Forecast Accuracy Analysis",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )

    fig3.update_yaxes(title_text="Accuracy (%)", row=1, col=1)
    fig3.update_yaxes(title_text="Accuracy (%)", row=2, col=1)
    fig3.update_xaxes(title_text="Fiscal Year", row=2, col=1)

    st.plotly_chart(fig3, use_container_width=True)

    # Additional analysis of forecast accuracy
    st.subheader("Forecast Accuracy Metrics")

    col1, col2, col3 = st.columns(3)

    with col1:
        avg_revenue_accuracy = filtered_df["netRevenueRate"].mean()
        st.metric(
            label="Average Revenue Forecast Accuracy",
            value=f"{avg_revenue_accuracy:.2f}%",
            delta=f"{avg_revenue_accuracy - 100:.2f}%",
        )

    with col2:
        avg_profit_accuracy = filtered_df["profitAftTaxRate"].mean()
        st.metric(
            label="Average Profit Forecast Accuracy",
            value=f"{avg_profit_accuracy:.2f}%",
            delta=f"{avg_profit_accuracy - 100:.2f}%",
        )

    with col3:
        # Calculate correlation between revenue and profit accuracy
        corr_accuracy = filtered_df["netRevenueRate"].corr(filtered_df["profitAftTaxRate"])
        st.metric(
            label="Revenue-Profit Accuracy Correlation", value=f"{corr_accuracy:.2f}", delta=None
        )

    # Scatter plot of revenue vs profit accuracy
    fig_scatter = px.scatter(
        filtered_df,
        x="netRevenueRate",
        y="profitAftTaxRate",
        title="Revenue vs. Profit Forecast Accuracy",
        labels={
            "netRevenueRate": "Revenue Forecast Accuracy (%)",
            "profitAftTaxRate": "Profit Forecast Accuracy (%)",
        },
        text="fiscalYear",
        size="totalRevenueVal_B",
        color="fiscalYear",
        color_continuous_scale=px.colors.sequential.Viridis,
    )

    fig_scatter.add_shape(
        type="line", x0=50, y0=50, x1=150, y1=150, line=dict(color="Gray", width=2, dash="dash")
    )

    fig_scatter.add_vline(x=100, line_dash="dot", line_color="gray")
    fig_scatter.add_hline(y=100, line_dash="dot", line_color="gray")

    fig_scatter.update_traces(textposition="top center")
    fig_scatter.update_layout(height=600)

    st.plotly_chart(fig_scatter, use_container_width=True)

with tab4:
    st.subheader("Raw Data Table")

    # Display columns in billions for better readability
    display_columns = [
        "fiscalYear",
        "netRevenueEst_B",
        "netRevenueVal_B",
        "netRevenueRate",
        "profitAftTaxEst_B",
        "profitAftTaxVal_B",
        "profitAftTaxRate",
    ]

    display_df = filtered_df[display_columns].copy()

    # Rename columns for better readability
    display_df.columns = [
        "Fiscal Year",
        "Net Revenue Est. (B)",
        "Net Revenue Actual (B)",
        "Revenue Accuracy %",
        "Profit Est. (B)",
        "Profit Actual (B)",
        "Profit Accuracy %",
    ]

    st.dataframe(
        display_df.style.background_gradient(
            subset=["Revenue Accuracy %", "Profit Accuracy %"], cmap="RdYlGn", vmin=50, vmax=150
        ),
        use_container_width=True,
    )
