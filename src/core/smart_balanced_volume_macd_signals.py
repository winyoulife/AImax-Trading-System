#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能平衡成交量增強MACD交易信號檢測系統
目標：在保持高勝率的同時增加交易機會
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class SmartBalancedVolumeAnalyzer:
    """智能平衡成交量分析器"""
    
    @staticmethod
    def calculate_smart_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """計算智能平衡技術指標"""
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
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # 市場趨勢指標
        df['ma50'] = df['close'].rolling(window=50).mean()
        df['ma200'] = df['close'].rolling(window=200).mean()
        df['trend_strength'] = (df['close'] - df['ma50']) / df['ma50']
        
        # 價格動能指標
        df['price_momentum_5'] = df['close'].pct_change(periods=5)
        df['price_momentum_10'] = df['close'].pct_change(periods=10)
        
        # 市場波動性
        df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
        df['volatility_ma'] = df['volatility'].rolling(window=10).mean()
        df['volatility_ratio'] = df['volatility'] / df['volatility_ma']
        
        # MACD強度指標
        df['macd_strength'] = abs(df['macd_hist']) / df['close'] * 10000
        df['macd_acceleration'] = df['macd_hist'].diff()
        
        # 成交量價格確認
        df['volume_price_trend'] = np.where(
            (df['close'].pct_change() > 0) & (df['volume_trend'] > 0), 1,
            np.where((df['close'].pct_change() < 0) & (df['volume_trend'] > 0), -1, 0)
        )
        
        # 新增：市場強度指標
        df['market_strength'] = (
            (df['rsi'] - 50) / 50 * 0.3 +
            df['trend_strength'] * 0.4 +
            (df['volume_ratio'] - 1) * 0.3
        )
        
        return df
    
    @staticmethod
    def smart_signal_validation(row: pd.Series, signal_type: str, market_context: Dict) -> Tuple[bool, str, float]:
        """
        智能平衡信號驗證
        根據市場條件動態調整評分標準
        """
        try:
            score = 0
            reasons = []
            
            # 根據市場強度動態調整閾值
            market_strength = row.get('market_strength', 0)
            volatility_ratio = row.get('volatility_ratio', 1)
            
            # 動態調整基準分數
            if abs(market_strength) > 0.1:  # 強勢市場
                base_threshold = 68
                strength_bonus = 5
            else:  # 弱勢市場
                base_threshold = 72
                strength_bonus = 0
            
            # 1. 成交量確認 (25分)
            volume_ratio = row.get('volume_ratio', 0)
            dynamic_volume_threshold = 0.95 + (volatility_ratio - 1) * 0.15
            dynamic_volume_threshold = max(0.8, min(1.3, dynamic_volume_threshold))
            
            if volume_ratio >= dynamic_volume_threshold * 1.1:
                score += 25
                reasons.append(f"量比{volume_ratio:.1f}✓")
            elif volume_ratio >= dynamic_volume_threshold:
                score += 18
                reasons.append(f"量比{volume_ratio:.1f}◐")
            elif volume_ratio >= dynamic_volume_threshold * 0.8:
                score += 10
                reasons.append(f"量比{volume_ratio:.1f}◑")
            else:
                reasons.append(f"量比{volume_ratio:.1f}✗")
            
            # 2. 成交量趨勢 (20分)
            volume_trend = row.get('volume_trend', 0)
            if signal_type == 'buy':
                if volume_trend > 0.05:
                    score += 20
                    reasons.append(f"量勢{volume_trend:.1%}✓")
                elif volume_trend > 0:
                    score += 12
                    reasons.append(f"量勢{volume_trend:.1%}◐")
                elif volume_trend > -0.05:
                    score += 6
                    reasons.append(f"量勢{volume_trend:.1%}◑")
                else:
                    reasons.append(f"量勢{volume_trend:.1%}✗")
            else:
                if volume_trend > -0.1:
                    score += 20
                    reasons.append(f"量勢{volume_trend:.1%}✓")
                elif volume_trend > -0.2:
                    score += 12
                    reasons.append(f"量勢{volume_trend:.1%}◐")
                else:
                    reasons.append(f"量勢{volume_trend:.1%}✗")
            
            # 3. RSI確認 (15分)
            rsi = row.get('rsi', 50)
            if signal_type == 'buy':
                if 25 <= rsi <= 75:
                    score += 15
                    reasons.append(f"RSI{rsi:.0f}✓")
                elif 20 <= rsi <= 80:
                    score += 10
                    reasons.append(f"RSI{rsi:.0f}◐")
                else:
                    reasons.append(f"RSI{rsi:.0f}✗")
            else:
                if 25 <= rsi <= 75:
                    score += 15
                    reasons.append(f"RSI{rsi:.0f}✓")
                elif 20 <= rsi <= 80:
                    score += 10
                    reasons.append(f"RSI{rsi:.0f}◐")
                else:
                    reasons.append(f"RSI{rsi:.0f}✗")
            
            # 4. 布林帶位置 (15分)
            bb_position = row.get('bb_position', 0.5)
            bb_width = row.get('bb_width', 0.1)
            
            if 0.02 <= bb_width <= 0.25:
                if signal_type == 'buy':
                    if 0.05 <= bb_position <= 0.65:
                        score += 15
                        reasons.append(f"BB位置{bb_position:.1f}✓")
                    elif 0 <= bb_position <= 0.8:
                        score += 10
                        reasons.append(f"BB位置{bb_position:.1f}◐")
                    else:
                        reasons.append(f"BB位置{bb_position:.1f}✗")
                else:
                    if 0.35 <= bb_position <= 0.95:
                        score += 15
                        reasons.append(f"BB位置{bb_position:.1f}✓")
                    elif 0.2 <= bb_position <= 1.0:
                        score += 10
                        reasons.append(f"BB位置{bb_position:.1f}◐")
                    else:
                        reasons.append(f"BB位置{bb_position:.1f}✗")
            else:
                score += 8
                reasons.append(f"BB寬度{bb_width:.2f}◐")
            
            # 5. 市場趨勢確認 (15分)
            trend_strength = row.get('trend_strength', 0)
            ma50 = row.get('ma50', 0)
            ma200 = row.get('ma200', 0)
            
            if signal_type == 'buy':
                if (trend_strength > -0.03 and ma50 > ma200) or trend_strength > 0.01:
                    score += 15
                    reasons.append(f"趨勢{trend_strength:.1%}✓")
                elif trend_strength > -0.06:
                    score += 10
                    reasons.append(f"趨勢{trend_strength:.1%}◐")
                elif trend_strength > -0.1:
                    score += 5
                    reasons.append(f"趨勢{trend_strength:.1%}◑")
                else:
                    reasons.append(f"趨勢{trend_strength:.1%}✗")
            else:
                if (trend_strength < 0.03 and ma50 < ma200) or trend_strength < -0.01:
                    score += 15
                    reasons.append(f"趨勢{trend_strength:.1%}✓")
                elif trend_strength < 0.06:
                    score += 10
                    reasons.append(f"趨勢{trend_strength:.1%}◐")
                elif trend_strength < 0.1:
                    score += 5
                    reasons.append(f"趨勢{trend_strength:.1%}◑")
                else:
                    reasons.append(f"趨勢{trend_strength:.1%}✗")
            
            # 6. MACD強度確認 (10分)
            macd_strength = row.get('macd_strength', 0)
            macd_acceleration = row.get('macd_acceleration', 0)
            
            if signal_type == 'buy':
                if macd_strength > 2 and macd_acceleration > 0:
                    score += 10
                    reasons.append(f"MACD強度{macd_strength:.1f}✓")
                elif macd_strength > 1:
                    score += 6
                    reasons.append(f"MACD強度{macd_strength:.1f}◐")
                else:
                    reasons.append(f"MACD強度{macd_strength:.1f}✗")
            else:
                if macd_strength > 2 and macd_acceleration < 0:
                    score += 10
                    reasons.append(f"MACD強度{macd_strength:.1f}✓")
                elif macd_strength > 1:
                    score += 6
                    reasons.append(f"MACD強度{macd_strength:.1f}◐")
                else:
                    reasons.append(f"MACD強度{macd_strength:.1f}✗")
            
            # 加上市場強度獎勵分數
            score += strength_bonus
            if strength_bonus > 0:
                reasons.append(f"市場強度獎勵+{strength_bonus}")
            
            # 動態閾值評估
            passed = score >= base_threshold
            info = f"智能確認({score}/{base_threshold}): {' '.join(reasons)}"
            
            return passed, info, score
            
        except Exception as e:
            logger.error(f"智能平衡信號驗證失敗: {e}")
            return False, f"驗證錯誤: {e}", 0

