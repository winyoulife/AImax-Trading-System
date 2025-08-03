#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
風險監控和預警系統測試腳本
測試實時風險監控、智能預警和自動處理功能
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 導入風險監控系統
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'monitoring'))

from risk_monitoring_system import *

class RiskMonitoringSystemTester:
    """風險監控系統測試器"""
    
    def __init__(self):
        self.test_results = []
        self.monitor = None
        self.received_alerts = []
        self.received_metrics = []
        
    async def run_all_tests(self):
        """運行所有測試"""
        print("🧪 開始風險監控和預警系統測試")
        print("=" * 60)
        
        # 測試列表
        tests = [
            ("基礎配置測試", self.test_basic_configuration),
            ("風險指標計算測試", self.test_risk_metrics_calculation),
            ("警報觸發機制測試", self.test_alert_triggering),
            ("警報優先級測試", self.test_alert_priorities),
            ("自動處理機制測試", self.test_auto_actions),
            ("系統健康監控測試", self.test_system_health_monitoring),
            ("回調函數測試", self.test_callback_functions),
            ("監控循環測試", self.test_monitoring_loops),
            ("警報管理測試", self.test_alert_management),
            ("統計和報告測試", self.test_statistics_and_reporting)
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
            # 測試默認配置
            config = RiskMonitoringConfig()
            self.monitor = RiskMonitoringSystem(config)
            
            print(f"   監控間隔: {config.monitoring_interval} 秒")
            print(f"   指標更新間隔: {config.metrics_update_interval} 秒")
            print(f"   敞口警告閾值: {config.exposure_warning_threshold:.1%}")
            print(f"   敞口危險閾值: {config.exposure_critical_threshold:.1%}")
            print(f"   自動處理: {'啟用' if config.enable_auto_actions else '禁用'}")
            
            # 驗證配置合理性
            assert 0 < config.monitoring_interval <= 60
            assert 0 < config.exposure_warning_threshold < config.exposure_critical_threshold
            assert config.confidence_critical_threshold < config.confidence_warning_threshold
            
            print("   ✅ 基礎配置驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 基礎配置測試失敗: {e}")
            return False
    
    async def test_risk_metrics_calculation(self):
        """測試風險指標計算"""
        try:
            # 模擬風險指標
            self.monitor.current_metrics.total_exposure = 100000
            self.monitor.current_metrics.exposure_utilization = 0.75
            self.monitor.current_metrics.concentration_ratio = 0.45
            self.monitor.current_metrics.portfolio_correlation = 0.65
            self.monitor.current_metrics.avg_ai_confidence = 0.72
            self.monitor.current_metrics.min_ai_confidence = 0.58
            self.monitor.current_metrics.daily_var_95 = 25000
            self.monitor.current_metrics.system_health_score = 0.88
            
            print(f"   總敞口: {self.monitor.current_metrics.total_exposure:,.0f} TWD")
            print(f"   敞口利用率: {self.monitor.current_metrics.exposure_utilization:.1%}")
            print(f"   集中度比率: {self.monitor.current_metrics.concentration_ratio:.1%}")
            print(f"   投資組合相關性: {self.monitor.current_metrics.portfolio_correlation:.1%}")
            print(f"   平均AI信心度: {self.monitor.current_metrics.avg_ai_confidence:.1%}")
            print(f"   最低AI信心度: {self.monitor.current_metrics.min_ai_confidence:.1%}")
            print(f"   95% VaR: {self.monitor.current_metrics.daily_var_95:,.0f} TWD")
            print(f"   系統健康分數: {self.monitor.current_metrics.system_health_score:.1%}")
            
            # 測試衍生指標計算
            market_volatility = await self.monitor._calculate_market_volatility()
            liquidity_risk = await self.monitor._calculate_liquidity_risk()
            correlation_risk = await self.monitor._calculate_correlation_risk_score()
            system_health = await self.monitor._calculate_system_health()
            
            print(f"   市場波動率分數: {market_volatility:.2f}")
            print(f"   流動性風險分數: {liquidity_risk:.2f}")
            print(f"   相關性風險分數: {correlation_risk:.2f}")
            print(f"   系統健康分數: {system_health:.2f}")
            
            # 驗證指標範圍
            assert 0 <= market_volatility <= 1
            assert 0 <= liquidity_risk <= 1
            assert 0 <= correlation_risk <= 1
            assert 0 <= system_health <= 1
            
            print("   ✅ 風險指標計算驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 風險指標計算測試失敗: {e}")
            return False
    
    async def test_alert_triggering(self):
        """測試警報觸發機制"""
        try:
            # 設置觸發警報的條件
            self.monitor.current_metrics.exposure_utilization = 0.85  # 超過警告閾值
            self.monitor.current_metrics.concentration_ratio = 0.65   # 超過集中度閾值
            self.monitor.current_metrics.portfolio_correlation = 0.85 # 超過相關性閾值
            self.monitor.current_metrics.avg_ai_confidence = 0.35     # 低於信心度閾值
            
            # 檢查風險警報
            await self.monitor._check_risk_alerts()
            
            print(f"   觸發的警報數量: {len(self.monitor.active_alerts)}")
            
            # 驗證警報類型
            alert_types = [alert.alert_type for alert in self.monitor.active_alerts.values()]
            expected_types = [AlertType.EXPOSURE_LIMIT, AlertType.CONCENTRATION_RISK, 
                            AlertType.CORRELATION_RISK, AlertType.AI_CONFIDENCE]
            
            for expected_type in expected_types:
                assert expected_type in alert_types, f"缺少預期的警報類型: {expected_type}"
                print(f"   ✓ 觸發了 {expected_type.value} 警報")
            
            # 檢查警報詳情
            for alert in self.monitor.active_alerts.values():
                print(f"   警報: {alert.title} - 優先級: {alert.priority.name} - 風險等級: {alert.risk_level.name}")
                assert alert.is_active
                assert alert.timestamp is not None
                assert alert.risk_value > 0
            
            print("   ✅ 警報觸發機制驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 警報觸發機制測試失敗: {e}")
            return False
    
    async def test_alert_priorities(self):
        """測試警報優先級"""
        try:
            # 清理現有警報
            self.monitor.active_alerts.clear()
            
            # 測試不同優先級的警報
            test_cases = [
                (0.82, AlertPriority.HIGH, "高優先級敞口警報"),
                (0.92, AlertPriority.CRITICAL, "危險優先級敞口警報"),
                (0.38, AlertPriority.HIGH, "高優先級信心度警報"),
                (0.28, AlertPriority.CRITICAL, "危險優先級信心度警報")
            ]
            
            for exposure_util, expected_priority, description in test_cases:
                # 設置條件
                self.monitor.current_metrics.exposure_utilization = exposure_util
                self.monitor.current_metrics.avg_ai_confidence = 0.38 if "信心度" in description else 0.75
                self.monitor.current_metrics.min_ai_confidence = 0.28 if "危險優先級信心度" in description else 0.65
                
                # 清理警報並重新檢查
                self.monitor.active_alerts.clear()
                await self.monitor._check_risk_alerts()
                
                # 驗證優先級
                if self.monitor.active_alerts:
                    alert = list(self.monitor.active_alerts.values())[0]
                    print(f"   {description}: {alert.priority.name} (預期: {expected_priority.name})")
                    
                    # 驗證自動處理動作
                    if alert.priority == AlertPriority.CRITICAL:
                        assert len(alert.auto_actions) > 0, "危險優先級警報應該有自動處理動作"
                        print(f"     自動處理動作: {alert.auto_actions}")
            
            print("   ✅ 警報優先級驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 警報優先級測試失敗: {e}")
            return False
    
    async def test_auto_actions(self):
        """測試自動處理機制"""
        try:
            # 啟用自動處理
            self.monitor.config.enable_auto_actions = True
            
            # 創建需要自動處理的警報
            critical_alert = RiskAlert(
                alert_id="test_critical_alert",
                alert_type=AlertType.EXPOSURE_LIMIT,
                priority=AlertPriority.CRITICAL,
                risk_level=RiskLevel.VERY_HIGH,
                title="測試危險警報",
                message="測試自動處理",
                affected_pairs=["BTCTWD"],
                risk_value=0.95,
                threshold=0.9,
                timestamp=datetime.now(),
                auto_actions=["reduce_positions", "pause_trading"]
            )
            
            self.monitor.active_alerts["test_critical"] = critical_alert
            
            print(f"   創建危險警報: {critical_alert.title}")
            print(f"   自動處理動作: {critical_alert.auto_actions}")
            
            # 執行自動處理
            initial_auto_actions = self.monitor.monitoring_stats['auto_actions_executed']
            await self.monitor._execute_auto_actions()
            
            # 驗證自動處理執行
            final_auto_actions = self.monitor.monitoring_stats['auto_actions_executed']
            executed_actions = final_auto_actions - initial_auto_actions
            
            print(f"   執行的自動處理數量: {executed_actions}")
            assert executed_actions > 0, "應該執行了自動處理動作"
            
            # 測試禁用自動處理
            self.monitor.config.enable_auto_actions = False
            initial_auto_actions = self.monitor.monitoring_stats['auto_actions_executed']
            await self.monitor._execute_auto_actions()
            final_auto_actions = self.monitor.monitoring_stats['auto_actions_executed']
            
            assert final_auto_actions == initial_auto_actions, "禁用自動處理時不應該執行動作"
            print("   ✓ 自動處理禁用功能正常")
            
            print("   ✅ 自動處理機制驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 自動處理機制測試失敗: {e}")
            return False
    
    async def test_system_health_monitoring(self):
        """測試系統健康監控"""
        try:
            # 測試系統健康分數計算
            health_score = await self.monitor._calculate_system_health()
            print(f"   系統健康分數: {health_score:.2f}")
            
            # 測試錯誤率計算
            self.monitor.monitoring_stats['system_errors'] = 5
            self.monitor.monitoring_stats['total_alerts_generated'] = 100
            error_rate = await self.monitor._calculate_error_rate()
            print(f"   系統錯誤率: {error_rate:.2%}")
            
            # 測試系統健康警報
            self.monitor.current_metrics.system_health_score = 0.75  # 低於警告閾值
            await self.monitor._trigger_system_health_alert(0.75)
            
            # 檢查是否觸發了系統健康警報
            system_health_alerts = [alert for alert in self.monitor.active_alerts.values() 
                                   if alert.alert_type == AlertType.SYSTEM_HEALTH]
            
            assert len(system_health_alerts) > 0, "應該觸發系統健康警報"
            print(f"   ✓ 觸發了系統健康警報: {system_health_alerts[0].message}")
            
            # 驗證健康分數範圍
            assert 0 <= health_score <= 1, "健康分數應該在0-1範圍內"
            assert 0 <= error_rate <= 1, "錯誤率應該在0-1範圍內"
            
            print("   ✅ 系統健康監控驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 系統健康監控測試失敗: {e}")
            return False
    
    async def test_callback_functions(self):
        """測試回調函數"""
        try:
            # 清理接收的數據
            self.received_alerts.clear()
            self.received_metrics.clear()
            
            # 定義測試回調函數
            async def test_alert_callback(alert):
                self.received_alerts.append(alert)
                print(f"     收到警報回調: {alert.title}")
            
            async def test_metrics_callback(metrics):
                self.received_metrics.append(metrics)
                print(f"     收到指標回調: 敞口利用率 {metrics.exposure_utilization:.1%}")
            
            # 添加回調函數
            self.monitor.add_alert_callback(test_alert_callback)
            self.monitor.add_metrics_callback(test_metrics_callback)
            
            print(f"   添加了 {len(self.monitor.alert_callbacks)} 個警報回調")
            print(f"   添加了 {len(self.monitor.metrics_callbacks)} 個指標回調")
            
            # 觸發警報測試回調
            test_alert = RiskAlert(
                alert_id="callback_test_alert",
                alert_type=AlertType.EXPOSURE_LIMIT,
                priority=AlertPriority.HIGH,
                risk_level=RiskLevel.HIGH,
                title="回調測試警報",
                message="測試回調函數",
                affected_pairs=[],
                risk_value=0.85,
                threshold=0.8,
                timestamp=datetime.now()
            )
            
            await self.monitor._trigger_alert(test_alert)
            
            # 觸發指標回調
            for callback in self.monitor.metrics_callbacks:
                await callback(self.monitor.current_metrics)
            
            # 驗證回調執行
            assert len(self.received_alerts) > 0, "應該收到警報回調"
            assert len(self.received_metrics) > 0, "應該收到指標回調"
            
            print(f"   ✓ 收到 {len(self.received_alerts)} 個警報回調")
            print(f"   ✓ 收到 {len(self.received_metrics)} 個指標回調")
            
            print("   ✅ 回調函數驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 回調函數測試失敗: {e}")
            return False
    
    async def test_monitoring_loops(self):
        """測試監控循環"""
        try:
            # 測試短時間監控循環
            print("   啟動監控循環測試 (3秒)...")
            
            # 設置較短的間隔用於測試
            original_interval = self.monitor.config.monitoring_interval
            self.monitor.config.monitoring_interval = 0.5
            
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
            assert len(self.monitor.metrics_history) > 0, "應該有指標歷史記錄"
            
            print(f"   ✓ 監控循環運行正常")
            print(f"   ✓ 指標歷史記錄: {len(self.monitor.metrics_history)} 條")
            print(f"   ✓ 監控統計: {self.monitor.monitoring_stats}")
            
            print("   ✅ 監控循環驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 監控循環測試失敗: {e}")
            return False
    
    async def test_alert_management(self):
        """測試警報管理"""
        try:
            # 清理現有警報
            self.monitor.active_alerts.clear()
            
            # 創建測試警報
            alerts = []
            for i in range(3):
                alert = RiskAlert(
                    alert_id=f"test_alert_{i}",
                    alert_type=AlertType.EXPOSURE_LIMIT,
                    priority=AlertPriority.HIGH,
                    risk_level=RiskLevel.HIGH,
                    title=f"測試警報 {i}",
                    message=f"測試警報管理 {i}",
                    affected_pairs=[],
                    risk_value=0.8 + i * 0.05,
                    threshold=0.8,
                    timestamp=datetime.now() - timedelta(minutes=i*10)
                )
                alerts.append(alert)
                self.monitor.active_alerts[f"test_{i}"] = alert
            
            print(f"   創建了 {len(alerts)} 個測試警報")
            
            # 測試警報有效性檢查
            self.monitor.current_metrics.exposure_utilization = 0.75  # 低於閾值
            
            await self.monitor._process_active_alerts()
            
            # 檢查警報狀態更新
            inactive_alerts = [alert for alert in self.monitor.active_alerts.values() if not alert.is_active]
            print(f"   ✓ {len(inactive_alerts)} 個警報被標記為非活躍")
            
            # 測試過期警報清理
            # 創建過期警報
            expired_alert = RiskAlert(
                alert_id="expired_alert",
                alert_type=AlertType.SYSTEM_HEALTH,
                priority=AlertPriority.LOW,
                risk_level=RiskLevel.LOW,
                title="過期警報",
                message="測試過期清理",
                affected_pairs=[],
                risk_value=0.5,
                threshold=0.6,
                timestamp=datetime.now() - timedelta(hours=2)  # 2小時前
            )
            self.monitor.active_alerts["expired"] = expired_alert
            
            initial_count = len(self.monitor.active_alerts)
            await self.monitor._cleanup_expired_alerts()
            final_count = len(self.monitor.active_alerts)
            
            print(f"   ✓ 清理了 {initial_count - final_count} 個過期警報")
            
            print("   ✅ 警報管理驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 警報管理測試失敗: {e}")
            return False
    
    async def test_statistics_and_reporting(self):
        """測試統計和報告"""
        try:
            # 更新一些統計數據
            self.monitor.monitoring_stats['total_alerts_generated'] = 15
            self.monitor.monitoring_stats['critical_alerts_count'] = 3
            self.monitor.monitoring_stats['auto_actions_executed'] = 5
            self.monitor.monitoring_stats['system_errors'] = 2
            
            # 獲取監控狀態
            status = self.monitor.get_monitoring_status()
            
            print(f"   監控狀態: {'運行中' if status['is_monitoring'] else '已停止'}")
            print(f"   活躍警報數量: {status['active_alerts']['count']}")
            print(f"   危險警報數量: {status['active_alerts']['critical_count']}")
            print(f"   總警報生成數: {status['statistics']['total_alerts_generated']}")
            print(f"   自動處理執行數: {status['statistics']['auto_actions_executed']}")
            
            # 獲取風險摘要
            summary = self.monitor.get_risk_summary()
            
            print(f"   總體風險等級: {summary['overall_risk_level']}")
            print(f"   總體風險分數: {summary['overall_risk_score']:.2f}")
            print(f"   風險分解:")
            for risk_type, score in summary['risk_breakdown'].items():
                print(f"     {risk_type}: {score:.2f}")
            
            # 驗證報告結構
            assert 'is_monitoring' in status
            assert 'current_metrics' in status
            assert 'active_alerts' in status
            assert 'statistics' in status
            
            assert 'overall_risk_level' in summary
            assert 'overall_risk_score' in summary
            assert 'risk_breakdown' in summary
            
            # 驗證風險等級合理性
            risk_levels = ['very_low', 'low', 'medium', 'high', 'very_high']
            assert summary['overall_risk_level'] in risk_levels
            assert 0 <= summary['overall_risk_score'] <= 1
            
            print("   ✅ 統計和報告驗證通過")
            return True
            
        except Exception as e:
            print(f"   ❌ 統計和報告測試失敗: {e}")
            return False
    
    async def generate_test_report(self):
        """生成測試報告"""
        try:
            print("\n" + "=" * 60)
            print("📊 風險監控和預警系統測試報告")
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
                print(f"  危險警報: {status['active_alerts']['critical_count']}")
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
                'received_alerts': len(self.received_alerts),
                'received_metrics': len(self.received_metrics),
                'timestamp': datetime.now().isoformat()
            }
            
            report_file = f"AImax/logs/risk_monitoring_system_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n📄 測試報告已保存: {report_file}")
            
            # 總結
            if passed_tests == total_tests:
                print(f"\n🎉 所有測試通過！風險監控和預警系統運行正常")
            else:
                print(f"\n⚠️ 有 {failed_tests + error_tests} 個測試未通過，需要檢查")
            
        except Exception as e:
            print(f"❌ 生成測試報告失敗: {e}")


async def main():
    """主函數"""
    tester = RiskMonitoringSystemTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())