#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
風險監控和預警系統 - 多維度風險指標監控和智能預警
提供實時風險監控、預警機制和自動處理功能
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import math
import numpy as np
from collections import deque

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """風險等級"""
    LOW = "low"           # 低風險
    MEDIUM = "medium"     # 中等風險
    HIGH = "high"         # 高風險
    CRITICAL = "critical" # 危險風險
    EMERGENCY = "emergency" # 緊急風險

class AlertType(Enum):
    """警報類型"""
    EXPOSURE_LIMIT = "exposure_limit"         # 敞口限制
    CONCENTRATION_RISK = "concentration_risk" # 集中度風險
    VAR_EXCEEDED = "var_exceeded"             # VaR超限
    CORRELATION_HIGH = "correlation_high"     # 相關性過高
    VOLATILITY_SPIKE = "volatility_spike"     # 波動率激增
    LIQUIDITY_RISK = "liquidity_risk"         # 流動性風險
    DRAWDOWN_LIMIT = "drawdown_limit"         # 回撤限制
    PERFORMANCE_ANOMALY = "performance_anomaly" # 績效異常

class AlertStatus(Enum):
    """警報狀態"""
    ACTIVE = "active"       # 活躍
    ACKNOWLEDGED = "acknowledged" # 已確認
    RESOLVED = "resolved"   # 已解決
    ESCALATED = "escalated" # 已升級

@dataclass
class RiskMetric:
    """風險指標"""
    metric_name: str
    current_value: float
    threshold_value: float
    risk_level: RiskLevel
    trend: str  # "increasing", "decreasing", "stable"
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class RiskAlert:
    """風險警報"""
    alert_id: str
    alert_type: AlertType
    risk_level: RiskLevel
    title: str
    message: str
    current_value: float
    threshold_value: float
    affected_pairs: List[str]
    affected_strategies: List[str]
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    escalation_count: int = 0

@dataclass
class RiskMonitoringConfig:
    """風險監控配置"""
    # 監控間隔
    monitoring_interval: float = 5.0           # 監控間隔(秒)
    alert_check_interval: float = 10.0         # 警報檢查間隔(秒)
    metric_history_size: int = 1000            # 指標歷史大小
    
    # 風險閾值
    exposure_warning_threshold: float = 0.7    # 敞口警告閾值
    exposure_critical_threshold: float = 0.9   # 敞口危險閾值
    concentration_warning_threshold: float = 0.3 # 集中度警告閾值
    concentration_critical_threshold: float = 0.5 # 集中度危險閾值
    var_warning_multiplier: float = 0.8        # VaR警告倍數
    var_critical_multiplier: float = 1.0       # VaR危險倍數
    correlation_warning_threshold: float = 0.7 # 相關性警告閾值
    correlation_critical_threshold: float = 0.85 # 相關性危險閾值
    volatility_spike_threshold: float = 2.0    # 波動率激增閾值
    drawdown_warning_threshold: float = 0.05   # 回撤警告閾值(5%)
    drawdown_critical_threshold: float = 0.1   # 回撤危險閾值(10%)
    
    # 警報設置
    alert_cooldown_period: float = 300.0       # 警報冷卻期(秒)
    auto_escalation_time: float = 1800.0       # 自動升級時間(秒)
    max_escalation_level: int = 3              # 最大升級等級
    
    # 自動處理
    enable_auto_response: bool = True          # 啟用自動響應
    emergency_auto_action: bool = False        # 緊急情況自動處理

