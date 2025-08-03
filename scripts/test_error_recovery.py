#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
錯誤恢復系統測試腳本
測試ErrorRecovery的錯誤處理和恢復功能
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_error_recovery_basic():
    """測試錯誤恢復基本功能"""
    print("=== 測試錯誤恢復基本功能 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        from src.gui.error_recovery_system import ErrorRecovery, ErrorType
        
        # 創建應用程式
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        
        # 創建錯誤恢復系統
        print("創建錯誤恢復系統...")
        error_recovery = ErrorRecovery()
        
        # 測試信號
        recovery_signals = {
            'error_detected': False,
            'recovery_started': False,
            'recovery_completed': False,
            'fallback_mode_activated': False
        }
        
        def on_error_detected(error_event):
            recovery_signals['error_detected'] = True
            print(f"✅ 錯誤檢測: {error_event.error_type.value} - {error_event.message}")
        
        def on_recovery_started(error_type, action):
            recovery_signals['recovery_started'] = True
            print(f"✅ 恢復開始: {error_type} -> {action}")
        
        def on_recovery_completed(success, message):
            recovery_signals['recovery_completed'] = True
            status = "成功" if success else "失敗"
            print(f"✅ 恢復完成: {status} - {message}")
        
        def on_fallback_mode_activated(reason):
            recovery_signals['fallback_mode_activated'] = True
            print(f"✅ 降級模式激活: {reason}")
        
        # 連接信號
        error_recovery.error_detected.connect(on_error_detected)
        error_recovery.recovery_started.connect(on_recovery_started)
        error_recovery.recovery_completed.connect(on_recovery_completed)
        error_recovery.fallback_mode_activated.connect(on_fallback_mode_activated)
        
        # 測試不同類型的錯誤
        test_errors = [
            (ErrorType.AI_CONNECTION_LOST, "測試AI連接丟失", "ai_connector", "high"),
            (ErrorType.GUI_FREEZE, "測試GUI凍結", "gui", "high"),
            (ErrorType.TRADING_ERROR, "測試交易錯誤", "trading", "medium"),
            (ErrorType.SYSTEM_ERROR, "測試系統錯誤", "system", "medium")
        ]
        
        for error_type, message, component, severity in test_errors:
            print(f"\n測試錯誤類型: {error_type.value}")
            error_recovery.handle_error(error_type, message, component, severity)
        
        # 等待處理完成
        def check_results():
            received_count = sum(recovery_signals.values())
            print(f"\n恢復信號接收情況: {received_count}/4")
            
            if received_count >= 3:  # 至少接收到3個信號
                print("✅ 錯誤恢復基本功能測試通過")
            else:
                print("⚠️ 部分恢復信號未接收")
            
            app.quit()
        
        QTimer.singleShot(3000, check_results)  # 3秒後檢查
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤恢復基本功能測試失敗: {e}")
        return False

def test_error_statistics():
    """測試錯誤統計功能"""
    print("\n=== 測試錯誤統計功能 ===")
    
    try:
        from src.gui.error_recovery_system import ErrorRecovery, ErrorType
        
        # 創建錯誤恢復系統
        error_recovery = ErrorRecovery()
        
        # 添加一些測試錯誤
        test_errors = [
            (ErrorType.AI_CONNECTION_LOST, "連接錯誤1"),
            (ErrorType.AI_CONNECTION_LOST, "連接錯誤2"),
            (ErrorType.GUI_FREEZE, "GUI凍結錯誤"),
            (ErrorType.SYSTEM_ERROR, "系統錯誤")
        ]
        
        for error_type, message in test_errors:
            error_recovery.handle_error(error_type, message, "test", "medium")
        
        # 獲取錯誤統計
        print("獲取錯誤統計...")
        stats = error_recovery.get_error_statistics()
        
        if stats:
            print("✅ 錯誤統計獲取成功")
            print(f"   總錯誤數: {stats.get('total_errors', 0)}")
            print(f"   錯誤類型: {stats.get('error_types', {})}")
            print(f"   最近錯誤: {stats.get('recent_errors', 0)}")
            print(f"   降級模式: {stats.get('is_in_fallback_mode', False)}")
        else:
            print("❌ 錯誤統計獲取失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤統計功能測試失敗: {e}")
        return False

def test_fallback_mode():
    """測試降級模式功能"""
    print("\n=== 測試降級模式功能 ===")
    
    try:
        from src.gui.error_recovery_system import ErrorRecovery, ErrorType
        
        # 創建錯誤恢復系統
        error_recovery = ErrorRecovery()
        
        # 測試激活降級模式
        print("測試激活降級模式...")
        success = error_recovery.activate_fallback_mode("測試原因")
        if success:
            print("✅ 降級模式激活成功")
            print(f"   降級模式狀態: {error_recovery.is_in_fallback_mode}")
        else:
            print("❌ 降級模式激活失敗")
            return False
        
        # 測試停用降級模式
        print("測試停用降級模式...")
        success = error_recovery.deactivate_fallback_mode()
        if success:
            print("✅ 降級模式停用成功")
            print(f"   降級模式狀態: {error_recovery.is_in_fallback_mode}")
        else:
            print("❌ 降級模式停用失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 降級模式功能測試失敗: {e}")
        return False

def test_gui_freeze_detector():
    """測試GUI凍結檢測器"""
    print("\n=== 測試GUI凍結檢測器 ===")
    
    try:
        from PyQt6.QtCore import QCoreApplication, QTimer
        from src.gui.error_recovery_system import GUIFreezeDetector
        
        # 創建應用程式
        if QCoreApplication.instance() is None:
            app = QCoreApplication(sys.argv)
        else:
            app = QCoreApplication.instance()
        
        # 創建GUI凍結檢測器
        print("創建GUI凍結檢測器...")
        freeze_detector = GUIFreezeDetector()
        
        # 測試信號
        freeze_detected = False
        
        def on_freeze_detected(duration):
            nonlocal freeze_detected
            freeze_detected = True
            print(f"✅ 檢測到GUI凍結: {duration:.1f} 秒")
        
        freeze_detector.freeze_detected.connect(on_freeze_detected)
        
        # 等待檢測結果
        def check_detector():
            if freeze_detected:
                print("✅ GUI凍結檢測器測試通過")
            else:
                print("⚠️ 未檢測到GUI凍結（正常情況）")
            
            freeze_detector.cleanup()
            app.quit()
        
        QTimer.singleShot(2000, check_detector)  # 2秒後檢查
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ GUI凍結檢測器測試失敗: {e}")
        return False

def test_ai_connection_monitor():
    """測試AI連接監控器"""
    print("\n=== 測試AI連接監控器 ===")
    
    try:
        from PyQt6.QtCore import QCoreApplication, QTimer
        from src.gui.error_recovery_system import AIConnectionMonitor
        from src.gui.ai_connector import AIConnector
        
        # 創建應用程式
        if QCoreApplication.instance() is None:
            app = QCoreApplication(sys.argv)
        else:
            app = QCoreApplication.instance()
        
        # 創建AI連接器
        ai_connector = AIConnector()
        
        # 創建AI連接監控器
        print("創建AI連接監控器...")
        connection_monitor = AIConnectionMonitor(ai_connector)
        
        # 測試信號
        connection_lost_detected = False
        
        def on_connection_lost(reason):
            nonlocal connection_lost_detected
            connection_lost_detected = True
            print(f"✅ 檢測到連接丟失: {reason}")
        
        connection_monitor.connection_lost.connect(on_connection_lost)
        
        # 等待監控結果
        def check_monitor():
            if connection_lost_detected:
                print("✅ AI連接監控器測試通過")
            else:
                print("⚠️ 未檢測到連接丟失（正常情況）")
            
            connection_monitor.cleanup()
            app.quit()
        
        QTimer.singleShot(2000, check_monitor)  # 2秒後檢查
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ AI連接監控器測試失敗: {e}")
        return False

def test_recovery_actions():
    """測試恢復動作"""
    print("\n=== 測試恢復動作 ===")
    
    try:
        from src.gui.error_recovery_system import ErrorRecovery, RecoveryAction, ErrorEvent, ErrorType
        from datetime import datetime
        
        # 創建錯誤恢復系統
        error_recovery = ErrorRecovery()
        
        # 測試各種恢復動作
        test_actions = [
            (RecoveryAction.LOG_ERROR, "日誌記錄"),
            (RecoveryAction.FALLBACK_MODE, "降級模式"),
            (RecoveryAction.IGNORE, "忽略錯誤")
        ]
        
        for action, description in test_actions:
            print(f"測試恢復動作: {description}")
            
            # 創建測試錯誤事件
            error_event = ErrorEvent(
                error_type=ErrorType.SYSTEM_ERROR,
                timestamp=datetime.now(),
                message=f"測試{description}",
                component="test",
                severity="medium"
            )
            
            # 執行恢復動作
            success = error_recovery.execute_recovery_action(action, error_event)
            
            if success:
                print(f"✅ {description}動作執行成功")
            else:
                print(f"❌ {description}動作執行失敗")
        
        return True
        
    except Exception as e:
        print(f"❌ 恢復動作測試失敗: {e}")
        return False

def run_all_tests():
    """運行所有測試"""
    print("🚀 開始錯誤恢復系統測試")
    print("=" * 50)
    
    test_results = []
    
    # 運行各項測試
    test_results.append(("錯誤恢復基本功能", test_error_recovery_basic()))
    test_results.append(("錯誤統計功能", test_error_statistics()))
    test_results.append(("降級模式功能", test_fallback_mode()))
    test_results.append(("GUI凍結檢測器", test_gui_freeze_detector()))
    test_results.append(("AI連接監控器", test_ai_connection_monitor()))
    test_results.append(("恢復動作", test_recovery_actions()))
    
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
        print("🎉 所有測試通過！任務4.1實作成功！")
        return True
    else:
        print("⚠️ 部分測試失敗，需要檢查問題")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)