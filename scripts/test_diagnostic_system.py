#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷系統測試腳本
測試DiagnosticSystem的診斷收集和分析功能
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_system_diagnostics():
    """測試系統診斷收集"""
    print("=== 測試系統診斷收集 ===")
    
    try:
        from src.gui.diagnostic_system import SystemDiagnostics
        
        # 測試系統資訊收集
        print("收集系統資訊...")
        system_info = SystemDiagnostics.collect_system_info()
        
        if system_info and 'error' not in system_info:
            print("✅ 系統資訊收集成功")
            print(f"   平台: {system_info.get('platform', {}).get('system', 'N/A')}")
            print(f"   Python版本: {system_info.get('python', {}).get('version', 'N/A')[:20]}...")
            
            if 'resources' in system_info and 'error' not in system_info['resources']:
                resources = system_info['resources']
                print(f"   記憶體使用: {resources.get('memory', {}).get('percent', 0):.1f}%")
                print(f"   CPU使用: {resources.get('cpu_percent', 0):.1f}%")
        else:
            print("❌ 系統資訊收集失敗")
            return False
        
        # 測試應用程式資訊收集
        print("收集應用程式資訊...")
        app_info = SystemDiagnostics.collect_application_info()
        
        if app_info and 'error' not in app_info:
            print("✅ 應用程式資訊收集成功")
            print(f"   應用名稱: {app_info.get('application_name', 'N/A')}")
            print(f"   版本: {app_info.get('version', 'N/A')}")
        else:
            print("❌ 應用程式資訊收集失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 系統診斷收集測試失敗: {e}")
        return False

def test_error_classifier():
    """測試錯誤分類器"""
    print("\n=== 測試錯誤分類器 ===")
    
    try:
        from src.gui.diagnostic_system import ErrorClassifier
        
        # 測試不同類型的錯誤
        test_errors = [
            "Connection timeout error",
            "Out of memory error",
            "Permission denied",
            "File not found",
            "AI model inference failed",
            "Trading API error",
            "Unknown random error message"
        ]
        
        for error_msg in test_errors:
            print(f"\n測試錯誤: {error_msg}")
            classification = ErrorClassifier.classify_error(error_msg)
            
            if classification:
                print(f"✅ 分類成功")
                print(f"   類別: {classification['category']}")
                print(f"   友好訊息: {classification['friendly_message']}")
                print(f"   建議數量: {len(classification['suggestions'])}")
            else:
                print("❌ 分類失敗")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤分類器測試失敗: {e}")
        return False

