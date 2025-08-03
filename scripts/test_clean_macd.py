#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試乾淨版MACD策略，確保獲利計算一致
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import pandas as pd
from datetime import datetime
from src.data.live_macd_service import LiveMACDService
from src.core.improved_trading_signals import detect_improved_trading_signals

async def test_clean_macd():
    """測試乾淨版MACD策略"""
    print("🔍 測試乾淨版1小時MACD策略...")
    
    try:
        # 獲取數據 - 使用與比較腳本完全相同的參數
        service = LiveMACDService()
        
        # 獲取1000筆數據，然後取最後500筆 - 與比較腳本一致
        hourly_klines = await service._fetch_klines("btctwd", "60", 1000)
        if hourly_klines is None:
            print("❌ 無法獲取1小時數據")
            return
        
        # 計算MACD數據
        hourly_macd_df = service._calculate_macd(hourly_klines, 12, 26, 9)
        if hourly_macd_df is None:
            print("❌ 無法計算1小時MACD")
            return
        
        # 使用相同的數據範圍 - 最後500筆
        macd_df = hourly_macd_df.tail(500).reset_index(drop=True)
        
        print(f"📊 數據範圍: {len(macd_df)} 筆1小時數據")
        print(f"時間範圍: {macd_df.iloc[0]['datetime']} 至 {macd_df.iloc[-1]['datetime']}")
        print()
        
        # 檢測MACD信號 - 使用相同的函數
        print("🎯 檢測1小時MACD交易信號...")
        macd_signals, macd_stats = detect_improved_trading_signals(macd_df)
        
        print(f"📊 1小時MACD策略結果:")
        print(f"總數據點: {len(macd_signals)}")
        print(f"買進信號: {macd_stats['buy_count']} 個")
        print(f"賣出信號: {macd_stats['sell_count']} 個")
        print(f"完整交易對: {macd_stats['complete_pairs']} 對")
        
        if macd_stats['complete_pairs'] > 0:
            print(f"總獲利: {macd_stats['total_profit']:,.0f} TWD")
            print(f"平均獲利: {macd_stats['average_profit']:,.0f} TWD")
            print(f"平均持倉時間: {macd_stats['average_hold_time']:.1f} 小時")
        
        # 顯示詳細交易記錄
        macd_buy_signals = macd_signals[macd_signals['signal_type'] == 'buy']
        macd_sell_signals = macd_signals[macd_signals['signal_type'] == 'sell']
        
        print(f"\n🟢 買進信號詳情:")
        for _, signal in macd_buy_signals.iterrows():
            print(f"  序號{signal['trade_sequence']}: {signal['datetime']} @ {signal['close']:,.0f}")
        
        print(f"\n🔴 賣出信號詳情:")
        for _, signal in macd_sell_signals.iterrows():
            print(f"  序號{signal['trade_sequence']}: {signal['datetime']} @ {signal['close']:,.0f}")
        
        # 顯示交易對詳情
        if 'trade_pairs' in macd_stats and macd_stats['trade_pairs']:
            print(f"\n💰 交易對詳情:")
            total_profit = 0
            for i, pair in enumerate(macd_stats['trade_pairs'], 1):
                profit = pair['profit']
                total_profit += profit
                print(f"  交易對{i}: 買進 {pair['buy_time']} @ {pair['buy_price']:,.0f}")
                print(f"           賣出 {pair['sell_time']} @ {pair['sell_price']:,.0f}")
                print(f"           獲利: {profit:,.0f} TWD")
                print()
            
            print(f"📈 驗證總獲利: {total_profit:,.0f} TWD")
            
            # 計算勝率
            winning_trades = sum(1 for pair in macd_stats['trade_pairs'] if pair['profit'] > 0)
            win_rate = (winning_trades / len(macd_stats['trade_pairs'])) * 100
            print(f"🎯 勝率: {win_rate:.1f}% ({winning_trades}/{len(macd_stats['trade_pairs'])})")
        
        await service.close()
        
        # 與之前的比較結果對比
        print(f"\n📊 與比較腳本結果對比:")
        print(f"預期結果: 8對交易，總獲利 108,774 TWD")
        print(f"實際結果: {macd_stats['complete_pairs']}對交易，總獲利 {macd_stats.get('total_profit', 0):,.0f} TWD")
        
        actual_profit = macd_stats.get('total_profit', 0)
        expected_profit = 108774
        
        if abs(actual_profit - expected_profit) < 1:  # 允許小數點誤差
            print("✅ 獲利計算一致！")
        else:
            print(f"⚠️ 獲利計算不一致: 實際 {actual_profit} vs 預期 {expected_profit}")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函數"""
    asyncio.run(test_clean_macd())

if __name__ == "__main__":
    main()