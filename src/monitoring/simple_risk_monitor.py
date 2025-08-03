#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化風險監控系統 - 用於測試和驗證
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """風險等級"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"

class AlertType(Enum):
    """警報類型"""
    EXPOSURE_LIMIT = "exposure_limit"
    CONCENTRATION_RISK = "concentration_risk"
    AI_CONFIDENCE = "ai_confidence"
    SYSTEM_HEALTH = "system_health"

class AlertPriority(Enum):
    """警報優先級"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5

@dataclass
class RiskAlert:
    """風險警報"""
    alert_id: str
    alert_type: AlertType
    priority: AlertPriority
    risk_level: RiskLevel
    title: str
    message: str
    risk_value: float
    threshold: float
    timestamp: datetime
    is_active: bool = True

@dataclass
class RiskMetrics:
    """風險指標"""
    total_exposure: float = 0.0
    exposure_utilization: float = 0.0
    concentration_ratio: float = 0.0
    avg_ai_confidence: float = 0.0
    system_health_score: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class RiskMonitoringConfig:
    """風險監控配置"""
    monitoring_interval: float = 5.0
    exposure_warning_threshold: float = 0.8
    exposure_critical_threshold: float = 0.9
    confidence_warning_threshold: float = 0.4
    enable_auto_actions: bool = True

