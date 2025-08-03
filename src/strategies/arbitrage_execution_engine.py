#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
套利執行引擎 - 專門負責套利交易的智能執行、路由和監控
支持多種執行策略、智能路由、實時監控和風險控制
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import time

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    """執行狀態"""
    PENDING = "pending"           # 待執行
    EXECUTING = "executing"       # 執行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 執行失敗
    CANCELLED = "cancelled"       # 已取消
    TIMEOUT = "timeout"          # 執行超時

class OrderType(Enum):
    """訂單類型"""
    MARKET = "market"            # 市價單
    LIMIT = "limit"              # 限價單
    STOP_LOSS = "stop_loss"      # 止損單
    TAKE_PROFIT = "take_profit"  # 止盈單

class ExecutionStrategy(Enum):
    """執行策略"""
    AGGRESSIVE = "aggressive"     # 激進執行 (市價單)
    CONSERVATIVE = "conservative" # 保守執行 (限價單)
    ADAPTIVE = "adaptive"        # 自適應執行
    TWAP = "twap"               # 時間加權平均價格
    VWAP = "vwap"               # 成交量加權平均價格

@dataclass
class OrderRequest:
    """訂單請求"""
    order_id: str
    exchange: str
    pair: str
    action: str  # buy/sell
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # GTC, IOC, FOK
    execution_strategy: ExecutionStrategy = ExecutionStrategy.ADAPTIVE
    max_slippage: float = 0.005  # 最大滑點 0.5%
    timeout: int = 30  # 超時時間(秒)
    
@dataclass
class OrderResult:
    """訂單結果"""
    order_id: str
    request: OrderRequest
    status: ExecutionStatus
    executed_quantity: float = 0.0
    executed_price: float = 0.0
    executed_value: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    execution_time: float = 0.0
    error_message: Optional[str] = None
    exchange_order_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
@dataclass
class ArbitrageExecution:
    """套利執行"""
    execution_id: str
    opportunity_id: str
    strategy: ExecutionStrategy
    orders: List[OrderRequest]
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_profit: float = 0.0
    total_fees: float = 0.0
    execution_results: List[OrderResult] = field(default_factory=list)
    error_message: Optional[str] = None

@dataclass
class ExecutionConfig:
    """執行配置"""
    # 基礎配置
    default_strategy: ExecutionStrategy = ExecutionStrategy.ADAPTIVE
    max_concurrent_executions: int = 5
    execution_timeout: int = 60  # 總執行超時時間
    order_timeout: int = 30      # 單個訂單超時時間
    
    # 風險控制
    max_slippage: float = 0.01   # 最大滑點 1%
    max_order_size: float = 100000  # 最大單筆訂單金額
    min_profit_threshold: float = 100  # 最小利潤閾值
    
    # 執行優化
    enable_smart_routing: bool = True
    enable_order_splitting: bool = True
    enable_timing_optimization: bool = True
    
    # 監控配置
    monitoring_interval: float = 0.1  # 監控間隔(秒)
    max_retry_attempts: int = 3
    retry_delay: float = 1.0

