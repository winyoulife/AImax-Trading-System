#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成交量增強MACD交易信號檢測系統
結合成交量分析來提升MACD信號品質
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class VolumeAnalyzer:
    """成交量分析器"""
    
    @staticmethod
    def calculate_volume_indicators(df: pd.DataFrame, volume_ma_period: int = 20) -> pd.DataFrame:
        """
        計算成交量指標
        
        Args:
            df: 包含OHLCV數據的DataFrame
            volume_ma_period: 成交量移動平均週期
            
        Returns:
            添加成交量指標的DataFrame
        """
        df = df.copy()
        
        # 成交量移動平均
        df['volume_ma'] = df['volume'].rolling(window=volume_ma_period).mean()
        
        # 相對成交量（當前成交量 / 平均成交量）
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # 成交量趨勢（5期成交量移動平均的斜率）
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_trend'] = df['volume_ma5'].pct_change(periods=3)
        
        # 價量背離指標
        df['price_change'] = df['close'].pct_change()
        df['volume_change'] = df['volume'].pct_change()
        
        # OBV (On Balance Volume) 能量潮指標
        df['obv'] = 0.0
        for i in range(1, len(df)):
            if df.iloc[i]['close'] > df.iloc[i-1]['close']:
                df.iloc[i, df.columns.get_loc('obv')] = df.iloc[i-1]['obv'] + df.iloc[i]['volume']
            elif df.iloc[i]['close'] < df.iloc[i-1]['close']:
                df.iloc[i, df.columns.get_loc('obv')] = df.iloc[i-1]['obv'] - df.iloc[i]['volume']
            else:
                df.iloc[i, df.columns.get_loc('obv')] = df.iloc[i-1]['obv']
        
        # OBV移動平均
        df['obv_ma'] = df['obv'].rolling(window=10).mean()
        df['obv_signal'] = df['obv'] > df['obv_ma']
        
        return df
    
    @staticmethod
    def validate_volume_confirmation(row: pd.Series, signal_type: str, 
                                   volume_threshold: float = 1.2,
                                   obv_confirmation: bool = True) -> Tuple[bool, str]:
        """
        驗證成交量確認信號
        
        Args:
            row: 當前數據行
            signal_type: 信號類型 ('buy' 或 'sell')
            volume_threshold: 成交量閾值（相對於平均成交量的倍數）
            obv_confirmation: 是否需要OBV確認
            
        Returns:
            (是否確認, 確認信息)
        """
        try:
            # 檢查必要的成交量數據
            required_cols = ['volume_ratio', 'volume_trend', 'obv_signal']
            for col in required_cols:
                if col not in row or pd.isna(row[col]):
                    return False, f"缺少{col}數據"
            
            volume_ratio = row['volume_ratio']
            volume_trend = row['volume_trend']
            obv_signal = row['obv_signal']
            
            # 基本成交量條件：成交量需要高於平均
            volume_ok = volume_ratio >= volume_threshold
            
            # 成交量趨勢條件
            if signal_type == 'buy':
                # 買進：希望成交量增加（正趨勢）
                trend_ok = volume_trend > 0
                # OBV確認：OBV應該向上
                obv_ok = obv_signal if obv_confirmation else True
            else:
                # 賣出：成交量增加也是好的（確認賣壓）
                trend_ok = volume_trend > -0.1  # 允許輕微下降
                # OBV確認：OBV應該向下
                obv_ok = not obv_signal if obv_confirmation else True
            
            # 綜合判斷
            all_ok = volume_ok and trend_ok and obv_ok
            
            # 生成確認信息
            info_parts = []
            info_parts.append(f"量比{volume_ratio:.1f}{'✓' if volume_ok else '✗'}")
            info_parts.append(f"量勢{volume_trend:.1%}{'✓' if trend_ok else '✗'}")
            if obv_confirmation:
                info_parts.append(f"OBV{'✓' if obv_ok else '✗'}")
            
            confirmation_info = f"成交量確認: {' '.join(info_parts)}"
            
            return all_ok, confirmation_info
            
        except Exception as e:
            logger.error(f"成交量確認驗證失敗: {e}")
            return False, f"驗證錯誤: {e}"

