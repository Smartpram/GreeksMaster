"""
Expanded Ticker & Index Configuration for Paper Trading
Based on ICICIDirect & NSE available instruments

Includes:
- NSE Indices (major benchmarks)
- Sectoral Indices
- Actively traded stocks
- Options expiry underlyings
"""

# ============================================================================
# MARKET INDICES - NSE (Primary Trading Instruments)
# ============================================================================

NSE_INDICES = {
    # Broad Market Indices
    'NIFTY50': {
        'symbol': 'NIFTY',
        'name': 'NIFTY 50',
        'segment': 'index',
        'category': 'broad_market',
        'priority': 1,  # Highest priority
        'description': 'Top 50 companies by market cap'
    },
    'BANKNIFTY': {
        'symbol': 'BANKNIFTY',
        'name': 'BANK NIFTY',
        'segment': 'index',
        'category': 'sectoral',
        'priority': 2,
        'description': 'Banking sector index'
    },
    'FINNIFTY': {
        'symbol': 'FINNIFTY',
        'name': 'NIFTY FINANCIAL',
        'segment': 'index',
        'category': 'sectoral',
        'priority': 2,
        'description': 'Financial services sector'
    },
    
    # Mid & Small Cap
    'NIFTYNXT50': {
        'symbol': 'NIFTYNXT50',
        'name': 'NIFTY NEXT 50',
        'segment': 'index',
        'category': 'broad_market',
        'priority': 3,
        'description': 'Top 50-100 companies'
    },
    'MIDCAPNIFTY': {
        'symbol': 'MIDCAPNIFTY',
        'name': 'NIFTY MIDCAP 50',
        'segment': 'index',
        'category': 'broad_market',
        'priority': 3,
        'description': 'Mid cap companies'
    },
    'NIFTYJR': {
        'symbol': 'NIFTYJR',
        'name': 'NIFTY NEXT 50',
        'segment': 'index',
        'category': 'broad_market',
        'priority': 4,
        'description': 'Junior index (51-100)'
    },
    
    # Sectoral Indices
    'NIFTYAUTO': {
        'symbol': 'NIFTYAUTO',
        'name': 'NIFTY AUTO',
        'segment': 'index',
        'category': 'sectoral',
        'priority': 3,
        'description': 'Automobile sector'
    },
    'NIFTYIT': {
        'symbol': 'NIFTYIT',
        'name': 'NIFTY IT',
        'segment': 'index',
        'category': 'sectoral',
        'priority': 3,
        'description': 'IT/Technology sector'
    },
    'NIFTYPHARMA': {
        'symbol': 'NIFTYPHARMA',
        'name': 'NIFTY PHARMA',
        'segment': 'index',
        'category': 'sectoral',
        'priority': 3,
        'description': 'Pharma sector'
    },
    'NIFTYPSE': {
        'symbol': 'NIFTYPSE',
        'name': 'NIFTY PSU',
        'segment': 'index',
        'category': 'sectoral',
        'priority': 3,
        'description': 'Public Sector Undertakings'
    },
    'NIFTYREALTY': {
        'symbol': 'NIFTYREALTY',
        'name': 'NIFTY REALTY',
        'segment': 'index',
        'category': 'sectoral',
        'priority': 3,
        'description': 'Real Estate sector'
    },
    'NIFTYFMCG': {
        'symbol': 'NIFTYFMCG',
        'name': 'NIFTY FMCG',
        'segment': 'index',
        'category': 'sectoral',
        'priority': 3,
        'description': 'FMCG sector'
    },
    'NIFTYMETAL': {
        'symbol': 'NIFTYMETAL',
        'name': 'NIFTY METALS',
        'segment': 'index',
        'category': 'sectoral',
        'priority': 3,
        'description': 'Metals sector'
    },
    'NIFTYPRIVBANK': {
        'symbol': 'NIFTYPRIVBANK',
        'name': 'NIFTY PRIVATE BANK',
        'segment': 'index',
        'category': 'sectoral',
        'priority': 2,
        'description': 'Private banks index'
    },
    
    # Volatility & Momentum
    'NIFTY200VOLATILITY': {
        'symbol': 'NIFTY200VOLATILITY',
        'name': 'NIFTY 200 VOLATILITY',
        'segment': 'index',
        'category': 'volatility',
        'priority': 4,
        'description': 'High volatility stocks'
    },
}

# ============================================================================
# HIGHLY LIQUID STOCKS - Options Available (Options Expiry Underlyings)
# ============================================================================

