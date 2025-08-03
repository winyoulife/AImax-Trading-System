#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析MA策略獲利
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import pandas as pd
from datetime import datetime
from src.data.live_macd_service import LiveMACDService
from src.core.multi_timeframe_trading_signals import detect_multi_timeframe_trading_signals

async def analyze_ma_profits():
    """分析MA策略獲利"""
    print("🔍 開始分析MA策略獲利...")
    
    try:
        # 獲取數據
        service = LiveMACDService()
        
        # 獲取1小時數據
        hourly_klines = await service._fetch_klines("btctwd", "60", 1000)
        if hourly_klines is None:
            print("❌ 無法獲取1小時數據")
            return
        
        hourly_df = service._calculate_macd(hourly_klines, 12, 26, 9)
        if hourly_df is None:
            print("❌ 無法計算1小時MACD")
            return
        
        # 獲取1小時MA數據
        hourly_ma_df = service._calculate_ma(hourly_klines, 9, 25, 99)
        if hourly_ma_df is None:
            print("❌ 無法計算1小時MA")
            return
        
        # 準備時間框架數據
        timeframe_dfs = {
            '30m': hourly_ma_df.tail(500).reset_index(drop=True)  # 使用1小時MA數據
        }
        
        # 檢測信號
        print("🎯 檢測多時間框架信號...")
        signals_dict, statistics, tracker = detect_multi_timeframe_trading_signals(
            hourly_df.tail(500).reset_index(drop=True), 
            timeframe_dfs
        )
        
        # 分析30分鐘MA策略獲利
        if '30m' in signals_dict and not signals_dict['30m'].empty:
            ma_signals = signals_dict['30m']
            print(f"\n📊 30分鐘MA策略信號分析:")
            print(f"總信號數: {len(ma_signals)}")
            
            # 提取買賣信號
            buy_signals = ma_signals[ma_signals['signal_type'] == 'buy'].copy()
            sell_signals = ma_signals[ma_signals['signal_type'] == 'sell'].copy()
            
            print(f"買進信號: {len(buy_signals)} 個")
            print(f"賣出信號: {len(sell_signals)} 個")
            
            if len(buy_signals) > 0:
                print(f"\n🟢 買進信號詳情:")
                for _, signal in buy_signals.iterrows():
                    print(f"  時間: {signal['datetime']}, 價格: {signal['close']:,.0f}, 序號: {signal['trade_sequence']}")
            
            if len(sell_signals) > 0:
                print(f"\n🔴 賣出信號詳情:")
                for _, signal in sell_signals.iterrows():
                    print(f"  時間: {signal['datetime']}, 價格: {signal['close']:,.0f}, 序號: {signal['trade_sequence']}")
            
            # 計算獲利
            print(f"\n💰 獲利分析:")
            total_profit = 0
            trade_count = 0
            
            # 按序號配對買賣信號
            for _, buy_signal in buy_signals.iterrows():
                buy_seq = buy_signal['trade_sequence']
                # 找到對應的賣出信號
                matching_sells = sell_signals[sell_signals['trade_sequence'] == buy_seq]
                
                if not matching_sells.empty:
                    sell_signal = matching_sells.iloc[0]
                    profit = sell_signal['close'] - buy_signal['close']
                    total_profit += profit
                    trade_count += 1
                    
                    print(f"  交易對 {buy_seq}:")
                    print(f"    買進: {buy_signal['datetime']} @ {buy_signal['close']:,.0f}")
                    print(f"    賣出: {sell_signal['datetime']} @ {sell_signal['close']:,.0f}")
                    print(f"    獲利: {profit:,.0f} TWD")
                    print()
            
            # 檢查是否有未配對的信號
            unmatched_buys = []
            unmatched_sells = []
            
            for _, buy_signal in buy_signals.iterrows():
                buy_seq = buy_signal['trade_sequence']
                matching_sells = sell_signals[sell_signals['trade_sequence'] == buy_seq]
                if matching_sells.empty:
                    unmatched_buys.append(buy_signal)
            
            for _, sell_signal in sell_signals.iterrows():
                sell_seq = sell_signal['trade_sequence']
                matching_buys = buy_signals[buy_signals['trade_sequence'] == sell_seq]
                if matching_buys.empty:
                    unmatched_sells.append(sell_signal)
            
            if unmatched_buys:
                print(f"⚠️  未配對的買進信號: {len(unmatched_buys)} 個")
                for signal in unmatched_buys:
                    print(f"    序號 {signal['trade_sequence']}: {signal['datetime']} @ {signal['close']:,.0f}")
            
            if unmatched_sells:
                print(f"⚠️  未配對的賣出信號: {len(unmatched_sells)} 個")
                for signal in unmatched_sells:
                    print(f"    序號 {signal['trade_sequence']}: {signal['datetime']} @ {signal['close']:,.0f}")
            
            # 總結
            print(f"\n📈 MA策略總結:")
            print(f"完整交易對: {trade_count} 對")
            print(f"總獲利: {total_profit:,.0f} TWD")
            if trade_count > 0:
                avg_profit = total_profit / trade_count
                print(f"平均每筆獲利: {avg_profit:,.0f} TWD")
                
                # 計算勝率
                winning_trades = sum(1 for _, buy in buy_signals.iterrows() 
                                   for _, sell in sell_signals.iterrows() 
                                   if buy['trade_sequence'] == sell['trade_sequence'] 
                                   and sell['close'] > buy['close'])
                
                if trade_count > 0:
                    win_rate = (winning_trades / trade_count) * 100
                    print(f"勝率: {win_rate:.1f}% ({winning_trades}/{trade_count})")
        
        else:
            print("❌ 沒有找到30分鐘MA策略信號")
        
        await service.close()
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函數"""
    asyncio.run(analyze_ma_profits())

if __name__ == "__main__":
    main()