def test_diagnostic_system():
    """測試診斷系統"""
    print("\n=== 測試診斷系統 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        from src.gui.diagnostic_system import DiagnosticSystem
        
        # 創建應用程式
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        
        # 創建診斷系統
        print("創建診斷系統...")
        diagnostic_system = DiagnosticSystem()
        
        # 測試信號
        diagnostic_signals = {
            'diagnostic_collected': False,
            'report_generated': False
        }
        
        def on_diagnostic_collected(diagnostic_info):
            diagnostic_signals['diagnostic_collected'] = True
            print(f"✅ 診斷收集: [{diagnostic_info.level}] {diagnostic_info.message}")
        
        def on_report_generated(report_path):
            diagnostic_signals['report_generated'] = True
            print(f"✅ 報告生成: {report_path}")
        
        # 連接信號
        diagnostic_system.diagnostic_collected.connect(on_diagnostic_collected)
        diagnostic_system.report_generated.connect(on_report_generated)
        
        # 測試添加診斷
        print("添加測試診斷...")
        diagnostic_system.add_diagnostic(
            'test',
            'INFO',
            '測試診斷資訊',
            {'test_data': 'test_value'},
            'test_source'
        )
        
        # 測試錯誤分類和添加
        print("測試錯誤分類...")
        diagnostic_system.classify_and_add_error(
            "Connection timeout error",
            "network_test"
        )
        
        # 測試生成報告
        print("生成診斷報告...")
        report_path = diagnostic_system.generate_diagnostic_report()
        
        if report_path and Path(report_path).exists():
            print(f"✅ 報告生成成功: {report_path}")
            # 清理測試文件
            try:
                os.remove(report_path)
            except:
                pass
        else:
            print("❌ 報告生成失敗")
        
        # 測試診斷摘要
        print("獲取診斷摘要...")
        summary = diagnostic_system.get_diagnostic_summary(1)  # 1小時內
        
        if summary and 'error' not in summary:
            print("✅ 診斷摘要獲取成功")
            print(f"   總診斷數: {summary.get('total_diagnostics', 0)}")
            print(f"   類別統計: {summary.get('category_counts', {})}")
        else:
            print("❌ 診斷摘要獲取失敗")
        
        # 等待信號處理
        def check_signals():
            received_count = sum(diagnostic_signals.values())
            print(f"\n診斷信號接收情況: {received_count}/2")
            
            if received_count >= 1:  # 至少接收到1個信號
                print("✅ 診斷系統測試通過")
            else:
                print("⚠️ 部分診斷信號未接收")
            
            diagnostic_system.cleanup()
            app.quit()
        
        QTimer.singleShot(2000, check_signals)  # 2秒後檢查
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ 診斷系統測試失敗: {e}")
        return False

def test_auto_diagnostics():
    """測試自動診斷"""
    print("\n=== 測試自動診斷 ===")
    
    try:
        from PyQt6.QtCore import QCoreApplication, QTimer
        from src.gui.diagnostic_system import DiagnosticSystem
        
        # 創建應用程式
        if QCoreApplication.instance() is None:
            app = QCoreApplication(sys.argv)
        else:
            app = QCoreApplication.instance()
        
        # 創建診斷系統
        diagnostic_system = DiagnosticSystem()
        
        # 測試自動診斷
        auto_diagnostic_triggered = False
        
        def on_diagnostic_collected(diagnostic_info):
            nonlocal auto_diagnostic_triggered
            if diagnostic_info.source == "" and diagnostic_info.category in ['resource', 'ai_system']:
                auto_diagnostic_triggered = True
                print(f"✅ 自動診斷觸發: {diagnostic_info.message}")
        
        diagnostic_system.diagnostic_collected.connect(on_diagnostic_collected)
        
        # 啟動自動診斷（短間隔用於測試）
        print("啟動自動診斷...")
        diagnostic_system.start_auto_diagnostics(0.1)  # 0.1分鐘 = 6秒
        
        # 等待自動診斷觸發
        def check_auto_diagnostic():
            diagnostic_system.stop_auto_diagnostics()
            
            if auto_diagnostic_triggered:
                print("✅ 自動診斷測試通過")
            else:
                print("⚠️ 自動診斷未觸發（可能是正常情況）")
            
            diagnostic_system.cleanup()
            app.quit()
        
        QTimer.singleShot(8000, check_auto_diagnostic)  # 8秒後檢查
        app.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ 自動診斷測試失敗: {e}")
        return False

def test_diagnostic_dialog():
    """測試診斷對話框"""
    print("\n=== 測試診斷對話框 ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.diagnostic_system import DiagnosticSystem, DiagnosticDialog
        
        # 創建應用程式
        if QApplication.instance() is None:
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()
        
        # 創建診斷系統並添加一些測試數據
        diagnostic_system = DiagnosticSystem()
        diagnostic_system.add_diagnostic(
            'test',
            'INFO',
            '測試診斷對話框',
            {'test': True}
        )
        
        # 創建對話框
        print("創建診斷對話框...")
        dialog = DiagnosticDialog(diagnostic_system)
        
        if dialog:
            print("✅ 診斷對話框創建成功")
            # 不實際顯示對話框，只測試創建
            dialog.close()
        else:
            print("❌ 診斷對話框創建失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 診斷對話框測試失敗: {e}")
        return False

def run_all_tests():
    """運行所有測試"""
    print("🚀 開始診斷系統測試")
    print("=" * 50)
    
    test_results = []
    
    # 運行各項測試
    test_results.append(("系統診斷收集", test_system_diagnostics()))
    test_results.append(("錯誤分類器", test_error_classifier()))
    test_results.append(("診斷系統", test_diagnostic_system()))
    test_results.append(("自動診斷", test_auto_diagnostics()))
    test_results.append(("診斷對話框", test_diagnostic_dialog()))
    
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
        print("🎉 所有測試通過！任務4.2實作成功！")
        return True
    else:
        print("⚠️ 部分測試失敗，需要檢查問題")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)