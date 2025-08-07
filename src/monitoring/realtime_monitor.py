#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 實時監控面板 - 任務13實現
實現實時系統狀態監控和可視化面板
"""

import sys
import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
import threading
import queue

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from src.logging.structured_logger import structured_logger, LogCategory
    from src.monitoring.resource_monitor import resource_monitor
    from src.strategy.strategy_config_manager import strategy_config_manager
except ImportError as e:
    print(f"警告: 無法導入某些模組: {e}")
    # 創建簡單的替代品
    class SimpleLogger:
        def info(self, category, message, **kwargs):
            print(f"INFO [{category}]: {message}")
        def warning(self, category, message, **kwargs):
            print(f"WARNING [{category}]: {message}")
        def error(self, category, message, **kwargs):
            print(f"ERROR [{category}]: {message}")
        def critical(self, category, message, **kwargs):
            print(f"CRITICAL [{category}]: {message}")
        def get_log_statistics(self):
            return {'queue_size': 0, 'errors_last_hour': 0}
    
    structured_logger = SimpleLogger()
    
    class LogCategory:
        SYSTEM = "SYSTEM"
        TRADING = "TRADING"
    
    class SimpleResourceMonitor:
        def _collect_system_resources(self):
            import psutil
            return type('ResourceUsage', (), {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage_gb': psutil.disk_usage('/').used / (1024**3),
                'network_io_mb': 0.0
            })()
    
    resource_monitor = SimpleResourceMonitor()
    
    class SimpleStrategyManager:
        def get_strategy_statistics(self):
            return {'active_strategies': 0, 'total_strategies': 0}
        def get_active_strategy(self):
            return None
    
    strategy_config_manager = SimpleStrategyManager()

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """系統指標數據"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage_gb: float
    network_io_mb: float
    active_threads: int
    log_queue_size: int
    error_count_1h: int
    trading_signals_1h: int
    system_uptime: float

@dataclass
class TradingMetrics:
    """交易指標數據"""
    timestamp: datetime
    active_strategies: int
    total_strategies: int
    signals_generated: int
    trades_executed: int
    success_rate: float
    current_balance: float
    daily_pnl: float
    open_positions: int

@dataclass
class AlertInfo:
    """警告信息"""
    timestamp: datetime
    level: str  # info, warning, error, critical
    category: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False

