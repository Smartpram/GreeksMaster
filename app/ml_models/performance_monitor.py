"""
Performance Monitoring Dashboard
Real-time metrics, daily reports, P&L tracking, alerts
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor trading system performance in real-time"""
    
    def __init__(self, symbols=['NIFTY50', 'BANKNIFTY', 'FINNIFTY']):
        self.symbols = symbols
        self.dashboard_dir = Path('data/dashboard')
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance metrics storage
        self.trades = []
        self.daily_pnl = defaultdict(lambda: {'trades': 0, 'pnl': 0, 'wins': 0})
        self.metrics_history = []
        
        # Thresholds for alerts
        self.alerts = {
            'daily_loss_limit': -1000,
            'max_drawdown': -0.15,
            'win_rate_alert': 0.40,
            'sharpe_alert': 0.3
        }
    
    def record_trade(self, symbol, entry_price, exit_price, quantity, direction, timestamp=None):
        """Record a trade execution"""
        if timestamp is None:
            timestamp = datetime.now()
        
        # Calculate P&L
        if direction == 'LONG':
            pnl = (exit_price - entry_price) * quantity
        else:  # SHORT
            pnl = (entry_price - exit_price) * quantity
        
        trade = {
            'timestamp': timestamp,
            'symbol': symbol,
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'pnl': pnl,
            'win': 1 if pnl > 0 else 0
        }
        
        self.trades.append(trade)
        
        # Update daily metrics
        date_key = timestamp.strftime('%Y-%m-%d')
        self.daily_pnl[date_key]['trades'] += 1
        self.daily_pnl[date_key]['pnl'] += pnl
        self.daily_pnl[date_key]['wins'] += trade['win']
        
        return trade
    
    def calculate_metrics(self):
        """Calculate comprehensive performance metrics"""
        if not self.trades:
            return {}
        
        trades_df = pd.DataFrame(self.trades)
        
        # Basic metrics
        total_trades = len(trades_df)
        total_pnl = trades_df['pnl'].sum()
        win_count = trades_df['win'].sum()
        win_rate = win_count / total_trades if total_trades > 0 else 0
        
        # Per-trade metrics
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if (trades_df['pnl'] > 0).any() else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if (trades_df['pnl'] < 0).any() else 0
        max_win = trades_df['pnl'].max()
        max_loss = trades_df['pnl'].min()
        
        # Profit factor
        profit_factor = -avg_win / avg_loss if avg_loss != 0 else 0
        
        # Consecutive metrics
        trades_df['cumsum_wins'] = (trades_df['win'] == 1).cumsum()
        consecutive_wins = trades_df.groupby('cumsum_wins').size().max() if len(trades_df) > 0 else 0
        
        # Drawdown
        cumulative_pnl = trades_df['pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = (cumulative_pnl - running_max).min()
        max_drawdown = drawdown / (running_max.max() if running_max.max() != 0 else 1)
        
        # Returns
        returns = trades_df['pnl'].pct_change().dropna()
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 0 and returns.std() != 0 else 0
        
        # Per-symbol metrics
        symbol_stats = {}
        for symbol in trades_df['symbol'].unique():
            symbol_trades = trades_df[trades_df['symbol'] == symbol]
            symbol_stats[symbol] = {
                'trades': len(symbol_trades),
                'pnl': symbol_trades['pnl'].sum(),
                'win_rate': symbol_trades['win'].sum() / len(symbol_trades) if len(symbol_trades) > 0 else 0
            }
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'total_trades': total_trades,
            'total_pnl': float(total_pnl),
            'win_rate': float(win_rate),
            'avg_win': float(avg_win),
            'avg_loss': float(avg_loss),
            'max_win': float(max_win),
            'max_loss': float(max_loss),
            'profit_factor': float(profit_factor),
            'consecutive_wins': int(consecutive_wins),
            'drawdown': float(drawdown),
            'max_drawdown': float(max_drawdown),
            'sharpe_ratio': float(sharpe),
            'symbol_stats': symbol_stats
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def check_alerts(self, metrics=None):
        """Check for alert conditions"""
        if metrics is None:
            metrics = self.calculate_metrics()
        
        alerts = []
        
        # Daily loss alert
        if metrics.get('drawdown', 0) < self.alerts['daily_loss_limit']:
            alerts.append({
                'level': 'CRITICAL',
                'message': f"Daily loss limit exceeded: {metrics['drawdown']:.0f}"
            })
        
        # Max drawdown alert
        if metrics.get('max_drawdown', 0) < self.alerts['max_drawdown']:
            alerts.append({
                'level': 'WARNING',
                'message': f"Maximum drawdown: {metrics['max_drawdown']:.1%}"
            })
        
        # Win rate alert
        if metrics.get('win_rate', 0) < self.alerts['win_rate_alert']:
            alerts.append({
                'level': 'WARNING',
                'message': f"Low win rate: {metrics['win_rate']:.1%}"
            })
        
        # Sharpe ratio alert
        if metrics.get('sharpe_ratio', 0) < self.alerts['sharpe_alert']:
            alerts.append({
                'level': 'INFO',
                'message': f"Low Sharpe ratio: {metrics['sharpe_ratio']:.2f}"
            })
        
        return alerts
    
    def generate_daily_report(self, date=None):
        """Generate daily performance report"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        elif isinstance(date, datetime):
            date = date.strftime('%Y-%m-%d')
        
        daily_data = self.daily_pnl.get(date, {})
        
        # Get trades for the day
        trades_df = pd.DataFrame(self.trades)
        if not trades_df.empty:
            trades_df['date'] = pd.to_datetime(trades_df['timestamp']).dt.strftime('%Y-%m-%d')
            day_trades = trades_df[trades_df['date'] == date]
        else:
            day_trades = pd.DataFrame()
        
        report = {
            'date': date,
            'trades_executed': daily_data.get('trades', 0),
            'total_pnl': daily_data.get('pnl', 0),
            'wins': daily_data.get('wins', 0),
            'win_rate': daily_data.get('wins', 0) / daily_data.get('trades', 1) if daily_data.get('trades', 0) > 0 else 0,
            'trades': day_trades.to_dict('records') if not day_trades.empty else []
        }
        
        return report
    
    def generate_html_dashboard(self, output_file=None):
        """Generate HTML dashboard"""
        if output_file is None:
            output_file = self.dashboard_dir / f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        metrics = self.calculate_metrics()
        alerts = self.check_alerts(metrics)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Trading System Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
        
        header {{ background: #1e3a5f; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
        h1 {{ font-size: 32px; margin-bottom: 5px; }}
        .timestamp {{ font-size: 14px; opacity: 0.8; }}
        
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card-title {{ font-size: 12px; color: #666; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 1px; }}
        .card-value {{ font-size: 32px; font-weight: bold; color: #1e3a5f; }}
        .card-subtitle {{ font-size: 12px; color: #999; margin-top: 5px; }}
        
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        
        .alerts {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .alerts h2 {{ margin-bottom: 15px; }}
        .alert {{ padding: 12px; margin-bottom: 10px; border-radius: 4px; border-left: 4px solid; }}
        .alert-critical {{ border-color: #dc3545; background: #f8d7da; color: #721c24; }}
        .alert-warning {{ border-color: #ffc107; background: #fff3cd; color: #856404; }}
        .alert-info {{ border-color: #17a2b8; background: #d1ecf1; color: #0c5460; }}
        
        .chart {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ background: #f8f9fa; padding: 12px; text-align: left; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
        td {{ padding: 12px; border-bottom: 1px solid #dee2e6; }}
        tr:hover {{ background: #f8f9fa; }}
        
        footer {{ text-align: center; color: #666; margin-top: 30px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Trading System Dashboard</h1>
            <div class="timestamp">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </header>
        
        <div class="grid">
            <div class="card">
                <div class="card-title">Total P&L</div>
                <div class="card-value {'positive' if metrics.get('total_pnl', 0) >= 0 else 'negative'}">
                    ₹{metrics.get('total_pnl', 0):.0f}
                </div>
                <div class="card-subtitle">Total profit/loss</div>
            </div>
            
            <div class="card">
                <div class="card-title">Win Rate</div>
                <div class="card-value {'positive' if metrics.get('win_rate', 0) >= 0.5 else 'negative'}">
                    {metrics.get('win_rate', 0):.1%}
                </div>
                <div class="card-subtitle">{metrics.get('total_trades', 0)} trades</div>
            </div>
            
            <div class="card">
                <div class="card-title">Max Drawdown</div>
                <div class="card-value negative">{metrics.get('max_drawdown', 0):.1%}</div>
                <div class="card-subtitle">Peak to trough</div>
            </div>
            
            <div class="card">
                <div class="card-title">Sharpe Ratio</div>
                <div class="card-value {'positive' if metrics.get('sharpe_ratio', 0) >= 0.5 else 'negative'}">
                    {metrics.get('sharpe_ratio', 0):.2f}
                </div>
                <div class="card-subtitle">Risk-adjusted returns</div>
            </div>
        </div>
        
        <div class="alerts">
            <h2>Alerts ({len(alerts)})</h2>
            {'' if alerts else '<p style="color: #666;">No active alerts</p>'}
            {''.join(f'<div class="alert alert-{alert["level"].lower()}"><strong>{alert["level"]}</strong>: {alert["message"]}</div>' for alert in alerts)}
        </div>
        
        <div class="chart">
            <h2 style="margin-bottom: 20px;">Recent Trades</h2>
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Symbol</th>
                        <th>Direction</th>
                        <th>Entry</th>
                        <th>Exit</th>
                        <th>P&L</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td>{trade.get("timestamp", "").strftime("%H:%M:%S") if isinstance(trade.get("timestamp"), datetime) else str(trade.get("timestamp", ""))}</td>
                        <td>{trade.get("symbol", "")}</td>
                        <td>{trade.get("direction", "")}</td>
                        <td>₹{trade.get("entry_price", 0):.2f}</td>
                        <td>₹{trade.get("exit_price", 0):.2f}</td>
                        <td class="{'positive' if trade.get('pnl', 0) >= 0 else 'negative'}">₹{trade.get("pnl", 0):.0f}</td>
                        <td>{'✓ Win' if trade.get('win', 0) else '✗ Loss'}</td>
                    </tr>
                    ''' for trade in self.trades[-20:])  # Last 20 trades
                    }
                </tbody>
            </table>
        </div>
        
        <footer>
            <p>Generated by Trading System Dashboard</p>
        </footer>
    </div>
</body>
</html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html)
        
        logger.info(f"[OK] Dashboard generated: {output_file}")
        return str(output_file)
    
    def export_metrics_json(self, output_file=None):
        """Export metrics to JSON"""
        if output_file is None:
            output_file = self.dashboard_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'metrics': self.calculate_metrics(),
            'trades': self.trades,
            'daily_pnl': dict(self.daily_pnl)
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"[OK] Metrics exported: {output_file}")
        return str(output_file)
    
    def generate_weekly_report(self, weeks_back=0):
        """Generate weekly performance report"""
        end_date = datetime.now() - timedelta(weeks=weeks_back)
        start_date = end_date - timedelta(weeks=1)
        
        trades_df = pd.DataFrame(self.trades)
        if not trades_df.empty:
            trades_df['date'] = pd.to_datetime(trades_df['timestamp'])
            week_trades = trades_df[(trades_df['date'] >= start_date) & (trades_df['date'] < end_date)]
        else:
            week_trades = pd.DataFrame()
        
        if week_trades.empty:
            return {'status': 'No trades this week'}
        
        report = {
            'week_start': start_date.strftime('%Y-%m-%d'),
            'week_end': end_date.strftime('%Y-%m-%d'),
            'total_trades': len(week_trades),
            'total_pnl': week_trades['pnl'].sum(),
            'win_rate': week_trades['win'].sum() / len(week_trades) if len(week_trades) > 0 else 0,
            'avg_trade_pnl': week_trades['pnl'].mean(),
            'best_day': week_trades.groupby(week_trades['date'].dt.strftime('%Y-%m-%d'))['pnl'].sum().idxmax(),
            'symbol_performance': week_trades.groupby('symbol')['pnl'].sum().to_dict()
        }
        
        return report


class ReportGenerator:
    """Generate various trading reports"""
    
    def __init__(self, monitor):
        self.monitor = monitor
        self.reports_dir = Path('data/reports')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_pdf_report(self, date=None):
        """Generate PDF report (requires reportlab)"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet
            
            if date is None:
                date = datetime.now()
            
            filename = self.reports_dir / f"report_{date.strftime('%Y%m%d')}.pdf"
            doc = SimpleDocTemplate(str(filename), pagesize=letter)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title = Paragraph(f"Trading Report - {date.strftime('%Y-%m-%d')}", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Metrics
            metrics = self.monitor.calculate_metrics()
            data = [
                ['Metric', 'Value'],
                ['Total Trades', str(metrics.get('total_trades', 0))],
                ['Total P&L', f"₹{metrics.get('total_pnl', 0):.0f}"],
                ['Win Rate', f"{metrics.get('win_rate', 0):.1%}"],
                ['Sharpe Ratio', f"{metrics.get('sharpe_ratio', 0):.2f}"]
            ]
            
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            doc.build(story)
            
            logger.info(f"[OK] PDF report generated: {filename}")
            return str(filename)
        
        except ImportError:
            logger.warning("[WARN] reportlab not installed, skipping PDF generation")
            return None


def main():
    """Test performance monitoring"""
    logger.info("\n[PERFORMANCE MONITOR] Starting...")
    
    monitor = PerformanceMonitor()
    
    # Simulate trades
    logger.info("\n[STEP 1] Recording sample trades...")
    trades_data = [
        ('NIFTY50', 19500, 19550, 1, 'LONG', 500),
        ('BANKNIFTY', 44000, 43950, 1, 'LONG', -500),
        ('FINNIFTY', 21000, 21050, 1, 'LONG', 500),
        ('NIFTY50', 19600, 19550, 1, 'SHORT', -500),
        ('BANKNIFTY', 44100, 44150, 1, 'LONG', 500),
    ]
    
    for symbol, entry, exit_p, qty, direction, pnl_exp in trades_data:
        monitor.record_trade(symbol, entry, exit_p, qty, direction)
    
    logger.info(f"  ✓ Recorded {len(monitor.trades)} trades")
    
    # Calculate metrics
    logger.info("\n[STEP 2] Calculating metrics...")
    metrics = monitor.calculate_metrics()
    logger.info(f"  ✓ Total P&L: ₹{metrics['total_pnl']:.0f}")
    logger.info(f"  ✓ Win Rate: {metrics['win_rate']:.1%}")
    logger.info(f"  ✓ Max Drawdown: {metrics['max_drawdown']:.1%}")
    logger.info(f"  ✓ Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    
    # Check alerts
    logger.info("\n[STEP 3] Checking alerts...")
    alerts = monitor.check_alerts(metrics)
    logger.info(f"  ✓ Active alerts: {len(alerts)}")
    
    # Generate reports
    logger.info("\n[STEP 4] Generating reports...")
    html_file = monitor.generate_html_dashboard()
    json_file = monitor.export_metrics_json()
    
    logger.info(f"\n[OK] Performance monitoring operational")
    logger.info(f"  HTML Dashboard: {html_file}")
    logger.info(f"  JSON Export: {json_file}")


if __name__ == '__main__':
    main()
