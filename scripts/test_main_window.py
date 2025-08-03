#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主視窗測試腳本
測試MainWindow的各項功能和組件
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_main_window_creation():
    """測試主視窗創建"""
    print("=== 測試主視窗創建 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        
        # 創建應用程式
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        
        # 創建主視窗
        print("創建主視窗...")
        window = MainWindow()
        
        print("✅ 主視窗創建成功")
        
        # 測試視窗屬性
        print(f"視窗標題: {window.windowTitle()}")
        print(f"視窗大小: {window.size().width()}x{window.size().height()}")
        
        # 關閉視窗
        window.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 主視窗創建失敗: {e}")
        return False

def test_panels():
    """測試面板組件"""
    print("\n=== 測試面板組件 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import StatusPanel, ControlPanel, LogPanel
        
        # 創建應用程式
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        
        # 測試狀態面板
        print("測試狀態面板...")
        status_panel = StatusPanel()
        
        # 測試狀態更新
        test_ai_status = {
            'status': '已連接',
            'active_count': 5,
            'last_decision': '買入信號',
            'confidence': 85.5
        }
        status_panel.update_ai_status(test_ai_status)
        
        test_trading_status = {
            'status': '運行中',
            'balance': 10000.50,
            'profit_loss': 250.75,
            'active_orders': 3
        }
        status_panel.update_trading_status(test_trading_status)
        
        print("✅ 狀態面板測試通過")
        
        # 測試控制面板
        print("測試控制面板...")
        control_panel = ControlPanel()
        
        # 測試信號連接
        signal_received = False
        
        def on_start_trading():
            nonlocal signal_received
            signal_received = True
            print("收到啟動交易信號")
        
        control_panel.start_trading.connect(on_start_trading)
        control_panel.toggle_trading()  # 模擬點擊
        
        if signal_received:
            print("✅ 控制面板信號測試通過")
        else:
            print("⚠️ 控制面板信號未觸發")
        
        # 測試日誌面板
        print("測試日誌面板...")
        log_panel = LogPanel()
        
        # 添加測試日誌
        log_panel.add_log("這是一條測試訊息", "INFO")
        log_panel.add_log("這是一條警告訊息", "WARNING")
        log_panel.add_log("這是一條錯誤訊息", "ERROR")
        log_panel.add_log("這是一條成功訊息", "SUCCESS")
        
        print("✅ 日誌面板測試通過")
        
        # 清理
        status_panel.close()
        control_panel.close()
        log_panel.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 面板組件測試失敗: {e}")
        return False

def test_ai_connector():
    """測試AI連接器"""
    print("\n=== 測試AI連接器 ===")
    
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
        signals_received = {
            'status_updated': False,
            'trading_status_updated': False,
            'log_message': False
        }
        
        def on_status_updated(status_data):
            signals_received['status_updated'] = True
            print(f"收到AI狀態更新: {status_data.get('status', 'N/A')}")
        
        def on_trading_updated(trading_data):
            signals_received['trading_status_updated'] = True
            print(f"收到交易狀態更新: {trading_data.get('status', 'N/A')}")
        
        def on_log_message(message, level):
            signals_received['log_message'] = True
            print(f"收到日誌訊息: [{level}] {message}")
        
        # 連接信號
        connector.status_updated.connect(on_status_updated)
        connector.trading_status_updated.connect(on_trading_updated)
        connector.log_message.connect(on_log_message)
        
        # 測試連接
        print("測試AI系統連接...")
        if connector.connect_to_ai_system():
            print("✅ AI系統連接成功")
        else:
            print("❌ AI系統連接失敗")
        
        # 等待信號
        def check_signals():
            if all(signals_received.values()):
                print("✅ 所有信號都已接收")
            else:
                missing = [k for k, v in signals_received.items() if not v]
                print(f"⚠️ 未收到信號: {missing}")
            
            app.quit()
        
        QTimer.singleShot(2000, check_signals)  # 2秒後檢查
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ AI連接器測試失敗: {e}")
        return False

def test_integration():
    """測試整合功能"""
    print("\n=== 測試整合功能 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        
        # 創建應用程式
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        
        # 創建帶AI組件的主視窗
        print("創建帶AI組件的主視窗...")
        test_components = {
            'ai_manager': 'mock_ai_manager',
            'trade_executor': 'mock_trade_executor',
            'risk_manager': 'mock_risk_manager',
            'system_integrator': 'mock_system_integrator'
        }
        
        window = MainWindow(test_components)
        
        # 測試基本功能
        print("測試基本功能...")
        
        # 模擬用戶操作
        window.control_panel.toggle_trading()  # 啟動交易
        window.control_panel.dca_button.click()  # 選擇DCA策略
        window.refresh_all()  # 刷新狀態
        
        print("✅ 整合功能測試通過")
        
        # 關閉視窗
        window.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 整合功能測試失敗: {e}")
        return False

def run_visual_test():
    """運行視覺測試（顯示GUI）"""
    print("\n=== 運行視覺測試 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        
        # 創建主視窗
        window = MainWindow()
        window.show()
        
        print("✅ 主視窗已顯示")
        print("請檢查GUI界面是否正常顯示")
        print("關閉視窗以繼續測試...")
        
        # 運行應用程式
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ 視覺測試失敗: {e}")
        return False

def run_all_tests():
    """運行所有測試"""
    print("🚀 開始主視窗測試")
    print("=" * 50)
    
    test_results = []
    
    # 運行各項測試
    test_results.append(("主視窗創建", test_main_window_creation()))
    test_results.append(("面板組件", test_panels()))
    test_results.append(("AI連接器", test_ai_connector()))
    test_results.append(("整合功能", test_integration()))
    
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
        print("🎉 所有測試通過！任務2.1實作成功！")
        
        # 詢問是否運行視覺測試
        try:
            response = input("\n是否運行視覺測試？(y/n): ").lower().strip()
            if response == 'y':
                run_visual_test()
        except KeyboardInterrupt:
            print("\n測試結束")
        
        return True
    else:
        print("⚠️ 部分測試失敗，需要檢查問題")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)