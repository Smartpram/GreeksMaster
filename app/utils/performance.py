"""
Performance Calculation Utilities
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformanceCalculator:
    """Calculate various performance metrics for trading strategies"""
    
    @staticmethod
    def calculate_metrics(trades: List[Dict], portfolio_values: List[Dict], 
                         initial_capital: float) -> Dict:
        """
        Calculate comprehensive performance metrics
        
        Args:
            trades: List of trade dictionaries
            portfolio_values: List of portfolio value over time
            initial_capital: Starting capital
            
        Returns:
            Dictionary containing performance metrics
        """
        try:
            if not trades or not portfolio_values:
                return {}
            
            # Convert to DataFrames
            trades_df = pd.DataFrame(trades)
            portfolio_df = pd.DataFrame(portfolio_values)
            portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
            portfolio_df = portfolio_df.set_index('date')
            
            # Calculate returns
            portfolio_df['returns'] = portfolio_df['value'].pct_change()
            portfolio_df['cumulative_returns'] = (1 + portfolio_df['returns']).cumprod() - 1
            
            # Basic metrics
            total_return = (portfolio_df['value'].iloc[-1] - initial_capital) / initial_capital * 100
            total_trades = len(trades)
            winning_trades = len(trades_df[trades_df['pnl'] > 0])
            losing_trades = len(trades_df[trades_df['pnl'] < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
            
            # P&L metrics
            total_pnl = trades_df['pnl'].sum()
            avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
            largest_win = trades_df['pnl'].max() if total_trades > 0 else 0
            largest_loss = trades_df['pnl'].min() if total_trades > 0 else 0
            
            # Risk metrics
            max_drawdown = PerformanceCalculator.calculate_max_drawdown(portfolio_df['value'])
            volatility = PerformanceCalculator.calculate_volatility(portfolio_df['returns'])
            sharpe_ratio = PerformanceCalculator.calculate_sharpe_ratio(portfolio_df['returns'])
            sortino_ratio = PerformanceCalculator.calculate_sortino_ratio(portfolio_df['returns'])
            calmar_ratio = total_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # Additional metrics
            profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else float('inf')
            average_trade = total_pnl / total_trades if total_trades > 0 else 0
            
            # Time-based metrics
            if len(portfolio_df) > 1:
                trading_period_days = (portfolio_df.index[-1] - portfolio_df.index[0]).days
                annualized_return = ((portfolio_df['value'].iloc[-1] / initial_capital) ** (365.0 / trading_period_days) - 1) * 100 if trading_period_days > 0 else 0
            else:
                trading_period_days = 1
                annualized_return = 0
            
            return {
                'total_return': round(total_return, 2),
                'annualized_return': round(annualized_return, 2),
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'average_trade': round(average_trade, 2),
                'average_win': round(avg_win, 2),
                'average_loss': round(avg_loss, 2),
                'largest_win': round(largest_win, 2),
                'largest_loss': round(largest_loss, 2),
                'profit_factor': round(profit_factor, 2),
                'max_drawdown': round(max_drawdown, 2),
                'volatility': round(volatility, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'sortino_ratio': round(sortino_ratio, 2),
                'calmar_ratio': round(calmar_ratio, 2),
                'trading_period_days': trading_period_days
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    @staticmethod
    def calculate_max_drawdown(portfolio_values: pd.Series) -> float:
        """Calculate maximum drawdown"""
        try:
            peak = portfolio_values.cummax()
            drawdown = (portfolio_values - peak) / peak * 100
            max_drawdown = drawdown.min()
            return max_drawdown
            
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0
    
    @staticmethod
    def calculate_volatility(returns: pd.Series, annualize: bool = True) -> float:
        """Calculate volatility (standard deviation of returns)"""
        try:
            returns = returns.dropna()
            if len(returns) == 0:
                return 0.0
            
            volatility = returns.std()
            
            if annualize:
                # Annualize assuming daily returns
                volatility *= np.sqrt(252)  # 252 trading days per year
            
            return volatility * 100  # Convert to percentage
            
        except Exception as e:
            logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.05) -> float:
        """Calculate Sharpe ratio"""
        try:
            returns = returns.dropna()
            if len(returns) == 0:
                return 0.0
            
            # Calculate excess returns
            daily_rf_rate = risk_free_rate / 252  # Convert annual rate to daily
            excess_returns = returns - daily_rf_rate
            
            if excess_returns.std() == 0:
                return 0.0
            
            sharpe = excess_returns.mean() / excess_returns.std()
            
            # Annualize
            sharpe *= np.sqrt(252)
            
            return sharpe
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0
    
    @staticmethod
    def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.05) -> float:
        """Calculate Sortino ratio (uses downside deviation instead of total volatility)"""
        try:
            returns = returns.dropna()
            if len(returns) == 0:
                return 0.0
            
            # Calculate excess returns
            daily_rf_rate = risk_free_rate / 252
            excess_returns = returns - daily_rf_rate
            
            # Calculate downside deviation
            negative_returns = excess_returns[excess_returns < 0]
            if len(negative_returns) == 0:
                return float('inf') if excess_returns.mean() > 0 else 0.0
            
            downside_deviation = negative_returns.std()
            
            if downside_deviation == 0:
                return 0.0
            
            sortino = excess_returns.mean() / downside_deviation
            
            # Annualize
            sortino *= np.sqrt(252)
            
            return sortino
            
        except Exception as e:
            logger.error(f"Error calculating Sortino ratio: {e}")
            return 0.0
    
    @staticmethod
    def calculate_var(returns: pd.Series, confidence_level: float = 0.05) -> float:
        """Calculate Value at Risk (VaR)"""
        try:
            returns = returns.dropna()
            if len(returns) == 0:
                return 0.0
            
            var = np.percentile(returns, confidence_level * 100)
            return var * 100  # Convert to percentage
            
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return 0.0
    
    @staticmethod
    def calculate_cvar(returns: pd.Series, confidence_level: float = 0.05) -> float:
        """Calculate Conditional Value at Risk (CVaR)"""
        try:
            returns = returns.dropna()
            if len(returns) == 0:
                return 0.0
            
            var = np.percentile(returns, confidence_level * 100)
            cvar = returns[returns <= var].mean()
            
            return cvar * 100  # Convert to percentage
            
        except Exception as e:
            logger.error(f"Error calculating CVaR: {e}")
            return 0.0
    
    @staticmethod
    def calculate_beta(strategy_returns: pd.Series, market_returns: pd.Series) -> float:
        """Calculate beta (correlation with market)"""
        try:
            if len(strategy_returns) != len(market_returns):
                return 0.0
            
            # Remove NaN values
            combined = pd.DataFrame({'strategy': strategy_returns, 'market': market_returns}).dropna()
            
            if len(combined) < 2:
                return 0.0
            
            covariance = combined['strategy'].cov(combined['market'])
            market_variance = combined['market'].var()
            
            if market_variance == 0:
                return 0.0
            
            beta = covariance / market_variance
            return beta
            
        except Exception as e:
            logger.error(f"Error calculating beta: {e}")
            return 0.0
    
    @staticmethod
    def calculate_alpha(strategy_returns: pd.Series, market_returns: pd.Series, 
                       risk_free_rate: float = 0.05) -> float:
        """Calculate alpha (excess return over expected return based on beta)"""
        try:
            if len(strategy_returns) != len(market_returns):
                return 0.0
            
            beta = PerformanceCalculator.calculate_beta(strategy_returns, market_returns)
            
            # Calculate average returns
            avg_strategy_return = strategy_returns.mean()
            avg_market_return = market_returns.mean()
            daily_rf_rate = risk_free_rate / 252
            
            # Alpha = (Strategy Return - Risk Free Rate) - Beta * (Market Return - Risk Free Rate)
            alpha = (avg_strategy_return - daily_rf_rate) - beta * (avg_market_return - daily_rf_rate)
            
            # Annualize
            alpha *= 252
            
            return alpha * 100  # Convert to percentage
            
        except Exception as e:
            logger.error(f"Error calculating alpha: {e}")
            return 0.0
    
    @staticmethod
    def calculate_information_ratio(strategy_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate Information Ratio"""
        try:
            if len(strategy_returns) != len(benchmark_returns):
                return 0.0
            
            # Calculate active returns
            active_returns = strategy_returns - benchmark_returns
            active_returns = active_returns.dropna()
            
            if len(active_returns) == 0 or active_returns.std() == 0:
                return 0.0
            
            information_ratio = active_returns.mean() / active_returns.std()
            
            # Annualize
            information_ratio *= np.sqrt(252)
            
            return information_ratio
            
        except Exception as e:
            logger.error(f"Error calculating Information Ratio: {e}")
            return 0.0
    
    @staticmethod
    def calculate_trade_statistics(trades: List[Dict]) -> Dict:
        """Calculate detailed trade statistics"""
        try:
            if not trades:
                return {}
            
            trades_df = pd.DataFrame(trades)
            
            # Holding period analysis
            holding_periods = trades_df['holding_days'].tolist()
            avg_holding_period = np.mean(holding_periods)
            median_holding_period = np.median(holding_periods)
            
            # Win/Loss streaks
            win_streak, loss_streak = PerformanceCalculator._calculate_streaks(trades_df['pnl'])
            
            # Monthly performance
            trades_df['exit_date'] = pd.to_datetime(trades_df['exit_date'])
            trades_df['month'] = trades_df['exit_date'].dt.to_period('M')
            monthly_pnl = trades_df.groupby('month')['pnl'].sum()
            
            return {
                'average_holding_period': round(avg_holding_period, 1),
                'median_holding_period': round(median_holding_period, 1),
                'longest_holding_period': max(holding_periods),
                'shortest_holding_period': min(holding_periods),
                'max_consecutive_wins': win_streak,
                'max_consecutive_losses': loss_streak,
                'profitable_months': len(monthly_pnl[monthly_pnl > 0]),
                'total_months': len(monthly_pnl),
                'monthly_win_rate': round(len(monthly_pnl[monthly_pnl > 0]) / len(monthly_pnl) * 100, 2) if len(monthly_pnl) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating trade statistics: {e}")
            return {}
    
    @staticmethod
    def _calculate_streaks(pnl_series: pd.Series) -> Tuple[int, int]:
        """Calculate maximum consecutive wins and losses"""
        try:
            wins = (pnl_series > 0).astype(int)
            losses = (pnl_series < 0).astype(int)
            
            # Calculate consecutive wins
            win_groups = (wins != wins.shift()).cumsum()
            win_streak = wins.groupby(win_groups).sum().max() if len(wins) > 0 else 0
            
            # Calculate consecutive losses
            loss_groups = (losses != losses.shift()).cumsum()
            loss_streak = losses.groupby(loss_groups).sum().max() if len(losses) > 0 else 0
            
            return int(win_streak), int(loss_streak)
            
        except Exception as e:
            logger.error(f"Error calculating streaks: {e}")
            return 0, 0
    
    @staticmethod
    def generate_performance_report(trades: List[Dict], portfolio_values: List[Dict], 
                                  initial_capital: float) -> str:
        """Generate a comprehensive performance report"""
        try:
            metrics = PerformanceCalculator.calculate_metrics(trades, portfolio_values, initial_capital)
            trade_stats = PerformanceCalculator.calculate_trade_statistics(trades)
            
            report = f"""
PERFORMANCE REPORT
==================

RETURN METRICS
--------------
Total Return: {metrics.get('total_return', 0):.2f}%
Annualized Return: {metrics.get('annualized_return', 0):.2f}%
Total P&L: ₹{metrics.get('total_pnl', 0):,.2f}

TRADE STATISTICS
----------------
Total Trades: {metrics.get('total_trades', 0)}
Winning Trades: {metrics.get('winning_trades', 0)}
Losing Trades: {metrics.get('losing_trades', 0)}
Win Rate: {metrics.get('win_rate', 0):.2f}%

Average Trade: ₹{metrics.get('average_trade', 0):,.2f}
Average Win: ₹{metrics.get('average_win', 0):,.2f}
Average Loss: ₹{metrics.get('average_loss', 0):,.2f}
Largest Win: ₹{metrics.get('largest_win', 0):,.2f}
Largest Loss: ₹{metrics.get('largest_loss', 0):,.2f}

RISK METRICS
------------
Maximum Drawdown: {metrics.get('max_drawdown', 0):.2f}%
Volatility: {metrics.get('volatility', 0):.2f}%
Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}
Calmar Ratio: {metrics.get('calmar_ratio', 0):.2f}
Profit Factor: {metrics.get('profit_factor', 0):.2f}

HOLDING PERIOD ANALYSIS
-----------------------
Average Holding Period: {trade_stats.get('average_holding_period', 0):.1f} days
Median Holding Period: {trade_stats.get('median_holding_period', 0):.1f} days
Longest Trade: {trade_stats.get('longest_holding_period', 0)} days
Shortest Trade: {trade_stats.get('shortest_holding_period', 0)} days

STREAK ANALYSIS
---------------
Max Consecutive Wins: {trade_stats.get('max_consecutive_wins', 0)}
Max Consecutive Losses: {trade_stats.get('max_consecutive_losses', 0)}

MONTHLY PERFORMANCE
-------------------
Profitable Months: {trade_stats.get('profitable_months', 0)}/{trade_stats.get('total_months', 0)}
Monthly Win Rate: {trade_stats.get('monthly_win_rate', 0):.2f}%

Trading Period: {metrics.get('trading_period_days', 0)} days
            """
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return "Error generating performance report"