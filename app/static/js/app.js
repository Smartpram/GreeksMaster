/**
 * MyBreezeApp JavaScript Module
 * Main application logic for the trading dashboard
 */

class MyBreezeApp {
    constructor() {
        this.isConnected = false;
        this.lastUpdate = null;
        this.chartInstances = {};
        this.refreshInterval = null;
        
        // API endpoints
        this.endpoints = {
            portfolio: '/api/portfolio',
            orders: '/api/orders',
            performance: '/api/performance',
            stream: {
                start: '/api/stream/start',
                stop: '/api/stream/stop'
            },
            strategy: {
                toggle: '/api/strategy/toggle'
            },
            backtest: '/api/backtest'
        };
        
        this.init();
    }
    
    init() {
        console.log('Initializing MyBreezeApp...');
        this.setupEventListeners();
        this.initializeCharts();
        this.startAutoRefresh();
    }
    
    setupEventListeners() {
        // Strategy control buttons
        document.getElementById('startStrategy')?.addEventListener('click', () => {
            this.toggleStrategy('start');
        });
        
        document.getElementById('stopStrategy')?.addEventListener('click', () => {
            this.toggleStrategy('stop');
        });
        
        document.getElementById('pauseStrategy')?.addEventListener('click', () => {
            this.toggleStrategy('pause');
        });
        
        // Refresh buttons
        document.addEventListener('click', (e) => {
            if (e.target.closest('[onclick*="refresh"]')) {
                const action = e.target.getAttribute('onclick');
                if (action.includes('refreshPositions')) {
                    this.refreshPositions();
                } else if (action.includes('refreshTrades')) {
                    this.refreshTrades();
                }
            }
        });
    }
    