class RealtimeMonitor:
    """實時監控器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # 監控數據存儲
        self.system_metrics_history: List[SystemMetrics] = []
        self.trading_metrics_history: List[TradingMetrics] = []
        self.active_alerts: List[AlertInfo] = []
        
        # 監控配置
        self.config = {
            'update_interval': 5,  # 5秒更新間隔
            'history_retention': 1440,  # 保留24小時數據（1440個5秒間隔）
            'alert_thresholds': {
                'cpu_warning': 80.0,
                'cpu_critical': 95.0,
                'memory_warning': 85.0,
                'memory_critical': 95.0,
                'error_rate_warning': 10,  # 每小時錯誤數
                'error_rate_critical': 50,
                'disk_warning': 85.0,
                'disk_critical': 95.0
            }
        }
        
        # 系統啟動時間
        self.start_time = datetime.now()
        
        structured_logger.info(LogCategory.SYSTEM, "實時監控器初始化完成")
    
    def start_monitoring(self):
        """開始實時監控"""
        if self.monitoring_active:
            structured_logger.warning(LogCategory.SYSTEM, "實時監控已在運行")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        structured_logger.info(LogCategory.SYSTEM, "實時監控已啟動")
    
    def stop_monitoring(self):
        """停止實時監控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        structured_logger.info(LogCategory.SYSTEM, "實時監控已停止")
    
    def _monitoring_loop(self):
        """監控循環"""
        while self.monitoring_active:
            try:
                # 收集系統指標
                system_metrics = self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # 收集交易指標
                trading_metrics = self._collect_trading_metrics()
                self.trading_metrics_history.append(trading_metrics)
                
                # 檢查警告條件
                self._check_alert_conditions(system_metrics, trading_metrics)
                
                # 清理舊數據
                self._cleanup_old_data()
                
                # 等待下次更新
                time.sleep(self.config['update_interval'])
                
            except Exception as e:
                structured_logger.error(LogCategory.SYSTEM, f"監控循環錯誤: {e}")
                time.sleep(self.config['update_interval'])
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """收集系統指標"""
        try:
            # 獲取資源使用情況
            resource_usage = resource_monitor._collect_system_resources()
            
            # 獲取日誌統計
            log_stats = structured_logger.get_log_statistics()
            
            # 計算系統運行時間
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            # 獲取活躍線程數
            active_threads = threading.active_count()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=resource_usage.cpu_percent,
                memory_percent=resource_usage.memory_percent,
                disk_usage_gb=resource_usage.disk_usage_gb,
                network_io_mb=resource_usage.network_io_mb,
                active_threads=active_threads,
                log_queue_size=log_stats['queue_size'],
                error_count_1h=log_stats['errors_last_hour'],
                trading_signals_1h=0,  # 待實現
                system_uptime=uptime
            )
            
        except Exception as e:
            structured_logger.error(LogCategory.SYSTEM, f"收集系統指標失敗: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0, memory_percent=0, disk_usage_gb=0,
                network_io_mb=0, active_threads=0, log_queue_size=0,
                error_count_1h=0, trading_signals_1h=0, system_uptime=0
            )
    
    def _collect_trading_metrics(self) -> TradingMetrics:
        """收集交易指標"""
        try:
            # 獲取策略統計
            strategy_stats = strategy_config_manager.get_strategy_statistics()
            
            # 獲取活躍策略
            active_strategy = strategy_config_manager.get_active_strategy()
            
            return TradingMetrics(
                timestamp=datetime.now(),
                active_strategies=strategy_stats['active_strategies'],
                total_strategies=strategy_stats['total_strategies'],
                signals_generated=0,  # 待實現
                trades_executed=0,    # 待實現
                success_rate=0.0,     # 待實現
                current_balance=10000.0,  # 待實現
                daily_pnl=0.0,        # 待實現
                open_positions=0      # 待實現
            )
            
        except Exception as e:
            structured_logger.error(LogCategory.TRADING, f"收集交易指標失敗: {e}")
            return TradingMetrics(
                timestamp=datetime.now(),
                active_strategies=0, total_strategies=0, signals_generated=0,
                trades_executed=0, success_rate=0.0, current_balance=0.0,
                daily_pnl=0.0, open_positions=0
            )
    
    def _check_alert_conditions(self, system_metrics: SystemMetrics, trading_metrics: TradingMetrics):
        """檢查警告條件"""
        thresholds = self.config['alert_thresholds']
        
        # CPU使用率警告
        if system_metrics.cpu_percent >= thresholds['cpu_critical']:
            self._create_alert('critical', 'system', 
                             f"CPU使用率危險: {system_metrics.cpu_percent:.1f}%",
                             {'cpu_percent': system_metrics.cpu_percent})
        elif system_metrics.cpu_percent >= thresholds['cpu_warning']:
            self._create_alert('warning', 'system',
                             f"CPU使用率警告: {system_metrics.cpu_percent:.1f}%",
                             {'cpu_percent': system_metrics.cpu_percent})
        
        # 記憶體使用率警告
        if system_metrics.memory_percent >= thresholds['memory_critical']:
            self._create_alert('critical', 'system',
                             f"記憶體使用率危險: {system_metrics.memory_percent:.1f}%",
                             {'memory_percent': system_metrics.memory_percent})
        elif system_metrics.memory_percent >= thresholds['memory_warning']:
            self._create_alert('warning', 'system',
                             f"記憶體使用率警告: {system_metrics.memory_percent:.1f}%",
                             {'memory_percent': system_metrics.memory_percent})
        
        # 錯誤率警告
        if system_metrics.error_count_1h >= thresholds['error_rate_critical']:
            self._create_alert('critical', 'system',
                             f"錯誤率過高: {system_metrics.error_count_1h} 錯誤/小時",
                             {'error_count': system_metrics.error_count_1h})
        elif system_metrics.error_count_1h >= thresholds['error_rate_warning']:
            self._create_alert('warning', 'system',
                             f"錯誤率警告: {system_metrics.error_count_1h} 錯誤/小時",
                             {'error_count': system_metrics.error_count_1h})
        
        # 交易系統警告
        if trading_metrics.active_strategies == 0 and trading_metrics.total_strategies > 0:
            self._create_alert('warning', 'trading',
                             "沒有活躍的交易策略",
                             {'total_strategies': trading_metrics.total_strategies})
    
    def _create_alert(self, level: str, category: str, message: str, details: Dict[str, Any]):
        """創建警告"""
        # 檢查是否已存在相同的警告（避免重複）
        for alert in self.active_alerts:
            if (alert.level == level and alert.category == category and 
                alert.message == message and not alert.acknowledged):
                return  # 已存在相同警告
        
        alert = AlertInfo(
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            details=details
        )
        
        self.active_alerts.append(alert)
        
        # 記錄到日誌
        log_level = {
            'info': structured_logger.info,
            'warning': structured_logger.warning,
            'error': structured_logger.error,
            'critical': structured_logger.critical
        }.get(level, structured_logger.info)
        
        log_category = LogCategory.SYSTEM if category == 'system' else LogCategory.TRADING
        log_level(log_category, f"警告: {message}", **details)
    
    def _cleanup_old_data(self):
        """清理舊數據"""
        max_items = self.config['history_retention']
        
        # 清理系統指標歷史
        if len(self.system_metrics_history) > max_items:
            self.system_metrics_history = self.system_metrics_history[-max_items:]
        
        # 清理交易指標歷史
        if len(self.trading_metrics_history) > max_items:
            self.trading_metrics_history = self.trading_metrics_history[-max_items:]
        
        # 清理已確認的舊警告
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.active_alerts = [
            alert for alert in self.active_alerts
            if not alert.acknowledged or alert.timestamp > cutoff_time
        ]
    
    def get_current_status(self) -> Dict[str, Any]:
        """獲取當前系統狀態"""
        current_system = self.system_metrics_history[-1] if self.system_metrics_history else None
        current_trading = self.trading_metrics_history[-1] if self.trading_metrics_history else None
        
        # 計算系統健康分數
        health_score = self._calculate_health_score(current_system)
        
        # 統計警告
        alert_counts = {
            'critical': len([a for a in self.active_alerts if a.level == 'critical' and not a.acknowledged]),
            'warning': len([a for a in self.active_alerts if a.level == 'warning' and not a.acknowledged]),
            'info': len([a for a in self.active_alerts if a.level == 'info' and not a.acknowledged])
        }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'health_score': health_score,
            'system_status': 'healthy' if health_score >= 80 else 'warning' if health_score >= 60 else 'critical',
            'system_metrics': {
                'cpu_percent': current_system.cpu_percent if current_system else 0,
                'memory_percent': current_system.memory_percent if current_system else 0,
                'disk_usage_gb': current_system.disk_usage_gb if current_system else 0,
                'active_threads': current_system.active_threads if current_system else 0,
                'uptime_hours': (current_system.system_uptime / 3600) if current_system else 0
            },
            'trading_metrics': {
                'active_strategies': current_trading.active_strategies if current_trading else 0,
                'total_strategies': current_trading.total_strategies if current_trading else 0,
                'current_balance': current_trading.current_balance if current_trading else 0,
                'daily_pnl': current_trading.daily_pnl if current_trading else 0
            },
            'alerts': {
                'total_active': len([a for a in self.active_alerts if not a.acknowledged]),
                'by_level': alert_counts,
                'recent_alerts': [
                    {
                        'timestamp': alert.timestamp.isoformat(),
                        'level': alert.level,
                        'category': alert.category,
                        'message': alert.message
                    }
                    for alert in self.active_alerts[-5:] if not alert.acknowledged
                ]
            },
            'monitoring_active': self.monitoring_active
        }
    
    def _calculate_health_score(self, system_metrics: SystemMetrics) -> int:
        """計算系統健康分數 (0-100)"""
        if not system_metrics:
            return 0
        
        score = 100
        
        # CPU使用率影響
        if system_metrics.cpu_percent > 90:
            score -= 30
        elif system_metrics.cpu_percent > 80:
            score -= 15
        elif system_metrics.cpu_percent > 70:
            score -= 5
        
        # 記憶體使用率影響
        if system_metrics.memory_percent > 90:
            score -= 25
        elif system_metrics.memory_percent > 80:
            score -= 10
        elif system_metrics.memory_percent > 70:
            score -= 3
        
        # 錯誤率影響
        if system_metrics.error_count_1h > 50:
            score -= 20
        elif system_metrics.error_count_1h > 10:
            score -= 10
        elif system_metrics.error_count_1h > 5:
            score -= 5
        
        # 日誌隊列大小影響
        if system_metrics.log_queue_size > 1000:
            score -= 10
        elif system_metrics.log_queue_size > 500:
            score -= 5
        
        return max(0, score)
    
    def get_metrics_history(self, hours: int = 1) -> Dict[str, Any]:
        """獲取指標歷史數據"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 過濾歷史數據
        system_history = [
            {
                'timestamp': m.timestamp.isoformat(),
                'cpu_percent': m.cpu_percent,
                'memory_percent': m.memory_percent,
                'error_count': m.error_count_1h
            }
            for m in self.system_metrics_history
            if m.timestamp > cutoff_time
        ]
        
        trading_history = [
            {
                'timestamp': m.timestamp.isoformat(),
                'active_strategies': m.active_strategies,
                'signals_generated': m.signals_generated,
                'success_rate': m.success_rate
            }
            for m in self.trading_metrics_history
            if m.timestamp > cutoff_time
        ]
        
        return {
            'system_metrics': system_history,
            'trading_metrics': trading_history,
            'data_points': len(system_history),
            'time_range_hours': hours
        }
    
    def acknowledge_alert(self, alert_index: int) -> bool:
        """確認警告"""
        try:
            if 0 <= alert_index < len(self.active_alerts):
                self.active_alerts[alert_index].acknowledged = True
                structured_logger.info(LogCategory.SYSTEM, f"警告已確認: {self.active_alerts[alert_index].message}")
                return True
            return False
        except Exception as e:
            structured_logger.error(LogCategory.SYSTEM, f"確認警告失敗: {e}")
            return False
    
    def get_system_summary(self) -> str:
        """獲取系統摘要報告"""
        status = self.get_current_status()
        
        summary = f"""
