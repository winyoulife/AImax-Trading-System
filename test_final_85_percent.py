#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試最終85%勝率策略
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from src.core.final_85_percent_strategy import Final85PercentStrategy
from src.data.simple_data_fetcher import DataFetcher

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_trading_performance(signals_df: pd.DataFrame, initial_capital: float = 100000) -> dict:
    """計算交易績效"""
    if signals_df.empty:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'total_profit': 0,
            'profit_percentage': 0,
            'avg_profit_per_trade': 0,
            'trades': []
        }
    
    trades = []
    current_capital = initial_capital
    buy_price = None
    buy_sequence = None
    
    for _, signal in signals_df.iterrows():
        if signal['signal_type'] == 'buy':
            buy_price = signal['close']
            buy_sequence = signal['trade_sequence']
            logger.info(f"🟢 買進 #{buy_sequence}: {buy_price:,.0f} TWD (信號強度: {signal['signal_strength']:.1f})")
            
        elif signal['signal_type'] == 'sell' and buy_price is not None:
            sell_price = signal['close']
            profit = sell_price - buy_price
            profit_pct = (profit / buy_price) * 100
            
            # 計算實際資金變化
            trade_amount = current_capital * 0.95  # 95%資金投入
            actual_profit = trade_amount * (profit / buy_price)
            current_capital += actual_profit
            
            trade_info = {
                'sequence': buy_sequence,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'profit': profit,
                'profit_pct': profit_pct,
                'actual_profit': actual_profit,
                'buy_strength': signals_df[signals_df['trade_sequence'] == buy_sequence]['signal_strength'].iloc[0] if not signals_df[signals_df['trade_sequence'] == buy_sequence].empty else 0,
                'sell_strength': signal['signal_strength'],
                'buy_date': signals_df[signals_df['trade_sequence'] == buy_sequence]['datetime'].iloc[0] if not signals_df[signals_df['trade_sequence'] == buy_sequence].empty else None,
                'sell_date': signal['datetime']
            }
            trades.append(trade_info)
            
            status = "✅ 獲利" if profit > 0 else "❌ 虧損"
            logger.info(f"🔴 賣出 #{buy_sequence}: {sell_price:,.0f} TWD → {status} {profit:+,.0f} TWD ({profit_pct:+.1f}%) [信號強度: {signal['signal_strength']:.1f}]")
            
            buy_price = None
            buy_sequence = None
    
    # 計算統計數據
    if not trades:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'total_profit': 0,
            'profit_percentage': 0,
            'avg_profit_per_trade': 0,
            'trades': []
        }
    
    winning_trades = [t for t in trades if t['profit'] > 0]
    total_profit = sum(t['actual_profit'] for t in trades)
    
    return {
        'total_trades': len(trades),
        'win_rate': len(winning_trades) / len(trades) * 100,
        'total_profit': total_profit,
        'profit_percentage': (current_capital - initial_capital) / initial_capital * 100,
        'avg_profit_per_trade': total_profit / len(trades),
        'final_capital': current_capital,
        'trades': trades
    }

def main():
    """主測試函數"""
    print("🚀 開始測試最終85%勝率策略...")
    print("=" * 60)
    
    try:
        # 初始化策略和數據獲取器
        strategy = Final85PercentStrategy()
        data_fetcher = DataFetcher()
        
        # 獲取歷史數據
        print("📊 獲取BTC歷史數據...")
        df = data_fetcher.get_historical_data('BTCUSDT', '1h', 1000)  # 獲取更多數據進行全面測試
        
        if df is None or df.empty:
            print("❌ 無法獲取數據")
            return
        
        print(f"✅ 成功獲取 {len(df)} 筆數據")
        print(f"📅 數據範圍: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        
        # 檢測交易信號
        print("\n🔍 檢測交易信號...")
        signals_df = strategy.detect_signals(df)
        
        if signals_df.empty:
            print("❌ 未檢測到任何交易信號")
            return
        
        print(f"✅ 檢測到 {len(signals_df)} 個交易信號")
        
        # 計算交易績效
        print("\n📈 計算交易績效...")
        performance = calculate_trading_performance(signals_df)
        
        # 顯示結果
        print("\n" + "=" * 60)
        print("🎯 最終85%勝率策略測試結果")
        print("=" * 60)
        
        print(f"📊 總交易次數: {performance['total_trades']} 筆")
        print(f"🎯 勝率: {performance['win_rate']:.1f}%")
        print(f"💰 總獲利: {performance['total_profit']:+,.0f} TWD")
        print(f"📈 獲利率: {performance['profit_percentage']:+.1f}%")
        print(f"💵 平均每筆獲利: {performance['avg_profit_per_trade']:+,.0f} TWD")
        print(f"🏦 最終資金: {performance['final_capital']:,.0f} TWD")
        
        # 詳細交易記錄
        if performance['trades']:
            print(f"\n📋 詳細交易記錄:")
            print("-" * 80)
            for i, trade in enumerate(performance['trades'], 1):
                status = "✅" if trade['profit'] > 0 else "❌"
                print(f"{i:2d}. {status} 買:{trade['buy_price']:7,.0f} → 賣:{trade['sell_price']:7,.0f} = {trade['profit']:+6,.0f} TWD ({trade['profit_pct']:+5.1f}%) [買進強度:{trade['buy_strength']:.0f} 賣出強度:{trade['sell_strength']:.0f}]")
        
        # 信號強度分析
        buy_signals = signals_df[signals_df['signal_type'] == 'buy']
        sell_signals = signals_df[signals_df['signal_type'] == 'sell']
        
        if not buy_signals.empty:
            print(f"\n🔍 信號強度分析:")
            print(f"   買進信號平均強度: {buy_signals['signal_strength'].mean():.1f}")
            print(f"   賣出信號平均強度: {sell_signals['signal_strength'].mean():.1f}")
            print(f"   最高信號強度: {signals_df['signal_strength'].max():.1f}")
            print(f"   最低信號強度: {signals_df['signal_strength'].min():.1f}")
        
        # 策略評估
        print(f"\n🎯 策略評估:")
        if performance['win_rate'] >= 85:
            print(f"🎉 恭喜！已達到85%勝率目標！({performance['win_rate']:.1f}%)")
        elif performance['win_rate'] >= 80:
            print(f"👍 接近目標！勝率{performance['win_rate']:.1f}%，距離85%還差{85-performance['win_rate']:.1f}%")
        elif performance['win_rate'] >= 75:
            print(f"📈 良好表現！勝率{performance['win_rate']:.1f}%，需要進一步優化")
        else:
            print(f"⚠️  需要改進！勝率{performance['win_rate']:.1f}%，低於預期")
        
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()