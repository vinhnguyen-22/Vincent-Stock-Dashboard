from contextlib import suppress
from datetime import datetime, timedelta
from math import sqrt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from vnstock import Vnstock
from src.company_profile import calculate_quant_metrics,calculate_stock_metrics
from src.features import (
    fetch_and_plot_ownership,
    get_fund_data,
    plot_cashflow_analysis,
    plot_pie_fund,
)
from src.filter import filter_by_pricing_stock, filter_stocks, filter_stocks_by_industry
from src.optimize_portfolio import (
    display_portfolio_analysis,
)
from src.plots import (
    get_firm_pricing,
    get_stock_price,
    plot_close_price_and_ratio,
    plot_firm_pricing,
    plot_foreign_trading,
    plot_proprietary_trading,
)

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
                "🎲 Phân Tích Định Lượng",
                "🌍 Tổng Quan Thị Trường",
                "🔍 Bộ Lọc Cổ Phiếu",
                "💰 Phân Tích Dòng Tiền",
                "🗂 Phân Bổ Danh Mục",
                "🧐 Danh Mục Tham Khảo"
            ],
        )
        stock = st.text_input("Nhập mã cổ phiếu", "FPT")
        
        start_date = st.date_input("Chọn ngày bắt đầu", datetime(2025, 1, 1))
        end_option = st.checkbox("Nhập ngày kết thúc")
        
        if page != "Tổng Quan Thị Trường" and not end_option:
            time_range = st.selectbox("Chọn khoảng thời gian", ["Tuần", "Tháng", "Qúy", "Năm"], index=1)
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
    plot_cashflow_analysis(df_price, stock, period )


def display_trading_analysis(stock, df_price,df_index, start_date, end_date):
    """Display trading analysis for the selected stock."""
    df_pricing = get_firm_pricing(stock, '2024-01-01')
    
    col_1, col_2 = st.columns(2)
    with col_1:
        st.subheader("ĐỊNH GIÁ CỔ PHIẾU")
        calculate_stock_metrics(df_price, df_index, df_pricing)
    with col_2:
        st.subheader("THÔNG TIN CỔ PHIẾU")
        company = Vnstock().stock(symbol=stock, source="TCBS").company
        profile = company.profile()
        profile.set_index("company_name", inplace=True)
        st.dataframe(profile.T, use_container_width=True, )
  
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
        plot_proprietary_trading(stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    with col_2:
        plot_foreign_trading(stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    st.divider()
    st.subheader("TƯƠNG QUAN GIAO DỊCH NƯỚC NGOÀI VÀ GIÁ CỔ PHIẾU")
    plot_close_price_and_ratio(df_price, stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    with st.popover("Hướng dẫn"):
        st.write("Update sau")
        
def display_overview_market():
    """Display market overview.""" 
    start = st.date_input("Chọn ngày: ", datetime(2025, 1, 1))
    df = get_fund_data(start.strftime("%Y-%m-%d"))
    plot_pie_fund(df)
    
def display_quant_analysis(stock,end_date):
    """Display market overview.""" 
    quant_metric = calculate_quant_metrics(stock,end_date)
    st.write(quant_metric)
    
def display_filter_stock(end_date):
    """Display market overview.""" 
    market_cap = st.slider("Vốn Hóa Thị Trường: ", min_value=1, max_value=500,value=1, step=10)
    net_bought_val = st.slider("GTNN mua ròng 20 ngày: ", min_value=1, max_value=200,value=5)
    # stocks = filter_stocks_by_industry()
    filter =  filter_stocks(end_date, market_cap=market_cap, net_bought_val=net_bought_val)
    # Reorder columns to show lines first
    if filter is None:
        st.warning("Không có dữ liệu")
    else:
        cols = ['lines'] + [col for col in filter.columns if col != 'lines']
        filter = filter[cols]
        st.data_editor(filter,
            column_config={
                "lines": st.column_config.LineChartColumn(
                    "Trend",
                    width="medium",
                ),
            },
            use_container_width=True
        )
    filter_by_pricing_stock(end_date)
    
    
def main():
    
    """Main function to run the Streamlit app."""
    configure_streamlit()
    stock, start_date, end_date,period, page = get_sidebar_inputs()
    st.title(f"Vincent App - {page}")
    st.divider()
    st.info("""
            Thông báo cập nhật 05/04/2025:
            - Cập nhật chức năng bộ loc cổ phiếu.
            - Cập nhật biểu đồ phân tích định lượng.
            - Chức năng tổng quan thị trường đang trong quá trình phát triển.
            """)
    
    if stock:
        df_price = get_stock_price(stock, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        df_index = get_stock_price("VNINDEX", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        if page == "💰 Phân Tích Dòng Tiền":
            display_cashflow_analysis(stock, df_price, period)
        elif page == "🌍 Tổng Quan Thị Trường":
            display_overview_market()
        elif page == "🎲 Phân Tích Định Lượng":
            display_quant_analysis(stock,end_date)
        elif page == "🗂 Phân Bổ Danh Mục":
            display_portfolio_analysis()
        elif page == "🔍 Bộ Lọc Cổ Phiếu":
                display_filter_stock(end_date)
        else:
            display_trading_analysis(stock, df_price, df_index, start_date, end_date)
            

if __name__ == "__main__":
    main()

