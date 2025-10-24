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


class DataPreprocessor:
    """Preprocess data and engineer features for the LSTM model."""

    def __init__(self, config_path='config/config.yaml'):
        """Initialize preprocessor with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.scaler = MinMaxScaler()
        self.feature_columns = []

    def add_technical_indicators(self, df):
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

    def create_sequences(self, df, lookback=60, target_col='close'):
        """
        Create sequences for LSTM training.

        This is the core data preparation for time series LSTM models.
        Converts a time series into supervised learning format using a sliding window approach.

        Args:
            df (pd.DataFrame): Preprocessed data with features
            lookback (int): Number of time steps to look back (window size)
            target_col (str): Column to predict (usually 'close' price)

        Returns:
            tuple: (X, y, indices) where:
                - X is input sequences: shape (num_samples, lookback, num_features)
                - y is targets: shape (num_samples,)
                - indices are the corresponding datetime indices

        Example:
            If lookback=60, we use the past 60 time steps to predict the next value.
            For row 60: X[0] = data[0:60], y[0] = data[60]
            For row 61: X[1] = data[1:61], y[1] = data[61]
            This creates overlapping sequences (sliding window).
        """
        # Select feature columns based on config
        feature_names = self.config['model']['features']

        # Ensure all features exist in the dataframe
        available_features = [f for f in feature_names if f in df.columns]
        if len(available_features) < len(feature_names):
            missing = set(feature_names) - set(available_features)
            print(f"Warning: Missing features {missing}. Using available features.")

        self.feature_columns = available_features

        # Drop NaN values (created by rolling window indicators like SMA, RSI, etc.)
        df = df.dropna()

        # Extract features as numpy array
        features = df[self.feature_columns].values

        # Normalize features to [0, 1] range for better LSTM training
        # Neural networks perform better when inputs are scaled to similar ranges
        features_scaled = self.scaler.fit_transform(features)

        # Create sequences using sliding window approach
        X, y = [], []

        # Start from 'lookback' index because we need 'lookback' previous values
        for i in range(lookback, len(features_scaled)):
            # X: sequence of past 'lookback' timesteps (all features)
            # Shape: (lookback, num_features) e.g., (60, 20)
            X.append(features_scaled[i - lookback:i])

            # y: target value at current timestep (only the target column, scaled)
            # We predict the current 'close' price using the past 'lookback' timesteps
            y.append(features_scaled[i, self.feature_columns.index(target_col)])

        # Convert lists to numpy arrays
        X = np.array(X)  # Shape: (num_samples, lookback, num_features)
        y = np.array(y)  # Shape: (num_samples,)

        print(f"Created {len(X)} sequences with shape {X.shape}")

        # Return the indices starting from 'lookback' position
        # This helps track which datetime each prediction corresponds to
        return X, y, df.index[lookback:]

    def inverse_transform_predictions(self, predictions, feature_idx=0):
        """
        Convert scaled predictions back to original scale.

        This is necessary because the LSTM model outputs predictions in scaled form [0, 1].
        We need to convert them back to actual price values for interpretation and trading.

        Args:
            predictions (np.array): Scaled predictions from LSTM (values in [0, 1])
            feature_idx (int): Index of the predicted feature in feature_columns
                              (default 0 assumes 'close' is the first feature)

        Returns:
            np.array: Unscaled predictions in original price units

        Example:
            Scaled prediction: 0.75
            After inverse transform: $45,234.56 (actual BTC price)

        Technical note:
            MinMaxScaler scales each feature independently. To inverse transform one feature,
            we must create a dummy array with all features, then extract only the target column.
        """
        # Create dummy array with same shape as original features
        # Required because MinMaxScaler was fitted on all features together
        n_features = len(self.feature_columns)
        dummy = np.zeros((len(predictions), n_features))

        # Fill in the predicted feature column with our predictions
        # All other columns remain zeros (will be ignored)
        dummy[:, feature_idx] = predictions.flatten()

        # Apply inverse transformation using the fitted scaler
        # This converts scaled values [0, 1] back to original price range
        unscaled = self.scaler.inverse_transform(dummy)

        # Extract and return only the predicted feature column (e.g., 'close' price)
        return unscaled[:, feature_idx]

    def save_scaler(self, filepath='data/scaler.pkl'):
        """Save the fitted scaler for later use."""
        Path(filepath).parent.mkdir(exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self.scaler, f)
        print(f"Scaler saved to {filepath}")

    def load_scaler(self, filepath='data/scaler.pkl'):
        """Load a previously fitted scaler."""
        with open(filepath, 'rb') as f:
            self.scaler = pickle.load(f)
        print(f"Scaler loaded from {filepath}")


def main():
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
