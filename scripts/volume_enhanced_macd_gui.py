#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成交量增強MACD策略GUI測試工具
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

class VolumeEnhancedMACDGUI:
    """成交量增強MACD策略GUI"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.volume_enhanced = VolumeEnhancedMACDSignals()
        self.setup_gui()
        
        # 測試結果
        self.original_results = None
        self.volume_results = None
        self.df = None
    
    def setup_gui(self):
        """設置GUI"""
        self.root = tk.Tk()
        self.root.title("成交量增強MACD策略測試")
        self.root.geometry("1200x800")
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 標題
        title_label = ttk.Label(main_frame, text="🚀 BTC成交量增強MACD策略測試", 
                               font=('Arial', 18, 'bold'))
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
        original_frame = ttk.LabelFrame(results_frame, text="🔵 原始MACD策略", padding="10")
        original_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        self.original_text = scrolledtext.ScrolledText(original_frame, width=40, height=25, 
                                                      font=('Consolas', 9))
        self.original_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 成交量增強結果
        volume_frame = ttk.LabelFrame(results_frame, text="🟢 成交量增強MACD策略", padding="10")
        volume_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 5))
        
        self.volume_text = scrolledtext.ScrolledText(volume_frame, width=40, height=25, 
                                                    font=('Consolas', 9))
        self.volume_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 比較結果
        comparison_frame = ttk.LabelFrame(results_frame, text="📊 策略比較", padding="10")
        comparison_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        
        self.comparison_text = scrolledtext.ScrolledText(comparison_frame, width=40, height=25, 
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
                
                self.root.after(0, self.update_progress, "正在測試原始MACD策略...")
                
                # 測試原始MACD策略
                original_signals = calculate_basic_macd_signals(self.df)
                self.original_results = calculate_trade_performance(original_signals)
                
                self.root.after(0, self.display_original_results)
                self.root.after(0, self.update_progress, "正在測試成交量增強策略...")
                
                # 測試成交量增強策略
                volume_signals = self.volume_enhanced.detect_enhanced_signals(self.df)
                self.volume_results = self.calculate_volume_performance(volume_signals)
                
                self.root.after(0, self.display_volume_results)
                self.root.after(0, self.display_comparison)
                self.root.after(0, self.update_progress, "測試完成！")
                
            except Exception as e:
                error_msg = f"測試過程中發生錯誤: {e}"
                self.root.after(0, self.display_error, error_msg)
            finally:
                self.root.after(0, lambda: self.start_button.config(state='normal'))
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def calculate_volume_performance(self, signals_df: pd.DataFrame) -> Dict:
        """計算成交量增強策略表現"""
        if signals_df.empty:
            return {
                'total_trades': 0,
                'total_profit': 0,
                'success_rate': 0,
                'avg_profit': 0,
                'trade_pairs': [],
                'confirmed_signals': 0,
                'rejected_signals': 0,
                'avg_signal_strength': 0
            }
        
        # 基本交易表現
        base_performance = calculate_trade_performance(signals_df)
        
        # 額外統計
        confirmed_signals = len(signals_df[signals_df['volume_confirmed'] == True])
        rejected_signals = len(signals_df[signals_df['volume_confirmed'] == False])
        confirmed_df = signals_df[signals_df['volume_confirmed'] == True]
        avg_signal_strength = confirmed_df['signal_strength'].mean() if not confirmed_df.empty else 0
        
        base_performance.update({
            'confirmed_signals': confirmed_signals,
            'rejected_signals': rejected_signals,
            'avg_signal_strength': avg_signal_strength if not pd.isna(avg_signal_strength) else 0,
            'all_signals': signals_df
        })
        
        return base_performance    

    def display_original_results(self):
        """顯示原始MACD結果"""
        if not self.original_results:
            return
        
        result_text = []
        result_text.append("=" * 35)
        result_text.append("🔵 原始MACD策略結果")
        result_text.append("=" * 35)
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
            result_text.append("-" * 35)
            
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
        result_text.append("=" * 35)
        result_text.append("🟢 成交量增強MACD策略結果")
        result_text.append("=" * 35)
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
            result_text.append("-" * 35)
            
            for i, trade in enumerate(self.volume_results['trade_pairs'], 1):
                buy_time = trade['buy_time'].strftime('%m/%d %H:%M')
                sell_time = trade['sell_time'].strftime('%m/%d %H:%M')
                profit_color = "+" if trade['profit'] > 0 else ""
                
                result_text.append(f"交易 {i:2d}:")
                result_text.append(f"  買入: {buy_time} {trade['buy_price']:>8,.0f}")
                result_text.append(f"  賣出: {sell_time} {trade['sell_price']:>8,.0f}")
                result_text.append(f"  獲利: {profit_color}{trade['profit']:>8,.0f} TWD")
                result_text.append(f"  報酬: {profit_color}{trade['profit_pct']:>7.1f}%")
                
                # 顯示成交量信息
                if 'buy_volume_info' in trade:
                    result_text.append(f"  買入量: {trade.get('buy_volume_info', 'N/A')}")
                if 'sell_volume_info' in trade:
                    result_text.append(f"  賣出量: {trade.get('sell_volume_info', 'N/A')}")
                
                result_text.append("")
        else:
            result_text.append("📋 沒有完整的交易對")
        
        # 被拒絕的信號樣本
        if 'all_signals' in self.volume_results:
            rejected_signals = self.volume_results['all_signals'][
                self.volume_results['all_signals']['volume_confirmed'] == False
            ]
            
            if not rejected_signals.empty:
                result_text.append("❌ 被拒絕信號樣本:")
                result_text.append("-" * 35)
                
                # 顯示前5個被拒絕的信號
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
        result_text.append("=" * 35)
        result_text.append("📊 策略比較結果")
        result_text.append("=" * 35)
        result_text.append("")
        
        # 獲利比較
        original_profit = self.original_results['total_profit']
        volume_profit = self.volume_results['total_profit']
        profit_improvement = volume_profit - original_profit
        
        result_text.append("💰 獲利比較:")
        result_text.append(f"   原始策略: {original_profit:>10,.0f} TWD")
        result_text.append(f"   增強策略: {volume_profit:>10,.0f} TWD")
        result_text.append(f"   改善幅度: {profit_improvement:>+10,.0f} TWD")
        
        if original_profit != 0:
            improvement_pct = (profit_improvement / abs(original_profit)) * 100
            result_text.append(f"   改善比例: {improvement_pct:>+10.1f}%")
        
        result_text.append("")     
   
        # 交易次數比較
        result_text.append("📈 交易次數比較:")
        result_text.append(f"   原始策略: {self.original_results['total_trades']:>10} 次")
        result_text.append(f"   增強策略: {self.volume_results['total_trades']:>10} 次")
        result_text.append(f"   減少交易: {self.original_results['total_trades'] - self.volume_results['total_trades']:>10} 次")
        result_text.append("")
        
        # 勝率比較
        result_text.append("🎯 勝率比較:")
        result_text.append(f"   原始策略: {self.original_results['success_rate']:>10.1f}%")
        result_text.append(f"   增強策略: {self.volume_results['success_rate']:>10.1f}%")
        rate_improvement = self.volume_results['success_rate'] - self.original_results['success_rate']
        result_text.append(f"   勝率改善: {rate_improvement:>+10.1f}%")
        result_text.append("")
        
        # 平均獲利比較
        result_text.append("💵 平均獲利比較:")
        result_text.append(f"   原始策略: {self.original_results['avg_profit']:>10,.0f} TWD")
        result_text.append(f"   增強策略: {self.volume_results['avg_profit']:>10,.0f} TWD")
        avg_improvement = self.volume_results['avg_profit'] - self.original_results['avg_profit']
        result_text.append(f"   平均改善: {avg_improvement:>+10,.0f} TWD")
        result_text.append("")
        
        # 成交量過濾效果
        result_text.append("🔍 成交量過濾效果:")
        total_signals = self.volume_results['confirmed_signals'] + self.volume_results['rejected_signals']
        filter_rate = (self.volume_results['rejected_signals'] / total_signals) * 100 if total_signals > 0 else 0
        result_text.append(f"   總信號數: {total_signals:>10}")
        result_text.append(f"   確認信號: {self.volume_results['confirmed_signals']:>10}")
        result_text.append(f"   拒絕信號: {self.volume_results['rejected_signals']:>10}")
        result_text.append(f"   過濾比例: {filter_rate:>10.1f}%")
        result_text.append(f"   信號強度: {self.volume_results['avg_signal_strength']:>10.1f}/100")
        result_text.append("")
        
        # 結論
        result_text.append("🎉 結論:")
        if profit_improvement > 0:
            result_text.append("   ✅ 成交量增強策略表現更好！")
            result_text.append("   📊 成功過濾假信號，提升獲利")
        elif profit_improvement < 0:
            result_text.append("   ⚠️  原始策略表現更好")
            result_text.append("   🔧 建議調整成交量過濾參數")
        else:
            result_text.append("   🤝 兩種策略表現相同")
        
        result_text.append("")
        result_text.append("💡 成交量增強策略的優勢:")
        result_text.append("   • 有效過濾假突破信號")
        result_text.append("   • 提高單筆交易品質")
        result_text.append("   • 減少不必要的交易頻率")
        result_text.append("   • 基於成交量確認真實突破")
        
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
    app = VolumeEnhancedMACDGUI()
    app.run()