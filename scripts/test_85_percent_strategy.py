#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試我們的85%獲利率策略
基於多時間框架交易信號系統
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
from datetime import datetime, timedelta
import logging

# 導入核心模組
from src.data.live_macd_service import LiveMACDService
from src.core.multi_timeframe_trading_signals import detect_multi_timeframe_trading_signals

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_strategy_performance(signals_dict, tracker):
    """計算策略績效"""
    print("\n" + "="*60)
    print("📊 85%獲利率策略績效分析")
    print("="*60)
    
    total_trades = 0
    total_profit = 0
    winning_trades = 0
    losing_trades = 0
    trade_details = []
    
    # 分析每個時間框架的交易
    for timeframe, signals_df in signals_dict.items():
        if signals_df.empty:
            continue
            
        print(f"\n🕐 {timeframe} 時間框架分析:")
        print(f"   總信號數: {len(signals_df)}")
        
        # 分離買賣信號
        buy_signals = signals_df[signals_df['signal_type'] == 'buy'].copy()
        sell_signals = signals_df[signals_df['signal_type'] == 'sell'].copy()
        
        print(f"   買入信號: {len(buy_signals)} 個")
        print(f"   賣出信號: {len(sell_signals)} 個")
        
        # 配對交易
        timeframe_trades = 0
        timeframe_profit = 0
        
        for _, buy_signal in buy_signals.iterrows():
            sequence = buy_signal['trade_sequence']
            matching_sells = sell_signals[sell_signals['trade_sequence'] == sequence]
            
            if not matching_sells.empty:
                sell_signal = matching_sells.iloc[0]
                
                buy_price = buy_signal['close']
                sell_price = sell_signal['close']
                profit = sell_price - buy_price
                profit_pct = (profit / buy_price) * 100
                
                # 計算持有時間
                buy_time = pd.to_datetime(buy_signal['datetime'])
                sell_time = pd.to_datetime(sell_signal['datetime'])
                hold_duration = sell_time - buy_time
                
                trade_info = {
                    'timeframe': timeframe,
                    'sequence': sequence,
                    'buy_time': buy_time,
                    'sell_time': sell_time,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'profit': profit,
                    'profit_pct': profit_pct,
                    'hold_duration': hold_duration,
                    'is_winning': profit > 0
                }
                
                trade_details.append(trade_info)
                timeframe_trades += 1
                timeframe_profit += profit
                
                if profit > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1
                
                print(f"   交易{sequence}: {buy_price:,.0f} -> {sell_price:,.0f} = {profit:+,.0f} TWD ({profit_pct:+.2f}%)")
        
        total_trades += timeframe_trades
        total_profit += timeframe_profit
        
        if timeframe_trades > 0:
            timeframe_win_rate = sum(1 for t in trade_details if t['timeframe'] == timeframe and t['is_winning']) / timeframe_trades * 100
            avg_profit = timeframe_profit / timeframe_trades
            print(f"   時間框架獲利: {timeframe_profit:+,.0f} TWD")
            print(f"   平均每筆: {avg_profit:+,.0f} TWD")
            print(f"   勝率: {timeframe_win_rate:.1f}%")
    
    # 整體績效統計
    print(f"\n🎯 整體策略績效:")
    print(f"   總交易數: {total_trades}")
    print(f"   獲利交易: {winning_trades}")
    print(f"   虧損交易: {losing_trades}")
    
    if total_trades > 0:
        win_rate = (winning_trades / total_trades) * 100
        avg_profit_per_trade = total_profit / total_trades
        
        print(f"   總獲利: {total_profit:+,.0f} TWD")
        print(f"   平均每筆獲利: {avg_profit_per_trade:+,.0f} TWD")
        print(f"   勝率: {win_rate:.1f}%")
        
        # 判斷是否達到85%目標
        if win_rate >= 85:
            print(f"   🎉 恭喜！達到85%獲利率目標！")
        elif win_rate >= 80:
            print(f"   🔥 接近85%目標，表現優秀！")
        elif win_rate >= 70:
            print(f"   👍 表現良好，還有提升空間")
        else:
            print(f"   ⚠️ 需要優化策略參數")
    
    # 詳細交易記錄
    if trade_details:
        print(f"\n📋 詳細交易記錄:")
        for trade in trade_details[-10:]:  # 顯示最近10筆交易
            status = "✅" if trade['is_winning'] else "❌"
            print(f"   {status} {trade['timeframe']} 交易{trade['sequence']}: "
                  f"{trade['buy_time'].strftime('%m-%d %H:%M')} -> "
                  f"{trade['sell_time'].strftime('%m-%d %H:%M')} | "
                  f"{trade['profit']:+,.0f} TWD ({trade['profit_pct']:+.2f}%)")
    
    return {
        'total_trades': total_trades,
        'total_profit': total_profit,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': (winning_trades / total_trades * 100) if total_trades > 0 else 0,
        'avg_profit_per_trade': (total_profit / total_trades) if total_trades > 0 else 0,
        'trade_details': trade_details
    }

