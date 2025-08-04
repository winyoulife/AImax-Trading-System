#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
終極優化成交量增強MACD交易信號檢測系統
目標：達到90%+勝率並增加交易機會
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class UltimateOptimizedVolumeAnalyzer:
    """終極優化成交量分析器"""
    
    @staticmethod
    def calculate_ultimate_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """計算終極優化技術指標"""
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
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma50'] = df['close'].rolling(window=50).mean()
        df['ma200'] = df['close'].rolling(window=200).mean()
        df['trend_strength'] = (df['close'] - df['ma50']) / df['ma50']
        df['short_trend'] = (df['close'] - df['ma20']) / df['ma20']
        
        # 價格動能指標
        df['price_momentum_3'] = df['close'].pct_change(periods=3)
        df['price_momentum_5'] = df['close'].pct_change(periods=5)
        df['price_momentum_10'] = df['close'].pct_change(periods=10)
        
        # 市場波動性
        df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
        df['volatility_ma'] = df['volatility'].rolling(window=10).mean()
        df['volatility_ratio'] = df['volatility'] / df['volatility_ma']
        
        # MACD強度指標
        df['macd_strength'] = abs(df['macd_hist']) / df['close'] * 10000
        df['macd_acceleration'] = df['macd_hist'].diff()
        df['macd_momentum'] = df['macd'].pct_change(periods=3)
        
        # 成交量價格確認
        df['volume_price_trend'] = np.where(
            (df['close'].pct_change() > 0) & (df['volume_trend'] > 0), 1,
            np.where((df['close'].pct_change() < 0) & (df['volume_trend'] > 0), -1, 0)
        )
        
        # 新增：多重確認指標
        df['trend_alignment'] = np.where(
            (df['ma20'] > df['ma50']) & (df['ma50'] > df['ma200']), 1,
            np.where((df['ma20'] < df['ma50']) & (df['ma50'] < df['ma200']), -1, 0)
        )
        
        # 新增：風險評估指標
        df['risk_score'] = (
            abs(df['price_momentum_5']) * 0.3 +
            df['volatility_ratio'] * 0.3 +
            abs(df['bb_position'] - 0.5) * 0.4
        )
        
        # 新增：市場強度綜合指標
        df['market_strength'] = (
            (df['rsi'] - 50) / 50 * 0.2 +
            df['trend_strength'] * 0.3 +
            (df['volume_ratio'] - 1) * 0.2 +
            df['short_trend'] * 0.3
        )
        
        # 新增：信號品質指標
        df['signal_quality'] = (
            (1 - abs(df['rsi'] - 50) / 50) * 0.3 +
            (1 - abs(df['bb_position'] - 0.5)) * 0.3 +
            np.minimum(df['volume_ratio'] / 2, 1) * 0.4
        )
        
        return df
    
    @staticmethod
    def ultimate_signal_validation(row: pd.Series, signal_type: str, market_context: Dict, recent_trades: List) -> Tuple[bool, str, float]:
        """
        終極優化信號驗證
        加入更多智能判斷和風險控制
        """
        try:
            score = 0
            reasons = []
            
            # 基礎市場條件評估
            market_strength = row.get('market_strength', 0)
            risk_score = row.get('risk_score', 1)
            signal_quality = row.get('signal_quality', 0.5)
            
            # 動態調整基準分數和獎勵
            if signal_quality > 0.7:
                base_threshold = 65
                quality_bonus = 8
            elif signal_quality > 0.5:
                base_threshold = 68
                quality_bonus = 5
            else:
                base_threshold = 72
                quality_bonus = 0
            
            # 風險調整
            if risk_score > 1.5:
                base_threshold += 5
                reasons.append(f"高風險+5")
            elif risk_score < 0.8:
                quality_bonus += 3
                reasons.append(f"低風險+3")
            
            # 1. 成交量確認 (25分) - 智能動態閾值
            volume_ratio = row.get('volume_ratio', 0)
            volatility_ratio = row.get('volatility_ratio', 1)
            
            # 更智能的成交量閾值計算
            if abs(market_strength) > 0.15:  # 強勢市場
                volume_threshold = 0.8 + (volatility_ratio - 1) * 0.1
            else:  # 一般市場
                volume_threshold = 1.0 + (volatility_ratio - 1) * 0.15
            
            volume_threshold = max(0.7, min(1.4, volume_threshold))
            
            if volume_ratio >= volume_threshold * 1.2:
                score += 25
                reasons.append(f"量比{volume_ratio:.1f}✓")
            elif volume_ratio >= volume_threshold:
                score += 20
                reasons.append(f"量比{volume_ratio:.1f}◐")
            elif volume_ratio >= volume_threshold * 0.8:
                score += 12
                reasons.append(f"量比{volume_ratio:.1f}◑")
            else:
                reasons.append(f"量比{volume_ratio:.1f}✗")
            
            # 2. 成交量趨勢 (20分) - 考慮市場方向
            volume_trend = row.get('volume_trend', 0)
            trend_alignment = row.get('trend_alignment', 0)
            
            if signal_type == 'buy':
                if volume_trend > 0.08 and trend_alignment >= 0:
                    score += 20
                    reasons.append(f"量勢{volume_trend:.1%}✓")
                elif volume_trend > 0.03:
                    score += 15
                    reasons.append(f"量勢{volume_trend:.1%}◐")
                elif volume_trend > -0.05:
                    score += 8
                    reasons.append(f"量勢{volume_trend:.1%}◑")
                else:
                    reasons.append(f"量勢{volume_trend:.1%}✗")
            else:
                if volume_trend > -0.08 and trend_alignment <= 0:
                    score += 20
                    reasons.append(f"量勢{volume_trend:.1%}✓")
                elif volume_trend > -0.15:
                    score += 15
                    reasons.append(f"量勢{volume_trend:.1%}◐")
                elif volume_trend > -0.25:
                    score += 8
                    reasons.append(f"量勢{volume_trend:.1%}◑")
                else:
                    reasons.append(f"量勢{volume_trend:.1%}✗")
            
            # 3. RSI確認 (15分) - 更精細的範圍
            rsi = row.get('rsi', 50)
            if signal_type == 'buy':
                if 35 <= rsi <= 65:
                    score += 15
                    reasons.append(f"RSI{rsi:.0f}✓")
                elif 30 <= rsi <= 70:
                    score += 12
                    reasons.append(f"RSI{rsi:.0f}◐")
                elif 25 <= rsi <= 75:
                    score += 8
                    reasons.append(f"RSI{rsi:.0f}◑")
                else:
                    reasons.append(f"RSI{rsi:.0f}✗")
            else:
                if 35 <= rsi <= 65:
                    score += 15
                    reasons.append(f"RSI{rsi:.0f}✓")
                elif 30 <= rsi <= 70:
                    score += 12
                    reasons.append(f"RSI{rsi:.0f}◐")
                elif 25 <= rsi <= 75:
                    score += 8
                    reasons.append(f"RSI{rsi:.0f}◑")
                else:
                    reasons.append(f"RSI{rsi:.0f}✗")
            
            # 4. 布林帶位置 (15分) - 考慮市場狀態
            bb_position = row.get('bb_position', 0.5)
            bb_width = row.get('bb_width', 0.1)
            
            if 0.02 <= bb_width <= 0.20:
                if signal_type == 'buy':
                    if 0.15 <= bb_position <= 0.55:
                        score += 15
                        reasons.append(f"BB{bb_position:.1f}✓")
                    elif 0.05 <= bb_position <= 0.70:
                        score += 12
                        reasons.append(f"BB{bb_position:.1f}◐")
                    elif 0 <= bb_position <= 0.80:
                        score += 8
                        reasons.append(f"BB{bb_position:.1f}◑")
                    else:
                        reasons.append(f"BB{bb_position:.1f}✗")
                else:
                    if 0.45 <= bb_position <= 0.85:
                        score += 15
                        reasons.append(f"BB{bb_position:.1f}✓")
                    elif 0.30 <= bb_position <= 0.95:
                        score += 12
                        reasons.append(f"BB{bb_position:.1f}◐")
                    elif 0.20 <= bb_position <= 1.0:
                        score += 8
                        reasons.append(f"BB{bb_position:.1f}◑")
                    else:
                        reasons.append(f"BB{bb_position:.1f}✗")
            else:
                score += 6
                reasons.append(f"BB寬度{bb_width:.2f}◐")
            
            # 5. 趨勢對齊確認 (15分) - 多重時間框架
            trend_strength = row.get('trend_strength', 0)
            short_trend = row.get('short_trend', 0)
            trend_alignment = row.get('trend_alignment', 0)
            
            if signal_type == 'buy':
                if trend_alignment > 0 and short_trend > -0.02:
                    score += 15
                    reasons.append(f"趨勢✓")
                elif trend_strength > -0.05:
                    score += 12
                    reasons.append(f"趨勢◐")
                elif trend_strength > -0.10:
                    score += 8
                    reasons.append(f"趨勢◑")
                else:
                    reasons.append(f"趨勢✗")
            else:
                if trend_alignment < 0 and short_trend < 0.02:
                    score += 15
                    reasons.append(f"趨勢✓")
                elif trend_strength < 0.05:
                    score += 12
                    reasons.append(f"趨勢◐")
                elif trend_strength < 0.10:
                    score += 8
                    reasons.append(f"趨勢◑")
                else:
                    reasons.append(f"趨勢✗")
            
            # 6. MACD動能確認 (10分) - 加入動能分析
            macd_strength = row.get('macd_strength', 0)
            macd_acceleration = row.get('macd_acceleration', 0)
            macd_momentum = row.get('macd_momentum', 0)
            
            if signal_type == 'buy':
                if macd_strength > 2 and macd_acceleration > 0 and macd_momentum > -0.1:
                    score += 10
                    reasons.append(f"MACD✓")
                elif macd_strength > 1.5:
                    score += 8
                    reasons.append(f"MACD◐")
                elif macd_strength > 1:
                    score += 5
                    reasons.append(f"MACD◑")
                else:
                    reasons.append(f"MACD✗")
            else:
                if macd_strength > 2 and macd_acceleration < 0 and macd_momentum < 0.1:
                    score += 10
                    reasons.append(f"MACD✓")
                elif macd_strength > 1.5:
                    score += 8
                    reasons.append(f"MACD◐")
                elif macd_strength > 1:
                    score += 5
                    reasons.append(f"MACD◑")
                else:
                    reasons.append(f"MACD✗")
            
            # 7. 近期交易歷史分析 (額外分數)
            if recent_trades:
                try:
                    last_trade = recent_trades[-1]
                    current_time = row.get('timestamp', pd.Timestamp.now())
                    last_exit_time = last_trade.get('exit_time', current_time)
                    
                    if isinstance(current_time, pd.Timestamp) and isinstance(last_exit_time, pd.Timestamp):
                        time_since_last = (current_time - last_exit_time).total_seconds() / 3600
                        
                        # 避免過於頻繁交易
                        if time_since_last < 6:  # 6小時內
                            score -= 5
                            reasons.append(f"頻繁交易-5")
                        elif time_since_last > 24:  # 24小時後
                            score += 3
                            reasons.append(f"間隔適當+3")
                except Exception:
                    pass  # 忽略時間比較錯誤
            
            # 加上品質獎勵分數
            score += quality_bonus
            if quality_bonus > 0:
                reasons.append(f"品質獎勵+{quality_bonus}")
            
            # 終極閾值評估
            passed = score >= base_threshold
            info = f"終極確認({score}/{base_threshold}): {' '.join(reasons)}"
            
            return passed, info, score
            
        except Exception as e:
            logger.error(f"終極優化信號驗證失敗: {e}")
            return False, f"驗證錯誤: {e}", 0

