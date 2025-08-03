#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能監控系統測試腳本
測試記憶體監控、UI響應監控和更新頻率優化功能
"""

import sys
import os
import time
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.gui.performance_monitor import (
    PerformanceMonitor,
    MemoryMonitor,
    UIResponseMonitor,
    UpdateRateOptimizer
)


class PerformanceMonitorTester:
    """性能監控系統測試器"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.test_results = {}
        self.current_test = 0
        self.total_tests = 5
        
    def run_all_tests(self):
        """運行所有測試"""
        print("🧪 性能監控系統測試開始")
        print("=" * 50)
        
        tests = [
            ("記憶體監控器測試", self.test_memory_monitor),
            ("UI響應監控器測試", self.test_ui_response_monitor),
            ("更新頻率優化器測試", self.test_update_rate_optimizer),
            ("完整性能監控測試", self.test_full_performance_monitor),
            ("性能壓力測試", self.test_performance_stress)
        ]
        
        for test_name, test_func in tests:
            self.current_test += 1
            print(f"\\n📋 測試 {self.current_test}/{self.total_tests}: {test_name}")
            print("-" * 30)
            
            try:
                result = test_func()
                self.test_results[test_name] = {
                    'success': True,
                    'result': result,
                    'error': None
                }
                print(f"✅ {test_name} 通過")
                
            except Exception as e:
                self.test_results[test_name] = {
                    'success': False,
                    'result': None,
                    'error': str(e)
                }
                print(f"❌ {test_name} 失敗: {e}")
        
        self.print_summary()
        return self.test_results
    
    def test_memory_monitor(self):
        """測試記憶體監控器"""
        monitor = MemoryMonitor(alert_threshold_mb=100.0)  # 低閾值用於測試
        
        # 記錄監控數據
        memory_data = []
        alerts = []
        
        def on_memory_updated(data):
            memory_data.append(data)
        
        def on_memory_alert(alert):
            alerts.append(alert)
        
        # 連接信號
        monitor.memory_updated.connect(on_memory_updated)
        monitor.memory_alert.connect(on_memory_alert)
        
        # 開始監控
        monitor.start_monitoring(interval_ms=100)  # 快速監控用於測試
        
        # 等待收集數據
        start_time = time.time()
        while len(memory_data) < 5 and time.time() - start_time < 2.0:
            self.app.processEvents()
            time.sleep(0.1)
        
        # 停止監控
        monitor.stop_monitoring()
        
        # 驗證結果
        assert len(memory_data) >= 3, f"應該收集到至少3個記憶體數據點，實際: {len(memory_data)}"
        
        # 檢查數據格式
        latest_data = memory_data[-1]
        required_keys = ['process_memory_mb', 'process_memory_percent', 'system_memory_percent']
        for key in required_keys:
            assert key in latest_data, f"記憶體數據缺少 {key} 欄位"
        
        # 檢查統計資訊
        stats = monitor.get_memory_statistics()
        assert 'current' in stats, "統計資訊應該包含 current"
        assert 'average' in stats, "統計資訊應該包含 average"
        assert stats['samples'] > 0, "應該有樣本數據"
        
        print(f"   收集到 {len(memory_data)} 個記憶體數據點")
        print(f"   當前記憶體使用: {latest_data['process_memory_mb']:.1f}MB")
        print(f"   平均記憶體使用: {stats['average']:.1f}MB")
        
        return {
            'data_points': len(memory_data),
            'alerts': len(alerts),
            'current_memory_mb': latest_data['process_memory_mb'],
            'average_memory_mb': stats['average']
        }
    
    def test_ui_response_monitor(self):
        """測試UI響應監控器"""
        monitor = UIResponseMonitor(alert_threshold_ms=50.0)  # 低閾值用於測試
        
        # 記錄響應數據
        response_data = []
        alerts = []
        
        def on_response_updated(data):
            response_data.append(data)
        
        def on_response_alert(alert):
            alerts.append(alert)
        
        # 連接信號
        monitor.response_time_updated.connect(on_response_updated)
        monitor.response_alert.connect(on_response_alert)
        
        # 開始監控
        monitor.start_monitoring(interval_ms=500)  # 快速測試
        
        # 等待收集數據
        start_time = time.time()
        while len(response_data) < 3 and time.time() - start_time < 3.0:
            self.app.processEvents()
            time.sleep(0.1)
        
        # 停止監控
        monitor.stop_monitoring()
        
        # 驗證結果
        assert len(response_data) >= 2, f"應該收集到至少2個響應數據點，實際: {len(response_data)}"
        
        # 檢查數據格式
        latest_data = response_data[-1]
        assert 'response_time_ms' in latest_data, "響應數據應該包含 response_time_ms"
        assert latest_data['response_time_ms'] >= 0, "響應時間應該為正數"
        
        # 檢查統計資訊
        stats = monitor.get_response_statistics()
        assert 'current' in stats, "統計資訊應該包含 current"
        assert 'average' in stats, "統計資訊應該包含 average"
        
        print(f"   收集到 {len(response_data)} 個響應數據點")
        print(f"   當前響應時間: {latest_data['response_time_ms']:.1f}ms")
        print(f"   平均響應時間: {stats['average']:.1f}ms")
        
        return {
            'data_points': len(response_data),
            'alerts': len(alerts),
            'current_response_ms': latest_data['response_time_ms'],
            'average_response_ms': stats['average']
        }
    
    def test_update_rate_optimizer(self):
        """測試更新頻率優化器"""
        optimizer = UpdateRateOptimizer()
        
        # 測試任務計數器
        task_counters = {
            'high_priority': 0,
            'medium_priority': 0,
            'low_priority': 0
        }
        
        # 註冊測試任務
        def create_test_task(priority):
            def task():
                task_counters[priority] += 1
            return task
        
        optimizer.register_update_task('high_priority', 'test_high', create_test_task('high_priority'))
        optimizer.register_update_task('medium_priority', 'test_medium', create_test_task('medium_priority'))
        optimizer.register_update_task('low_priority', 'test_low', create_test_task('low_priority'))
        
        # 等待任務執行
        start_time = time.time()
        while time.time() - start_time < 3.0:
            self.app.processEvents()
            time.sleep(0.1)
        
        # 驗證結果
        assert task_counters['high_priority'] > 0, "高優先級任務應該被執行"
        
        # 檢查統計資訊
        stats = optimizer.get_update_statistics()
        assert 'high_priority' in stats, "統計資訊應該包含高優先級"
        assert stats['high_priority']['task_count'] == 1, "高優先級應該有1個任務"
        
        print(f"   高優先級任務執行次數: {task_counters['high_priority']}")
        print(f"   中優先級任務執行次數: {task_counters['medium_priority']}")
        print(f"   低優先級任務執行次數: {task_counters['low_priority']}")
        
        return {
            'high_priority_executions': task_counters['high_priority'],
            'medium_priority_executions': task_counters['medium_priority'],
            'low_priority_executions': task_counters['low_priority'],
            'total_tasks': sum(stats[p]['task_count'] for p in stats)
        }
    
    def test_full_performance_monitor(self):
        """測試完整性能監控系統"""
        monitor = PerformanceMonitor()
        
        # 記錄數據
        performance_updates = []
        alerts = []
        suggestions = []
        
        def on_performance_updated(data):
            performance_updates.append(data)
        
        def on_performance_alert(alert):
            alerts.append(alert)
        
        def on_optimization_suggestion(suggestion):
            suggestions.append(suggestion)
        
        # 連接信號
        monitor.performance_updated.connect(on_performance_updated)
        monitor.performance_alert.connect(on_performance_alert)
        monitor.optimization_suggestion.connect(on_optimization_suggestion)
        
        # 註冊測試更新任務
        test_task_count = 0
        
        def test_update_task():
            nonlocal test_task_count
            test_task_count += 1
        
        monitor.register_update_task('high_priority', 'test_integration', test_update_task)
        
        # 開始監控
        monitor.start_monitoring()
        
        # 等待數據收集
        start_time = time.time()
        while len(performance_updates) < 5 and time.time() - start_time < 3.0:
            self.app.processEvents()
            time.sleep(0.1)
        
        # 獲取性能報告
        report = monitor.get_performance_report()
        
        # 停止監控
        monitor.stop_monitoring()
        monitor.cleanup()
        
        # 驗證結果
        assert len(performance_updates) >= 3, f"應該收集到至少3個性能更新，實際: {len(performance_updates)}"
        assert report['monitoring_active'] == False, "監控應該已停止"
        assert 'memory_statistics' in report, "報告應該包含記憶體統計"
        assert 'response_statistics' in report, "報告應該包含響應統計"
        
        print(f"   性能更新數量: {len(performance_updates)}")
        print(f"   警告數量: {len(alerts)}")
        print(f"   優化建議數量: {len(suggestions)}")
        print(f"   測試任務執行次數: {test_task_count}")
        
        return {
            'performance_updates': len(performance_updates),
            'alerts': len(alerts),
            'suggestions': len(suggestions),
            'test_task_executions': test_task_count,
            'report_complete': bool(report)
        }
    
    def test_performance_stress(self):
        """測試性能壓力情況"""
        monitor = PerformanceMonitor()
        
        # 記錄數據
        updates_count = 0
        alerts_count = 0
        
        def on_performance_updated(data):
            nonlocal updates_count
            updates_count += 1
        
        def on_performance_alert(alert):
            nonlocal alerts_count
            alerts_count += 1
        
        # 連接信號
        monitor.performance_updated.connect(on_performance_updated)
        monitor.performance_alert.connect(on_performance_alert)
        
        # 註冊多個更新任務模擬壓力
        task_execution_counts = [0] * 10
        
        for i in range(10):
            def create_stress_task(index):
                def task():
                    task_execution_counts[index] += 1
                    # 模擬一些工作負載
                    time.sleep(0.001)
                return task
            
            priority = ['high_priority', 'medium_priority', 'low_priority'][i % 3]
            monitor.register_update_task(priority, f'stress_task_{i}', create_stress_task(i))
        
        # 開始監控
        monitor.start_monitoring()
        
        # 運行壓力測試
        start_time = time.time()
        while time.time() - start_time < 2.0:
            self.app.processEvents()
            time.sleep(0.01)
        
        # 獲取最終報告
        final_report = monitor.get_performance_report()
        
        # 停止監控
        monitor.stop_monitoring()
        monitor.cleanup()
        
        # 驗證結果
        total_task_executions = sum(task_execution_counts)
        assert total_task_executions > 0, "壓力測試任務應該被執行"
        assert updates_count > 0, "應該有性能更新"
        
        print(f"   總任務執行次數: {total_task_executions}")
        print(f"   性能更新次數: {updates_count}")
        print(f"   警告次數: {alerts_count}")
        print(f"   註冊任務數: {sum(final_report['update_statistics'][p]['task_count'] for p in final_report['update_statistics'])}")
        
        return {
            'total_task_executions': total_task_executions,
            'performance_updates': updates_count,
            'alerts': alerts_count,
            'registered_tasks': sum(final_report['update_statistics'][p]['task_count'] for p in final_report['update_statistics'])
        }
    
    def print_summary(self):
        """打印測試摘要"""
        print("\\n" + "=" * 50)
        print("📊 測試摘要")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"總測試數: {total_tests}")
        print(f"通過測試: {passed_tests}")
        print(f"失敗測試: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\\n❌ 失敗的測試:")
            for test_name, result in self.test_results.items():
                if not result['success']:
                    print(f"   - {test_name}: {result['error']}")
        
        print("\\n✅ 性能監控系統測試完成！")


def main():
    """主函數"""
    try:
        tester = PerformanceMonitorTester()
        results = tester.run_all_tests()
        
        # 返回適當的退出碼
        success_count = sum(1 for r in results.values() if r['success'])
        return 0 if success_count == len(results) else 1
        
    except Exception as e:
        print(f"💥 測試過程中發生嚴重錯誤: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)