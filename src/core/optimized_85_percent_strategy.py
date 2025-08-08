#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 優化版85%勝率策略 v2.0
基於測試結果的深度優化，專注於提高勝率
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class Optimized85PercentStrategy:
    """優化版85%勝率策略"""
    
    def __init__(self):
        # 基於分析結果的優化參數
        self.min_confidence_threshold = 78  # 降低到78分，平衡勝率和交易頻率
        
        # 成交量優化 - 基於成功交易的特徵
        self.volume_ratio_buy_min = 1.2   # 買入最低成交量比
        self.volume_ratio_sell_min = 1.0  # 賣出最低成交量比
        self.volume_trend_threshold = 0.1  # 成交量趋势閾值
        
        # RSI優化 - 基於歷史成功案例
        self.rsi_buy_range = (35, 55)     # 買入RSI範圍
        self.rsi_sell_range = (45, 70)    # 賣出RSI範圍
        self.rsi_momentum_threshold = 2    # RSI動能閾值
        
        # 布林帶優化
        self.bb_buy_range = (0.1, 0.6)    # 買入布林帶位置
        self.bb_sell_range = (0.4, 0.9)   # 賣出布林帶位置
        
        # MACD優化
        self.macd_strength_threshold = 500  # MACD強度閾值
        
        # 趨勢確認優化
        self.trend_strength_max = 0.025    # 最大趨勢強度（避免追高殺低）
        
        # 新增：止損和止盈邏輯
        self.enable_stop_loss = True
        self.stop_loss_pct = 0.02         # 2%止損
        self.take_profit_pct = 0.05       # 5%止盈
        
        # 新增：市場狀態過濾
        self.volatility_filter = True
        self.max_volatility_percentile = 0.8  # 最大波動率百分位
        
    def calculate_optimized_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算優化版技術指標"""
        df = df.copy()
        
        # 基本MACD
        ema_fast = df['close'].ewm(span=12).mean()
        ema_slow = df['close'].ewm(span=26).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 優化版成交量指標
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma20']
        df['volume_trend'] = df['volume_ma5'].pct_change(periods=3)
        
        # 成交量品質評分
        df['volume_score'] = np.where(
            (df['volume_ratio'] >= 1.2) & (df['volume_trend'] > 0.05),
            3,  # 優秀
            np.where(
                (df['volume_ratio'] >= 1.0) & (df['volume_trend'] > -0.05),
                2,  # 良好
                np.where(df['volume_ratio'] >= 0.8, 1, 0)  # 一般/差
            )
        )
        
        # RSI with 動能
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi_momentum'] = df['rsi'].diff(3)
        
        # 布林帶
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # 移動平均線
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma50'] = df['close'].rolling(window=50).mean()
        
        # 趨勢強度
        df['trend_strength'] = abs((df['close'] - df['ma20']) / df['ma20'])
        df['trend_direction'] = np.where(df['close'] > df['ma20'], 1, -1)
        
        # 市場波動率
        df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
        df['volatility_percentile'] = df['volatility'].rolling(window=100).rank(pct=True)
        
        # 價格位置（相對於近期高低點）
        df['high_20'] = df['high'].rolling(window=20).max()
        df['low_20'] = df['low'].rolling(window=20).min()
        df['price_position'] = (df['close'] - df['low_20']) / (df['high_20'] - df['low_20'])
        
        return df
    
    def _calculate_signal_confidence(self, row: pd.Series, signal_type: str) -> Tuple[float, List[str]]:
        """計算信號信心度"""
        score = 0
        reasons = []
        
        # 1. 成交量確認 (30分)
        volume_ratio = row.get('volume_ratio', 0)
        volume_score = row.get('volume_score', 0)
        
        if signal_type == 'buy':
            if volume_ratio >= self.volume_ratio_buy_min and volume_score >= 2:
                score += 30
                reasons.append(f"量比{volume_ratio:.1f}✓")
            elif volume_ratio >= 1.0:
                score += 20
                reasons.append(f"量比{volume_ratio:.1f}◐")
            elif volume_ratio >= 0.8:
                score += 10
                reasons.append(f"量比{volume_ratio:.1f}◑")
        else:
            if volume_ratio >= self.volume_ratio_sell_min and volume_score >= 1:
                score += 30
                reasons.append(f"量比{volume_ratio:.1f}✓")
            elif volume_ratio >= 0.8:
                score += 20
                reasons.append(f"量比{volume_ratio:.1f}◐")
            elif volume_ratio >= 0.6:
                score += 10
                reasons.append(f"量比{volume_ratio:.1f}◑")
        
        # 2. RSI確認 (25分)
        rsi = row.get('rsi', 50)
        rsi_momentum = row.get('rsi_momentum', 0)
        
        if signal_type == 'buy':
            if (self.rsi_buy_range[0] <= rsi <= self.rsi_buy_range[1] and 
                rsi_momentum > self.rsi_momentum_threshold):
                score += 25
                reasons.append(f"RSI{rsi:.0f}✓動能+")
            elif self.rsi_buy_range[0] <= rsi <= self.rsi_buy_range[1]:
                score += 20
                reasons.append(f"RSI{rsi:.0f}✓")
            elif 30 <= rsi <= 60:
                score += 15
                reasons.append(f"RSI{rsi:.0f}◐")
        else:
            if (self.rsi_sell_range[0] <= rsi <= self.rsi_sell_range[1] and 
                rsi_momentum < -self.rsi_momentum_threshold):
                score += 25
                reasons.append(f"RSI{rsi:.0f}✓動能-")
            elif self.rsi_sell_range[0] <= rsi <= self.rsi_sell_range[1]:
                score += 20
                reasons.append(f"RSI{rsi:.0f}✓")
            elif 40 <= rsi <= 70:
                score += 15
                reasons.append(f"RSI{rsi:.0f}◐")
        
        # 3. 布林帶位置 (20分)
        bb_position = row.get('bb_position', 0.5)
        
        if signal_type == 'buy':
            if self.bb_buy_range[0] <= bb_position <= self.bb_buy_range[1]:
                score += 20
                reasons.append(f"BB{bb_position:.1f}✓")
            elif bb_position <= 0.7:
                score += 15
                reasons.append(f"BB{bb_position:.1f}◐")
        else:
            if self.bb_sell_range[0] <= bb_position <= self.bb_sell_range[1]:
                score += 20
                reasons.append(f"BB{bb_position:.1f}✓")
            elif bb_position >= 0.3:
                score += 15
                reasons.append(f"BB{bb_position:.1f}◐")
        
        # 4. MACD強度 (15分)
        macd_hist = abs(row.get('macd_hist', 0))
        if macd_hist >= self.macd_strength_threshold:
            score += 15
            reasons.append("MACD強度✓")
        elif macd_hist >= self.macd_strength_threshold * 0.7:
            score += 10
            reasons.append("MACD強度◐")
        
        # 5. 趨勢確認 (10分)
        trend_strength = row.get('trend_strength', 0)
        trend_direction = row.get('trend_direction', 0)
        
        if trend_strength <= self.trend_strength_max:
            if signal_type == 'buy' and trend_direction >= 0:
                score += 10
                reasons.append("趨勢✓")
            elif signal_type == 'sell' and trend_direction <= 0:
                score += 10
                reasons.append("趨勢✓")
            else:
                score += 5
                reasons.append("趨勢◐")
        
        # 6. 市場狀態過濾 (額外分數或扣分)
        if self.volatility_filter:
            volatility_percentile = row.get('volatility_percentile', 0.5)
            if volatility_percentile <= self.max_volatility_percentile:
                if 0.3 <= volatility_percentile <= 0.7:
                    score += 5
                    reasons.append("波動適中+5")
            else:
                score -= 10
                reasons.append("波動過高-10")
        
        # 7. 價格位置確認 (額外分數)
        price_position = row.get('price_position', 0.5)
        if signal_type == 'buy' and price_position <= 0.4:
            score += 5
            reasons.append("低位買入+5")
        elif signal_type == 'sell' and price_position >= 0.6:
            score += 5
            reasons.append("高位賣出+5")
        
        return score, reasons
    
    def _should_stop_loss_or_take_profit(self, current_price: float, entry_price: float, signal_type: str) -> Tuple[bool, str]:
        """檢查是否應該止損或止盈"""
        if not self.enable_stop_loss:
            return False, ""
        
        if signal_type == 'buy':  # 檢查賣出止損/止盈
            pct_change = (current_price - entry_price) / entry_price
            if pct_change <= -self.stop_loss_pct:
                return True, f"止損{pct_change*100:.1f}%"
            elif pct_change >= self.take_profit_pct:
                return True, f"止盈{pct_change*100:.1f}%"
        else:  # 檢查買入止損/止盈
            pct_change = (entry_price - current_price) / entry_price
            if pct_change <= -self.stop_loss_pct:
                return True, f"止損{pct_change*100:.1f}%"
            elif pct_change >= self.take_profit_pct:
                return True, f"止盈{pct_change*100:.1f}%"
        
        return False, ""
    
    def detect_optimized_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """檢測優化版85%勝率信號"""
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 計算優化版指標
        df = self.calculate_optimized_indicators(df)
        
        signals = []
        current_position = 0
        trade_sequence = 0
        entry_price = 0
        entry_signal_type = ""
        
        for i in range(50, len(df)):
            current_row = df.iloc[i]
            previous_row = df.iloc[i-1]
            
            # 檢查止損/止盈
            if current_position == 1 and entry_price > 0:
                should_exit, exit_reason = self._should_stop_loss_or_take_profit(
                    current_row['close'], entry_price, entry_signal_type
                )
                
                if should_exit:
                    current_position = 0
                    
                    signal = {
                        'datetime': current_row.get('timestamp', i),
                        'close': current_row['close'],
                        'signal_type': 'sell' if entry_signal_type == 'buy' else 'buy',
                        'trade_sequence': trade_sequence,
                        'macd': current_row['macd'],
                        'macd_signal': current_row['macd_signal'],
                        'macd_hist': current_row['macd_hist'],
                        'validation_info': f"優化確認: {exit_reason}",
                        'signal_strength': 100,  # 止損/止盈信號強度設為100
                        'strategy_version': 'Optimized85%',
                        'exit_reason': exit_reason
                    }
                    signals.append(signal)
                    logger.info(f"✅ 優化{exit_reason}: {current_row['close']:,.0f}")
                    continue
            
            # 檢查MACD買進信號
            macd_buy_signal = (
                current_row['macd'] > current_row['macd_signal'] and 
                previous_row['macd'] <= previous_row['macd_signal'] and
                current_row['macd_hist'] > 0
            )
            
            if macd_buy_signal and current_position == 0:
                score, reasons = self._calculate_signal_confidence(current_row, 'buy')
                
                if score >= self.min_confidence_threshold:
                    trade_sequence += 1
                    current_position = 1
                    entry_price = current_row['close']
                    entry_signal_type = 'buy'
                    
                    signal = {
                        'datetime': current_row.get('timestamp', i),
                        'close': current_row['close'],
                        'signal_type': 'buy',
                        'trade_sequence': trade_sequence,
                        'macd': current_row['macd'],
                        'macd_signal': current_row['macd_signal'],
                        'macd_hist': current_row['macd_hist'],
                        'validation_info': f"優化確認({score}/{self.min_confidence_threshold}): {' '.join(reasons)}",
                        'signal_strength': score,
                        'strategy_version': 'Optimized85%'
                    }
                    signals.append(signal)
                    logger.info(f"✅ 優化買進 #{trade_sequence}: {current_row['close']:,.0f} - 信心度{score}")
            
            # 檢查MACD賣出信號
            macd_sell_signal = (
                current_row['macd'] < current_row['macd_signal'] and 
                previous_row['macd'] >= previous_row['macd_signal'] and
                current_row['macd_hist'] < 0
            )
            
            if macd_sell_signal and current_position == 1:
                score, reasons = self._calculate_signal_confidence(current_row, 'sell')
                
                if score >= self.min_confidence_threshold:
                    current_position = 0
                    entry_price = 0
                    entry_signal_type = ""
                    
                    signal = {
                        'datetime': current_row.get('timestamp', i),
                        'close': current_row['close'],
                        'signal_type': 'sell',
                        'trade_sequence': trade_sequence,
                        'macd': current_row['macd'],
                        'macd_signal': current_row['macd_signal'],
                        'macd_hist': current_row['macd_hist'],
                        'validation_info': f"優化確認({score}/{self.min_confidence_threshold}): {' '.join(reasons)}",
                        'signal_strength': score,
                        'strategy_version': 'Optimized85%'
                    }
                    signals.append(signal)
                    logger.info(f"✅ 優化賣出 #{trade_sequence}: {current_row['close']:,.0f} - 信心度{score}")
        
        return pd.DataFrame(signals)