#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔍 測試策略敏感度分析
分析不同信心度閾值下的策略表現
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import json

# 添加src目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.clean_ultimate_signals import UltimateOptimizedVolumeEnhancedMACDSignals
from data.data_fetcher import DataFetcher

class StrategySensitivityTester:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        
    def test_different_confidence_levels(self):
        """測試不同信心度閾值下的信號數量"""
        print("🔍 策略敏感度分析")
        print("=" * 50)
        
        # 獲取更長的歷史數據
        print("📡 獲取最近30天的歷史數據...")
        df = self.data_fetcher.get_kline_data('btctwd', '1h', limit=30*24)
        
        if df is None or len(df) < 100:
            print("❌ 歷史數據不足")
            return
        
        print(f"✅ 成功獲取 {len(df)} 筆歷史數據")
        print(f"💰 價格範圍: NT$ {df['low'].min():,.0f} - NT$ {df['high'].max():,.0f}")
        
        # 測試不同的信心度閾值
        confidence_levels = [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
        
        print("\n📊 不同信心度閾值下的信號分析:")
        print("-" * 60)
        print(f"{'信心度閾值':<10} {'信號數量':<10} {'買入信號':<10} {'賣出信號':<10}")
        print("-" * 60)
        
        for confidence in confidence_levels:
            # 創建臨時策略實例並修改信心度
            strategy = UltimateOptimizedVolumeEnhancedMACDSignals()
            strategy.min_confidence = confidence
            
            # 計算技術指標
            df_with_indicators = strategy.calculate_indicators(df)
            
            # 檢測信號
            signals = strategy.detect_signals(df_with_indicators)
            
            buy_signals = len([s for s in signals if s['action'] == 'buy'])
            sell_signals = len([s for s in signals if s['action'] == 'sell'])
            
            print(f"{confidence*100:>8.0f}%     {len(signals):>8}     {buy_signals:>8}     {sell_signals:>8}")
        
        # 詳細分析85%信心度的信號
        print("\n🎯 85%信心度詳細分析:")
        print("-" * 50)
        
        strategy_85 = UltimateOptimizedVolumeEnhancedMACDSignals()
        df_with_indicators = strategy_85.calculate_indicators(df)
        signals_85 = strategy_85.detect_signals(df_with_indicators)
        
        if signals_85:
            print(f"✅ 檢測到 {len(signals_85)} 個85%信心度信號")
            for i, signal in enumerate(signals_85[:5]):  # 顯示前5個信號
                print(f"   信號 #{i+1}: {signal['action']} @ NT$ {signal['price']:,.0f}")
                print(f"            信心度: {signal['confidence']*100:.1f}%")
                print(f"            原因: {', '.join(signal['reasons'])}")
        else:
            print("❌ 85%信心度下無信號")
            print("   建議:")
            print("   1. 降低信心度閾值到75-80%")
            print("   2. 使用更長的歷史數據")
            print("   3. 調整技術指標參數")
        
        # 分析技術指標狀態
        self.analyze_technical_indicators(df_with_indicators)
    
    def analyze_technical_indicators(self, df):
        """分析技術指標狀態"""
        print("\n📈 當前技術指標狀態:")
        print("-" * 50)
        
        latest = df.iloc[-1]
        
        print(f"MACD線: {latest['macd']:.4f}")
        print(f"MACD信號線: {latest['macd_signal']:.4f}")
        print(f"MACD柱狀圖: {latest['macd_hist']:.4f}")
        print(f"RSI: {latest['rsi']:.2f}")
        print(f"布林帶上軌: NT$ {latest['bb_upper']:,.0f}")
        print(f"布林帶中軌: NT$ {latest['bb_middle']:,.0f}")
        print(f"布林帶下軌: NT$ {latest['bb_lower']:,.0f}")
        print(f"當前價格: NT$ {latest['close']:,.0f}")
        
        # 分析市場狀態
        print("\n🔍 市場狀態分析:")
        if latest['macd'] > latest['macd_signal']:
            print("   MACD: 多頭趨勢")
        else:
            print("   MACD: 空頭趨勢")
            
        if latest['rsi'] > 70:
            print("   RSI: 超買區域")
        elif latest['rsi'] < 30:
            print("   RSI: 超賣區域")
        else:
            print("   RSI: 正常區域")
            
        if latest['close'] > latest['bb_upper']:
            print("   布林帶: 價格突破上軌")
        elif latest['close'] < latest['bb_lower']:
            print("   布林帶: 價格跌破下軌")
        else:
            print("   布林帶: 價格在正常範圍")

def main():
    """主函數"""
    try:
        tester = StrategySensitivityTester()
        tester.test_different_confidence_levels()
        
        print("\n💡 結論:")
        print("   • 85%信心度是非常保守的設定")
        print("   • 策略寧可錯過機會也不做錯誤交易")
        print("   • 這是高品質信號的體現")
        print("   • 可以考慮降低到75-80%來增加交易頻率")
        
        return 0
        
    except Exception as e:
        print(f"💥 分析過程發生錯誤: {e}")
        return 1

if __name__ == "__main__":
    exit(main())