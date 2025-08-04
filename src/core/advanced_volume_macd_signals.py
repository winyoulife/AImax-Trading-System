#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
進階成交量增強MACD交易信號檢測系統
目標：將勝率從66.7%提升到75%+
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class AdvancedVolumeAnalyzer:
    """進階成交量分析器"""
    
    @staticmethod
    def calculate_advanced_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """計算進階技術指標"""
        df = df.copy()
        
        # 基本成交量指標
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma20']
        
        # 成交量趨勢強度
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_trend'] = df['volume_ma5'].pct_change(periods=3)
        
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
        
        # OBV能量潮
        df['obv'] = 0.0
        for i in range(1, len(df)):
            if df.iloc[i]['close'] > df.iloc[i-1]['close']:
                df.iloc[i, df.columns.get_loc('obv')] = df.iloc[i-1]['obv'] + df.iloc[i]['volume']
            elif df.iloc[i]['close'] < df.iloc[i-1]['close']:
                df.iloc[i, df.columns.get_loc('obv')] = df.iloc[i-1]['obv'] - df.iloc[i]['volume']
            else:
                df.iloc[i, df.columns.get_loc('obv')] = df.iloc[i-1]['obv']
        
        df['obv_ma'] = df['obv'].rolling(window=10).mean()
        df['obv_trend'] = df['obv'].pct_change(periods=5)
        
        # 價格動能
        df['price_momentum'] = df['close'].pct_change(periods=5)
        
        # 市場波動性
        df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
        
        return df
    
    @staticmethod
    def advanced_signal_validation(row: pd.Series, signal_type: str) -> Tuple[bool, str, float]:
        """
        進階信號驗證
        
        Returns:
            (是否通過, 驗證信息, 信號強度分數)
        """
        try:
            score = 0
            reasons = []
            
            # 1. 成交量確認 (30分)
            volume_ratio = row.get('volume_ratio', 0)
            if volume_ratio >= 1.3:  # 適中閾值
                score += 30
                reasons.append(f"量比{volume_ratio:.1f}✓")
            else:
                reasons.append(f"量比{volume_ratio:.1f}✗")
            
            # 2. 成交量趨勢 (25分)
            volume_trend = row.get('volume_trend', 0)
            if signal_type == 'buy':
                if volume_trend > 0.1:  # 買進需要成交量明顯增加
                    score += 25
                    reasons.append(f"量勢{volume_trend:.1%}✓")
                else:
                    reasons.append(f"量勢{volume_trend:.1%}✗")
            else:
                if volume_trend > -0.2:  # 賣出允許成交量輕微下降
                    score += 25
                    reasons.append(f"量勢{volume_trend:.1%}✓")
                else:
                    reasons.append(f"量勢{volume_trend:.1%}✗")
            
            # 3. RSI確認 (20分)
            rsi = row.get('rsi', 50)
            if signal_type == 'buy':
                if 30 <= rsi <= 70:  # 避免超買超賣
                    score += 20
                    reasons.append(f"RSI{rsi:.0f}✓")
                else:
                    reasons.append(f"RSI{rsi:.0f}✗")
            else:
                if 30 <= rsi <= 70:
                    score += 20
                    reasons.append(f"RSI{rsi:.0f}✓")
                else:
                    reasons.append(f"RSI{rsi:.0f}✗")
            
            # 4. 布林帶位置 (15分) - 放寬條件
            bb_position = row.get('bb_position', 0.5)
            if signal_type == 'buy':
                if 0.1 <= bb_position <= 0.6:  # 放寬買入範圍
                    score += 15
                    reasons.append(f"BB位置{bb_position:.1f}✓")
                else:
                    reasons.append(f"BB位置{bb_position:.1f}✗")
            else:
                if 0.4 <= bb_position <= 0.9:  # 放寬賣出範圍
                    score += 15
                    reasons.append(f"BB位置{bb_position:.1f}✓")
                else:
                    reasons.append(f"BB位置{bb_position:.1f}✗")
            
            # 5. OBV趨勢 (10分)
            obv_trend = row.get('obv_trend', 0)
            if signal_type == 'buy':
                if obv_trend > 0:
                    score += 10
                    reasons.append(f"OBV勢{obv_trend:.1%}✓")
                else:
                    reasons.append(f"OBV勢{obv_trend:.1%}✗")
            else:
                if obv_trend < 0:
                    score += 10
                    reasons.append(f"OBV勢{obv_trend:.1%}✓")
                else:
                    reasons.append(f"OBV勢{obv_trend:.1%}✗")
            
            # 總分評估 (需要70分以上才通過，平衡過濾效果)
            passed = score >= 70
            info = f"進階確認({score}/100): {' '.join(reasons)}"
            
            return passed, info, score
            
        except Exception as e:
            logger.error(f"進階信號驗證失敗: {e}")
            return False, f"驗證錯誤: {e}", 0

