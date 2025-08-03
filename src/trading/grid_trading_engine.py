#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
網格交易核心引擎 - 實現智能網格交易策略
支持多交易對的AI驅動網格交易系統
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

class GridStatus(Enum):
    """網格狀態"""
    INACTIVE = "inactive"      # 未激活
    ACTIVE = "active"          # 運行中
    PAUSED = "paused"          # 暫停
    STOPPED = "stopped"        # 已停止
    ERROR = "error"            # 錯誤狀態

class OrderType(Enum):
    """訂單類型"""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    """訂單狀態"""
    PENDING = "pending"        # 待執行
    FILLED = "filled"          # 已成交
    CANCELLED = "cancelled"    # 已取消
    FAILED = "failed"          # 失敗

@dataclass
class GridLevel:
    """網格層級"""
    level: int                 # 層級編號
    price: float              # 價格
    buy_order_id: Optional[str] = None    # 買單ID
    sell_order_id: Optional[str] = None   # 賣單ID
    buy_filled: bool = False              # 買單是否成交
    sell_filled: bool = False             # 賣單是否成交
    profit_realized: float = 0.0          # 已實現盈利
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class GridOrder:
    """網格訂單"""
    order_id: str
    pair: str
    order_type: OrderType
    price: float
    quantity: float
    status: OrderStatus
    grid_level: int
    created_time: datetime
    filled_time: Optional[datetime] = None
    filled_price: Optional[float] = None
    filled_quantity: Optional[float] = None
    commission: float = 0.0

@dataclass
class GridConfig:
    """網格配置"""
    pair: str                  # 交易對
    base_price: float         # 基準價格
    grid_spacing: float       # 網格間距 (百分比)
    grid_levels: int          # 網格層數
    order_amount: float       # 每格訂單金額 (TWD)
    upper_limit: float        # 上限價格
    lower_limit: float        # 下限價格
    stop_loss: Optional[float] = None     # 止損價格
    take_profit: Optional[float] = None   # 止盈價格
    max_position: float = 0.3             # 最大倉位 (百分比)
    enabled: bool = True                  # 是否啟用

@dataclass
class GridPerformance:
    """網格績效"""
    total_profit: float = 0.0             # 總盈利
    realized_profit: float = 0.0          # 已實現盈利
    unrealized_profit: float = 0.0        # 未實現盈利
    total_trades: int = 0                 # 總交易次數
    successful_trades: int = 0            # 成功交易次數
    win_rate: float = 0.0                 # 勝率
    average_profit_per_trade: float = 0.0 # 平均每筆盈利
    max_drawdown: float = 0.0             # 最大回撤
    sharpe_ratio: float = 0.0             # 夏普比率
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)

