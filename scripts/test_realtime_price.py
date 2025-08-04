#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試實時BTC價格獲取
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.data_fetcher import DataFetcher
from datetime import datetime
import time

def test_realtime_price():
    """測試實時價格獲取"""
    print("🔍 測試實時BTC價格獲取...")
    print("=" * 50)
    
    data_fetcher = DataFetcher()
    
    try:
        # 測試實時行情API
        print("📡 測試實時行情API...")
        ticker = data_fetcher.get_realtime_ticker('BTCTWD')
        
        if ticker:
            print(f"✅ 實時行情數據:")
            print(f"   當前價格: {ticker['last_price']:,.0f} TWD")
            print(f"   24h最高: {ticker['high_24h']:,.0f} TWD")
            print(f"   24h最低: {ticker['low_24h']:,.0f} TWD")
            print(f"   24h成交量: {ticker['volume_24h']:.4f} BTC")
            print(f"   更新時間: {ticker['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("❌ 無法獲取實時行情數據")
        
        print("\n" + "=" * 50)
        
        # 測試實時交易數據
        print("📊 測試實時交易數據...")
        df = data_fetcher.get_realtime_data_for_trading('BTCTWD', limit=5)
        
        if df is not None and not df.empty:
            print(f"✅ 獲取到 {len(df)} 條數據")
            print(f"   最新價格: {df['close'].iloc[-1]:,.0f} TWD")
            print(f"   最新時間: {df['timestamp'].iloc[-1]}")
            
            print(f"\n📈 最近5筆數據:")
            for i, row in df.iterrows():
                is_current = i == df.index[-1]
                marker = "🔴" if is_current else "  "
                print(f"   {marker} {row['timestamp'].strftime('%m-%d %H:%M')} - {row['close']:,.0f} TWD")
        else:
            print("❌ 無法獲取實時交易數據")
        
        print("\n" + "=" * 50)
        
        # 連續監控5次，每次間隔10秒
        print("🔄 連續監控價格變化 (5次，每10秒)...")
        for i in range(5):
            ticker = data_fetcher.get_realtime_ticker('BTCTWD')
            if ticker:
                now = datetime.now().strftime('%H:%M:%S')
                print(f"   [{now}] {ticker['last_price']:,.0f} TWD")
            else:
                print(f"   [{datetime.now().strftime('%H:%M:%S')}] 獲取失敗")
            
            if i < 4:  # 最後一次不需要等待
                time.sleep(10)
                
    except Exception as e:
        print(f"❌ 錯誤: {e}")

if __name__ == "__main__":
    test_realtime_price()