class AdvancedVolumeEnhancedMACDSignals:
    """進階成交量增強MACD信號檢測器"""
    
    def __init__(self):
        self.volume_analyzer = AdvancedVolumeAnalyzer()
        
        # 持倉狀態追蹤
        self.current_position = 0
        self.trade_sequence = 0
        self.trade_history = []
        
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
    
    def detect_advanced_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """檢測進階成交量增強MACD信號"""
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 重置狀態
        self.current_position = 0
        self.trade_sequence = 0
        self.trade_history = []
        
        # 計算所有指標
        df = self.calculate_macd(df)
        df = self.volume_analyzer.calculate_advanced_indicators(df)
        
        signals = []
        
        for i in range(1, len(df)):
            current_row = df.iloc[i]
            previous_row = df.iloc[i-1]
            
            # 檢查MACD買進信號
            macd_buy_signal = self._check_macd_buy_signal(current_row, previous_row)
            if macd_buy_signal and self.current_position == 0:
                # 進階驗證
                passed, info, score = self.volume_analyzer.advanced_signal_validation(current_row, 'buy')
                
                if passed:
                    # 執行買進
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
                    self.trade_history.append(signal)
                    
                    logger.info(f"✅ 進階確認買進 #{self.trade_sequence}: {current_row['close']:,.0f} - {info}")
                else:
                    # 信號被拒絕
                    signal = {
                        'datetime': current_row['timestamp'],
                        'close': current_row['close'],
                        'signal_type': 'buy_rejected',
                        'trade_sequence': 0,
                        'macd': current_row['macd'],
                        'macd_signal': current_row['macd_signal'],
                        'macd_hist': current_row['macd_hist'],
                        'volume_confirmed': False,
                        'validation_info': info,
                        'signal_strength': score
                    }
                    signals.append(signal)
                    
                    logger.info(f"❌ 買進信號被拒絕: {current_row['close']:,.0f} - {info}")
            
            # 檢查MACD賣出信號
            macd_sell_signal = self._check_macd_sell_signal(current_row, previous_row)
            if macd_sell_signal and self.current_position == 1:
                # 進階驗證
                passed, info, score = self.volume_analyzer.advanced_signal_validation(current_row, 'sell')
                
                if passed:
                    # 執行賣出
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
                    self.trade_history.append(signal)
                    
                    logger.info(f"✅ 進階確認賣出 #{self.trade_sequence}: {current_row['close']:,.0f} - {info}")
                else:
                    # 信號被拒絕
                    signal = {
                        'datetime': current_row['timestamp'],
                        'close': current_row['close'],
                        'signal_type': 'sell_rejected',
                        'trade_sequence': 0,
                        'macd': current_row['macd'],
                        'macd_signal': current_row['macd_signal'],
                        'macd_hist': current_row['macd_hist'],
                        'volume_confirmed': False,
                        'validation_info': info,
                        'signal_strength': score
                    }
                    signals.append(signal)
                    
                    logger.info(f"❌ 賣出信號被拒絕: {current_row['close']:,.0f} - {info}")
        
        return pd.DataFrame(signals)
    
    def _check_macd_buy_signal(self, current_row: pd.Series, previous_row: pd.Series) -> bool:
        """檢查MACD買進信號"""
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
        """檢查MACD賣出信號"""
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