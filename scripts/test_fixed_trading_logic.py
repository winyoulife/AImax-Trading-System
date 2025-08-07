#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試修正後的交易邏輯
驗證一買一賣的嚴格執行
"""

import os
import sys
from datetime import datetime

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.trading.simulation_manager import SimulationTradingManager

def test_fixed_trading_logic():
    """測試修正後的交易邏輯"""
    print("🧪 測試修正後的交易邏輯")
    print("=" * 50)
    
    # 初始化模擬交易管理器
    sim_manager = SimulationTradingManager()
    
    print(f"💰 當前餘額: {sim_manager.current_balance:,.0f} TWD")
    print(f"💼 當前持倉: {sim_manager.positions}")
    
    # 測試1: 嘗試重複買入 (應該被拒絕)
    print("\n🧪 測試1: 嘗試重複買入 (應該被拒絕)")
    buy_signal = {'action': 'buy', 'symbol': 'BTCTWD', 'price': 95000.0, 'confidence': 0.85}
    result = sim_manager.execute_simulation_trade(buy_signal)
    if not result.get('success', False):
        print("✅ 正確拒絕了重複買入信號")
        print(f"📋 拒絕原因: {result.get('reason', '未知')}")
    else:
        print("❌ 錯誤：允許了重複買入")
    
    # 測試2: 嘗試賣出 (應該成功)
    print("\n🧪 測試2: 嘗試賣出 (應該成功)")
    sell_signal = {'action': 'sell', 'symbol': 'BTCTWD', 'price': 96000.0, 'confidence': 0.85}
    result = sim_manager.execute_simulation_trade(sell_signal)
    if result.get('success', False):
        print("✅ 成功執行賣出")
        print(f"📊 賣出記錄: {result}")
        print(f"💰 賣出後餘額: {sim_manager.current_balance:,.0f} TWD")
        print(f"💼 賣出後持倉: {sim_manager.positions}")
    else:
        print("❌ 錯誤：賣出失敗")
        print(f"📋 失敗原因: {result.get('reason', '未知')}")
    
    # 測試3: 賣出後嘗試再次賣出 (應該被拒絕)
    print("\n🧪 測試3: 賣出後嘗試再次賣出 (應該被拒絕)")
    sell_signal2 = {'action': 'sell', 'symbol': 'BTCTWD', 'price': 97000.0, 'confidence': 0.85}
    result = sim_manager.execute_simulation_trade(sell_signal2)
    if not result.get('success', False):
        print("✅ 正確拒絕了空倉賣出信號")
        print(f"📋 拒絕原因: {result.get('reason', '未知')}")
    else:
        print("❌ 錯誤：允許了空倉賣出")
    
    # 測試4: 賣出後嘗試買入 (應該成功)
    print("\n🧪 測試4: 賣出後嘗試買入 (應該成功)")
    buy_signal2 = {'action': 'buy', 'symbol': 'BTCTWD', 'price': 94000.0, 'confidence': 0.85}
    result = sim_manager.execute_simulation_trade(buy_signal2)
    if result.get('success', False):
        print("✅ 成功執行新的買入")
        print(f"📊 買入記錄: {result}")
        print(f"💰 買入後餘額: {sim_manager.current_balance:,.0f} TWD")
        print(f"💼 買入後持倉: {sim_manager.positions}")
    else:
        print("❌ 錯誤：買入失敗")
        print(f"📋 失敗原因: {result.get('reason', '未知')}")
    
    print("\n" + "=" * 50)
    print("🧪 交易邏輯測試完成")
    
    # 顯示最終狀態
    print(f"\n📊 最終狀態:")
    print(f"💰 餘額: {sim_manager.current_balance:,.0f} TWD")
    print(f"💼 持倉: {sim_manager.positions}")
    print(f"📋 總交易數: {len(sim_manager.trade_history)}")

if __name__ == "__main__":
    test_fixed_trading_logic()