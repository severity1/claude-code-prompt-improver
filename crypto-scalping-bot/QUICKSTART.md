# Quick Start Guide

Get your crypto scalping bot up and running in minutes!

## Prerequisites

- Python 3.8 or higher
- pip package manager
- 2-4 GB of free disk space (for data and models)

## Installation

### 1. Install Dependencies

```bash
cd crypto-scalping-bot
pip install -r requirements.txt
```

This will install all required packages including:
- CCXT (exchange connectivity)
- TensorFlow (deep learning)
- Backtesting.py (simulation framework)
- Technical analysis libraries

### 2. Configure Settings (Optional)

The default configuration works out of the box, but you can customize:

```bash
# Edit trading parameters, model architecture, etc.
nano config/config.yaml
```

Key settings you might want to adjust:
- `trading.symbol`: Which crypto to trade (default: BTC/USDT:USDT)
- `trading.initial_capital`: Starting capital for backtest (default: $10,000)
- `model.epochs`: Training epochs (default: 50)
- `backtesting.start_date`: Backtest period start

## Running the Bot

### Option 1: Complete Pipeline (Recommended for First Run)

Run everything in one go:

```bash
python run_pipeline.py
```

This will:
1. Fetch historical data from OKX (2024 data by default)
2. Preprocess data and calculate technical indicators
3. Train the LSTM model
4. Run backtests with multiple strategy variants
5. Generate performance reports and visualizations

**Note:** First run will take 15-30 minutes depending on your hardware.

### Option 2: Step-by-Step Execution

If you prefer to run each step manually:

```bash
# 1. Fetch historical data
cd src/data
python fetch_data.py

# 2. Preprocess and add indicators
python preprocess.py

# 3. Train LSTM model
cd ../models
python train_lstm.py

# 4. Run backtest
cd ../backtesting
python backtest_runner.py
```

### Option 3: Quick Iterations (After First Run)

Once you have data and a trained model, you can skip those steps:

```bash
# Skip data fetch and training
python run_pipeline.py --skip-fetch --skip-train

# Or just skip data fetch
python run_pipeline.py --skip-fetch
```

## Understanding the Results

After running, check the `results/` directory:

### Key Files

1. **backtest_plot.html** - Interactive visualization
   - Open in your browser
   - Shows equity curve, trades, and indicators
   - Zoom and pan to explore different periods

2. **backtest_results.csv** - Detailed metrics
   - Return percentage
   - Sharpe ratio
   - Max drawdown
   - Win rate
   - Trade statistics

3. **strategy_comparison.csv** - Compare variants
   - Default LSTM strategy
   - Aggressive variant (tighter stops, higher frequency)
   - Conservative variant (wider stops, lower frequency)

4. **equity_curve.png** - Equity and drawdown charts

5. **training_history.png** - Model training progress

### Key Metrics to Watch

- **Return [%]**: Total profit/loss percentage
- **Sharpe Ratio**: Risk-adjusted returns (higher is better, >1 is good)
- **Max Drawdown [%]**: Worst peak-to-trough decline (lower is better)
- **Win Rate [%]**: Percentage of profitable trades
- **Profit Factor**: Gross profit / gross loss (>1 is profitable)

## Next Steps

### 1. Analyze Results

```bash
# View results summary
cat results/backtest_results.csv

# Open interactive plot
open results/backtest_plot.html
```

### 2. Iterate on the Strategy

Edit parameters in `config/config.yaml`:
- Adjust stop-loss and take-profit levels
- Change LSTM architecture (layers, units)
- Modify technical indicators
- Try different prediction thresholds

Then re-run:
```bash
python run_pipeline.py --skip-fetch
```

### 3. Optimize Parameters

The backtest runner includes parameter optimization:

```python
# Edit src/backtesting/backtest_runner.py
# Uncomment the optimization section at the bottom
# Then run the backtest
```

### 4. Try Different Time Periods

```bash
# Edit config/config.yaml
# Change backtesting.start_date and end_date
# Then re-fetch data
python run_pipeline.py
```

## Troubleshooting

### "No data files found"
Run the data fetching step:
```bash
cd src/data
python fetch_data.py
```

### "Model not trained"
Train the LSTM model:
```bash
cd src/models
python train_lstm.py
```

### Rate limit errors from OKX
The script includes automatic rate limiting, but if you still hit limits:
- Wait a few minutes
- Edit `src/data/fetch_data.py` and increase the sleep time

### Out of memory during training
Reduce batch size in `config/config.yaml`:
```yaml
model:
  batch_size: 16  # Reduce from 32
```

### Poor backtest performance
This is normal for a first iteration! Try:
1. Training on more data
2. Adjusting strategy parameters
3. Adding more features to the model
4. Trying different LSTM architectures

## Understanding the Strategy

The bot uses a multi-layered approach:

1. **LSTM Prediction**: Predicts next-period price
2. **Signal Generation**: Generates long/short signals based on predictions
3. **Confirmation**: Uses RSI and MACD to confirm signals
4. **Risk Management**: Applies stop-loss and take-profit automatically
5. **Position Sizing**: Manages position size based on equity

### Long Signal Conditions
- LSTM predicts price increase > threshold (default 0.2%)
- RSI < 70 (not overbought)
- MACD > Signal line (bullish momentum)

### Short Signal Conditions
- LSTM predicts price decrease > threshold
- RSI > 30 (not oversold)
- MACD < Signal line (bearish momentum)

## Important Disclaimers

⚠️ **This is for educational and research purposes only**

- Past performance does not guarantee future results
- Backtests can be misleading due to overfitting
- Real trading involves slippage, latency, and market impact
- Never trade with money you can't afford to lose
- Always paper trade extensively before considering live deployment

## Support and Resources

- Check the main README.md for architecture details
- Review the code comments for implementation details
- See config/config.yaml for all configurable parameters
- Review individual module files for specific functionality

## What's Next?

After you're comfortable with the simulator:

1. **Enhance the Model**
   - Try transformer architectures
   - Add more features (order book data, funding rates)
   - Implement ensemble methods

2. **Improve the Strategy**
   - Add volatility-based position sizing
   - Implement dynamic stop-loss adjustment
   - Add time-based filters (avoid low-liquidity periods)

3. **Advanced Analysis**
   - Walk-forward optimization
   - Monte Carlo simulation
   - Sensitivity analysis

4. **Production Considerations** (only after extensive testing!)
   - Paper trading with live data
   - Implement proper logging and monitoring
   - Add circuit breakers and kill switches
   - Consider using Hummingbot for live execution

Happy trading! 🚀
