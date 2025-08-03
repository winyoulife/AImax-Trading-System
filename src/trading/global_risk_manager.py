#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局風險管理器 - 統一管理所有交易策略的風險控制
提供多交易對風險敞口計算、相關性分析和全局風險限額控制
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import math
import numpy as np

logger = logging.getLogger(__name__)

class RiskCategory(Enum):
    """風險類別"""
    MARKET_RISK = "market_risk"           # 市場風險
    CREDIT_RISK = "credit_risk"           # 信用風險
    LIQUIDITY_RISK = "liquidity_risk"     # 流動性風險
    OPERATIONAL_RISK = "operational_risk" # 操作風險
    CONCENTRATION_RISK = "concentration_risk" # 集中度風險

class AlertLevel(Enum):
    """警報等級"""
    INFO = "info"         # 信息
    WARNING = "warning"   # 警告
    CRITICAL = "critical" # 危險
    EMERGENCY = "emergency" # 緊急

@dataclass
class RiskExposure:
    """風險敞口"""
    pair: str
    strategy: str
    exposure_amount: float
    risk_weight: float
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class GlobalRiskMetrics:
    """全局風險指標"""
    # 敞口指標
    total_exposure: float = 0.0
    max_exposure_limit: float = 0.0
    exposure_utilization: float = 0.0
    
    # 集中度指標
    max_single_pair_exposure: float = 0.0
    max_single_strategy_exposure: float = 0.0
    concentration_ratio: float = 0.0
    
    # 相關性指標
    portfolio_correlation: float = 0.0
    diversification_ratio: float = 0.0
    
    # VaR指標
    daily_var_95: float = 0.0
    daily_var_99: float = 0.0
    expected_shortfall: float = 0.0
    
    # 時間戳
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class GlobalRiskConfig:
    """全局風險配置"""
    # 敞口限制
    max_total_exposure: float = 1000000     # 最大總敞口
    max_single_pair_exposure: float = 200000 # 單一交易對最大敞口
    max_single_strategy_exposure: float = 300000 # 單一策略最大敞口
    
    # 集中度限制
    max_concentration_ratio: float = 0.4    # 最大集中度比例
    max_correlation_threshold: float = 0.8  # 最大相關性閾值
    
    # VaR限制
    max_daily_var_95: float = 50000        # 95% VaR限制
    max_daily_var_99: float = 80000        # 99% VaR限制
    
    # 監控設置
    risk_check_interval: float = 5.0       # 風險檢查間隔(秒)
    correlation_update_interval: float = 60.0 # 相關性更新間隔(秒)
    
    # 警報閾值
    alert_thresholds: Dict[AlertLevel, float] = field(default_factory=lambda: {
        AlertLevel.INFO: 0.7,
        AlertLevel.WARNING: 0.8,
        AlertLevel.CRITICAL: 0.9,
        AlertLevel.EMERGENCY: 0.95
    })

