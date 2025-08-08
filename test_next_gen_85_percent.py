#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 測試次世代85%+勝率策略
基於現有策略的深度優化版本
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import json

# 添加src目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.next_gen_85_percent_strategy import NextGen85PercentStrategy
from core.smart_balanced_volume_macd_signals import SmartBalancedVolumeEnhancedMACDSignals
from data.data_fetcher import DataFetcher

class NextGenStrategyTester:
    def __init__(self):
        self.next_gen_strategy = NextGen85PercentStrategy()
        self.baseline_strategy = SmartBalancedVolumeEnhancedMACDSignals()
        self.data_fetcher = DataFetcher()
        
    def get_test_data(self):
        """獲取測試數據"""
        print("📊 獲取BTC歷史數據...")
        
        try:
            df = self.data_fetcher.get_kline_data('btctwd', '1h', limit=2000)
            
            if df is None or len(df) < 100:
                print("❌ 數據獲取失敗")
                return None
            
            # 添加時間戳
            if 'timestamp' not in df.columns:
                df['timestamp'] = pd.date_range(
                    start='2025-05-17 02:00:00', 
                    periods=len(df), 
                    freq='H'
                )
            
            print(f"✅ 成功獲取 {len(df)} 筆BTC數據")
            print(f"   時間範圍: {df['timestamp'].iloc[0]} 到 {df['timestamp'].iloc[-1]}")
            
            return df
            
        except Exception as e:
            print(f"❌ 數據獲取失敗: {e}")
            return None
    
    def calculate_performance_metrics(self, signals_df, strategy_name):
        """計算策略績效指標"""
        if signals_df.empty:
            return {
                'strategy_name': strategy_name,
                'total_trades': 0,
                'total_profit': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'avg_signal_strength': 0,
                'max_profit': 0,
                'max_loss': 0,
                'profit_factor': 0
            }
        
        # 配對買賣信號
        buy_signals = signals_df[signals_df['signal_type'] == 'buy'].copy()
        sell_signals = signals_df[signals_df['signal_type'] == 'sell'].copy()
        
        trades = []
        total_profit = 0
        
        for _, buy in buy_signals.iterrows():
            sequence = buy['trade_sequence']
            matching_sells = sell_signals[sell_signals['trade_sequence'] == sequence]
            
            if not matching_sells.empty:
                sell = matching_sells.iloc[0]
                profit = sell['close'] - buy['close']
                profit_pct = (profit / buy['close']) * 100
                
                trades.append({
                    'sequence': sequence,
                    'buy_price': buy['close'],
                    'sell_price': sell['close'],
                    'profit': profit,
                    'profit_pct': profit_pct,
                    'buy_strength': buy.get('signal_strength', 0),
                    'sell_strength': sell.get('signal_strength', 0),
                    'is_winning': profit > 0
                })
                total_profit += profit
        
        if not trades:
            return {
                'strategy_name': strategy_name,
                'total_trades': 0,
                'total_profit': 0,
                'win_rate': 0,
                'avg_profit': 0,
                'avg_signal_strength': 0,
                'max_profit': 0,
                'max_loss': 0,
                'profit_factor': 0
            }
        
        # 計算指標
        winning_trades = [t for t in trades if t['is_winning']]
        losing_trades = [t for t in trades if not t['is_winning']]
        
        win_rate = len(winning_trades) / len(trades) * 100
        avg_profit = total_profit / len(trades)
        
        profits = [t['profit'] for t in trades]
        max_profit = max(profits) if profits else 0
        max_loss = min(profits) if profits else 0
        
        # 計算平均信號強度
        all_strengths = []
        for _, signal in signals_df.iterrows():
            strength = signal.get('signal_strength', 0)
            if strength > 0:
                all_strengths.append(strength)
        
        avg_signal_strength = np.mean(all_strengths) if all_strengths else 0
        
        # 計算獲利因子
        gross_profit = sum(t['profit'] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t['profit'] for t in losing_trades)) if losing_trades else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        return {
            'strategy_name': strategy_name,
            'total_trades': len(trades),
            'total_profit': total_profit,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_signal_strength': avg_signal_strength,
            'max_profit': max_profit,
            'max_loss': max_loss,
            'profit_factor': profit_factor,
            'trades': trades
        }
    
    def run_comparison_test(self):
        """運行對比測試"""
        print("🚀 次世代85%+勝率策略對比測試")
        print("=" * 60)
        
        # 獲取數據
        df = self.get_test_data()
        if df is None:
            return
        
        results = {}
        
        # 測試基準策略（智能平衡版本）
        print("\n🔵 測試基準策略（智能平衡版本）...")
        try:
            baseline_signals = self.baseline_strategy.detect_smart_balanced_signals(df)
            baseline_metrics = self.calculate_performance_metrics(baseline_signals, "智能平衡版本")
            results['baseline'] = baseline_metrics
            
            print(f"   交易次數: {baseline_metrics['total_trades']}")
            print(f"   總獲利: {baseline_metrics['total_profit']:,.0f} TWD")
            print(f"   勝率: {baseline_metrics['win_rate']:.1f}%")
            print(f"   平均信號強度: {baseline_metrics['avg_signal_strength']:.1f}")
            
        except Exception as e:
            print(f"   ❌ 基準策略測試失敗: {e}")
            results['baseline'] = None
        
        # 測試次世代策略
        print("\n🚀 測試次世代85%+策略...")
        try:
            nextgen_signals = self.next_gen_strategy.detect_next_gen_signals(df)
            nextgen_metrics = self.calculate_performance_metrics(nextgen_signals, "次世代85%+")
            results['nextgen'] = nextgen_metrics
            
            print(f"   交易次數: {nextgen_metrics['total_trades']}")
            print(f"   總獲利: {nextgen_metrics['total_profit']:,.0f} TWD")
            print(f"   勝率: {nextgen_metrics['win_rate']:.1f}%")
            print(f"   平均信號強度: {nextgen_metrics['avg_signal_strength']:.1f}")
            
        except Exception as e:
            print(f"   ❌ 次世代策略測試失敗: {e}")
            results['nextgen'] = None
        
        # 對比分析
        self.analyze_comparison_results(results)
        
        # 保存結果
        self.save_test_results(results)
        
        return results
    
    def analyze_comparison_results(self, results):
        """分析對比結果"""
        print("\n" + "=" * 60)
        print("📊 策略對比分析")
        print("=" * 60)
        
        baseline = results.get('baseline')
        nextgen = results.get('nextgen')
        
        if not baseline or not nextgen:
            print("❌ 無法進行對比分析（缺少測試結果）")
            return
        
        print(f"{'指標':<15} {'基準策略':<15} {'次世代策略':<15} {'改進幅度':<15}")
        print("-" * 65)
        
        # 勝率對比
        win_rate_improvement = nextgen['win_rate'] - baseline['win_rate']
        print(f"{'勝率':<15} {baseline['win_rate']:<14.1f}% {nextgen['win_rate']:<14.1f}% {win_rate_improvement:+.1f}%")
        
        # 總獲利對比
        profit_improvement = nextgen['total_profit'] - baseline['total_profit']
        profit_improvement_pct = (profit_improvement / baseline['total_profit'] * 100) if baseline['total_profit'] != 0 else 0
        print(f"{'總獲利':<15} {baseline['total_profit']:<14,.0f} {nextgen['total_profit']:<14,.0f} {profit_improvement_pct:+.1f}%")
        
        # 平均獲利對比
        avg_profit_improvement = nextgen['avg_profit'] - baseline['avg_profit']
        print(f"{'平均獲利':<15} {baseline['avg_profit']:<14,.0f} {nextgen['avg_profit']:<14,.0f} {avg_profit_improvement:+,.0f}")
        
        # 信號強度對比
        strength_improvement = nextgen['avg_signal_strength'] - baseline['avg_signal_strength']
        print(f"{'信號強度':<15} {baseline['avg_signal_strength']:<14.1f} {nextgen['avg_signal_strength']:<14.1f} {strength_improvement:+.1f}")
        
        # 獲利因子對比
        pf_improvement = nextgen['profit_factor'] - baseline['profit_factor']
        print(f"{'獲利因子':<15} {baseline['profit_factor']:<14.2f} {nextgen['profit_factor']:<14.2f} {pf_improvement:+.2f}")
        
        print("\n🎯 85%勝率目標評估:")
        if nextgen['win_rate'] >= 85:
            print(f"   🎉 次世代策略成功達到85%勝率目標！({nextgen['win_rate']:.1f}%)")
        elif nextgen['win_rate'] >= 80:
            print(f"   🔥 次世代策略接近85%目標！({nextgen['win_rate']:.1f}%，還差{85-nextgen['win_rate']:.1f}%)")
        elif nextgen['win_rate'] > baseline['win_rate']:
            print(f"   📈 次世代策略有所改進！({nextgen['win_rate']:.1f}% vs {baseline['win_rate']:.1f}%)")
        else:
            print(f"   ⚠️ 次世代策略需要進一步優化")
        
        # 詳細交易分析
        if nextgen.get('trades'):
            print(f"\n📋 次世代策略交易明細:")
            for i, trade in enumerate(nextgen['trades'][:10], 1):  # 顯示前10筆
                status = "✅" if trade['is_winning'] else "❌"
                print(f"   {status} 交易{i}: {trade['buy_price']:,.0f} → {trade['sell_price']:,.0f} = "
                      f"{trade['profit']:+,.0f} TWD ({trade['profit_pct']:+.2f}%)")
    
    def save_test_results(self, results):
        """保存測試結果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/next_gen_85_percent_test_{timestamp}.json"
        
        try:
            os.makedirs('data', exist_ok=True)
            
            # 準備保存數據（移除不可序列化的對象）
            save_data = {
                'test_date': datetime.now().isoformat(),
                'test_type': '次世代85%+勝率策略對比測試',
                'results': {}
            }
            
            for key, result in results.items():
                if result:
                    save_result = result.copy()
                    # 移除trades詳情以減少文件大小
                    if 'trades' in save_result:
                        save_result['sample_trades'] = save_result['trades'][:5]  # 只保存前5筆
                        del save_result['trades']
                    save_data['results'][key] = save_result
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 測試結果已保存: {filename}")
            
        except Exception as e:
            print(f"\n❌ 保存結果失敗: {e}")

def main():
    """主函數"""
    try:
        tester = NextGenStrategyTester()
        results = tester.run_comparison_test()
        
        print("\n🎉 次世代85%+勝率策略測試完成！")
        
        if results and results.get('nextgen'):
            nextgen_win_rate = results['nextgen']['win_rate']
            if nextgen_win_rate >= 85:
                print(f"🏆 恭喜！次世代策略成功突破85%勝率！({nextgen_win_rate:.1f}%)")
            else:
                print(f"📈 次世代策略表現: {nextgen_win_rate:.1f}%勝率，持續優化中...")
        
        return 0
        
    except Exception as e:
        print(f"\n💥 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())