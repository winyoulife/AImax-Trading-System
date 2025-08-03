#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化風險監控系統測試腳本
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.monitoring.simple_risk_monitor import (
    SimpleRiskMonitor,
    RiskMonitoringConfig,
    RiskLevel,
    AlertType,
    AlertPriority
)

class SimpleRiskMonitorTester:
    """簡化風險監控系統測試器"""
    
    def __init__(self):
        self.test_results = []
        self.monitor = None
        
    async def run_all_tests(self):
        """運行所有測試"""
        print("🧪 開始簡化風險監控系統測試")
        print("=" * 60)
        
        # 測試列表
        tests = [
            ("基礎配置測試", self.test_basic_configuration),
            ("風險指標更新測試", self.test_metrics_update),
            ("警報觸發測試", self.test_alert_triggering),
            ("監控循環測試", self.test_monitoring_loop),
            ("狀態報告測試", self.test_status_reporting)
        ]
        
        # 執行測試
        for test_name, test_func in tests:
            try:
                print(f"\n🔍 {test_name}")
                print("-" * 40)
                result = await test_func()
                self.test_results.append({
                    'test_name': test_name,
                    'status': 'PASSED' if result else 'FAILED',
                    'timestamp': datetime.now()
                })
                print(f"✅ {test_name}: {'通過' if result else '失敗'}")
            except Exception as e:
                print(f"❌ {test_name}: 錯誤 - {e}")
                self.test_results.append({
                    'test_name': test_name,
                    'status': 'ERROR',
                    'error': str(e),
                    'timestamp': datetime.now()
                })
        
        # 生成測試報告
        await self.generate_test_report()
    
    async def test_basic_configuration(self):
        """測試基礎配置"""
        try:
            # 創建配置
            config = RiskMonitoringConfig()
            self.monitor = SimpleRiskMonitor(config)
            
            print(f"   監控間隔: {config.monitoring_interval} 秒")
            print(f"   敞口警告閾值: {config.exposure_warning_threshold:.1%}")
            print(f"   敞口危險閾值: {config.exposure_critical_threshold:.1%}")
            print(f"   信心度警告閾值: {config.confidence_warning_threshold:.1%}")
            print(f"   自動處理: {'啟用' if config.enable_auto_actions else '禁用'}")
            
            # 驗證配置
            assert hasattr(self.monitor, 'config')
            assert hasattr(self.monitor, 'current_metrics')
            assert hasattr(self.monitor, 'active_alerts')
            
            print("   ✅ 基礎配置驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 基礎配置測試失敗: {e}")
            return False
    
    async def test_metrics_update(self):
        """測試風險指標更新"""
        try:
            # 記錄初始指標
            initial_timestamp = self.monitor.current_metrics.timestamp
            
            # 更新指標
            await self.monitor._update_metrics()
            
            # 檢查指標更新
            updated_timestamp = self.monitor.current_metrics.timestamp
            
            print(f"   總敞口: {self.monitor.current_metrics.total_exposure:,.0f} TWD")
            print(f"   敞口利用率: {self.monitor.current_metrics.exposure_utilization:.1%}")
            print(f"   集中度比率: {self.monitor.current_metrics.concentration_ratio:.1%}")
            print(f"   AI信心度: {self.monitor.current_metrics.avg_ai_confidence:.1%}")
            print(f"   系統健康: {self.monitor.current_metrics.system_health_score:.1%}")
            
            # 驗證指標範圍
            assert 0 <= self.monitor.current_metrics.exposure_utilization <= 1
            assert 0 <= self.monitor.current_metrics.concentration_ratio <= 1
            assert 0 <= self.monitor.current_metrics.avg_ai_confidence <= 1
            assert 0 <= self.monitor.current_metrics.system_health_score <= 1
            assert updated_timestamp > initial_timestamp
            
            print("   ✅ 風險指標更新驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 風險指標更新測試失敗: {e}")
            return False
    
    async def test_alert_triggering(self):
        """測試警報觸發"""
        try:
            # 清理現有警報
            self.monitor.active_alerts.clear()
            
            # 設置觸發警報的條件
            self.monitor.current_metrics.exposure_utilization = 0.85  # 超過警告閾值
            self.monitor.current_metrics.avg_ai_confidence = 0.35     # 低於信心度閾值
            
            # 檢查警報
            await self.monitor._check_alerts()
            
            print(f"   觸發的警報數量: {len(self.monitor.active_alerts)}")
            
            # 檢查警報詳情
            for alert_id, alert in self.monitor.active_alerts.items():
                print(f"   警報: {alert.title} - 優先級: {alert.priority.name}")
                assert alert.is_active
                assert alert.timestamp is not None
            
            # 驗證至少觸發了一個警報
            assert len(self.monitor.active_alerts) > 0, "應該觸發至少一個警報"
            
            print("   ✅ 警報觸發驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 警報觸發測試失敗: {e}")
            return False
    
    async def test_monitoring_loop(self):
        """測試監控循環"""
        try:
            # 設置較短的監控間隔
            original_interval = self.monitor.config.monitoring_interval
            self.monitor.config.monitoring_interval = 0.5
            
            print("   啟動監控循環測試 (3秒)...")
            
            # 啟動監控任務
            monitoring_task = asyncio.create_task(self.monitor.start_monitoring())
            
            # 運行3秒
            await asyncio.sleep(3)
            
            # 停止監控
            await self.monitor.stop_monitoring()
            monitoring_task.cancel()
            
            # 恢復原始間隔
            self.monitor.config.monitoring_interval = original_interval
            
            # 檢查監控狀態
            assert not self.monitor.is_monitoring, "監控應該已停止"
            
            print(f"   ✓ 監控循環運行正常")
            print(f"   ✓ 生成警報數: {self.monitor.monitoring_stats['total_alerts_generated']}")
            print(f"   ✓ 系統錯誤數: {self.monitor.monitoring_stats['system_errors']}")
            
            print("   ✅ 監控循環驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 監控循環測試失敗: {e}")
            return False
    
    async def test_status_reporting(self):
        """測試狀態報告"""
        try:
            # 獲取監控狀態
            status = self.monitor.get_monitoring_status()
            
            print(f"   監控狀態: {'運行中' if status['is_monitoring'] else '已停止'}")
            print(f"   活躍警報數: {status['active_alerts']['count']}")
            print(f"   總警報生成數: {status['statistics']['total_alerts_generated']}")
            
            # 獲取風險摘要
            summary = self.monitor.get_risk_summary()
            
            print(f"   總體風險等級: {summary['overall_risk_level']}")
            print(f"   總體風險分數: {summary['overall_risk_score']:.2f}")
            print(f"   活躍警報數: {summary['active_alerts_count']}")
            
            # 驗證報告結構
            assert 'is_monitoring' in status
            assert 'current_metrics' in status
            assert 'active_alerts' in status
            assert 'statistics' in status
            
            assert 'overall_risk_level' in summary
            assert 'overall_risk_score' in summary
            assert 'active_alerts_count' in summary
            
            # 驗證風險等級
            risk_levels = ['very_low', 'low', 'medium', 'high', 'very_high']
            assert summary['overall_risk_level'] in risk_levels
            assert 0 <= summary['overall_risk_score'] <= 1
            
            print("   ✅ 狀態報告驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 狀態報告測試失敗: {e}")
            return False
    
    async def generate_test_report(self):
        """生成測試報告"""
        try:
            print("\n" + "=" * 60)
            print("📊 簡化風險監控系統測試報告")
            print("=" * 60)
            
            # 統計測試結果
            total_tests = len(self.test_results)
            passed_tests = len([r for r in self.test_results if r['status'] == 'PASSED'])
            failed_tests = len([r for r in self.test_results if r['status'] == 'FAILED'])
            error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])
            
            print(f"總測試數量: {total_tests}")
            print(f"通過測試: {passed_tests} ✅")
            print(f"失敗測試: {failed_tests} ❌")
            print(f"錯誤測試: {error_tests} 💥")
            print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
            
            # 詳細結果
            print(f"\n詳細測試結果:")
            for result in self.test_results:
                status_icon = "✅" if result['status'] == 'PASSED' else "❌" if result['status'] == 'FAILED' else "💥"
                print(f"  {status_icon} {result['test_name']}: {result['status']}")
                if 'error' in result:
                    print(f"     錯誤: {result['error']}")
            
            # 系統狀態
            if self.monitor:
                status = self.monitor.get_monitoring_status()
                summary = self.monitor.get_risk_summary()
                
                print(f"\n系統狀態:")
                print(f"  監控狀態: {'運行中' if status['is_monitoring'] else '已停止'}")
                print(f"  活躍警報: {status['active_alerts']['count']}")
                print(f"  總體風險等級: {summary['overall_risk_level']}")
                print(f"  總體風險分數: {summary['overall_risk_score']:.2f}")
                print(f"  系統健康分數: {status['current_metrics']['system_health_score']:.2f}")
            
            # 保存報告到文件
            report_data = {
                'test_summary': {
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'error_tests': error_tests,
                    'success_rate': (passed_tests/total_tests)*100
                },
                'test_results': self.test_results,
                'system_status': status if self.monitor else {},
                'risk_summary': summary if self.monitor else {},
                'timestamp': datetime.now().isoformat()
            }
            
            report_file = f"AImax/logs/simple_risk_monitor_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n📄 測試報告已保存: {report_file}")
            
            # 總結
            if passed_tests == total_tests:
                print(f"\n🎉 所有測試通過！簡化風險監控系統運行正常")
            else:
                print(f"\n⚠️ 有 {failed_tests + error_tests} 個測試未通過，需要檢查")
            
        except Exception as e:
            print(f"❌ 生成測試報告失敗: {e}")


async def main():
    """主函數"""
    tester = SimpleRiskMonitorTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())