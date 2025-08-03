#!/usr/bin/env python3
"""
測試不同時間框架在相同時間點的價格一致性
檢查MAX API是否在同一時間點返回相同的價格
"""

import asyncio
import aiohttp
import pandas as pd
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.live_macd_service import LiveMACDService

async def test_price_consistency():
    """測試價格一致性"""
    print("🔍 測試不同時間框架在相同時間點的價格一致性")
    print("=" * 60)
    
    service = LiveMACDService()
    
    try:
        # 獲取不同時間框架的數據
        print("📡 獲取不同時間框架的K線數據...")
        
        # 1小時數據
        hourly_data = await service._fetch_klines("btctwd", "60", 50)
        print(f"✅ 1小時數據: {len(hourly_data) if hourly_data is not None else 0} 筆")
        
        # 30分鐘數據
        thirty_data = await service._fetch_klines("btctwd", "30", 100)
        print(f"✅ 30分鐘數據: {len(thirty_data) if thirty_data is not None else 0} 筆")
        
        # 15分鐘數據
        fifteen_data = await service._fetch_klines("btctwd", "15", 200)
        print(f"✅ 15分鐘數據: {len(fifteen_data) if fifteen_data is not None else 0} 筆")
        
        # 5分鐘數據
        five_data = await service._fetch_klines("btctwd", "5", 600)
        print(f"✅ 5分鐘數據: {len(five_data) if five_data is not None else 0} 筆")
        
        print("\n🔍 比較相同時間點的價格...")
        print("-" * 60)
        
        if all(data is not None for data in [hourly_data, thirty_data, fifteen_data, five_data]):
            # 找到共同的時間點
            hourly_times = set(hourly_data['datetime'].dt.floor('H'))
            thirty_times = set(thirty_data['datetime'].dt.floor('H'))
            fifteen_times = set(fifteen_data['datetime'].dt.floor('H'))
            five_times = set(five_data['datetime'].dt.floor('H'))
            
            # 找到所有時間框架都有的時間點
            common_times = hourly_times & thirty_times & fifteen_times & five_times
            common_times = sorted(list(common_times))[-10:]  # 取最近10個時間點
            
            print(f"找到 {len(common_times)} 個共同時間點")
            print("\n時間點比較 (格式: 時間 | 1H價格 | 30M價格 | 15M價格 | 5M價格 | 差異)")
            print("-" * 100)
            
            for time_point in common_times:
                # 找到每個時間框架在該時間點的價格
                hourly_price = None
                thirty_price = None
                fifteen_price = None
                five_price = None
                
                # 1小時價格
                hourly_match = hourly_data[hourly_data['datetime'].dt.floor('H') == time_point]
                if not hourly_match.empty:
                    hourly_price = hourly_match.iloc[0]['close']
                
                # 30分鐘價格 (找最接近整點的)
                thirty_match = thirty_data[thirty_data['datetime'].dt.floor('H') == time_point]
                if not thirty_match.empty:
                    thirty_price = thirty_match.iloc[-1]['close']  # 取最後一個
                
                # 15分鐘價格 (找最接近整點的)
                fifteen_match = fifteen_data[fifteen_data['datetime'].dt.floor('H') == time_point]
                if not fifteen_match.empty:
                    fifteen_price = fifteen_match.iloc[-1]['close']  # 取最後一個
                
                # 5分鐘價格 (找最接近整點的)
                five_match = five_data[five_data['datetime'].dt.floor('H') == time_point]
                if not five_match.empty:
                    five_price = five_match.iloc[-1]['close']  # 取最後一個
                
                # 計算價格差異
                prices = [p for p in [hourly_price, thirty_price, fifteen_price, five_price] if p is not None]
                if prices:
                    max_price = max(prices)
                    min_price = min(prices)
                    diff = max_price - min_price
                    diff_pct = (diff / min_price) * 100 if min_price > 0 else 0
                    
                    status = "✅ 一致" if diff < 1 else f"❌ 差異 {diff:.0f} ({diff_pct:.3f}%)"
                    
                    print(f"{time_point.strftime('%m-%d %H:%M')} | "
                          f"{hourly_price:>8.0f} | "
                          f"{thirty_price:>8.0f} | "
                          f"{fifteen_price:>8.0f} | "
                          f"{five_price:>8.0f} | "
                          f"{status}")
        
        print("\n📋 API調用詳情:")
        print(f"API URL: https://max-api.maicoin.com/api/v2/k")
        print(f"參數格式: market=btctwd&period=[60|30|15|5]&limit=[數量]")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_price_consistency())