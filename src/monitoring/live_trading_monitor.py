#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實盤交易實時監控系統
提供實時監控、警報和緊急停止功能
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import json
import threading
import time
import queue
from pathlib import Path

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """警報等級"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class Alert:
    """警報"""
    timestamp: datetime
    level: AlertLevel
    title: str
    message: str
    data: Dict[str, Any]
    acknowledged: bool = False

@dataclass
class MonitoringMetrics:
    """監控指標"""
    timestamp: datetime
    balance: float
    daily_pnl: float
    total_trades: int
    consecutive_losses: int
    ai_confidence: float
    system_health: str
    active_positions: int
    risk_level: str

class LiveTradingMonitor:
    """實盤交易監控器"""
    
    def __init__(self):
        """初始化監控器"""
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.alerts: List[Alert] = []
        self.metrics_history: List[MonitoringMetrics] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        self.emergency_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # 監控配置
        self.monitor_interval = 5  # 秒
        self.max_alerts = 1000
        self.max_metrics_history = 10000
        
        # 警報閾值
        self.alert_thresholds = {
            'balance_drop_pct': 5.0,      # 餘額下降5%警報
            'consecutive_losses': 3,       # 連續虧損3次警報
            'low_confidence': 0.6,         # AI信心度低於60%警報
            'high_risk_trades': 5,         # 高風險交易數量警報
            'system_error_count': 3        # 系統錯誤次數警報
        }
        
        # 緊急停止條件
        self.emergency_conditions = {
            'balance_drop_pct': 10.0,      # 餘額下降10%緊急停止
            'consecutive_losses': 5,       # 連續虧損5次緊急停止
            'system_critical_errors': 5    # 系統嚴重錯誤5次緊急停止
        }
        
        # 狀態追蹤
        self.last_balance = 0.0
        self.initial_balance = 0.0
        self.error_count = 0
        self.critical_error_count = 0
        
        logger.info("👁️ 實盤交易監控器初始化完成")
    
    def start_monitoring(self, initial_balance: float) -> None:
        """開始監控"""
        if self.is_monitoring:
            logger.warning("⚠️ 監控已在運行中")
            return
        
        self.initial_balance = initial_balance
        self.last_balance = initial_balance
        self.is_monitoring = True
        
        # 創建日誌目錄
        Path("AImax/logs/monitoring").mkdir(parents=True, exist_ok=True)
        
        # 啟動監控線程
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # 發送開始監控警報
        self._create_alert(
            AlertLevel.INFO,
            "監控開始",
            f"實盤交易監控已啟動，初始資金: {initial_balance:.2f} TWD",
            {'initial_balance': initial_balance}
        )
        
        logger.info(f"👁️ 實盤交易監控已啟動 - 初始資金: {initial_balance:.2f} TWD")
    
    def stop_monitoring(self) -> None:
        """停止監控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        # 發送停止監控警報
        self._create_alert(
            AlertLevel.INFO,
            "監控停止",
            "實盤交易監控已停止",
            {}
        )
        
        # 保存監控報告
        self._save_monitoring_report()
        
        logger.info("👁️ 實盤交易監控已停止")
    
    def update_metrics(self, balance: float, daily_pnl: float, total_trades: int,
                      consecutive_losses: int, ai_confidence: float,
                      active_positions: int = 0, system_health: str = "healthy") -> None:
        """更新監控指標"""
        
        # 計算風險等級
        risk_level = self._calculate_risk_level(balance, consecutive_losses, ai_confidence)
        
        # 創建指標記錄
        metrics = MonitoringMetrics(
            timestamp=datetime.now(),
            balance=balance,
            daily_pnl=daily_pnl,
            total_trades=total_trades,
            consecutive_losses=consecutive_losses,
            ai_confidence=ai_confidence,
            system_health=system_health,
            active_positions=active_positions,
            risk_level=risk_level
        )
        
        # 添加到歷史記錄
        self.metrics_history.append(metrics)
        
        # 限制歷史記錄數量
        if len(self.metrics_history) > self.max_metrics_history:
            self.metrics_history = self.metrics_history[-self.max_metrics_history:]
        
        # 檢查警報條件
        self._check_alert_conditions(metrics)
        
        # 檢查緊急停止條件
        self._check_emergency_conditions(metrics)
        
        # 更新最後餘額
        self.last_balance = balance
    
    def _calculate_risk_level(self, balance: float, consecutive_losses: int, 
                            ai_confidence: float) -> str:
        """計算風險等級"""
        risk_score = 0
        
        # 餘額下降風險
        if self.initial_balance > 0:
            balance_drop_pct = (self.initial_balance - balance) / self.initial_balance * 100
            if balance_drop_pct > 5:
                risk_score += 2
            elif balance_drop_pct > 2:
                risk_score += 1
        
        # 連續虧損風險
        if consecutive_losses >= 3:
            risk_score += 2
        elif consecutive_losses >= 2:
            risk_score += 1
        
        # AI信心度風險
        if ai_confidence < 0.6:
            risk_score += 2
        elif ai_confidence < 0.7:
            risk_score += 1
        
        # 系統錯誤風險
        if self.critical_error_count > 0:
            risk_score += 2
        elif self.error_count > 3:
            risk_score += 1
        
        # 風險等級判定
        if risk_score >= 5:
            return "極高"
        elif risk_score >= 3:
            return "高"
        elif risk_score >= 1:
            return "中"
        else:
            return "低"
    
    def _check_alert_conditions(self, metrics: MonitoringMetrics) -> None:
        """檢查警報條件"""
        
        # 餘額下降警報
        if self.initial_balance > 0:
            balance_drop_pct = (self.initial_balance - metrics.balance) / self.initial_balance * 100
            if balance_drop_pct >= self.alert_thresholds['balance_drop_pct']:
                self._create_alert(
                    AlertLevel.WARNING,
                    "餘額下降警報",
                    f"餘額下降 {balance_drop_pct:.1f}%，當前餘額: {metrics.balance:.2f} TWD",
                    {'balance_drop_pct': balance_drop_pct, 'current_balance': metrics.balance}
                )
        
        # 連續虧損警報
        if metrics.consecutive_losses >= self.alert_thresholds['consecutive_losses']:
            self._create_alert(
                AlertLevel.WARNING,
                "連續虧損警報",
                f"連續虧損 {metrics.consecutive_losses} 次",
                {'consecutive_losses': metrics.consecutive_losses}
            )
        
        # AI信心度警報
        if metrics.ai_confidence < self.alert_thresholds['low_confidence']:
            self._create_alert(
                AlertLevel.WARNING,
                "AI信心度低警報",
                f"AI信心度僅 {metrics.ai_confidence:.1%}，低於閾值 {self.alert_thresholds['low_confidence']:.1%}",
                {'ai_confidence': metrics.ai_confidence}
            )
        
        # 系統健康警報
        if metrics.system_health != "healthy":
            self._create_alert(
                AlertLevel.CRITICAL,
                "系統健康警報",
                f"系統健康狀態: {metrics.system_health}",
                {'system_health': metrics.system_health}
            )
        
        # 高風險等級警報
        if metrics.risk_level in ["高", "極高"]:
            self._create_alert(
                AlertLevel.CRITICAL,
                "高風險警報",
                f"當前風險等級: {metrics.risk_level}",
                {'risk_level': metrics.risk_level}
            )
    
    def _check_emergency_conditions(self, metrics: MonitoringMetrics) -> None:
        """檢查緊急停止條件"""
        emergency_reasons = []
        
        # 餘額下降緊急停止
        if self.initial_balance > 0:
            balance_drop_pct = (self.initial_balance - metrics.balance) / self.initial_balance * 100
            if balance_drop_pct >= self.emergency_conditions['balance_drop_pct']:
                emergency_reasons.append(f"餘額下降 {balance_drop_pct:.1f}%")
        
        # 連續虧損緊急停止
        if metrics.consecutive_losses >= self.emergency_conditions['consecutive_losses']:
            emergency_reasons.append(f"連續虧損 {metrics.consecutive_losses} 次")
        
        # 系統嚴重錯誤緊急停止
        if self.critical_error_count >= self.emergency_conditions['system_critical_errors']:
            emergency_reasons.append(f"系統嚴重錯誤 {self.critical_error_count} 次")
        
        if emergency_reasons:
            self._trigger_emergency_stop(emergency_reasons, metrics)
    
    def _trigger_emergency_stop(self, reasons: List[str], metrics: MonitoringMetrics) -> None:
        """觸發緊急停止"""
        emergency_info = {
            'timestamp': datetime.now().isoformat(),
            'reasons': reasons,
            'metrics': {
                'balance': metrics.balance,
                'daily_pnl': metrics.daily_pnl,
                'total_trades': metrics.total_trades,
                'consecutive_losses': metrics.consecutive_losses,
                'ai_confidence': metrics.ai_confidence,
                'risk_level': metrics.risk_level
            },
            'initial_balance': self.initial_balance,
            'total_loss': self.initial_balance - metrics.balance
        }
        
        # 創建緊急警報
        self._create_alert(
            AlertLevel.EMERGENCY,
            "緊急停止觸發",
            f"緊急停止條件觸發: {', '.join(reasons)}",
            emergency_info
        )
        
        # 執行緊急回調
        for callback in self.emergency_callbacks:
            try:
                callback(emergency_info)
            except Exception as e:
                logger.error(f"❌ 緊急回調執行失敗: {e}")
        
        # 保存緊急停止記錄
        self._save_emergency_stop_record(emergency_info)
        
        logger.critical(f"🚨 緊急停止觸發 - 原因: {', '.join(reasons)}")
    
    def _create_alert(self, level: AlertLevel, title: str, message: str, 
                     data: Dict[str, Any]) -> None:
        """創建警報"""
        alert = Alert(
            timestamp=datetime.now(),
            level=level,
            title=title,
            message=message,
            data=data
        )
        
        self.alerts.append(alert)
        
        # 限制警報數量
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # 執行警報回調
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"❌ 警報回調執行失敗: {e}")
        
        # 記錄警報
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🚨",
            AlertLevel.EMERGENCY: "🆘"
        }
        
        logger.log(
            logging.INFO if level == AlertLevel.INFO else
            logging.WARNING if level == AlertLevel.WARNING else
            logging.ERROR,
            f"{level_emoji[level]} {title}: {message}"
        )
    
    def _monitoring_loop(self) -> None:
        """監控循環"""
        while self.is_monitoring:
            try:
                # 檢查系統狀態
                self._check_system_health()
                
                # 清理過期警報
                self._cleanup_old_alerts()
                
                # 定期保存監控數據
                if len(self.metrics_history) % 100 == 0:
                    self._save_monitoring_data()
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.error_count += 1
                logger.error(f"❌ 監控循環錯誤: {e}")
                
                if "critical" in str(e).lower():
                    self.critical_error_count += 1
                
                time.sleep(self.monitor_interval * 2)  # 錯誤時延長間隔
    
    def _check_system_health(self) -> None:
        """檢查系統健康狀態"""
        # 這裡可以添加系統健康檢查邏輯
        # 例如：檢查API連接、數據庫狀態、AI模型狀態等
        pass
    
    def _cleanup_old_alerts(self) -> None:
        """清理過期警報"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.alerts = [alert for alert in self.alerts if alert.timestamp > cutoff_time]
    
    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """添加警報回調"""
        self.alert_callbacks.append(callback)
    
    def add_emergency_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """添加緊急停止回調"""
        self.emergency_callbacks.append(callback)
    
    def get_recent_alerts(self, hours: int = 1) -> List[Alert]:
        """獲取最近的警報"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alerts if alert.timestamp > cutoff_time]
    
    def get_current_status(self) -> Dict[str, Any]:
        """獲取當前監控狀態"""
        recent_metrics = self.metrics_history[-1] if self.metrics_history else None
        recent_alerts = self.get_recent_alerts(1)
        
        return {
            'is_monitoring': self.is_monitoring,
            'total_alerts': len(self.alerts),
            'recent_alerts': len(recent_alerts),
            'error_count': self.error_count,
            'critical_error_count': self.critical_error_count,
            'current_metrics': {
                'balance': recent_metrics.balance if recent_metrics else 0,
                'risk_level': recent_metrics.risk_level if recent_metrics else "未知",
                'ai_confidence': recent_metrics.ai_confidence if recent_metrics else 0,
                'consecutive_losses': recent_metrics.consecutive_losses if recent_metrics else 0
            } if recent_metrics else None,
            'alert_summary': {
                'info': len([a for a in recent_alerts if a.level == AlertLevel.INFO]),
                'warning': len([a for a in recent_alerts if a.level == AlertLevel.WARNING]),
                'critical': len([a for a in recent_alerts if a.level == AlertLevel.CRITICAL]),
                'emergency': len([a for a in recent_alerts if a.level == AlertLevel.EMERGENCY])
            }
        }
    
    def _save_monitoring_data(self) -> None:
        """保存監控數據"""
        try:
            # 保存指標歷史
            metrics_file = f"AImax/logs/monitoring/metrics_{datetime.now().strftime('%Y%m%d')}.json"
            with open(metrics_file, 'w', encoding='utf-8') as f:
                metrics_data = [
                    {
                        'timestamp': m.timestamp.isoformat(),
                        'balance': m.balance,
                        'daily_pnl': m.daily_pnl,
                        'total_trades': m.total_trades,
                        'consecutive_losses': m.consecutive_losses,
                        'ai_confidence': m.ai_confidence,
                        'system_health': m.system_health,
                        'active_positions': m.active_positions,
                        'risk_level': m.risk_level
                    }
                    for m in self.metrics_history[-100:]  # 只保存最近100條
                ]
                json.dump(metrics_data, f, ensure_ascii=False, indent=2)
            
            # 保存警報歷史
            alerts_file = f"AImax/logs/monitoring/alerts_{datetime.now().strftime('%Y%m%d')}.json"
            with open(alerts_file, 'w', encoding='utf-8') as f:
                alerts_data = [
                    {
                        'timestamp': a.timestamp.isoformat(),
                        'level': a.level.value,
                        'title': a.title,
                        'message': a.message,
                        'data': a.data,
                        'acknowledged': a.acknowledged
                    }
                    for a in self.alerts[-100:]  # 只保存最近100條
                ]
                json.dump(alerts_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ 保存監控數據失敗: {e}")
    
    def _save_monitoring_report(self) -> None:
        """保存監控報告"""
        try:
            report = {
                'monitoring_period': {
                    'start': self.metrics_history[0].timestamp.isoformat() if self.metrics_history else None,
                    'end': datetime.now().isoformat()
                },
                'summary': {
                    'total_metrics_recorded': len(self.metrics_history),
                    'total_alerts': len(self.alerts),
                    'error_count': self.error_count,
                    'critical_error_count': self.critical_error_count,
                    'initial_balance': self.initial_balance,
                    'final_balance': self.metrics_history[-1].balance if self.metrics_history else 0
                },
                'alert_breakdown': {
                    'info': len([a for a in self.alerts if a.level == AlertLevel.INFO]),
                    'warning': len([a for a in self.alerts if a.level == AlertLevel.WARNING]),
                    'critical': len([a for a in self.alerts if a.level == AlertLevel.CRITICAL]),
                    'emergency': len([a for a in self.alerts if a.level == AlertLevel.EMERGENCY])
                }
            }
            
            report_file = f"AImax/logs/monitoring/monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📄 監控報告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存監控報告失敗: {e}")
    
    def _save_emergency_stop_record(self, emergency_info: Dict[str, Any]) -> None:
        """保存緊急停止記錄"""
        try:
            emergency_file = f"AImax/logs/monitoring/emergency_stop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(emergency_file, 'w', encoding='utf-8') as f:
                json.dump(emergency_info, f, ensure_ascii=False, indent=2)
            
            logger.critical(f"🚨 緊急停止記錄已保存: {emergency_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存緊急停止記錄失敗: {e}")