class VolumeEnhancedMACDSignals:
    """成交量增強MACD信號檢測器"""
    
    def __init__(self, 
                 fast_period: int = 12,
                 slow_period: int = 26, 
                 signal_period: int = 9,
                 volume_ma_period: int = 20,
                 volume_threshold: float = 1.2,
                 require_obv_confirmation: bool = True):
        """
        初始化成交量增強MACD檢測器
        
        Args:
            fast_period: MACD快線週期
            slow_period: MACD慢線週期
            signal_period: MACD信號線週期
            volume_ma_period: 成交量移動平均週期
            volume_threshold: 成交量確認閾值
            require_obv_confirmation: 是否需要OBV確認
        """
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.volume_ma_period = volume_ma_period
        self.volume_threshold = volume_threshold
        self.require_obv_confirmation = require_obv_confirmation
        
        self.volume_analyzer = VolumeAnalyzer()
        
        # 持倉狀態追蹤
        self.current_position = 0  # 0=空倉, 1=持倉
        self.trade_sequence = 0
        self.trade_history = []
        
    def calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算MACD指標"""
        df = df.copy()
        
        # 計算EMA
        ema_fast = df['close'].ewm(span=self.fast_period).mean()
        ema_slow = df['close'].ewm(span=self.slow_period).mean()
        
        # 計算MACD線
        df['macd'] = ema_fast - ema_slow
        
        # 計算信號線
        df['macd_signal'] = df['macd'].ewm(span=self.signal_period).mean()
        
        # 計算MACD柱
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def detect_enhanced_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        檢測成交量增強的MACD信號
        
        Args:
            df: 包含OHLCV數據的DataFrame
            
        Returns:
            包含信號的DataFrame
        """
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 重置狀態
        self.current_position = 0
        self.trade_sequence = 0
        self.trade_history = []
        
        # 計算MACD指標
        df = self.calculate_macd(df)
        
        # 計算成交量指標
        df = self.volume_analyzer.calculate_volume_indicators(df, self.volume_ma_period)
        
        # 檢測信號
        signals = []
        
        for i in range(1, len(df)):
            current_row = df.iloc[i]
            previous_row = df.iloc[i-1]
            
            # 檢查MACD買進信號（金叉）
            macd_buy_signal = self._check_macd_buy_signal(current_row, previous_row)
            if macd_buy_signal and self.current_position == 0:
                # 成交量確認
                volume_confirmed, volume_info = self.volume_analyzer.validate_volume_confirmation(
                    current_row, 'buy', self.volume_threshold, self.require_obv_confirmation
                )
                
                if volume_confirmed:
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
                        'volume': current_row['volume'],
                        'volume_ratio': current_row['volume_ratio'],
                        'volume_trend': current_row['volume_trend'],
                        'obv_signal': current_row['obv_signal'],
                        'volume_confirmed': True,
                        'volume_info': volume_info,
                        'signal_strength': self._calculate_signal_strength(current_row, 'buy')
                    }
                    signals.append(signal)
                    self.trade_history.append(signal)
                    
                    logger.info(f"✅ 成交量確認買進 #{self.trade_sequence}: {current_row['close']:,.0f} - {volume_info}")
                else:
                    # MACD信號但成交量未確認
                    signal = {
                        'datetime': current_row['timestamp'],
                        'close': current_row['close'],
                        'signal_type': 'buy_rejected',
                        'trade_sequence': 0,
                        'macd': current_row['macd'],
                        'macd_signal': current_row['macd_signal'],
                        'macd_hist': current_row['macd_hist'],
                        'volume': current_row['volume'],
                        'volume_ratio': current_row['volume_ratio'],
                        'volume_trend': current_row['volume_trend'],
                        'obv_signal': current_row['obv_signal'],
                        'volume_confirmed': False,
                        'volume_info': volume_info,
                        'signal_strength': 0
                    }
                    signals.append(signal)
                    
                    logger.info(f"❌ 買進信號被拒絕: {current_row['close']:,.0f} - {volume_info}")
            
            # 檢查MACD賣出信號（死叉）
            macd_sell_signal = self._check_macd_sell_signal(current_row, previous_row)
            if macd_sell_signal and self.current_position == 1:
                # 成交量確認
                volume_confirmed, volume_info = self.volume_analyzer.validate_volume_confirmation(
                    current_row, 'sell', self.volume_threshold, self.require_obv_confirmation
                )
                
                if volume_confirmed:
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
                        'volume': current_row['volume'],
                        'volume_ratio': current_row['volume_ratio'],
                        'volume_trend': current_row['volume_trend'],
                        'obv_signal': current_row['obv_signal'],
                        'volume_confirmed': True,
                        'volume_info': volume_info,
                        'signal_strength': self._calculate_signal_strength(current_row, 'sell')
                    }
                    signals.append(signal)
                    self.trade_history.append(signal)
                    
                    logger.info(f"✅ 成交量確認賣出 #{self.trade_sequence}: {current_row['close']:,.0f} - {volume_info}")
                else:
                    # MACD信號但成交量未確認
                    signal = {
                        'datetime': current_row['timestamp'],
                        'close': current_row['close'],
                        'signal_type': 'sell_rejected',
                        'trade_sequence': 0,
                        'macd': current_row['macd'],
                        'macd_signal': current_row['macd_signal'],
                        'macd_hist': current_row['macd_hist'],
                        'volume': current_row['volume'],
                        'volume_ratio': current_row['volume_ratio'],
                        'volume_trend': current_row['volume_trend'],
                        'obv_signal': current_row['obv_signal'],
                        'volume_confirmed': False,
                        'volume_info': volume_info,
                        'signal_strength': 0
                    }
                    signals.append(signal)
                    
                    logger.info(f"❌ 賣出信號被拒絕: {current_row['close']:,.0f} - {volume_info}")
        
        return pd.DataFrame(signals)
    
    def _check_macd_buy_signal(self, current_row: pd.Series, previous_row: pd.Series) -> bool:
        """檢查MACD買進信號（金叉）"""
        try:
            # 基本MACD金叉條件
            basic_conditions = (
                previous_row['macd_hist'] < 0 and  # 前一期MACD柱為負
                previous_row['macd'] <= previous_row['macd_signal'] and  # 前一期MACD <= 信號線
                current_row['macd'] > current_row['macd_signal']  # 當前MACD > 信號線
            )
            
            # 負值區域條件（更保守）
            negative_conditions = (
                current_row['macd'] < 0 and  # MACD線為負
                current_row['macd_signal'] < 0  # 信號線為負
            )
            
            return basic_conditions and negative_conditions
            
        except Exception as e:
            logger.error(f"MACD買進信號檢查失敗: {e}")
            return False
    
    def _check_macd_sell_signal(self, current_row: pd.Series, previous_row: pd.Series) -> bool:
        """檢查MACD賣出信號（死叉）"""
        try:
            # 基本MACD死叉條件
            basic_conditions = (
                previous_row['macd_hist'] > 0 and  # 前一期MACD柱為正
                previous_row['macd'] >= previous_row['macd_signal'] and  # 前一期MACD >= 信號線
                current_row['macd_signal'] > current_row['macd']  # 當前信號線 > MACD
            )
            
            # 正值區域條件（更保守）
            positive_conditions = (
                current_row['macd'] > 0 and  # MACD線為正
                current_row['macd_signal'] > 0  # 信號線為正
            )
            
            return basic_conditions and positive_conditions
            
        except Exception as e:
            logger.error(f"MACD賣出信號檢查失敗: {e}")
            return False
    
    def _calculate_signal_strength(self, row: pd.Series, signal_type: str) -> float:
        """
        計算信號強度（0-100）
        
        結合MACD強度和成交量強度
        """
        try:
            # MACD強度（基於MACD柱的絕對值）
            macd_strength = min(abs(row['macd_hist']) * 10, 50)  # 最大50分
            
            # 成交量強度
            volume_strength = min((row['volume_ratio'] - 1) * 25, 30)  # 最大30分
            
            # 趨勢強度（基於成交量趋势）
            trend_strength = min(abs(row['volume_trend']) * 100, 20)  # 最大20分
            
            total_strength = macd_strength + volume_strength + trend_strength
            return min(total_strength, 100)
            
        except Exception as e:
            logger.error(f"信號強度計算失敗: {e}")
            return 0
    
    def get_trade_summary(self) -> Dict:
        """獲取交易摘要"""
        if not self.trade_history:
            return {'total_trades': 0, 'buy_count': 0, 'sell_count': 0}
        
        buy_count = len([t for t in self.trade_history if t['signal_type'] == 'buy'])
        sell_count = len([t for t in self.trade_history if t['signal_type'] == 'sell'])
        
        return {
            'total_trades': len(self.trade_history),
            'buy_count': buy_count,
            'sell_count': sell_count,
            'current_position': self.current_position,
            'trade_sequence': self.trade_sequence
        }