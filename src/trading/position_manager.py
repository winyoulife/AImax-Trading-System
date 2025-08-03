#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
倉位管理器 - 智能倉位管理和止損機制
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PositionStatus(Enum):
    """倉位狀態"""
    ACTIVE = "active"
    CLOSED = "closed"
    STOPPED = "stopped"

@dataclass
class PositionInfo:
    """倉位信息"""
    position_id: str
    symbol: str
    side: str  # BUY/SELL
    quantity: float
    entry_price: float
    current_price: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    status: PositionStatus = PositionStatus.ACTIVE
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    max_profit: float = 0.0
    max_loss: float = 0.0
    ai_decision_id: Optional[str] = None

class PositionManager:
    """倉位管理器"""
    
    def __init__(self):
        """初始化倉位管理器"""
        self.positions: List[PositionInfo] = []
        self.closed_positions: List[PositionInfo] = []
        
        # 倉位管理配置
        self.config = {
            'default_stop_loss': 0.02,      # 2%止損
            'default_take_profit': 0.05,    # 5%止盈
            'trailing_stop_ratio': 0.015,   # 1.5%追蹤止損
            'max_holding_time': 24,         # 最大持倉24小時
            'position_size_limit': 0.05,    # 單倉位最大5%
            'total_exposure_limit': 0.30    # 總暴露最大30%
        }
        
        # 統計信息
        self.stats = {
            'total_positions': 0,
            'profitable_positions': 0,
            'loss_positions': 0,
            'avg_holding_time': 0.0,
            'avg_profit': 0.0,
            'avg_loss': 0.0,
            'win_rate': 0.0,
            'total_pnl': 0.0
        }
        
        logger.info("📊 倉位管理器初始化完成")
    
    def create_position(self, trade_result: Dict[str, Any], 
                       ai_decision: Dict[str, Any]) -> PositionInfo:
        """創建新倉位"""
        try:
            position = PositionInfo(
                position_id=f"POS_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.positions)}",
                symbol=trade_result.get('symbol', 'BTCTWD'),
                side=trade_result.get('side', 'buy'),
                quantity=trade_result.get('filled_quantity', 0),
                entry_price=trade_result.get('filled_price', 0),
                current_price=trade_result.get('filled_price', 0),
                entry_time=datetime.now(),
                ai_decision_id=ai_decision.get('decision_id')
            )
            
            # 設置止損止盈
            self._set_stop_loss_take_profit(position)
            
            # 添加到活躍倉位
            self.positions.append(position)
            self.stats['total_positions'] += 1
            
            logger.info(f"📈 創建倉位: {position.position_id} - {position.side} {position.quantity:.6f} @ {position.entry_price:,.0f}")
            
            return position
            
        except Exception as e:
            logger.error(f"❌ 創建倉位失敗: {e}")
            raise
    
    def update_positions(self, current_price: float) -> List[Dict[str, Any]]:
        """更新所有倉位"""
        try:
            actions = []
            
            for position in self.positions.copy():
                # 更新當前價格和盈虧
                position.current_price = current_price
                self._update_position_pnl(position)
                
                # 檢查止損止盈條件
                action = self._check_exit_conditions(position)
                if action:
                    actions.append(action)
                
                # 更新追蹤止損
                self._update_trailing_stop(position)
                
                # 檢查最大持倉時間
                if self._should_close_by_time(position):
                    actions.append({
                        'action': 'close_position',
                        'position': position,
                        'reason': 'max_holding_time',
                        'price': current_price
                    })
            
            return actions
            
        except Exception as e:
            logger.error(f"❌ 更新倉位失敗: {e}")
            return []    

    def close_position(self, position: PositionInfo, close_price: float, 
                      reason: str = "manual") -> Dict[str, Any]:
        """關閉倉位"""
        try:
            # 計算最終盈虧
            if position.side.lower() == 'buy':
                pnl = (close_price - position.entry_price) * position.quantity
            else:
                pnl = (position.entry_price - close_price) * position.quantity
            
            position.realized_pnl = pnl
            position.status = PositionStatus.CLOSED
            
            # 從活躍倉位移除
            if position in self.positions:
                self.positions.remove(position)
            
            # 添加到已關閉倉位
            self.closed_positions.append(position)
            
            # 更新統計
            self._update_stats(position)
            
            close_result = {
                'position_id': position.position_id,
                'symbol': position.symbol,
                'side': position.side,
                'quantity': position.quantity,
                'entry_price': position.entry_price,
                'close_price': close_price,
                'pnl': pnl,
                'return_rate': pnl / (position.entry_price * position.quantity),
                'holding_time': datetime.now() - position.entry_time,
                'reason': reason
            }
            
            logger.info(f"📉 關閉倉位: {position.position_id} - 盈虧: {pnl:+,.0f} TWD ({close_result['return_rate']:+.2%})")
            
            return close_result
            
        except Exception as e:
            logger.error(f"❌ 關閉倉位失敗: {e}")
            return {}
    
    def _set_stop_loss_take_profit(self, position: PositionInfo):
        """設置止損止盈"""
        try:
            if position.side.lower() == 'buy':
                # 買入倉位
                position.stop_loss = position.entry_price * (1 - self.config['default_stop_loss'])
                position.take_profit = position.entry_price * (1 + self.config['default_take_profit'])
            else:
                # 賣出倉位
                position.stop_loss = position.entry_price * (1 + self.config['default_stop_loss'])
                position.take_profit = position.entry_price * (1 - self.config['default_take_profit'])
            
            # 設置追蹤止損
            position.trailing_stop = position.stop_loss
            
        except Exception as e:
            logger.error(f"❌ 設置止損止盈失敗: {e}")
    
    def _update_position_pnl(self, position: PositionInfo):
        """更新倉位盈虧"""
        try:
            if position.side.lower() == 'buy':
                pnl = (position.current_price - position.entry_price) * position.quantity
            else:
                pnl = (position.entry_price - position.current_price) * position.quantity
            
            position.unrealized_pnl = pnl
            
            # 更新最大盈利和最大虧損
            position.max_profit = max(position.max_profit, pnl)
            position.max_loss = min(position.max_loss, pnl)
            
        except Exception as e:
            logger.error(f"❌ 更新倉位盈虧失敗: {e}")
    
    def _check_exit_conditions(self, position: PositionInfo) -> Optional[Dict[str, Any]]:
        """檢查退出條件"""
        try:
            current_price = position.current_price
            
            # 檢查止損
            if position.side.lower() == 'buy' and current_price <= position.stop_loss:
                return {
                    'action': 'close_position',
                    'position': position,
                    'reason': 'stop_loss',
                    'price': current_price
                }
            elif position.side.lower() == 'sell' and current_price >= position.stop_loss:
                return {
                    'action': 'close_position',
                    'position': position,
                    'reason': 'stop_loss',
                    'price': current_price
                }
            
            # 檢查止盈
            if position.side.lower() == 'buy' and current_price >= position.take_profit:
                return {
                    'action': 'close_position',
                    'position': position,
                    'reason': 'take_profit',
                    'price': current_price
                }
            elif position.side.lower() == 'sell' and current_price <= position.take_profit:
                return {
                    'action': 'close_position',
                    'position': position,
                    'reason': 'take_profit',
                    'price': current_price
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 檢查退出條件失敗: {e}")
            return None
    
    def _update_trailing_stop(self, position: PositionInfo):
        """更新追蹤止損"""
        try:
            if not position.trailing_stop:
                return
            
            current_price = position.current_price
            trailing_ratio = self.config['trailing_stop_ratio']
            
            if position.side.lower() == 'buy':
                # 買入倉位：價格上漲時提高止損線
                new_trailing_stop = current_price * (1 - trailing_ratio)
                if new_trailing_stop > position.trailing_stop:
                    position.trailing_stop = new_trailing_stop
                    position.stop_loss = new_trailing_stop
            else:
                # 賣出倉位：價格下跌時降低止損線
                new_trailing_stop = current_price * (1 + trailing_ratio)
                if new_trailing_stop < position.trailing_stop:
                    position.trailing_stop = new_trailing_stop
                    position.stop_loss = new_trailing_stop
            
        except Exception as e:
            logger.error(f"❌ 更新追蹤止損失敗: {e}")
    
    def _should_close_by_time(self, position: PositionInfo) -> bool:
        """檢查是否應該按時間關閉倉位"""
        try:
            holding_time = datetime.now() - position.entry_time
            max_holding_time = timedelta(hours=self.config['max_holding_time'])
            
            return holding_time >= max_holding_time
            
        except Exception as e:
            logger.error(f"❌ 檢查時間關閉條件失敗: {e}")
            return False
    
    def _update_stats(self, position: PositionInfo):
        """更新統計信息"""
        try:
            if position.realized_pnl > 0:
                self.stats['profitable_positions'] += 1
                self.stats['avg_profit'] = (
                    (self.stats['avg_profit'] * (self.stats['profitable_positions'] - 1) + position.realized_pnl) /
                    self.stats['profitable_positions']
                )
            else:
                self.stats['loss_positions'] += 1
                self.stats['avg_loss'] = (
                    (self.stats['avg_loss'] * (self.stats['loss_positions'] - 1) + position.realized_pnl) /
                    self.stats['loss_positions']
                )
            
            # 更新勝率
            total_closed = self.stats['profitable_positions'] + self.stats['loss_positions']
            if total_closed > 0:
                self.stats['win_rate'] = self.stats['profitable_positions'] / total_closed
            
            # 更新總盈虧
            self.stats['total_pnl'] += position.realized_pnl
            
            # 更新平均持倉時間
            holding_time_hours = (datetime.now() - position.entry_time).total_seconds() / 3600
            self.stats['avg_holding_time'] = (
                (self.stats['avg_holding_time'] * (total_closed - 1) + holding_time_hours) /
                total_closed
            )
            
        except Exception as e:
            logger.error(f"❌ 更新統計信息失敗: {e}")
    
    def get_active_positions(self) -> List[Dict[str, Any]]:
        """獲取活躍倉位摘要"""
        try:
            positions_summary = []
            
            for position in self.positions:
                summary = {
                    'position_id': position.position_id,
                    'symbol': position.symbol,
                    'side': position.side,
                    'quantity': position.quantity,
                    'entry_price': position.entry_price,
                    'current_price': position.current_price,
                    'unrealized_pnl': position.unrealized_pnl,
                    'unrealized_return': position.unrealized_pnl / (position.entry_price * position.quantity),
                    'entry_time': position.entry_time,
                    'holding_duration': datetime.now() - position.entry_time,
                    'stop_loss': position.stop_loss,
                    'take_profit': position.take_profit,
                    'trailing_stop': position.trailing_stop,
                    'max_profit': position.max_profit,
                    'max_loss': position.max_loss
                }
                positions_summary.append(summary)
            
            return positions_summary
            
        except Exception as e:
            logger.error(f"❌ 獲取活躍倉位失敗: {e}")
            return []
    
    def get_position_stats(self) -> Dict[str, Any]:
        """獲取倉位統計"""
        try:
            total_unrealized_pnl = sum(p.unrealized_pnl for p in self.positions)
            
            return {
                'active_positions': len(self.positions),
                'total_positions': self.stats['total_positions'],
                'profitable_positions': self.stats['profitable_positions'],
                'loss_positions': self.stats['loss_positions'],
                'win_rate': self.stats['win_rate'],
                'avg_profit': self.stats['avg_profit'],
                'avg_loss': self.stats['avg_loss'],
                'total_realized_pnl': self.stats['total_pnl'],
                'total_unrealized_pnl': total_unrealized_pnl,
                'total_pnl': self.stats['total_pnl'] + total_unrealized_pnl,
                'avg_holding_time_hours': self.stats['avg_holding_time']
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取倉位統計失敗: {e}")
            return {}
    
    def adjust_position_size(self, confidence: float, market_volatility: str) -> float:
        """根據信心度和市場波動調整倉位大小"""
        try:
            base_size = self.config['position_size_limit']
            
            # 信心度調整
            confidence_multiplier = min(confidence / 0.6, 1.5)
            
            # 波動率調整
            volatility_multiplier = {
                '低': 1.2,
                '中': 1.0,
                '高': 0.7
            }.get(market_volatility, 1.0)
            
            # 當前倉位數量調整
            position_count_multiplier = max(0.5, 1.0 - len(self.positions) * 0.1)
            
            adjusted_size = base_size * confidence_multiplier * volatility_multiplier * position_count_multiplier
            
            return min(adjusted_size, self.config['position_size_limit'])
            
        except Exception as e:
            logger.error(f"❌ 調整倉位大小失敗: {e}")
            return self.config['position_size_limit']


# 創建全局倉位管理器實例
def create_position_manager() -> PositionManager:
    """創建倉位管理器實例"""
    return PositionManager()


# 測試代碼
if __name__ == "__main__":
    print("🧪 測試倉位管理器...")
    
    position_manager = create_position_manager()
    
    # 模擬交易結果
    trade_result = {
        'symbol': 'BTCTWD',
        'side': 'buy',
        'filled_quantity': 0.01,
        'filled_price': 1500000
    }
    
    # 模擬AI決策
    ai_decision = {
        'decision_id': 'test_001',
        'confidence': 0.75
    }
    
    # 創建倉位
    position = position_manager.create_position(trade_result, ai_decision)
    print(f"✅ 創建倉位: {position.position_id}")
    
    # 更新倉位（模擬價格變化）
    actions = position_manager.update_positions(1520000)  # 價格上漲
    print(f"📊 倉位更新動作: {len(actions)}")
    
    # 獲取活躍倉位
    active_positions = position_manager.get_active_positions()
    print(f"📈 活躍倉位: {len(active_positions)}")
    
    # 獲取統計信息
    stats = position_manager.get_position_stats()
    print(f"📊 倉位統計: {stats}")