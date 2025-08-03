#!/usr/bin/env python3
"""
多時間週期獨立確認MACD回測分析器
1小時MACD金叉/死叉 + 短時間週期動態追蹤
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import asyncio
import threading
import json
import os
from datetime import datetime
import sys
import os

# 添加項目根目錄到Python路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.live_macd_service import LiveMACDService
from src.core.multi_timeframe_trading_signals import detect_multi_timeframe_trading_signals

class MultiTimeframeMACDBacktestGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("多時間週期獨立確認MACD回測分析器")
        self.root.geometry("1400x900")
        
        # 數據服務
        self.macd_service = LiveMACDService()
        
        # 數據存儲
        self.hourly_data = None
        self.timeframe_data = {
            '30m': None,
            '15m': None,
            '5m': None
        }
        self.signals_data = {
            '1h': pd.DataFrame(),
            '30m': pd.DataFrame(),
            '15m': pd.DataFrame(),
            '5m': pd.DataFrame()
        }
        self.statistics = {}
        
        # 顏色配置
        self.colors = {
            '1h_buy': '#FFE6E6',      # 淡紅色
            '1h_sell': '#FFCCCC',     # 深一點的紅色
            '30m_buy': '#FFFFE6',     # 淡黃色
            '30m_sell': '#FFFFCC',    # 深一點的黃色
            '15m_buy': '#E6FFE6',     # 淡綠色
            '15m_sell': '#CCFFCC',    # 深一點的綠色
            '5m_buy': '#E6E6FF',      # 淡藍色
            '5m_sell': '#CCCCFF'      # 深一點的藍色
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """設置用戶界面"""
        # 主標題
        title_frame = tk.Frame(self.root)
        title_frame.pack(fill='x', padx=10, pady=5)
        
        title_label = tk.Label(title_frame, text="🚀 多時間週期獨立確認MACD回測分析器", 
                              font=('Arial', 16, 'bold'))
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame, text="📋 1小時MACD金叉/死叉 + 短時間週期動態追蹤", 
                                 font=('Arial', 12))
        subtitle_label.pack()
        
        # 控制面板
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # 確認超時時間選擇
        tk.Label(control_frame, text="確認超時時間:").pack(side='left', padx=5)
        self.timeout_var = tk.StringVar(value="2")
        timeout_combo = ttk.Combobox(control_frame, textvariable=self.timeout_var, 
                                    values=["1", "2", "3", "4"], width=10)
        timeout_combo.pack(side='left', padx=5)
        
        # 按鈕
        tk.Button(control_frame, text="開始回測", command=self.start_backtest).pack(side='left', padx=10)
        tk.Button(control_frame, text="保存數據", command=self.save_data).pack(side='left', padx=5)
        tk.Button(control_frame, text="清空數據", command=self.clear_data).pack(side='left', padx=5)
        
        # 狀態顯示
        self.status_var = tk.StringVar(value="就緒")
        status_label = tk.Label(control_frame, textvariable=self.status_var, 
                               font=('Arial', 10, 'bold'), fg='blue')
        status_label.pack(side='right', padx=10)
        
        # 統計信息
        stats_frame = tk.Frame(self.root)
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=4, font=('Arial', 10))
        self.stats_text.pack(fill='x')
        
        # 四個時間週期的表格
        self.create_timeframe_tables()
        
    def create_timeframe_tables(self):
        """創建四個時間週期的表格"""
        # 表格容器 - 使用Grid布局，2行2列
        tables_frame = tk.Frame(self.root)
        tables_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 第一行：1小時和30分鐘
        # 1小時表格
        hour_frame = tk.LabelFrame(tables_frame, text="1小時 (MACD金叉/死叉)", 
                                  font=('Arial', 12, 'bold'))
        hour_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        self.hour_tree = ttk.Treeview(hour_frame, columns=('時間', '價格', '信號類型', 'MACD柱狀圖'), 
                                     show='headings', height=12)
        self.hour_tree.heading('時間', text='時間')
        self.hour_tree.heading('價格', text='價格')
        self.hour_tree.heading('信號類型', text='信號類型')
        self.hour_tree.heading('MACD柱狀圖', text='MACD柱狀圖')
        self.hour_tree.column('時間', width=150)
        self.hour_tree.column('價格', width=100)
        self.hour_tree.column('信號類型', width=80)
        self.hour_tree.column('MACD柱狀圖', width=100)
        
        hour_scrollbar = ttk.Scrollbar(hour_frame, orient='vertical', command=self.hour_tree.yview)
        self.hour_tree.configure(yscrollcommand=hour_scrollbar.set)
        self.hour_tree.pack(side='left', fill='both', expand=True)
        hour_scrollbar.pack(side='right', fill='y')
        
        # 30分鐘表格
        thirty_frame = tk.LabelFrame(tables_frame, text="30分鐘 (動態追蹤)", 
                                    font=('Arial', 12, 'bold'))
        thirty_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        
        self.thirty_tree = ttk.Treeview(thirty_frame, columns=('時間', '價格', '信號類型', '交易序號'), 
                                       show='headings', height=12)
        self.thirty_tree.heading('時間', text='時間')
        self.thirty_tree.heading('價格', text='價格')
        self.thirty_tree.heading('信號類型', text='信號類型')
        self.thirty_tree.heading('交易序號', text='交易序號')
        self.thirty_tree.column('時間', width=150)
        self.thirty_tree.column('價格', width=100)
        self.thirty_tree.column('信號類型', width=80)
        self.thirty_tree.column('交易序號', width=80)
        
        thirty_scrollbar = ttk.Scrollbar(thirty_frame, orient='vertical', command=self.thirty_tree.yview)
        self.thirty_tree.configure(yscrollcommand=thirty_scrollbar.set)
        self.thirty_tree.pack(side='left', fill='both', expand=True)
        thirty_scrollbar.pack(side='right', fill='y')
        
        # 第二行：15分鐘和5分鐘
        # 15分鐘表格
        fifteen_frame = tk.LabelFrame(tables_frame, text="15分鐘 (動態追蹤)", 
                                     font=('Arial', 12, 'bold'))
        fifteen_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        
        self.fifteen_tree = ttk.Treeview(fifteen_frame, columns=('時間', '價格', '信號類型', '交易序號'), 
                                        show='headings', height=12)
        self.fifteen_tree.heading('時間', text='時間')
        self.fifteen_tree.heading('價格', text='價格')
        self.fifteen_tree.heading('信號類型', text='信號類型')
        self.fifteen_tree.heading('交易序號', text='交易序號')
        self.fifteen_tree.column('時間', width=150)
        self.fifteen_tree.column('價格', width=100)
        self.fifteen_tree.column('信號類型', width=80)
        self.fifteen_tree.column('交易序號', width=80)
        
        fifteen_scrollbar = ttk.Scrollbar(fifteen_frame, orient='vertical', command=self.fifteen_tree.yview)
        self.fifteen_tree.configure(yscrollcommand=fifteen_scrollbar.set)
        self.fifteen_tree.pack(side='left', fill='both', expand=True)
        fifteen_scrollbar.pack(side='right', fill='y')
        
        # 5分鐘表格
        five_frame = tk.LabelFrame(tables_frame, text="5分鐘 (動態追蹤)", 
                                  font=('Arial', 12, 'bold'))
        five_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        
        self.five_tree = ttk.Treeview(five_frame, columns=('時間', '價格', '信號類型', '交易序號'), 
                                     show='headings', height=12)
        self.five_tree.heading('時間', text='時間')
        self.five_tree.heading('價格', text='價格')
        self.five_tree.heading('信號類型', text='信號類型')
        self.five_tree.heading('交易序號', text='交易序號')
        self.five_tree.column('時間', width=150)
        self.five_tree.column('價格', width=100)
        self.five_tree.column('信號類型', width=80)
        self.five_tree.column('交易序號', width=80)
        
        five_scrollbar = ttk.Scrollbar(five_frame, orient='vertical', command=self.five_tree.yview)
        self.five_tree.configure(yscrollcommand=five_scrollbar.set)
        self.five_tree.pack(side='left', fill='both', expand=True)
        five_scrollbar.pack(side='right', fill='y')
        
        # 配置Grid權重，讓表格能夠均勻分布
        tables_frame.grid_rowconfigure(0, weight=1)
        tables_frame.grid_rowconfigure(1, weight=1)
        tables_frame.grid_columnconfigure(0, weight=1)
        tables_frame.grid_columnconfigure(1, weight=1)
        
    def start_backtest(self):
        """開始回測"""
        self.status_var.set("正在獲取數據...")
        self.root.update()
        
        # 在新線程中執行數據獲取
        thread = threading.Thread(target=self.run_backtest)
        thread.daemon = True
        thread.start()
        
    def run_backtest(self):
        """執行回測"""
        try:
            # 創建新的事件循環
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 獲取1小時數據
                self.status_var.set("正在獲取1小時MACD數據...")
                self.root.update()
                
                self.hourly_data = loop.run_until_complete(self.macd_service._fetch_klines("btctwd", "60", 400))  # 獲取更多數據以確保有足夠的歷史數據
                if self.hourly_data is None or self.hourly_data.empty:
                    raise Exception("無法獲取1小時數據")
                
                # 確保datetime列存在
                if 'datetime' not in self.hourly_data.columns and 'timestamp' in self.hourly_data.columns:
                    self.hourly_data['datetime'] = pd.to_datetime(self.hourly_data['timestamp'], unit='s')
                
                # 計算MACD
                self.hourly_data = self.macd_service._calculate_macd(self.hourly_data, 12, 26, 9)
                
                # 獲取短時間週期數據
                timeframes = {'30m': '30', '15m': '15', '5m': '5'}
                
                for timeframe, minutes in timeframes.items():
                    self.status_var.set(f"正在獲取{timeframe}數據...")
                    self.root.update()
                    
                    df = loop.run_until_complete(self.macd_service._fetch_klines("btctwd", minutes, 2400))  # 獲取更多數據以確保有足夠的歷史數據
                    if df is not None and not df.empty:
                        # 確保datetime列存在
                        if 'datetime' not in df.columns and 'timestamp' in df.columns:
                            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
                        
                        df = self.macd_service._calculate_macd(df, 12, 26, 9)
                        self.timeframe_data[timeframe] = df
                
                # 檢測信號
                self.status_var.set("正在檢測多時間週期信號...")
                self.root.update()
                
                confirmation_timeout = int(self.timeout_var.get())
                self.signals_data, self.statistics = detect_multi_timeframe_trading_signals(
                    self.hourly_data, self.timeframe_data, confirmation_timeout
                )
                
                # 更新界面
                self.root.after(0, self.update_tables)
                self.root.after(0, self.update_statistics)
                self.root.after(0, lambda: self.status_var.set("數據載入完成"))
                
            finally:
                # 關閉aiohttp會話
                if self.macd_service.session:
                    loop.run_until_complete(self.macd_service.session.close())
                loop.close()
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self.status_var.set(f"錯誤: {error_msg}"))
            self.root.after(0, lambda: messagebox.showerror("錯誤", f"回測失敗: {error_msg}"))
    
    def update_tables(self):
        """更新表格數據"""
        # 清空所有表格
        for tree in [self.hour_tree, self.thirty_tree, self.fifteen_tree, self.five_tree]:
            for item in tree.get_children():
                tree.delete(item)
        
        # 更新1小時表格
        if not self.signals_data['1h'].empty:
            for _, row in self.signals_data['1h'].iterrows():
                signal_type = row['signal_type']
                color_key = f"1h_{signal_type}"
                color = self.colors.get(color_key, 'white')
                
                item = self.hour_tree.insert('', 'end', values=(
                    row['datetime'].strftime('%Y/%m/%d %H:%M'),
                    f"{row['close']:,.0f}",
                    signal_type,
                    f"{row['macd_hist']:.2f}"
                ))
                
                # 設置顏色
                self.hour_tree.tag_configure(color_key, background=color)
                self.hour_tree.item(item, tags=(color_key,))
        
        # 更新短時間週期表格
        timeframe_trees = {
            '30m': self.thirty_tree,
            '15m': self.fifteen_tree,
            '5m': self.five_tree
        }
        
        for timeframe, tree in timeframe_trees.items():
            if not self.signals_data[timeframe].empty:
                for _, row in self.signals_data[timeframe].iterrows():
                    signal_type = row['signal_type']
                    color_key = f"{timeframe}_{signal_type}"
                    color = self.colors.get(color_key, 'white')
                    
                    item = tree.insert('', 'end', values=(
                        row['datetime'].strftime('%Y/%m/%d %H:%M'),
                        f"{row['close']:,.0f}",
                        signal_type,
                        row['trade_sequence'] if row['trade_sequence'] > 0 else ''
                    ))
                    
                    # 設置顏色
                    tree.tag_configure(color_key, background=color)
                    tree.item(item, tags=(color_key,))
    
    def update_statistics(self):
        """更新統計信息"""
        stats = self.statistics
        current_status = stats.get('current_status', {})
        
        stats_text = f"""