class ArbitrageExecutionEngine:
    """套利執行引擎"""
    
    def __init__(self, config: ExecutionConfig):
        self.config = config
        
        # 執行狀態
        self.active_executions: Dict[str, ArbitrageExecution] = {}
        self.execution_history: List[ArbitrageExecution] = []
        self.order_results: Dict[str, OrderResult] = {}
        
        # 執行統計
        self.execution_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'cancelled_executions': 0,
            'timeout_executions': 0,
            'total_profit': 0.0,
            'total_fees': 0.0,
            'avg_execution_time': 0.0,
            'success_rate': 0.0,
            'avg_slippage': 0.0
        }
        
        # 路由和優化
        self.exchange_latency: Dict[str, float] = {}  # 交易所延遲
        self.exchange_fees: Dict[str, float] = {}     # 交易所手續費
        self.market_conditions: Dict[str, Dict] = {}  # 市場條件
        
        # 監控狀態
        self.is_running = False
        
        logger.info("⚡ 套利執行引擎初始化完成")
        logger.info(f"   默認策略: {config.default_strategy.value}")
        logger.info(f"   最大並發: {config.max_concurrent_executions}")
        logger.info(f"   智能路由: {'啟用' if config.enable_smart_routing else '禁用'}")
    
    async def start(self):
        """啟動執行引擎"""
        if self.is_running:
            logger.warning("⚠️ 執行引擎已在運行中")
            return
        
        self.is_running = True
        logger.info("🚀 啟動套利執行引擎")
        
        try:
            # 啟動監控任務
            monitoring_tasks = [
                self._execution_monitoring_loop(),
                self._market_monitoring_loop(),
                self._performance_monitoring_loop()
            ]
            
            await asyncio.gather(*monitoring_tasks)
            
        except Exception as e:
            logger.error(f"❌ 執行引擎啟動失敗: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """停止執行引擎"""
        logger.info("🛑 停止套利執行引擎")
        
        self.is_running = False
        
        # 等待所有執行完成
        await self._wait_for_executions_complete()
        
        logger.info("✅ 套利執行引擎已停止")
    
    async def execute_arbitrage(self, opportunity_id: str, execution_path: List[Dict[str, Any]], 
                              strategy: ExecutionStrategy = None) -> str:
        """執行套利交易"""
        try:
            execution_id = f"exec_{opportunity_id}_{int(time.time() * 1000)}"
            
            # 使用默認策略
            if strategy is None:
                strategy = self.config.default_strategy
            
            logger.info(f"🚀 開始執行套利: {execution_id}")
            logger.info(f"   機會ID: {opportunity_id}")
            logger.info(f"   執行策略: {strategy.value}")
            logger.info(f"   執行步驟: {len(execution_path)} 步")
            
            # 檢查並發限制
            if len(self.active_executions) >= self.config.max_concurrent_executions:
                raise Exception(f"達到最大並發執行限制: {self.config.max_concurrent_executions}")
            
            # 創建訂單請求
            orders = await self._create_order_requests(execution_path, strategy)
            
            # 創建執行記錄
            execution = ArbitrageExecution(
                execution_id=execution_id,
                opportunity_id=opportunity_id,
                strategy=strategy,
                orders=orders,
                start_time=datetime.now()
            )
            
            # 添加到活躍執行
            self.active_executions[execution_id] = execution
            
            # 異步執行套利
            asyncio.create_task(self._execute_arbitrage_async(execution))
            
            return execution_id
            
        except Exception as e:
            logger.error(f"❌ 執行套利失敗: {e}")
            raise
    
    async def _execute_arbitrage_async(self, execution: ArbitrageExecution):
        """異步執行套利"""
        try:
            execution.status = ExecutionStatus.EXECUTING
            
            logger.info(f"⚡ 開始異步執行套利: {execution.execution_id}")
            
            # 執行所有訂單
            success = await self._execute_orders_sequence(execution)
            
            # 更新執行狀態
            execution.end_time = datetime.now()
            
            if success:
                execution.status = ExecutionStatus.COMPLETED
                
                # 計算總利潤和手續費
                execution.total_profit = sum(
                    result.executed_value * (1 if result.request.action == 'sell' else -1)
                    for result in execution.execution_results
                )
                execution.total_fees = sum(result.fees for result in execution.execution_results)
                
                logger.info(f"✅ 套利執行成功: {execution.execution_id}")
                logger.info(f"   總利潤: {execution.total_profit:.2f} TWD")
                logger.info(f"   總手續費: {execution.total_fees:.2f} TWD")
                logger.info(f"   淨利潤: {execution.total_profit - execution.total_fees:.2f} TWD")
                
                self.execution_stats['successful_executions'] += 1
                self.execution_stats['total_profit'] += execution.total_profit - execution.total_fees
                
            else:
                execution.status = ExecutionStatus.FAILED
                logger.error(f"❌ 套利執行失敗: {execution.execution_id}")
                self.execution_stats['failed_executions'] += 1
            
            # 更新統計
            self.execution_stats['total_executions'] += 1
            self._update_execution_stats()
            
        except Exception as e:
            logger.error(f"❌ 異步執行套利異常: {e}")
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            self.execution_stats['failed_executions'] += 1
        
        finally:
            # 移動到歷史記錄
            if execution.execution_id in self.active_executions:
                self.execution_history.append(self.active_executions[execution.execution_id])
                del self.active_executions[execution.execution_id]
            
            # 保持歷史記錄在合理範圍內
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-500:]
    
    async def _create_order_requests(self, execution_path: List[Dict[str, Any]], 
                                   strategy: ExecutionStrategy) -> List[OrderRequest]:
        """創建訂單請求"""
        orders = []
        
        try:
            for i, step in enumerate(execution_path):
                order_id = f"order_{int(time.time() * 1000)}_{i}"
                
                # 基礎訂單信息
                exchange = step.get('exchange', 'unknown')
                pair = step.get('pair', 'unknown')
                action = step.get('action', 'buy')
                quantity = step.get('volume', 0.0)
                price = step.get('price', 0.0)
                
                # 根據策略確定訂單類型
                order_type = self._determine_order_type(strategy, step)
                
                # 智能路由優化
                if self.config.enable_smart_routing:
                    exchange, price = await self._optimize_routing(exchange, pair, action, quantity, price)
                
                # 創建訂單請求
                order = OrderRequest(
                    order_id=order_id,
                    exchange=exchange,
                    pair=pair,
                    action=action,
                    order_type=order_type,
                    quantity=quantity,
                    price=price if order_type == OrderType.LIMIT else None,
                    execution_strategy=strategy,
                    max_slippage=self.config.max_slippage,
                    timeout=self.config.order_timeout
                )
                
                orders.append(order)
                
                logger.debug(f"   創建訂單 {i+1}: {action.upper()} {quantity:.4f} {pair} @ {exchange}")
            
            return orders
            
        except Exception as e:
            logger.error(f"❌ 創建訂單請求失敗: {e}")
            raise
    
    def _determine_order_type(self, strategy: ExecutionStrategy, step: Dict[str, Any]) -> OrderType:
        """根據策略確定訂單類型"""
        try:
            if strategy == ExecutionStrategy.AGGRESSIVE:
                return OrderType.MARKET
            elif strategy == ExecutionStrategy.CONSERVATIVE:
                return OrderType.LIMIT
            elif strategy == ExecutionStrategy.ADAPTIVE:
                # 根據市場條件自適應選擇
                pair = step.get('pair', '')
                market_condition = self.market_conditions.get(pair, {})
                volatility = market_condition.get('volatility', 0.01)
                
                # 高波動性使用限價單，低波動性使用市價單
                return OrderType.LIMIT if volatility > 0.02 else OrderType.MARKET
            else:
                return OrderType.MARKET
                
        except Exception as e:
            logger.error(f"❌ 確定訂單類型失敗: {e}")
            return OrderType.MARKET
    
    async def _optimize_routing(self, exchange: str, pair: str, action: str, 
                              quantity: float, price: float) -> Tuple[str, float]:
        """智能路由優化"""
        try:
            # 簡化版本：基於延遲和手續費選擇最優交易所
            available_exchanges = ['binance', 'max']  # 可用交易所
            
            if exchange not in available_exchanges:
                exchange = available_exchanges[0]  # 默認選擇第一個
            
            # 考慮延遲和手續費
            latency = self.exchange_latency.get(exchange, 0.1)
            fee_rate = self.exchange_fees.get(exchange, 0.001)
            
            # 價格優化 (簡化版本)
            optimized_price = price * (1 + fee_rate) if action == 'buy' else price * (1 - fee_rate)
            
            logger.debug(f"   路由優化: {exchange} (延遲: {latency:.3f}s, 手續費: {fee_rate:.3%})")
            
            return exchange, optimized_price
            
        except Exception as e:
            logger.error(f"❌ 智能路由優化失敗: {e}")
            return exchange, price
    
    async def _execute_orders_sequence(self, execution: ArbitrageExecution) -> bool:
        """按順序執行訂單"""
        try:
            logger.info(f"📋 開始執行 {len(execution.orders)} 個訂單")
            
            for i, order in enumerate(execution.orders):
                logger.info(f"   執行訂單 {i+1}/{len(execution.orders)}: {order.order_id}")
                
                # 執行單個訂單
                result = await self._execute_single_order(order)
                execution.execution_results.append(result)
                
                # 檢查執行結果
                if result.status != ExecutionStatus.COMPLETED:
                    logger.error(f"   ❌ 訂單執行失敗: {result.error_message}")
                    
                    # 如果是關鍵訂單失敗，取消後續訂單
                    if i == 0:  # 第一個訂單失敗
                        execution.error_message = f"關鍵訂單執行失敗: {result.error_message}"
                        return False
                    
                    # 嘗試回滾已執行的訂單
                    await self._rollback_executed_orders(execution.execution_results[:-1])
                    return False
                
                logger.info(f"   ✅ 訂單執行成功: {result.executed_quantity:.4f} @ {result.executed_price:.2f}")
                
                # 訂單間延遲 (避免過快執行)
                if i < len(execution.orders) - 1:
                    await asyncio.sleep(0.1)
            
            logger.info(f"✅ 所有訂單執行完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 執行訂單序列失敗: {e}")
            execution.error_message = str(e)
            return False
    
    async def _execute_single_order(self, order: OrderRequest) -> OrderResult:
        """執行單個訂單"""
        start_time = time.time()
        
        try:
            logger.debug(f"🔄 執行訂單: {order.action.upper()} {order.quantity:.4f} {order.pair} @ {order.exchange}")
            
            # 創建訂單結果
            result = OrderResult(
                order_id=order.order_id,
                request=order,
                status=ExecutionStatus.EXECUTING
            )
            
            # 模擬訂單執行
            success, execution_data = await self._simulate_order_execution(order)
            
            if success:
                result.status = ExecutionStatus.COMPLETED
                result.executed_quantity = execution_data['quantity']
                result.executed_price = execution_data['price']
                result.executed_value = result.executed_quantity * result.executed_price
                result.fees = execution_data['fees']
                result.slippage = execution_data['slippage']
                result.exchange_order_id = execution_data['exchange_order_id']
                
                logger.debug(f"   ✅ 訂單執行成功")
                logger.debug(f"      執行數量: {result.executed_quantity:.4f}")
                logger.debug(f"      執行價格: {result.executed_price:.2f}")
                logger.debug(f"      滑點: {result.slippage:.3%}")
                logger.debug(f"      手續費: {result.fees:.2f}")
                
            else:
                result.status = ExecutionStatus.FAILED
                result.error_message = execution_data.get('error', 'Unknown error')
                
                logger.debug(f"   ❌ 訂單執行失敗: {result.error_message}")
            
            # 計算執行時間
            result.execution_time = time.time() - start_time
            
            # 存儲訂單結果
            self.order_results[order.order_id] = result
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 執行單個訂單異常: {e}")
            
            result = OrderResult(
                order_id=order.order_id,
                request=order,
                status=ExecutionStatus.FAILED,
                error_message=str(e),
                execution_time=time.time() - start_time
            )
            
            return result
    
    async def _simulate_order_execution(self, order: OrderRequest) -> Tuple[bool, Dict[str, Any]]:
        """模擬訂單執行"""
        try:
            # 模擬執行延遲
            execution_delay = self.exchange_latency.get(order.exchange, 0.1)
            await asyncio.sleep(execution_delay)
            
            import random
            
            # 90%成功率
            success_rate = 0.9
            if random.random() > success_rate:
                return False, {'error': '訂單執行失敗 (模擬)'}
            
            # 模擬執行結果
            executed_quantity = order.quantity
            
            # 模擬滑點
            if order.order_type == OrderType.MARKET:
                slippage = random.uniform(-0.002, 0.005)  # 市價單滑點 -0.2% 到 +0.5%
            else:
                slippage = random.uniform(-0.001, 0.001)  # 限價單滑點較小
            
            # 計算執行價格
            if order.price:
                executed_price = order.price * (1 + slippage)
            else:
                # 模擬市場價格
                base_prices = {
                    "BTCTWD": 3500000,
                    "ETHTWD": 120000,
                    "USDTTWD": 31.5
                }
                base_price = base_prices.get(order.pair, 100000)
                executed_price = base_price * (1 + slippage)
            
            # 計算手續費
            fee_rate = self.exchange_fees.get(order.exchange, 0.001)  # 0.1%手續費
            fees = executed_quantity * executed_price * fee_rate
            
            # 生成交易所訂單ID
            exchange_order_id = f"{order.exchange}_{random.randint(100000, 999999)}"
            
            return True, {
                'quantity': executed_quantity,
                'price': executed_price,
                'fees': fees,
                'slippage': slippage,
                'exchange_order_id': exchange_order_id
            }
            
        except Exception as e:
            logger.error(f"❌ 模擬訂單執行失敗: {e}")
            return False, {'error': str(e)}
    
    async def _rollback_executed_orders(self, executed_results: List[OrderResult]):
        """回滾已執行的訂單"""
        try:
            logger.warning(f"🔄 開始回滾 {len(executed_results)} 個已執行訂單")
            
            # 反向執行已完成的訂單
            for result in reversed(executed_results):
                if result.status == ExecutionStatus.COMPLETED:
                    # 創建反向訂單
                    reverse_action = 'sell' if result.request.action == 'buy' else 'buy'
                    
                    reverse_order = OrderRequest(
                        order_id=f"rollback_{result.order_id}",
                        exchange=result.request.exchange,
                        pair=result.request.pair,
                        action=reverse_action,
                        order_type=OrderType.MARKET,  # 使用市價單快速執行
                        quantity=result.executed_quantity,
                        timeout=15  # 較短的超時時間
                    )
                    
                    logger.info(f"   回滾訂單: {reverse_action.upper()} {reverse_order.quantity:.4f} {reverse_order.pair}")
                    
                    # 執行回滾訂單
                    rollback_result = await self._execute_single_order(reverse_order)
                    
                    if rollback_result.status == ExecutionStatus.COMPLETED:
                        logger.info(f"   ✅ 回滾成功")
                    else:
                        logger.error(f"   ❌ 回滾失敗: {rollback_result.error_message}")
            
            logger.info(f"✅ 訂單回滾完成")
            
        except Exception as e:
            logger.error(f"❌ 回滾已執行訂單失敗: {e}")
    
    async def _execution_monitoring_loop(self):
        """執行監控循環"""
        while self.is_running:
            try:
                # 監控活躍執行
                await self._monitor_active_executions()
                
                # 等待下次監控
                await asyncio.sleep(self.config.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ 執行監控循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _market_monitoring_loop(self):
        """市場監控循環"""
        while self.is_running:
            try:
                # 更新市場條件
                await self._update_market_conditions()
                
                # 更新交易所信息
                await self._update_exchange_info()
                
                # 等待下次更新
                await asyncio.sleep(5.0)  # 每5秒更新一次
                
            except Exception as e:
                logger.error(f"❌ 市場監控循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _performance_monitoring_loop(self):
        """性能監控循環"""
        while self.is_running:
            try:
                # 更新執行統計
                self._update_execution_stats()
                
                # 清理過期數據
                await self._cleanup_expired_data()
                
                # 等待下次更新
                await asyncio.sleep(10.0)  # 每10秒更新一次
                
            except Exception as e:
                logger.error(f"❌ 性能監控循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _monitor_active_executions(self):
        """監控活躍執行"""
        try:
            current_time = datetime.now()
            timeout_executions = []
            
            for execution_id, execution in self.active_executions.items():
                # 檢查執行超時
                if execution.start_time:
                    execution_duration = (current_time - execution.start_time).total_seconds()
                    
                    if execution_duration > self.config.execution_timeout:
                        timeout_executions.append(execution_id)
                        execution.status = ExecutionStatus.TIMEOUT
                        execution.error_message = "執行超時"
                        execution.end_time = current_time
                        
                        logger.warning(f"⚠️ 套利執行超時: {execution_id}")
            
            # 處理超時執行
            for execution_id in timeout_executions:
                if execution_id in self.active_executions:
                    self.execution_history.append(self.active_executions[execution_id])
                    del self.active_executions[execution_id]
                    
                    self.execution_stats['timeout_executions'] += 1
            
        except Exception as e:
            logger.error(f"❌ 監控活躍執行失敗: {e}")
    
    async def _update_market_conditions(self):
        """更新市場條件"""
        try:
            # 模擬市場條件更新
            import random
            
            pairs = ["BTCTWD", "ETHTWD", "USDTTWD"]
            
            for pair in pairs:
                self.market_conditions[pair] = {
                    'volatility': random.uniform(0.005, 0.05),  # 0.5%-5%波動率
                    'liquidity': random.uniform(0.5, 2.0),     # 流動性指標
                    'spread': random.uniform(0.0005, 0.002),   # 點差
                    'volume': random.uniform(1000, 10000),     # 成交量
                    'timestamp': datetime.now()
                }
            
        except Exception as e:
            logger.error(f"❌ 更新市場條件失敗: {e}")
    
    async def _update_exchange_info(self):
        """更新交易所信息"""
        try:
            # 模擬交易所信息更新
            import random
            
            exchanges = ["binance", "max"]
            
            for exchange in exchanges:
                self.exchange_latency[exchange] = random.uniform(0.05, 0.3)  # 50-300ms延遲
                self.exchange_fees[exchange] = random.uniform(0.0005, 0.002)  # 0.05%-0.2%手續費
            
        except Exception as e:
            logger.error(f"❌ 更新交易所信息失敗: {e}")
    
    def _update_execution_stats(self):
        """更新執行統計"""
        try:
            total_executions = self.execution_stats['total_executions']
            
            if total_executions > 0:
                self.execution_stats['success_rate'] = (
                    self.execution_stats['successful_executions'] / total_executions
                )
            
            # 計算平均執行時間
            if self.execution_history:
                recent_executions = self.execution_history[-100:]  # 最近100次執行
                
                total_time = 0
                count = 0
                
                for execution in recent_executions:
                    if execution.start_time and execution.end_time:
                        duration = (execution.end_time - execution.start_time).total_seconds()
                        total_time += duration
                        count += 1
                
                if count > 0:
                    self.execution_stats['avg_execution_time'] = total_time / count
            
            # 計算平均滑點
            if self.order_results:
                recent_orders = list(self.order_results.values())[-100:]  # 最近100個訂單
                slippages = [order.slippage for order in recent_orders if order.slippage != 0]
                
                if slippages:
                    self.execution_stats['avg_slippage'] = sum(slippages) / len(slippages)
            
        except Exception as e:
            logger.error(f"❌ 更新執行統計失敗: {e}")
    
    async def _cleanup_expired_data(self):
        """清理過期數據"""
        try:
            # 清理過期的訂單結果 (保留最近1000個)
            if len(self.order_results) > 1000:
                # 按時間排序，保留最新的
                sorted_orders = sorted(
                    self.order_results.items(),
                    key=lambda x: x[1].timestamp,
                    reverse=True
                )
                
                # 保留最新的500個
                self.order_results = dict(sorted_orders[:500])
            
            # 清理過期的市場條件數據
            current_time = datetime.now()
            for pair in list(self.market_conditions.keys()):
                condition = self.market_conditions[pair]
                if 'timestamp' in condition:
                    age = (current_time - condition['timestamp']).total_seconds()
                    if age > 300:  # 5分鐘過期
                        del self.market_conditions[pair]
            
        except Exception as e:
            logger.error(f"❌ 清理過期數據失敗: {e}")
    
    async def _wait_for_executions_complete(self):
        """等待所有執行完成"""
        timeout = 60  # 60秒超時
        start_time = datetime.now()
        
        while self.active_executions and (datetime.now() - start_time).total_seconds() < timeout:
            logger.info(f"⏳ 等待 {len(self.active_executions)} 個套利執行完成...")
            await asyncio.sleep(1.0)
        
        if self.active_executions:
            logger.warning(f"⚠️ 仍有 {len(self.active_executions)} 個執行未完成，強制停止")
            
            # 強制移動到歷史記錄
            for execution in self.active_executions.values():
                execution.status = ExecutionStatus.CANCELLED
                execution.error_message = "引擎停止時強制終止"
                execution.end_time = datetime.now()
                self.execution_history.append(execution)
            
            self.active_executions.clear()
    
    # 公共接口方法
    
    def get_execution_status(self, execution_id: str) -> Optional[ArbitrageExecution]:
        """獲取執行狀態"""
        # 先檢查活躍執行
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]
        
        # 再檢查歷史記錄
        for execution in self.execution_history:
            if execution.execution_id == execution_id:
                return execution
        
        return None
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """獲取引擎統計"""
        return {
            'execution_stats': self.execution_stats.copy(),
            'active_executions': len(self.active_executions),
            'execution_history_count': len(self.execution_history),
            'order_results_count': len(self.order_results),
            'market_conditions': {
                pair: {
                    'volatility': condition['volatility'],
                    'liquidity': condition['liquidity'],
                    'spread': condition['spread']
                }
                for pair, condition in self.market_conditions.items()
            },
            'exchange_info': {
                'latency': self.exchange_latency.copy(),
                'fees': self.exchange_fees.copy()
            },
            'config': {
                'default_strategy': self.config.default_strategy.value,
                'max_concurrent_executions': self.config.max_concurrent_executions,
                'execution_timeout': self.config.execution_timeout,
                'max_slippage': self.config.max_slippage,
                'smart_routing': self.config.enable_smart_routing
            }
        }
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取執行歷史"""
        try:
            recent_executions = self.execution_history[-limit:] if limit > 0 else self.execution_history
            
            return [
                {
                    'execution_id': exec.execution_id,
                    'opportunity_id': exec.opportunity_id,
                    'strategy': exec.strategy.value,
                    'status': exec.status.value,
                    'orders_count': len(exec.orders),
                    'executed_orders': len(exec.execution_results),
                    'total_profit': exec.total_profit,
                    'total_fees': exec.total_fees,
                    'net_profit': exec.total_profit - exec.total_fees,
                    'execution_time': (exec.end_time - exec.start_time).total_seconds() if exec.start_time and exec.end_time else 0,
                    'error_message': exec.error_message,
                    'timestamp': exec.start_time.isoformat() if exec.start_time else None
                }
                for exec in recent_executions
            ]
            
        except Exception as e:
            logger.error(f"❌ 獲取執行歷史失敗: {e}")
            return []
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """取消執行"""
        try:
            if execution_id not in self.active_executions:
                logger.warning(f"⚠️ 執行不存在或已完成: {execution_id}")
                return False
            
            execution = self.active_executions[execution_id]
            execution.status = ExecutionStatus.CANCELLED
            execution.error_message = "用戶取消執行"
            execution.end_time = datetime.now()
            
            logger.info(f"🚫 取消套利執行: {execution_id}")
            
            # 移動到歷史記錄
            self.execution_history.append(execution)
            del self.active_executions[execution_id]
            
            self.execution_stats['cancelled_executions'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 取消執行失敗: {e}")
            return False


# 創建套利執行引擎實例
def create_arbitrage_execution_engine(config: ExecutionConfig) -> ArbitrageExecutionEngine:
    """創建套利執行引擎實例"""
    return ArbitrageExecutionEngine(config)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_execution_engine():
        """測試套利執行引擎"""
        print("🧪 測試套利執行引擎...")
        
        # 創建配置
        config = ExecutionConfig(
            default_strategy=ExecutionStrategy.ADAPTIVE,
            max_concurrent_executions=3,
            enable_smart_routing=True
        )
        
        # 創建引擎
        engine = create_arbitrage_execution_engine(config)
        
        try:
            # 模擬執行路徑
            execution_path = [
                {
                    'action': 'buy',
                    'exchange': 'binance',
                    'pair': 'BTCTWD',
                    'price': 3500000,
                    'volume': 0.001
                },
                {
                    'action': 'sell',
                    'exchange': 'max',
                    'pair': 'BTCTWD',
                    'price': 3505000,
                    'volume': 0.001
                }
            ]
            
            # 執行套利
            print(f"\n🚀 執行套利測試...")
            execution_id = await engine.execute_arbitrage(
                opportunity_id="test_opp_001",
                execution_path=execution_path,
                strategy=ExecutionStrategy.ADAPTIVE
            )
            
            print(f"   執行ID: {execution_id}")
            
            # 等待執行完成
            await asyncio.sleep(2)
            
            # 獲取執行狀態
            execution = engine.get_execution_status(execution_id)
            if execution:
                print(f"   執行狀態: {execution.status.value}")
                print(f"   總利潤: {execution.total_profit:.2f} TWD")
                print(f"   總手續費: {execution.total_fees:.2f} TWD")
                print(f"   淨利潤: {execution.total_profit - execution.total_fees:.2f} TWD")
            
            # 獲取引擎統計
            stats = engine.get_engine_stats()
            print(f"\n📊 引擎統計:")
            print(f"   總執行次數: {stats['execution_stats']['total_executions']}")
            print(f"   成功次數: {stats['execution_stats']['successful_executions']}")
            print(f"   成功率: {stats['execution_stats']['success_rate']:.1%}")
            print(f"   平均執行時間: {stats['execution_stats']['avg_execution_time']:.2f} 秒")
            
            # 獲取執行歷史
            history = engine.get_execution_history(5)
            print(f"\n📜 執行歷史:")
            for i, exec in enumerate(history, 1):
                print(f"   {i}. {exec['execution_id']}")
                print(f"      狀態: {exec['status']}")
                print(f"      淨利潤: {exec['net_profit']:.2f} TWD")
                print(f"      執行時間: {exec['execution_time']:.2f} 秒")
            
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
        
        print("🎉 套利執行引擎測試完成！")
    
    # 運行測試
    asyncio.run(test_execution_engine())