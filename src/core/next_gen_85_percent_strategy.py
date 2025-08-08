#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 次世代85%+勝率策略
基於現有75%勝率策略的深度優化版本
目標：突破85%勝率並保持獲利能力
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class NextGen85PercentStrategy:
    """次世代85%+勝率策略"""
    
    def __init__(self):
        # 基於測試結果的優化參數
        self.min_confidence_threshold = 85  # 提高到85分
        self.volume_threshold_multiplier = 1.2  # 提高成交量要求
        self.rsi_optimal_range = (35, 65)  # 縮小RSI範圍
        self.bb_optimal_range = (0.2, 0.8)  # 優化布林帶範圍
        
        # 新增：市場狀態感知
        self.market_volatility_threshold = 0.02
        self.trend_strength_threshold = 0.015
        
        # 新增：時間過濾
        self.avoid_weekend_hours = True
        self.optimal_trading_hours = [(9, 17), (21, 23)]  # 台灣時間最佳交易時段
        
        # 新增：動態調整機制
        self.recent_performance_window = 10
        self.performance_adjustment_factor = 0.1
        
    def calculate_enhanced_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算增強版技術指標"""
        df = df.copy()
        
        # 基本MACD
        ema_fast = df['close'].ewm(span=12).mean()
        ema_slow = df['close'].ewm(span=26).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 增強版成交量指標
        df['volume_ma20'] = df['volume'].rolling(window=20).mean()
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma20']
        df['volume_trend'] = df['volume_ma5'].pct_change(periods=3)
        
        # 新增：成交量品質指標
        df['volume_quality'] = (
            (df['volume_ratio'] > 1.0).astype(int) * 0.3 +
            (df['volume_trend'] > 0).astype(int) * 0.3 +
            (df['volume'] > df['volume'].rolling(50).quantile(0.6)).astype(int) * 0.4
        )
        
        # RSI with 動態調整
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 新增：RSI動能
        df['rsi_momentum'] = df['rsi'].diff(3)
        df['rsi_divergence'] = self._calculate_rsi_divergence(df)
        
        # 增強版布林帶
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # 新增：布林帶擠壓檢測
        df['bb_squeeze'] = df['bb_width'] < df['bb_width'].rolling(20).quantile(0.2)
        
        # 多重移動平均線
        df['ma9'] = df['close'].rolling(window=9).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma50'] = df['close'].rolling(window=50).mean()
        df['ma200'] = df['close'].rolling(window=200).mean()
        
        # 新增：趨勢強度和一致性
        df['trend_strength'] = abs((df['close'] - df['ma20']) / df['ma20'])
        df['trend_consistency'] = (
            ((df['ma9'] > df['ma20']) & (df['ma20'] > df['ma50']) & (df['ma50'] > df['ma200'])).astype(int) -
            ((df['ma9'] < df['ma20']) & (df['ma20'] < df['ma50']) & (df['ma50'] < df['ma200'])).astype(int)
        )
        
        # 新增：市場波動率
        df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
        df['volatility_percentile'] = df['volatility'].rolling(window=100).rank(pct=True)
        
        # 新增：價格動能
        df['price_momentum'] = df['close'].pct_change(5)
        df['momentum_acceleration'] = df['price_momentum'].diff(3)
        
        # 新增：支撐阻力位
        df['support_level'] = df['low'].rolling(window=20).min()
        df['resistance_level'] = df['high'].rolling(window=20).max()
        df['support_distance'] = (df['close'] - df['support_level']) / df['close']
        df['resistance_distance'] = (df['resistance_level'] - df['close']) / df['close']
        
        return df
    
    def _calculate_rsi_divergence(self, df: pd.DataFrame) -> pd.Series:
        """計算RSI背離"""
        try:
            rsi_peaks = df['rsi'].rolling(window=5).max() == df['rsi']
            price_peaks = df['close'].rolling(window=5).max() == df['close']
            
            # 簡化的背離檢測
            divergence = np.where(
                rsi_peaks & (df['rsi'].shift(10) > df['rsi']) & (df['close'].shift(10) < df['close']),
                1,  # 看跌背離
                np.where(
                    rsi_peaks & (df['rsi'].shift(10) < df['rsi']) & (df['close'].shift(10) > df['close']),
                    -1,  # 看漲背離
                    0
                )
            )
            return pd.Series(divergence, index=df.index)
        except:
            return pd.Series(0, index=df.index)
    
    def _is_optimal_trading_time(self, timestamp) -> bool:
        """檢查是否為最佳交易時間"""
        try:
            if isinstance(timestamp, (int, float)):
                return True  # 如果是數字索引，跳過時間檢查
            
            if not isinstance(timestamp, pd.Timestamp):
                timestamp = pd.to_datetime(timestamp)
            
            hour = timestamp.hour
            weekday = timestamp.weekday()
            
            # 避免週末（如果啟用）
            if self.avoid_weekend_hours and weekday >= 5:
                return False
            
            # 檢查是否在最佳交易時段
            for start_hour, end_hour in self.optimal_trading_hours:
                if start_hour <= hour <= end_hour:
                    return True
            
            return False
        except:
            return True  # 出錯時默認允許交易
    
    def _calculate_market_context_score(self, row: pd.Series) -> float:
        """計算市場環境評分"""
        score = 0
        
        # 波動率評分 (0-20分)
        volatility_percentile = row.get('volatility_percentile', 0.5)
        if 0.3 <= volatility_percentile <= 0.7:  # 適中波動率
            score += 20
        elif 0.2 <= volatility_percentile <= 0.8:
            score += 15
        elif volatility_percentile < 0.2 or volatility_percentile > 0.8:
            score += 5  # 極端波動率扣分
        
        # 趨勢一致性評分 (0-15分)
        trend_consistency = row.get('trend_consistency', 0)
        if abs(trend_consistency) == 1:  # 完全一致的趨勢
            score += 15
        elif trend_consistency == 0:  # 混亂趨勢
            score += 5
        
        # 布林帶擠壓評分 (0-10分)
        if row.get('bb_squeeze', False):
            score += 10  # 擠壓後通常有大行情
        
        return score
    
    def _enhanced_signal_validation(self, row: pd.Series, signal_type: str, recent_performance: List) -> Tuple[bool, str, float]:
        """增強版信號驗證"""
        score = 0
        reasons = []
        
        # 1. 時間過濾 (必要條件)
        if not self._is_optimal_trading_time(row.get('timestamp', 0)):
            return False, "非最佳交易時間", 0
        
        # 2. 成交量確認 (25分) - 提高標準
        volume_ratio = row.get('volume_ratio', 0)
        volume_quality = row.get('volume_quality', 0)
        
        if volume_ratio >= 1.8 and volume_quality >= 0.7:
            score += 25
            reasons.append(f"量比{volume_ratio:.1f}✓品質{volume_quality:.1f}✓")
        elif volume_ratio >= 1.5 and volume_quality >= 0.5:
            score += 20
            reasons.append(f"量比{volume_ratio:.1f}◐品質{volume_quality:.1f}◐")
        elif volume_ratio >= 1.2:
            score += 15
            reasons.append(f"量比{volume_ratio:.1f}◑")
        else:
            reasons.append(f"量比{volume_ratio:.1f}✗")
        
        # 3. RSI優化確認 (20分)
        rsi = row.get('rsi', 50)
        rsi_momentum = row.get('rsi_momentum', 0)
        rsi_divergence = row.get('rsi_divergence', 0)
        
        if signal_type == 'buy':
            if 30 <= rsi <= 50 and rsi_momentum > 0:
                score += 20
                reasons.append(f"RSI{rsi:.0f}✓動能+")
            elif 25 <= rsi <= 55:
                score += 15
                reasons.append(f"RSI{rsi:.0f}◐")
            elif rsi_divergence == -1:  # 看漲背離
                score += 25
                reasons.append(f"RSI看漲背離✓")
        else:
            if 50 <= rsi <= 70 and rsi_momentum < 0:
                score += 20
                reasons.append(f"RSI{rsi:.0f}✓動能-")
            elif 45 <= rsi <= 75:
                score += 15
                reasons.append(f"RSI{rsi:.0f}◐")
            elif rsi_divergence == 1:  # 看跌背離
                score += 25
                reasons.append(f"RSI看跌背離✓")
        
        # 4. 布林帶精確定位 (15分)
        bb_position = row.get('bb_position', 0.5)
        bb_squeeze = row.get('bb_squeeze', False)
        
        if signal_type == 'buy':
            if 0.1 <= bb_position <= 0.4:
                score += 15
                reasons.append(f"BB位置{bb_position:.1f}✓")
            elif bb_position <= 0.6:
                score += 10
                reasons.append(f"BB位置{bb_position:.1f}◐")
        else:
            if 0.6 <= bb_position <= 0.9:
                score += 15
                reasons.append(f"BB位置{bb_position:.1f}✓")
            elif bb_position >= 0.4:
                score += 10
                reasons.append(f"BB位置{bb_position:.1f}◐")
        
        if bb_squeeze:
            score += 5
            reasons.append("BB擠壓+5")
        
        # 5. 趨勢強度確認 (15分)
        trend_strength = row.get('trend_strength', 0)
        trend_consistency = row.get('trend_consistency', 0)
        
        if signal_type == 'buy':
            if trend_consistency >= 0 and trend_strength < 0.03:
                score += 15
                reasons.append("趨勢✓")
            elif trend_consistency >= -1:
                score += 10
                reasons.append("趨勢◐")
        else:
            if trend_consistency <= 0 and trend_strength < 0.03:
                score += 15
                reasons.append("趨勢✓")
            elif trend_consistency <= 1:
                score += 10
                reasons.append("趨勢◐")
        
        # 6. MACD動能確認 (10分)
        macd_hist = abs(row.get('macd_hist', 0))
        if macd_hist > 1000:  # 調整閾值
            score += 10
            reasons.append(f"MACD強度✓")
        elif macd_hist > 500:
            score += 5
            reasons.append(f"MACD強度◐")
        
        # 7. 市場環境評分 (0-45分)
        market_score = self._calculate_market_context_score(row)
        score += market_score
        if market_score >= 35:
            reasons.append("市場環境優✓")
        elif market_score >= 25:
            reasons.append("市場環境良◐")
        
        # 8. 支撐阻力確認 (10分)
        support_distance = row.get('support_distance', 0)
        resistance_distance = row.get('resistance_distance', 0)
        
        if signal_type == 'buy' and support_distance <= 0.02:
            score += 10
            reasons.append("近支撐✓")
        elif signal_type == 'sell' and resistance_distance <= 0.02:
            score += 10
            reasons.append("近阻力✓")
        
        # 9. 動態調整基於近期表現
        if recent_performance:
            recent_win_rate = sum(1 for p in recent_performance[-5:] if p > 0) / min(len(recent_performance[-5:]), 5)
            if recent_win_rate >= 0.8:
                score += 5
                reasons.append("近期表現佳+5")
            elif recent_win_rate <= 0.4:
                score -= 5
                reasons.append("近期表現差-5")
        
        # 最終評估
        passed = score >= self.min_confidence_threshold
        info = f"次世代確認({score}/{self.min_confidence_threshold}): {' '.join(reasons)}"
        
        return passed, info, score
    
    def detect_next_gen_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """檢測次世代85%+勝率信號"""
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 計算增強版指標
        df = self.calculate_enhanced_indicators(df)
        
        signals = []
        current_position = 0
        trade_sequence = 0
        recent_performance = []
        
        for i in range(50, len(df)):  # 需要足夠的歷史數據
            current_row = df.iloc[i]
            previous_row = df.iloc[i-1]
            
            # 檢查MACD買進信號
            macd_buy_signal = (
                current_row['macd'] > current_row['macd_signal'] and 
                previous_row['macd'] <= previous_row['macd_signal'] and
                current_row['macd_hist'] > 0
            )
            
            if macd_buy_signal and current_position == 0:
                passed, info, score = self._enhanced_signal_validation(
                    current_row, 'buy', recent_performance
                )
                
                if passed:
                    trade_sequence += 1
                    current_position = 1
                    
                    signal = {
                        'datetime': current_row.get('timestamp', i),
                        'close': current_row['close'],
                        'signal_type': 'buy',
                        'trade_sequence': trade_sequence,
                        'macd': current_row['macd'],
                        'macd_signal': current_row['macd_signal'],
                        'macd_hist': current_row['macd_hist'],
                        'validation_info': info,
                        'signal_strength': score,
                        'strategy_version': 'NextGen85+'
                    }
                    signals.append(signal)
                    logger.info(f"✅ 次世代買進 #{trade_sequence}: {current_row['close']:,.0f} - {info}")
                else:
                    logger.debug(f"❌ 買進信號被拒絕: {current_row['close']:,.0f} - {info}")
            
            # 檢查MACD賣出信號
            macd_sell_signal = (
                current_row['macd'] < current_row['macd_signal'] and 
                previous_row['macd'] >= previous_row['macd_signal'] and
                current_row['macd_hist'] < 0
            )
            
            if macd_sell_signal and current_position == 1:
                passed, info, score = self._enhanced_signal_validation(
                    current_row, 'sell', recent_performance
                )
                
                if passed:
                    current_position = 0
                    
                    signal = {
                        'datetime': current_row.get('timestamp', i),
                        'close': current_row['close'],
                        'signal_type': 'sell',
                        'trade_sequence': trade_sequence,
                        'macd': current_row['macd'],
                        'macd_signal': current_row['macd_signal'],
                        'macd_hist': current_row['macd_hist'],
                        'validation_info': info,
                        'signal_strength': score,
                        'strategy_version': 'NextGen85+'
                    }
                    signals.append(signal)
                    
                    # 計算這筆交易的表現並加入歷史
                    if signals and len(signals) >= 2:
                        last_buy = None
                        for s in reversed(signals[:-1]):
                            if s['signal_type'] == 'buy' and s['trade_sequence'] == trade_sequence:
                                last_buy = s
                                break
                        
                        if last_buy:
                            profit = current_row['close'] - last_buy['close']
                            recent_performance.append(profit)
                            if len(recent_performance) > self.recent_performance_window:
                                recent_performance.pop(0)
                    
                    logger.info(f"✅ 次世代賣出 #{trade_sequence}: {current_row['close']:,.0f} - {info}")
                else:
                    logger.debug(f"❌ 賣出信號被拒絕: {current_row['close']:,.0f} - {info}")
        
        return pd.DataFrame(signals)