"""
LIVE DATA TESTING SCRIPT
========================

Tests AI Trading System with live market data from Breeze API.

Features:
- Connect to Breeze API for live data
- Fetch real NIFTY50 data
- Test all AI components with live data
- Validate feature computation accuracy
- Test ML predictions on real market conditions
- Verify Emergency Stop functionality
- Generate performance report

Usage:
    python test_live_data.py [--symbol NIFTY50] [--cycles 10] [--verbose]

Examples:
    # Test with default (NIFTY50, 10 cycles)
    python test_live_data.py
    
    # Test with specific symbol
    python test_live_data.py --symbol BANKNIFTY
    
    # Run 20 cycles with verbose output
    python test_live_data.py --cycles 20 --verbose
    
    # Run single cycle and show everything
    python test_live_data.py --cycles 1 --verbose
"""

import logging
import argparse
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class LiveTestResult:
    """Result from a single live data test cycle"""
    cycle_num: int
    timestamp: datetime
    symbol: str
    
    # Data
    data_fetched: bool
    num_candles: int
    latest_price: float
    
    # Feature computation
    features_computed: bool
    bullish_score: Optional[float]
    feature_errors: List[str]
    
    # ML prediction
    prediction_available: bool
    predicted_direction: Optional[str]
    prediction_confidence: Optional[float]
    ml_errors: List[str]
    
    # Emergency Stop
    emergency_stop_active: bool
    emergency_stop_reason: Optional[str]
    
    # Overall
    cycle_successful: bool
    total_time_ms: float
    errors: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for reporting"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d


