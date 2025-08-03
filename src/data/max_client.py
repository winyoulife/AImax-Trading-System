#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣MAX API客戶端 - 為AI提供實時市場數據
專注於技術指標和價格模式，不依賴市場新聞
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class MAXDataClient:
    """台灣MAX數據客戶端 - 專為AI分析優化"""
    
    def __init__(self, base_url: str = "https://max-api.maicoin.com/api/v2"):
        self.base_url = base_url
        self.session = None
        
        # API請求設置
        self.request_delay = 0.1
        self.max_retries = 3
        self.timeout = 10
        
        logger.info("📊 MAX數據客戶端初始化完成")
    
    async def get_enhanced_market_data(self, market: str = "btctwd") -> Dict[str, Any]:
        """
        獲取增強的市場數據，專為AI分析設計
        
        Returns:
            包含豐富技術指標的市場數據
        """
        try:
            # 並行獲取多種數據
            tasks = [
                self._get_current_ticker(market),
                self._get_recent_klines(market, period=1, limit=100),  # 1分鐘K線
                self._get_recent_klines(market, period=5, limit=50),   # 5分鐘K線
                self._get_recent_klines(market, period=60, limit=24),  # 1小時K線
            ]
            
            ticker, klines_1m, klines_5m, klines_1h = await asyncio.gather(*tasks)
            
            if not all([ticker, klines_1m is not None, klines_5m is not None]):
                logger.error("❌ 獲取市場數據失敗")
                return None
            
            # 計算技術指標
            enhanced_data = self._calculate_technical_indicators(
                ticker, klines_1m, klines_5m, klines_1h
            )
            
            # 添加市場微觀結構數據
            enhanced_data.update(self._calculate_market_microstructure(klines_1m))
            
            # 添加時間特徵
            enhanced_data.update(self._calculate_temporal_features())
            
            logger.info(f"✅ 獲取增強市場數據成功: {market}")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"❌ 獲取增強市場數據失敗: {e}")
            return None
    
    async def _get_current_ticker(self, market: str) -> Optional[Dict]:
        """獲取當前ticker數據"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"{self.base_url}/tickers/{market}"
            
            async with self.session.get(url, timeout=self.timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'symbol': market.upper(),
                        'timestamp': datetime.now(),
                        'last_price': float(data['last']),
                        'volume': float(data['vol']),
                        'high': float(data['high']),
                        'low': float(data['low']),
                        'open': float(data['open']),
                        'bid': float(data.get('buy', data['last'])),
                        'ask': float(data.get('sell', data['last']))
                    }
                else:
                    logger.error(f"❌ Ticker API錯誤: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ 獲取ticker失敗: {e}")
            return None
    
    async def _get_recent_klines(self, market: str, period: int, limit: int) -> Optional[pd.DataFrame]:
        """獲取最近的K線數據"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"{self.base_url}/k"
            params = {
                'market': market,
                'period': period,
                'limit': limit
            }
            
            async with self.session.get(url, params=params, timeout=self.timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data and isinstance(data, list):
                        df = pd.DataFrame(data, columns=[
                            'timestamp', 'open', 'high', 'low', 'close', 'volume'
                        ])
                        
                        # 數據類型轉換
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                        for col in ['open', 'high', 'low', 'close', 'volume']:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        
                        df = df.sort_values('timestamp').reset_index(drop=True)
                        return df
                    else:
                        return None
                else:
                    logger.error(f"❌ K線API錯誤: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ 獲取K線失敗: {e}")
            return None
    
    def _calculate_technical_indicators(self, ticker: Dict, klines_1m: pd.DataFrame, 
                                      klines_5m: pd.DataFrame, klines_1h: pd.DataFrame) -> Dict[str, Any]:
        """計算技術指標"""
        try:
            current_price = ticker['last_price']
            
            # 基礎價格信息
            base_data = {
                'current_price': current_price,
                'timestamp': ticker['timestamp'],
                'volume_24h': ticker['volume'],
                'high_24h': ticker['high'],
                'low_24h': ticker['low'],
                'open_24h': ticker['open']
            }
            
            # 價格變化（基於1分鐘數據）
            if len(klines_1m) >= 5:
                prices_1m = klines_1m['close'].values
                base_data.update({
                    'price_change_1m': ((current_price - prices_1m[-2]) / prices_1m[-2] * 100) if len(prices_1m) > 1 else 0,
                    'price_change_5m': ((current_price - prices_1m[-6]) / prices_1m[-6] * 100) if len(prices_1m) > 5 else 0,
                    'price_change_15m': ((current_price - prices_1m[-16]) / prices_1m[-16] * 100) if len(prices_1m) > 15 else 0,
                })
            
            # 技術指標（基於5分鐘數據）
            if len(klines_5m) >= 20:
                tech_indicators = self._calculate_indicators_for_timeframe(klines_5m)
                base_data.update(tech_indicators)
            
            # 趨勢指標（基於1小時數據）
            if len(klines_1h) >= 10:
                trend_indicators = self._calculate_trend_indicators(klines_1h)
                base_data.update(trend_indicators)
            
            return base_data
            
        except Exception as e:
            logger.error(f"❌ 計算技術指標失敗: {e}")
            return {'current_price': ticker['last_price'], 'timestamp': ticker['timestamp']}
    
    def _calculate_indicators_for_timeframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """為特定時間框架計算技術指標"""
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
            
            # 移動平均線
            if len(df) >= 20:
                indicators['sma_10'] = float(df['close'].rolling(10).mean().iloc[-1])
                indicators['sma_20'] = float(df['close'].rolling(20).mean().iloc[-1])
                indicators['ema_10'] = float(df['close'].ewm(span=10).mean().iloc[-1])
                indicators['ema_20'] = float(df['close'].ewm(span=20).mean().iloc[-1])
            
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
                
                # MACD趨勢判斷
                if macd_line.iloc[-1] > signal_line.iloc[-1]:
                    indicators['macd_trend'] = "金叉向上" if histogram.iloc[-1] > 0 else "金叉"
                else:
                    indicators['macd_trend'] = "死叉向下" if histogram.iloc[-1] < 0 else "死叉"
            
            # 布林帶
            if len(df) >= 20:
                sma_20 = df['close'].rolling(20).mean()
                std_20 = df['close'].rolling(20).std()
                upper_band = sma_20 + (std_20 * 2)
                lower_band = sma_20 - (std_20 * 2)
                
                current_price = df['close'].iloc[-1]
                indicators['bollinger_upper'] = float(upper_band.iloc[-1])
                indicators['bollinger_lower'] = float(lower_band.iloc[-1])
                indicators['bollinger_middle'] = float(sma_20.iloc[-1])
                
                # 布林帶位置
                bb_position = (current_price - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])
                indicators['bollinger_position'] = float(bb_position)
            
            return indicators
            
        except Exception as e:
            logger.error(f"❌ 計算時間框架指標失敗: {e}")
            return {}
    
    def _calculate_trend_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """計算趨勢指標"""
        try:
            trend_data = {}
            
            if len(df) >= 10:
                # 價格趨勢
                prices = df['close'].values
                recent_trend = np.polyfit(range(len(prices[-10:])), prices[-10:], 1)[0]
                trend_data['price_trend_slope'] = float(recent_trend)
                trend_data['price_trend'] = "上升" if recent_trend > 0 else "下降"
                
                # 成交量趨勢
                volumes = df['volume'].values
                volume_trend = np.polyfit(range(len(volumes[-10:])), volumes[-10:], 1)[0]
                trend_data['volume_trend_slope'] = float(volume_trend)
                trend_data['volume_trend'] = "增加" if volume_trend > 0 else "減少"
                
                # 波動率
                returns = df['close'].pct_change().dropna()
                if len(returns) > 0:
                    volatility = returns.std() * np.sqrt(24)  # 日化波動率
                    trend_data['volatility'] = float(volatility)
                    trend_data['volatility_level'] = "高" if volatility > 0.05 else "中" if volatility > 0.02 else "低"
            
            return trend_data
            
        except Exception as e:
            logger.error(f"❌ 計算趨勢指標失敗: {e}")
            return {}
    
    def _calculate_market_microstructure(self, klines_1m: pd.DataFrame) -> Dict[str, Any]:
        """計算市場微觀結構數據"""
        try:
            micro_data = {}
            
            if len(klines_1m) >= 10:
                # 成交量分析
                volumes = klines_1m['volume'].values
                avg_volume = np.mean(volumes[-10:])
                current_volume = volumes[-1]
                
                micro_data['volume_ratio'] = float(current_volume / avg_volume) if avg_volume > 0 else 1.0
                micro_data['volume_spike'] = current_volume > avg_volume * 1.5
                
                # 價格跳躍分析
                price_changes = klines_1m['close'].pct_change().abs()
                avg_change = price_changes.mean()
                recent_change = price_changes.iloc[-1]
                
                micro_data['price_jump_ratio'] = float(recent_change / avg_change) if avg_change > 0 else 1.0
                micro_data['price_jump'] = recent_change > avg_change * 2
                
                # 連續方向統計
                price_directions = np.sign(klines_1m['close'].diff())
                consecutive_up = 0
                consecutive_down = 0
                
                for direction in reversed(price_directions.values[-10:]):
                    if direction > 0:
                        consecutive_up += 1
                        break
                    elif direction < 0:
                        consecutive_down += 1
                        break
                
                micro_data['consecutive_up'] = consecutive_up
                micro_data['consecutive_down'] = consecutive_down
            
            return micro_data
            
        except Exception as e:
            logger.error(f"❌ 計算市場微觀結構失敗: {e}")
            return {}
    
    def _calculate_temporal_features(self) -> Dict[str, Any]:
        """計算時間特徵"""
        try:
            now = datetime.now()
            
            return {
                'hour_of_day': now.hour,
                'day_of_week': now.weekday(),  # 0=Monday, 6=Sunday
                'is_weekend': now.weekday() >= 5,
                'is_trading_hours': 0 <= now.hour <= 23,  # 加密貨幣24小時交易
                'time_zone': 'Asia/Taipei'
            }
            
        except Exception as e:
            logger.error(f"❌ 計算時間特徵失敗: {e}")
            return {}
    
    async def close(self):
        """關閉連接"""
        if self.session:
            await self.session.close()
    
    def format_data_for_ai(self, market_data: Dict[str, Any]) -> str:
        """將市場數據格式化為AI友好的格式"""
        try:
            if not market_data:
                return "市場數據不可用"
            
            # 基礎信息
            formatted = f"""
🔍 實時市場數據分析 ({market_data.get('timestamp', datetime.now()).strftime('%H:%M:%S')})

📊 價格信息:
- 當前價格: {market_data.get('current_price', 0):,.0f} TWD
- 1分鐘變化: {market_data.get('price_change_1m', 0):+.2f}%
- 5分鐘變化: {market_data.get('price_change_5m', 0):+.2f}%
- 15分鐘變化: {market_data.get('price_change_15m', 0):+.2f}%

📈 技術指標:
- RSI: {market_data.get('rsi', 50):.1f}
- MACD趨勢: {market_data.get('macd_trend', '中性')}
- 價格趨勢: {market_data.get('price_trend', '中性')}
- 波動率: {market_data.get('volatility_level', '中等')}

📊 成交量分析:
- 成交量比率: {market_data.get('volume_ratio', 1.0):.2f}x
- 成交量趨勢: {market_data.get('volume_trend', '穩定')}
- 成交量異常: {'是' if market_data.get('volume_spike', False) else '否'}

⏰ 市場時機:
- 交易時段: {market_data.get('hour_of_day', 0)}點
- 星期: {['一', '二', '三', '四', '五', '六', '日'][market_data.get('day_of_week', 0)]}
"""
            
            return formatted.strip()
            
        except Exception as e:
            logger.error(f"❌ 格式化數據失敗: {e}")
            return "數據格式化失敗"


# 創建全局客戶端實例
def create_max_client() -> MAXDataClient:
    """創建MAX數據客戶端實例"""
    return MAXDataClient()


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_max_client():
        """測試MAX數據客戶端"""
        print("🧪 測試MAX數據客戶端...")
        
        client = create_max_client()
        
        try:
            # 獲取增強市場數據
            market_data = await client.get_enhanced_market_data("btctwd")
            
            if market_data:
                print("✅ 獲取市場數據成功!")
                
                # 格式化顯示
                formatted_data = client.format_data_for_ai(market_data)
                print(formatted_data)
                
                print(f"\n📋 原始數據鍵數量: {len(market_data)}")
                print(f"主要指標: {list(market_data.keys())[:10]}")
                
            else:
                print("❌ 獲取市場數據失敗")
                
        finally:
            await client.close()
    
    # 運行測試
    asyncio.run(test_max_client())