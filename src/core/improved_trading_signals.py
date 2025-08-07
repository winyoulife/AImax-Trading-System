#!/usr/bin/env python3
"""
改進版MACD交易信號檢測系統
實現低點買入、高點賣出的順序性交易邏輯
"""

import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class PositionTracker:
    """持倉狀態追蹤器"""
    
    def __init__(self):
        self.current_position = 0  # 0=空倉, 1=持倉
        self.trade_sequence = 0    # 當前交易序號
        self.buy_count = 0         # 總買進次數
        self.sell_count = 0        # 總賣出次數
        self.trade_pairs = []      # 完整交易對
        self.open_trades = []      # 未平倉交易
        self.trade_history = []    # 完整交易歷史
    
    def can_buy(self) -> bool:
        """檢查是否可以買進"""
        return self.current_position == 0
    
    def can_sell(self) -> bool:
        """檢查是否可以賣出"""
        return self.current_position == 1
    
    def execute_buy(self, timestamp: datetime, price: float) -> int:
        """執行買進操作"""
        if not self.can_buy():
            logger.warning(f"無法買進: 當前持倉狀態 = {self.current_position}")
            return 0
        
        self.current_position = 1
        self.buy_count += 1
        self.trade_sequence = self.buy_count
        
        trade_record = {
            'type': 'buy',
            'sequence': self.trade_sequence,
            'timestamp': timestamp,
            'price': price
        }
        
        self.open_trades.append(trade_record)
        self.trade_history.append(trade_record)
        
        logger.info(f"執行買進: 買{self.trade_sequence}, 價格: {price}")
        return self.trade_sequence
    
    def execute_sell(self, timestamp: datetime, price: float) -> int:
        """執行賣出操作"""
        if not self.can_sell():
            logger.warning(f"無法賣出: 當前持倉狀態 = {self.current_position}")
            return 0
        
        self.current_position = 0
        self.sell_count += 1
        
        # 配對最近的買進交易
        if self.open_trades:
            buy_trade = self.open_trades.pop()
            trade_pair = {
                'buy_sequence': buy_trade['sequence'],
                'sell_sequence': buy_trade['sequence'],  # 賣出序號與買進序號相同
                'buy_time': buy_trade['timestamp'],
                'sell_time': timestamp,
                'buy_price': buy_trade['price'],
                'sell_price': price,
                'profit': price - buy_trade['price']
            }
            self.trade_pairs.append(trade_pair)
            
            sell_record = {
                'type': 'sell',
                'sequence': buy_trade['sequence'],
                'timestamp': timestamp,
                'price': price,
                'paired_with': buy_trade['sequence']
            }
            self.trade_history.append(sell_record)
            
            logger.info(f"執行賣出: 賣{buy_trade['sequence']}, 價格: {price}, 利潤: {price - buy_trade['price']:.1f}")
            return buy_trade['sequence']
        
        return 0
    
    def get_status(self) -> Dict:
        """獲取當前狀態"""
        return {
            'position': self.current_position,
            'position_status': '持倉' if self.current_position == 1 else '空倉',
            'buy_count': self.buy_count,
            'sell_count': self.sell_count,
            'complete_pairs': len(self.trade_pairs),
            'open_positions': len(self.open_trades),
            'next_trade_sequence': self.buy_count + 1 if self.current_position == 0 else self.buy_count
        }

