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
        
        # 趨勢強度
        df['trend_strength'] = (df['close'] - df['ma20']) / df['ma20']
        df['short_trend'] = (df['ma20'] - df['ma50']) / df['ma50']
        df['long_trend'] = (df['ma50'] - df['ma200']) / df['ma200']
        
        # 趨勢對齊
        df['trend_alignment'] = np.where(
            (df['close'] > df['ma20']) & (df['ma20'] > df['ma50']) & (df['ma50'] > df['ma200']), 1,
            np.where((df['close'] < df['ma20']) & (df['ma20'] < df['ma50']) & (df['ma50'] < df['ma200']), -1, 0)
        )
        
        # 波動率指標
        df['volatility'] = df['close'].rolling(window=20).std()
        df['volatility_ratio'] = df['volatility'] / df['volatility'].rolling(window=50).mean()
        
        # 市場強度指標
        df['market_strength'] = (
            df['trend_strength'] * 0.4 +
            df['short_trend'] * 0.3 +
            df['long_trend'] * 0.3
        )
        
        # 風險評分
        df['risk_score'] = (
            abs(df['trend_strength']) * 0.3 +
            df['volatility_ratio'] * 0.4 +
            (1 - abs(df['rsi'] - 50) / 50) * 0.3
        )
        
        # MACD強度和動能
        df['macd_strength'] = abs(df.get('macd_hist', 0))
        df['macd_acceleration'] = df['macd_strength'].diff()
        df['macd_momentum'] = df['macd_strength'].pct_change()
        
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
            
            # 動態調整基準分數和獎勵 - 大幅提高閾值以達到高勝率
            if signal_quality > 0.85:
                base_threshold = 95  # 大幅提高閾值
                quality_bonus = 15
            elif signal_quality > 0.7:
                base_threshold = 100  # 極高閾值
                quality_bonus = 12
            else:
                base_threshold = 110  # 超高閾值，只接受最優質信號
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
            
            # 極嚴格的成交量閾值計算 - 只接受高質量信號
            if abs(market_strength) > 0.15:  # 強勢市場
                volume_threshold = 1.8 + (volatility_ratio - 1) * 0.1  # 極高閾值
            else:  # 一般市場
                volume_threshold = 2.2 + (volatility_ratio - 1) * 0.15  # 超高閾值
            
            volume_threshold = max(1.8, min(3.0, volume_threshold))  # 大幅提高最低閾值
            
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
                if volume_trend > 0.25 and trend_alignment >= 0:  # 極高要求
                    score += 20
                    reasons.append(f"量勢{volume_trend:.1%}✓")
                elif volume_trend > 0.15:  # 高要求
                    score += 15
                    reasons.append(f"量勢{volume_trend:.1%}◐")
                elif volume_trend > 0.08:  # 中等要求
                    score += 8
                    reasons.append(f"量勢{volume_trend:.1%}◑")
                else:
                    reasons.append(f"量勢{volume_trend:.1%}✗")
            else:
                if volume_trend > 0.05 and trend_alignment <= 0:  # 極高要求
                    score += 20
                    reasons.append(f"量勢{volume_trend:.1%}✓")
                elif volume_trend > -0.05:  # 高要求
                    score += 15
                    reasons.append(f"量勢{volume_trend:.1%}◐")
                elif volume_trend > -0.15:  # 中等要求
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
                if macd_strength > 3 and macd_acceleration > 0.5 and macd_momentum > 0:  # 提高要求
                    score += 10
                    reasons.append(f"MACD✓")
                elif macd_strength > 2.5 and macd_acceleration > 0:  # 提高要求
                    score += 8
                    reasons.append(f"MACD◐")
                elif macd_strength > 2:  # 提高要求
                    score += 5
                    reasons.append(f"MACD◑")
                else:
                    reasons.append(f"MACD✗")
            else:
                if macd_strength > 3 and macd_acceleration < -0.5 and macd_momentum < 0:  # 提高要求
                    score += 10
                    reasons.append(f"MACD✓")
                elif macd_strength > 2.5 and macd_acceleration < 0:  # 提高要求
                    score += 8
                    reasons.append(f"MACD◐")
                elif macd_strength > 2:  # 提高要求
                    score += 5
                    reasons.append(f"MACD◑")
                else:
                    reasons.append(f"MACD✗")
            
            # 7. 近期交易歷史分析 (額外分數) - 加強交易間隔控制
            if recent_trades:
                try:
                    last_trade = recent_trades[-1]
                    current_time = row.get('timestamp', pd.Timestamp.now())
                    last_exit_time = last_trade.get('exit_time', current_time)
                    
                    if isinstance(current_time, pd.Timestamp) and isinstance(last_exit_time, pd.Timestamp):
                        time_since_last = (current_time - last_exit_time).total_seconds() / 3600
                        
                        # 更嚴格的交易間隔控制
                        if time_since_last < 2:  # 2小時內 - 嚴格禁止
                            score -= 20
                            reasons.append(f"過度頻繁-20")
                        elif time_since_last < 6:  # 6小時內 - 重度懲罰
                            score -= 15
                            reasons.append(f"頻繁交易-15")
                        elif time_since_last < 12:  # 12小時內 - 輕度懲罰
                            score -= 8
                            reasons.append(f"間隔偏短-8")
                        elif time_since_last > 48:  # 48小時後 - 獎勵
                            score += 8
                            reasons.append(f"間隔充足+8")
                        elif time_since_last > 24:  # 24小時後 - 小獎勵
                            score += 5
                            reasons.append(f"間隔適當+5")
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
    
    def _check_macd_buy_signal(self, current_row: pd.Series, previous_row: pd.Series) -> bool:
        """檢查MACD買進信號"""
        try:
            # MACD金叉：MACD線上穿信號線
            macd_cross = (current_row['macd'] > current_row['macd_signal'] and 
                         previous_row['macd'] <= previous_row['macd_signal'])
            
            # MACD柱狀圖轉正
            hist_positive = current_row['macd_hist'] > 0 and previous_row['macd_hist'] <= 0
            
            return macd_cross or hist_positive
            
        except Exception as e:
            logger.error(f"MACD買進信號檢測失敗: {e}")
            return False
    
    def _check_macd_sell_signal(self, current_row: pd.Series, previous_row: pd.Series) -> bool:
        """檢查MACD賣出信號"""
        try:
            # MACD死叉：MACD線下穿信號線
            macd_cross = (current_row['macd'] < current_row['macd_signal'] and 
                         previous_row['macd'] >= previous_row['macd_signal'])
            
            # MACD柱狀圖轉負
            hist_negative = current_row['macd_hist'] < 0 and previous_row['macd_hist'] >= 0
            
            return macd_cross or hist_negative
            
        except Exception as e:
            logger.error(f"MACD賣出信號檢測失敗: {e}")
            return False
    
    def analyze_market_context(self, df: pd.DataFrame, current_index: int) -> Dict:
        """分析市場環境"""
        try:
            current_row = df.iloc[current_index]
            
            # 基本市場信息
            context = {
                'volatility': current_row.get('volatility_ratio', 1),
                'trend_strength': current_row.get('trend_strength', 0),
                'market_phase': self._determine_market_phase(current_row),
                'risk_level': current_row.get('risk_score', 1)
            }
            
            return context
            
        except Exception as e:
            logger.error(f"市場環境分析失敗: {e}")
            return {}
    
    def _determine_market_phase(self, row: pd.Series) -> str:
        """判斷市場階段"""
        try:
            trend_strength = row.get('trend_strength', 0)
            volatility = row.get('volatility_ratio', 1)
            
            if abs(trend_strength) > 0.05 and volatility < 1.5:
                return 'trending'
            elif volatility > 2:
                return 'volatile'
            else:
                return 'ranging'
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
                passed, info, score = UltimateOptimizedVolumeAnalyzer.ultimate_signal_validation(
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
                    logger.info(f"❌ 買進信號被拒絕: {current_row['close']:,.0f} - {info}")
            
            # 檢查MACD賣出信號
            macd_sell_signal = self._check_macd_sell_signal(current_row, previous_row)
            if macd_sell_signal and self.current_position == 1:
                # 終極優化驗證
                passed, info, score = UltimateOptimizedVolumeAnalyzer.ultimate_signal_validation(
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
                    
                    # 更新交易歷史
                    if self.trade_history:
                        last_buy = self.trade_history[-1]
                        trade_record = {
                            'entry_time': last_buy['entry_time'],
                            'exit_time': current_row['timestamp'],
                            'entry_price': last_buy['close'],
                            'exit_price': current_row['close'],
                            'profit': current_row['close'] - last_buy['close'],
                            'profit_pct': (current_row['close'] - last_buy['close']) / last_buy['close']
                        }
                        self.recent_trades.append(trade_record)
                    
                    logger.info(f"✅ 終極確認賣出 #{self.trade_sequence}: {current_row['close']:,.0f} - {info}")
                else:
                    # 信號被拒絕
                    logger.info(f"❌ 賣出信號被拒絕: {current_row['close']:,.0f} - {info}")
        
        return pd.DataFrame(signals)