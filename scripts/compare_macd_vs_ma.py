#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比較1小時MACD策略 vs 1小時MA策略的獲利
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import pandas as pd
from datetime import datetime
from src.data.live_macd_service import LiveMACDService
from src.core.improved_trading_signals import detect_improved_trading_signals
from src.core.multi_timeframe_trading_signals import detect_multi_timeframe_trading_signals

async def compare_strategies():
    """比較MACD vs MA策略"""
    print("🔍 開始比較1小時MACD策略 vs 1小時MA策略...")
    
    try:
        # 獲取數據
        service = LiveMACDService()
        
        # 獲取1小時數據 - 使用相同的數據量確保公平比較
        hourly_klines = await service._fetch_klines("btctwd", "60", 1000)
        if hourly_klines is None:
            print("❌ 無法獲取1小時數據")
            return
        
        # 計算MACD數據
        hourly_macd_df = service._calculate_macd(hourly_klines, 12, 26, 9)
        if hourly_macd_df is None:
            print("❌ 無法計算1小時MACD")
            return
        
        # 計算MA數據
        hourly_ma_df = service._calculate_ma(hourly_klines, 9, 25, 99)
        if hourly_ma_df is None:
            print("❌ 無法計算1小時MA")
            return
        
        # 使用相同的數據範圍
        data_range = 500
        macd_df = hourly_macd_df.tail(data_range).reset_index(drop=True)
        ma_df = hourly_ma_df.tail(data_range).reset_index(drop=True)
        
        print(f"📊 數據範圍: {data_range} 筆1小時數據")
        print(f"時間範圍: {macd_df.iloc[0]['datetime']} 至 {macd_df.iloc[-1]['datetime']}")
        print()
        
        # ==================== 1小時MACD策略分析 ====================
        print("🟦 1小時MACD策略分析:")
        macd_signals, macd_stats = detect_improved_trading_signals(macd_df)
        
        print(f"總數據點: {len(macd_signals)}")
        print(f"買進信號: {macd_stats['buy_count']} 個")
        print(f"賣出信號: {macd_stats['sell_count']} 個")
        print(f"完整交易對: {macd_stats['complete_pairs']} 對")
        
        if macd_stats['complete_pairs'] > 0:
            print(f"總獲利: {macd_stats['total_profit']:,.0f} TWD")
            print(f"平均獲利: {macd_stats['average_profit']:,.0f} TWD")
            print(f"平均持倉時間: {macd_stats['average_hold_time']:.1f} 小時")
        
        # 顯示MACD交易詳情
        macd_buy_signals = macd_signals[macd_signals['signal_type'] == 'buy']
        macd_sell_signals = macd_signals[macd_signals['signal_type'] == 'sell']
        
        print(f"\n🟢 MACD買進信號詳情:")
        for _, signal in macd_buy_signals.iterrows():
            print(f"  時間: {signal['datetime']}, 價格: {signal['close']:,.0f}, 序號: {signal['trade_sequence']}")
        
        print(f"\n🔴 MACD賣出信號詳情:")
        for _, signal in macd_sell_signals.iterrows():
            print(f"  時間: {signal['datetime']}, 價格: {signal['close']:,.0f}, 序號: {signal['trade_sequence']}")
        
        print("\n" + "="*60)
        
        # ==================== 1小時MA策略分析 ====================
        print("🟨 1小時MA策略分析:")
        
        # 準備時間框架數據
        timeframe_dfs = {
            '30m': ma_df  # 使用1小時MA數據
        }
        
        # 檢測MA信號
        ma_signals_dict, ma_statistics, ma_tracker = detect_multi_timeframe_trading_signals(
            macd_df,  # 需要1小時MACD數據作為基準
            timeframe_dfs
        )
        
        if '30m' in ma_signals_dict and not ma_signals_dict['30m'].empty:
            ma_signals = ma_signals_dict['30m']
            
            # 提取買賣信號
            ma_buy_signals = ma_signals[ma_signals['signal_type'] == 'buy']
            ma_sell_signals = ma_signals[ma_signals['signal_type'] == 'sell']
            
            print(f"總數據點: {len(ma_signals)}")
            print(f"買進信號: {len(ma_buy_signals)} 個")
            print(f"賣出信號: {len(ma_sell_signals)} 個")
            
            # 計算MA策略獲利
            ma_total_profit = 0
            ma_trade_count = 0
            ma_trades = []
            
            # 按序號配對買賣信號
            for _, buy_signal in ma_buy_signals.iterrows():
                buy_seq = buy_signal['trade_sequence']
                matching_sells = ma_sell_signals[ma_sell_signals['trade_sequence'] == buy_seq]
                
                if not matching_sells.empty:
                    sell_signal = matching_sells.iloc[0]
                    profit = sell_signal['close'] - buy_signal['close']
                    ma_total_profit += profit
                    ma_trade_count += 1
                    
                    ma_trades.append({
                        'sequence': buy_seq,
                        'buy_time': buy_signal['datetime'],
                        'sell_time': sell_signal['datetime'],
                        'buy_price': buy_signal['close'],
                        'sell_price': sell_signal['close'],
                        'profit': profit
                    })
            
            print(f"完整交易對: {ma_trade_count} 對")
            if ma_trade_count > 0:
                print(f"總獲利: {ma_total_profit:,.0f} TWD")
                print(f"平均獲利: {ma_total_profit/ma_trade_count:,.0f} TWD")
            
            print(f"\n🟢 MA買進信號詳情:")
            for _, signal in ma_buy_signals.iterrows():
                print(f"  時間: {signal['datetime']}, 價格: {signal['close']:,.0f}, 序號: {signal['trade_sequence']}")
            
            print(f"\n🔴 MA賣出信號詳情:")
            for _, signal in ma_sell_signals.iterrows():
                print(f"  時間: {signal['datetime']}, 價格: {signal['close']:,.0f}, 序號: {signal['trade_sequence']}")
        
        print("\n" + "="*60)
        
        # ==================== 策略比較 ====================
        print("📊 策略比較總結:")
        
        macd_profit = macd_stats.get('total_profit', 0)
        macd_trades = macd_stats.get('complete_pairs', 0)
        
        print(f"\n🟦 1小時MACD策略:")
        print(f"  完整交易對: {macd_trades} 對")
        print(f"  總獲利: {macd_profit:,.0f} TWD")
        if macd_trades > 0:
            print(f"  平均每筆: {macd_profit/macd_trades:,.0f} TWD")
        
        print(f"\n🟨 1小時MA策略:")
        print(f"  完整交易對: {ma_trade_count} 對")
        print(f"  總獲利: {ma_total_profit:,.0f} TWD")
        if ma_trade_count > 0:
            print(f"  平均每筆: {ma_total_profit/ma_trade_count:,.0f} TWD")
        
        print(f"\n💰 獲利差異:")
        profit_diff = ma_total_profit - macd_profit
        if profit_diff > 0:
            print(f"  MA策略比MACD策略多賺: {profit_diff:,.0f} TWD")
        elif profit_diff < 0:
            print(f"  MACD策略比MA策略多賺: {abs(profit_diff):,.0f} TWD")
        else:
            print(f"  兩策略獲利相同")
        
        print(f"\n📈 交易頻率:")
        print(f"  MACD策略: {macd_trades} 筆交易")
        print(f"  MA策略: {ma_trade_count} 筆交易")
        
        if macd_trades > 0 and ma_trade_count > 0:
            print(f"\n🎯 策略效率:")
            macd_efficiency = macd_profit / macd_trades if macd_trades > 0 else 0
            ma_efficiency = ma_total_profit / ma_trade_count if ma_trade_count > 0 else 0
            
            if ma_efficiency > macd_efficiency:
                print(f"  MA策略效率更高 (每筆平均獲利: {ma_efficiency:,.0f} vs {macd_efficiency:,.0f})")
            elif macd_efficiency > ma_efficiency:
                print(f"  MACD策略效率更高 (每筆平均獲利: {macd_efficiency:,.0f} vs {ma_efficiency:,.0f})")
            else:
                print(f"  兩策略效率相同")
        
        await service.close()
        
    except Exception as e:
        print(f"❌ 比較分析失敗: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函數"""
    asyncio.run(compare_strategies())

if __name__ == "__main__":
    main()