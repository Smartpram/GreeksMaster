"""
Normalized Signal Engine
========================

Converts stock screener signals into normalized options-ready events.
Pure data science / statistical layer - NO broker dependency.

Output: Normalized JSON signal events ready for options strategy selector.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class SignalType(Enum):
    """Normalized signal types"""
    BREAKOUT = "BREAKOUT"
    MOMENTUM = "MOMENTUM"
    REVERSAL = "REVERSAL"
    CONSOLIDATION = "CONSOLIDATION"


class Direction(Enum):
    """Signal direction"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class Confidence(Enum):
    """Confidence bands"""
    LOW = "LOW"           # 0-40%
    MEDIUM = "MEDIUM"     # 40-70%
    HIGH = "HIGH"         # 70-90%
    VERY_HIGH = "VERY_HIGH"  # 90%+


@dataclass
class NormalizedSignal:
    """Normalized signal event - ready for options strategy selector"""
    
    # Identification
    signal_id: str
    timestamp: str
    symbol: str
    
    # Core signal properties
    signal_type: str  # BREAKOUT, MOMENTUM, REVERSAL, CONSOLIDATION
    direction: str    # BULLISH, BEARISH, NEUTRAL
    confidence: int   # 0-100
    confidence_band: str  # LOW, MEDIUM, HIGH, VERY_HIGH
    
    # Price and market context
    spot_price: float
    spot_date: str
    
    # Technical features
    features: Dict = None  # {sma20_diff_pct, atr, trend_pct_5d, volatility, etc.}
    
    # Expected behavior
    expected_move_pct: float = 0.0  # ATR-based expected move
    holding_period_days: int = 5    # Days to hold
    
    # Risk context
    volatility: float = 0.0         # Annual volatility
    atr: float = 0.0                # Average True Range
    
    # Entry recommendation
    urgency: str = "SWING"          # INTRADAY, SWING, POSITIONAL
    
    # Additional metadata
    metadata: Dict = None
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(asdict(self), indent=2, default=str)


