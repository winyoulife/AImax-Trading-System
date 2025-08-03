#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI啟動測試腳本
測試GUI啟動時間、穩定性和功能完整性
驗證5秒啟動需求和30分鐘穩定運行
"""

import sys
import os
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QThread, pyqtSignal


class StartupTimeTest:
    """啟動時間測試"""
    
    def __init__(self):
        self.target_startup_time = 5.0  # 目標啟動時間（秒）
        
    def test_startup_time(self) -> dict:
        """測試啟動時間"""
        print("🚀 測試GUI啟動時間...")
        
        try:
            # 記錄開始時間
            start_time = time.time()
            
            # 導入GUI啟動器
            from src.gui.simple_gui_launcher import SimpleGUILauncher
            
            # 創建應用程式
            app = QApplication(sys.argv)
            
            # 創建GUI啟動器
            launcher = SimpleGUILauncher()
            
            # 設置啟動完成回調
            startup_completed = False
            startup_error = None
            
            def on_gui_ready(main_window):
                nonlocal startup_completed
                startup_completed = True
            
            def on_launch_failed(error_message):
                nonlocal startup_error
                startup_error = error_message
            
            # 連接信號
            launcher.gui_ready.connect(on_gui_ready)
            launcher.launch_failed.connect(on_launch_failed)
            
            # 啟動GUI
            if not launcher.launch_gui():
                return {
                    'success': False,
                    'startup_time': 0,
                    'error': 'GUI啟動失敗'
                }
            
            # 等待啟動完成或超時
            timeout = 10.0  # 10秒超時
            elapsed = 0.0
            
            while not startup_completed and startup_error is None and elapsed < timeout:
                app.processEvents()
                time.sleep(0.01)
                elapsed = time.time() - start_time
            
            # 計算啟動時間
            startup_time = time.time() - start_time
            
            # 清理資源
            launcher.cleanup()
            
            # 檢查結果
            if startup_error:
                return {
                    'success': False,
                    'startup_time': startup_time,
                    'error': startup_error
                }
            
            if not startup_completed:
                return {
                    'success': False,
                    'startup_time': startup_time,
                    'error': '啟動超時'
                }
            
            # 檢查是否達到目標時間
            target_met = startup_time <= self.target_startup_time
            
            return {
                'success': True,
                'startup_time': startup_time,
                'target_time': self.target_startup_time,
                'target_met': target_met,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'startup_time': 0,
                'error': str(e)
            }


class StabilityTest(QThread):
    """穩定性測試線程"""
    
    progress_updated = pyqtSignal(str, float)  # 消息, 進度百分比
    test_completed = pyqtSignal(dict)  # 測試結果
    
    def __init__(self, duration_minutes: int = 30):
        super().__init__()
        self.duration_minutes = duration_minutes
        self.running = False
        
    def run(self):
        """運行穩定性測試"""
        self.running = True
        
        try:
            print(f"🔄 開始{self.duration_minutes}分鐘穩定性測試...")
            
            # 導入GUI組件
            from src.gui.simple_gui_launcher import SimpleGUILauncher
            from src.gui.performance_monitor import PerformanceMonitor
            
            # 創建應用程式
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
            
            # 創建GUI啟動器
            launcher = SimpleGUILauncher()
            
            # 創建性能監控器
            monitor = PerformanceMonitor()
            
            # 記錄測試數據
            test_data = {
                'start_time': datetime.now(),
                'errors': [],
                'performance_alerts': [],
                'memory_peaks': [],
                'response_times': []
            }
            
            # 設置回調
            def on_performance_alert(alert):
                test_data['performance_alerts'].append({
                    'timestamp': datetime.now(),
                    'message': alert.message,
                    'severity': alert.severity
                })
            
            def on_performance_updated(data):
                if data['category'] == 'memory':
                    memory_mb = data['data']['process_memory_mb']
                    test_data['memory_peaks'].append(memory_mb)
                elif data['category'] == 'ui_response':
                    response_ms = data['data']['response_time_ms']
                    test_data['response_times'].append(response_ms)
            
            # 連接信號
            monitor.performance_alert.connect(on_performance_alert)
            monitor.performance_updated.connect(on_performance_updated)
            
            # 啟動GUI
            if not launcher.launch_gui():
                self.test_completed.emit({
                    'success': False,
                    'error': 'GUI啟動失敗',
                    'duration': 0
                })
                return
            
            # 開始性能監控
            monitor.start_monitoring()
            
            # 運行測試
            duration_seconds = self.duration_minutes * 60
            start_time = time.time()
            
            while self.running and (time.time() - start_time) < duration_seconds:
                try:
                    # 處理事件
                    app.processEvents()
                    
                    # 更新進度
                    elapsed = time.time() - start_time
                    progress = (elapsed / duration_seconds) * 100
                    remaining_minutes = (duration_seconds - elapsed) / 60
                    
                    self.progress_updated.emit(
                        f"穩定性測試進行中... 剩餘 {remaining_minutes:.1f} 分鐘",
                        progress
                    )
                    
                    # 短暫休息
                    time.sleep(0.1)
                    
                except Exception as e:
                    test_data['errors'].append({
                        'timestamp': datetime.now(),
                        'error': str(e)
                    })
            
            # 停止監控
            monitor.stop_monitoring()
            monitor.cleanup()
            
            # 清理資源
            launcher.cleanup()
            
            # 計算結果
            actual_duration = time.time() - start_time
            test_data['end_time'] = datetime.now()
            test_data['actual_duration'] = actual_duration
            
            # 分析結果
            result = self._analyze_stability_results(test_data)
            
            self.test_completed.emit(result)
            
        except Exception as e:
            self.test_completed.emit({
                'success': False,
                'error': str(e),
                'duration': 0
            })
    
    def stop_test(self):
        """停止測試"""
        self.running = False
    
    def _analyze_stability_results(self, test_data: dict) -> dict:
        """分析穩定性測試結果"""
        try:
            # 基本統計
            error_count = len(test_data['errors'])
            alert_count = len(test_data['performance_alerts'])
            
            # 記憶體分析
            memory_stats = {}
            if test_data['memory_peaks']:
                memory_stats = {
                    'max_memory_mb': max(test_data['memory_peaks']),
                    'avg_memory_mb': sum(test_data['memory_peaks']) / len(test_data['memory_peaks']),
                    'memory_samples': len(test_data['memory_peaks'])
                }
            
            # 響應時間分析
            response_stats = {}
            if test_data['response_times']:
                response_stats = {
                    'max_response_ms': max(test_data['response_times']),
                    'avg_response_ms': sum(test_data['response_times']) / len(test_data['response_times']),
                    'response_samples': len(test_data['response_times'])
                }
            
            # 判斷成功標準
            success = (
                error_count == 0 and  # 無錯誤
                alert_count < 10 and  # 警告數量少
                test_data['actual_duration'] >= (self.duration_minutes * 60 * 0.9)  # 至少運行90%時間
            )
            
            return {
                'success': success,
                'duration_minutes': test_data['actual_duration'] / 60,
                'error_count': error_count,
                'alert_count': alert_count,
                'memory_stats': memory_stats,
                'response_stats': response_stats,
                'errors': test_data['errors'][-5:],  # 最後5個錯誤
                'start_time': test_data['start_time'].isoformat(),
                'end_time': test_data['end_time'].isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'結果分析失敗: {str(e)}',
                'duration_minutes': 0
            }


class IntegrationTest:
    """AI系統整合測試"""
    
    def __init__(self):
        pass
    
    def test_ai_integration(self) -> dict:
        """測試AI系統整合"""
        print("🤖 測試AI系統整合...")
        
        try:
            # 測試AI組件導入
            ai_components = [
                ('AI管理器', 'src.ai.ai_manager', 'AIManager'),
                ('交易執行器', 'src.trading.trade_executor', 'TradeExecutor'),
                ('風險管理器', 'src.trading.risk_manager', 'RiskManager'),
                ('系統整合器', 'src.core.trading_system_integrator', 'TradingSystemIntegrator')
            ]
            
            import_results = []
            
            for name, module_path, class_name in ai_components:
                try:
                    module = __import__(module_path, fromlist=[class_name])
                    component_class = getattr(module, class_name)
                    
                    # 嘗試創建實例（基本測試）
                    instance = component_class()
                    
                    import_results.append({
                        'name': name,
                        'success': True,
                        'error': None
                    })
                    
                except Exception as e:
                    import_results.append({
                        'name': name,
                        'success': False,
                        'error': str(e)
                    })
            
            # 計算成功率
            successful_imports = sum(1 for r in import_results if r['success'])
            total_imports = len(import_results)
            success_rate = (successful_imports / total_imports) * 100
            
            return {
                'success': success_rate >= 75,  # 至少75%成功率
                'success_rate': success_rate,
                'successful_imports': successful_imports,
                'total_imports': total_imports,
                'import_results': import_results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'success_rate': 0
            }


class GUITestSuite:
    """GUI測試套件"""
    
    def __init__(self):
        self.startup_test = StartupTimeTest()
        self.integration_test = IntegrationTest()
        
    def run_quick_tests(self) -> dict:
        """運行快速測試"""
        print("🧪 開始GUI快速測試套件")
        print("=" * 50)
        
        results = {}
        
        # 測試1: 啟動時間測試
        print("\\n📋 測試 1/2: 啟動時間測試")
        print("-" * 30)
        
        startup_result = self.startup_test.test_startup_time()
        results['startup_time'] = startup_result
        
        if startup_result['success']:
            print(f"✅ 啟動時間測試通過")
            print(f"   啟動時間: {startup_result['startup_time']:.2f}s")
            print(f"   目標時間: {startup_result['target_time']}s")
            print(f"   目標達成: {'是' if startup_result['target_met'] else '否'}")
        else:
            print(f"❌ 啟動時間測試失敗: {startup_result['error']}")
        
        # 測試2: AI系統整合測試
        print("\\n📋 測試 2/2: AI系統整合測試")
        print("-" * 30)
        
        integration_result = self.integration_test.test_ai_integration()
        results['ai_integration'] = integration_result
        
        if integration_result['success']:
            print(f"✅ AI系統整合測試通過")
            print(f"   成功率: {integration_result['success_rate']:.1f}%")
            print(f"   成功組件: {integration_result['successful_imports']}/{integration_result['total_imports']}")
        else:
            print(f"❌ AI系統整合測試失敗")
            if 'error' in integration_result:
                print(f"   錯誤: {integration_result['error']}")
            else:
                print(f"   成功率: {integration_result['success_rate']:.1f}%")
        
        # 打印摘要
        self._print_quick_test_summary(results)
        
        return results
    
    def run_stability_test(self, duration_minutes: int = 30) -> dict:
        """運行穩定性測試"""
        print(f"🔄 開始{duration_minutes}分鐘穩定性測試")
        print("=" * 50)
        
        # 創建應用程式
        app = QApplication(sys.argv)
        
        # 創建穩定性測試線程
        stability_test = StabilityTest(duration_minutes)
        
        # 測試結果
        test_result = {}
        
        def on_progress_updated(message, progress):
            print(f"\\r{message} ({progress:.1f}%)", end="", flush=True)
        
        def on_test_completed(result):
            nonlocal test_result
            test_result = result
            app.quit()
        
        # 連接信號
        stability_test.progress_updated.connect(on_progress_updated)
        stability_test.test_completed.connect(on_test_completed)
        
        # 開始測試
        stability_test.start()
        
        # 運行應用程式
        app.exec()
        
        # 等待線程完成
        stability_test.wait()
        
        # 打印結果
        print("\\n")  # 換行
        self._print_stability_test_result(test_result)
        
        return test_result
    
    def _print_quick_test_summary(self, results: dict):
        """打印快速測試摘要"""
        print("\\n" + "=" * 50)
        print("📊 快速測試摘要")
        print("=" * 50)
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r['success'])
        
        print(f"總測試數: {total_tests}")
        print(f"通過測試: {passed_tests}")
        print(f"失敗測試: {total_tests - passed_tests}")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        # 詳細結果
        if results['startup_time']['success']:
            startup_time = results['startup_time']['startup_time']
            target_met = results['startup_time']['target_met']
            print(f"\\n🚀 啟動性能:")
            print(f"   啟動時間: {startup_time:.2f}s")
            print(f"   目標達成: {'✅' if target_met else '❌'}")
        
        if results['ai_integration']['success']:
            success_rate = results['ai_integration']['success_rate']
            print(f"\\n🤖 AI整合:")
            print(f"   整合成功率: {success_rate:.1f}%")
        
        print("\\n✅ 快速測試完成！")
    
    def _print_stability_test_result(self, result: dict):
        """打印穩定性測試結果"""
        print("=" * 50)
        print("📊 穩定性測試結果")
        print("=" * 50)
        
        if result['success']:
            print("✅ 穩定性測試通過")
            print(f"   運行時間: {result['duration_minutes']:.1f} 分鐘")
            print(f"   錯誤數量: {result['error_count']}")
            print(f"   警告數量: {result['alert_count']}")
            
            if 'memory_stats' in result and result['memory_stats']:
                memory = result['memory_stats']
                print(f"   記憶體使用: 平均 {memory['avg_memory_mb']:.1f}MB, 峰值 {memory['max_memory_mb']:.1f}MB")
            
            if 'response_stats' in result and result['response_stats']:
                response = result['response_stats']
                print(f"   響應時間: 平均 {response['avg_response_ms']:.1f}ms, 最大 {response['max_response_ms']:.1f}ms")
        else:
            print("❌ 穩定性測試失敗")
            if 'error' in result:
                print(f"   錯誤: {result['error']}")
            else:
                print(f"   運行時間: {result.get('duration_minutes', 0):.1f} 分鐘")
                print(f"   錯誤數量: {result.get('error_count', 0)}")
        
        print("\\n🔄 穩定性測試完成！")


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GUI測試套件')
    parser.add_argument('--quick', action='store_true', help='運行快速測試')
    parser.add_argument('--stability', type=int, default=30, help='運行穩定性測試（分鐘）')
    parser.add_argument('--all', action='store_true', help='運行所有測試')
    
    args = parser.parse_args()
    
    # 創建測試套件
    test_suite = GUITestSuite()
    
    try:
        if args.quick or args.all:
            # 運行快速測試
            quick_results = test_suite.run_quick_tests()
            
            if not args.all:
                # 返回適當的退出碼
                success_count = sum(1 for r in quick_results.values() if r['success'])
                return 0 if success_count == len(quick_results) else 1
        
        if args.stability or args.all:
            # 運行穩定性測試
            duration = args.stability if args.stability else 30
            stability_result = test_suite.run_stability_test(duration)
            
            return 0 if stability_result['success'] else 1
        
        if not any([args.quick, args.stability, args.all]):
            # 默認運行快速測試
            quick_results = test_suite.run_quick_tests()
            success_count = sum(1 for r in quick_results.values() if r['success'])
            return 0 if success_count == len(quick_results) else 1
        
        return 0
        
    except Exception as e:
        print(f"💥 測試過程中發生嚴重錯誤: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)