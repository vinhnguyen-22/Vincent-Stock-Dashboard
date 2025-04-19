import base64
import io
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from PIL import Image
from streamlit_option_menu import option_menu
from vnstock.explorer.fmarket.fund import Fund

fund = Fund()


def custom_metric(label, value, delta=None, prefix="", suffix=""):
    """Hiển thị metric tùy chỉnh với styling đẹp hơn"""
    delta_html = ""
    if delta is not None:
        delta_class = "positive-delta" if float(delta.replace("%", "")) >= 0 else "negative-delta"
        delta_symbol = "▲" if float(delta.replace("%", "")) >= 0 else "▼"
        delta_html = (
            f'<span class="custom-metric-delta {delta_class}">{delta_symbol} {delta}</span>'
        )

    st.markdown(
        f"""
    <div class="custom-metric-container">
        <div class="custom-metric-label">{label}</div>
        <div class="custom-metric-value">{prefix}{value}{suffix} {delta_html}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ----- CACHING AND DATA LOADING FUNCTIONS -----


@st.cache_data(ttl=3600)
def get_fund_list():
    """Lấy danh sách các quỹ từ API"""
    try:
        return fund.listing()
    except Exception as e:
        st.error(f"Không thể kết nối đến API: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_fund_detail(fund_code):
    """Lấy thông tin chi tiết của quỹ từ API"""
    try:
        url = f"https://api.fmarket.vn/home/product/{fund_code}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Lỗi khi lấy thông tin quỹ {fund_code}: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"Không thể kết nối đến API: {str(e)}")
        return {}


@st.cache_data(ttl=3600)
def process_fund_data(fund_detail):
    """Xử lý dữ liệu quỹ thành các DataFrame riêng biệt"""
    try:
        if not fund_detail or "data" not in fund_detail:
            return None, None, None, None, None

        data = fund_detail["data"]

        # Danh mục cổ phiếu
        holdings_df = pd.DataFrame(data.get("productTopHoldingList", []))

        # Phân bổ ngành
        industry_df = pd.DataFrame(data.get("productIndustriesHoldingList", []))

        # Phân bổ tài sản
        asset_df = pd.DataFrame(data.get("productAssetHoldingList", []))

        # Hiệu suất NAV
        nav_df = pd.DataFrame(fund.details.nav_report(data.get("shortName")))

        # Thông tin tổng quan

        return holdings_df, industry_df, asset_df, nav_df
    except Exception as e:
        st.error(f"Lỗi khi xử lý dữ liệu quỹ: {str(e)}")
        return None, None, None, None, None


@st.cache_data(ttl=3600)
def get_all_funds_data(funds_df, fund_type=None, with_progress=False):
    """Lấy dữ liệu của tất cả các quỹ với hỗ trợ hiển thị tiến trình và timeout cho mỗi request"""

    # Lọc quỹ theo loại nếu cần
    if fund_type and fund_type != "Tất cả":
        funds_df = funds_df[funds_df["fund_type"] == fund_type]

    all_holdings = []
    all_industries = []
    all_assets = []

    total_funds = len(funds_df)
    failed_funds = []

    if total_funds == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), []

    # Tạo thanh tiến trình nếu được yêu cầu
    progress = st.progress(0) if with_progress else None
    status_text = st.empty() if with_progress else None

    for i, (_, fund_row) in enumerate(funds_df.iterrows()):
        fund_code = fund_row["short_name"]
        try:
            if status_text:
                status_text.text(f"Đang xử lý quỹ {i+1}/{total_funds}: {fund_code}")

            # Gọi API với timeout
            fund_detail = get_fund_detail(fund_code)
            holdings_df, industry_df, asset_df, nav_df = process_fund_data(fund_detail)

            # Xử lý danh mục cổ phiếu
            if holdings_df is not None and not holdings_df.empty:
                holdings_df["fund_code"] = fund_code
                holdings_df["fund_name"] = fund_row["name"]
                holdings_df["fund_type"] = fund_row["fund_type"]
                # Thêm thông tin NAV của quỹ
                holdings_df["fund_nav"] = fund_row["nav"]
                holdings_df["fund_aum"] = fund_row.get("aum", None)
                holdings_df["nav_date"] = fund_row.get("nav_date", None)
                all_holdings.append(holdings_df)

            # Xử lý phân bổ ngành
            if industry_df is not None and not industry_df.empty:
                industry_df["fund_code"] = fund_code
                industry_df["fund_name"] = fund_row["name"]
                industry_df["fund_type"] = fund_row["fund_type"]
                industry_df["fund_nav"] = fund_row["nav"]
                industry_df["fund_aum"] = fund_row.get("aum", None)
                all_industries.append(industry_df)

            # Xử lý phân bổ tài sản
            if asset_df is not None and not asset_df.empty:
                asset_df["fund_code"] = fund_code
                asset_df["fund_name"] = fund_row["name"]
                asset_df["fund_type"] = fund_row["fund_type"]
                asset_df["fund_nav"] = fund_row["nav"]
                asset_df["fund_aum"] = fund_row.get("aum", None)
                all_assets.append(asset_df)

        except Exception as e:
            failed_funds.append(fund_code)
            st.warning(f"Không thể lấy dữ liệu cho quỹ {fund_code}: {str(e)}")

        # Cập nhật tiến trình
        if progress:
            progress.progress((i + 1) / total_funds)

    # Xóa thanh tiến trình và thông báo
    if progress:
        progress.empty()
    if status_text:
        if failed_funds:
            status_text.text(f"Hoàn thành! Không thể lấy dữ liệu của {len(failed_funds)} quỹ.")
        else:
            status_text.text("Hoàn thành! Đã lấy dữ liệu tất cả các quỹ.")

    # Kết hợp dữ liệu
    holdings_combined = (
        pd.concat(all_holdings, ignore_index=True) if all_holdings else pd.DataFrame()
    )
    industry_combined = (
        pd.concat(all_industries, ignore_index=True) if all_industries else pd.DataFrame()
    )
    asset_combined = pd.concat(all_assets, ignore_index=True) if all_assets else pd.DataFrame()

    return holdings_combined, industry_combined, asset_combined, failed_funds


# ----- VISUALIZATION HELPER FUNCTIONS -----


def create_bar_chart(
    df,
    x,
    y,
    title,
    labels,
    text=None,
    color=None,
    orientation="v",
    height=500,
    color_discrete_sequence=None,
):
    """Tạo biểu đồ cột có thể tái sử dụng với nhiều tùy chỉnh hơn"""
    if df is None or df.empty:
        return None

    fig = px.bar(
        df,
        x=x,
        y=y,
        text=text if text else y,
        color=color,
        title=title,
        labels=labels,
        height=height,
        orientation="h" if orientation == "h" else "v",
        color_discrete_sequence=color_discrete_sequence,
    )

    # Định dạng giá trị hiển thị
    if text:
        if (
            "percent" in str(text).lower()
            or "weight" in str(text).lower()
            or "trọng" in str(text).lower()
        ):
            fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        else:
            fig.update_traces(texttemplate="%{text}", textposition="outside")

    # Sắp xếp theo thứ tự
    if orientation == "h":
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
    else:
        fig.update_layout(xaxis={"categoryorder": "total descending", "tickangle": 45})

    # Thêm tùy chỉnh layout chung
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="right", x=0.5),
    )

    return fig


def create_pie_chart(
    df,
    values,
    names,
    title,
    height=400,
    color_sequence=None,
    hole=0.3,
    show_percent=True,
    show_label=True,
):
    """Tạo biểu đồ tròn có thể tái sử dụng với nhiều tùy chỉnh hơn"""
    if df is None or df.empty:
        return None

    fig = px.pie(
        df,
        values=values,
        names=names,
        title=title,
        height=height,
        color_discrete_sequence=color_sequence,
        hole=hole,
    )

    text_info = "percent" if show_percent else ""
    if show_label:
        text_info = "label+" + text_info if text_info else "label"

    fig.update_traces(textposition="inside", textinfo=text_info)

    # Thêm tùy chỉnh layout
    fig.update_layout()

    return fig


def create_treemap(df, path, values, color, title, height=600, color_scale="Viridis"):
    """Tạo biểu đồ treemap có thể tái sử dụng với nhiều tùy chỉnh hơn"""
    if df is None or df.empty:
        return None

    fig = px.treemap(
        df,
        path=path,
        values=values,
        color=color,
        title=title,
        height=height,
        color_continuous_scale=color_scale,
        labels={values: "Tổng tỷ trọng", color: "Tỷ trọng TB (%)"},
    )
    fig.update_traces(textinfo="label+value+percent parent")

    # Thêm tùy chỉnh layout
    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig


def create_scatter_plot(
    df, x, y, title, labels, color=None, size=None, hover_name=None, trend_line=False, height=500
):
    """Tạo biểu đồ scatter với nhiều tùy chỉnh"""
    if df is None or df.empty:
        return None

    fig = px.scatter(
        df,
        x=x,
        y=y,
        color=color,
        size=size,
        hover_name=hover_name,
        title=title,
        labels=labels,
        height=height,
    )

    # Thêm đường trend nếu cần
    if trend_line:
        fig.update_layout(
            shapes=[
                {
                    "type": "line",
                    "x0": df[x].min(),
                    "y0": df[y].min(),
                    "x1": df[x].max(),
                    "y1": df[y].max(),
                    "line": {
                        "color": "lightgrey",
                        "width": 2,
                        "dash": "dash",
                    },
                }
            ]
        )

    # Thêm tùy chỉnh layout
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )

    return fig


def format_percent(value):
    """Định dạng giá trị số thành phần trăm"""
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"


def format_number(value, prefix="", suffix=""):
    """Định dạng số với dấu phân cách hàng nghìn"""
    if pd.isna(value):
        return "N/A"
    return f"{prefix}{value:,.2f}{suffix}"


# ----- LOAD DATA -----
def display_fund_data():
    # Tải danh sách quỹ
    funds_df = get_fund_list()
    # Lọc quỹ - chỉ giữ lại các loại quỹ phù hợp cho phân tích cổ phiếu
    funds_df = funds_df[~funds_df["fund_type"].isin(["Quỹ trái phiếu"])]

    if funds_df.empty:
        st.error("Không thể tải dữ liệu quỹ. Vui lòng kiểm tra kết nối và thử lại sau.")
        st.stop()

    # ----- APP LAYOUT AND NAVIGATION -----

    # Logo và tiêu đề
    st.markdown(
        """
        Dashboard phân tích danh mục đầu tư của các quỹ tại Việt Nam.
        Khám phá danh mục từng quỹ, cổ phiếu được nắm giữ nhiều nhất, và sự phân bổ ngành.
        """
    )

    # Navigation menu
    selected_tab = option_menu(
        menu_title=None,
        options=[
            "Phân tích quỹ",
            "Cổ phiếu phổ biến",
            "Phân tích ngành",
        ],
        icons=["bar-chart-fill", "graph-up", "pie-chart-fill", "cash-coin", "arrows-angle-expand"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )

    # ----- TAB 1: PHÂN TÍCH TỪNG QUỸ -----
    if selected_tab == "Phân tích quỹ":
        st.header("Phân tích chi tiết quỹ")

        # Chọn quỹ
        col1, col2 = st.columns([1, 2])

        with col1:
            # Filter theo loại quỹ
            fund_types_list = funds_df["fund_type"].unique().tolist()
            if "Quỹ trái phiếu" in fund_types_list:
                fund_types_list.remove("Quỹ trái phiếu")
            fund_types = ["Tất cả"] + sorted(fund_types_list)
            selected_fund_type = st.selectbox("Chọn loại quỹ", fund_types)

            # Lọc quỹ theo loại
            filtered_funds = (
                funds_df
                if selected_fund_type == "Tất cả"
                else funds_df[funds_df["fund_type"] == selected_fund_type]
            )

            if not filtered_funds.empty:
                # Hiển thị một searchbox để lọc quỹ
                search_term = st.text_input("Tìm kiếm quỹ", "")

                if search_term:
                    filtered_funds = filtered_funds[
                        filtered_funds["name"].str.contains(search_term, case=False)
                        | filtered_funds["short_name"].str.contains(search_term, case=False)
                    ]

                if filtered_funds.empty:
                    st.warning("Không tìm thấy quỹ nào. Vui lòng thử từ khóa khác.")
                    st.stop()

                selected_fund = st.selectbox(
                    "Chọn quỹ",
                    options=filtered_funds["short_name"].tolist(),
                    format_func=lambda x: f"{x} - {filtered_funds[filtered_funds['short_name'] == x]['name'].values[0][:40]}...",
                )
            else:
                st.error("Không có quỹ nào thuộc loại đã chọn.")
                st.stop()

        # Lấy thông tin chi tiết của quỹ
        fund_detail = get_fund_detail(selected_fund)
        holdings_df, industry_df, asset_df, nav_df = process_fund_data(fund_detail)

        # Hiển thị thông tin quỹ
        with col2:
            fund_info = filtered_funds[filtered_funds["short_name"] == selected_fund].iloc[0]
            st.markdown(f"### {fund_info['name']}")

            metrics_cols = st.columns(4)
            with metrics_cols[0]:
                custom_metric("Loại quỹ", fund_info["fund_type"])
            with metrics_cols[1]:
                custom_metric("NAV mới nhất", format_number(fund_info["nav"]), suffix=" VND")
            with metrics_cols[2]:
                delta = (
                    f"{fund_info['nav_change_previous']:.2f}%"
                    if not pd.isna(fund_info["nav_change_previous"])
                    else None
                )
                custom_metric(
                    "Thay đổi NAV (1D)",
                    format_percent(fund_info["nav_change_previous"]),
                    delta=delta,
                )
            with metrics_cols[3]:
                delta = (
                    f"{fund_info['nav_change_last_year']:.2f}%"
                    if not pd.isna(fund_info["nav_change_last_year"])
                    else None
                )
                custom_metric(
                    "Thay đổi NAV (1Y)",
                    format_percent(fund_info["nav_change_last_year"]),
                    delta=delta,
                )

        # Tab cho thông tin chi tiết
        fund_subtabs = st.tabs(
            ["Danh mục đầu tư", "Hiệu suất", "Phân bổ ngành", "Phân bổ tài sản"]
        )

        # Tab danh mục đầu tư
        with fund_subtabs[0]:
            st.subheader("Top cổ phiếu nắm giữ")
            if holdings_df is not None and not holdings_df.empty:
                # Hiển thị dữ liệu dạng bảng và biểu đồ
                col1, col2 = st.columns([2, 3])

                with col1:
                    # Sử dụng hàm tạo biểu đồ
                    fig = create_bar_chart(
                        holdings_df.head(10),
                        x=(
                            "assetPercent"
                            if "assetPercent" in holdings_df.columns
                            else "netAssetPercent"
                        ),
                        y="stockCode",
                        title=f"Top 10 cổ phiếu - {selected_fund}",
                        labels={
                            "assetPercent": "Tỷ trọng danh mục (%)",
                            "assetPercent": "Tỷ trọng danh mục (%)",
                            "stockCode": "Mã cổ phiếu",
                        },
                        text=(
                            "assetPercent"
                            if "assetPercent" in holdings_df.columns
                            else "netAssetPercent"
                        ),
                        orientation="h",
                        color_discrete_sequence=px.colors.qualitative.Plotly,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Hiển thị dữ liệu dạng bảng với styling
                    weight_col = (
                        "assetPercent"
                        if "assetPercent" in holdings_df.columns
                        else "netAssetPercent"
                    )

                    # Tính giá trị ước tính theo NAV
                    if "fund_nav" in holdings_df.columns:
                        holdings_df["estimated_value"] = (
                            holdings_df[weight_col] * fund_info["nav"] / 100
                        )

                    # Hiển thị bảng dữ liệu
                    st.dataframe(
                        holdings_df[
                            (
                                ["stockCode", weight_col, "estimated_value"]
                                if "estimated_value" in holdings_df.columns
                                else ["stockCode", weight_col]
                            )
                        ]
                        .rename(
                            columns={
                                "stockCode": "Mã CP",
                                weight_col: "Tỷ trọng (%)",
                                "estimated_value": "Giá trị ước tính (VND/CCQ)",
                            }
                        )
                        .style.format(
                            {"Tỷ trọng (%)": "{:.2f}%", "Giá trị ước tính (VND/CCQ)": "{:,.2f}"}
                        ),
                        height=400,
                        use_container_width=True,
                    )

            else:
                st.info("Không có dữ liệu về danh mục cổ phiếu của quỹ này.")

        # Tab hiệu suất
        with fund_subtabs[1]:
            st.subheader("Hiệu suất NAV theo thời gian")
            if (
                nav_df is not None
                and not nav_df.empty
                and "date" in nav_df.columns
                and ("nav" in nav_df.columns or "nav_per_unit" in nav_df.columns)
            ):
                # Chuyển đổi ngày thành datetime
                nav_df["date"] = pd.to_datetime(nav_df["date"])

                # Sắp xếp theo ngày
                nav_df = nav_df.sort_values("date")

                # Tạo các cột hiệu suất
                nav_column = "nav" if "nav" in nav_df.columns else "nav_per_unit"

                # Chuẩn hóa NAV (base 100)
                first_nav = nav_df[nav_column].iloc[0]
                nav_df["nav_normalized"] = nav_df[nav_column] / first_nav * 100

                # Tính hiệu suất theo thời gian
                nav_df["return_1d"] = nav_df[nav_column].pct_change() * 100
                nav_df["return_1w"] = (
                    nav_df[nav_column].pct_change(5) * 100
                )  # Giả sử 5 ngày giao dịch/tuần
                nav_df["return_1m"] = (
                    nav_df[nav_column].pct_change(21) * 100
                )  # Giả sử 21 ngày giao dịch/tháng
                nav_df["return_3m"] = (
                    nav_df[nav_column].pct_change(63) * 100
                )  # Giả sử 63 ngày giao dịch/quý
                nav_df["return_6m"] = (
                    nav_df[nav_column].pct_change(126) * 100
                )  # Giả sử 126 ngày giao dịch/6 tháng
                nav_df["return_1y"] = (
                    nav_df[nav_column].pct_change(252) * 100
                )  # Giả sử 252 ngày giao dịch/năm

                # Hiển thị các số liệu hiệu suất
                latest_nav = nav_df.iloc[-1]
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    custom_metric(
                        "NAV hiện tại", format_number(latest_nav[nav_column]), suffix=" VND"
                    )
                with col2:
                    custom_metric("Ngày cập nhật", latest_nav["date"].strftime("%d/%m/%Y"))
                with col3:
                    custom_metric(
                        "Thay đổi 1 tháng",
                        format_percent(latest_nav["return_1m"]),
                        delta=f"{latest_nav['return_1m']:.2f}%",
                    )
                with col4:
                    custom_metric(
                        "Thay đổi 1 năm",
                        format_percent(latest_nav["return_1y"]),
                        delta=f"{latest_nav['return_1y']:.2f}%",
                    )

                # Chọn khoảng thời gian hiển thị
                time_periods = {
                    "1 tháng": 30,
                    "3 tháng": 90,
                    "6 tháng": 180,
                    "1 năm": 365,
                    "2 năm": 730,
                    "5 năm": 1825,
                    "Tất cả": None,
                }

                selected_period = st.selectbox("Chọn khoảng thời gian", list(time_periods.keys()))
                days = time_periods[selected_period]

                # Lọc dữ liệu theo khoảng thời gian
                if days:
                    cutoff_date = latest_nav["date"] - timedelta(days=days)
                    filtered_nav_df = nav_df[nav_df["date"] >= cutoff_date]
                else:
                    filtered_nav_df = nav_df

                # Vẽ biểu đồ NAV theo thời gian
                fig = px.line(
                    filtered_nav_df,
                    x="date",
                    y=nav_column,
                    title=f"NAV của quỹ {selected_fund} theo thời gian",
                    labels={"date": "Ngày", nav_column: "NAV (VND)"},
                )

                # Thêm tùy chỉnh
                fig.update_layout(
                    xaxis_title="Ngày",
                    yaxis_title="NAV (VND)",
                    hovermode="x unified",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=40, b=20),
                )

                st.plotly_chart(fig, use_container_width=True)

                # Vẽ biểu đồ hiệu suất chuẩn hóa
                fig2 = px.line(
                    filtered_nav_df,
                    x="date",
                    y="nav_normalized",
                    title=f"Hiệu suất chuẩn hóa (Base 100) của quỹ {selected_fund}",
                    labels={"date": "Ngày", "nav_normalized": "NAV (Base 100)"},
                )

                # Thêm tùy chỉnh
                fig2.update_layout(
                    xaxis_title="Ngày",
                    yaxis_title="NAV (Base 100)",
                    hovermode="x unified",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=40, b=20),
                )

                st.plotly_chart(fig2, use_container_width=True)

                # Hiển thị dữ liệu dạng bảng
                with st.expander("Xem dữ liệu NAV chi tiết"):
                    st.dataframe(
                        filtered_nav_df[
                            [
                                "date",
                                nav_column,
                                "return_1d",
                                "return_1w",
                                "return_1m",
                                "return_3m",
                                "return_6m",
                                "return_1y",
                            ]
                        ]
                        .rename(
                            columns={
                                "date": "Ngày",
                                nav_column: "NAV (VND)",
                                "return_1d": "Lợi nhuận 1 ngày (%)",
                                "return_1w": "Lợi nhuận 1 tuần (%)",
                                "return_1m": "Lợi nhuận 1 tháng (%)",
                                "return_3m": "Lợi nhuận 3 tháng (%)",
                                "return_6m": "Lợi nhuận 6 tháng (%)",
                                "return_1y": "Lợi nhuận 1 năm (%)",
                            }
                        )
                        .sort_values("Ngày", ascending=False)
                        .style.format(
                            {
                                "NAV (VND)": "{:,.2f}",
                                "Lợi nhuận 1 ngày (%)": "{:.2f}%",
                                "Lợi nhuận 1 tuần (%)": "{:.2f}%",
                                "Lợi nhuận 1 tháng (%)": "{:.2f}%",
                                "Lợi nhuận 3 tháng (%)": "{:.2f}%",
                                "Lợi nhuận 6 tháng (%)": "{:.2f}%",
                                "Lợi nhuận 1 năm (%)": "{:.2f}%",
                            }
                        ),
                        height=400,
                        use_container_width=True,
                    )

                    # Thêm nút tải dữ liệu
                    export_nav_df = filtered_nav_df[
                        [
                            "date",
                            nav_column,
                            "return_1d",
                            "return_1w",
                            "return_1m",
                            "return_3m",
                            "return_6m",
                            "return_1y",
                        ]
                    ]
                    export_nav_df.columns = [
                        "Ngày",
                        "NAV (VND)",
                        "Lợi nhuận 1 ngày (%)",
                        "Lợi nhuận 1 tuần (%)",
                        "Lợi nhuận 1 tháng (%)",
                        "Lợi nhuận 3 tháng (%)",
                        "Lợi nhuận 6 tháng (%)",
                        "Lợi nhuận 1 năm (%)",
                    ]
            else:
                st.info("Không có dữ liệu hiệu suất NAV cho quỹ này.")

        # Tab phân bổ ngành
        with fund_subtabs[2]:
            st.subheader("Phân bổ theo ngành")
            if industry_df is not None and not industry_df.empty:
                # Hiển thị dữ liệu dạng biểu đồ và bảng
                col1, col2 = st.columns([2, 3])

                with col1:
                    # Sử dụng hàm tạo biểu đồ tròn
                    fig = create_pie_chart(
                        industry_df,
                        values=(
                            "assetPercent"
                            if "assetPercent" in industry_df.columns
                            else "netAssetPercent"
                        ),
                        names="industry",
                        title=f"Phân bổ ngành - {selected_fund}",
                        color_sequence=px.colors.qualitative.Set3,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Sử dụng hàm tạo biểu đồ cột
                    weight_col = (
                        "assetPercent"
                        if "assetPercent" in industry_df.columns
                        else "netAssetPercent"
                    )
                    fig2 = create_bar_chart(
                        industry_df.sort_values(weight_col, ascending=False),
                        x="industry",
                        y=weight_col,
                        title=f"Phân bổ ngành - {selected_fund}",
                        labels={"industry": "Ngành", weight_col: "Tỷ trọng (%)"},
                        text=weight_col,
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                # Hiển thị dữ liệu dạng bảng
                st.dataframe(
                    industry_df[["industry", weight_col]]
                    .rename(columns={"industry": "Tên ngành", weight_col: "Tỷ trọng (%)"})
                    .sort_values("Tỷ trọng (%)", ascending=False)
                    .style.format({"Tỷ trọng (%)": "{:.2f}%"}),
                    height=400,
                    use_container_width=True,
                )

            else:
                st.info("Không có dữ liệu phân bổ ngành cho quỹ này.")

        # Tab phân bổ tài sản
        with fund_subtabs[3]:
            st.subheader("Phân bổ loại tài sản")
            if asset_df is not None and not asset_df.empty:
                # Hiển thị dữ liệu dạng biểu đồ và bảng
                col1, col2 = st.columns([2, 3])

                with col1:
                    # Sử dụng hàm tạo biểu đồ tròn
                    weight_col = (
                        "assetPercent" if "assetPercent" in asset_df.columns else "netAssetPercent"
                    )
                    fig = create_pie_chart(
                        asset_df,
                        values=weight_col,
                        names="assetType",
                        title=f"Phân bổ tài sản - {selected_fund}",
                        color_sequence=px.colors.qualitative.Pastel,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Sử dụng hàm tạo biểu đồ cột
                    fig2 = create_bar_chart(
                        asset_df.sort_values(weight_col, ascending=False),
                        x="assetType",
                        y=weight_col,
                        title=f"Phân bổ tài sản - {selected_fund}",
                        labels={"assetType": "Loại tài sản", weight_col: "Tỷ trọng (%)"},
                        text=weight_col,
                    )
                    st.plotly_chart(fig2, use_container_width=True)

                # Hiển thị dữ liệu dạng bảng
                st.dataframe(
                    asset_df[["assetType", weight_col]]
                    .rename(columns={"assetType": "Loại tài sản", weight_col: "Tỷ trọng (%)"})
                    .sort_values("Tỷ trọng (%)", ascending=False)
                    .style.format({"Tỷ trọng (%)": "{:.2f}%"}),
                    height=400,
                    use_container_width=True,
                )

            else:
                st.info("Không có dữ liệu phân bổ tài sản cho quỹ này.")

    # ----- TAB 2: CỔ PHIẾU PHỔ BIẾN -----
    elif selected_tab == "Cổ phiếu phổ biến":
        st.header("Phân tích cổ phiếu phổ biến nhất trong danh mục các quỹ")

        # Chọn loại quỹ để phân tích
        col1, col2 = st.columns([1, 2])

        with col1:
            # Filter theo loại quỹ
            fund_types = ["Tất cả", "Quỹ cân bằng", "Quỹ cổ phiếu"]
            multi_fund_type = st.multiselect(
                "Chọn loại quỹ (có thể chọn nhiều)", fund_types, default=["Tất cả"]
            )

            if "Tất cả" in multi_fund_type:
                multi_fund_type = ["Tất cả"]

        with col2:
            st.info(
                """
                Phân tích này sẽ tổng hợp danh mục của tất cả các quỹ đã chọn để tìm ra:
                - Các cổ phiếu được nắm giữ phổ biến nhất (xuất hiện trong nhiều quỹ)
                - Tỷ trọng trung bình của mỗi cổ phiếu trong các quỹ
                - Số lượng quỹ nắm giữ mỗi cổ phiếu
                """
            )

        # Lấy dữ liệu của tất cả các quỹ thuộc loại đã chọn
        with st.spinner("Đang tải dữ liệu tất cả các quỹ..."):
            holdings_combined, industry_combined, asset_combined, failed_funds = (
                get_all_funds_data(
                    funds_df,
                    fund_type="Tất cả" if "Tất cả" in multi_fund_type else None,
                    with_progress=True,
                )
            )

            # Lọc theo loại quỹ đã chọn nếu không phải "Tất cả"
            if "Tất cả" not in multi_fund_type:
                holdings_combined = holdings_combined[
                    holdings_combined["fund_type"].isin(multi_fund_type)
                ]
                industry_combined = industry_combined[
                    industry_combined["fund_type"].isin(multi_fund_type)
                ]
                asset_combined = asset_combined[asset_combined["fund_type"].isin(multi_fund_type)]

        if failed_funds:
            st.warning(
                f"Không thể lấy dữ liệu của {len(failed_funds)} quỹ: {', '.join(failed_funds[:5])}{'...' if len(failed_funds) > 5 else ''}"
            )

        if holdings_combined.empty:
            st.error("Không có dữ liệu danh mục đầu tư cho các quỹ đã chọn.")
            st.stop()

        # Phân tích cổ phiếu phổ biến
        st.subheader("Cổ phiếu phổ biến nhất")

        # Tạo DataFrame mới với thông tin tổng hợp của các cổ phiếu
        weight_col = (
            "netAssetPercent"
            if "netAssetPercent" in holdings_combined.columns
            else "netAssetsPercent"
        )

        stock_summary = (
            holdings_combined.groupby("stockCode")
            .agg(
                stock_name=("stockCode", "first"),
                avg_weight=((weight_col), "mean"),
                max_weight=((weight_col), "max"),
                min_weight=((weight_col), "min"),
                std_weight=((weight_col), "std"),
                fund_count=("fund_code", "nunique"),
                fund_list=("fund_code", lambda x: ", ".join(sorted(x.unique()))),
            )
            .reset_index()
        )

        # Tính tỷ lệ phần trăm số quỹ nắm giữ
        total_funds = holdings_combined["fund_code"].nunique()
        stock_summary["fund_percent"] = stock_summary["fund_count"] / total_funds * 100

        # Hiển thị biểu đồ và bảng dữ liệu
        col1, col2 = st.columns([3, 2])

        with col1:
            # Top cổ phiếu được nhiều quỹ nắm giữ nhất
            top_stocks_fig = create_bar_chart(
                stock_summary.nlargest(15, "fund_count"),
                x="stockCode",
                y="fund_count",
                title="Top 15 cổ phiếu được nhiều quỹ nắm giữ nhất",
                labels={"stockCode": "Mã cổ phiếu", "fund_count": "Số quỹ nắm giữ"},
                text="fund_count",
                color="fund_percent",
                color_discrete_sequence=px.colors.sequential.Blues,
            )
            st.plotly_chart(top_stocks_fig, use_container_width=True)

            # Biểu đồ tỷ trọng trung bình của top cổ phiếu
            top_weight_fig = create_bar_chart(
                stock_summary.nlargest(15, "avg_weight"),
                x="stockCode",
                y="avg_weight",
                title="Top 15 cổ phiếu có tỷ trọng trung bình cao nhất",
                labels={"stockCode": "Mã cổ phiếu", "avg_weight": "Tỷ trọng trung bình (%)"},
                text="avg_weight",
                color="fund_count",
                color_discrete_sequence=px.colors.sequential.Oranges,
            )
            st.plotly_chart(top_weight_fig, use_container_width=True)

        with col2:
            # Biểu đồ bubble chart
            bubble_fig = px.scatter(
                stock_summary.nlargest(30, "fund_count"),
                x="fund_count",
                y="avg_weight",
                size="fund_percent",
                color="fund_percent",
                hover_name="stockCode",
                text="stockCode",
                title="Top 30 cổ phiếu phổ biến (Số quỹ vs Tỷ trọng TB)",
                labels={
                    "fund_count": "Số quỹ nắm giữ",
                    "avg_weight": "Tỷ trọng trung bình (%)",
                    "fund_percent": "% số quỹ nắm giữ",
                },
                color_continuous_scale=px.colors.sequential.Viridis,
            )

            bubble_fig.update_traces(
                textposition="top center",
                marker=dict(sizemode="area", sizeref=0.1),
            )

            bubble_fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=40, b=20),
            )

            st.plotly_chart(bubble_fig, use_container_width=True)

            # Thống kê tổng quan
            st.metric("Tổng số quỹ phân tích", total_funds)
            st.metric("Tổng số cổ phiếu duy nhất", len(stock_summary))

            # Top 5 cổ phiếu phổ biến nhất
            st.markdown("#### Top 5 cổ phiếu phổ biến nhất")
            for _, row in stock_summary.nlargest(5, "fund_count").iterrows():
                st.markdown(
                    f"""
                **{row['stockCode']}**  
                Số quỹ nắm giữ: {row['fund_count']} ({row['fund_percent']:.1f}%)  
                Tỷ trọng TB: {row['avg_weight']:.2f}% (Min: {row['min_weight']:.2f}%, Max: {row['max_weight']:.2f}%)
                """
                )

        # Hiển thị bảng dữ liệu đầy đủ
        st.subheader("Bảng tổng hợp tất cả cổ phiếu")

        # Hiển thị số cột tùy chọn
        num_stocks = st.slider("Số lượng cổ phiếu hiển thị", 10, 100, 50)

        # Sắp xếp và hiển thị
        sorted_summary = stock_summary

        # Hiển thị bảng dữ liệu
        display_df = sorted_summary[
            [
                "stockCode",
                "fund_count",
                "fund_percent",
                "avg_weight",
                "max_weight",
                "min_weight",
                "std_weight",
            ]
        ]
        display_df.columns = [
            "Mã CP",
            "Số quỹ",
            "% số quỹ",
            "Tỷ trọng TB (%)",
            "Tỷ trọng Max (%)",
            "Tỷ trọng Min (%)",
            "Độ lệch chuẩn (%)",
        ]

        st.dataframe(
            display_df.style.format(
                {
                    "% số quỹ": "{:.2f}%",
                    "Tỷ trọng TB (%)": "{:.2f}%",
                    "Tỷ trọng Max (%)": "{:.2f}%",
                    "Tỷ trọng Min (%)": "{:.2f}%",
                    "Độ lệch chuẩn (%)": "{:.2f}%",
                }
            ),
            height=500,
            use_container_width=True,
        )

        # Hiển thị danh sách quỹ nắm giữ cho một cổ phiếu cụ thể
        st.subheader("Xem chi tiết cổ phiếu")

        # Chọn cổ phiếu để xem chi tiết
        selected_stock = st.selectbox(
            "Chọn cổ phiếu để xem danh sách quỹ nắm giữ",
            options=sorted(stock_summary["stockCode"].unique()),
            format_func=lambda x: f"{x} - {stock_summary[stock_summary['stockCode'] == x]['stock_name'].values[0]}",
        )

        # Lọc dữ liệu cho cổ phiếu đã chọn
        stock_details = holdings_combined[holdings_combined["stockCode"] == selected_stock]

        if not stock_details.empty:
            # Hiển thị thông tin chi tiết
            stock_name = stock_details["stockCode"].iloc[0]
            fund_count = len(stock_details["fund_code"].unique())
            avg_weight = stock_details[weight_col].mean()

            col1, col2, col3 = st.columns(3)
            with col1:
                custom_metric("Cổ phiếu", f"{selected_stock} - {stock_name}")
            with col2:
                custom_metric(
                    "Số quỹ nắm giữ", f"{fund_count} ({fund_count/total_funds*100:.1f}%)"
                )
            with col3:
                custom_metric("Tỷ trọng trung bình", f"{avg_weight:.2f}%")

            # Biểu đồ tỷ trọng của cổ phiếu trong các quỹ
            stock_details_sorted = stock_details.sort_values(weight_col, ascending=False)

            fig = create_bar_chart(
                stock_details_sorted,
                x="fund_code",
                y=weight_col,
                title=f"Tỷ trọng của {selected_stock} trong các quỹ",
                labels={"fund_code": "Mã quỹ", weight_col: "Tỷ trọng (%)"},
                text=weight_col,
                color="fund_type",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Hiển thị bảng dữ liệu
            st.dataframe(
                stock_details_sorted[
                    ["fund_code", "fund_name", "fund_type", weight_col, "nav_date"]
                ]
                .rename(
                    columns={
                        "fund_code": "Mã quỹ",
                        "fund_name": "Tên quỹ",
                        "fund_type": "Loại quỹ",
                        weight_col: "Tỷ trọng (%)",
                        "nav_date": "Ngày cập nhật",
                    }
                )
                .style.format(
                    {
                        "Tỷ trọng (%)": "{:.2f}%",
                    }
                ),
                height=400,
                use_container_width=True,
            )

        else:
            st.info(f"Không tìm thấy dữ liệu cho cổ phiếu {selected_stock}")

    # ----- TAB 3: PHÂN TÍCH NGÀNH -----
    elif selected_tab == "Phân tích ngành":
        st.header("Phân tích phân bổ ngành của các quỹ")

        # Chọn loại quỹ để phân tích
        col1, col2 = st.columns([1, 1])

        with col1:
            # Filter theo loại quỹ
            fund_types = ["Tất cả", "Quỹ cân bằng", "Quỹ cổ phiếu"]
            industry_fund_type = st.selectbox("Chọn loại quỹ", fund_types)

        with col2:
            st.info(
                """
                Phân tích này sẽ tổng hợp phân bổ ngành của tất cả các quỹ thuộc loại đã chọn để:
                - Xác định các ngành được phân bổ nhiều nhất
                - So sánh mức độ phân bổ ngành giữa các quỹ
                - Tìm ra các quỹ có mức độ phân bổ cao vào các ngành cụ thể
                """
            )

        # Lấy dữ liệu của tất cả các quỹ thuộc loại đã chọn
        with st.spinner("Đang tải dữ liệu tất cả các quỹ..."):
            holdings_combined, industry_combined, asset_combined, failed_funds = (
                get_all_funds_data(funds_df, fund_type=industry_fund_type, with_progress=True)
            )

        if failed_funds:
            st.warning(
                f"Không thể lấy dữ liệu của {len(failed_funds)} quỹ: {', '.join(failed_funds[:5])}{'...' if len(failed_funds) > 5 else ''}"
            )

        if industry_combined.empty:
            st.error("Không có dữ liệu phân bổ ngành cho các quỹ đã chọn.")
            st.stop()

        # Phân tích phân bổ ngành
        st.subheader("Tổng hợp phân bổ ngành")

        # Tạo DataFrame mới với thông tin tổng hợp của các ngành
        weight_col = (
            "assetPercent" if "assetPercent" in industry_combined.columns else "netAssetsPercent"
        )

        industry_summary = (
            industry_combined.groupby("industry")
            .agg(
                avg_weight=((weight_col), "mean"),
                max_weight=((weight_col), "max"),
                min_weight=((weight_col), "min"),
                std_weight=((weight_col), "std"),
                fund_count=("fund_code", "nunique"),
                fund_list=("fund_code", lambda x: ", ".join(sorted(x.unique()))),
            )
            .reset_index()
        )

        # Tính tỷ lệ phần trăm số quỹ đầu tư vào ngành
        total_funds = industry_combined["fund_code"].nunique()
        industry_summary["fund_percent"] = industry_summary["fund_count"] / total_funds * 100

        # Tạo một bản tóm tắt mới dựa trên nhóm ngành
        industry_group_summary = (
            industry_summary.groupby("industry")
            .agg(
                total_weight=(("avg_weight", "sum")),
                avg_weight=(("avg_weight", "mean")),
                max_weight=(("max_weight", "max")),
                min_weight=(("min_weight", "min")),
                std_weight=(("std_weight", "mean")),
                fund_count=(("fund_count", "sum")),
            )
            .reset_index()
        )

        # Sắp xếp lại theo tổng tỷ trọng
        industry_group_summary = industry_group_summary.sort_values(
            "total_weight", ascending=False
        )

        # Hiển thị biểu đồ và bảng dữ liệu
        col1, col2 = st.columns([3, 2])

        with col1:
            # Biểu đồ tỷ trọng trung bình ngành
            industry_fig = create_bar_chart(
                industry_group_summary.head(15),
                x="industry",
                y="avg_weight",
                title="Top 15 ngành có tỷ trọng trung bình cao nhất",
                labels={"industry": "Ngành", "avg_weight": "Tỷ trọng trung bình (%)"},
                text="avg_weight",
                color="fund_count",
                color_discrete_sequence=px.colors.sequential.Blues,
            )
            st.plotly_chart(industry_fig, use_container_width=True)

            # Biểu đồ treemap phân bổ ngành
            treemap_data = industry_group_summary.copy()
            treemap_data["size_value"] = treemap_data[
                "total_weight"
            ]  # Giá trị để xác định kích thước ô

            fig = create_treemap(
                treemap_data,
                path=["industry"],
                values="size_value",
                color="avg_weight",
                title="Treemap phân bổ ngành",
                height=500,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Biểu đồ pie chart phân bổ ngành
            pie_fig = create_pie_chart(
                industry_group_summary,
                values="total_weight",
                names="industry",
                title="Phân bổ ngành tổng hợp",
                color_sequence=px.colors.qualitative.Set3,
                show_percent=True,
                show_label=True,
            )
            st.plotly_chart(pie_fig, use_container_width=True)

            # Thống kê tổng quan
            st.metric("Tổng số quỹ phân tích", total_funds)
            st.metric("Tổng số ngành duy nhất", len(industry_group_summary))

            # Top 5 ngành phổ biến nhất
            st.markdown("#### Top 5 ngành có tỷ trọng cao nhất")
            for _, row in industry_group_summary.head(5).iterrows():
                st.markdown(
                    f"""
                **{row['industry']}**  
                Tỷ trọng TB: {row['avg_weight']:.2f}% (Min: {row['min_weight']:.2f}%, Max: {row['max_weight']:.2f}%)  
                Số quỹ phân bổ: {row['fund_count']}
                """
                )

        # Hiển thị bảng dữ liệu đầy đủ
        st.subheader("Bảng tổng hợp tất cả ngành")

        # Hiển thị số cột tùy chọn
        num_industries = st.slider(
            "Số lượng ngành hiển thị",
            10,
            len(industry_group_summary),
            min(20, len(industry_group_summary)),
        )

        # Sort options
        sort_options = {
            "Tỷ trọng trung bình (giảm dần)": ("avg_weight", False),
            "Tỷ trọng cao nhất (giảm dần)": ("max_weight", False),
            "Số quỹ phân bổ (giảm dần)": ("fund_count", False),
            "Tên ngành (A-Z)": ("industry", True),
        }

        sort_by = st.selectbox("Sắp xếp theo", list(sort_options.keys()))
        sort_col, ascending = sort_options[sort_by]

        # Sắp xếp và hiển thị
        sorted_summary = industry_group_summary.sort_values(sort_col, ascending=ascending).head(
            num_industries
        )

        # Hiển thị bảng dữ liệu
        display_df = sorted_summary[
            ["industry", "avg_weight", "max_weight", "min_weight", "std_weight", "fund_count"]
        ]
        display_df.columns = [
            "Ngành",
            "Tỷ trọng TB (%)",
            "Tỷ trọng Max (%)",
            "Tỷ trọng Min (%)",
            "Độ lệch chuẩn (%)",
            "Số quỹ",
        ]

        st.dataframe(
            display_df.style.format(
                {
                    "Tỷ trọng TB (%)": "{:.2f}%",
                    "Tỷ trọng Max (%)": "{:.2f}%",
                    "Tỷ trọng Min (%)": "{:.2f}%",
                    "Độ lệch chuẩn (%)": "{:.2f}%",
                }
            ),
            height=500,
            use_container_width=True,
        )

        # Phân tích chi tiết từng ngành
        st.subheader("Xem chi tiết ngành")

        # Chọn ngành để xem chi tiết
        selected_industry_group = st.selectbox(
            "Chọn ngành để xem danh sách quỹ phân bổ",
            options=sorted(industry_group_summary["industry"].unique()),
        )

        # Tìm tất cả ngành thuộc nhóm đã chọn
        industry_names = industry_summary[industry_summary["industry"] == selected_industry_group][
            "industry"
        ].unique()

        # Lọc dữ liệu cho ngành đã chọn
        industry_details = industry_combined[industry_combined["industry"].isin(industry_names)]

        if not industry_details.empty:
            # Hiển thị thông tin chi tiết
            fund_count = len(industry_details["fund_code"].unique())
            avg_weight = industry_details[weight_col].mean()

            col1, col2, col3 = st.columns(3)
            with col1:
                custom_metric("Ngành", selected_industry_group)
            with col2:
                custom_metric(
                    "Số quỹ phân bổ", f"{fund_count} ({fund_count/total_funds*100:.1f}%)"
                )
            with col3:
                custom_metric("Tỷ trọng trung bình", f"{avg_weight:.2f}%")

            # Biểu đồ tỷ trọng của ngành trong các quỹ
            industry_details_sorted = industry_details.sort_values(weight_col, ascending=False)
            fig = create_bar_chart(
                industry_details_sorted,
                x="fund_code",
                y=weight_col,
                title=f"Tỷ trọng của ngành {selected_industry_group} trong các quỹ",
                labels={"fund_code": "Mã quỹ", weight_col: "Tỷ trọng (%)"},
                text=weight_col,
                color="fund_type",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Hiển thị bảng dữ liệu
            st.dataframe(
                industry_details_sorted[
                    ["fund_code", "fund_name", "fund_type", "industry", weight_col]
                ]
                .rename(
                    columns={
                        "fund_code": "Mã quỹ",
                        "fund_name": "Tên quỹ",
                        "fund_type": "Loại quỹ",
                        "industry": "Tên ngành chi tiết",
                        weight_col: "Tỷ trọng (%)",
                    }
                )
                .style.format(
                    {
                        "Tỷ trọng (%)": "{:.2f}%",
                    }
                ),
                height=400,
                use_container_width=True,
            )

        else:
            st.info(f"Không tìm thấy dữ liệu cho ngành {selected_industry_group}")
