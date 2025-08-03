#!/usr/bin/env python3
"""
改進的混合MACD交易信號檢測系統
使用1小時MACD作為趨勢確認，短時間週期作為精確入場時機
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class ImprovedHybridPositionTracker:
    """改進的混合策略持倉狀態追蹤器"""
    
    def __init__(self):
        self.current_position = 0  # 0=空倉, 1=持倉
        self.trade_sequence = 0    # 當前交易序號
        self.buy_count = 0         # 總買進次數
        self.sell_count = 0        # 總賣出次數
        self.trade_pairs = []      # 完整交易對
        self.open_trades = []      # 未平倉交易
        self.trade_history = []    # 完整交易歷史
        
        # 改進的混合策略相關
        self.hourly_signal = None  # 1小時MACD信號
        self.dynamic_timeframe = "5"  # 短時間週期（分鐘）
        self.is_waiting_for_entry = False  # 是否等待入場
        self.entry_observation_start = None  # 入場觀察開始時間
        self.entry_observation_hours = 1     # 入場觀察時間（小時）
        self.best_entry_price = None         # 最佳入場價格
        self.entry_trigger_price = None      # 入場觸發價格
        
    def can_buy(self) -> bool:
        """檢查是否可以買進"""
        return self.current_position == 0 and not self.is_waiting_for_entry
    
    def can_sell(self) -> bool:
        """檢查是否可以賣出"""
        return self.current_position == 1
    
    def start_entry_observation(self, timestamp: datetime, hourly_signal: str):
        """開始入場觀察期"""
        self.is_waiting_for_entry = True
        self.entry_observation_start = timestamp
        self.hourly_signal = hourly_signal
        self.best_entry_price = None
        self.entry_trigger_price = None
        logger.info(f"開始入場觀察期: 1小時信號: {hourly_signal}, 短時間週期: {self.dynamic_timeframe}分鐘")
    
    def update_entry_opportunity(self, price: float, timestamp: datetime):
        """更新入場機會"""
        if not self.is_waiting_for_entry:
            return
        
        # 記錄最佳入場價格（最低點）
        if self.best_entry_price is None or price < self.best_entry_price:
            self.best_entry_price = price
            logger.debug(f"更新最佳入場價格: {price:,.0f}")
        
        # 設置入場觸發價格（比最佳價格稍高一點）
        if self.entry_trigger_price is None:
            self.entry_trigger_price = price * 1.001  # 0.1%的緩衝
            logger.debug(f"設置入場觸發價格: {self.entry_trigger_price:,.0f}")
    
    def check_entry_trigger(self, current_price: float) -> bool:
        """檢查是否觸發入場"""
        if not self.is_waiting_for_entry or self.entry_trigger_price is None:
            return False
        
        # 價格回升突破觸發價格
        if current_price > self.entry_trigger_price:
            logger.info(f"入場觸發: 當前價格 {current_price:,.0f} > 觸發價格 {self.entry_trigger_price:,.0f}")
            return True
        
        return False
    
    def is_entry_observation_expired(self, current_time: datetime) -> bool:
        """檢查入場觀察期是否過期"""
        if not self.is_waiting_for_entry or self.entry_observation_start is None:
            return False
        
        elapsed = current_time - self.entry_observation_start
        return elapsed.total_seconds() / 3600 >= self.entry_observation_hours
    
    def execute_buy(self, timestamp: datetime, price: float) -> int:
        """執行買進交易"""
        if not self.can_buy() and not self.is_waiting_for_entry:
            logger.warning("無法買進：當前已有持倉或不在觀察期")
            return 0
        
        self.trade_sequence += 1
        self.current_position = 1
        self.buy_count += 1
        
        trade = {
            'sequence': self.trade_sequence,
            'type': 'buy',
            'timestamp': timestamp,
            'price': price,
            'hourly_signal': self.hourly_signal,
            'dynamic_timeframe': self.dynamic_timeframe,
            'best_entry_price': self.best_entry_price,
            'entry_trigger_price': self.entry_trigger_price
        }
        
        self.open_trades.append(trade)
        self.trade_history.append(trade)
        
        # 清除觀察狀態
        self.is_waiting_for_entry = False
        self.entry_observation_start = None
        self.best_entry_price = None
        self.entry_trigger_price = None
        
        logger.info(f"✅ 執行買進交易 #{self.trade_sequence}: 價格 {price:,.0f}")
        return self.trade_sequence
    
    def execute_sell(self, timestamp: datetime, price: float) -> int:
        """執行賣出交易"""
        if not self.can_sell():
            logger.warning("無法賣出：當前無持倉")
            return 0
        
        self.trade_sequence += 1
        self.current_position = 0
        self.sell_count += 1
        
        # 找到對應的買進交易
        buy_trade = None
        for trade in self.open_trades:
            if trade['type'] == 'buy':
                buy_trade = trade
                break
        
        if buy_trade:
            self.open_trades.remove(buy_trade)
            
            # 計算利潤
            profit = price - buy_trade['price']
            
            # 創建交易對
            trade_pair = {
                'buy_sequence': buy_trade['sequence'],
                'sell_sequence': self.trade_sequence,
                'buy_price': buy_trade['price'],
                'sell_price': price,
                'profit': profit,
                'buy_time': buy_trade['timestamp'],
                'sell_time': timestamp,
                'hourly_signal': buy_trade['hourly_signal'],
                'dynamic_timeframe': buy_trade['dynamic_timeframe'],
                'best_entry_price': buy_trade.get('best_entry_price'),
                'entry_trigger_price': buy_trade.get('entry_trigger_price')
            }
            
            self.trade_pairs.append(trade_pair)
        
        trade = {
            'sequence': self.trade_sequence,
            'type': 'sell',
            'timestamp': timestamp,
            'price': price,
            'hourly_signal': self.hourly_signal,
            'dynamic_timeframe': self.dynamic_timeframe
        }
        
        self.trade_history.append(trade)
        
        logger.info(f"✅ 執行賣出交易 #{self.trade_sequence}: 價格 {price:,.0f}, 利潤 {profit:,.0f}")
        return self.trade_sequence
    
    def get_status(self) -> Dict:
        """獲取當前狀態"""
        return {
            'current_position': self.current_position,
            'trade_sequence': self.trade_sequence,
            'buy_count': self.buy_count,
            'sell_count': self.sell_count,
            'is_waiting_for_entry': self.is_waiting_for_entry,
            'best_entry_price': self.best_entry_price,
            'entry_trigger_price': self.entry_trigger_price,
            'dynamic_timeframe': self.dynamic_timeframe,
            'hourly_signal': self.hourly_signal
        }

class ImprovedHybridSignalValidator:
    """改進的混合策略信號驗證器"""
    
    @staticmethod
    def validate_hourly_buy_signal(current_row: pd.Series, previous_row: pd.Series) -> bool:
        """驗證1小時MACD買進信號"""
        if previous_row is None:
            return False
        
        # MACD柱狀圖由負轉正（金叉）
        current_hist = current_row['macd_hist']
        previous_hist = previous_row['macd_hist']
        
        return previous_hist < 0 and current_hist > 0
    
    @staticmethod
    def validate_hourly_sell_signal(current_row: pd.Series, previous_row: pd.Series) -> bool:
        """驗證1小時MACD賣出信號"""
        if previous_row is None:
            return False
        
        # MACD柱狀圖由正轉負（死叉）
        current_hist = current_row['macd_hist']
        previous_hist = previous_row['macd_hist']
        
        return previous_hist > 0 and current_hist < 0

class ImprovedHybridSignalDetectionEngine:
    """改進的混合策略信號檢測引擎"""
    
    def __init__(self, dynamic_timeframe: str = "5", entry_observation_hours: int = 1):
        self.tracker = ImprovedHybridPositionTracker()
        self.tracker.dynamic_timeframe = dynamic_timeframe
        self.tracker.entry_observation_hours = entry_observation_hours
        self.validator = ImprovedHybridSignalValidator()
        
    def detect_signals(self, hourly_df: pd.DataFrame, dynamic_df: pd.DataFrame) -> pd.DataFrame:
        """檢測改進的混合策略信號"""
        signals = []
        
        # 處理1小時數據
        for i, row in hourly_df.iterrows():
            previous_row = hourly_df.iloc[i-1] if i > 0 else None
            
            # 檢查1小時MACD信號
            if self.validator.validate_hourly_buy_signal(row, previous_row):
                if self.tracker.can_buy():
                    # 開始入場觀察期
                    self.tracker.start_entry_observation(
                        row['datetime'], 
                        f"1小時MACD金叉: {row['macd_hist']:.2f}"
                    )
            
            elif self.validator.validate_hourly_sell_signal(row, previous_row):
                if self.tracker.can_sell():
                    # 直接執行賣出（基於1小時信號）
                    trade_seq = self.tracker.execute_sell(row['datetime'], row['close'])
                    signals.append({
                        'datetime': row['datetime'],
                        'close': row['close'],
                        'signal_type': 'sell',
                        'trade_sequence': trade_seq,
                        'hourly_signal': f"1小時MACD死叉: {row['macd_hist']:.2f}",
                        'dynamic_timeframe': self.tracker.dynamic_timeframe,
                        'macd_hist': row['macd_hist'],
                        'macd': row['macd'],
                        'macd_signal': row['macd_signal']
                    })
        
        # 處理短時間週期數據
        for i, row in dynamic_df.iterrows():
            # 更新入場機會
            if self.tracker.is_waiting_for_entry:
                self.tracker.update_entry_opportunity(row['close'], row['datetime'])
                
                # 檢查入場觸發
                if self.tracker.check_entry_trigger(row['close']):
                    trade_seq = self.tracker.execute_buy(row['datetime'], row['close'])
                    signals.append({
                        'datetime': row['datetime'],
                        'close': row['close'],
                        'signal_type': 'buy',
                        'trade_sequence': trade_seq,
                        'hourly_signal': self.tracker.hourly_signal,
                        'dynamic_timeframe': self.tracker.dynamic_timeframe,
                        'macd_hist': row['macd_hist'],
                        'macd': row['macd'],
                        'macd_signal': row['macd_signal']
                    })
                
                # 檢查觀察期是否過期
                elif self.tracker.is_entry_observation_expired(row['datetime']):
                    # 觀察期過期，使用最佳入場價格執行買進
                    entry_price = self.tracker.best_entry_price or row['close']
                    trade_seq = self.tracker.execute_buy(row['datetime'], entry_price)
                    signals.append({
                        'datetime': row['datetime'],
                        'close': entry_price,
                        'signal_type': 'buy',
                        'trade_sequence': trade_seq,
                        'hourly_signal': self.tracker.hourly_signal,
                        'dynamic_timeframe': self.tracker.dynamic_timeframe,
                        'macd_hist': row['macd_hist'],
                        'macd': row['macd'],
                        'macd_signal': row['macd_signal']
                    })
        
        return pd.DataFrame(signals) if signals else pd.DataFrame()
    
    def get_statistics(self) -> Dict:
        """獲取統計信息"""
        return {
            'total_trades': len(self.tracker.trade_pairs),
            'buy_count': self.tracker.buy_count,
            'sell_count': self.tracker.sell_count,
            'trade_pairs': self.tracker.trade_pairs,
            'current_status': self.tracker.get_status()
        }

def detect_improved_hybrid_trading_signals(hourly_df: pd.DataFrame, dynamic_df: pd.DataFrame, 
                                         dynamic_timeframe: str = "5", entry_observation_hours: int = 1) -> Tuple[pd.DataFrame, Dict]:
    """
    檢測改進的混合策略交易信號
    
    Args:
        hourly_df: 1小時MACD數據
        dynamic_df: 短時間週期數據
        dynamic_timeframe: 短時間週期（分鐘）
        entry_observation_hours: 入場觀察時間（小時）
    
    Returns:
        (signals_df, statistics)
    """
    engine = ImprovedHybridSignalDetectionEngine(dynamic_timeframe, entry_observation_hours)
    signals_df = engine.detect_signals(hourly_df, dynamic_df)
    statistics = engine.get_statistics()
    
    return signals_df, statistics 