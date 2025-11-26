"""
Backtesting Engine for Strategy Testing
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from app.strategies.base_strategy import BaseStrategy
from app.services.data_stream import HistoricalDataService
from app.utils.performance import PerformanceCalculator

logger = logging.getLogger(__name__)

class BacktestingEngine:
    """Engine for backtesting trading strategies"""
    
    def __init__(self):
        self.results = {}
        self.performance_calculator = PerformanceCalculator()
        
    def run_backtest(self, strategy: BaseStrategy, instrument: str, 
                    start_date: str, end_date: str, initial_capital: float = 100000,
                    data_interval: str = "1day") -> Dict:
        """
        Run backtest for a strategy
        
        Args:
            strategy: Strategy instance to test
            instrument: Stock code to test on
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_capital: Starting capital
            data_interval: Data interval for backtesting
            
        Returns:
            Dictionary containing backtest results
        """
        try:
            logger.info(f"Starting backtest for {instrument} from {start_date} to {end_date}")
            
            # Initialize backtest state
            backtest_state = BacktestState(initial_capital)
            
            # Get historical data
            historical_service = HistoricalDataService(strategy.order_manager.breeze_service)
            
            # Calculate days between dates
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            days_back = (end_dt - start_dt).days
            
            historical_data = historical_service.get_historical_data(
                instrument=instrument,
                interval=data_interval,
                days_back=days_back
            )
            
            if not historical_data:
                raise ValueError(f"No historical data available for {instrument}")
            
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(historical_data)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')
            
            # Filter data by date range
            df = df.loc[start_date:end_date]
            
            if df.empty:
                raise ValueError("No data in specified date range")
            
            # Run backtest simulation
            results = self._simulate_trading(strategy, instrument, df, backtest_state)
            
            # Calculate performance metrics
            performance_metrics = self.performance_calculator.calculate_metrics(
                results['trades'],
                results['portfolio_values'],
                initial_capital
            )
            
            # Combine results
            backtest_results = {
                'instrument': instrument,
                'start_date': start_date,
                'end_date': end_date,
                'initial_capital': initial_capital,
                'final_capital': backtest_state.capital,
                'total_return': (backtest_state.capital - initial_capital) / initial_capital * 100,
                'total_trades': len(results['trades']),
                'winning_trades': len([t for t in results['trades'] if t['pnl'] > 0]),
                'losing_trades': len([t for t in results['trades'] if t['pnl'] < 0]),
                'win_rate': len([t for t in results['trades'] if t['pnl'] > 0]) / len(results['trades']) * 100 if results['trades'] else 0,
                'trades': results['trades'],
                'portfolio_values': results['portfolio_values'],
                'performance_metrics': performance_metrics,
                'drawdown_periods': results['drawdown_periods']
            }
            
            logger.info(f"Backtest completed. Total return: {backtest_results['total_return']:.2f}%")
            
            return backtest_results
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {'error': str(e)}
    
    def _simulate_trading(self, strategy: BaseStrategy, instrument: str, 
                         df: pd.DataFrame, state: 'BacktestState') -> Dict:
        """Simulate trading using historical data"""
        trades = []
        portfolio_values = []
        drawdown_periods = []
        current_position = None
        peak_value = state.capital
        
        try:
            for i, (timestamp, row) in enumerate(df.iterrows()):
                current_data = {
                    instrument: {
                        'datetime': timestamp,
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close'],
                        'volume': row['volume']
                    }
                }
                
                # Generate signals
                signals = strategy.generate_signals({instrument: df.iloc[:i+1].to_dict('records')})
                
                # Process signals
                if instrument in signals:
                    signal = signals[instrument]
                    
                    if signal['action'] == 'BUY' and current_position is None:
                        # Enter position
                        entry_price = row['close']
                        quantity = int(state.capital * 0.95 / entry_price)  # Use 95% of capital
                        
                        if quantity > 0:
                            cost = quantity * entry_price
                            state.capital -= cost
                            
                            current_position = {
                                'instrument': instrument,
                                'quantity': quantity,
                                'entry_price': entry_price,
                                'entry_date': timestamp,
                                'stop_loss': signal.get('stop_loss', entry_price * 0.95),
                                'target': signal.get('target', entry_price * 1.15)
                            }
                    
                    elif signal['action'] == 'SELL' and current_position is not None:
                        # Exit position
                        exit_price = row['close']
                        quantity = current_position['quantity']
                        proceeds = quantity * exit_price
                        state.capital += proceeds
                        
                        # Record trade
                        pnl = proceeds - (quantity * current_position['entry_price'])
                        pnl_percent = (exit_price - current_position['entry_price']) / current_position['entry_price'] * 100
                        
                        trade = {
                            'instrument': instrument,
                            'entry_date': current_position['entry_date'],
                            'exit_date': timestamp,
                            'entry_price': current_position['entry_price'],
                            'exit_price': exit_price,
                            'quantity': quantity,
                            'pnl': pnl,
                            'pnl_percent': pnl_percent,
                            'holding_days': (timestamp - current_position['entry_date']).days,
                            'exit_reason': signal.get('reason', 'signal')
                        }
                        trades.append(trade)
                        current_position = None
                
                # Check stop loss and target for current position
                if current_position is not None:
                    if row['low'] <= current_position['stop_loss']:
                        # Stop loss hit
                        exit_price = current_position['stop_loss']
                        quantity = current_position['quantity']
                        proceeds = quantity * exit_price
                        state.capital += proceeds
                        
                        pnl = proceeds - (quantity * current_position['entry_price'])
                        pnl_percent = (exit_price - current_position['entry_price']) / current_position['entry_price'] * 100
                        
                        trade = {
                            'instrument': instrument,
                            'entry_date': current_position['entry_date'],
                            'exit_date': timestamp,
                            'entry_price': current_position['entry_price'],
                            'exit_price': exit_price,
                            'quantity': quantity,
                            'pnl': pnl,
                            'pnl_percent': pnl_percent,
                            'holding_days': (timestamp - current_position['entry_date']).days,
                            'exit_reason': 'stop_loss'
                        }
                        trades.append(trade)
                        current_position = None
                    
                    elif row['high'] >= current_position['target']:
                        # Target hit
                        exit_price = current_position['target']
                        quantity = current_position['quantity']
                        proceeds = quantity * exit_price
                        state.capital += proceeds
                        
                        pnl = proceeds - (quantity * current_position['entry_price'])
                        pnl_percent = (exit_price - current_position['entry_price']) / current_position['entry_price'] * 100
                        
                        trade = {
                            'instrument': instrument,
                            'entry_date': current_position['entry_date'],
                            'exit_date': timestamp,
                            'entry_price': current_position['entry_price'],
                            'exit_price': exit_price,
                            'quantity': quantity,
                            'pnl': pnl,
                            'pnl_percent': pnl_percent,
                            'holding_days': (timestamp - current_position['entry_date']).days,
                            'exit_reason': 'target'
                        }
                        trades.append(trade)
                        current_position = None
                
                # Calculate portfolio value
                portfolio_value = state.capital
                if current_position is not None:
                    position_value = current_position['quantity'] * row['close']
                    portfolio_value += position_value
                
                portfolio_values.append({
                    'date': timestamp,
                    'value': portfolio_value,
                    'cash': state.capital,
                    'position_value': position_value if current_position else 0
                })
                
                # Track drawdown
                if portfolio_value > peak_value:
                    peak_value = portfolio_value
                else:
                    drawdown = (peak_value - portfolio_value) / peak_value * 100
                    if drawdown > 5:  # Record significant drawdowns
                        drawdown_periods.append({
                            'start_date': timestamp,
                            'peak_value': peak_value,
                            'current_value': portfolio_value,
                            'drawdown_percent': drawdown
                        })
            
            return {
                'trades': trades,
                'portfolio_values': portfolio_values,
                'drawdown_periods': drawdown_periods
            }
            
        except Exception as e:
            logger.error(f"Error in trading simulation: {e}")
            return {'trades': [], 'portfolio_values': [], 'drawdown_periods': []}
    
    def compare_strategies(self, strategies: List[BaseStrategy], instrument: str,
                          start_date: str, end_date: str, initial_capital: float = 100000) -> Dict:
        """Compare multiple strategies"""
        try:
            results = {}
            
            for strategy in strategies:
                strategy_name = strategy.__class__.__name__
                result = self.run_backtest(
                    strategy=strategy,
                    instrument=instrument,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=initial_capital
                )
                results[strategy_name] = result
            
            # Create comparison summary
            comparison = {
                'strategies': list(results.keys()),
                'comparison_metrics': {},
                'detailed_results': results
            }
            
            for metric in ['total_return', 'win_rate', 'total_trades', 'max_drawdown']:
                comparison['comparison_metrics'][metric] = {
                    name: result.get('performance_metrics', {}).get(metric, 0) if metric == 'max_drawdown'
                    else result.get(metric, 0)
                    for name, result in results.items()
                }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing strategies: {e}")
            return {'error': str(e)}
    
    def optimize_parameters(self, strategy_class, instrument: str, start_date: str,
                           end_date: str, parameter_ranges: Dict) -> Dict:
        """Optimize strategy parameters"""
        try:
            best_params = None
            best_return = float('-inf')
            optimization_results = []
            
            # Generate parameter combinations
            param_combinations = self._generate_param_combinations(parameter_ranges)
            
            logger.info(f"Testing {len(param_combinations)} parameter combinations")
            
            for i, params in enumerate(param_combinations):
                # Create strategy instance with parameters
                strategy = strategy_class(**params)
                
                # Run backtest
                result = self.run_backtest(
                    strategy=strategy,
                    instrument=instrument,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if 'error' not in result:
                    total_return = result['total_return']
                    optimization_results.append({
                        'parameters': params,
                        'total_return': total_return,
                        'win_rate': result['win_rate'],
                        'total_trades': result['total_trades'],
                        'max_drawdown': result.get('performance_metrics', {}).get('max_drawdown', 0)
                    })
                    
                    if total_return > best_return:
                        best_return = total_return
                        best_params = params
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Completed {i + 1}/{len(param_combinations)} optimizations")
            
            return {
                'best_parameters': best_params,
                'best_return': best_return,
                'all_results': optimization_results,
                'total_combinations_tested': len(param_combinations)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing parameters: {e}")
            return {'error': str(e)}
    
    def _generate_param_combinations(self, parameter_ranges: Dict) -> List[Dict]:
        """Generate all combinations of parameters"""
        import itertools
        
        param_names = list(parameter_ranges.keys())
        param_values = list(parameter_ranges.values())
        
        combinations = []
        for combination in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combination))
            combinations.append(param_dict)
        
        return combinations


class BacktestState:
    """Maintains state during backtesting"""
    
    def __init__(self, initial_capital: float):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.positions = {}
        self.trade_history = []
        
    def get_portfolio_value(self, current_prices: Dict) -> float:
        """Calculate current portfolio value"""
        portfolio_value = self.capital
        
        for instrument, position in self.positions.items():
            if position['quantity'] > 0 and instrument in current_prices:
                position_value = position['quantity'] * current_prices[instrument]
                portfolio_value += position_value
        
        return portfolio_value
    
    def get_returns(self) -> float:
        """Calculate total returns"""
        return (self.capital - self.initial_capital) / self.initial_capital * 100