# 創建全局監控器實例
def create_live_monitor() -> LiveTradingMonitor:
    """創建實盤交易監控器實例"""
    return LiveTradingMonitor()


# 測試代碼
if __name__ == "__main__":
    import time
    
    def alert_callback(alert: Alert):
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️", 
            AlertLevel.CRITICAL: "🚨",
            AlertLevel.EMERGENCY: "🆘"
        }
        print(f"{level_emoji[alert.level]} {alert.title}: {alert.message}")
    
    def emergency_callback(emergency_info):
        print(f"🚨 緊急停止: {emergency_info}")
    
    # 測試監控器
    print("🧪 測試實盤交易監控器...")
    
    monitor = create_live_monitor()
    monitor.add_alert_callback(alert_callback)
    monitor.add_emergency_callback(emergency_callback)
    
    # 開始監控
    monitor.start_monitoring(10000.0)
    
    # 模擬一些指標更新
    print("\n📊 模擬指標更新...")
    
    # 正常狀態
    monitor.update_metrics(10000.0, 0.0, 0, 0, 0.8)
    time.sleep(1)
    
    # 輕微虧損
    monitor.update_metrics(9800.0, -200.0, 1, 1, 0.75)
    time.sleep(1)
    
    # 連續虧損
    monitor.update_metrics(9500.0, -500.0, 3, 3, 0.65)
    time.sleep(1)
    
    # 觸發緊急停止
    monitor.update_metrics(8900.0, -1100.0, 5, 5, 0.5)
    time.sleep(1)
    
    # 檢查狀態
    status = monitor.get_current_status()
    print(f"\n📊 監控狀態:")
    print(f"   總警報: {status['total_alerts']}")
    print(f"   最近警報: {status['recent_alerts']}")
    print(f"   當前風險等級: {status['current_metrics']['risk_level'] if status['current_metrics'] else '未知'}")
    
    # 停止監控
    time.sleep(2)
    monitor.stop_monitoring()
    
    print("\n✅ 監控器測試完成")