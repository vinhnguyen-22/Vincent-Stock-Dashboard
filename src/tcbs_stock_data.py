# tcbs_stock_data.py
"""
Module để lấy dữ liệu chứng khoán từ TCBS API.
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import requests

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tcbs_stock_data")


class TCBSStockData:
    """
    Class để lấy và xử lý dữ liệu chứng khoán từ TCBS API.
    """

    BASE_URL = "https://apipubaws.tcbs.com.vn/stock-insight/v2/stock/bars-long-term"

    def __init__(self, rate_limit_pause: float = 0.25):
        """
        Khởi tạo đối tượng TCBSStockData.

        Args:
            rate_limit_pause: Thời gian chờ giữa các request (giây) để tránh bị chặn bởi rate limit
        """
        self.rate_limit_pause = rate_limit_pause

    def _convert_timestamp_to_date(self, timestamp: int) -> str:
        """
        Chuyển đổi timestamp sang định dạng ngày YYYY-MM-DD.

        Args:
            timestamp: Unix timestamp (seconds since epoch)

        Returns:
            Chuỗi ngày theo định dạng YYYY-MM-DD
        """
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

    def _parse_trading_date(self, date_str: str) -> str:
        """
        Chuyển đổi chuỗi ngày từ API sang định dạng YYYY-MM-DD.

        Args:
            date_str: Chuỗi ngày theo định dạng ISO từ API (e.g., "2024-01-02T00:00:00.000Z")

        Returns:
            Chuỗi ngày theo định dạng YYYY-MM-DD
        """
        return date_str.split("T")[0]

    def _date_to_timestamp(self, date_str: str) -> int:
        """
        Chuyển đổi chuỗi ngày YYYY-MM-DD sang Unix timestamp.

        Args:
            date_str: Chuỗi ngày theo định dạng YYYY-MM-DD

        Returns:
            Unix timestamp
        """
        return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())

    def fetch_data(
        self,
        ticker: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        resolution: str = "D",
    ) -> pd.DataFrame:
        """
        Lấy dữ liệu chứng khoán cho một mã cụ thể trong khoảng thời gian.

        Args:
            ticker: Mã chứng khoán (vd: HPG)
            from_date: Ngày bắt đầu theo định dạng YYYY-MM-DD (mặc định: lấy từ đầu có thể)
            to_date: Ngày kết thúc theo định dạng YYYY-MM-DD (mặc định: hiện tại)
            resolution: Độ phân giải dữ liệu (D: ngày, W: tuần, M: tháng)

        Returns:
            DataFrame chứa dữ liệu chứng khoán
        """
        # Chuyển đổi ngày thành timestamp nếu được cung cấp
        from_timestamp = (
            int(datetime.strptime(from_date, "%Y-%m-%d").timestamp()) if from_date else 946684800
        )  # 2000-01-01
        to_timestamp = (
            int(datetime.strptime(to_date, "%Y-%m-%d").timestamp())
            if to_date
            else int(time.time())
        )

        all_data = []
        current_to = to_timestamp
        max_count_per_request = 5000  # Số lượng điểm dữ liệu tối đa mỗi request

        logger.info(
            f"Bắt đầu lấy dữ liệu cho {ticker} từ {from_date or '2000-01-01'} đến {to_date or 'hiện tại'}"
        )

        while current_to >= from_timestamp:
            params = {
                "ticker": ticker,
                "type": "index" if ticker == "VNINDEX" else "stock",
                "resolution": resolution,
                "to": current_to,
                "countBack": max_count_per_request,
            }

            try:
                response = requests.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                # Kiểm tra cấu trúc dữ liệu
                if "data" in data:
                    # Định dạng dữ liệu mới
                    stock_data = data["data"]
                    if not stock_data:
                        logger.info("Không còn dữ liệu khả dụng.")
                        break

                    # Thêm vào danh sách dữ liệu
                    all_data.extend(stock_data)

                    # Tìm ngày giao dịch cũ nhất để cập nhật cho request tiếp theo
                    oldest_date = min(item["tradingDate"] for item in stock_data)
                    oldest_timestamp = int(
                        datetime.strptime(oldest_date.split("T")[0], "%Y-%m-%d").timestamp()
                    )
                    current_to = oldest_timestamp - 86400  # Trừ đi 1 ngày

                    logger.info(
                        f"Đã lấy {len(stock_data)} điểm dữ liệu từ {oldest_date.split('T')[0]}"
                    )

                elif "t" in data:
                    # Định dạng dữ liệu cũ (nếu API thay đổi trong tương lai)
                    if not data["t"]:
                        logger.info("Không còn dữ liệu khả dụng.")
                        break

                    # Chuyển đổi định dạng cũ sang định dạng mới
                    for i in range(len(data["t"])):
                        trading_date = self._convert_timestamp_to_date(data["t"][i])
                        stock_item = {
                            "open": data["o"][i],
                            "high": data["h"][i],
                            "low": data["l"][i],
                            "close": data["c"][i],
                            "volume": data["v"][i],
                            "tradingDate": f"{trading_date}T00:00:00.000Z",
                        }
                        all_data.append(stock_item)

                    oldest_timestamp = min(data["t"])
                    current_to = oldest_timestamp - 1

                    logger.info(
                        f"Đã lấy {len(data['t'])} điểm dữ liệu từ {self._convert_timestamp_to_date(oldest_timestamp)}"
                    )

                else:
                    logger.warning("Định dạng dữ liệu không được hỗ trợ")
                    break

                # Tạm dừng để tránh rate limit
                time.sleep(self.rate_limit_pause)

            except Exception as e:
                logger.error(f"Lỗi khi lấy dữ liệu: {str(e)}")
                break

        if not all_data:
            logger.warning("Không có dữ liệu được lấy")
            return pd.DataFrame()

        # Chuyển đổi thành DataFrame
        df = pd.DataFrame(all_data)

        # Xử lý cột ngày
        df["time"] = df["tradingDate"].apply(lambda x: self._parse_trading_date(x))

        # Sắp xếp theo ngày
        df = df.sort_values("time")

        # Lọc dữ liệu theo khoảng thời gian nếu cần
        if from_date:
            df = df[df["time"] >= from_date]

        if to_date:
            df = df[df["time"] <= to_date]

        # Loại bỏ trùng lặp nếu có
        df = df.drop_duplicates(subset="time")

        logger.info(
            f"Đã hoàn thành lấy dữ liệu cho {ticker}: {len(df)} điểm dữ liệu từ {df['time'].min()} đến {df['time'].max()}"
        )

        return df

    def get_stock_data_by_date_range(
        self, ticker: str, start_date: str, end_date: str, resolution: str = "D"
    ) -> pd.DataFrame:
        """
        Lấy dữ liệu chứng khoán cho một mã cụ thể từ ngày đến ngày theo định dạng chuẩn.

        Args:
            ticker: Mã chứng khoán (vd: HPG)
            start_date: Ngày bắt đầu theo định dạng YYYY-MM-DD
            end_date: Ngày kết thúc theo định dạng YYYY-MM-DD
            resolution: Độ phân giải dữ liệu (D: ngày, W: tuần, M: tháng)

        Returns:
            DataFrame chứa dữ liệu chứng khoán trong khoảng thời gian chỉ định
        """
        # Kiểm tra định dạng ngày
        try:
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Định dạng ngày không hợp lệ. Vui lòng sử dụng định dạng YYYY-MM-DD")

        # Kiểm tra thứ tự ngày
        if start_date > end_date:
            raise ValueError("Ngày bắt đầu phải nhỏ hơn hoặc bằng ngày kết thúc")

        logger.info(f"Lấy dữ liệu {ticker} từ {start_date} đến {end_date}")

        # Gọi hàm fetch_data với khoảng thời gian cụ thể
        df = self.fetch_data(ticker, from_date=start_date, to_date=end_date, resolution=resolution)

        # Báo cáo kết quả
        if df.empty:
            logger.warning(f"Không có dữ liệu cho {ticker} từ {start_date} đến {end_date}")
        else:
            actual_start = df["time"].min()
            actual_end = df["time"].max()
            logger.info(f"Lấy được {len(df)} điểm dữ liệu từ {actual_start} đến {actual_end}")

            # Kiểm tra và cảnh báo nếu khoảng thời gian thực tế khác với yêu cầu
            if actual_start > start_date:
                logger.warning(
                    f"Lưu ý: Dữ liệu sớm nhất có từ {actual_start} (muộn hơn {start_date} yêu cầu)"
                )

            if actual_end < end_date:
                logger.warning(
                    f"Lưu ý: Dữ liệu mới nhất đến {actual_end} (sớm hơn {end_date} yêu cầu)"
                )
        return df

    def save_to_csv(self, df: pd.DataFrame, filename: str) -> None:
        """
        Lưu DataFrame vào file CSV.

        Args:
            df: DataFrame cần lưu
            filename: Tên file đầu ra
        """
        df.to_csv(filename, index=False)
        logger.info(f"Đã lưu dữ liệu vào file: {filename}")

    def get_multiple_tickers(
        self,
        tickers: List[str],
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        resolution: str = "D",
    ) -> Dict[str, pd.DataFrame]:
        """
        Lấy dữ liệu cho nhiều mã chứng khoán.

        Args:
            tickers: Danh sách các mã chứng khoán
            from_date: Ngày bắt đầu theo định dạng YYYY-MM-DD
            to_date: Ngày kết thúc theo định dạng YYYY-MM-DD
            resolution: Độ phân giải dữ liệu (D: ngày, W: tuần, M: tháng)

        Returns:
            Dictionary với key là mã chứng khoán và value là DataFrame tương ứng
        """
        result = {}
        for ticker in tickers:
            logger.info(f"Đang lấy dữ liệu cho {ticker}...")
            df = self.fetch_data(ticker, from_date, to_date, resolution)
            if not df.empty:
                result[ticker] = df

        return result

    def get_multiple_tickers_by_date_range(
        self, tickers: List[str], start_date: str, end_date: str, resolution: str = "D"
    ) -> Dict[str, pd.DataFrame]:
        """
        Lấy dữ liệu cho nhiều mã chứng khoán trong khoảng thời gian cụ thể.

        Args:
            tickers: Danh sách các mã chứng khoán
            start_date: Ngày bắt đầu theo định dạng YYYY-MM-DD
            end_date: Ngày kết thúc theo định dạng YYYY-MM-DD
            resolution: Độ phân giải dữ liệu (D: ngày, W: tuần, M: tháng)

        Returns:
            Dictionary với key là mã chứng khoán và value là DataFrame tương ứng
        """
        result = {}
        for ticker in tickers:
            logger.info(f"Đang lấy dữ liệu cho {ticker}...")
            df = self.get_stock_data_by_date_range(ticker, start_date, end_date, resolution)
            if not df.empty:
                result[ticker] = df

        return result

    def get_stock_history(
        self, ticker: str, years_back: int = 10, resolution: str = "D"
    ) -> pd.DataFrame:
        """
        Lấy dữ liệu lịch sử của một mã chứng khoán trong X năm gần đây.

        Args:
            ticker: Mã chứng khoán
            years_back: Số năm cần lấy dữ liệu
            resolution: Độ phân giải dữ liệu (D: ngày, W: tuần, M: tháng)

        Returns:
            DataFrame chứa dữ liệu lịch sử
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        start_year = datetime.now().year - years_back
        start_date = f"{start_year}-01-01"

        return self.fetch_data(
            ticker, from_date=start_date, to_date=current_date, resolution=resolution
        )

    def calculate_returns(self, df: pd.DataFrame, period: str = "daily") -> pd.DataFrame:
        """
        Tính toán lợi nhuận theo các khoảng thời gian.

        Args:
            df: DataFrame chứa dữ liệu chứng khoán với cột 'close' và 'time'
            period: Khoảng thời gian tính lợi nhuận ('daily', 'weekly', 'monthly', 'yearly')

        Returns:
            DataFrame chứa dữ liệu lợi nhuận
        """
        # Đảm bảo dữ liệu được sắp xếp theo ngày
        df = df.sort_values("time")
        df = df.copy()

        # Chuyển đổi cột ngày thành datetime
        df["time"] = pd.to_datetime(df["time"])

        # Tính lợi nhuận hàng ngày
        df["daily_return"] = df["close"].pct_change()

        if period == "daily":
            return df[["time", "close", "daily_return"]]

        # Tính lợi nhuận theo khoảng thời gian khác
        if period == "weekly":
            df["period"] = df["time"].dt.isocalendar().week
            period_label = "Tuần"
        elif period == "monthly":
            df["period"] = df["time"].dt.month
            period_label = "Tháng"
        elif period == "yearly":
            df["period"] = df["time"].dt.year
            period_label = "Năm"
        else:
            raise ValueError(
                "period phải là một trong các giá trị: 'daily', 'weekly', 'monthly', 'yearly'"
            )

        # Nhóm theo khoảng thời gian và tính lợi nhuận
        grouped = df.groupby("period").agg(
            start_date=("time", "first"),
            end_date=("time", "last"),
            start_price=("close", "first"),
            end_price=("close", "last"),
        )

        grouped["return"] = (grouped["end_price"] / grouped["start_price"]) - 1
        grouped.reset_index(inplace=True)
        grouped.rename(columns={"period": period_label}, inplace=True)

        return grouped