class SimpleRiskMonitor:
    """簡化風險監控系統"""
    
    def __init__(self, config: RiskMonitoringConfig = None):
        self.config = config or RiskMonitoringConfig()
        self.current_metrics = RiskMetrics()
        self.active_alerts: Dict[str, RiskAlert] = {}
        self.is_monitoring = False
        self.monitoring_stats = {
            'total_alerts_generated': 0,
            'auto_actions_executed': 0,
            'system_errors': 0
        }
        
        logger.info("🔍 簡化風險監控系統初始化完成")
    
    async def start_monitoring(self):
        """啟動監控"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        logger.info("🚀 啟動風險監控")
        
        try:
            await self._monitoring_loop()
        except Exception as e:
            logger.error(f"❌ 監控錯誤: {e}")
            self.is_monitoring = False
    
    async def stop_monitoring(self):
        """停止監控"""
        logger.info("🛑 停止風險監控")
        self.is_monitoring = False
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                # 更新指標
                await self._update_metrics()
                
                # 檢查警報
                await self._check_alerts()
                
                # 等待下次循環
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ 監控循環錯誤: {e}")
                self.monitoring_stats['system_errors'] += 1
                await asyncio.sleep(1.0)
    
    async def _update_metrics(self):
        """更新風險指標"""
        try:
            # 模擬指標更新
            import random
            self.current_metrics.total_exposure = random.uniform(50000, 150000)
            self.current_metrics.exposure_utilization = random.uniform(0.3, 0.9)
            self.current_metrics.concentration_ratio = random.uniform(0.2, 0.7)
            self.current_metrics.avg_ai_confidence = random.uniform(0.4, 0.9)
            self.current_metrics.system_health_score = random.uniform(0.7, 1.0)
            self.current_metrics.timestamp = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ 更新指標失敗: {e}")
    
    async def _check_alerts(self):
        """檢查警報"""
        try:
            # 檢查敞口警報
            if self.current_metrics.exposure_utilization >= self.config.exposure_critical_threshold:
                await self._trigger_alert("exposure_critical", AlertType.EXPOSURE_LIMIT, 
                                         AlertPriority.CRITICAL, "敞口危險警報")
            elif self.current_metrics.exposure_utilization >= self.config.exposure_warning_threshold:
                await self._trigger_alert("exposure_warning", AlertType.EXPOSURE_LIMIT, 
                                         AlertPriority.HIGH, "敞口警告")
            
            # 檢查AI信心度警報
            if self.current_metrics.avg_ai_confidence <= self.config.confidence_warning_threshold:
                await self._trigger_alert("confidence_low", AlertType.AI_CONFIDENCE, 
                                         AlertPriority.HIGH, "AI信心度過低")
            
        except Exception as e:
            logger.error(f"❌ 檢查警報失敗: {e}")
    
    async def _trigger_alert(self, alert_id: str, alert_type: AlertType, 
                           priority: AlertPriority, title: str):
        """觸發警報"""
        try:
            if alert_id in self.active_alerts:
                return  # 警報已存在
            
            alert = RiskAlert(
                alert_id=alert_id,
                alert_type=alert_type,
                priority=priority,
                risk_level=RiskLevel.HIGH if priority == AlertPriority.HIGH else RiskLevel.CRITICAL,
                title=title,
                message=f"{title}: {self.current_metrics.exposure_utilization:.1%}",
                risk_value=self.current_metrics.exposure_utilization,
                threshold=self.config.exposure_warning_threshold,
                timestamp=datetime.now()
            )
            
            self.active_alerts[alert_id] = alert
            self.monitoring_stats['total_alerts_generated'] += 1
            
            logger.warning(f"🚨 風險警報: {title}")
            
        except Exception as e:
            logger.error(f"❌ 觸發警報失敗: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """獲取監控狀態"""
        try:
            return {
                'is_monitoring': self.is_monitoring,
                'current_metrics': {
                    'total_exposure': self.current_metrics.total_exposure,
                    'exposure_utilization': self.current_metrics.exposure_utilization,
                    'concentration_ratio': self.current_metrics.concentration_ratio,
                    'avg_ai_confidence': self.current_metrics.avg_ai_confidence,
                    'system_health_score': self.current_metrics.system_health_score
                },
                'active_alerts': {
                    'count': len(self.active_alerts),
                    'alerts': [
                        {
                            'title': alert.title,
                            'priority': alert.priority.name,
                            'message': alert.message
                        }
                        for alert in self.active_alerts.values()
                    ]
                },
                'statistics': self.monitoring_stats.copy()
            }
        except Exception as e:
            logger.error(f"❌ 獲取監控狀態失敗: {e}")
            return {}
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """獲取風險摘要"""
        try:
            # 計算總體風險等級
            risk_score = (
                self.current_metrics.exposure_utilization * 0.3 +
                self.current_metrics.concentration_ratio * 0.2 +
                (1.0 - self.current_metrics.avg_ai_confidence) * 0.3 +
                (1.0 - self.current_metrics.system_health_score) * 0.2
            )
            
            if risk_score >= 0.8:
                overall_risk = RiskLevel.VERY_HIGH
            elif risk_score >= 0.6:
                overall_risk = RiskLevel.HIGH
            elif risk_score >= 0.4:
                overall_risk = RiskLevel.MEDIUM
            elif risk_score >= 0.2:
                overall_risk = RiskLevel.LOW
            else:
                overall_risk = RiskLevel.VERY_LOW
            
            return {
                'overall_risk_level': overall_risk.value,
                'overall_risk_score': risk_score,
                'active_alerts_count': len(self.active_alerts),
                'last_update': self.current_metrics.timestamp.isoformat()
            }
        except Exception as e:
            logger.error(f"❌ 獲取風險摘要失敗: {e}")
            return {}


# 創建簡化風險監控系統實例
def create_simple_risk_monitor(config: RiskMonitoringConfig = None) -> SimpleRiskMonitor:
    """創建簡化風險監控系統實例"""
    return SimpleRiskMonitor(config)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_simple_risk_monitor():
        """測試簡化風險監控系統"""
        print("🧪 測試簡化風險監控系統...")
        
        # 創建監控系統
        monitor = create_simple_risk_monitor()
        
        # 啟動監控任務
        monitoring_task = asyncio.create_task(monitor.start_monitoring())
        
        # 運行5秒
        await asyncio.sleep(5)
        
        # 停止監控
        await monitor.stop_monitoring()
        monitoring_task.cancel()
        
        # 獲取狀態
        status = monitor.get_monitoring_status()
        summary = monitor.get_risk_summary()
        
        print(f"✅ 監控狀態: {status}")
        print(f"✅ 風險摘要: {summary}")
        
        print("✅ 簡化風險監控系統測試完成")
    
    # 運行測試
    asyncio.run(test_simple_risk_monitor())