    async toggleStrategy(action) {
        try {
            this.showLoading('Updating strategy...');
            
            const response = await fetch(this.endpoints.strategy.toggle, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action: action })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.updateStrategyStatus(action);
                this.showNotification(`Strategy ${action}ed successfully`, 'success');
            } else {
                this.showNotification(result.error || 'Failed to update strategy', 'error');
            }
        } catch (error) {
            console.error('Error toggling strategy:', error);
            this.showNotification('Network error occurred', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    updateStrategyStatus(status) {
        const statusElement = document.getElementById('strategyStatus');
        if (statusElement) {
            statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            statusElement.className = 'badge';
            
            switch (status) {
                case 'start':
                case 'running':
                    statusElement.classList.add('bg-success');
                    break;
                case 'stop':
                case 'stopped':
                    statusElement.classList.add('bg-danger');
                    break;
                case 'pause':
                case 'paused':
                    statusElement.classList.add('bg-warning');
                    break;
                default:
                    statusElement.classList.add('bg-secondary');
            }
        }
    }
    
    async updateDashboard() {
        try {
            // Update portfolio metrics
            await this.updatePortfolioMetrics();
            
            // Update positions
            await this.updatePositions();
            
            // Update recent trades
            await this.updateRecentTrades();
            
            // Update performance metrics
            await this.updatePerformanceMetrics();
            
            // Update charts
            await this.updateCharts();
            
            this.lastUpdate = new Date();
            
        } catch (error) {
            console.error('Error updating dashboard:', error);
        }
    }
    
    async updatePortfolioMetrics() {
        try {
            const response = await fetch(this.endpoints.portfolio);
            if (!response.ok) return;
            
            const data = await response.json();
            
            // Update metric cards
            this.updateElement('totalPnL', this.formatCurrency(data.total_pnl || 0));
            this.updateElement('todayPnL', this.formatCurrency(data.today_pnl || 0));
            this.updateElement('activePositions', data.active_positions || 0);
            this.updateElement('portfolioValue', this.formatCurrency(data.portfolio_value || 0));
            
            // Update P&L colors
            this.updatePnLColors('totalPnL', data.total_pnl || 0);
            this.updatePnLColors('todayPnL', data.today_pnl || 0);
            
        } catch (error) {
            console.error('Error updating portfolio metrics:', error);
        }
    }
    
    async updatePositions() {
        try {
            const response = await fetch(this.endpoints.portfolio);
            if (!response.ok) return;
            
            const data = await response.json();
            const positions = data.positions || [];
            
            const tableBody = document.getElementById('positionsTable');
            if (!tableBody) return;
            
            if (positions.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No active positions</td></tr>';
                return;
            }
            
            tableBody.innerHTML = positions.map(position => `
                <tr>
                    <td><strong>${position.symbol}</strong></td>
                    <td>${position.quantity}</td>
                    <td>₹${position.current_price?.toFixed(2) || '0.00'}</td>
                    <td class="${position.pnl >= 0 ? 'profit' : 'loss'}">
                        ₹${position.pnl?.toFixed(2) || '0.00'}
                    </td>
                </tr>
            `).join('');
            
        } catch (error) {
            console.error('Error updating positions:', error);
        }
    }
    
    async updateRecentTrades() {
        try {
            const response = await fetch(this.endpoints.orders);
            if (!response.ok) return;
            
            const trades = await response.json();
            
            const tableBody = document.getElementById('tradesTable');
            if (!tableBody) return;
            
            if (!trades || trades.length === 0) {
                tableBody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No recent trades</td></tr>';
                return;
            }
            
            // Show only last 5 trades
            const recentTrades = trades.slice(-5);
            
            tableBody.innerHTML = recentTrades.map(trade => `
                <tr>
                    <td><small>${this.formatTime(trade.timestamp)}</small></td>
                    <td><strong>${trade.symbol}</strong></td>
                    <td>
                        <span class="badge ${trade.action === 'BUY' ? 'bg-success' : 'bg-danger'}">
                            ${trade.action}
                        </span>
                    </td>
                    <td class="${(trade.pnl || 0) >= 0 ? 'profit' : 'loss'}">
                        ₹${(trade.pnl || 0).toFixed(2)}
                    </td>
                </tr>
            `).join('');
            
        } catch (error) {
            console.error('Error updating recent trades:', error);
        }
    }
    
    async updatePerformanceMetrics() {
        try {
            const response = await fetch(this.endpoints.performance);
            if (!response.ok) return;
            
            const metrics = await response.json();
            
            this.updateElement('winRate', `${metrics.win_rate?.toFixed(1) || 0}%`);
            this.updateElement('sharpeRatio', metrics.sharpe_ratio?.toFixed(2) || '0.00');
            this.updateElement('maxDrawdown', `${Math.abs(metrics.max_drawdown || 0).toFixed(1)}%`);
            this.updateElement('totalTrades', metrics.total_trades || 0);
            
        } catch (error) {
            console.error('Error updating performance metrics:', error);
        }
    }
    
    async updateCharts() {
        try {
            const response = await fetch(this.endpoints.performance);
            if (!response.ok) return;
            
            const data = await response.json();
            
            if (data.portfolio_history) {
                this.updatePortfolioChart(data.portfolio_history);
            }
            
        } catch (error) {
            console.error('Error updating charts:', error);
        }
    }
    
    initializeCharts() {
        // Initialize empty portfolio chart
        const portfolioChartDiv = document.getElementById('portfolioChart');
        if (portfolioChartDiv) {
            const layout = {
                title: '',
                xaxis: { title: 'Date' },
                yaxis: { title: 'Portfolio Value (₹)' },
                margin: { l: 50, r: 20, t: 20, b: 40 },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)'
            };
            
            const config = {
                responsive: true,
                displayModeBar: false
            };
            
            Plotly.newPlot(portfolioChartDiv, [], layout, config);
            this.chartInstances.portfolio = portfolioChartDiv;
        }
    }
    
    updatePortfolioChart(data) {
        if (!this.chartInstances.portfolio || !data || data.length === 0) return;
        
        const dates = data.map(item => item.date);
        const values = data.map(item => item.value);
        
        const trace = {
            x: dates,
            y: values,
            type: 'scatter',
            mode: 'lines',
            name: 'Portfolio Value',
            line: {
                color: '#667eea',
                width: 2
            },
            fill: 'tonexty',
            fillcolor: 'rgba(102, 126, 234, 0.1)'
        };
        
        Plotly.redraw(this.chartInstances.portfolio, [trace]);
    }
    
    // Utility functions
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }
    
    updatePnLColors(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            const card = element.closest('.card');
            if (card) {
                // Remove existing color classes
                card.classList.remove('bg-success', 'bg-danger', 'bg-primary');
                
                // Add appropriate color class
                if (value > 0) {
                    card.classList.add('bg-success');
                } else if (value < 0) {
                    card.classList.add('bg-danger');
                } else {
                    card.classList.add('bg-primary');
                }
            }
        }
    }
    
    formatCurrency(amount) {
        if (Math.abs(amount) >= 10000000) {
            return `₹${(amount / 10000000).toFixed(2)}Cr`;
        } else if (Math.abs(amount) >= 100000) {
            return `₹${(amount / 100000).toFixed(2)}L`;
        } else if (Math.abs(amount) >= 1000) {
            return `₹${(amount / 1000).toFixed(2)}K`;
        } else {
            return `₹${amount.toFixed(2)}`;
        }
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-IN', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    showLoading(message = 'Loading...') {
        // Implementation for loading indicator
        console.log('Loading:', message);
    }
    
    hideLoading() {
        // Implementation for hiding loading indicator
        console.log('Loading complete');
    }
    
    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.updateDashboard();
        }, 5000); // Update every 5 seconds
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    // Public methods for manual refresh
    async refreshPositions() {
        await this.updatePositions();
        this.showNotification('Positions updated', 'success');
    }
    
    async refreshTrades() {
        await this.updateRecentTrades();
        this.showNotification('Trades updated', 'success');
    }
}

// Global functions for backward compatibility
let app;

function initializeDashboard() {
    app = new MyBreezeApp();
}

function updateDashboard() {
    if (app) {
        app.updateDashboard();
    }
}

function refreshPositions() {
    if (app) {
        app.refreshPositions();
    }
}

function refreshTrades() {
    if (app) {
        app.refreshTrades();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (typeof initializeDashboard === 'function') {
        initializeDashboard();
    }
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MyBreezeApp;
}