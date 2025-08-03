#!/usr/bin/env python3
"""
簡單測試追蹤數據管理系統
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 測試基本導入
try:
    print("測試導入 dynamic_trading_config...")
    from src.core.dynamic_trading_config import PerformanceConfig
    print("✅ PerformanceConfig 導入成功")
    
    print("測試導入 dynamic_trading_data_structures...")
    from src.core.dynamic_trading_data_structures import (
        DynamicTradeResult, TrackingStatistics, SignalType, ExecutionReason
    )
    print("✅ 數據結構導入成功")
    
    print("測試創建 PerformanceConfig...")
    config = PerformanceConfig()
    print("✅ PerformanceConfig 創建成功")
    
    print("測試導入 tracking_data_manager...")
    from src.data.tracking_data_manager import TrackingDataManager
    print("✅ TrackingDataManager 導入成功")
    
    print("測試創建 TrackingDataManager...")
    manager = TrackingDataManager(config, "test_tracking.db")
    print("✅ TrackingDataManager 創建成功")
    
    print("測試創建統計對象...")
    stats = TrackingStatistics()
    print("✅ TrackingStatistics 創建成功")
    
    print("\n🎉 所有基本測試通過！")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()