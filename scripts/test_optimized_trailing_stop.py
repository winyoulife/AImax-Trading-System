#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試優化的移動停利停損策略
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

def test_multiple_strategies():
    """測試多種移動停損參數組合"""
    print("🔬 優化移動停利停損策略測試")
    print("=" * 60)
    
    # 獲取數據
    print("📡 獲取歷史數據...")
    data_fetcher = DataFetcher()
    df = data_fetcher.fetch_data('BTCUSDT', '1h', 2000)
    
    if df is None or df.empty:
        print("❌ 無法獲取數據")
        return
    
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
    
    # 測試原始策略作為基準
    print("\n🔵 基準：原始MACD策略")
    original_engine = SignalDetectionEngine()
    original_results = original_engine.detect_signals(macd_df)
    
    # 計算原始策略統計
    original_trades = []
    position = None
    
    for idx, row in original_results.iterrows():
        if row['signal_type'] == 'buy' and position is None:
            position = {'buy_price': row['close']}
        elif row['signal_type'] == 'sell' and position is not None:
            profit = row['close'] - position['buy_price']
            original_trades.append({'profit': profit})
            position = None
    
    original_total = sum(t['profit'] for t in original_trades)
    original_win_rate = (len([t for t in original_trades if t['profit'] > 0]) / len(original_trades)) * 100 if original_trades else 0
    
    print(f"   📈 總獲利: ${original_total:,.0f}")
    print(f"   🎯 交易對: {len(original_trades)} 對")
    print(f"   📊 勝率: {original_win_rate:.1f}%")
    
    # 測試多種移動停損參數
    strategies = [
        {"name": "保守型", "stop_loss": 0.03, "profit_trigger": 0.02, "trailing": 0.015, "desc": "3%停損,2%啟動,1.5%移動"},
        {"name": "平衡型", "stop_loss": 0.025, "profit_trigger": 0.015, "trailing": 0.01, "desc": "2.5%停損,1.5%啟動,1%移動"},
        {"name": "激進型", "stop_loss": 0.02, "profit_trigger": 0.01, "trailing": 0.008, "desc": "2%停損,1%啟動,0.8%移動"},
        {"name": "超激進", "stop_loss": 0.015, "profit_trigger": 0.008, "trailing": 0.006, "desc": "1.5%停損,0.8%啟動,0.6%移動"},
    ]
    
    best_strategy = None
    best_profit = original_total
    
    print(f"\n🧪 測試不同移動停損策略:")
    print("-" * 60)
    
    for strategy in strategies:
        print(f"\n🟢 {strategy['name']} ({strategy['desc']})")
        
        trailing_engine = TrailingStopTradingSignals(
            stop_loss_pct=strategy['stop_loss'],
            profit_trigger_pct=strategy['profit_trigger'],
            trailing_pct=strategy['trailing']
        )
        
        trailing_results = trailing_engine.detect_signals(macd_df)
        stats = trailing_engine.get_statistics()
        
        print(f"   📈 總獲利: ${stats['total_profit']:,.0f}")
        print(f"   🎯 交易對: {stats['complete_pairs']} 對")
        print(f"   📊 勝率: {stats['win_rate']:.1f}%")
        print(f"   🛑 停損賣出: {stats['stop_loss_count']} 次")
        print(f"   🔴 MACD賣出: {stats['macd_sell_count']} 次")
        
        # 計算改進幅度
        if original_total != 0:
            improvement = ((stats['total_profit'] - original_total) / abs(original_total)) * 100
            print(f"   📈 vs基準: {improvement:+.1f}%")
            
            if stats['total_profit'] > best_profit:
                best_strategy = strategy.copy()
                best_strategy['stats'] = stats
                best_profit = stats['total_profit']
    
    # 顯示最佳策略
    print(f"\n" + "=" * 60)
    print("🏆 最佳策略結果")
    print("=" * 60)
    
    if best_strategy and best_profit > original_total:
        print(f"🥇 最佳策略: {best_strategy['name']}")
        print(f"📋 參數: {best_strategy['desc']}")
        print(f"📈 總獲利: ${best_strategy['stats']['total_profit']:,.0f}")
        print(f"🎯 勝率: {best_strategy['stats']['win_rate']:.1f}%")
        print(f"🛑 停損保護: {best_strategy['stats']['stop_loss_count']} 次")
        
        improvement = ((best_strategy['stats']['total_profit'] - original_total) / abs(original_total)) * 100
        print(f"🚀 改進幅度: +{improvement:.1f}%")
        
        print(f"\n💡 建議使用參數:")
        print(f"   • 停損比例: {best_strategy['stop_loss']*100:.1f}%")
        print(f"   • 啟動獲利: {best_strategy['profit_trigger']*100:.1f}%")
        print(f"   • 移動幅度: {best_strategy['trailing']*100:.1f}%")
        
    else:
        print("🤔 所有移動停損策略都沒有超越原始MACD策略")
        print("💡 建議:")
        print("   • 原始MACD策略已經相當優秀")
        print("   • 可以考慮其他優化方向")
        print("   • 或者在不同市場條件下測試")
    
    print(f"\n⏰ 測試完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        test_multiple_strategies()
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()