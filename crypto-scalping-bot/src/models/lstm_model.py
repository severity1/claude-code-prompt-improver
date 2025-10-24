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
    """LSTM neural network for predicting cryptocurrency prices.

    This class provides a complete interface for building, training, evaluating,
    and saving LSTM models for time-series price prediction. It handles model
    architecture construction, training with callbacks, and performance evaluation.

    Attributes:
        config (dict): Configuration dictionary from YAML file.
        model (keras.Model): Compiled LSTM model, None until build_model() is called.
        history (keras.callbacks.History): Training history, None until train() is called.

    Example:
        >>> predictor = LSTMPricePredictor()
        >>> predictor.build_model(input_shape=(60, 15))
        >>> history = predictor.train(X_train, y_train, X_val, y_val)
        >>> predictions = predictor.predict(X_test)
        >>> predictor.save_model()
    """

    def __init__(self, config_path='config/config.yaml'):
        """Initialize the LSTM model with configuration from YAML file.

        Args:
            config_path (str, optional): Path to the YAML configuration file
                containing model hyperparameters. Defaults to 'config/config.yaml'.

        Example:
            >>> predictor = LSTMPricePredictor()
            >>> predictor = LSTMPricePredictor('custom/config.yaml')
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.model = None
        self.history = None

    def build_model(self, input_shape):
        """Build and compile LSTM model architecture with dropout regularization.

        Creates a sequential LSTM model with:
        - Multiple stacked LSTM layers (configured in config)
        - Dropout layers for regularization
        - Dense output layer for regression
        - Adam optimizer with MSE loss

        Args:
            input_shape (tuple): Shape of input sequences as (timesteps, n_features).
                Example: (60, 15) for 60 time steps with 15 features each.

        Returns:
            keras.Model: Compiled LSTM model ready for training.

        Example:
            >>> predictor = LSTMPricePredictor()
            >>> model = predictor.build_model(input_shape=(60, 15))
            >>> model.summary()
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

    def train(self, X_train, y_train, X_val=None, y_val=None):
        """Train the LSTM model with early stopping and learning rate scheduling.

        Automatically builds the model if not already built. Uses callbacks for:
        - Early stopping to prevent overfitting
        - Learning rate reduction on plateau
        - Model checkpointing to save best weights

        Args:
            X_train (np.ndarray): Training input sequences with shape
                (n_samples, timesteps, n_features).
            y_train (np.ndarray): Training target values with shape (n_samples,).
            X_val (np.ndarray, optional): Validation sequences. If None, no validation
                is performed. Defaults to None.
            y_val (np.ndarray, optional): Validation targets. Required if X_val is
                provided. Defaults to None.

        Returns:
            keras.callbacks.History: Training history object containing loss and
                metrics for each epoch.

        Example:
            >>> predictor = LSTMPricePredictor()
            >>> history = predictor.train(X_train, y_train, X_val, y_val)
            >>> print(f"Final loss: {history.history['loss'][-1]:.4f}")
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

    def predict(self, X):
        """Make predictions using the trained LSTM model.

        Args:
            X (np.ndarray): Input sequences with shape (n_samples, timesteps, n_features).
                Must have the same timesteps and features as the training data.

        Returns:
            np.ndarray: Predicted values with shape (n_samples, 1). Values are in
                the same scaled range as the training targets.

        Raises:
            ValueError: If model hasn't been trained yet.

        Example:
            >>> predictor = LSTMPricePredictor()
            >>> predictor.train(X_train, y_train)
            >>> predictions = predictor.predict(X_test)
            >>> print(f"Predicted shape: {predictions.shape}")
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict(X, verbose=0)

    def evaluate(self, X_test, y_test):
        """Evaluate model performance on test data with multiple metrics.

        Calculates comprehensive evaluation metrics including:
        - MSE (Mean Squared Error)
        - MAE (Mean Absolute Error)
        - RMSE (Root Mean Squared Error)
        - Direction accuracy (percentage of correct up/down predictions)

        Args:
            X_test (np.ndarray): Test input sequences with shape
                (n_samples, timesteps, n_features).
            y_test (np.ndarray): Test target values with shape (n_samples,).

        Returns:
            dict: Dictionary containing evaluation metrics:
                - 'mse': Mean squared error
                - 'mae': Mean absolute error
                - 'rmse': Root mean squared error
                - 'direction_accuracy': Percentage of correct directional predictions

        Example:
            >>> predictor = LSTMPricePredictor()
            >>> predictor.train(X_train, y_train)
            >>> metrics = predictor.evaluate(X_test, y_test)
            >>> print(f"RMSE: {metrics['rmse']:.4f}")
            >>> print(f"Direction Accuracy: {metrics['direction_accuracy']:.2%}")
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

    def plot_training_history(self, save_path='models/training_history.png'):
        """Plot and save training and validation loss/MAE curves.

        Creates a two-panel plot showing loss (MSE) and MAE over training epochs.
        Includes both training and validation curves if validation data was used.

        Args:
            save_path (str, optional): Path where the plot image will be saved.
                Defaults to 'models/training_history.png'.

        Returns:
            None

        Example:
            >>> predictor = LSTMPricePredictor()
            >>> predictor.train(X_train, y_train, X_val, y_val)
            >>> predictor.plot_training_history()
            >>> predictor.plot_training_history('results/my_plot.png')
        """
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
        """Save the trained model to disk in Keras format.

        Args:
            filepath (str, optional): Path where model will be saved.
                Defaults to 'models/lstm_model.keras'.

        Returns:
            None

        Example:
            >>> predictor = LSTMPricePredictor()
            >>> predictor.train(X_train, y_train)
            >>> predictor.save_model()
            >>> predictor.save_model('models/best_model_v2.keras')
        """
        Path(filepath).parent.mkdir(exist_ok=True)
        self.model.save(filepath)
        print(f"Model saved to {filepath}")

    def load_model(self, filepath='models/lstm_model.keras'):
        """Load a previously trained model from disk.

        Args:
            filepath (str, optional): Path to the saved model file.
                Defaults to 'models/lstm_model.keras'.

        Returns:
            None

        Example:
            >>> predictor = LSTMPricePredictor()
            >>> predictor.load_model()
            >>> predictions = predictor.predict(X_new)
        """
        self.model = keras.models.load_model(filepath)
        print(f"Model loaded from {filepath}")


def main():
    """Complete LSTM model training pipeline.

    Loads data, preprocesses it, splits into train/val/test sets,
    trains the LSTM model, evaluates performance, and saves artifacts.

    Returns:
        None

    Example:
        Run from command line:
        $ python lstm_model.py
    """
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
