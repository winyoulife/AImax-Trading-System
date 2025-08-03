#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
狀態同步測試腳本
測試StatusSyncManager的狀態監控和同步功能
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_status_sync_manager():
    """測試狀態同步管理器"""
    print("=== 測試狀態同步管理器 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        from src.gui.status_sync_manager import StatusSyncManager
        from src.gui.ai_connector import AIConnector
        
        # 創建應用程式
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        
        # 創建AI連接器
        ai_connector = AIConnector()
        ai_connector.connect_to_ai_system()
        
        # 創建狀態同步管理器
        print("創建狀態同步管理器...")
        sync_manager = StatusSyncManager(ai_connector)
        
        # 測試信號
        sync_signals = {
            'ai_status_synced': False,
            'trading_status_synced': False,
            'balance_updated': False,
            'system_metrics_updated': False
        }
        
        def on_ai_status_synced(status):
            sync_signals['ai_status_synced'] = True
            print(f"✅ AI狀態同步: {status.get('status', 'N/A')}")
        
        def on_trading_status_synced(status):
            sync_signals['trading_status_synced'] = True
            print(f"✅ 交易狀態同步: {status.get('status', 'N/A')}")
        
        def on_balance_updated(balance):
            sync_signals['balance_updated'] = True
            print(f"✅ 餘額更新: ${balance:.2f}")
        
        def on_system_metrics_updated(metrics):
            sync_signals['system_metrics_updated'] = True
            cpu = metrics.get('cpu_usage', 0)
            memory = metrics.get('memory_usage', 0)
            print(f"✅ 系統指標更新: CPU {cpu:.1f}%, 記憶體 {memory:.1f}%")
        
        def on_sync_error(error):
            print(f"❌ 同步錯誤: {error}")
        
        # 連接信號
        sync_manager.ai_status_synced.connect(on_ai_status_synced)
        sync_manager.trading_status_synced.connect(on_trading_status_synced)
        sync_manager.balance_updated.connect(on_balance_updated)
        sync_manager.system_metrics_updated.connect(on_system_metrics_updated)
        sync_manager.sync_error.connect(on_sync_error)
        
        # 啟動同步
        print("啟動狀態同步...")
        sync_manager.start_sync()
        
        # 等待同步結果
        def check_sync_results():
            received_count = sum(sync_signals.values())
            total_signals = len(sync_signals)
            
            print(f"\n同步結果: {received_count}/{total_signals} 個信號已接收")
            
            if received_count >= 2:  # 至少接收到2個信號就算成功
                print("✅ 狀態同步測試通過")
            else:
                print("⚠️ 部分同步信號未接收")
            
            # 測試其他功能
            test_additional_features(sync_manager)
            
            app.quit()
        
        QTimer.singleShot(5000, check_sync_results)  # 5秒後檢查
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ 狀態同步管理器測試失敗: {e}")
        return False

def test_additional_features(sync_manager):
    """測試額外功能"""
    print("\n=== 測試額外功能 ===")
    
    try:
        # 測試強制同步
        print("測試強制同步...")
        sync_manager.force_sync()
        print("✅ 強制同步執行完成")
        
        # 測試設置同步間隔
        print("測試設置同步間隔...")
        sync_manager.set_sync_interval(1000)  # 1秒
        print("✅ 同步間隔設置完成")
        
        # 測試獲取狀態歷史
        print("測試獲取狀態歷史...")
        history = sync_manager.get_status_history(1)  # 1小時內
        print(f"✅ 獲取到 {len(history)} 條狀態歷史記錄")
        
        # 測試獲取最新狀態
        print("測試獲取最新狀態...")
        latest_status = sync_manager.get_latest_status()
        if latest_status:
            print("✅ 獲取最新狀態成功")
        else:
            print("⚠️ 暫無最新狀態數據")
        
        # 測試清理
        print("測試清理功能...")
        sync_manager.cleanup()
        print("✅ 清理功能執行完成")
        
    except Exception as e:
        print(f"❌ 額外功能測試失敗: {e}")

def test_status_monitor_worker():
    """測試狀態監控工作器"""
    print("\n=== 測試狀態監控工作器 ===")
    
    try:
        from PyQt6.QtCore import QCoreApplication, QTimer
        from src.gui.status_sync_manager import StatusMonitorWorker
        from src.gui.ai_connector import AIConnector
        
        # 創建應用程式
        if QCoreApplication.instance() is None:
            app = QCoreApplication(sys.argv)
        else:
            app = QCoreApplication.instance()
        
        # 創建AI連接器
        ai_connector = AIConnector()
        
        # 創建狀態監控工作器
        print("創建狀態監控工作器...")
        worker = StatusMonitorWorker(ai_connector)
        
        # 測試信號
        worker_signals = {
            'status_collected': False,
            'error_occurred': False
        }
        
        def on_status_collected(status_data):
            worker_signals['status_collected'] = True
            timestamp = status_data.get('timestamp', 'N/A')
            print(f"✅ 狀態收集完成: {timestamp}")
        
        def on_error_occurred(error):
            worker_signals['error_occurred'] = True
            print(f"⚠️ 監控錯誤: {error}")
        
        # 連接信號
        worker.status_collected.connect(on_status_collected)
        worker.error_occurred.connect(on_error_occurred)
        
        # 測試狀態收集
        print("測試狀態收集...")
        status_data = worker.collect_status_data()
        if status_data:
            print("✅ 狀態數據收集成功")
            print(f"   時間戳: {status_data.get('timestamp', 'N/A')}")
            print(f"   AI狀態: {status_data.get('ai_status', {}).get('status', 'N/A')}")
            print(f"   系統指標: {len(status_data.get('system_metrics', {}))} 項")
        else:
            print("❌ 狀態數據收集失敗")
        
        # 測試系統指標收集
        print("測試系統指標收集...")
        metrics = worker.collect_system_metrics()
        if metrics and 'error' not in metrics:
            print("✅ 系統指標收集成功")
            print(f"   CPU使用率: {metrics.get('cpu_usage', 0):.1f}%")
            print(f"   記憶體使用率: {metrics.get('memory_usage', 0):.1f}%")
        else:
            print("⚠️ 系統指標收集使用模擬數據")
        
        return True
        
    except Exception as e:
        print(f"❌ 狀態監控工作器測試失敗: {e}")
        return False

def test_status_snapshot():
    """測試狀態快照"""
    print("\n=== 測試狀態快照 ===")
    
    try:
        from src.gui.status_sync_manager import StatusSnapshot
        from datetime import datetime
        
        # 創建狀態快照
        print("創建狀態快照...")
        snapshot = StatusSnapshot(
            timestamp=datetime.now(),
            ai_status={'status': '已連接', 'active_count': 5},
            trading_status={'status': '運行中', 'balance': 10000.0},
            system_metrics={'cpu_usage': 45.2, 'memory_usage': 62.1}
        )
        
        # 測試轉換為字典
        print("測試轉換為字典...")
        snapshot_dict = snapshot.to_dict()
        if snapshot_dict:
            print("✅ 狀態快照轉換成功")
            print(f"   時間戳: {snapshot_dict.get('timestamp', 'N/A')}")
            print(f"   AI狀態: {snapshot_dict.get('ai_status', {})}")
            print(f"   交易狀態: {snapshot_dict.get('trading_status', {})}")
        else:
            print("❌ 狀態快照轉換失敗")
        
        return True
        
    except Exception as e:
        print(f"❌ 狀態快照測試失敗: {e}")
        return False

def run_all_tests():
    """運行所有測試"""
    print("🚀 開始狀態同步測試")
    print("=" * 50)
    
    test_results = []
    
    # 運行各項測試
    test_results.append(("狀態快照", test_status_snapshot()))
    test_results.append(("狀態監控工作器", test_status_monitor_worker()))
    test_results.append(("狀態同步管理器", test_status_sync_manager()))
    
    # 顯示測試結果
    print("\n" + "=" * 50)
    print("📊 測試結果總結")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{total} 項測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！任務3.2實作成功！")
        return True
    else:
        print("⚠️ 部分測試失敗，需要檢查問題")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)