#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能監控系統 - 監控GUI和系統性能
提供記憶體使用監控、UI響應時間監控和性能優化建議
"""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import deque

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from PyQt6.QtWidgets import QApplication


@dataclass
class PerformanceMetric:
    """性能指標"""
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    category: str = "general"


@dataclass
class PerformanceAlert:
    """性能警告"""
    timestamp: datetime
    alert_type: str
    message: str
    severity: str  # low, medium, high, critical
    metric_value: float
    threshold: float


class MemoryMonitor(QObject):
    """記憶體監控器"""
    
    memory_updated = pyqtSignal(dict)  # 記憶體資訊
    memory_alert = pyqtSignal(object)  # PerformanceAlert
    
    def __init__(self, alert_threshold_mb: float = 500.0):
        super().__init__()
        
        self.alert_threshold_mb = alert_threshold_mb
        self.process = psutil.Process()
        self.monitoring = False
        
        # 記憶體歷史記錄
        self.memory_history = deque(maxlen=100)
        
        # 監控定時器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_memory)
        
    def start_monitoring(self, interval_ms: int = 1000):
        """開始記憶體監控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_timer.start(interval_ms)
            print("📊 記憶體監控已啟動")
    
    def stop_monitoring(self):
        """停止記憶體監控"""
        if self.monitoring:
            self.monitoring = False
            self.monitor_timer.stop()
            print("📊 記憶體監控已停止")
    
    def check_memory(self):
        """檢查記憶體使用情況"""
        try:
            # 獲取進程記憶體資訊
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()
            
            # 獲取系統記憶體資訊
            system_memory = psutil.virtual_memory()
            
            memory_data = {
                'process_memory_mb': memory_info.rss / 1024 / 1024,
                'process_memory_percent': memory_percent,
                'system_memory_percent': system_memory.percent,
                'system_available_mb': system_memory.available / 1024 / 1024,
                'timestamp': datetime.now()
            }
            
            # 記錄歷史
            metric = PerformanceMetric(
                timestamp=datetime.now(),
                metric_name="process_memory",
                value=memory_data['process_memory_mb'],
                unit="MB",
                category="memory"
            )
            self.memory_history.append(metric)
            
            # 檢查警告
            if memory_data['process_memory_mb'] > self.alert_threshold_mb:
                alert = PerformanceAlert(
                    timestamp=datetime.now(),
                    alert_type="high_memory_usage",
                    message=f"進程記憶體使用過高: {memory_data['process_memory_mb']:.1f}MB",
                    severity="medium" if memory_data['process_memory_mb'] < self.alert_threshold_mb * 1.5 else "high",
                    metric_value=memory_data['process_memory_mb'],
                    threshold=self.alert_threshold_mb
                )
                self.memory_alert.emit(alert)
            
            # 發送更新信號
            self.memory_updated.emit(memory_data)
            
        except Exception as e:
            print(f"記憶體監控錯誤: {e}")
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """獲取記憶體統計資訊"""
        if not self.memory_history:
            return {}
        
        values = [metric.value for metric in self.memory_history]
        
        return {
            'current': values[-1] if values else 0,
            'average': sum(values) / len(values),
            'maximum': max(values),
            'minimum': min(values),
            'samples': len(values)
        }


class UIResponseMonitor(QObject):
    """UI響應時間監控器"""
    
    response_time_updated = pyqtSignal(dict)  # 響應時間資訊
    response_alert = pyqtSignal(object)  # PerformanceAlert
    
    def __init__(self, alert_threshold_ms: float = 100.0):
        super().__init__()
        
        self.alert_threshold_ms = alert_threshold_ms
        self.monitoring = False
        
        # 響應時間歷史記錄
        self.response_history = deque(maxlen=50)
        
        # 測試定時器
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self.test_ui_response)
        
        # 響應時間測量
        self.test_start_time = None
        
    def start_monitoring(self, interval_ms: int = 5000):
        """開始UI響應監控"""
        if not self.monitoring:
            self.monitoring = True
            self.test_timer.start(interval_ms)
            print("📊 UI響應監控已啟動")
    
    def stop_monitoring(self):
        """停止UI響應監控"""
        if self.monitoring:
            self.monitoring = False
            self.test_timer.stop()
            print("📊 UI響應監控已停止")
    
    def test_ui_response(self):
        """測試UI響應時間"""
        try:
            self.test_start_time = time.time()
            
            # 使用QTimer.singleShot來測試事件循環響應
            QTimer.singleShot(0, self.measure_response_time)
            
        except Exception as e:
            print(f"UI響應測試錯誤: {e}")
    
    def measure_response_time(self):
        """測量響應時間"""
        if self.test_start_time is None:
            return
        
        response_time_ms = (time.time() - self.test_start_time) * 1000
        
        response_data = {
            'response_time_ms': response_time_ms,
            'timestamp': datetime.now()
        }
        
        # 記錄歷史
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name="ui_response_time",
            value=response_time_ms,
            unit="ms",
            category="ui"
        )
        self.response_history.append(metric)
        
        # 檢查警告
        if response_time_ms > self.alert_threshold_ms:
            alert = PerformanceAlert(
                timestamp=datetime.now(),
                alert_type="slow_ui_response",
                message=f"UI響應時間過慢: {response_time_ms:.1f}ms",
                severity="medium" if response_time_ms < self.alert_threshold_ms * 2 else "high",
                metric_value=response_time_ms,
                threshold=self.alert_threshold_ms
            )
            self.response_alert.emit(alert)
        
        # 發送更新信號
        self.response_time_updated.emit(response_data)
        
        self.test_start_time = None
    
    def get_response_statistics(self) -> Dict[str, Any]:
        """獲取響應時間統計資訊"""
        if not self.response_history:
            return {}
        
        values = [metric.value for metric in self.response_history]
        
        return {
            'current': values[-1] if values else 0,
            'average': sum(values) / len(values),
            'maximum': max(values),
            'minimum': min(values),
            'samples': len(values)
        }