class SignalValidator:
    """信號驗證器"""
    
    @staticmethod
    def validate_buy_signal(current_row: pd.Series, previous_row: pd.Series) -> bool:
        """
        驗證買進信號的所有條件
        
        條件:
        1. MACD柱為負 (macd_hist < 0)
        2. MACD線突破信號線向上 (前一時點 macd <= signal，當前時點 macd > signal)
        3. MACD線為負 (macd < 0)
        4. 信號線為負 (signal < 0)
        """
        try:
            # 基本MACD條件
            basic_conditions = (
                previous_row['macd_hist'] < 0 and  # MACD柱為負
                previous_row['macd'] <= previous_row['macd_signal'] and  # 前一時點MACD <= 信號線
                current_row['macd'] > current_row['macd_signal']  # 當前MACD > 信號線
            )
            
            # 新增的負值條件
            negative_conditions = (
                current_row['macd'] < 0 and  # MACD線為負
                current_row['macd_signal'] < 0  # 信號線為負
            )
            
            result = basic_conditions and negative_conditions
            
            if result:
                logger.debug(f"買進信號驗證通過: MACD={current_row['macd']:.1f}, 信號={current_row['macd_signal']:.1f}, 柱={current_row['macd_hist']:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"買進信號驗證失敗: {e}")
            return False
    
    @staticmethod
    def validate_sell_signal(current_row: pd.Series, previous_row: pd.Series) -> bool:
        """
        驗證賣出信號的所有條件
        
        條件:
        1. MACD柱為正 (macd_hist > 0)
        2. 信號線突破MACD線向上 (前一時點 macd >= signal，當前時點 signal > macd)
        3. MACD線為正 (macd > 0)
        4. 信號線為正 (signal > 0)
        """
        try:
            # 基本MACD條件
            basic_conditions = (
                previous_row['macd_hist'] > 0 and  # MACD柱為正
                previous_row['macd'] >= previous_row['macd_signal'] and  # 前一時點MACD >= 信號線
                current_row['macd_signal'] > current_row['macd']  # 當前信號線 > MACD
            )
            
            # 新增的正值條件
            positive_conditions = (
                current_row['macd'] > 0 and  # MACD線為正
                current_row['macd_signal'] > 0  # 信號線為正
            )
            
            result = basic_conditions and positive_conditions
            
            if result:
                logger.debug(f"賣出信號驗證通過: MACD={current_row['macd']:.1f}, 信號={current_row['macd_signal']:.1f}, 柱={current_row['macd_hist']:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"賣出信號驗證失敗: {e}")
            return False

class SignalDetectionEngine:
    """信號檢測引擎"""
    
    def __init__(self):
        self.position_tracker = PositionTracker()
        self.signal_validator = SignalValidator()
    
    def detect_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        檢測交易信號
        
        Args:
            df: 包含MACD數據的DataFrame
            
        Returns:
            添加了交易信號的DataFrame
        """
        if len(df) < 2:
            logger.warning("數據不足，無法檢測信號")
            return df
        
        # 初始化信號欄位
        df = df.copy()
        df['trading_signal'] = '⚪ 持有'
        df['signal_type'] = 'hold'
        df['trade_sequence'] = 0
        df['position_status'] = '空倉'
        df['signal_valid'] = True
        
        # 重置追蹤器
        self.position_tracker = PositionTracker()
        
        # 逐行檢測信號
        for i in range(1, len(df)):
            current_row = df.iloc[i]
            previous_row = df.iloc[i-1]
            
            signal_detected = False
            
            # 檢測買進信號
            if (self.signal_validator.validate_buy_signal(current_row, previous_row) and 
                self.position_tracker.can_buy()):
                
                sequence = self.position_tracker.execute_buy(
                    current_row['datetime'], 
                    current_row['close']
                )
                
                df.at[i, 'trading_signal'] = f'🟢 買{sequence}'
                df.at[i, 'signal_type'] = 'buy'
                df.at[i, 'trade_sequence'] = sequence
                signal_detected = True
            
            # 檢測賣出信號
            elif (self.signal_validator.validate_sell_signal(current_row, previous_row) and 
                  self.position_tracker.can_sell()):
                
                sequence = self.position_tracker.execute_sell(
                    current_row['datetime'], 
                    current_row['close']
                )
                
                df.at[i, 'trading_signal'] = f'🔴 賣{sequence}'
                df.at[i, 'signal_type'] = 'sell'
                df.at[i, 'trade_sequence'] = sequence
                signal_detected = True
            
            # 更新持倉狀態
            status = self.position_tracker.get_status()
            df.at[i, 'position_status'] = status['position_status']
            
            # 檢查無效信號
            if not signal_detected:
                # 檢查是否有被忽略的信號
                buy_conditions_met = self.signal_validator.validate_buy_signal(current_row, previous_row)
                sell_conditions_met = self.signal_validator.validate_sell_signal(current_row, previous_row)
                
                if buy_conditions_met and not self.position_tracker.can_buy():
                    df.at[i, 'signal_valid'] = False
                    logger.warning(f"忽略買進信號 (已持倉): 時間 {current_row['datetime']}")
                
                if sell_conditions_met and not self.position_tracker.can_sell():
                    df.at[i, 'signal_valid'] = False
                    logger.warning(f"忽略賣出信號 (空倉): 時間 {current_row['datetime']}")
        
        return df
    
    def get_statistics(self) -> Dict:
        """獲取交易統計信息"""
        status = self.position_tracker.get_status()
        
        # 計算額外統計信息
        total_profit = sum(pair['profit'] for pair in self.position_tracker.trade_pairs)
        avg_profit = total_profit / len(self.position_tracker.trade_pairs) if self.position_tracker.trade_pairs else 0
        
        # 計算持倉時間
        avg_hold_time = 0
        if self.position_tracker.trade_pairs:
            hold_times = []
            for pair in self.position_tracker.trade_pairs:
                hold_time = (pair['sell_time'] - pair['buy_time']).total_seconds() / 3600  # 小時
                hold_times.append(hold_time)
            avg_hold_time = sum(hold_times) / len(hold_times)
        
        return {
            **status,
            'total_profit': total_profit,
            'average_profit': avg_profit,
            'average_hold_time': avg_hold_time,
            'trade_pairs': self.position_tracker.trade_pairs,
            'trade_history': self.position_tracker.trade_history
        }

# 便利函數
def detect_improved_trading_signals(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    便利函數：檢測改進版交易信號
    
    Args:
        df: 包含MACD數據的DataFrame
        
    Returns:
        (添加了信號的DataFrame, 統計信息字典)
    """
    engine = SignalDetectionEngine()
    df_with_signals = engine.detect_smart_balanced_signals(df)
    statistics = engine.get_statistics()
    
    return df_with_signals, statistics

# 測試代碼
if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 創建測試數據
    import numpy as np
    
    test_data = {
        'datetime': pd.date_range('2025-07-23', periods=10, freq='H'),
        'close': np.random.uniform(3500000, 3600000, 10),
        'macd': [-100, -80, -60, -40, -20, 10, 30, 50, 30, 10],
        'macd_signal': [-120, -100, -80, -60, -40, -10, 10, 30, 40, 20],
        'macd_hist': [20, 20, 20, 20, 20, 20, 20, 20, -10, -10],
        'volume': np.random.uniform(1, 10, 10)
    }
    
    df = pd.DataFrame(test_data)
    
    print("🧪 測試改進版交易信號檢測...")
    df_result, stats = detect_improved_trading_signals(df)
    
    print("\n📊 檢測結果:")
    for _, row in df_result.iterrows():
        if row['signal_type'] != 'hold':
            print(f"{row['datetime'].strftime('%m-%d %H:%M')} | {row['trading_signal']} | MACD:{row['macd']:6.1f} | 信號:{row['macd_signal']:6.1f}")
    
    print(f"\n📈 統計信息:")
    print(f"買進次數: {stats['buy_count']}")
    print(f"賣出次數: {stats['sell_count']}")
    print(f"完整交易對: {stats['complete_pairs']}")
    print(f"當前狀態: {stats['position_status']}")