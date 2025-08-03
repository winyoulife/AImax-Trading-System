#!/usr/bin/env python3
"""
測試增強版MACD回測分析器的核心功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import pandas as pd
from datetime import datetime
from src.data.live_macd_service import LiveMACDService

def detect_trading_signals(df):
    """測試交易信號檢測邏輯"""
    if len(df) < 2:
        return df
    
    # 初始化信號欄
    df['trading_signal'] = '持有'
    df['signal_type'] = 'hold'
    
    buy_count = 0
    sell_count = 0
    
    for i in range(1, len(df)):
        current = df.iloc[i]
        previous = df.iloc[i-1]
        
        # 買進信號：MACD柱為負，然後MACD線突然大於信號線
        if (previous['macd_hist'] < 0 and  # 前一個柱狀圖為負
            previous['macd'] <= previous['macd_signal'] and  # 前一個MACD <= 信號線
            current['macd'] > current['macd_signal']):  # 當前MACD > 信號線
            df.at[i, 'trading_signal'] = '🟢 買進'
            df.at[i, 'signal_type'] = 'buy'
            buy_count += 1
        
        # 賣出信號：MACD柱為正，然後信號線突然大於MACD線
        elif (previous['macd_hist'] > 0 and  # 前一個柱狀圖為正
              previous['macd'] >= previous['macd_signal'] and  # 前一個MACD >= 信號線
              current['macd_signal'] > current['macd']):  # 當前信號線 > MACD
            df.at[i, 'trading_signal'] = '🔴 賣出'
            df.at[i, 'signal_type'] = 'sell'
            sell_count += 1
        else:
            df.at[i, 'trading_signal'] = '⚪ 持有'
            df.at[i, 'signal_type'] = 'hold'
    
    return df, buy_count, sell_count

async def test_enhanced_macd_backtest():
    """測試增強版MACD回測功能"""
    print("🧪 測試增強版MACD回測分析器...")
    print("=" * 60)
    
    try:
        # 初始化服務
        service = LiveMACDService()
        
        # 獲取7天數據
        print("📡 正在獲取7天歷史數據...")
        klines = await service._fetch_klines("btctwd", "60", 400)
        
        if klines is None:
            print("❌ 無法獲取歷史數據")
            return
        
        print(f"✅ 獲取了 {len(klines)} 筆K線數據")
        
        # 計算MACD
        print("🧮 正在計算MACD指標...")
        macd_df = service._calculate_macd(klines, 12, 26, 9)
        
        if macd_df is None:
            print("❌ 無法計算MACD")
            return
        
        # 獲取最近7天數據
        df_7day = macd_df.tail(168).reset_index(drop=True)
        print(f"✅ 獲取了 {len(df_7day)} 筆7天MACD數據")
        
        # 檢測交易信號
        print("🎯 正在檢測交易信號...")
        df_with_signals, buy_count, sell_count = detect_trading_signals(df_7day)
        
        # 統計結果
        hold_count = len(df_with_signals) - buy_count - sell_count
        total_count = len(df_with_signals)
        
        print("\n📊 交易信號統計:")
        print("-" * 40)
        print(f"🟢 買進信號: {buy_count} 次 ({buy_count/total_count*100:.1f}%)")
        print(f"🔴 賣出信號: {sell_count} 次 ({sell_count/total_count*100:.1f}%)")
        print(f"⚪ 持有狀態: {hold_count} 次 ({hold_count/total_count*100:.1f}%)")
        print(f"📋 總數據點: {total_count} 筆")
        
        # 顯示最近的信號
        print("\n📈 最近10個交易信號:")
        print("-" * 60)
        recent_signals = df_with_signals.tail(10)
        for _, row in recent_signals.iterrows():
            time_str = row['datetime'].strftime('%m-%d %H:%M')
            signal = row['trading_signal']
            macd = row['macd']
            signal_line = row['macd_signal']
            hist = row['macd_hist']
            print(f"{time_str} | {signal:8s} | MACD:{macd:7.1f} | 信號:{signal_line:7.1f} | 柱:{hist:7.1f}")
        
        # 顯示數據範圍
        start_time = df_with_signals.iloc[0]['datetime'].strftime('%Y-%m-%d %H:%M')
        end_time = df_with_signals.iloc[-1]['datetime'].strftime('%Y-%m-%d %H:%M')
        print(f"\n⏰ 數據時間範圍: {start_time} 至 {end_time}")
        
        # 測試導出功能
        print("\n💾 測試數據導出功能...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"AImax/data/test_macd_7day_backtest_{timestamp}.csv"
        
        # 準備導出數據
        export_df = df_with_signals.copy()
        export_df['datetime_str'] = export_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 選擇要導出的欄位
        export_columns = ['datetime_str', 'close', 'macd_hist', 'macd', 'macd_signal', 
                        'volume', 'trading_signal', 'signal_type']
        export_df = export_df[export_columns]
        
        # 重命名欄位
        export_df.columns = ['時間', '價格', '柱狀圖', 'MACD線', '信號線', 
                           '成交量', '交易信號', '信號類型']
        
        # 導出到CSV
        export_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ 測試數據已導出到: {filename}")
        
        await service.close()
        
        print("\n🎉 增強版MACD回測分析器測試完成！")
        print("✅ 所有功能正常運行")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函數"""
    asyncio.run(test_enhanced_macd_backtest())

if __name__ == "__main__":
    main()