#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
狀態同步管理器 - 管理AI狀態監控和實時同步
確保GUI與AI系統狀態保持一致
"""

import time
import threading
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread


@dataclass
class StatusSnapshot:
    """狀態快照"""
    timestamp: datetime
    ai_status: Dict[str, Any] = field(default_factory=dict)
    trading_status: Dict[str, Any] = field(default_factory=dict)
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'ai_status': self.ai_status,
            'trading_status': self.trading_status,
            'system_metrics': self.system_metrics
        }


class StatusMonitorWorker(QObject):
    """狀態監控工作器"""
    
    status_collected = pyqtSignal(dict)  # 狀態收集完成
    error_occurred = pyqtSignal(str)     # 發生錯誤
    
    def __init__(self, ai_connector):
        super().__init__()
        self.ai_connector = ai_connector
        self.is_monitoring = False
        self.monitor_interval = 2.0  # 監控間隔（秒）
        
    def start_monitoring(self):
        """開始監控"""
        self.is_monitoring = True
        self.monitor_loop()
    
    def stop_monitoring(self):
        """停止監控"""
        self.is_monitoring = False
    
    def monitor_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                # 收集狀態數據
                status_data = self.collect_status_data()
                
                # 發送狀態更新
                self.status_collected.emit(status_data)
                
                # 等待下次監控
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.error_occurred.emit(f"狀態監控錯誤: {str(e)}")
                time.sleep(self.monitor_interval)
    
    def collect_status_data(self) -> Dict[str, Any]:
        """收集狀態數據"""
        try:
            current_time = datetime.now()
            
            # 收集AI狀態
            ai_status = self.ai_connector.get_ai_status() if self.ai_connector else {}
            
            # 收集交易狀態
            trading_status = self.ai_connector.get_trading_status() if self.ai_connector else {}
            
            # 收集系統指標
            system_metrics = self.collect_system_metrics()
            
            return {
                'timestamp': current_time.isoformat(),
                'ai_status': ai_status,
                'trading_status': trading_status,
                'system_metrics': system_metrics
            }
            
        except Exception as e:
            raise Exception(f"收集狀態數據失敗: {str(e)}")
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """收集系統指標"""
        try:
            metrics = {
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'network_status': 'unknown',
                'disk_usage': 0.0,
                'uptime': 0
            }
            
            # 嘗試獲取系統指標
            try:
                import psutil
                
                # CPU使用率
                metrics['cpu_usage'] = psutil.cpu_percent(interval=0.1)
                
                # 記憶體使用率
                memory = psutil.virtual_memory()
                metrics['memory_usage'] = memory.percent
                
                # 磁碟使用率
                disk = psutil.disk_usage('/')
                metrics['disk_usage'] = (disk.used / disk.total) * 100
                
                # 網路狀態（簡化）
                net_io = psutil.net_io_counters()
                metrics['network_status'] = 'active' if net_io.bytes_sent > 0 else 'inactive'
                
                # 系統運行時間
                boot_time = psutil.boot_time()
                metrics['uptime'] = int(time.time() - boot_time)
                
            except ImportError:
                # 如果psutil不可用，使用模擬數據
                import random
                metrics.update({
                    'cpu_usage': random.uniform(10, 80),
                    'memory_usage': random.uniform(30, 70),
                    'network_status': 'active',
                    'disk_usage': random.uniform(20, 60),
                    'uptime': int(time.time() % 86400)  # 模擬運行時間
                })
            
            return metrics
            
        except Exception as e:
            return {'error': f"收集系統指標失敗: {str(e)}"}


class StatusSyncManager(QObject):
    """狀態同步管理器"""
    
    # 信號定義
    ai_status_synced = pyqtSignal(dict)      # AI狀態同步
    trading_status_synced = pyqtSignal(dict) # 交易狀態同步
    balance_updated = pyqtSignal(float)      # 餘額更新
    system_metrics_updated = pyqtSignal(dict) # 系統指標更新
    sync_error = pyqtSignal(str)             # 同步錯誤
    
    def __init__(self, ai_connector=None):
        super().__init__()
        
        self.ai_connector = ai_connector
        self.is_syncing = False
        self.sync_interval = 2000  # 同步間隔（毫秒）
        
        # 狀態歷史記錄
        self.status_history: List[StatusSnapshot] = []
        self.max_history_size = 100
        
        # 狀態變化檢測
        self.last_ai_status = {}
        self.last_trading_status = {}
        self.last_balance = 0.0
        
        # 同步定時器
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.sync_status)
        
        # 狀態監控工作器
        self.monitor_thread = QThread()
        self.monitor_worker = None
        
        # 餘額變化監控
        self.balance_monitor_timer = QTimer()
        self.balance_monitor_timer.timeout.connect(self.monitor_balance_changes)
        
    def start_sync(self):
        """開始狀態同步"""
        try:
            if self.is_syncing:
                return
            
            self.is_syncing = True
            
            # 啟動同步定時器
            self.sync_timer.start(self.sync_interval)
            
            # 啟動餘額監控
            self.balance_monitor_timer.start(1000)  # 每秒檢查餘額變化
            
            # 啟動狀態監控工作器
            self.start_status_monitor()
            
            print("狀態同步管理器已啟動")
            
        except Exception as e:
            self.sync_error.emit(f"啟動狀態同步失敗: {str(e)}")
    
    def stop_sync(self):
        """停止狀態同步"""
        try:
            if not self.is_syncing:
                return
            
            self.is_syncing = False
            
            # 停止定時器
            self.sync_timer.stop()
            self.balance_monitor_timer.stop()
            
            # 停止狀態監控工作器
            self.stop_status_monitor()
            
            print("狀態同步管理器已停止")
            
        except Exception as e:
            self.sync_error.emit(f"停止狀態同步失敗: {str(e)}")
    
    def start_status_monitor(self):
        """啟動狀態監控工作器"""
        try:
            if self.ai_connector:
                self.monitor_worker = StatusMonitorWorker(self.ai_connector)
                self.monitor_worker.moveToThread(self.monitor_thread)
                
                # 連接信號
                self.monitor_worker.status_collected.connect(self.on_status_collected)
                self.monitor_worker.error_occurred.connect(self.sync_error.emit)
                
                # 啟動監控線程
                self.monitor_thread.started.connect(self.monitor_worker.start_monitoring)
                self.monitor_thread.start()
                
        except Exception as e:
            self.sync_error.emit(f"啟動狀態監控失敗: {str(e)}")
    
    def stop_status_monitor(self):
        """停止狀態監控工作器"""
        try:
            if self.monitor_worker:
                self.monitor_worker.stop_monitoring()
            
            if self.monitor_thread.isRunning():
                self.monitor_thread.quit()
                self.monitor_thread.wait(2000)
                
        except Exception as e:
            self.sync_error.emit(f"停止狀態監控失敗: {str(e)}")
    
    def sync_status(self):
        """同步狀態"""
        try:
            if not self.ai_connector:
                return
            
            # 獲取當前狀態
            current_ai_status = self.ai_connector.get_ai_status()
            current_trading_status = self.ai_connector.get_trading_status()
            
            # 檢查AI狀態變化
            if self.has_status_changed(current_ai_status, self.last_ai_status):
                self.ai_status_synced.emit(current_ai_status)
                self.last_ai_status = current_ai_status.copy()
            
            # 檢查交易狀態變化
            if self.has_status_changed(current_trading_status, self.last_trading_status):
                self.trading_status_synced.emit(current_trading_status)
                self.last_trading_status = current_trading_status.copy()
            
        except Exception as e:
            self.sync_error.emit(f"狀態同步失敗: {str(e)}")
    
    def monitor_balance_changes(self):
        """監控餘額變化"""
        try:
            if not self.ai_connector:
                return
            
            trading_status = self.ai_connector.get_trading_status()
            current_balance = trading_status.get('balance', 0.0)
            
            # 檢查餘額是否有顯著變化（超過0.01）
            if abs(current_balance - self.last_balance) > 0.01:
                self.balance_updated.emit(current_balance)
                self.last_balance = current_balance
                
        except Exception as e:
            self.sync_error.emit(f"餘額監控失敗: {str(e)}")
    
    def on_status_collected(self, status_data: Dict[str, Any]):
        """處理收集到的狀態數據"""
        try:
            # 創建狀態快照
            snapshot = StatusSnapshot(
                timestamp=datetime.fromisoformat(status_data['timestamp']),
                ai_status=status_data.get('ai_status', {}),
                trading_status=status_data.get('trading_status', {}),
                system_metrics=status_data.get('system_metrics', {})
            )
            
            # 添加到歷史記錄
            self.add_status_snapshot(snapshot)
            
            # 發送系統指標更新
            self.system_metrics_updated.emit(snapshot.system_metrics)
            
        except Exception as e:
            self.sync_error.emit(f"處理狀態數據失敗: {str(e)}")
    
    def add_status_snapshot(self, snapshot: StatusSnapshot):
        """添加狀態快照到歷史記錄"""
        try:
            self.status_history.append(snapshot)
            
            # 限制歷史記錄大小
            if len(self.status_history) > self.max_history_size:
                self.status_history.pop(0)
                
        except Exception as e:
            self.sync_error.emit(f"添加狀態快照失敗: {str(e)}")
    
    def has_status_changed(self, current_status: Dict[str, Any], last_status: Dict[str, Any]) -> bool:
        """檢查狀態是否有變化"""
        try:
            # 比較關鍵字段
            key_fields = ['status', 'active_count', 'balance', 'profit_loss', 'active_orders']
            
            for field in key_fields:
                if current_status.get(field) != last_status.get(field):
                    return True
            
            return False
            
        except Exception:
            return True  # 如果比較失敗，假設有變化
    
    def get_status_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """獲取指定時間範圍內的狀態歷史"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            filtered_history = [
                snapshot.to_dict() 
                for snapshot in self.status_history 
                if snapshot.timestamp >= cutoff_time
            ]
            
            return filtered_history
            
        except Exception as e:
            self.sync_error.emit(f"獲取狀態歷史失敗: {str(e)}")
            return []
    
    def get_latest_status(self) -> Optional[Dict[str, Any]]:
        """獲取最新狀態"""
        try:
            if self.status_history:
                return self.status_history[-1].to_dict()
            return None
            
        except Exception as e:
            self.sync_error.emit(f"獲取最新狀態失敗: {str(e)}")
            return None
    
    def set_sync_interval(self, interval_ms: int):
        """設置同步間隔"""
        try:
            self.sync_interval = max(500, interval_ms)  # 最小500ms
            
            if self.is_syncing:
                self.sync_timer.stop()
                self.sync_timer.start(self.sync_interval)
                
        except Exception as e:
            self.sync_error.emit(f"設置同步間隔失敗: {str(e)}")
    
    def force_sync(self):
        """強制同步"""
        try:
            self.sync_status()
            self.monitor_balance_changes()
            
        except Exception as e:
            self.sync_error.emit(f"強制同步失敗: {str(e)}")
    
    def cleanup(self):
        """清理資源"""
        try:
            self.stop_sync()
            self.status_history.clear()
            
        except Exception as e:
            self.sync_error.emit(f"清理資源失敗: {str(e)}")


if __name__ == "__main__":
    # 測試狀態同步管理器
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 創建狀態同步管理器
    sync_manager = StatusSyncManager()
    
    def on_ai_status_synced(status):
        print(f"AI狀態同步: {status}")
    
    def on_trading_status_synced(status):
        print(f"交易狀態同步: {status}")
    
    def on_balance_updated(balance):
        print(f"餘額更新: ${balance:.2f}")
    
    def on_system_metrics_updated(metrics):
        print(f"系統指標更新: {metrics}")
    
    def on_sync_error(error):
        print(f"同步錯誤: {error}")
    
    # 連接信號
    sync_manager.ai_status_synced.connect(on_ai_status_synced)
    sync_manager.trading_status_synced.connect(on_trading_status_synced)
    sync_manager.balance_updated.connect(on_balance_updated)
    sync_manager.system_metrics_updated.connect(on_system_metrics_updated)
    sync_manager.sync_error.connect(on_sync_error)
    
    # 啟動同步
    sync_manager.start_sync()
    
    # 運行5秒後退出
    QTimer.singleShot(5000, app.quit)
    
    sys.exit(app.exec())