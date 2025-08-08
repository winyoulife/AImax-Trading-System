#!/usr/bin/env python3
"""
🧪 測試修正後的GUI - 檢查價格一致性和初始化延遲
"""
import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from trading.virtual_trading_engine import VirtualTradingEngine

def test_fixed_issues():
    print("🧪 測試修正後的虛擬交易引擎...")
    
    # 初始化引擎
    engine = VirtualTradingEngine(initial_balance=100000)
    
    print("\n📊 測試1: 價格一致性")
    print("=" * 40)
    
    # 測試價格獲取
    price1 = engine.get_current_price()
    print(f"get_current_price(): NT$ {price1:,.0f}")
    
    # 測試信號檢測中的價格
    print("\n🔍 測試信號檢測...")
    signal = engine.check_trading_signals()
    
    if signal:
        price2 = signal['current_price']
        print(f"信號中的價格: NT$ {price2:,.0f}")
        
        if abs(price1 - price2) < 1000:  # 允許小幅差異
            print("✅ 價格一致性測試通過")
        else:
            print(f"❌ 價格不一致: {price1:,.0f} vs {price2:,.0f}")
    else:
        print("✅ 初始化延遲正常工作 (無信號)")
    
    print("\n⏳ 測試2: 初始化延遲")
    print("=" * 40)
    
    # 測試多次信號檢測
    for i in range(3):
        print(f"第 {i+1} 次檢測...")
        signal = engine.check_trading_signals()
        if signal:
            print(f"  ⚠️ 檢測到信號: {signal['signal_type']}")
        else:
            print("  ✅ 延遲中，無信號")
        time.sleep(2)
    
    print("\n📊 測試3: 帳戶狀態")
    print("=" * 40)
    status = engine.get_account_status()
    print(f"當前價格: NT$ {status['current_price']:,.0f}")
    print(f"總資產: NT$ {status['total_value']:,.0f}")
    print(f"TWD餘額: NT$ {status['twd_balance']:,.0f}")
    print(f"BTC餘額: {status['btc_balance']:.6f}")

if __name__ == "__main__":
    test_fixed_issues()