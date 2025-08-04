#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試BTC成交量增強MACD策略
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import logging

# 導入必要的模組
from src.data.data_fetcher import DataFetcher
from src.core.volume_enhanced_macd_signals import VolumeEnhancedMACDSignals
from src.core.improved_trading_signals import SignalDetectionEngine

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_basic_macd_signals(df: pd.DataFrame) -> pd.DataFrame:
    """計算基本MACD信號（用於比較）"""
    if df is None or df.empty:
        return pd.DataFrame()
    
    df = df.copy()
    
    # 計算MACD
    ema_fast = df['close'].ewm(span=12).mean()
    ema_slow = df['close'].ewm(span=26).mean()
    df['macd'] = ema_fast - ema_slow
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # 檢測信號
    signals = []
    position = 0  # 0=空倉, 1=持倉
    trade_sequence = 0
    
    for i in range(1, len(df)):
        current_row = df.iloc[i]
        previous_row = df.iloc[i-1]
        
        # MACD買進信號（金叉）
        if (previous_row['macd_hist'] < 0 and 
            previous_row['macd'] <= previous_row['macd_signal'] and 
            current_row['macd'] > current_row['macd_signal'] and
            current_row['macd'] < 0 and current_row['macd_signal'] < 0 and
            position == 0):
            
            trade_sequence += 1
            position = 1
            signals.append({
                'datetime': current_row['timestamp'],
                'close': current_row['close'],
                'signal_type': 'buy',
                'trade_sequence': trade_sequence,
                'macd': current_row['macd'],
                'macd_signal': current_row['macd_signal'],
                'macd_hist': current_row['macd_hist']
            })
        
        # MACD賣出信號（死叉）
        elif (previous_row['macd_hist'] > 0 and 
              previous_row['macd'] >= previous_row['macd_signal'] and 
              current_row['macd_signal'] > current_row['macd'] and
              current_row['macd'] > 0 and current_row['macd_signal'] > 0 and
              position == 1):
            
            position = 0
            signals.append({
                'datetime': current_row['timestamp'],
                'close': current_row['close'],
                'signal_type': 'sell',
                'trade_sequence': trade_sequence,
                'macd': current_row['macd'],
                'macd_signal': current_row['macd_signal'],
                'macd_hist': current_row['macd_hist']
            })
    
    return pd.DataFrame(signals)

def calculate_trade_performance(signals_df: pd.DataFrame) -> Dict:
    """計算交易表現"""
    if signals_df.empty:
        return {
            'total_trades': 0,
            'total_profit': 0,
            'success_rate': 0,
            'avg_profit': 0,
            'trade_pairs': []
        }
    
    buy_signals = signals_df[signals_df['signal_type'] == 'buy'].copy()
    sell_signals = signals_df[signals_df['signal_type'] == 'sell'].copy()
    
    trade_pairs = []
    total_profit = 0
    
    # 配對買賣信號
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
                'profit_pct': (profit / buy_signal['close']) * 100
            }
            trade_pairs.append(trade_pair)
            total_profit += profit
    
    # 計算統計數據
    success_count = len([tp for tp in trade_pairs if tp['profit'] > 0])
    success_rate = (success_count / len(trade_pairs)) * 100 if trade_pairs else 0
    avg_profit = total_profit / len(trade_pairs) if trade_pairs else 0
    
    return {
        'total_trades': len(trade_pairs),
        'total_profit': total_profit,
        'success_rate': success_rate,
        'avg_profit': avg_profit,
        'trade_pairs': trade_pairs
    }

