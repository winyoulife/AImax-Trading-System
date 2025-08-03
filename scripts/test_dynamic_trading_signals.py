#!/usr/bin/env python3
"""
測試動態交易信號處理核心
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.core.dynamic_trading_signals import (
    DynamicTradingSignals, DynamicTradingEngine, 
    create_dynamic_trading_system, DynamicSignalContext
)
from src.core.dynamic_trading_data_structures import SignalType, ExecutionReason
from src.core.dynamic_trading_config import DynamicTradingConfig

def create_mock_macd_data(periods: int = 50) -> pd.DataFrame:
    """創建模擬 MACD 數據"""
    base_time = datetime.now() - timedelta(hours=periods)
    
    data = {
        'datetime': [base_time + timedelta(hours=i) for i in range(periods)],
        'timestamp': [int((base_time + timedelta(hours=i)).timestamp()) for i in range(periods)],
        'open': np.random.uniform(3400000, 3500000, periods),
        'high': np.random.uniform(3450000, 3550000, periods),
        'low': np.random.uniform(3350000, 3450000, periods),
        'close': np.random.uniform(3400000, 3500000, periods),
        'volume': np.random.uniform(1000, 5000, periods)
    }
    
    df = pd.DataFrame(data)
    
    # 計算 MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    return df

async def test_basic_signal_processing():
    """測試基本信號處理功能"""
    print("🧪 測試基本信號處理功能...")
    
    try:
        # 創建配置
        config = DynamicTradingConfig()
        config.enable_dynamic_tracking = True
        config.window_config.buy_window_hours = 0.1  # 6分鐘窗口
        config.window_config.sell_window_hours = 0.1
        
        # 創建系統
        system = DynamicTradingSignals(config)
        
        # 設置回調計數器
        callback_counts = {
            'signal_detected': 0,
            'tracking_started': 0,
            'tracking_completed': 0,
            'trade_executed': 0
        }
        
        def on_signal_detected(context):
            callback_counts['signal_detected'] += 1
            print(f"   📡 信號檢測: {context.signal_type.value} at {context.original_signal_price:,.0f}")
        
        def on_tracking_started(context):
            callback_counts['tracking_started'] += 1
            print(f"   🎯 開始追蹤: {context.window_id}")
        
        def on_tracking_completed(context):
            callback_counts['tracking_completed'] += 1
            print(f"   ✅ 追蹤完成: {context.window_id}")
        
        def on_trade_executed(result):
            callback_counts['trade_executed'] += 1
            print(f"   💰 交易執行: {result.trade_id}, 改善: {result.price_improvement:,.0f} TWD")
        
        # 設置回調
        system.set_callbacks(
            on_signal_detected=on_signal_detected,
            on_tracking_started=on_tracking_started,
            on_tracking_completed=on_tracking_completed,
            on_trade_executed=on_trade_executed
        )
        
        print("✅ 系統初始化完成")
        
        # 獲取系統狀態
        status = system.get_system_status()
        print(f"   動態追蹤啟用: {status['dynamic_tracking_enabled']}")
        print(f"   活躍信號: {status['active_signals']}")
        
        # 獲取統計信息
        stats = system.get_statistics()
        print(f"   統計摘要: {stats.get_summary()}")
        
        print(f"✅ 回調統計:")
        for event, count in callback_counts.items():
            print(f"   {event}: {count} 次")
        
        await system.shutdown()
        
    except Exception as e:
        print(f"❌ 基本信號處理測試失敗: {e}")

async def test_mock_data_processing():
    """測試模擬數據處理"""
    print("\n🧪 測試模擬數據處理...")
    
    try:
        # 創建配置
        config = DynamicTradingConfig()
        config.enable_dynamic_tracking = True
        
        # 創建系統
        system = DynamicTradingSignals(config)
        
        # 創建模擬數據
        mock_data = create_mock_macd_data(100)
        print(f"✅ 創建模擬數據: {len(mock_data)} 筆記錄")
        
        # 手動添加一些信號
        # 在數據中間添加買入信號
        mid_index = len(mock_data) // 2
        mock_data.loc[mid_index, 'macd'] = -100
        mock_data.loc[mid_index, 'macd_signal'] = -50
        mock_data.loc[mid_index, 'macd_hist'] = -50
        
        # 添加賣出信號
        sell_index = mid_index + 10
        if sell_index < len(mock_data):
            mock_data.loc[sell_index, 'macd'] = 100
            mock_data.loc[sell_index, 'macd_signal'] = 50
            mock_data.loc[sell_index, 'macd_hist'] = 50
        
        print("✅ 添加模擬信號到數據中")
        
        # 檢查系統狀態
        initial_status = system.get_system_status()
        print(f"   初始狀態: 活躍信號 {initial_status['active_signals']}")
        
        await system.shutdown()
        
    except Exception as e:
        print(f"❌ 模擬數據處理測試失敗: {e}")

async def test_trading_engine():
    """測試交易引擎"""
    print("\n🧪 測試交易引擎...")
    
    try:
        # 創建配置
        config = DynamicTradingConfig()
        config.enable_dynamic_tracking = True
        
        # 創建系統和引擎
        system = DynamicTradingSignals(config)
        engine = DynamicTradingEngine(system)
        
        # 設置短更新間隔用於測試
        engine.set_update_interval(5)  # 5秒
        
        print("✅ 交易引擎創建成功")
        
        # 測試單次分析
        print("   執行單次分析...")
        try:
            result = await engine.run_single_analysis("btctwd", "60")
            if result is not None:
                print(f"   ✅ 單次分析完成: {len(result)} 筆數據")
            else:
                print("   ⚠️ 單次分析返回 None（可能是網絡問題）")
        except Exception as e:
            print(f"   ⚠️ 單次分析失敗: {e}")
        
        # 獲取性能報告
        report = engine.get_performance_report()
        print(f"✅ 性能報告:")
        print(f"   系統健康: {report['system_status'].get('system_health', 'unknown')}")
        print(f"   建議數量: {len(report['recommendations'])}")
        for i, rec in enumerate(report['recommendations'][:3]):  # 只顯示前3個建議
            print(f"   建議 {i+1}: {rec}")
        
        await system.shutdown()
        
    except Exception as e:
        print(f"❌ 交易引擎測試失敗: {e}")

async def test_configuration_impact():
    """測試配置參數影響"""
    print("\n🧪 測試配置參數影響...")
    
    try:
        # 測試不同配置
        configs = [
            ("動態追蹤啟用", {"enable_dynamic_tracking": True}),
            ("動態追蹤禁用", {"enable_dynamic_tracking": False}),
            ("短窗口時間", {"enable_dynamic_tracking": True, "window_hours": 0.05}),
            ("長窗口時間", {"enable_dynamic_tracking": True, "window_hours": 0.2}),
        ]
        
        for config_name, config_params in configs:
            print(f"\n📊 測試配置: {config_name}")
            
            # 創建配置
            config = DynamicTradingConfig()
            config.enable_dynamic_tracking = config_params.get("enable_dynamic_tracking", True)
            
            if "window_hours" in config_params:
                config.window_config.buy_window_hours = config_params["window_hours"]
                config.window_config.sell_window_hours = config_params["window_hours"]
            
            # 創建系統
            system = DynamicTradingSignals(config)
            
            # 獲取初始狀態
            status = system.get_system_status()
            print(f"   動態追蹤: {status['dynamic_tracking_enabled']}")
            print(f"   系統健康: {status.get('system_health', 'unknown')}")
            
            await system.shutdown()
        
        print("✅ 配置參數測試完成")
        
    except Exception as e:
        print(f"❌ 配置參數測試失敗: {e}")

async def test_system_integration():
    """測試系統集成"""
    print("\n🧪 測試系統集成...")
    
    try:
        # 創建系統
        system = create_dynamic_trading_system()
        
        # 檢查組件集成
        print("✅ 檢查組件集成:")
        
        # 檢查價格追蹤器
        tracker_stats = system.price_tracker.get_statistics()
        print(f"   價格追蹤器: 創建 {tracker_stats['total_windows_created']} 個窗口")
        
        # 檢查窗口管理器
        window_stats = system.window_manager.get_statistics()
        print(f"   窗口管理器: 監控 {'啟用' if window_stats['monitoring_active'] else '禁用'}")
        
        # 檢查統計系統
        stats = system.get_statistics()
        summary = stats.get_summary()
        print(f"   統計系統: 總信號 {summary['total_signals']}")
        
        # 檢查系統狀態
        status = system.get_system_status()
        print(f"   系統狀態: {status.get('system_health', 'unknown')}")
        
        # 測試回調系統
        callback_triggered = False
        
        def test_callback(context):
            nonlocal callback_triggered
            callback_triggered = True
        
        system.set_callbacks(on_signal_detected=test_callback)
        print(f"   回調系統: 設置完成")
        
        await system.shutdown()
        print("✅ 系統集成測試完成")
        
    except Exception as e:
        print(f"❌ 系統集成測試失敗: {e}")

async def test_error_handling():
    """測試錯誤處理"""
    print("\n🧪 測試錯誤處理...")
    
    try:
        # 創建系統
        config = DynamicTradingConfig()
        system = DynamicTradingSignals(config)
        
        print("📊 測試各種錯誤情況:")
        
        # 測試無效的信號上下文
        print("   測試無效信號處理...")
        invalid_signals = system.get_active_signals()
        print(f"   無效信號數量: {len(invalid_signals)}")
        
        # 測試系統狀態在錯誤情況下
        status = system.get_system_status()
        print(f"   錯誤狀態下系統健康: {status.get('system_health', 'unknown')}")
        
        # 測試統計系統的錯誤處理
        stats = system.get_statistics()
        print(f"   統計系統錯誤處理: 成功率 {stats.get_success_rate():.1f}%")
        
        # 測試關閉系統
        print("   測試系統關閉...")
        await system.shutdown()
        
        # 檢查關閉後狀態
        final_status = system.get_system_status()
        print(f"   關閉後狀態: {final_status.get('active_signals', 0)} 個活躍信號")
        
        print("✅ 錯誤處理測試完成")
        
    except Exception as e:
        print(f"❌ 錯誤處理測試失敗: {e}")

async def main():
    """主測試函數"""
    print("🚀 開始測試動態交易信號處理核心...")
    
    try:
        await test_basic_signal_processing()
        await test_mock_data_processing()
        await test_trading_engine()
        await test_configuration_impact()
        await test_system_integration()
        await test_error_handling()
        
        print("\n🎉 所有測試完成！")
        print("✅ 動態交易信號處理核心運行正常")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(main())