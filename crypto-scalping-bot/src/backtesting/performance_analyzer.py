"""
Performance analysis and visualization for backtest results.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json


class PerformanceAnalyzer:
    """Analyze and visualize trading performance."""

    def __init__(self, trades_df=None, equity_curve=None):
        """
        Initialize analyzer with trade data.

        Args:
            trades_df (pd.DataFrame): DataFrame of individual trades
            equity_curve (pd.Series): Time series of equity values
        """
        self.trades_df = trades_df
        self.equity_curve = equity_curve

    def calculate_metrics(self, initial_capital=10000):
        """
        Calculate comprehensive performance metrics.

        Args:
            initial_capital (float): Starting capital

        Returns:
            dict: Performance metrics
        """
        if self.trades_df is None or len(self.trades_df) == 0:
            return {}

        trades = self.trades_df.copy()

        # Basic metrics
        total_trades = len(trades)
        winning_trades = len(trades[trades['PnL'] > 0])
        losing_trades = len(trades[trades['PnL'] < 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # PnL metrics
        total_pnl = trades['PnL'].sum()
        avg_win = trades[trades['PnL'] > 0]['PnL'].mean() if winning_trades > 0 else 0
        avg_loss = trades[trades['PnL'] < 0]['PnL'].mean() if losing_trades > 0 else 0
        largest_win = trades['PnL'].max() if total_trades > 0 else 0
        largest_loss = trades['PnL'].min() if total_trades > 0 else 0

        # Risk metrics
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else float('inf')

        # Calculate returns
        returns = trades['PnL'] / initial_capital
        avg_return = returns.mean()
        std_return = returns.std()
        sharpe_ratio = (avg_return / std_return * np.sqrt(252)) if std_return > 0 else 0  # Annualized

        # Drawdown analysis
        if self.equity_curve is not None:
            running_max = self.equity_curve.expanding().max()
            drawdown = (self.equity_curve - running_max) / running_max * 100
            max_drawdown = drawdown.min()
            avg_drawdown = drawdown[drawdown < 0].mean() if len(drawdown[drawdown < 0]) > 0 else 0
        else:
            max_drawdown = 0
            avg_drawdown = 0

        # Trade duration
        if 'EntryTime' in trades.columns and 'ExitTime' in trades.columns:
            trades['Duration'] = pd.to_datetime(trades['ExitTime']) - pd.to_datetime(trades['EntryTime'])
            avg_duration = trades['Duration'].mean()
            max_duration = trades['Duration'].max()
            min_duration = trades['Duration'].min()
        else:
            avg_duration = max_duration = min_duration = None

        # Consecutive wins/losses
        trades['Win'] = trades['PnL'] > 0
        trades['Streak'] = trades['Win'].ne(trades['Win'].shift()).cumsum()
        win_streaks = trades[trades['Win']].groupby('Streak').size()
        loss_streaks = trades[~trades['Win']].groupby('Streak').size()
        max_consecutive_wins = win_streaks.max() if len(win_streaks) > 0 else 0
        max_consecutive_losses = loss_streaks.max() if len(loss_streaks) > 0 else 0

        metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate_pct': win_rate,
            'total_pnl': total_pnl,
            'total_return_pct': (total_pnl / initial_capital * 100),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'profit_factor': profit_factor,
            'avg_return_pct': avg_return * 100,
            'std_return_pct': std_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown,
            'avg_drawdown_pct': avg_drawdown,
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            'avg_trade_duration': str(avg_duration) if avg_duration else 'N/A',
            'max_trade_duration': str(max_duration) if max_duration else 'N/A',
            'min_trade_duration': str(min_duration) if min_duration else 'N/A',
        }

        return metrics

    def plot_equity_curve(self, save_path='results/equity_curve.png'):
        """Plot equity curve over time."""
        if self.equity_curve is None:
            print("No equity curve data available.")
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Equity curve
        ax1.plot(self.equity_curve.index, self.equity_curve.values, linewidth=2, color='#2E86AB')
        ax1.fill_between(self.equity_curve.index, self.equity_curve.values, alpha=0.3, color='#2E86AB')
        ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Equity ($)')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=self.equity_curve.iloc[0], color='red', linestyle='--', alpha=0.5, label='Initial Capital')
        ax1.legend()

        # Drawdown
        running_max = self.equity_curve.expanding().max()
        drawdown = (self.equity_curve - running_max) / running_max * 100

        ax2.fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='#A23B72')
        ax2.plot(drawdown.index, drawdown.values, linewidth=2, color='#A23B72')
        ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Drawdown (%)')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        Path(save_path).parent.mkdir(exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Equity curve plot saved to {save_path}")
        plt.close()

    def plot_trade_analysis(self, save_path='results/trade_analysis.png'):
        """Plot trade distribution and analysis."""
        if self.trades_df is None or len(self.trades_df) == 0:
            print("No trade data available.")
            return

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # PnL distribution
        ax1 = axes[0, 0]
        self.trades_df['PnL'].hist(bins=50, ax=ax1, color='#2E86AB', alpha=0.7, edgecolor='black')
        ax1.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax1.set_title('PnL Distribution', fontsize=12, fontweight='bold')
        ax1.set_xlabel('PnL ($)')
        ax1.set_ylabel('Frequency')
        ax1.grid(True, alpha=0.3)

        # Cumulative PnL
        ax2 = axes[0, 1]
        cumulative_pnl = self.trades_df['PnL'].cumsum()
        ax2.plot(cumulative_pnl.index, cumulative_pnl.values, linewidth=2, color='#F18F01')
        ax2.fill_between(cumulative_pnl.index, cumulative_pnl.values, alpha=0.3, color='#F18F01')
        ax2.set_title('Cumulative PnL', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Trade Number')
        ax2.set_ylabel('Cumulative PnL ($)')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='red', linestyle='--', alpha=0.5)

        # Win/Loss by hour (if timestamp available)
        ax3 = axes[1, 0]
        if 'EntryTime' in self.trades_df.columns:
            self.trades_df['Hour'] = pd.to_datetime(self.trades_df['EntryTime']).dt.hour
            hourly_pnl = self.trades_df.groupby('Hour')['PnL'].sum()
            colors = ['#06A77D' if x > 0 else '#D62246' for x in hourly_pnl.values]
            hourly_pnl.plot(kind='bar', ax=ax3, color=colors, alpha=0.7)
            ax3.set_title('PnL by Hour of Day', fontsize=12, fontweight='bold')
            ax3.set_xlabel('Hour')
            ax3.set_ylabel('Total PnL ($)')
            ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            ax3.grid(True, alpha=0.3, axis='y')
        else:
            ax3.text(0.5, 0.5, 'Hour data not available', ha='center', va='center')
            ax3.set_title('PnL by Hour of Day', fontsize=12, fontweight='bold')

        # Win rate over time (rolling)
        ax4 = axes[1, 1]
        self.trades_df['Win'] = self.trades_df['PnL'] > 0
        rolling_win_rate = self.trades_df['Win'].rolling(window=20, min_periods=1).mean() * 100
        ax4.plot(rolling_win_rate.index, rolling_win_rate.values, linewidth=2, color='#6A4C93')
        ax4.fill_between(rolling_win_rate.index, rolling_win_rate.values, alpha=0.3, color='#6A4C93')
        ax4.axhline(y=50, color='red', linestyle='--', linewidth=2, label='50% Baseline')
        ax4.set_title('Rolling Win Rate (20 trades)', fontsize=12, fontweight='bold')
        ax4.set_xlabel('Trade Number')
        ax4.set_ylabel('Win Rate (%)')
        ax4.set_ylim([0, 100])
        ax4.grid(True, alpha=0.3)
        ax4.legend()

        plt.tight_layout()
        Path(save_path).parent.mkdir(exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Trade analysis plot saved to {save_path}")
        plt.close()

    def plot_returns_distribution(self, save_path='results/returns_distribution.png'):
        """Plot returns distribution and statistics."""
        if self.trades_df is None or len(self.trades_df) == 0:
            print("No trade data available.")
            return

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Returns histogram with normal curve
        ax1 = axes[0]
        returns = self.trades_df['ReturnPct'] if 'ReturnPct' in self.trades_df.columns else self.trades_df['PnL']

        ax1.hist(returns, bins=50, density=True, alpha=0.7, color='#2E86AB', edgecolor='black')

        # Fit normal distribution
        mu, std = returns.mean(), returns.std()
        x = np.linspace(returns.min(), returns.max(), 100)
        ax1.plot(x, 1/(std * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((x - mu)/std)**2),
                linewidth=2, color='red', label=f'Normal (μ={mu:.2f}, σ={std:.2f})')

        ax1.axvline(x=0, color='black', linestyle='--', linewidth=1)
        ax1.set_title('Returns Distribution', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Return')
        ax1.set_ylabel('Density')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Q-Q plot
        ax2 = axes[1]
        from scipy import stats
        stats.probplot(returns, dist="norm", plot=ax2)
        ax2.set_title('Q-Q Plot (Normal Distribution)', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        Path(save_path).parent.mkdir(exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Returns distribution plot saved to {save_path}")
        plt.close()

    def generate_report(self, save_path='results/performance_report.json', initial_capital=10000):
        """Generate comprehensive performance report."""
        metrics = self.calculate_metrics(initial_capital)

        # Add trade details if available
        if self.trades_df is not None and len(self.trades_df) > 0:
            metrics['trades_summary'] = {
                'first_trade': str(self.trades_df.iloc[0]['EntryTime']) if 'EntryTime' in self.trades_df.columns else 'N/A',
                'last_trade': str(self.trades_df.iloc[-1]['ExitTime']) if 'ExitTime' in self.trades_df.columns else 'N/A',
                'total_volume': self.trades_df['Size'].sum() if 'Size' in self.trades_df.columns else 'N/A',
            }

        Path(save_path).parent.mkdir(exist_ok=True)
        with open(save_path, 'w') as f:
            json.dump(metrics, f, indent=4, default=str)

        print(f"\nPerformance report saved to {save_path}")

        # Print summary to console
        print("\n" + "=" * 70)
        print("PERFORMANCE SUMMARY")
        print("=" * 70)
        print(f"Total Trades:              {metrics['total_trades']}")
        print(f"Win Rate:                  {metrics['win_rate_pct']:.2f}%")
        print(f"Total Return:              {metrics['total_return_pct']:.2f}%")
        print(f"Profit Factor:             {metrics['profit_factor']:.2f}")
        print(f"Sharpe Ratio:              {metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:              {metrics['max_drawdown_pct']:.2f}%")
        print(f"Largest Win:               ${metrics['largest_win']:.2f}")
        print(f"Largest Loss:              ${metrics['largest_loss']:.2f}")
        print(f"Max Consecutive Wins:      {metrics['max_consecutive_wins']}")
        print(f"Max Consecutive Losses:    {metrics['max_consecutive_losses']}")
        print("=" * 70)

        return metrics


def main():
    """Generate performance analysis from backtest results."""
    from pathlib import Path
    import sys

    results_dir = Path('results')

    # Check if backtest results exist
    if not (results_dir / 'backtest_results.csv').exists():
        print("No backtest results found. Run backtest first.")
        sys.exit(1)

    # Load results
    results = pd.read_csv(results_dir / 'backtest_results.csv', index_col=0)

    print("Generating performance analysis...")

    # Note: This would need to be adapted based on actual backtest output format
    # For now, this is a template showing how to use the analyzer

    analyzer = PerformanceAnalyzer()

    print("\nPerformance analysis complete!")
    print("Check the 'results' directory for visualizations.")


if __name__ == '__main__':
    main()