📊 AImax 實時監控摘要
{'='*40}

🏥 系統健康: {status['health_score']}/100 ({status['system_status'].upper()})
⏰ 運行時間: {status['system_metrics']['uptime_hours']:.1f} 小時

💻 系統資源:
   CPU: {status['system_metrics']['cpu_percent']:.1f}%
   記憶體: {status['system_metrics']['memory_percent']:.1f}%
   磁碟: {status['system_metrics']['disk_usage_gb']:.2f} GB
   線程: {status['system_metrics']['active_threads']}

💰 交易狀態:
   活躍策略: {status['trading_metrics']['active_strategies']}/{status['trading_metrics']['total_strategies']}
   當前餘額: ${status['trading_metrics']['current_balance']:,.2f}
   今日盈虧: ${status['trading_metrics']['daily_pnl']:+,.2f}

⚠️ 警告狀態:
   危險: {status['alerts']['by_level']['critical']}
   警告: {status['alerts']['by_level']['warning']}
   信息: {status['alerts']['by_level']['info']}

{'='*40}
更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return summary.strip()

# 全局實時監控器實例
realtime_monitor = RealtimeMonitor()

# 便捷函數
def start_realtime_monitoring():
    """啟動實時監控"""
    realtime_monitor.start_monitoring()

def stop_realtime_monitoring():
    """停止實時監控"""
    realtime_monitor.stop_monitoring()

def get_system_status() -> Dict[str, Any]:
    """獲取系統狀態"""
    return realtime_monitor.get_current_status()

def get_monitoring_summary() -> str:
    """獲取監控摘要"""
    return realtime_monitor.get_system_summary()