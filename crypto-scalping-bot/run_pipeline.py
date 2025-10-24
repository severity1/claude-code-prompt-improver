#!/usr/bin/env python3
"""
Complete pipeline to run the crypto scalping bot from start to finish.

Usage:
    python run_pipeline.py [--skip-fetch] [--skip-train]

Options:
    --skip-fetch    Skip data fetching step (use existing data)
    --skip-train    Skip model training (use existing model)
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))


def run_pipeline(skip_fetch=False, skip_train=False):
    """Run the complete trading bot pipeline from data fetching to backtesting.

    This function orchestrates the entire workflow:
    1. Fetches historical OHLCV data from OKX
    2. Preprocesses data and adds technical indicators
    3. Trains the LSTM model
    4. Runs backtest with the trained model

    Args:
        skip_fetch (bool, optional): If True, skips data fetching step and uses existing data.
            Defaults to False.
        skip_train (bool, optional): If True, skips model training step and uses existing model.
            Defaults to False.

    Returns:
        bool: True if pipeline completed successfully, False if any step failed.

    Example:
        >>> # Run complete pipeline
        >>> run_pipeline()

        >>> # Skip fetching if data already exists
        >>> run_pipeline(skip_fetch=True)

        >>> # Use existing data and model, only run backtest
        >>> run_pipeline(skip_fetch=True, skip_train=True)
    """
    print("=" * 70)
    print("CRYPTO SCALPING BOT - COMPLETE PIPELINE")
    print("=" * 70)

    # Step 1: Fetch data
    if not skip_fetch:
        print("\n" + "=" * 70)
        print("STEP 1: FETCHING HISTORICAL DATA")
        print("=" * 70)
        try:
            from data.fetch_data import main as fetch_main
            fetch_main()
        except Exception as e:
            print(f"Error fetching data: {e}")
            print("You can skip this step with --skip-fetch if you already have data")
            return False
    else:
        print("\nSkipping data fetch (using existing data)")

    # Step 2: Preprocess data
    print("\n" + "=" * 70)
    print("STEP 2: PREPROCESSING DATA AND ADDING INDICATORS")
    print("=" * 70)
    try:
        from data.preprocess import main as preprocess_main
        preprocess_main()
    except Exception as e:
        print(f"Error preprocessing data: {e}")
        return False

    # Step 3: Train LSTM model
    if not skip_train:
        print("\n" + "=" * 70)
        print("STEP 3: TRAINING LSTM MODEL")
        print("=" * 70)
        try:
            from models.lstm_model import main as train_main
            train_main()
        except Exception as e:
            print(f"Error training model: {e}")
            print("You can skip this step with --skip-train if you already have a trained model")
            return False
    else:
        print("\nSkipping model training (using existing model)")

    # Step 4: Run backtest
    print("\n" + "=" * 70)
    print("STEP 4: RUNNING BACKTEST")
    print("=" * 70)
    try:
        from backtesting.backtest_runner import main as backtest_main
        backtest_main()
    except Exception as e:
        print(f"Error running backtest: {e}")
        return False

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE!")
    print("=" * 70)
    print("\nResults are available in the 'results' directory:")
    print("  - backtest_plot.html: Interactive backtest visualization")
    print("  - backtest_results.csv: Detailed backtest metrics")
    print("  - strategy_comparison.csv: Comparison of different strategies")
    print("  - equity_curve.png: Equity and drawdown charts")
    print("\nNext steps:")
    print("  1. Review the backtest results")
    print("  2. Analyze the strategy comparison to see which variant performs best")
    print("  3. Iterate on model architecture and strategy parameters")
    print("  4. Run parameter optimization if needed")
    print("=" * 70)

    return True


def main():
    """Parse command-line arguments and run the trading bot pipeline.

    This function handles command-line argument parsing for the pipeline script.
    It accepts optional flags to skip data fetching and model training steps.

    Returns:
        None: Exits with code 0 on success, 1 on failure.

    Example:
        Command-line usage:
        $ python run_pipeline.py
        $ python run_pipeline.py --skip-fetch
        $ python run_pipeline.py --skip-train
        $ python run_pipeline.py --skip-fetch --skip-train
    """
    parser = argparse.ArgumentParser(
        description='Run the complete crypto scalping bot pipeline'
    )
    parser.add_argument(
        '--skip-fetch',
        action='store_true',
        help='Skip data fetching (use existing data)'
    )
    parser.add_argument(
        '--skip-train',
        action='store_true',
        help='Skip model training (use existing model)'
    )

    args = parser.parse_args()

    success = run_pipeline(
        skip_fetch=args.skip_fetch,
        skip_train=args.skip_train
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
