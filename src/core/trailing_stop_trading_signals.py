#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移動停利停損交易信號系統
結合MACD買進信號和移動停損賣出策略
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class TrailingStopTradingSignals:
    """移動停利停損交易信號系統"""
    
    def __init__(self, 
                 stop_loss_pct: float = 0.05,      # 停損比例 5%
                 profit_trigger_pct: float = 0.03,  # 啟動移動停損的獲利比例 3%
                 trailing_pct: float = 0.02):       # 移動停損幅度 2%
        
        self.stop_loss_pct = stop_loss_pct
        self.profit_trigger_pct = profit_trigger_pct
        self.trailing_pct = trailing_pct
        
        # 交易狀態
        self.current_position = 0  # 0=空倉, 1=持倉
        self.trade_sequence = 0
        self.buy_count = 0
        self.sell_count = 0
        
        # 持倉信息
        self.buy_price = 0.0
        self.highest_price = 0.0
        self.stop_loss_price = 0.0
        self.trailing_active = False
        
        # 交易記錄
        self.open_trades = []
        self.trade_pairs = []
        self.trade_history = []
    
    def can_buy(self) -> bool:
        """檢查是否可以買進"""
        return self.current_position == 0
    
    def can_sell(self) -> bool:
        """檢查是否可以賣出"""
        return self.current_position == 1
    
    def execute_buy(self, timestamp: datetime, price: float) -> int:
        """執行買進操作"""
        if not self.can_buy():
            return 0
        
        self.current_position = 1
        self.buy_count += 1
        self.trade_sequence += 1
        
        # 設定持倉信息
        self.buy_price = price
        self.highest_price = price
        self.stop_loss_price = price * (1 - self.stop_loss_pct)  # 初始停損點
        self.trailing_active = False
        
        # 記錄交易
        trade_record = {
            'type': 'buy',
            'sequence': self.trade_sequence,
            'timestamp': timestamp,
            'price': price,
            'stop_loss_price': self.stop_loss_price
        }
        
        self.open_trades.append(trade_record)
        self.trade_history.append(trade_record)
        
        logger.info(f"執行買進: 買{self.trade_sequence}, 價格: {price:.0f}, 停損: {self.stop_loss_price:.0f}")
        return self.trade_sequence
    
    def update_trailing_stop(self, current_price: float) -> Dict:
        """更新移動停損"""
        if not self.can_sell():
            return {}
        
        # 更新最高價
        if current_price > self.highest_price:
            self.highest_price = current_price
        
        # 計算當前獲利比例
        profit_pct = (current_price - self.buy_price) / self.buy_price
        
        # 檢查是否啟動移動停損
        if profit_pct >= self.profit_trigger_pct:
            self.trailing_active = True
            # 更新移動停損點
            new_stop_loss = self.highest_price * (1 - self.trailing_pct)
            if new_stop_loss > self.stop_loss_price:
                self.stop_loss_price = new_stop_loss
        
        return {
            'current_price': current_price,
            'buy_price': self.buy_price,
            'highest_price': self.highest_price,
            'stop_loss_price': self.stop_loss_price,
            'trailing_active': self.trailing_active,
            'profit_pct': profit_pct * 100,
            'unrealized_profit': current_price - self.buy_price
        }
    
    def check_stop_loss(self, current_price: float) -> bool:
        """檢查是否觸發停損"""
        if not self.can_sell():
            return False
        
        return current_price <= self.stop_loss_price
    
    def execute_sell(self, timestamp: datetime, price: float, reason: str = "MACD") -> int:
        """執行賣出操作"""
        if not self.can_sell():
            return 0
        
        self.current_position = 0
        self.sell_count += 1
        
        # 配對交易
        if self.open_trades:
            buy_trade = self.open_trades.pop()
            profit = price - buy_trade['price']
            profit_pct = (profit / buy_trade['price']) * 100
            
            trade_pair = {
                'buy_sequence': buy_trade['sequence'],
                'sell_sequence': buy_trade['sequence'],
                'buy_time': buy_trade['timestamp'],
                'sell_time': timestamp,
                'buy_price': buy_trade['price'],
                'sell_price': price,
                'profit': profit,
                'profit_pct': profit_pct,
                'sell_reason': reason,
                'highest_price': self.highest_price,
                'stop_loss_triggered': reason == "STOP_LOSS"
            }
            self.trade_pairs.append(trade_pair)
            
            sell_record = {
                'type': 'sell',
                'sequence': buy_trade['sequence'],
                'timestamp': timestamp,
                'price': price,
                'reason': reason,
                'profit': profit,
                'profit_pct': profit_pct
            }
            self.trade_history.append(sell_record)
            
            logger.info(f"執行賣出: 賣{buy_trade['sequence']}, 價格: {price:.0f}, "
                       f"利潤: {profit:.0f} ({profit_pct:+.2f}%), 原因: {reason}")
            
            # 重置持倉信息
            self.buy_price = 0.0
            self.highest_price = 0.0
            self.stop_loss_price = 0.0
            self.trailing_active = False
            
            return buy_trade['sequence']
        
        return 0
    
    def detect_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """檢測交易信號（結合MACD買進和移動停損賣出）"""
        if len(df) < 2:
            return df
        
        # 初始化信號欄位
        df = df.copy()
        df['trading_signal'] = '⚪ 持有'
        df['signal_type'] = 'hold'
        df['trade_sequence'] = 0
        df['position_status'] = '空倉'
        df['stop_loss_price'] = 0.0
        df['trailing_active'] = False
        df['profit_pct'] = 0.0
        df['sell_reason'] = ''
        
        # 重置狀態
        self.current_position = 0
        self.trade_sequence = 0
        self.buy_count = 0
        self.sell_count = 0
        self.open_trades = []
        self.trade_pairs = []
        self.trade_history = []
        
        # 逐行處理
        for i in range(1, len(df)):
            current_row = df.iloc[i]
            previous_row = df.iloc[i-1]
            current_price = current_row['close']
            
            # 檢查買進信號（MACD金叉）
            if (self.can_buy() and 
                self._validate_buy_signal(current_row, previous_row)):
                
                sequence = self.execute_buy(current_row['datetime'], current_price)
                df.at[i, 'trading_signal'] = f'🟢 買{sequence}'
                df.at[i, 'signal_type'] = 'buy'
                df.at[i, 'trade_sequence'] = sequence
            
            # 更新移動停損（如果持倉）
            elif self.can_sell():
                trailing_info = self.update_trailing_stop(current_price)
                
                # 檢查賣出條件
                sell_reason = None
                
                # 1. 檢查移動停損
                if self.check_stop_loss(current_price):
                    sell_reason = "STOP_LOSS"
                
                # 2. 檢查MACD死叉（只有在沒有觸發停損時才考慮）
                elif self._validate_sell_signal(current_row, previous_row):
                    sell_reason = "MACD"
                
                # 執行賣出
                if sell_reason:
                    sequence = self.execute_sell(current_row['datetime'], current_price, sell_reason)
                    
                    emoji = "🛑" if sell_reason == "STOP_LOSS" else "🔴"
                    reason_text = "停損" if sell_reason == "STOP_LOSS" else "MACD"
                    
                    df.at[i, 'trading_signal'] = f'{emoji} 賣{sequence}({reason_text})'
                    df.at[i, 'signal_type'] = 'sell'
                    df.at[i, 'trade_sequence'] = sequence
                    df.at[i, 'sell_reason'] = sell_reason
                
                # 更新持倉信息到DataFrame
                if trailing_info:
                    df.at[i, 'stop_loss_price'] = trailing_info['stop_loss_price']
                    df.at[i, 'trailing_active'] = trailing_info['trailing_active']
                    df.at[i, 'profit_pct'] = trailing_info['profit_pct']
            
            # 更新持倉狀態
            df.at[i, 'position_status'] = '持倉' if self.current_position == 1 else '空倉'
        
        return df
    
    def _validate_buy_signal(self, current_row: pd.Series, previous_row: pd.Series) -> bool:
        """驗證MACD買進信號"""
        try:
            # MACD金叉條件
            return (previous_row['macd_hist'] < 0 and 
                   previous_row['macd'] <= previous_row['macd_signal'] and 
                   current_row['macd'] > current_row['macd_signal'] and
                   current_row['macd'] < 0 and 
                   current_row['macd_signal'] < 0)
        except Exception as e:
            logger.error(f"買進信號驗證失敗: {e}")
            return False
    
    def _validate_sell_signal(self, current_row: pd.Series, previous_row: pd.Series) -> bool:
        """驗證MACD賣出信號（作為備用條件）"""
        try:
            # MACD死叉條件
            return (previous_row['macd_hist'] > 0 and 
                   previous_row['macd'] >= previous_row['macd_signal'] and 
                   current_row['macd_signal'] > current_row['macd'] and
                   current_row['macd'] > 0 and 
                   current_row['macd_signal'] > 0)
        except Exception as e:
            logger.error(f"賣出信號驗證失敗: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """獲取交易統計"""
        if not self.trade_pairs:
            return {
                'total_profit': 0,
                'complete_pairs': 0,
                'buy_count': self.buy_count,
                'sell_count': self.sell_count,
                'win_rate': 0,
                'average_profit': 0,
                'stop_loss_count': 0,
                'macd_sell_count': 0
            }
        
        total_profit = sum(pair['profit'] for pair in self.trade_pairs)
        winning_trades = [pair for pair in self.trade_pairs if pair['profit'] > 0]
        stop_loss_trades = [pair for pair in self.trade_pairs if pair['stop_loss_triggered']]
        
        return {
            'total_profit': total_profit,
            'complete_pairs': len(self.trade_pairs),
            'buy_count': self.buy_count,
            'sell_count': self.sell_count,
            'win_rate': (len(winning_trades) / len(self.trade_pairs)) * 100,
            'average_profit': total_profit / len(self.trade_pairs),
            'stop_loss_count': len(stop_loss_trades),
            'macd_sell_count': len(self.trade_pairs) - len(stop_loss_trades),
            'trade_pairs': self.trade_pairs
        }