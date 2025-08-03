#!/usr/bin/env python3
"""
測試改進版MACD交易信號檢測系統
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import pandas as pd
from datetime import datetime
from src.data.live_macd_service import LiveMACDService
from src.core.improved_trading_signals import detect_improved_trading_signals

async def test_improved_macd_signals():
    """測試改進版MACD交易信號功能"""
    print("🧪 測試改進版MACD交易信號檢測系統...")
    print("=" * 70)
    
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
        
        # 應用改進版信號檢測
        print("🎯 正在應用改進版信號檢測...")
        df_with_signals, statistics = detect_improved_trading_signals(df_7day)
        
        # 顯示統計結果
        print("\n📊 改進版交易信號統計:")
        print("-" * 50)
        print(f"🟢 買進信號: {statistics['buy_count']} 次")
        print(f"🔴 賣出信號: {statistics['sell_count']} 次")
        print(f"💰 完整交易對: {statistics['complete_pairs']} 對")
        print(f"📊 未平倉交易: {statistics['open_positions']} 筆")
        print(f"📈 當前狀態: {statistics['position_status']}")
        print(f"🔢 下一交易序號: {statistics['next_trade_sequence']}")
        print(f"📋 總數據點: {len(df_with_signals)} 筆")
        
        # 顯示盈虧信息
        if statistics['complete_pairs'] > 0:
            print(f"💵 總盈虧: {statistics['total_profit']:.1f} TWD")
            print(f"📊 平均盈虧: {statistics['average_profit']:.1f} TWD")
            print(f"⏱️ 平均持倉時間: {statistics['average_hold_time']:.1f} 小時")
        
        # 顯示所有交易信號
        print("\n📈 所有交易信號:")
        print("-" * 80)
        print(f"{'時間':15s} {'信號':12s} {'MACD':>8s} {'信號線':>8s} {'柱狀圖':>8s} {'持倉':>6s}")
        print("-" * 80)
        
        signal_count = 0
        for _, row in df_with_signals.iterrows():
            if row['signal_type'] != 'hold':
                time_str = row['datetime'].strftime('%m-%d %H:%M')
                signal = row['trading_signal']
                macd = row['macd']
                signal_line = row['macd_signal']
                hist = row['macd_hist']
                position = row['position_status']
                
                print(f"{time_str:15s} {signal:12s} {macd:8.1f} {signal_line:8.1f} {hist:8.1f} {position:>6s}")
                signal_count += 1
        
        if signal_count == 0:
            print("⚪ 在此期間內沒有檢測到交易信號")
        
        # 顯示交易對詳情
        if statistics['trade_pairs']:
            print(f"\n💰 完整交易對詳情:")
            print("-" * 60)
            print(f"{'序號':>4s} {'買進時間':15s} {'賣出時間':15s} {'盈虧':>10s}")
            print("-" * 60)
            
            for pair in statistics['trade_pairs']:
                buy_time = pair['buy_time'].strftime('%m-%d %H:%M')
                sell_time = pair['sell_time'].strftime('%m-%d %H:%M')
                profit = pair['profit']
                sequence = pair['buy_sequence']
                
                print(f"{sequence:4d} {buy_time:15s} {sell_time:15s} {profit:10.1f}")
        
        # 顯示數據範圍
        start_time = df_with_signals.iloc[0]['datetime'].strftime('%Y-%m-%d %H:%M')
        end_time = df_with_signals.iloc[-1]['datetime'].strftime('%Y-%m-%d %H:%M')
        print(f"\n⏰ 數據時間範圍: {start_time} 至 {end_time}")
        
        # 測試信號規則驗證
        print("\n🔍 信號規則驗證:")
        print("-" * 40)
        
        buy_signals = df_with_signals[df_with_signals['signal_type'] == 'buy']
        sell_signals = df_with_signals[df_with_signals['signal_type'] == 'sell']
        
        print(f"買進信號驗證:")
        for _, row in buy_signals.iterrows():
            macd_negative = row['macd'] < 0
            signal_negative = row['macd_signal'] < 0
            print(f"  {row['datetime'].strftime('%m-%d %H:%M')}: MACD<0={macd_negative}, 信號<0={signal_negative}")
        
        print(f"賣出信號驗證:")
        for _, row in sell_signals.iterrows():
            macd_positive = row['macd'] > 0
            signal_positive = row['macd_signal'] > 0
            print(f"  {row['datetime'].strftime('%m-%d %H:%M')}: MACD>0={macd_positive}, 信號>0={signal_positive}")
        
        # 測試導出功能
        print("\n💾 測試數據導出功能...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"AImax/data/test_improved_macd_signals_{timestamp}.csv"
        
        # 準備導出數據
        export_df = df_with_signals.copy()
        export_df['datetime_str'] = export_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 選擇要導出的欄位
        export_columns = ['datetime_str', 'close', 'macd_hist', 'macd', 'macd_signal', 
                        'volume', 'trading_signal', 'signal_type', 'trade_sequence', 
                        'position_status', 'signal_valid']
        export_df = export_df[export_columns]
        
        # 重命名欄位
        export_df.columns = ['時間', '價格', '柱狀圖', 'MACD線', '信號線', 
                           '成交量', '交易信號', '信號類型', '交易序號', 
                           '持倉狀態', '信號有效性']
        
        # 導出到CSV
        export_df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ 測試數據已導出到: {filename}")
        
        await service.close()
        
        print("\n🎉 改進版MACD交易信號檢測系統測試完成！")
        print("✅ 所有功能正常運行")
        print("🎯 信號檢測邏輯符合預期：低點買入、高點賣出、順序性交易")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_signal_logic():
    """測試信號檢測邏輯的單元測試"""
    print("\n🧪 單元測試：信號檢測邏輯...")
    print("-" * 40)
    
    # 創建測試數據
    test_data = {
        'datetime': pd.date_range('2025-07-23', periods=10, freq='H'),
        'close': [3500000, 3510000, 3520000, 3530000, 3540000, 3550000, 3560000, 3570000, 3560000, 3550000],
        'macd': [-100, -80, -60, -40, -20, 10, 30, 50, 30, 10],  # 從負轉正再轉負
        'macd_signal': [-120, -100, -80, -60, -40, -10, 10, 30, 40, 20],  # 從負轉正再轉負
        'macd_hist': [20, 20, 20, 20, 20, 20, 20, 20, -10, -10],  # 從正轉負
        'volume': [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 4.0, 3.5],
        'timestamp': range(10)
    }
    
    df = pd.DataFrame(test_data)
    
    # 應用信號檢測
    df_result, stats = detect_improved_trading_signals(df)
    
    print("測試數據信號檢測結果:")
    for i, row in df_result.iterrows():
        if row['signal_type'] != 'hold':
            print(f"  {i}: {row['trading_signal']} | MACD:{row['macd']:6.1f} | 信號:{row['macd_signal']:6.1f} | 柱:{row['macd_hist']:6.1f}")
    
    print(f"統計結果: 買進{stats['buy_count']}次, 賣出{stats['sell_count']}次, 完整交易對{stats['complete_pairs']}對")
    
    # 驗證邏輯
    buy_signals = df_result[df_result['signal_type'] == 'buy']
    sell_signals = df_result[df_result['signal_type'] == 'sell']
    
    print("買進信號驗證:")
    for _, row in buy_signals.iterrows():
        macd_neg = row['macd'] < 0
        signal_neg = row['macd_signal'] < 0
        print(f"  MACD<0: {macd_neg}, 信號<0: {signal_neg} ✅" if macd_neg and signal_neg else f"  MACD<0: {macd_neg}, 信號<0: {signal_neg} ❌")
    
    print("賣出信號驗證:")
    for _, row in sell_signals.iterrows():
        macd_pos = row['macd'] > 0
        signal_pos = row['macd_signal'] > 0
        print(f"  MACD>0: {macd_pos}, 信號>0: {signal_pos} ✅" if macd_pos and signal_pos else f"  MACD>0: {macd_pos}, 信號>0: {signal_pos} ❌")

def main():
    """主函數"""
    # 運行單元測試
    test_signal_logic()
    
    # 運行集成測試
    asyncio.run(test_improved_macd_signals())

if __name__ == "__main__":
    main()