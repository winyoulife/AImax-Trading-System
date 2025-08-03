#!/usr/bin/env python3
"""
實時 MACD 數據服務

直接從 MAX API 獲取 K線數據，計算實時 MACD 指標
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import aiohttp
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class LiveMACDService:
    """實時 MACD 數據服務"""
    
    def __init__(self, base_url: str = "https://max-api.maicoin.com/api/v2"):
        self.base_url = base_url
        self.session = None
        
    async def get_live_macd(self, market: str = "btctwd", period: str = "60", 
                           fast_period: int = 12, slow_period: int = 26, 
                           signal_period: int = 9) -> Optional[Dict]:
        """
        獲取實時 MACD 數據
        
        Args:
            market: 交易對 (如 btctwd)
            period: 時間週期 (60=1小時, 5=5分鐘)
            fast_period: 快線週期 (默認12)
            slow_period: 慢線週期 (默認26)
            signal_period: 信號線週期 (默認9)
            
        Returns:
            包含 MACD 數據的字典
        """
        try:
            # 獲取足夠的 K線數據
            limit = max(100, slow_period + signal_period + 20)  # 確保有足夠數據
            klines = await self._fetch_klines(market, period, limit)
            
            if klines is None or len(klines) < slow_period + signal_period:
                logger.error(f"數據不足，無法計算 MACD")
                return None
            
            # 計算 MACD
            macd_data = self._calculate_macd(
                klines, fast_period, slow_period, signal_period
            )
            
            if macd_data is None:
                return None
            
            # 獲取最新值
            latest = macd_data.iloc[-1]
            
            result = {
                'timestamp': latest['datetime'],
                'market': market.upper(),
                'period': f"{period}分鐘",
                'price': latest['close'],
                'macd': {
                    'histogram': round(latest['macd_hist'], 1),
                    'macd_line': round(latest['macd'], 1),
                    'signal_line': round(latest['macd_signal'], 1)
                },
                'trend': self._analyze_trend(macd_data),
                'parameters': {
                    'fast': fast_period,
                    'slow': slow_period,
                    'signal': signal_period
                }
            }
            
            logger.info(f"✅ 獲取 {market} MACD 數據成功")
            return result
            
        except Exception as e:
            logger.error(f"❌ 獲取 MACD 數據失敗: {e}")
            return None
    
    async def _fetch_klines(self, market: str, period: str, limit: int) -> Optional[pd.DataFrame]:
        """獲取 K線數據"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"{self.base_url}/k"
            params = {
                'market': market,
                'period': period,
                'limit': limit
            }
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if not data:
                        return None
                    
                    # 轉換為 DataFrame
                    df_data = []
                    for item in data:
                        df_data.append({
                            'timestamp': int(item[0]),
                            'datetime': datetime.fromtimestamp(int(item[0])),
                            'open': float(item[1]),
                            'high': float(item[2]),
                            'low': float(item[3]),
                            'close': float(item[4]),
                            'volume': float(item[5])
                        })
                    
                    df = pd.DataFrame(df_data)
                    df = df.sort_values('timestamp').reset_index(drop=True)
                    
                    return df
                else:
                    logger.error(f"API 錯誤: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"獲取 K線數據失敗: {e}")
            return None
    
    def _calculate_macd(self, df: pd.DataFrame, fast_period: int, 
                       slow_period: int, signal_period: int) -> Optional[pd.DataFrame]:
        """計算 MACD 指標"""
        try:
            if len(df) < slow_period + signal_period:
                return None
            
            # 計算 EMA
            exp1 = df['close'].ewm(span=fast_period, adjust=False).mean()
            exp2 = df['close'].ewm(span=slow_period, adjust=False).mean()
            
            # 計算 MACD 線
            df['macd'] = exp1 - exp2
            
            # 計算信號線
            df['macd_signal'] = df['macd'].ewm(span=signal_period, adjust=False).mean()
            
            # 計算柱狀圖
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            return df
            
        except Exception as e:
            logger.error(f"計算 MACD 失敗: {e}")
            return None
    
    def _calculate_ma(self, df: pd.DataFrame, ma9_period: int = 9, 
                     ma25_period: int = 25, ma99_period: int = 99) -> Optional[pd.DataFrame]:
        """計算移動平均線指標 (MA9, MA25, MA99)"""
        try:
            if len(df) < ma99_period:
                return None
            
            # 計算移動平均線
            df['ma9'] = df['close'].rolling(window=ma9_period).mean()
            df['ma25'] = df['close'].rolling(window=ma25_period).mean()
            df['ma99'] = df['close'].rolling(window=ma99_period).mean()
            
            # 計算MA信號
            # 買入信號：MA9 > MA25 > MA99 且價格 > MA9
            df['ma_buy_signal'] = (
                (df['ma9'] > df['ma25']) & 
                (df['ma25'] > df['ma99']) & 
                (df['close'] > df['ma9'])
            )
            
            # 賣出信號：MA9 < MA25 < MA99 且價格 < MA9
            df['ma_sell_signal'] = (
                (df['ma9'] < df['ma25']) & 
                (df['ma25'] < df['ma99']) & 
                (df['close'] < df['ma9'])
            )
            
            return df
            
        except Exception as e:
            logger.error(f"計算 MA 失敗: {e}")
            return None
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, str]:
        """分析 MACD 趨勢"""
        try:
            if len(df) < 2:
                return {'signal': '數據不足', 'trend': '未知'}
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            # 判斷金叉死叉
            if latest['macd'] > latest['macd_signal']:
                if prev['macd'] <= prev['macd_signal']:
                    signal = "🟢 金叉 (買入信號)"
                else:
                    signal = "🟢 多頭趨勢"
            else:
                if prev['macd'] >= prev['macd_signal']:
                    signal = "🔴 死叉 (賣出信號)"
                else:
                    signal = "🔴 空頭趨勢"
            
            # 判斷柱狀圖趨勢
            if latest['macd_hist'] > prev['macd_hist']:
                trend = "📈 動能增強"
            elif latest['macd_hist'] < prev['macd_hist']:
                trend = "📉 動能減弱"
            else:
                trend = "➡️ 動能持平"
            
            return {
                'signal': signal,
                'trend': trend,
                'histogram_direction': '上升' if latest['macd_hist'] > prev['macd_hist'] else '下降'
            }
            
        except Exception as e:
            logger.error(f"分析趨勢失敗: {e}")
            return {'signal': '分析失敗', 'trend': '未知'}
    
    def format_for_display(self, macd_data: Dict) -> str:
        """格式化顯示 MACD 數據"""
        if not macd_data:
            return "❌ MACD 數據不可用"
        
        return f"""
🎯 實時 MACD 指標 ({macd_data['market']})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ 時間: {macd_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
💰 價格: {macd_data['price']:,.0f} TWD
📊 週期: {macd_data['period']}

📈 MACD 數值:
   柱狀圖: {macd_data['macd']['histogram']:>8.1f}
   MACD線: {macd_data['macd']['macd_line']:>8.1f}  
   信號線: {macd_data['macd']['signal_line']:>8.1f}

🔍 趨勢分析:
   信號: {macd_data['trend']['signal']}
   動能: {macd_data['trend']['trend']}

⚙️ 參數: ({macd_data['parameters']['fast']}, {macd_data['parameters']['slow']}, {macd_data['parameters']['signal']})
"""
    
    async def close(self):
        """關閉連接"""
        if self.session:
            await self.session.close()

