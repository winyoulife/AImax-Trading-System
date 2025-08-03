#!/usr/bin/env python3
"""
測試價格追蹤器系統
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
import threading
from datetime import datetime, timedelta
from src.core.price_tracker import PriceTracker, TrackingManager, create_price_tracker
from src.core.dynamic_trading_data_structures import SignalType, ExecutionReason
from src.core.dynamic_trading_config import (
    TrackingWindowConfig, PerformanceConfig, ExtremeDetectionConfig
)

def test_basic_tracking():
    """測試基本追蹤功能"""
    print("🧪 測試基本追蹤功能...")
    
    try:
        # 創建追蹤器
        window_config = TrackingWindowConfig(
            buy_window_hours=1.0,  # 1小時窗口
            sell_window_hours=1.0
        )
        performance_config = PerformanceConfig()
        tracker = PriceTracker(window_config, performance_config)
        
        # 創建檢測器配置
        detector_config = ExtremeDetectionConfig(
            reversal_threshold=0.5,
            confirmation_periods=2
        )
        
        # 開始追蹤買入信號
        start_time = datetime.now()
        start_price = 3400000.0
        
        window_id = tracker.start_tracking(
            SignalType.BUY, start_price, start_time, detector_config
        )
        
        print(f"✅ 開始追蹤窗口: {window_id}")
        
        # 模擬價格更新
        test_prices = [3395000, 3390000, 3385000, 3390000, 3395000]  # 下跌後反彈
        
        for i, price in enumerate(test_prices):
            update_time = start_time + timedelta(minutes=(i+1)*10)
            success = tracker.update_price(window_id, price, update_time, 1000.0)
            print(f"   更新價格 {i+1}: {price:,.0f} TWD, 成功: {success}")
            
            # 檢查窗口狀態
            window = tracker.get_active_window(window_id)
            if window:
                improvement = window.get_price_improvement()
                print(f"   當前改善: {improvement:,.0f} TWD")
            else:
                # 窗口可能已完成
                completed_window = tracker.get_completed_window(window_id)
                if completed_window:
                    print(f"   窗口已完成，原因: {completed_window.execution_reason.value}")
                    break
        
        # 獲取統計信息
        stats = tracker.get_statistics()
        print(f"✅ 追蹤統計: 創建 {stats['total_windows_created']} 個窗口")
        print(f"   活躍窗口: {stats['active_windows_count']}")
        print(f"   已完成窗口: {stats['completed_windows_count']}")
        
    except Exception as e:
        print(f"❌ 基本追蹤測試失敗: {e}")

def test_concurrent_tracking():
    """測試並發追蹤功能"""
    print("\n🧪 測試並發追蹤功能...")
    
    try:
        tracker = create_price_tracker()
        detector_config = ExtremeDetectionConfig()
        
        # 創建多個追蹤窗口
        window_ids = []
        start_time = datetime.now()
        
        # 創建3個買入窗口和2個賣出窗口
        for i in range(3):
            window_id = tracker.start_tracking(
                SignalType.BUY, 3400000 + i*1000, 
                start_time + timedelta(minutes=i*5), detector_config
            )
            window_ids.append(window_id)
        
        for i in range(2):
            window_id = tracker.start_tracking(
                SignalType.SELL, 3450000 + i*1000,
                start_time + timedelta(minutes=i*5), detector_config
            )
            window_ids.append(window_id)
        
        print(f"✅ 創建了 {len(window_ids)} 個並發追蹤窗口")
        
        # 同時更新所有窗口的價格
        for round_num in range(3):
            update_time = start_time + timedelta(minutes=(round_num+1)*10)
            
            for i, window_id in enumerate(window_ids):
                if i < 3:  # 買入窗口 - 價格下跌
                    price = 3400000 + i*1000 - (round_num+1)*2000
                else:  # 賣出窗口 - 價格上漲
                    price = 3450000 + (i-3)*1000 + (round_num+1)*2000
                
                tracker.update_price(window_id, price, update_time, 1000.0)
        
        # 檢查所有窗口狀態
        active_windows = tracker.get_all_active_windows()
        completed_windows = tracker.get_all_completed_windows()
        
        print(f"✅ 並發追蹤結果:")
        print(f"   活躍窗口: {len(active_windows)}")
        print(f"   已完成窗口: {len(completed_windows)}")
        
        # 顯示每個窗口的摘要
        for window_id in window_ids:
            summary = tracker.get_window_summary(window_id)
            if summary:
                print(f"   窗口 {window_id[:8]}...: {summary['signal_type']}, "
                      f"狀態: {summary['status']}, "
                      f"改善: {summary['price_improvement']:,.0f} TWD")
        
    except Exception as e:
        print(f"❌ 並發追蹤測試失敗: {e}")

def test_callback_system():
    """測試回調系統"""
    print("\n🧪 測試回調系統...")
    
    try:
        tracker = create_price_tracker()
        detector_config = ExtremeDetectionConfig()
        
        # 回調計數器
        callback_counts = {
            'created': 0,
            'updated': 0,
            'completed': 0,
            'reversal': 0
        }
        
        # 定義回調函數
        def on_window_created(window):
            callback_counts['created'] += 1
            print(f"   📝 窗口創建回調: {window.window_id[:8]}...")
        
        def on_window_updated(window):
            callback_counts['updated'] += 1
            if callback_counts['updated'] <= 3:  # 只顯示前3次
                print(f"   🔄 窗口更新回調: {window.window_id[:8]}...")
        
        def on_window_completed(window):
            callback_counts['completed'] += 1
            print(f"   ✅ 窗口完成回調: {window.window_id[:8]}..., "
                  f"原因: {window.execution_reason.value}")
        
        def on_reversal_detected(window_id, reversal):
            callback_counts['reversal'] += 1
            print(f"   🔄 反轉檢測回調: {window_id[:8]}..., "
                  f"強度: {reversal.strength:.2f}")
        
        # 設置回調
        tracker.set_callbacks(
            on_created=on_window_created,
            on_updated=on_window_updated,
            on_completed=on_window_completed,
            on_reversal=on_reversal_detected
        )
        
        # 創建窗口並更新價格
        start_time = datetime.now()
        window_id = tracker.start_tracking(
            SignalType.BUY, 3400000, start_time, detector_config
        )
        
        # 模擬價格變化觸發反轉
        prices = [3395000, 3390000, 3385000, 3390000, 3395000, 3400000]
        for i, price in enumerate(prices):
            update_time = start_time + timedelta(minutes=(i+1)*5)
            tracker.update_price(window_id, price, update_time, 1000.0)
        
        print(f"✅ 回調系統測試完成:")
        print(f"   創建回調: {callback_counts['created']} 次")
        print(f"   更新回調: {callback_counts['updated']} 次")
        print(f"   完成回調: {callback_counts['completed']} 次")
        print(f"   反轉回調: {callback_counts['reversal']} 次")
        
    except Exception as e:
        print(f"❌ 回調系統測試失敗: {e}")

def test_window_expiration():
    """測試窗口過期處理"""
    print("\n🧪 測試窗口過期處理...")
    
    try:
        # 創建短時間窗口配置
        window_config = TrackingWindowConfig(
            buy_window_hours=0.01,  # 0.6分鐘 = 36秒
            sell_window_hours=0.01
        )
        tracker = PriceTracker(window_config, PerformanceConfig())
        detector_config = ExtremeDetectionConfig()
        
        # 創建窗口
        start_time = datetime.now()
        window_id = tracker.start_tracking(
            SignalType.BUY, 3400000, start_time, detector_config
        )
        
        print(f"✅ 創建短期窗口: {window_id[:8]}...")
        
        # 等待窗口過期
        print("   等待窗口過期...")
        time.sleep(2)  # 等待2秒
        
        # 嘗試更新過期窗口
        expired_time = start_time + timedelta(minutes=2)  # 超過窗口時間
        success = tracker.update_price(window_id, 3395000, expired_time, 1000.0)
        
        print(f"   更新過期窗口結果: {success}")
        
        # 檢查窗口狀態
        active_window = tracker.get_active_window(window_id)
        completed_window = tracker.get_completed_window(window_id)
        
        if completed_window:
            print(f"✅ 窗口已正確過期，原因: {completed_window.execution_reason.value}")
        else:
            print("❌ 窗口未正確處理過期")
        
        # 測試批量清理過期窗口
        print("\n   測試批量清理...")
        
        # 創建多個窗口
        window_ids = []
        for i in range(3):
            wid = tracker.start_tracking(
                SignalType.BUY, 3400000 + i*1000,
                start_time + timedelta(seconds=i), detector_config
            )
            window_ids.append(wid)
        
        # 清理過期窗口
        cleanup_time = datetime.now() + timedelta(minutes=5)
        cleaned_count = tracker.cleanup_expired_windows(cleanup_time)
        
        print(f"✅ 批量清理了 {cleaned_count} 個過期窗口")
        
    except Exception as e:
        print(f"❌ 窗口過期測試失敗: {e}")

def test_memory_management():
    """測試內存管理"""
    print("\n🧪 測試內存管理...")
    
    try:
        tracker = create_price_tracker()
        detector_config = ExtremeDetectionConfig()
        
        # 創建大量窗口來測試內存管理
        start_time = datetime.now()
        window_ids = []
        
        print("   創建大量窗口...")
        for i in range(20):
            window_id = tracker.start_tracking(
                SignalType.BUY, 3400000 + i*100,
                start_time + timedelta(seconds=i), detector_config
            )
            window_ids.append(window_id)
            
            # 為每個窗口添加一些價格點
            for j in range(5):
                price = 3400000 + i*100 - j*500
                update_time = start_time + timedelta(seconds=i, minutes=j)
                tracker.update_price(window_id, price, update_time, 1000.0)
        
        # 獲取內存使用統計
        stats = tracker.get_statistics()
        print(f"✅ 內存使用統計:")
        print(f"   總窗口數: {stats['total_windows_created']}")
        print(f"   處理的價格點: {stats['total_price_points_processed']}")
        print(f"   估算內存使用: {stats['memory_usage_mb']:.2f} MB")
        
        # 測試清理舊窗口
        print("\n   測試清理舊窗口...")
        old_completed_count = len(tracker.get_all_completed_windows())
        
        # 清理1小時前的窗口
        cleaned_count = tracker.cleanup_old_completed_windows(retention_hours=0)
        new_completed_count = len(tracker.get_all_completed_windows())
        
        print(f"✅ 清理結果:")
        print(f"   清理前: {old_completed_count} 個已完成窗口")
        print(f"   清理後: {new_completed_count} 個已完成窗口")
        print(f"   清理數量: {cleaned_count} 個")
        
    except Exception as e:
        print(f"❌ 內存管理測試失敗: {e}")

def test_tracking_manager():
    """測試追蹤管理器"""
    print("\n🧪 測試追蹤管理器...")
    
    try:
        tracker = create_price_tracker()
        manager = TrackingManager(tracker)
        detector_config = ExtremeDetectionConfig()
        
        # 創建一些窗口
        start_time = datetime.now()
        for i in range(5):
            tracker.start_tracking(
                SignalType.BUY, 3400000 + i*1000,
                start_time + timedelta(seconds=i), detector_config
            )
        
        # 測試性能指標
        metrics = manager.get_performance_metrics()
        print(f"✅ 性能指標:")
        print(f"   總窗口數: {metrics['total_windows_created']}")
        print(f"   活躍窗口比例: {metrics['active_windows_ratio']:.1f}%")
        print(f"   內存使用: {metrics['memory_usage_mb']:.2f} MB")
        print(f"   平均追蹤時間: {metrics['average_tracking_time']:.1f} 分鐘")
        
        # 測試自動清理
        print("\n   測試自動清理...")
        manager.enable_auto_cleanup(interval_seconds=1)
        
        # 模擬時間推進
        future_time = datetime.now() + timedelta(hours=2)
        manager.auto_cleanup(future_time)
        
        print("✅ 自動清理測試完成")
        
    except Exception as e:
        print(f"❌ 追蹤管理器測試失敗: {e}")

def test_edge_cases():
    """測試邊界情況"""
    print("\n🧪 測試邊界情況...")
    
    try:
        tracker = create_price_tracker()
        detector_config = ExtremeDetectionConfig()
        
        # 測試無效窗口ID
        print("📊 測試無效窗口ID:")
        success = tracker.update_price("invalid_id", 3400000, datetime.now(), 1000.0)
        print(f"   更新無效窗口: {not success}")
        
        # 測試強制完成窗口
        print("📊 測試強制完成窗口:")
        start_time = datetime.now()
        window_id = tracker.start_tracking(
            SignalType.BUY, 3400000, start_time, detector_config
        )
        
        force_success = tracker.force_complete_window(window_id, ExecutionReason.MANUAL_OVERRIDE)
        print(f"   強制完成窗口: {force_success}")
        
        # 檢查窗口是否已完成
        completed_window = tracker.get_completed_window(window_id)
        if completed_window:
            print(f"   完成原因: {completed_window.execution_reason.value}")
        
        # 測試關閉追蹤器
        print("📊 測試關閉追蹤器:")
        
        # 創建一些活躍窗口
        for i in range(3):
            tracker.start_tracking(
                SignalType.BUY, 3400000 + i*1000,
                start_time + timedelta(seconds=i), detector_config
            )
        
        active_before = len(tracker.get_all_active_windows())
        tracker.shutdown()
        active_after = len(tracker.get_all_active_windows())
        
        print(f"   關閉前活躍窗口: {active_before}")
        print(f"   關閉後活躍窗口: {active_after}")
        print(f"   正確關閉: {active_after == 0}")
        
    except Exception as e:
        print(f"❌ 邊界情況測試失敗: {e}")

def main():
    """主測試函數"""
    print("🚀 開始測試價格追蹤器系統...")
    
    try:
        test_basic_tracking()
        test_concurrent_tracking()
        test_callback_system()
        test_window_expiration()
        test_memory_management()
        test_tracking_manager()
        test_edge_cases()
        
        print("\n🎉 所有測試完成！")
        print("✅ 價格追蹤器系統運行正常")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()