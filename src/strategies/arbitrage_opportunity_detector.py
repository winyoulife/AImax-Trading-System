#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
套利機會識別系統 - 實現多交易對價格差異監控和套利機會識別
支持三角套利、跨交易所套利、時間套利等多種套利策略
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import math
import itertools
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class ArbitrageType(Enum):
    """套利類型"""
    TRIANGULAR = "triangular"          # 三角套利
    CROSS_EXCHANGE = "cross_exchange"  # 跨交易所套利
    TEMPORAL = "temporal"              # 時間套利
    STATISTICAL = "statistical"        # 統計套利
    FUNDING_RATE = "funding_rate"      # 資金費率套利

class OpportunityStatus(Enum):
    """機會狀態"""
    ACTIVE = "active"                  # 活躍
    EXPIRED = "expired"                # 已過期
    EXECUTED = "executed"              # 已執行
    CANCELLED = "cancelled"            # 已取消
    MONITORING = "monitoring"          # 監控中

@dataclass
class PriceData:
    """價格數據"""
    pair: str
    exchange: str
    bid_price: float
    ask_price: float
    bid_volume: float
    ask_volume: float
    timestamp: datetime
    spread: float = field(init=False)
    mid_price: float = field(init=False)
    
    def __post_init__(self):
        self.spread = self.ask_price - self.bid_price
        self.mid_price = (self.bid_price + self.ask_price) / 2

@dataclass
class ArbitrageOpportunity:
    """套利機會"""
    opportunity_id: str
    arbitrage_type: ArbitrageType
    pairs: List[str]
    exchanges: List[str]
    expected_profit: float
    profit_percentage: float
    required_capital: float
    execution_path: List[Dict[str, Any]]
    risk_score: float
    confidence: float
    timestamp: datetime
    expiry_time: datetime
    status: OpportunityStatus = OpportunityStatus.ACTIVE
    min_profit_threshold: float = 0.001  # 最小利潤閾值
    max_slippage: float = 0.002          # 最大滑點
    
@dataclass
class ArbitrageConfig:
    """套利配置"""
    enabled_types: List[ArbitrageType]
    min_profit_percentage: float = 0.005     # 最小利潤百分比
    max_capital_per_trade: float = 100000    # 單筆最大資金
    max_risk_score: float = 0.7              # 最大風險分數
    opportunity_timeout: int = 30            # 機會超時時間(秒)
    price_update_interval: float = 1.0       # 價格更新間隔(秒)
    exchanges: List[str] = field(default_factory=lambda: ["binance", "max"])
    trading_pairs: List[str] = field(default_factory=lambda: ["BTCTWD", "ETHTWD", "USDTTWD"])
    enable_cross_exchange: bool = True
    enable_triangular: bool = True
    enable_statistical: bool = False

