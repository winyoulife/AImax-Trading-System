#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡單交易測試腳本
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# 添加項目路徑
sys.path.append('.')

print("🧪 測試AImax交易系統...")

try:
    # 測試數據獲取器
    from src.data.simple_data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    print("✅ DataFetcher導入成功")
    
    # 測試獲取價格
    price = fetcher.get_current_price('BTCUSDT')
    print(f"✅ 獲取BTC價格成功: ${price:,.2f}")
    
    # 測試獲取歷史數據
    df = fetcher.get_historical_data('BTCUSDT', '1h', 50)
    print(f"✅ 獲取歷史數據成功: {len(df)} 條記錄")
    
    # 測試策略
    from src.core.clean_ultimate_signals import UltimateOptimizedVolumeEnhancedMACDSignals
    
    strategy = UltimateOptimizedVolumeEnhancedMACDSignals()
    print("✅ 策略導入成功")
    
    # 測試信號檢測
    signals = strategy.detect_signals(df)
    print(f"✅ 信號檢測成功: {len(signals)} 個信號")
    
    # 測試模擬交易管理器
    from src.trading.simulation_manager import SimulationTradingManager
    
    sim_manager = SimulationTradingManager()
    print("✅ 模擬交易管理器初始化成功")
    
    # 生成測試信號
    if len(signals) == 0:
        # 創建一個測試信號
        test_signal = {
            'action': 'buy',
            'price': price,
            'confidence': 0.87,
            'symbol': 'BTCUSDT'
        }
        
        result = sim_manager.execute_simulation_trade(test_signal)
        if result['success']:
            print("✅ 模擬交易執行成功")
        else:
            print(f"⚠️ 模擬交易跳過: {result['reason']}")
    
    # 生成報告
    report = sim_manager.get_performance_report()
    print("\n" + "="*50)
    print(report)
    print("="*50)
    
    print("\n🎉 所有測試通過！系統運行正常")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)