async def test_85_percent_strategy():
    """測試85%獲利率策略"""
    print("🚀 開始測試85%獲利率策略...")
    print("策略特點:")
    print("  • 多時間框架確認 (1小時 + 30分鐘 + 15分鐘 + 5分鐘)")
    print("  • MACD金叉死叉主信號")
    print("  • 動態價格追蹤確認")
    print("  • 高信心度過濾")
    
    try:
        # 初始化服務
        service = LiveMACDService()
        
        # 獲取1小時數據作為主要信號源
        print("\n📊 獲取歷史數據...")
        hourly_klines = await service._fetch_klines("btctwd", "60", 500)
        if hourly_klines is None:
            print("❌ 無法獲取1小時數據")
            return
        
        hourly_df = service._calculate_macd(hourly_klines, 12, 26, 9)
        if hourly_df is None:
            print("❌ 無法計算1小時MACD")
            return
        
        print(f"✅ 獲取到 {len(hourly_df)} 個1小時數據點")
        
        # 獲取其他時間框架數據
        timeframe_dfs = {}
        
        # 30分鐘數據
        thirty_klines = await service._fetch_klines("btctwd", "30", 1000)
        if thirty_klines is not None:
            thirty_df = service._calculate_macd(thirty_klines, 12, 26, 9)
            if thirty_df is not None:
                timeframe_dfs['30m'] = thirty_df.tail(500).reset_index(drop=True)
                print(f"✅ 獲取到 {len(timeframe_dfs['30m'])} 個30分鐘數據點")
        
        # 15分鐘數據
        fifteen_klines = await service._fetch_klines("btctwd", "15", 1000)
        if fifteen_klines is not None:
            fifteen_df = service._calculate_macd(fifteen_klines, 12, 26, 9)
            if fifteen_df is not None:
                timeframe_dfs['15m'] = fifteen_df.tail(500).reset_index(drop=True)
                print(f"✅ 獲取到 {len(timeframe_dfs['15m'])} 個15分鐘數據點")
        
        # 5分鐘數據
        five_klines = await service._fetch_klines("btctwd", "5", 1000)
        if five_klines is not None:
            five_df = service._calculate_macd(five_klines, 12, 26, 9)
            if five_df is not None:
                timeframe_dfs['5m'] = five_df.tail(500).reset_index(drop=True)
                print(f"✅ 獲取到 {len(timeframe_dfs['5m'])} 個5分鐘數據點")
        
        await service.close()
        
        # 執行多時間框架信號檢測
        print("\n🎯 執行多時間框架信號檢測...")
        signals_dict, statistics, tracker = detect_multi_timeframe_trading_signals(
            hourly_df.tail(300).reset_index(drop=True),  # 使用最近300個1小時數據點
            timeframe_dfs
        )
        
        # 計算策略績效
        performance = calculate_strategy_performance(signals_dict, tracker)
        
        # 顯示策略狀態
        print(f"\n🔍 當前策略狀態:")
        if tracker:
            print(f"   持倉狀態: {'持倉中' if tracker.current_position == 1 else '空倉'}")
            print(f"   總買入次數: {tracker.buy_count}")
            print(f"   總賣出次數: {tracker.sell_count}")
            print(f"   完成交易對: {len(tracker.trade_pairs)}")
            
            if tracker.waiting_for_confirmation:
                print(f"   等待確認: {tracker.pending_signal_type} 信號")
                print(f"   基準價格: {tracker.pending_signal_price:,.0f} TWD")
        
        # 總結
        print(f"\n🎊 策略測試總結:")
        if performance['win_rate'] >= 85:
            print(f"   🏆 策略表現優異！勝率 {performance['win_rate']:.1f}% 達到85%目標")
        elif performance['win_rate'] >= 75:
            print(f"   🔥 策略表現良好！勝率 {performance['win_rate']:.1f}% 接近目標")
        else:
            print(f"   ⚠️ 策略需要調整，當前勝率 {performance['win_rate']:.1f}%")
        
        print(f"   總獲利: {performance['total_profit']:+,.0f} TWD")
        print(f"   交易次數: {performance['total_trades']}")
        
        return performance
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        logger.error(f"策略測試錯誤: {e}")
        return None

def main():
    """主函數"""
    print("🎯 AImax 85%獲利率策略測試")
    print("="*50)
    
    # 運行異步測試
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        performance = loop.run_until_complete(test_85_percent_strategy())
        
        if performance:
            print(f"\n✅ 測試完成！")
            if performance['win_rate'] >= 85:
                print(f"🎉 恭喜！我們的策略確實達到了85%的高獲利率！")
            else:
                print(f"📈 策略仍有優化空間，繼續改進中...")
        else:
            print(f"\n❌ 測試失敗，請檢查數據連接")
            
    except KeyboardInterrupt:
        print(f"\n⏹️ 用戶中斷測試")
    except Exception as e:
        print(f"\n❌ 測試異常: {e}")
    finally:
        loop.close()

if __name__ == '__main__':
    main()