#!/usr/bin/env python3
"""
多時間框架MACD回測GUI - 整合原始1小時邏輯
基於improved_macd_backtest_gui.py的1小時邏輯，添加多時間框架動態追蹤
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import threading
from datetime import datetime, timedelta
import json
import pandas as pd

# 導入核心模組
from src.data.live_macd_service import LiveMACDService
from src.core.improved_trading_signals import detect_improved_trading_signals
from src.core.multi_timeframe_trading_signals import detect_multi_timeframe_trading_signals

class MultiTimeframeMACDBacktestGUI:
    """多時間框架MACD回測GUI - 整合原始1小時邏輯"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("多時間框架MACD回測分析器 - 整合原始1小時邏輯")
        self.root.geometry("1800x1200")
        self.root.configure(bg='#f0f0f0')
        
        # 數據存儲
        self.hourly_data = None
        self.hourly_statistics = None
        self.multi_timeframe_data = None
        self.multi_timeframe_statistics = None
        self.multi_timeframe_tracker = None  # 存儲tracker對象
        
        # 設置樣式
        self.setup_styles()
        
        # 創建界面
        self.create_widgets()
        
        # 自動載入數據
        self.load_data()
        
        # 初始化多時間框架狀態顯示
        self.update_multi_timeframe_status(None)
    
    def setup_styles(self):
        """設置GUI樣式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置樣式
        style.configure('Title.TLabel', 
                       background='#f0f0f0', 
                       foreground='#000080', 
                       font=('Arial', 16, 'bold'))
        
        style.configure('Header.TLabel', 
                       background='#f0f0f0', 
                       foreground='#008000', 
                       font=('Arial', 12, 'bold'))
        
        style.configure('Data.TLabel', 
                       background='#f0f0f0', 
                       foreground='#333333', 
                       font=('Consolas', 10))
        
        style.configure('Custom.TButton',
                       background='#e0e0e0',
                       foreground='#000000',
                       font=('Arial', 10))
        
        style.configure('Status.TLabel',
                       background='#f0f0f0',
                       foreground='#0066cc',
                       font=('Arial', 11, 'bold'))
    
    def create_widgets(self):
        """創建GUI組件"""
        # 主標題
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(fill='x', padx=10, pady=5)
        
        title_label = ttk.Label(title_frame, 
                               text="📈 多時間框架MACD回測分析器 - 整合原始1小時邏輯", 
                               style='Title.TLabel')
        title_label.pack(side='left')
        
        # 控制面板
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(fill='x', padx=10, pady=5)
        
        refresh_btn = ttk.Button(control_frame, text="🔄 重新載入", 
                               command=self.load_data, style='Custom.TButton')
        refresh_btn.pack(side='left', padx=5)
        
        backtest_btn = ttk.Button(control_frame, text="🎯 多時間框架回測", 
                                command=self.run_backtest, style='Custom.TButton')
        backtest_btn.pack(side='left', padx=5)
        
        save_btn = ttk.Button(control_frame, text="💾 導出數據", 
                            command=self.save_data, style='Custom.TButton')
        save_btn.pack(side='left', padx=5)
        
        # 狀態標籤
        self.status_label = ttk.Label(control_frame, text="準備就緒", style='Data.TLabel')
        self.status_label.pack(side='right', padx=5)
        
        # 創建2x2網格布局
        grid_frame = tk.Frame(self.root, bg='#f0f0f0')
        grid_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 1小時原始邏輯區域 (左上)
        hourly_frame = tk.LabelFrame(grid_frame, text="1小時原始邏輯 (improved_macd_backtest_gui.py)", 
                                   bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        hourly_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        # 1小時統計
        self.hourly_stats_text = tk.Text(hourly_frame, height=4, bg='#ffffff', fg='#006400',
                                        font=('Consolas', 8), wrap='word')
        self.hourly_stats_text.pack(fill='x', padx=5, pady=5)
        
        # 多時間框架狀態顯示
        status_frame = tk.LabelFrame(hourly_frame, text="多時間框架狀態", 
                                   bg='#f0f0f0', fg='#800080', font=('Arial', 9, 'bold'))
        status_frame.pack(fill='x', padx=5, pady=2)
        
        self.multi_status_text = tk.Text(status_frame, height=3, bg='#fff8dc', fg='#800080',
                                        font=('Consolas', 8), wrap='word')
        self.multi_status_text.pack(fill='x', padx=3, pady=3)
        
        # 1小時表格
        hourly_table_frame = tk.Frame(hourly_frame)
        hourly_table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        columns = ('時間', '價格', '柱狀圖', 'MACD線', '信號線', '交易信號', '持倉狀態')
        self.hourly_tree = ttk.Treeview(hourly_table_frame, columns=columns, show='headings', height=15)
        
        self.hourly_tree.heading('時間', text='時間')
        self.hourly_tree.heading('價格', text='價格')
        self.hourly_tree.heading('柱狀圖', text='柱狀圖')
        self.hourly_tree.heading('MACD線', text='MACD線')
        self.hourly_tree.heading('信號線', text='信號線')
        self.hourly_tree.heading('交易信號', text='交易信號')
        self.hourly_tree.heading('持倉狀態', text='持倉狀態')
        
        self.hourly_tree.column('時間', width=120)
        self.hourly_tree.column('價格', width=80)
        self.hourly_tree.column('柱狀圖', width=70)
        self.hourly_tree.column('MACD線', width=70)
        self.hourly_tree.column('信號線', width=70)
        self.hourly_tree.column('交易信號', width=80)
        self.hourly_tree.column('持倉狀態', width=70)
        
        hourly_scrollbar = ttk.Scrollbar(hourly_table_frame, orient='vertical', command=self.hourly_tree.yview)
        self.hourly_tree.configure(yscrollcommand=hourly_scrollbar.set)
        
        self.hourly_tree.pack(side='left', fill='both', expand=True)
        hourly_scrollbar.pack(side='right', fill='y')
        
        # 30分鐘動態追蹤區域 (右上)
        thirty_frame = tk.LabelFrame(grid_frame, text="30分鐘動態追蹤", 
                                   bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        thirty_frame.grid(row=0, column=1, sticky='nsew', padx=5, pady=5)
        
        self.thirty_tree = ttk.Treeview(thirty_frame, columns=columns, show='headings', height=15)
        
        self.thirty_tree.heading('時間', text='時間')
        self.thirty_tree.heading('價格', text='價格')
        self.thirty_tree.heading('柱狀圖', text='柱狀圖')
        self.thirty_tree.heading('MACD線', text='MACD線')
        self.thirty_tree.heading('信號線', text='信號線')
        self.thirty_tree.heading('交易信號', text='交易信號')
        self.thirty_tree.heading('持倉狀態', text='持倉狀態')
        
        self.thirty_tree.column('時間', width=120)
        self.thirty_tree.column('價格', width=80)
        self.thirty_tree.column('柱狀圖', width=70)
        self.thirty_tree.column('MACD線', width=70)
        self.thirty_tree.column('信號線', width=70)
        self.thirty_tree.column('交易信號', width=80)
        self.thirty_tree.column('持倉狀態', width=70)
        
        thirty_scrollbar = ttk.Scrollbar(thirty_frame, orient='vertical', command=self.thirty_tree.yview)
        self.thirty_tree.configure(yscrollcommand=thirty_scrollbar.set)
        
        self.thirty_tree.pack(side='left', fill='both', expand=True)
        thirty_scrollbar.pack(side='right', fill='y')
        
        # 15分鐘動態追蹤區域 (左下)
        fifteen_frame = tk.LabelFrame(grid_frame, text="15分鐘動態追蹤", 
                                    bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        fifteen_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        
        self.fifteen_tree = ttk.Treeview(fifteen_frame, columns=columns, show='headings', height=15)
        
        self.fifteen_tree.heading('時間', text='時間')
        self.fifteen_tree.heading('價格', text='價格')
        self.fifteen_tree.heading('柱狀圖', text='柱狀圖')
        self.fifteen_tree.heading('MACD線', text='MACD線')
        self.fifteen_tree.heading('信號線', text='信號線')
        self.fifteen_tree.heading('交易信號', text='交易信號')
        self.fifteen_tree.heading('持倉狀態', text='持倉狀態')
        
        self.fifteen_tree.column('時間', width=120)
        self.fifteen_tree.column('價格', width=80)
        self.fifteen_tree.column('柱狀圖', width=70)
        self.fifteen_tree.column('MACD線', width=70)
        self.fifteen_tree.column('信號線', width=70)
        self.fifteen_tree.column('交易信號', width=80)
        self.fifteen_tree.column('持倉狀態', width=70)
        
        fifteen_scrollbar = ttk.Scrollbar(fifteen_frame, orient='vertical', command=self.fifteen_tree.yview)
        self.fifteen_tree.configure(yscrollcommand=fifteen_scrollbar.set)
        
        self.fifteen_tree.pack(side='left', fill='both', expand=True)
        fifteen_scrollbar.pack(side='right', fill='y')
        
        # 5分鐘動態追蹤區域 (右下)
        five_frame = tk.LabelFrame(grid_frame, text="5分鐘動態追蹤", 
                                 bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        five_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=5)
        
        self.five_tree = ttk.Treeview(five_frame, columns=columns, show='headings', height=15)
        
        self.five_tree.heading('時間', text='時間')
        self.five_tree.heading('價格', text='價格')
        self.five_tree.heading('柱狀圖', text='柱狀圖')
        self.five_tree.heading('MACD線', text='MACD線')
        self.five_tree.heading('信號線', text='信號線')
        self.five_tree.heading('交易信號', text='交易信號')
        self.five_tree.heading('持倉狀態', text='持倉狀態')
        
        self.five_tree.column('時間', width=120)
        self.five_tree.column('價格', width=80)
        self.five_tree.column('柱狀圖', width=70)
        self.five_tree.column('MACD線', width=70)
        self.five_tree.column('信號線', width=70)
        self.five_tree.column('交易信號', width=80)
        self.five_tree.column('持倉狀態', width=70)
        
        five_scrollbar = ttk.Scrollbar(five_frame, orient='vertical', command=self.five_tree.yview)
        self.five_tree.configure(yscrollcommand=five_scrollbar.set)
        
        self.five_tree.pack(side='left', fill='both', expand=True)
        five_scrollbar.pack(side='right', fill='y')
        
        # 配置網格權重
        grid_frame.grid_rowconfigure(0, weight=1)
        grid_frame.grid_rowconfigure(1, weight=1)
        grid_frame.grid_columnconfigure(0, weight=1)
        grid_frame.grid_columnconfigure(1, weight=1)
        
        # 設置標籤顏色
        self.hourly_tree.tag_configure('buy_signal', background='#ffcccc')  # 淡紅色
        self.hourly_tree.tag_configure('sell_signal', background='#ccffcc')  # 淡綠色
        self.hourly_tree.tag_configure('normal', background='#ffffff')
        
        # 30分鐘顏色設置
        self.thirty_tree.tag_configure('buy_signal', background='#ffe6e6')  # 1小時買入信號 - 淡紅色
        self.thirty_tree.tag_configure('sell_signal', background='#e6ffe6')  # 1小時賣出信號 - 淡綠色
        self.thirty_tree.tag_configure('thirty_buy', background='#e6f3ff')  # 30分鐘買入 - 淺藍色
        self.thirty_tree.tag_configure('thirty_sell', background='#fff0e6')  # 30分鐘賣出 - 淺橙色
        self.thirty_tree.tag_configure('tracking', background='#f9f9f9')  # 追蹤中 - 淺灰色
        self.thirty_tree.tag_configure('normal', background='#ffffff')
        
        self.fifteen_tree.tag_configure('buy_signal', background='#ffe6e6')  # 更淡的紅色
        self.fifteen_tree.tag_configure('sell_signal', background='#e6ffe6')  # 更淡的綠色
        self.fifteen_tree.tag_configure('normal', background='#ffffff')
        
        self.five_tree.tag_configure('buy_signal', background='#ffe6e6')  # 更淡的紅色
        self.five_tree.tag_configure('sell_signal', background='#e6ffe6')  # 更淡的綠色
        self.five_tree.tag_configure('normal', background='#ffffff')
    
    def load_data(self):
        """載入1小時原始數據（在後台線程中執行）"""
        def load_thread():
            # 使用asyncio運行異步數據獲取
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                data = loop.run_until_complete(self.get_hourly_data())
                if data is not None:
                    self.hourly_data, self.hourly_statistics = data
                    self.root.after(0, self.update_hourly_table)
                    self.root.after(0, self.update_hourly_statistics)
            finally:
                loop.close()
        
        # 在後台線程中執行，避免阻塞GUI
        thread = threading.Thread(target=load_thread)
        thread.daemon = True
        thread.start()
    
    async def get_hourly_data(self):
        """獲取1小時數據 - 直接使用原始improved_macd_backtest_gui.py的邏輯"""
        try:
            self.update_status("正在獲取1小時歷史數據...")
            
            # 直接使用已驗證的LiveMACDService
            service = LiveMACDService()
            
            # 獲取7天的數據 (7天 * 24小時 = 168筆數據，加上計算MACD需要的額外數據)
            klines = await service._fetch_klines("btctwd", "60", 400)
            
            if klines is None:
                self.update_status("❌ 無法獲取歷史數據")
                await service.close()
                return None
            
            # 使用相同的計算方法
            macd_df = service._calculate_macd(klines, 12, 26, 9)
            
            if macd_df is None:
                self.update_status("❌ 無法計算歷史MACD")
                await service.close()
                return None
            
            # 獲取最近7天的數據 (168小時)
            df = macd_df.tail(168).reset_index(drop=True)
            
            self.update_status("🎯 正在應用原始1小時信號檢測...")
            
            # 應用原始改進版交易信號檢測
            df_with_signals, statistics = detect_improved_trading_signals(df)
            
            self.update_status(f"✅ 成功獲取 {len(df_with_signals)} 筆1小時歷史數據，檢測到 {statistics['buy_count']} 個買進信號，{statistics['sell_count']} 個賣出信號")
            await service.close()
            return df_with_signals, statistics
            
        except Exception as e:
            self.update_status(f"❌ 獲取數據失敗: {e}")
            return None
    
    def update_hourly_table(self):
        """更新1小時表格數據 - 只顯示買賣信號"""
        if self.hourly_data is None:
            return
        
        # 清空現有數據
        for item in self.hourly_tree.get_children():
            self.hourly_tree.delete(item)
        
        # 從最新到最舊排序
        df_sorted = self.hourly_data.sort_values('timestamp', ascending=False)
        
        # 只插入有買賣信號的數據
        for _, row in df_sorted.iterrows():
            # 只顯示買進或賣出信號，隱藏持有信號
            if row['signal_type'] in ['buy', 'sell']:
                datetime_str = row['datetime'].strftime('%Y-%m-%d %H:%M')
                price = f"{row['close']:,.0f}"
                hist = f"{row['macd_hist']:.1f}"
                macd = f"{row['macd']:.1f}"
                signal = f"{row['macd_signal']:.1f}"
                trading_signal = row['trading_signal']
                position_status = row['position_status']
                
                # 根據交易信號設置標籤
                if row['signal_type'] == 'buy':
                    tag = 'buy_signal'
                elif row['signal_type'] == 'sell':
                    tag = 'sell_signal'
                else:
                    tag = 'normal'
                
                self.hourly_tree.insert('', 'end', 
                                      values=(datetime_str, price, hist, macd, signal, trading_signal, position_status), 
                                      tags=(tag,))
    
    def update_hourly_statistics(self):
        """更新1小時統計信息"""
        if self.hourly_statistics is None:
            return
        
        # 計算時間範圍
        if len(self.hourly_data) > 0:
            start_time = self.hourly_data.iloc[0]['datetime'].strftime('%Y-%m-%d %H:%M')
            end_time = self.hourly_data.iloc[-1]['datetime'].strftime('%Y-%m-%d %H:%M')
            time_range = f"{start_time} 至 {end_time}"
        else:
            time_range = "無數據"
        
        # 獲取最新信號
        latest_signal = self.hourly_data.iloc[-1]['trading_signal'] if len(self.hourly_data) > 0 else "無數據"
        
        # 計算成功率
        total_signals = self.hourly_statistics['buy_count'] + self.hourly_statistics['sell_count']
        signal_freq = (total_signals / len(self.hourly_data)) * 100 if len(self.hourly_data) > 0 else 0
        
        stats_text = f"""📊 原始1小時交易信號統計:
