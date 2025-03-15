from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from streamlit_tags import st_tags

from src.features import plot_cashflow_analysis, plot_price_chart
from src.optimize_portfolio import (
    calculate_optimal_portfolio,
    get_port,
    get_port_price,
    plot_optimal_portfolio_chart,
)
from src.plots import (
    get_stock_price,
    plot_close_price_and_ratio,
    plot_firm_pricing,
    plot_foreign_trading,
    plot_proprietary_trading,
)


def filter_stock_fullroom():

    pass


def main():
    pass


if __name__ == "__main__":
    main()
