import math

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Set page configuration
st.set_page_config(page_title="Bảng Điều Khiển Sức Khỏe Tài Chính HPG", layout="wide")

# Page title and description
st.title("Bảng Điều Khiển Sức Khỏe Tài Chính HPG")
st.markdown(
    """
Bảng điều khiển này phân tích sức khỏe tài chính của HPG dựa trên các mô hình tài chính:
- **Piotroski F-Score**: Đánh giá sức mạnh tài chính (thang điểm 0-9)
- **Altman Z-Score**: Dự báo rủi ro phá sản
- **Beneish M-Score**: Phát hiện khả năng gian lận lợi nhuận
"""
)


# Load and prepare data
@st.cache_data
def load_data():
    cf_df = pd.read_csv("CF.csv")
    is_df = pd.read_csv("IS.csv")
    bs_df = pd.read_csv("BS.csv")

    # Reverse rows to have chronological order
    cf_df = cf_df.iloc[::-1].reset_index(drop=True)
    is_df = is_df.iloc[::-1].reset_index(drop=True)
    bs_df = bs_df.iloc[::-1].reset_index(drop=True)

    return cf_df, is_df, bs_df


try:
    cf_df, is_df, bs_df = load_data()

    # Create year lists for selection
    years = is_df["yearReport"].unique().tolist()

    # Create tabs for the different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "Piotroski F-Score", "Altman Z-Score", "Beneish M-Score", "DuPont Analysis"]
    )

    with tab1:
        st.header("Financial Overview")

        col1, col2 = st.columns(2)

        with col1:
            # Create revenue chart
            fig_revenue = px.line(
                is_df,
                x="yearReport",
                y="Revenue (Bn. VND)",
                title="Annual Revenue (Billion VND)",
                markers=True,
            )
            fig_revenue.update_layout(xaxis_title="Year", yaxis_title="Revenue (Billion VND)")
            st.plotly_chart(fig_revenue, use_container_width=True)

            # Create net profit chart
            fig_profit = px.line(
                is_df,
                x="yearReport",
                y="Net Profit For the Year",
                title="Net Profit (Billion VND)",
                markers=True,
            )
            fig_profit.update_layout(xaxis_title="Year", yaxis_title="Net Profit (Billion VND)")
            st.plotly_chart(fig_profit, use_container_width=True)

        with col2:
            # Create assets and liabilities chart
            fig_balance = go.Figure()
            fig_balance.add_trace(
                go.Bar(
                    x=bs_df["yearReport"],
                    y=bs_df["TOTAL ASSETS (Bn. VND)"],
                    name="Total Assets",
                    marker_color="royalblue",
                )
            )
            fig_balance.add_trace(
                go.Bar(
                    x=bs_df["yearReport"],
                    y=bs_df["LIABILITIES (Bn. VND)"],
                    name="Total Liabilities",
                    marker_color="crimson",
                )
            )
            fig_balance.update_layout(
                title="Balance Sheet Overview",
                barmode="group",
                xaxis_title="Year",
                yaxis_title="Amount (Billion VND)",
            )
            st.plotly_chart(fig_balance, use_container_width=True)

            # Cash flow from operations
            fig_cf = px.line(
                cf_df,
                x="yearReport",
                y="Net cash inflows/outflows from operating activities",
                title="Operating Cash Flow (Billion VND)",
                markers=True,
            )
            fig_cf.update_layout(
                xaxis_title="Year", yaxis_title="Operating Cash Flow (Billion VND)"
            )
            st.plotly_chart(fig_cf, use_container_width=True)

    with tab2:
        st.header("Piotroski F-Score Analysis")
        st.markdown(
            """
        **Piotroski F-Score** là một công cụ đánh giá toàn diện về sức khỏe tài chính của doanh nghiệp.

        Chỉ số này gồm 9 tiêu chí thuộc 3 nhóm: lợi nhuận, đòn bẩy/thanh khoản, và hiệu quả hoạt động:

        **Lợi nhuận**
        - Tỷ suất lợi nhuận trên tài sản (ROA) > 0
        - Dòng tiền hoạt động > 0
        - ROA tăng so với năm trước
        - Dòng tiền hoạt động > ROA

        **Đòn bẩy, Thanh khoản và Nguồn vốn**
        - Tỷ lệ nợ dài hạn giảm
        - Tỷ số thanh toán hiện hành tăng
        - Không phát hành thêm cổ phiếu

        **Hiệu quả hoạt động**
        - Biên lợi nhuận gộp tăng
        - Vòng quay tài sản tăng

        **Ý nghĩa:**
        - Điểm 7-9: Tài chính mạnh
        - Điểm 4-6: Tài chính trung bình
        - Điểm 0-3: Tài chính yếu
        """
        )

        # Calculate Piotroski F-Score
        def calculate_f_score(year_index, cf_df, is_df, bs_df):
            scores = {}
            total_score = 0

            # Check if we have sufficient data for comparison (need current and previous year)
            if year_index < 1:
                return None, None

            # 1. Profitability
            # ROA
            net_profit = is_df.loc[year_index, "Net Profit For the Year"]
            total_assets = bs_df.loc[year_index, "TOTAL ASSETS (Bn. VND)"]
            prev_total_assets = bs_df.loc[year_index - 1, "TOTAL ASSETS (Bn. VND)"]

            roa = net_profit / total_assets
            scores["ROA > 0"] = 1 if roa > 0 else 0
            total_score += scores["ROA > 0"]

            # ROA Change
            prev_net_profit = is_df.loc[year_index - 1, "Net Profit For the Year"]
            prev_roa = prev_net_profit / prev_total_assets
            scores["ROA Increasing"] = 1 if roa > prev_roa else 0
            total_score += scores["ROA Increasing"]

            # Operating Cash Flow
            op_cash_flow = cf_df.loc[
                year_index, "Net cash inflows/outflows from operating activities"
            ]
            scores["Operating CF > 0"] = 1 if op_cash_flow > 0 else 0
            total_score += scores["Operating CF > 0"]

            # Cash Flow vs ROA
            cash_flow_ratio = op_cash_flow / total_assets
            scores["CF > ROA"] = 1 if cash_flow_ratio > roa else 0
            total_score += scores["CF > ROA"]

            # 2. Leverage, Liquidity, and Source of Funds
            # Long-term Debt Ratio
            lt_debt = bs_df.loc[year_index, "Long-term liabilities (Bn. VND)"]
            lt_debt_ratio = lt_debt / total_assets

            prev_lt_debt = bs_df.loc[year_index - 1, "Long-term liabilities (Bn. VND)"]
            prev_lt_debt_ratio = prev_lt_debt / prev_total_assets

            scores["Decreasing LT Debt Ratio"] = 1 if lt_debt_ratio < prev_lt_debt_ratio else 0
            total_score += scores["Decreasing LT Debt Ratio"]

            # Current Ratio
            current_assets = bs_df.loc[year_index, "CURRENT ASSETS (Bn. VND)"]
            current_liabilities = bs_df.loc[year_index, "Current liabilities (Bn. VND)"]
            current_ratio = current_assets / current_liabilities

            prev_current_assets = bs_df.loc[year_index - 1, "CURRENT ASSETS (Bn. VND)"]
            prev_current_liabilities = bs_df.loc[year_index - 1, "Current liabilities (Bn. VND)"]
            prev_current_ratio = prev_current_assets / prev_current_liabilities

            scores["Increasing Current Ratio"] = 1 if current_ratio > prev_current_ratio else 0
            total_score += scores["Increasing Current Ratio"]

            # Check if new shares were issued
            shares = bs_df.loc[year_index, "Common shares (Bn. VND)"]
            prev_shares = bs_df.loc[year_index - 1, "Common shares (Bn. VND)"]
            scores["No New Shares"] = 1 if shares <= prev_shares else 0
            total_score += scores["No New Shares"]

            # 3. Operating Efficiency
            # Gross Margin
            gross_profit = is_df.loc[year_index, "Gross Profit"]
            net_sales = is_df.loc[year_index, "Net Sales"]
            gross_margin = gross_profit / net_sales

            prev_gross_profit = is_df.loc[year_index - 1, "Gross Profit"]
            prev_net_sales = is_df.loc[year_index - 1, "Net Sales"]
            prev_gross_margin = prev_gross_profit / prev_net_sales

            scores["Increasing Gross Margin"] = 1 if gross_margin > prev_gross_margin else 0
            total_score += scores["Increasing Gross Margin"]

            # Asset Turnover
            asset_turnover = net_sales / total_assets
            prev_asset_turnover = prev_net_sales / prev_total_assets

            scores["Increasing Asset Turnover"] = 1 if asset_turnover > prev_asset_turnover else 0
            total_score += scores["Increasing Asset Turnover"]

            return total_score, scores

        # Calculate F-Score for all applicable years
        f_scores = []
        f_score_details = []
        f_score_years = []

        for i in range(len(is_df)):
            year = is_df.loc[i, "yearReport"]
            score, details = calculate_f_score(i, cf_df, is_df, bs_df)
            if score is not None:
                f_scores.append(score)
                f_score_details.append(details)
                f_score_years.append(year)

        # Create F-score visualization
        fig_f_score = go.Figure()
        fig_f_score.add_trace(
            go.Bar(
                x=f_score_years,
                y=f_scores,
                marker_color=[
                    "red" if s <= 3 else "yellow" if s <= 6 else "green" for s in f_scores
                ],
                text=f_scores,
                textposition="auto",
            )
        )

        fig_f_score.update_layout(
            title="Piotroski F-Score by Year",
            xaxis_title="Year",
            yaxis_title="F-Score",
            yaxis=dict(range=[0, 9]),
            shapes=[
                dict(
                    type="rect",
                    xref="paper",
                    yref="y",
                    x0=0,
                    y0=0,
                    x1=1,
                    y1=3,
                    fillcolor="rgba(255,0,0,0.1)",
                    line=dict(width=0),
                ),
                dict(
                    type="rect",
                    xref="paper",
                    yref="y",
                    x0=0,
                    y0=3,
                    x1=1,
                    y1=6,
                    fillcolor="rgba(255,255,0,0.1)",
                    line=dict(width=0),
                ),
                dict(
                    type="rect",
                    xref="paper",
                    yref="y",
                    x0=0,
                    y0=6,
                    x1=1,
                    y1=9,
                    fillcolor="rgba(0,255,0,0.1)",
                    line=dict(width=0),
                ),
            ],
            annotations=[
                dict(x=0.5, y=1.5, xref="paper", yref="y", text="Weak", showarrow=False),
                dict(x=0.5, y=4.5, xref="paper", yref="y", text="Moderate", showarrow=False),
                dict(x=0.5, y=7.5, xref="paper", yref="y", text="Strong", showarrow=False),
            ],
        )

        st.plotly_chart(fig_f_score, use_container_width=True)

        # F-score breakdown for selected year
        selected_year_index = st.selectbox(
            "Select Year for F-Score Details:",
            options=list(range(len(f_score_years))),
            format_func=lambda x: f_score_years[x],
        )

        if selected_year_index is not None:
            selected_details = f_score_details[selected_year_index]
            selected_year = f_score_years[selected_year_index]

            st.write(f"### F-Score Breakdown for {selected_year}")

            criteria_df = pd.DataFrame(
                {
                    "Criteria": list(selected_details.keys()),
                    "Score": list(selected_details.values()),
                }
            )

            fig_breakdown = px.bar(
                criteria_df,
                x="Criteria",
                y="Score",
                color="Score",
                color_continuous_scale=["red", "green"],
                range_color=[0, 1],
            )
            fig_breakdown.update_layout(height=400, yaxis=dict(range=[0, 1.1], tickvals=[0, 1]))

            st.plotly_chart(fig_breakdown, use_container_width=True)

    with tab3:
        st.header("Altman Z-Score Analysis")
        st.markdown(
            """
        **Altman Z-Score** là một mô hình dự báo nguy cơ phá sản, kết hợp 5 tỷ số tài chính với các hệ số trọng số.

        **Công thức:**
        Z = 1.2A + 1.4B + 3.3C + 0.6D + 1.0E

        Trong đó:
        - A = Vốn lưu động / Tổng tài sản
        - B = Lợi nhuận giữ lại / Tổng tài sản
        - C = EBIT / Tổng tài sản
        - D = Giá trị vốn chủ sở hữu / Tổng nợ phải trả
        - E = Doanh thu / Tổng tài sản

        **Ý nghĩa:**
        - Z > 2.99: "Vùng an toàn" - Nguy cơ phá sản thấp
        - 1.81 < Z < 2.99: "Vùng xám" - Nguy cơ trung bình
        - Z < 1.81: "Vùng nguy hiểm" - Nguy cơ phá sản cao
        """
        )

        # Calculate Altman Z-Score
        def calculate_z_score(year_index, cf_df, is_df, bs_df):
            if year_index >= len(bs_df):
                return None

            # Extract needed values
            total_assets = bs_df.loc[year_index, "TOTAL ASSETS (Bn. VND)"]
            current_assets = bs_df.loc[year_index, "CURRENT ASSETS (Bn. VND)"]
            current_liabilities = bs_df.loc[year_index, "Current liabilities (Bn. VND)"]
            retained_earnings = bs_df.loc[year_index, "Undistributed earnings (Bn. VND)"]
            ebit = is_df.loc[
                year_index, "Profit before tax"
            ]  # Using profit before tax as proxy for EBIT
            total_liabilities = bs_df.loc[year_index, "LIABILITIES (Bn. VND)"]
            equity = bs_df.loc[
                year_index, "OWNER'S EQUITY(Bn.VND)"
            ]  # Using book value as proxy for market value
            sales = is_df.loc[year_index, "Net Sales"]

            # Calculate working capital
            working_capital = current_assets - current_liabilities

            # Calculate ratios
            A = working_capital / total_assets
            B = retained_earnings / total_assets
            C = ebit / total_assets
            D = equity / total_liabilities  # Using book value as a proxy for market value
            E = sales / total_assets

            # Calculate Z-Score
            Z = 1.2 * A + 1.4 * B + 3.3 * C + 0.6 * D + 1.0 * E

            # Store components for breakdown
            components = {
                "Working Capital/Total Assets": 1.2 * A,
                "Retained Earnings/Total Assets": 1.4 * B,
                "EBIT/Total Assets": 3.3 * C,
                "Equity/Total Liabilities": 0.6 * D,
                "Sales/Total Assets": 1.0 * E,
            }

            return Z, components

        # Calculate Z-Score for all years
        z_scores = []
        z_components = []
        z_years = []

        for i in range(len(is_df)):
            year = is_df.loc[i, "yearReport"]
            result = calculate_z_score(i, cf_df, is_df, bs_df)

            if result is not None:
                z, components = result
                z_scores.append(z)
                z_components.append(components)
                z_years.append(year)

        # Create Z-score visualization
        fig_z_score = go.Figure()

        # Color based on risk zones
        colors = ["red" if z < 1.81 else "yellow" if z < 2.99 else "green" for z in z_scores]

        fig_z_score.add_trace(
            go.Scatter(
                x=z_years,
                y=z_scores,
                mode="lines+markers",
                marker=dict(color=colors, size=10),
                line=dict(color="blue", width=2),
                text=[f"{z:.2f}" for z in z_scores],
                hoverinfo="text",
            )
        )

        fig_z_score.update_layout(
            title="Altman Z-Score by Year",
            xaxis_title="Year",
            yaxis_title="Z-Score",
            shapes=[
                dict(
                    type="rect",
                    xref="paper",
                    yref="y",
                    x0=0,
                    y0=0,
                    x1=1,
                    y1=1.81,
                    fillcolor="rgba(255,0,0,0.1)",
                    line=dict(width=0),
                ),
                dict(
                    type="rect",
                    xref="paper",
                    yref="y",
                    x0=0,
                    y0=1.81,
                    x1=1,
                    y1=2.99,
                    fillcolor="rgba(255,255,0,0.1)",
                    line=dict(width=0),
                ),
                dict(
                    type="rect",
                    xref="paper",
                    yref="y",
                    x0=0,
                    y0=2.99,
                    x1=1,
                    y1=max(z_scores) + 1,
                    fillcolor="rgba(0,255,0,0.1)",
                    line=dict(width=0),
                ),
            ],
            annotations=[
                dict(x=0.5, y=0.9, xref="paper", yref="y", text="Distress Zone", showarrow=False),
                dict(x=0.5, y=2.4, xref="paper", yref="y", text="Grey Zone", showarrow=False),
                dict(
                    x=0.5,
                    y=min(max(z_scores), 6),
                    xref="paper",
                    yref="y",
                    text="Safe Zone",
                    showarrow=False,
                ),
            ],
        )

        st.plotly_chart(fig_z_score, use_container_width=True)

        # Z-score breakdown for selected year
        selected_z_year_index = st.selectbox(
            "Select Year for Z-Score Components:",
            options=list(range(len(z_years))),
            format_func=lambda x: z_years[x],
        )

        if selected_z_year_index is not None:
            selected_components = z_components[selected_z_year_index]
            selected_z_year = z_years[selected_z_year_index]
            selected_z = z_scores[selected_z_year_index]

            st.write(f"### Z-Score Breakdown for {selected_z_year}: {selected_z:.2f}")

            component_df = pd.DataFrame(
                {
                    "Component": list(selected_components.keys()),
                    "Value": list(selected_components.values()),
                }
            )

            fig_z_breakdown = px.bar(
                component_df,
                x="Component",
                y="Value",
                color="Value",
                color_continuous_scale="RdYlGn",
            )

            st.plotly_chart(fig_z_breakdown, use_container_width=True)

    with tab4:
        st.header("Beneish M-Score Analysis")
        st.markdown(
            """
        **Beneish M-Score** là mô hình phát hiện khả năng gian lận lợi nhuận, kết hợp 8 chỉ số tài chính để nhận diện dấu hiệu bất thường trong báo cáo tài chính.
        
        **Công thức:**
        M = -4.84 + 0.92×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI
        
        **Các chỉ số chính:**
        - DSRI (Chỉ số doanh thu chưa thu tiền)
        - GMI (Chỉ số biên lợi nhuận gộp)
        - AQI (Chỉ số chất lượng tài sản)
        - SGI (Chỉ số tăng trưởng doanh thu)
        - DEPI (Chỉ số khấu hao)
        - SGAI (Chỉ số chi phí bán hàng & quản lý)
        - TATA (Tổng khoản dồn tích trên tổng tài sản)
        - LVGI (Chỉ số đòn bẩy tài chính)
        
        **Ý nghĩa:**
        - M > -1.78: Nguy cơ gian lận lợi nhuận cao
        - M < -1.78: Nguy cơ gian lận lợi nhuận thấp
        """
        )

        # Calculate Beneish M-Score
        def calculate_m_score(year_index, cf_df, is_df, bs_df):
            if year_index < 1:  # Need previous year data
                return None, None

            # Calculate DSRI - Days Sales in Receivables Index
            receivables = bs_df.loc[year_index, "Accounts receivable (Bn. VND)"]
            sales = is_df.loc[year_index, "Net Sales"]
            prev_receivables = bs_df.loc[year_index - 1, "Accounts receivable (Bn. VND)"]
            prev_sales = is_df.loc[year_index - 1, "Net Sales"]

            if prev_sales == 0 or prev_receivables == 0:
                return None, None

            dsri = (receivables / sales) / (prev_receivables / prev_sales)

            # Calculate GMI - Gross Margin Index
            gross_profit = is_df.loc[year_index, "Gross Profit"]
            prev_gross_profit = is_df.loc[year_index - 1, "Gross Profit"]

            prev_gross_margin = prev_gross_profit / prev_sales
            gross_margin = gross_profit / sales

            if prev_gross_margin == 0:
                return None, None

            gmi = prev_gross_margin / gross_margin

            # Calculate AQI - Asset Quality Index
            current_assets = bs_df.loc[year_index, "CURRENT ASSETS (Bn. VND)"]
            total_assets = bs_df.loc[year_index, "TOTAL ASSETS (Bn. VND)"]
            prev_current_assets = bs_df.loc[year_index - 1, "CURRENT ASSETS (Bn. VND)"]
            prev_total_assets = bs_df.loc[year_index - 1, "TOTAL ASSETS (Bn. VND)"]

            non_current_assets = total_assets - current_assets
            prev_non_current_assets = prev_total_assets - prev_current_assets

            if prev_total_assets == 0 or prev_non_current_assets == 0:
                return None, None

            aqi = (non_current_assets / total_assets) / (
                prev_non_current_assets / prev_total_assets
            )

            # Calculate SGI - Sales Growth Index
            sgi = sales / prev_sales

            # Calculate DEPI - Depreciation Index
            depreciation = cf_df.loc[year_index, "Depreciation and Amortisation"]
            prev_depreciation = cf_df.loc[year_index - 1, "Depreciation and Amortisation"]

            fixed_assets = bs_df.loc[year_index, "Fixed assets (Bn. VND)"]
            prev_fixed_assets = bs_df.loc[year_index - 1, "Fixed assets (Bn. VND)"]

            if fixed_assets == 0 or prev_fixed_assets == 0 or prev_depreciation == 0:
                return None, None

            depi = (prev_depreciation / prev_fixed_assets) / (depreciation / fixed_assets)

            # Calculate SGAI - SG&A Expense Index
            sga = (
                is_df.loc[year_index, "Selling Expenses"]
                + is_df.loc[year_index, "General & Admin Expenses"]
            )
            prev_sga = (
                is_df.loc[year_index - 1, "Selling Expenses"]
                + is_df.loc[year_index - 1, "General & Admin Expenses"]
            )

            if prev_sga == 0 or prev_sales == 0:
                return None, None

            sgai = (sga / sales) / (prev_sga / prev_sales)

            # Calculate TATA - Total Accruals to Total Assets
            net_income = is_df.loc[year_index, "Net Profit For the Year"]
            op_cash_flow = cf_df.loc[
                year_index, "Net cash inflows/outflows from operating activities"
            ]

            if total_assets == 0:
                return None, None

            tata = (net_income - op_cash_flow) / total_assets

            # Calculate LVGI - Leverage Index
            total_liabilities = bs_df.loc[year_index, "LIABILITIES (Bn. VND)"]
            prev_total_liabilities = bs_df.loc[year_index - 1, "LIABILITIES (Bn. VND)"]

            if prev_total_liabilities == 0 or prev_total_assets == 0:
                return None, None

            lvgi = (total_liabilities / total_assets) / (
                prev_total_liabilities / prev_total_assets
            )

            # Calculate M-Score using the Beneish model
            m_score = (
                -4.84
                + 0.92 * dsri
                + 0.528 * gmi
                + 0.404 * aqi
                + 0.892 * sgi
                + 0.115 * depi
                - 0.172 * sgai
                + 4.679 * tata
                - 0.327 * lvgi
            )

            # Store components
            components = {
                "Days Sales in Receivables Index (DSRI)": dsri,
                "Gross Margin Index (GMI)": gmi,
                "Asset Quality Index (AQI)": aqi,
                "Sales Growth Index (SGI)": sgi,
                "Depreciation Index (DEPI)": depi,
                "SG&A Expense Index (SGAI)": sgai,
                "Total Accruals to Total Assets (TATA)": tata,
                "Leverage Index (LVGI)": lvgi,
            }

            return m_score, components

        # Calculate M-Score for all years
        m_scores = []
        m_components = []
        m_years = []

        for i in range(len(is_df)):
            year = is_df.loc[i, "yearReport"]
            result = calculate_m_score(i, cf_df, is_df, bs_df)

            if result is not None and result[0] is not None:
                m, components = result
                m_scores.append(m)
                m_components.append(components)
                m_years.append(year)

        # Create M-score visualization
        fig_m_score = go.Figure()

        threshold = -1.78
        colors = ["red" if m > threshold else "green" for m in m_scores]

        fig_m_score.add_trace(
            go.Scatter(
                x=m_years,
                y=m_scores,
                mode="lines+markers",
                marker=dict(color=colors, size=10),
                line=dict(color="blue", width=2),
                text=[f"{m:.2f}" for m in m_scores],
                hoverinfo="text",
            )
        )

        fig_m_score.add_trace(
            go.Scatter(
                x=[m_years[0], m_years[-1]],
                y=[threshold, threshold],
                mode="lines",
                line=dict(color="red", width=2, dash="dash"),
                name="Threshold (-1.78)",
            )
        )

        fig_m_score.update_layout(
            title="Beneish M-Score by Year",
            xaxis_title="Year",
            yaxis_title="M-Score",
            shapes=[
                dict(
                    type="rect",
                    xref="paper",
                    yref="y",
                    x0=0,
                    y0=-10,
                    x1=1,
                    y1=threshold,
                    fillcolor="rgba(0,255,0,0.1)",
                    line=dict(width=0),
                ),
                dict(
                    type="rect",
                    xref="paper",
                    yref="y",
                    x0=0,
                    y0=threshold,
                    x1=1,
                    y1=5,
                    fillcolor="rgba(255,0,0,0.1)",
                    line=dict(width=0),
                ),
            ],
            annotations=[
                dict(
                    x=0.5,
                    y=-5,
                    xref="paper",
                    yref="y",
                    text="Low Manipulation Risk",
                    showarrow=False,
                ),
                dict(
                    x=0.5,
                    y=0,
                    xref="paper",
                    yref="y",
                    text="High Manipulation Risk",
                    showarrow=False,
                ),
            ],
        )

        st.plotly_chart(fig_m_score, use_container_width=True)

        # M-score breakdown for selected year
        if len(m_years) > 0:
            selected_m_year_index = st.selectbox(
                "Select Year for M-Score Components:",
                options=list(range(len(m_years))),
                format_func=lambda x: m_years[x],
            )

            if selected_m_year_index is not None and selected_m_year_index < len(m_components):
                selected_m_components = m_components[selected_m_year_index]
                selected_m_year = m_years[selected_m_year_index]
                selected_m = m_scores[selected_m_year_index]

                st.write(f"### M-Score Breakdown for {selected_m_year}")

                component_df = pd.DataFrame(
                    {
                        "Component": list(selected_m_components.keys()),
                        "Value": list(selected_m_components.values()),
                    }
                )

                fig_m_breakdown = px.bar(
                    component_df,
                    x="Component",
                    y="Value",
                    color="Value",
                    color_continuous_scale="RdYlGn",
                )

                fig_m_breakdown.update_layout(
                    title=f"M-Score Components for {selected_m_year} (Total Score: {selected_m:.2f})",
                    xaxis_title="Component",
                    yaxis_title="Value",
                    height=500,
                )

                st.plotly_chart(fig_m_breakdown, use_container_width=True)

                # Add interpretation
                st.markdown(
                    """
                **Giải thích các thành phần:**
                - **DSRI > 1.031**: Có thể cho thấy doanh thu chưa thu tiền tăng bất thường (nguy cơ thổi phồng doanh thu)
                - **GMI > 1.014**: Biên lợi nhuận gộp giảm, có thể do chi phí tăng hoặc doanh thu giảm
                - **AQI > 1.040**: Chất lượng tài sản giảm, tài sản vô hình/tài sản không sinh lời tăng
                - **SGI > 1.134**: Tăng trưởng doanh thu mạnh, cần chú ý nếu không đi kèm lợi nhuận
                - **DEPI < 0.804**: Tỷ lệ khấu hao giảm, có thể do giảm trích khấu hao (làm đẹp lợi nhuận)
                - **SGAI > 1.054**: Chi phí bán hàng & quản lý tăng nhanh hơn doanh thu
                - **TATA > 0.018**: Khoản dồn tích cao, có thể là dấu hiệu điều chỉnh lợi nhuận
                - **LVGI > 1.037**: Đòn bẩy tài chính tăng, rủi ro tài chính cao hơn
                """
                )

    with tab5:
        st.header("DuPont Analysis")
        st.markdown(
            """
        **Phân tích DuPont** giúp tách nhỏ tỷ suất lợi nhuận trên vốn chủ sở hữu (ROE) thành 3 thành phần để hiểu rõ động lực tạo ra lợi nhuận của doanh nghiệp:
        
        1. **Biên lợi nhuận** = Lợi nhuận ròng / Doanh thu
        2. **Vòng quay tài sản** = Doanh thu / Tổng tài sản
        3. **Đòn bẩy tài chính** = Tổng tài sản / Vốn chủ sở hữu
        
        ROE = Biên lợi nhuận × Vòng quay tài sản × Đòn bẩy tài chính
        
        Phân tích này giúp xác định ROE của doanh nghiệp đến từ:
        - Hiệu quả hoạt động (Biên lợi nhuận)
        - Khả năng sử dụng tài sản (Vòng quay tài sản)
        - Mức độ sử dụng đòn bẩy tài chính (Đòn bẩy tài chính)
        """
        )

        # Calculate DuPont components
        def calculate_dupont(year_index, is_df, bs_df):
            if year_index >= len(is_df):
                return None

            # Extract values
            net_income = is_df.loc[year_index, "Net Profit For the Year"]
            sales = is_df.loc[year_index, "Net Sales"]
            total_assets = bs_df.loc[year_index, "TOTAL ASSETS (Bn. VND)"]
            equity = bs_df.loc[year_index, "OWNER'S EQUITY(Bn.VND)"]

            # Calculate components
            profit_margin = net_income / sales if sales != 0 else 0
            asset_turnover = sales / total_assets if total_assets != 0 else 0
            financial_leverage = total_assets / equity if equity != 0 else 0

            # Calculate ROE
            roe = profit_margin * asset_turnover * financial_leverage

            components = {
                "Profit Margin": profit_margin,
                "Asset Turnover": asset_turnover,
                "Financial Leverage": financial_leverage,
                "ROE": roe,
            }

            return components

        # Calculate DuPont components for all years
        dupont_components = []
        dupont_years = []

        for i in range(len(is_df)):
            year = is_df.loc[i, "yearReport"]
            components = calculate_dupont(i, is_df, bs_df)

            if components is not None:
                dupont_components.append(components)
                dupont_years.append(year)

        # Create DuPont visualization
        fig_dupont = go.Figure()

        # Add traces for each component
        fig_dupont.add_trace(
            go.Scatter(
                x=dupont_years,
                y=[comp["Profit Margin"] for comp in dupont_components],
                mode="lines+markers",
                name="Profit Margin",
                line=dict(color="blue"),
            )
        )

        fig_dupont.add_trace(
            go.Scatter(
                x=dupont_years,
                y=[comp["Asset Turnover"] for comp in dupont_components],
                mode="lines+markers",
                name="Asset Turnover",
                line=dict(color="green"),
            )
        )

        fig_dupont.add_trace(
            go.Scatter(
                x=dupont_years,
                y=[comp["Financial Leverage"] for comp in dupont_components],
                mode="lines+markers",
                name="Financial Leverage",
                line=dict(color="red"),
            )
        )

        fig_dupont.add_trace(
            go.Scatter(
                x=dupont_years,
                y=[comp["ROE"] for comp in dupont_components],
                mode="lines+markers",
                name="ROE",
                line=dict(color="purple", width=3),
            )
        )

        fig_dupont.update_layout(
            title="DuPont Analysis Components Over Time",
            xaxis_title="Year",
            yaxis_title="Value",
            hovermode="x unified",
        )

        st.plotly_chart(fig_dupont, use_container_width=True)

        # Add component breakdown for selected year
        if len(dupont_years) > 0:
            selected_dupont_year_index = st.selectbox(
                "Select Year for DuPont Components:",
                options=list(range(len(dupont_years))),
                format_func=lambda x: dupont_years[x],
            )

            if selected_dupont_year_index is not None:
                selected_components = dupont_components[selected_dupont_year_index]
                selected_year = dupont_years[selected_dupont_year_index]

                st.write(f"### DuPont Analysis Breakdown for {selected_year}")

                # Create component breakdown visualization
                component_df = pd.DataFrame(
                    {
                        "Component": list(selected_components.keys()),
                        "Value": list(selected_components.values()),
                    }
                )

                fig_breakdown = px.bar(
                    component_df,
                    x="Component",
                    y="Value",
                    color="Value",
                    color_continuous_scale="RdYlGn",
                )

                fig_breakdown.update_layout(
                    title=f"DuPont Components for {selected_year}",
                    xaxis_title="Component",
                    yaxis_title="Value",
                    height=400,
                )

                st.plotly_chart(fig_breakdown, use_container_width=True)

                # Add interpretation
                st.markdown(
                    """
                **Giải thích các thành phần:**
                - **Biên lợi nhuận**: Giá trị cao cho thấy doanh nghiệp hoạt động hiệu quả, kiểm soát tốt chi phí.
                - **Vòng quay tài sản**: Giá trị cao thể hiện doanh nghiệp sử dụng tài sản hiệu quả để tạo ra doanh thu.
                - **Đòn bẩy tài chính**: Giá trị cao cho thấy doanh nghiệp sử dụng nhiều nợ vay, tiềm ẩn rủi ro tài chính.
                - **ROE**: Chỉ số tổng hợp thể hiện khả năng sinh lời trên vốn chủ sở hữu.
                
                **Bối cảnh ngành:**
                - So sánh các tỷ số này với trung bình ngành để đánh giá vị thế doanh nghiệp.
                - Theo dõi xu hướng và biến động lớn qua các năm.
                - Cân nhắc giữa việc tăng đòn bẩy và rủi ro tài chính.
                """
                )

        # Calculate C-Score
        st.write("### C-Score Analysis")

        try:
            # Calculate C-Score components for all years
            def calculate_c_score(year_index, cf_df, is_df, bs_df):
                if year_index < 1:  # Need previous year data
                    return None, None

                c_score = 0
                components = {}

                # Check for accruals
                net_income = is_df.loc[year_index, "Net Profit For the Year"]
                op_cash_flow = cf_df.loc[
                    year_index, "Net cash inflows/outflows from operating activities"
                ]
                components["Accruals > Operating Cash Flow"] = (
                    1 if net_income > op_cash_flow else 0
                )
                c_score += components["Accruals > Operating Cash Flow"]

                # Check leverage change
                total_liabilities = bs_df.loc[year_index, "LIABILITIES (Bn. VND)"]
                total_assets = bs_df.loc[year_index, "TOTAL ASSETS (Bn. VND)"]
                prev_total_liabilities = bs_df.loc[year_index - 1, "LIABILITIES (Bn. VND)"]
                prev_total_assets = bs_df.loc[year_index - 1, "TOTAL ASSETS (Bn. VND)"]

                leverage_current = total_liabilities / total_assets
                leverage_prev = prev_total_liabilities / prev_total_assets
                components["Increasing Leverage"] = 1 if leverage_current > leverage_prev else 0
                c_score += components["Increasing Leverage"]

                # Check liquidity change
                current_assets = bs_df.loc[year_index, "CURRENT ASSETS (Bn. VND)"]
                current_liabilities = bs_df.loc[year_index, "Current liabilities (Bn. VND)"]
                prev_current_assets = bs_df.loc[year_index - 1, "CURRENT ASSETS (Bn. VND)"]
                prev_current_liabilities = bs_df.loc[
                    year_index - 1, "Current liabilities (Bn. VND)"
                ]

                current_ratio = current_assets / current_liabilities
                prev_current_ratio = prev_current_assets / prev_current_liabilities
                components["Decreasing Liquidity"] = 1 if current_ratio < prev_current_ratio else 0
                c_score += components["Decreasing Liquidity"]

                # Check for equity dilution
                shares = bs_df.loc[year_index, "Common shares (Bn. VND)"]
                prev_shares = bs_df.loc[year_index - 1, "Common shares (Bn. VND)"]
                components["Equity Dilution"] = 1 if shares > prev_shares else 0
                c_score += components["Equity Dilution"]

                # Check gross margin change
                gross_profit = is_df.loc[year_index, "Gross Profit"]
                sales = is_df.loc[year_index, "Net Sales"]
                prev_gross_profit = is_df.loc[year_index - 1, "Gross Profit"]
                prev_sales = is_df.loc[year_index - 1, "Net Sales"]

                gross_margin = gross_profit / sales
                prev_gross_margin = prev_gross_profit / prev_sales
                components["Declining Gross Margins"] = (
                    1 if gross_margin < prev_gross_margin else 0
                )
                c_score += components["Declining Gross Margins"]

                return c_score, components

            # Calculate C-Score for all years
            c_scores = []
            c_components = []
            c_years = []

            for i in range(len(is_df)):
                year = is_df.loc[i, "yearReport"]
                result = calculate_c_score(i, cf_df, is_df, bs_df)

                if result is not None and result[0] is not None:
                    score, components = result
                    c_scores.append(score)
                    c_components.append(components)
                    c_years.append(year)

                # Create C-score visualization
                fig_c_score = go.Figure()

                # Color based on risk levels
                colors = ["green" if c <= 1 else "yellow" if c <= 3 else "red" for c in c_scores]

                fig_c_score.add_trace(
                    go.Bar(
                        x=c_years,
                        y=c_scores,
                        marker_color=colors,
                        text=c_scores,
                        textposition="auto",
                    )
                )

                fig_c_score.update_layout(
                    title="C-Score Over Time",
                    xaxis_title="Year",
                    yaxis_title="C-Score",
                    yaxis=dict(range=[0, 5]),
                    shapes=[
                        dict(
                            type="rect",
                            xref="paper",
                            yref="y",
                            x0=0,
                            y0=0,
                            x1=1,
                            y1=2,
                            fillcolor="rgba(0,255,0,0.1)",
                            line=dict(width=0),
                        ),
                        dict(
                            type="rect",
                            xref="paper",
                            yref="y",
                            x0=0,
                            y0=2,
                            x1=1,
                            y1=4,
                            fillcolor="rgba(255,255,0,0.1)",
                            line=dict(width=0),
                        ),
                        dict(
                            type="rect",
                            xref="paper",
                            yref="y",
                            x0=0,
                            y0=4,
                            x1=1,
                            y1=5,
                            fillcolor="rgba(255,0,0,0.1)",
                            line=dict(width=0),
                        ),
                    ],
                )

            st.plotly_chart(fig_c_score, use_container_width=True)

            # C-score breakdown for selected year
            selected_c_year_index = st.selectbox(
                "Select Year for C-Score Components:",
                options=list(range(len(c_years))),
                format_func=lambda x: c_years[x],
            )

            if selected_c_year_index is not None:
                selected_components = c_components[selected_c_year_index]
                selected_year = c_years[selected_c_year_index]

                st.write(f"### C-Score Breakdown for {selected_year}")

                component_df = pd.DataFrame(
                    {
                        "Component": list(selected_components.keys()),
                        "Value": list(selected_components.values()),
                    }
                )

                fig_breakdown = px.bar(
                    component_df,
                    x="Component",
                    y="Value",
                    color="Value",
                    color_continuous_scale=["green", "red"],
                    range_color=[0, 1],
                )

                st.plotly_chart(fig_breakdown, use_container_width=True)

                st.markdown(
                    """
                **Giải thích C-Score:**
                - Điểm số dao động từ 0 (rủi ro thấp nhất) đến 5 (rủi ro cao nhất)
                - Mỗi điểm phản ánh một dấu hiệu cảnh báo tiềm ẩn:
                    - Accruals > Dòng tiền hoạt động: Có thể có dấu hiệu điều chỉnh lợi nhuận
                    - Đòn bẩy tăng: Rủi ro tài chính cao hơn
                    - Thanh khoản giảm: Có thể gặp khó khăn về dòng tiền
                    - Pha loãng cổ phiếu: Giá trị cổ phiếu có thể bị giảm
                    - Biên lợi nhuận gộp giảm: Áp lực cạnh tranh hoặc chi phí tăng
                - Điểm càng cao càng cho thấy nguy cơ gặp khó khăn tài chính lớn hơn
                """
                )

        except Exception as e:
            st.warning(f"Unable to calculate C-Score: {str(e)}")

except Exception as e:
    st.error(f"An error occurred: {str(e)}")
