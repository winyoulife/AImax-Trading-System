#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試當前BTC價格獲取
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.data_fetcher import DataFetcher
from datetime import datetime

def test_current_price():
    """測試當前價格獲取"""
    print("🔍 測試BTC價格獲取...")
    print("=" * 50)
    
    data_fetcher = DataFetcher()
    
    try:
        # 獲取最新數據
        df = data_fetcher.fetch_data('BTCTWD', limit=5)
        
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            
            print(f"📊 最新BTC數據:")
            print(f"   價格: {latest['close']:,.0f} TWD")
            print(f"   成交量: {latest['volume']:.4f} BTC")
            print(f"   時間: {latest['timestamp']}")
            print(f"   最高: {latest['high']:,.0f} TWD")
            print(f"   最低: {latest['low']:,.0f} TWD")
            
            # 檢查數據新鮮度
            now = datetime.now()
            data_time = latest['timestamp']
            
            if hasattr(data_time, 'to_pydatetime'):
                data_time = data_time.to_pydatetime()
            
            time_diff = (now - data_time).total_seconds() / 60  # 分鐘
            
            print(f"\n⏰ 數據新鮮度:")
            print(f"   當前時間: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   數據時間: {data_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   時間差: {time_diff:.1f} 分鐘")
            
            if time_diff <= 60:  # 1小時內
                print("   ✅ 數據是最新的！")
            else:
                print("   ⚠️  數據可能不是最新的")
            
            # 顯示最近5筆數據
            print(f"\n📈 最近5筆數據:")
            for i, row in df.iterrows():
                print(f"   {row['timestamp'].strftime('%H:%M')} - {row['close']:,.0f} TWD")
                
        else:
            print("❌ 無法獲取數據")
            
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    test_current_price()