class SignalNormalizer:
    """Converts stock screener output into normalized signals"""
    
    def __init__(self):
        self.signals = []
        self.logger = logger
    
    @staticmethod
    def _get_confidence_band(confidence: int) -> str:
        """Map confidence % to band"""
        if confidence < 40:
            return Confidence.LOW.value
        elif confidence < 70:
            return Confidence.MEDIUM.value
        elif confidence < 90:
            return Confidence.HIGH.value
        else:
            return Confidence.VERY_HIGH.value
    
    @staticmethod
    def _calculate_expected_move(atr: float, spot_price: float) -> float:
        """Calculate expected move % based on ATR"""
        if atr == 0 or spot_price == 0:
            return 0.0
        return (atr / spot_price) * 100
    
    @staticmethod
    def _determine_holding_period(signal_type: str, confidence: int, trend_days: int) -> int:
        """Determine holding period based on signal properties"""
        base_hold = {
            SignalType.BREAKOUT.value: 5,
            SignalType.MOMENTUM.value: 3,
            SignalType.REVERSAL.value: 7,
            SignalType.CONSOLIDATION.value: 10,
        }
        
        hold = base_hold.get(signal_type, 5)
        
        # Adjust for confidence
        if confidence >= 80:
            hold = min(hold + 2, 10)
        elif confidence < 50:
            hold = max(hold - 2, 2)
        
        # Adjust for trend persistence
        hold = min(hold + (trend_days // 5), 15)
        
        return hold
    
    @staticmethod
    def _determine_urgency(signal_type: str, confidence: int, volatility: float) -> str:
        """Determine trade urgency"""
        if signal_type == SignalType.BREAKOUT.value and confidence >= 70:
            return "INTRADAY"  # Exploit breakout quickly
        elif volatility > 0.30 and confidence >= 75:
            return "INTRADAY"  # High vol opportunities are time-sensitive
        else:
            return "SWING"
    
    def normalize_from_stock_analysis(
        self,
        symbol: str,
        signal_type: str,
        direction: str,
        confidence: int,
        spot_price: float,
        sma_20: Optional[float],
        sma_50: Optional[float],
        atr: float,
        volatility: float,
        volume: int,
        avg_volume: float,
        price_change_20d: float,
        signal_date: str = None
    ) -> NormalizedSignal:
        """
        Normalize output from Indian stock backtester into options-ready signal
        
        Args (match backtest_indian_stocks_real_data.py output):
            symbol: Stock symbol
            signal_type: BREAKOUT, MOMENTUM, REVERSAL, CONSOLIDATION
            direction: BULLISH, BEARISH, NEUTRAL
            confidence: 0-100
            spot_price: Current price
            sma_20, sma_50: Moving averages
            atr: Average True Range
            volatility: Annual volatility (decimal)
            volume: Current volume
            avg_volume: Average volume
            price_change_20d: 20-day % change
            signal_date: Date of signal (default: today)
        
        Returns:
            NormalizedSignal ready for options strategy selector
        """
        if signal_date is None:
            signal_date = datetime.now().strftime('%Y-%m-%d')
        
        timestamp = datetime.now().isoformat()
        signal_id = f"{symbol}_{signal_type}_{timestamp.split('T')[0]}"
        
        # Calculate features
        sma20_diff_pct = 0.0
        if sma_20 and spot_price > 0:
            sma20_diff_pct = ((spot_price - sma_20) / sma_20) * 100
        
        sma50_diff_pct = 0.0
        if sma_50 and spot_price > 0:
            sma50_diff_pct = ((spot_price - sma_50) / sma_50) * 100
        
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        
        # Expected move
        expected_move_pct = self._calculate_expected_move(atr, spot_price)
        
        # Holding period
        holding_period = self._determine_holding_period(
            signal_type,
            confidence,
            int(abs(price_change_20d))
        )
        
        # Urgency
        urgency = self._determine_urgency(signal_type, confidence, volatility)
        
        # Build features dict
        features = {
            "sma20_diff_pct": round(sma20_diff_pct, 2),
            "sma50_diff_pct": round(sma50_diff_pct, 2),
            "atr": round(atr, 2),
            "atr_pct": round((atr / spot_price) * 100, 2),
            "trend_pct_20d": round(price_change_20d, 2),
            "volume_ratio": round(volume_ratio, 2),
            "volatility": round(volatility, 4),
        }
        
        # Create signal
        signal = NormalizedSignal(
            signal_id=signal_id,
            timestamp=timestamp,
            symbol=symbol,
            signal_type=signal_type,
            direction=direction,
            confidence=confidence,
            confidence_band=self._get_confidence_band(confidence),
            spot_price=spot_price,
            spot_date=signal_date,
            features=features,
            expected_move_pct=round(expected_move_pct, 2),
            holding_period_days=holding_period,
            volatility=volatility,
            atr=atr,
            urgency=urgency,
            metadata={
                "symbol_canonical": symbol,
                "exchange": "NSE",
                "sector": self._infer_sector(symbol)
            }
        )
        
        self.signals.append(signal)
        
        self.logger.info(
            f"✓ Normalized: {symbol} {signal_type} {direction} "
            f"(Conf: {confidence}%, Move: {expected_move_pct:.1f}%, Hold: {holding_period}d)"
        )
        
        return signal
    
    @staticmethod
    def _infer_sector(symbol: str) -> str:
        """Infer sector from symbol (simple mapping)"""
        sector_map = {
            'INFY': 'IT', 'TCS': 'IT', 'WIPRO': 'IT', 'TECHM': 'IT',
            'HDFC': 'BANKING', 'AXIS': 'BANKING', 'SBIN': 'BANKING', 'ICICI': 'BANKING',
            'MARUTI': 'AUTO', 'TATAMOTORS': 'AUTO', 'HERO': 'AUTO',
            'SUNPHARMA': 'PHARMA', 'CIPLA': 'PHARMA', 'LUPIN': 'PHARMA',
        }
        return sector_map.get(symbol, 'OTHER')
    
    def get_signals_by_confidence_band(self, band: str) -> List[NormalizedSignal]:
        """Get all signals in confidence band"""
        return [s for s in self.signals if s.confidence_band == band]
    
    def get_bullish_signals(self) -> List[NormalizedSignal]:
        """Get all bullish signals"""
        return [s for s in self.signals if s.direction == Direction.BULLISH.value]
    
    def get_bearish_signals(self) -> List[NormalizedSignal]:
        """Get all bearish signals"""
        return [s for s in self.signals if s.direction == Direction.BEARISH.value]
    
    def get_high_confidence_signals(self, min_confidence: int = 70) -> List[NormalizedSignal]:
        """Get signals above confidence threshold"""
        return [s for s in self.signals if s.confidence >= min_confidence]
    
    def export_signals_json(self, filename: str = None) -> str:
        """Export signals to JSON file"""
        if filename is None:
            filename = f"normalized_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        signals_data = {
            'timestamp': datetime.now().isoformat(),
            'signal_count': len(self.signals),
            'signals': [asdict(s) for s in self.signals]
        }
        
        with open(filename, 'w') as f:
            json.dump(signals_data, f, indent=2, default=str)
        
        self.logger.info(f"✓ Exported {len(self.signals)} signals to {filename}")
        return filename
    
    def print_summary(self):
        """Print signal summary"""
        if not self.signals:
            print("No signals generated")
            return
        
        print("\n" + "="*80)
        print("NORMALIZED SIGNALS SUMMARY")
        print("="*80)
        print(f"Total Signals: {len(self.signals)}\n")
        
        # By confidence band
        print("By Confidence Band:")
        for band in [Confidence.VERY_HIGH.value, Confidence.HIGH.value, 
                     Confidence.MEDIUM.value, Confidence.LOW.value]:
            sigs = self.get_signals_by_confidence_band(band)
            if sigs:
                print(f"  {band}: {len(sigs)}")
                for sig in sigs:
                    print(f"    • {sig.symbol} {sig.signal_type} {sig.direction} "
                          f"(Conf: {sig.confidence}%)")
        
        print("\nBy Direction:")
        bullish = self.get_bullish_signals()
        bearish = self.get_bearish_signals()
        print(f"  BULLISH: {len(bullish)}")
        print(f"  BEARISH: {len(bearish)}")
        
        print("\nBy Signal Type:")
        for sig_type in [SignalType.BREAKOUT.value, SignalType.MOMENTUM.value,
                        SignalType.REVERSAL.value, SignalType.CONSOLIDATION.value]:
            sigs = [s for s in self.signals if s.signal_type == sig_type]
            if sigs:
                print(f"  {sig_type}: {len(sigs)}")
        
        print("\n" + "="*80)


def example_usage():
    """Example: Convert AXIS signal from backtest to normalized signal"""
    normalizer = SignalNormalizer()
    
    # Example: AXIS BREAKOUT signal (from backtest_indian_stocks_real_data.py)
    signal = normalizer.normalize_from_stock_analysis(
        symbol="AXIS",
        signal_type="BREAKOUT",
        direction="BULLISH",
        confidence=70,
        spot_price=1292.40,
        sma_20=1269.67,
        sma_50=None,
        atr=24.54,
        volatility=0.20,
        volume=7533477,
        avg_volume=7533477,
        price_change_20d=2.9,
        signal_date="2026-06-09"
    )
    
    # Print as formatted JSON
    print("\n" + "="*80)
    print("EXAMPLE: NORMALIZED SIGNAL (Ready for Options Strategy Selector)")
    print("="*80)
    print(signal.to_json())
    
    # Add another signal
    signal2 = normalizer.normalize_from_stock_analysis(
        symbol="INFY",
        signal_type="MOMENTUM",
        direction="BULLISH",
        confidence=65,
        spot_price=1180.30,
        sma_20=1175.27,
        sma_50=None,
        atr=31.69,
        volatility=0.33,
        volume=10983029,
        avg_volume=10983029,
        price_change_20d=5.1,
        signal_date="2026-06-09"
    )
    
    # Print summary
    normalizer.print_summary()
    
    # Export to JSON
    filepath = normalizer.export_signals_json("backtest_reports/normalized_signals_example.json")
    print(f"\nExported to: {filepath}")


if __name__ == "__main__":
    example_usage()
