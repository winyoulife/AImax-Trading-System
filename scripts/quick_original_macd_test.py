#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試你原本的MACD策略 - 提取自clean_macd_backtest_gui.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import logging

# 導入核心模組
from src.data.data_fetcher import DataFetcher
from src.core.improved_trading_signals import SignalDetectionEngine

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_original_macd_strategy():
    """測試你原本的MACD策略"""
    print("🚀 開始測試你原本的MACD策略")
    print("=" * 60)
    
    try:
        # 初始化服務
        data_fetcher = DataFetcher()
        
        # 獲取BTC數據
        print("📊 獲取BTC數據...")
        symbol = 'BTCTWD'
        
        # 獲取1小時數據
        hourly_data = data_fetcher.fetch_data(symbol, '1h', limit=2000)
        
        if hourly_data is None or hourly_data.empty:
            print("❌ 無法獲取數據")
            return
        
        print(f"✅ 成功獲取 {len(hourly_data)} 筆1小時數據")
        print(f"   時間範圍: {hourly_data['timestamp'].min()} 到 {hourly_data['timestamp'].max()}")
        
        # 添加datetime列並計算MACD
        hourly_data['datetime'] = hourly_data['timestamp']
        
        # 計算MACD指標
        ema_fast = hourly_data['close'].ewm(span=12).mean()
        ema_slow = hourly_data['close'].ewm(span=26).mean()
        hourly_data['macd'] = ema_fast - ema_slow
        hourly_data['macd_signal'] = hourly_data['macd'].ewm(span=9).mean()
        hourly_data['macd_hist'] = hourly_data['macd'] - hourly_data['macd_signal']
        
        # 使用你原本的信號檢測引擎
        print("\n🔍 檢測MACD交易信號...")
        engine = SignalDetectionEngine()
        result_df = engine.detect_smart_balanced_signals(hourly_data)
        
        # 獲取統計信息
        stats = engine.get_statistics()
        
        print("\n" + "=" * 60)
        print("📊 你原本的MACD策略結果")
        print("=" * 60)
        
        # 基本統計
        trade_pairs = stats.get('trade_pairs', [])
        total_profit = stats.get('total_profit', 0)
        
        print(f"📈 基本統計:")
        print(f"   交易次數: {len(trade_pairs)}")
        print(f"   總獲利: {total_profit:,.0f} TWD")
        
        if trade_pairs:
            success_count = len([tp for tp in trade_pairs if tp['profit'] > 0])
            success_rate = (success_count / len(trade_pairs)) * 100
            avg_profit = total_profit / len(trade_pairs)
            
            print(f"   勝率: {success_rate:.1f}%")
            print(f"   平均獲利: {avg_profit:,.0f} TWD")
            print(f"   成功交易: {success_count}/{len(trade_pairs)}")
        
        # 交易明細
        if trade_pairs:
            print(f"\n📋 交易明細:")
            print("-" * 60)
            
            for i, trade in enumerate(trade_pairs, 1):
                buy_time = trade['buy_time'].strftime('%m/%d %H:%M')
                sell_time = trade['sell_time'].strftime('%m/%d %H:%M')
                profit_color = "+" if trade['profit'] > 0 else ""
                profit_pct = (trade['profit'] / trade['buy_price']) * 100
                
                print(f"交易 {i:2d}:")
                print(f"  買入: {buy_time} {trade['buy_price']:>8,.0f}")
                print(f"  賣出: {sell_time} {trade['sell_price']:>8,.0f}")
                print(f"  獲利: {profit_color}{trade['profit']:>8,.0f} TWD")
                print(f"  報酬: {profit_color}{profit_pct:>7.1f}%")
                print("")
        else:
            print("\n📋 沒有完整的交易對")
        
        # 信號分析
        buy_signals = result_df[result_df['signal_type'] == 'buy']
        sell_signals = result_df[result_df['signal_type'] == 'sell']
        
        print(f"\n🔍 信號分析:")
        print(f"   買進信號: {len(buy_signals)} 個")
        print(f"   賣出信號: {len(sell_signals)} 個")
        print(f"   完成交易對: {len(trade_pairs)} 對")
        
        print("\n" + "=" * 60)
        print("✅ 測試完成！")
        
        return {
            'total_trades': len(trade_pairs),
            'total_profit': total_profit,
            'success_rate': success_rate if trade_pairs else 0,
            'avg_profit': avg_profit if trade_pairs else 0,
            'trade_pairs': trade_pairs
        }
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_original_macd_strategy()