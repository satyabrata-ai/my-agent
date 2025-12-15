#!/usr/bin/env python3
"""
Test script for Event Impact Correlation Agent - Bond Volatility Analysis
"""
import sys
from app.sub_agents.event_impact_agent.tools import analyze_bond_volatility

def test_bond_volatility():
    """Test the bond volatility analysis tool"""
    
    print("="*80)
    print("TESTING BOND VOLATILITY ANALYSIS")
    print("="*80)
    print("\nQuery: 'I want to trade around market volatility for 10-year bonds")
    print("       for a time horizon of 5 years. Provide confidence and reasoning.'\n")
    
    try:
        # Call the bond volatility analysis tool
        result = analyze_bond_volatility(
            instrument="10Y",
            time_horizon_years=5,
            confidence_threshold=0.7
        )
        
        if result['status'] == 'success':
            print("\n" + "="*80)
            print("✅ ANALYSIS SUCCESSFUL!")
            print("="*80)
            
            # Display key results
            print(f"\n📊 INSTRUMENT: {result['instrument']}")
            print(f"⏱️  ANALYSIS PERIOD: {result['analysis_period']['start']} to {result['analysis_period']['end']}")
            
            print(f"\n📈 VOLATILITY METRICS:")
            vm = result['volatility_metrics']
            print(f"   Current: {vm['current_volatility']}%")
            print(f"   Mean (5Y): {vm['mean_volatility']}%")
            print(f"   Percentile: {vm['volatility_percentile']}%")
            print(f"   High Vol Threshold: {vm['high_vol_threshold']}%")
            
            print(f"\n🎯 TRADING SIGNAL:")
            ts = result['trading_signal']
            print(f"   Signal: {ts['signal']}")
            print(f"   Strength: {ts['strength']}")
            print(f"   Confidence: {ts['confidence_percentage']}")
            print(f"   Status: {ts['recommendation_status']}")
            
            print(f"\n💪 CONFIDENCE BREAKDOWN:")
            cb = result['confidence_breakdown']
            print(f"   Data Completeness: {cb['data_completeness']:.1%}")
            print(f"   Event Coverage: {cb['event_coverage']:.1%}")
            print(f"   Volatility Consistency: {cb['volatility_consistency']:.1%}")
            print(f"   Overall: {cb['overall_confidence']:.1%}")
            
            print(f"\n📝 RATIONALE:")
            print(f"   {ts['rationale']}")
            
            print(f"\n✅ RECOMMENDATION:")
            print(f"   {result['recommendation']}")
            
            print(f"\n⚠️  RISK DISCLAIMER:")
            print(f"   {result['risk_disclaimer']}")
            
            print("\n" + "="*80)
            print("TEST PASSED ✅")
            print("="*80)
            
            return True
            
        else:
            print("\n" + "="*80)
            print("❌ ANALYSIS FAILED")
            print("="*80)
            print(f"\nError: {result.get('message', 'Unknown error')}")
            if 'traceback' in result:
                print(f"\nTraceback:\n{result['traceback']}")
            
            return False
            
    except Exception as e:
        print("\n" + "="*80)
        print("❌ TEST FAILED WITH EXCEPTION")
        print("="*80)
        print(f"\nException: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_bond_volatility()
    sys.exit(0 if success else 1)

