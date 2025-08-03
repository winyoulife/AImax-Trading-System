#!/usr/bin/env python3
"""
測試動態交易系統核心數據結構和配置
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
from src.core.dynamic_trading_data_structures import (
    SignalType, WindowStatus, ExecutionReason,
    PricePoint, TrackingWindow, DynamicTradeResult, TrackingStatistics,
    create_window_id, create_trade_id
)
from src.core.dynamic_trading_config import (
    DynamicTradingConfig, ConfigManager,
    get_config, load_config, save_config
)

def test_data_structures():
    """測試數據結構"""
    print("🧪 測試核心數據結構...")
    
    # 測試 PricePoint
    print("\n1. 測試 PricePoint")
    try:
        price_point = PricePoint(
            timestamp=datetime.now(),
            price=3400000.0,
            volume=1000.0,
            is_extreme=True,
            reversal_strength=0.8
        )
        print(f"✅ PricePoint 創建成功: {price_point.price} TWD")
    except Exception as e:
        print(f"❌ PricePoint 測試失敗: {e}")
    
    # 測試 TrackingWindow
    print("\n2. 測試 TrackingWindow")
    try:
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=4)
        
        window = TrackingWindow(
            window_id="test_buy_001",
            signal_type=SignalType.BUY,
            start_time=start_time,
            end_time=end_time,
            start_price=3400000.0,
            current_extreme_price=3400000.0,
            extreme_time=start_time
        )
        
        # 添加價格點
        for i in range(5):
            price = 3400000.0 - (i * 5000)  # 價格逐漸下降
            point = PricePoint(
                timestamp=start_time + timedelta(minutes=i*30),
                price=price,
                volume=1000.0
            )
            window.add_price_point(point)
        
        improvement = window.get_price_improvement()
        improvement_pct = window.get_improvement_percentage()
        
        print(f"✅ TrackingWindow 創建成功")
        print(f"   起始價格: {window.start_price:,.0f} TWD")
        print(f"   極值價格: {window.current_extreme_price:,.0f} TWD")
        print(f"   價格改善: {improvement:,.0f} TWD ({improvement_pct:.2f}%)")
        print(f"   價格點數量: {len(window.price_history)}")
        
    except Exception as e:
        print(f"❌ TrackingWindow 測試失敗: {e}")
    
    # 測試 DynamicTradeResult
    print("\n3. 測試 DynamicTradeResult")
    try:
        result = DynamicTradeResult(
            trade_id="trade_001",
            signal_type=SignalType.BUY,
            original_signal_time=start_time,
            original_signal_price=3400000.0,
            actual_execution_time=start_time + timedelta(hours=2),
            actual_execution_price=3380000.0,
            execution_reason=ExecutionReason.REVERSAL_DETECTED,
            window_data=window
        )
        
        summary = result.get_performance_summary()
        print(f"✅ DynamicTradeResult 創建成功")
        print(f"   價格改善: {result.price_improvement:,.0f} TWD")
        print(f"   改善百分比: {result.improvement_percentage:.2f}%")
        print(f"   追蹤時間: {result.tracking_duration}")
        print(f"   是否改善: {result.is_improvement()}")
        
    except Exception as e:
        print(f"❌ DynamicTradeResult 測試失敗: {e}")
    
    # 測試 TrackingStatistics
    print("\n4. 測試 TrackingStatistics")
    try:
        stats = TrackingStatistics()
        
        # 添加多個交易結果
        for i in range(3):
            test_result = DynamicTradeResult(
                trade_id=f"trade_{i:03d}",
                signal_type=SignalType.BUY if i % 2 == 0 else SignalType.SELL,
                original_signal_time=start_time + timedelta(hours=i),
                original_signal_price=3400000.0,
                actual_execution_time=start_time + timedelta(hours=i+2),
                actual_execution_price=3400000.0 + ((-1)**i * 10000),  # 交替改善
                execution_reason=ExecutionReason.REVERSAL_DETECTED
            )
            stats.update_with_result(test_result)
        
        summary = stats.get_summary()
        print(f"✅ TrackingStatistics 創建成功")
        print(f"   總信號數: {stats.total_signals}")
        print(f"   成功改善: {stats.improved_trades}")
        print(f"   成功率: {stats.get_success_rate():.1f}%")
        print(f"   平均改善: {stats.average_improvement:,.0f} TWD")
        
    except Exception as e:
        print(f"❌ TrackingStatistics 測試失敗: {e}")

def test_config_system():
    """測試配置系統"""
    print("\n🔧 測試配置系統...")
    
    # 測試默認配置
    print("\n1. 測試默認配置")
    try:
        config = DynamicTradingConfig()
        print(f"✅ 默認配置創建成功")
        print(f"   買入窗口: {config.window_config.buy_window_hours} 小時")
        print(f"   賣出窗口: {config.window_config.sell_window_hours} 小時")
        print(f"   反轉閾值: {config.detection_config.reversal_threshold}%")
        print(f"   風險閾值: {config.risk_config.risk_threshold}%")
        print(f"   配置有效: {config.is_valid()}")
        
    except Exception as e:
        print(f"❌ 默認配置測試失敗: {e}")
    
    # 測試配置管理器
    print("\n2. 測試配置管理器")
    try:
        config_manager = ConfigManager("AImax/config/test_dynamic_config.json")
        
        # 載入配置
        config = config_manager.load_config()
        print(f"✅ 配置載入成功")
        
        # 更新配置
        success = config_manager.update_config(
            buy_window_hours=6.0,
            reversal_threshold=0.8
        )
        print(f"✅ 配置更新成功: {success}")
        
        # 獲取配置摘要
        summary = config_manager.get_config_summary()
        print(f"✅ 配置摘要獲取成功")
        print(f"   買入窗口: {summary['window_settings']['buy_window_hours']} 小時")
        print(f"   反轉閾值: {summary['detection_settings']['reversal_threshold']}%")
        
    except Exception as e:
        print(f"❌ 配置管理器測試失敗: {e}")
    
    # 測試配置驗證
    print("\n3. 測試配置驗證")
    try:
        config = DynamicTradingConfig()
        
        # 測試有效配置
        validation = config.validate_all()
        print(f"✅ 配置驗證完成")
        for key, valid in validation.items():
            status = "✅" if valid else "❌"
            print(f"   {key}: {status}")
        
        # 測試無效配置
        config.window_config.buy_window_hours = -1.0  # 無效值
        invalid_validation = config.validate_all()
        print(f"✅ 無效配置檢測完成")
        print(f"   整體有效性: {config.is_valid()}")
        
    except Exception as e:
        print(f"❌ 配置驗證測試失敗: {e}")

def test_utility_functions():
    """測試工具函數"""
    print("\n🛠️ 測試工具函數...")
    
    try:
        now = datetime.now()
        
        # 測試 ID 生成
        window_id = create_window_id(SignalType.BUY, now)
        trade_id = create_trade_id(SignalType.SELL, now)
        
        print(f"✅ 工具函數測試成功")
        print(f"   窗口 ID: {window_id}")
        print(f"   交易 ID: {trade_id}")
        
    except Exception as e:
        print(f"❌ 工具函數測試失敗: {e}")

def main():
    """主測試函數"""
    print("🚀 開始測試動態交易系統核心組件...")
    
    try:
        test_data_structures()
        test_config_system()
        test_utility_functions()
        
        print("\n🎉 所有測試完成！")
        print("✅ 核心數據結構和配置系統運行正常")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()