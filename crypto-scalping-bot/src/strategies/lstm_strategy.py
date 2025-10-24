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
        self.predictions = self.data.Predicted_Price
        self.current_price = self.data.Close

        # Calculate prediction signal strength
        self.price_change_predicted = (
            (self.predictions - self.current_price) / self.current_price
        )

        # Technical indicators from data
        self.rsi = self.data.RSI
        self.macd = self.data.MACD
        self.macd_signal = self.data.MACD_Signal

    def next(self):
        """Execute strategy logic on each bar."""
        # Skip if not enough data
        if len(self.data) < 2:
            return

        current_prediction = self.price_change_predicted[-1]
        current_rsi = self.rsi[-1]
        current_macd = self.macd[-1]
        current_macd_signal = self.macd_signal[-1]

        # If we have a position, check stop-loss and take-profit
        if self.position:
            self._manage_position()
            return

        # Generate long signal
        if self._should_go_long(current_prediction, current_rsi, current_macd, current_macd_signal):
            self._open_long()

        # Generate short signal
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
        prediction_bullish = prediction > self.prediction_threshold
        rsi_ok = rsi < self.rsi_overbought
        macd_bullish = macd > macd_signal

        return prediction_bullish and rsi_ok and macd_bullish

    def _should_go_short(self, prediction, rsi, macd, macd_signal):
        """
        Determine if we should open a short position.

        Short conditions:
        - LSTM predicts price decrease below threshold
        - RSI not oversold
        - MACD bearish (below signal line or crossing below)
        """
        prediction_bearish = prediction < -self.prediction_threshold
        rsi_ok = rsi > self.rsi_oversold
        macd_bearish = macd < macd_signal

        return prediction_bearish and rsi_ok and macd_bearish

    def _open_long(self):
        """Open a long position with risk management."""
        # Calculate position size based on available equity
        size = self.position_size

        # Set stop loss and take profit
        entry_price = self.data.Close[-1]
        sl_price = entry_price * (1 - self.stop_loss_pct)
        tp_price = entry_price * (1 + self.take_profit_pct)

        self.buy(size=size, sl=sl_price, tp=tp_price)

    def _open_short(self):
        """Open a short position with risk management."""
        # Calculate position size based on available equity
        size = self.position_size

        # Set stop loss and take profit
        entry_price = self.data.Close[-1]
        sl_price = entry_price * (1 + self.stop_loss_pct)
        tp_price = entry_price * (1 - self.take_profit_pct)

        self.sell(size=size, sl=sl_price, tp=tp_price)

    def _manage_position(self):
        """
        Manage existing position with trailing stop and exit conditions.
        """
        current_prediction = self.price_change_predicted[-1]

        # Exit long if prediction turns bearish
        if self.position.is_long and current_prediction < -self.prediction_threshold:
            self.position.close()

        # Exit short if prediction turns bullish
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
