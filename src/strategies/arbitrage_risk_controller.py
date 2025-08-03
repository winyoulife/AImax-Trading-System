#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
套利風險控制系統 - 專門負責套利交易的風險評估、倉位管理和風險監控
提供多層風險控制機制，確保套利交易的安全性和穩定性
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import math

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """風險等級"""
    LOW = "low"           # 低風險
    MEDIUM = "medium"     # 中等風險
    HIGH = "high"         # 高風險
    CRITICAL = "critical" # 危險風險
    EMERGENCY = "emergency" # 緊急風險

class RiskAction(Enum):
    """風險動作"""
    ALLOW = "allow"           # 允許執行
    LIMIT = "limit"           # 限制執行
    REDUCE = "reduce"         # 減少倉位
    STOP = "stop"             # 停止執行
    EMERGENCY_EXIT = "emergency_exit"  # 緊急退出

class PositionStatus(Enum):
    """倉位狀態"""
    OPEN = "open"         # 開倉
    PARTIAL = "partial"   # 部分成交
    CLOSED = "closed"     # 已平倉
    FAILED = "failed"     # 失敗
    EMERGENCY = "emergency" # 緊急狀態

@dataclass
class RiskMetrics:
    """風險指標"""
    # 基礎風險指標
    position_risk: float = 0.0      # 倉位風險
    market_risk: float = 0.0        # 市場風險
    liquidity_risk: float = 0.0     # 流動性風險
    execution_risk: float = 0.0     # 執行風險
    correlation_risk: float = 0.0   # 相關性風險
    
    # 綜合風險指標
    total_risk_score: float = 0.0   # 總風險分數
    risk_level: RiskLevel = RiskLevel.LOW
    
    # 風險限制
    max_position_size: float = 0.0  # 最大倉位
    max_daily_loss: float = 0.0     # 最大日虧損
    max_drawdown: float = 0.0       # 最大回撤
    
    # 時間戳
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ArbitragePosition:
    """套利倉位"""
    position_id: str
    opportunity_id: str
    execution_id: str
    
    # 倉位信息
    pairs: List[str]
    exchanges: List[str]
    entry_time: datetime
    expected_profit: float
    required_capital: float
    
    # 當前狀態
    status: PositionStatus = PositionStatus.OPEN
    current_value: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    # 風險指標
    risk_metrics: RiskMetrics = field(default_factory=RiskMetrics)
    
    # 止損設置
    stop_loss_price: Optional[float] = None
    stop_loss_percentage: float = 0.05  # 5%止損
    
    # 更新時間
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class RiskControlConfig:
    """風險控制配置"""
    # 全局風險限制
    max_total_exposure: float = 500000      # 最大總敞口
    max_single_position: float = 100000     # 最大單筆倉位
    max_daily_loss: float = 10000          # 最大日虧損
    max_drawdown: float = 0.1              # 最大回撤 10%
    
    # 風險閾值
    risk_thresholds: Dict[RiskLevel, float] = field(default_factory=lambda: {
        RiskLevel.LOW: 0.2,
        RiskLevel.MEDIUM: 0.4,
        RiskLevel.HIGH: 0.6,
        RiskLevel.CRITICAL: 0.8,
        RiskLevel.EMERGENCY: 1.0
    })
    
    # 倉位管理
    position_sizing_method: str = "fixed"   # fixed, percentage, volatility
    base_position_size: float = 50000      # 基礎倉位大小
    max_positions: int = 10                # 最大同時持倉數
    
    # 止損設置
    enable_stop_loss: bool = True
    default_stop_loss: float = 0.05        # 默認5%止損
    trailing_stop: bool = True             # 跟蹤止損
    
    # 監控設置
    monitoring_interval: float = 1.0       # 監控間隔(秒)
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'position_risk': 0.7,
        'daily_loss': 0.8,
        'drawdown': 0.8
    })

