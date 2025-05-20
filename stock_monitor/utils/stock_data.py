# stock_data.py
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

def fetch_stock_data(symbol: str, interval: str = "1min"):
    """Fetch intraday stock data from Yahoo Finance."""
    try:
        # Map interval to yfinance format
        interval_map = {"1min": "1m", "5min": "5m", "15min": "15m"}
        yf_interval = interval_map.get(interval, "1m")
        
        # Fetch data for the last 7 days (yfinance limit for 1min data)
        stock = yf.Ticker(symbol)
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        data = stock.history(start=start_time, end=end_time, interval=yf_interval, auto_adjust=True)
        
        if data.empty:
            raise Exception(f"No data returned for symbol {symbol}. Possibly delisted, invalid symbol, or market closed.")
        
        return data
    except Exception as e:
        raise Exception(f"Failed to fetch data from Yahoo Finance: {e}")

def parse_stock_data(data: pd.DataFrame):
    """Parse yfinance DataFrame for plotting."""
    try:
        if data.empty:
            raise Exception("Empty DataFrame received")
        
        # Extract timestamps and closing prices
        dates = [str(idx)[:19] for idx in data.index]  # Convert to string, limit to YYYY-MM-DD HH:MM:SS
        prices = data['Close'].tolist()
        
        if not dates or not prices:
            raise Exception("No valid dates or prices found")
        
        return dates, prices
    except Exception as e:
        raise Exception(f"Data parsing error: {e}")