#!/usr/bin/env python3
"""
AImax GUI安全測試腳本 - 避免卡住問題
"""
import sys
import logging
import signal
import threading
import time
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 全局變量用於控制測試
test_running = True
test_timeout = 30  # 30秒超時

def signal_handler(signum, frame):
    """信號處理器"""
    global test_running
    print("\n⏹️ 收到中斷信號，正在停止測試...")
    test_running = False
    sys.exit(0)

def timeout_handler():
    """超時處理器"""
    global test_running
    time.sleep(test_timeout)
    if test_running:
        print(f"\n⏰ 測試超時 ({test_timeout}秒)，強制退出")
        test_running = False
        sys.exit(1)

def safe_test_imports():
    """安全測試導入"""
    print("🧪 測試模塊導入...")
    
    try:
        # 測試基本導入
        from src.gui.component_manager import ComponentManager
        print("✅ ComponentManager 導入成功")
        
        from src.gui.error_handler import ErrorHandler
        print("✅ ErrorHandler 導入成功")
        
        from src.gui.state_manager import StateManager
        print("✅ StateManager 導入成功")
        
        # 測試監控組件（可能有問題的部分）
        try:
            from src.gui.monitoring_dashboard import SystemMonitorThread
            print("✅ SystemMonitorThread 導入成功")
        except Exception as e:
            print(f"⚠️ SystemMonitorThread 導入失敗: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 模塊導入失敗: {e}")
        return False

def safe_test_component_manager():
    """安全測試組件管理器"""
    print("\n🧪 測試組件管理器...")
    
    try:
        from src.gui.component_manager import ComponentManager
        
        manager = ComponentManager(max_retries=1)  # 減少重試次數
        print("✅ 組件管理器創建成功")
        
        # 簡單測試組件
        class SimpleTestComponent:
            def __init__(self):
                self.status = "ready"
        
        success = manager.register_component("simple_test", SimpleTestComponent)
        if not success:
            print("❌ 組件註冊失敗")
            return False
        
        print("✅ 組件註冊成功")
        return True
        
    except Exception as e:
        print(f"❌ 組件管理器測試失敗: {e}")
        return False

def safe_test_monitoring_thread():
    """安全測試監控線程（不啟動）"""
    print("\n🧪 測試監控線程（僅創建，不啟動）...")
    
    try:
        from src.gui.monitoring_dashboard import SystemMonitorThread
        
        # 只創建，不啟動線程
        monitor = SystemMonitorThread()
        print("✅ 監控線程創建成功")
        
        # 測試初始化組件
        monitor.initialize_components()
        print("✅ 監控組件初始化完成")
        
        # 測試數據收集方法（不在線程中運行）
        try:
            performance_data = monitor._collect_performance_data()
            if performance_data:
                print("✅ 性能數據收集測試成功")
            else:
                print("⚠️ 性能數據收集返回空數據")
        except Exception as e:
            print(f"⚠️ 性能數據收集測試失敗: {e}")
        
        # 確保不啟動線程
        monitor.running = False
        print("✅ 監控線程測試完成（未啟動實際監控）")
        
        return True
        
    except Exception as e:
        print(f"❌ 監控線程測試失敗: {e}")
        return False

def safe_test_pyqt_availability():
    """安全測試PyQt6可用性"""
    print("\n🧪 測試PyQt6可用性...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        
        # 創建應用程序實例（但不運行事件循環）
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        print("✅ PyQt6應用程序創建成功")
        
        # 測試定時器創建（但不啟動）
        timer = QTimer()
        timer.setSingleShot(True)
        timer.setInterval(100)
        print("✅ PyQt6定時器創建成功")
        
        # 不調用app.exec()避免卡住
        print("✅ PyQt6基本功能測試完成")
        
        return True
        
    except ImportError:
        print("⚠️ PyQt6未安裝，將使用文本模式")
        return True  # 這不是錯誤
    except Exception as e:
        print(f"❌ PyQt6測試失敗: {e}")
        return False

def safe_test_state_persistence():
    """安全測試狀態持久化"""
    print("\n🧪 測試狀態持久化...")
    
    try:
        from src.gui.state_manager import StateManager
        
        # 使用臨時文件
        test_file = "test_state_temp.json"
        manager = StateManager(test_file)
        
        # 測試狀態操作
        manager.set_component_state("test_comp", {"key": "value"})
        retrieved = manager.get_component_state("test_comp")
        
        if retrieved.get("key") == "value":
            print("✅ 狀態設置和獲取成功")
        else:
            print("❌ 狀態設置和獲取失敗")
            return False
        
        # 清理測試文件
        try:
            import os
            if os.path.exists(test_file):
                os.remove(test_file)
        except:
            pass
        
        print("✅ 狀態持久化測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 狀態持久化測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    global test_running
    
    print("🚀 開始 AImax GUI 安全測試")
    print("=" * 50)
    print(f"⏰ 測試超時設置: {test_timeout} 秒")
    print("💡 按 Ctrl+C 可隨時中斷測試")
    print("=" * 50)
    
    # 設置信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 啟動超時處理器
    timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
    timeout_thread.start()
    
    # 設置簡單日誌
    logging.basicConfig(level=logging.WARNING)
    
    test_results = []
    
    # 執行安全測試
    if test_running:
        test_results.append(("模塊導入", safe_test_imports()))
    
    if test_running:
        test_results.append(("組件管理器", safe_test_component_manager()))
    
    if test_running:
        test_results.append(("PyQt6可用性", safe_test_pyqt_availability()))
    
    if test_running:
        test_results.append(("狀態持久化", safe_test_state_persistence()))
    
    if test_running:
        test_results.append(("監控線程", safe_test_monitoring_thread()))
    
    # 輸出測試結果
    if test_running:
        print("\n" + "=" * 50)
        print("📊 安全測試結果摘要:")
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
            print("🎉 所有安全測試通過！")
            print("💡 建議：可以嘗試運行完整GUI，但要注意可能的卡住問題")
        else:
            print("⚠️ 部分測試失敗，建議修復後再運行完整GUI")
        
        print("\n💡 如果完整GUI卡住，可能的原因：")
        print("   1. 監控線程沒有正確停止")
        print("   2. PyQt6事件循環問題")
        print("   3. 系統資源不足")
        print("   4. 依賴組件初始化失敗")
        
        return passed == total
    
    return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 測試過程中發生異常: {e}")
        sys.exit(1)