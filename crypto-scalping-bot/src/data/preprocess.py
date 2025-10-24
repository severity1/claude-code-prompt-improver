"""
Data preprocessing and feature engineering for LSTM model.
"""

import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
import yaml
from sklearn.preprocessing import MinMaxScaler
import pickle
from pathlib import Path
from typing import Tuple, List
from numpy.typing import NDArray


class DataPreprocessor:
    """Preprocess data and engineer features for the LSTM model."""

    def __init__(self, config_path: str = 'config/config.yaml') -> None:
        """Initialize preprocessor with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.scaler = MinMaxScaler()
        self.feature_columns = []

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to the dataframe.

        Args:
            df (pd.DataFrame): OHLCV data

        Returns:
            pd.DataFrame: Data with technical indicators
        """
        df = df.copy()

        # RSI
        rsi_period = self.config['indicators']['rsi_period']
        rsi = RSIIndicator(close=df['close'], window=rsi_period)
        df['rsi_14'] = rsi.rsi()

        # MACD
        macd_fast = self.config['indicators']['macd_fast']
        macd_slow = self.config['indicators']['macd_slow']
        macd_signal = self.config['indicators']['macd_signal']
        macd = MACD(
            close=df['close'],
            window_slow=macd_slow,
            window_fast=macd_fast,
            window_sign=macd_signal
        )
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()

        # Bollinger Bands
        bb_period = self.config['indicators']['bb_period']
        bb_std = self.config['indicators']['bb_std']
        bb = BollingerBands(
            close=df['close'],
            window=bb_period,
            window_dev=bb_std
        )
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()
        df['bb_width'] = bb.bollinger_wband()

        # Additional features
        df['price_change'] = df['close'].pct_change()
        df['volume_change'] = df['volume'].pct_change()

        # High-low range
        df['hl_range'] = (df['high'] - df['low']) / df['close']

        # Moving averages
        df['sma_10'] = df['close'].rolling(window=10).mean()
        df['sma_30'] = df['close'].rolling(window=30).mean()
        df['ema_10'] = df['close'].ewm(span=10, adjust=False).mean()

        # Volume indicators
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']

        return df

    def create_sequences(self, df: pd.DataFrame, lookback: int = 60, target_col: str = 'close') -> Tuple[NDArray, NDArray, pd.DatetimeIndex]:
        """
        Create sequences for LSTM training.

        Args:
            df (pd.DataFrame): Preprocessed data with features
            lookback (int): Number of time steps to look back
            target_col (str): Column to predict

        Returns:
            tuple: (X, y) where X is input sequences and y is targets
        """
        # Select feature columns based on config
        feature_names = self.config['model']['features']

        # Ensure all features exist
        available_features = [f for f in feature_names if f in df.columns]
        if len(available_features) < len(feature_names):
            missing = set(feature_names) - set(available_features)
            print(f"Warning: Missing features {missing}. Using available features.")

        self.feature_columns = available_features

        # Drop NaN values (from indicators)
        df = df.dropna()

        # Extract features
        features = df[self.feature_columns].values

        # Normalize features
        features_scaled = self.scaler.fit_transform(features)

        # Create sequences
        X, y = [], []

        for i in range(lookback, len(features_scaled)):
            X.append(features_scaled[i - lookback:i])
            # Predict next period's close price (scaled)
            y.append(features_scaled[i, self.feature_columns.index(target_col)])

        X = np.array(X)
        y = np.array(y)

        print(f"Created {len(X)} sequences with shape {X.shape}")

        return X, y, df.index[lookback:]

    def inverse_transform_predictions(self, predictions: NDArray, feature_idx: int = 0) -> NDArray:
        """
        Convert scaled predictions back to original scale.

        Args:
            predictions (np.array): Scaled predictions
            feature_idx (int): Index of the predicted feature

        Returns:
            np.array: Unscaled predictions
        """
        # Create dummy array with same shape as original features
        n_features = len(self.feature_columns)
        dummy = np.zeros((len(predictions), n_features))
        dummy[:, feature_idx] = predictions.flatten()

        # Inverse transform
        unscaled = self.scaler.inverse_transform(dummy)

        return unscaled[:, feature_idx]

    def save_scaler(self, filepath: str = 'data/scaler.pkl') -> None:
        """Save the fitted scaler for later use."""
        Path(filepath).parent.mkdir(exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self.scaler, f)
        print(f"Scaler saved to {filepath}")

    def load_scaler(self, filepath: str = 'data/scaler.pkl') -> None:
        """Load a previously fitted scaler."""
        with open(filepath, 'rb') as f:
            self.scaler = pickle.load(f)
        print(f"Scaler loaded from {filepath}")


def main() -> None:
    """Test preprocessing pipeline."""
    import sys
    from pathlib import Path

    # Load the most recent data file
    data_dir = Path('data')
    csv_files = list(data_dir.glob('*.csv'))

    if not csv_files:
        print("No data files found. Run fetch_data.py first.")
        sys.exit(1)

    # Get the most recent file
    latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
    print(f"Loading data from {latest_file}")

    df = pd.read_csv(latest_file)
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Initialize preprocessor
    preprocessor = DataPreprocessor()

    # Add technical indicators
    print("\nAdding technical indicators...")
    df_with_indicators = preprocessor.add_technical_indicators(df)

    print("\nFeatures added:")
    print(df_with_indicators.columns.tolist())

    # Create sequences
    print("\nCreating sequences for LSTM...")
    X, y, indices = preprocessor.create_sequences(df_with_indicators, lookback=60)

    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")

    # Save preprocessor
    preprocessor.save_scaler()

    # Save processed data
    output_file = data_dir / 'processed_data.csv'
    df_with_indicators.to_csv(output_file, index=False)
    print(f"\nProcessed data saved to {output_file}")


if __name__ == '__main__':
    main()
