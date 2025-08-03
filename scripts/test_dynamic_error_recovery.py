#!/usr/bin/env python3
"""
測試動態錯誤處理和恢復機制
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
import threading
from datetime import datetime, timedelta
import tempfile
import shutil

def test_error_handler_creation():
    """測試錯誤處理器創建"""
    print("\n🧪 測試錯誤處理器創建...")
    try:
        from src.core.dynamic_error_handler import DynamicErrorHandler, ErrorType, ErrorSeverity
        
        # 創建臨時日誌目錄
        temp_dir = tempfile.mkdtemp()
        try:
            handler = DynamicErrorHandler(log_dir=temp_dir)
            print("✅ 錯誤處理器創建成功")
            
            # 測試配置
            print(f"   最大錯誤記錄數: {handler.max_error_records}")
            print(f"   恢復策略數量: {len(handler.recovery_strategies)}")
            print(f"   日誌目錄: {handler.log_dir}")
            
            return True
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 錯誤處理器創建測試失敗: {e}")
        return False

def test_error_handling():
    """測試錯誤處理功能"""
    print("\n🧪 測試錯誤處理功能...")
    try:
        from src.core.dynamic_error_handler import DynamicErrorHandler, ErrorType, ErrorSeverity
        
        temp_dir = tempfile.mkdtemp()
        try:
            handler = DynamicErrorHandler(log_dir=temp_dir)
            
            # 測試不同類型的錯誤
            test_errors = [
                (ValueError("測試數據錯誤"), "test_component", "test_function"),
                (ConnectionError("測試網絡錯誤"), "network_component", "connect_function"),
                (MemoryError("測試內存錯誤"), "memory_component", "allocate_function"),
                (TimeoutError("測試超時錯誤"), "timeout_component", "wait_function")
            ]
            
            for error, component, function in test_errors:
                error_record = handler.handle_error(
                    error=error,
                    component=component,
                    function_name=function,
                    context_data={"test_data": "測試上下文"}
                )
                
                print(f"   ✓ 處理錯誤: {error_record.error_type.value} - {error_record.error_id}")
            
            # 檢查錯誤統計
            stats = handler.get_error_statistics()
            print(f"   總錯誤數: {stats['total_errors']}")
            print(f"   解決率: {stats['resolution_rate']:.1f}%")
            
            return True
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 錯誤處理功能測試失敗: {e}")
        return False

def test_error_callbacks():
    """測試錯誤回調功能"""
    print("\n🧪 測試錯誤回調功能...")
    try:
        from src.core.dynamic_error_handler import DynamicErrorHandler
        
        temp_dir = tempfile.mkdtemp()
        try:
            handler = DynamicErrorHandler(log_dir=temp_dir)
            
            # 回調計數器
            callback_count = 0
            
            def error_callback(error_record):
                nonlocal callback_count
                callback_count += 1
                print(f"   📞 錯誤回調觸發: {error_record.error_id}")
            
            # 添加回調
            handler.add_error_callback(error_callback)
            
            # 觸發錯誤
            handler.handle_error(
                error=RuntimeError("測試回調錯誤"),
                component="callback_test",
                function_name="test_callback"
            )
            
            if callback_count == 1:
                print("✅ 錯誤回調功能正常")
                return True
            else:
                print(f"❌ 回調次數不正確: {callback_count}")
                return False
                
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 錯誤回調功能測試失敗: {e}")
        return False

def test_error_decorator():
    """測試錯誤處理裝飾器"""
    print("\n🧪 測試錯誤處理裝飾器...")
    try:
        from src.core.dynamic_error_handler import DynamicErrorHandler, handle_errors
        
        temp_dir = tempfile.mkdtemp()
        try:
            handler = DynamicErrorHandler(log_dir=temp_dir)
            
            @handle_errors("decorator_test", handler)
            def test_function_with_error():
                raise ValueError("裝飾器測試錯誤")
            
            @handle_errors("decorator_test", handler)
            def test_function_normal():
                return "正常執行"
            
            # 測試正常執行
            result = test_function_normal()
            if result == "正常執行":
                print("   ✓ 裝飾器正常函數執行成功")
            
            # 測試錯誤處理
            try:
                test_function_with_error()
                print("❌ 應該拋出異常")
                return False
            except ValueError:
                print("   ✓ 裝飾器錯誤處理成功")
            
            # 檢查錯誤記錄
            if len(handler.error_records) > 0:
                print("   ✓ 錯誤記錄已創建")
                return True
            else:
                print("❌ 錯誤記錄未創建")
                return False
                
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 錯誤處理裝飾器測試失敗: {e}")
        return False

def test_recovery_manager_creation():
    """測試恢復管理器創建"""
    print("\n🧪 測試恢復管理器創建...")
    try:
        from src.core.dynamic_recovery_manager import DynamicRecoveryManager
        from src.core.dynamic_error_handler import DynamicErrorHandler
        from src.core.dynamic_trading_config import DynamicTradingConfig
        
        temp_dir = tempfile.mkdtemp()
        try:
            config = DynamicTradingConfig()
            error_handler = DynamicErrorHandler(log_dir=temp_dir)
            recovery_manager = DynamicRecoveryManager(
                config=config,
                error_handler=error_handler,
                backup_dir=os.path.join(temp_dir, "backups")
            )
            
            print("✅ 恢復管理器創建成功")
            print(f"   備份目錄: {recovery_manager.backup_dir}")
            print(f"   最大快照數: {recovery_manager.max_snapshots}")
            print(f"   自動備份間隔: {recovery_manager.auto_backup_interval} 秒")
            
            # 測試狀態
            status = recovery_manager.get_recovery_status()
            print(f"   恢復狀態: {status['recovery_state']}")
            print(f"   註冊組件數: {len(status['registered_components'])}")
            
            recovery_manager.cleanup()
            return True
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 恢復管理器創建測試失敗: {e}")
        return False

def test_component_registration():
    """測試組件註冊功能"""
    print("\n🧪 測試組件註冊功能...")
    try:
        from src.core.dynamic_recovery_manager import DynamicRecoveryManager
        from src.core.dynamic_error_handler import DynamicErrorHandler
        from src.core.dynamic_trading_config import DynamicTradingConfig
        
        temp_dir = tempfile.mkdtemp()
        try:
            config = DynamicTradingConfig()
            error_handler = DynamicErrorHandler(log_dir=temp_dir)
            recovery_manager = DynamicRecoveryManager(
                config=config,
                error_handler=error_handler,
                backup_dir=os.path.join(temp_dir, "backups")
            )
            
            # 創建測試組件
            class TestComponent:
                def __init__(self):
                    self.data = {"value": 100, "status": "active"}
                
                def get_state(self):
                    return self.data
                
                def restore_state(self, state):
                    self.data = state
            
            test_component = TestComponent()
            
            # 註冊組件
            recovery_manager.register_component("test_component", test_component)
            
            # 檢查註冊狀態
            status = recovery_manager.get_recovery_status()
            if "test_component" in status['registered_components']:
                print("✅ 組件註冊成功")
                return True
            else:
                print("❌ 組件註冊失敗")
                return False
                
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 組件註冊功能測試失敗: {e}")
        return False

def test_snapshot_creation():
    """測試快照創建功能"""
    print("\n🧪 測試快照創建功能...")
    try:
        from src.core.dynamic_recovery_manager import DynamicRecoveryManager, BackupType
        from src.core.dynamic_error_handler import DynamicErrorHandler
        from src.core.dynamic_trading_config import DynamicTradingConfig
        
        temp_dir = tempfile.mkdtemp()
        try:
            config = DynamicTradingConfig()
            error_handler = DynamicErrorHandler(log_dir=temp_dir)
            recovery_manager = DynamicRecoveryManager(
                config=config,
                error_handler=error_handler,
                backup_dir=os.path.join(temp_dir, "backups")
            )
            
            # 註冊測試組件
            class TestComponent:
                def __init__(self):
                    self.data = {"counter": 42, "name": "test"}
                
                def get_state(self):
                    return self.data
            
            recovery_manager.register_component("test_comp", TestComponent())
            
            # 創建快照
            snapshot = recovery_manager.create_snapshot(BackupType.FULL)
            
            print(f"✅ 快照創建成功: {snapshot.snapshot_id}")
            print(f"   快照類型: {snapshot.backup_type.value}")
            print(f"   組件數量: {len(snapshot.components)}")
            print(f"   文件路徑: {snapshot.file_path}")
            
            # 檢查快照文件是否存在
            if snapshot.file_path and os.path.exists(snapshot.file_path):
                print("   ✓ 快照文件已創建")
                return True
            else:
                print("   ❌ 快照文件未創建")
                return False
                
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 快照創建功能測試失敗: {e}")
        return False

def test_snapshot_restore():
    """測試快照恢復功能"""
    print("\n🧪 測試快照恢復功能...")
    try:
        from src.core.dynamic_recovery_manager import DynamicRecoveryManager, BackupType
        from src.core.dynamic_error_handler import DynamicErrorHandler
        from src.core.dynamic_trading_config import DynamicTradingConfig
        
        temp_dir = tempfile.mkdtemp()
        try:
            config = DynamicTradingConfig()
            error_handler = DynamicErrorHandler(log_dir=temp_dir)
            recovery_manager = DynamicRecoveryManager(
                config=config,
                error_handler=error_handler,
                backup_dir=os.path.join(temp_dir, "backups")
            )
            
            # 創建測試組件
            class TestComponent:
                def __init__(self):
                    self.data = {"value": 100}
                
                def get_state(self):
                    return self.data
                
                def restore_state(self, state):
                    self.data = state
            
            test_component = TestComponent()
            recovery_manager.register_component("test_comp", test_component)
            
            # 創建快照
            snapshot = recovery_manager.create_snapshot(BackupType.FULL)
            
            # 修改組件數據
            test_component.data["value"] = 200
            print(f"   修改後的值: {test_component.data['value']}")
            
            # 從快照恢復
            success = recovery_manager.restore_from_snapshot(snapshot.snapshot_id)
            
            if success and test_component.data["value"] == 100:
                print("✅ 快照恢復成功")
                print(f"   恢復後的值: {test_component.data['value']}")
                return True
            else:
                print(f"❌ 快照恢復失敗，當前值: {test_component.data['value']}")
                return False
                
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 快照恢復功能測試失敗: {e}")
        return False

def test_recovery_plan_creation():
    """測試恢復計劃創建"""
    print("\n🧪 測試恢復計劃創建...")
    try:
        from src.core.dynamic_recovery_manager import DynamicRecoveryManager
        from src.core.dynamic_error_handler import DynamicErrorHandler, ErrorRecord, ErrorType, ErrorSeverity
        from src.core.dynamic_trading_config import DynamicTradingConfig
        from datetime import datetime
        
        temp_dir = tempfile.mkdtemp()
        try:
            config = DynamicTradingConfig()
            error_handler = DynamicErrorHandler(log_dir=temp_dir)
            recovery_manager = DynamicRecoveryManager(
                config=config,
                error_handler=error_handler,
                backup_dir=os.path.join(temp_dir, "backups")
            )
            
            # 創建測試錯誤記錄
            error_record = ErrorRecord(
                error_id="test_error_001",
                timestamp=datetime.now(),
                error_type=ErrorType.DATA_ERROR,
                severity=ErrorSeverity.HIGH,
                component="test_component",
                function_name="test_function",
                error_message="測試錯誤",
                stack_trace="測試堆棧跟蹤",
                context_data={"test": "data"}
            )
            
            # 創建恢復計劃
            recovery_plan = recovery_manager.create_recovery_plan(error_record)
            
            print(f"✅ 恢復計劃創建成功: {recovery_plan.plan_id}")
            print(f"   恢復步驟數: {len(recovery_plan.recovery_steps)}")
            print(f"   估計時間: {recovery_plan.estimated_time:.0f} 秒")
            print(f"   成功概率: {recovery_plan.success_probability:.1%}")
            print(f"   回滾步驟數: {len(recovery_plan.rollback_plan)}")
            
            # 檢查恢復步驟
            for i, step in enumerate(recovery_plan.recovery_steps):
                print(f"   步驟 {i+1}: {step['description']}")
            
            return True
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 恢復計劃創建測試失敗: {e}")
        return False

def test_auto_backup():
    """測試自動備份功能"""
    print("\n🧪 測試自動備份功能...")
    try:
        from src.core.dynamic_recovery_manager import DynamicRecoveryManager
        from src.core.dynamic_error_handler import DynamicErrorHandler
        from src.core.dynamic_trading_config import DynamicTradingConfig
        
        temp_dir = tempfile.mkdtemp()
        try:
            config = DynamicTradingConfig()
            error_handler = DynamicErrorHandler(log_dir=temp_dir)
            recovery_manager = DynamicRecoveryManager(
                config=config,
                error_handler=error_handler,
                backup_dir=os.path.join(temp_dir, "backups")
            )
            
            # 設置短的備份間隔用於測試
            recovery_manager.auto_backup_interval = 2  # 2秒
            
            # 註冊測試組件
            class TestComponent:
                def __init__(self):
                    self.counter = 0
                
                def get_state(self):
                    return {"counter": self.counter}
            
            test_component = TestComponent()
            recovery_manager.register_component("auto_backup_test", test_component)
            
            # 啟動自動備份
            recovery_manager.start_auto_backup()
            
            initial_snapshots = len(recovery_manager.snapshots)
            print(f"   初始快照數: {initial_snapshots}")
            
            # 等待自動備份觸發
            time.sleep(3)
            
            final_snapshots = len(recovery_manager.snapshots)
            print(f"   最終快照數: {final_snapshots}")
            
            # 停止自動備份
            recovery_manager.stop_auto_backup()
            
            if final_snapshots > initial_snapshots:
                print("✅ 自動備份功能正常")
                return True
            else:
                print("❌ 自動備份未觸發")
                return False
                
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 自動備份功能測試失敗: {e}")
        return False

def test_error_statistics():
    """測試錯誤統計功能"""
    print("\n🧪 測試錯誤統計功能...")
    try:
        from src.core.dynamic_error_handler import DynamicErrorHandler
        
        temp_dir = tempfile.mkdtemp()
        try:
            handler = DynamicErrorHandler(log_dir=temp_dir)
            
            # 創建多個不同類型的錯誤
            errors = [
                (ValueError("數據錯誤1"), "comp1", "func1"),
                (ValueError("數據錯誤2"), "comp1", "func2"),
                (ConnectionError("網絡錯誤1"), "comp2", "func1"),
                (MemoryError("內存錯誤1"), "comp3", "func1")
            ]
            
            for error, component, function in errors:
                handler.handle_error(error, component, function)
            
            # 獲取統計信息
            stats = handler.get_error_statistics()
            
            print(f"✅ 錯誤統計獲取成功")
            print(f"   總錯誤數: {stats['total_errors']}")
            print(f"   未解決錯誤: {stats['unresolved_errors']}")
            print(f"   解決率: {stats['resolution_rate']:.1f}%")
            
            # 檢查按類型統計
            print("   按類型統計:")
            for error_type, count in stats['error_by_type'].items():
                if count > 0:
                    print(f"     {error_type}: {count}")
            
            # 檢查按組件統計
            print("   按組件統計:")
            for component, count in stats['error_by_component'].items():
                print(f"     {component}: {count}")
            
            # 測試組件健康狀態
            health = handler.get_component_health("comp1")
            print(f"   組件 comp1 健康狀態: {health['status']}")
            
            return True
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 錯誤統計功能測試失敗: {e}")
        return False

def test_error_export():
    """測試錯誤報告導出"""
    print("\n🧪 測試錯誤報告導出...")
    try:
        from src.core.dynamic_error_handler import DynamicErrorHandler
        
        temp_dir = tempfile.mkdtemp()
        try:
            handler = DynamicErrorHandler(log_dir=temp_dir)
            
            # 創建一些錯誤
            handler.handle_error(ValueError("測試導出錯誤"), "export_test", "test_function")
            
            # 導出報告
            report_path = os.path.join(temp_dir, "error_report.json")
            success = handler.export_error_report(report_path)
            
            if success and os.path.exists(report_path):
                print("✅ 錯誤報告導出成功")
                
                # 檢查文件大小
                file_size = os.path.getsize(report_path)
                print(f"   報告文件大小: {file_size} 字節")
                
                return True
            else:
                print("❌ 錯誤報告導出失敗")
                return False
                
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        print(f"❌ 錯誤報告導出測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試動態錯誤處理和恢復機制...")
    print("=" * 60)
    
    test_results = []
    
    # 執行各項測試
    test_results.append(("錯誤處理器創建", test_error_handler_creation()))
    test_results.append(("錯誤處理功能", test_error_handling()))
    test_results.append(("錯誤回調功能", test_error_callbacks()))
    test_results.append(("錯誤處理裝飾器", test_error_decorator()))
    test_results.append(("恢復管理器創建", test_recovery_manager_creation()))
    test_results.append(("組件註冊功能", test_component_registration()))
    test_results.append(("快照創建功能", test_snapshot_creation()))
    test_results.append(("快照恢復功能", test_snapshot_restore()))
    test_results.append(("恢復計劃創建", test_recovery_plan_creation()))
    test_results.append(("自動備份功能", test_auto_backup()))
    test_results.append(("錯誤統計功能", test_error_statistics()))
    test_results.append(("錯誤報告導出", test_error_export()))
    
    # 顯示測試結果
    print("\n" + "=" * 60)
    print("📊 測試結果摘要:")
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{len(test_results)} 項測試通過")
    
    if passed == len(test_results):
        print("\n🎉 所有測試通過！動態錯誤處理和恢復機制已準備就緒！")
        print("\n📋 功能摘要:")
        print("• 全面的錯誤處理和分類")
        print("• 自動錯誤恢復策略")
        print("• 系統快照和恢復")
        print("• 組件註冊和管理")
        print("• 自動備份機制")
        print("• 錯誤統計和分析")
        print("• 恢復計劃生成")
        print("• 錯誤回調系統")
        print("• 裝飾器支持")
        print("• 報告導出功能")
    else:
        print(f"\n⚠️  有 {len(test_results) - passed} 項測試失敗，請檢查相關功能")
    
    print("\n✨ 動態錯誤處理和恢復機制測試完成！")

if __name__ == "__main__":
    main()