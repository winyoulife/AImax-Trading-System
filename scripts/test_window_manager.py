#!/usr/bin/env python3
"""
測試時間窗口管理器
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
import threading
from datetime import datetime, timedelta
from src.core.window_manager import (
    WindowManager, WindowScheduler, WindowPriority,
    create_window_manager, high_value_signal_rule, time_critical_rule
)
from src.core.dynamic_trading_data_structures import SignalType, ExecutionReason
from src.core.dynamic_trading_config import TrackingWindowConfig

def test_basic_window_management():
    """測試基本窗口管理功能"""
    print("🧪 測試基本窗口管理功能...")
    
    try:
        # 創建窗口管理器
        config = TrackingWindowConfig()
        manager = WindowManager(config)
        
        # 創建測試窗口
        start_time = datetime.now()
        duration = timedelta(minutes=5)  # 5分鐘窗口
        
        success = manager.create_window(
            window_id="test_buy_001",
            signal_type=SignalType.BUY,
            start_time=start_time,
            duration=duration,
            priority=WindowPriority.NORMAL
        )
        
        print(f"✅ 創建窗口: {success}")
        
        # 檢查窗口狀態
        is_expired = manager.is_window_expired("test_buy_001")
        time_remaining = manager.get_time_remaining("test_buy_001")
        
        print(f"   窗口是否過期: {is_expired}")
        print(f"   剩餘時間: {time_remaining.total_seconds():.1f} 秒")
        
        # 更新窗口活動
        update_success = manager.update_window_activity("test_buy_001", datetime.now())
        print(f"   更新活動: {update_success}")
        
        # 獲取窗口摘要
        summary = manager.get_window_summary("test_buy_001")
        if summary:
            print(f"   窗口摘要: {summary['signal_type']}, 優先級: {summary['priority']}")
        
        # 關閉窗口
        close_success = manager.close_window("test_buy_001", ExecutionReason.MANUAL_OVERRIDE)
        print(f"✅ 關閉窗口: {close_success}")
        
        # 獲取統計信息
        stats = manager.get_statistics()
        print(f"✅ 統計信息: 總調度 {stats['total_windows_scheduled']}, "
              f"活躍 {stats['active_windows']}, 已完成 {stats['completed_windows']}")
        
        manager.shutdown()
        
    except Exception as e:
        print(f"❌ 基本窗口管理測試失敗: {e}")

def test_window_expiration():
    """測試窗口過期處理"""
    print("\n🧪 測試窗口過期處理...")
    
    try:
        config = TrackingWindowConfig()
        manager = WindowManager(config)
        
        # 設置短監控間隔
        manager.set_monitoring_interval(1)  # 1秒檢查一次
        
        # 回調計數器
        callback_counts = {'timeout': 0, 'warning': 0}
        
        def on_timeout(window_id, schedule):
            callback_counts['timeout'] += 1
            print(f"   🔔 超時回調: {window_id}")
        
        def on_warning(window_id, schedule, remaining_minutes):
            callback_counts['warning'] += 1
            print(f"   ⚠️ 警告回調: {window_id}, 剩餘 {remaining_minutes:.1f} 分鐘")
        
        # 設置回調
        manager.set_callbacks(on_timeout=on_timeout, on_warning=on_warning)
        
        # 創建短期窗口
        start_time = datetime.now()
        short_duration = timedelta(seconds=3)  # 3秒窗口
        
        manager.create_window(
            window_id="short_window_001",
            signal_type=SignalType.BUY,
            start_time=start_time,
            duration=short_duration,
            priority=WindowPriority.HIGH
        )
        
        print("✅ 創建短期窗口，等待過期...")
        
        # 等待窗口過期
        time.sleep(5)
        
        # 檢查過期窗口
        expired_windows = manager.get_expired_windows()
        print(f"   過期窗口數量: {len(expired_windows)}")
        
        # 檢查回調是否被觸發
        print(f"✅ 回調統計: 超時 {callback_counts['timeout']} 次, "
              f"警告 {callback_counts['warning']} 次")
        
        manager.shutdown()
        
    except Exception as e:
        print(f"❌ 窗口過期測試失敗: {e}")

def test_multiple_windows():
    """測試多窗口管理"""
    print("\n🧪 測試多窗口管理...")
    
    try:
        config = TrackingWindowConfig()
        manager = WindowManager(config)
        
        # 創建多個不同類型和優先級的窗口
        start_time = datetime.now()
        window_configs = [
            ("buy_high_001", SignalType.BUY, WindowPriority.HIGH, 10),
            ("sell_normal_001", SignalType.SELL, WindowPriority.NORMAL, 15),
            ("buy_low_001", SignalType.BUY, WindowPriority.LOW, 20),
            ("sell_critical_001", SignalType.SELL, WindowPriority.CRITICAL, 5),
        ]
        
        created_windows = []
        for window_id, signal_type, priority, duration_minutes in window_configs:
            success = manager.create_window(
                window_id=window_id,
                signal_type=signal_type,
                start_time=start_time + timedelta(seconds=len(created_windows)),
                duration=timedelta(minutes=duration_minutes),
                priority=priority
            )
            if success:
                created_windows.append(window_id)
        
        print(f"✅ 創建了 {len(created_windows)} 個窗口")
        
        # 獲取所有活躍調度
        active_schedules = manager.get_all_active_schedules()
        print(f"   活躍調度數量: {len(active_schedules)}")
        
        # 按優先級顯示窗口
        for window_id, schedule in active_schedules.items():
            remaining = manager.get_time_remaining(window_id)
            print(f"   窗口 {window_id}: {schedule.signal_type.value}, "
                  f"優先級 {schedule.priority.name}, "
                  f"剩餘 {remaining.total_seconds()/60:.1f} 分鐘")
        
        # 測試批量操作
        print("\n   測試批量關閉...")
        for window_id in created_windows[:2]:  # 關閉前兩個窗口
            manager.close_window(window_id, ExecutionReason.MANUAL_OVERRIDE)
        
        # 檢查統計信息
        stats = manager.get_statistics()
        print(f"✅ 更新後統計: 活躍 {stats['active_windows']}, "
              f"已完成 {stats['completed_windows']}")
        
        # 按類型統計
        type_stats = stats['active_windows_by_type']
        priority_stats = stats['active_windows_by_priority']
        print(f"   按類型: 買入 {type_stats['buy']}, 賣出 {type_stats['sell']}")
        print(f"   按優先級: {priority_stats}")
        
        manager.shutdown()
        
    except Exception as e:
        print(f"❌ 多窗口管理測試失敗: {e}")

def test_warning_system():
    """測試警告系統"""
    print("\n🧪 測試警告系統...")
    
    try:
        config = TrackingWindowConfig()
        manager = WindowManager(config)
        
        # 設置短警告閾值
        manager.set_warning_threshold(1)  # 1分鐘警告
        manager.set_monitoring_interval(2)  # 2秒檢查
        
        # 警告記錄
        warnings_received = []
        
        def on_warning(window_id, schedule, remaining_minutes):
            warnings_received.append({
                'window_id': window_id,
                'remaining_minutes': remaining_minutes,
                'timestamp': datetime.now()
            })
            print(f"   ⚠️ 收到警告: {window_id}, 剩餘 {remaining_minutes:.1f} 分鐘")
        
        manager.set_callbacks(on_warning=on_warning)
        
        # 創建即將過期的窗口
        start_time = datetime.now()
        manager.create_window(
            window_id="warning_test_001",
            signal_type=SignalType.BUY,
            start_time=start_time,
            duration=timedelta(minutes=1.5),  # 1.5分鐘窗口
            priority=WindowPriority.NORMAL
        )
        
        print("✅ 創建測試窗口，等待警告...")
        
        # 等待警告觸發
        time.sleep(4)
        
        # 檢查即將過期的窗口
        near_expiry = manager.get_windows_near_expiry(warning_minutes=2)
        print(f"   即將過期窗口: {len(near_expiry)}")
        
        # 檢查警告統計
        stats = manager.get_statistics()
        print(f"✅ 警告統計: 已發出 {stats['warning_issued']} 次警告")
        print(f"   收到警告: {len(warnings_received)} 次")
        
        manager.shutdown()
        
    except Exception as e:
        print(f"❌ 警告系統測試失敗: {e}")

def test_window_scheduler():
    """測試窗口調度器"""
    print("\n🧪 測試窗口調度器...")
    
    try:
        config = TrackingWindowConfig()
        manager = WindowManager(config)
        scheduler = WindowScheduler(manager)
        
        # 添加調度規則
        scheduler.add_scheduling_rule(high_value_signal_rule)
        scheduler.add_scheduling_rule(time_critical_rule)
        
        # 創建測試窗口
        start_time = datetime.now()
        test_windows = [
            ("normal_001", SignalType.BUY, WindowPriority.NORMAL, 30),
            ("short_001", SignalType.SELL, WindowPriority.LOW, 5),  # 短期窗口
            ("long_001", SignalType.BUY, WindowPriority.HIGH, 60),
        ]
        
        for window_id, signal_type, priority, duration_minutes in test_windows:
            manager.create_window(
                window_id=window_id,
                signal_type=signal_type,
                start_time=start_time,
                duration=timedelta(minutes=duration_minutes),
                priority=priority
            )
        
        # 獲取優先級隊列
        priority_queue = scheduler.get_priority_queue()
        
        print(f"✅ 優先級隊列 ({len(priority_queue)} 個窗口):")
        for i, schedule in enumerate(priority_queue):
            print(f"   {i+1}. {schedule.window_id}: {schedule.priority.name}")
        
        # 測試規則計算
        for schedule in priority_queue:
            calculated_priority = scheduler.calculate_priority(schedule)
            print(f"   {schedule.window_id} 計算優先級: {calculated_priority.name}")
        
        manager.shutdown()
        
    except Exception as e:
        print(f"❌ 窗口調度器測試失敗: {e}")

def test_callback_system():
    """測試回調系統"""
    print("\n🧪 測試回調系統...")
    
    try:
        config = TrackingWindowConfig()
        manager = WindowManager(config)
        
        # 回調計數器
        callback_events = {
            'created': [],
            'updated': [],
            'timeout': [],
            'warning': []
        }
        
        def on_created(schedule):
            callback_events['created'].append(schedule.window_id)
            print(f"   📝 創建回調: {schedule.window_id}")
        
        def on_updated(schedule):
            callback_events['updated'].append(schedule.window_id)
            if len(callback_events['updated']) <= 3:  # 只顯示前3次
                print(f"   🔄 更新回調: {schedule.window_id}")
        
        def on_timeout(window_id, schedule):
            callback_events['timeout'].append(window_id)
            print(f"   ⏰ 超時回調: {window_id}")
        
        def on_warning(window_id, schedule, remaining_minutes):
            callback_events['warning'].append(window_id)
            print(f"   ⚠️ 警告回調: {window_id}")
        
        # 設置回調
        manager.set_callbacks(
            on_created=on_created,
            on_updated=on_updated,
            on_timeout=on_timeout,
            on_warning=on_warning
        )
        
        # 設置短間隔以快速觸發事件
        manager.set_monitoring_interval(1)
        manager.set_warning_threshold(1)
        
        # 創建測試窗口
        start_time = datetime.now()
        window_id = manager.create_window(
            window_id="callback_test_001",
            signal_type=SignalType.BUY,
            start_time=start_time,
            duration=timedelta(seconds=3),  # 3秒窗口
            priority=WindowPriority.NORMAL
        )
        
        # 多次更新窗口活動
        for i in range(5):
            time.sleep(0.5)
            manager.update_window_activity("callback_test_001", datetime.now())
        
        # 等待超時
        time.sleep(4)
        
        print(f"✅ 回調統計:")
        print(f"   創建: {len(callback_events['created'])} 次")
        print(f"   更新: {len(callback_events['updated'])} 次")
        print(f"   超時: {len(callback_events['timeout'])} 次")
        print(f"   警告: {len(callback_events['warning'])} 次")
        
        manager.shutdown()
        
    except Exception as e:
        print(f"❌ 回調系統測試失敗: {e}")

def test_edge_cases():
    """測試邊界情況"""
    print("\n🧪 測試邊界情況...")
    
    try:
        config = TrackingWindowConfig()
        manager = WindowManager(config)
        
        # 測試重複創建窗口
        print("📊 測試重複創建窗口:")
        start_time = datetime.now()
        success1 = manager.create_window(
            "duplicate_test", SignalType.BUY, start_time, 
            timedelta(minutes=5), WindowPriority.NORMAL
        )
        success2 = manager.create_window(
            "duplicate_test", SignalType.SELL, start_time, 
            timedelta(minutes=10), WindowPriority.HIGH
        )
        print(f"   第一次創建: {success1}, 第二次創建: {success2}")
        
        # 測試操作不存在的窗口
        print("📊 測試操作不存在的窗口:")
        update_result = manager.update_window_activity("nonexistent", datetime.now())
        close_result = manager.close_window("nonexistent", ExecutionReason.MANUAL_OVERRIDE)
        remaining = manager.get_time_remaining("nonexistent")
        print(f"   更新不存在窗口: {update_result}")
        print(f"   關閉不存在窗口: {close_result}")
        print(f"   獲取剩餘時間: {remaining is None}")
        
        # 測試已過期窗口的操作
        print("📊 測試已過期窗口:")
        past_time = datetime.now() - timedelta(hours=1)
        manager.create_window(
            "expired_test", SignalType.BUY, past_time,
            timedelta(minutes=5), WindowPriority.NORMAL
        )
        
        is_expired = manager.is_window_expired("expired_test")
        remaining = manager.get_time_remaining("expired_test")
        print(f"   過期窗口檢測: {is_expired}")
        print(f"   過期窗口剩餘時間: {remaining.total_seconds() if remaining else 0} 秒")
        
        # 測試關閉管理器
        print("📊 測試關閉管理器:")
        active_before = len(manager.get_all_active_schedules())
        manager.shutdown()
        active_after = len(manager.get_all_active_schedules())
        
        print(f"   關閉前活躍窗口: {active_before}")
        print(f"   關閉後活躍窗口: {active_after}")
        print(f"   正確關閉: {active_after == 0}")
        
    except Exception as e:
        print(f"❌ 邊界情況測試失敗: {e}")

def main():
    """主測試函數"""
    print("🚀 開始測試時間窗口管理器...")
    
    try:
        test_basic_window_management()
        test_window_expiration()
        test_multiple_windows()
        test_warning_system()
        test_window_scheduler()
        test_callback_system()
        test_edge_cases()
        
        print("\n🎉 所有測試完成！")
        print("✅ 時間窗口管理器運行正常")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()