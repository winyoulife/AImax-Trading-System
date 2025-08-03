#!/usr/bin/env python3
"""
AImax GUI最小化測試 - 避免卡住問題的簡化版本
"""
import sys
import logging
import signal
import time
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def signal_handler(signum, frame):
    """信號處理器"""
    print("\n⏹️ 收到中斷信號，正在退出...")
    sys.exit(0)

def test_minimal_gui():
    """測試最小化GUI"""
    print("🧪 測試最小化GUI...")
    
    try:
        # 檢查PyQt6
        try:
            from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
            from PyQt6.QtCore import QTimer
            print("✅ PyQt6導入成功")
        except ImportError:
            print("⚠️ PyQt6未安裝，跳過GUI測試")
            return True
        
        # 創建最小化應用程序
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # 創建簡單窗口
        window = QMainWindow()
        window.setWindowTitle("AImax 最小化測試")
        window.setGeometry(100, 100, 400, 300)
        
        # 中央組件
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # 添加標籤
        label = QLabel("AImax GUI 最小化測試")
        label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 20px;")
        layout.addWidget(label)
        
        status_label = QLabel("狀態: 測試運行中...")
        layout.addWidget(status_label)
        
        window.setCentralWidget(central_widget)
        
        # 創建定時器自動關閉窗口
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: (
            status_label.setText("狀態: 測試完成，即將關閉..."),
            QTimer.singleShot(1000, app.quit)
        ))
        timer.start(3000)  # 3秒後關閉
        
        # 顯示窗口
        window.show()
        print("✅ 窗口已顯示，將在3秒後自動關閉")
        
        # 運行事件循環（有超時保護）
        start_time = time.time()
        while time.time() - start_time < 5:  # 最多運行5秒
            app.processEvents()
            if not window.isVisible():
                break
            time.sleep(0.01)
        
        print("✅ GUI測試完成")
        return True
        
    except Exception as e:
        print(f"❌ GUI測試失敗: {e}")
        return False

def test_component_creation():
    """測試組件創建（不啟動）"""
    print("\n🧪 測試組件創建...")
    
    try:
        from src.gui.component_manager import ComponentManager
        from src.gui.error_handler import ErrorHandler
        from src.gui.state_manager import StateManager
        
        # 創建組件（不初始化）
        component_manager = ComponentManager()
        error_handler = ErrorHandler()
        state_manager = StateManager("test_temp.json")
        
        print("✅ 核心組件創建成功")
        
        # 測試基本功能
        state_manager.set_global_state("test_key", "test_value")
        value = state_manager.get_global_state("test_key")
        
        if value == "test_value":
            print("✅ 狀態管理功能正常")
        else:
            print("❌ 狀態管理功能異常")
            return False
        
        # 清理
        try:
            import os
            if os.path.exists("test_temp.json"):
                os.remove("test_temp.json")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ 組件創建測試失敗: {e}")
        return False

def test_monitoring_components():
    """測試監控組件（不啟動線程）"""
    print("\n🧪 測試監控組件...")
    
    try:
        from src.gui.monitoring_dashboard import SystemMonitorThread
        
        # 創建監控線程（不啟動）
        monitor = SystemMonitorThread()
        print("✅ 監控線程創建成功")
        
        # 初始化組件
        monitor.initialize_components()
        print("✅ 監控組件初始化完成")
        
        # 測試數據收集（單次）
        performance_data = monitor._collect_performance_data()
        if performance_data and "system" in performance_data:
            cpu_percent = performance_data["system"].get("cpu_percent", 0)
            memory_percent = performance_data["system"].get("memory_percent", 0)
            print(f"✅ 性能數據收集成功: CPU {cpu_percent:.1f}%, 內存 {memory_percent:.1f}%")
        else:
            print("⚠️ 性能數據收集返回空數據")
        
        # 確保線程未啟動
        if not monitor.isRunning():
            print("✅ 監控線程未啟動（符合預期）")
        else:
            print("⚠️ 監控線程意外啟動")
        
        return True
        
    except Exception as e:
        print(f"❌ 監控組件測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 開始 AImax GUI 最小化測試")
    print("=" * 50)
    print("💡 這是一個安全的最小化測試，不會卡住")
    print("💡 按 Ctrl+C 可隨時中斷")
    print("=" * 50)
    
    # 設置信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 設置日誌
    logging.basicConfig(level=logging.WARNING)
    
    test_results = []
    
    # 執行測試
    test_results.append(("組件創建", test_component_creation()))
    test_results.append(("監控組件", test_monitoring_components()))
    test_results.append(("最小化GUI", test_minimal_gui()))
    
    # 輸出結果
    print("\n" + "=" * 50)
    print("📊 最小化測試結果:")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name:15} : {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("🎉 所有最小化測試通過！")
        print("\n💡 下一步建議:")
        print("   1. 可以嘗試運行完整GUI: python AImax/scripts/run_gui.py")
        print("   2. 如果仍然卡住，問題可能在於:")
        print("      - 監控線程的事件循環")
        print("      - PyQt6的信號槽機制")
        print("      - 系統資源監控")
    else:
        print("⚠️ 部分測試失敗，建議先修復基礎問題")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 測試異常: {e}")
        sys.exit(1)