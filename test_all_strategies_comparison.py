#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
所有策略對比測試
比較進階策略(75%目標)、最終策略(85%目標)和原始策略的表現
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from src.core.final_85_percent_strategy import Final85PercentStrategy
from src.core.advanced_volume_macd_signals import AdvancedVolumeEnhancedMACDSignals
from src.core.clean_ultimate_signals import UltimateOptimizedVolumeEnhancedMACDSignals
from src.data.simple_data_fetcher import DataFetcher

# 設置日誌
logging.basicConfig(level=logging.WARNING)  # 減少日誌輸出
logger = logging.getLogger(__name__)

def calculate_performance(signals_df: pd.DataFrame, strategy_name: str) -> dict:
    """計算策略績效"""
    if signals_df.empty:
        return {
            'strategy': strategy_name,
            'total_trades': 0,
            'win_rate': 0,
            'total_profit': 0,
            'avg_signal_strength': 0
        }
    
    trades = []
    buy_price = None
    buy_sequence = None
    
    for _, signal in signals_df.iterrows():
        if signal['signal_type'] == 'buy':
            buy_price = signal['close']
            buy_sequence = signal['trade_sequence']
            
        elif signal['signal_type'] == 'sell' and buy_price is not None:
            sell_price = signal['close']
            profit = sell_price - buy_price
            
            trades.append({
                'profit': profit,
                'profit_pct': (profit / buy_price) * 100
            })
            
            buy_price = None
            buy_sequence = None
    
    if not trades:
        return {
            'strategy': strategy_name,
            'total_trades': 0,
            'win_rate': 0,
            'total_profit': 0,
            'avg_signal_strength': signals_df['signal_strength'].mean() if 'signal_strength' in signals_df.columns else 0
        }
    
    winning_trades = [t for t in trades if t['profit'] > 0]
    total_profit = sum(t['profit'] for t in trades)
    
    return {
        'strategy': strategy_name,
        'total_trades': len(trades),
        'win_rate': len(winning_trades) / len(trades) * 100,
        'total_profit': total_profit,
        'avg_profit_per_trade': total_profit / len(trades),
        'avg_signal_strength': signals_df['signal_strength'].mean() if 'signal_strength' in signals_df.columns else 0,
        'trades': trades
    }

def main():
    """主測試函數"""
    print("🚀 開始所有策略對比測試...")
    print("=" * 80)
    
    try:
        # 獲取測試數據
        data_fetcher = DataFetcher()
        print("📊 生成測試數據...")
        df = data_fetcher.get_historical_data('BTCUSDT', '1h', 1000)
        print(f"✅ 生成 {len(df)} 筆數據，價格範圍: {df['close'].min():,.0f} - {df['close'].max():,.0f}")
        
        # 初始化所有策略
        strategies = [
            ("進階策略(75%目標)", AdvancedVolumeEnhancedMACDSignals()),
            ("最終策略(85%目標)", Final85PercentStrategy()),
            ("原始策略(85%閾值)", UltimateOptimizedVolumeEnhancedMACDSignals())
        ]
        
        results = []
        
        print("\n🔍 測試各策略表現...")
        print("-" * 80)
        
        for strategy_name, strategy in strategies:
            print(f"\n測試 {strategy_name}...")
            
            try:
                if hasattr(strategy, 'detect_advanced_signals'):
                    signals_df = strategy.detect_advanced_signals(df)
                elif hasattr(strategy, 'detect_signals'):
                    signals_df = strategy.detect_signals(df)
                else:
                    print(f"❌ {strategy_name} 沒有檢測方法")
                    continue
                
                performance = calculate_performance(signals_df, strategy_name)
                results.append(performance)
                
                print(f"   📊 交易次數: {performance['total_trades']} 筆")
                print(f"   🎯 勝率: {performance['win_rate']:.1f}%")
                print(f"   💰 總獲利: {performance['total_profit']:+,.0f} TWD")
                if performance['total_trades'] > 0:
                    print(f"   💵 平均每筆: {performance['avg_profit_per_trade']:+,.0f} TWD")
                print(f"   🔍 平均信號強度: {performance['avg_signal_strength']:.1f}")
                
            except Exception as e:
                print(f"❌ {strategy_name} 測試失敗: {e}")
                continue
        
        # 顯示對比結果
        print("\n" + "=" * 80)
        print("📊 策略對比結果總覽")
        print("=" * 80)
        
        if results:
            # 按勝率排序
            results.sort(key=lambda x: x['win_rate'], reverse=True)
            
            print(f"{'策略名稱':<20} {'交易次數':<8} {'勝率':<8} {'總獲利':<12} {'平均獲利':<12} {'信號強度':<8}")
            print("-" * 80)
            
            for result in results:
                avg_profit = result['avg_profit_per_trade'] if result['total_trades'] > 0 else 0
                print(f"{result['strategy']:<20} {result['total_trades']:<8} {result['win_rate']:<7.1f}% {result['total_profit']:<+11,.0f} {avg_profit:<+11,.0f} {result['avg_signal_strength']:<7.1f}")
            
            # 找出最佳策略
            best_strategy = max(results, key=lambda x: x['win_rate'])
            most_profitable = max(results, key=lambda x: x['total_profit'])
            most_active = max(results, key=lambda x: x['total_trades'])
            
            print("\n🏆 策略評估:")
            print(f"   🎯 最高勝率: {best_strategy['strategy']} ({best_strategy['win_rate']:.1f}%)")
            print(f"   💰 最高獲利: {most_profitable['strategy']} ({most_profitable['total_profit']:+,.0f} TWD)")
            print(f"   📈 最多交易: {most_active['strategy']} ({most_active['total_trades']} 筆)")
            
            # 策略建議
            print(f"\n💡 策略建議:")
            for result in results:
                if result['win_rate'] >= 85:
                    print(f"   ✅ {result['strategy']}: 已達到85%勝率目標！")
                elif result['win_rate'] >= 75:
                    print(f"   👍 {result['strategy']}: 表現良好，接近目標")
                elif result['win_rate'] >= 60:
                    print(f"   ⚠️  {result['strategy']}: 需要優化")
                else:
                    print(f"   ❌ {result['strategy']}: 表現不佳")
        
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()