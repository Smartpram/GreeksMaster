"""
Live Data Test Script for Options Screeners
============================================

Tests all 6 screeners with REAL data from Breeze API
"""

import logging
import sys
from datetime import datetime
from typing import Dict, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from app.services.breeze_api import BreezeAPIService
from app.options_screener import OptionsScreener
from app.config import Config


class LiveDataTester:
    """Test screeners with live Breeze API data"""
    
    def __init__(self):
        """Initialize live data tester"""
        self.config = Config()
        self.api = None
        self.screener = None
        self.connection_status = False
        self.test_results = {}
    
    def setup_api_connection(self) -> bool:
        """Setup and verify API connection"""
        print("\n" + "="*100)
        print("STEP 1: TESTING API CONNECTION")
        print("="*100)
        
        try:
            logger.info("Initializing Breeze API...")
            self.api = BreezeAPIService()
            
            logger.info("Attempting to authenticate...")
            auth_result = self.api.authenticate()
            
            if auth_result.get('success'):
                print(f"\n✅ API CONNECTION SUCCESSFUL")
                print(f"   User: {auth_result.get('user_name')}")
                print(f"   User ID: {auth_result.get('user_id')}")
                print(f"   Session Token: {auth_result.get('session_token')[:20]}...")
                print(f"   Segments Allowed: {auth_result.get('segments')}")
                
                self.connection_status = True
                return True
            else:
                print(f"\n❌ API AUTHENTICATION FAILED")
                print(f"   Error: {auth_result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"\n❌ API CONNECTION ERROR")
            print(f"   Exception: {str(e)}")
            logger.error(f"API connection failed: {e}")
            return False
    
    def test_iv_screener(self) -> Dict:
        """Test IV Screener with live data"""
        print("\n" + "="*100)
        print("STEP 2: TESTING IV SCREENER (High Implied Volatility)")
        print("="*100)
        
        if not self.connection_status:
            print("\n⚠️  SKIPPING: API not connected")
            return {'success': False, 'reason': 'API not connected'}
        
        try:
            print("\nScanning for high IV opportunities (IV percentile > 75%)...")
            
            # Create screener
            screener = OptionsScreener(api_service=self.api)
            
            # Run screener
            results = screener.screen_high_iv(iv_percentile_min=75, limit=20)
            
            if results:
                print(f"\n✅ IV SCREENER SUCCESSFUL - Found {len(results)} opportunities")
                print("\nTop 5 Results:")
                screener.print_iv_screener_results(results, top_n=5)
                
                self.test_results['iv_screener'] = {
                    'success': True,
                    'count': len(results),
                    'top_symbols': [r.symbol for r in results[:5]]
                }
                return {'success': True, 'count': len(results)}
            else:
                print(f"\n⚠️  IV SCREENER: No opportunities found")
                print("   This may indicate: No high IV stocks currently, or data retrieval issue")
                
                self.test_results['iv_screener'] = {
                    'success': True,
                    'count': 0,
                    'note': 'No high IV opportunities'
                }
                return {'success': True, 'count': 0}
        
        except Exception as e:
            print(f"\n❌ IV SCREENER ERROR: {str(e)}")
            logger.error(f"IV Screener error: {e}", exc_info=True)
            
            self.test_results['iv_screener'] = {
                'success': False,
                'error': str(e)
            }
            return {'success': False, 'error': str(e)}
    
    def test_earnings_screener(self) -> Dict:
        """Test Earnings Screener with live data"""
        print("\n" + "="*100)
        print("STEP 3: TESTING EARNINGS SCREENER (Upcoming Earnings)")
        print("="*100)
        
        if not self.connection_status:
            print("\n⚠️  SKIPPING: API not connected")
            return {'success': False, 'reason': 'API not connected'}
        
        try:
            print("\nScanning for earnings plays (within 14 days)...")
            
            screener = OptionsScreener(api_service=self.api)
            results = screener.screen_earnings_plays(days_to_earnings=14, limit=20)
            
            if results:
                print(f"\n✅ EARNINGS SCREENER SUCCESSFUL - Found {len(results)} opportunities")
                print("\nTop 5 Results:")
                screener.print_earnings_screener_results(results, top_n=5)
                
                self.test_results['earnings_screener'] = {
                    'success': True,
                    'count': len(results),
                    'top_symbols': [r.symbol for r in results[:5]]
                }
                return {'success': True, 'count': len(results)}
            else:
                print(f"\n⚠️  EARNINGS SCREENER: No opportunities found")
                print("   This may indicate: No upcoming earnings, or earnings data unavailable")
                
                self.test_results['earnings_screener'] = {
                    'success': True,
                    'count': 0,
                    'note': 'No upcoming earnings'
                }
                return {'success': True, 'count': 0}
        
        except Exception as e:
            print(f"\n❌ EARNINGS SCREENER ERROR: {str(e)}")
            logger.error(f"Earnings Screener error: {e}", exc_info=True)
            
            self.test_results['earnings_screener'] = {
                'success': False,
                'error': str(e)
            }
            return {'success': False, 'error': str(e)}
    
    def test_theta_screener(self) -> Dict:
        """Test Theta Decay Screener with live data"""
        print("\n" + "="*100)
        print("STEP 4: TESTING THETA DECAY SCREENER (3-8 Days to Expiry)")
        print("="*100)
        
        if not self.connection_status:
            print("\n⚠️  SKIPPING: API not connected")
            return {'success': False, 'reason': 'API not connected'}
        
        try:
            print("\nScanning for theta decay opportunities (3-8 DTE)...")
            
            screener = OptionsScreener(api_service=self.api)
            results = screener.screen_theta_decay(dte_range=(3, 8), theta_min=-0.5, limit=50)
            
            if results:
                print(f"\n✅ THETA SCREENER SUCCESSFUL - Found {len(results)} opportunities")
                print("\nTop 10 Results:")
                screener.print_theta_screener_results(results, top_n=10)
                
                self.test_results['theta_screener'] = {
                    'success': True,
                    'count': len(results),
                    'top_symbols': [r.symbol for r in results[:10]]
                }
                return {'success': True, 'count': len(results)}
            else:
                print(f"\n⚠️  THETA SCREENER: No opportunities found")
                print("   This may indicate: No options with 3-8 DTE, or API data issue")
                
                self.test_results['theta_screener'] = {
                    'success': True,
                    'count': 0,
                    'note': 'No theta decay opportunities'
                }
                return {'success': True, 'count': 0}
        
        except Exception as e:
            print(f"\n❌ THETA SCREENER ERROR: {str(e)}")
            logger.error(f"Theta Screener error: {e}", exc_info=True)
            
            self.test_results['theta_screener'] = {
                'success': False,
                'error': str(e)
            }
            return {'success': False, 'error': str(e)}
    
    def test_combo_screener(self) -> Dict:
        """Test Combo (Greeks + Technical) Screener with live data"""
        print("\n" + "="*100)
        print("STEP 5: TESTING COMBO SCREENER (Greeks + Technical)")
        print("="*100)
        
        if not self.connection_status:
            print("\n⚠️  SKIPPING: API not connected")
            return {'success': False, 'reason': 'API not connected'}
        
        try:
            print("\nScanning for high-probability combo setups...")
            
            screener = OptionsScreener(api_service=self.api)
            results = screener.screen_greeks_technical_combo(technical_score_min=60, limit=20)
            
            if results:
                print(f"\n✅ COMBO SCREENER SUCCESSFUL - Found {len(results)} opportunities")
                print("\nTop 5 Results:")
                screener.print_combo_screener_results(results, top_n=5)
                
                self.test_results['combo_screener'] = {
                    'success': True,
                    'count': len(results),
                    'top_symbols': [r.symbol for r in results[:5]]
                }
                return {'success': True, 'count': len(results)}
            else:
                print(f"\n⚠️  COMBO SCREENER: No opportunities found")
                print("   This may indicate: No high-probability setups, or technical data unavailable")
                
                self.test_results['combo_screener'] = {
                    'success': True,
                    'count': 0,
                    'note': 'No combo opportunities'
                }
                return {'success': True, 'count': 0}
        
        except Exception as e:
            print(f"\n❌ COMBO SCREENER ERROR: {str(e)}")
            logger.error(f"Combo Screener error: {e}", exc_info=True)
            
            self.test_results['combo_screener'] = {
                'success': False,
                'error': str(e)
            }
            return {'success': False, 'error': str(e)}
    
    def test_hedging_screener(self) -> Dict:
        """Test Hedging Pairs Screener with live data"""
        print("\n" + "="*100)
        print("STEP 6: TESTING HEDGING SCREENER (Correlated Pairs)")
        print("="*100)
        
        if not self.connection_status:
            print("\n⚠️  SKIPPING: API not connected")
            return {'success': False, 'reason': 'API not connected'}
        
        try:
            print("\nScanning for hedging pair opportunities (correlation > 0.70)...")
            
            screener = OptionsScreener(api_service=self.api)
            results = screener.screen_hedging_pairs(correlation_min=0.70, limit=10)
            
            if results:
                print(f"\n✅ HEDGING SCREENER SUCCESSFUL - Found {len(results)} opportunities")
                print("\nTop 5 Results:")
                screener.print_hedging_pairs_results(results, top_n=5)
                
                self.test_results['hedging_screener'] = {
                    'success': True,
                    'count': len(results),
                    'top_pairs': [f"{r.symbol_long}-{r.symbol_short}" for r in results[:5]]
                }
                return {'success': True, 'count': len(results)}
            else:
                print(f"\n⚠️  HEDGING SCREENER: No opportunities found")
                print("   This may indicate: No highly correlated pairs, or correlation data unavailable")
                
                self.test_results['hedging_screener'] = {
                    'success': True,
                    'count': 0,
                    'note': 'No hedging pairs'
                }
                return {'success': True, 'count': 0}
        
        except Exception as e:
            print(f"\n❌ HEDGING SCREENER ERROR: {str(e)}")
            logger.error(f"Hedging Screener error: {e}", exc_info=True)
            
            self.test_results['hedging_screener'] = {
                'success': False,
                'error': str(e)
            }
            return {'success': False, 'error': str(e)}
    
    def test_delta_neutral_screener(self) -> Dict:
        """Test Delta Neutral Screener with live data"""
        print("\n" + "="*100)
        print("STEP 7: TESTING DELTA NEUTRAL SCREENER (Butterfly Spreads)")
        print("="*100)
        
        if not self.connection_status:
            print("\n⚠️  SKIPPING: API not connected")
            return {'success': False, 'reason': 'API not connected'}
        
        try:
            print("\nScanning for delta-neutral setup opportunities...")
            
            screener = OptionsScreener(api_service=self.api)
            results = screener.screen_delta_neutral_setups(delta_tolerance=0.05, limit=15)
            
            if results:
                print(f"\n✅ DELTA NEUTRAL SCREENER SUCCESSFUL - Found {len(results)} opportunities")
                print("\nTop 5 Results:")
                screener.print_delta_neutral_results(results, top_n=5)
                
                self.test_results['delta_neutral_screener'] = {
                    'success': True,
                    'count': len(results),
                    'top_symbols': [r.symbol for r in results[:5]]
                }
                return {'success': True, 'count': len(results)}
            else:
                print(f"\n⚠️  DELTA NEUTRAL SCREENER: No opportunities found")
                print("   This may indicate: No delta-neutral setups available, or options data incomplete")
                
                self.test_results['delta_neutral_screener'] = {
                    'success': True,
                    'count': 0,
                    'note': 'No delta neutral opportunities'
                }
                return {'success': True, 'count': 0}
        
        except Exception as e:
            print(f"\n❌ DELTA NEUTRAL SCREENER ERROR: {str(e)}")
            logger.error(f"Delta Neutral Screener error: {e}", exc_info=True)
            
            self.test_results['delta_neutral_screener'] = {
                'success': False,
                'error': str(e)
            }
            return {'success': False, 'error': str(e)}
    
    def print_comprehensive_report(self):
        """Print comprehensive test report"""
        print("\n" + "="*100)
        print("COMPREHENSIVE TEST REPORT - LIVE DATA")
        print("="*100)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print("API CONNECTION STATUS:")
        print(f"  Status: {'✅ CONNECTED' if self.connection_status else '❌ NOT CONNECTED'}\n")
        
        print("SCREENER TEST RESULTS:")
        print("-" * 100)
        
        screener_names = [
            'iv_screener',
            'earnings_screener', 
            'theta_screener',
            'combo_screener',
            'hedging_screener',
            'delta_neutral_screener'
        ]
        
        total_opportunities = 0
        successful_screeners = 0
        
        for screener_name in screener_names:
            result = self.test_results.get(screener_name, {})
            
            if result.get('success'):
                status = "✅"
                successful_screeners += 1
            else:
                status = "❌"
            
            count = result.get('count', 0)
            total_opportunities += count
            
            display_name = screener_name.replace('_', ' ').title()
            print(f"{status} {display_name:<30} - {count:>3} opportunities found")
            
            if result.get('error'):
                print(f"   Error: {result['error']}")
            elif result.get('note'):
                print(f"   Note: {result['note']}")
        
        print("\n" + "-" * 100)
        print(f"SUMMARY:")
        print(f"  Total Screeners Tested: 6")
        print(f"  Successful Screeners: {successful_screeners}/6")
        print(f"  Total Opportunities Found: {total_opportunities}")
        print(f"  Average per Screener: {total_opportunities / 6:.1f}")
        
        print("\n" + "="*100)
        print("TEST COMPLETE")
        print("="*100)
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n")
        print("╔" + "="*98 + "╗")
        print("║" + "LIVE DATA TEST - OPTIONS SCREENERS".center(98) + "║")
        print("║" + f"Testing with REAL Breeze API Data".center(98) + "║")
        print("║" + f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(98) + "║")
        print("╚" + "="*98 + "╝")
        
        # Step 1: API Connection
        if not self.setup_api_connection():
            print("\n❌ Cannot proceed without API connection")
            self.print_comprehensive_report()
            return False
        
        # Step 2-7: Run screeners
        print("\n" + "="*100)
        print("RUNNING ALL SCREENERS WITH LIVE DATA")
        print("="*100)
        
        self.test_iv_screener()
        self.test_earnings_screener()
        self.test_theta_screener()
        self.test_combo_screener()
        self.test_hedging_screener()
        self.test_delta_neutral_screener()
        
        # Print comprehensive report
        self.print_comprehensive_report()
        
        return True


def main():
    """Main execution"""
    try:
        tester = LiveDataTester()
        success = tester.run_all_tests()
        
        if success:
            print("\n✅ Live Data Testing Complete - Check results above\n")
            return 0
        else:
            print("\n❌ Live Data Testing Failed - See errors above\n")
            return 1
    
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        logger.error(f"Critical error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
