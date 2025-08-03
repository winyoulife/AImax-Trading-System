#!/usr/bin/env python3
"""
測試時間對齊問題
檢查為什麼相同價格出現在不同時間點
"""

import asyncio
import pandas as pd
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.live_macd_service import LiveMACDService

async def test_time_alignment():
    """測試時間對齊問題"""
    print("🕐 測試時間對齊問題")
    print("=" * 80)
    
    service = LiveMACDService()
    
    try:
        # 獲取數據
        print("📡 獲取數據...")
        hourly_data = await service._fetch_klines("btctwd", "60", 50)
        fifteen_data = await service._fetch_klines("btctwd", "15", 200)
        five_data = await service._fetch_klines("btctwd", "5", 600)
        
        if all(data is not None for data in [hourly_data, fifteen_data, five_data]):
            print(f"✅ 1小時數據: {len(hourly_data)} 筆")
            print(f"✅ 15分鐘數據: {len(fifteen_data)} 筆")
            print(f"✅ 5分鐘數據: {len(five_data)} 筆")
            
            # 找一個特定的1小時價格，看它在其他時間框架的哪個時間點出現
            target_time = hourly_data.iloc[-5]['datetime']  # 取倒數第5個時間點
            target_price = hourly_data.iloc[-5]['close']
            
            print(f"\n🎯 目標時間點: {target_time}")
            print(f"🎯 目標價格: {target_price:,.0f}")
            print("-" * 80)
            
            # 在15分鐘數據中找相同價格
            print("🔍 在15分鐘數據中尋找相同價格...")
            fifteen_matches = fifteen_data[abs(fifteen_data['close'] - target_price) < 1]
            if not fifteen_matches.empty:
                print(f"找到 {len(fifteen_matches)} 個匹配:")
                for _, row in fifteen_matches.iterrows():
                    time_diff = abs((row['datetime'] - target_time).total_seconds() / 60)
                    print(f"  時間: {row['datetime']} | 價格: {row['close']:,.0f} | 時間差: {time_diff:.0f}分鐘")
            else:
                print("❌ 未找到匹配的價格")
            
            # 在5分鐘數據中找相同價格
            print("\n🔍 在5分鐘數據中尋找相同價格...")
            five_matches = five_data[abs(five_data['close'] - target_price) < 1]
            if not five_matches.empty:
                print(f"找到 {len(five_matches)} 個匹配:")
                for _, row in five_matches.iterrows():
                    time_diff = abs((row['datetime'] - target_time).total_seconds() / 60)
                    print(f"  時間: {row['datetime']} | 價格: {row['close']:,.0f} | 時間差: {time_diff:.0f}分鐘")
            else:
                print("❌ 未找到匹配的價格")
            
            # 檢查時間戳格式
            print(f"\n📅 時間戳格式檢查:")
            print(f"1小時數據時間戳: {hourly_data.iloc[-1]['datetime']} (類型: {type(hourly_data.iloc[-1]['datetime'])})")
            print(f"15分鐘數據時間戳: {fifteen_data.iloc[-1]['datetime']} (類型: {type(fifteen_data.iloc[-1]['datetime'])})")
            print(f"5分鐘數據時間戳: {five_data.iloc[-1]['datetime']} (類型: {type(five_data.iloc[-1]['datetime'])})")
            
            # 檢查最近幾個時間點的對齊情況
            print(f"\n🔍 最近5個1小時時間點的對齊情況:")
            print("-" * 80)
            print("1小時時間 | 15分鐘最接近時間 | 5分鐘最接近時間 | 價格匹配")
            print("-" * 80)
            
            for i in range(-5, 0):
                h_time = hourly_data.iloc[i]['datetime']
                h_price = hourly_data.iloc[i]['close']
                
                # 找15分鐘最接近的時間點
                fifteen_closest_idx = (fifteen_data['datetime'] - h_time).abs().idxmin()
                fifteen_closest = fifteen_data.loc[fifteen_closest_idx]
                fifteen_time_diff = abs((fifteen_closest['datetime'] - h_time).total_seconds() / 60)
                
                # 找5分鐘最接近的時間點
                five_closest_idx = (five_data['datetime'] - h_time).abs().idxmin()
                five_closest = five_data.loc[five_closest_idx]
                five_time_diff = abs((five_closest['datetime'] - h_time).total_seconds() / 60)
                
                # 檢查價格匹配
                fifteen_price_match = abs(fifteen_closest['close'] - h_price) < 1
                five_price_match = abs(five_closest['close'] - h_price) < 1
                
                match_status = "✅" if fifteen_price_match and five_price_match else "❌"
                
                print(f"{h_time.strftime('%m-%d %H:%M')} | "
                      f"{fifteen_closest['datetime'].strftime('%m-%d %H:%M')}({fifteen_time_diff:.0f}m) | "
                      f"{five_closest['datetime'].strftime('%m-%d %H:%M')}({five_time_diff:.0f}m) | "
                      f"{match_status}")
                
                if not fifteen_price_match or not five_price_match:
                    print(f"    價格: 1H={h_price:,.0f} | 15M={fifteen_closest['close']:,.0f} | 5M={five_closest['close']:,.0f}")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_time_alignment())