總交易次數: {stats.get('total_trades', 0)} | 買進次數: {stats.get('buy_count', 0)} | 賣出次數: {stats.get('sell_count', 0)}
當前狀態: {'持倉' if current_status.get('current_position') == 1 else '空倉'} | 交易序號: {current_status.get('trade_sequence', 0)}
等待確認: {'是' if current_status.get('waiting_for_confirmation') else '否'} | 觀察中: {'是' if current_status.get('is_observing') else '否'}
1小時信號: {current_status.get('hourly_signal', '無')}
        """
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
        
        # 計算總利潤
        total_profit = sum(trade['profit'] for trade in stats.get('trade_pairs', []))
        if stats.get('trade_pairs'):
            profit_text = f"\n總利潤: {total_profit:,.0f} | 平均利潤: {total_profit/len(stats['trade_pairs']):,.0f}"
            self.stats_text.insert(tk.END, profit_text)
    
    def save_data(self):
        """保存數據"""
        if not self.signals_data['1h'].empty or not any(not df.empty for df in self.signals_data.values()):
            messagebox.showwarning("警告", "沒有數據可保存")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存CSV文件
        csv_filename = f"AImax/data/multi_timeframe_macd_7day_backtest_{timestamp}.csv"
        
        # 合併所有信號數據
        all_signals = []
        for timeframe, df in self.signals_data.items():
            if not df.empty:
                df_copy = df.copy()
                df_copy['timeframe'] = timeframe
                all_signals.append(df_copy)
        
        if all_signals:
            combined_df = pd.concat(all_signals, ignore_index=True)
            combined_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
        
        # 保存統計信息
        stats_filename = f"AImax/data/multi_timeframe_macd_stats_{timestamp}.json"
        with open(stats_filename, 'w', encoding='utf-8') as f:
            json.dump(self.statistics, f, ensure_ascii=False, indent=2, default=str)
        
        messagebox.showinfo("成功", f"數據已保存:\n{csv_filename}\n{stats_filename}")
    
    def clear_data(self):
        """清空數據"""
        self.hourly_data = None
        self.timeframe_data = {'30m': None, '15m': None, '5m': None}
        self.signals_data = {'1h': pd.DataFrame(), '30m': pd.DataFrame(), '15m': pd.DataFrame(), '5m': pd.DataFrame()}
        self.statistics = {}
        
        self.update_tables()
        self.update_statistics()
        self.status_var.set("數據已清空")
    
    def run(self):
        """運行GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    print("🚀 啟動多時間週期獨立確認MACD回測分析器...")
    print("📋 1小時MACD金叉/死叉 + 短時間週期動態追蹤")
    print("🎯 四個獨立時間週期比較分析")
    
    app = MultiTimeframeMACDBacktestGUI()
    app.run() 