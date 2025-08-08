#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終85%勝率策略 - 結合進階策略優點
基於75%勝率策略進行微調，目標達到85%勝率
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class Final85PercentStrategy:
    """最終85%勝率交易策略"""
    
    def __init__(self):
        # 調整信心度閾值到80分 - 平衡勝率和交易頻率
        self.min_confidence_score = 80  # 從85降到80
        self.current_position = 0
        self.trade_sequence = 0
        
    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算MACD指標"""
        df = df.copy()
        
        # 計算EMA
        ema_fast = df['close'].ewm(span=12).mean()
        ema_slow = df['close'].ewm(span=26).mean()
        
        # 計算MACD線
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def calculate_advanced_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算進階技術指標"""
        df = df.copy()
        
        # 基本成交量指標
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma20']
        
        # 成交量趨勢強度
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_trend'] = df['volume_ma5'].pct_change(periods=3)
        
        # RSI指標 - 優化參數
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 布林帶
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # OBV能量潮
        df['obv'] = 0.0
        for i in range(1, len(df)):
            if df.iloc[i]['close'] > df.iloc[i-1]['close']:
                df.iloc[i, df.columns.get_loc('obv')] = df.iloc[i-1]['obv'] + df.iloc[i]['volume']
            elif df.iloc[i]['close'] < df.iloc[i-1]['close']:
                df.iloc[i, df.columns.get_loc('obv')] = df.iloc[i-1]['obv'] - df.iloc[i]['volume']
            else:
                df.iloc[i, df.columns.get_loc('obv')] = df.iloc[i-1]['obv']
        
        df['obv_trend'] = df['obv'].pct_change(periods=5)
        
        # 移動平均趨勢
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma50'] = df['close'].rolling(window=50).mean()
        df['trend_up'] = (df['ma20'] > df['ma50']).astype(int)
        
        # 價格動能
        df['price_momentum'] = df['close'].pct_change(periods=5)
        
        return df
    
    def detect_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """檢測交易信號"""
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 重置狀態
        self.current_position = 0
        self.trade_sequence = 0
        
        # 計算所有指標
        df = self.calculate_macd(df)
        df = self.calculate_advanced_indicators(df)
        
        signals = []
        
        for i in range(50, len(df)):  # 從第50個數據點開始，確保指標穩定
            current_row = df.iloc[i]
            previous_row = df.iloc[i-1]
            
            # 檢查MACD買進信號
            if self._check_macd_buy_signal(current_row, previous_row) and self.current_position == 0:
                passed, info, score = self._validate_buy_signal(current_row)
                
                if passed:
                    self.trade_sequence += 1
                    self.current_position = 1
                    
                    signal = {
                        'datetime': current_row['timestamp'],
                        'close': current_row['close'],
                        'signal_type': 'buy',
                        'trade_sequence': self.trade_sequence,
                        'macd': current_row['macd'],
                        'macd_signal': current_row['macd_signal'],
                        'macd_hist': current_row['macd_hist'],
                        'volume_confirmed': True,
                        'validation_info': info,
                        'signal_strength': score
                    }
                    signals.append(signal)
                    logger.info(f"✅ 85%策略買進 #{self.trade_sequence}: {current_row['close']:,.0f} - {info}")
            
            # 檢查MACD賣出信號
            elif self._check_macd_sell_signal(current_row, previous_row) and self.current_position == 1:
                passed, info, score = self._validate_sell_signal(current_row)
                
                if passed:
                    self.current_position = 0
                    
                    signal = {
                        'datetime': current_row['timestamp'],
                        'close': current_row['close'],
                        'signal_type': 'sell',
                        'trade_sequence': self.trade_sequence,
                        'macd': current_row['macd'],
                        'macd_signal': current_row['macd_signal'],
                        'macd_hist': current_row['macd_hist'],
                        'volume_confirmed': True,
                        'validation_info': info,
                        'signal_strength': score
                    }
                    signals.append(signal)
                    logger.info(f"✅ 85%策略賣出 #{self.trade_sequence}: {current_row['close']:,.0f} - {info}")
        
        return pd.DataFrame(signals)
    
    def _check_macd_buy_signal(self, current_row: pd.Series, previous_row: pd.Series) -> bool:
        """檢查MACD買進信號 - 使用進階策略的成功邏輯"""
        try:
            return (
                previous_row['macd_hist'] < 0 and
                previous_row['macd'] <= previous_row['macd_signal'] and
                current_row['macd'] > current_row['macd_signal'] and
                current_row['macd'] < 0 and
                current_row['macd_signal'] < 0
            )
        except Exception as e:
            logger.error(f"MACD買進信號檢查失敗: {e}")
            return False
    
    def _check_macd_sell_signal(self, current_row: pd.Series, previous_row: pd.Series) -> bool:
        """檢查MACD賣出信號 - 使用進階策略的成功邏輯"""
        try:
            return (
                previous_row['macd_hist'] > 0 and
                previous_row['macd'] >= previous_row['macd_signal'] and
                current_row['macd_signal'] > current_row['macd'] and
                current_row['macd'] > 0 and
                current_row['macd_signal'] > 0
            )
        except Exception as e:
            logger.error(f"MACD賣出信號檢查失敗: {e}")
            return False
    
    def _validate_buy_signal(self, row: pd.Series) -> Tuple[bool, str, float]:
        """
        買進信號驗證 - 優化版本
        目標：提高到85%勝率
        """
        try:
            score = 0
            reasons = []
            
            # 1. 成交量確認 (30分) - 稍微提高要求
            volume_ratio = row.get('volume_ratio', 0)
            if volume_ratio >= 1.4:  # 從1.3提高到1.4
                score += 30
                reasons.append(f"量比{volume_ratio:.1f}✓")
            elif volume_ratio >= 1.2:  # 給予部分分數
                score += 20
                reasons.append(f"量比{volume_ratio:.1f}△")
            else:
                reasons.append(f"量比{volume_ratio:.1f}✗")
            
            # 2. 成交量趨勢 (25分) - 更嚴格的要求
            volume_trend = row.get('volume_trend', 0)
            if volume_trend > 0.15:  # 從0.1提高到0.15
                score += 25
                reasons.append(f"量勢{volume_trend:.1%}✓")
            elif volume_trend > 0.05:
                score += 15
                reasons.append(f"量勢{volume_trend:.1%}△")
            else:
                reasons.append(f"量勢{volume_trend:.1%}✗")
            
            # 3. RSI確認 (20分) - 優化範圍
            rsi = row.get('rsi', 50)
            if 35 <= rsi <= 65:  # 縮小範圍，避免極端值
                score += 20
                reasons.append(f"RSI{rsi:.0f}✓")
            elif 30 <= rsi <= 70:
                score += 10
                reasons.append(f"RSI{rsi:.0f}△")
            else:
                reasons.append(f"RSI{rsi:.0f}✗")
            
            # 4. 布林帶位置 (15分) - 更精確的範圍
            bb_position = row.get('bb_position', 0.5)
            if 0.15 <= bb_position <= 0.5:  # 更精確的買入區間
                score += 15
                reasons.append(f"BB位置{bb_position:.1f}✓")
            elif 0.1 <= bb_position <= 0.6:
                score += 8
                reasons.append(f"BB位置{bb_position:.1f}△")
            else:
                reasons.append(f"BB位置{bb_position:.1f}✗")
            
            # 5. OBV趨勢 (10分) - 保持原有邏輯
            obv_trend = row.get('obv_trend', 0)
            if obv_trend > 0:
                score += 10
                reasons.append(f"OBV勢{obv_trend:.1%}✓")
            else:
                reasons.append(f"OBV勢{obv_trend:.1%}✗")
            
            # 6. 趨勢確認 (額外5分) - 新增
            trend_up = row.get('trend_up', 0)
            if trend_up == 1:
                score += 5
                reasons.append("趨勢向上✓")
            
            # 總分評估 - 需要80分以上才通過
            passed = score >= self.min_confidence_score
            info = f"買進確認({score}/100): {' '.join(reasons)}"
            
            return passed, info, score
            
        except Exception as e:
            logger.error(f"買進信號驗證失敗: {e}")
            return False, f"驗證錯誤: {e}", 0
    
    def _validate_sell_signal(self, row: pd.Series) -> Tuple[bool, str, float]:
        """
        賣出信號驗證 - 優化版本
        目標：提高到85%勝率
        """
        try:
            score = 0
            reasons = []
            
            # 1. 成交量確認 (30分)
            volume_ratio = row.get('volume_ratio', 0)
            if volume_ratio >= 1.3:  # 賣出時成交量要求稍低
                score += 30
                reasons.append(f"量比{volume_ratio:.1f}✓")
            elif volume_ratio >= 1.1:
                score += 20
                reasons.append(f"量比{volume_ratio:.1f}△")
            else:
                reasons.append(f"量比{volume_ratio:.1f}✗")
            
            # 2. 成交量趨勢 (25分)
            volume_trend = row.get('volume_trend', 0)
            if volume_trend > -0.1:  # 允許輕微下降
                score += 25
                reasons.append(f"量勢{volume_trend:.1%}✓")
            elif volume_trend > -0.2:
                score += 15
                reasons.append(f"量勢{volume_trend:.1%}△")
            else:
                reasons.append(f"量勢{volume_trend:.1%}✗")
            
            # 3. RSI確認 (20分)
            rsi = row.get('rsi', 50)
            if 35 <= rsi <= 65:
                score += 20
                reasons.append(f"RSI{rsi:.0f}✓")
            elif 30 <= rsi <= 70:
                score += 10
                reasons.append(f"RSI{rsi:.0f}△")
            else:
                reasons.append(f"RSI{rsi:.0f}✗")
            
            # 4. 布林帶位置 (15分)
            bb_position = row.get('bb_position', 0.5)
            if 0.5 <= bb_position <= 0.85:  # 賣出區間
                score += 15
                reasons.append(f"BB位置{bb_position:.1f}✓")
            elif 0.4 <= bb_position <= 0.9:
                score += 8
                reasons.append(f"BB位置{bb_position:.1f}△")
            else:
                reasons.append(f"BB位置{bb_position:.1f}✗")
            
            # 5. OBV趨勢 (10分)
            obv_trend = row.get('obv_trend', 0)
            if obv_trend < 0:
                score += 10
                reasons.append(f"OBV勢{obv_trend:.1%}✓")
            else:
                reasons.append(f"OBV勢{obv_trend:.1%}✗")
            
            # 6. 趨勢確認 (額外5分)
            trend_up = row.get('trend_up', 1)
            if trend_up == 0:
                score += 5
                reasons.append("趨勢向下✓")
            
            # 總分評估 - 需要80分以上才通過
            passed = score >= self.min_confidence_score
            info = f"賣出確認({score}/100): {' '.join(reasons)}"
            
            return passed, info, score
            
        except Exception as e:
            logger.error(f"賣出信號驗證失敗: {e}")
            return False, f"驗證錯誤: {e}", 0