class ArbitrageRiskController:
    """套利風險控制系統"""
    
    def __init__(self, config: RiskControlConfig):
        self.config = config
        
        # 倉位管理
        self.active_positions: Dict[str, ArbitragePosition] = {}
        self.position_history: List[ArbitragePosition] = []
        
        # 風險監控
        self.current_exposure: float = 0.0
        self.daily_pnl: float = 0.0
        self.max_drawdown_today: float = 0.0
        self.peak_equity: float = 0.0
        
        # 風險統計
        self.risk_stats = {
            'total_positions': 0,
            'stopped_positions': 0,
            'emergency_exits': 0,
            'avg_risk_score': 0.0,
            'max_risk_score': 0.0,
            'risk_violations': 0,
            'total_loss_prevented': 0.0
        }
        
        # 市場數據
        self.market_data: Dict[str, Dict] = {}
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        
        # 監控狀態
        self.is_monitoring = False
        self.last_risk_check: datetime = datetime.now()
        
        logger.info("🛡️ 套利風險控制系統初始化完成")
        logger.info(f"   最大總敞口: {config.max_total_exposure:,.0f} TWD")
        logger.info(f"   最大單筆倉位: {config.max_single_position:,.0f} TWD")
        logger.info(f"   最大日虧損: {config.max_daily_loss:,.0f} TWD")
        logger.info(f"   止損功能: {'啟用' if config.enable_stop_loss else '禁用'}")
    
    async def start_monitoring(self):
        """啟動風險監控"""
        if self.is_monitoring:
            logger.warning("⚠️ 風險監控已在運行中")
            return
        
        self.is_monitoring = True
        logger.info("🚀 啟動套利風險監控")
        
        try:
            # 啟動監控任務
            monitoring_tasks = [
                self._risk_monitoring_loop(),
                self._position_monitoring_loop(),
                self._market_monitoring_loop()
            ]
            
            await asyncio.gather(*monitoring_tasks)
            
        except Exception as e:
            logger.error(f"❌ 風險監控啟動失敗: {e}")
            self.is_monitoring = False
            raise
    
    async def stop_monitoring(self):
        """停止風險監控"""
        logger.info("🛑 停止套利風險監控")
        self.is_monitoring = False
        
        # 等待所有倉位處理完成
        await self._wait_for_positions_close()
        
        logger.info("✅ 套利風險監控已停止")
    
    async def evaluate_opportunity_risk(self, opportunity: Dict[str, Any]) -> Tuple[RiskLevel, RiskAction, RiskMetrics]:
        """評估套利機會風險"""
        try:
            logger.debug(f"🔍 評估套利機會風險: {opportunity.get('opportunity_id', 'unknown')}")
            
            # 創建風險指標
            risk_metrics = RiskMetrics()
            
            # 1. 倉位風險評估
            risk_metrics.position_risk = await self._calculate_position_risk(opportunity)
            
            # 2. 市場風險評估
            risk_metrics.market_risk = await self._calculate_market_risk(opportunity)
            
            # 3. 流動性風險評估
            risk_metrics.liquidity_risk = await self._calculate_liquidity_risk(opportunity)
            
            # 4. 執行風險評估
            risk_metrics.execution_risk = await self._calculate_execution_risk(opportunity)
            
            # 5. 相關性風險評估
            risk_metrics.correlation_risk = await self._calculate_correlation_risk(opportunity)
            
            # 計算總風險分數
            risk_metrics.total_risk_score = self._calculate_total_risk_score(risk_metrics)
            
            # 確定風險等級
            risk_metrics.risk_level = self._determine_risk_level(risk_metrics.total_risk_score)
            
            # 確定風險動作
            risk_action = self._determine_risk_action(risk_metrics)
            
            logger.debug(f"   風險評估結果:")
            logger.debug(f"      總風險分數: {risk_metrics.total_risk_score:.3f}")
            logger.debug(f"      風險等級: {risk_metrics.risk_level.value}")
            logger.debug(f"      建議動作: {risk_action.value}")
            
            return risk_metrics.risk_level, risk_action, risk_metrics
            
        except Exception as e:
            logger.error(f"❌ 評估套利機會風險失敗: {e}")
            # 默認返回高風險和停止動作
            return RiskLevel.HIGH, RiskAction.STOP, RiskMetrics()
    
    async def _calculate_position_risk(self, opportunity: Dict[str, Any]) -> float:
        """計算倉位風險"""
        try:
            required_capital = opportunity.get('required_capital', 0)
            
            # 檢查單筆倉位限制
            if required_capital > self.config.max_single_position:
                return 1.0  # 超過單筆限制，最高風險
            
            # 檢查總敞口限制
            if self.current_exposure + required_capital > self.config.max_total_exposure:
                return 0.9  # 接近總敞口限制
            
            # 計算倉位集中度風險
            position_concentration = required_capital / self.config.max_total_exposure
            
            # 檢查持倉數量
            position_count_risk = len(self.active_positions) / self.config.max_positions
            
            # 綜合倉位風險
            position_risk = max(position_concentration, position_count_risk)
            
            return min(1.0, position_risk)
            
        except Exception as e:
            logger.error(f"❌ 計算倉位風險失敗: {e}")
            return 0.5  # 默認中等風險
    
    async def _calculate_market_risk(self, opportunity: Dict[str, Any]) -> float:
        """計算市場風險"""
        try:
            pairs = opportunity.get('pairs', [])
            market_risk_factors = []
            
            for pair in pairs:
                # 獲取市場數據
                market_data = self.market_data.get(pair, {})
                
                # 波動率風險
                volatility = market_data.get('volatility', 0.02)
                volatility_risk = min(1.0, volatility / 0.1)  # 10%波動率為滿分
                
                # 流動性風險
                liquidity = market_data.get('liquidity', 1.0)
                liquidity_risk = max(0.0, 1.0 - liquidity)
                
                # 點差風險
                spread = market_data.get('spread', 0.001)
                spread_risk = min(1.0, spread / 0.01)  # 1%點差為滿分
                
                pair_risk = (volatility_risk + liquidity_risk + spread_risk) / 3
                market_risk_factors.append(pair_risk)
            
            # 計算平均市場風險
            if market_risk_factors:
                return sum(market_risk_factors) / len(market_risk_factors)
            else:
                return 0.3  # 默認風險
                
        except Exception as e:
            logger.error(f"❌ 計算市場風險失敗: {e}")
            return 0.5
    
    async def _calculate_liquidity_risk(self, opportunity: Dict[str, Any]) -> float:
        """計算流動性風險"""
        try:
            execution_path = opportunity.get('execution_path', [])
            liquidity_risks = []
            
            for step in execution_path:
                pair = step.get('pair', '')
                volume = step.get('volume', 0)
                
                # 獲取市場流動性數據
                market_data = self.market_data.get(pair, {})
                available_volume = market_data.get('volume', 1000)
                
                # 計算流動性使用率
                liquidity_usage = volume / available_volume if available_volume > 0 else 1.0
                
                # 流動性風險評分
                if liquidity_usage > 0.5:
                    liquidity_risk = 0.8  # 高流動性風險
                elif liquidity_usage > 0.2:
                    liquidity_risk = 0.5  # 中等流動性風險
                else:
                    liquidity_risk = 0.2  # 低流動性風險
                
                liquidity_risks.append(liquidity_risk)
            
            # 返回最高流動性風險
            return max(liquidity_risks) if liquidity_risks else 0.3
            
        except Exception as e:
            logger.error(f"❌ 計算流動性風險失敗: {e}")
            return 0.5
    
    async def _calculate_execution_risk(self, opportunity: Dict[str, Any]) -> float:
        """計算執行風險"""
        try:
            execution_path = opportunity.get('execution_path', [])
            
            # 執行步驟數量風險
            steps_count = len(execution_path)
            steps_risk = min(1.0, (steps_count - 1) / 5)  # 6步以上為最高風險
            
            # 交易所數量風險
            exchanges = set(step.get('exchange', '') for step in execution_path)
            exchange_risk = min(1.0, (len(exchanges) - 1) / 3)  # 4個交易所以上為最高風險
            
            # 時間風險 (基於機會過期時間)
            expiry_time = opportunity.get('expiry_time')
            if expiry_time:
                if isinstance(expiry_time, str):
                    expiry_time = datetime.fromisoformat(expiry_time.replace('Z', '+00:00'))
                
                time_to_expiry = (expiry_time - datetime.now()).total_seconds()
                time_risk = max(0.0, 1.0 - time_to_expiry / 60)  # 1分鐘內過期為最高風險
            else:
                time_risk = 0.3
            
            # 綜合執行風險
            execution_risk = (steps_risk + exchange_risk + time_risk) / 3
            
            return min(1.0, execution_risk)
            
        except Exception as e:
            logger.error(f"❌ 計算執行風險失敗: {e}")
            return 0.5
    
    async def _calculate_correlation_risk(self, opportunity: Dict[str, Any]) -> float:
        """計算相關性風險"""
        try:
            pairs = opportunity.get('pairs', [])
            
            if len(pairs) < 2:
                return 0.1  # 單一交易對，相關性風險較低
            
            correlation_risks = []
            
            # 計算交易對間的相關性
            for i in range(len(pairs)):
                for j in range(i + 1, len(pairs)):
                    pair_a = pairs[i]
                    pair_b = pairs[j]
                    
                    # 獲取相關性數據
                    correlation = self.correlation_matrix.get(pair_a, {}).get(pair_b, 0.0)
                    
                    # 高相關性意味著高風險
                    correlation_risk = abs(correlation)
                    correlation_risks.append(correlation_risk)
            
            # 返回最高相關性風險
            return max(correlation_risks) if correlation_risks else 0.2
            
        except Exception as e:
            logger.error(f"❌ 計算相關性風險失敗: {e}")
            return 0.3
    
    def _calculate_total_risk_score(self, risk_metrics: RiskMetrics) -> float:
        """計算總風險分數"""
        try:
            # 風險權重
            weights = {
                'position_risk': 0.25,
                'market_risk': 0.25,
                'liquidity_risk': 0.20,
                'execution_risk': 0.20,
                'correlation_risk': 0.10
            }
            
            # 加權計算總風險
            total_risk = (
                risk_metrics.position_risk * weights['position_risk'] +
                risk_metrics.market_risk * weights['market_risk'] +
                risk_metrics.liquidity_risk * weights['liquidity_risk'] +
                risk_metrics.execution_risk * weights['execution_risk'] +
                risk_metrics.correlation_risk * weights['correlation_risk']
            )
            
            return min(1.0, total_risk)
            
        except Exception as e:
            logger.error(f"❌ 計算總風險分數失敗: {e}")
            return 0.5
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """確定風險等級"""
        try:
            for level, threshold in self.config.risk_thresholds.items():
                if risk_score <= threshold:
                    return level
            
            return RiskLevel.EMERGENCY  # 超過所有閾值
            
        except Exception as e:
            logger.error(f"❌ 確定風險等級失敗: {e}")
            return RiskLevel.HIGH
    
    def _determine_risk_action(self, risk_metrics: RiskMetrics) -> RiskAction:
        """確定風險動作"""
        try:
            risk_level = risk_metrics.risk_level
            
            # 根據風險等級確定動作
            if risk_level == RiskLevel.LOW:
                return RiskAction.ALLOW
            elif risk_level == RiskLevel.MEDIUM:
                return RiskAction.ALLOW  # 中等風險仍允許
            elif risk_level == RiskLevel.HIGH:
                return RiskAction.LIMIT  # 高風險限制執行
            elif risk_level == RiskLevel.CRITICAL:
                return RiskAction.STOP   # 危險風險停止執行
            else:  # EMERGENCY
                return RiskAction.EMERGENCY_EXIT  # 緊急風險立即退出
            
        except Exception as e:
            logger.error(f"❌ 確定風險動作失敗: {e}")
            return RiskAction.STOP
    
    async def register_position(self, execution_id: str, opportunity: Dict[str, Any]) -> str:
        """註冊新倉位"""
        try:
            position_id = f"pos_{execution_id}_{int(datetime.now().timestamp())}"
            
            # 創建倉位記錄
            position = ArbitragePosition(
                position_id=position_id,
                opportunity_id=opportunity.get('opportunity_id', ''),
                execution_id=execution_id,
                pairs=opportunity.get('pairs', []),
                exchanges=opportunity.get('exchanges', []),
                entry_time=datetime.now(),
                expected_profit=opportunity.get('expected_profit', 0),
                required_capital=opportunity.get('required_capital', 0)
            )
            
            # 評估初始風險
            _, _, risk_metrics = await self.evaluate_opportunity_risk(opportunity)
            position.risk_metrics = risk_metrics
            
            # 設置止損
            if self.config.enable_stop_loss:
                position.stop_loss_percentage = self.config.default_stop_loss
                position.stop_loss_price = position.required_capital * (1 - position.stop_loss_percentage)
            
            # 註冊倉位
            self.active_positions[position_id] = position
            
            # 更新總敞口
            self.current_exposure += position.required_capital
            
            logger.info(f"📝 註冊新套利倉位: {position_id}")
            logger.info(f"   所需資金: {position.required_capital:,.2f} TWD")
            logger.info(f"   預期利潤: {position.expected_profit:,.2f} TWD")
            logger.info(f"   風險分數: {position.risk_metrics.total_risk_score:.3f}")
            
            # 更新統計
            self.risk_stats['total_positions'] += 1
            
            return position_id
            
        except Exception as e:
            logger.error(f"❌ 註冊倉位失敗: {e}")
            raise
    
    async def update_position(self, position_id: str, current_value: float, 
                            unrealized_pnl: float) -> bool:
        """更新倉位狀態"""
        try:
            if position_id not in self.active_positions:
                logger.warning(f"⚠️ 倉位不存在: {position_id}")
                return False
            
            position = self.active_positions[position_id]
            
            # 更新倉位數據
            position.current_value = current_value
            position.unrealized_pnl = unrealized_pnl
            position.last_update = datetime.now()
            
            # 檢查止損
            if self.config.enable_stop_loss and position.stop_loss_price:
                if current_value <= position.stop_loss_price:
                    logger.warning(f"🚨 觸發止損: {position_id}")
                    await self._trigger_stop_loss(position)
                    return True
            
            # 更新風險指標
            await self._update_position_risk(position)
            
            # 檢查風險警報
            await self._check_position_alerts(position)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新倉位失敗: {e}")
            return False
    
    async def close_position(self, position_id: str, realized_pnl: float, 
                           status: PositionStatus = PositionStatus.CLOSED) -> bool:
        """關閉倉位"""
        try:
            if position_id not in self.active_positions:
                logger.warning(f"⚠️ 倉位不存在: {position_id}")
                return False
            
            position = self.active_positions[position_id]
            
            # 更新倉位狀態
            position.status = status
            position.realized_pnl = realized_pnl
            position.last_update = datetime.now()
            
            # 更新總敞口
            self.current_exposure -= position.required_capital
            self.current_exposure = max(0, self.current_exposure)  # 確保不為負數
            
            # 更新日損益
            self.daily_pnl += realized_pnl
            
            # 移動到歷史記錄
            self.position_history.append(position)
            del self.active_positions[position_id]
            
            # 保持歷史記錄在合理範圍內
            if len(self.position_history) > 1000:
                self.position_history = self.position_history[-500:]
            
            logger.info(f"📋 關閉套利倉位: {position_id}")
            logger.info(f"   狀態: {status.value}")
            logger.info(f"   實現損益: {realized_pnl:,.2f} TWD")
            logger.info(f"   當前總敞口: {self.current_exposure:,.2f} TWD")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 關閉倉位失敗: {e}")
            return False
    
    async def _trigger_stop_loss(self, position: ArbitragePosition):
        """觸發止損"""
        try:
            logger.warning(f"🛑 執行止損: {position.position_id}")
            
            # 計算止損損失
            stop_loss_amount = position.required_capital * position.stop_loss_percentage
            
            # 更新統計
            self.risk_stats['stopped_positions'] += 1
            self.risk_stats['total_loss_prevented'] += abs(position.unrealized_pnl - stop_loss_amount)
            
            # 關閉倉位
            await self.close_position(position.position_id, -stop_loss_amount, PositionStatus.FAILED)
            
            logger.info(f"✅ 止損執行完成，損失: {stop_loss_amount:,.2f} TWD")
            
        except Exception as e:
            logger.error(f"❌ 執行止損失敗: {e}")
    
    async def _update_position_risk(self, position: ArbitragePosition):
        """更新倉位風險"""
        try:
            # 重新計算風險指標
            opportunity_data = {
                'opportunity_id': position.opportunity_id,
                'pairs': position.pairs,
                'exchanges': position.exchanges,
                'required_capital': position.required_capital,
                'expected_profit': position.expected_profit
            }
            
            _, _, risk_metrics = await self.evaluate_opportunity_risk(opportunity_data)
            position.risk_metrics = risk_metrics
            
            # 更新統計
            self.risk_stats['avg_risk_score'] = self._calculate_avg_risk_score()
            self.risk_stats['max_risk_score'] = max(
                self.risk_stats['max_risk_score'],
                risk_metrics.total_risk_score
            )
            
        except Exception as e:
            logger.error(f"❌ 更新倉位風險失敗: {e}")
    
    async def _check_position_alerts(self, position: ArbitragePosition):
        """檢查倉位警報"""
        try:
            risk_metrics = position.risk_metrics
            
            # 檢查風險閾值
            for alert_type, threshold in self.config.alert_thresholds.items():
                if alert_type == 'position_risk' and risk_metrics.position_risk > threshold:
                    logger.warning(f"⚠️ 倉位風險警報: {position.position_id} - 風險分數: {risk_metrics.position_risk:.3f}")
                
                elif alert_type == 'daily_loss' and self.daily_pnl < -self.config.max_daily_loss * threshold:
                    logger.warning(f"⚠️ 日損失警報: 當前損失: {self.daily_pnl:,.2f} TWD")
                
                elif alert_type == 'drawdown':
                    current_drawdown = self._calculate_current_drawdown()
                    if current_drawdown > self.config.max_drawdown * threshold:
                        logger.warning(f"⚠️ 回撤警報: 當前回撤: {current_drawdown:.2%}")
            
        except Exception as e:
            logger.error(f"❌ 檢查倉位警報失敗: {e}")
    
    def _calculate_avg_risk_score(self) -> float:
        """計算平均風險分數"""
        try:
            if not self.active_positions:
                return 0.0
            
            total_risk = sum(pos.risk_metrics.total_risk_score for pos in self.active_positions.values())
            return total_risk / len(self.active_positions)
            
        except Exception as e:
            logger.error(f"❌ 計算平均風險分數失敗: {e}")
            return 0.0
    
    def _calculate_current_drawdown(self) -> float:
        """計算當前回撤"""
        try:
            if self.peak_equity == 0:
                return 0.0
            
            current_equity = self.peak_equity + self.daily_pnl
            drawdown = (self.peak_equity - current_equity) / self.peak_equity
            
            return max(0.0, drawdown)
            
        except Exception as e:
            logger.error(f"❌ 計算當前回撤失敗: {e}")
            return 0.0
    
    async def _risk_monitoring_loop(self):
        """風險監控循環"""
        while self.is_monitoring:
            try:
                # 檢查全局風險限制
                await self._check_global_risk_limits()
                
                # 更新風險統計
                self._update_risk_stats()
                
                # 等待下次檢查
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ 風險監控循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _position_monitoring_loop(self):
        """倉位監控循環"""
        while self.is_monitoring:
            try:
                # 監控所有活躍倉位
                for position_id, position in list(self.active_positions.items()):
                    await self._monitor_single_position(position)
                
                # 等待下次監控
                await asyncio.sleep(self.config.monitoring_interval * 2)
                
            except Exception as e:
                logger.error(f"❌ 倉位監控循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _market_monitoring_loop(self):
        """市場監控循環"""
        while self.is_monitoring:
            try:
                # 更新市場數據
                await self._update_market_data()
                
                # 更新相關性矩陣
                await self._update_correlation_matrix()
                
                # 等待下次更新
                await asyncio.sleep(5.0)  # 每5秒更新一次
                
            except Exception as e:
                logger.error(f"❌ 市場監控循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _check_global_risk_limits(self):
        """檢查全局風險限制"""
        try:
            # 檢查總敞口
            if self.current_exposure > self.config.max_total_exposure:
                logger.error(f"🚨 總敞口超限: {self.current_exposure:,.2f} > {self.config.max_total_exposure:,.2f}")
                await self._handle_exposure_violation()
            
            # 檢查日損失
            if self.daily_pnl < -self.config.max_daily_loss:
                logger.error(f"🚨 日損失超限: {self.daily_pnl:,.2f} < -{self.config.max_daily_loss:,.2f}")
                await self._handle_daily_loss_violation()
            
            # 檢查最大回撤
            current_drawdown = self._calculate_current_drawdown()
            if current_drawdown > self.config.max_drawdown:
                logger.error(f"🚨 回撤超限: {current_drawdown:.2%} > {self.config.max_drawdown:.2%}")
                await self._handle_drawdown_violation()
            
            self.last_risk_check = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ 檢查全局風險限制失敗: {e}")
    
    async def _handle_exposure_violation(self):
        """處理敞口違規"""
        try:
            logger.warning("🚨 處理敞口違規，開始減倉...")
            
            # 按風險分數排序，優先關閉高風險倉位
            positions = sorted(
                self.active_positions.values(),
                key=lambda x: x.risk_metrics.total_risk_score,
                reverse=True
            )
            
            for position in positions:
                if self.current_exposure <= self.config.max_total_exposure:
                    break
                
                logger.info(f"🔄 強制關閉高風險倉位: {position.position_id}")
                await self.close_position(position.position_id, position.unrealized_pnl, PositionStatus.EMERGENCY)
            
            self.risk_stats['risk_violations'] += 1
            
        except Exception as e:
            logger.error(f"❌ 處理敞口違規失敗: {e}")
    
    async def _handle_daily_loss_violation(self):
        """處理日損失違規"""
        try:
            logger.warning("🚨 處理日損失違規，停止新倉位...")
            
            # 停止所有新的套利機會
            # 這裡可以設置一個標誌，讓外部系統知道暫停交易
            
            self.risk_stats['risk_violations'] += 1
            
        except Exception as e:
            logger.error(f"❌ 處理日損失違規失敗: {e}")
    
    async def _handle_drawdown_violation(self):
        """處理回撤違規"""
        try:
            logger.warning("🚨 處理回撤違規，緊急平倉...")
            
            # 緊急關閉所有倉位
            for position_id, position in list(self.active_positions.items()):
                logger.info(f"🚨 緊急關閉倉位: {position_id}")
                await self.close_position(position_id, position.unrealized_pnl, PositionStatus.EMERGENCY)
            
            self.risk_stats['emergency_exits'] += 1
            self.risk_stats['risk_violations'] += 1
            
        except Exception as e:
            logger.error(f"❌ 處理回撤違規失敗: {e}")
    
    async def _monitor_single_position(self, position: ArbitragePosition):
        """監控單個倉位"""
        try:
            # 檢查倉位年齡
            position_age = (datetime.now() - position.entry_time).total_seconds()
            
            # 如果倉位持續時間過長，增加風險分數
            if position_age > 3600:  # 1小時
                logger.warning(f"⚠️ 倉位持續時間過長: {position.position_id} ({position_age/3600:.1f}小時)")
            
            # 更新倉位風險
            await self._update_position_risk(position)
            
        except Exception as e:
            logger.error(f"❌ 監控單個倉位失敗: {e}")
    
    async def _update_market_data(self):
        """更新市場數據"""
        try:
            # 模擬市場數據更新
            import random
            
            pairs = ["BTCTWD", "ETHTWD", "USDTTWD"]
            
            for pair in pairs:
                self.market_data[pair] = {
                    'volatility': random.uniform(0.01, 0.05),
                    'liquidity': random.uniform(0.5, 2.0),
                    'spread': random.uniform(0.0005, 0.002),
                    'volume': random.uniform(1000, 10000),
                    'timestamp': datetime.now()
                }
            
        except Exception as e:
            logger.error(f"❌ 更新市場數據失敗: {e}")
    
    async def _update_correlation_matrix(self):
        """更新相關性矩陣"""
        try:
            # 模擬相關性矩陣更新
            import random
            
            pairs = ["BTCTWD", "ETHTWD", "USDTTWD"]
            
            for pair_a in pairs:
                if pair_a not in self.correlation_matrix:
                    self.correlation_matrix[pair_a] = {}
                
                for pair_b in pairs:
                    if pair_a != pair_b:
                        # 模擬相關性 (-1 到 1)
                        correlation = random.uniform(-0.5, 0.8)
                        self.correlation_matrix[pair_a][pair_b] = correlation
            
        except Exception as e:
            logger.error(f"❌ 更新相關性矩陣失敗: {e}")
    
    def _update_risk_stats(self):
        """更新風險統計"""
        try:
            # 更新峰值權益
            current_equity = sum(pos.current_value for pos in self.active_positions.values()) + self.daily_pnl
            self.peak_equity = max(self.peak_equity, current_equity)
            
            # 更新最大回撤
            current_drawdown = self._calculate_current_drawdown()
            self.max_drawdown_today = max(self.max_drawdown_today, current_drawdown)
            
        except Exception as e:
            logger.error(f"❌ 更新風險統計失敗: {e}")
    
    async def _wait_for_positions_close(self):
        """等待所有倉位關閉"""
        timeout = 60  # 60秒超時
        start_time = datetime.now()
        
        while self.active_positions and (datetime.now() - start_time).total_seconds() < timeout:
            logger.info(f"⏳ 等待 {len(self.active_positions)} 個倉位關閉...")
            await asyncio.sleep(1.0)
        
        if self.active_positions:
            logger.warning(f"⚠️ 仍有 {len(self.active_positions)} 個倉位未關閉，強制關閉")
            
            # 強制關閉所有倉位
            for position_id, position in list(self.active_positions.items()):
                await self.close_position(position_id, position.unrealized_pnl, PositionStatus.EMERGENCY)
    
    # 公共接口方法
    
    def get_risk_status(self) -> Dict[str, Any]:
        """獲取風險狀態"""
        try:
            return {
                'current_exposure': self.current_exposure,
                'max_exposure': self.config.max_total_exposure,
                'exposure_utilization': self.current_exposure / self.config.max_total_exposure,
                'active_positions': len(self.active_positions),
                'max_positions': self.config.max_positions,
                'daily_pnl': self.daily_pnl,
                'max_daily_loss': self.config.max_daily_loss,
                'current_drawdown': self._calculate_current_drawdown(),
                'max_drawdown': self.config.max_drawdown,
                'avg_risk_score': self._calculate_avg_risk_score(),
                'risk_stats': self.risk_stats.copy(),
                'last_risk_check': self.last_risk_check.isoformat(),
                'monitoring_status': self.is_monitoring
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取風險狀態失敗: {e}")
            return {'error': str(e)}
    
    def get_position_summary(self) -> Dict[str, Any]:
        """獲取倉位摘要"""
        try:
            active_positions = []
            
            for position in self.active_positions.values():
                active_positions.append({
                    'position_id': position.position_id,
                    'opportunity_id': position.opportunity_id,
                    'pairs': position.pairs,
                    'exchanges': position.exchanges,
                    'entry_time': position.entry_time.isoformat(),
                    'required_capital': position.required_capital,
                    'current_value': position.current_value,
                    'unrealized_pnl': position.unrealized_pnl,
                    'risk_score': position.risk_metrics.total_risk_score,
                    'risk_level': position.risk_metrics.risk_level.value,
                    'status': position.status.value
                })
            
            return {
                'active_positions': active_positions,
                'total_positions': len(active_positions),
                'total_capital': sum(pos.required_capital for pos in self.active_positions.values()),
                'total_unrealized_pnl': sum(pos.unrealized_pnl for pos in self.active_positions.values()),
                'position_history_count': len(self.position_history)
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取倉位摘要失敗: {e}")
            return {'error': str(e)}
    
    async def emergency_stop_all(self) -> bool:
        """緊急停止所有倉位"""
        try:
            logger.error("🚨 執行緊急停止所有倉位")
            
            # 關閉所有活躍倉位
            for position_id, position in list(self.active_positions.items()):
                await self.close_position(position_id, position.unrealized_pnl, PositionStatus.EMERGENCY)
            
            # 更新統計
            self.risk_stats['emergency_exits'] += 1
            
            logger.info("✅ 緊急停止完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 緊急停止失敗: {e}")
            return False


# 創建套利風險控制系統實例
def create_arbitrage_risk_controller(config: RiskControlConfig) -> ArbitrageRiskController:
    """創建套利風險控制系統實例"""
    return ArbitrageRiskController(config)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_risk_controller():
        """測試套利風險控制系統"""
        print("🧪 測試套利風險控制系統...")
        
        # 創建配置
        config = RiskControlConfig(
            max_total_exposure=200000,
            max_single_position=50000,
            max_daily_loss=5000,
            enable_stop_loss=True
        )
        
        # 創建風險控制器
        controller = create_arbitrage_risk_controller(config)
        
        try:
            # 模擬套利機會
            opportunity = {
                'opportunity_id': 'test_opp_001',
                'pairs': ['BTCTWD', 'ETHTWD'],
                'exchanges': ['binance', 'max'],
                'required_capital': 30000,
                'expected_profit': 500,
                'execution_path': [
                    {'pair': 'BTCTWD', 'volume': 0.01, 'exchange': 'binance'},
                    {'pair': 'ETHTWD', 'volume': 0.25, 'exchange': 'max'}
                ]
            }
            
            # 評估風險
            print(f"\n🔍 評估套利機會風險...")
            risk_level, risk_action, risk_metrics = await controller.evaluate_opportunity_risk(opportunity)
            
            print(f"   風險等級: {risk_level.value}")
            print(f"   建議動作: {risk_action.value}")
            print(f"   總風險分數: {risk_metrics.total_risk_score:.3f}")
            print(f"   倉位風險: {risk_metrics.position_risk:.3f}")
            print(f"   市場風險: {risk_metrics.market_risk:.3f}")
            print(f"   流動性風險: {risk_metrics.liquidity_risk:.3f}")
            
            # 註冊倉位
            if risk_action in [RiskAction.ALLOW, RiskAction.LIMIT]:
                print(f"\n📝 註冊套利倉位...")
                position_id = await controller.register_position('exec_001', opportunity)
                print(f"   倉位ID: {position_id}")
                
                # 模擬倉位更新
                print(f"\n🔄 模擬倉位更新...")
                await controller.update_position(position_id, 29500, -500)
                await controller.update_position(position_id, 29000, -1000)
                
                # 關閉倉位
                print(f"\n📋 關閉倉位...")
                await controller.close_position(position_id, -800)
            
            # 獲取風險狀態
            risk_status = controller.get_risk_status()
            print(f"\n📊 風險狀態:")
            print(f"   當前敞口: {risk_status['current_exposure']:,.2f} TWD")
            print(f"   敞口利用率: {risk_status['exposure_utilization']:.1%}")
            print(f"   活躍倉位: {risk_status['active_positions']}")
            print(f"   日損益: {risk_status['daily_pnl']:,.2f} TWD")
            print(f"   當前回撤: {risk_status['current_drawdown']:.2%}")
            
            # 獲取倉位摘要
            position_summary = controller.get_position_summary()
            print(f"\n📋 倉位摘要:")
            print(f"   活躍倉位數: {position_summary['total_positions']}")
            print(f"   總資金: {position_summary['total_capital']:,.2f} TWD")
            print(f"   未實現損益: {position_summary['total_unrealized_pnl']:,.2f} TWD")
            
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
        
        print("🎉 套利風險控制系統測試完成！")
    
    # 運行測試
    asyncio.run(test_risk_controller())