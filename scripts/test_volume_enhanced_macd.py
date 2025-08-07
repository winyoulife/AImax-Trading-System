#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試成交量增強MACD策略 vs 原始MACD策略
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
from src.core.improved_trading_signals import SignalDetectionEngine  # 原始MACD策略

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VolumeEnhancedMACDTester:
    """成交量增強MACD策略測試器"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.volume_enhanced = VolumeEnhancedMACDSignals()
        self.original_macd = SignalDetectionEngine()
        
        # 測試參數
        self.test_symbols = [
            'BTCTWD', 'ETHTWD', 'ADATWD', 'DOTTWD', 'LINKTWD',
            'LTCTWD', 'BCHTWD', 'XRPTWD', 'EOSTWD', 'TRXTWD'
        ]
        
        self.results = {
            'original': {},
            'volume_enhanced': {},
            'comparison': {}
        }
    
    def fetch_test_data(self, symbol: str, days: int = 90) -> pd.DataFrame:
        """獲取測試數據"""
        try:
            # 獲取更多數據以確保有足夠的歷史數據計算指標
            df = self.data_fetcher.fetch_data(symbol, '1h', limit=days * 24)
            
            if df is None or df.empty:
                logger.error(f"無法獲取 {symbol} 的數據")
                return pd.DataFrame()
            
            # 確保數據按時間排序
            df = df.sort_values('datetime').reset_index(drop=True)
            
            # 檢查必要的列
            required_cols = ['datetime', 'open', 'high', 'low', 'close', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.error(f"{symbol} 缺少必要的列: {missing_cols}")
                return pd.DataFrame()
            
            logger.info(f"成功獲取 {symbol} 數據: {len(df)} 筆記錄")
            return df
            
        except Exception as e:
            logger.error(f"獲取 {symbol} 數據時發生錯誤: {e}")
            return pd.DataFrame()
    
    def test_original_macd(self, df: pd.DataFrame, symbol: str) -> Dict:
        """測試原始MACD策略"""
        try:
            # 使用原始MACD策略檢測信號
            signals_df = self.original_macd.detect_smart_balanced_signals(df)
            
            if signals_df.empty:
                return {
                    'symbol': symbol,
                    'total_trades': 0,
                    'buy_signals': 0,
                    'sell_signals': 0,
                    'total_profit': 0,
                    'trade_pairs': [],
                    'success_rate': 0,
                    'avg_profit': 0
                }
            
            # 計算交易對和利潤
            buy_signals = signals_df[signals_df['signal_type'] == 'buy'].copy()
            sell_signals = signals_df[signals_df['signal_type'] == 'sell'].copy()
            
            trade_pairs = []
            total_profit = 0
            
            # 配對買賣信號
            for _, buy_signal in buy_signals.iterrows():
                # 找到對應的賣出信號
                matching_sells = sell_signals[
                    (sell_signals['trade_sequence'] == buy_signal['trade_sequence']) |
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
                'symbol': symbol,
                'total_trades': len(trade_pairs),
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'total_profit': total_profit,
                'trade_pairs': trade_pairs,
                'success_rate': success_rate,
                'avg_profit': avg_profit
            }
            
        except Exception as e:
            logger.error(f"測試原始MACD策略時發生錯誤 ({symbol}): {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def test_volume_enhanced_macd(self, df: pd.DataFrame, symbol: str) -> Dict:
        """測試成交量增強MACD策略"""
        try:
            # 使用成交量增強MACD策略檢測信號
            signals_df = self.volume_enhanced.detect_enhanced_signals(df)
            
            if signals_df.empty:
                return {
                    'symbol': symbol,
                    'total_trades': 0,
                    'buy_signals': 0,
                    'sell_signals': 0,
                    'confirmed_signals': 0,
                    'rejected_signals': 0,
                    'total_profit': 0,
                    'trade_pairs': [],
                    'success_rate': 0,
                    'avg_profit': 0,
                    'avg_signal_strength': 0
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
                # 找到對應的賣出信號
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
                'symbol': symbol,
                'total_trades': len(trade_pairs),
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'confirmed_signals': confirmed_signals,
                'rejected_signals': rejected_signals,
                'total_profit': total_profit,
                'trade_pairs': trade_pairs,
                'success_rate': success_rate,
                'avg_profit': avg_profit,
                'avg_signal_strength': avg_signal_strength
            }
            
        except Exception as e:
            logger.error(f"測試成交量增強MACD策略時發生錯誤 ({symbol}): {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def run_comparison_test(self, progress_callback=None):
        """運行比較測試"""
        logger.info("開始成交量增強MACD策略比較測試")
        
        total_symbols = len(self.test_symbols)
        
        for i, symbol in enumerate(self.test_symbols):
            if progress_callback:
                progress_callback(f"測試 {symbol}...", (i / total_symbols) * 100)
            
            logger.info(f"測試 {symbol} ({i+1}/{total_symbols})")
            
            # 獲取數據
            df = self.fetch_test_data(symbol)
            if df.empty:
                continue
            
            # 測試原始MACD策略
            original_result = self.test_original_macd(df, symbol)
            self.results['original'][symbol] = original_result
            
            # 測試成交量增強MACD策略
            volume_result = self.test_volume_enhanced_macd(df, symbol)
            self.results['volume_enhanced'][symbol] = volume_result
            
            # 比較結果
            if 'error' not in original_result and 'error' not in volume_result:
                comparison = {
                    'symbol': symbol,
                    'original_profit': original_result['total_profit'],
                    'volume_profit': volume_result['total_profit'],
                    'profit_improvement': volume_result['total_profit'] - original_result['total_profit'],
                    'profit_improvement_pct': ((volume_result['total_profit'] - original_result['total_profit']) / abs(original_result['total_profit'])) * 100 if original_result['total_profit'] != 0 else 0,
                    'original_trades': original_result['total_trades'],
                    'volume_trades': volume_result['total_trades'],
                    'original_success_rate': original_result['success_rate'],
                    'volume_success_rate': volume_result['success_rate'],
                    'signals_rejected': volume_result.get('rejected_signals', 0),
                    'avg_signal_strength': volume_result.get('avg_signal_strength', 0)
                }
                self.results['comparison'][symbol] = comparison
        
        if progress_callback:
            progress_callback("測試完成！", 100)
        
        logger.info("成交量增強MACD策略比較測試完成")
    
    def generate_summary_report(self) -> str:
        """生成摘要報告"""
        report = []
        report.append("=" * 80)
        report.append("成交量增強MACD策略 vs 原始MACD策略 比較報告")
        report.append("=" * 80)
        
        if not self.results['comparison']:
            report.append("沒有可比較的結果")
            return "\n".join(report)
        
        # 總體統計
        comparisons = list(self.results['comparison'].values())
        
        total_original_profit = sum(c['original_profit'] for c in comparisons)
        total_volume_profit = sum(c['volume_profit'] for c in comparisons)
        total_improvement = total_volume_profit - total_original_profit
        
        avg_original_success = np.mean([c['original_success_rate'] for c in comparisons])
        avg_volume_success = np.mean([c['volume_success_rate'] for c in comparisons])
        
        total_rejected = sum(c['signals_rejected'] for c in comparisons)
        avg_signal_strength = np.mean([c['avg_signal_strength'] for c in comparisons if c['avg_signal_strength'] > 0])
        
        report.append(f"\n📊 總體表現比較:")
        report.append(f"原始MACD總獲利: {total_original_profit:,.0f} TWD")
        report.append(f"成交量增強總獲利: {total_volume_profit:,.0f} TWD")
        report.append(f"獲利改善: {total_improvement:,.0f} TWD ({(total_improvement/abs(total_original_profit)*100):+.1f}%)")
        report.append(f"")
        report.append(f"平均勝率比較:")
        report.append(f"原始MACD: {avg_original_success:.1f}%")
        report.append(f"成交量增強: {avg_volume_success:.1f}%")
        report.append(f"勝率改善: {avg_volume_success - avg_original_success:+.1f}%")
        report.append(f"")
        report.append(f"成交量過濾效果:")
        report.append(f"總共拒絕信號: {total_rejected} 個")
        report.append(f"平均信號強度: {avg_signal_strength:.1f}/100")
        
        # 個別交易對表現
        report.append(f"\n📈 個別交易對表現:")
        report.append(f"{'交易對':<10} {'原始獲利':<12} {'增強獲利':<12} {'改善':<10} {'改善%':<8} {'拒絕信號':<8}")
        report.append("-" * 70)
        
        for comparison in sorted(comparisons, key=lambda x: x['profit_improvement'], reverse=True):
            symbol = comparison['symbol']
            original = comparison['original_profit']
            volume = comparison['volume_profit']
            improvement = comparison['profit_improvement']
            improvement_pct = comparison['profit_improvement_pct']
            rejected = comparison['signals_rejected']
            
            report.append(f"{symbol:<10} {original:>10,.0f} {volume:>10,.0f} {improvement:>8,.0f} {improvement_pct:>6.1f}% {rejected:>6}")
        
        # 成功案例分析
        successful_improvements = [c for c in comparisons if c['profit_improvement'] > 0]
        if successful_improvements:
            report.append(f"\n🎯 成功改善案例 ({len(successful_improvements)}/{len(comparisons)}):")
            for case in successful_improvements[:5]:  # 顯示前5個最佳案例
                report.append(f"  {case['symbol']}: +{case['profit_improvement']:,.0f} TWD ({case['profit_improvement_pct']:+.1f}%)")
        
        # 需要改進的案例
        need_improvement = [c for c in comparisons if c['profit_improvement'] < 0]
        if need_improvement:
            report.append(f"\n⚠️  需要改進案例 ({len(need_improvement)}/{len(comparisons)}):")
            for case in sorted(need_improvement, key=lambda x: x['profit_improvement'])[:3]:
                report.append(f"  {case['symbol']}: {case['profit_improvement']:,.0f} TWD ({case['profit_improvement_pct']:+.1f}%)")
        
        return "\n".join(report)

class VolumeEnhancedMACDTestGUI:
    """成交量增強MACD測試GUI"""
    
    def __init__(self):
        self.tester = VolumeEnhancedMACDTester()
        self.setup_gui()
    
    def setup_gui(self):
        """設置GUI"""
        self.root = tk.Tk()
        self.root.title("成交量增強MACD策略測試")
        self.root.geometry("1000x700")
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 標題
        title_label = ttk.Label(main_frame, text="成交量增強MACD策略 vs 原始MACD策略", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 控制面板
        control_frame = ttk.LabelFrame(main_frame, text="測試控制", padding="10")
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 開始測試按鈕
        self.start_button = ttk.Button(control_frame, text="開始比較測試", 
                                      command=self.start_test, style='Accent.TButton')
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # 進度條
        self.progress_var = tk.StringVar(value="準備就緒")
        self.progress_label = ttk.Label(control_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=1, padx=(10, 0))
        
        self.progress_bar = ttk.Progressbar(control_frame, length=300, mode='determinate')
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 結果顯示區域
        result_frame = ttk.LabelFrame(main_frame, text="測試結果", padding="10")
        result_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # 結果文本框
        self.result_text = scrolledtext.ScrolledText(result_frame, width=100, height=30, 
                                                    font=('Consolas', 10))
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置網格權重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
    
    def update_progress(self, message, progress):
        """更新進度"""
        self.progress_var.set(message)
        self.progress_bar['value'] = progress
        self.root.update_idletasks()
    
    def start_test(self):
        """開始測試"""
        self.start_button.config(state='disabled')
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "開始成交量增強MACD策略比較測試...\n\n")
        
        # 在新線程中運行測試
        def run_test():
            try:
                self.tester.run_comparison_test(self.update_progress)
                
                # 生成報告
                report = self.tester.generate_summary_report()
                
                # 在主線程中更新GUI
                self.root.after(0, self.display_results, report)
                
            except Exception as e:
                error_msg = f"測試過程中發生錯誤: {e}"
                self.root.after(0, self.display_error, error_msg)
            finally:
                self.root.after(0, lambda: self.start_button.config(state='normal'))
        
        threading.Thread(target=run_test, daemon=True).start()
    
    def display_results(self, report):
        """顯示結果"""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, report)
        self.progress_var.set("測試完成")
    
    def display_error(self, error_msg):
        """顯示錯誤"""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"錯誤: {error_msg}")
        self.progress_var.set("測試失敗")
    
    def run(self):
        """運行GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    # 運行GUI測試
    app = VolumeEnhancedMACDTestGUI()
    app.run()