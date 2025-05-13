from email.policy import default
from operator import index

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from vnstock import Vnstock


def display_dupont_analysis(stock):
    if stock in [
        "ABB",
        "ACB",
        "BAB",
        "BID",
        "BVB",
        "CTG",
        "EIB",
        "EVF",
        "HDB",
        "KLB",
        "LPB",
        "MBB",
        "MSB",
        "NAB",
        "NVB",
        "OCB",
        "PGB",
        "SGB",
        "SHB",
        "SSB",
        "STB",
        "TCB",
        "TIN",
        "TPB",
        "VAB",
        "VBB",
        "VCB",
        "VIB",
        "VPB",
    ]:
        st.warning("Chức năng này không hỗ trợ cho ngân hàng.")
        return
    else:
        vn_stock = Vnstock().stock(symbol=stock, source="VCI")
        is_df = vn_stock.finance.income_statement(period="year", lang="en").head(8)
        bs_df = vn_stock.finance.balance_sheet(period="year", lang="en").head(8)
        cf_df = vn_stock.finance.cash_flow(period="year", lang="en").head(8)

        """
        Hiển thị phân tích DuPont cho một công ty dựa trên dữ liệu bảng cân đối kế toán và báo cáo kết quả hoạt động kinh doanh.
        """
        # Lấy danh sách các năm từ dữ liệu bảng cân đối kế toán
        years = sorted(bs_df["yearReport"].unique(), reverse=True)

        # Kiểm tra xem có đủ dữ liệu không
        if len(years) < 2:
            st.warning("Không đủ dữ liệu để thực hiện phân tích DuPont.")
            return

        # Tiêu đề

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
                "Hiệu suất sử dụng tài sản": st.column_config.TextColumn(
                    "Hiệu suất sử dụng tài sản"
                ),
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

        # Chuyển đổi dữ liệu về float để vẽ biểu đồ
        numeric_dupont_df = dupont_df.copy()
        for col in [
            "ROE",
            "ROA",
            "Gánh nặng thuế",
            "Gánh nặng lãi vay",
            "Biên lợi nhuận hoạt động",
            "Hiệu suất sử dụng tài sản",
            "Đòn bẩy tài chính",
        ]:
            numeric_dupont_df[col] = numeric_dupont_df[col].astype(float)

        # Màu sắc dịu mắt hơn (pastel)
        pastel_colors = {
            "Gánh nặng thuế": "#8dd3c7",  # teal pastel
            "Gánh nặng lãi vay": "#b3cde3",  # blue pastel
            "Biên lợi nhuận hoạt động": "#bebada",  # purple pastel
            "Hiệu suất sử dụng tài sản": "#fdb462",  # orange pastel
            "Đòn bẩy tài chính": "#fb8072",  # red pastel
            "ROE": "#333366",  # dark blue
            "ROA": "#888888",  # gray
        }

        # Tạo biểu đồ: các thành phần ROE nâng cao là cột nhóm (không chồng), ROE và ROA là đường
        fig = go.Figure()

        # Thêm các thành phần ROE nâng cao (grouped bar)
        fig.add_trace(
            go.Bar(
                x=numeric_dupont_df["Năm"],
                y=numeric_dupont_df["Gánh nặng thuế"] * 100,
                name="Gánh nặng thuế (%)",
                marker_color=pastel_colors["Gánh nặng thuế"],
            )
        )
        fig.add_trace(
            go.Bar(
                x=numeric_dupont_df["Năm"],
                y=numeric_dupont_df["Gánh nặng lãi vay"] * 100,
                name="Gánh nặng lãi vay (%)",
                marker_color=pastel_colors["Gánh nặng lãi vay"],
            )
        )
        fig.add_trace(
            go.Bar(
                x=numeric_dupont_df["Năm"],
                y=numeric_dupont_df["Biên lợi nhuận hoạt động"] * 100,
                name="Biên LN hoạt động (%)",
                marker_color=pastel_colors["Biên lợi nhuận hoạt động"],
            )
        )
        fig.add_trace(
            go.Bar(
                x=numeric_dupont_df["Năm"],
                y=numeric_dupont_df["Hiệu suất sử dụng tài sản"] * 100,
                name="Hiệu suất TS (%)",
                marker_color=pastel_colors["Hiệu suất sử dụng tài sản"],
            )
        )
        fig.add_trace(
            go.Bar(
                x=numeric_dupont_df["Năm"],
                y=numeric_dupont_df["Đòn bẩy tài chính"] * 100,
                name="Đòn bẩy TC (%)",
                marker_color=pastel_colors["Đòn bẩy tài chính"],
            )
        )

        # Thêm đường ROE
        fig.add_trace(
            go.Scatter(
                x=numeric_dupont_df["Năm"],
                y=numeric_dupont_df["ROE"] * 100,
                mode="lines+markers",
                name="ROE (%)",
                line=dict(color=pastel_colors["ROE"], width=3),
                yaxis="y2",
            )
        )

        # Thêm đường ROA
        fig.add_trace(
            go.Scatter(
                x=numeric_dupont_df["Năm"],
                y=numeric_dupont_df["ROA"] * 100,
                mode="lines+markers",
                name="ROA (%)",
                line=dict(color=pastel_colors["ROA"], width=3, dash="dot"),
                yaxis="y2",
            )
        )

        # Cập nhật layout với 2 trục y, cột dạng group
        fig.update_layout(
            barmode="group",
            title="Phân tích ROE nâng cao (DuPont mở rộng) qua các năm",
            xaxis_title="Năm",
            yaxis=dict(
                title="Thành phần ROE (%)",
                showgrid=True,
                zeroline=True,
            ),
            yaxis2=dict(
                title="ROE/ROA (%)",
                overlaying="y",
                side="right",
                showgrid=False,
                zeroline=False,
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="x unified",
        )

        st.plotly_chart(fig, use_container_width=True)

        # Phân tích sự thay đổi của ROE qua các năm
        st.subheader("4. Phân tích thay đổi ROE (DuPont mở rộng)")

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

            # DuPont mở rộng: ROE = Tax Burden × Interest Burden × Operating Margin × Asset Turnover × Equity Multiplier
            tb_c = current_year_data["Gánh nặng thuế"]
            tb_p = prev_year_data["Gánh nặng thuế"]
            ib_c = current_year_data["Gánh nặng lãi vay"]
            ib_p = prev_year_data["Gánh nặng lãi vay"]
            om_c = current_year_data["Biên lợi nhuận hoạt động"]
            om_p = prev_year_data["Biên lợi nhuận hoạt động"]
            at_c = current_year_data["Hiệu suất sử dụng tài sản"]
            at_p = prev_year_data["Hiệu suất sử dụng tài sản"]
            em_c = current_year_data["Đòn bẩy tài chính"]
            em_p = prev_year_data["Đòn bẩy tài chính"]

            roe_current = tb_c * ib_c * om_c * at_c * em_c
            roe_prev = tb_p * ib_p * om_p * at_p * em_p
            roe_change = roe_current - roe_prev
            roe_change_percent = (roe_change / abs(roe_prev)) * 100 if roe_prev != 0 else 0

            # Ảnh hưởng từng thành phần (phân rã theo phương pháp logarit vi phân)
            # ΔROE ≈ (ΔTB/TB) + (ΔIB/IB) + (ΔOM/OM) + (ΔAT/AT) + (ΔEM/EM)
            effect_tb = (tb_c - tb_p) * ib_p * om_p * at_p * em_p
            effect_ib = tb_c * (ib_c - ib_p) * om_p * at_p * em_p
            effect_om = tb_c * ib_c * (om_c - om_p) * at_p * em_p
            effect_at = tb_c * ib_c * om_c * (at_c - at_p) * em_p
            effect_em = tb_c * ib_c * om_c * at_c * (em_c - em_p)
            total_effect = effect_tb + effect_ib + effect_om + effect_at + effect_em

            # Tạo biểu đồ waterfall cho sự thay đổi ROE mở rộng
            waterfall_data = {
                "Chỉ số": [
                    "ROE " + str(prev_year),
                    "Gánh nặng thuế",
                    "Gánh nặng lãi vay",
                    "Biên LN hoạt động",
                    "Hiệu suất TS",
                    "Đòn bẩy TC",
                    "ROE " + str(selected_year),
                ],
                "Giá trị": [
                    roe_prev * 100,
                    effect_tb * 100,
                    effect_ib * 100,
                    effect_om * 100,
                    effect_at * 100,
                    effect_em * 100,
                    roe_current * 100,
                ],
            }

            waterfall_df = pd.DataFrame(waterfall_data)

            fig_waterfall = go.Figure(
                go.Waterfall(
                    name="Phân tích thay đổi ROE mở rộng",
                    orientation="v",
                    measure=[
                        "absolute",
                        "relative",
                        "relative",
                        "relative",
                        "relative",
                        "relative",
                        "total",
                    ],
                    x=waterfall_df["Chỉ số"],
                    textposition="outside",
                    text=[f"{val:.2f}%" for val in waterfall_df["Giá trị"]],
                    y=waterfall_df["Giá trị"],
                    connector={"line": {"color": "rgb(63, 63, 63)"}},
                )
            )

            fig_waterfall.update_layout(
                title=f"Phân tích thay đổi ROE (DuPont mở rộng) từ năm {prev_year} đến năm {selected_year}",
                showlegend=False,
            )

            st.plotly_chart(fig_waterfall, use_container_width=True)

            # Hiển thị bảng phân tích
            st.markdown(
                f"""
            ### Phân tích sự thay đổi ROE (DuPont mở rộng) từ {prev_year} đến {selected_year}
            
            - ROE năm {prev_year}: **{roe_prev*100:.2f}%**
            - ROE năm {selected_year}: **{roe_current*100:.2f}%**
            - Thay đổi: **{roe_change*100:.2f}%** ({roe_change_percent:.2f}%)
            
            #### Ảnh hưởng của từng thành phần:
            
            1. **Gánh nặng thuế**: {effect_tb*100:.2f}% ({effect_tb/roe_change*100 if roe_change!=0 else 0:.2f}% tổng thay đổi)
            2. **Gánh nặng lãi vay**: {effect_ib*100:.2f}% ({effect_ib/roe_change*100 if roe_change!=0 else 0:.2f}% tổng thay đổi)
            3. **Biên lợi nhuận hoạt động**: {effect_om*100:.2f}% ({effect_om/roe_change*100 if roe_change!=0 else 0:.2f}% tổng thay đổi)
            4. **Hiệu suất sử dụng tài sản**: {effect_at*100:.2f}% ({effect_at/roe_change*100 if roe_change!=0 else 0:.2f}% tổng thay đổi)
            5. **Đòn bẩy tài chính**: {effect_em*100:.2f}% ({effect_em/roe_change*100 if roe_change!=0 else 0:.2f}% tổng thay đổi)
            
            > Lưu ý: Có thể có chênh lệch nhỏ do làm tròn số. Tổng ảnh hưởng: {total_effect*100:.2f}%, ROE thay đổi thực tế: {roe_change*100:.2f}%.
            """
            )

    # Load and prepare data


@st.cache_data
def load_data(stock):
    vn_stock = Vnstock().stock(symbol=stock, source="VCI")
    is_df = vn_stock.finance.income_statement(period="year", lang="en").head(8)
    bs_df = vn_stock.finance.balance_sheet(period="year", lang="en").head(8)
    cf_df = vn_stock.finance.cash_flow(period="year", lang="en").head(8)

    # Reverse rows to have chronological order
    cf_df = cf_df.iloc[::-1].reset_index(drop=True)
    is_df = is_df.iloc[::-1].reset_index(drop=True)
    bs_df = bs_df.iloc[::-1].reset_index(drop=True)

    return cf_df, is_df, bs_df


def display_stock_score(stock):
    if stock in [
        "ABB",
        "ACB",
        "BAB",
        "BID",
        "BVB",
        "CTG",
        "EIB",
        "EVF",
        "HDB",
        "KLB",
        "LPB",
        "MBB",
        "MSB",
        "NAB",
        "NVB",
        "OCB",
        "PGB",
        "SGB",
        "SHB",
        "SSB",
        "STB",
        "TCB",
        "TIN",
        "TPB",
        "VAB",
        "VBB",
        "VCB",
        "VIB",
        "VPB",
    ]:
        st.warning("Chức năng này không hỗ trợ cho ngân hàng.")
        return
    else:
        st.markdown(
            """
        Bảng điều khiển này phân tích sức khỏe tài chính của HPG dựa trên các mô hình tài chính:
        - **Piotroski F-Score**: Đánh giá sức mạnh tài chính (thang điểm 0-9)
        - **Altman Z-Score**: Dự báo rủi ro phá sản
        - **Beneish M-Score**: Phát hiện khả năng gian lận lợi nhuận
        """
        )
        try:
            cf_df, is_df, bs_df = load_data(stock)

            # Create tabs for the different sections
            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                [
                    "Overview",
                    "Piotroski F-Score",
                    "Altman Z-Score",
                    "Beneish M-Score",
                    "DuPont Analysis",
                ]
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
                    fig_revenue.update_layout(
                        xaxis_title="Year", yaxis_title="Revenue (Billion VND)"
                    )
                    st.plotly_chart(fig_revenue, use_container_width=True)

                    # Create net profit chart
                    fig_profit = px.line(
                        is_df,
                        x="yearReport",
                        y="Net Profit For the Year",
                        title="Net Profit (Billion VND)",
                        markers=True,
                    )
                    fig_profit.update_layout(
                        xaxis_title="Year", yaxis_title="Net Profit (Billion VND)"
                    )
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

                    scores["Decreasing LT Debt Ratio"] = (
                        1 if lt_debt_ratio < prev_lt_debt_ratio else 0
                    )
                    total_score += scores["Decreasing LT Debt Ratio"]

                    # Current Ratio
                    current_assets = bs_df.loc[year_index, "CURRENT ASSETS (Bn. VND)"]
                    current_liabilities = bs_df.loc[year_index, "Current liabilities (Bn. VND)"]
                    current_ratio = current_assets / current_liabilities

                    prev_current_assets = bs_df.loc[year_index - 1, "CURRENT ASSETS (Bn. VND)"]
                    prev_current_liabilities = bs_df.loc[
                        year_index - 1, "Current liabilities (Bn. VND)"
                    ]
                    prev_current_ratio = prev_current_assets / prev_current_liabilities

                    scores["Increasing Current Ratio"] = (
                        1 if current_ratio > prev_current_ratio else 0
                    )
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

                    scores["Increasing Gross Margin"] = (
                        1 if gross_margin > prev_gross_margin else 0
                    )
                    total_score += scores["Increasing Gross Margin"]

                    # Asset Turnover
                    asset_turnover = net_sales / total_assets
                    prev_asset_turnover = prev_net_sales / prev_total_assets

                    scores["Increasing Asset Turnover"] = (
                        1 if asset_turnover > prev_asset_turnover else 0
                    )
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
                        dict(
                            x=0.5, y=4.5, xref="paper", yref="y", text="Moderate", showarrow=False
                        ),
                        dict(x=0.5, y=7.5, xref="paper", yref="y", text="Strong", showarrow=False),
                    ],
                )

                st.plotly_chart(fig_f_score, use_container_width=True)

                # F-score breakdown for selected year
                # Show F-Score breakdown as a table for the 5 most recent years
                num_years = min(10, len(f_score_years))
                recent_years = f_score_years[-num_years:]
                recent_details = f_score_details[-num_years:]

                # Prepare DataFrame for display
                criteria = list(recent_details[-1].keys()) if recent_details else []
                data = {"Tiêu chí": criteria}
                for i, year in enumerate(recent_years):
                    data[str(year)] = [recent_details[i][c] for c in criteria]

                fscore_df = pd.DataFrame(data)

                # Column configs: first column is text, others are boolean (0/1)
                column_config = {
                    "Tiêu chí": st.column_config.TextColumn("Tiêu chí"),
                }
                for year in recent_years:
                    column_config[str(year)] = st.column_config.CheckboxColumn(
                        f"{year}",
                        help="1: Đạt tiêu chí, 0: Không đạt",
                    )

                st.dataframe(
                    fscore_df,
                    column_config=column_config,
                    hide_index=True,
                    use_container_width=True,
                )

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

                def get_z_score_components(year_index, is_df, bs_df):
                    """Extract and calculate Altman Z-Score components for a given year index."""
                    total_assets = bs_df.loc[year_index, "TOTAL ASSETS (Bn. VND)"]
                    current_assets = bs_df.loc[year_index, "CURRENT ASSETS (Bn. VND)"]
                    current_liabilities = bs_df.loc[year_index, "Current liabilities (Bn. VND)"]
                    retained_earnings = bs_df.loc[year_index, "Undistributed earnings (Bn. VND)"]
                    ebit = is_df.loc[year_index, "Profit before tax"]
                    total_liabilities = bs_df.loc[year_index, "LIABILITIES (Bn. VND)"]
                    equity = bs_df.loc[year_index, "OWNER'S EQUITY(Bn.VND)"]
                    sales = is_df.loc[year_index, "Net Sales"]

                    working_capital = current_assets - current_liabilities

                    # Avoid division by zero
                    if total_assets == 0 or total_liabilities == 0:
                        return None

                    A = working_capital / total_assets
                    B = retained_earnings / total_assets
                    C = ebit / total_assets
                    D = equity / total_liabilities
                    E = sales / total_assets

                    z_score = 1.2 * A + 1.4 * B + 3.3 * C + 0.6 * D + 1.0 * E
                    components = {
                        "Working Capital/Total Assets": 1.2 * A,
                        "Retained Earnings/Total Assets": 1.4 * B,
                        "EBIT/Total Assets": 3.3 * C,
                        "Equity/Total Liabilities": 0.6 * D,
                        "Sales/Total Assets": 1.0 * E,
                    }
                    raw_components = (A, B, C, D, E)
                    return z_score, components, raw_components

                def diagnose_z_score_components(A, B, C, D, E):
                    """Return list of warning messages based on Z-Score component values."""
                    reasons = []
                    if A < 0.1:
                        reasons.append(
                            "🔴 *Working Capital / Total Assets* rất thấp (<0.1): Công ty có thể gặp khó khăn thanh toán ngắn hạn, rủi ro mất khả năng thanh toán."
                        )
                    elif A < 0.2:
                        reasons.append(
                            "🟠 *Working Capital / Total Assets* thấp (<0.2): Khả năng thanh khoản yếu, cần chú ý dòng tiền hoạt động."
                        )
                    if B < 0.1:
                        reasons.append(
                            "🔴 *Retained Earnings / Total Assets* rất thấp (<0.1): Công ty chưa tích lũy được lợi nhuận, nền tảng tài chính yếu."
                        )
                    elif B < 0.3:
                        reasons.append(
                            "🟠 *Retained Earnings / Total Assets* thấp (<0.3): Lợi nhuận giữ lại chưa cao, tích lũy vốn còn hạn chế."
                        )
                    if C < 0.05:
                        reasons.append(
                            "🔴 *EBIT / Total Assets* rất thấp (<0.05): Hiệu quả sinh lời từ tài sản rất kém, rủi ro kinh doanh cao."
                        )
                    elif C < 0.1:
                        reasons.append(
                            "🟠 *EBIT / Total Assets* thấp (<0.1): Hiệu quả sử dụng tài sản còn hạn chế."
                        )
                    if D < 0.3:
                        reasons.append(
                            "🔴 *Equity / Total Liabilities* rất thấp (<0.3): Đòn bẩy tài chính rất cao, rủi ro nợ lớn."
                        )
                    elif D < 0.6:
                        reasons.append(
                            "🟠 *Equity / Total Liabilities* thấp (<0.6): Đòn bẩy tài chính cao, cần kiểm soát rủi ro nợ vay."
                        )
                    if E < 0.7:
                        reasons.append(
                            "🟠 *Sales / Total Assets* thấp (<0.7): Hiệu quả sử dụng tài sản tạo doanh thu còn thấp."
                        )
                    elif E > 1.5:
                        reasons.append(
                            "🟢 *Sales / Total Assets* rất cao (>1.5): Công ty sử dụng tài sản hiệu quả để tạo doanh thu."
                        )
                    return reasons

                # Calculate Z-Score for all years
                z_scores, z_components, z_years, z_raws = [], [], [], []
                for i in range(len(is_df)):
                    year = is_df.loc[i, "yearReport"]
                    result = get_z_score_components(i, is_df, bs_df)
                    if result is not None:
                        z, comp, raw = result
                        z_scores.append(z)
                        z_components.append(comp)
                        z_years.append(year)
                        z_raws.append(raw)

                # Visualization
                colors = [
                    "red" if z < 1.81 else "yellow" if z < 2.99 else "green" for z in z_scores
                ]
                fig_z_score = go.Figure()
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
                        dict(
                            x=0.5,
                            y=0.9,
                            xref="paper",
                            yref="y",
                            text="Distress Zone",
                            showarrow=False,
                        ),
                        dict(
                            x=0.5, y=2.4, xref="paper", yref="y", text="Grey Zone", showarrow=False
                        ),
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
                    index=len(z_years) - 1,
                )

                if selected_z_year_index is not None:
                    selected_components = z_components[selected_z_year_index]
                    selected_z_year = z_years[selected_z_year_index]
                    selected_z = z_scores[selected_z_year_index]
                    selected_raw = z_raws[selected_z_year_index]

                    st.write(f"### Z-Score Breakdown for {selected_z_year}: {selected_z:.2f}")

                    # Compare with previous year if possible
                    if selected_z_year_index > 0:
                        prev_components = z_components[selected_z_year_index - 1]
                        prev_z_year = z_years[selected_z_year_index - 1]
                        prev_z = z_scores[selected_z_year_index - 1]

                        compare_df = pd.DataFrame(
                            {
                                "Component": list(selected_components.keys()),
                                f"{selected_z_year}": list(selected_components.values()),
                                f"{prev_z_year}": list(prev_components.values()),
                            }
                        )
                        compare_df["Change"] = (
                            (compare_df[f"{selected_z_year}"] - compare_df[f"{prev_z_year}"])
                            / compare_df[f"{prev_z_year}"].replace(0, np.nan)
                        ) * 100

                        st.dataframe(
                            compare_df.style.format(
                                {
                                    f"{selected_z_year}": "{:.3f}",
                                    f"{prev_z_year}": "{:.3f}",
                                    "Change": "{:+.2f}%",
                                }
                            ),
                            use_container_width=True,
                        )

                        fig_z_breakdown = px.bar(
                            compare_df,
                            x="Component",
                            y=f"{selected_z_year}",
                            color=f"{selected_z_year}",
                            color_continuous_scale="RdYlGn",
                        )
                        fig_z_breakdown.update_layout(
                            title=f"Z-Score Components for {selected_z_year}",
                            xaxis_title="Component",
                            yaxis_title="Value",
                        )
                        st.plotly_chart(fig_z_breakdown, use_container_width=True)

                        fig_z_change = px.bar(
                            compare_df,
                            x="Component",
                            y="Change",
                            color="Change",
                            color_continuous_scale="RdYlGn",
                        )
                        fig_z_change.update_layout(
                            title=f"Change in Z-Score Components: {prev_z_year} → {selected_z_year}",
                            xaxis_title="Component",
                            yaxis_title="Change (%)",
                        )
                        st.plotly_chart(fig_z_change, use_container_width=True)

                        st.markdown(
                            f"**Z-Score {prev_z_year}: {prev_z:.2f} → {selected_z_year}: {selected_z:.2f} ({selected_z - prev_z:+.2f})**"
                        )
                    else:
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

                    # Diagnosis
                    reasons = diagnose_z_score_components(*selected_raw)
                    if reasons:
                        st.markdown("#### Giải thích chi tiết các điểm yếu theo Altman Z-Score:")
                        for r in reasons:
                            st.markdown(f"- {r}")
                    else:
                        st.markdown(
                            "✅ Không có dấu hiệu cảnh báo lớn theo các thành phần Z-Score."
                        )

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
                    # Handle missing columns for SGA calculation
                    selling_expenses_col = (
                        "Selling Expenses" if "Selling Expenses" in is_df.columns else None
                    )
                    admin_expenses_col = (
                        "General & Admin Expenses"
                        if "General & Admin Expenses" in is_df.columns
                        else None
                    )

                    def get_expense(df, idx, col):
                        return df.loc[idx, col] if col and col in df.columns else 0

                    sga = get_expense(is_df, year_index, selling_expenses_col) + get_expense(
                        is_df, year_index, admin_expenses_col
                    )
                    prev_sga = get_expense(
                        is_df, year_index - 1, selling_expenses_col
                    ) + get_expense(is_df, year_index - 1, admin_expenses_col)

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
                        index=len(m_years) - 1,  # Default to the most recent year
                    )

                    if selected_m_year_index is not None and selected_m_year_index < len(
                        m_components
                    ):
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

                        # Add comparison chart with previous year if possible
                        if selected_m_year_index > 0:
                            prev_m_components = m_components[selected_m_year_index - 1]
                            prev_m_year = m_years[selected_m_year_index - 1]
                            compare_df = pd.DataFrame(
                                {
                                    "Component": list(selected_m_components.keys()),
                                    f"{prev_m_year}": [
                                        prev_m_components[k] for k in selected_m_components.keys()
                                    ],
                                    f"{selected_m_year}": [
                                        selected_m_components[k]
                                        for k in selected_m_components.keys()
                                    ],
                                }
                            )
                            compare_df["Change (%)"] = (
                                (compare_df[f"{selected_m_year}"] - compare_df[f"{prev_m_year}"])
                                / compare_df[f"{prev_m_year}"].replace(0, np.nan)
                            ) * 100

                            fig_compare = go.Figure()
                            fig_compare.add_trace(
                                go.Bar(
                                    x=compare_df["Component"],
                                    y=compare_df[f"{prev_m_year}"],
                                    name=f"{prev_m_year}",
                                    marker_color="lightgray",
                                )
                            )
                            fig_compare.add_trace(
                                go.Bar(
                                    x=compare_df["Component"],
                                    y=compare_df[f"{selected_m_year}"],
                                    name=f"{selected_m_year}",
                                    marker_color="royalblue",
                                )
                            )
                            fig_compare.update_layout(
                                barmode="group",
                                title=f"So sánh các thành phần M-Score: {prev_m_year} vs {selected_m_year}",
                                xaxis_title="Component",
                                yaxis_title="Value",
                                height=400,
                            )
                            st.plotly_chart(fig_compare, use_container_width=True)

                            # Hiển thị bảng thay đổi phần trăm
                            st.dataframe(
                                compare_df[
                                    [
                                        "Component",
                                        f"{prev_m_year}",
                                        f"{selected_m_year}",
                                        "Change (%)",
                                    ]
                                ].style.format(
                                    {
                                        f"{prev_m_year}": "{:.3f}",
                                        f"{selected_m_year}": "{:.3f}",
                                        "Change (%)": "{:+.2f}%",
                                    }
                                ),
                                use_container_width=True,
                            )

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

                        # Đánh giá tự động các thành phần M-Score
                        def beneish_component_assessment(components):
                            notes = []
                            if components["Days Sales in Receivables Index (DSRI)"] > 1.031:
                                notes.append(
                                    "- **DSRI** cao: Doanh thu chưa thu tiền tăng bất thường."
                                )
                            if components["Gross Margin Index (GMI)"] > 1.014:
                                notes.append(
                                    "- **GMI** cao: Biên lợi nhuận gộp giảm, cần chú ý chi phí/doanh thu."
                                )
                            if components["Asset Quality Index (AQI)"] > 1.040:
                                notes.append(
                                    "- **AQI** cao: Chất lượng tài sản giảm, tài sản không sinh lời tăng."
                                )
                            if components["Sales Growth Index (SGI)"] > 1.134:
                                notes.append(
                                    "- **SGI** cao: Tăng trưởng doanh thu mạnh, cần kiểm tra chất lượng tăng trưởng."
                                )
                            if components["Depreciation Index (DEPI)"] < 0.804:
                                notes.append(
                                    "- **DEPI** thấp: Tỷ lệ khấu hao giảm, có thể làm đẹp lợi nhuận."
                                )
                            if components["SG&A Expense Index (SGAI)"] > 1.054:
                                notes.append(
                                    "- **SGAI** cao: Chi phí bán hàng & quản lý tăng nhanh hơn doanh thu."
                                )
                            if components["Total Accruals to Total Assets (TATA)"] > 0.018:
                                notes.append(
                                    "- **TATA** cao: Khoản dồn tích lớn, có thể điều chỉnh lợi nhuận."
                                )
                            if components["Leverage Index (LVGI)"] > 1.037:
                                notes.append(
                                    "- **LVGI** cao: Đòn bẩy tài chính tăng, rủi ro tài chính cao hơn."
                                )
                            if not notes:
                                notes.append(
                                    "✅ Không có dấu hiệu bất thường nổi bật theo các chỉ số Beneish."
                                )
                            return notes

                        # Hiển thị đánh giá Beneish cho năm được chọn
                        st.markdown("#### Đánh giá nhanh các chỉ số Beneish:")
                        for note in beneish_component_assessment(selected_m_components):
                            st.markdown(note)

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
                        index=len(dupont_years) - 1,  # Default to the most recent year
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
                        components["Increasing Leverage"] = (
                            1 if leverage_current > leverage_prev else 0
                        )
                        c_score += components["Increasing Leverage"]

                        # Check liquidity change
                        current_assets = bs_df.loc[year_index, "CURRENT ASSETS (Bn. VND)"]
                        current_liabilities = bs_df.loc[
                            year_index, "Current liabilities (Bn. VND)"
                        ]
                        prev_current_assets = bs_df.loc[year_index - 1, "CURRENT ASSETS (Bn. VND)"]
                        prev_current_liabilities = bs_df.loc[
                            year_index - 1, "Current liabilities (Bn. VND)"
                        ]

                        current_ratio = current_assets / current_liabilities
                        prev_current_ratio = prev_current_assets / prev_current_liabilities
                        components["Decreasing Liquidity"] = (
                            1 if current_ratio < prev_current_ratio else 0
                        )
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
                        colors = [
                            "green" if c <= 1 else "yellow" if c <= 3 else "red" for c in c_scores
                        ]

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
                        index=len(c_years) - 1,  # Default to the most recent year
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
            st.error(f"Error fetching data for {stock}: {str(e)}")