class UltimateOptimizedVolumeEnhancedMACDSignals:
    """終極優化成交量增強MACD信號檢測器"""
    
    def __init__(self):
        self.volume_analyzer = UltimateOptimizedVolumeAnalyzer()
        
        # 持倉狀態追蹤
        self.current_position = 0
        self.trade_sequence = 0
        self.trade_history = []
        self.recent_trades = []
        
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
            
            recent_data = df.iloc[max(0, current_index-30):current_index+1]
            
            # 趨勢分析
            ma50_slope = (recent_data['ma50'].iloc[-1] - recent_data['ma50'].iloc[-15]) / recent_data['ma50'].iloc[-15]
            
            if ma50_slope > 0.025:
                trend = 'strong_bullish'
            elif ma50_slope > 0.01:
                trend = 'bullish'
            elif ma50_slope < -0.025:
                trend = 'strong_bearish'
            elif ma50_slope < -0.01:
                trend = 'bearish'
            else:
                trend = 'sideways'
            
            # 波動性分析
            avg_volatility = recent_data['volatility'].mean()
            if avg_volatility > 0.035:
                volatility = 'very_high'
            elif avg_volatility > 0.025:
                volatility = 'high'
            elif avg_volatility < 0.012:
                volatility = 'low'
            else:
                volatility = 'normal'
            
            return {
                'trend': trend,
                'volatility': volatility,
                'strength': abs(ma50_slope),
                'avg_volatility': avg_volatility,
                'market_phase': self._determine_market_phase(recent_data)
            }
            
        except Exception as e:
            logger.error(f"市場環境分析失敗: {e}")
            return {'trend': 'unknown', 'volatility': 'normal', 'strength': 0}
    
    def _determine_market_phase(self, recent_data: pd.DataFrame) -> str:
        """判斷市場階段"""
        try:
            price_change = (recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) / recent_data['close'].iloc[0]
            volume_trend = recent_data['volume_trend'].mean()
            
            if price_change > 0.05 and volume_trend > 0.1:
                return 'bull_run'
            elif price_change < -0.05 and volume_trend > 0.1:
                return 'bear_crash'
            elif abs(price_change) < 0.02:
                return 'consolidation'
            else:
                return 'trending'
        except:
            return 'unknown'
    
    def detect_ultimate_optimized_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """檢測終極優化成交量增強MACD信號"""
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 重置狀態
        self.current_position = 0
        self.trade_sequence = 0
        self.trade_history = []
        self.recent_trades = []
        
        # 計算所有指標
        df = self.calculate_macd(df)
        df = self.volume_analyzer.calculate_ultimate_indicators(df)
        
        signals = []
        
        for i in range(1, len(df)):
            current_row = df.iloc[i]
            previous_row = df.iloc[i-1]
            
            # 分析市場環境
            market_context = self.analyze_market_context(df, i)
            
            # 檢查MACD買進信號
            macd_buy_signal = self._check_macd_buy_signal(current_row, previous_row)
            if macd_buy_signal and self.current_position == 0:
                # 終極優化驗證
                passed, info, score = self.volume_analyzer.ultimate_signal_validation(
                    current_row, 'buy', market_context, self.recent_trades
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
                        'market_context': market_context,
                        'entry_time': current_row['timestamp']
                    }
                    signals.append(signal)
                    self.trade_history.append(signal)
                    
                    logger.info(f"✅ 終極確認買進 #{self.trade_sequence}: {current_row['close']:,.0f} - {info}")
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
                # 終極優化驗證
                passed, info, score = self.volume_analyzer.ultimate_signal_validation(
                    current_row, 'sell', market_context, self.recent_trades
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
                        'market_context': market_context,
                        'exit_time': current_row['timestamp']
                    }
                    signals.append(signal)
                    self.trade_history.append(signal)
                    
                    # 更新近期交易記錄
                    self.recent_trades.append({
                        'exit_time': current_row['timestamp'],
                        'sequence': self.trade_sequence
                    })
                    
                    logger.info(f"✅ 終極確認賣出 #{self.trade_sequence}: {current_row['close']:,.0f} - {info}")
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