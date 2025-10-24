"""
LSTM-based scalping strategy for crypto perpetual futures.
"""

import numpy as np
import pandas as pd
from backtesting import Strategy
from backtesting.lib import crossover
import yaml


class LSTMScalpingStrategy(Strategy):
    """
    Scalping strategy using LSTM predictions for both long and short positions.

    The strategy generates signals based on:
    1. LSTM price predictions
    2. Prediction confidence (magnitude of predicted change)
    3. Technical indicator confirmation (RSI, MACD)
    4. Risk management rules
    """

    # Strategy parameters (can be optimized)
    prediction_threshold = 0.002  # Minimum predicted price change (0.2%)
    rsi_oversold = 30
    rsi_overbought = 70
    stop_loss_pct = 0.005        # 0.5% stop loss
    take_profit_pct = 0.01       # 1% take profit
    position_size = 0.95         # Use 95% of available equity

    def init(self):
        """Initialize strategy with indicators and predictions."""
        # Get predictions from the dataframe
        # These should be added to the data before backtesting
        self.predictions = self.data.Predicted_Price  # LSTM model's price predictions
        self.current_price = self.data.Close  # Actual closing prices

        # Calculate prediction signal strength
        # This converts absolute price predictions to percentage changes
        # Example: if current price is $100 and predicted is $100.50, this gives 0.005 (0.5%)
        # Positive values = predicted price increase, Negative values = predicted price decrease
        self.price_change_predicted = (
            (self.predictions - self.current_price) / self.current_price
        )

        # Technical indicators from data (used for confirmation of LSTM signals)
        self.rsi = self.data.RSI  # Relative Strength Index: identifies overbought/oversold conditions
        self.macd = self.data.MACD  # Moving Average Convergence Divergence: trend-following momentum indicator
        self.macd_signal = self.data.MACD_Signal  # Signal line for MACD crossovers

    def next(self):
        """Execute strategy logic on each bar."""
        # Skip if not enough data
        if len(self.data) < 2:
            return

        # Get current values ([-1] means the most recent/current bar)
        current_prediction = self.price_change_predicted[-1]  # Predicted price change percentage
        current_rsi = self.rsi[-1]
        current_macd = self.macd[-1]
        current_macd_signal = self.macd_signal[-1]

        # If we have an open position, manage it (check exit conditions)
        # Return early to avoid opening new positions while one is active
        if self.position:
            self._manage_position()
            return

        # Only open new positions when we don't have an active one
        # Generate long signal (buy/bullish position)
        if self._should_go_long(current_prediction, current_rsi, current_macd, current_macd_signal):
            self._open_long()

        # Generate short signal (sell/bearish position)
        elif self._should_go_short(current_prediction, current_rsi, current_macd, current_macd_signal):
            self._open_short()

    def _should_go_long(self, prediction, rsi, macd, macd_signal):
        """
        Determine if we should open a long position.

        Long conditions:
        - LSTM predicts price increase above threshold
        - RSI not overbought
        - MACD bullish (above signal line or crossing above)
        """
        # Check if LSTM prediction is bullish enough (predicts price increase > threshold)
        # Example: if threshold is 0.002 (0.2%), prediction must be > 0.002
        prediction_bullish = prediction > self.prediction_threshold

        # Ensure we're not buying into an overbought market (RSI < 70)
        # RSI > 70 typically indicates overbought conditions (may reverse downward)
        rsi_ok = rsi < self.rsi_overbought

        # Confirm with MACD: bullish when MACD line is above signal line
        # This indicates upward momentum
        macd_bullish = macd > macd_signal

        # All three conditions must be true for a long signal (conservative approach)
        return prediction_bullish and rsi_ok and macd_bullish

    def _should_go_short(self, prediction, rsi, macd, macd_signal):
        """
        Determine if we should open a short position.

        Short conditions:
        - LSTM predicts price decrease below threshold
        - RSI not oversold
        - MACD bearish (below signal line or crossing below)
        """
        # Check if LSTM prediction is bearish enough (predicts price decrease > threshold)
        # Example: if threshold is 0.002, prediction must be < -0.002
        prediction_bearish = prediction < -self.prediction_threshold

        # Ensure we're not selling into an oversold market (RSI > 30)
        # RSI < 30 typically indicates oversold conditions (may reverse upward)
        rsi_ok = rsi > self.rsi_oversold

        # Confirm with MACD: bearish when MACD line is below signal line
        # This indicates downward momentum
        macd_bearish = macd < macd_signal

        # All three conditions must be true for a short signal (conservative approach)
        return prediction_bearish and rsi_ok and macd_bearish

    def _open_long(self):
        """Open a long position with risk management."""
        # Calculate position size based on available equity
        # size=0.95 means use 95% of available capital for this trade
        size = self.position_size

        # Set stop loss and take profit levels
        entry_price = self.data.Close[-1]
        # Stop loss: Exit if price drops by stop_loss_pct (e.g., 0.5%)
        # Example: entry=$100, stop_loss_pct=0.005 → sl_price=$99.50
        sl_price = entry_price * (1 - self.stop_loss_pct)
        # Take profit: Exit if price rises by take_profit_pct (e.g., 1%)
        # Example: entry=$100, take_profit_pct=0.01 → tp_price=$101.00
        tp_price = entry_price * (1 + self.take_profit_pct)

        # Execute the long trade with automatic stop-loss and take-profit
        self.buy(size=size, sl=sl_price, tp=tp_price)

    def _open_short(self):
        """Open a short position with risk management."""
        # Calculate position size based on available equity
        size = self.position_size

        # Set stop loss and take profit levels (reversed for short positions)
        entry_price = self.data.Close[-1]
        # Stop loss: Exit if price RISES by stop_loss_pct (loss on short)
        # Example: entry=$100, stop_loss_pct=0.005 → sl_price=$100.50
        sl_price = entry_price * (1 + self.stop_loss_pct)
        # Take profit: Exit if price FALLS by take_profit_pct (profit on short)
        # Example: entry=$100, take_profit_pct=0.01 → tp_price=$99.00
        tp_price = entry_price * (1 - self.take_profit_pct)

        # Execute the short trade with automatic stop-loss and take-profit
        self.sell(size=size, sl=sl_price, tp=tp_price)

    def _manage_position(self):
        """
        Manage existing position with trailing stop and exit conditions.

        This method monitors open positions and closes them early if:
        - The LSTM prediction reverses direction (early exit signal)
        - Stop-loss or take-profit levels are hit (handled automatically by backtesting framework)
        """
        current_prediction = self.price_change_predicted[-1]

        # Exit long position early if LSTM prediction turns bearish
        # This allows us to exit before hitting stop-loss if model predicts reversal
        if self.position.is_long and current_prediction < -self.prediction_threshold:
            self.position.close()

        # Exit short position early if LSTM prediction turns bullish
        # This allows us to exit before hitting stop-loss if model predicts reversal
        elif self.position.is_short and current_prediction > self.prediction_threshold:
            self.position.close()


class AggressiveLSTMStrategy(LSTMScalpingStrategy):
    """
    More aggressive version of the LSTM strategy with:
    - Lower prediction threshold
    - Tighter stops and targets
    - Higher position sizing
    """
    prediction_threshold = 0.001  # 0.1% threshold
    stop_loss_pct = 0.003        # 0.3% stop
    take_profit_pct = 0.006      # 0.6% target
    position_size = 0.98         # 98% of equity


class ConservativeLSTMStrategy(LSTMScalpingStrategy):
    """
    More conservative version with:
    - Higher prediction threshold
    - Wider stops and targets
    - Lower position sizing
    """
    prediction_threshold = 0.004  # 0.4% threshold
    stop_loss_pct = 0.01         # 1% stop
    take_profit_pct = 0.02       # 2% target
    position_size = 0.5          # 50% of equity