LIQUID_STOCKS_ICICIDIRECT = {
    # Large Cap - High Liquidity & Options Available
    'RELIANCE': {
        'symbol': 'RELIANCE',
        'name': 'Reliance Industries',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 1,
        'description': 'Oil & gas, petrochemicals'
    },
    'TCS': {
        'symbol': 'TCS',
        'name': 'Tata Consultancy Services',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 1,
        'description': 'IT services'
    },
    'INFY': {
        'symbol': 'INFY',
        'name': 'Infosys',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 1,
        'description': 'IT services'
    },
    'WIPRO': {
        'symbol': 'WIPRO',
        'name': 'Wipro',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'IT services'
    },
    'HCLTECH': {
        'symbol': 'HCLTECH',
        'name': 'HCL Technologies',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'IT services'
    },
    'TECHM': {
        'symbol': 'TECHM',
        'name': 'Tech Mahindra',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'IT services'
    },
    
    # Banking - High Liquidity & Options
    'HDFC': {
        'symbol': 'HDFC',
        'name': 'HDFC Bank',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 1,
        'description': 'Private bank'
    },
    'ICICIBANK': {
        'symbol': 'ICICIBANK',
        'name': 'ICICI Bank',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 1,
        'description': 'Private bank'
    },
    'SBIN': {
        'symbol': 'SBIN',
        'name': 'State Bank of India',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 1,
        'description': 'State bank'
    },
    'AXISBANK': {
        'symbol': 'AXISBANK',
        'name': 'Axis Bank',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'Private bank'
    },
    'KOTAKBANK': {
        'symbol': 'KOTAKBANK',
        'name': 'Kotak Bank',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'Private bank'
    },
    
    # Automobile - Active Options
    'MARUTI': {
        'symbol': 'MARUTI',
        'name': 'Maruti Suzuki',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'Car manufacturer'
    },
    'TATAMOTORS': {
        'symbol': 'TATAMOTORS',
        'name': 'Tata Motors',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'Car & truck manufacturer'
    },
    'BHARATPETROL': {
        'symbol': 'BHARATPETROL',
        'name': 'Bharat Petroleum',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'Energy/Oil'
    },
    
    # Pharma - Active Trading
    'SUNPHARMA': {
        'symbol': 'SUNPHARMA',
        'name': 'Sun Pharma',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'Pharmaceutical'
    },
    'CIPLA': {
        'symbol': 'CIPLA',
        'name': 'Cipla',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'Pharmaceutical'
    },
    'DRREDDY': {
        'symbol': 'DRREDDY',
        'name': 'Dr Reddy Labs',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'Pharmaceutical'
    },
    
    # FMCG & Consumer
    'HINDUNILVR': {
        'symbol': 'HINDUNILVR',
        'name': 'Hindustan Unilever',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'FMCG'
    },
    'ITC': {
        'symbol': 'ITC',
        'name': 'ITC Limited',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'Tobacco, FMCG'
    },
    
    # Realty & Infrastructure
    'BHARTIARTL': {
        'symbol': 'BHARTIARTL',
        'name': 'Bharti Airtel',
        'segment': 'equity',
        'category': 'large_cap',
        'options': True,
        'priority': 2,
        'description': 'Telecom'
    },
    'JIO': {
        'symbol': 'JIO',
        'name': 'Reliance Jio (via RELIANCE)',
        'segment': 'equity',
        'category': 'large_cap',
        'options': False,
        'priority': 3,
        'description': 'Telecom'
    },
}

# ============================================================================
# PRESET CONFIGURATIONS
# ============================================================================

# High Priority (Best for Paper Trading - Most Liquid)
HIGH_PRIORITY_INDICES = {
    k: v for k, v in NSE_INDICES.items() 
    if v.get('priority', 5) <= 2
}

HIGH_PRIORITY_STOCKS = {
    k: v for k, v in LIQUID_STOCKS_ICICIDIRECT.items() 
    if v.get('priority', 5) <= 2 and v.get('options') is True
}

# Balanced Portfolio (Mix of indices & stocks)
BALANCED_PORTFOLIO = {
    'indices': list(HIGH_PRIORITY_INDICES.keys())[:5],  # Top 5 indices
    'stocks': list(HIGH_PRIORITY_STOCKS.keys())[:10],   # Top 10 stocks
}

# Aggressive Portfolio (Maximum data collection)
AGGRESSIVE_PORTFOLIO = {
    'indices': list(NSE_INDICES.keys())[:15],           # Top 15 indices
    'stocks': list(LIQUID_STOCKS_ICICIDIRECT.keys())[:25],  # Top 25 stocks
}