# 便利函數
async def get_btc_macd(period: str = "60") -> Optional[Dict]:
    """快速獲取 BTC/TWD 的 MACD 數據"""
    service = LiveMACDService()
    try:
        return await service.get_live_macd("btctwd", period)
    finally:
        await service.close()

async def get_multiple_timeframes(market: str = "btctwd") -> Dict[str, Dict]:
    """獲取多個時間週期的 MACD 數據"""
    service = LiveMACDService()
    try:
        timeframes = ["5", "15", "60", "240"]  # 5分鐘, 15分鐘, 1小時, 4小時
        results = {}
        
        for tf in timeframes:
            macd_data = await service.get_live_macd(market, tf)
            if macd_data:
                results[f"{tf}分鐘"] = macd_data
        
        return results
    finally:
        await service.close()

# 測試代碼
if __name__ == "__main__":
    async def test_service():
        """測試 MACD 服務"""
        print("🧪 測試實時 MACD 服務...")
        
        service = LiveMACDService()
        
        try:
            # 測試單個時間週期
            macd_data = await service.get_live_macd("btctwd", "60")
            
            if macd_data:
                print("✅ 獲取 MACD 數據成功!")
                print(service.format_for_display(macd_data))
            else:
                print("❌ 獲取 MACD 數據失敗")
            
            # 測試多時間週期
            print("\n🔄 獲取多時間週期數據...")
            multi_data = await get_multiple_timeframes("btctwd")
            
            for timeframe, data in multi_data.items():
                print(f"\n📊 {timeframe}:")
                print(f"   MACD: {data['macd']['macd_line']:.1f}")
                print(f"   信號: {data['trend']['signal']}")
                
        finally:
            await service.close()
    
    # 運行測試
    asyncio.run(test_service())