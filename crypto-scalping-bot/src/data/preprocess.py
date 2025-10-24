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
    """Preprocess OHLCV data and engineer features for LSTM model training.

    This class handles all data preprocessing tasks including:
    - Adding technical indicators (RSI, MACD, Bollinger Bands, etc.)
    - Creating time-series sequences for LSTM input
    - Feature scaling using MinMaxScaler
    - Inverse transformation for predictions

    Attributes:
        config (dict): Configuration dictionary from YAML file.
        scaler (sklearn.preprocessing.MinMaxScaler): Fitted scaler for feature normalization.
        feature_columns (list): List of feature column names used for training.

    Example:
        >>> preprocessor = DataPreprocessor()
        >>> df_processed = preprocessor.add_technical_indicators(df)
        >>> X, y, indices = preprocessor.create_sequences(df_processed)
        >>> preprocessor.save_scaler()
    """

    def __init__(self, config_path='config/config.yaml'):
        """Initialize preprocessor with configuration from YAML file.

        Args:
            config_path (str, optional): Path to the YAML configuration file.
                Defaults to 'config/config.yaml'.

        Example:
            >>> preprocessor = DataPreprocessor()
            >>> preprocessor = DataPreprocessor('custom/config.yaml')
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.scaler = MinMaxScaler()
        self.feature_columns = []

    def add_technical_indicators(self, df):
        """Add technical indicators to OHLCV dataframe for feature engineering.

        Calculates and adds the following indicators:
        - RSI (Relative Strength Index)
        - MACD (Moving Average Convergence Divergence) with signal and histogram
        - Bollinger Bands (upper, middle, lower, width)
        - Price and volume changes (percentage)
        - High-low range
        - Simple and exponential moving averages
        - Volume indicators

        Args:
            df (pd.DataFrame): DataFrame with OHLCV data containing columns:
                ['open', 'high', 'low', 'close', 'volume'].

        Returns:
            pd.DataFrame: Copy of input DataFrame with added technical indicator columns.
                New columns include: rsi_14, macd, macd_signal, macd_diff, bb_upper,
                bb_middle, bb_lower, bb_width, price_change, volume_change, hl_range,
                sma_10, sma_30, ema_10, volume_sma_20, volume_ratio.

        Example:
            >>> preprocessor = DataPreprocessor()
            >>> df = pd.read_csv('data/BTC_USDT.csv')
            >>> df_with_indicators = preprocessor.add_technical_indicators(df)
            >>> print(df_with_indicators.columns)
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
        """Create time-series sequences for LSTM training using sliding window approach.

        Transforms the dataframe into supervised learning format where each sample
        consists of 'lookback' time steps of features and one target value.
        All features are normalized using MinMaxScaler.

        Args:
            df (pd.DataFrame): Preprocessed DataFrame with technical indicators.
            lookback (int, optional): Number of previous time steps to use as input
                for each prediction. Defaults to 60.
            target_col (str, optional): Name of the column to predict. Must be in
                the feature list defined in config. Defaults to 'close'.

        Returns:
            tuple: Three-element tuple containing:
                - X (np.ndarray): Input sequences with shape (samples, lookback, features).
                - y (np.ndarray): Target values with shape (samples,). Scaled values
                  of the target column.
                - indices (pd.Index): DatetimeIndex corresponding to each sample,
                  useful for aligning predictions with original data.

        Example:
            >>> preprocessor = DataPreprocessor()
            >>> df = preprocessor.add_technical_indicators(raw_df)
            >>> X, y, indices = preprocessor.create_sequences(df, lookback=60)
            >>> print(f"X shape: {X.shape}")  # (samples, 60, n_features)
            >>> print(f"y shape: {y.shape}")  # (samples,)
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

    def inverse_transform_predictions(self, predictions, feature_idx=0):
        """Convert scaled predictions back to original price scale.

        Takes predictions in normalized [0,1] range and converts them back to
        actual price values using the fitted scaler.

        Args:
            predictions (np.ndarray): Array of scaled predictions in range [0,1].
            feature_idx (int, optional): Index of the predicted feature in the
                feature_columns list. Defaults to 0 (typically 'close' price).

        Returns:
            np.ndarray: Unscaled predictions in original price units.

        Example:
            >>> preprocessor = DataPreprocessor()
            >>> # After training and getting predictions
            >>> scaled_predictions = model.predict(X_test)
            >>> actual_prices = preprocessor.inverse_transform_predictions(
            ...     scaled_predictions,
            ...     feature_idx=0
            ... )
            >>> print(f"Predicted price: ${actual_prices[0]:.2f}")
        """
        # Create dummy array with same shape as original features
        n_features = len(self.feature_columns)
        dummy = np.zeros((len(predictions), n_features))
        dummy[:, feature_idx] = predictions.flatten()

        # Inverse transform
        unscaled = self.scaler.inverse_transform(dummy)

        return unscaled[:, feature_idx]

    def save_scaler(self, filepath='data/scaler.pkl'):
        """Save the fitted scaler to disk for later use in predictions.

        Args:
            filepath (str, optional): Path where scaler will be saved as pickle file.
                Defaults to 'data/scaler.pkl'.

        Returns:
            None

        Example:
            >>> preprocessor = DataPreprocessor()
            >>> X, y, _ = preprocessor.create_sequences(df)
            >>> preprocessor.save_scaler()
            >>> preprocessor.save_scaler('models/my_scaler.pkl')
        """
        Path(filepath).parent.mkdir(exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self.scaler, f)
        print(f"Scaler saved to {filepath}")

    def load_scaler(self, filepath='data/scaler.pkl'):
        """Load a previously fitted scaler from disk.

        Args:
            filepath (str, optional): Path to the saved scaler pickle file.
                Defaults to 'data/scaler.pkl'.

        Returns:
            None

        Example:
            >>> preprocessor = DataPreprocessor()
            >>> preprocessor.load_scaler()
            >>> # Now can use for inverse transform
            >>> prices = preprocessor.inverse_transform_predictions(predictions)
        """
        with open(filepath, 'rb') as f:
            self.scaler = pickle.load(f)
        print(f"Scaler loaded from {filepath}")


def main():
    """Test and run the complete preprocessing pipeline.

    Loads the most recent CSV data file, adds technical indicators,
    creates sequences for LSTM training, and saves the processed data.

    Returns:
        None

    Example:
        Run from command line:
        $ python preprocess.py
    """
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
