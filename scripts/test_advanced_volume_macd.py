#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試進階成交量增強MACD策略
目標：將勝率從66.7%提升到75%+
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import logging

# 導入模組
from src.data.data_fetcher import DataFetcher
from src.core.volume_enhanced_macd_signals import VolumeEnhancedMACDSignals
from src.core.advanced_volume_macd_signals import AdvancedVolumeEnhancedMACDSignals

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_performance(signals_df: pd.DataFrame) -> Dict:
    """計算策略表現"""
    if signals_df.empty:
        return {
            'total_trades': 0,
            'total_profit': 0,
            'success_rate': 0,
            'avg_profit': 0,
            'trade_pairs': [],
            'confirmed_signals': 0,
            'rejected_signals': 0,
            'avg_signal_strength': 0
        }
    
    # 分析信號類型
    buy_signals = signals_df[signals_df['signal_type'] == 'buy'].copy()
    sell_signals = signals_df[signals_df['signal_type'] == 'sell'].copy()
    buy_rejected = signals_df[signals_df['signal_type'] == 'buy_rejected']
    sell_rejected = signals_df[signals_df['signal_type'] == 'sell_rejected']
    
    confirmed_signals = len(buy_signals) + len(sell_signals)
    rejected_signals = len(buy_rejected) + len(sell_rejected)
    
    # 計算交易對
    trade_pairs = []
    total_profit = 0
    
    for _, buy_signal in buy_signals.iterrows():
        matching_sells = sell_signals[
            (sell_signals['trade_sequence'] == buy_signal['trade_sequence']) &
            (sell_signals['datetime'] > buy_signal['datetime'])
        ]
        
        if not matching_sells.empty:
            sell_signal = matching_sells.iloc[0]
            profit = sell_signal['close'] - buy_signal['close']
            
            trade_pair = {
                'buy_time': buy_signal['datetime'],
                'sell_time': sell_signal['datetime'],
                'buy_price': buy_signal['close'],
                'sell_price': sell_signal['close'],
                'profit': profit,
                'profit_pct': (profit / buy_signal['close']) * 100,
                'buy_strength': buy_signal.get('signal_strength', 0),
                'sell_strength': sell_signal.get('signal_strength', 0)
            }
            trade_pairs.append(trade_pair)
            total_profit += profit
    
    # 計算統計數據
    success_count = len([tp for tp in trade_pairs if tp['profit'] > 0])
    success_rate = (success_count / len(trade_pairs)) * 100 if trade_pairs else 0
    avg_profit = total_profit / len(trade_pairs) if trade_pairs else 0
    
    # 計算平均信號強度
    all_confirmed = pd.concat([buy_signals, sell_signals]) if not buy_signals.empty and not sell_signals.empty else pd.DataFrame()
    avg_signal_strength = all_confirmed['signal_strength'].mean() if not all_confirmed.empty else 0
    
    return {
        'total_trades': len(trade_pairs),
        'total_profit': total_profit,
        'success_rate': success_rate,
        'avg_profit': avg_profit,
        'trade_pairs': trade_pairs,
        'confirmed_signals': confirmed_signals,
        'rejected_signals': rejected_signals,
        'avg_signal_strength': avg_signal_strength if not pd.isna(avg_signal_strength) else 0
    }

