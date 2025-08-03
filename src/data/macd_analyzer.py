#!/usr/bin/env python3
"""
MACD分析器 - 整合到AImax交易系統
提供MACD技術分析功能給交易策略使用
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import os
import sys

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.macd_data_reader import MACDDataReader

class MACDAnalyzer:
    """MACD分析器 - 為交易系統提供MACD分析功能"""
    
    def __init__(self, db_path="data/macd_data.db"):
        self.reader = MACDDataReader(db_path)
        self.cache = {}  # 緩存最近的分析結果
        self.cache_timeout = 300  # 5分鐘緩存
    
    def get_macd_signals(self, symbol='btctwd', period='60', force_refresh=False):
        """獲取MACD信號 - 主要接口"""
        cache_key = f"{symbol}_{period}"
        current_time = datetime.now()
        
        # 檢查緩存
        if not force_refresh and cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if (current_time - cached_data['timestamp']).seconds < self.cache_timeout:
                return cached_data['signals']
        
        # 獲取新數據並分析
        df = self.reader.get_max_data(symbol, period, 100)
        if df is None or df.empty:
            return None
        
        # 儲存到數據庫
        self.reader.save_data(df, symbol, period)
        
        # 分析MACD信號
        analysis = self.reader.analyze_macd_signals(df)
        
        # 生成標準化信號
        signals = self._generate_standardized_signals(analysis, df)
        
        # 更新緩存
        self.cache[cache_key] = {
            'signals': signals,
            'timestamp': current_time
        }
        
        return signals
    
    def _generate_standardized_signals(self, analysis, df):
        """生成標準化的MACD信號"""
        if not analysis or df.empty:
            return None
        
        latest = df.iloc[-1]  # 最新數據
        
        signals = {
            'symbol': latest.get('symbol', 'UNKNOWN'),
            'timestamp': latest['datetime'].isoformat() if 'datetime' in latest else datetime.now().isoformat(),
            'price': latest['close'],
            
            # MACD核心數據
            'macd': {
                'value': analysis.get('latest_macd', 0),
                'signal': analysis.get('latest_signal', 0),
                'histogram': analysis.get('latest_hist', 0),
                'trend': analysis.get('macd_trend', 'unknown')
            },
            
            # 交易信號
            'signals': {
                'type': self._determine_signal_type(analysis),
                'strength': self._calculate_signal_strength(analysis, df),
                'confidence': self._calculate_confidence(analysis, df),
                'reason': self._generate_signal_reason(analysis)
            },
            
            # 市場狀態
            'market_state': {
                'momentum': analysis.get('momentum', 'neutral'),
                'position': analysis.get('macd_position', 'unknown'),
                'trend_strength': self._calculate_trend_strength(df)
            },
            
            # 統計數據
            'statistics': {
                'volatility': self._calculate_volatility(df),
                'macd_range': {
                    'max': analysis.get('max_macd', 0),
                    'min': analysis.get('min_macd', 0),
                    'avg': analysis.get('avg_macd', 0)
                }
            }
        }
        
        return signals
    
    def _determine_signal_type(self, analysis):
        """判斷信號類型"""
        signal_type = analysis.get('signal_type', 'none')
        momentum = analysis.get('momentum', 'neutral')
        
        if signal_type == 'golden_cross':
            return 'BUY'
        elif signal_type == 'death_cross':
            return 'SELL'
        elif momentum == 'bullish':
            return 'WEAK_BUY'
        elif momentum == 'bearish':
            return 'WEAK_SELL'
        else:
            return 'HOLD'
    
    def _calculate_signal_strength(self, analysis, df):
        """計算信號強度"""
        signal_type = analysis.get('signal_type', 'none')
        momentum = analysis.get('momentum', 'neutral')
        hist_trend = analysis.get('hist_trend', 'unknown')
        
        strength = 0
        
        # 金叉死叉加分
        if signal_type in ['golden_cross', 'death_cross']:
            strength += 40
        
        # 動量一致性加分
        if momentum == 'bullish' and hist_trend == 'up':
            strength += 30
        elif momentum == 'bearish' and hist_trend == 'down':
            strength += 30
        
        # MACD位置加分
        if analysis.get('macd_position') == 'above_zero' and momentum == 'bullish':
            strength += 20
        elif analysis.get('macd_position') == 'below_zero' and momentum == 'bearish':
            strength += 20
        
        # 趨勢強度加分
        trend_strength = self._calculate_trend_strength(df)
        strength += min(trend_strength * 10, 10)
        
        return min(strength, 100)
    
    def _calculate_confidence(self, analysis, df):
        """計算信號信心度"""
        base_confidence = 0.5
        
        # 數據量充足度
        if len(df) >= 50:
            base_confidence += 0.1
        
        # 信號明確度
        signal_type = analysis.get('signal_type', 'none')
        if signal_type in ['golden_cross', 'death_cross']:
            base_confidence += 0.2
        
        # 趨勢一致性
        if analysis.get('macd_trend') == analysis.get('hist_trend'):
            base_confidence += 0.1
        
        # 動量強度
        hist_abs = abs(analysis.get('latest_hist', 0))
        if hist_abs > 1000:  # 根據BTC價格調整
            base_confidence += 0.1
        
        return min(base_confidence, 0.95)
    
    def _generate_signal_reason(self, analysis):
        """生成信號原因說明"""
        signal_type = analysis.get('signal_type', 'none')
        momentum = analysis.get('momentum', 'neutral')
        position = analysis.get('macd_position', 'unknown')
        
        if signal_type == 'golden_cross':
            return "MACD金叉形成，趨勢轉強"
        elif signal_type == 'death_cross':
            return "MACD死叉形成，趨勢轉弱"
        elif momentum == 'bullish' and position == 'above_zero':
            return "MACD在零軸上方，動量向上"
        elif momentum == 'bearish' and position == 'below_zero':
            return "MACD在零軸下方，動量向下"
        elif momentum == 'bullish':
            return "柱狀圖擴張，動量增強"
        elif momentum == 'bearish':
            return "柱狀圖收縮，動量減弱"
        else:
            return "MACD信號不明確，建議觀望"
    
    def _calculate_trend_strength(self, df):
        """計算趨勢強度 (0-10)"""
        if len(df) < 10:
            return 0
        
        # 使用最近10期的MACD柱狀圖變化
        recent_hist = df['macd_hist'].tail(10)
        
        # 計算連續同向的期數
        consecutive_count = 0
        last_sign = None
        
        for hist in recent_hist:
            current_sign = 1 if hist > 0 else -1
            if last_sign is None or current_sign == last_sign:
                consecutive_count += 1
            else:
                consecutive_count = 1
            last_sign = current_sign
        
        # 計算平均絕對值
        avg_abs = recent_hist.abs().mean()
        
        # 綜合評分
        strength = min(consecutive_count * 2 + (avg_abs / 1000), 10)
        return max(0, strength)
    
    def _calculate_volatility(self, df):
        """計算價格波動率"""
        if len(df) < 20:
            return 0
        
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(24)  # 假設小時數據
        return volatility
    
    def get_multi_timeframe_analysis(self, symbol='btctwd'):
        """多時間框架MACD分析"""
        timeframes = [
            ('15', '15分鐘'),
            ('60', '1小時'), 
            ('240', '4小時'),
            ('1440', '1天')
        ]
        
        analysis_results = {}
        
        for period, name in timeframes:
            try:
                signals = self.get_macd_signals(symbol, period)
                if signals:
                    analysis_results[name] = {
                        'period': period,
                        'signal_type': signals['signals']['type'],
                        'strength': signals['signals']['strength'],
                        'confidence': signals['signals']['confidence'],
                        'momentum': signals['market_state']['momentum'],
                        'reason': signals['signals']['reason']
                    }
            except Exception as e:
                print(f"⚠️ {name} 分析失敗: {e}")
                analysis_results[name] = None
        
        return analysis_results
    
    def get_trading_recommendation(self, symbol='btctwd'):
        """獲取綜合交易建議"""
        multi_analysis = self.get_multi_timeframe_analysis(symbol)
        
        # 計算綜合評分
        buy_score = 0
        sell_score = 0
        total_weight = 0
        
        # 時間框架權重
        weights = {
            '15分鐘': 1,
            '1小時': 2,
            '4小時': 3,
            '1天': 4
        }
        
        for timeframe, weight in weights.items():
            if timeframe in multi_analysis and multi_analysis[timeframe]:
                analysis = multi_analysis[timeframe]
                signal_type = analysis['signal_type']
                strength = analysis['strength']
                confidence = analysis['confidence']
                
                score = strength * confidence * weight
                
                if signal_type in ['BUY', 'WEAK_BUY']:
                    buy_score += score
                elif signal_type in ['SELL', 'WEAK_SELL']:
                    sell_score += score
                
                total_weight += weight
        
        # 生成最終建議
        if total_weight == 0:
            return {
                'recommendation': 'HOLD',
                'confidence': 0.5,
                'reason': '數據不足，建議觀望',
                'details': multi_analysis
            }
        
        buy_avg = buy_score / total_weight if total_weight > 0 else 0
        sell_avg = sell_score / total_weight if total_weight > 0 else 0
        
        if buy_avg > sell_avg and buy_avg > 30:
            recommendation = 'BUY'
            confidence = min(buy_avg / 100, 0.9)
            reason = f"多時間框架偏多，綜合評分: {buy_avg:.1f}"
        elif sell_avg > buy_avg and sell_avg > 30:
            recommendation = 'SELL'
            confidence = min(sell_avg / 100, 0.9)
            reason = f"多時間框架偏空，綜合評分: {sell_avg:.1f}"
        else:
            recommendation = 'HOLD'
            confidence = 0.6
            reason = "多時間框架信號不一致，建議觀望"
        
        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'reason': reason,
            'buy_score': buy_avg,
            'sell_score': sell_avg,
            'details': multi_analysis
        }

# 使用示例
if __name__ == "__main__":
    analyzer = MACDAnalyzer()
    
    # 獲取單一時間框架信號
    signals = analyzer.get_macd_signals('btctwd', '60')
    if signals:
        print("📊 MACD信號分析:")
        print(f"信號類型: {signals['signals']['type']}")
        print(f"信號強度: {signals['signals']['strength']}")
        print(f"信心度: {signals['signals']['confidence']:.2%}")
        print(f"原因: {signals['signals']['reason']}")
    
    # 獲取多時間框架分析
    print("\n📈 多時間框架分析:")
    multi_analysis = analyzer.get_multi_timeframe_analysis('btctwd')
    for timeframe, analysis in multi_analysis.items():
        if analysis:
            print(f"{timeframe}: {analysis['signal_type']} (強度: {analysis['strength']}, 信心: {analysis['confidence']:.2%})")
    
    # 獲取交易建議
    print("\n🎯 交易建議:")
    recommendation = analyzer.get_trading_recommendation('btctwd')
    print(f"建議: {recommendation['recommendation']}")
    print(f"信心度: {recommendation['confidence']:.2%}")
    print(f"原因: {recommendation['reason']}")