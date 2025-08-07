#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試智能平衡成交量增強MACD策略
目標：在保持高勝率的同時增加交易機會
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# 導入相關模組
from src.data.data_fetcher import DataFetcher
from src.core.volume_enhanced_macd_signals import VolumeEnhancedMACDSignals
from src.core.advanced_volume_macd_signals import AdvancedVolumeEnhancedMACDSignals
from src.core.ultra_advanced_volume_macd_signals import UltraAdvancedVolumeEnhancedMACDSignals
from src.core.smart_balanced_volume_macd_signals import SmartBalancedVolumeEnhancedMACDSignals
from src.core.smart_balanced_volume_macd_signals import SmartBalancedVolumeEnhancedMACDSignals

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_trade_performance(signals_df: pd.DataFrame) -> dict:
    """計算交易績效"""
    if signals_df.empty:
        return {
            'total_trades': 0,
            'total_profit': 0,
            'win_rate': 0,
            'avg_profit': 0,
            'avg_signal_strength': 0,
            'trades': []
        }
    
    # 過濾出實際交易信號
    buy_signals = signals_df[signals_df['signal_type'] == 'buy'].copy()
    sell_signals = signals_df[signals_df['signal_type'] == 'sell'].copy()
    
    trades = []
    total_profit = 0
    wins = 0
    
    # 配對買賣信號
    for _, buy_signal in buy_signals.iterrows():
        trade_seq = buy_signal['trade_sequence']
        
        # 找到對應的賣出信號
        matching_sell = sell_signals[sell_signals['trade_sequence'] == trade_seq]
        
        if not matching_sell.empty:
            sell_signal = matching_sell.iloc[0]
            
            # 計算獲利
            buy_price = buy_signal['close']
            sell_price = sell_signal['close']
            profit = sell_price - buy_price
            profit_pct = (profit / buy_price) * 100
            
            total_profit += profit
            if profit > 0:
                wins += 1
            
            trade_info = {
                'sequence': trade_seq,
                'buy_time': buy_signal['datetime'],
                'sell_time': sell_signal['datetime'],
                'buy_price': buy_price,
                'sell_price': sell_price,
                'profit': profit,
                'profit_pct': profit_pct,
                'buy_strength': buy_signal['signal_strength'],
                'sell_strength': sell_signal['signal_strength']
            }
            trades.append(trade_info)
    
    total_trades = len(trades)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    avg_profit = total_profit / total_trades if total_trades > 0 else 0
    
    # 計算平均信號強度
    all_signals = signals_df[signals_df['signal_type'].isin(['buy', 'sell'])]
    avg_signal_strength = all_signals['signal_strength'].mean() if not all_signals.empty else 0
    
    return {
        'total_trades': total_trades,
        'total_profit': total_profit,
        'win_rate': win_rate,
        'avg_profit': avg_profit,
        'avg_signal_strength': avg_signal_strength,
        'trades': trades
    }