def main():
    """主函數"""
    print("🚀 測試進階成交量增強MACD策略")
    print("目標：將勝率從66.7%提升到75%+")
    print("=" * 60)
    
    # 獲取數據
    data_fetcher = DataFetcher()
    df = data_fetcher.fetch_data('BTCTWD', '1h', limit=2000)
    
    if df is None or df.empty:
        print("❌ 無法獲取BTC數據")
        return
    
    print(f"✅ 成功獲取 {len(df)} 筆BTC數據")
    print(f"   時間範圍: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
    
    # 測試基礎成交量增強策略
    print("\n🔵 測試基礎成交量增強策略...")
    basic_enhanced = VolumeEnhancedMACDSignals()
    basic_signals = basic_enhanced.detect_enhanced_signals(df)
    basic_performance = calculate_performance(basic_signals)
    
    print(f"   交易次數: {basic_performance['total_trades']}")
    print(f"   總獲利: {basic_performance['total_profit']:,.0f} TWD")
    print(f"   勝率: {basic_performance['success_rate']:.1f}%")
    print(f"   平均信號強度: {basic_performance['avg_signal_strength']:.1f}/100")
    print(f"   拒絕信號: {basic_performance['rejected_signals']}")
    
    # 測試進階成交量增強策略
    print("\n🟢 測試進階成交量增強策略...")
    advanced_enhanced = AdvancedVolumeEnhancedMACDSignals()
    advanced_signals = advanced_enhanced.detect_advanced_signals(df)
    advanced_performance = calculate_performance(advanced_signals)
    
    print(f"   交易次數: {advanced_performance['total_trades']}")
    print(f"   總獲利: {advanced_performance['total_profit']:,.0f} TWD")
    print(f"   勝率: {advanced_performance['success_rate']:.1f}%")
    print(f"   平均信號強度: {advanced_performance['avg_signal_strength']:.1f}/100")
    print(f"   拒絕信號: {advanced_performance['rejected_signals']}")
    
    # 比較結果
    print("\n" + "=" * 60)
    print("📊 策略比較結果")
    print("=" * 60)
    
    print(f"💰 獲利比較:")
    profit_improvement = advanced_performance['total_profit'] - basic_performance['total_profit']
    print(f"   基礎版本: {basic_performance['total_profit']:>10,.0f} TWD")
    print(f"   進階版本: {advanced_performance['total_profit']:>10,.0f} TWD")
    print(f"   改善幅度: {profit_improvement:>+10,.0f} TWD")
    
    print(f"\n🎯 勝率比較:")
    rate_improvement = advanced_performance['success_rate'] - basic_performance['success_rate']
    print(f"   基礎版本: {basic_performance['success_rate']:>10.1f}%")
    print(f"   進階版本: {advanced_performance['success_rate']:>10.1f}%")
    print(f"   勝率改善: {rate_improvement:>+10.1f}%")
    
    print(f"\n📈 交易品質比較:")
    print(f"   基礎版本交易: {basic_performance['total_trades']:>10} 次")
    print(f"   進階版本交易: {advanced_performance['total_trades']:>10} 次")
    print(f"   基礎版本強度: {basic_performance['avg_signal_strength']:>10.1f}/100")
    print(f"   進階版本強度: {advanced_performance['avg_signal_strength']:>10.1f}/100")
    
    # 顯示交易明細
    if advanced_performance['trade_pairs']:
        print(f"\n📋 進階版本交易明細:")
        for i, trade in enumerate(advanced_performance['trade_pairs'], 1):
            buy_time = trade['buy_time'].strftime('%m/%d %H:%M')
            sell_time = trade['sell_time'].strftime('%m/%d %H:%M')
            profit_color = "+" if trade['profit'] > 0 else ""
            
            print(f"   {i}. {buy_time} 買入 {trade['buy_price']:,.0f} → "
                  f"{sell_time} 賣出 {trade['sell_price']:,.0f} "
                  f"= {profit_color}{trade['profit']:,.0f} TWD ({trade['profit_pct']:+.1f}%)")
            print(f"      信號強度: 買{trade['buy_strength']:.0f} 賣{trade['sell_strength']:.0f}")
    
    # 結論
    print(f"\n🎉 結論:")
    if advanced_performance['success_rate'] > basic_performance['success_rate']:
        print("   ✅ 進階版本成功提升了勝率！")
        if advanced_performance['success_rate'] >= 75:
            print("   🏆 達成75%+勝率目標！")
        else:
            print(f"   📈 距離75%目標還差 {75 - advanced_performance['success_rate']:.1f}%")
    else:
        print("   ⚠️  進階版本需要進一步調整")
    
    print("\n✅ 測試完成！")

if __name__ == "__main__":
    main()