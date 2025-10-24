"""
LSTM model for crypto price prediction.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks
import yaml
import pickle
from pathlib import Path
import matplotlib.pyplot as plt
from typing import Tuple, Optional, Dict, Any
from numpy.typing import NDArray


class LSTMPricePredictor:
    """LSTM neural network for predicting crypto prices."""

    def __init__(self, config_path: str = 'config/config.yaml') -> None:
        """Initialize the LSTM model with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.model = None
        self.history = None

    def build_model(self, input_shape: Tuple[int, int]) -> keras.Model:
        """
        Build LSTM model architecture.

        Args:
            input_shape (tuple): Shape of input data (timesteps, features)

        Returns:
            keras.Model: Compiled LSTM model
        """
        lstm_units = self.config['model']['lstm_units']
        dropout_rate = self.config['model']['dropout_rate']
        learning_rate = self.config['model']['learning_rate']

        model = keras.Sequential()

        # First LSTM layer
        model.add(layers.LSTM(
            lstm_units[0],
            return_sequences=True if len(lstm_units) > 1 else False,
            input_shape=input_shape
        ))
        model.add(layers.Dropout(dropout_rate))

        # Additional LSTM layers
        for i, units in enumerate(lstm_units[1:]):
            return_seq = i < len(lstm_units) - 2
            model.add(layers.LSTM(units, return_sequences=return_seq))
            model.add(layers.Dropout(dropout_rate))

        # Output layer
        model.add(layers.Dense(1))

        # Compile model
        optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
        model.compile(
            optimizer=optimizer,
            loss='mse',
            metrics=['mae']
        )

        self.model = model

        print("\nModel Architecture:")
        model.summary()

        return model

    def train(self, X_train: NDArray, y_train: NDArray, X_val: Optional[NDArray] = None, y_val: Optional[NDArray] = None) -> keras.callbacks.History:
        """
        Train the LSTM model.

        Args:
            X_train (np.array): Training sequences
            y_train (np.array): Training targets
            X_val (np.array): Validation sequences (optional)
            y_val (np.array): Validation targets (optional)

        Returns:
            keras.callbacks.History: Training history
        """
        if self.model is None:
            input_shape = (X_train.shape[1], X_train.shape[2])
            self.build_model(input_shape)

        epochs = self.config['model']['epochs']
        batch_size = self.config['model']['batch_size']

        # Callbacks
        early_stopping = callbacks.EarlyStopping(
            monitor='val_loss' if X_val is not None else 'loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        )

        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss' if X_val is not None else 'loss',
            factor=0.5,
            patience=5,
            min_lr=1e-7,
            verbose=1
        )

        checkpoint_dir = Path('models/checkpoints')
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        model_checkpoint = callbacks.ModelCheckpoint(
            checkpoint_dir / 'best_model.keras',
            monitor='val_loss' if X_val is not None else 'loss',
            save_best_only=True,
            verbose=1
        )

        callback_list = [early_stopping, reduce_lr, model_checkpoint]

        # Train model
        validation_data = (X_val, y_val) if X_val is not None else None

        print(f"\nTraining model for up to {epochs} epochs...")
        self.history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=validation_data,
            callbacks=callback_list,
            verbose=1
        )

        return self.history

    def predict(self, X: NDArray) -> NDArray:
        """
        Make predictions with the trained model.

        Args:
            X (np.array): Input sequences

        Returns:
            np.array: Predictions
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict(X, verbose=0)

    def evaluate(self, X_test: NDArray, y_test: NDArray) -> Dict[str, float]:
        """
        Evaluate model performance on test data.

        Args:
            X_test (np.array): Test sequences
            y_test (np.array): Test targets

        Returns:
            dict: Evaluation metrics
        """
        predictions = self.predict(X_test)

        mse = np.mean((predictions.flatten() - y_test) ** 2)
        mae = np.mean(np.abs(predictions.flatten() - y_test))
        rmse = np.sqrt(mse)

        # Direction accuracy (did we predict up/down correctly?)
        actual_direction = np.sign(np.diff(y_test))
        pred_direction = np.sign(np.diff(predictions.flatten()))
        direction_accuracy = np.mean(actual_direction == pred_direction)

        metrics = {
            'mse': mse,
            'mae': mae,
            'rmse': rmse,
            'direction_accuracy': direction_accuracy
        }

        print("\nEvaluation Metrics:")
        for key, value in metrics.items():
            print(f"{key}: {value:.6f}")

        return metrics

    def plot_training_history(self, save_path: str = 'models/training_history.png') -> None:
        """Plot training and validation loss."""
        if self.history is None:
            print("No training history available.")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

        # Loss plot
        ax1.plot(self.history.history['loss'], label='Training Loss')
        if 'val_loss' in self.history.history:
            ax1.plot(self.history.history['val_loss'], label='Validation Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss (MSE)')
        ax1.set_title('Model Loss')
        ax1.legend()
        ax1.grid(True)

        # MAE plot
        ax2.plot(self.history.history['mae'], label='Training MAE')
        if 'val_mae' in self.history.history:
            ax2.plot(self.history.history['val_mae'], label='Validation MAE')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('MAE')
        ax2.set_title('Mean Absolute Error')
        ax2.legend()
        ax2.grid(True)

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Training history plot saved to {save_path}")
        plt.close()

    def save_model(self, filepath: str = 'models/lstm_model.keras') -> None:
        """Save the trained model."""
        Path(filepath).parent.mkdir(exist_ok=True)
        self.model.save(filepath)
        print(f"Model saved to {filepath}")

    def load_model(self, filepath: str = 'models/lstm_model.keras') -> None:
        """Load a trained model."""
        self.model = keras.models.load_model(filepath)
        print(f"Model loaded from {filepath}")


def main() -> None:
    """Train the LSTM model."""
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))

    from data.preprocess import DataPreprocessor

    print("Loading and preprocessing data...")

    # Load processed data
    data_dir = Path('data')
    csv_files = list(data_dir.glob('*.csv'))

    if not csv_files:
        print("No data files found. Run fetch_data.py first.")
        sys.exit(1)

    latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
    df = pd.read_csv(latest_file)
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Preprocess data
    preprocessor = DataPreprocessor()
    df_processed = preprocessor.add_technical_indicators(df)
    X, y, indices = preprocessor.create_sequences(df_processed, lookback=60)
    preprocessor.save_scaler()

    # Split data: 70% train, 15% validation, 15% test
    train_size = int(len(X) * 0.7)
    val_size = int(len(X) * 0.15)

    X_train = X[:train_size]
    y_train = y[:train_size]

    X_val = X[train_size:train_size + val_size]
    y_val = y[train_size:train_size + val_size]

    X_test = X[train_size + val_size:]
    y_test = y[train_size + val_size:]

    print(f"\nData split:")
    print(f"Training: {len(X_train)} samples")
    print(f"Validation: {len(X_val)} samples")
    print(f"Test: {len(X_test)} samples")

    # Train model
    model = LSTMPricePredictor()
    model.train(X_train, y_train, X_val, y_val)

    # Evaluate on test set
    print("\n=== Test Set Performance ===")
    metrics = model.evaluate(X_test, y_test)

    # Plot training history
    model.plot_training_history()

    # Save model
    model.save_model()

    # Save predictions for analysis
    test_predictions = model.predict(X_test)
    results_df = pd.DataFrame({
        'actual': y_test,
        'predicted': test_predictions.flatten(),
        'datetime': df['datetime'].iloc[indices[train_size + val_size:]]
    })

    results_path = data_dir / 'predictions.csv'
    results_df.to_csv(results_path, index=False)
    print(f"\nPredictions saved to {results_path}")

    print("\n=== Training Complete ===")
    print("Next step: Run backtesting with the trained model")


if __name__ == '__main__':
    main()
