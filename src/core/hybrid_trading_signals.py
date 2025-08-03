#!/usr/bin/env python3
"""
混合MACD交易信號檢測系統
使用1小時MACD作為信號基準，短時間週期進行動態追蹤
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class HybridPositionTracker:
    """混合策略持倉狀態追蹤器"""
    
    def __init__(self):
        self.current_position = 0  # 0=空倉, 1=持倉
        self.trade_sequence = 0    # 當前交易序號
        self.buy_count = 0         # 總買進次數
        self.sell_count = 0        # 總賣出次數
        self.trade_pairs = []      # 完整交易對
        self.open_trades = []      # 未平倉交易
        self.trade_history = []    # 完整交易歷史
        
        # 混合策略相關
        self.hourly_signal = None  # 1小時MACD信號
        self.dynamic_timeframe = "5"  # 動態追蹤時間週期（分鐘）
        self.dynamic_buy_price = None   # 動態買進基準價
        self.dynamic_sell_price = None  # 動態賣出基準價
        self.observation_start_time = None  # 觀察開始時間
        self.observation_hours = 2      # 觀察時間（小時）
        self.is_observing = False       # 是否在觀察期間
    
    def can_buy(self) -> bool:
        """檢查是否可以買進"""
        return self.current_position == 0
    
    def can_sell(self) -> bool:
        """檢查是否可以賣出"""
        return self.current_position == 1
    
    def start_buy_observation(self, timestamp: datetime, price: float, hourly_signal: str):
        """開始買進觀察期"""
        self.dynamic_buy_price = price
        self.observation_start_time = timestamp
        self.is_observing = True
        self.hourly_signal = hourly_signal
        logger.info(f"開始買進觀察期: 基準價 {price:,.0f}, 1小時信號: {hourly_signal}, 動態週期: {self.dynamic_timeframe}分鐘")
    
    def start_sell_observation(self, timestamp: datetime, price: float, hourly_signal: str):
        """開始賣出觀察期"""
        self.dynamic_sell_price = price
        self.observation_start_time = timestamp
        self.is_observing = True
        self.hourly_signal = hourly_signal
        logger.info(f"開始賣出觀察期: 基準價 {price:,.0f}, 1小時信號: {hourly_signal}, 動態週期: {self.dynamic_timeframe}分鐘")
    
    def update_buy_price(self, price: float):
        """更新動態買進基準價（只能往下調整）"""
        if self.dynamic_buy_price is None:
            return
        
        if price < self.dynamic_buy_price:
            old_price = self.dynamic_buy_price
            self.dynamic_buy_price = price
            logger.debug(f"買進基準價調整: {old_price:,.0f} → {price:,.0f}")
    
    def update_sell_price(self, price: float):
        """更新動態賣出基準價（只能往上調整）"""
        if self.dynamic_sell_price is None:
            return
        
        if price > self.dynamic_sell_price:
            old_price = self.dynamic_sell_price
            self.dynamic_sell_price = price
            logger.debug(f"賣出基準價調整: {old_price:,.0f} → {price:,.0f}")
    
    def check_buy_trigger(self, current_price: float) -> bool:
        """檢查是否觸發買進"""
        if not self.is_observing or self.dynamic_buy_price is None:
            return False
        
        # 價格回升突破基準價
        if current_price > self.dynamic_buy_price:
            logger.info(f"買進觸發: 當前價格 {current_price:,.0f} > 基準價 {self.dynamic_buy_price:,.0f}")
            return True
        
        return False
    
    def check_sell_trigger(self, current_price: float) -> bool:
        """檢查是否觸發賣出"""
        if not self.is_observing or self.dynamic_sell_price is None:
            return False
        
        # 價格回跌跌破基準價
        if current_price < self.dynamic_sell_price:
            logger.info(f"賣出觸發: 當前價格 {current_price:,.0f} < 基準價 {self.dynamic_sell_price:,.0f}")
            return True
        
        return False
    
    def is_observation_expired(self, current_time: datetime) -> bool:
        """檢查觀察期是否過期"""
        if not self.is_observing or self.observation_start_time is None:
            return False
        
        elapsed = current_time - self.observation_start_time
        return elapsed.total_seconds() / 3600 >= self.observation_hours
    
    def execute_buy(self, timestamp: datetime, price: float) -> int:
        """執行買進交易"""
        if not self.can_buy():
            logger.warning("無法買進：當前已有持倉")
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
            'dynamic_timeframe': self.dynamic_timeframe
        }
        
        self.open_trades.append(trade)
        self.trade_history.append(trade)
        
        # 清除觀察狀態
        self.is_observing = False
        self.dynamic_buy_price = None
        self.observation_start_time = None
        
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
                'dynamic_timeframe': buy_trade['dynamic_timeframe']
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
        
        # 清除觀察狀態
        self.is_observing = False
        self.dynamic_sell_price = None
        self.observation_start_time = None
        
        logger.info(f"✅ 執行賣出交易 #{self.trade_sequence}: 價格 {price:,.0f}, 利潤 {profit:,.0f}")
        return self.trade_sequence
    
    def get_status(self) -> Dict:
        """獲取當前狀態"""
        return {
            'current_position': self.current_position,
            'trade_sequence': self.trade_sequence,
            'buy_count': self.buy_count,
            'sell_count': self.sell_count,
            'is_observing': self.is_observing,
            'dynamic_buy_price': self.dynamic_buy_price,
            'dynamic_sell_price': self.dynamic_sell_price,
            'dynamic_timeframe': self.dynamic_timeframe,
            'hourly_signal': self.hourly_signal
        }

class HybridSignalValidator:
    """混合策略信號驗證器"""
    
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

class HybridSignalDetectionEngine:
    """混合策略信號檢測引擎"""
    
    def __init__(self, dynamic_timeframe: str = "5", observation_hours: int = 2):
        self.tracker = HybridPositionTracker()
        self.tracker.dynamic_timeframe = dynamic_timeframe
        self.tracker.observation_hours = observation_hours
        self.validator = HybridSignalValidator()
        
    def detect_signals(self, hourly_df: pd.DataFrame, dynamic_df: pd.DataFrame) -> pd.DataFrame:
        """檢測混合策略信號"""
        signals = []
        
        # 處理1小時數據
        for i, row in hourly_df.iterrows():
            previous_row = hourly_df.iloc[i-1] if i > 0 else None
            
            # 檢查1小時MACD信號
            if self.validator.validate_hourly_buy_signal(row, previous_row):
                if self.tracker.can_buy():
                    # 開始買進觀察期
                    self.tracker.start_buy_observation(
                        row['datetime'], 
                        row['close'], 
                        f"1小時MACD金叉: {row['macd_hist']:.2f}"
                    )
            
            elif self.validator.validate_hourly_sell_signal(row, previous_row):
                if self.tracker.can_sell():
                    # 開始賣出觀察期
                    self.tracker.start_sell_observation(
                        row['datetime'], 
                        row['close'], 
                        f"1小時MACD死叉: {row['macd_hist']:.2f}"
                    )
        
        # 處理動態時間週期數據
        for i, row in dynamic_df.iterrows():
            # 更新動態基準價
            if self.tracker.is_observing:
                if self.tracker.dynamic_buy_price is not None:
                    self.tracker.update_buy_price(row['close'])
                elif self.tracker.dynamic_sell_price is not None:
                    self.tracker.update_sell_price(row['close'])
                
                # 檢查觸發條件
                if self.tracker.check_buy_trigger(row['close']):
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
                
                elif self.tracker.check_sell_trigger(row['close']):
                    trade_seq = self.tracker.execute_sell(row['datetime'], row['close'])
                    signals.append({
                        'datetime': row['datetime'],
                        'close': row['close'],
                        'signal_type': 'sell',
                        'trade_sequence': trade_seq,
                        'hourly_signal': self.tracker.hourly_signal,
                        'dynamic_timeframe': self.tracker.dynamic_timeframe,
                        'macd_hist': row['macd_hist'],
                        'macd': row['macd'],
                        'macd_signal': row['macd_signal']
                    })
                
                # 檢查觀察期是否過期
                elif self.tracker.is_observation_expired(row['datetime']):
                    if self.tracker.dynamic_buy_price is not None:
                        # 觀察期過期，執行買進
                        trade_seq = self.tracker.execute_buy(row['datetime'], self.tracker.dynamic_buy_price)
                        signals.append({
                            'datetime': row['datetime'],
                            'close': self.tracker.dynamic_buy_price,
                            'signal_type': 'buy',
                            'trade_sequence': trade_seq,
                            'hourly_signal': self.tracker.hourly_signal,
                            'dynamic_timeframe': self.tracker.dynamic_timeframe,
                            'macd_hist': row['macd_hist'],
                            'macd': row['macd'],
                            'macd_signal': row['macd_signal']
                        })
                    elif self.tracker.dynamic_sell_price is not None:
                        # 觀察期過期，執行賣出
                        trade_seq = self.tracker.execute_sell(row['datetime'], self.tracker.dynamic_sell_price)
                        signals.append({
                            'datetime': row['datetime'],
                            'close': self.tracker.dynamic_sell_price,
                            'signal_type': 'sell',
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

def detect_hybrid_trading_signals(hourly_df: pd.DataFrame, dynamic_df: pd.DataFrame, 
                                dynamic_timeframe: str = "5", observation_hours: int = 2) -> Tuple[pd.DataFrame, Dict]:
    """
    檢測混合策略交易信號
    
    Args:
        hourly_df: 1小時MACD數據
        dynamic_df: 動態時間週期數據
        dynamic_timeframe: 動態追蹤時間週期（分鐘）
        observation_hours: 觀察時間（小時）
    
    Returns:
        (signals_df, statistics)
    """
    engine = HybridSignalDetectionEngine(dynamic_timeframe, observation_hours)
    signals_df = engine.detect_signals(hourly_df, dynamic_df)
    statistics = engine.get_statistics()
    
    return signals_df, statistics 