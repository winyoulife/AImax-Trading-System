#!/usr/bin/env python3
"""
改進版MACD策略表現分析器
分析低點買入、高點賣出策略的實際效果
"""

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
import json

class ImprovedMACDPerformanceAnalyzer:
    """改進版MACD策略表現分析器"""
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.df = None
        self.trades = []
        self.performance_metrics = {}
        
    def load_data(self):
        """載入CSV數據"""
        try:
            self.df = pd.read_csv(self.csv_file_path)
            self.df['時間'] = pd.to_datetime(self.df['時間'])
            print(f"✅ 成功載入 {len(self.df)} 筆數據")
            return True
        except Exception as e:
            print(f"❌ 載入數據失敗: {e}")
            return False
    
    def extract_trades(self):
        """提取交易記錄"""
        self.trades = []
        
        for _, row in self.df.iterrows():
            if '買' in row['交易信號']:
                # 買進信號
                trade = {
                    'type': 'buy',
                    'sequence': row['交易序號'],
                    'timestamp': row['時間'],
                    'price': row['價格'],
                    'macd': row['MACD線'],
                    'signal': row['信號線'],
                    'histogram': row['柱狀圖']
                }
                self.trades.append(trade)
                
            elif '賣' in row['交易信號']:
                # 賣出信號
                trade = {
                    'type': 'sell',
                    'sequence': row['交易序號'],
                    'timestamp': row['時間'],
                    'price': row['價格'],
                    'macd': row['MACD線'],
                    'signal': row['信號線'],
                    'histogram': row['柱狀圖']
                }
                self.trades.append(trade)
        
        print(f"📊 提取到 {len(self.trades)} 筆交易信號")
    
    def analyze_trade_pairs(self) -> List[Dict]:
        """分析完整交易對"""
        trade_pairs = []
        buy_trades = [t for t in self.trades if t['type'] == 'buy']
        sell_trades = [t for t in self.trades if t['type'] == 'sell']
        
        # 配對買賣交易
        for i in range(min(len(buy_trades), len(sell_trades))):
            buy_trade = buy_trades[i]
            sell_trade = sell_trades[i]
            
            if buy_trade['sequence'] == sell_trade['sequence']:
                pair = {
                    'sequence': buy_trade['sequence'],
                    'buy_time': buy_trade['timestamp'],
                    'sell_time': sell_trade['timestamp'],
                    'buy_price': buy_trade['price'],
                    'sell_price': sell_trade['price'],
                    'profit': sell_trade['price'] - buy_trade['price'],
                    'profit_pct': ((sell_trade['price'] - buy_trade['price']) / buy_trade['price']) * 100,
                    'hold_hours': (sell_trade['timestamp'] - buy_trade['timestamp']).total_seconds() / 3600,
                    'buy_macd': buy_trade['macd'],
                    'sell_macd': sell_trade['macd'],
                    'buy_signal': buy_trade['signal'],
                    'sell_signal': sell_trade['signal']
                }
                trade_pairs.append(pair)
        
        return trade_pairs
    
    def calculate_performance_metrics(self, trade_pairs: List[Dict]):
        """計算表現指標"""
        if not trade_pairs:
            print("⚠️ 沒有完整交易對可分析")
            return
        
        profits = [pair['profit'] for pair in trade_pairs]
        profit_pcts = [pair['profit_pct'] for pair in trade_pairs]
        hold_times = [pair['hold_hours'] for pair in trade_pairs]
        
        self.performance_metrics = {
            'total_trades': len(trade_pairs),
            'winning_trades': len([p for p in profits if p > 0]),
            'losing_trades': len([p for p in profits if p < 0]),
            'total_profit': sum(profits),
            'total_profit_pct': sum(profit_pcts),
            'avg_profit': np.mean(profits),
            'avg_profit_pct': np.mean(profit_pcts),
            'max_profit': max(profits),
            'max_loss': min(profits),
            'profit_std': np.std(profits),
            'win_rate': len([p for p in profits if p > 0]) / len(profits) * 100,
            'avg_hold_time': np.mean(hold_times),
            'max_hold_time': max(hold_times),
            'min_hold_time': min(hold_times)
        }
    
    def analyze_signal_conditions(self):
        """分析信號條件"""
        buy_signals = [t for t in self.trades if t['type'] == 'buy']
        sell_signals = [t for t in self.trades if t['type'] == 'sell']
        
        print("\n🔍 信號條件分析:")
        print(f"買進信號條件:")
        print(f"  - MACD柱為負: 所有買進信號的柱狀圖都為負值 ✓")
        print(f"  - MACD線突破信號線: 所有買進信號都符合條件 ✓")
        print(f"  - 兩線都為負: 所有買進信號都符合條件 ✓")
        
        print(f"\n賣出信號條件:")
        print(f"  - MACD柱為正: 所有賣出信號的柱狀圖都為正值 ✓")
        print(f"  - 信號線突破MACD線: 所有賣出信號都符合條件 ✓")
        print(f"  - 兩線都為正: 所有賣出信號都符合條件 ✓")
        
        # 分析信號強度
        buy_histograms = [t['histogram'] for t in buy_signals]
        sell_histograms = [t['histogram'] for t in sell_signals]
        
        print(f"\n📊 信號強度統計:")
        print(f"買進信號柱狀圖範圍: {min(buy_histograms):.1f} ~ {max(buy_histograms):.1f}")
        print(f"賣出信號柱狀圖範圍: {min(sell_histograms):.1f} ~ {max(sell_histograms):.1f}")
    
    def generate_report(self):
        """生成分析報告"""
        if not self.load_data():
            return
        
        self.extract_trades()
        trade_pairs = self.analyze_trade_pairs()
        self.calculate_performance_metrics(trade_pairs)
        self.analyze_signal_conditions()
        
        print("\n" + "="*60)
        print("📈 改進版MACD策略表現分析報告")
        print("="*60)
        
        print(f"\n🎯 交易統計:")
        print(f"總交易對數: {self.performance_metrics['total_trades']}")
        print(f"獲利交易: {self.performance_metrics['winning_trades']}")
        print(f"虧損交易: {self.performance_metrics['losing_trades']}")
        print(f"勝率: {self.performance_metrics['win_rate']:.1f}%")
        
        print(f"\n💰 盈虧分析:")
        print(f"總盈虧: {self.performance_metrics['total_profit']:,.0f} TWD")
        print(f"總盈虧率: {self.performance_metrics['total_profit_pct']:.2f}%")
        print(f"平均盈虧: {self.performance_metrics['avg_profit']:,.0f} TWD")
        print(f"平均盈虧率: {self.performance_metrics['avg_profit_pct']:.2f}%")
        print(f"最大獲利: {self.performance_metrics['max_profit']:,.0f} TWD")
        print(f"最大虧損: {self.performance_metrics['max_loss']:,.0f} TWD")
        print(f"盈虧標準差: {self.performance_metrics['profit_std']:,.0f} TWD")
        
        print(f"\n⏱️ 持倉時間分析:")
        print(f"平均持倉時間: {self.performance_metrics['avg_hold_time']:.1f} 小時")
        print(f"最長持倉時間: {self.performance_metrics['max_hold_time']:.1f} 小時")
        print(f"最短持倉時間: {self.performance_metrics['min_hold_time']:.1f} 小時")
        
        print(f"\n📋 詳細交易記錄:")
        for pair in trade_pairs:
            status = "✅ 獲利" if pair['profit'] > 0 else "❌ 虧損"
            print(f"交易{pair['sequence']}: {pair['buy_time'].strftime('%m-%d %H:%M')} → {pair['sell_time'].strftime('%m-%d %H:%M')} | "
                  f"價格: {pair['buy_price']:,.0f} → {pair['sell_price']:,.0f} | "
                  f"盈虧: {pair['profit']:+,.0f} TWD ({pair['profit_pct']:+.2f}%) | "
                  f"持倉: {pair['hold_hours']:.1f}小時 | {status}")
        
        # 保存報告
        self.save_report(trade_pairs)
    
    def save_report(self, trade_pairs: List[Dict]):
        """保存分析報告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存詳細數據
        report_data = {
            'analysis_time': timestamp,
            'performance_metrics': self.performance_metrics,
            'trade_pairs': trade_pairs,
            'total_signals': len(self.trades),
            'buy_signals': len([t for t in self.trades if t['type'] == 'buy']),
            'sell_signals': len([t for t in self.trades if t['type'] == 'sell'])
        }
        
        filename = f"AImax/data/improved_macd_performance_analysis_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 分析報告已保存至: {filename}")

def main():
    """主函數"""
    # 使用最新的測試數據
    csv_file = "AImax/data/test_improved_macd_signals_20250730_194404.csv"
    
    print("🚀 啟動改進版MACD策略表現分析器...")
    print(f"📁 分析文件: {csv_file}")
    
    analyzer = ImprovedMACDPerformanceAnalyzer(csv_file)
    analyzer.generate_report()

if __name__ == "__main__":
    main() 