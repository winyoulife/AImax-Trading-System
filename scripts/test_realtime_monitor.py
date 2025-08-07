#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試實時監控系統
驗證監控器的各項功能
"""

import sys
import os
import time
import json
import threading
from pathlib import Path
from datetime import datetime

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.monitoring.realtime_monitor import realtime_monitor
from src.logging.structured_logger import structured_logger, LogCategory

def test_basic_functionality():
    """測試基本功能"""
    print("🧪 測試基本功能...")
    
    # 測試獲取當前狀態
    try:
        status = realtime_monitor.get_current_status()
        print(f"✅ 獲取狀態成功: 健康分數 {status['health_score']}")
        print(f"   系統狀態: {status['system_status']}")
        print(f"   監控活躍: {status['monitoring_active']}")
    except Exception as e:
        print(f"❌ 獲取狀態失敗: {e}")
        return False
    
    # 測試獲取摘要
    try:
        summary = realtime_monitor.get_system_summary()
        print(f"✅ 獲取摘要成功 ({len(summary)} 字符)")
    except Exception as e:
        print(f"❌ 獲取摘要失敗: {e}")
        return False
    
    return True

def test_monitoring_lifecycle():
    """測試監控生命週期"""
    print("\n🔄 測試監控生命週期...")
    
    # 確保監控未啟動
    if realtime_monitor.monitoring_active:
        realtime_monitor.stop_monitoring()
        time.sleep(1)
    
    # 測試啟動監控
    try:
        print("   啟動監控...")
        realtime_monitor.start_monitoring()
        time.sleep(2)  # 等待監控啟動
        
        if realtime_monitor.monitoring_active:
            print("✅ 監控啟動成功")
        else:
            print("❌ 監控啟動失敗")
            return False
            
    except Exception as e:
        print(f"❌ 啟動監控失敗: {e}")
        return False
    
    # 測試監控運行
    try:
        print("   等待監控數據收集...")
        time.sleep(8)  # 等待至少一個監控週期
        
        status = realtime_monitor.get_current_status()
        if len(realtime_monitor.system_metrics_history) > 0:
            print(f"✅ 監控數據收集成功 ({len(realtime_monitor.system_metrics_history)} 個數據點)")
        else:
            print("❌ 監控數據收集失敗")
            return False
            
    except Exception as e:
        print(f"❌ 監控運行測試失敗: {e}")
        return False
    
    # 測試停止監控
    try:
        print("   停止監控...")
        realtime_monitor.stop_monitoring()
        time.sleep(1)
        
        if not realtime_monitor.monitoring_active:
            print("✅ 監控停止成功")
        else:
            print("❌ 監控停止失敗")
            return False
            
    except Exception as e:
        print(f"❌ 停止監控失敗: {e}")
        return False
    
    return True

def test_metrics_collection():
    """測試指標收集"""
    print("\n📊 測試指標收集...")
    
    try:
        # 測試系統指標收集
        system_metrics = realtime_monitor._collect_system_metrics()
        print(f"✅ 系統指標收集成功:")
        print(f"   CPU: {system_metrics.cpu_percent:.1f}%")
        print(f"   記憶體: {system_metrics.memory_percent:.1f}%")
        print(f"   活躍線程: {system_metrics.active_threads}")
        print(f"   運行時間: {system_metrics.system_uptime:.1f}秒")
        
    except Exception as e:
        print(f"❌ 系統指標收集失敗: {e}")
        return False
    
    try:
        # 測試交易指標收集
        trading_metrics = realtime_monitor._collect_trading_metrics()
        print(f"✅ 交易指標收集成功:")
        print(f"   活躍策略: {trading_metrics.active_strategies}")
        print(f"   總策略數: {trading_metrics.total_strategies}")
        print(f"   當前餘額: ${trading_metrics.current_balance:,.2f}")
        
    except Exception as e:
        print(f"❌ 交易指標收集失敗: {e}")
        return False
    
    return True

def test_alert_system():
    """測試警告系統"""
    print("\n⚠️ 測試警告系統...")
    
    try:
        # 創建測試警告
        realtime_monitor._create_alert('warning', 'test', '這是一個測試警告', {'test': True})
        realtime_monitor._create_alert('critical', 'test', '這是一個危險警告', {'test': True})
        
        if len(realtime_monitor.active_alerts) >= 2:
            print(f"✅ 警告創建成功 ({len(realtime_monitor.active_alerts)} 個警告)")
        else:
            print("❌ 警告創建失敗")
            return False
        
        # 測試警告確認
        success = realtime_monitor.acknowledge_alert(0)
        if success:
            print("✅ 警告確認成功")
        else:
            print("❌ 警告確認失敗")
            return False
            
    except Exception as e:
        print(f"❌ 警告系統測試失敗: {e}")
        return False
    
    return True

def test_health_score_calculation():
    """測試健康分數計算"""
    print("\n💊 測試健康分數計算...")
    
    try:
        # 創建測試指標
        from src.monitoring.realtime_monitor import SystemMetrics
        
        # 正常狀態
        normal_metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=30.0,
            memory_percent=50.0,
            disk_usage_gb=100.0,
            network_io_mb=10.0,
            active_threads=5,
            log_queue_size=10,
            error_count_1h=2,
            trading_signals_1h=5,
            system_uptime=3600.0
        )
        
        normal_score = realtime_monitor._calculate_health_score(normal_metrics)
        print(f"✅ 正常狀態健康分數: {normal_score}/100")
        
        # 高負載狀態
        high_load_metrics = SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=95.0,
            memory_percent=90.0,
            disk_usage_gb=100.0,
            network_io_mb=10.0,
            active_threads=20,
            log_queue_size=1500,
            error_count_1h=60,
            trading_signals_1h=5,
            system_uptime=3600.0
        )
        
        high_load_score = realtime_monitor._calculate_health_score(high_load_metrics)
        print(f"✅ 高負載狀態健康分數: {high_load_score}/100")
        
        if normal_score > high_load_score:
            print("✅ 健康分數計算邏輯正確")
        else:
            print("❌ 健康分數計算邏輯錯誤")
            return False
            
    except Exception as e:
        print(f"❌ 健康分數計算測試失敗: {e}")
        return False
    
    return True

def test_data_cleanup():
    """測試數據清理"""
    print("\n🧹 測試數據清理...")
    
    try:
        # 保存原始配置
        original_retention = realtime_monitor.config['history_retention']
        
        # 設置較小的保留數量進行測試
        realtime_monitor.config['history_retention'] = 3
        
        # 添加測試數據
        from src.monitoring.realtime_monitor import SystemMetrics, TradingMetrics
        
        for i in range(5):
            test_system_metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=50.0, memory_percent=60.0, disk_usage_gb=100.0,
                network_io_mb=10.0, active_threads=5, log_queue_size=10,
                error_count_1h=0, trading_signals_1h=0, system_uptime=3600.0
            )
            realtime_monitor.system_metrics_history.append(test_system_metrics)
        
        print(f"   添加了 5 個測試數據點")
        
        # 執行清理
        realtime_monitor._cleanup_old_data()
        
        if len(realtime_monitor.system_metrics_history) <= 3:
            print(f"✅ 數據清理成功 (保留 {len(realtime_monitor.system_metrics_history)} 個數據點)")
        else:
            print(f"❌ 數據清理失敗 (仍有 {len(realtime_monitor.system_metrics_history)} 個數據點)")
            return False
        
        # 恢復原始配置
        realtime_monitor.config['history_retention'] = original_retention
        
    except Exception as e:
        print(f"❌ 數據清理測試失敗: {e}")
        return False
    
    return True

def test_history_retrieval():
    """測試歷史數據檢索"""
    print("\n📈 測試歷史數據檢索...")
    
    try:
        # 確保有一些歷史數據
        if not realtime_monitor.system_metrics_history:
            # 添加一些測試數據
            from src.monitoring.realtime_monitor import SystemMetrics
            test_metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=45.0, memory_percent=65.0, disk_usage_gb=100.0,
                network_io_mb=10.0, active_threads=5, log_queue_size=10,
                error_count_1h=0, trading_signals_1h=0, system_uptime=3600.0
            )
            realtime_monitor.system_metrics_history.append(test_metrics)
        
        # 測試獲取歷史數據
        history = realtime_monitor.get_metrics_history(1)
        
        print(f"✅ 歷史數據檢索成功:")
        print(f"   系統指標數據點: {len(history['system_metrics'])}")
        print(f"   交易指標數據點: {len(history['trading_metrics'])}")
        print(f"   時間範圍: {history['time_range_hours']} 小時")
        
    except Exception as e:
        print(f"❌ 歷史數據檢索測試失敗: {e}")
        return False
    
    return True

def stress_test():
    """壓力測試"""
    print("\n🔥 執行壓力測試...")
    
    try:
        # 啟動監控
        realtime_monitor.start_monitoring()
        
        # 模擬高頻率請求
        print("   執行高頻率狀態查詢...")
        for i in range(20):
            status = realtime_monitor.get_current_status()
            if i % 5 == 0:
                print(f"   查詢 {i+1}/20 完成")
            time.sleep(0.1)
        
        print("✅ 高頻率查詢測試通過")
        
        # 測試並發訪問
        print("   測試並發訪問...")
        results = []
        
        def concurrent_request():
            try:
                status = realtime_monitor.get_current_status()
                results.append(True)
            except:
                results.append(False)
        
        threads = []
        for i in range(10):
            thread = threading.Thread(target=concurrent_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        success_rate = sum(results) / len(results) * 100
        print(f"✅ 並發訪問測試完成 (成功率: {success_rate:.1f}%)")
        
        # 停止監控
        realtime_monitor.stop_monitoring()
        
        if success_rate >= 90:
            return True
        else:
            print("❌ 並發訪問成功率過低")
            return False
            
    except Exception as e:
        print(f"❌ 壓力測試失敗: {e}")
        realtime_monitor.stop_monitoring()
        return False

def main():
    """主測試函數"""
    print("🚀 AImax 實時監控系統測試")
    print("=" * 50)
    
    test_results = []
    
    # 執行各項測試
    tests = [
        ("基本功能", test_basic_functionality),
        ("監控生命週期", test_monitoring_lifecycle),
        ("指標收集", test_metrics_collection),
        ("警告系統", test_alert_system),
        ("健康分數計算", test_health_score_calculation),
        ("數據清理", test_data_cleanup),
        ("歷史數據檢索", test_history_retrieval),
        ("壓力測試", stress_test)
    ]
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            test_results.append((test_name, result))
            
            if result:
                print(f"✅ {test_name} 通過")
            else:
                print(f"❌ {test_name} 失敗")
                
        except Exception as e:
            print(f"❌ {test_name} 執行錯誤: {e}")
            test_results.append((test_name, False))
    
    # 顯示測試結果摘要
    print("\n" + "=" * 50)
    print("📊 測試結果摘要")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"總測試數: {total}")
    print(f"通過數量: {passed}")
    print(f"失敗數量: {total - passed}")
    print(f"通過率: {passed/total*100:.1f}%")
    
    # 確保監控已停止
    if realtime_monitor.monitoring_active:
        realtime_monitor.stop_monitoring()
    
    # 顯示系統摘要
    print("\n" + "=" * 50)
    print("📋 最終系統摘要")
    print("=" * 50)
    try:
        summary = realtime_monitor.get_system_summary()
        print(summary)
    except Exception as e:
        print(f"無法獲取系統摘要: {e}")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    exit(main())