#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
終極優化MACD交易信號檢測系統 - 清理版
目標：達到85%+勝率
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class UltimateOptimizedVolumeEnhancedMACDSignals:
    """終極優化成交量增強MACD交易信號檢測系統"""
    
    def __init__(self):
        self.min_confidence = 0.85  # 85%最低信心度
        
    def calculate_macd(self, df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
        """計算MACD指標"""
        df = df.copy()
        
        # 計算EMA
        ema_fast = df['close'].ewm(span=fast).mean()
        ema_slow = df['close'].ewm(span=slow).mean()
        
        # 計算MACD線
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=signal).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標"""
        df = df.copy()
        
        # 基本成交量指標
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma20']
        
        # RSI指標
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
        
        # 移動平均線
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma50'] = df['close'].rolling(window=50).mean()
        
        # 趨勢確認
        df['trend_up'] = (df['ma20'] > df['ma50']).astype(int)
        
        return df
        
    def detect_signals(self, df: pd.DataFrame) -> List[Dict]:
        """檢測交易信號"""
        try:
            # 計算MACD
            df = self.calculate_macd(df)
            
            # 計算技術指標
            df = self.calculate_indicators(df)
            
            signals = []
            
            for i in range(50, len(df)):  # 從第50個數據點開始
                current = df.iloc[i]
                prev = df.iloc[i-1]
                
                # 檢測買入信號
                buy_signal = self._detect_buy_signal(current, prev)
                if buy_signal:
                    signals.append({
                        'timestamp': current.name if hasattr(current, 'name') else datetime.now(),
                        'action': 'buy',
                        'price': current['close'],
                        'confidence': buy_signal['confidence'],
                        'reasons': buy_signal['reasons'],
                        'symbol': 'BTCUSDT'
                    })
                
                # 檢測賣出信號
                sell_signal = self._detect_sell_signal(current, prev)
                if sell_signal:
                    signals.append({
                        'timestamp': current.name if hasattr(current, 'name') else datetime.now(),
                        'action': 'sell',
                        'price': current['close'],
                        'confidence': sell_signal['confidence'],
                        'reasons': sell_signal['reasons'],
                        'symbol': 'BTCUSDT'
                    })
            
            logger.info(f"檢測到 {len(signals)} 個交易信號")
            return signals
            
        except Exception as e:
            logger.error(f"信號檢測失敗: {e}")
            return []
    
    def _detect_buy_signal(self, current, prev) -> Dict:
        """檢測買入信號"""
        try:
            confidence = 0.0
            reasons = []
            
            # 1. MACD金叉 (30分)
            if (current['macd'] > current['macd_signal'] and 
                prev['macd'] <= prev['macd_signal']):
                confidence += 0.30
                reasons.append("MACD金叉")
            
            # 2. 成交量確認 (25分)
            if current['volume_ratio'] > 1.5:
                confidence += 0.25
                reasons.append(f"成交量放大{current['volume_ratio']:.1f}倍")
            
            # 3. RSI超賣反彈 (20分)
            if 25 <= current['rsi'] <= 45:
                confidence += 0.20
                reasons.append(f"RSI反彈{current['rsi']:.1f}")
            
            # 4. 布林帶位置 (15分)
            if current['bb_position'] < 0.3:
                confidence += 0.15
                reasons.append("布林帶下軌支撐")
            
            # 5. 趨勢確認 (10分)
            if current['trend_up'] == 1:
                confidence += 0.10
                reasons.append("趨勢向上")
            
            # 只有信心度達到85%以上才發出信號
            if confidence >= self.min_confidence and len(reasons) >= 3:
                return {
                    'confidence': confidence,
                    'reasons': reasons
                }
            
            return None
            
        except Exception as e:
            logger.error(f"買入信號檢測失敗: {e}")
            return None
    
    def _detect_sell_signal(self, current, prev) -> Dict:
        """檢測賣出信號"""
        try:
            confidence = 0.0
            reasons = []
            
            # 1. MACD死叉 (30分)
            if (current['macd'] < current['macd_signal'] and 
                prev['macd'] >= prev['macd_signal']):
                confidence += 0.30
                reasons.append("MACD死叉")
            
            # 2. 成交量確認 (25分)
            if current['volume_ratio'] > 1.3:
                confidence += 0.25
                reasons.append(f"成交量放大{current['volume_ratio']:.1f}倍")
            
            # 3. RSI超買回調 (20分)
            if 55 <= current['rsi'] <= 75:
                confidence += 0.20
                reasons.append(f"RSI回調{current['rsi']:.1f}")
            
            # 4. 布林帶位置 (15分)
            if current['bb_position'] > 0.7:
                confidence += 0.15
                reasons.append("布林帶上軌阻力")
            
            # 5. 趨勢確認 (10分)
            if current['trend_up'] == 0:
                confidence += 0.10
                reasons.append("趨勢向下")
            
            # 只有信心度達到85%以上才發出信號
            if confidence >= self.min_confidence and len(reasons) >= 3:
                return {
                    'confidence': confidence,
                    'reasons': reasons
                }
            
            return None
            
        except Exception as e:
            logger.error(f"賣出信號檢測失敗: {e}")
            return None