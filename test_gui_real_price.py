#!/usr/bin/env python3
"""
🧪 測試GUI是否使用真實MAX API價格
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from trading.virtual_trading_engine import VirtualTradingEngine

def test_real_price():
    print("🧪 測試虛擬交易引擎的真實價格獲取...")
    
    # 初始化引擎
    engine = VirtualTradingEngine(initial_balance=100000)
    
    # 測試價格獲取
    print("🔍 獲取當前BTC價格...")
    price = engine.get_current_price()
    
    if price:
        print(f"✅ 成功獲取價格: NT$ {price:,.0f}")
        
        # 檢查是否為真實價格範圍
        if 2500000 <= price <= 4000000:
            print("✅ 價格在合理範圍內 (250萬-400萬)")
        else:
            print(f"⚠️ 價格可能不是真實的: {price:,.0f}")
    else:
        print("❌ 無法獲取價格")
    
    # 測試帳戶狀態
    print("\n📊 測試帳戶狀態...")
    status = engine.get_account_status()
    print(f"當前價格: NT$ {status['current_price']:,.0f}")
    print(f"總資產: NT$ {status['total_value']:,.0f}")

if __name__ == "__main__":
    test_real_price()