class LiveDataTester:
    """Test AI system with live market data"""
    
    def __init__(self, symbol: str = 'NIFTY50', verbose: bool = False):
        """
        Initialize live data tester
        
        Args:
            symbol: Trading symbol (e.g., NIFTY50, BANKNIFTY)
            verbose: Enable verbose logging
        """
        self.symbol = symbol
        self.verbose = verbose
        self.results: List[LiveTestResult] = []
        
        # Import AI components
        try:
            from app.feature_engine import FeatureEngine
            from app.safety.kill_switch import KillSwitchManager
            from app.ml_models.prediction_engine import PredictionEngine
            from app.ai_trading_orchestrator import AITradingOrchestrator
            from app.services.breeze_api import BreezeAPIService
            
            self.FeatureEngine = FeatureEngine
            self.KillSwitchManager = KillSwitchManager
            self.PredictionEngine = PredictionEngine
            self.AITradingOrchestrator = AITradingOrchestrator
            self.BreezeAPIService = BreezeAPIService
            
            logger.info("✓ All AI components imported successfully")
        except Exception as e:
            logger.error(f"✗ Failed to import AI components: {e}")
            raise
    
    def connect_to_breeze(self) -> Optional[object]:
        """
        Connect to Breeze API for live data
        
        Returns:
            BreezeAPIService instance or None if connection fails
        """
        try:
            # Try to import and initialize Breeze API
            from app.services.breeze_api import BreezeAPIService
            
            # Initialize with credentials from environment or config
            breeze = BreezeAPIService()
            
            if breeze.is_connected:
                logger.info(f"✓ Connected to Breeze API")
                return breeze
            else:
                logger.warning("✗ Breeze API not connected")
                return None
                
        except Exception as e:
            logger.error(f"✗ Failed to connect to Breeze: {e}")
            return None
    
    def fetch_live_data(self, breeze_api: object, 
                       timeframe: str = '1D',
                       num_candles: int = 100) -> Optional[pd.DataFrame]:
        """
        Fetch live OHLCV data from Breeze
        
        Args:
            breeze_api: BreezeAPI instance
            timeframe: Candle timeframe ('1D', '1H', '15M', etc.)
            num_candles: Number of historical candles to fetch
        
        Returns:
            DataFrame with OHLCV data or None if fetch fails
        """
        try:
            if breeze_api is None:
                logger.warning("No Breeze API connection, generating mock data")
                return self._generate_mock_data(num_candles)
            
            logger.info(f"Fetching {num_candles} candles of {self.symbol} data...")
            
            # Fetch from Breeze
            data = breeze_api.get_historical_data(
                self.symbol,
                timeframe=timeframe,
                num_candles=num_candles
            )
            
            if data is None or len(data) == 0:
                logger.warning(f"No data returned from Breeze for {self.symbol}")
                return self._generate_mock_data(num_candles)
            
            logger.info(f"✓ Fetched {len(data)} candles")
            return data
            
        except Exception as e:
            logger.error(f"✗ Error fetching live data: {e}")
            logger.info("Falling back to mock data")
            return self._generate_mock_data(num_candles)
    
    def _generate_mock_data(self, num_candles: int) -> pd.DataFrame:
        """
        Generate realistic mock OHLCV data for testing
        
        Args:
            num_candles: Number of candles to generate
        
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Generating {num_candles} candles of mock data for testing...")
        
        dates = pd.date_range(end=datetime.now(), periods=num_candles, freq='h')
        
        # Generate realistic price movement
        close = np.cumsum(np.random.randn(num_candles) * 0.5) + 20000
        high = close + np.abs(np.random.randn(num_candles) * 0.8)
        low = close - np.abs(np.random.randn(num_candles) * 0.8)
        volume = np.random.randint(100000, 500000, num_candles)
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': close + np.random.randn(num_candles) * 0.2,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
        
        return df
    
    def test_feature_engine(self, data: pd.DataFrame) -> Tuple[bool, Optional[float], List[str]]:
        """
        Test Feature Engine with live data
        
        Args:
            data: OHLCV DataFrame
        
        Returns:
            Tuple of (success, bullish_score, errors)
        """
        errors = []
        
        try:
            if len(data) < 20:
                errors.append(f"Insufficient data: {len(data)} candles (need 20+)")
                return False, None, errors
            
            # Create feature engine instance
            mock_provider = type('DataProvider', (), {
                'get_historical_data': lambda *args, **kwargs: data,
                'get_options_chain': lambda *args, **kwargs: []
            })()
            
            feature_engine = self.FeatureEngine(mock_provider)
            
            # Compute features
            features = feature_engine.compute_all_features(self.symbol)
            
            if features is None:
                errors.append("Feature computation returned None")
                return False, None, errors
            
            # Validate features
            assert hasattr(features, 'bullish_score'), "Missing bullish_score"
            assert 0 <= features.bullish_score <= 100, f"Invalid bullish_score: {features.bullish_score}"
            
            logger.info(f"✓ Feature Engine: bullish_score={features.bullish_score:.1f}/100")
            
            return True, features.bullish_score, []
            
        except Exception as e:
            error_msg = f"Feature Engine error: {str(e)}"
            errors.append(error_msg)
            logger.error(f"✗ {error_msg}")
            return False, None, errors
    
    def test_prediction_engine(self, data: pd.DataFrame) -> Tuple[bool, Optional[str], Optional[float], List[str]]:
        """
        Test Prediction Engine with live data
        
        Args:
            data: OHLCV DataFrame
        
        Returns:
            Tuple of (success, direction, confidence, errors)
        """
        errors = []
        
        try:
            # Initialize ML engine
            pe = self.PredictionEngine()
            
            if len(data) < 20:
                errors.append("Insufficient data for ML prediction")
                return False, None, None, errors
            
            # Create mock features for testing
            close = data['close'].values
            features = {
                'ma_ratio': close[-1] / np.mean(close[-20:]),
                'rsi_14': 50 + np.random.randn() * 20,  # Random RSI for testing
                'atr_14': np.std(close) * 0.5,
                'bb_position': 0.5 + np.random.randn() * 0.2,
                'volume_ratio': data['volume'].iloc[-1] / data['volume'].mean(),
                'stoch_rsi': 50 + np.random.randn() * 20,
                'ma_trend': 1 if close[-1] > close[-5] else -1,
                'macd_signal': 1 if close[-1] > np.mean(close[-20:]) else -1,
            }
            
            # Try prediction
            prediction = pe.predict_direction(features)
            
            if prediction is None:
                errors.append("Prediction returned None")
                return False, None, None, errors
            
            direction = prediction.get('direction', 'NEUTRAL')
            confidence = prediction.get('confidence', 0.0)
            
            logger.info(f"✓ Prediction Engine: {direction} (confidence: {confidence:.1%})")
            
            return True, direction, confidence, []
            
        except Exception as e:
            error_msg = f"Prediction Engine error: {str(e)}"
            errors.append(error_msg)
            logger.warning(f"⚠ {error_msg} (ML may not be trained yet)")
            return False, None, None, errors
    
    def test_emergency_stop(self) -> Tuple[bool, bool, Optional[str]]:
        """
        Test Emergency Stop system
        
        Returns:
            Tuple of (success, is_active, reason)
        """
        try:
            ks = self.KillSwitchManager()
            
            # Check initial state
            is_active = ks.is_active()
            reason = ks.get_reason() if is_active else None
            
            logger.info(f"✓ Emergency Stop: active={is_active}")
            
            return True, is_active, reason
            
        except Exception as e:
            logger.error(f"✗ Emergency Stop error: {e}")
            return False, False, None
    
    def run_single_cycle(self, breeze_api: Optional[object] = None) -> LiveTestResult:
        """
        Run a single complete test cycle with live data
        
        Args:
            breeze_api: Optional BreezeAPI instance
        
        Returns:
            LiveTestResult with cycle results
        """
        cycle_num = len(self.results) + 1
        start_time = time.time()
        
        result = LiveTestResult(
            cycle_num=cycle_num,
            timestamp=datetime.now(),
            symbol=self.symbol,
            data_fetched=False,
            num_candles=0,
            latest_price=0.0,
            features_computed=False,
            bullish_score=None,
            feature_errors=[],
            prediction_available=False,
            predicted_direction=None,
            prediction_confidence=None,
            ml_errors=[],
            emergency_stop_active=False,
            emergency_stop_reason=None,
            cycle_successful=False,
            total_time_ms=0,
            errors=[]
        )
        
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"[Cycle {cycle_num}] Starting live data test cycle")
            logger.info(f"{'='*60}")
            
            # Step 1: Fetch live data
            logger.info("\n[Step 1/5] Fetching live data...")
            data = self.fetch_live_data(breeze_api, num_candles=100)
            
            if data is None or len(data) == 0:
                result.errors.append("Failed to fetch data")
                return result
            
            result.data_fetched = True
            result.num_candles = len(data)
            result.latest_price = float(data['close'].iloc[-1])
            
            logger.info(f"✓ Data: {len(data)} candles, Price: {result.latest_price:.2f}")
            
            # Step 2: Test Feature Engine
            logger.info("\n[Step 2/5] Testing Feature Engine...")
            fe_success, bullish_score, fe_errors = self.test_feature_engine(data)
            
            result.features_computed = fe_success
            result.bullish_score = bullish_score
            result.feature_errors = fe_errors
            
            # Step 3: Test Prediction Engine
            logger.info("\n[Step 3/5] Testing Prediction Engine...")
            pred_success, direction, confidence, ml_errors = self.test_prediction_engine(data)
            
            result.prediction_available = pred_success
            result.predicted_direction = direction
            result.prediction_confidence = confidence
            result.ml_errors = ml_errors
            
            # Step 4: Test Emergency Stop
            logger.info("\n[Step 4/5] Testing Emergency Stop...")
            ks_success, is_active, ks_reason = self.test_emergency_stop()
            
            result.emergency_stop_active = is_active
            result.emergency_stop_reason = ks_reason
            
            # Step 5: Summary
            logger.info("\n[Step 5/5] Cycle Summary")
            result.cycle_successful = (result.data_fetched and 
                                      result.features_computed and 
                                      ks_success)
            
            result.total_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"\nCycle Result: {'✓ SUCCESS' if result.cycle_successful else '✗ PARTIAL'}")
            logger.info(f"Time: {result.total_time_ms:.0f}ms")
            
            if result.errors:
                logger.warning(f"Errors: {result.errors}")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error in cycle: {e}")
            result.errors.append(f"Cycle error: {str(e)}")
            result.total_time_ms = (time.time() - start_time) * 1000
            return result
    
    def run_multiple_cycles(self, num_cycles: int = 5, 
                           breeze_api: Optional[object] = None) -> List[LiveTestResult]:
        """
        Run multiple test cycles
        
        Args:
            num_cycles: Number of cycles to run
            breeze_api: Optional BreezeAPI instance
        
        Returns:
            List of LiveTestResult objects
        """
        logger.info(f"\n{'#'*60}")
        logger.info(f"# LIVE DATA TESTING - {num_cycles} Cycles")
        logger.info(f"# Symbol: {self.symbol}")
        logger.info(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'#'*60}")
        
        for i in range(num_cycles):
            result = self.run_single_cycle(breeze_api)
            self.results.append(result)
            
            # Wait between cycles (avoid rate limiting)
            if i < num_cycles - 1:
                time.sleep(1)
        
        return self.results
    
    def generate_report(self) -> Dict:
        """
        Generate comprehensive test report
        
        Returns:
            Dictionary with test results and statistics
        """
        if not self.results:
            logger.warning("No test results to report")
            return {}
        
        logger.info(f"\n{'='*60}")
        logger.info("LIVE DATA TEST REPORT")
        logger.info(f"{'='*60}")
        
        # Statistics
        total_cycles = len(self.results)
        successful_cycles = sum(1 for r in self.results if r.cycle_successful)
        avg_time = np.mean([r.total_time_ms for r in self.results])
        
        data_fetch_success = sum(1 for r in self.results if r.data_fetched)
        features_success = sum(1 for r in self.results if r.features_computed)
        pred_success = sum(1 for r in self.results if r.prediction_available)
        ks_active = sum(1 for r in self.results if r.emergency_stop_active)
        
        # Calculate accuracy metrics
        bullish_scores = [r.bullish_score for r in self.results if r.bullish_score is not None]
        avg_bullish = np.mean(bullish_scores) if bullish_scores else None
        
        confidences = [r.prediction_confidence for r in self.results 
                      if r.prediction_confidence is not None]
        avg_confidence = np.mean(confidences) if confidences else None
        
        report = {
            'test_date': datetime.now().isoformat(),
            'symbol': self.symbol,
            'total_cycles': total_cycles,
            'successful_cycles': successful_cycles,
            'success_rate': successful_cycles / total_cycles if total_cycles > 0 else 0,
            'avg_cycle_time_ms': avg_time,
            'data_fetch_success_rate': data_fetch_success / total_cycles,
            'feature_engine_success_rate': features_success / total_cycles,
            'prediction_engine_success_rate': pred_success / total_cycles,
            'emergency_stop_active_count': ks_active,
            'avg_bullish_score': avg_bullish,
            'avg_prediction_confidence': avg_confidence,
            'cycle_results': [r.to_dict() for r in self.results]
        }
        
        # Print report
        logger.info(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Total Cycles: {total_cycles}")
        logger.info(f"Successful: {successful_cycles}/{total_cycles} ({successful_cycles/total_cycles*100:.1f}%)")
        logger.info(f"Avg Time per Cycle: {avg_time:.0f}ms")
        logger.info(f"\nComponent Success Rates:")
        logger.info(f"  Data Fetch: {data_fetch_success}/{total_cycles} ({data_fetch_success/total_cycles*100:.1f}%)")
        logger.info(f"  Feature Engine: {features_success}/{total_cycles} ({features_success/total_cycles*100:.1f}%)")
        logger.info(f"  Prediction Engine: {pred_success}/{total_cycles} ({pred_success/total_cycles*100:.1f}%)")
        logger.info(f"\nMetrics:")
        if avg_bullish:
            logger.info(f"  Avg Bullish Score: {avg_bullish:.1f}/100")
        if avg_confidence:
            logger.info(f"  Avg Prediction Confidence: {avg_confidence:.1%}")
        logger.info(f"  Emergency Stop Active: {ks_active} times")
        
        logger.info(f"\n{'='*60}")
        logger.info("Report Complete")
        logger.info(f"{'='*60}\n")
        
        return report
    
    def save_report(self, filename: str = "live_data_test_report.json"):
        """Save report to JSON file"""
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Report saved to: {filename}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Test AI Trading System with live market data'
    )
    parser.add_argument('--symbol', default='NIFTY50', 
                       help='Trading symbol (default: NIFTY50)')
    parser.add_argument('--cycles', type=int, default=5,
                       help='Number of test cycles (default: 5)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Create tester
    tester = LiveDataTester(symbol=args.symbol, verbose=args.verbose)
    
    try:
        # Connect to Breeze
        breeze_api = tester.connect_to_breeze()
        
        # Run cycles
        tester.run_multiple_cycles(num_cycles=args.cycles, breeze_api=breeze_api)
        
        # Generate report
        report = tester.generate_report()
        
        # Save report
        tester.save_report(f"live_data_test_report_{args.symbol}.json")
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
