#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正確的成交量增強MACD策略GUI測試工具
使用你原本成功的MACD策略作為基準
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import logging
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading

# 導入必要的模組
from src.data.data_fetcher import DataFetcher
from src.core.volume_enhanced_macd_signals import VolumeEnhancedMACDSignals
from src.core.improved_trading_signals import SignalDetectionEngine

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_original_macd_strategy(df: pd.DataFrame) -> Dict:
    """測試你原本成功的MACD策略"""
    if df is None or df.empty:
        return {'total_trades': 0, 'total_profit': 0, 'success_rate': 0, 'trade_pairs': []}
    
    # 使用你原本的SignalDetectionEngine
    engine = SignalDetectionEngine()
    
    df = df.copy()
    
    # 計算MACD
    ema_fast = df['close'].ewm(span=12).mean()
    ema_slow = df['close'].ewm(span=26).mean()
    df['macd'] = ema_fast - ema_slow
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # 添加datetime列（如果不存在）
    if 'datetime' not in df.columns:
        df['datetime'] = df['timestamp']
    
    # 使用你原本的信號檢測引擎
    result_df = engine.detect_signals(df)
    
    # 獲取統計信息
    stats = engine.get_statistics()
    
    # 計算成功率並添加profit_pct字段
    trade_pairs = stats.get('trade_pairs', [])
    
    # 為每個交易對添加profit_pct字段
    for trade_pair in trade_pairs:
        if 'profit_pct' not in trade_pair:
            trade_pair['profit_pct'] = (trade_pair['profit'] / trade_pair['buy_price']) * 100
    
    success_count = len([tp for tp in trade_pairs if tp['profit'] > 0])
    success_rate = (success_count / len(trade_pairs)) * 100 if trade_pairs else 0
    avg_profit = stats.get('total_profit', 0) / len(trade_pairs) if trade_pairs else 0
    
    return {
        'total_trades': len(trade_pairs),
        'total_profit': stats.get('total_profit', 0),
        'success_rate': success_rate,
        'avg_profit': avg_profit,
        'trade_pairs': trade_pairs,
        'signals_df': result_df
    }

def test_volume_enhanced_strategy(df: pd.DataFrame) -> Dict:
    """測試成交量增強MACD策略"""
    if df is None or df.empty:
        return {'total_trades': 0, 'total_profit': 0, 'success_rate': 0, 'trade_pairs': []}
    
    volume_enhanced = VolumeEnhancedMACDSignals()
    signals_df = volume_enhanced.detect_enhanced_signals(df)
    
    if signals_df.empty:
        return {
            'total_trades': 0,
            'total_profit': 0,
            'success_rate': 0,
            'avg_profit': 0,
            'trade_pairs': [],
            'confirmed_signals': 0,
            'rejected_signals': 0,
            'avg_signal_strength': 0,
            'all_signals': pd.DataFrame()
        }
    
    # 分析信號類型
    buy_signals = signals_df[signals_df['signal_type'] == 'buy'].copy()
    sell_signals = signals_df[signals_df['signal_type'] == 'sell'].copy()
    buy_rejected = signals_df[signals_df['signal_type'] == 'buy_rejected']
    sell_rejected = signals_df[signals_df['signal_type'] == 'sell_rejected']
    
    confirmed_signals = len(buy_signals) + len(sell_signals)
    rejected_signals = len(buy_rejected) + len(sell_rejected)
    
    # 計算交易對和利潤
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
                'profit_pct': (profit / buy_signal['close']) * 100,
                'buy_volume_info': buy_signal.get('volume_info', ''),
                'sell_volume_info': sell_signal.get('volume_info', ''),
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
        'avg_signal_strength': avg_signal_strength if not pd.isna(avg_signal_strength) else 0,
        'all_signals': signals_df
    }

