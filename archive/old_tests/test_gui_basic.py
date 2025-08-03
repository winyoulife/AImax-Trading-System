#!/usr/bin/env python3
"""
AImax GUI基本功能測試腳本
"""
import sys
import logging
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """測試導入"""
    print("🧪 測試模塊導入...")
    
    try:
        from src.gui.component_manager import ComponentManager, ComponentStatus
        print("✅ ComponentManager 導入成功")
    except Exception as e:
        print(f"❌ ComponentManager 導入失敗: {e}")
        return False
    
    try:
        from src.gui.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
        print("✅ ErrorHandler 導入成功")
    except Exception as e:
        print(f"❌ ErrorHandler 導入失敗: {e}")
        return False
    
    try:
        from src.gui.state_manager import StateManager
        print("✅ StateManager 導入成功")
    except Exception as e:
        print(f"❌ StateManager 導入失敗: {e}")
        return False
    
    try:
        from src.gui.monitoring_dashboard import MonitoringDashboard
        print("✅ MonitoringDashboard 導入成功")
    except Exception as e:
        print(f"❌ MonitoringDashboard 導入失敗: {e}")
        return False
    
    return True

def test_component_manager():
    """測試組件管理器"""
    print("\n🧪 測試組件管理器...")
    
    try:
        from src.gui.component_manager import ComponentManager
        
        # 創建組件管理器
        manager = ComponentManager()
        print("✅ 組件管理器創建成功")
        
        # 測試組件註冊
        class TestComponent:
            def __init__(self):
                self.initialized = True
        
        success = manager.register_component("test_component", TestComponent)
        if success:
            print("✅ 組件註冊成功")
        else:
            print("❌ 組件註冊失敗")
            return False
        
        # 測試組件初始化
        success = manager.initialize_components()
        if success:
            print("✅ 組件初始化成功")
        else:
            print("❌ 組件初始化失敗")
            return False
        
        # 測試組件獲取
        component = manager.get_component("test_component")
        if component and hasattr(component, 'initialized'):
            print("✅ 組件獲取成功")
        else:
            print("❌ 組件獲取失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 組件管理器測試失敗: {e}")
        return False

def test_error_handler():
    """測試錯誤處理器"""
    print("\n🧪 測試錯誤處理器...")
    
    try:
        from src.gui.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
        
        # 創建錯誤處理器
        handler = ErrorHandler()
        print("✅ 錯誤處理器創建成功")
        
        # 測試異常處理
        test_exception = ValueError("測試異常")
        success = handler.handle_exception(
            test_exception, 
            "test_component",
            ErrorCategory.RUNTIME,
            ErrorSeverity.MEDIUM
        )
        print(f"✅ 異常處理測試完成，恢復成功: {success}")
        
        # 測試錯誤統計
        stats = handler.get_error_statistics()
        if stats["total_errors"] > 0:
            print("✅ 錯誤統計功能正常")
        else:
            print("❌ 錯誤統計功能異常")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤處理器測試失敗: {e}")
        return False

def test_state_manager():
    """測試狀態管理器"""
    print("\n🧪 測試狀態管理器...")
    
    try:
        from src.gui.state_manager import StateManager
        
        # 創建狀態管理器
        manager = StateManager("test_state.json")
        print("✅ 狀態管理器創建成功")
        
        # 測試狀態設置和獲取
        test_state = {"key1": "value1", "key2": 123}
        manager.set_component_state("test_component", test_state)
        
        retrieved_state = manager.get_component_state("test_component")
        if retrieved_state == test_state:
            print("✅ 狀態設置和獲取成功")
        else:
            print("❌ 狀態設置和獲取失敗")
            return False
        
        # 測試全局狀態
        manager.set_global_state("global_key", "global_value")
        global_value = manager.get_global_state("global_key")
        if global_value == "global_value":
            print("✅ 全局狀態功能正常")
        else:
            print("❌ 全局狀態功能異常")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 狀態管理器測試失敗: {e}")
        return False

def test_monitoring_dashboard():
    """測試監控儀表板"""
    print("\n🧪 測試監控儀表板...")
    
    try:
        from src.gui.monitoring_dashboard import SystemMonitorThread
        
        # 創建監控線程
        monitor = SystemMonitorThread()
        print("✅ 監控線程創建成功")
        
        # 測試組件初始化
        monitor.initialize_components()
        print("✅ 監控組件初始化完成")
        
        # 測試數據收集（不啟動線程）
        performance_data = monitor._collect_performance_data()
        if performance_data and "system" in performance_data:
            print("✅ 性能數據收集成功")
        else:
            print("❌ 性能數據收集失敗")
            return False
        
        ai_status = monitor._collect_ai_status()
        if ai_status and "models" in ai_status:
            print("✅ AI狀態收集成功")
        else:
            print("❌ AI狀態收集失敗")
            return False
        
        trading_status = monitor._collect_trading_status()
        if trading_status and "account" in trading_status:
            print("✅ 交易狀態收集成功")
        else:
            print("❌ 交易狀態收集失敗")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 監控儀表板測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始 AImax GUI 基本功能測試")
    print("=" * 50)
    
    # 設置簡單日誌
    logging.basicConfig(level=logging.WARNING)
    
    test_results = []
    
    # 執行測試
    test_results.append(("模塊導入", test_imports()))
    test_results.append(("組件管理器", test_component_manager()))
    test_results.append(("錯誤處理器", test_error_handler()))
    test_results.append(("狀態管理器", test_state_manager()))
    test_results.append(("監控儀表板", test_monitoring_dashboard()))
    
    # 輸出測試結果
    print("\n" + "=" * 50)
    print("📊 測試結果摘要:")
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
        print("🎉 所有測試通過！GUI系統基本功能正常")
        return True
    else:
        print("⚠️ 部分測試失敗，請檢查相關組件")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)