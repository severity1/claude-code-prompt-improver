"""
Run backtests with the LSTM trading strategy.
"""

import pandas as pd
import numpy as np
from backtesting import Backtest
from pathlib import Path
import yaml
import sys

sys.path.append(str(Path(__file__).parent.parent))

from strategies.lstm_strategy import LSTMScalpingStrategy, AggressiveLSTMStrategy, ConservativeLSTMStrategy
from models.lstm_model import LSTMPricePredictor
from data.preprocess import DataPreprocessor


class BacktestRunner:
    """Run and manage backtests for the trading bot."""

    def __init__(self, config_path='config/config.yaml'):
        """Initialize backtest runner with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.results = None
        self.bt = None

    def prepare_data_for_backtest(self, df, predictions):
        """
        Prepare data in the format required by backtesting.py.

        Args:
            df (pd.DataFrame): OHLCV data with technical indicators
            predictions (np.array): LSTM predictions

        Returns:
            pd.DataFrame: Data formatted for backtesting.py
        """
        # Backtesting.py requires specific column names
        bt_data = pd.DataFrame({
            'Open': df['open'].values,
            'High': df['high'].values,
            'Low': df['low'].values,
            'Close': df['close'].values,
            'Volume': df['volume'].values,
        }, index=pd.to_datetime(df['datetime']))

        # Add technical indicators
        bt_data['RSI'] = df['rsi_14'].values
        bt_data['MACD'] = df['macd'].values
        bt_data['MACD_Signal'] = df['macd_signal'].values
        bt_data['BB_Upper'] = df['bb_upper'].values
        bt_data['BB_Lower'] = df['bb_lower'].values

        # Add predictions (align with dataframe length)
        if len(predictions) < len(bt_data):
            # Pad with NaN at the beginning
            padded_predictions = np.full(len(bt_data), np.nan)
            padded_predictions[-len(predictions):] = predictions
            bt_data['Predicted_Price'] = padded_predictions
        else:
            bt_data['Predicted_Price'] = predictions[:len(bt_data)]

        # Drop rows with NaN predictions
        bt_data = bt_data.dropna()

        return bt_data

    def run_backtest(self, data, strategy_class=LSTMScalpingStrategy, cash=10000, commission=0.0004):
        """
        Run a backtest with the specified strategy.

        Args:
            data (pd.DataFrame): Prepared data for backtesting
            strategy_class: Strategy class to use
            cash (float): Initial capital
            commission (float): Trading commission (0.0004 = 0.04%)

        Returns:
            pd.Series: Backtest results
        """
        self.bt = Backtest(
            data,
            strategy_class,
            cash=cash,
            commission=commission,
            exclusive_orders=True,  # Close position before opening new one
            trade_on_close=False    # Trade on open of next bar
        )

        print(f"\nRunning backtest with {strategy_class.__name__}...")
        print(f"Initial capital: ${cash:,.2f}")
        print(f"Commission: {commission * 100}%")
        print(f"Data period: {data.index[0]} to {data.index[-1]}")
        print(f"Total bars: {len(data)}")

        self.results = self.bt.run()

        return self.results

    def print_results(self):
        """Print backtest results in a formatted way."""
        if self.results is None:
            print("No results available. Run a backtest first.")
            return

        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)

        # Key metrics
        print(f"\nPerformance:")
        print(f"  Start Value:              ${self.results['Start']:,.2f}")
        print(f"  End Value:                ${self.results['End']:,.2f}")
        print(f"  Return:                   {self.results['Return [%]']:.2f}%")
        print(f"  Max Drawdown:             {self.results['Max. Drawdown [%]']:.2f}%")
        print(f"  Sharpe Ratio:             {self.results['Sharpe Ratio']:.2f}")

        print(f"\nTrades:")
        print(f"  Total Trades:             {self.results['# Trades']}")
        print(f"  Win Rate:                 {self.results['Win Rate [%]']:.2f}%")
        print(f"  Best Trade:               {self.results['Best Trade [%]']:.2f}%")
        print(f"  Worst Trade:              {self.results['Worst Trade [%]']:.2f}%")
        print(f"  Avg Trade:                {self.results['Avg. Trade [%]']:.2f}%")

        print(f"\nRisk Metrics:")
        print(f"  Max Drawdown Duration:    {self.results['Max. Drawdown Duration']}")
        print(f"  Calmar Ratio:             {self.results.get('Calmar Ratio', 'N/A')}")

        print("\n" + "=" * 60)

    def plot_results(self, save_path='results/backtest_plot.html'):
        """Generate interactive plot of backtest results."""
        if self.bt is None:
            print("No backtest available. Run a backtest first.")
            return

        Path(save_path).parent.mkdir(exist_ok=True)
        self.bt.plot(filename=save_path, open_browser=False)
        print(f"\nBacktest plot saved to {save_path}")

    def optimize_strategy(self, data, cash=10000, commission=0.0004):
        """
        Optimize strategy parameters using grid search.

        Args:
            data (pd.DataFrame): Prepared data for backtesting
            cash (float): Initial capital
            commission (float): Trading commission

        Returns:
            pd.DataFrame: Optimization results
        """
        print("\nOptimizing strategy parameters...")
        print("This may take several minutes...")

        bt = Backtest(
            data,
            LSTMScalpingStrategy,
            cash=cash,
            commission=commission,
            exclusive_orders=True
        )

        # Parameter grid
        optimization_results = bt.optimize(
            prediction_threshold=[0.001, 0.002, 0.003, 0.004],
            stop_loss_pct=[0.003, 0.005, 0.007, 0.01],
            take_profit_pct=[0.006, 0.01, 0.015, 0.02],
            position_size=[0.5, 0.7, 0.9, 0.95],
            maximize='Sharpe Ratio',
            constraint=lambda p: p.take_profit_pct > p.stop_loss_pct
        )

        print("\nOptimal parameters found:")
        print(optimization_results)

        return optimization_results


def main():
    """Run the full backtest pipeline."""
    print("=" * 60)
    print("CRYPTO SCALPING BOT - BACKTEST")
    print("=" * 60)

    # 1. Load data and model
    print("\n1. Loading data and model...")
    data_dir = Path('data')

    # Load processed data with indicators
    processed_data_path = data_dir / 'processed_data.csv'
    if not processed_data_path.exists():
        print("Processed data not found. Run preprocess.py first.")
        sys.exit(1)

    df = pd.read_csv(processed_data_path)
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Load predictions
    predictions_path = data_dir / 'predictions.csv'
    if not predictions_path.exists():
        print("Predictions not found. Train the LSTM model first.")
        sys.exit(1)

    predictions_df = pd.read_csv(predictions_path)

    # 2. Load preprocessor and unscale predictions
    print("\n2. Preparing predictions...")
    preprocessor = DataPreprocessor()
    preprocessor.load_scaler()

    # Unscale predictions
    predictions_unscaled = preprocessor.inverse_transform_predictions(
        predictions_df['predicted'].values,
        feature_idx=0  # Close price is first feature
    )

    # Align predictions with processed data
    # Match by datetime
    pred_dates = pd.to_datetime(predictions_df['datetime'])
    pred_dict = dict(zip(pred_dates, predictions_unscaled))

    # Add predictions to dataframe
    df['predicted_price'] = df['datetime'].map(pred_dict)

    # 3. Prepare data for backtesting
    print("\n3. Preparing data for backtesting...")
    runner = BacktestRunner()
    bt_data = runner.prepare_data_for_backtest(
        df[df['predicted_price'].notna()],
        df[df['predicted_price'].notna()]['predicted_price'].values
    )

    print(f"Backtest data ready: {len(bt_data)} bars")

    # 4. Run backtest with default strategy
    print("\n4. Running backtest with default LSTM strategy...")
    results = runner.run_backtest(
        bt_data,
        strategy_class=LSTMScalpingStrategy,
        cash=runner.config['trading']['initial_capital'],
        commission=runner.config['backtesting']['commission']
    )

    runner.print_results()

    # 5. Save results
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)

    results_path = results_dir / 'backtest_results.csv'
    results.to_csv(results_path)
    print(f"\nResults saved to {results_path}")

    # 6. Plot results
    runner.plot_results()

    # 7. Compare strategies
    print("\n" + "=" * 60)
    print("COMPARING STRATEGY VARIANTS")
    print("=" * 60)

    strategies = [
        ('Aggressive', AggressiveLSTMStrategy),
        ('Conservative', ConservativeLSTMStrategy),
    ]

    comparison_results = []

    for name, strategy_class in strategies:
        print(f"\nTesting {name} strategy...")
        results = runner.run_backtest(
            bt_data,
            strategy_class=strategy_class,
            cash=runner.config['trading']['initial_capital'],
            commission=runner.config['backtesting']['commission']
        )

        comparison_results.append({
            'Strategy': name,
            'Return [%]': results['Return [%]'],
            'Sharpe Ratio': results['Sharpe Ratio'],
            'Max Drawdown [%]': results['Max. Drawdown [%]'],
            'Win Rate [%]': results['Win Rate [%]'],
            '# Trades': results['# Trades']
        })

    # Create comparison DataFrame
    comparison_df = pd.DataFrame(comparison_results)
    print("\n" + "=" * 60)
    print("STRATEGY COMPARISON")
    print("=" * 60)
    print(comparison_df.to_string(index=False))

    comparison_path = results_dir / 'strategy_comparison.csv'
    comparison_df.to_csv(comparison_path, index=False)
    print(f"\nComparison saved to {comparison_path}")

    print("\n" + "=" * 60)
    print("BACKTEST COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