class UpdateRateOptimizer(QObject):
    """更新頻率優化器"""
    
    def __init__(self):
        super().__init__()
        
        # 更新頻率配置
        self.update_rates = {
            'high_priority': 1000,    # 1秒 - 重要狀態
            'medium_priority': 3000,  # 3秒 - 一般資訊
            'low_priority': 10000,    # 10秒 - 非關鍵資訊
            'background': 30000       # 30秒 - 背景任務
        }
        
        # 註冊的更新任務
        self.update_tasks = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': [],
            'background': []
        }
        
        # 定時器
        self.timers = {}
        
        self._setup_timers()
    
    def _setup_timers(self):
        """設置定時器"""
        for priority, interval in self.update_rates.items():
            timer = QTimer()
            timer.timeout.connect(lambda p=priority: self._execute_updates(p))
            timer.start(interval)
            self.timers[priority] = timer
    
    def register_update_task(self, priority: str, task_name: str, callback: Callable):
        """註冊更新任務"""
        if priority not in self.update_tasks:
            print(f"警告: 未知的優先級 {priority}")
            priority = 'medium_priority'
        
        task = {
            'name': task_name,
            'callback': callback,
            'last_update': None,
            'error_count': 0
        }
        
        self.update_tasks[priority].append(task)
        print(f"📊 註冊更新任務: {task_name} ({priority})")
    
    def _execute_updates(self, priority: str):
        """執行指定優先級的更新任務"""
        tasks = self.update_tasks.get(priority, [])
        
        for task in tasks:
            try:
                task['callback']()
                task['last_update'] = datetime.now()
                task['error_count'] = 0
                
            except Exception as e:
                task['error_count'] += 1
                print(f"更新任務 {task['name']} 執行失敗: {e}")
                
                # 如果錯誤次數過多，暫時禁用任務
                if task['error_count'] >= 5:
                    print(f"任務 {task['name']} 錯誤次數過多，暫時禁用")
                    tasks.remove(task)
    
    def get_update_statistics(self) -> Dict[str, Any]:
        """獲取更新統計資訊"""
        stats = {}
        
        for priority, tasks in self.update_tasks.items():
            stats[priority] = {
                'task_count': len(tasks),
                'update_interval': self.update_rates[priority],
                'tasks': [
                    {
                        'name': task['name'],
                        'last_update': task['last_update'].isoformat() if task['last_update'] else None,
                        'error_count': task['error_count']
                    }
                    for task in tasks
                ]
            }
        
        return stats


