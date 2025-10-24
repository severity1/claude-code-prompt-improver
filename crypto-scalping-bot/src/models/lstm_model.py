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


class LSTMPricePredictor:
    """LSTM neural network for predicting crypto prices."""

    def __init__(self, config_path='config/config.yaml'):
        """Initialize the LSTM model with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.model = None
        self.history = None

    def build_model(self, input_shape):
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
        # return_sequences=True means the LSTM will output the full sequence (needed when stacking LSTMs)
        # return_sequences=False means only the final output is returned (used for the last LSTM layer)
        model.add(layers.LSTM(
            lstm_units[0],  # Number of LSTM units (memory cells) in the first layer
            return_sequences=True if len(lstm_units) > 1 else False,  # True if we're stacking multiple LSTM layers
            input_shape=input_shape  # (timesteps, features) e.g., (60, 20)
        ))
        # Dropout prevents overfitting by randomly setting a fraction of input units to 0 during training
        model.add(layers.Dropout(dropout_rate))

        # Additional LSTM layers (if configured for a deeper network)
        for i, units in enumerate(lstm_units[1:]):
            # For all layers except the last one, return_sequences=True to pass the sequence to the next LSTM
            # The last LSTM layer returns only the final output (return_sequences=False)
            return_seq = i < len(lstm_units) - 2
            model.add(layers.LSTM(units, return_sequences=return_seq))
            model.add(layers.Dropout(dropout_rate))

        # Output layer: Single neuron that predicts the next price (regression task)
        model.add(layers.Dense(1))

        # Compile model with Adam optimizer and Mean Squared Error loss
        # MSE is appropriate for regression tasks (price prediction)
        optimizer = keras.optimizers.Adam(learning_rate=learning_rate)
        model.compile(
            optimizer=optimizer,
            loss='mse',  # Mean Squared Error: measures average squared difference between predictions and actual values
            metrics=['mae']  # Mean Absolute Error: easier to interpret than MSE (in same units as target)
        )

        self.model = model

        print("\nModel Architecture:")
        model.summary()

        return model

    def train(self, X_train, y_train, X_val=None, y_val=None):
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

        # Callbacks for training optimization and model checkpointing
        # Early Stopping: Stops training when validation loss stops improving
        # This prevents overfitting and saves computation time
        early_stopping = callbacks.EarlyStopping(
            monitor='val_loss' if X_val is not None else 'loss',  # Metric to monitor
            patience=10,  # Number of epochs with no improvement before stopping
            restore_best_weights=True,  # Restore model weights from the epoch with best monitored value
            verbose=1
        )

        # Learning Rate Reduction: Reduces learning rate when a metric has stopped improving
        # Helps the model fine-tune by taking smaller steps as it approaches optimal weights
        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss' if X_val is not None else 'loss',
            factor=0.5,  # Factor by which the learning rate will be reduced (new_lr = lr * factor)
            patience=5,  # Number of epochs with no improvement before reducing LR
            min_lr=1e-7,  # Lower bound on the learning rate
            verbose=1
        )

        # Model Checkpoint: Saves the model after every epoch (only if it's the best so far)
        checkpoint_dir = Path('models/checkpoints')
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        model_checkpoint = callbacks.ModelCheckpoint(
            checkpoint_dir / 'best_model.keras',
            monitor='val_loss' if X_val is not None else 'loss',
            save_best_only=True,  # Only save when the monitored metric improves
            verbose=1
        )

        callback_list = [early_stopping, reduce_lr, model_checkpoint]

        # Prepare validation data tuple for training
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

    def predict(self, X):
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

    def evaluate(self, X_test, y_test):
        """
        Evaluate model performance on test data.

        Args:
            X_test (np.array): Test sequences
            y_test (np.array): Test targets

        Returns:
            dict: Evaluation metrics
        """
        predictions = self.predict(X_test)

        # Calculate standard regression metrics
        mse = np.mean((predictions.flatten() - y_test) ** 2)  # Mean Squared Error
        mae = np.mean(np.abs(predictions.flatten() - y_test))  # Mean Absolute Error
        rmse = np.sqrt(mse)  # Root Mean Squared Error (in same units as target)

        # Direction accuracy: Critical metric for trading strategy
        # This measures whether we correctly predict if price will go UP or DOWN
        # More important than exact price prediction for trading decisions
        # np.diff calculates the difference between consecutive elements (price changes)
        actual_direction = np.sign(np.diff(y_test))  # +1 for up, -1 for down, 0 for no change
        pred_direction = np.sign(np.diff(predictions.flatten()))  # Same for predictions
        # Calculate percentage of times we correctly predicted the direction
        direction_accuracy = np.mean(actual_direction == pred_direction)

        metrics = {
            'mse': mse,
            'mae': mae,
            'rmse': rmse,
            'direction_accuracy': direction_accuracy  # >0.5 means better than random guessing
        }

        print("\nEvaluation Metrics:")
        for key, value in metrics.items():
            print(f"{key}: {value:.6f}")

        return metrics

    def plot_training_history(self, save_path='models/training_history.png'):
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

    def save_model(self, filepath='models/lstm_model.keras'):
        """Save the trained model."""
        Path(filepath).parent.mkdir(exist_ok=True)
        self.model.save(filepath)
        print(f"Model saved to {filepath}")

    def load_model(self, filepath='models/lstm_model.keras'):
        """Load a trained model."""
        self.model = keras.models.load_model(filepath)
        print(f"Model loaded from {filepath}")


def main():
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
