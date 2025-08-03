#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實時技術指標計算器 - 為AI提供豐富的技術分析數據
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TechnicalIndicatorCalculator:
    """實時技術指標計算器"""
    
    def __init__(self):
        """初始化技術指標計算器"""
        self.cache = {}  # 緩存計算結果
        logger.info("📊 技術指標計算器初始化完成")
    
    def calculate_comprehensive_indicators(self, klines_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        計算全面的技術指標
        
        Args:
            klines_data: 包含不同時間框架的K線數據
                - '1m': 1分鐘K線
                - '5m': 5分鐘K線
                - '1h': 1小時K線
        
        Returns:
            包含所有技術指標的字典
        """
        try:
            indicators = {}
            
            # 基於1分鐘數據的短期指標
            if '1m' in klines_data and len(klines_data['1m']) >= 20:
                short_term = self._calculate_short_term_indicators(klines_data['1m'])
                indicators.update({f"short_{k}": v for k, v in short_term.items()})
            
            # 基於5分鐘數據的中期指標
            if '5m' in klines_data and len(klines_data['5m']) >= 50:
                medium_term = self._calculate_medium_term_indicators(klines_data['5m'])
                indicators.update({f"medium_{k}": v for k, v in medium_term.items()})
            
            # 基於1小時數據的長期指標
            if '1h' in klines_data and len(klines_data['1h']) >= 24:
                long_term = self._calculate_long_term_indicators(klines_data['1h'])
                indicators.update({f"long_{k}": v for k, v in long_term.items()})
            
            # 跨時間框架分析
            cross_timeframe = self._calculate_cross_timeframe_analysis(klines_data)
            indicators.update(cross_timeframe)
            
            # 市場情緒指標
            sentiment = self._calculate_market_sentiment(klines_data)
            indicators.update(sentiment)
            
            logger.info(f"✅ 計算了 {len(indicators)} 個技術指標")
            return indicators
            
        except Exception as e:
            logger.error(f"❌ 技術指標計算失敗: {e}")
            return {}
    
    def _calculate_short_term_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """計算短期指標（1分鐘數據）"""
        try:
            indicators = {}
            
            # 快速移動平均
            indicators['ema_5'] = float(df['close'].ewm(span=5).mean().iloc[-1])
            indicators['ema_10'] = float(df['close'].ewm(span=10).mean().iloc[-1])
            indicators['sma_5'] = float(df['close'].rolling(5).mean().iloc[-1])
            indicators['sma_10'] = float(df['close'].rolling(10).mean().iloc[-1])
            
            # 價格動量
            indicators['momentum_5'] = float((df['close'].iloc[-1] - df['close'].iloc[-6]) / df['close'].iloc[-6] * 100)
            indicators['momentum_10'] = float((df['close'].iloc[-1] - df['close'].iloc[-11]) / df['close'].iloc[-11] * 100)
            
            # 成交量指標
            indicators['volume_sma'] = float(df['volume'].rolling(10).mean().iloc[-1])
            indicators['volume_ratio'] = float(df['volume'].iloc[-1] / indicators['volume_sma'])
            
            # 價格波動
            returns = df['close'].pct_change()
            indicators['volatility_1m'] = float(returns.rolling(10).std() * np.sqrt(1440))  # 日化波動率
            
            # 支撐阻力
            recent_high = float(df['high'].rolling(10).max().iloc[-1])
            recent_low = float(df['low'].rolling(10).min().iloc[-1])
            current_price = float(df['close'].iloc[-1])
            
            indicators['resistance_level'] = recent_high
            indicators['support_level'] = recent_low
            indicators['price_position'] = (current_price - recent_low) / (recent_high - recent_low) if recent_high != recent_low else 0.5
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ 短期指標計算失敗: {e}")
            return {}
    
    def _calculate_medium_term_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """計算中期指標（5分鐘數據）"""
        try:
            indicators = {}
            
            # RSI
            if len(df) >= 14:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators['rsi'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50
                
                # RSI趨勢
                rsi_trend = rsi.diff().iloc[-1]
                indicators['rsi_trend'] = "上升" if rsi_trend > 0 else "下降" if rsi_trend < 0 else "平穩"
            
            # MACD
            if len(df) >= 26:
                ema_12 = df['close'].ewm(span=12).mean()
                ema_26 = df['close'].ewm(span=26).mean()
                macd_line = ema_12 - ema_26
                signal_line = macd_line.ewm(span=9).mean()
                histogram = macd_line - signal_line
                
                indicators['macd'] = float(macd_line.iloc[-1])
                indicators['macd_signal'] = float(signal_line.iloc[-1])
                indicators['macd_histogram'] = float(histogram.iloc[-1])
                
                # MACD信號
                if macd_line.iloc[-1] > signal_line.iloc[-1]:
                    if macd_line.iloc[-2] <= signal_line.iloc[-2]:
                        indicators['macd_signal_type'] = "金叉"
                    else:
                        indicators['macd_signal_type'] = "多頭"
                else:
                    if macd_line.iloc[-2] >= signal_line.iloc[-2]:
                        indicators['macd_signal_type'] = "死叉"
                    else:
                        indicators['macd_signal_type'] = "空頭"
            
            # 布林帶
            if len(df) >= 20:
                sma_20 = df['close'].rolling(20).mean()
                std_20 = df['close'].rolling(20).std()
                upper_band = sma_20 + (std_20 * 2)
                lower_band = sma_20 - (std_20 * 2)
                
                current_price = df['close'].iloc[-1]
                indicators['bb_upper'] = float(upper_band.iloc[-1])
                indicators['bb_middle'] = float(sma_20.iloc[-1])
                indicators['bb_lower'] = float(lower_band.iloc[-1])
                indicators['bb_position'] = float((current_price - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1]))
                
                # 布林帶信號
                if current_price > upper_band.iloc[-1]:
                    indicators['bb_signal'] = "超買"
                elif current_price < lower_band.iloc[-1]:
                    indicators['bb_signal'] = "超賣"
                else:
                    indicators['bb_signal'] = "正常"
            
            # KDJ指標
            if len(df) >= 9:
                low_9 = df['low'].rolling(9).min()
                high_9 = df['high'].rolling(9).max()
                rsv = (df['close'] - low_9) / (high_9 - low_9) * 100
                k = rsv.ewm(com=2).mean()
                d = k.ewm(com=2).mean()
                j = 3 * k - 2 * d
                
                indicators['kdj_k'] = float(k.iloc[-1])
                indicators['kdj_d'] = float(d.iloc[-1])
                indicators['kdj_j'] = float(j.iloc[-1])
                
                # KDJ信號
                if k.iloc[-1] > d.iloc[-1] and k.iloc[-2] <= d.iloc[-2]:
                    indicators['kdj_signal'] = "金叉"
                elif k.iloc[-1] < d.iloc[-1] and k.iloc[-2] >= d.iloc[-2]:
                    indicators['kdj_signal'] = "死叉"
                else:
                    indicators['kdj_signal'] = "持續"
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ 中期指標計算失敗: {e}")
            return {}
    
    def _calculate_long_term_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """計算長期指標（1小時數據）"""
        try:
            indicators = {}
            
            # 長期移動平均
            if len(df) >= 20:
                indicators['sma_20'] = float(df['close'].rolling(20).mean().iloc[-1])
                indicators['ema_20'] = float(df['close'].ewm(span=20).mean().iloc[-1])
                
                # 趨勢判斷
                current_price = df['close'].iloc[-1]
                if current_price > indicators['sma_20']:
                    indicators['trend_sma20'] = "上升"
                else:
                    indicators['trend_sma20'] = "下降"
            
            # 價格通道
            if len(df) >= 20:
                high_20 = df['high'].rolling(20).max()
                low_20 = df['low'].rolling(20).min()
                
                indicators['channel_high'] = float(high_20.iloc[-1])
                indicators['channel_low'] = float(low_20.iloc[-1])
                indicators['channel_position'] = float((df['close'].iloc[-1] - low_20.iloc[-1]) / (high_20.iloc[-1] - low_20.iloc[-1]))
            
            # 成交量趨勢
            if len(df) >= 10:
                volume_trend = np.polyfit(range(10), df['volume'].iloc[-10:].values, 1)[0]
                indicators['volume_trend_slope'] = float(volume_trend)
                indicators['volume_trend'] = "增加" if volume_trend > 0 else "減少"
            
            # 波動率分析
            returns = df['close'].pct_change().dropna()
            if len(returns) >= 10:
                indicators['volatility_1h'] = float(returns.rolling(10).std() * np.sqrt(24))
                indicators['volatility_level'] = "高" if indicators['volatility_1h'] > 0.05 else "中" if indicators['volatility_1h'] > 0.02 else "低"
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ 長期指標計算失敗: {e}")
            return {}
    
    def _calculate_cross_timeframe_analysis(self, klines_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """跨時間框架分析"""
        try:
            analysis = {}
            
            # 多時間框架趨勢一致性
            trends = []
            
            if '1m' in klines_data and len(klines_data['1m']) >= 10:
                short_trend = self._get_price_trend(klines_data['1m'], 10)
                trends.append(short_trend)
                analysis['trend_1m'] = short_trend
            
            if '5m' in klines_data and len(klines_data['5m']) >= 10:
                medium_trend = self._get_price_trend(klines_data['5m'], 10)
                trends.append(medium_trend)
                analysis['trend_5m'] = medium_trend
            
            if '1h' in klines_data and len(klines_data['1h']) >= 10:
                long_trend = self._get_price_trend(klines_data['1h'], 10)
                trends.append(long_trend)
                analysis['trend_1h'] = long_trend
            
            # 趨勢一致性評分
            if trends:
                up_count = trends.count("上升")
                down_count = trends.count("下降")
                total = len(trends)
                
                analysis['trend_consistency'] = max(up_count, down_count) / total
                analysis['dominant_trend'] = "上升" if up_count > down_count else "下降" if down_count > up_count else "震盪"
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ 跨時間框架分析失敗: {e}")
            return {}
    
    def _calculate_market_sentiment(self, klines_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """計算市場情緒指標"""
        try:
            sentiment = {}
            
            # 基於5分鐘數據的情緒分析
            if '5m' in klines_data and len(klines_data['5m']) >= 20:
                df = klines_data['5m']
                
                # 多空力量對比
                green_candles = (df['close'] > df['open']).sum()
                red_candles = (df['close'] < df['open']).sum()
                total_candles = len(df)
                
                sentiment['bullish_ratio'] = green_candles / total_candles
                sentiment['bearish_ratio'] = red_candles / total_candles
                
                # 市場情緒評級
                if sentiment['bullish_ratio'] > 0.6:
                    sentiment['market_mood'] = "樂觀"
                elif sentiment['bearish_ratio'] > 0.6:
                    sentiment['market_mood'] = "悲觀"
                else:
                    sentiment['market_mood'] = "中性"
                
                # 成交量情緒
                recent_volume = df['volume'].iloc[-5:].mean()
                avg_volume = df['volume'].mean()
                sentiment['volume_sentiment'] = "活躍" if recent_volume > avg_volume * 1.2 else "低迷" if recent_volume < avg_volume * 0.8 else "正常"
            
            return sentiment
            
        except Exception as e:
            logger.error(f"❌ 市場情緒計算失敗: {e}")
            return {}
    
    def _get_price_trend(self, df: pd.DataFrame, periods: int) -> str:
        """獲取價格趨勢"""
        try:
            if len(df) < periods:
                return "不明"
            
            prices = df['close'].iloc[-periods:].values
            trend_slope = np.polyfit(range(periods), prices, 1)[0]
            
            if trend_slope > 0:
                return "上升"
            elif trend_slope < 0:
                return "下降"
            else:
                return "震盪"
                
        except Exception:
            return "不明"
    
    def format_indicators_for_ai(self, indicators: Dict[str, Any]) -> str:
        """將技術指標格式化為AI友好的格式"""
        try:
            if not indicators:
                return "技術指標數據不可用"
            
            formatted = f"""
📊 技術指標全面分析

🔥 短期指標 (1分鐘):
- EMA5: {indicators.get('short_ema_5', 'N/A'):,.0f}
- EMA10: {indicators.get('short_ema_10', 'N/A'):,.0f}
- 5分鐘動量: {indicators.get('short_momentum_5', 0):+.2f}%
- 成交量比率: {indicators.get('short_volume_ratio', 1.0):.2f}x
- 價格位置: {indicators.get('short_price_position', 0.5):.1%}

📈 中期指標 (5分鐘):
- RSI: {indicators.get('medium_rsi', 50):.1f} ({indicators.get('medium_rsi_trend', '平穩')})
- MACD: {indicators.get('medium_macd_signal_type', '中性')}
- 布林帶: {indicators.get('medium_bb_signal', '正常')} (位置: {indicators.get('medium_bb_position', 0.5):.1%})
- KDJ: {indicators.get('medium_kdj_signal', '持續')} (K:{indicators.get('medium_kdj_k', 50):.1f})

📊 長期指標 (1小時):
- SMA20趨勢: {indicators.get('long_trend_sma20', '不明')}
- 通道位置: {indicators.get('long_channel_position', 0.5):.1%}
- 成交量趨勢: {indicators.get('long_volume_trend', '穩定')}
- 波動率: {indicators.get('long_volatility_level', '中等')}

🎯 跨時間框架分析:
- 主導趨勢: {indicators.get('dominant_trend', '震盪')}
- 趨勢一致性: {indicators.get('trend_consistency', 0.5):.1%}
- 1分鐘趨勢: {indicators.get('trend_1m', '不明')}
- 5分鐘趨勢: {indicators.get('trend_5m', '不明')}
- 1小時趨勢: {indicators.get('trend_1h', '不明')}

💭 市場情緒:
- 市場情緒: {indicators.get('market_mood', '中性')}
- 多頭比例: {indicators.get('bullish_ratio', 0.5):.1%}
- 空頭比例: {indicators.get('bearish_ratio', 0.5):.1%}
- 成交量情緒: {indicators.get('volume_sentiment', '正常')}
"""
            
            return formatted.strip()
            
        except Exception as e:
            logger.error(f"❌ 指標格式化失敗: {e}")
            return "技術指標格式化失敗"


# 創建全局技術指標計算器實例
def create_technical_calculator() -> TechnicalIndicatorCalculator:
    """創建技術指標計算器實例"""
    return TechnicalIndicatorCalculator()


# 測試代碼
if __name__ == "__main__":
    print("🧪 測試技術指標計算器...")
    
    # 創建測試數據
    import pandas as pd
    from datetime import datetime, timedelta
    
    # 模擬K線數據
    dates = pd.date_range(start=datetime.now() - timedelta(hours=2), periods=120, freq='1min')
    test_data = {
        '1m': pd.DataFrame({
            'timestamp': dates,
            'open': np.random.normal(1500000, 10000, 120),
            'high': np.random.normal(1505000, 10000, 120),
            'low': np.random.normal(1495000, 10000, 120),
            'close': np.random.normal(1500000, 10000, 120),
            'volume': np.random.normal(1000, 200, 120)
        }),
        '5m': pd.DataFrame({
            'timestamp': pd.date_range(start=datetime.now() - timedelta(hours=4), periods=48, freq='5min'),
            'open': np.random.normal(1500000, 15000, 48),
            'high': np.random.normal(1510000, 15000, 48),
            'low': np.random.normal(1490000, 15000, 48),
            'close': np.random.normal(1500000, 15000, 48),
            'volume': np.random.normal(5000, 1000, 48)
        }),
        '1h': pd.DataFrame({
            'timestamp': pd.date_range(start=datetime.now() - timedelta(hours=24), periods=24, freq='1h'),
            'open': np.random.normal(1500000, 25000, 24),
            'high': np.random.normal(1520000, 25000, 24),
            'low': np.random.normal(1480000, 25000, 24),
            'close': np.random.normal(1500000, 25000, 24),
            'volume': np.random.normal(20000, 5000, 24)
        })
    }
    
    # 測試計算器
    calculator = create_technical_calculator()
    indicators = calculator.calculate_comprehensive_indicators(test_data)
    
    print(f"✅ 計算了 {len(indicators)} 個技術指標")
    
    # 格式化顯示
    formatted = calculator.format_indicators_for_ai(indicators)
    print(formatted)