def main():
    """主函數"""
    print("🚀 開始測試BTC成交量增強MACD策略")
    print("=" * 60)
    
    # 初始化
    data_fetcher = DataFetcher()
    volume_enhanced = VolumeEnhancedMACDSignals()
    
    # 獲取BTC數據
    print("📊 獲取BTC數據...")
    df = data_fetcher.fetch_data('BTCTWD', '1h', limit=2000)  # 約3個月數據
    
    if df is None or df.empty:
        print("❌ 無法獲取BTC數據")
        return
    
    print(f"✅ 成功獲取 {len(df)} 筆BTC數據")
    print(f"   時間範圍: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
    
    # 檢查成交量數據
    if 'volume' not in df.columns or df['volume'].isna().all():
        print("❌ 缺少成交量數據")
        return
    
    print(f"   平均成交量: {df['volume'].mean():,.0f}")
    print(f"   成交量範圍: {df['volume'].min():,.0f} - {df['volume'].max():,.0f}")
    
    print("\n" + "=" * 60)
    
    # 測試原始MACD策略
    print("🔵 測試原始MACD策略...")
    try:
        original_signals = calculate_basic_macd_signals(df)
        original_performance = calculate_trade_performance(original_signals)
        
        print(f"   交易次數: {original_performance['total_trades']}")
        print(f"   總獲利: {original_performance['total_profit']:,.0f} TWD")
        print(f"   勝率: {original_performance['success_rate']:.1f}%")
        print(f"   平均獲利: {original_performance['avg_profit']:,.0f} TWD")
        
    except Exception as e:
        print(f"❌ 原始MACD策略測試失敗: {e}")
        original_performance = {'total_trades': 0, 'total_profit': 0}
    
    print("\n" + "-" * 60)
    
    # 測試成交量增強MACD策略
    print("🟢 測試成交量增強MACD策略...")
    try:
        volume_signals = volume_enhanced.detect_enhanced_signals(df)
        
        if volume_signals.empty:
            print("   沒有檢測到信號")
            volume_performance = {'total_trades': 0, 'total_profit': 0, 'confirmed_signals': 0, 'rejected_signals': 0}
        else:
            volume_performance = calculate_trade_performance(volume_signals)
            
            # 額外統計
            confirmed_signals = len(volume_signals[volume_signals['volume_confirmed'] == True])
            rejected_signals = len(volume_signals[volume_signals['volume_confirmed'] == False])
            avg_signal_strength = volume_signals[volume_signals['volume_confirmed'] == True]['signal_strength'].mean()
            
            volume_performance['confirmed_signals'] = confirmed_signals
            volume_performance['rejected_signals'] = rejected_signals
            volume_performance['avg_signal_strength'] = avg_signal_strength if not pd.isna(avg_signal_strength) else 0
            
            print(f"   確認信號: {confirmed_signals}")
            print(f"   拒絕信號: {rejected_signals}")
            print(f"   交易次數: {volume_performance['total_trades']}")
            print(f"   總獲利: {volume_performance['total_profit']:,.0f} TWD")
            print(f"   勝率: {volume_performance['success_rate']:.1f}%")
            print(f"   平均獲利: {volume_performance['avg_profit']:,.0f} TWD")
            print(f"   平均信號強度: {volume_performance['avg_signal_strength']:.1f}/100")
        
    except Exception as e:
        print(f"❌ 成交量增強MACD策略測試失敗: {e}")
        import traceback
        traceback.print_exc()
        volume_performance = {'total_trades': 0, 'total_profit': 0, 'confirmed_signals': 0, 'rejected_signals': 0}
    
    print("\n" + "=" * 60)
    
    # 比較結果
    print("📈 策略比較結果:")
    
    if original_performance['total_trades'] > 0 and volume_performance['total_trades'] > 0:
        profit_improvement = volume_performance['total_profit'] - original_performance['total_profit']
        improvement_pct = (profit_improvement / abs(original_performance['total_profit'])) * 100 if original_performance['total_profit'] != 0 else 0
        
        print(f"   獲利改善: {profit_improvement:+,.0f} TWD ({improvement_pct:+.1f}%)")
        
        if profit_improvement > 0:
            print("   🎉 成交量增強策略表現更好！")
        elif profit_improvement < 0:
            print("   ⚠️  原始策略表現更好")
        else:
            print("   🤝 兩種策略表現相同")
            
        # 信號過濾效果
        if 'rejected_signals' in volume_performance:
            print(f"   信號過濾: 拒絕了 {volume_performance['rejected_signals']} 個可能的假信號")
    
    elif original_performance['total_trades'] == 0 and volume_performance['total_trades'] == 0:
        print("   ⚪ 兩種策略都沒有產生交易信號")
    
    elif original_performance['total_trades'] > 0:
        print("   📊 只有原始策略產生了交易信號")
        print("   💡 成交量過濾可能過於嚴格，建議調整參數")
    
    else:
        print("   📊 只有成交量增強策略產生了交易信號")
    
    print("\n" + "=" * 60)
    print("✅ 測試完成！")
    
    # 顯示詳細交易記錄（最近5筆）
    if volume_performance.get('trade_pairs'):
        print(f"\n📋 最近5筆成交量增強策略交易:")
        recent_trades = volume_performance['trade_pairs'][-5:]
        for i, trade in enumerate(recent_trades, 1):
            print(f"   {i}. {trade['buy_time'].strftime('%m/%d %H:%M')} 買入 {trade['buy_price']:,.0f} → "
                  f"{trade['sell_time'].strftime('%m/%d %H:%M')} 賣出 {trade['sell_price']:,.0f} "
                  f"= {trade['profit']:+,.0f} TWD ({trade['profit_pct']:+.1f}%)")

if __name__ == "__main__":
    main()