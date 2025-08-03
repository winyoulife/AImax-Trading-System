#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化網格交易引擎 - 核心網格交易功能實現
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class GridStatus(Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"

@dataclass
class GridConfig:
    pair: str
    base_price: float
    grid_spacing: float
    grid_levels: int
    order_amount: float
    upper_limit: float
    lower_limit: float
    max_position: float = 0.3

@dataclass
class GridLevel:
    level: int
    price: float
    buy_filled: bool = False
    sell_filled: bool = False
    profit: float = 0.0

class SimpleGridEngine:
    def __init__(self, config: GridConfig):
        self.config = config
        self.status = GridStatus.INACTIVE
        self.grid_levels: Dict[int, GridLevel] = {}
        self.current_price = config.base_price
        self.current_position = 0.0
        self.available_balance = 0.0
        self.total_profit = 0.0
        self.total_trades = 0
        self.buy_orders = 0
        self.sell_orders = 0
        
        logger.info(f"🔲 簡化網格引擎初始化: {config.pair}")
    
    def initialize_grid(self) -> bool:
        try:
            logger.info(f"🔲 初始化 {self.config.pair} 網格...")
            
            base_price = self.config.base_price
            spacing = self.config.grid_spacing / 100
            levels = self.config.grid_levels
            
            upper_levels = levels // 2
            lower_levels = levels - upper_levels
            
            for i in range(-lower_levels, upper_levels + 1):
                if i == 0:
                    continue
                
                level_price = base_price * (1 + i * spacing)
                
                if (level_price <= self.config.upper_limit and 
                    level_price >= self.config.lower_limit):
                    
                    self.grid_levels[i] = GridLevel(
                        level=i,
                        price=level_price
                    )
            
            self.status = GridStatus.ACTIVE
            logger.info(f"✅ 網格初始化完成: {len(self.grid_levels)} 個層級")
            return True
            
        except Exception as e:
            logger.error(f"❌ 網格初始化失敗: {e}")
            return False
    
    async def update_price(self, new_price: float) -> Dict[str, Any]:
        try:
            old_price = self.current_price
            self.current_price = new_price
            
            triggered_actions = []
            
            if self.status == GridStatus.ACTIVE:
                for level_num, grid_level in self.grid_levels.items():
                    level_price = grid_level.price
                    
                    # 檢查買入觸發
                    if (old_price > level_price >= new_price and 
                        not grid_level.buy_filled):
                        
                        if self._can_buy():
                            grid_level.buy_filled = True
                            self.current_position += self.config.order_amount / level_price
                            self.available_balance -= self.config.order_amount
                            self.buy_orders += 1
                            
                            triggered_actions.append({
                                "action": "buy_triggered",
                                "level": level_num,
                                "price": level_price,
                                "amount": self.config.order_amount
                            })
                            
                            logger.info(f"🟢 買入觸發: 層級{level_num}, 價格{level_price:.0f}")
                    
                    # 檢查賣出觸發
                    if (old_price < level_price <= new_price and 
                        not grid_level.sell_filled and 
                        self.current_position > 0):
                        
                        sell_quantity = min(self.current_position * 0.1, 
                                          self.config.order_amount / level_price)
                        
                        if sell_quantity > 0:
                            grid_level.sell_filled = True
                            self.current_position -= sell_quantity
                            self.available_balance += sell_quantity * level_price
                            self.sell_orders += 1
                            
                            # 計算盈利
                            profit = sell_quantity * level_price - self.config.order_amount
                            grid_level.profit = profit
                            self.total_profit += profit
                            self.total_trades += 1
                            
                            triggered_actions.append({
                                "action": "sell_triggered",
                                "level": level_num,
                                "price": level_price,
                                "quantity": sell_quantity,
                                "profit": profit
                            })
                            
                            logger.info(f"🔴 賣出觸發: 層級{level_num}, 價格{level_price:.0f}, 盈利{profit:.2f}")
            
            return {
                "price_updated": True,
                "old_price": old_price,
                "new_price": new_price,
                "triggered_actions": triggered_actions
            }
            
        except Exception as e:
            logger.error(f"❌ 價格更新失敗: {e}")
            return {"price_updated": False, "error": str(e)}
    
    def _can_buy(self) -> bool:
        return (self.current_position < self.config.max_position and 
                self.available_balance >= self.config.order_amount)
    
    def set_balance(self, balance: float):
        self.available_balance = balance
        logger.info(f"💰 設置餘額: {balance:.2f} TWD")
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "pair": self.config.pair,
            "status": self.status.value,
            "current_price": self.current_price,
            "current_position": self.current_position,
            "available_balance": self.available_balance,
            "total_profit": self.total_profit,
            "total_trades": self.total_trades,
            "buy_orders": self.buy_orders,
            "sell_orders": self.sell_orders,
            "grid_levels": len(self.grid_levels)
        }
    
    def get_grid_info(self) -> List[Dict[str, Any]]:
        return [
            {
                "level": level.level,
                "price": level.price,
                "buy_filled": level.buy_filled,
                "sell_filled": level.sell_filled,
                "profit": level.profit
            }
            for level in sorted(self.grid_levels.values(), key=lambda x: x.level)
        ]
    
    def pause(self) -> bool:
        if self.status == GridStatus.ACTIVE:
            self.status = GridStatus.PAUSED
            return True
        return False
    
    def resume(self) -> bool:
        if self.status == GridStatus.PAUSED:
            self.status = GridStatus.ACTIVE
            return True
        return False
    
    def stop(self) -> bool:
        self.status = GridStatus.STOPPED
        return True

def create_simple_grid_engine(config: GridConfig) -> SimpleGridEngine:
    return SimpleGridEngine(config)

# 測試代碼
if __name__ == "__main__":
    async def test_simple_grid():
        print("🧪 測試簡化網格引擎...")
        
        config = GridConfig(
            pair="BTCTWD",
            base_price=3500000,
            grid_spacing=2.0,
            grid_levels=10,
            order_amount=10000,
            upper_limit=4000000,
            lower_limit=3000000
        )
        
        engine = create_simple_grid_engine(config)
        engine.set_balance(100000)
        
        if engine.initialize_grid():
            print("✅ 網格初始化成功")
            
            prices = [3500000, 3430000, 3570000, 3360000, 3640000]
            
            for price in prices:
                result = await engine.update_price(price)
                print(f"📈 價格: {price:,.0f}, 觸發: {len(result.get('triggered_actions', []))}")
                
                status = engine.get_status()
                print(f"💰 盈利: {status['total_profit']:.2f}, 倉位: {status['current_position']:.6f}")
            
            print("🎉 測試完成！")
    
    asyncio.run(test_simple_grid())