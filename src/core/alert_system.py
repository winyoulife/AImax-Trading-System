#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
警報系統 - 提供錯誤日誌和警報功能
"""

import sys
import os
import logging
import json
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
from queue import Queue, Empty

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """警報級別"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertChannel(Enum):
    """警報通道"""
    LOG = "log"
    EMAIL = "email"
    CONSOLE = "console"
    FILE = "file"
    WEBHOOK = "webhook"

@dataclass
class Alert:
    """警報信息"""
    id: str
    level: AlertLevel
    title: str
    message: str
    component: str
    timestamp: datetime
    channels: List[AlertChannel]
    metadata: Dict[str, Any]
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

@dataclass
class AlertRule:
    """警報規則"""
    name: str
    condition: Callable
    level: AlertLevel
    channels: List[AlertChannel]
    cooldown_minutes: int = 5
    enabled: bool = True
    last_triggered: Optional[datetime] = None

class AlertSystem:
    """警報系統"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.alerts: List[Alert] = []
        self.rules: Dict[str, AlertRule] = {}
        self.channels: Dict[AlertChannel, Callable] = {}
        self.alert_queue = Queue()
        self.processing_thread = None
        self.running = False
        self.max_alerts_history = 1000
        
        # 初始化默認通道
        self._initialize_default_channels()
        
        # 初始化默認規則
        self._initialize_default_rules()
        
        self.logger.info("🚨 警報系統初始化完成")
    
    def _initialize_default_channels(self):
        """初始化默認通道"""
        self.channels.update({
            AlertChannel.LOG: self._send_log_alert,
            AlertChannel.CONSOLE: self._send_console_alert,
            AlertChannel.FILE: self._send_file_alert
        })
    
    def _initialize_default_rules(self):
        """初始化默認規則"""
        # CPU使用率警報
        self.rules['high_cpu'] = AlertRule(
            name="高CPU使用率",
            condition=lambda: self._check_cpu_usage() > 90,
            level=AlertLevel.WARNING,
            channels=[AlertChannel.LOG, AlertChannel.CONSOLE],
            cooldown_minutes=5
        )
        
        # 內存使用率警報
        self.rules['high_memory'] = AlertRule(
            name="高內存使用率",
            condition=lambda: self._check_memory_usage() > 90,
            level=AlertLevel.WARNING,
            channels=[AlertChannel.LOG, AlertChannel.CONSOLE],
            cooldown_minutes=5
        )
        
        # 磁盤空間警報
        self.rules['low_disk'] = AlertRule(
            name="磁盤空間不足",
            condition=lambda: self._check_disk_usage() > 90,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.LOG, AlertChannel.CONSOLE, AlertChannel.FILE],
            cooldown_minutes=10
        )
    
    def start(self):
        """啟動警報系統"""
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(
                target=self._process_alerts,
                daemon=True
            )
            self.processing_thread.start()
            self.logger.info("🚀 警報系統已啟動")
    
    def stop(self):
        """停止警報系統"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        self.logger.info("⏹️ 警報系統已停止")
    
    def send_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        component: str = "system",
        channels: Optional[List[AlertChannel]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """發送警報"""
        alert_id = self._generate_alert_id()
        
        alert = Alert(
            id=alert_id,
            level=level,
            title=title,
            message=message,
            component=component,
            timestamp=datetime.now(),
            channels=channels or [AlertChannel.LOG],
            metadata=metadata or {}
        )
        
        # 添加到隊列
        self.alert_queue.put(alert)
        
        # 添加到歷史
        self._add_to_history(alert)
        
        return alert_id
    
    def _generate_alert_id(self) -> str:
        """生成警報ID"""
        return f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.alerts):04d}"
    
    def _add_to_history(self, alert: Alert):
        """添加到歷史記錄"""
        self.alerts.append(alert)
        
        # 限制歷史大小
        if len(self.alerts) > self.max_alerts_history:
            self.alerts = self.alerts[-self.max_alerts_history:]
    
    def _process_alerts(self):
        """處理警報隊列"""
        while self.running:
            try:
                alert = self.alert_queue.get(timeout=1)
                self._dispatch_alert(alert)
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"❌ 處理警報時發生錯誤: {e}")
    
    def _dispatch_alert(self, alert: Alert):
        """分發警報"""
        for channel in alert.channels:
            try:
                if channel in self.channels:
                    self.channels[channel](alert)
                else:
                    self.logger.warning(f"⚠️ 未知的警報通道: {channel}")
            except Exception as e:
                self.logger.error(f"❌ 發送警報到通道 {channel} 失敗: {e}")
    
    def _send_log_alert(self, alert: Alert):
        """發送日誌警報"""
        level_map = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }
        
        log_level = level_map.get(alert.level, logging.INFO)
        self.logger.log(log_level, f"[{alert.id}] {alert.title}: {alert.message}")
    
    def _send_console_alert(self, alert: Alert):
        """發送控制台警報"""
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        emoji = level_emoji.get(alert.level, "📢")
        timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"\n{emoji} [{alert.level.value.upper()}] {timestamp}")
        print(f"   標題: {alert.title}")
        print(f"   組件: {alert.component}")
        print(f"   消息: {alert.message}")
        if alert.metadata:
            print(f"   詳情: {alert.metadata}")
        print("-" * 50)
    
    def _send_file_alert(self, alert: Alert):
        """發送文件警報"""
        try:
            # 確保日誌目錄存在
            log_dir = Path("AImax/logs/alerts")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # 按日期創建日誌文件
            log_file = log_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.log"
            
            # 格式化警報信息
            alert_data = {
                'id': alert.id,
                'timestamp': alert.timestamp.isoformat(),
                'level': alert.level.value,
                'title': alert.title,
                'message': alert.message,
                'component': alert.component,
                'metadata': alert.metadata
            }
            
            # 寫入文件
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(alert_data, ensure_ascii=False) + '\n')
                
        except Exception as e:
            self.logger.error(f"❌ 寫入警報文件失敗: {e}")
    
    def _send_email_alert(self, alert: Alert):
        """發送郵件警報"""
        # 這裡可以實現郵件發送邏輯
        # 需要配置SMTP服務器信息
        self.logger.info(f"📧 郵件警報: {alert.title}")
    
    def _send_webhook_alert(self, alert: Alert):
        """發送Webhook警報"""
        # 這裡可以實現Webhook發送邏輯
        self.logger.info(f"🔗 Webhook警報: {alert.title}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system"):
        """確認警報"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.now()
                self.logger.info(f"✅ 警報已確認: {alert_id} by {acknowledged_by}")
                return True
        
        self.logger.warning(f"⚠️ 未找到警報: {alert_id}")
        return False
    
    def add_rule(self, rule: AlertRule):
        """添加警報規則"""
        self.rules[rule.name] = rule
        self.logger.info(f"📝 已添加警報規則: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """移除警報規則"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            self.logger.info(f"🗑️ 已移除警報規則: {rule_name}")
    
    def enable_rule(self, rule_name: str):
        """啟用警報規則"""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = True
            self.logger.info(f"✅ 已啟用警報規則: {rule_name}")
    
    def disable_rule(self, rule_name: str):
        """禁用警報規則"""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = False
            self.logger.info(f"❌ 已禁用警報規則: {rule_name}")
    
    def check_rules(self):
        """檢查警報規則"""
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            # 檢查冷卻時間
            if rule.last_triggered:
                cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                if datetime.now() < cooldown_end:
                    continue
            
            try:
                # 檢查條件
                if rule.condition():
                    # 觸發警報
                    self.send_alert(
                        level=rule.level,
                        title=f"規則觸發: {rule.name}",
                        message=f"警報規則 '{rule.name}' 的條件已滿足",
                        component="alert_system",
                        channels=rule.channels,
                        metadata={'rule_name': rule_name}
                    )
                    
                    rule.last_triggered = datetime.now()
                    
            except Exception as e:
                self.logger.error(f"❌ 檢查規則 {rule_name} 時發生錯誤: {e}")
    
    def _check_cpu_usage(self) -> float:
        """檢查CPU使用率"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except:
            return 0.0
    
    def _check_memory_usage(self) -> float:
        """檢查內存使用率"""
        try:
            import psutil
            return psutil.virtual_memory().percent
        except:
            return 0.0
    
    def _check_disk_usage(self) -> float:
        """檢查磁盤使用率"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return (disk.used / disk.total) * 100
        except:
            return 0.0
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """獲取警報統計"""
        if not self.alerts:
            return {
                'total_alerts': 0,
                'acknowledged_alerts': 0,
                'unacknowledged_alerts': 0,
                'levels': {},
                'components': {},
                'recent_alerts': []
            }
        
        total_alerts = len(self.alerts)
        acknowledged_alerts = sum(1 for a in self.alerts if a.acknowledged)
        unacknowledged_alerts = total_alerts - acknowledged_alerts
        
        # 按級別統計
        levels = {}
        for alert in self.alerts:
            level = alert.level.value
            if level not in levels:
                levels[level] = 0
            levels[level] += 1
        
        # 按組件統計
        components = {}
        for alert in self.alerts:
            component = alert.component
            if component not in components:
                components[component] = 0
            components[component] += 1
        
        # 最近的警報（最近10條）
        recent_alerts = []
        for alert in self.alerts[-10:]:
            recent_alerts.append({
                'id': alert.id,
                'level': alert.level.value,
                'title': alert.title,
                'component': alert.component,
                'timestamp': alert.timestamp.isoformat(),
                'acknowledged': alert.acknowledged
            })
        
        return {
            'total_alerts': total_alerts,
            'acknowledged_alerts': acknowledged_alerts,
            'unacknowledged_alerts': unacknowledged_alerts,
            'levels': levels,
            'components': components,
            'recent_alerts': recent_alerts
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """獲取活躍警報（未確認的）"""
        active_alerts = []
        for alert in self.alerts:
            if not alert.acknowledged:
                active_alerts.append({
                    'id': alert.id,
                    'level': alert.level.value,
                    'title': alert.title,
                    'message': alert.message,
                    'component': alert.component,
                    'timestamp': alert.timestamp.isoformat(),
                    'metadata': alert.metadata
                })
        
        return active_alerts
    
    def export_alerts(self, filepath: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        """導出警報記錄"""
        try:
            # 過濾警報
            filtered_alerts = self.alerts
            
            if start_date:
                filtered_alerts = [a for a in filtered_alerts if a.timestamp >= start_date]
            
            if end_date:
                filtered_alerts = [a for a in filtered_alerts if a.timestamp <= end_date]
            
            # 準備導出數據
            export_data = {
                'export_time': datetime.now().isoformat(),
                'total_alerts': len(filtered_alerts),
                'date_range': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                },
                'statistics': self.get_alert_statistics(),
                'alerts': []
            }
            
            # 轉換警報數據
            for alert in filtered_alerts:
                alert_data = asdict(alert)
                alert_data['timestamp'] = alert_data['timestamp'].isoformat()
                alert_data['level'] = alert_data['level'].value
                alert_data['channels'] = [c.value for c in alert_data['channels']]
                if alert_data['acknowledged_at']:
                    alert_data['acknowledged_at'] = alert_data['acknowledged_at'].isoformat()
                export_data['alerts'].append(alert_data)
            
            # 寫入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📄 警報記錄已導出到: {filepath}")
            
        except Exception as e:
            self.logger.error(f"❌ 導出警報記錄失敗: {e}")
    
    def register_channel(self, channel: AlertChannel, handler: Callable):
        """註冊警報通道"""
        self.channels[channel] = handler
        self.logger.info(f"📝 已註冊警報通道: {channel.value}")

def create_alert_system() -> AlertSystem:
    """創建警報系統實例"""
    return AlertSystem()

if __name__ == "__main__":
    # 測試警報系統
    logging.basicConfig(level=logging.INFO)
    
    alert_system = create_alert_system()
    alert_system.start()
    
    try:
        # 發送測試警報
        alert_system.send_alert(
            AlertLevel.INFO,
            "系統啟動",
            "AImax交易系統已成功啟動",
            "system",
            [AlertChannel.LOG, AlertChannel.CONSOLE]
        )
        
        alert_system.send_alert(
            AlertLevel.WARNING,
            "測試警告",
            "這是一個測試警告消息",
            "test_component",
            [AlertChannel.LOG, AlertChannel.CONSOLE, AlertChannel.FILE]
        )
        
        # 檢查規則
        alert_system.check_rules()
        
        import time
        time.sleep(2)  # 等待處理完成
        
        # 輸出統計
        stats = alert_system.get_alert_statistics()
        print(f"警報統計: {stats}")
        
        # 輸出活躍警報
        active = alert_system.get_active_alerts()
        print(f"活躍警報: {active}")
        
    finally:
        alert_system.stop()