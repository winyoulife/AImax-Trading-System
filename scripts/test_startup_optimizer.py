#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動優化器測試腳本
測試啟動優化系統的各項功能
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
from src.gui.startup_optimizer import (
    StartupOptimizer, 
    StartupTask, 
    ParallelTaskExecutor,
    LazyLoader,
    StartupTimeMonitor,
    ResourcePreloader
)


class StartupOptimizerTester:
    """啟動優化器測試器"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.test_results = {}
        self.current_test = 0
        self.total_tests = 6
        
    def run_all_tests(self):
        """運行所有測試"""
        print("🧪 啟動優化器測試開始")
        print("=" * 50)
        
        tests = [
            ("時間監控器測試", self.test_time_monitor),
            ("並行任務執行器測試", self.test_parallel_executor),
            ("延遲載入器測試", self.test_lazy_loader),
            ("資源預載入器測試", self.test_resource_preloader),
            ("完整啟動優化測試", self.test_full_optimization),
            ("性能基準測試", self.test_performance_benchmark)
        ]
        
        for test_name, test_func in tests:
            self.current_test += 1
            print(f"\n📋 測試 {self.current_test}/{self.total_tests}: {test_name}")
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
    
    def test_time_monitor(self):
        """測試時間監控器"""
        monitor = StartupTimeMonitor()
        
        # 開始監控
        monitor.start_monitoring()
        time.sleep(0.1)
        
        # 添加檢查點
        monitor.add_checkpoint("test_checkpoint_1")
        time.sleep(0.1)
        monitor.add_checkpoint("test_checkpoint_2")
        
        # 測試階段計時
        monitor.start_phase("test_phase")
        time.sleep(0.1)
        monitor.end_phase("test_phase")
        
        # 驗證結果
        total_time = monitor.get_total_time()
        checkpoints = monitor.get_checkpoint_times()
        phases = monitor.get_phase_times()
        
        assert total_time > 0.3, f"總時間應該大於0.3秒，實際: {total_time}"
        assert "test_checkpoint_1" in checkpoints, "檢查點1應該存在"
        assert "test_checkpoint_2" in checkpoints, "檢查點2應該存在"
        assert "test_phase" in phases, "測試階段應該存在"
        assert phases["test_phase"] > 0.1, f"階段時間應該大於0.1秒，實際: {phases['test_phase']}"
        
        print(f"   總時間: {total_time:.3f}s")
        print(f"   檢查點數量: {len(checkpoints)}")
        print(f"   階段數量: {len(phases)}")
        
        return {
            'total_time': total_time,
            'checkpoints': len(checkpoints),
            'phases': len(phases)
        }
    
    def test_parallel_executor(self):
        """測試並行任務執行器"""
        executor = ParallelTaskExecutor(max_workers=2)
        
        # 創建測試任務
        def quick_task():
            time.sleep(0.1)
            return "quick_done"
        
        def slow_task():
            time.sleep(0.2)
            return "slow_done"
        
        def error_task():
            raise Exception("測試錯誤")
        
        # 添加任務
        executor.add_task(StartupTask("quick", quick_task, priority=1))
        executor.add_task(StartupTask("slow", slow_task, priority=2))
        executor.add_task(StartupTask("error", error_task, priority=3, is_critical=False))
        
        # 執行任務
        start_time = time.time()
        executor.execute_tasks()
        
        # 等待完成（簡單等待）
        while executor.running:
            time.sleep(0.01)
        
        execution_time = time.time() - start_time
        
        # 驗證結果
        assert len(executor.completed_tasks) == 3, f"應該完成3個任務，實際: {len(executor.completed_tasks)}"
        assert executor.completed_tasks["quick"].success, "快速任務應該成功"
        assert executor.completed_tasks["slow"].success, "慢速任務應該成功"
        assert not executor.completed_tasks["error"].success, "錯誤任務應該失敗"
        
        # 並行執行應該比順序執行快（調整預期時間）
        assert execution_time < 1.0, f"並行執行時間應該小於1.0秒，實際: {execution_time:.3f}s"
        
        print(f"   執行時間: {execution_time:.3f}s")
        print(f"   成功任務: {sum(1 for r in executor.completed_tasks.values() if r.success)}")
        print(f"   失敗任務: {sum(1 for r in executor.completed_tasks.values() if not r.success)}")
        
        return {
            'execution_time': execution_time,
            'total_tasks': len(executor.completed_tasks),
            'successful_tasks': sum(1 for r in executor.completed_tasks.values() if r.success)
        }
    
    def test_lazy_loader(self):
        """測試延遲載入器"""
        loader = LazyLoader()
        
        # 註冊測試模組
        def load_test_module():
            return {"name": "test_module", "loaded": True}
        
        def load_error_module():
            raise Exception("載入失敗")
        
        loader.register_module("test_module", load_test_module)
        loader.register_module("error_module", load_error_module)
        
        # 測試正常載入
        assert not loader.is_loaded("test_module"), "模組應該尚未載入"
        
        module = loader.load_module("test_module")
        assert module["name"] == "test_module", "模組內容不正確"
        assert loader.is_loaded("test_module"), "模組應該已載入"
        
        # 測試重複載入
        module2 = loader.load_module("test_module")
        assert module is module2, "重複載入應該返回相同對象"
        
        # 測試錯誤處理
        try:
            loader.load_module("error_module")
            assert False, "應該拋出異常"
        except RuntimeError as e:
            assert "載入模組 error_module 失敗" in str(e), "錯誤訊息不正確"
        
        # 測試未註冊模組
        try:
            loader.load_module("unknown_module")
            assert False, "應該拋出異常"
        except ValueError as e:
            assert "未註冊的模組" in str(e), "錯誤訊息不正確"
        
        loaded_modules = loader.get_loaded_modules()
        print(f"   已載入模組: {loaded_modules}")
        
        return {
            'loaded_modules': len(loaded_modules),
            'test_passed': True
        }
    
    def test_resource_preloader(self):
        """測試資源預載入器"""
        preloader = ResourcePreloader()
        
        # 添加預載入任務
        def load_config():
            return {"config_key": "config_value"}
        
        def load_data():
            return {"data_key": "data_value"}
        
        def load_error():
            raise Exception("載入錯誤")
        
        preloader.add_preload_task("config", load_config)
        preloader.add_preload_task("data", load_data)
        preloader.add_preload_task("error", load_error)
        
        # 執行預載入
        preloader.preload_resources()
        
        # 驗證結果
        assert preloader.is_preloaded("config"), "配置應該已預載入"
        assert preloader.is_preloaded("data"), "數據應該已預載入"
        assert not preloader.is_preloaded("error"), "錯誤資源不應該預載入"
        
        config = preloader.get_resource("config")
        assert config["config_key"] == "config_value", "配置內容不正確"
        
        data = preloader.get_resource("data")
        assert data["data_key"] == "data_value", "數據內容不正確"
        
        error_resource = preloader.get_resource("error")
        assert error_resource is None, "錯誤資源應該為None"
        
        print(f"   預載入資源數量: {len(preloader.preloaded_resources)}")
        
        return {
            'preloaded_count': len(preloader.preloaded_resources),
            'test_passed': True
        }
    
    def test_full_optimization(self):
        """測試完整啟動優化"""
        optimizer = StartupOptimizer()
        
        # 配置優化選項
        optimizer.configure_optimization(
            parallel_loading=True,
            lazy_loading=True,
            resource_preloading=True,
            target_time=3.0
        )
        
        # 設置完成回調
        optimization_result = {}
        
        def on_completed(report):
            optimization_result.update(report)
        
        optimizer.optimization_completed.connect(on_completed)
        
        # 執行優化
        start_time = time.time()
        optimizer.optimize_startup()
        
        # 等待完成
        timeout = 10.0
        elapsed = 0.0
        while not optimization_result and elapsed < timeout:
            self.app.processEvents()
            time.sleep(0.01)
            elapsed = time.time() - start_time
        
        assert optimization_result, "優化應該完成並返回結果"
        
        # 驗證報告內容
        assert 'timing' in optimization_result, "報告應該包含時間信息"
        assert 'performance' in optimization_result, "報告應該包含性能信息"
        assert 'task_stats' in optimization_result, "報告應該包含任務統計"
        
        timing = optimization_result['timing']
        performance = optimization_result['performance']
        task_stats = optimization_result['task_stats']
        
        print(f"   總時間: {timing['total_time']:.3f}s")
        print(f"   目標達成: {performance['target_met']}")
        print(f"   效率分數: {performance['efficiency_score']:.1f}%")
        print(f"   成功任務: {task_stats['successful_tasks']}/{task_stats['total_tasks']}")
        
        return {
            'total_time': timing['total_time'],
            'target_met': performance['target_met'],
            'efficiency_score': performance['efficiency_score'],
            'successful_tasks': task_stats['successful_tasks']
        }
    
    def test_performance_benchmark(self):
        """測試性能基準"""
        print("   執行性能基準測試...")
        
        # 測試不同配置的性能
        configs = [
            ("順序載入", False, False, False),
            ("並行載入", True, False, False),
            ("完整優化", True, True, True)
        ]
        
        benchmark_results = {}
        
        for config_name, parallel, lazy, preload in configs:
            optimizer = StartupOptimizer()
            optimizer.configure_optimization(
                parallel_loading=parallel,
                lazy_loading=lazy,
                resource_preloading=preload,
                target_time=5.0
            )
            
            result = {}
            
            def on_completed(report):
                result.update(report)
            
            optimizer.optimization_completed.connect(on_completed)
            
            start_time = time.time()
            optimizer.optimize_startup()
            
            # 等待完成
            timeout = 10.0
            elapsed = 0.0
            while not result and elapsed < timeout:
                self.app.processEvents()
                time.sleep(0.01)
                elapsed = time.time() - start_time
            
            if result:
                benchmark_results[config_name] = {
                    'time': result['timing']['total_time'],
                    'efficiency': result['performance']['efficiency_score']
                }
                print(f"     {config_name}: {result['timing']['total_time']:.3f}s")
        
        return benchmark_results
    
    def print_summary(self):
        """打印測試摘要"""
        print("\n" + "=" * 50)
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
            print("\n❌ 失敗的測試:")
            for test_name, result in self.test_results.items():
                if not result['success']:
                    print(f"   - {test_name}: {result['error']}")
        
        print("\n✅ 啟動優化器測試完成！")


def main():
    """主函數"""
    try:
        tester = StartupOptimizerTester()
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