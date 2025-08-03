#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易執行器 - 將AI決策轉化為實際交易操作
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class OrderType(Enum):
    """訂單類型"""
    MARKET = "market"      # 市價單
    LIMIT = "limit"        # 限價單
    STOP_LOSS = "stop"     # 止損單

class OrderSide(Enum):
    """訂單方向"""
    BUY = "buy"
    SELL = "sell"

class OrderStatus(Enum):
    """訂單狀態"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    FAILED = "failed"

@dataclass
class TradingOrder:
    """交易訂單"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = None
    filled_at: Optional[datetime] = None
    filled_price: Optional[float] = None
    filled_quantity: Optional[float] = None
    ai_decision_id: Optional[str] = None
    reasoning: Optional[str] = None

@dataclass
class Position:
    """持倉信息"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None

@dataclass
class TradingAccount:
    """交易賬戶"""
    balance: float
    available_balance: float
    total_equity: float
    margin_used: float
    positions: List[Position]
    open_orders: List[TradingOrder]

class TradeExecutor:
    """交易執行器"""
    
    def __init__(self, initial_balance: float = 100000.0, max_position_size: float = 0.05):
        """
        初始化交易執行器
        
        Args:
            initial_balance: 初始資金 (TWD)
            max_position_size: 最大單筆交易佔總資金比例
        """
        self.account = TradingAccount(
            balance=initial_balance,
            available_balance=initial_balance,
            total_equity=initial_balance,
            margin_used=0.0,
            positions=[],
            open_orders=[]
        )
        
        self.max_position_size = max_position_size
        self.trade_history = []
        self.execution_stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'average_trade_time': 0.0
        }
        
        # 模擬交易設置
        self.simulation_mode = True  # 默認模擬模式
        self.slippage = 0.001  # 0.1% 滑點
        self.commission = 0.001  # 0.1% 手續費
        
        logger.info(f"🏦 交易執行器初始化完成，初始資金: {initial_balance:,.0f} TWD")
    
    async def execute_ai_decision(self, ai_decision: Dict[str, Any], 
                                market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行AI交易決策
        
        Args:
            ai_decision: AI決策結果
            market_data: 當前市場數據
            
        Returns:
            執行結果
        """
        try:
            decision_action = ai_decision.get('final_decision', 'HOLD')
            confidence = ai_decision.get('confidence', 0.0)
            reasoning = ai_decision.get('reasoning', '')
            
            logger.info(f"🤖 執行AI決策: {decision_action} (信心度: {confidence:.1%})")
            
            # 檢查是否應該執行交易
            if not self._should_execute_trade(decision_action, confidence, market_data):
                return {
                    'status': 'skipped',
                    'reason': '不滿足執行條件',
                    'decision': decision_action,
                    'confidence': confidence
                }
            
            # 根據決策類型執行相應操作
            if decision_action == 'BUY':
                result = await self._execute_buy_order(ai_decision, market_data)
            elif decision_action == 'SELL':
                result = await self._execute_sell_order(ai_decision, market_data)
            else:  # HOLD
                result = await self._execute_hold_action(ai_decision, market_data)
            
            # 更新統計
            self._update_execution_stats(result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 執行AI決策失敗: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'decision': decision_action
            }
    
    def _should_execute_trade(self, decision: str, confidence: float, 
                            market_data: Dict[str, Any]) -> bool:
        """判斷是否應該執行交易"""
        try:
            # 基本條件檢查
            if decision == 'HOLD':
                return True  # HOLD總是可以執行
            
            # 信心度檢查
            min_confidence = 0.6  # 最低信心度要求
            if confidence < min_confidence:
                logger.info(f"⚠️ 信心度過低: {confidence:.1%} < {min_confidence:.1%}")
                return False
            
            # 資金檢查
            if self.account.available_balance < 1000:  # 最低1000 TWD
                logger.warning("⚠️ 可用資金不足")
                return False
            
            # 持倉檢查
            current_positions = len(self.account.positions)
            max_positions = 3  # 最多同時持有3個倉位
            
            if decision == 'BUY' and current_positions >= max_positions:
                logger.info(f"⚠️ 持倉數量已達上限: {current_positions}/{max_positions}")
                return False
            
            if decision == 'SELL' and current_positions == 0:
                logger.info("⚠️ 無持倉可賣出")
                return False
            
            # 市場條件檢查
            current_price = market_data.get('current_price', 0)
            if current_price <= 0:
                logger.error("❌ 無效的市場價格")
                return False
            
            # 波動率檢查
            volatility = market_data.get('volatility_level', 'medium')
            if volatility == '高' and confidence < 0.8:
                logger.info("⚠️ 高波動市場需要更高信心度")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 交易條件檢查失敗: {e}")
            return False
    
    async def _execute_buy_order(self, ai_decision: Dict[str, Any], 
                               market_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行買入訂單"""
        try:
            current_price = market_data['current_price']
            confidence = ai_decision.get('confidence', 0.0)
            
            # 計算交易數量
            position_size = self._calculate_position_size(confidence, current_price)
            
            if position_size <= 0:
                return {
                    'status': 'failed',
                    'reason': '計算的交易數量無效',
                    'position_size': position_size
                }
            
            # 創建買入訂單
            order = TradingOrder(
                order_id=f"BUY_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                symbol="BTCTWD",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=position_size,
                ai_decision_id=ai_decision.get('decision_id'),
                reasoning=ai_decision.get('reasoning', '')
            )
            
            # 模擬執行訂單
            execution_result = await self._simulate_order_execution(order, current_price)
            
            if execution_result['status'] == 'filled':
                # 創建持倉
                position = Position(
                    symbol="BTCTWD",
                    quantity=execution_result['filled_quantity'],
                    entry_price=execution_result['filled_price'],
                    current_price=current_price,
                    unrealized_pnl=0.0,
                    realized_pnl=0.0,
                    entry_time=datetime.now(),
                    stop_loss=self._calculate_stop_loss(execution_result['filled_price'], 'BUY'),
                    take_profit=self._calculate_take_profit(execution_result['filled_price'], 'BUY')
                )
                
                self.account.positions.append(position)
                self._update_account_balance(execution_result)
                
                logger.info(f"✅ 買入成功: {execution_result['filled_quantity']:.6f} BTC @ {execution_result['filled_price']:,.0f} TWD")
            
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ 執行買入訂單失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _execute_sell_order(self, ai_decision: Dict[str, Any], 
                                market_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行賣出訂單"""
        try:
            if not self.account.positions:
                return {
                    'status': 'failed',
                    'reason': '無持倉可賣出'
                }
            
            current_price = market_data['current_price']
            
            # 選擇要賣出的持倉（這裡簡化為賣出第一個）
            position = self.account.positions[0]
            
            # 創建賣出訂單
            order = TradingOrder(
                order_id=f"SELL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                symbol="BTCTWD",
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=position.quantity,
                ai_decision_id=ai_decision.get('decision_id'),
                reasoning=ai_decision.get('reasoning', '')
            )
            
            # 模擬執行訂單
            execution_result = await self._simulate_order_execution(order, current_price)
            
            if execution_result['status'] == 'filled':
                # 計算盈虧
                pnl = (execution_result['filled_price'] - position.entry_price) * position.quantity
                pnl_after_commission = pnl - (execution_result['filled_price'] * position.quantity * self.commission)
                
                # 移除持倉
                self.account.positions.remove(position)
                self._update_account_balance(execution_result, pnl_after_commission)
                
                execution_result['pnl'] = pnl_after_commission
                execution_result['return_rate'] = pnl_after_commission / (position.entry_price * position.quantity)
                
                logger.info(f"✅ 賣出成功: {execution_result['filled_quantity']:.6f} BTC @ {execution_result['filled_price']:,.0f} TWD")
                logger.info(f"💰 盈虧: {pnl_after_commission:+,.0f} TWD ({execution_result['return_rate']:+.2%})")
            
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ 執行賣出訂單失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _execute_hold_action(self, ai_decision: Dict[str, Any], 
                                 market_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行持有操作"""
        try:
            current_price = market_data['current_price']
            
            # 更新現有持倉的未實現盈虧
            for position in self.account.positions:
                position.current_price = current_price
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
            
            # 檢查是否需要止損或止盈
            stop_loss_triggered = []
            take_profit_triggered = []
            
            for position in self.account.positions:
                if position.stop_loss and current_price <= position.stop_loss:
                    stop_loss_triggered.append(position)
                elif position.take_profit and current_price >= position.take_profit:
                    take_profit_triggered.append(position)
            
            result = {
                'status': 'hold',
                'action': 'HOLD',
                'current_price': current_price,
                'positions_count': len(self.account.positions),
                'total_unrealized_pnl': sum(p.unrealized_pnl for p in self.account.positions),
                'stop_loss_triggered': len(stop_loss_triggered),
                'take_profit_triggered': len(take_profit_triggered)
            }
            
            # 執行自動止損/止盈
            if stop_loss_triggered or take_profit_triggered:
                auto_trades = []
                
                for position in stop_loss_triggered + take_profit_triggered:
                    auto_sell_result = await self._execute_auto_sell(position, current_price, 
                                                                   'stop_loss' if position in stop_loss_triggered else 'take_profit')
                    auto_trades.append(auto_sell_result)
                
                result['auto_trades'] = auto_trades
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 執行持有操作失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _simulate_order_execution(self, order: TradingOrder, 
                                      market_price: float) -> Dict[str, Any]:
        """模擬訂單執行"""
        try:
            # 模擬執行延遲
            await asyncio.sleep(0.1)
            
            # 計算滑點
            if order.side == OrderSide.BUY:
                execution_price = market_price * (1 + self.slippage)
            else:
                execution_price = market_price * (1 - self.slippage)
            
            # 計算手續費
            commission_amount = execution_price * order.quantity * self.commission
            
            # 更新訂單狀態
            order.status = OrderStatus.FILLED
            order.filled_at = datetime.now()
            order.filled_price = execution_price
            order.filled_quantity = order.quantity
            
            result = {
                'status': 'filled',
                'order_id': order.order_id,
                'symbol': order.symbol,
                'side': order.side.value,
                'filled_quantity': order.quantity,
                'filled_price': execution_price,
                'commission': commission_amount,
                'total_cost': execution_price * order.quantity + commission_amount,
                'execution_time': order.filled_at,
                'slippage': abs(execution_price - market_price) / market_price
            }
            
            # 記錄交易歷史
            self.trade_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 模擬訂單執行失敗: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    def _calculate_position_size(self, confidence: float, price: float) -> float:
        """計算交易數量"""
        try:
            # 基於信心度調整倉位大小
            base_position_ratio = self.max_position_size
            confidence_multiplier = min(confidence / 0.6, 1.5)  # 信心度越高，倉位越大
            
            position_ratio = base_position_ratio * confidence_multiplier
            position_value = self.account.available_balance * position_ratio
            
            # 計算BTC數量
            btc_quantity = position_value / price
            
            # 確保最小交易量
            min_quantity = 0.001  # 最小0.001 BTC
            btc_quantity = max(btc_quantity, min_quantity)
            
            logger.info(f"💰 計算倉位: {position_value:,.0f} TWD = {btc_quantity:.6f} BTC")
            
            return btc_quantity
            
        except Exception as e:
            logger.error(f"❌ 計算倉位大小失敗: {e}")
            return 0.0
    
    def _calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """計算止損價格"""
        stop_loss_ratio = 0.02  # 2%止損
        
        if side == 'BUY':
            return entry_price * (1 - stop_loss_ratio)
        else:
            return entry_price * (1 + stop_loss_ratio)
    
    def _calculate_take_profit(self, entry_price: float, side: str) -> float:
        """計算止盈價格"""
        take_profit_ratio = 0.05  # 5%止盈
        
        if side == 'BUY':
            return entry_price * (1 + take_profit_ratio)
        else:
            return entry_price * (1 - take_profit_ratio)
    
    def _update_account_balance(self, execution_result: Dict[str, Any], pnl: float = 0.0):
        """更新賬戶餘額"""
        try:
            if execution_result['side'] == 'buy':
                # 買入：減少可用餘額
                cost = execution_result['total_cost']
                self.account.available_balance -= cost
                self.account.margin_used += cost
            else:
                # 賣出：增加可用餘額
                proceeds = execution_result['filled_price'] * execution_result['filled_quantity']
                commission = execution_result['commission']
                net_proceeds = proceeds - commission + pnl
                
                self.account.available_balance += net_proceeds
                self.account.margin_used -= (execution_result['filled_price'] * execution_result['filled_quantity'])
            
            # 更新總權益
            unrealized_pnl = sum(p.unrealized_pnl for p in self.account.positions)
            self.account.total_equity = self.account.balance + unrealized_pnl
            
        except Exception as e:
            logger.error(f"❌ 更新賬戶餘額失敗: {e}")
    
    async def _execute_auto_sell(self, position: Position, current_price: float, 
                               reason: str) -> Dict[str, Any]:
        """執行自動賣出（止損/止盈）"""
        try:
            order = TradingOrder(
                order_id=f"AUTO_{reason.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                symbol=position.symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=position.quantity,
                reasoning=f"自動{reason}"
            )
            
            execution_result = await self._simulate_order_execution(order, current_price)
            
            if execution_result['status'] == 'filled':
                # 計算盈虧
                pnl = (execution_result['filled_price'] - position.entry_price) * position.quantity
                pnl_after_commission = pnl - execution_result['commission']
                
                # 移除持倉
                self.account.positions.remove(position)
                self._update_account_balance(execution_result, pnl_after_commission)
                
                execution_result['pnl'] = pnl_after_commission
                execution_result['reason'] = reason
                
                logger.info(f"🛡️ 自動{reason}: {execution_result['filled_quantity']:.6f} BTC @ {execution_result['filled_price']:,.0f} TWD")
                logger.info(f"💰 盈虧: {pnl_after_commission:+,.0f} TWD")
            
            return execution_result
            
        except Exception as e:
            logger.error(f"❌ 執行自動賣出失敗: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _update_execution_stats(self, result: Dict[str, Any]):
        """更新執行統計"""
        try:
            self.execution_stats['total_trades'] += 1
            
            if result['status'] in ['filled', 'hold']:
                self.execution_stats['successful_trades'] += 1
            else:
                self.execution_stats['failed_trades'] += 1
            
            # 更新勝率
            if self.execution_stats['total_trades'] > 0:
                self.execution_stats['win_rate'] = (
                    self.execution_stats['successful_trades'] / 
                    self.execution_stats['total_trades']
                )
            
            # 更新總盈虧
            if 'pnl' in result:
                self.execution_stats['total_pnl'] += result['pnl']
            
        except Exception as e:
            logger.error(f"❌ 更新執行統計失敗: {e}")
    
    def get_account_status(self) -> Dict[str, Any]:
        """獲取賬戶狀態"""
        try:
            total_unrealized_pnl = sum(p.unrealized_pnl for p in self.account.positions)
            
            return {
                'balance': self.account.balance,
                'available_balance': self.account.available_balance,
                'total_equity': self.account.balance + total_unrealized_pnl,
                'margin_used': self.account.margin_used,
                'unrealized_pnl': total_unrealized_pnl,
                'positions_count': len(self.account.positions),
                'open_orders_count': len(self.account.open_orders),
                'execution_stats': self.execution_stats.copy()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取賬戶狀態失敗: {e}")
            return {}
    
    def get_positions_summary(self) -> List[Dict[str, Any]]:
        """獲取持倉摘要"""
        try:
            positions_summary = []
            
            for position in self.account.positions:
                summary = {
                    'symbol': position.symbol,
                    'quantity': position.quantity,
                    'entry_price': position.entry_price,
                    'current_price': position.current_price,
                    'unrealized_pnl': position.unrealized_pnl,
                    'unrealized_return': position.unrealized_pnl / (position.entry_price * position.quantity),
                    'entry_time': position.entry_time,
                    'holding_duration': datetime.now() - position.entry_time,
                    'stop_loss': position.stop_loss,
                    'take_profit': position.take_profit
                }
                positions_summary.append(summary)
            
            return positions_summary
            
        except Exception as e:
            logger.error(f"❌ 獲取持倉摘要失敗: {e}")
            return []


# 創建全局交易執行器實例
def create_trade_executor(initial_balance: float = 100000.0) -> TradeExecutor:
    """創建交易執行器實例"""
    return TradeExecutor(initial_balance)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_trade_executor():
        """測試交易執行器"""
        print("🧪 測試交易執行器...")
        
        executor = create_trade_executor(100000.0)
        
        # 模擬AI決策
        ai_decision = {
            'final_decision': 'BUY',
            'confidence': 0.75,
            'reasoning': '技術指標顯示買入信號',
            'decision_id': 'test_001'
        }
        
        # 模擬市場數據
        market_data = {
            'current_price': 1500000,
            'volatility_level': '中'
        }
        
        # 執行交易
        result = await executor.execute_ai_decision(ai_decision, market_data)
        
        print(f"✅ 交易執行結果: {result}")
        
        # 顯示賬戶狀態
        account_status = executor.get_account_status()
        print(f"💰 賬戶狀態: {account_status}")
        
        # 顯示持倉
        positions = executor.get_positions_summary()
        print(f"📊 持倉摘要: {positions}")
    
    # 運行測試
    asyncio.run(test_trade_executor())