class GridTradingEngine:
    """網格交易核心引擎"""
    
    def __init__(self, config: GridConfig):
        self.config = config
        self.status = GridStatus.INACTIVE
        
        # 網格層級管理
        self.grid_levels: Dict[int, GridLevel] = {}
        self.active_orders: Dict[str, GridOrder] = {}
        self.order_history: List[GridOrder] = []
        
        # 績效統計
        self.performance = GridPerformance()
        
        # 價格監控
        self.current_price = config.base_price
        self.price_history: List[Tuple[datetime, float]] = []
        
        # 風險控制
        self.current_position = 0.0  # 當前倉位
        self.available_balance = 0.0  # 可用餘額
        self.reserved_balance = 0.0   # 預留餘額
        
        # 統計數據
        self.stats = {
            "grid_hits": 0,           # 網格觸發次數
            "buy_orders": 0,          # 買單數量
            "sell_orders": 0,         # 賣單數量
            "avg_holding_time": 0.0,  # 平均持倉時間
            "price_range_utilization": 0.0  # 價格區間利用率
        }
        
        logger.info(f"🔲 網格交易引擎初始化完成: {config.pair}")
    
    def initialize_grid(self) -> bool:
        """初始化網格"""
        try:
            logger.info(f"🔲 初始化 {self.config.pair} 網格...")
            
            # 計算網格層級
            self._calculate_grid_levels()
            
            # 驗證配置
            if not self._validate_grid_config():
                logger.error("❌ 網格配置驗證失敗")
                return False
            
            # 設置初始狀態
            self.status = GridStatus.ACTIVE
            self.performance.start_time = datetime.now()
            
            logger.info(f"✅ 網格初始化完成: {len(self.grid_levels)} 個層級")
            return True
            
        except Exception as e:
            logger.error(f"❌ 網格初始化失敗: {e}")
            self.status = GridStatus.ERROR
            return False
    
    def _calculate_grid_levels(self):
        """計算網格層級"""
        try:
            base_price = self.config.base_price
            spacing = self.config.grid_spacing / 100  # 轉換為小數
            levels = self.config.grid_levels
            
            # 計算上下網格
            upper_levels = levels // 2
            lower_levels = levels - upper_levels
            
            # 生成網格層級
            for i in range(-lower_levels, upper_levels + 1):
                if i == 0:
                    continue  # 跳過基準價格層級
                
                level_price = base_price * (1 + i * spacing)
                
                # 檢查價格限制
                if (level_price <= self.config.upper_limit and 
                    level_price >= self.config.lower_limit):
                    
                    self.grid_levels[i] = GridLevel(
                        level=i,
                        price=level_price
                    )
            
            logger.info(f"📊 計算網格層級: {len(self.grid_levels)} 個有效層級")
            
        except Exception as e:
            logger.error(f"❌ 計算網格層級失敗: {e}")
            raise
    
    def _validate_grid_config(self) -> bool:
        """驗證網格配置"""
        try:
            # 檢查基本參數
            if self.config.grid_spacing <= 0:
                logger.error("網格間距必須大於0")
                return False
            
            if self.config.order_amount <= 0:
                logger.error("訂單金額必須大於0")
                return False
            
            if self.config.upper_limit <= self.config.lower_limit:
                logger.error("上限價格必須大於下限價格")
                return False
            
            if not (self.config.lower_limit <= self.config.base_price <= self.config.upper_limit):
                logger.error("基準價格必須在上下限之間")
                return False
            
            # 檢查網格層級數量
            if len(self.grid_levels) < 2:
                logger.error("有效網格層級不足")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置驗證失敗: {e}")
            return False
    
    async def update_price(self, new_price: float) -> Dict[str, Any]:
        """更新價格並處理網格邏輯"""
        try:
            old_price = self.current_price
            self.current_price = new_price
            self.price_history.append((datetime.now(), new_price))
            
            # 保持價格歷史在合理範圍內
            if len(self.price_history) > 1000:
                self.price_history = self.price_history[-500:]
            
            # 檢查網格觸發
            triggered_actions = await self._check_grid_triggers(old_price, new_price)
            
            # 更新績效統計
            self._update_performance_stats()
            
            return {
                "price_updated": True,
                "old_price": old_price,
                "new_price": new_price,
                "triggered_actions": triggered_actions,
                "grid_status": self.status.value
            }
            
        except Exception as e:
            logger.error(f"❌ 價格更新失敗: {e}")
            return {"price_updated": False, "error": str(e)}
    
    async def _check_grid_triggers(self, old_price: float, new_price: float) -> List[Dict[str, Any]]:
        """檢查網格觸發"""
        triggered_actions = []
        
        try:
            if self.status != GridStatus.ACTIVE:
                return triggered_actions
            
            # 檢查每個網格層級
            for level_num, grid_level in self.grid_levels.items():
                level_price = grid_level.price
                
                # 檢查買入觸發 (價格下跌穿過網格線)
                if (old_price > level_price >= new_price and 
                    not grid_level.buy_filled and 
                    grid_level.buy_order_id is None):
                    
                    buy_action = await self._trigger_buy_order(level_num, grid_level)
                    if buy_action:
                        triggered_actions.append(buy_action)
                
                # 檢查賣出觸發 (價格上漲穿過網格線)
                if (old_price < level_price <= new_price and 
                    not grid_level.sell_filled and 
                    grid_level.sell_order_id is None and
                    self.current_position > 0):
                    
                    sell_action = await self._trigger_sell_order(level_num, grid_level)
                    if sell_action:
                        triggered_actions.append(sell_action)
            
            # 檢查止損止盈
            stop_actions = await self._check_stop_conditions(new_price)
            triggered_actions.extend(stop_actions)
            
            return triggered_actions
            
        except Exception as e:
            logger.error(f"❌ 網格觸發檢查失敗: {e}")
            return triggered_actions
    
    async def _trigger_buy_order(self, level_num: int, grid_level: GridLevel) -> Optional[Dict[str, Any]]:
        """觸發買入訂單"""
        try:
            # 檢查資金和風險限制
            if not self._can_place_buy_order():
                return None
            
            # 計算訂單數量
            order_quantity = self._calculate_order_quantity(grid_level.price, OrderType.BUY)
            
            if order_quantity <= 0:
                return None
            
            # 創建買入訂單
            order_id = f"grid_buy_{self.config.pair}_{level_num}_{int(time.time())}"
            
            grid_order = GridOrder(
                order_id=order_id,
                pair=self.config.pair,
                order_type=OrderType.BUY,
                price=grid_level.price,
                quantity=order_quantity,
                status=OrderStatus.PENDING,
                grid_level=level_num,
                created_time=datetime.now()
            )
            
            # 模擬訂單執行 (實際應該調用交易所API)
            success = await self._execute_order(grid_order)
            
            if success:
                grid_level.buy_order_id = order_id
                self.active_orders[order_id] = grid_order
                self.stats["buy_orders"] += 1
                self.stats["grid_hits"] += 1
                
                logger.info(f"🟢 觸發買入: 層級{level_num}, 價格{grid_level.price:.2f}, 數量{order_quantity:.6f}")
                
                return {
                    "action": "buy_triggered",
                    "level": level_num,
                    "price": grid_level.price,
                    "quantity": order_quantity,
                    "order_id": order_id
                }
            
        except Exception as e:
            logger.error(f"❌ 觸發買入訂單失敗: {e}")
        
        return None
    
    async def _trigger_sell_order(self, level_num: int, grid_level: GridLevel) -> Optional[Dict[str, Any]]:
        """觸發賣出訂單"""
        try:
            # 檢查持倉
            if self.current_position <= 0:
                return None
            
            # 計算訂單數量
            order_quantity = self._calculate_order_quantity(grid_level.price, OrderType.SELL)
            
            if order_quantity <= 0:
                return None
            
            # 創建賣出訂單
            order_id = f"grid_sell_{self.config.pair}_{level_num}_{int(time.time())}"
            
            grid_order = GridOrder(
                order_id=order_id,
                pair=self.config.pair,
                order_type=OrderType.SELL,
                price=grid_level.price,
                quantity=order_quantity,
                status=OrderStatus.PENDING,
                grid_level=level_num,
                created_time=datetime.now()
            )
            
            # 模擬訂單執行
            success = await self._execute_order(grid_order)
            
            if success:
                grid_level.sell_order_id = order_id
                self.active_orders[order_id] = grid_order
                self.stats["sell_orders"] += 1
                self.stats["grid_hits"] += 1
                
                logger.info(f"🔴 觸發賣出: 層級{level_num}, 價格{grid_level.price:.2f}, 數量{order_quantity:.6f}")
                
                return {
                    "action": "sell_triggered",
                    "level": level_num,
                    "price": grid_level.price,
                    "quantity": order_quantity,
                    "order_id": order_id
                }
            
        except Exception as e:
            logger.error(f"❌ 觸發賣出訂單失敗: {e}")
        
        return None
    
    def _can_place_buy_order(self) -> bool:
        """檢查是否可以下買單"""
        try:
            # 檢查倉位限制
            if self.current_position >= self.config.max_position:
                return False
            
            # 檢查資金充足性
            required_amount = self.config.order_amount
            if self.available_balance < required_amount:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _calculate_order_quantity(self, price: float, order_type: OrderType) -> float:
        """計算訂單數量"""
        try:
            if order_type == OrderType.BUY:
                # 買入：根據訂單金額計算數量
                quantity = self.config.order_amount / price
            else:
                # 賣出：根據持倉計算數量
                max_sell_quantity = self.current_position * 0.1  # 每次賣出10%持倉
                quantity = min(max_sell_quantity, self.config.order_amount / price)
            
            return max(0, quantity)
            
        except Exception as e:
            logger.error(f"❌ 計算訂單數量失敗: {e}")
            return 0.0
    
    async def _execute_order(self, order: GridOrder) -> bool:
        """執行訂單 (模擬)"""
        try:
            # 模擬訂單執行延遲
            await asyncio.sleep(0.1)
            
            # 模擬成交 (實際應該調用交易所API)
            order.status = OrderStatus.FILLED
            order.filled_time = datetime.now()
            order.filled_price = order.price
            order.filled_quantity = order.quantity
            order.commission = order.quantity * order.price * 0.001  # 0.1% 手續費
            
            # 更新倉位和餘額
            if order.order_type == OrderType.BUY:
                self.current_position += order.quantity
                self.available_balance -= (order.quantity * order.price + order.commission)
            else:
                self.current_position -= order.quantity
                self.available_balance += (order.quantity * order.price - order.commission)
            
            # 移動到歷史記錄
            self.order_history.append(order)
            if order.order_id in self.active_orders:
                del self.active_orders[order.order_id]
            
            # 更新網格層級狀態
            grid_level = self.grid_levels.get(order.grid_level)
            if grid_level:
                if order.order_type == OrderType.BUY:
                    grid_level.buy_filled = True
                else:
                    grid_level.sell_filled = True
                    # 計算盈利
                    grid_level.profit_realized += self._calculate_trade_profit(order)
                
                grid_level.last_update = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 訂單執行失敗: {e}")
            order.status = OrderStatus.FAILED
            return False
    
    def _calculate_trade_profit(self, sell_order: GridOrder) -> float:
        """計算交易盈利"""
        try:
            # 尋找對應的買入訂單
            buy_orders = [o for o in self.order_history 
                         if (o.order_type == OrderType.BUY and 
                             o.grid_level < sell_order.grid_level and
                             o.status == OrderStatus.FILLED)]
            
            if not buy_orders:
                return 0.0
            
            # 使用最近的買入訂單計算盈利
            buy_order = max(buy_orders, key=lambda x: x.filled_time)
            
            profit = ((sell_order.filled_price - buy_order.filled_price) * 
                     min(sell_order.filled_quantity, buy_order.filled_quantity) - 
                     sell_order.commission - buy_order.commission)
            
            return profit
            
        except Exception as e:
            logger.error(f"❌ 計算交易盈利失敗: {e}")
            return 0.0
    
    async def _check_stop_conditions(self, current_price: float) -> List[Dict[str, Any]]:
        """檢查止損止盈條件"""
        stop_actions = []
        
        try:
            # 檢查止損
            if (self.config.stop_loss and 
                current_price <= self.config.stop_loss and 
                self.current_position > 0):
                
                stop_action = await self._execute_stop_loss(current_price)
                if stop_action:
                    stop_actions.append(stop_action)
            
            # 檢查止盈
            if (self.config.take_profit and 
                current_price >= self.config.take_profit and 
                self.current_position > 0):
                
                profit_action = await self._execute_take_profit(current_price)
                if profit_action:
                    stop_actions.append(profit_action)
            
        except Exception as e:
            logger.error(f"❌ 止損止盈檢查失敗: {e}")
        
        return stop_actions
    
    async def _execute_stop_loss(self, current_price: float) -> Optional[Dict[str, Any]]:
        """執行止損"""
        try:
            if self.current_position <= 0:
                return None
            
            # 創建止損訂單
            order_id = f"stop_loss_{self.config.pair}_{int(time.time())}"
            
            stop_order = GridOrder(
                order_id=order_id,
                pair=self.config.pair,
                order_type=OrderType.SELL,
                price=current_price,
                quantity=self.current_position,
                status=OrderStatus.PENDING,
                grid_level=-999,  # 特殊標記
                created_time=datetime.now()
            )
            
            success = await self._execute_order(stop_order)
            
            if success:
                self.status = GridStatus.STOPPED
                logger.warning(f"🛑 執行止損: 價格{current_price:.2f}, 數量{self.current_position:.6f}")
                
                return {
                    "action": "stop_loss_executed",
                    "price": current_price,
                    "quantity": self.current_position,
                    "order_id": order_id
                }
            
        except Exception as e:
            logger.error(f"❌ 執行止損失敗: {e}")
        
        return None
    
    async def _execute_take_profit(self, current_price: float) -> Optional[Dict[str, Any]]:
        """執行止盈"""
        try:
            if self.current_position <= 0:
                return None
            
            # 創建止盈訂單
            order_id = f"take_profit_{self.config.pair}_{int(time.time())}"
            
            profit_order = GridOrder(
                order_id=order_id,
                pair=self.config.pair,
                order_type=OrderType.SELL,
                price=current_price,
                quantity=self.current_position,
                status=OrderStatus.PENDING,
                grid_level=999,  # 特殊標記
                created_time=datetime.now()
            )
            
            success = await self._execute_order(profit_order)
            
            if success:
                self.status = GridStatus.STOPPED
                logger.info(f"🎯 執行止盈: 價格{current_price:.2f}, 數量{self.current_position:.6f}")
                
                return {
                    "action": "take_profit_executed",
                    "price": current_price,
                    "quantity": self.current_position,
                    "order_id": order_id
                }
            
        except Exception as e:
            logger.error(f"❌ 執行止盈失敗: {e}")
        
        return None
    
    def _update_performance_stats(self):
        """更新績效統計"""
        try:
            # 計算已實現盈利
            realized_profit = sum(
                order.filled_quantity * order.filled_price - order.commission
                for order in self.order_history
                if order.status == OrderStatus.FILLED and order.order_type == OrderType.SELL
            ) - sum(
                order.filled_quantity * order.filled_price + order.commission
                for order in self.order_history
                if order.status == OrderStatus.FILLED and order.order_type == OrderType.BUY
            )
            
            # 計算未實現盈利
            unrealized_profit = 0.0
            if self.current_position > 0:
                avg_buy_price = self._calculate_average_buy_price()
                unrealized_profit = (self.current_price - avg_buy_price) * self.current_position
            
            # 更新績效指標
            self.performance.realized_profit = realized_profit
            self.performance.unrealized_profit = unrealized_profit
            self.performance.total_profit = realized_profit + unrealized_profit
            
            # 計算交易統計
            filled_orders = [o for o in self.order_history if o.status == OrderStatus.FILLED]
            self.performance.total_trades = len(filled_orders)
            
            if self.performance.total_trades > 0:
                profitable_trades = sum(1 for order in filled_orders 
                                      if order.order_type == OrderType.SELL and 
                                      self._calculate_trade_profit(order) > 0)
                
                self.performance.successful_trades = profitable_trades
                self.performance.win_rate = profitable_trades / (self.performance.total_trades / 2)  # 除以2因為買賣成對
                self.performance.average_profit_per_trade = realized_profit / (self.performance.total_trades / 2)
            
            # 計算最大回撤
            self.performance.max_drawdown = self._calculate_max_drawdown()
            
            # 計算夏普比率
            self.performance.sharpe_ratio = self._calculate_sharpe_ratio()
            
            self.performance.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ 更新績效統計失敗: {e}")
    
    def _calculate_average_buy_price(self) -> float:
        """計算平均買入價格"""
        try:
            buy_orders = [o for o in self.order_history 
                         if o.status == OrderStatus.FILLED and o.order_type == OrderType.BUY]
            
            if not buy_orders:
                return self.config.base_price
            
            total_cost = sum(o.filled_quantity * o.filled_price + o.commission for o in buy_orders)
            total_quantity = sum(o.filled_quantity for o in buy_orders)
            
            return total_cost / total_quantity if total_quantity > 0 else self.config.base_price
            
        except Exception:
            return self.config.base_price
    
    def _calculate_max_drawdown(self) -> float:
        """計算最大回撤"""
        try:
            if len(self.price_history) < 2:
                return 0.0
            
            peak = self.price_history[0][1]
            max_drawdown = 0.0
            
            for _, price in self.price_history:
                if price > peak:
                    peak = price
                
                drawdown = (peak - price) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception:
            return 0.0
    
    def _calculate_sharpe_ratio(self) -> float:
        """計算夏普比率"""
        try:
            if len(self.price_history) < 30:  # 需要足夠的數據點
                return 0.0
            
            # 計算收益率序列
            returns = []
            for i in range(1, len(self.price_history)):
                prev_price = self.price_history[i-1][1]
                curr_price = self.price_history[i][1]
                returns.append((curr_price - prev_price) / prev_price)
            
            if not returns:
                return 0.0
            
            # 計算平均收益率和標準差
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            
            # 假設無風險利率為0
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0.0
            
            return sharpe_ratio
            
        except Exception:
            return 0.0
    
    def pause_grid(self) -> bool:
        """暫停網格"""
        try:
            if self.status == GridStatus.ACTIVE:
                self.status = GridStatus.PAUSED
                logger.info(f"⏸️ 網格已暫停: {self.config.pair}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 暫停網格失敗: {e}")
            return False
    
    def resume_grid(self) -> bool:
        """恢復網格"""
        try:
            if self.status == GridStatus.PAUSED:
                self.status = GridStatus.ACTIVE
                logger.info(f"▶️ 網格已恢復: {self.config.pair}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ 恢復網格失敗: {e}")
            return False
    
    def stop_grid(self) -> bool:
        """停止網格"""
        try:
            self.status = GridStatus.STOPPED
            
            # 取消所有活躍訂單
            cancelled_orders = []
            for order_id, order in self.active_orders.items():
                order.status = OrderStatus.CANCELLED
                cancelled_orders.append(order_id)
            
            self.active_orders.clear()
            
            logger.info(f"🛑 網格已停止: {self.config.pair}, 取消 {len(cancelled_orders)} 個訂單")
            return True
            
        except Exception as e:
            logger.error(f"❌ 停止網格失敗: {e}")
            return False
    
    def get_grid_status(self) -> Dict[str, Any]:
        """獲取網格狀態"""
        try:
            return {
                "pair": self.config.pair,
                "status": self.status.value,
                "current_price": self.current_price,
                "base_price": self.config.base_price,
                "grid_levels": len(self.grid_levels),
                "active_orders": len(self.active_orders),
                "current_position": self.current_position,
                "available_balance": self.available_balance,
                "performance": {
                    "total_profit": self.performance.total_profit,
                    "realized_profit": self.performance.realized_profit,
                    "unrealized_profit": self.performance.unrealized_profit,
                    "total_trades": self.performance.total_trades,
                    "win_rate": self.performance.win_rate,
                    "max_drawdown": self.performance.max_drawdown,
                    "sharpe_ratio": self.performance.sharpe_ratio
                },
                "statistics": self.stats,
                "last_update": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取網格狀態失敗: {e}")
            return {"error": str(e)}
    
    def get_grid_levels_info(self) -> List[Dict[str, Any]]:
        """獲取網格層級信息"""
        try:
            levels_info = []
            
            for level_num, grid_level in sorted(self.grid_levels.items()):
                level_info = {
                    "level": level_num,
                    "price": grid_level.price,
                    "buy_order_active": grid_level.buy_order_id is not None,
                    "sell_order_active": grid_level.sell_order_id is not None,
                    "buy_filled": grid_level.buy_filled,
                    "sell_filled": grid_level.sell_filled,
                    "profit_realized": grid_level.profit_realized,
                    "distance_from_current": abs(grid_level.price - self.current_price) / self.current_price,
                    "last_update": grid_level.last_update.isoformat()
                }
                levels_info.append(level_info)
            
            return levels_info
            
        except Exception as e:
            logger.error(f"❌ 獲取網格層級信息失敗: {e}")
            return []
    
    def get_order_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取訂單歷史"""
        try:
            recent_orders = self.order_history[-limit:] if limit > 0 else self.order_history
            
            order_history = []
            for order in recent_orders:
                order_info = {
                    "order_id": order.order_id,
                    "pair": order.pair,
                    "type": order.order_type.value,
                    "price": order.price,
                    "quantity": order.quantity,
                    "status": order.status.value,
                    "grid_level": order.grid_level,
                    "created_time": order.created_time.isoformat(),
                    "filled_time": order.filled_time.isoformat() if order.filled_time else None,
                    "filled_price": order.filled_price,
                    "filled_quantity": order.filled_quantity,
                    "commission": order.commission
                }
                order_history.append(order_info)
            
            return order_history
            
        except Exception as e:
            logger.error(f"❌ 獲取訂單歷史失敗: {e}")
            return []
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """更新網格配置"""
        try:
            # 只允許在非活躍狀態下更新配置
            if self.status == GridStatus.ACTIVE:
                logger.warning("網格運行中，無法更新配置")
                return False
            
            # 更新配置
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            # 重新計算網格層級
            self.grid_levels.clear()
            self._calculate_grid_levels()
            
            # 重新驗證配置
            if not self._validate_grid_config():
                logger.error("新配置驗證失敗")
                return False
            
            logger.info(f"✅ 網格配置已更新: {self.config.pair}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新網格配置失敗: {e}")
            return False
    
    def set_balance(self, balance: float):
        """設置可用餘額"""
        self.available_balance = balance
        logger.info(f"💰 設置餘額: {balance:.2f} TWD")
    
    def export_performance_report(self) -> Dict[str, Any]:
        """導出績效報告"""
        try:
            runtime = datetime.now() - self.performance.start_time
            
            report = {
                "grid_config": {
                    "pair": self.config.pair,
                    "base_price": self.config.base_price,
                    "grid_spacing": self.config.grid_spacing,
                    "grid_levels": self.config.grid_levels,
                    "order_amount": self.config.order_amount,
                    "upper_limit": self.config.upper_limit,
                    "lower_limit": self.config.lower_limit
                },
                "performance_summary": {
                    "runtime_hours": runtime.total_seconds() / 3600,
                    "total_profit": self.performance.total_profit,
                    "realized_profit": self.performance.realized_profit,
                    "unrealized_profit": self.performance.unrealized_profit,
                    "total_trades": self.performance.total_trades,
                    "successful_trades": self.performance.successful_trades,
                    "win_rate": self.performance.win_rate,
                    "average_profit_per_trade": self.performance.average_profit_per_trade,
                    "max_drawdown": self.performance.max_drawdown,
                    "sharpe_ratio": self.performance.sharpe_ratio
                },
                "trading_statistics": self.stats,
                "current_status": {
                    "status": self.status.value,
                    "current_price": self.current_price,
                    "current_position": self.current_position,
                    "available_balance": self.available_balance,
                    "active_orders": len(self.active_orders)
                },
                "report_time": datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 導出績效報告失敗: {e}")
            return {"error": str(e)}


# 創建網格交易引擎實例
def create_grid_trading_engine(config: GridConfig) -> GridTradingEngine:
    """創建網格交易引擎實例"""
    return GridTradingEngine(config)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_grid_trading_engine():
        """測試網格交易引擎"""
        print("🧪 測試網格交易引擎...")
        
        # 創建測試配置
        test_config = GridConfig(
            pair="BTCTWD",
            base_price=3500000,  # 350萬TWD
            grid_spacing=2.0,    # 2%間距
            grid_levels=10,      # 10個層級
            order_amount=10000,  # 每格1萬TWD
            upper_limit=4000000, # 上限400萬
            lower_limit=3000000, # 下限300萬
            max_position=0.3     # 最大30%倉位
        )
        
        # 創建網格引擎
        engine = create_grid_trading_engine(test_config)
        engine.set_balance(100000)  # 設置10萬TWD餘額
        
        # 初始化網格
        if engine.initialize_grid():
            print("✅ 網格初始化成功")
            
            # 模擬價格變化
            test_prices = [3500000, 3430000, 3570000, 3360000, 3640000]
            
            for price in test_prices:
                print(f"\\n📈 更新價格: {price:,.0f} TWD")
                result = await engine.update_price(price)
                
                if result["triggered_actions"]:
                    for action in result["triggered_actions"]:
                        print(f"   🎯 觸發動作: {action}")
                
                # 顯示狀態
                status = engine.get_grid_status()
                print(f"   💰 總盈利: {status['performance']['total_profit']:.2f} TWD")
                print(f"   📊 活躍訂單: {status['active_orders']} 個")
                print(f"   📈 當前倉位: {status['current_position']:.6f}")
            
            # 顯示最終報告
            report = engine.export_performance_report()
            print(f"\\n📊 最終績效報告:")
            print(f"   總交易次數: {report['performance_summary']['total_trades']}")
            print(f"   勝率: {report['performance_summary']['win_rate']:.1%}")
            print(f"   總盈利: {report['performance_summary']['total_profit']:.2f} TWD")
            
        else:
            print("❌ 網格初始化失敗")
    
    # 運行測試
    asyncio.run(test_grid_trading_engine())