class GlobalRiskManager:
    """全局風險管理器"""
    
    def __init__(self, config: GlobalRiskConfig):
        self.config = config
        
        # 風險敞口追蹤
        self.risk_exposures: Dict[str, RiskExposure] = {}  # {exposure_id: RiskExposure}
        self.strategy_exposures: Dict[str, float] = {}     # {strategy: total_exposure}
        self.pair_exposures: Dict[str, float] = {}         # {pair: total_exposure}
        
        # 風險指標
        self.current_metrics = GlobalRiskMetrics()
        self.metrics_history: List[GlobalRiskMetrics] = []
        
        # 相關性矩陣
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        self.price_history: Dict[str, List[float]] = {}
        
        # 風險限制狀態
        self.risk_violations: List[Dict[str, Any]] = []
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        
        # 統計數據
        self.risk_stats = {
            'total_exposures_tracked': 0,
            'risk_violations_count': 0,
            'alerts_triggered': 0,
            'max_exposure_reached': 0.0,
            'avg_correlation': 0.0,
            'diversification_score': 0.0
        }
        
        # 監控狀態
        self.is_monitoring = False
        self.last_risk_check = datetime.now()
        
        logger.info("🌐 全局風險管理器初始化完成")
        logger.info(f"   最大總敞口: {config.max_total_exposure:,.0f} TWD")
        logger.info(f"   最大單一交易對敞口: {config.max_single_pair_exposure:,.0f} TWD")
        logger.info(f"   最大單一策略敞口: {config.max_single_strategy_exposure:,.0f} TWD")
        logger.info(f"   風險檢查間隔: {config.risk_check_interval} 秒")
    
    async def start_monitoring(self):
        """啟動全局風險監控"""
        if self.is_monitoring:
            logger.warning("⚠️ 全局風險監控已在運行中")
            return
        
        self.is_monitoring = True
        logger.info("🚀 啟動全局風險監控")
        
        try:
            # 啟動監控任務
            monitoring_tasks = [
                self._risk_monitoring_loop(),
                self._correlation_update_loop(),
                self._metrics_calculation_loop()
            ]
            
            await asyncio.gather(*monitoring_tasks)
            
        except Exception as e:
            logger.error(f"❌ 全局風險監控啟動失敗: {e}")
            self.is_monitoring = False
            raise
    
    async def stop_monitoring(self):
        """停止全局風險監控"""
        logger.info("🛑 停止全局風險監控")
        self.is_monitoring = False
        logger.info("✅ 全局風險監控已停止")
    
    async def register_exposure(self, exposure_id: str, pair: str, strategy: str, 
                              amount: float, risk_weight: float = 1.0) -> bool:
        """註冊風險敞口"""
        try:
            # 檢查敞口限制
            if not await self._check_exposure_limits(pair, strategy, amount):
                logger.warning(f"⚠️ 敞口超限，拒絕註冊: {exposure_id}")
                return False
            
            # 創建敞口記錄
            exposure = RiskExposure(
                pair=pair,
                strategy=strategy,
                exposure_amount=amount,
                risk_weight=risk_weight
            )
            
            # 註冊敞口
            self.risk_exposures[exposure_id] = exposure
            
            # 更新策略和交易對敞口
            self.strategy_exposures[strategy] = self.strategy_exposures.get(strategy, 0) + amount
            self.pair_exposures[pair] = self.pair_exposures.get(pair, 0) + amount
            
            # 更新統計
            self.risk_stats['total_exposures_tracked'] += 1
            
            logger.info(f"📝 註冊風險敞口: {exposure_id}")
            logger.info(f"   交易對: {pair}")
            logger.info(f"   策略: {strategy}")
            logger.info(f"   金額: {amount:,.2f} TWD")
            logger.info(f"   風險權重: {risk_weight:.2f}")
            
            # 立即更新風險指標
            await self._update_risk_metrics()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 註冊風險敞口失敗: {e}")
            return False 
   
    async def update_exposure(self, exposure_id: str, new_amount: float) -> bool:
        """更新風險敞口"""
        try:
            if exposure_id not in self.risk_exposures:
                logger.warning(f"⚠️ 敞口不存在: {exposure_id}")
                return False
            
            exposure = self.risk_exposures[exposure_id]
            old_amount = exposure.exposure_amount
            
            # 更新敞口金額
            exposure.exposure_amount = new_amount
            exposure.last_update = datetime.now()
            
            # 更新策略和交易對敞口
            self.strategy_exposures[exposure.strategy] += (new_amount - old_amount)
            self.pair_exposures[exposure.pair] += (new_amount - old_amount)
            
            # 確保不為負數
            self.strategy_exposures[exposure.strategy] = max(0, self.strategy_exposures[exposure.strategy])
            self.pair_exposures[exposure.pair] = max(0, self.pair_exposures[exposure.pair])
            
            logger.debug(f"🔄 更新風險敞口: {exposure_id} ({old_amount:,.2f} → {new_amount:,.2f})")
            
            # 更新風險指標
            await self._update_risk_metrics()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新風險敞口失敗: {e}")
            return False
    
    async def remove_exposure(self, exposure_id: str) -> bool:
        """移除風險敞口"""
        try:
            if exposure_id not in self.risk_exposures:
                logger.warning(f"⚠️ 敞口不存在: {exposure_id}")
                return False
            
            exposure = self.risk_exposures[exposure_id]
            
            # 更新策略和交易對敞口
            self.strategy_exposures[exposure.strategy] -= exposure.exposure_amount
            self.pair_exposures[exposure.pair] -= exposure.exposure_amount
            
            # 確保不為負數
            self.strategy_exposures[exposure.strategy] = max(0, self.strategy_exposures[exposure.strategy])
            self.pair_exposures[exposure.pair] = max(0, self.pair_exposures[exposure.pair])
            
            # 移除敞口記錄
            del self.risk_exposures[exposure_id]
            
            logger.info(f"🗑️ 移除風險敞口: {exposure_id}")
            
            # 更新風險指標
            await self._update_risk_metrics()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 移除風險敞口失敗: {e}")
            return False
    
    async def _check_exposure_limits(self, pair: str, strategy: str, amount: float) -> bool:
        """檢查敞口限制"""
        try:
            # 檢查總敞口限制
            current_total = sum(exp.exposure_amount for exp in self.risk_exposures.values())
            if current_total + amount > self.config.max_total_exposure:
                logger.warning(f"⚠️ 總敞口超限: {current_total + amount:,.2f} > {self.config.max_total_exposure:,.2f}")
                return False
            
            # 檢查單一交易對敞口限制
            current_pair_exposure = self.pair_exposures.get(pair, 0)
            if current_pair_exposure + amount > self.config.max_single_pair_exposure:
                logger.warning(f"⚠️ 交易對敞口超限 {pair}: {current_pair_exposure + amount:,.2f} > {self.config.max_single_pair_exposure:,.2f}")
                return False
            
            # 檢查單一策略敞口限制
            current_strategy_exposure = self.strategy_exposures.get(strategy, 0)
            if current_strategy_exposure + amount > self.config.max_single_strategy_exposure:
                logger.warning(f"⚠️ 策略敞口超限 {strategy}: {current_strategy_exposure + amount:,.2f} > {self.config.max_single_strategy_exposure:,.2f}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 檢查敞口限制失敗: {e}")
            return False
    
    async def _update_risk_metrics(self):
        """更新風險指標"""
        try:
            metrics = GlobalRiskMetrics()
            
            # 計算總敞口
            metrics.total_exposure = sum(exp.exposure_amount for exp in self.risk_exposures.values())
            metrics.max_exposure_limit = self.config.max_total_exposure
            metrics.exposure_utilization = metrics.total_exposure / metrics.max_exposure_limit if metrics.max_exposure_limit > 0 else 0
            
            # 計算集中度指標
            if self.pair_exposures:
                metrics.max_single_pair_exposure = max(self.pair_exposures.values())
            if self.strategy_exposures:
                metrics.max_single_strategy_exposure = max(self.strategy_exposures.values())
            
            metrics.concentration_ratio = metrics.max_single_pair_exposure / metrics.total_exposure if metrics.total_exposure > 0 else 0
            
            # 計算相關性指標
            metrics.portfolio_correlation = await self._calculate_portfolio_correlation()
            metrics.diversification_ratio = await self._calculate_diversification_ratio()
            
            # 計算VaR指標
            metrics.daily_var_95, metrics.daily_var_99 = await self._calculate_var()
            metrics.expected_shortfall = await self._calculate_expected_shortfall()
            
            # 更新當前指標
            self.current_metrics = metrics
            
            # 添加到歷史記錄
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-500:]
            
            # 檢查風險警報
            await self._check_risk_alerts()
            
        except Exception as e:
            logger.error(f"❌ 更新風險指標失敗: {e}")
    
    async def _calculate_portfolio_correlation(self) -> float:
        """計算投資組合相關性"""
        try:
            if len(self.pair_exposures) < 2:
                return 0.0
            
            pairs = list(self.pair_exposures.keys())
            correlations = []
            
            for i in range(len(pairs)):
                for j in range(i + 1, len(pairs)):
                    pair_a, pair_b = pairs[i], pairs[j]
                    correlation = self.correlation_matrix.get(pair_a, {}).get(pair_b, 0.0)
                    
                    # 根據敞口加權
                    weight_a = self.pair_exposures[pair_a] / self.current_metrics.total_exposure
                    weight_b = self.pair_exposures[pair_b] / self.current_metrics.total_exposure
                    weighted_correlation = correlation * weight_a * weight_b
                    
                    correlations.append(weighted_correlation)
            
            return sum(correlations) / len(correlations) if correlations else 0.0
            
        except Exception as e:
            logger.error(f"❌ 計算投資組合相關性失敗: {e}")
            return 0.0
    
    async def _calculate_diversification_ratio(self) -> float:
        """計算分散化比率"""
        try:
            if not self.pair_exposures or len(self.pair_exposures) < 2:
                return 1.0  # 單一資產，無分散化
            
            # 計算權重
            total_exposure = sum(self.pair_exposures.values())
            weights = {pair: exposure / total_exposure for pair, exposure in self.pair_exposures.items()}
            
            # 計算加權平均波動率
            weighted_volatility = 0.0
            for pair, weight in weights.items():
                # 模擬波動率數據
                volatility = self._get_pair_volatility(pair)
                weighted_volatility += weight * volatility
            
            # 計算投資組合波動率（考慮相關性）
            portfolio_variance = 0.0
            pairs = list(weights.keys())
            
            for i, pair_a in enumerate(pairs):
                for j, pair_b in enumerate(pairs):
                    weight_a = weights[pair_a]
                    weight_b = weights[pair_b]
                    vol_a = self._get_pair_volatility(pair_a)
                    vol_b = self._get_pair_volatility(pair_b)
                    
                    if i == j:
                        correlation = 1.0
                    else:
                        correlation = self.correlation_matrix.get(pair_a, {}).get(pair_b, 0.0)
                    
                    portfolio_variance += weight_a * weight_b * vol_a * vol_b * correlation
            
            portfolio_volatility = math.sqrt(portfolio_variance)
            
            # 分散化比率 = 加權平均波動率 / 投資組合波動率
            diversification_ratio = weighted_volatility / portfolio_volatility if portfolio_volatility > 0 else 1.0
            
            return min(diversification_ratio, 2.0)  # 限制最大值
            
        except Exception as e:
            logger.error(f"❌ 計算分散化比率失敗: {e}")
            return 1.0
    
    def _get_pair_volatility(self, pair: str) -> float:
        """獲取交易對波動率"""
        try:
            # 模擬波動率數據
            volatility_map = {
                "BTCTWD": 0.04,   # 4%日波動率
                "ETHTWD": 0.05,   # 5%日波動率
                "USDTTWD": 0.001, # 0.1%日波動率
                "LTCTWD": 0.06,   # 6%日波動率
                "BCHTWD": 0.07    # 7%日波動率
            }
            return volatility_map.get(pair, 0.03)  # 默認3%
            
        except Exception as e:
            logger.error(f"❌ 獲取交易對波動率失敗: {e}")
            return 0.03
    
    async def _calculate_var(self) -> Tuple[float, float]:
        """計算VaR (Value at Risk)"""
        try:
            if not self.pair_exposures:
                return 0.0, 0.0
            
            # 簡化的VaR計算
            total_exposure = sum(self.pair_exposures.values())
            
            # 計算投資組合日波動率
            portfolio_volatility = 0.0
            total_weight = 0.0
            
            for pair, exposure in self.pair_exposures.items():
                weight = exposure / total_exposure
                volatility = self._get_pair_volatility(pair)
                portfolio_volatility += weight * volatility
                total_weight += weight
            
            if total_weight > 0:
                portfolio_volatility /= total_weight
            
            # VaR計算 (假設正態分布)
            # 95% VaR = 1.645 * 波動率 * 敞口
            # 99% VaR = 2.326 * 波動率 * 敞口
            var_95 = 1.645 * portfolio_volatility * total_exposure
            var_99 = 2.326 * portfolio_volatility * total_exposure
            
            return var_95, var_99
            
        except Exception as e:
            logger.error(f"❌ 計算VaR失敗: {e}")
            return 0.0, 0.0
    
    async def _calculate_expected_shortfall(self) -> float:
        """計算預期損失 (Expected Shortfall)"""
        try:
            if not self.pair_exposures:
                return 0.0
            
            # 簡化的ES計算
            _, var_99 = await self._calculate_var()
            
            # ES通常比VaR高20-30%
            expected_shortfall = var_99 * 1.25
            
            return expected_shortfall
            
        except Exception as e:
            logger.error(f"❌ 計算預期損失失敗: {e}")
            return 0.0
    
    async def _check_risk_alerts(self):
        """檢查風險警報"""
        try:
            metrics = self.current_metrics
            alerts_to_trigger = []
            
            # 檢查敞口利用率
            if metrics.exposure_utilization > 0:
                for level, threshold in self.config.alert_thresholds.items():
                    if metrics.exposure_utilization >= threshold:
                        alert_id = f"exposure_utilization_{level.value}"
                        if alert_id not in self.active_alerts:
                            alerts_to_trigger.append({
                                'alert_id': alert_id,
                                'level': level,
                                'type': 'exposure_utilization',
                                'value': metrics.exposure_utilization,
                                'threshold': threshold,
                                'message': f"敞口利用率達到 {metrics.exposure_utilization:.1%}"
                            })
            
            # 檢查集中度風險
            if metrics.concentration_ratio > self.config.max_concentration_ratio:
                alert_id = "concentration_risk"
                if alert_id not in self.active_alerts:
                    alerts_to_trigger.append({
                        'alert_id': alert_id,
                        'level': AlertLevel.WARNING,
                        'type': 'concentration_risk',
                        'value': metrics.concentration_ratio,
                        'threshold': self.config.max_concentration_ratio,
                        'message': f"集中度風險過高: {metrics.concentration_ratio:.1%}"
                    })
            
            # 檢查VaR限制
            if metrics.daily_var_95 > self.config.max_daily_var_95:
                alert_id = "var_95_exceeded"
                if alert_id not in self.active_alerts:
                    alerts_to_trigger.append({
                        'alert_id': alert_id,
                        'level': AlertLevel.CRITICAL,
                        'type': 'var_risk',
                        'value': metrics.daily_var_95,
                        'threshold': self.config.max_daily_var_95,
                        'message': f"95% VaR超限: {metrics.daily_var_95:,.0f} TWD"
                    })
            
            # 觸發新警報
            for alert in alerts_to_trigger:
                await self._trigger_alert(alert)
            
        except Exception as e:
            logger.error(f"❌ 檢查風險警報失敗: {e}")
    
    async def _trigger_alert(self, alert: Dict[str, Any]):
        """觸發風險警報"""
        try:
            alert_id = alert['alert_id']
            level = alert['level']
            message = alert['message']
            
            # 添加時間戳
            alert['timestamp'] = datetime.now()
            
            # 記錄活躍警報
            self.active_alerts[alert_id] = alert
            
            # 記錄統計
            self.risk_stats['alerts_triggered'] += 1
            
            # 根據警報等級記錄日誌
            if level == AlertLevel.INFO:
                logger.info(f"ℹ️ 風險警報: {message}")
            elif level == AlertLevel.WARNING:
                logger.warning(f"⚠️ 風險警報: {message}")
            elif level == AlertLevel.CRITICAL:
                logger.error(f"🚨 風險警報: {message}")
            elif level == AlertLevel.EMERGENCY:
                logger.critical(f"🚨🚨 緊急風險警報: {message}")
                # 緊急情況下可能需要自動處理
                await self._handle_emergency_alert(alert)
            
        except Exception as e:
            logger.error(f"❌ 觸發風險警報失敗: {e}")
    
    async def _handle_emergency_alert(self, alert: Dict[str, Any]):
        """處理緊急風險警報"""
        try:
            logger.critical("🚨 處理緊急風險警報，考慮自動風險控制措施")
            
            # 這裡可以實現自動風險控制措施
            # 例如：自動減倉、停止新交易等
            
            # 記錄風險違規
            violation = {
                'timestamp': datetime.now(),
                'alert': alert,
                'action_taken': 'emergency_alert_logged',
                'severity': 'emergency'
            }
            
            self.risk_violations.append(violation)
            self.risk_stats['risk_violations_count'] += 1
            
        except Exception as e:
            logger.error(f"❌ 處理緊急風險警報失敗: {e}")
    
    async def _risk_monitoring_loop(self):
        """風險監控循環"""
        while self.is_monitoring:
            try:
                # 更新風險指標
                await self._update_risk_metrics()
                
                # 更新統計
                self._update_risk_stats()
                
                # 清理過期警報
                await self._cleanup_expired_alerts()
                
                self.last_risk_check = datetime.now()
                
                # 等待下次檢查
                await asyncio.sleep(self.config.risk_check_interval)
                
            except Exception as e:
                logger.error(f"❌ 風險監控循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _correlation_update_loop(self):
        """相關性更新循環"""
        while self.is_monitoring:
            try:
                # 更新相關性矩陣
                await self._update_correlation_matrix()
                
                # 等待下次更新
                await asyncio.sleep(self.config.correlation_update_interval)
                
            except Exception as e:
                logger.error(f"❌ 相關性更新循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _metrics_calculation_loop(self):
        """指標計算循環"""
        while self.is_monitoring:
            try:
                # 定期重新計算所有風險指標
                await self._update_risk_metrics()
                
                # 等待下次計算
                await asyncio.sleep(10.0)  # 每10秒重新計算一次
                
            except Exception as e:
                logger.error(f"❌ 指標計算循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _update_correlation_matrix(self):
        """更新相關性矩陣"""
        try:
            # 模擬相關性矩陣更新
            import random
            
            pairs = list(set(exp.pair for exp in self.risk_exposures.values()))
            
            for pair_a in pairs:
                if pair_a not in self.correlation_matrix:
                    self.correlation_matrix[pair_a] = {}
                
                for pair_b in pairs:
                    if pair_a != pair_b:
                        # 模擬相關性計算
                        if pair_b not in self.correlation_matrix[pair_a]:
                            # 基於交易對類型設置基礎相關性
                            base_correlation = self._get_base_correlation(pair_a, pair_b)
                            # 添加隨機波動
                            correlation = base_correlation + random.uniform(-0.1, 0.1)
                            correlation = max(-1.0, min(1.0, correlation))  # 限制在[-1, 1]
                            
                            self.correlation_matrix[pair_a][pair_b] = correlation
                            
                            # 確保對稱性
                            if pair_b not in self.correlation_matrix:
                                self.correlation_matrix[pair_b] = {}
                            self.correlation_matrix[pair_b][pair_a] = correlation
            
        except Exception as e:
            logger.error(f"❌ 更新相關性矩陣失敗: {e}")
    
    def _get_base_correlation(self, pair_a: str, pair_b: str) -> float:
        """獲取基礎相關性"""
        try:
            # 基於交易對類型的基礎相關性
            crypto_pairs = ["BTCTWD", "ETHTWD", "LTCTWD", "BCHTWD"]
            stable_pairs = ["USDTTWD"]
            
            # 加密貨幣之間通常有較高相關性
            if pair_a in crypto_pairs and pair_b in crypto_pairs:
                if "BTC" in pair_a and "ETH" in pair_b:
                    return 0.7  # BTC和ETH高度相關
                else:
                    return 0.5  # 其他加密貨幣中等相關
            
            # 穩定幣與加密貨幣相關性較低
            elif (pair_a in stable_pairs and pair_b in crypto_pairs) or \
                 (pair_a in crypto_pairs and pair_b in stable_pairs):
                return 0.1
            
            # 穩定幣之間相關性很高
            elif pair_a in stable_pairs and pair_b in stable_pairs:
                return 0.9
            
            return 0.3  # 默認相關性
            
        except Exception as e:
            logger.error(f"❌ 獲取基礎相關性失敗: {e}")
            return 0.3
    
    def _update_risk_stats(self):
        """更新風險統計"""
        try:
            # 更新最大敞口記錄
            current_total = sum(exp.exposure_amount for exp in self.risk_exposures.values())
            self.risk_stats['max_exposure_reached'] = max(
                self.risk_stats['max_exposure_reached'], 
                current_total
            )
            
            # 更新平均相關性
            if self.correlation_matrix:
                correlations = []
                for pair_a in self.correlation_matrix:
                    for pair_b, correlation in self.correlation_matrix[pair_a].items():
                        correlations.append(abs(correlation))
                
                if correlations:
                    self.risk_stats['avg_correlation'] = sum(correlations) / len(correlations)
            
            # 更新分散化分數
            self.risk_stats['diversification_score'] = self.current_metrics.diversification_ratio
            
        except Exception as e:
            logger.error(f"❌ 更新風險統計失敗: {e}")
    
    async def _cleanup_expired_alerts(self):
        """清理過期警報"""
        try:
            current_time = datetime.now()
            expired_alerts = []
            
            for alert_id, alert in self.active_alerts.items():
                # 警報1小時後自動過期
                if (current_time - alert['timestamp']).total_seconds() > 3600:
                    expired_alerts.append(alert_id)
            
            for alert_id in expired_alerts:
                del self.active_alerts[alert_id]
                logger.debug(f"🧹 清理過期警報: {alert_id}")
            
        except Exception as e:
            logger.error(f"❌ 清理過期警報失敗: {e}")
    
    # 公共接口方法
    
    def get_global_risk_status(self) -> Dict[str, Any]:
        """獲取全局風險狀態"""
        try:
            return {
                'metrics': {
                    'total_exposure': self.current_metrics.total_exposure,
                    'max_exposure_limit': self.current_metrics.max_exposure_limit,
                    'exposure_utilization': self.current_metrics.exposure_utilization,
                    'max_single_pair_exposure': self.current_metrics.max_single_pair_exposure,
                    'max_single_strategy_exposure': self.current_metrics.max_single_strategy_exposure,
                    'concentration_ratio': self.current_metrics.concentration_ratio,
                    'portfolio_correlation': self.current_metrics.portfolio_correlation,
                    'diversification_ratio': self.current_metrics.diversification_ratio,
                    'daily_var_95': self.current_metrics.daily_var_95,
                    'daily_var_99': self.current_metrics.daily_var_99,
                    'expected_shortfall': self.current_metrics.expected_shortfall
                },
                'exposures': {
                    'total_exposures': len(self.risk_exposures),
                    'strategy_exposures': self.strategy_exposures.copy(),
                    'pair_exposures': self.pair_exposures.copy()
                },
                'alerts': {
                    'active_alerts_count': len(self.active_alerts),
                    'active_alerts': list(self.active_alerts.values()),
                    'risk_violations_count': len(self.risk_violations)
                },
                'stats': self.risk_stats.copy(),
                'monitoring_status': self.is_monitoring,
                'last_risk_check': self.last_risk_check.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取全局風險狀態失敗: {e}")
            return {'error': str(e)}
    
    def get_exposure_summary(self) -> Dict[str, Any]:
        """獲取敞口摘要"""
        try:
            exposures_by_strategy = {}
            exposures_by_pair = {}
            
            for exposure_id, exposure in self.risk_exposures.items():
                # 按策略分組
                if exposure.strategy not in exposures_by_strategy:
                    exposures_by_strategy[exposure.strategy] = []
                exposures_by_strategy[exposure.strategy].append({
                    'exposure_id': exposure_id,
                    'pair': exposure.pair,
                    'amount': exposure.exposure_amount,
                    'risk_weight': exposure.risk_weight,
                    'last_update': exposure.last_update.isoformat()
                })
                
                # 按交易對分組
                if exposure.pair not in exposures_by_pair:
                    exposures_by_pair[exposure.pair] = []
                exposures_by_pair[exposure.pair].append({
                    'exposure_id': exposure_id,
                    'strategy': exposure.strategy,
                    'amount': exposure.exposure_amount,
                    'risk_weight': exposure.risk_weight,
                    'last_update': exposure.last_update.isoformat()
                })
            
            return {
                'total_exposures': len(self.risk_exposures),
                'total_exposure_amount': sum(exp.exposure_amount for exp in self.risk_exposures.values()),
                'exposures_by_strategy': exposures_by_strategy,
                'exposures_by_pair': exposures_by_pair,
                'strategy_totals': self.strategy_exposures.copy(),
                'pair_totals': self.pair_exposures.copy()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取敞口摘要失敗: {e}")
            return {'error': str(e)}
    
    def get_correlation_matrix(self) -> Dict[str, Dict[str, float]]:
        """獲取相關性矩陣"""
        return self.correlation_matrix.copy()
    
    async def emergency_risk_shutdown(self) -> bool:
        """緊急風險關閉"""
        try:
            logger.critical("🚨 執行緊急風險關閉")
            
            # 清除所有敞口
            exposure_ids = list(self.risk_exposures.keys())
            for exposure_id in exposure_ids:
                await self.remove_exposure(exposure_id)
            
            # 觸發緊急警報
            emergency_alert = {
                'alert_id': 'emergency_shutdown',
                'level': AlertLevel.EMERGENCY,
                'type': 'emergency_action',
                'message': '執行緊急風險關閉',
                'timestamp': datetime.now()
            }
            
            await self._trigger_alert(emergency_alert)
            
            logger.critical("✅ 緊急風險關閉完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 緊急風險關閉失敗: {e}")
            return False


# 創建全局風險管理器實例
def create_global_risk_manager(config: GlobalRiskConfig) -> GlobalRiskManager:
    """創建全局風險管理器實例"""
    return GlobalRiskManager(config)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_global_risk_manager():
        """測試全局風險管理器"""
        print("🧪 測試全局風險管理器...")
        
        # 創建配置
        config = GlobalRiskConfig(
            max_total_exposure=500000,
            max_single_pair_exposure=150000,
            max_single_strategy_exposure=200000
        )
        
        # 創建風險管理器
        manager = create_global_risk_manager(config)
        
        try:
            # 註冊多個敞口
            await manager.register_exposure("exp_001", "BTCTWD", "grid_trading", 100000, 1.0)
            await manager.register_exposure("exp_002", "ETHTWD", "dca_strategy", 80000, 0.8)
            await manager.register_exposure("exp_003", "BTCTWD", "arbitrage", 50000, 1.2)
            
            # 獲取風險狀態
            risk_status = manager.get_global_risk_status()
            print(f"✅ 風險狀態:")
            print(f"   總敞口: {risk_status['metrics']['total_exposure']:,.2f} TWD")
            print(f"   敞口利用率: {risk_status['metrics']['exposure_utilization']:.1%}")
            print(f"   集中度比率: {risk_status['metrics']['concentration_ratio']:.1%}")
            print(f"   分散化比率: {risk_status['metrics']['diversification_ratio']:.2f}")
            print(f"   95% VaR: {risk_status['metrics']['daily_var_95']:,.2f} TWD")
            
            # 獲取敞口摘要
            exposure_summary = manager.get_exposure_summary()
            print(f"\\n📊 敞口摘要:")
            print(f"   總敞口數: {exposure_summary['total_exposures']}")
            print(f"   策略分布: {exposure_summary['strategy_totals']}")
            print(f"   交易對分布: {exposure_summary['pair_totals']}")
            
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
        
        print("🎉 全局風險管理器測試完成！")
    
    # 運行測試
    asyncio.run(test_global_risk_manager())