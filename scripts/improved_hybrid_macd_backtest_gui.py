#!/usr/bin/env python3
"""
改進的混合MACD回測GUI查看器
使用1小時MACD作為趨勢確認，短時間週期作為精確入場時機
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
from src.core.improved_hybrid_trading_signals import detect_improved_hybrid_trading_signals

class ImprovedHybridMACDBacktestGUI:
    """改進的混合MACD回測GUI - 1小時趨勢確認 + 短時間週期精確入場"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("改進的混合MACD回測分析器 - 1小時趨勢確認 + 短時間週期精確入場")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#f0f0f0')
        
        # 數據存儲
        self.current_data = None
        self.statistics = None
        self.entry_observation_hours = 1  # 預設入場觀察時間
        self.dynamic_timeframe = "5"  # 預設短時間週期（分鐘）
        
        # 設置樣式
        self.setup_styles()
        
        # 創建界面
        self.create_widgets()
        
        # 自動載入數據
        self.load_data()
    
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
                               text="📈 改進的混合MACD回測分析器 - 1小時趨勢確認 + 短時間週期精確入場", 
                               style='Title.TLabel')
        title_label.pack(side='left')
        
        # 控制面板
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # 短時間週期選擇器
        tf_label = ttk.Label(control_frame, text="短時間週期:", style='Header.TLabel')
        tf_label.pack(side='left', padx=5)
        
        self.tf_var = tk.StringVar(value="5")
        tf_combo = ttk.Combobox(control_frame, textvariable=self.tf_var, 
                               values=["1", "5", "15", "30"], width=5)
        tf_combo.pack(side='left', padx=5)
        tf_combo.bind('<<ComboboxSelected>>', self.on_timeframe_change)
        
        # 入場觀察時間選擇器
        obs_label = ttk.Label(control_frame, text="入場觀察時間:", style='Header.TLabel')
        obs_label.pack(side='left', padx=5)
        
        self.obs_var = tk.StringVar(value="1")
        obs_combo = ttk.Combobox(control_frame, textvariable=self.obs_var, 
                                values=["1", "2", "3", "4"], width=5)
        obs_combo.pack(side='left', padx=5)
        obs_combo.bind('<<ComboboxSelected>>', self.on_observation_change)
        
        refresh_btn = ttk.Button(control_frame, text="🔄 重新載入", 
                               command=self.load_data, style='Custom.TButton')
        refresh_btn.pack(side='left', padx=10)
        
        save_btn = ttk.Button(control_frame, text="💾 導出數據", 
                            command=self.save_data, style='Custom.TButton')
        save_btn.pack(side='left', padx=5)
        
        signal_btn = ttk.Button(control_frame, text="🎯 分析信號", 
                              command=self.analyze_signals, style='Custom.TButton')
        signal_btn.pack(side='left', padx=5)
        
        # 持倉狀態指示器
        self.position_label = ttk.Label(control_frame, text="當前狀態: 載入中...", style='Status.TLabel')
        self.position_label.pack(side='right', padx=20)
        
        # 狀態標籤
        self.status_label = ttk.Label(control_frame, text="準備就緒", style='Data.TLabel')
        self.status_label.pack(side='right', padx=5)
        
        # 改進策略說明區域
        info_frame = tk.LabelFrame(self.root, text="改進的混合策略說明", 
                                  bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        info_frame.pack(fill='x', padx=10, pady=5)
        
        info_text = tk.Text(info_frame, height=3, bg='#ffffff', fg='#006400',
                           font=('Consolas', 9), wrap='word')
        info_text.pack(fill='x', padx=5, pady=5)
        info_text.insert('1.0', 
                        "策略邏輯：1小時MACD交叉作為趨勢確認 → 在短時間週期上尋找最佳入場時機 → "
                        "價格回升突破觸發價格時執行買進 → 1小時MACD死叉時直接賣出")
        info_text.config(state='disabled')
        
        # 入場觀察狀態區域
        entry_frame = tk.LabelFrame(self.root, text="入場觀察狀態", 
                                   bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        entry_frame.pack(fill='x', padx=10, pady=5)
        
        self.entry_text = tk.Text(entry_frame, height=4, bg='#ffffff', fg='#006400',
                                 font=('Consolas', 9), wrap='word')
        self.entry_text.pack(fill='x', padx=5, pady=5)
        
        # 交易統計區域
        stats_frame = tk.LabelFrame(self.root, text="改進的混合策略交易信號統計", 
                                   bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=5, bg='#ffffff', fg='#006400',
                                 font=('Consolas', 9), wrap='word')
        self.stats_text.pack(fill='x', padx=5, pady=5)
        
        # 數據表格區域
        table_frame = tk.LabelFrame(self.root, text="改進的混合MACD 7天歷史回測數據", 
                                   bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 創建表格 (增加改進策略欄位)
        columns = ('時間', '價格', '柱狀圖', 'MACD線', '信號線', '成交量', '交易信號', '持倉狀態', 
                  '1小時信號', '短時間週期', '最佳入場價', '觸發價格', '觀察中')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=25)
        
        # 設置列標題和寬度
        self.tree.heading('時間', text='時間')
        self.tree.heading('價格', text='價格 (TWD)')
        self.tree.heading('柱狀圖', text='柱狀圖')
        self.tree.heading('MACD線', text='MACD線')
        self.tree.heading('信號線', text='信號線')
        self.tree.heading('成交量', text='成交量')
        self.tree.heading('交易信號', text='交易信號')
        self.tree.heading('持倉狀態', text='持倉狀態')
        self.tree.heading('1小時信號', text='1小時信號')
        self.tree.heading('短時間週期', text='短時間週期')
        self.tree.heading('最佳入場價', text='最佳入場價')
        self.tree.heading('觸發價格', text='觸發價格')
        self.tree.heading('觀察中', text='觀察中')
        
        self.tree.column('時間', width=140)
        self.tree.column('價格', width=100)
        self.tree.column('柱狀圖', width=80)
        self.tree.column('MACD線', width=80)
        self.tree.column('信號線', width=80)
        self.tree.column('成交量', width=80)
        self.tree.column('交易信號', width=120)
        self.tree.column('持倉狀態', width=80)
        self.tree.column('1小時信號', width=120)
        self.tree.column('短時間週期', width=80)
        self.tree.column('最佳入場價', width=100)
        self.tree.column('觸發價格', width=100)
        self.tree.column('觀察中', width=60)
        
        # 添加滾動條
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 打包表格和滾動條
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 綁定雙擊事件
        self.tree.bind('<Double-1>', self.on_item_double_click)
    
    def on_timeframe_change(self, event=None):
        """短時間週期改變事件"""
        try:
            self.dynamic_timeframe = self.tf_var.get()
            self.update_status(f"短時間週期已更改為 {self.dynamic_timeframe} 分鐘")
            self.load_data()
        except Exception as e:
            messagebox.showerror("錯誤", f"更改時間週期失敗: {e}")
    
    def on_observation_change(self, event=None):
        """入場觀察時間改變事件"""
        try:
            self.entry_observation_hours = int(self.obs_var.get())
            self.update_status(f"入場觀察時間已更改為 {self.entry_observation_hours} 小時")
            self.load_data()
        except Exception as e:
            messagebox.showerror("錯誤", f"更改觀察時間失敗: {e}")
    
    def load_data(self):
        """載入數據"""
        def load_thread():
            # 使用asyncio運行異步數據獲取
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                data = loop.run_until_complete(self.get_improved_hybrid_macd_data())
                if data:
                    self.current_data = data
                    self.root.after(0, self.update_table)
                    self.root.after(0, self.update_statistics)
                    self.root.after(0, lambda: self.update_status("數據載入完成"))
                else:
                    self.root.after(0, lambda: self.update_status("數據載入失敗"))
            except Exception as e:
                self.root.after(0, lambda: self.update_status(f"載入錯誤: {e}"))
            finally:
                loop.close()
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    async def get_improved_hybrid_macd_data(self):
        """獲取改進的混合MACD數據"""
        try:
            self.update_status("正在獲取1小時MACD數據...")
            macd_service = LiveMACDService()
            
            # 獲取1小時數據（7天）
            hourly_limit = 7 * 24  # 7天的小時數
            hourly_klines = await macd_service._fetch_klines(
                market="btctwd",
                period="60",
                limit=hourly_limit
            )
            
            if hourly_klines is None or hourly_klines.empty:
                self.update_status("無法獲取1小時數據")
                return None
            
            # 確保datetime列存在
            if 'datetime' not in hourly_klines.columns:
                hourly_klines['datetime'] = pd.to_datetime(hourly_klines['timestamp'], unit='s')
            
            # 計算1小時MACD
            hourly_df = macd_service._calculate_macd(hourly_klines, 12, 26, 9)
            
            self.update_status("正在獲取短時間週期數據...")
            
            # 獲取短時間週期數據（7天）
            dynamic_limit = (7 * 24 * 60) // int(self.dynamic_timeframe)  # 7天的數據點數
            dynamic_klines = await macd_service._fetch_klines(
                market="btctwd",
                period=self.dynamic_timeframe,
                limit=dynamic_limit
            )
            
            if dynamic_klines is None or dynamic_klines.empty:
                self.update_status("無法獲取短時間週期數據")
                return None
            
            # 確保datetime列存在
            if 'datetime' not in dynamic_klines.columns:
                dynamic_klines['datetime'] = pd.to_datetime(dynamic_klines['timestamp'], unit='s')
            
            # 計算短時間週期MACD
            dynamic_df = macd_service._calculate_macd(dynamic_klines, 12, 26, 9)
            
            self.update_status("正在檢測改進的混合策略信號...")
            
            # 檢測改進的混合策略信號
            signals_df, stats = detect_improved_hybrid_trading_signals(
                hourly_df, dynamic_df, self.dynamic_timeframe, self.entry_observation_hours
            )
            
            self.statistics = stats
            
            # 合併數據用於顯示
            combined_data = []
            
            # 添加1小時信號數據
            for _, row in hourly_df.iterrows():
                combined_data.append({
                    'datetime': row['datetime'],
                    'close': row['close'],
                    'macd_hist': row['macd_hist'],
                    'macd': row['macd'],
                    'macd_signal': row['macd_signal'],
                    'volume': row['volume'],
                    'timeframe': '1小時',
                    'signal_type': 'hourly',
                    'trade_sequence': '',
                    'position_status': '',
                    'hourly_signal': '',
                    'dynamic_timeframe': '',
                    'best_entry_price': '',
                    'entry_trigger_price': '',
                    'is_observing': ''
                })
            
            # 添加短時間週期信號數據
            for _, row in signals_df.iterrows():
                combined_data.append({
                    'datetime': row['datetime'],
                    'close': row['close'],
                    'macd_hist': row['macd_hist'],
                    'macd': row['macd'],
                    'macd_signal': row['macd_signal'],
                    'volume': 0,  # 短時間數據可能沒有volume
                    'timeframe': f'{self.dynamic_timeframe}分鐘',
                    'signal_type': row['signal_type'],
                    'trade_sequence': row['trade_sequence'],
                    'position_status': '持倉' if row['signal_type'] == 'buy' else '空倉',
                    'hourly_signal': row['hourly_signal'],
                    'dynamic_timeframe': row['dynamic_timeframe'],
                    'best_entry_price': '',
                    'entry_trigger_price': '',
                    'is_observing': '是'
                })
            
            # 按時間排序
            combined_data.sort(key=lambda x: x['datetime'])
            
            return combined_data
            
        except Exception as e:
            self.update_status(f"獲取數據失敗: {e}")
            return None
    
    def update_table(self):
        """更新表格數據"""
        if not self.current_data:
            return
        
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加數據
        for data in self.current_data:
            self.tree.insert('', 'end', values=(
                data['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                f"{data['close']:,.0f}",
                f"{data['macd_hist']:.2f}",
                f"{data['macd']:.2f}",
                f"{data['macd_signal']:.2f}",
                f"{data['volume']:,.0f}",
                data['signal_type'],
                data['position_status'],
                data['hourly_signal'],
                data['dynamic_timeframe'],
                data['best_entry_price'],
                data['entry_trigger_price'],
                data['is_observing']
            ))
        
        self.update_entry_status()
        self.update_position_status()
    
    def update_statistics(self):
        """更新統計信息"""
        if not self.statistics:
            return
        
        stats = self.statistics
        stats_text = f"""
📊 改進的混合策略統計信息
==========================
總交易次數: {stats['total_trades']}
買進次數: {stats['buy_count']}
賣出次數: {stats['sell_count']}
當前狀態: {stats['current_status']['current_position']}

🔍 當前入場觀察狀態:
等待入場: {'是' if stats['current_status']['is_waiting_for_entry'] else '否'}
最佳入場價: {stats['current_status']['best_entry_price']:,.0f if stats['current_status']['best_entry_price'] is not None else '無'}
觸發價格: {stats['current_status']['entry_trigger_price']:,.0f if stats['current_status']['entry_trigger_price'] is not None else '無'}
短時間週期: {stats['current_status']['dynamic_timeframe']}分鐘
1小時信號: {stats['current_status']['hourly_signal'] or '無'}
"""
        
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert('1.0', stats_text)
    
    def update_entry_status(self):
        """更新入場觀察狀態"""
        if not self.statistics:
            return
        
        status = self.statistics['current_status']
        status_text = f"""
🔄 入場觀察狀態
===============
1小時MACD信號: {status['hourly_signal'] or '等待信號'}
短時間週期: {status['dynamic_timeframe']}分鐘
觀察狀態: {'等待入場' if status['is_waiting_for_entry'] else '等待信號'}
觀察時間: {self.entry_observation_hours}小時

💰 入場價格追蹤:
最佳入場價: {status['best_entry_price']:,.0f if status['best_entry_price'] is not None else '未設置'}
觸發價格: {status['entry_trigger_price']:,.0f if status['entry_trigger_price'] is not None else '未設置'}
"""
        
        self.entry_text.delete('1.0', tk.END)
        self.entry_text.insert('1.0', status_text)
    
    def update_position_status(self):
        """更新持倉狀態"""
        if not self.statistics:
            return
        
        status = self.statistics['current_status']
        position_text = f"當前狀態: {'持倉中' if status['current_position'] == 1 else '空倉中'}"
        self.position_label.config(text=position_text)
    
    def analyze_signals(self):
        """分析信號"""
        if not self.current_data:
            messagebox.showwarning("警告", "請先載入數據")
            return
        
        # 計算基本統計
        signals = [d for d in self.current_data if d['signal_type'] in ['buy', 'sell']]
        buy_signals = [s for s in signals if s['signal_type'] == 'buy']
        sell_signals = [s for s in signals if s['signal_type'] == 'sell']
        
        analysis_text = f"""
🎯 改進的混合策略信號分析
==========================
總信號數: {len(signals)}
買進信號: {len(buy_signals)}
賣出信號: {len(sell_signals)}
短時間週期: {self.dynamic_timeframe}分鐘
入場觀察時間: {self.entry_observation_hours}小時

📈 策略特點:
• 使用1小時MACD作為趨勢確認
• 在{self.dynamic_timeframe}分鐘週期尋找最佳入場時機
• 入場觀察時間為{self.entry_observation_hours}小時
• 價格回升突破觸發價格時執行買進
• 1小時MACD死叉時直接賣出
"""
        
        messagebox.showinfo("信號分析", analysis_text)
    
    def save_data(self):
        """保存數據"""
        if not self.current_data:
            messagebox.showwarning("警告", "沒有數據可保存")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"improved_hybrid_macd_7day_backtest_{timestamp}.csv"
            filepath = os.path.join("AImax", "data", filename)
            
            # 確保目錄存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # 準備保存數據
            save_data = []
            for data in self.current_data:
                save_data.append({
                    'datetime': data['datetime'].strftime('%Y-%m-%d %H:%M:%S'),
                    'close': data['close'],
                    'macd_hist': data['macd_hist'],
                    'macd': data['macd'],
                    'macd_signal': data['macd_signal'],
                    'volume': data['volume'],
                    'signal_type': data['signal_type'],
                    'trade_sequence': data['trade_sequence'],
                    'hourly_signal': data['hourly_signal'],
                    'dynamic_timeframe': data['dynamic_timeframe'],
                    'position_status': data['position_status']
                })
            
            # 保存為CSV
            df = pd.DataFrame(save_data)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            # 保存統計信息
            stats_filename = f"improved_hybrid_macd_stats_{timestamp}.json"
            stats_filepath = os.path.join("AImax", "data", stats_filename)
            
            with open(stats_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.statistics, f, ensure_ascii=False, indent=2, default=str)
            
            messagebox.showinfo("保存成功", f"數據已保存到:\n{filepath}\n統計信息已保存到:\n{stats_filepath}")
            
        except Exception as e:
            messagebox.showerror("保存失敗", f"保存數據時發生錯誤:\n{e}")
    
    def on_item_double_click(self, event):
        """雙擊表格項目事件"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        values = item['values']
        
        if len(values) >= 7 and values[6] in ['buy', 'sell']:
            detail_text = f"""
📋 交易信號詳情
===============
時間: {values[0]}
價格: {values[1]}
信號類型: {values[6]}
持倉狀態: {values[7]}
1小時信號: {values[8]}
短時間週期: {values[9]}
MACD柱狀圖: {values[2]}
MACD線: {values[3]}
信號線: {values[4]}
"""
            messagebox.showinfo("交易詳情", detail_text)
    
    def update_status(self, message):
        """更新狀態"""
        self.status_label.config(text=message)
        print(f"狀態更新: {message}")
    
    def run(self):
        """運行GUI"""
        self.root.mainloop()

def main():
    """主函數"""
    print("🚀 啟動改進的混合MACD回測分析器...")
    print("📋 1小時趨勢確認 + 短時間週期精確入場")
    print("🎯 改進的混合策略邏輯")
    
    app = ImprovedHybridMACDBacktestGUI()
    app.run()

if __name__ == "__main__":
    main() 