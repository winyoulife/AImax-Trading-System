#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試移動停利停損策略 vs 原始MACD策略
"""

import sys
import os
import numpy as np
from datetime import datetime

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.data.data_fetcher import DataFetcher
from src.core.improved_max_macd_calculator import ImprovedMaxMACDCalculator
from src.core.improved_trading_signals import SignalDetectionEngine
from src.core.trailing_stop_trading_signals import TrailingStopTradingSignals

def compare_strategies():
    """比較兩種策略的表現"""
    print("📊 移動停利停損策略 vs 原始MACD策略比較")
    print("=" * 60)
    
    # 獲取數據
    print("📡 獲取歷史數據...")
    data_fetcher = DataFetcher()
    df = data_fetcher.fetch_data('BTCUSDT', '1h', 2000)
    
    if df is None or df.empty:
        print("❌ 無法獲取數據")
        return
    
    print(f"✅ 獲取了 {len(df)} 條數據")
    
    # 計算MACD
    print("🔢 計算MACD指標...")
    macd_calculator = ImprovedMaxMACDCalculator()
    prices = df['close'].tolist()
    timestamps = df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
    
    macd_line, signal_line, hist = macd_calculator.calculate_macd(prices, timestamps)
    
    # 創建包含MACD數據的DataFrame
    macd_df = df.copy()
    macd_df['datetime'] = df['timestamp']
    
    # 填充MACD數據
    macd_len = len(macd_line)
    total_len = len(df)
    
    macd_df['macd'] = [np.nan] * (total_len - macd_len) + macd_line
    macd_df['macd_signal'] = [np.nan] * (total_len - macd_len) + signal_line
    macd_df['macd_hist'] = [np.nan] * (total_len - macd_len) + hist
    
    # 移除NaN行
    macd_df = macd_df.dropna().reset_index(drop=True)
    
    print(f"📊 有效數據: {len(macd_df)} 條")
    
    # 測試原始MACD策略
    print("\n🔵 測試原始MACD策略...")
    original_engine = SignalDetectionEngine()
    original_results = original_engine.detect_signals(macd_df)
    original_stats = original_engine.position_tracker.get_status()
    
    # 計算原始策略統計
    original_trades = []
    position = None
    
    for idx, row in original_results.iterrows():
        if row['signal_type'] == 'buy' and position is None:
            position = {
                'buy_time': row['datetime'],
                'buy_price': row['close'],
            }
        elif row['signal_type'] == 'sell' and position is not None:
            trade = {
                'buy_time': position['buy_time'],
                'sell_time': row['datetime'],
                'buy_price': position['buy_price'],
                'sell_price': row['close'],
                'profit': row['close'] - position['buy_price'],
                'profit_pct': ((row['close'] - position['buy_price']) / position['buy_price']) * 100,
                'sell_reason': 'MACD'
            }
            original_trades.append(trade)
            position = None
    
    # 測試移動停損策略
    print("🟢 測試移動停利停損策略...")
    trailing_engine = TrailingStopTradingSignals(
        stop_loss_pct=0.05,      # 5% 停損
        profit_trigger_pct=0.03, # 3% 開始移動停損
        trailing_pct=0.02        # 2% 移動幅度
    )
    trailing_results = trailing_engine.detect_signals(macd_df)
    trailing_stats = trailing_engine.get_statistics()
    
    # 顯示比較結果
    print("\n" + "=" * 60)
    print("📊 策略比較結果")
    print("=" * 60)
    
    # 原始MACD策略統計
    if original_trades:
        original_total_profit = sum(trade['profit'] for trade in original_trades)
        original_winning = [t for t in original_trades if t['profit'] > 0]
        original_win_rate = (len(original_winning) / len(original_trades)) * 100
        original_avg_profit = original_total_profit / len(original_trades)
    else:
        original_total_profit = 0
        original_win_rate = 0
        original_avg_profit = 0
    
    print(f"\n🔵 原始MACD策略:")
    print(f"   📈 總獲利: ${original_total_profit:,.0f}")
    print(f"   🎯 交易對: {len(original_trades)} 對")
    print(f"   📊 勝率: {original_win_rate:.1f}%")
    print(f"   💰 平均獲利: ${original_avg_profit:,.0f}")
    print(f"   🔴 賣出方式: 100% MACD死叉")
    
    print(f"\n🟢 移動停利停損策略:")
    print(f"   📈 總獲利: ${trailing_stats['total_profit']:,.0f}")
    print(f"   🎯 交易對: {trailing_stats['complete_pairs']} 對")
    print(f"   📊 勝率: {trailing_stats['win_rate']:.1f}%")
    print(f"   💰 平均獲利: ${trailing_stats['average_profit']:,.0f}")
    print(f"   🛑 停損賣出: {trailing_stats['stop_loss_count']} 次")
    print(f"   🔴 MACD賣出: {trailing_stats['macd_sell_count']} 次")
    
    # 計算改進幅度
    if original_total_profit != 0:
        profit_improvement = ((trailing_stats['total_profit'] - original_total_profit) / abs(original_total_profit)) * 100
        win_rate_improvement = trailing_stats['win_rate'] - original_win_rate
        
        print(f"\n📈 改進幅度:")
        print(f"   💰 獲利改進: {profit_improvement:+.1f}%")
        print(f"   🎯 勝率改進: {win_rate_improvement:+.1f}%")
        
        if profit_improvement > 0:
            print(f"   ✅ 移動停損策略表現更好！")
        else:
            print(f"   ⚠️ 原始策略表現更好")
    
    # 顯示最近的交易對比
    print(f"\n📋 最近5筆交易對比:")
    print("   🔵 原始策略 vs 🟢 移動停損策略")
    
    for i in range(min(5, len(original_trades), len(trailing_stats.get('trade_pairs', [])))):
        if i < len(original_trades):
            orig_trade = original_trades[-(i+1)]
            orig_profit = orig_trade['profit']
            orig_pct = orig_trade['profit_pct']
        else:
            orig_profit = 0
            orig_pct = 0
        
        if i < len(trailing_stats.get('trade_pairs', [])):
            trail_trade = trailing_stats['trade_pairs'][-(i+1)]
            trail_profit = trail_trade['profit']
            trail_pct = trail_trade['profit_pct']
            trail_reason = trail_trade['sell_reason']
        else:
            trail_profit = 0
            trail_pct = 0
            trail_reason = ""
        
        print(f"   第{len(original_trades)-i}筆: 🔵${orig_profit:+,.0f}({orig_pct:+.1f}%) vs 🟢${trail_profit:+,.0f}({trail_pct:+.1f}%)[{trail_reason}]")
    
    print(f"\n⏰ 分析完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return {
        'original': {
            'total_profit': original_total_profit,
            'trades': len(original_trades),
            'win_rate': original_win_rate
        },
        'trailing': trailing_stats
    }

if __name__ == "__main__":
    try:
        results = compare_strategies()
    except Exception as e:
        print(f"❌ 分析過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()