class CorrectVolumeEnhancedMACDGUI:
    """正確的成交量增強MACD策略GUI"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.setup_gui()
        
        # 測試結果
        self.original_results = None
        self.volume_results = None
        self.df = None
    
    def setup_gui(self):
        """設置GUI"""
        self.root = tk.Tk()
        self.root.title("🚀 BTC成交量增強MACD策略測試 (正確版)")
        self.root.geometry("1400x900")
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 標題
        title_label = ttk.Label(main_frame, text="🚀 BTC成交量增強MACD策略測試 (使用你原本成功的MACD策略)", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="測試控制", padding="10")
        control_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 開始測試按鈕
        self.start_button = ttk.Button(control_frame, text="🔍 開始測試", 
                                      command=self.start_test, style='Accent.TButton')
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # 進度標籤
        self.progress_var = tk.StringVar(value="準備就緒")
        self.progress_label = ttk.Label(control_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=1, padx=(10, 0))
        
        # 結果對比框架
        results_frame = ttk.Frame(main_frame)
        results_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # 原始MACD結果
        original_frame = ttk.LabelFrame(results_frame, text="🔵 你原本的MACD策略 (成功版)", padding="10")
        original_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.original_text = scrolledtext.ScrolledText(original_frame, width=45, height=30, 
                                                      font=('Consolas', 9))
        self.original_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 成交量增強結果
        volume_frame = ttk.LabelFrame(results_frame, text="🟢 成交量增強MACD策略", padding="10")
        volume_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 5))
        
        self.volume_text = scrolledtext.ScrolledText(volume_frame, width=45, height=30, 
                                                    font=('Consolas', 9))
        self.volume_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 比較結果
        comparison_frame = ttk.LabelFrame(results_frame, text="📊 策略比較分析", padding="10")
        comparison_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        self.comparison_text = scrolledtext.ScrolledText(comparison_frame, width=45, height=30, 
                                                        font=('Consolas', 9))
        self.comparison_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置網格權重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(2, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(2, weight=1)
        results_frame.rowconfigure(0, weight=1)
        original_frame.columnconfigure(0, weight=1)
        original_frame.rowconfigure(0, weight=1)
        volume_frame.columnconfigure(0, weight=1)
        volume_frame.rowconfigure(0, weight=1)
        comparison_frame.columnconfigure(0, weight=1)
        comparison_frame.rowconfigure(0, weight=1)
    
    def start_test(self):
        """開始測試"""
        self.start_button.config(state='disabled')
        self.clear_all_text()
        self.progress_var.set("正在獲取BTC數據...")
        
        # 在新線程中運行測試
        def run_test():
            try:
                # 獲取數據
                self.df = self.data_fetcher.fetch_data('BTCTWD', '1h', limit=2000)
                
                if self.df is None or self.df.empty:
                    self.root.after(0, self.display_error, "無法獲取BTC數據")
                    return
                
                self.root.after(0, self.update_progress, "正在測試你原本的MACD策略...")
                
                # 測試原始MACD策略
                self.original_results = test_original_macd_strategy(self.df)
                
                self.root.after(0, self.display_original_results)
                self.root.after(0, self.update_progress, "正在測試成交量增強策略...")
                
                # 測試成交量增強策略
                self.volume_results = test_volume_enhanced_strategy(self.df)
                
                self.root.after(0, self.display_volume_results)
                self.root.after(0, self.display_comparison)
                self.root.after(0, self.update_progress, "測試完成！")
                
            except Exception as e:
                error_msg = f"測試過程中發生錯誤: {e}"
                self.root.after(0, self.display_error, error_msg)
                import traceback
                traceback.print_exc()
            finally:
                self.root.after(0, lambda: self.start_button.config(state='normal'))
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def display_original_results(self):
        """顯示原始MACD結果"""
        if not self.original_results:
            return
        
        result_text = []
        result_text.append("=" * 40)
        result_text.append("🔵 你原本的MACD策略結果")
        result_text.append("=" * 40)
        result_text.append("")
        
        # 基本統計
        result_text.append(f"📊 基本統計:")
        result_text.append(f"   交易次數: {self.original_results['total_trades']}")
        result_text.append(f"   總獲利: {self.original_results['total_profit']:,.0f} TWD")
        result_text.append(f"   勝率: {self.original_results['success_rate']:.1f}%")
        result_text.append(f"   平均獲利: {self.original_results['avg_profit']:,.0f} TWD")
        result_text.append("")
        
        # 交易明細
        if self.original_results['trade_pairs']:
            result_text.append("📋 交易明細:")
            result_text.append("-" * 40)
            
            for i, trade in enumerate(self.original_results['trade_pairs'], 1):
                buy_time = trade['buy_time'].strftime('%m/%d %H:%M')
                sell_time = trade['sell_time'].strftime('%m/%d %H:%M')
                profit_color = "+" if trade['profit'] > 0 else ""
                
                result_text.append(f"交易 {i:2d}:")
                result_text.append(f"  買入: {buy_time} {trade['buy_price']:>8,.0f}")
                result_text.append(f"  賣出: {sell_time} {trade['sell_price']:>8,.0f}")
                result_text.append(f"  獲利: {profit_color}{trade['profit']:>8,.0f} TWD")
                result_text.append(f"  報酬: {profit_color}{trade['profit_pct']:>7.1f}%")
                result_text.append("")
        else:
            result_text.append("📋 沒有完整的交易對")
        
        self.original_text.delete(1.0, tk.END)
        self.original_text.insert(tk.END, "\n".join(result_text))  
  
    def display_volume_results(self):
        """顯示成交量增強結果"""
        if not self.volume_results:
            return
        
        result_text = []
        result_text.append("=" * 40)
        result_text.append("🟢 成交量增強MACD策略結果")
        result_text.append("=" * 40)
        result_text.append("")
        
        # 基本統計
        result_text.append(f"📊 基本統計:")
        result_text.append(f"   確認信號: {self.volume_results['confirmed_signals']}")
        result_text.append(f"   拒絕信號: {self.volume_results['rejected_signals']}")
        result_text.append(f"   交易次數: {self.volume_results['total_trades']}")
        result_text.append(f"   總獲利: {self.volume_results['total_profit']:,.0f} TWD")
        result_text.append(f"   勝率: {self.volume_results['success_rate']:.1f}%")
        result_text.append(f"   平均獲利: {self.volume_results['avg_profit']:,.0f} TWD")
        result_text.append(f"   信號強度: {self.volume_results['avg_signal_strength']:.1f}/100")
        result_text.append("")
        
        # 交易明細
        if self.volume_results['trade_pairs']:
            result_text.append("📋 交易明細:")
            result_text.append("-" * 40)
            
            for i, trade in enumerate(self.volume_results['trade_pairs'], 1):
                buy_time = trade['buy_time'].strftime('%m/%d %H:%M')
                sell_time = trade['sell_time'].strftime('%m/%d %H:%M')
                profit_color = "+" if trade['profit'] > 0 else ""
                
                result_text.append(f"交易 {i:2d}:")
                result_text.append(f"  買入: {buy_time} {trade['buy_price']:>8,.0f}")
                result_text.append(f"  賣出: {sell_time} {trade['sell_price']:>8,.0f}")
                result_text.append(f"  獲利: {profit_color}{trade['profit']:>8,.0f} TWD")
                result_text.append(f"  報酬: {profit_color}{trade['profit_pct']:>7.1f}%")
                result_text.append(f"  買強度: {trade.get('buy_strength', 0):.1f}")
                result_text.append(f"  賣強度: {trade.get('sell_strength', 0):.1f}")
                result_text.append("")
        else:
            result_text.append("📋 沒有完整的交易對")
        
        # 被拒絕的信號樣本
        if 'all_signals' in self.volume_results and not self.volume_results['all_signals'].empty:
            rejected_signals = self.volume_results['all_signals'][
                self.volume_results['all_signals']['volume_confirmed'] == False
            ]
            
            if not rejected_signals.empty:
                result_text.append("❌ 被拒絕信號樣本 (前5個):")
                result_text.append("-" * 40)
                
                for i, (_, signal) in enumerate(rejected_signals.head(5).iterrows(), 1):
                    signal_time = signal['datetime'].strftime('%m/%d %H:%M')
                    signal_type = "買入" if signal['signal_type'] == 'buy_rejected' else "賣出"
                    
                    result_text.append(f"拒絕 {i}: {signal_time} {signal_type}")
                    result_text.append(f"  價格: {signal['close']:,.0f}")
                    result_text.append(f"  原因: {signal.get('volume_info', 'N/A')}")
                    result_text.append("")
        
        self.volume_text.delete(1.0, tk.END)
        self.volume_text.insert(tk.END, "\n".join(result_text))  
  
    def display_comparison(self):
        """顯示比較結果"""
        if not self.original_results or not self.volume_results:
            return
        
        result_text = []
        result_text.append("=" * 40)
        result_text.append("📊 策略比較分析")
        result_text.append("=" * 40)
        result_text.append("")
        
        # 獲利比較
        original_profit = self.original_results['total_profit']
        volume_profit = self.volume_results['total_profit']
        profit_improvement = volume_profit - original_profit
        
        result_text.append("💰 獲利比較:")
        result_text.append(f"   原本策略: {original_profit:>12,.0f} TWD")
        result_text.append(f"   增強策略: {volume_profit:>12,.0f} TWD")
        result_text.append(f"   改善幅度: {profit_improvement:>+12,.0f} TWD")
        
        if original_profit != 0:
            improvement_pct = (profit_improvement / abs(original_profit)) * 100
            result_text.append(f"   改善比例: {improvement_pct:>+12.1f}%")
        
        result_text.append("")
        
        # 交易次數比較
        result_text.append("📈 交易次數比較:")
        result_text.append(f"   原本策略: {self.original_results['total_trades']:>12} 次")
        result_text.append(f"   增強策略: {self.volume_results['total_trades']:>12} 次")
        trade_reduction = self.original_results['total_trades'] - self.volume_results['total_trades']
        result_text.append(f"   減少交易: {trade_reduction:>12} 次")
        result_text.append("")
        
        # 勝率比較
        result_text.append("🎯 勝率比較:")
        result_text.append(f"   原本策略: {self.original_results['success_rate']:>12.1f}%")
        result_text.append(f"   增強策略: {self.volume_results['success_rate']:>12.1f}%")
        rate_improvement = self.volume_results['success_rate'] - self.original_results['success_rate']
        result_text.append(f"   勝率改善: {rate_improvement:>+12.1f}%")
        result_text.append("")
        
        # 平均獲利比較
        result_text.append("💵 平均獲利比較:")
        result_text.append(f"   原本策略: {self.original_results['avg_profit']:>12,.0f} TWD")
        result_text.append(f"   增強策略: {self.volume_results['avg_profit']:>12,.0f} TWD")
        avg_improvement = self.volume_results['avg_profit'] - self.original_results['avg_profit']
        result_text.append(f"   平均改善: {avg_improvement:>+12,.0f} TWD")
        result_text.append("")
        
        # 成交量過濾效果
        result_text.append("🔍 成交量過濾效果:")
        total_signals = self.volume_results['confirmed_signals'] + self.volume_results['rejected_signals']
        filter_rate = (self.volume_results['rejected_signals'] / total_signals) * 100 if total_signals > 0 else 0
        result_text.append(f"   總信號數: {total_signals:>12}")
        result_text.append(f"   確認信號: {self.volume_results['confirmed_signals']:>12}")
        result_text.append(f"   拒絕信號: {self.volume_results['rejected_signals']:>12}")
        result_text.append(f"   過濾比例: {filter_rate:>12.1f}%")
        result_text.append(f"   信號強度: {self.volume_results['avg_signal_strength']:>12.1f}/100")
        result_text.append("")
        
        # 結論
        result_text.append("🎉 結論:")
        if profit_improvement > 0:
            result_text.append("   ✅ 成交量增強策略表現更好！")
            result_text.append("   📊 成功過濾假信號，提升獲利")
            result_text.append("")
            result_text.append("   🌟 主要改善:")
            result_text.append(f"   • 獲利提升 {improvement_pct:+.1f}%")
            result_text.append(f"   • 減少 {trade_reduction} 次不必要交易")
            result_text.append(f"   • 過濾掉 {filter_rate:.1f}% 的假信號")
        elif profit_improvement < 0:
            result_text.append("   ⚠️  原本策略表現更好")
            result_text.append("   🔧 建議調整成交量過濾參數")
        else:
            result_text.append("   🤝 兩種策略表現相同")
        
        result_text.append("")
        result_text.append("💡 成交量增強策略的優勢:")
        result_text.append("   • 有效過濾假突破信號")
        result_text.append("   • 提高單筆交易品質")
        result_text.append("   • 減少不必要的交易頻率")
        result_text.append("   • 基於成交量確認真實突破")
        result_text.append("   • 提供信號強度評分")
        
        self.comparison_text.delete(1.0, tk.END)
        self.comparison_text.insert(tk.END, "\n".join(result_text))
    
    def clear_all_text(self):
        """清空所有文本框"""
        self.original_text.delete(1.0, tk.END)
        self.volume_text.delete(1.0, tk.END)
        self.comparison_text.delete(1.0, tk.END)
    
    def update_progress(self, message):
        """更新進度"""
        self.progress_var.set(message)
    
    def display_error(self, error_msg):
        """顯示錯誤"""
        self.comparison_text.delete(1.0, tk.END)
        self.comparison_text.insert(tk.END, f"❌ 錯誤: {error_msg}")
        self.progress_var.set("測試失敗")
    
    def run(self):
        """運行GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    app = CorrectVolumeEnhancedMACDGUI()
    app.run()