def main():
    """主函數"""
    print("🚀 測試終極優化成交量增強MACD策略")
    print("目標：達到90%+勝率並增加交易機會")
    print("=" * 50)
    
    # 初始化數據獲取器
    data_fetcher = DataFetcher()
    
    # 獲取BTC數據
    print("📊 獲取BTC歷史數據...")
    try:
        df = data_fetcher.fetch_data('BTCTWD', limit=2000)
        if df is None or df.empty:
            print("❌ 無法獲取數據")
            return
        
        print(f"✅ 成功獲取 {len(df)} 筆BTC數據")
        print(f"   時間範圍: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        print()
        
    except Exception as e:
        print(f"❌ 數據獲取失敗: {e}")
        return
    
    # 測試各種策略
    strategies = [
        ("基礎版本", VolumeEnhancedMACDSignals(), "detect_volume_enhanced_signals"),
        ("進階版本", AdvancedVolumeEnhancedMACDSignals(), "detect_advanced_signals"),
        ("超級版本", UltraAdvancedVolumeEnhancedMACDSignals(), "detect_ultra_advanced_signals"),
        ("智能平衡版本", SmartBalancedVolumeEnhancedMACDSignals(), "detect_smart_balanced_signals"),
        ("終極優化版本", SmartBalancedVolumeEnhancedMACDSignals(), "detect_ultimate_optimized_signals")
    ]
    
    results = {}
    
    for strategy_name, detector, method_name in strategies:
        print(f"🔵 測試{strategy_name}...")
        try:
            # 執行策略
            method = getattr(detector, method_name)
            signals_df = method(df)
            
            # 計算績效
            performance = calculate_trade_performance(signals_df)
            results[strategy_name] = performance
            
            # 顯示結果
            print(f"   交易次數: {performance['total_trades']}")
            print(f"   總獲利: {performance['total_profit']:,.0f} TWD")
            print(f"   勝率: {performance['win_rate']:.1f}%")
            print(f"   平均信號強度: {performance['avg_signal_strength']:.1f}/100")
            
            # 計算拒絕信號數量
            if not signals_df.empty:
                rejected_signals = len(signals_df[signals_df['signal_type'].str.contains('rejected')])
                print(f"   拒絕信號: {rejected_signals}")
            
            print()
            
        except Exception as e:
            print(f"❌ {strategy_name}測試失敗: {e}")
            results[strategy_name] = {
                'total_trades': 0,
                'total_profit': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'avg_signal_strength': 0,
                'trades': []
            }
            print()
    
    # 顯示策略比較
    print("📊 策略進化比較")
    print("=" * 50)
    print(f"{'策略':<12} {'交易次數':<8} {'總獲利':<12} {'勝率':<8} {'平均獲利':<12} {'信號強度'}")
    print("-" * 70)
    
    for strategy_name, perf in results.items():
        print(f"{strategy_name:<12} {perf['total_trades']:<8} {perf['total_profit']:>10,.0f} {perf['win_rate']:>6.1f}% {perf['avg_profit']:>10,.0f} {perf['avg_signal_strength']:>8.1f}")
    
    print()
    
    # 顯示勝率進化
    if len(results) >= 2:
        print("🎯 勝率進化:")
        strategy_names = list(results.keys())
        for i in range(1, len(strategy_names)):
            prev_name = strategy_names[i-1]
            curr_name = strategy_names[i]
            prev_rate = results[prev_name]['win_rate']
            curr_rate = results[curr_name]['win_rate']
            change = curr_rate - prev_rate
            print(f"   {prev_name} → {curr_name}: {prev_rate:.1f}% → {curr_rate:.1f}% ({change:+.1f}%)")
        
        # 總體提升
        first_rate = results[strategy_names[0]]['win_rate']
        last_rate = results[strategy_names[-1]]['win_rate']
        total_change = last_rate - first_rate
        print(f"   總體提升: {first_rate:.1f}% → {last_rate:.1f}% ({total_change:+.1f}%)")
        print()
    
    # 顯示最佳策略的詳細交易記錄
    best_strategy = max(results.keys(), key=lambda k: results[k]['win_rate'])
    best_performance = results[best_strategy]
    
    if best_performance['trades']:
        print(f"📋 {best_strategy}交易明細:")
        for i, trade in enumerate(best_performance['trades'], 1):
            profit_sign = "+" if trade['profit'] > 0 else ""
            print(f"   {i}. {trade['buy_time'].strftime('%m/%d %H:%M')} 買入 {trade['buy_price']:,.0f} → "
                  f"{trade['sell_time'].strftime('%m/%d %H:%M')} 賣出 {trade['sell_price']:,.0f} = "
                  f"{profit_sign}{trade['profit']:,.0f} TWD ({profit_sign}{trade['profit_pct']:.1f}%)")
            print(f"      信號強度: 買{trade['buy_strength']:.0f} 賣{trade['sell_strength']:.0f}")
        
        # 驗證勝率
        wins = sum(1 for trade in best_performance['trades'] if trade['profit'] > 0)
        actual_win_rate = wins / len(best_performance['trades']) * 100
        print(f"   實際勝率驗證: {wins}/{len(best_performance['trades'])} = {actual_win_rate:.1f}%")
        print()
    
    # 結論
    print("🎉 結論:")
    if best_performance['win_rate'] >= 80:
        print(f"   🏆 成功達成80%+勝率目標！")
        print(f"   🌟 {best_strategy}勝率: {best_performance['win_rate']:.1f}%")
    elif best_performance['win_rate'] >= 75:
        print(f"   ✅ {best_strategy}成功提升了勝率！")
        print(f"   📈 距離80%目標還差 {80 - best_performance['win_rate']:.1f}%")
    else:
        print(f"   ⚠️  {best_strategy}需要進一步調整")
        print(f"   💡 可能需要優化參數或增加更多條件")
    
    print("\n✅ 測試完成！")

if __name__ == "__main__":
    main()