class PerformanceMonitor(QObject):
    """性能監控主類"""
    
    performance_updated = pyqtSignal(dict)  # 性能資訊更新
    performance_alert = pyqtSignal(object)  # 性能警告
    optimization_suggestion = pyqtSignal(str)  # 優化建議
    
    def __init__(self):
        super().__init__()
        
        # 子監控器
        self.memory_monitor = MemoryMonitor()
        self.ui_response_monitor = UIResponseMonitor()
        self.update_optimizer = UpdateRateOptimizer()
        
        # 性能歷史記錄
        self.performance_history = deque(maxlen=200)
        self.alerts_history = deque(maxlen=50)
        
        # 連接信號
        self.memory_monitor.memory_updated.connect(self.on_memory_updated)
        self.memory_monitor.memory_alert.connect(self.on_performance_alert)
        self.ui_response_monitor.response_time_updated.connect(self.on_response_updated)
        self.ui_response_monitor.response_alert.connect(self.on_performance_alert)
        
        # 優化建議定時器
        self.suggestion_timer = QTimer()
        self.suggestion_timer.timeout.connect(self.generate_optimization_suggestions)
        self.suggestion_timer.start(60000)  # 每分鐘檢查一次
        
        # 監控狀態
        self.monitoring_active = False
    
    def start_monitoring(self):
        """開始性能監控"""
        if not self.monitoring_active:
            self.monitoring_active = True
            
            # 啟動子監控器
            self.memory_monitor.start_monitoring()
            self.ui_response_monitor.start_monitoring()
            
            print("🚀 性能監控系統已啟動")
    
    def stop_monitoring(self):
        """停止性能監控"""
        if self.monitoring_active:
            self.monitoring_active = False
            
            # 停止子監控器
            self.memory_monitor.stop_monitoring()
            self.ui_response_monitor.stop_monitoring()
            
            print("⏹️ 性能監控系統已停止")
    
    def on_memory_updated(self, memory_data: Dict[str, Any]):
        """處理記憶體更新"""
        self.record_performance_data('memory', memory_data)
    
    def on_response_updated(self, response_data: Dict[str, Any]):
        """處理響應時間更新"""
        self.record_performance_data('ui_response', response_data)
    
    def on_performance_alert(self, alert: PerformanceAlert):
        """處理性能警告"""
        self.alerts_history.append(alert)
        self.performance_alert.emit(alert)
        
        print(f"⚠️ 性能警告: {alert.message}")
    
    def record_performance_data(self, category: str, data: Dict[str, Any]):
        """記錄性能數據"""
        performance_data = {
            'category': category,
            'data': data,
            'timestamp': datetime.now()
        }
        
        self.performance_history.append(performance_data)
        self.performance_updated.emit(performance_data)
    
    def generate_optimization_suggestions(self):
        """生成優化建議"""
        try:
            suggestions = []
            
            # 記憶體優化建議
            memory_stats = self.memory_monitor.get_memory_statistics()
            if memory_stats and memory_stats.get('average', 0) > 300:
                suggestions.append("建議: 記憶體使用較高，考慮減少同時運行的功能")
            
            # UI響應優化建議
            response_stats = self.ui_response_monitor.get_response_statistics()
            if response_stats and response_stats.get('average', 0) > 50:
                suggestions.append("建議: UI響應較慢，考慮減少更新頻率或優化渲染")
            
            # 更新頻率優化建議
            update_stats = self.update_optimizer.get_update_statistics()
            high_priority_tasks = len(update_stats.get('high_priority', {}).get('tasks', []))
            if high_priority_tasks > 5:
                suggestions.append("建議: 高優先級更新任務過多，考慮降低部分任務優先級")
            
            # 發送建議
            for suggestion in suggestions:
                self.optimization_suggestion.emit(suggestion)
                
        except Exception as e:
            print(f"生成優化建議時發生錯誤: {e}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """獲取性能報告"""
        return {
            'monitoring_active': self.monitoring_active,
            'memory_statistics': self.memory_monitor.get_memory_statistics(),
            'response_statistics': self.ui_response_monitor.get_response_statistics(),
            'update_statistics': self.update_optimizer.get_update_statistics(),
            'recent_alerts': [
                {
                    'timestamp': alert.timestamp.isoformat(),
                    'alert_type': alert.alert_type,
                    'message': alert.message,
                    'severity': alert.severity
                }
                for alert in list(self.alerts_history)[-10:]
            ],
            'performance_samples': len(self.performance_history),
            'report_timestamp': datetime.now().isoformat()
        }
    
    def register_update_task(self, priority: str, task_name: str, callback: Callable):
        """註冊更新任務（代理到優化器）"""
        self.update_optimizer.register_update_task(priority, task_name, callback)
    
    def cleanup(self):
        """清理資源"""
        self.stop_monitoring()
        
        # 停止定時器
        if hasattr(self, 'suggestion_timer'):
            self.suggestion_timer.stop()


if __name__ == "__main__":
    # 測試性能監控器
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 創建性能監控器
    monitor = PerformanceMonitor()
    
    def on_performance_updated(data):
        print(f"性能更新: {data['category']} - {data['data']}")
    
    def on_performance_alert(alert):
        print(f"性能警告: {alert.message}")
    
    def on_optimization_suggestion(suggestion):
        print(f"優化建議: {suggestion}")
    
    # 連接信號
    monitor.performance_updated.connect(on_performance_updated)
    monitor.performance_alert.connect(on_performance_alert)
    monitor.optimization_suggestion.connect(on_optimization_suggestion)
    
    # 註冊測試更新任務
    def test_update():
        print("執行測試更新任務")
    
    monitor.register_update_task('high_priority', 'test_task', test_update)
    
    # 開始監控
    monitor.start_monitoring()
    
    # 運行5秒後停止
    QTimer.singleShot(5000, lambda: (
        print("\\n性能報告:"),
        print(monitor.get_performance_report()),
        monitor.cleanup(),
        app.quit()
    ))
    
    sys.exit(app.exec())