class ArbitrageOpportunityDetector:
    """套利機會識別系統"""
    
    def __init__(self, config: ArbitrageConfig):
        self.config = config
        
        # 價格數據存儲
        self.price_data: Dict[str, Dict[str, PriceData]] = defaultdict(dict)  # {exchange: {pair: PriceData}}
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))  # 價格歷史
        
        # 套利機會
        self.active_opportunities: Dict[str, ArbitrageOpportunity] = {}
        self.opportunity_history: List[ArbitrageOpportunity] = []
        
        # 統計數據
        self.detection_stats = {
            'total_opportunities': 0,
            'profitable_opportunities': 0,
            'executed_opportunities': 0,
            'avg_profit_percentage': 0.0,
            'best_opportunity_profit': 0.0,
            'detection_accuracy': 0.0
        }
        
        # 監控狀態
        self.is_monitoring = False
        self.last_update_time = datetime.now()
        
        logger.info(f"🔍 套利機會識別系統初始化完成")
        logger.info(f"   啟用套利類型: {[t.value for t in config.enabled_types]}")
        logger.info(f"   監控交易所: {config.exchanges}")
        logger.info(f"   監控交易對: {config.trading_pairs}")
    
    async def start_monitoring(self):
        """開始監控套利機會"""
        if self.is_monitoring:
            logger.warning("⚠️ 套利監控已在運行中")
            return
        
        self.is_monitoring = True
        logger.info("🚀 開始套利機會監控")
        
        try:
            # 啟動監控任務
            monitoring_tasks = [
                self._price_monitoring_loop(),
                self._opportunity_detection_loop(),
                self._opportunity_cleanup_loop()
            ]
            
            await asyncio.gather(*monitoring_tasks)
            
        except Exception as e:
            logger.error(f"❌ 套利監控失敗: {e}")
            self.is_monitoring = False
    
    async def stop_monitoring(self):
        """停止監控套利機會"""
        self.is_monitoring = False
        logger.info("🛑 套利機會監控已停止")
    
    async def _price_monitoring_loop(self):
        """價格監控循環"""
        while self.is_monitoring:
            try:
                # 更新價格數據
                await self._update_price_data()
                
                # 等待下次更新
                await asyncio.sleep(self.config.price_update_interval)
                
            except Exception as e:
                logger.error(f"❌ 價格監控循環錯誤: {e}")
                await asyncio.sleep(1)
    
    async def _opportunity_detection_loop(self):
        """機會檢測循環"""
        while self.is_monitoring:
            try:
                # 檢測套利機會
                await self._detect_arbitrage_opportunities()
                
                # 等待下次檢測
                await asyncio.sleep(0.5)  # 更頻繁的機會檢測
                
            except Exception as e:
                logger.error(f"❌ 機會檢測循環錯誤: {e}")
                await asyncio.sleep(1)
    
    async def _opportunity_cleanup_loop(self):
        """機會清理循環"""
        while self.is_monitoring:
            try:
                # 清理過期機會
                await self._cleanup_expired_opportunities()
                
                # 等待下次清理
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ 機會清理循環錯誤: {e}")
                await asyncio.sleep(1)
    
    async def _update_price_data(self):
        """更新價格數據"""
        try:
            # 模擬從多個交易所獲取價格數據
            for exchange in self.config.exchanges:
                for pair in self.config.trading_pairs:
                    # 模擬價格數據
                    price_data = await self._fetch_price_data(exchange, pair)
                    
                    if price_data:
                        # 存儲價格數據
                        self.price_data[exchange][pair] = price_data
                        
                        # 更新價格歷史
                        history_key = f"{exchange}_{pair}"
                        self.price_history[history_key].append({
                            'timestamp': price_data.timestamp,
                            'mid_price': price_data.mid_price,
                            'spread': price_data.spread
                        })
            
            self.last_update_time = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ 更新價格數據失敗: {e}")
    
    async def _fetch_price_data(self, exchange: str, pair: str) -> Optional[PriceData]:
        """獲取價格數據 (模擬)"""
        try:
            # 模擬價格數據生成
            import random
            
            # 基礎價格
            base_prices = {
                "BTCTWD": 3500000,
                "ETHTWD": 120000,
                "USDTTWD": 31.5
            }
            
            base_price = base_prices.get(pair, 100000)
            
            # 添加隨機波動
            volatility = 0.001  # 0.1%波動
            price_change = random.uniform(-volatility, volatility)
            current_price = base_price * (1 + price_change)
            
            # 添加交易所間的價格差異
            exchange_bias = {
                "binance": 0.0,
                "max": random.uniform(-0.002, 0.002)  # MAX交易所可能有±0.2%的價格差異
            }
            
            bias = exchange_bias.get(exchange, 0.0)
            current_price *= (1 + bias)
            
            # 計算買賣價格
            spread_pct = random.uniform(0.0005, 0.002)  # 0.05%-0.2%點差
            spread = current_price * spread_pct
            
            bid_price = current_price - spread / 2
            ask_price = current_price + spread / 2
            
            # 模擬交易量
            bid_volume = random.uniform(0.1, 10.0)
            ask_volume = random.uniform(0.1, 10.0)
            
            return PriceData(
                pair=pair,
                exchange=exchange,
                bid_price=bid_price,
                ask_price=ask_price,
                bid_volume=bid_volume,
                ask_volume=ask_volume,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ 獲取價格數據失敗 {exchange}-{pair}: {e}")
            return None
    
    async def _detect_arbitrage_opportunities(self):
        """檢測套利機會"""
        try:
            new_opportunities = []
            
            # 檢測跨交易所套利
            if ArbitrageType.CROSS_EXCHANGE in self.config.enabled_types:
                cross_exchange_ops = await self._detect_cross_exchange_arbitrage()
                new_opportunities.extend(cross_exchange_ops)
            
            # 檢測三角套利
            if ArbitrageType.TRIANGULAR in self.config.enabled_types:
                triangular_ops = await self._detect_triangular_arbitrage()
                new_opportunities.extend(triangular_ops)
            
            # 檢測統計套利
            if ArbitrageType.STATISTICAL in self.config.enabled_types:
                statistical_ops = await self._detect_statistical_arbitrage()
                new_opportunities.extend(statistical_ops)
            
            # 處理新發現的機會
            for opportunity in new_opportunities:
                await self._process_new_opportunity(opportunity)
            
            # 更新統計
            self._update_detection_stats()
            
        except Exception as e:
            logger.error(f"❌ 檢測套利機會失敗: {e}")
    
    async def _detect_cross_exchange_arbitrage(self) -> List[ArbitrageOpportunity]:
        """檢測跨交易所套利機會"""
        opportunities = []
        
        try:
            for pair in self.config.trading_pairs:
                # 獲取所有交易所的價格
                exchange_prices = {}
                for exchange in self.config.exchanges:
                    if exchange in self.price_data and pair in self.price_data[exchange]:
                        exchange_prices[exchange] = self.price_data[exchange][pair]
                
                if len(exchange_prices) < 2:
                    continue
                
                # 尋找價格差異
                exchanges = list(exchange_prices.keys())
                for i in range(len(exchanges)):
                    for j in range(i + 1, len(exchanges)):
                        exchange_a = exchanges[i]
                        exchange_b = exchanges[j]
                        
                        price_a = exchange_prices[exchange_a]
                        price_b = exchange_prices[exchange_b]
                        
                        # 計算套利機會
                        opportunity = self._calculate_cross_exchange_opportunity(
                            pair, exchange_a, exchange_b, price_a, price_b
                        )
                        
                        if opportunity:
                            opportunities.append(opportunity)
            
        except Exception as e:
            logger.error(f"❌ 檢測跨交易所套利失敗: {e}")
        
        return opportunities
    
    def _calculate_cross_exchange_opportunity(self, pair: str, exchange_a: str, exchange_b: str,
                                           price_a: PriceData, price_b: PriceData) -> Optional[ArbitrageOpportunity]:
        """計算跨交易所套利機會"""
        try:
            # 檢查是否可以從A買入，B賣出
            profit_a_to_b = price_b.bid_price - price_a.ask_price
            profit_b_to_a = price_a.bid_price - price_b.ask_price
            
            # 選擇更有利的方向
            if profit_a_to_b > profit_b_to_a:
                buy_exchange = exchange_a
                sell_exchange = exchange_b
                buy_price = price_a.ask_price
                sell_price = price_b.bid_price
                profit = profit_a_to_b
                available_volume = min(price_a.ask_volume, price_b.bid_volume)
            else:
                buy_exchange = exchange_b
                sell_exchange = exchange_a
                buy_price = price_b.ask_price
                sell_price = price_a.bid_price
                profit = profit_b_to_a
                available_volume = min(price_b.ask_volume, price_a.bid_volume)
            
            # 檢查是否滿足最小利潤要求
            profit_percentage = profit / buy_price
            if profit_percentage < self.config.min_profit_percentage:
                return None
            
            # 計算所需資金
            required_capital = buy_price * available_volume
            if required_capital > self.config.max_capital_per_trade:
                available_volume = self.config.max_capital_per_trade / buy_price
                required_capital = self.config.max_capital_per_trade
            
            # 計算預期利潤
            expected_profit = profit * available_volume
            
            # 風險評估
            risk_score = self._calculate_cross_exchange_risk(price_a, price_b)
            
            # 創建套利機會
            opportunity_id = f"cross_{pair}_{buy_exchange}_{sell_exchange}_{int(datetime.now().timestamp())}"
            
            execution_path = [
                {
                    'action': 'buy',
                    'exchange': buy_exchange,
                    'pair': pair,
                    'price': buy_price,
                    'volume': available_volume
                },
                {
                    'action': 'sell',
                    'exchange': sell_exchange,
                    'pair': pair,
                    'price': sell_price,
                    'volume': available_volume
                }
            ]
            
            return ArbitrageOpportunity(
                opportunity_id=opportunity_id,
                arbitrage_type=ArbitrageType.CROSS_EXCHANGE,
                pairs=[pair],
                exchanges=[buy_exchange, sell_exchange],
                expected_profit=expected_profit,
                profit_percentage=profit_percentage,
                required_capital=required_capital,
                execution_path=execution_path,
                risk_score=risk_score,
                confidence=max(0.5, 1.0 - risk_score),
                timestamp=datetime.now(),
                expiry_time=datetime.now() + timedelta(seconds=self.config.opportunity_timeout)
            )
            
        except Exception as e:
            logger.error(f"❌ 計算跨交易所套利機會失敗: {e}")
            return None
    
    def _calculate_cross_exchange_risk(self, price_a: PriceData, price_b: PriceData) -> float:
        """計算跨交易所套利風險"""
        try:
            # 基礎風險因子
            risk_factors = []
            
            # 點差風險
            avg_spread = (price_a.spread + price_b.spread) / 2
            avg_price = (price_a.mid_price + price_b.mid_price) / 2
            spread_risk = avg_spread / avg_price
            risk_factors.append(min(1.0, spread_risk * 100))
            
            # 流動性風險
            min_volume = min(price_a.ask_volume, price_a.bid_volume, price_b.ask_volume, price_b.bid_volume)
            liquidity_risk = 1.0 / (1.0 + min_volume)  # 流動性越低風險越高
            risk_factors.append(liquidity_risk)
            
            # 時間風險 (價格數據的新鮮度)
            time_diff = abs((price_a.timestamp - price_b.timestamp).total_seconds())
            time_risk = min(1.0, time_diff / 10.0)  # 10秒以上認為有時間風險
            risk_factors.append(time_risk)
            
            # 綜合風險分數
            risk_score = sum(risk_factors) / len(risk_factors)
            
            return min(1.0, risk_score)
            
        except Exception as e:
            logger.error(f"❌ 計算跨交易所套利風險失敗: {e}")
            return 0.8  # 默認高風險
    
    async def _detect_triangular_arbitrage(self) -> List[ArbitrageOpportunity]:
        """檢測三角套利機會"""
        opportunities = []
        
        try:
            # 三角套利需要至少3個相關的交易對
            triangular_sets = self._find_triangular_sets()
            
            for triangle_set in triangular_sets:
                for exchange in self.config.exchanges:
                    opportunity = await self._calculate_triangular_opportunity(exchange, triangle_set)
                    if opportunity:
                        opportunities.append(opportunity)
            
        except Exception as e:
            logger.error(f"❌ 檢測三角套利失敗: {e}")
        
        return opportunities
    
    def _find_triangular_sets(self) -> List[Tuple[str, str, str]]:
        """尋找三角套利組合"""
        triangular_sets = []
        
        try:
            # 基於現有交易對尋找三角組合
            pairs = self.config.trading_pairs
            
            # 簡化版本：假設有BTC/TWD, ETH/TWD, USDT/TWD
            if all(pair in pairs for pair in ["BTCTWD", "ETHTWD", "USDTTWD"]):
                triangular_sets.append(("BTCTWD", "ETHTWD", "USDTTWD"))
            
        except Exception as e:
            logger.error(f"❌ 尋找三角套利組合失敗: {e}")
        
        return triangular_sets
    
    async def _calculate_triangular_opportunity(self, exchange: str, 
                                             triangle_set: Tuple[str, str, str]) -> Optional[ArbitrageOpportunity]:
        """計算三角套利機會"""
        try:
            pair_a, pair_b, pair_c = triangle_set
            
            # 檢查價格數據是否可用
            if (exchange not in self.price_data or 
                not all(pair in self.price_data[exchange] for pair in triangle_set)):
                return None
            
            price_a = self.price_data[exchange][pair_a]
            price_b = self.price_data[exchange][pair_b]
            price_c = self.price_data[exchange][pair_c]
            
            # 計算三角套利路徑
            path1_profit = self._calculate_triangular_path_profit(
                [(price_a, 'buy'), (price_b, 'sell'), (price_c, 'buy')], 100000
            )
            
            path2_profit = self._calculate_triangular_path_profit(
                [(price_b, 'buy'), (price_a, 'sell'), (price_c, 'buy')], 100000
            )
            
            # 選擇更有利的路徑
            if path1_profit['profit'] > path2_profit['profit'] and path1_profit['profit'] > 0:
                selected_path = path1_profit
                execution_path = [
                    {'action': 'buy', 'exchange': exchange, 'pair': pair_a, 'price': price_a.ask_price},
                    {'action': 'sell', 'exchange': exchange, 'pair': pair_b, 'price': price_b.bid_price},
                    {'action': 'buy', 'exchange': exchange, 'pair': pair_c, 'price': price_c.ask_price}
                ]
            elif path2_profit['profit'] > 0:
                selected_path = path2_profit
                execution_path = [
                    {'action': 'buy', 'exchange': exchange, 'pair': pair_b, 'price': price_b.ask_price},
                    {'action': 'sell', 'exchange': exchange, 'pair': pair_a, 'price': price_a.bid_price},
                    {'action': 'buy', 'exchange': exchange, 'pair': pair_c, 'price': price_c.ask_price}
                ]
            else:
                return None
            
            profit_percentage = selected_path['profit'] / selected_path['initial_capital']
            
            # 檢查是否滿足最小利潤要求
            if profit_percentage < self.config.min_profit_percentage:
                return None
            
            # 風險評估
            risk_score = self._calculate_triangular_risk(price_a, price_b, price_c)
            
            # 創建套利機會
            opportunity_id = f"triangular_{exchange}_{int(datetime.now().timestamp())}"
            
            return ArbitrageOpportunity(
                opportunity_id=opportunity_id,
                arbitrage_type=ArbitrageType.TRIANGULAR,
                pairs=list(triangle_set),
                exchanges=[exchange],
                expected_profit=selected_path['profit'],
                profit_percentage=profit_percentage,
                required_capital=selected_path['initial_capital'],
                execution_path=execution_path,
                risk_score=risk_score,
                confidence=max(0.4, 1.0 - risk_score),
                timestamp=datetime.now(),
                expiry_time=datetime.now() + timedelta(seconds=self.config.opportunity_timeout)
            )
            
        except Exception as e:
            logger.error(f"❌ 計算三角套利機會失敗: {e}")
            return None
    
    def _calculate_triangular_path_profit(self, path: List[Tuple[PriceData, str]], 
                                        initial_capital: float) -> Dict[str, float]:
        """計算三角套利路徑利潤"""
        try:
            current_amount = initial_capital
            
            for price_data, action in path:
                if action == 'buy':
                    current_amount = current_amount / price_data.ask_price
                else:  # sell
                    current_amount = current_amount * price_data.bid_price
                
                # 扣除手續費 (假設0.1%)
                current_amount *= 0.999
            
            profit = current_amount - initial_capital
            
            return {
                'initial_capital': initial_capital,
                'final_amount': current_amount,
                'profit': profit
            }
            
        except Exception as e:
            logger.error(f"❌ 計算三角套利路徑利潤失敗: {e}")
            return {'initial_capital': initial_capital, 'final_amount': 0, 'profit': -initial_capital}
    
    def _calculate_triangular_risk(self, price_a: PriceData, price_b: PriceData, 
                                 price_c: PriceData) -> float:
        """計算三角套利風險"""
        try:
            risk_factors = []
            
            # 點差風險
            avg_spread = (price_a.spread + price_b.spread + price_c.spread) / 3
            avg_price = (price_a.mid_price + price_b.mid_price + price_c.mid_price) / 3
            spread_risk = avg_spread / avg_price
            risk_factors.append(min(1.0, spread_risk * 50))
            
            # 流動性風險
            min_volume = min(price_a.ask_volume, price_a.bid_volume,
                           price_b.ask_volume, price_b.bid_volume,
                           price_c.ask_volume, price_c.bid_volume)
            liquidity_risk = 1.0 / (1.0 + min_volume)
            risk_factors.append(liquidity_risk)
            
            # 執行複雜度風險
            execution_risk = 0.6
            risk_factors.append(execution_risk)
            
            return sum(risk_factors) / len(risk_factors)
            
        except Exception as e:
            logger.error(f"❌ 計算三角套利風險失敗: {e}")
            return 0.8
    
    async def _detect_statistical_arbitrage(self) -> List[ArbitrageOpportunity]:
        """檢測統計套利機會"""
        opportunities = []
        
        try:
            for pair in self.config.trading_pairs:
                for exchange in self.config.exchanges:
                    opportunity = await self._calculate_statistical_opportunity(exchange, pair)
                    if opportunity:
                        opportunities.append(opportunity)
            
        except Exception as e:
            logger.error(f"❌ 檢測統計套利失敗: {e}")
        
        return opportunities
    
    async def _calculate_statistical_opportunity(self, exchange: str, 
                                               pair: str) -> Optional[ArbitrageOpportunity]:
        """計算統計套利機會"""
        try:
            history_key = f"{exchange}_{pair}"
            
            if (history_key not in self.price_history or 
                len(self.price_history[history_key]) < 20):
                return None
            
            # 獲取歷史價格
            history = list(self.price_history[history_key])
            prices = [h['mid_price'] for h in history]
            
            # 計算移動平均和標準差
            window = 10
            if len(prices) < window:
                return None
            
            recent_prices = prices[-window:]
            avg_price = sum(recent_prices) / len(recent_prices)
            
            # 計算標準差
            variance = sum((p - avg_price) ** 2 for p in recent_prices) / len(recent_prices)
            std_dev = math.sqrt(variance)
            
            current_price = prices[-1]
            
            # 檢查是否偏離均值超過2個標準差
            deviation = abs(current_price - avg_price) / std_dev
            
            if deviation < 2.0:
                return None
            
            # 判斷方向
            if current_price > avg_price + 2 * std_dev:
                expected_direction = 'sell'
                expected_target = avg_price
            elif current_price < avg_price - 2 * std_dev:
                expected_direction = 'buy'
                expected_target = avg_price
            else:
                return None
            
            # 計算預期利潤
            expected_profit_pct = abs(expected_target - current_price) / current_price
            
            if expected_profit_pct < self.config.min_profit_percentage:
                return None
            
            # 風險評估
            risk_score = 0.7 + (deviation - 2.0) * 0.1
            risk_score = min(1.0, risk_score)
            
            # 創建套利機會
            opportunity_id = f"statistical_{exchange}_{pair}_{int(datetime.now().timestamp())}"
            
            execution_path = [{
                'action': expected_direction,
                'exchange': exchange,
                'pair': pair,
                'price': current_price,
                'target_price': expected_target,
                'volume': 1.0
            }]
            
            return ArbitrageOpportunity(
                opportunity_id=opportunity_id,
                arbitrage_type=ArbitrageType.STATISTICAL,
                pairs=[pair],
                exchanges=[exchange],
                expected_profit=expected_profit_pct * 10000,
                profit_percentage=expected_profit_pct,
                required_capital=10000,
                execution_path=execution_path,
                risk_score=risk_score,
                confidence=max(0.3, 1.0 - risk_score),
                timestamp=datetime.now(),
                expiry_time=datetime.now() + timedelta(seconds=self.config.opportunity_timeout * 2)
            )
            
        except Exception as e:
            logger.error(f"❌ 計算統計套利機會失敗: {e}")
            return None
    
    async def _process_new_opportunity(self, opportunity: ArbitrageOpportunity):
        """處理新發現的機會"""
        try:
            # 檢查是否已存在類似機會
            if self._is_duplicate_opportunity(opportunity):
                return
            
            # 風險檢查
            if opportunity.risk_score > self.config.max_risk_score:
                logger.debug(f"⚠️ 機會風險過高，跳過: {opportunity.opportunity_id}")
                return
            
            # 添加到活躍機會列表
            self.active_opportunities[opportunity.opportunity_id] = opportunity
            
            # 記錄到歷史
            self.opportunity_history.append(opportunity)
            
            # 保持歷史記錄在合理範圍內
            if len(self.opportunity_history) > 1000:
                self.opportunity_history = self.opportunity_history[-500:]
            
            logger.info(f"🎯 發現新套利機會: {opportunity.arbitrage_type.value} - "
                       f"預期利潤: {opportunity.expected_profit:.2f} ({opportunity.profit_percentage:.2%})")
            
        except Exception as e:
            logger.error(f"❌ 處理新機會失敗: {e}")
    
    def _is_duplicate_opportunity(self, new_opportunity: ArbitrageOpportunity) -> bool:
        """檢查是否為重複機會"""
        try:
            for existing_id, existing_opp in self.active_opportunities.items():
                if (existing_opp.arbitrage_type == new_opportunity.arbitrage_type and
                    set(existing_opp.pairs) == set(new_opportunity.pairs) and
                    set(existing_opp.exchanges) == set(new_opportunity.exchanges)):
                    return True
            return False
            
        except Exception as e:
            logger.error(f"❌ 檢查重複機會失敗: {e}")
            return False
    
    async def _cleanup_expired_opportunities(self):
        """清理過期機會"""
        try:
            current_time = datetime.now()
            expired_ids = []
            
            for opp_id, opportunity in self.active_opportunities.items():
                if current_time > opportunity.expiry_time:
                    expired_ids.append(opp_id)
                    opportunity.status = OpportunityStatus.EXPIRED
            
            # 移除過期機會
            for opp_id in expired_ids:
                del self.active_opportunities[opp_id]
            
            if expired_ids:
                logger.debug(f"🧹 清理 {len(expired_ids)} 個過期套利機會")
            
        except Exception as e:
            logger.error(f"❌ 清理過期機會失敗: {e}")
    
    def _update_detection_stats(self):
        """更新檢測統計"""
        try:
            if not self.opportunity_history:
                return
            
            recent_opportunities = self.opportunity_history[-100:]
            
            self.detection_stats.update({
                'total_opportunities': len(self.opportunity_history),
                'profitable_opportunities': sum(1 for opp in recent_opportunities 
                                               if opp.expected_profit > 0),
                'executed_opportunities': sum(1 for opp in recent_opportunities 
                                            if opp.status == OpportunityStatus.EXECUTED),
                'avg_profit_percentage': sum(opp.profit_percentage for opp in recent_opportunities) / len(recent_opportunities),
                'best_opportunity_profit': max((opp.expected_profit for opp in recent_opportunities), default=0)
            })
            
            # 計算檢測準確率
            if self.detection_stats['total_opportunities'] > 0:
                self.detection_stats['detection_accuracy'] = (
                    self.detection_stats['profitable_opportunities'] / 
                    len(recent_opportunities)
                )
            
        except Exception as e:
            logger.error(f"❌ 更新檢測統計失敗: {e}")
    
    def get_active_opportunities(self, sort_by: str = 'profit_percentage') -> List[ArbitrageOpportunity]:
        """獲取活躍套利機會"""
        try:
            opportunities = list(self.active_opportunities.values())
            
            # 排序
            if sort_by == 'profit_percentage':
                opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
            elif sort_by == 'expected_profit':
                opportunities.sort(key=lambda x: x.expected_profit, reverse=True)
            elif sort_by == 'risk_score':
                opportunities.sort(key=lambda x: x.risk_score)
            elif sort_by == 'confidence':
                opportunities.sort(key=lambda x: x.confidence, reverse=True)
            
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ 獲取活躍機會失敗: {e}")
            return []
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """獲取檢測統計"""
        try:
            return {
                'detection_stats': self.detection_stats.copy(),
                'active_opportunities_count': len(self.active_opportunities),
                'monitoring_status': self.is_monitoring,
                'last_update_time': self.last_update_time,
                'price_data_status': {
                    exchange: list(pairs.keys()) 
                    for exchange, pairs in self.price_data.items()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取檢測統計失敗: {e}")
            return {'error': str(e)}
    
    def get_opportunity_by_id(self, opportunity_id: str) -> Optional[ArbitrageOpportunity]:
        """根據ID獲取套利機會"""
        return self.active_opportunities.get(opportunity_id)
    
    async def manual_detect_opportunities(self) -> List[ArbitrageOpportunity]:
        """手動檢測套利機會"""
        try:
            logger.info("🔍 開始手動檢測套利機會...")
            
            # 更新價格數據
            await self._update_price_data()
            
            # 檢測機會
            await self._detect_arbitrage_opportunities()
            
            # 返回活躍機會
            opportunities = self.get_active_opportunities()
            
            logger.info(f"✅ 手動檢測完成，發現 {len(opportunities)} 個套利機會")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ 手動檢測套利機會失敗: {e}")
            return []


# 創建套利機會識別系統實例
def create_arbitrage_opportunity_detector(config: ArbitrageConfig) -> ArbitrageOpportunityDetector:
    """創建套利機會識別系統實例"""
    return ArbitrageOpportunityDetector(config)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_arbitrage_detector():
        """測試套利機會識別系統"""
        print("🧪 測試套利機會識別系統...")
        
        # 創建配置
        config = ArbitrageConfig(
            enabled_types=[ArbitrageType.CROSS_EXCHANGE, ArbitrageType.TRIANGULAR],
            min_profit_percentage=0.002,
            max_capital_per_trade=50000,
            exchanges=["binance", "max"],
            trading_pairs=["BTCTWD", "ETHTWD", "USDTTWD"]
        )
        
        # 創建檢測器
        detector = create_arbitrage_opportunity_detector(config)
        
        # 手動檢測機會
        opportunities = await detector.manual_detect_opportunities()
        
        print(f"✅ 檢測結果:")
        print(f"   發現機會: {len(opportunities)} 個")
        
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"   機會 {i}: {opp.arbitrage_type.value}")
            print(f"      交易對: {opp.pairs}")
            print(f"      交易所: {opp.exchanges}")
            print(f"      預期利潤: {opp.expected_profit:.2f} TWD ({opp.profit_percentage:.2%})")
            print(f"      風險分數: {opp.risk_score:.2f}")
            print(f"      信心度: {opp.confidence:.2f}")
        
        # 獲取統計
        stats = detector.get_detection_stats()
        print(f"\n📊 檢測統計:")
        print(f"   總機會數: {stats['detection_stats']['total_opportunities']}")
        print(f"   盈利機會: {stats['detection_stats']['profitable_opportunities']}")
        print(f"   平均利潤率: {stats['detection_stats']['avg_profit_percentage']:.2%}")
        
        print("🎉 套利機會識別系統測試完成！")
    
    # 運行測試
    asyncio.run(test_arbitrage_detector())