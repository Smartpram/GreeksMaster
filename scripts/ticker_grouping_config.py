"""
Ticker Grouping Configuration for Hybrid ML Models
Defines how tickers are grouped for model training
"""


class TickerGroupingConfig:
    """
    Manages ticker groups for hierarchical ML training
    """
    
    def __init__(self):
        # Tier 2: Group-level tickers
        self.groups = {
            'indices': {
                'tickers': ['NIFTY', 'BANKNIFTY', 'FINNIFTY'],
                'description': 'Index futures and indices',
                'characteristics': ['liquid', 'high_correlation', 'market_sensitive']
            },
            'stocks': {
                'tickers': ['INFY', 'TCS', 'RELIANCE', 'WIPRO', 'LT', 'M&M', 
                           'BAJAJFINSV', 'SBIN', 'ICICIBANK', 'HDFC'],
                'description': 'Individual equity stocks',
                'characteristics': ['varied_liquidity', 'sector_specific', 'company_specific']
            }
        }
        
        # Tier 3: Premium tickers (eligible for per-ticker models)
        self.premium_tickers = {
            'NIFTY': {
                'volume_threshold': 50,  # Min trades/day
                'min_model_ready_days': 3,
                'priority': 1,
                'description': 'Most traded index, primary focus'
            },
            'BANKNIFTY': {
                'volume_threshold': 40,
                'min_model_ready_days': 3,
                'priority': 2,
                'description': 'High-frequency index'
            },
            'INFY': {
                'volume_threshold': 30,
                'min_model_ready_days': 4,
                'priority': 3,
                'description': 'Tech sector flagship'
            },
            'TCS': {
                'volume_threshold': 25,
                'min_model_ready_days': 4,
                'priority': 4,
                'description': 'IT sector stock'
            }
        }
        
        # Tier 1: Global model (all tickers)
        self.global_config = {
            'description': 'Universal model trained on all tickers',
            'data_sources': ['indices', 'stocks'],
            'min_samples_to_retrain': 100,
            'rolling_window_size': 1000,
            'retraining_frequency': 'dynamic',  # Retrain after N samples or daily
            'features': 12,
            'model_ensemble': ['xgboost', 'random_forest', 'gradient_boosting'],
            'weights': {'xgboost': 0.33, 'random_forest': 0.33, 'gradient_boosting': 0.34}
        }
    
    def get_group_for_ticker(self, ticker: str) -> str:
        """Get group name for a ticker"""
        for group_name, group_info in self.groups.items():
            if ticker in group_info['tickers']:
                return group_name
        return 'other'
    
    def get_tickers_for_group(self, group_name: str) -> list:
        """Get list of tickers in a group"""
        return self.groups.get(group_name, {}).get('tickers', [])
    
    def is_premium_ticker(self, ticker: str) -> bool:
        """Check if ticker is eligible for per-ticker model"""
        return ticker in self.premium_tickers
    
    def get_premium_ticker_priority(self, ticker: str) -> int:
        """Get priority for per-ticker model training"""
        return self.premium_tickers.get(ticker, {}).get('priority', 999)
    
    def get_all_tickers(self) -> list:
        """Get all tickers"""
        all_tickers = []
        for group_info in self.groups.values():
            all_tickers.extend(group_info['tickers'])
        return all_tickers
    
    def get_tier_1_config(self) -> dict:
        """Get global model configuration"""
        return self.global_config
    
    def get_tier_2_configs(self) -> dict:
        """Get group model configurations"""
        return {
            group_name: {
                'tickers': group_info['tickers'],
                'description': group_info['description'],
                'characteristics': group_info['characteristics'],
                'min_samples_to_retrain': 100,
                'rolling_window_size': 500,
                'retraining_frequency': 'dynamic'
            }
            for group_name, group_info in self.groups.items()
        }
    
    def get_tier_3_configs(self) -> dict:
        """Get per-ticker model configurations"""
        return self.premium_tickers
    
    def get_ensemble_weights(self) -> dict:
        """Get default ensemble weights for hybrid predictions"""
        return {
            'global': 0.50,  # Global model - backbone (50%)
            'group': 0.30,   # Group model - mid-level (30%)
            'ticker': 0.20   # Per-ticker model - specialist (20%)
        }
    
    def get_model_architecture(self) -> dict:
        """Get complete model architecture specification"""
        return {
            'name': 'Hybrid Multi-Tier ML Ensemble',
            'version': '1.0',
            'tier_1': {
                'name': 'Global Model',
                'purpose': 'Market-wide patterns and regime detection',
                'training_data': 'All tickers combined',
                'sample_count': '1,700+ per day',
                'retrain_threshold': 100,
                'ensemble': self.global_config['model_ensemble'],
                'weight': 0.50
            },
            'tier_2': {
                'name': 'Group Models',
                'purpose': 'Asset-class specific patterns',
                'groups': list(self.groups.keys()),
                'retrain_threshold': 100,
                'ensemble': self.global_config['model_ensemble'],
                'weight': 0.30
            },
            'tier_3': {
                'name': 'Per-Ticker Models',
                'purpose': 'Instrument-specific specialization',
                'tickers': list(self.premium_tickers.keys()),
                'min_daily_volume': [
                    self.premium_tickers[t].get('volume_threshold')
                    for t in self.premium_tickers.keys()
                ],
                'retrain_threshold': 100,
                'ensemble': self.global_config['model_ensemble'],
                'weight': 0.20
            },
            'final_prediction': {
                'method': 'Weighted average of tier outputs',
                'formula': '(0.50×Global + 0.30×Group + 0.20×Ticker)',
                'confidence_threshold': 0.55,
                'hybrid_score': '(Technical×0.5 + ML×0.5)'
            }
        }
    
    def print_architecture(self):
        """Print model architecture to console"""
        arch = self.get_model_architecture()
        
        print("\n" + "="*80)
        print("HYBRID MULTI-TIER ML ARCHITECTURE")
        print("="*80)
        
        print(f"\nName: {arch['name']}")
        print(f"Version: {arch['version']}")
        
        print("\n" + "-"*80)
        print("TIER 1: GLOBAL MODEL (50% Weight)")
        print("-"*80)
        print(f"Purpose: {arch['tier_1']['purpose']}")
        print(f"Training Data: {arch['tier_1']['training_data']}")
        print(f"Daily Samples: {arch['tier_1']['sample_count']}")
        print(f"Retrain Threshold: {arch['tier_1']['retrain_threshold']} samples")
        print(f"Ensemble: {', '.join(arch['tier_1']['ensemble'])}")
        
        print("\n" + "-"*80)
        print("TIER 2: GROUP MODELS (30% Weight)")
        print("-"*80)
        for group_name in arch['tier_2']['groups']:
            tickers = self.get_tickers_for_group(group_name)
            print(f"\n  {group_name.upper()}: {', '.join(tickers)}")
        print(f"\nPurpose: {arch['tier_2']['purpose']}")
        print(f"Retrain Threshold: {arch['tier_2']['retrain_threshold']} samples/group")
        print(f"Ensemble: {', '.join(arch['tier_2']['ensemble'])}")
        
        print("\n" + "-"*80)
        print("TIER 3: PER-TICKER MODELS (20% Weight)")
        print("-"*80)
        print(f"Purpose: {arch['tier_3']['purpose']}")
        for i, ticker in enumerate(arch['tier_3']['tickers']):
            volume = arch['tier_3']['min_daily_volume'][i]
            print(f"  {ticker}: Min {volume} trades/day to activate")
        print(f"Retrain Threshold: {arch['tier_3']['retrain_threshold']} samples/ticker")
        print(f"Ensemble: {', '.join(arch['tier_3']['ensemble'])}")
        
        print("\n" + "-"*80)
        print("FINAL PREDICTION")
        print("-"*80)
        print(f"Method: {arch['final_prediction']['method']}")
        print(f"Formula: {arch['final_prediction']['formula']}")
        print(f"Hybrid Score: {arch['final_prediction']['hybrid_score']}")
        print(f"Confidence Threshold: {arch['final_prediction']['confidence_threshold']}")
        
        print("\n" + "="*80)


# Singleton instance
_config = None

def get_ticker_grouping_config() -> TickerGroupingConfig:
    """Get singleton instance of ticker grouping config"""
    global _config
    if _config is None:
        _config = TickerGroupingConfig()
    return _config


if __name__ == "__main__":
    config = TickerGroupingConfig()
    config.print_architecture()