# Ví dụ sử dụng
def example_usage():
    # Khởi tạo đối tượng
    tcbs = TCBSStockData(rate_limit_pause=1.0)

    # Ví dụ 1: Lấy dữ liệu HPG từ đầu năm 2023 đến nay
    df_hpg = tcbs.fetch_data("HPG", from_date="2023-01-01")

    # Ví dụ 2: Lấy dữ liệu HPG trong khoảng thời gian cụ thể
    df_hpg_range = tcbs.get_stock_data_by_date_range("HPG", "2000-01-01", "2023-12-31")

    # Ví dụ 3: Lấy dữ liệu nhiều mã trong khoảng thời gian cụ thể
    multi_stocks = tcbs.get_multiple_tickers_by_date_range(
        ["HPG", "VNM", "FPT"], "2023-01-01", "2023-12-31"
    )

    # Lưu vào file CSV
    tcbs.save_to_csv(df_hpg, "HPG_from_2023.csv")
    tcbs.save_to_csv(df_hpg_range, "HPG_2023_full_year.csv")

    # Tính lợi nhuận hàng tháng cho HPG
    monthly_returns = tcbs.calculate_returns(df_hpg, period="monthly")

    return df_hpg, df_hpg_range, multi_stocks, monthly_returns


if __name__ == "__main__":
    # Chạy ví dụ sử dụng nếu file được thực thi trực tiếp
    df, df_range, stocks, returns = example_usage()

    # Hiển thị thông tin
    print("\n5 dòng đầu dữ liệu HPG (toàn bộ):")
    print(df.head())

    print("\n5 dòng đầu dữ liệu HPG (khoảng thời gian cụ thể):")
    print(df_range.head())

    print("\nThông tin các mã chứng khoán đã lấy:")
    for ticker, data in stocks.items():
        print(
            f"{ticker}: {len(data)} dòng dữ liệu từ {data['time'].min()} đến {data['time'].max()}"
        )

    print("\nLợi nhuận hàng tháng của HPG:")
    print(returns.head())
