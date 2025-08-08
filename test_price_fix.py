#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試價格修正
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.trading.virtual_trading_engine import VirtualTradingEngine

def test_price():
    print("🧪 測試修正後的價格系統...")
    
    engine = VirtualTradingEngine(100000)
    status = engine.get_account_status()
    
    print("📊 修正後的價格測試結果:")
    print(f"   當前價格: NT$ {status['current_price']:,.0f}")
    print(f"   TWD餘額: NT$ {status['twd_balance']:,.0f}")
    print(f"   BTC餘額: {status['btc_balance']:.6f}")
    print(f"   總資產: NT$ {status['total_value']:,.0f}")
    print(f"   已實現獲利: NT$ {status['realized_profit']:+,.0f}")
    print(f"   未實現獲利: NT$ {status['unrealized_profit']:+,.0f}")
    
    # 檢查價格是否合理
    price = status['current_price']
    if 90000 <= price <= 100000:
        print("✅ 價格範圍合理 (90,000 - 100,000)")
    else:
        print(f"❌ 價格不合理: {price:,.0f}")

if __name__ == "__main__":
    test_price()