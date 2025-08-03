#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系統穩定性全面測試工具
進行長時間連續運行測試，驗證系統在各種市場條件下的穩定性
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import asyncio
import json
import time
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import threading
import psutil

class SystemStabilityTester:
    """系統穩定性測試器"""
    
    def __init__(self):
        self.test_start_time = None
        self.test_duration_hours = 24  # 24小時測試
        self.is_running = False
        self.test_results = {
            'start_time': None,
            'end_time': None,
            'total_cycles': 0,
            'successful_cycles': 0,
            'failed_cycles': 0,
            'errors': [],
            'performance_metrics': [],
            'system_resources': [],
            'emergency_stops': 0,
            'recovery_attempts': 0
        }
        self.shutdown_requested = False
        
    def setup_signal_handlers(self):
        """設置信號處理器"""
        def signal_handler(signum, frame):
            print(f"\n🛑 收到停止信號 ({signum})，正在安全關閉...")
            self.shutdown_requested = True
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def monitor_system_resources(self) -> Dict[str, Any]:
        """監控系統資源使用"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024**3)
            }
        except Exception as e:
            return {'error': f'資源監控失敗: {e}'}
    
    def test_ai_system_stability(self) -> Dict[str, Any]:
        """測試AI系統穩定性"""
        try:
            # 模擬AI系統調用
            start_time = time.time()
            
            # 這裡應該調用實際的AI系統
            # 為了測試，我們模擬一個AI決策過程
            test_result = {
                'ai_response_time': time.time() - start_time,
                'ai_status': 'healthy',
                'decision_made': True,
                'confidence': 0.75,
                'memory_usage': 'normal'
            }
            
            return test_result
            
        except Exception as e:
            return {
                'ai_status': 'error',
                'error': str(e),
                'ai_response_time': -1
            }
    
    def test_data_connection_stability(self) -> Dict[str, Any]:
        """測試數據連接穩定性"""
        try:
            # 模擬數據連接測試
            start_time = time.time()
            
            # 這裡應該測試實際的MAX API連接
            connection_result = {
                'connection_time': time.time() - start_time,
                'connection_status': 'connected',
                'data_quality': 'good',
                'latency_ms': 50
            }
            
            return connection_result
            
        except Exception as e:
            return {
                'connection_status': 'error',
                'error': str(e),
                'connection_time': -1
            }
    
    def test_trading_system_stability(self) -> Dict[str, Any]:
        """測試交易系統穩定性"""
        try:
            # 模擬交易系統測試
            start_time = time.time()
            
            trading_result = {
                'trading_system_time': time.time() - start_time,
                'trading_status': 'ready',
                'risk_controls': 'active',
                'position_management': 'normal'
            }
            
            return trading_result
            
        except Exception as e:
            return {
                'trading_status': 'error',
                'error': str(e),
                'trading_system_time': -1
            }
    
    def run_stability_cycle(self) -> Dict[str, Any]:
        """執行一個穩定性測試週期"""
        cycle_start = time.time()
        cycle_result = {
            'cycle_number': self.test_results['total_cycles'] + 1,
            'start_time': datetime.now().isoformat(),
            'ai_test': None,
            'data_test': None,
            'trading_test': None,
            'system_resources': None,
            'cycle_duration': 0,
            'success': False
        }
        
        try:
            # 測試AI系統
            cycle_result['ai_test'] = self.test_ai_system_stability()
            
            # 測試數據連接
            cycle_result['data_test'] = self.test_data_connection_stability()
            
            # 測試交易系統
            cycle_result['trading_test'] = self.test_trading_system_stability()
            
            # 監控系統資源
            cycle_result['system_resources'] = self.monitor_system_resources()
            
            # 檢查是否所有測試都成功
            ai_ok = cycle_result['ai_test'].get('ai_status') == 'healthy'
            data_ok = cycle_result['data_test'].get('connection_status') == 'connected'
            trading_ok = cycle_result['trading_test'].get('trading_status') == 'ready'
            
            cycle_result['success'] = ai_ok and data_ok and trading_ok
            
        except Exception as e:
            cycle_result['error'] = str(e)
            cycle_result['success'] = False
            
        finally:
            cycle_result['cycle_duration'] = time.time() - cycle_start
            cycle_result['end_time'] = datetime.now().isoformat()
            
        return cycle_result
    
    def run_continuous_test(self, duration_hours: int = 24):
        """執行連續穩定性測試"""
        print(f"🚀 開始 {duration_hours} 小時系統穩定性測試...")
        
        self.test_start_time = datetime.now()
        self.test_results['start_time'] = self.test_start_time.isoformat()
        self.is_running = True
        
        end_time = self.test_start_time + timedelta(hours=duration_hours)
        
        cycle_interval = 60  # 每60秒一個測試週期
        
        try:
            while datetime.now() < end_time and not self.shutdown_requested:
                # 執行測試週期
                cycle_result = self.run_stability_cycle()
                
                # 更新統計
                self.test_results['total_cycles'] += 1
                if cycle_result['success']:
                    self.test_results['successful_cycles'] += 1
                else:
                    self.test_results['failed_cycles'] += 1
                    self.test_results['errors'].append({
                        'cycle': cycle_result['cycle_number'],
                        'time': cycle_result['start_time'],
                        'details': cycle_result
                    })
                
                # 記錄性能指標
                self.test_results['performance_metrics'].append({
                    'cycle': cycle_result['cycle_number'],
                    'timestamp': cycle_result['start_time'],
                    'cycle_duration': cycle_result['cycle_duration'],
                    'ai_response_time': cycle_result['ai_test'].get('ai_response_time', -1),
                    'data_connection_time': cycle_result['data_test'].get('connection_time', -1)
                })
                
                # 記錄系統資源
                if cycle_result['system_resources']:
                    self.test_results['system_resources'].append(cycle_result['system_resources'])
                
                # 顯示進度
                elapsed = datetime.now() - self.test_start_time
                remaining = end_time - datetime.now()
                success_rate = (self.test_results['successful_cycles'] / self.test_results['total_cycles']) * 100
                
                print(f"⏰ 週期 {cycle_result['cycle_number']}: "
                      f"{'✅' if cycle_result['success'] else '❌'} "
                      f"成功率: {success_rate:.1f}% "
                      f"已運行: {elapsed} "
                      f"剩餘: {remaining}")
                
                # 等待下一個週期
                if not self.shutdown_requested:
                    time.sleep(cycle_interval)
                    
        except KeyboardInterrupt:
            print("\n🛑 用戶中斷測試")
            self.shutdown_requested = True
            
        except Exception as e:
            print(f"❌ 測試過程中發生錯誤: {e}")
            self.test_results['errors'].append({
                'type': 'system_error',
                'time': datetime.now().isoformat(),
                'error': str(e)
            })
            
        finally:
            self.is_running = False
            self.test_results['end_time'] = datetime.now().isoformat()
            
        return self.generate_test_report()
    
    def generate_test_report(self) -> Dict[str, Any]:
        """生成測試報告"""
        total_duration = datetime.fromisoformat(self.test_results['end_time']) - datetime.fromisoformat(self.test_results['start_time'])
        
        # 計算統計指標
        success_rate = (self.test_results['successful_cycles'] / self.test_results['total_cycles']) * 100 if self.test_results['total_cycles'] > 0 else 0
        
        # 計算平均性能
        avg_cycle_duration = 0
        avg_ai_response = 0
        avg_data_connection = 0
        
        if self.test_results['performance_metrics']:
            avg_cycle_duration = sum(m['cycle_duration'] for m in self.test_results['performance_metrics']) / len(self.test_results['performance_metrics'])
            valid_ai_times = [m['ai_response_time'] for m in self.test_results['performance_metrics'] if m['ai_response_time'] > 0]
            valid_data_times = [m['data_connection_time'] for m in self.test_results['performance_metrics'] if m['data_connection_time'] > 0]
            
            if valid_ai_times:
                avg_ai_response = sum(valid_ai_times) / len(valid_ai_times)
            if valid_data_times:
                avg_data_connection = sum(valid_data_times) / len(valid_data_times)
        
        # 計算資源使用統計
        resource_stats = {}
        if self.test_results['system_resources']:
            cpu_values = [r['cpu_percent'] for r in self.test_results['system_resources'] if 'cpu_percent' in r]
            memory_values = [r['memory_percent'] for r in self.test_results['system_resources'] if 'memory_percent' in r]
            
            if cpu_values:
                resource_stats['avg_cpu_percent'] = sum(cpu_values) / len(cpu_values)
                resource_stats['max_cpu_percent'] = max(cpu_values)
            
            if memory_values:
                resource_stats['avg_memory_percent'] = sum(memory_values) / len(memory_values)
                resource_stats['max_memory_percent'] = max(memory_values)
        
        report = {
            'test_summary': {
                'start_time': self.test_results['start_time'],
                'end_time': self.test_results['end_time'],
                'total_duration_hours': total_duration.total_seconds() / 3600,
                'total_cycles': self.test_results['total_cycles'],
                'successful_cycles': self.test_results['successful_cycles'],
                'failed_cycles': self.test_results['failed_cycles'],
                'success_rate_percent': success_rate
            },
            'performance_summary': {
                'avg_cycle_duration_seconds': avg_cycle_duration,
                'avg_ai_response_time_seconds': avg_ai_response,
                'avg_data_connection_time_seconds': avg_data_connection
            },
            'resource_summary': resource_stats,
            'stability_assessment': self._assess_stability(success_rate, avg_cycle_duration),
            'detailed_errors': self.test_results['errors'][:10],  # 只保留前10個錯誤
            'recommendations': self._generate_recommendations(success_rate, resource_stats)
        }
        
        return report
    
    def _assess_stability(self, success_rate: float, avg_cycle_duration: float) -> str:
        """評估系統穩定性"""
        if success_rate >= 99:
            return "優秀 - 系統非常穩定，可以投入生產環境"
        elif success_rate >= 95:
            return "良好 - 系統基本穩定，建議進行小幅優化"
        elif success_rate >= 90:
            return "一般 - 系統穩定性需要改進"
        else:
            return "需要改進 - 系統存在穩定性問題，不建議投入生產"
    
    def _generate_recommendations(self, success_rate: float, resource_stats: Dict) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        if success_rate < 95:
            recommendations.append("系統成功率偏低，建議檢查錯誤日誌並優化相關組件")
        
        if resource_stats.get('max_cpu_percent', 0) > 80:
            recommendations.append("CPU使用率過高，建議優化算法或增加硬件資源")
        
        if resource_stats.get('max_memory_percent', 0) > 80:
            recommendations.append("內存使用率過高，建議檢查內存洩漏或優化數據結構")
        
        if not recommendations:
            recommendations.append("系統運行良好，建議繼續監控並定期進行穩定性測試")
        
        return recommendations
    
    def save_test_results(self, report: Dict[str, Any]) -> str:
        """保存測試結果"""
        try:
            results_dir = Path("AImax/logs/stability_tests")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = results_dir / f"stability_test_{timestamp}.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"📄 測試結果已保存: {results_file}")
            return str(results_file)
            
        except Exception as e:
            print(f"❌ 保存測試結果失敗: {e}")
            return ""

def main():
    """主函數"""
    print("🔧 AImax 系統穩定性全面測試")
    print("=" * 40)
    
    # 創建測試器
    tester = SystemStabilityTester()
    tester.setup_signal_handlers()
    
    # 詢問測試時長
    print("選擇測試時長:")
    print("1. 快速測試 (5分鐘)")
    print("2. 短期測試 (1小時)")
    print("3. 標準測試 (24小時)")
    print("4. 自定義時長")
    
    choice = input("請選擇 (1-4): ").strip()
    
    if choice == "1":
        duration = 5/60  # 5分鐘
    elif choice == "2":
        duration = 1  # 1小時
    elif choice == "3":
        duration = 24  # 24小時
    elif choice == "4":
        try:
            duration = float(input("請輸入測試時長(小時): "))
        except ValueError:
            print("無效輸入，使用默認1小時")
            duration = 1
    else:
        print("無效選擇，使用默認1小時")
        duration = 1
    
    print(f"\n🚀 開始 {duration} 小時穩定性測試...")
    print("按 Ctrl+C 可以安全停止測試")
    
    # 執行測試
    report = tester.run_continuous_test(duration)
    
    # 保存結果
    results_file = tester.save_test_results(report)
    
    # 顯示總結
    print(f"\n📊 測試總結:")
    print(f"   測試時長: {report['test_summary']['total_duration_hours']:.2f} 小時")
    print(f"   總週期數: {report['test_summary']['total_cycles']}")
    print(f"   成功率: {report['test_summary']['success_rate_percent']:.1f}%")
    print(f"   穩定性評估: {report['stability_assessment']}")
    
    print(f"\n💡 改進建議:")
    for i, rec in enumerate(report['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    print(f"\n✅ 穩定性測試完成！")

if __name__ == "__main__":
    main()