🟢 買進信號: {self.hourly_statistics['buy_count']} 次
🔴 賣出信號: {self.hourly_statistics['sell_count']} 次
💰 完整交易對: {self.hourly_statistics['complete_pairs']} 對
📊 未平倉交易: {self.hourly_statistics['open_positions']} 筆
📈 當前狀態: {self.hourly_statistics['position_status']}
🔢 下一交易序號: {self.hourly_statistics['next_trade_sequence']}
📋 信號頻率: {signal_freq:.1f}%
📈 最新信號: {latest_signal}
⏰ 數據範圍: {time_range}
📋 總數據點: {len(self.hourly_data)} 筆"""
        
        # 如果有完整交易對，顯示盈虧信息
        if self.hourly_statistics['complete_pairs'] > 0:
            stats_text += f"""
💵 總盈虧: {self.hourly_statistics['total_profit']:.1f} TWD
📊 平均盈虧: {self.hourly_statistics['average_profit']:.1f} TWD
⏱️ 平均持倉時間: {self.hourly_statistics['average_hold_time']:.1f} 小時"""
        
        # 更新統計文本框
        self.hourly_stats_text.delete(1.0, tk.END)
        self.hourly_stats_text.insert(1.0, stats_text)
    
    def run_backtest(self):
        """運行多時間框架回測"""
        def backtest_thread():
            # 使用asyncio運行異步數據獲取
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                data = loop.run_until_complete(self.get_multi_timeframe_data())
                if data is not None:
                    self.multi_timeframe_data, self.multi_timeframe_statistics = data
                    self.root.after(0, lambda: self.update_multi_timeframe_tables(self.multi_timeframe_tracker))
            finally:
                loop.close()
        
        # 在後台線程中執行，避免阻塞GUI
        thread = threading.Thread(target=backtest_thread)
        thread.daemon = True
        thread.start()
    
    async def get_multi_timeframe_data(self):
        """獲取多時間框架數據"""
        try:
            self.update_status("正在獲取多時間框架數據...")
            
            # 直接使用已驗證的LiveMACDService
            service = LiveMACDService()
            
            # 獲取不同時間框架的數據
            timeframe_dfs = {}
            
            # 1小時數據
            hourly_klines = await service._fetch_klines("btctwd", "60", 400)
            if hourly_klines is not None:
                hourly_df = service._calculate_macd(hourly_klines, 12, 26, 9)
                if hourly_df is not None:
                    timeframe_dfs['1h'] = hourly_df.tail(168).reset_index(drop=True)
            
            # 30分鐘數據
            thirty_klines = await service._fetch_klines("btctwd", "30", 2400)
            if thirty_klines is not None:
                thirty_df = service._calculate_macd(thirty_klines, 12, 26, 9)
                if thirty_df is not None:
                    timeframe_dfs['30m'] = thirty_df.tail(336).reset_index(drop=True)
            
            # 15分鐘數據
            fifteen_klines = await service._fetch_klines("btctwd", "15", 2400)
            if fifteen_klines is not None:
                fifteen_df = service._calculate_macd(fifteen_klines, 12, 26, 9)
                if fifteen_df is not None:
                    timeframe_dfs['15m'] = fifteen_df.tail(672).reset_index(drop=True)
            
            # 5分鐘數據
            five_klines = await service._fetch_klines("btctwd", "5", 2400)
            if five_klines is not None:
                five_df = service._calculate_macd(five_klines, 12, 26, 9)
                if five_df is not None:
                    timeframe_dfs['5m'] = five_df.tail(2016).reset_index(drop=True)
            
            if not timeframe_dfs:
                self.update_status("❌ 無法獲取多時間框架數據")
                await service.close()
                return None
            
            self.update_status("🎯 正在應用多時間框架信號檢測...")
            
            # 應用多時間框架交易信號檢測
            # 需要傳遞1小時數據和其他時間框架數據
            hourly_df = timeframe_dfs.get('1h')
            if hourly_df is not None:
                # 移除1小時數據，只保留短時間框架
                short_timeframe_dfs = {k: v for k, v in timeframe_dfs.items() if k != '1h'}
                result_data, statistics, tracker = detect_multi_timeframe_trading_signals(hourly_df, short_timeframe_dfs)
                
                # 存儲tracker對象以便在更新表格時使用
                self.multi_timeframe_tracker = tracker
                
                # 同時保存原始數據和信號數據
                # 原始數據用於顯示，信號數據用於統計
                self.multi_timeframe_raw_data = short_timeframe_dfs  # 原始數據
                self.multi_timeframe_signals = result_data  # 信號數據
            else:
                self.update_status("❌ 缺少1小時數據")
                await service.close()
                return None
            
            self.update_status(f"✅ 成功獲取多時間框架數據，檢測到 {statistics['total_signals']} 個信號")
            await service.close()
            return result_data, statistics
            
        except Exception as e:
            self.update_status(f"❌ 多時間框架回測失敗: {e}")
            return None
    
    def update_multi_timeframe_tables(self, tracker=None):
        """更新多時間框架表格"""
        if not hasattr(self, 'multi_timeframe_raw_data') or self.multi_timeframe_raw_data is None:
            # 如果沒有多時間框架數據，清空表格並顯示提示
            self.clear_timeframe_tables()
            return
        
        # 使用存儲的tracker對象，如果沒有傳入參數
        if tracker is None:
            tracker = self.multi_timeframe_tracker
        
        # 更新多時間框架狀態顯示
        self.update_multi_timeframe_status(tracker)
        
        # 更新30分鐘表格 - 先使用原始數據確保能顯示
        if '30m' in self.multi_timeframe_raw_data:
            self.update_timeframe_table(self.thirty_tree, self.multi_timeframe_raw_data['30m'], '30m', tracker)
        elif hasattr(self, 'multi_timeframe_signals') and '30m' in self.multi_timeframe_signals:
            # 備用：如果沒有原始數據，使用信號數據
            self.update_timeframe_table(self.thirty_tree, self.multi_timeframe_signals['30m'], '30m', tracker)
        
        # 更新15分鐘表格 - 使用原始數據
        if '15m' in self.multi_timeframe_raw_data:
            self.update_timeframe_table(self.fifteen_tree, self.multi_timeframe_raw_data['15m'], '15m', tracker)
        
        # 更新5分鐘表格 - 使用原始數據
        if '5m' in self.multi_timeframe_raw_data:
            self.update_timeframe_table(self.five_tree, self.multi_timeframe_raw_data['5m'], '5m', tracker)
    
    def clear_timeframe_tables(self):
        """清空時間框架表格"""
        for tree in [self.thirty_tree, self.fifteen_tree, self.five_tree]:
            for item in tree.get_children():
                tree.delete(item)
    
    def get_position_status_at_time(self, target_time, tracker):
        """獲取指定時間點的持倉狀態 - 只考慮30分鐘的實際交易"""
        if not tracker or not hasattr(tracker, 'trade_history'):
            return '空倉'
        
        # 初始狀態為空倉
        position = 0
        
        # 遍歷所有交易歷史，找到目標時間之前的最後一個實際交易狀態
        # 只考慮30分鐘時間框架的交易，忽略1小時基準點
        for trade in tracker.trade_history:
            if trade['timestamp'] <= target_time:
                # 只處理30分鐘時間框架的實際交易
                if trade.get('timeframe') == '30m':
                    if trade['type'] == 'buy':
                        position = 1  # 持倉
                    elif trade['type'] == 'sell':
                        position = 0  # 空倉
            else:
                break  # 超過目標時間，停止檢查
        
        return '持倉' if position == 1 else '空倉'
    
    def get_next_sequence_number(self, signal_type):
        """獲取下一個交易序號"""
        if hasattr(self, 'multi_timeframe_tracker') and self.multi_timeframe_tracker:
            # 對於基準點，使用當前序號+1
            next_seq = self.multi_timeframe_tracker.trade_sequence + 1
            print(f"DEBUG: 獲取{signal_type}基準點序號: {next_seq}")
            return next_seq
        print(f"DEBUG: 沒有tracker，返回序號1")
        return 1
    
    def update_timeframe_table(self, tree, data, timeframe=None, tracker=None):
        """更新指定時間框架的表格 - 實現條件顯示邏輯"""
        # 清空現有數據
        for item in tree.get_children():
            tree.delete(item)
        
        # 檢查數據是否為空
        if data.empty:
            return
        
        # 檢查是否有datetime列，如果沒有則使用timestamp
        time_column = 'datetime' if 'datetime' in data.columns else 'timestamp'
        
        # 從最新到最舊排序
        df_sorted = data.sort_values(time_column, ascending=False)
        
        # 插入新數據
        displayed_count = 0
        total_count = len(df_sorted)
        filtered_count = 0  # 被條件過濾的數據數量
        
        for _, row in df_sorted.iterrows():
            # 處理時間格式
            if time_column == 'datetime':
                datetime_str = row['datetime'].strftime('%Y-%m-%d %H:%M')
                data_time = row['datetime']
            else:
                datetime_str = pd.to_datetime(row['timestamp']).strftime('%Y-%m-%d %H:%M')
                data_time = pd.to_datetime(row['timestamp'])
            
            # 條件顯示邏輯：檢查是否應該顯示這行數據
            should_display = True
            if timeframe and tracker:
                should_display = tracker.should_display_timeframe_data(timeframe, data_time)
                if not should_display:
                    filtered_count += 1
                    continue  # 跳過不符合條件的數據
            
            displayed_count += 1
            
            price = f"{row['close']:,.0f}"
            hist = f"{row['macd_hist']:.1f}"
            macd = f"{row['macd']:.1f}"
            signal = f"{row['macd_signal']:.1f}"
            
            # 處理交易信號 - 根據歷史交易記錄計算該時間點的持倉狀態
            trading_signal = '⚪ 持有'
            tag = 'normal'
            position_status = self.get_position_status_at_time(data_time, tracker)
            
            # 如果是30分鐘，直接檢查1小時數據中是否有對應的信號
            if timeframe == '30m' and hasattr(self, 'hourly_data') and self.hourly_data is not None:
                # 檢查1小時數據中是否有相同時間點的信號
                matching_hourly = self.hourly_data[self.hourly_data['datetime'] == data_time]
                if not matching_hourly.empty:
                    hourly_row = matching_hourly.iloc[0]
                    if hourly_row['signal_type'] == 'buy':
                        trading_signal = f"🔵 1小時{hourly_row['trading_signal']}"
                        tag = 'buy_signal'
                        position_status = '空倉'
                    elif hourly_row['signal_type'] == 'sell':
                        trading_signal = f"🔴 1小時{hourly_row['trading_signal']}"
                        tag = 'sell_signal'
                        position_status = '持倉'
                
                # 不再使用模擬30分鐘信號，改用真實的多時間框架信號
            
            # 檢查是否有信號數據可以標記
            if hasattr(self, 'multi_timeframe_signals') and self.multi_timeframe_signals is not None:
                # 先檢查30分鐘自己的信號
                if timeframe in self.multi_timeframe_signals and not self.multi_timeframe_signals[timeframe].empty:
                    signal_df = self.multi_timeframe_signals[timeframe]
                    matching_signals = signal_df[signal_df['datetime'] == data_time]
                    if not matching_signals.empty:
                        signal_row = matching_signals.iloc[0]
                        print(f"DEBUG: 找到信號 時間={data_time}, 類型={signal_row['signal_type']}")
                        
                        # 處理不同類型的信號
                        if signal_row['signal_type'] == 'buy':
                            trading_signal = signal_row.get('hourly_signal', f"🔵 30分買{signal_row.get('trade_sequence', '')}")
                            tag = 'thirty_buy'  # 使用30分鐘買入顏色
                            position_status = '持倉'
                        elif signal_row['signal_type'] == 'sell':
                            trading_signal = signal_row.get('hourly_signal', f"🟠 30分賣{signal_row.get('trade_sequence', '')}")
                            tag = 'thirty_sell'  # 使用30分鐘賣出顏色
                            position_status = '空倉'
                        elif signal_row['signal_type'] == 'buy_reference':
                            # 使用信號中記錄的序號
                            trading_signal = signal_row.get('hourly_signal', '🔵 1小時買入基準點')
                            tag = 'buy_signal'
                            # 從信號中獲取序號
                            sequence_num = int(signal_row.get('reference_sequence', signal_row.get('trade_sequence', 1)))
                            position_status = f'買{sequence_num}基準點'
                            print(f"DEBUG: 處理買入基準點，序號={sequence_num}, 狀態={position_status}")
                        elif signal_row['signal_type'] == 'sell_reference':
                            # 使用信號中記錄的序號
                            trading_signal = signal_row.get('hourly_signal', '🔴 1小時賣出基準點')
                            tag = 'sell_signal'
                            # 從信號中獲取序號
                            sequence_num = int(signal_row.get('reference_sequence', signal_row.get('trade_sequence', 1)))
                            position_status = f'賣{sequence_num}基準點'
                        elif signal_row['signal_type'] == 'tracking':
                            trading_signal = signal_row.get('hourly_signal', '⚪ 追蹤中')
                            tag = 'tracking'  # 使用追蹤顏色
                            position_status = '追蹤中'
            
            tree.insert('', 'end', 
                       values=(datetime_str, price, hist, macd, signal, trading_signal, position_status), 
                       tags=(tag,))
        
        # 更新狀態信息，顯示條件過濾的效果
        if timeframe and tracker:
            status_info = f"{timeframe}: 顯示 {displayed_count}/{total_count} 條數據"
            if filtered_count > 0:
                status_info += f" (過濾 {filtered_count} 條)"
            
            # 顯示當前時間框架的狀態
            if timeframe in tracker.short_timeframe_display_status:
                tf_status = tracker.short_timeframe_display_status[timeframe]
                if tf_status['active']:
                    if tf_status['start_time']:
                        status_info += f" [活躍中，從 {tf_status['start_time'].strftime('%H:%M')} 開始]"
                    else:
                        status_info += " [活躍中]"
                elif tf_status['confirmed']:
                    status_info += " [已確認交易]"
                else:
                    status_info += " [未激活]"
            
            # 添加等待確認狀態
            if tracker.waiting_for_confirmation:
                status_info += f" [等待{tracker.pending_signal_type}確認]"
            
            self.update_status(status_info)
        else:
            self.update_status(f"{timeframe}時間框架: 顯示 {displayed_count}/{total_count} 條數據")
    
    def save_data(self):
        """導出數據到CSV文件"""
        if self.hourly_data is None:
            messagebox.showwarning("警告", "沒有數據可導出")
            return
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AImax/data/multi_timeframe_macd_backtest_{timestamp}.csv"
            
            # 準備導出數據
            export_df = self.hourly_data.copy()
            export_df['datetime_str'] = export_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 選擇要導出的欄位
            export_columns = ['datetime_str', 'close', 'macd_hist', 'macd', 'macd_signal', 
                            'trading_signal', 'signal_type', 'trade_sequence', 
                            'position_status', 'signal_valid']
            export_df = export_df[export_columns]
            
            # 重命名欄位
            export_df.columns = ['時間', '價格', '柱狀圖', 'MACD線', '信號線', 
                               '交易信號', '信號類型', '交易序號', 
                               '持倉狀態', '信號有效性']
            
            # 導出到CSV
            export_df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            # 同時導出統計信息
            stats_filename = f"AImax/data/multi_timeframe_statistics_{timestamp}.json"
            with open(stats_filename, 'w', encoding='utf-8') as f:
                json.dump(self.hourly_statistics, f, ensure_ascii=False, indent=2, default=str)
            
            messagebox.showinfo("導出成功", f"數據已導出到:\n{filename}\n{stats_filename}")
            
        except Exception as e:
            error_msg = str(e)
            messagebox.showerror("導出失敗", f"導出數據時發生錯誤: {error_msg}")
    
    def update_multi_timeframe_status(self, tracker):
        """更新多時間框架狀態顯示"""
        if not tracker:
            status_text = "🎯 多時間框架動態追蹤狀態:\n"
            status_text += "📋 請點擊「多時間框架回測」按鈕開始分析\n"
            status_text += "⚪ 30分鐘、15分鐘、5分鐘: 等待回測啟動"
            self.multi_status_text.delete(1.0, tk.END)
            self.multi_status_text.insert(1.0, status_text)
            return
        
        status_text = "🎯 多時間框架動態追蹤狀態:\n"
        
        # 顯示當前等待狀態
        if tracker.waiting_for_confirmation:
            price_str = f"{tracker.pending_signal_price:,.0f}" if tracker.pending_signal_price else "未知"
            status_text += f"⏳ 等待確認: {tracker.pending_signal_type}信號 (價格: {price_str})\n"
            if tracker.hourly_trigger_time:
                status_text += f"🕐 1小時觸發時間: {tracker.hourly_trigger_time.strftime('%Y-%m-%d %H:%M')}\n"
        else:
            status_text += "💤 等待1小時MACD信號觸發\n"
        
        # 顯示各時間框架狀態
        timeframe_names = {'30m': '30分鐘', '15m': '15分鐘', '5m': '5分鐘'}
        for tf, name in timeframe_names.items():
            if tf in tracker.short_timeframe_display_status:
                tf_status = tracker.short_timeframe_display_status[tf]
                if tf_status['active'] and not tf_status['confirmed']:
                    status_text += f"🟢 {name}: 顯示中 "
                    if tf_status['start_time']:
                        status_text += f"(從 {tf_status['start_time'].strftime('%H:%M')} 開始)"
                elif tf_status['confirmed']:
                    status_text += f"✅ {name}: 已確認交易"
                else:
                    status_text += f"⚪ {name}: 未激活"
                status_text += "\n"
        
        # 添加獲利分析
        if hasattr(self, 'multi_timeframe_signals') and self.multi_timeframe_signals:
            profit_analysis = self.calculate_timeframe_profits()
            status_text += "\n" + "="*50 + "\n"
            status_text += "💰 各時間框架獲利分析:\n"
            status_text += profit_analysis
        
        # 更新狀態文本框
        self.multi_status_text.delete(1.0, tk.END)
        self.multi_status_text.insert(1.0, status_text)
    
    def calculate_timeframe_profits(self):
        """計算各時間框架的獲利"""
        if not hasattr(self, 'multi_timeframe_signals') or not self.multi_timeframe_signals:
            return "無交易數據"
        
        profit_text = ""
        timeframe_names = {'1h': '1小時', '30m': '30分鐘', '15m': '15分鐘', '5m': '5分鐘'}
        
        for timeframe, name in timeframe_names.items():
            if timeframe not in self.multi_timeframe_signals:
                continue
                
            df = self.multi_timeframe_signals[timeframe]
            if df.empty:
                continue
            
            # 計算該時間框架的交易對和獲利
            buy_signals = df[df['signal_type'] == 'buy'].copy()
            sell_signals = df[df['signal_type'] == 'sell'].copy()
            
            if len(buy_signals) == 0 and len(sell_signals) == 0:
                continue
            
            # 配對買賣信號計算獲利
            total_profit = 0
            trade_count = 0
            
            # 簡單配對：按序號配對
            for _, buy_row in buy_signals.iterrows():
                sequence = buy_row.get('trade_sequence', 0)
                # 找到對應的賣出信號
                matching_sells = sell_signals[sell_signals.get('trade_sequence', 0) == sequence]
                if not matching_sells.empty:
                    sell_row = matching_sells.iloc[0]
                    profit = sell_row['close'] - buy_row['close']
                    total_profit += profit
                    trade_count += 1
            
            # 反向配對：賣出開始的交易
            for _, sell_row in sell_signals.iterrows():
                sequence = sell_row.get('trade_sequence', 0)
                # 找到對應的買入信號（平倉）
                matching_buys = buy_signals[buy_signals.get('trade_sequence', 0) == sequence]
                if not matching_buys.empty:
                    buy_row = matching_buys.iloc[0]
                    # 賣出開始的交易：賣高買低
                    if buy_row['datetime'] > sell_row['datetime']:  # 確保是平倉買入
                        profit = sell_row['close'] - buy_row['close']
                        total_profit += profit
                        trade_count += 1
            
            avg_profit = total_profit / trade_count if trade_count > 0 else 0
            
            profit_text += f"📊 {name}: {trade_count}筆交易, 總獲利: {total_profit:,.0f} TWD, 平均: {avg_profit:,.0f} TWD\n"
        
        return profit_text if profit_text else "無完整交易對"
    
    def update_status(self, message):
        """更新狀態標籤"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def run(self):
        """運行GUI"""
        self.root.mainloop()

def main():
    """主函數"""
    try:
        print("啟動多時間框架MACD回測分析器...")
        print("整合原始1小時邏輯 + 多時間框架動態追蹤")
        print("基於已驗證的improved_macd_backtest_gui.py")
        
        app = MultiTimeframeMACDBacktestGUI()
        app.run()
    except Exception as e:
        print(f"程序運行錯誤: {e}")

if __name__ == "__main__":
    main() 