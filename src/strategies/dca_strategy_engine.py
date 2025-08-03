#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DCA定投策略核心引擎 - 實現智能定投策略
支持多種定投模式和動態調整機制
"""

import logging
import asyncio
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
from pathlib import Path

logger = logging.getLogger(__name__)

class DCAMode(Enum):
    """DCA模式"""
    FIXED_AMOUNT = "fixed_amount"      # 固定金額定投
    FIXED_RATIO = "fixed_ratio"        # 固定比例定投
    DYNAMIC_AMOUNT = "dynamic_amount"  # 動態金額定投
    SMART_DCA = "smart_dca"           # 智能定投

class DCAStatus(Enum):
    """DCA狀態"""
    INACTIVE = "inactive"      # 未激活
    ACTIVE = "active"          # 運行中
    PAUSED = "paused"          # 暫停
    STOPPED = "stopped"        # 已停止
    ERROR = "error"            # 錯誤狀態

class DCAFrequency(Enum):
    """定投頻率"""
    DAILY = "daily"            # 每日
    WEEKLY = "weekly"          # 每週
    MONTHLY = "monthly"        # 每月
    CUSTOM = "custom"          # 自定義間隔

class MarketCondition(Enum):
    """市場條件"""
    BULL = "bull"              # 牛市
    BEAR = "bear"              # 熊市
    SIDEWAYS = "sideways"      # 震盪市
    VOLATILE = "volatile"      # 高波動

@dataclass
class DCAOrder:
    """DCA訂單"""
    order_id: str                      # 訂單ID
    timestamp: datetime                # 時間戳
    pair: str                         # 交易對
    amount: float                     # 投資金額
    price: float                      # 執行價格
    quantity: float                   # 購買數量
    status: str = "pending"           # 訂單狀態
    market_condition: str = "unknown" # 市場條件
    confidence: float = 0.5           # AI信心度
    commission: float = 0.0           # 手續費
    executed_time: Optional[datetime] = None  # 執行時間

@dataclass
class DCAConfig:
    """DCA配置"""
    pair: str                         # 交易對
    mode: DCAMode                     # DCA模式
    frequency: DCAFrequency           # 定投頻率
    base_amount: float                # 基礎投資金額
    max_total_investment: float       # 最大總投資額
    target_allocation: float = 1.0    # 目標分配比例
    
    # 動態調整參數
    bull_market_multiplier: float = 0.8    # 牛市投資倍數
    bear_market_multiplier: float = 1.5    # 熊市投資倍數
    volatility_threshold: float = 0.05     # 波動率閾值
    
    # 風險控制
    max_single_investment: float = 0.0     # 單次最大投資額
    min_price_threshold: float = 0.0       # 最低價格閾值
    max_price_threshold: float = 0.0       # 最高價格閾值
    
    # 時間控制
    start_time: Optional[datetime] = None   # 開始時間
    end_time: Optional[datetime] = None     # 結束時間
    custom_interval_hours: int = 24         # 自定義間隔(小時)
    
    # AI增強
    use_ai_timing: bool = True             # 使用AI時機選擇
    ai_confidence_threshold: float = 0.6   # AI信心度閾值
    
    def __post_init__(self):
        if self.max_single_investment == 0.0:
            self.max_single_investment = self.base_amount * 3
        if self.start_time is None:
            self.start_time = datetime.now()

@dataclass
class DCAPerformance:
    """DCA績效統計"""
    total_investments: int = 0              # 總投資次數
    total_amount_invested: float = 0.0      # 總投資金額
    total_quantity_acquired: float = 0.0    # 總購買數量
    average_cost: float = 0.0               # 平均成本
    current_value: float = 0.0              # 當前價值
    unrealized_pnl: float = 0.0             # 未實現盈虧
    unrealized_pnl_pct: float = 0.0         # 未實現盈虧百分比
    total_fees: float = 0.0                 # 總手續費
    
    # 市場條件統計
    bull_investments: int = 0               # 牛市投資次數
    bear_investments: int = 0               # 熊市投資次數
    sideways_investments: int = 0           # 震盪市投資次數
    
    # 時間統計
    first_investment: Optional[datetime] = None  # 首次投資時間
    last_investment: Optional[datetime] = None   # 最後投資時間
    investment_period_days: int = 0              # 投資週期天數
    
    # 風險指標
    max_drawdown: float = 0.0               # 最大回撤
    volatility: float = 0.0                 # 波動率
    sharpe_ratio: float = 0.0               # 夏普比率
    
    last_update: datetime = field(default_factory=datetime.now)

class DCAStrategyEngine:
    """DCA定投策略核心引擎"""
    
    def __init__(self, config: DCAConfig):
        self.config = config
        self.status = DCAStatus.INACTIVE
        
        # 訂單管理
        self.order_history: List[DCAOrder] = []
        self.pending_orders: List[DCAOrder] = []
        
        # 績效統計
        self.performance = DCAPerformance()
        
        # 市場數據
        self.current_price = 0.0
        self.price_history: List[Tuple[datetime, float]] = []
        self.market_condition = MarketCondition.SIDEWAYS
        
        # 定時器和控制
        self.next_investment_time: Optional[datetime] = None
        self.timer_thread: Optional[threading.Thread] = None
        self.timer_active = False
        
        # AI增強
        self.ai_coordinator = None  # 將在初始化時設置
        
        logger.info(f"🔥 DCA策略引擎初始化完成: {config.pair} ({config.mode.value})")
    
    def set_ai_coordinator(self, ai_coordinator):
        """設置AI協調器"""
        self.ai_coordinator = ai_coordinator
        logger.info("🧠 AI協調器已設置")
    
    def start_dca(self) -> bool:
        """啟動DCA策略"""
        try:
            if self.status != DCAStatus.INACTIVE:
                logger.warning(f"⚠️ DCA策略已在運行狀態: {self.status.value}")
                return False
            
            # 計算下次投資時間
            self._calculate_next_investment_time()
            
            # 更新狀態
            self.status = DCAStatus.ACTIVE
            self.performance.first_investment = datetime.now()
            
            # 啟動定時器
            self._start_timer()
            
            logger.info(f"🚀 {self.config.pair} DCA策略啟動成功")
            logger.info(f"📅 下次投資時間: {self.next_investment_time}")
            return True
            
        except Exception as e:
            logger.error(f"❌ DCA策略啟動失敗: {e}")
            self.status = DCAStatus.ERROR
            return False
    
    def stop_dca(self) -> bool:
        """停止DCA策略"""
        try:
            if self.status == DCAStatus.INACTIVE:
                logger.warning("⚠️ DCA策略未啟動")
                return False
            
            # 停止定時器
            self._stop_timer()
            
            # 取消待處理訂單
            self.pending_orders.clear()
            
            # 更新狀態
            self.status = DCAStatus.STOPPED
            
            logger.info(f"🛑 {self.config.pair} DCA策略已停止")
            return True
            
        except Exception as e:
            logger.error(f"❌ DCA策略停止失敗: {e}")
            return False
    
    def pause_dca(self) -> bool:
        """暫停DCA策略"""
        try:
            if self.status != DCAStatus.ACTIVE:
                logger.warning(f"⚠️ DCA策略不在運行狀態: {self.status.value}")
                return False
            
            self.status = DCAStatus.PAUSED
            logger.info(f"⏸️ {self.config.pair} DCA策略已暫停")
            return True
            
        except Exception as e:
            logger.error(f"❌ DCA策略暫停失敗: {e}")
            return False
    
    def resume_dca(self) -> bool:
        """恢復DCA策略"""
        try:
            if self.status != DCAStatus.PAUSED:
                logger.warning(f"⚠️ DCA策略不在暫停狀態: {self.status.value}")
                return False
            
            self.status = DCAStatus.ACTIVE
            logger.info(f"▶️ {self.config.pair} DCA策略已恢復")
            return True
            
        except Exception as e:
            logger.error(f"❌ DCA策略恢復失敗: {e}")
            return False
    
    def update_market_price(self, new_price: float) -> Dict[str, Any]:
        """更新市場價格"""
        try:
            old_price = self.current_price
            self.current_price = new_price
            self.price_history.append((datetime.now(), new_price))
            
            # 保持價格歷史在合理範圍內
            if len(self.price_history) > 1000:
                self.price_history = self.price_history[-500:]
            
            # 分析市場條件
            self._analyze_market_condition()
            
            # 更新績效統計
            self._update_performance_stats()
            
            # 檢查是否需要立即投資（智能DCA模式）
            immediate_investment = None
            if (self.config.mode == DCAMode.SMART_DCA and 
                self.status == DCAStatus.ACTIVE):
                immediate_investment = self._check_immediate_investment_opportunity()
            
            return {
                "status": self.status.value,
                "price_updated": True,
                "old_price": old_price,
                "new_price": new_price,
                "market_condition": self.market_condition.value,
                "next_investment_time": self.next_investment_time,
                "immediate_investment": immediate_investment,
                "current_value": self.performance.current_value,
                "unrealized_pnl": self.performance.unrealized_pnl,
                "unrealized_pnl_pct": self.performance.unrealized_pnl_pct
            }
            
        except Exception as e:
            logger.error(f"❌ 更新市場價格失敗: {e}")
            return {"status": "error", "error": str(e)}
    
    def execute_investment(self, amount: Optional[float] = None, 
                          force: bool = False) -> Dict[str, Any]:
        """執行投資"""
        try:
            if not force and self.status != DCAStatus.ACTIVE:
                return {"success": False, "error": "DCA策略未激活"}
            
            if self.current_price <= 0:
                return {"success": False, "error": "無效的市場價格"}
            
            # 計算投資金額
            investment_amount = amount if amount else self._calculate_investment_amount()
            
            # 風險檢查
            risk_check = self._perform_risk_checks(investment_amount)
            if not risk_check["passed"]:
                return {"success": False, "error": risk_check["reason"]}
            
            # AI時機檢查
            if self.config.use_ai_timing and not force:
                ai_check = self._check_ai_timing()
                if not ai_check["approved"]:
                    return {"success": False, "error": ai_check["reason"]}
            
            # 創建訂單
            order = DCAOrder(
                order_id=f"dca_{self.config.pair}_{int(datetime.now().timestamp())}",
                timestamp=datetime.now(),
                pair=self.config.pair,
                amount=investment_amount,
                price=self.current_price,
                quantity=investment_amount / self.current_price,
                market_condition=self.market_condition.value,
                confidence=0.8,  # 默認信心度
                commission=investment_amount * 0.001  # 假設0.1%手續費
            )
            
            # 模擬執行訂單
            success = self._execute_order(order)
            
            if success:
                # 更新下次投資時間
                self._calculate_next_investment_time()
                
                # 更新績效統計
                self._update_performance_stats()
                
                logger.info(f"✅ DCA投資執行成功: {investment_amount:,.2f} TWD @ {self.current_price:,.2f}")
                
                return {
                    "success": True,
                    "order": {
                        "order_id": order.order_id,
                        "amount": order.amount,
                        "price": order.price,
                        "quantity": order.quantity,
                        "market_condition": order.market_condition
                    },
                    "next_investment_time": self.next_investment_time,
                    "total_invested": self.performance.total_amount_invested,
                    "average_cost": self.performance.average_cost
                }
            else:
                return {"success": False, "error": "訂單執行失敗"}
            
        except Exception as e:
            logger.error(f"❌ 執行投資失敗: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_investment_amount(self) -> float:
        """計算投資金額"""
        try:
            base_amount = self.config.base_amount
            
            if self.config.mode == DCAMode.FIXED_AMOUNT:
                return base_amount
            
            elif self.config.mode == DCAMode.FIXED_RATIO:
                # 基於剩餘資金的固定比例
                remaining_budget = (self.config.max_total_investment - 
                                  self.performance.total_amount_invested)
                return min(base_amount, remaining_budget * self.config.target_allocation)
            
            elif self.config.mode == DCAMode.DYNAMIC_AMOUNT:
                # 基於市場條件動態調整
                multiplier = self._get_market_multiplier()
                return base_amount * multiplier
            
            elif self.config.mode == DCAMode.SMART_DCA:
                # AI增強的智能投資金額
                multiplier = self._get_market_multiplier()
                ai_multiplier = self._get_ai_multiplier()
                return base_amount * multiplier * ai_multiplier
            
            return base_amount
            
        except Exception as e:
            logger.error(f"❌ 計算投資金額失敗: {e}")
            return self.config.base_amount
    
    def _get_market_multiplier(self) -> float:
        """獲取市場條件倍數"""
        if self.market_condition == MarketCondition.BULL:
            return self.config.bull_market_multiplier
        elif self.market_condition == MarketCondition.BEAR:
            return self.config.bear_market_multiplier
        elif self.market_condition == MarketCondition.VOLATILE:
            return 1.2  # 高波動時稍微增加投資
        else:
            return 1.0  # 震盪市正常投資
    
    def _get_ai_multiplier(self) -> float:
        """獲取AI建議倍數"""
        try:
            if not self.ai_coordinator:
                return 1.0
            
            # 這裡可以調用AI協調器獲取投資建議
            # 暫時返回基於價格趨勢的簡單邏輯
            if len(self.price_history) >= 5:
                recent_prices = [price for _, price in self.price_history[-5:]]
                price_trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
                
                if price_trend < -0.05:  # 價格下跌超過5%
                    return 1.3  # 增加投資
                elif price_trend > 0.05:  # 價格上漲超過5%
                    return 0.7  # 減少投資
            
            return 1.0
            
        except Exception as e:
            logger.error(f"❌ 獲取AI倍數失敗: {e}")
            return 1.0
    
    def _perform_risk_checks(self, amount: float) -> Dict[str, Any]:
        """執行風險檢查"""
        try:
            # 檢查單次投資限額
            if amount > self.config.max_single_investment:
                return {
                    "passed": False,
                    "reason": f"投資金額 {amount:,.2f} 超過單次限額 {self.config.max_single_investment:,.2f}"
                }
            
            # 檢查總投資限額
            if (self.performance.total_amount_invested + amount > 
                self.config.max_total_investment):
                return {
                    "passed": False,
                    "reason": f"總投資將超過限額 {self.config.max_total_investment:,.2f}"
                }
            
            # 檢查價格閾值
            if (self.config.min_price_threshold > 0 and 
                self.current_price < self.config.min_price_threshold):
                return {
                    "passed": False,
                    "reason": f"價格 {self.current_price:,.2f} 低於最低閾值 {self.config.min_price_threshold:,.2f}"
                }
            
            if (self.config.max_price_threshold > 0 and 
                self.current_price > self.config.max_price_threshold):
                return {
                    "passed": False,
                    "reason": f"價格 {self.current_price:,.2f} 高於最高閾值 {self.config.max_price_threshold:,.2f}"
                }
            
            # 檢查時間範圍
            now = datetime.now()
            if self.config.end_time and now > self.config.end_time:
                return {
                    "passed": False,
                    "reason": "已超過投資結束時間"
                }
            
            return {"passed": True, "reason": "所有風險檢查通過"}
            
        except Exception as e:
            logger.error(f"❌ 風險檢查失敗: {e}")
            return {"passed": False, "reason": f"風險檢查錯誤: {e}"}
    
    def _check_ai_timing(self) -> Dict[str, Any]:
        """檢查AI時機"""
        try:
            if not self.ai_coordinator:
                return {"approved": True, "reason": "無AI協調器，默認通過"}
            
            # 這裡可以調用AI協調器進行時機分析
            # 暫時使用簡化邏輯
            
            # 基於市場條件的簡單判斷
            if self.market_condition == MarketCondition.BEAR:
                return {"approved": True, "reason": "熊市適合定投"}
            elif self.market_condition == MarketCondition.VOLATILE:
                return {"approved": True, "reason": "高波動適合定投"}
            elif self.market_condition == MarketCondition.BULL:
                # 牛市中需要更謹慎
                if len(self.price_history) >= 3:
                    recent_prices = [price for _, price in self.price_history[-3:]]
                    if recent_prices[-1] < recent_prices[0]:  # 最近有回調
                        return {"approved": True, "reason": "牛市回調，適合投資"}
                    else:
                        return {"approved": False, "reason": "牛市持續上漲，等待回調"}
            
            return {"approved": True, "reason": "時機檢查通過"}
            
        except Exception as e:
            logger.error(f"❌ AI時機檢查失敗: {e}")
            return {"approved": True, "reason": "AI檢查錯誤，默認通過"}
    
    def _execute_order(self, order: DCAOrder) -> bool:
        """執行訂單"""
        try:
            # 模擬訂單執行
            order.status = "filled"
            order.executed_time = datetime.now()
            
            # 添加到歷史記錄
            self.order_history.append(order)
            
            # 更新績效統計
            self.performance.total_investments += 1
            self.performance.total_amount_invested += order.amount
            self.performance.total_quantity_acquired += order.quantity
            self.performance.total_fees += order.commission
            self.performance.last_investment = order.executed_time
            
            # 更新市場條件統計
            if order.market_condition == "bull":
                self.performance.bull_investments += 1
            elif order.market_condition == "bear":
                self.performance.bear_investments += 1
            else:
                self.performance.sideways_investments += 1
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 執行訂單失敗: {e}")
            return False
    
    def _analyze_market_condition(self):
        """分析市場條件"""
        try:
            if len(self.price_history) < 10:
                self.market_condition = MarketCondition.SIDEWAYS
                return
            
            # 獲取最近的價格數據
            recent_prices = [price for _, price in self.price_history[-20:]]
            
            # 計算價格變化和波動率
            price_changes = []
            for i in range(1, len(recent_prices)):
                change = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
                price_changes.append(change)
            
            if not price_changes:
                self.market_condition = MarketCondition.SIDEWAYS
                return
            
            # 計算平均變化和波動率
            avg_change = sum(price_changes) / len(price_changes)
            volatility = math.sqrt(sum((change - avg_change) ** 2 for change in price_changes) / len(price_changes))
            
            # 判斷市場條件
            if volatility > self.config.volatility_threshold:
                self.market_condition = MarketCondition.VOLATILE
            elif avg_change > 0.01:  # 平均上漲超過1%
                self.market_condition = MarketCondition.BULL
            elif avg_change < -0.01:  # 平均下跌超過1%
                self.market_condition = MarketCondition.BEAR
            else:
                self.market_condition = MarketCondition.SIDEWAYS
            
        except Exception as e:
            logger.error(f"❌ 分析市場條件失敗: {e}")
            self.market_condition = MarketCondition.SIDEWAYS
    
    def _check_immediate_investment_opportunity(self) -> Optional[Dict[str, Any]]:
        """檢查立即投資機會（智能DCA模式）"""
        try:
            if len(self.price_history) < 5:
                return None
            
            # 檢查價格是否有顯著下跌
            recent_prices = [price for _, price in self.price_history[-5:]]
            price_drop = (recent_prices[0] - recent_prices[-1]) / recent_prices[0]
            
            # 如果價格下跌超過3%，考慮立即投資
            if price_drop > 0.03:
                investment_amount = self._calculate_investment_amount() * 0.5  # 減半投資
                
                # 執行風險檢查
                risk_check = self._perform_risk_checks(investment_amount)
                if risk_check["passed"]:
                    return {
                        "recommended": True,
                        "amount": investment_amount,
                        "reason": f"價格下跌 {price_drop:.2%}，建議立即投資",
                        "confidence": 0.7
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 檢查立即投資機會失敗: {e}")
            return None
    
    def _calculate_next_investment_time(self):
        """計算下次投資時間"""
        try:
            now = datetime.now()
            
            if self.config.frequency == DCAFrequency.DAILY:
                self.next_investment_time = now + timedelta(days=1)
            elif self.config.frequency == DCAFrequency.WEEKLY:
                self.next_investment_time = now + timedelta(weeks=1)
            elif self.config.frequency == DCAFrequency.MONTHLY:
                self.next_investment_time = now + timedelta(days=30)
            elif self.config.frequency == DCAFrequency.CUSTOM:
                self.next_investment_time = now + timedelta(hours=self.config.custom_interval_hours)
            else:
                self.next_investment_time = now + timedelta(days=1)  # 默認每日
            
        except Exception as e:
            logger.error(f"❌ 計算下次投資時間失敗: {e}")
            self.next_investment_time = datetime.now() + timedelta(days=1)
    
    def _update_performance_stats(self):
        """更新績效統計"""
        try:
            if self.performance.total_quantity_acquired > 0:
                # 計算平均成本
                self.performance.average_cost = (
                    self.performance.total_amount_invested / 
                    self.performance.total_quantity_acquired
                )
                
                # 計算當前價值
                self.performance.current_value = (
                    self.performance.total_quantity_acquired * self.current_price
                )
                
                # 計算未實現盈虧
                self.performance.unrealized_pnl = (
                    self.performance.current_value - 
                    self.performance.total_amount_invested
                )
                
                # 計算未實現盈虧百分比
                if self.performance.total_amount_invested > 0:
                    self.performance.unrealized_pnl_pct = (
                        self.performance.unrealized_pnl / 
                        self.performance.total_amount_invested
                    )
            
            # 計算投資週期
            if self.performance.first_investment and self.performance.last_investment:
                period = self.performance.last_investment - self.performance.first_investment
                self.performance.investment_period_days = period.days
            
            # 計算最大回撤（簡化版本）
            if len(self.order_history) > 1:
                values = []
                cumulative_invested = 0
                cumulative_quantity = 0
                
                for order in self.order_history:
                    cumulative_invested += order.amount
                    cumulative_quantity += order.quantity
                    current_value = cumulative_quantity * order.price
                    pnl_pct = (current_value - cumulative_invested) / cumulative_invested
                    values.append(pnl_pct)
                
                if values:
                    peak = values[0]
                    max_drawdown = 0
                    for value in values:
                        if value > peak:
                            peak = value
                        drawdown = peak - value
                        if drawdown > max_drawdown:
                            max_drawdown = drawdown
                    
                    self.performance.max_drawdown = max_drawdown
            
            self.performance.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ 更新績效統計失敗: {e}")
    
    def _start_timer(self):
        """啟動定時器"""
        try:
            self.timer_active = True
            self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self.timer_thread.start()
            logger.info("⏰ DCA定時器已啟動")
            
        except Exception as e:
            logger.error(f"❌ 啟動定時器失敗: {e}")
    
    def _stop_timer(self):
        """停止定時器"""
        try:
            self.timer_active = False
            if self.timer_thread and self.timer_thread.is_alive():
                self.timer_thread.join(timeout=5)
            logger.info("⏰ DCA定時器已停止")
            
        except Exception as e:
            logger.error(f"❌ 停止定時器失敗: {e}")
    
    def _timer_loop(self):
        """定時器循環"""
        while self.timer_active:
            try:
                if (self.status == DCAStatus.ACTIVE and 
                    self.next_investment_time and 
                    datetime.now() >= self.next_investment_time):
                    
                    # 執行定期投資
                    result = self.execute_investment()
                    if result["success"]:
                        logger.info(f"⏰ 定期投資執行成功: {result['order']['amount']:,.2f} TWD")
                    else:
                        logger.warning(f"⚠️ 定期投資執行失敗: {result['error']}")
                
                # 每分鐘檢查一次
                import time
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ 定時器循環錯誤: {e}")
                import time
                time.sleep(300)  # 錯誤時等待5分鐘
    
    def get_dca_status(self) -> Dict[str, Any]:
        """獲取DCA狀態"""
        try:
            return {
                "pair": self.config.pair,
                "status": self.status.value,
                "mode": self.config.mode.value,
                "frequency": self.config.frequency.value,
                "current_price": self.current_price,
                "market_condition": self.market_condition.value,
                "next_investment_time": self.next_investment_time,
                "total_investments": self.performance.total_investments,
                "total_amount_invested": self.performance.total_amount_invested,
                "total_quantity_acquired": self.performance.total_quantity_acquired,
                "average_cost": self.performance.average_cost,
                "current_value": self.performance.current_value,
                "unrealized_pnl": self.performance.unrealized_pnl,
                "unrealized_pnl_pct": self.performance.unrealized_pnl_pct,
                "investment_progress": (
                    self.performance.total_amount_invested / 
                    self.config.max_total_investment
                ),
                "last_update": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取DCA狀態失敗: {e}")
            return {"error": str(e)}
    
    def get_performance_report(self) -> Dict[str, Any]:
        """獲取績效報告"""
        try:
            return {
                "pair": self.config.pair,
                "strategy_info": {
                    "mode": self.config.mode.value,
                    "frequency": self.config.frequency.value,
                    "base_amount": self.config.base_amount,
                    "max_total_investment": self.config.max_total_investment
                },
                "investment_summary": {
                    "total_investments": self.performance.total_investments,
                    "total_amount_invested": self.performance.total_amount_invested,
                    "total_quantity_acquired": self.performance.total_quantity_acquired,
                    "average_cost": self.performance.average_cost,
                    "total_fees": self.performance.total_fees
                },
                "current_position": {
                    "current_price": self.current_price,
                    "current_value": self.performance.current_value,
                    "unrealized_pnl": self.performance.unrealized_pnl,
                    "unrealized_pnl_pct": f"{self.performance.unrealized_pnl_pct:.2%}",
                    "cost_basis": self.performance.total_amount_invested
                },
                "market_analysis": {
                    "current_condition": self.market_condition.value,
                    "bull_investments": self.performance.bull_investments,
                    "bear_investments": self.performance.bear_investments,
                    "sideways_investments": self.performance.sideways_investments
                },
                "risk_metrics": {
                    "max_drawdown": f"{self.performance.max_drawdown:.2%}",
                    "investment_period_days": self.performance.investment_period_days,
                    "investment_progress": f"{(self.performance.total_amount_invested / self.config.max_total_investment):.1%}"
                },
                "time_info": {
                    "first_investment": self.performance.first_investment,
                    "last_investment": self.performance.last_investment,
                    "next_investment": self.next_investment_time
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取績效報告失敗: {e}")
            return {"error": str(e)}
    
    def export_dca_data(self, filepath: str) -> bool:
        """導出DCA數據"""
        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "config": {
                    "pair": self.config.pair,
                    "mode": self.config.mode.value,
                    "frequency": self.config.frequency.value,
                    "base_amount": self.config.base_amount,
                    "max_total_investment": self.config.max_total_investment
                },
                "performance": self.get_performance_report(),
                "order_history": [
                    {
                        "order_id": order.order_id,
                        "timestamp": order.timestamp.isoformat(),
                        "amount": order.amount,
                        "price": order.price,
                        "quantity": order.quantity,
                        "market_condition": order.market_condition,
                        "status": order.status,
                        "executed_time": order.executed_time.isoformat() if order.executed_time else None
                    }
                    for order in self.order_history
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ DCA數據已導出: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 導出DCA數據失敗: {e}")
            return False


# 創建DCA策略引擎實例
def create_dca_strategy_engine(config: DCAConfig) -> DCAStrategyEngine:
    """創建DCA策略引擎實例"""
    return DCAStrategyEngine(config)


# 測試代碼
if __name__ == "__main__":
    print("🧪 測試DCA策略核心引擎...")
    
    # 創建測試配置
    test_config = DCAConfig(
        pair="BTCTWD",
        mode=DCAMode.DYNAMIC_AMOUNT,
        frequency=DCAFrequency.DAILY,
        base_amount=5000,
        max_total_investment=100000,
        bull_market_multiplier=0.7,
        bear_market_multiplier=1.5
    )
    
    # 創建引擎
    engine = create_dca_strategy_engine(test_config)
    
    # 啟動DCA
    if engine.start_dca():
        print("✅ DCA策略啟動成功")
        
        # 模擬價格變化和投資
        test_prices = [3500000, 3450000, 3400000, 3480000, 3520000]
        
        for price in test_prices:
            result = engine.update_market_price(price)
            print(f"價格更新: {price:,.0f} -> 市場條件: {result.get('market_condition')}")
            
            # 模擬執行投資
            investment_result = engine.execute_investment()
            if investment_result["success"]:
                print(f"投資執行: {investment_result['order']['amount']:,.2f} TWD")
        
        # 獲取狀態
        status = engine.get_dca_status()
        print(f"DCA狀態: 總投資 {status['total_investments']} 次")
        print(f"平均成本: {status['average_cost']:,.2f} TWD")
        print(f"未實現盈虧: {status['unrealized_pnl']:,.2f} TWD ({status['unrealized_pnl_pct']:.2%})")
        
        # 停止DCA
        engine.stop_dca()
    
    print("🎉 DCA策略引擎測試完成！")