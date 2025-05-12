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
                    (
                        latest_data["Hiệu suất sử dụng tài sản"]
                        - prev_data["Hiệu suất sử dụng tài sản"]
                    )
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
            assessment += f"- **Hiệu suất sử dụng tài sản**: {latest_data['Hiệu suất sử dụng tài sản']:.2f}\n\n"
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
            "Chỉ số": [
                "ROE",
                "Biên lợi nhuận ròng",
                "Hiệu suất sử dụng tài sản",
                "Đòn bẩy tài chính",
            ],
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
                colors = [
                    "red" if z < 1.81 else "yellow" if z < 2.99 else "green" for z in z_scores
                ]

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
                    index=len(z_years) - 1,  # Default to the most recent year
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
