# Crypto Scalping Bot with Deep Learning

A high-frequency crypto perpetual futures trading bot that uses LSTM neural networks for scalping both long and short positions.

## Features

- **Exchange**: OKX Perpetual Futures
- **Strategy**: Deep learning-based scalping (1-5 minute timeframes)
- **Model**: LSTM neural networks for price prediction
- **Directions**: Both long and short positions
- **Backtesting**: Historical simulation using real market data

## Project Structure

```
crypto-scalping-bot/
├── src/
│   ├── data/              # Data fetching and preprocessing
│   ├── models/            # LSTM and ML models
│   ├── strategies/        # Trading strategy logic
│   └── backtesting/       # Simulation and backtesting
├── config/                # Configuration files
├── notebooks/             # Jupyter notebooks for experimentation
├── tests/                 # Unit tests
└── requirements.txt       # Python dependencies
```

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment** (optional for backtesting):
   ```bash
   cp .env.example .env
   # Edit .env with your OKX API credentials if fetching live data
   ```

3. **Adjust configuration**:
   Edit `config/config.yaml` to customize trading parameters, model architecture, and backtesting settings.

## Usage

### 1. Fetch Historical Data
```bash
python src/data/fetch_data.py
```

### 2. Train LSTM Model
```bash
python src/models/train_lstm.py
```

### 3. Run Backtest
```bash
python src/backtesting/run_backtest.py
```

### 4. Analyze Results
```bash
python src/backtesting/analyze_results.py
```

## Strategy Overview

The bot uses a multi-step approach:

1. **Data Collection**: Fetches 1-minute OHLCV data from OKX perpetual futures
2. **Feature Engineering**: Calculates technical indicators (RSI, MACD, Bollinger Bands)
3. **Price Prediction**: LSTM model predicts next-period price movement
4. **Signal Generation**: Generates long/short signals based on predictions and confidence thresholds
5. **Risk Management**: Applies position sizing, stop-loss, and take-profit rules
6. **Execution**: Simulates trades with realistic fees and slippage

## Risk Warning

This is experimental software for educational and research purposes. Cryptocurrency trading involves substantial risk of loss. Never trade with money you cannot afford to lose. Always test thoroughly with paper trading before considering live deployment.

## Next Steps

1. Run initial backtest with default parameters
2. Analyze performance metrics
3. Iterate on model architecture and hyperparameters
4. Implement more sophisticated features (order book data, sentiment analysis)
5. Consider ensemble methods or reinforcement learning