class SmartBalancedVolumeEnhancedMACDSignals:
    """智能平衡成交量增強MACD信號檢測器"""
    
    def __init__(self):
        self.volume_analyzer = SmartBalancedVolumeAnalyzer()
        
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
    
    def analyze_market_context(self, df: pd.DataFrame, current_index: int) -> Dict:
        """分析市場環境上下文"""
        try:
            if current_index < 50:
                return {'trend': 'unknown', 'volatility': 'normal', 'strength': 0}
            
            recent_data = df.iloc[max(0, current_index-20):current_index+1]
            
            # 趨勢分析
            ma50_slope = (recent_data['ma50'].iloc[-1] - recent_data['ma50'].iloc[-10]) / recent_data['ma50'].iloc[-10]
            
            if ma50_slope > 0.02:
                trend = 'bullish'
            elif ma50_slope < -0.02:
                trend = 'bearish'
            else:
                trend = 'sideways'
            
            # 波動性分析
            avg_volatility = recent_data['volatility'].mean()
            if avg_volatility > 0.03:
                volatility = 'high'
            elif avg_volatility < 0.015:
                volatility = 'low'
            else:
                volatility = 'normal'
            
            return {
                'trend': trend,
                'volatility': volatility,
                'strength': abs(ma50_slope),
                'avg_volatility': avg_volatility
            }
            
        except Exception as e:
            logger.error(f"市場環境分析失敗: {e}")
            return {'trend': 'unknown', 'volatility': 'normal', 'strength': 0}
    
    def detect_smart_balanced_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """檢測智能平衡成交量增強MACD信號"""
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 重置狀態
        self.current_position = 0
        self.trade_sequence = 0
        self.trade_history = []
        
        # 計算所有指標
        df = self.calculate_macd(df)
        df = self.volume_analyzer.calculate_smart_indicators(df)
        
        signals = []
        
        for i in range(1, len(df)):
            current_row = df.iloc[i]
            previous_row = df.iloc[i-1]
            
            # 分析市場環境
            market_context = self.analyze_market_context(df, i)
            
            # 檢查MACD買進信號
            macd_buy_signal = self._check_macd_buy_signal(current_row, previous_row)
            if macd_buy_signal and self.current_position == 0:
                # 智能平衡驗證
                passed, info, score = self.volume_analyzer.smart_signal_validation(
                    current_row, 'buy', market_context
                )
                
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
                        'signal_strength': score,
                        'market_context': market_context
                    }
                    signals.append(signal)
                    self.trade_history.append(signal)
                    
                    logger.info(f"✅ 智能確認買進 #{self.trade_sequence}: {current_row['close']:,.0f} - {info}")
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
                        'signal_strength': score,
                        'market_context': market_context
                    }
                    signals.append(signal)
                    
                    logger.info(f"❌ 買進信號被拒絕: {current_row['close']:,.0f} - {info}")
            
            # 檢查MACD賣出信號
            macd_sell_signal = self._check_macd_sell_signal(current_row, previous_row)
            if macd_sell_signal and self.current_position == 1:
                # 智能平衡驗證
                passed, info, score = self.volume_analyzer.smart_signal_validation(
                    current_row, 'sell', market_context
                )
                
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
                        'signal_strength': score,
                        'market_context': market_context
                    }
                    signals.append(signal)
                    self.trade_history.append(signal)
                    
                    logger.info(f"✅ 智能確認賣出 #{self.trade_sequence}: {current_row['close']:,.0f} - {info}")
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
                        'signal_strength': score,
                        'market_context': market_context
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