# Conservative Portfolio (Minimum, high quality)
CONSERVATIVE_PORTFOLIO = {
    'indices': list(HIGH_PRIORITY_INDICES.keys())[:3],  # Top 3 indices
    'stocks': list(HIGH_PRIORITY_STOCKS.keys())[:5],    # Top 5 stocks
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_ticker_config(portfolio='balanced'):
    """Get ticker configuration by portfolio type"""
    portfolios = {
        'balanced': BALANCED_PORTFOLIO,
        'aggressive': AGGRESSIVE_PORTFOLIO,
        'conservative': CONSERVATIVE_PORTFOLIO,
    }
    return portfolios.get(portfolio, BALANCED_PORTFOLIO)

def get_all_indices():
    """Get list of all available indices"""
    return list(NSE_INDICES.keys())

def get_all_stocks():
    """Get list of all available stocks"""
    return list(LIQUID_STOCKS_ICICIDIRECT.keys())

def get_options_available_stocks():
    """Get only stocks with options available (best for derivatives trading)"""
    return [k for k, v in LIQUID_STOCKS_ICICIDIRECT.items() if v.get('options')]

def get_ticker_info(ticker):
    """Get detailed info about a ticker"""
    # Check indices first
    if ticker in NSE_INDICES:
        return NSE_INDICES[ticker]
    # Check stocks
    if ticker in LIQUID_STOCKS_ICICIDIRECT:
        return LIQUID_STOCKS_ICICIDIRECT[ticker]
    return None

def get_tickers_by_category(category):
    """Get tickers by category (e.g., 'broad_market', 'sectoral', 'large_cap')"""
    indices = {k: v for k, v in NSE_INDICES.items() if v.get('category') == category}
    stocks = {k: v for k, v in LIQUID_STOCKS_ICICIDIRECT.items() if v.get('category') == category}
    return {**indices, **stocks}

def get_top_n_tickers(n=10):
    """Get top N tickers by priority (best for paper trading)"""
    all_tickers = {**NSE_INDICES, **LIQUID_STOCKS_ICICIDIRECT}
    sorted_tickers = sorted(all_tickers.items(), key=lambda x: x[1].get('priority', 10))
    return {k: v for k, v in sorted_tickers[:n]}

def get_recommended_paper_trading_set():
    """
    Get recommended set for paper trading
    - Balanced across indices and stocks
    - All high liquidity
    - Diverse sectors
    - Maximum data for ML training
    """
    return {
        'indices': [
            'NIFTY50', 'BANKNIFTY', 'FINNIFTY',  # Core
            'NIFTYNXT50', 'MIDCAPNIFTY',          # Mid-cap
            'NIFTYIT', 'NIFTYPHARMA',             # Sectors
        ],
        'stocks': [
            'RELIANCE', 'TCS', 'INFY',            # Blue chips
            'HDFC', 'ICICIBANK', 'SBIN',          # Banking
            'MARUTI', 'SUNPHARMA', 'HINDUNILVR',  # Diversified
            'BHARTIARTL',                         # Telecom
        ],
    }

# ============================================================================
# EXPANSION TARGETS FOR PAPER TRADING
# ============================================================================

PAPER_TRADING_EXPANSION = {
    'current': {
        'indices': 3,    # NIFTY50, BANKNIFTY, FINNIFTY
        'stocks': 0,     # None
        'total': 3,
    },
    'phase_1': {
        'indices': 8,    # Add NIFTYNXT50, MIDCAPNIFTY + sectoral
        'stocks': 5,     # Add top 5 stocks
        'total': 13,
        'reason': 'Balanced indices + blue-chip stocks',
    },
    'phase_2': {
        'indices': 12,   # Add more sectoral
        'stocks': 15,    # Add more liquid stocks
        'total': 27,
        'reason': 'Comprehensive coverage across sectors',
    },
    'phase_3': {
        'indices': 16,   # Nearly all available
        'stocks': 25,    # Most liquid stocks
        'total': 41,
        'reason': 'Maximum data collection for ML training',
    },
    'production': {
        'indices': 20,   # All indices + micro caps
        'stocks': 50,    # Very comprehensive
        'total': 70,
        'reason': 'Production-ready comprehensive coverage',
    },
}

if __name__ == '__main__':
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║  EXPANDED TICKER & INDEX CONFIGURATION                         ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print()
    print(f"Total Indices Available: {len(NSE_INDICES)}")
    print(f"Total Stocks Available:  {len(LIQUID_STOCKS_ICICIDIRECT)}")
    print(f"Total Instruments:       {len(NSE_INDICES) + len(LIQUID_STOCKS_ICICIDIRECT)}")
    print()
    
    print("📊 PAPER TRADING EXPANSION ROADMAP:")
    print()
    for phase, config in PAPER_TRADING_EXPANSION.items():
        if phase != 'current':
            print(f"  {phase.upper()}: {config['total']} instruments")
            print(f"    - {config['indices']} indices, {config['stocks']} stocks")
            print(f"    - {config['reason']}")
            print()
    
    print("🎯 RECOMMENDED SET FOR PAPER TRADING:")
    recommended = get_recommended_paper_trading_set()
    print(f"  Indices: {len(recommended['indices'])} -> {recommended['indices']}")
    print(f"  Stocks:  {len(recommended['stocks'])} -> {recommended['stocks']}")
    print()
    
    print("✅ Top 10 Tickers by Priority:")
    top = get_top_n_tickers(10)
    for i, (ticker, info) in enumerate(top.items(), 1):
        print(f"  {i}. {ticker}: {info['name']}")
