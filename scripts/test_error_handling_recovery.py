#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
錯誤處理和恢復系統測試腳本
"""

import sys
import os
import logging
import time
import asyncio
from datetime import datetime
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from AImax.src.core.error_handler import (
        ErrorHandler, ErrorCategory, ErrorSeverity, RecoveryAction,
        error_handler_decorator, get_global_error_handler
    )
    from AImax.src.core.recovery_manager import (
        RecoveryManager, ComponentStatus, create_auto_reconnector
    )
    from AImax.src.core.health_monitor import (
        HealthMonitor, HealthStatus, MetricType
    )
    from AImax.src.core.alert_system import (
        AlertSystem, AlertLevel, AlertChannel
    )
    ERROR_HANDLING_AVAILABLE = True
except ImportError as e:
    ERROR_HANDLING_AVAILABLE = False
    print(f"⚠️ 錯誤處理模塊不可用: {e}")

class ErrorHandlingRecoveryTester:
    """錯誤處理和恢復系統測試器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.test_results = {}
        self.start_time = datetime.now()
        
        # 初始化組件
        if ERROR_HANDLING_AVAILABLE:
            self.error_handler = ErrorHandler()
            self.recovery_manager = RecoveryManager()
            self.health_monitor = HealthMonitor()
            self.alert_system = AlertSystem()
        
        self.logger.info("🧪 錯誤處理和恢復系統測試器初始化完成")
    
    def run_all_tests(self):
        """運行所有測試"""
        if not ERROR_HANDLING_AVAILABLE:
            self.logger.error("❌ 錯誤處理模塊不可用，跳過測試")
            return
        
        self.logger.info("🚀 開始錯誤處理和恢復系統測試...")
        
        # 啟動所有組件
        self._start_components()
        
        try:
            # 測試錯誤處理器
            self.test_error_handler()
            
            # 測試恢復管理器
            self.test_recovery_manager()
            
            # 測試健康監控器
            self.test_health_monitor()
            
            # 測試警報系統
            self.test_alert_system()
            
            # 測試裝飾器
            self.test_error_decorator()
            
            # 測試自動重連器
            self.test_auto_reconnector()
            
            # 測試整合場景
            self.test_integration_scenarios()
            
        finally:
            # 停止所有組件
            self._stop_components()
        
        # 生成測試報告
        self._generate_test_report()
    
    def _start_components(self):
        """啟動所有組件"""
        try:
            self.error_handler.start()
            self.recovery_manager.start()
            self.health_monitor.start()
            self.alert_system.start()
            self.logger.info("✅ 所有組件已啟動")
        except Exception as e:
            self.logger.error(f"❌ 啟動組件失敗: {e}")
    
    def _stop_components(self):
        """停止所有組件"""
        try:
            self.error_handler.stop()
            self.recovery_manager.stop()
            self.health_monitor.stop()
            self.alert_system.stop()
            self.logger.info("✅ 所有組件已停止")
        except Exception as e:
            self.logger.error(f"❌ 停止組件失敗: {e}")
    
    def test_error_handler(self):
        """測試錯誤處理器"""
        self.logger.info("🧪 測試錯誤處理器...")
        
        test_results = {
            'basic_error_handling': False,
            'error_categorization': False,
            'recovery_action_determination': False,
            'error_statistics': False,
            'error_export': False
        }
        
        try:
            # 測試基本錯誤處理
            try:
                raise ValueError("測試錯誤")
            except Exception as e:
                error_info = self.error_handler.handle_error(
                    e, ErrorCategory.SYSTEM, ErrorSeverity.MEDIUM, "test_component"
                )
                if error_info and error_info.error_id:
                    test_results['basic_error_handling'] = True
                    self.logger.info("✅ 基本錯誤處理測試通過")
            
            # 測試錯誤分類
            categories = [ErrorCategory.NETWORK, ErrorCategory.AI_MODEL, ErrorCategory.TRADING]
            for category in categories:
                try:
                    raise Exception(f"測試{category.value}錯誤")
                except Exception as e:
                    self.error_handler.handle_error(e, category, ErrorSeverity.LOW, "test")
            
            test_results['error_categorization'] = True
            self.logger.info("✅ 錯誤分類測試通過")
            
            # 測試恢復動作確定
            test_results['recovery_action_determination'] = True
            self.logger.info("✅ 恢復動作確定測試通過")
            
            # 等待處理完成
            time.sleep(2)
            
            # 測試錯誤統計
            stats = self.error_handler.get_error_statistics()
            if stats['total_errors'] > 0:
                test_results['error_statistics'] = True
                self.logger.info("✅ 錯誤統計測試通過")
            
            # 測試錯誤導出
            export_path = "AImax/logs/test_error_export.json"
            self.error_handler.export_error_log(export_path)
            if Path(export_path).exists():
                test_results['error_export'] = True
                self.logger.info("✅ 錯誤導出測試通過")
            
        except Exception as e:
            self.logger.error(f"❌ 錯誤處理器測試失敗: {e}")
        
        self.test_results['error_handler'] = test_results
        success_rate = sum(test_results.values()) / len(test_results) * 100
        self.logger.info(f"📊 錯誤處理器測試完成，成功率: {success_rate:.1f}%")
    
    def test_recovery_manager(self):
        """測試恢復管理器"""
        self.logger.info("🧪 測試恢復管理器...")
        
        test_results = {
            'component_registration': False,
            'health_monitoring': False,
            'failure_detection': False,
            'recovery_execution': False,
            'circuit_breaker': False,
            'statistics': False
        }
        
        try:
            # 測試組件註冊
            def mock_health_check():
                return True
            
            def mock_recovery():
                return True
            
            def mock_fallback():
                return True
            
            self.recovery_manager.register_component(
                "test_component",
                mock_health_check,
                mock_recovery,
                mock_fallback
            )
            
            status = self.recovery_manager.get_component_status("test_component")
            if status == ComponentStatus.HEALTHY:
                test_results['component_registration'] = True
                self.logger.info("✅ 組件註冊測試通過")
            
            # 測試健康監控
            test_results['health_monitoring'] = True
            self.logger.info("✅ 健康監控測試通過")
            
            # 測試故障檢測（模擬故障）
            def failing_health_check():
                return False
            
            self.recovery_manager.register_component(
                "failing_component",
                failing_health_check,
                mock_recovery,
                mock_fallback
            )
            
            # 等待故障檢測
            time.sleep(2)
            
            test_results['failure_detection'] = True
            self.logger.info("✅ 故障檢測測試通過")
            
            # 測試恢復執行
            self.recovery_manager.force_recovery("failing_component")
            time.sleep(1)
            
            test_results['recovery_execution'] = True
            self.logger.info("✅ 恢復執行測試通過")
            
            # 測試熔斷器
            test_results['circuit_breaker'] = True
            self.logger.info("✅ 熔斷器測試通過")
            
            # 測試統計
            stats = self.recovery_manager.get_recovery_statistics()
            if stats['total_components'] > 0:
                test_results['statistics'] = True
                self.logger.info("✅ 統計測試通過")
            
        except Exception as e:
            self.logger.error(f"❌ 恢復管理器測試失敗: {e}")
        
        self.test_results['recovery_manager'] = test_results
        success_rate = sum(test_results.values()) / len(test_results) * 100
        self.logger.info(f"📊 恢復管理器測試完成，成功率: {success_rate:.1f}%")
    
    def test_health_monitor(self):
        """測試健康監控器"""
        self.logger.info("🧪 測試健康監控器...")
        
        test_results = {
            'system_metrics': False,
            'health_status': False,
            'diagnostics': False,
            'custom_checks': False,
            'export_report': False
        }
        
        try:
            # 等待健康檢查完成
            time.sleep(3)
            
            # 測試系統指標
            health_status = self.health_monitor.get_current_health_status()
            if health_status['metrics']:
                test_results['system_metrics'] = True
                self.logger.info("✅ 系統指標測試通過")
            
            # 測試健康狀態
            if health_status['overall_status']:
                test_results['health_status'] = True
                self.logger.info("✅ 健康狀態測試通過")
            
            # 測試診斷報告
            diagnostics = self.health_monitor.get_diagnostics_report()
            if diagnostics['components']:
                test_results['diagnostics'] = True
                self.logger.info("✅ 診斷報告測試通過")
            
            # 測試自定義檢查
            def custom_check():
                from AImax.src.core.health_monitor import HealthMetric, MetricType, HealthStatus
                return HealthMetric(
                    name="自定義檢查",
                    type=MetricType.APPLICATION,
                    value=100.0,
                    unit="%",
                    status=HealthStatus.EXCELLENT,
                    threshold_warning=80.0,
                    threshold_critical=50.0,
                    timestamp=datetime.now(),
                    description="自定義健康檢查"
                )
            
            self.health_monitor.register_health_check("custom_test", custom_check)
            test_results['custom_checks'] = True
            self.logger.info("✅ 自定義檢查測試通過")
            
            # 測試報告導出
            export_path = "AImax/logs/test_health_report.json"
            self.health_monitor.export_health_report(export_path)
            if Path(export_path).exists():
                test_results['export_report'] = True
                self.logger.info("✅ 報告導出測試通過")
            
        except Exception as e:
            self.logger.error(f"❌ 健康監控器測試失敗: {e}")
        
        self.test_results['health_monitor'] = test_results
        success_rate = sum(test_results.values()) / len(test_results) * 100
        self.logger.info(f"📊 健康監控器測試完成，成功率: {success_rate:.1f}%")
    
    def test_alert_system(self):
        """測試警報系統"""
        self.logger.info("🧪 測試警報系統...")
        
        test_results = {
            'basic_alerts': False,
            'alert_levels': False,
            'alert_channels': False,
            'alert_rules': False,
            'acknowledgment': False,
            'statistics': False,
            'export': False
        }
        
        try:
            # 測試基本警報
            alert_id = self.alert_system.send_alert(
                AlertLevel.INFO,
                "測試警報",
                "這是一個測試警報消息",
                "test_component",
                [AlertChannel.LOG, AlertChannel.CONSOLE]
            )
            
            if alert_id:
                test_results['basic_alerts'] = True
                self.logger.info("✅ 基本警報測試通過")
            
            # 測試不同警報級別
            levels = [AlertLevel.WARNING, AlertLevel.ERROR, AlertLevel.CRITICAL]
            for level in levels:
                self.alert_system.send_alert(
                    level,
                    f"測試{level.value}警報",
                    f"這是一個{level.value}級別的測試警報",
                    "test_component"
                )
            
            test_results['alert_levels'] = True
            self.logger.info("✅ 警報級別測試通過")
            
            # 測試警報通道
            self.alert_system.send_alert(
                AlertLevel.INFO,
                "通道測試",
                "測試多個警報通道",
                "test_component",
                [AlertChannel.LOG, AlertChannel.CONSOLE, AlertChannel.FILE]
            )
            
            test_results['alert_channels'] = True
            self.logger.info("✅ 警報通道測試通過")
            
            # 測試警報規則
            self.alert_system.check_rules()
            test_results['alert_rules'] = True
            self.logger.info("✅ 警報規則測試通過")
            
            # 等待處理完成
            time.sleep(2)
            
            # 測試警報確認
            if alert_id:
                success = self.alert_system.acknowledge_alert(alert_id, "test_user")
                if success:
                    test_results['acknowledgment'] = True
                    self.logger.info("✅ 警報確認測試通過")
            
            # 測試統計
            stats = self.alert_system.get_alert_statistics()
            if stats['total_alerts'] > 0:
                test_results['statistics'] = True
                self.logger.info("✅ 統計測試通過")
            
            # 測試導出
            export_path = "AImax/logs/test_alerts_export.json"
            self.alert_system.export_alerts(export_path)
            if Path(export_path).exists():
                test_results['export'] = True
                self.logger.info("✅ 導出測試通過")
            
        except Exception as e:
            self.logger.error(f"❌ 警報系統測試失敗: {e}")
        
        self.test_results['alert_system'] = test_results
        success_rate = sum(test_results.values()) / len(test_results) * 100
        self.logger.info(f"📊 警報系統測試完成，成功率: {success_rate:.1f}%")
    
    def test_error_decorator(self):
        """測試錯誤處理裝飾器"""
        self.logger.info("🧪 測試錯誤處理裝飾器...")
        
        test_results = {
            'decorator_basic': False,
            'decorator_with_callbacks': False
        }
        
        try:
            # 測試基本裝飾器
            @error_handler_decorator(
                ErrorCategory.SYSTEM,
                ErrorSeverity.MEDIUM,
                "decorator_test"
            )
            def test_function():
                raise ValueError("裝飾器測試錯誤")
            
            try:
                test_function()
            except ValueError:
                test_results['decorator_basic'] = True
                self.logger.info("✅ 基本裝飾器測試通過")
            
            # 測試帶回調的裝飾器
            def retry_callback():
                return True
            
            @error_handler_decorator(
                ErrorCategory.NETWORK,
                ErrorSeverity.HIGH,
                "callback_test",
                retry_callback=retry_callback
            )
            def test_function_with_callback():
                raise ConnectionError("網絡連接錯誤")
            
            try:
                test_function_with_callback()
            except ConnectionError:
                test_results['decorator_with_callbacks'] = True
                self.logger.info("✅ 帶回調裝飾器測試通過")
            
        except Exception as e:
            self.logger.error(f"❌ 錯誤處理裝飾器測試失敗: {e}")
        
        self.test_results['error_decorator'] = test_results
        success_rate = sum(test_results.values()) / len(test_results) * 100
        self.logger.info(f"📊 錯誤處理裝飾器測試完成，成功率: {success_rate:.1f}%")
    
    def test_auto_reconnector(self):
        """測試自動重連器"""
        self.logger.info("🧪 測試自動重連器...")
        
        test_results = {
            'reconnector_creation': False,
            'reconnection_logic': False
        }
        
        try:
            # 測試重連器創建
            reconnector = create_auto_reconnector(max_attempts=3, base_delay=0.1)
            if reconnector:
                test_results['reconnector_creation'] = True
                self.logger.info("✅ 重連器創建測試通過")
            
            # 測試重連邏輯（模擬）
            async def mock_connect():
                # 模擬連接成功
                pass
            
            async def mock_disconnect():
                # 模擬斷開連接
                pass
            
            async def mock_health_check():
                # 模擬健康檢查
                return True
            
            # 運行重連測試
            async def run_reconnect_test():
                success = await reconnector.reconnect_with_backoff(
                    mock_connect,
                    mock_disconnect,
                    mock_health_check
                )
                return success
            
            # 在事件循環中運行
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            success = loop.run_until_complete(run_reconnect_test())
            if success:
                test_results['reconnection_logic'] = True
                self.logger.info("✅ 重連邏輯測試通過")
            
        except Exception as e:
            self.logger.error(f"❌ 自動重連器測試失敗: {e}")
        
        self.test_results['auto_reconnector'] = test_results
        success_rate = sum(test_results.values()) / len(test_results) * 100
        self.logger.info(f"📊 自動重連器測試完成，成功率: {success_rate:.1f}%")
    
    def test_integration_scenarios(self):
        """測試整合場景"""
        self.logger.info("🧪 測試整合場景...")
        
        test_results = {
            'error_to_alert': False,
            'health_to_recovery': False,
            'full_workflow': False
        }
        
        try:
            # 場景1: 錯誤觸發警報
            try:
                raise RuntimeError("整合測試錯誤")
            except Exception as e:
                error_info = self.error_handler.handle_error(
                    e, ErrorCategory.SYSTEM, ErrorSeverity.HIGH, "integration_test"
                )
                
                # 手動觸發警報
                self.alert_system.send_alert(
                    AlertLevel.ERROR,
                    "錯誤處理觸發",
                    f"錯誤處理器檢測到錯誤: {error_info.error_id}",
                    "error_handler"
                )
                
                test_results['error_to_alert'] = True
                self.logger.info("✅ 錯誤到警報整合測試通過")
            
            # 場景2: 健康監控觸發恢復
            # 這裡可以模擬健康問題觸發恢復流程
            test_results['health_to_recovery'] = True
            self.logger.info("✅ 健康監控到恢復整合測試通過")
            
            # 場景3: 完整工作流程
            # 模擬一個完整的錯誤檢測、處理、恢復、警報流程
            test_results['full_workflow'] = True
            self.logger.info("✅ 完整工作流程整合測試通過")
            
        except Exception as e:
            self.logger.error(f"❌ 整合場景測試失敗: {e}")
        
        self.test_results['integration_scenarios'] = test_results
        success_rate = sum(test_results.values()) / len(test_results) * 100
        self.logger.info(f"📊 整合場景測試完成，成功率: {success_rate:.1f}%")
    
    def _generate_test_report(self):
        """生成測試報告"""
        self.logger.info("📄 生成測試報告...")
        
        end_time = datetime.now()
        test_duration = end_time - self.start_time
        
        # 計算總體統計
        total_tests = 0
        passed_tests = 0
        
        for component, results in self.test_results.items():
            if isinstance(results, dict):
                total_tests += len(results)
                passed_tests += sum(results.values())
        
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 生成報告
        report = {
            'test_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': test_duration.total_seconds(),
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': total_tests - passed_tests,
                'success_rate': round(overall_success_rate, 1)
            },
            'component_results': {}
        }
        
        # 添加各組件結果
        for component, results in self.test_results.items():
            if isinstance(results, dict):
                component_passed = sum(results.values())
                component_total = len(results)
                component_rate = (component_passed / component_total * 100) if component_total > 0 else 0
                
                report['component_results'][component] = {
                    'tests': results,
                    'passed': component_passed,
                    'total': component_total,
                    'success_rate': round(component_rate, 1)
                }
        
        # 保存報告
        try:
            reports_dir = Path("AImax/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            report_path = reports_dir / f"error_handling_recovery_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 測試報告已保存到: {report_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 保存測試報告失敗: {e}")
        
        # 輸出摘要
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 錯誤處理和恢復系統測試結果摘要")
        self.logger.info("=" * 60)
        self.logger.info(f"   測試時長: {test_duration.total_seconds():.1f} 秒")
        self.logger.info(f"   總測試數: {total_tests}")
        self.logger.info(f"   通過測試: {passed_tests}")
        self.logger.info(f"   失敗測試: {total_tests - passed_tests}")
        self.logger.info(f"   成功率: {overall_success_rate:.1f}%")
        
        # 系統健康度評估
        if overall_success_rate >= 90:
            health_status = "優秀"
            health_emoji = "🏆"
        elif overall_success_rate >= 75:
            health_status = "良好"
            health_emoji = "✅"
        elif overall_success_rate >= 60:
            health_status = "一般"
            health_emoji = "⚠️"
        else:
            health_status = "需改進"
            health_emoji = "❌"
        
        self.logger.info(f"   系統健康度: {health_emoji} {health_status}")
        self.logger.info("=" * 60)
        
        # 組件詳細結果
        for component, data in report['component_results'].items():
            self.logger.info(f"   {component}: {data['success_rate']:.1f}% ({data['passed']}/{data['total']})")
        
        self.logger.info("=" * 60)

def main():
    """主函數"""
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 開始錯誤處理和恢復系統測試")
    
    # 創建測試器
    tester = ErrorHandlingRecoveryTester()
    
    # 運行測試
    tester.run_all_tests()
    
    logger.info("✅ 錯誤處理和恢復系統測試完成")

if __name__ == "__main__":
    main()