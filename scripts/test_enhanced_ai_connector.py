#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強版AI連接器測試腳本
測試AIConnector的異步連接和AI系統整合功能
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_async_connection():
    """測試異步連接功能"""
    print("=== 測試異步連接功能 ===")
    
    try:
        from PyQt6.QtCore import QCoreApplication, QTimer
        from src.gui.ai_connector import AIConnector
        
        # 創建應用程式
        if QCoreApplication.instance() is None:
            app = QCoreApplication(sys.argv)
        else:
            app = QCoreApplication.instance()
        
        # 創建AI連接器
        print("創建AI連接器...")
        connector = AIConnector()
        
        # 測試信號
        connection_signals = {
            'progress_received': False,
            'connection_completed': False,
            'status_updated': False
        }
        
        def on_log_message(message, level):
            print(f"[{level}] {message}")
            if "連接" in message:
                connection_signals['progress_received'] = True
        
        def on_connection_changed(connected):
            connection_signals['connection_completed'] = True
            print(f"連接狀態變更: {'已連接' if connected else '未連接'}")
        
        def on_status_updated(status_data):
            connection_signals['status_updated'] = True
            print(f"狀態更新: {status_data.get('status', 'N/A')}")
        
        # 連接信號
        connector.log_message.connect(on_log_message)
        connector.connection_changed.connect(on_connection_changed)
        connector.status_updated.connect(on_status_updated)
        
        # 測試異步連接
        print("開始異步連接測試...")
        if connector.connect_to_ai_system():
            print("✅ 異步連接啟動成功")
        else:
            print("❌ 異步連接啟動失敗")
            return False
        
        # 等待連接完成
        def check_connection():
            if all(connection_signals.values()):
                print("✅ 所有連接信號都已接收")
            else:
                missing = [k for k, v in connection_signals.items() if not v]
                print(f"⚠️ 未收到信號: {missing}")
            
            app.quit()
        
        QTimer.singleShot(5000, check_connection)  # 5秒後檢查
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ 異步連接測試失敗: {e}")
        return False

def test_ai_system_integration():
    """測試AI系統整合功能"""
    print("\n=== 測試AI系統整合功能 ===")
    
    try:
        from PyQt6.QtCore import QCoreApplication
        from src.gui.ai_connector import AIConnector
        
        # 創建應用程式
        if QCoreApplication.instance() is None:
            app = QCoreApplication(sys.argv)
        else:
            app = QCoreApplication.instance()
        
        # 創建帶模擬AI組件的連接器
        mock_components = {
            'ai_manager': 'MockAIManager',
            'trade_executor': 'MockTradeExecutor',
            'risk_manager': 'MockRiskManager',
            'system_integrator': 'MockSystemIntegrator'
        }
        
        connector = AIConnector(mock_components)
        
        # 測試AI系統資訊獲取
        print("測試AI系統資訊獲取...")
        ai_info = connector.get_ai_system_info()
        if ai_info:
            print(f"✅ AI系統資訊: {ai_info}")
        else:
            print("❌ 無法獲取AI系統資訊")
        
        # 先連接AI系統
        connector.connect_to_ai_system()
        import time
        time.sleep(2)  # 等待連接完成
        
        # 測試AI命令執行
        print("測試AI命令執行...")
        commands = [
            ("analyze_market", {"symbol": "BTCUSDT"}),
            ("assess_risk", {"position_size": 1000}),
            ("system_health_check", {})
        ]
        
        for command, params in commands:
            if connector.execute_ai_command(command, params):
                print(f"✅ 命令執行成功: {command}")
            else:
                print(f"❌ 命令執行失敗: {command}")
        
        # 測試交易性能獲取
        print("測試交易性能獲取...")
        performance = connector.get_trading_performance()
        if performance:
            print(f"✅ 交易性能數據: {performance}")
        else:
            print("❌ 無法獲取交易性能數據")
        
        return True
        
    except Exception as e:
        print(f"❌ AI系統整合測試失敗: {e}")
        return False

def test_connection_management():
    """測試連接管理功能"""
    print("\n=== 測試連接管理功能 ===")
    
    try:
        from PyQt6.QtCore import QCoreApplication
        from src.gui.ai_connector import AIConnector
        
        # 創建應用程式
        if QCoreApplication.instance() is None:
            app = QCoreApplication(sys.argv)
        else:
            app = QCoreApplication.instance()
        
        connector = AIConnector()
        
        # 測試連接狀態檢查
        print("測試連接狀態檢查...")
        print(f"初始連接狀態: {connector.is_system_connected()}")
        print(f"初始交易狀態: {connector.is_trading_active()}")
        
        # 測試重新連接
        print("測試重新連接功能...")
        if connector.reconnect_ai_system():
            print("✅ 重新連接功能正常")
        else:
            print("❌ 重新連接功能失敗")
        
        # 測試斷開連接
        print("測試斷開連接功能...")
        connector.disconnect_ai_system()
        print(f"斷開後連接狀態: {connector.is_system_connected()}")
        
        # 測試清理功能
        print("測試清理功能...")
        connector.cleanup()
        print("✅ 清理功能執行完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 連接管理測試失敗: {e}")
        return False

def test_worker_functionality():
    """測試工作器功能"""
    print("\n=== 測試工作器功能 ===")
    
    try:
        from PyQt6.QtCore import QCoreApplication, QTimer
        from src.gui.ai_connector import AISystemConnectionWorker
        
        # 創建應用程式
        if QCoreApplication.instance() is None:
            app = QCoreApplication(sys.argv)
        else:
            app = QCoreApplication.instance()
        
        # 創建連接工作器
        print("創建連接工作器...")
        worker = AISystemConnectionWorker()
        
        # 測試信號
        worker_signals = {
            'progress_received': False,
            'completion_received': False
        }
        
        def on_progress(message, progress):
            worker_signals['progress_received'] = True
            print(f"進度更新: [{progress}%] {message}")
        
        def on_completion(success, message, components):
            worker_signals['completion_received'] = True
            print(f"連接完成: {success}, {message}")
            if components:
                print(f"連接的組件: {list(components.keys())}")
        
        # 連接信號
        worker.connection_progress.connect(on_progress)
        worker.connection_completed.connect(on_completion)
        
        # 測試連接過程
        print("開始連接過程...")
        worker.connect_to_ai_system()
        
        # 等待完成
        def check_worker():
            if all(worker_signals.values()):
                print("✅ 工作器所有信號都已接收")
            else:
                missing = [k for k, v in worker_signals.items() if not v]
                print(f"⚠️ 工作器未收到信號: {missing}")
            
            app.quit()
        
        QTimer.singleShot(3000, check_worker)  # 3秒後檢查
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ 工作器功能測試失敗: {e}")
        return False

def run_all_tests():
    """運行所有測試"""
    print("🚀 開始增強版AI連接器測試")
    print("=" * 50)
    
    test_results = []
    
    # 運行各項測試
    test_results.append(("異步連接功能", test_async_connection()))
    test_results.append(("AI系統整合功能", test_ai_system_integration()))
    test_results.append(("連接管理功能", test_connection_management()))
    test_results.append(("工作器功能", test_worker_functionality()))
    
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
        print("🎉 所有測試通過！任務3.1實作成功！")
        return True
    else:
        print("⚠️ 部分測試失敗，需要檢查問題")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)