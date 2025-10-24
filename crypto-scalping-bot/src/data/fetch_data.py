"""
Fetch historical OHLCV data from OKX perpetual futures.
"""

import ccxt
import pandas as pd
import yaml
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


class OKXDataFetcher:
    """Fetch and save historical data from OKX."""

    def __init__(self, config_path: str = 'config/config.yaml') -> None:
        """Initialize the data fetcher with configuration."""
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

    def fetch_ohlcv(self, start_date: str, end_date: Optional[str] = None, limit: int = 1000) -> pd.DataFrame:
        """
        Fetch OHLCV data for the specified date range.

        Args:
            start_date (str): Start date in 'YYYY-MM-DD' format
            end_date (str): End date in 'YYYY-MM-DD' format (default: today)
            limit (int): Number of candles per request (max 1000 for OKX)

        Returns:
            pd.DataFrame: OHLCV data with columns [timestamp, open, high, low, close, volume]
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

    def save_data(self, df: pd.DataFrame, filename: Optional[str] = None) -> Path:
        """
        Save data to CSV file.

        Args:
            df (pd.DataFrame): Data to save
            filename (str): Output filename (default: auto-generated)
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


def main() -> None:
    """Main execution function."""
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