class RiskMonitoringSystem:
    """風險監控和預警系統"""
    
    def __init__(self, config: RiskMonitoringConfig):
        self.config = config
        
        # 風險指標
        self.risk_metrics: Dict[str, RiskMetric] = {}
        self.metric_history: Dict[str, deque] = {}
        
        # 警報管理
        self.active_alerts: Dict[str, RiskAlert] = {}
        self.alert_history: List[RiskAlert] = []
        self.alert_cooldowns: Dict[str, datetime] = {}
        
        # 監控狀態
        self.is_monitoring = False
        self.last_monitoring_time = datetime.now()
        
        # 回調函數
        self.alert_callbacks: List[Callable] = []
        self.metric_callbacks: List[Callable] = []
        
        # 統計數據
        self.monitoring_stats = {
            'total_alerts_generated': 0,
            'alerts_by_type': {},
            'alerts_by_level': {},
            'avg_response_time': 0.0,
            'escalated_alerts': 0,
            'auto_resolved_alerts': 0,
            'monitoring_uptime': 0.0,
            'last_critical_alert': None
        }
        
        # 外部系統引用
        self.global_risk_manager = None
        self.position_manager = None
        
        logger.info("👁️ 風險監控和預警系統初始化完成")
        logger.info(f"   監控間隔: {config.monitoring_interval} 秒")
        logger.info(f"   警報檢查間隔: {config.alert_check_interval} 秒")
        logger.info(f"   自動響應: {'啟用' if config.enable_auto_response else '禁用'}")
    
    def set_external_systems(self, global_risk_manager=None, position_manager=None):
        """設置外部系統引用"""
        self.global_risk_manager = global_risk_manager
        self.position_manager = position_manager
        logger.info("🔗 外部系統引用設置完成")
    
    def add_alert_callback(self, callback: Callable):
        """添加警報回調函數"""
        self.alert_callbacks.append(callback)
        logger.debug(f"📞 添加警報回調函數: {callback.__name__}")
    
    def add_metric_callback(self, callback: Callable):
        """添加指標回調函數"""
        self.metric_callbacks.append(callback)
        logger.debug(f"📞 添加指標回調函數: {callback.__name__}")
    
    async def start_monitoring(self):
        """啟動風險監控"""
        if self.is_monitoring:
            logger.warning("⚠️ 風險監控已在運行中")
            return
        
        self.is_monitoring = True
        logger.info("🚀 啟動風險監控和預警系統")
        
        try:
            # 啟動監控任務
            monitoring_tasks = [
                self._risk_monitoring_loop(),
                self._alert_management_loop(),
                self._metric_calculation_loop(),
                self._escalation_management_loop()
            ]
            
            await asyncio.gather(*monitoring_tasks)
            
        except Exception as e:
            logger.error(f"❌ 風險監控啟動失敗: {e}")
            self.is_monitoring = False
            raise
    
    async def stop_monitoring(self):
        """停止風險監控"""
        logger.info("🛑 停止風險監控和預警系統")
        self.is_monitoring = False
        logger.info("✅ 風險監控已停止")
    
    async def update_risk_metric(self, metric_name: str, value: float, 
                                threshold: float, risk_level: RiskLevel = None):
        """更新風險指標"""
        try:
            # 計算風險等級
            if risk_level is None:
                risk_level = self._calculate_risk_level(value, threshold, metric_name)
            
            # 計算趨勢
            trend = self._calculate_trend(metric_name, value)
            
            # 創建或更新指標
            metric = RiskMetric(
                metric_name=metric_name,
                current_value=value,
                threshold_value=threshold,
                risk_level=risk_level,
                trend=trend
            )
            
            self.risk_metrics[metric_name] = metric
            
            # 更新歷史記錄
            if metric_name not in self.metric_history:
                self.metric_history[metric_name] = deque(maxlen=self.config.metric_history_size)
            
            self.metric_history[metric_name].append({
                'timestamp': datetime.now(),
                'value': value,
                'risk_level': risk_level.value
            })
            
            # 檢查是否需要觸發警報
            await self._check_metric_alerts(metric)
            
            # 調用回調函數
            for callback in self.metric_callbacks:
                try:
                    await callback(metric)
                except Exception as e:
                    logger.error(f"❌ 指標回調函數執行失敗: {e}")
            
            logger.debug(f"📊 更新風險指標: {metric_name} = {value:.4f} ({risk_level.value})")
            
        except Exception as e:
            logger.error(f"❌ 更新風險指標失敗: {e}")
    
    async def create_alert(self, alert_type: AlertType, risk_level: RiskLevel,
                          title: str, message: str, current_value: float,
                          threshold_value: float, affected_pairs: List[str] = None,
                          affected_strategies: List[str] = None) -> str:
        """創建風險警報"""
        try:
            # 檢查冷卻期
            alert_key = f"{alert_type.value}_{risk_level.value}"
            if self._is_in_cooldown(alert_key):
                logger.debug(f"🔇 警報在冷卻期內，跳過: {alert_key}")
                return None
            
            # 生成警報ID
            alert_id = f"alert_{alert_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # 創建警報
            alert = RiskAlert(
                alert_id=alert_id,
                alert_type=alert_type,
                risk_level=risk_level,
                title=title,
                message=message,
                current_value=current_value,
                threshold_value=threshold_value,
                affected_pairs=affected_pairs or [],
                affected_strategies=affected_strategies or []
            )
            
            # 註冊警報
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # 設置冷卻期
            self.alert_cooldowns[alert_key] = datetime.now()
            
            # 更新統計
            self.monitoring_stats['total_alerts_generated'] += 1
            
            if alert_type.value not in self.monitoring_stats['alerts_by_type']:
                self.monitoring_stats['alerts_by_type'][alert_type.value] = 0
            self.monitoring_stats['alerts_by_type'][alert_type.value] += 1
            
            if risk_level.value not in self.monitoring_stats['alerts_by_level']:
                self.monitoring_stats['alerts_by_level'][risk_level.value] = 0
            self.monitoring_stats['alerts_by_level'][risk_level.value] += 1
            
            if risk_level == RiskLevel.CRITICAL:
                self.monitoring_stats['last_critical_alert'] = datetime.now()
            
            # 記錄日誌
            self._log_alert(alert)
            
            # 調用回調函數
            for callback in self.alert_callbacks:
                try:
                    await callback(alert)
                except Exception as e:
                    logger.error(f"❌ 警報回調函數執行失敗: {e}")
            
            # 自動響應處理
            if self.config.enable_auto_response:
                await self._handle_auto_response(alert)
            
            return alert_id
            
        except Exception as e:
            logger.error(f"❌ 創建風險警報失敗: {e}")
            return None
    
    async def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """確認警報"""
        try:
            if alert_id not in self.active_alerts:
                logger.warning(f"⚠️ 警報不存在: {alert_id}")
                return False
            
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now()
            
            logger.info(f"✅ 警報已確認: {alert_id} (by {user})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 確認警報失敗: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str, user: str = "system") -> bool:
        """解決警報"""
        try:
            if alert_id not in self.active_alerts:
                logger.warning(f"⚠️ 警報不存在: {alert_id}")
                return False
            
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            # 從活躍警報中移除
            del self.active_alerts[alert_id]
            
            logger.info(f"✅ 警報已解決: {alert_id} (by {user})")
            return True
            
        except Exception as e:
            logger.error(f"❌ 解決警報失敗: {e}")
            return False
    
    def _calculate_risk_level(self, value: float, threshold: float, metric_name: str) -> RiskLevel:
        """計算風險等級"""
        try:
            ratio = value / threshold if threshold > 0 else 0
            
            # 根據指標類型調整計算邏輯
            if metric_name in ['exposure_utilization', 'concentration_ratio']:
                if ratio >= 1.0:
                    return RiskLevel.EMERGENCY
                elif ratio >= 0.9:
                    return RiskLevel.CRITICAL
                elif ratio >= 0.7:
                    return RiskLevel.HIGH
                elif ratio >= 0.5:
                    return RiskLevel.MEDIUM
                else:
                    return RiskLevel.LOW
            
            elif metric_name in ['daily_var_95', 'daily_var_99']:
                if ratio >= 1.2:
                    return RiskLevel.EMERGENCY
                elif ratio >= 1.0:
                    return RiskLevel.CRITICAL
                elif ratio >= 0.8:
                    return RiskLevel.HIGH
                elif ratio >= 0.6:
                    return RiskLevel.MEDIUM
                else:
                    return RiskLevel.LOW
            
            else:
                # 默認邏輯
                if ratio >= 1.0:
                    return RiskLevel.CRITICAL
                elif ratio >= 0.8:
                    return RiskLevel.HIGH
                elif ratio >= 0.6:
                    return RiskLevel.MEDIUM
                else:
                    return RiskLevel.LOW
                    
        except Exception as e:
            logger.error(f"❌ 計算風險等級失敗: {e}")
            return RiskLevel.MEDIUM
    
    def _calculate_trend(self, metric_name: str, current_value: float) -> str:
        """計算趨勢"""
        try:
            if metric_name not in self.metric_history:
                return "stable"
            
            history = self.metric_history[metric_name]
            if len(history) < 3:
                return "stable"
            
            # 取最近3個值計算趨勢
            recent_values = [entry['value'] for entry in list(history)[-3:]]
            
            # 計算變化率
            change_rate = (recent_values[-1] - recent_values[0]) / recent_values[0] if recent_values[0] != 0 else 0
            
            if change_rate > 0.05:  # 5%以上增長
                return "increasing"
            elif change_rate < -0.05:  # 5%以上下降
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"❌ 計算趨勢失敗: {e}")
            return "stable"
    
    def _is_in_cooldown(self, alert_key: str) -> bool:
        """檢查是否在冷卻期內"""
        try:
            if alert_key not in self.alert_cooldowns:
                return False
            
            cooldown_end = self.alert_cooldowns[alert_key] + timedelta(seconds=self.config.alert_cooldown_period)
            return datetime.now() < cooldown_end
            
        except Exception as e:
            logger.error(f"❌ 檢查冷卻期失敗: {e}")
            return False
    
    def _log_alert(self, alert: RiskAlert):
        """記錄警報日誌"""
        try:
            level_emoji = {
                RiskLevel.LOW: "🟢",
                RiskLevel.MEDIUM: "🟡",
                RiskLevel.HIGH: "🟠",
                RiskLevel.CRITICAL: "🔴",
                RiskLevel.EMERGENCY: "🚨"
            }
            
            emoji = level_emoji.get(alert.risk_level, "⚠️")
            
            if alert.risk_level in [RiskLevel.CRITICAL, RiskLevel.EMERGENCY]:
                logger.critical(f"{emoji} {alert.title}: {alert.message}")
            elif alert.risk_level == RiskLevel.HIGH:
                logger.error(f"{emoji} {alert.title}: {alert.message}")
            elif alert.risk_level == RiskLevel.MEDIUM:
                logger.warning(f"{emoji} {alert.title}: {alert.message}")
            else:
                logger.info(f"{emoji} {alert.title}: {alert.message}")
            
            logger.info(f"   當前值: {alert.current_value:.4f}")
            logger.info(f"   閾值: {alert.threshold_value:.4f}")
            if alert.affected_pairs:
                logger.info(f"   影響交易對: {', '.join(alert.affected_pairs)}")
            if alert.affected_strategies:
                logger.info(f"   影響策略: {', '.join(alert.affected_strategies)}")
                
        except Exception as e:
            logger.error(f"❌ 記錄警報日誌失敗: {e}")
    
    async def _check_metric_alerts(self, metric: RiskMetric):
        """檢查指標警報"""
        try:
            metric_name = metric.metric_name
            current_value = metric.current_value
            threshold = metric.threshold_value
            risk_level = metric.risk_level
            
            # 根據指標類型和風險等級決定是否觸發警報
            should_alert = False
            alert_type = None
            title = ""
            message = ""
            
            if metric_name == "exposure_utilization":
                if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EMERGENCY]:
                    should_alert = True
                    alert_type = AlertType.EXPOSURE_LIMIT
                    title = "敞口利用率警報"
                    message = f"敞口利用率達到 {current_value:.1%}，超過安全閾值"
            
            elif metric_name == "concentration_ratio":
                if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EMERGENCY]:
                    should_alert = True
                    alert_type = AlertType.CONCENTRATION_RISK
                    title = "集中度風險警報"
                    message = f"投資組合集中度達到 {current_value:.1%}，存在集中度風險"
            
            elif metric_name in ["daily_var_95", "daily_var_99"]:
                if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EMERGENCY]:
                    should_alert = True
                    alert_type = AlertType.VAR_EXCEEDED
                    title = "VaR超限警報"
                    message = f"{metric_name} 達到 {current_value:,.0f} TWD，超過風險限制"
            
            elif metric_name == "portfolio_correlation":
                if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EMERGENCY]:
                    should_alert = True
                    alert_type = AlertType.CORRELATION_HIGH
                    title = "相關性過高警報"
                    message = f"投資組合相關性達到 {current_value:.1%}，分散化效果降低"
            
            # 觸發警報
            if should_alert and alert_type:
                await self.create_alert(
                    alert_type=alert_type,
                    risk_level=risk_level,
                    title=title,
                    message=message,
                    current_value=current_value,
                    threshold_value=threshold
                )
            
        except Exception as e:
            logger.error(f"❌ 檢查指標警報失敗: {e}")
    
    async def _handle_auto_response(self, alert: RiskAlert):
        """處理自動響應"""
        try:
            if not self.config.enable_auto_response:
                return
            
            # 根據警報類型和風險等級決定自動響應
            if alert.risk_level == RiskLevel.EMERGENCY and self.config.emergency_auto_action:
                logger.critical("🚨 緊急風險警報，執行自動響應")
                
                # 這裡可以實現自動響應邏輯
                # 例如：自動減倉、停止新交易等
                
                # 記錄自動響應
                logger.critical(f"🤖 自動響應已執行: {alert.alert_type.value}")
            
            elif alert.risk_level == RiskLevel.CRITICAL:
                logger.error("🔴 危險風險警報，建議人工干預")
                
                # 可以發送通知、記錄等
                
            elif alert.risk_level == RiskLevel.HIGH:
                logger.warning("🟠 高風險警報，密切監控")
            
        except Exception as e:
            logger.error(f"❌ 處理自動響應失敗: {e}")
    
    async def _risk_monitoring_loop(self):
        """風險監控循環"""
        while self.is_monitoring:
            try:
                start_time = datetime.now()
                
                # 從外部系統獲取風險數據
                if self.global_risk_manager:
                    await self._update_global_risk_metrics()
                
                if self.position_manager:
                    await self._update_position_risk_metrics()
                
                # 更新監控統計
                self.monitoring_stats['monitoring_uptime'] += self.config.monitoring_interval
                self.last_monitoring_time = datetime.now()
                
                # 等待下次監控
                elapsed = (datetime.now() - start_time).total_seconds()
                sleep_time = max(0, self.config.monitoring_interval - elapsed)
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"❌ 風險監控循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _alert_management_loop(self):
        """警報管理循環"""
        while self.is_monitoring:
            try:
                # 檢查警報狀態
                await self._check_alert_resolution()
                
                # 清理過期警報
                await self._cleanup_expired_alerts()
                
                # 等待下次檢查
                await asyncio.sleep(self.config.alert_check_interval)
                
            except Exception as e:
                logger.error(f"❌ 警報管理循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _metric_calculation_loop(self):
        """指標計算循環"""
        while self.is_monitoring:
            try:
                # 計算衍生指標
                await self._calculate_derived_metrics()
                
                # 等待下次計算
                await asyncio.sleep(30.0)  # 每30秒計算一次
                
            except Exception as e:
                logger.error(f"❌ 指標計算循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _escalation_management_loop(self):
        """升級管理循環"""
        while self.is_monitoring:
            try:
                # 檢查需要升級的警報
                await self._check_alert_escalation()
                
                # 等待下次檢查
                await asyncio.sleep(60.0)  # 每分鐘檢查一次
                
            except Exception as e:
                logger.error(f"❌ 升級管理循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _update_global_risk_metrics(self):
        """更新全局風險指標"""
        try:
            if not self.global_risk_manager:
                return
            
            # 獲取全局風險狀態
            risk_status = self.global_risk_manager.get_global_risk_status()
            
            if 'metrics' in risk_status:
                metrics = risk_status['metrics']
                
                # 更新各項風險指標
                await self.update_risk_metric(
                    "exposure_utilization",
                    metrics.get('exposure_utilization', 0),
                    1.0
                )
                
                await self.update_risk_metric(
                    "concentration_ratio",
                    metrics.get('concentration_ratio', 0),
                    self.config.concentration_warning_threshold
                )
                
                await self.update_risk_metric(
                    "daily_var_95",
                    metrics.get('daily_var_95', 0),
                    50000  # 假設的VaR限制
                )
                
                await self.update_risk_metric(
                    "portfolio_correlation",
                    metrics.get('portfolio_correlation', 0),
                    self.config.correlation_warning_threshold
                )
                
                await self.update_risk_metric(
                    "diversification_ratio",
                    metrics.get('diversification_ratio', 1.0),
                    1.5  # 期望的分散化比率
                )
            
        except Exception as e:
            logger.error(f"❌ 更新全局風險指標失敗: {e}")
    
    async def _update_position_risk_metrics(self):
        """更新倉位風險指標"""
        try:
            if not self.position_manager:
                return
            
            # 獲取倉位狀態
            position_status = self.position_manager.get_position_status()
            
            if 'capital' in position_status:
                capital = position_status['capital']
                
                # 更新資金利用率
                await self.update_risk_metric(
                    "capital_utilization",
                    capital.get('utilization_rate', 0),
                    0.8  # 80%利用率警告
                )
            
            if 'performance' in position_status:
                performance = position_status['performance']
                
                # 更新未實現盈虧風險
                total_pnl = performance.get('total_unrealized_pnl', 0)
                if total_pnl < 0:  # 只關注虧損
                    await self.update_risk_metric(
                        "unrealized_loss",
                        abs(total_pnl),
                        50000  # 50,000 TWD虧損警告
                    )
            
        except Exception as e:
            logger.error(f"❌ 更新倉位風險指標失敗: {e}")
    
    async def _calculate_derived_metrics(self):
        """計算衍生指標"""
        try:
            # 計算風險趨勢指標
            if len(self.risk_metrics) >= 2:
                high_risk_count = sum(1 for metric in self.risk_metrics.values() 
                                    if metric.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL, RiskLevel.EMERGENCY])
                
                total_metrics = len(self.risk_metrics)
                risk_ratio = high_risk_count / total_metrics if total_metrics > 0 else 0
                
                await self.update_risk_metric(
                    "overall_risk_ratio",
                    risk_ratio,
                    0.3  # 30%的指標處於高風險狀態時警告
                )
            
        except Exception as e:
            logger.error(f"❌ 計算衍生指標失敗: {e}")
    
    async def _check_alert_resolution(self):
        """檢查警報解決"""
        try:
            alerts_to_resolve = []
            
            for alert_id, alert in self.active_alerts.items():
                # 檢查對應的風險指標是否已經改善
                metric_name = self._get_metric_name_for_alert(alert.alert_type)
                
                if metric_name in self.risk_metrics:
                    metric = self.risk_metrics[metric_name]
                    
                    # 如果風險等級降低到中等以下，自動解決警報
                    if metric.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]:
                        alerts_to_resolve.append(alert_id)
            
            # 解決警報
            for alert_id in alerts_to_resolve:
                await self.resolve_alert(alert_id, "auto_resolution")
                self.monitoring_stats['auto_resolved_alerts'] += 1
            
        except Exception as e:
            logger.error(f"❌ 檢查警報解決失敗: {e}")
    
    async def _cleanup_expired_alerts(self):
        """清理過期警報"""
        try:
            current_time = datetime.now()
            expired_cooldowns = []
            
            # 清理過期的冷卻期
            for alert_key, cooldown_time in self.alert_cooldowns.items():
                if (current_time - cooldown_time).total_seconds() > self.config.alert_cooldown_period:
                    expired_cooldowns.append(alert_key)
            
            for alert_key in expired_cooldowns:
                del self.alert_cooldowns[alert_key]
            
        except Exception as e:
            logger.error(f"❌ 清理過期警報失敗: {e}")
    
    async def _check_alert_escalation(self):
        """檢查警報升級"""
        try:
            current_time = datetime.now()
            
            for alert_id, alert in self.active_alerts.items():
                # 檢查是否需要升級
                if (alert.status == AlertStatus.ACTIVE and 
                    alert.escalation_count < self.config.max_escalation_level):
                    
                    time_since_created = (current_time - alert.created_at).total_seconds()
                    
                    if time_since_created > self.config.auto_escalation_time:
                        # 升級警報
                        alert.escalation_count += 1
                        alert.status = AlertStatus.ESCALATED
                        
                        self.monitoring_stats['escalated_alerts'] += 1
                        
                        logger.warning(f"⬆️ 警報已升級: {alert_id} (等級 {alert.escalation_count})")
            
        except Exception as e:
            logger.error(f"❌ 檢查警報升級失敗: {e}")
    
    def _get_metric_name_for_alert(self, alert_type: AlertType) -> str:
        """獲取警報類型對應的指標名稱"""
        mapping = {
            AlertType.EXPOSURE_LIMIT: "exposure_utilization",
            AlertType.CONCENTRATION_RISK: "concentration_ratio",
            AlertType.VAR_EXCEEDED: "daily_var_95",
            AlertType.CORRELATION_HIGH: "portfolio_correlation",
            AlertType.DRAWDOWN_LIMIT: "unrealized_loss"
        }
        return mapping.get(alert_type, "")
    
    # 公共接口方法
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """獲取監控狀態"""
        try:
            return {
                'monitoring_info': {
                    'is_monitoring': self.is_monitoring,
                    'last_monitoring_time': self.last_monitoring_time.isoformat(),
                    'monitoring_uptime': self.monitoring_stats['monitoring_uptime'],
                    'config': {
                        'monitoring_interval': self.config.monitoring_interval,
                        'alert_check_interval': self.config.alert_check_interval,
                        'enable_auto_response': self.config.enable_auto_response
                    }
                },
                'risk_metrics': {
                    'total_metrics': len(self.risk_metrics),
                    'metrics_by_level': {
                        level.value: sum(1 for m in self.risk_metrics.values() if m.risk_level == level)
                        for level in RiskLevel
                    },
                    'current_metrics': {
                        name: {
                            'value': metric.current_value,
                            'threshold': metric.threshold_value,
                            'risk_level': metric.risk_level.value,
                            'trend': metric.trend
                        }
                        for name, metric in self.risk_metrics.items()
                    }
                },
                'alerts': {
                    'active_alerts_count': len(self.active_alerts),
                    'total_alerts_generated': self.monitoring_stats['total_alerts_generated'],
                    'alerts_by_type': self.monitoring_stats['alerts_by_type'],
                    'alerts_by_level': self.monitoring_stats['alerts_by_level'],
                    'escalated_alerts': self.monitoring_stats['escalated_alerts'],
                    'auto_resolved_alerts': self.monitoring_stats['auto_resolved_alerts'],
                    'active_alerts': [
                        {
                            'alert_id': alert.alert_id,
                            'type': alert.alert_type.value,
                            'level': alert.risk_level.value,
                            'title': alert.title,
                            'status': alert.status.value,
                            'created_at': alert.created_at.isoformat(),
                            'escalation_count': alert.escalation_count
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
            # 計算整體風險等級
            if not self.risk_metrics:
                overall_risk = RiskLevel.LOW
            else:
                risk_scores = {
                    RiskLevel.LOW: 1,
                    RiskLevel.MEDIUM: 2,
                    RiskLevel.HIGH: 3,
                    RiskLevel.CRITICAL: 4,
                    RiskLevel.EMERGENCY: 5
                }
                
                avg_score = sum(risk_scores[m.risk_level] for m in self.risk_metrics.values()) / len(self.risk_metrics)
                
                if avg_score >= 4.5:
                    overall_risk = RiskLevel.EMERGENCY
                elif avg_score >= 3.5:
                    overall_risk = RiskLevel.CRITICAL
                elif avg_score >= 2.5:
                    overall_risk = RiskLevel.HIGH
                elif avg_score >= 1.5:
                    overall_risk = RiskLevel.MEDIUM
                else:
                    overall_risk = RiskLevel.LOW
            
            # 獲取最高風險指標
            highest_risk_metric = None
            if self.risk_metrics:
                highest_risk_metric = max(self.risk_metrics.values(), 
                                        key=lambda m: risk_scores[m.risk_level])
            
            return {
                'overall_risk_level': overall_risk.value,
                'total_metrics': len(self.risk_metrics),
                'active_alerts': len(self.active_alerts),
                'highest_risk_metric': {
                    'name': highest_risk_metric.metric_name,
                    'level': highest_risk_metric.risk_level.value,
                    'value': highest_risk_metric.current_value,
                    'trend': highest_risk_metric.trend
                } if highest_risk_metric else None,
                'recent_alerts': len([a for a in self.active_alerts.values() 
                                    if (datetime.now() - a.created_at).total_seconds() < 3600]),
                'monitoring_health': 'healthy' if self.is_monitoring else 'stopped'
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取風險摘要失敗: {e}")
            return {}

# 使用示例
async def main():
    """測試風險監控和預警系統"""
    try:
        # 創建配置
        config = RiskMonitoringConfig(
            monitoring_interval=2.0,
            alert_check_interval=5.0,
            enable_auto_response=True
        )
        
        # 創建監控系統
        monitor = RiskMonitoringSystem(config)
        
        # 添加回調函數
        async def alert_callback(alert):
            print(f"🚨 收到警報: {alert.title}")
        
        async def metric_callback(metric):
            print(f"📊 指標更新: {metric.metric_name} = {metric.current_value:.4f}")
        
        monitor.add_alert_callback(alert_callback)
        monitor.add_metric_callback(metric_callback)
        
        # 啟動監控（在後台運行）
        monitoring_task = asyncio.create_task(monitor.start_monitoring())
        
        # 模擬風險指標更新
        await asyncio.sleep(1)
        
        # 正常風險
        await monitor.update_risk_metric("exposure_utilization", 0.5, 1.0)
        await monitor.update_risk_metric("concentration_ratio", 0.2, 0.3)
        
        await asyncio.sleep(3)
        
        # 高風險
        await monitor.update_risk_metric("exposure_utilization", 0.85, 1.0)
        await monitor.update_risk_metric("daily_var_95", 45000, 50000)
        
        await asyncio.sleep(3)
        
        # 危險風險
        await monitor.update_risk_metric("concentration_ratio", 0.6, 0.3)
        
        await asyncio.sleep(5)
        
        # 獲取監控狀態
        status = monitor.get_monitoring_status()
        summary = monitor.get_risk_summary()
        
        print("\n📊 監控狀態:")
        print(f"活躍警報: {status['alerts']['active_alerts_count']}")
        print(f"總指標數: {status['risk_metrics']['total_metrics']}")
        print(f"整體風險等級: {summary['overall_risk_level']}")
        
        # 停止監控
        await monitor.stop_monitoring()
        monitoring_task.cancel()
        
        print("✅ 風險監控和預警系統測試完成")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    asyncio.run(main())