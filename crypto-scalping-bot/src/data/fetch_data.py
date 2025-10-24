"""
Fetch historical OHLCV data from OKX perpetual futures.
"""

import ccxt
import pandas as pd
import yaml
import os
from datetime import datetime, timedelta
from pathlib import Path


class OKXDataFetcher:
    """Fetch and save historical OHLCV data from OKX perpetual futures exchange.

    This class provides methods to fetch historical candlestick data from OKX's
    public API without requiring authentication. It handles pagination, rate
    limiting, and data cleaning automatically.

    Attributes:
        config (dict): Configuration dictionary loaded from YAML file.
        exchange (ccxt.okx): CCXT exchange object configured for OKX.
        symbol (str): Trading symbol (e.g., 'BTC/USDT:USDT').
        timeframe (str): Candlestick timeframe (e.g., '5m', '15m', '1h').

    Example:
        >>> fetcher = OKXDataFetcher()
        >>> df = fetcher.fetch_ohlcv('2024-01-01', '2024-01-31')
        >>> fetcher.save_data(df)
    """

    def __init__(self, config_path='config/config.yaml'):
        """Initialize the data fetcher with configuration from YAML file.

        Args:
            config_path (str, optional): Path to the YAML configuration file.
                Defaults to 'config/config.yaml'.

        Example:
            >>> fetcher = OKXDataFetcher()
            >>> fetcher = OKXDataFetcher('custom/config.yaml')
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize OKX exchange (public API, no auth needed for historical data)
        self.exchange = ccxt.okx({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',  # Perpetual futures
            }
        })

        self.symbol = self.config['trading']['symbol']
        self.timeframe = self.config['trading']['timeframe']

    def fetch_ohlcv(self, start_date, end_date=None, limit=1000):
        """Fetch OHLCV (Open, High, Low, Close, Volume) data for the specified date range.

        This method handles pagination automatically to fetch data beyond the single
        request limit. It respects rate limits and removes duplicate entries.

        Args:
            start_date (str): Start date in 'YYYY-MM-DD' format (e.g., '2024-01-01').
            end_date (str, optional): End date in 'YYYY-MM-DD' format. If None, uses today.
                Defaults to None.
            limit (int, optional): Number of candles per API request. Maximum 1000 for OKX.
                Defaults to 1000.

        Returns:
            pd.DataFrame: DataFrame with columns:
                - timestamp (int): Unix timestamp in milliseconds
                - open (float): Opening price
                - high (float): Highest price in the period
                - low (float): Lowest price in the period
                - close (float): Closing price
                - volume (float): Trading volume
                - datetime (datetime): Timestamp converted to datetime object

        Example:
            >>> fetcher = OKXDataFetcher()
            >>> # Fetch one month of data
            >>> df = fetcher.fetch_ohlcv('2024-01-01', '2024-01-31')
            >>> print(f"Fetched {len(df)} candles")
            >>> # Fetch until today
            >>> df = fetcher.fetch_ohlcv('2024-01-01')
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')

        print(f"Fetching {self.symbol} {self.timeframe} data from {start_date} to {end_date}")

        all_candles = []
        current_dt = start_dt

        while current_dt < end_dt:
            since = int(current_dt.timestamp() * 1000)  # Convert to milliseconds

            try:
                candles = self.exchange.fetch_ohlcv(
                    self.symbol,
                    timeframe=self.timeframe,
                    since=since,
                    limit=limit
                )

                if not candles:
                    break

                all_candles.extend(candles)

                # Move to the timestamp of the last candle
                last_timestamp = candles[-1][0]
                current_dt = datetime.fromtimestamp(last_timestamp / 1000)

                print(f"Fetched {len(candles)} candles. Current date: {current_dt.strftime('%Y-%m-%d %H:%M')}")

                # Small delay to respect rate limits
                self.exchange.sleep(100)

            except Exception as e:
                print(f"Error fetching data: {e}")
                break

        # Convert to DataFrame
        df = pd.DataFrame(
            all_candles,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )

        # Remove duplicates and sort
        df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')

        # Convert timestamp to datetime
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Filter to exact date range
        df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]

        print(f"Total candles fetched: {len(df)}")

        return df

    def save_data(self, df, filename=None):
        """Save OHLCV data to a CSV file in the data directory.

        If no filename is provided, generates a descriptive filename automatically
        based on the symbol, timeframe, and date range.

        Args:
            df (pd.DataFrame): DataFrame containing OHLCV data to save.
            filename (str, optional): Output filename. If None, generates filename
                automatically in format: SYMBOL_TIMEFRAME_STARTDATE_to_ENDDATE.csv
                Defaults to None.

        Returns:
            pathlib.Path: Path object pointing to the saved file.

        Example:
            >>> fetcher = OKXDataFetcher()
            >>> df = fetcher.fetch_ohlcv('2024-01-01', '2024-01-31')
            >>> # Auto-generate filename
            >>> path = fetcher.save_data(df)
            >>> # Custom filename
            >>> path = fetcher.save_data(df, 'my_data.csv')
        """
        if filename is None:
            # Create filename from symbol and date range
            start_date = df['datetime'].min().strftime('%Y%m%d')
            end_date = df['datetime'].max().strftime('%Y%m%d')
            symbol_clean = self.symbol.replace('/', '_').replace(':', '_')
            filename = f"{symbol_clean}_{self.timeframe}_{start_date}_to_{end_date}.csv"

        # Create data directory if it doesn't exist
        data_dir = Path('data')
        data_dir.mkdir(exist_ok=True)

        filepath = data_dir / filename
        df.to_csv(filepath, index=False)
        print(f"Data saved to {filepath}")

        return filepath


def main():
    """Main execution function to fetch and save historical data.

    Loads configuration, fetches OHLCV data for the date range specified
    in the config file, displays statistics, and saves the data to CSV.

    Returns:
        None

    Example:
        Run from command line:
        $ python fetch_data.py
    """
    # Load config to get date range
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    fetcher = OKXDataFetcher()

    # Fetch historical data
    start_date = config['backtesting']['start_date']
    end_date = config['backtesting']['end_date']

    df = fetcher.fetch_ohlcv(start_date, end_date)

    # Display basic statistics
    print("\nData Statistics:")
    print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"Total rows: {len(df)}")
    print(f"Missing values: {df.isnull().sum().sum()}")
    print("\nFirst few rows:")
    print(df.head())
    print("\nPrice statistics:")
    print(df[['open', 'high', 'low', 'close', 'volume']].describe())

    # Save to CSV
    fetcher.save_data(df)


if __name__ == '__main__':
    main()
