#!/usr/bin/env python3
"""
動態追蹤MACD回測GUI查看器
基於improved_macd_backtest_gui.py，實現動態基準價調整的交易邏輯
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
from src.core.dynamic_trading_signals import detect_dynamic_trading_signals

class DynamicMACDBacktestGUI:
    """動態追蹤MACD回測GUI - 動態基準價調整策略"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("動態追蹤MACD回測分析器 - 動態基準價調整 + 順序性交易")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#f0f0f0')
        
        # 數據存儲
        self.current_data = None
        self.statistics = None
        self.observation_hours = 2  # 預設觀察時間
        self.timeframe = "5"  # 預設5分鐘時間週期
        
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
                               text="📈 動態追蹤MACD回測分析器 - 動態基準價調整 + 順序性交易", 
                               style='Title.TLabel')
        title_label.pack(side='left')
        
        # 控制面板
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # 時間週期選擇器
        tf_label = ttk.Label(control_frame, text="時間週期:", style='Header.TLabel')
        tf_label.pack(side='left', padx=5)
        
        self.tf_var = tk.StringVar(value="5")
        tf_combo = ttk.Combobox(control_frame, textvariable=self.tf_var, 
                               values=["1", "5", "15", "30", "60"], width=5)
        tf_combo.pack(side='left', padx=5)
        tf_combo.bind('<<ComboboxSelected>>', self.on_timeframe_change)
        
        # 觀察時間選擇器
        obs_label = ttk.Label(control_frame, text="觀察時間:", style='Header.TLabel')
        obs_label.pack(side='left', padx=5)
        
        self.obs_var = tk.StringVar(value="2")
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
        
        # 動態追蹤狀態區域
        dynamic_frame = tk.LabelFrame(self.root, text="動態追蹤狀態", 
                                     bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        dynamic_frame.pack(fill='x', padx=10, pady=5)
        
        self.dynamic_text = tk.Text(dynamic_frame, height=4, bg='#ffffff', fg='#006400',
                                   font=('Consolas', 9), wrap='word')
        self.dynamic_text.pack(fill='x', padx=5, pady=5)
        
        # 交易統計區域
        stats_frame = tk.LabelFrame(self.root, text="動態追蹤交易信號統計", 
                                   bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=5, bg='#ffffff', fg='#006400',
                                 font=('Consolas', 9), wrap='word')
        self.stats_text.pack(fill='x', padx=5, pady=5)
        
        # 數據表格區域
        table_frame = tk.LabelFrame(self.root, text="MACD 7天歷史回測數據 - 動態追蹤信號檢測", 
                                  bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 創建表格 (增加動態追蹤欄位)
        columns = ('時間', '價格', '柱狀圖', 'MACD線', '信號線', '成交量', '交易信號', '持倉狀態', '動態買價', '動態賣價', '觀察中')
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
        self.tree.heading('動態買價', text='動態買價')
        self.tree.heading('動態賣價', text='動態賣價')
        self.tree.heading('觀察中', text='觀察中')
        
        self.tree.column('時間', width=140)
        self.tree.column('價格', width=100)
        self.tree.column('柱狀圖', width=80)
        self.tree.column('MACD線', width=80)
        self.tree.column('信號線', width=80)
        self.tree.column('成交量', width=80)
        self.tree.column('交易信號', width=120)
        self.tree.column('持倉狀態', width=80)
        self.tree.column('動態買價', width=100)
        self.tree.column('動態賣價', width=100)
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
        """時間週期改變事件"""
        try:
            self.timeframe = self.tf_var.get()
            self.update_status(f"時間週期已更改為 {self.timeframe} 分鐘")
            self.load_data()  # 重新載入數據
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的時間週期")
    
    def on_observation_change(self, event=None):
        """觀察時間改變事件"""
        try:
            self.observation_hours = int(self.obs_var.get())
            self.update_status(f"觀察時間已更改為 {self.observation_hours} 小時")
            self.load_data()  # 重新載入數據
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的觀察時間")
    
    def load_data(self):
        """載入數據（在後台線程中執行）"""
        def load_thread():
            # 使用asyncio運行異步數據獲取
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                data = loop.run_until_complete(self.get_7day_macd_data())
                if data is not None:
                    self.current_data, self.statistics = data
                    self.root.after(0, self.update_table)
                    self.root.after(0, self.update_statistics)
                    self.root.after(0, self.update_dynamic_status)
                    self.root.after(0, self.update_position_status)
            finally:
                loop.close()
        
        # 在後台線程中執行，避免阻塞GUI
        thread = threading.Thread(target=load_thread)
        thread.daemon = True
        thread.start()
    
    async def get_7day_macd_data(self):
        """獲取7天的MACD歷史數據並應用動態追蹤信號檢測"""
        try:
            self.update_status("正在獲取7天歷史數據...")
            
            # 直接使用已驗證的LiveMACDService
            service = LiveMACDService()
            
            # 根據時間週期計算需要的數據量
            timeframe_minutes = int(self.timeframe)
            hours_per_day = 24
            minutes_per_day = hours_per_day * 60
            data_points_per_day = minutes_per_day // timeframe_minutes
            total_data_points = data_points_per_day * 7 + 100  # 7天 + 緩衝數據
            
            # 獲取數據
            klines = await service._fetch_klines("btctwd", str(timeframe_minutes), total_data_points)
            
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
            
            # 獲取最近7天的數據
            data_points_per_day = (24 * 60) // int(self.timeframe)
            total_points = data_points_per_day * 7
            df = macd_df.tail(total_points).reset_index(drop=True)
            
            self.update_status(f"🎯 正在應用動態追蹤信號檢測 (觀察時間: {self.observation_hours}小時)...")
            
            # 將觀察時間從小時轉換為分鐘
            observation_minutes = self.observation_hours * 60
            
            # 應用動態追蹤交易信號檢測
            df_with_signals, statistics = detect_dynamic_trading_signals(df, observation_minutes)
            
            self.update_status(f"✅ 成功獲取 {len(df_with_signals)} 筆7天歷史數據，檢測到 {statistics['buy_count']} 個買進信號，{statistics['sell_count']} 個賣出信號")
            await service.close()
            return df_with_signals, statistics
            
        except Exception as e:
            self.update_status(f"❌ 獲取數據失敗: {e}")
            return None
    
    def update_table(self):
        """更新表格數據"""
        if self.current_data is None:
            return
        
        # 清空現有數據
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 從最新到最舊排序
        df_sorted = self.current_data.sort_values('datetime', ascending=False)
        
        # 插入新數據
        for _, row in df_sorted.iterrows():
            datetime_str = row['datetime'].strftime('%Y-%m-%d %H:%M')
            price = f"{row['close']:,.0f}"
            hist = f"{row['macd_hist']:.1f}"
            macd = f"{row['macd']:.1f}"
            signal = f"{row['macd_signal']:.1f}"
            volume = f"{row['volume']:,.0f}"
            trading_signal = row['trading_signal']
            position_status = row['position_status']
            
            # 動態價格顯示
            dynamic_buy = f"{row['dynamic_buy_price']:,.0f}" if pd.notna(row['dynamic_buy_price']) else ""
            dynamic_sell = f"{row['dynamic_sell_price']:,.0f}" if pd.notna(row['dynamic_sell_price']) else ""
            is_observing = "是" if row['is_observing'] else ""
            
            # 根據交易信號設置標籤
            if row['signal_type'] == 'buy':
                tag = 'buy_signal'
            elif row['signal_type'] == 'sell':
                tag = 'sell_signal'
            elif row['signal_type'] in ['observe_buy', 'observe_sell']:
                tag = 'observe_signal'
            else:
                tag = 'normal'
            
            self.tree.insert('', 'end', 
                           values=(datetime_str, price, hist, macd, signal, volume, 
                                  trading_signal, position_status, dynamic_buy, dynamic_sell, is_observing), 
                           tags=(tag,))
        
        # 設置標籤顏色
        self.tree.tag_configure('buy_signal', background='#ffcccc')  # 淡紅色
        self.tree.tag_configure('sell_signal', background='#ccffcc')  # 淡綠色
        self.tree.tag_configure('observe_signal', background='#ffffcc')  # 淡黃色
        self.tree.tag_configure('normal', background='#ffffff')
    
    def update_statistics(self):
        """更新統計信息"""
        if self.statistics is None:
            return
        
        # 計算時間範圍
        if len(self.current_data) > 0:
            start_time = self.current_data.iloc[0]['datetime'].strftime('%Y-%m-%d %H:%M')
            end_time = self.current_data.iloc[-1]['datetime'].strftime('%Y-%m-%d %H:%M')
            time_range = f"{start_time} 至 {end_time}"
        else:
            time_range = "無數據"
        
        # 獲取最新信號
        latest_signal = self.current_data.iloc[-1]['trading_signal'] if len(self.current_data) > 0 else "無數據"
        
        # 計算成功率
        total_signals = self.statistics['buy_count'] + self.statistics['sell_count']
        signal_freq = (total_signals / len(self.current_data)) * 100 if len(self.current_data) > 0 else 0
        
        stats_text = f"""📊 動態追蹤交易信號統計 (觀察時間: {self.observation_hours}小時):
🟢 買進信號: {self.statistics['buy_count']} 次
🔴 賣出信號: {self.statistics['sell_count']} 次
💰 完整交易對: {self.statistics['complete_pairs']} 對
📊 未平倉交易: {self.statistics['open_positions']} 筆
📈 當前狀態: {self.statistics['position_status']}
🔢 下一交易序號: {self.statistics['next_trade_sequence']}
📋 信號頻率: {signal_freq:.1f}%
📈 最新信號: {latest_signal}
⏰ 數據範圍: {time_range}
📋 總數據點: {len(self.current_data)} 筆"""
        
        # 如果有完整交易對，顯示盈虧信息
        if self.statistics['complete_pairs'] > 0:
            stats_text += f"""
💵 總盈虧: {self.statistics['total_profit']:.1f} TWD
📊 平均盈虧: {self.statistics['average_profit']:.1f} TWD
⏱️ 平均持倉時間: {self.statistics['average_hold_time']:.1f} 小時"""
        
        # 更新統計文本框
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
    
    def update_dynamic_status(self):
        """更新動態追蹤狀態"""
        if self.statistics is None:
            return
        
        dynamic_text = f"""🎯 動態追蹤策略說明:
📋 觀察時間: {self.observation_hours} 小時
🔄 動態調整: 基準價只能往有利方向移動
⚡ 即時觸發: 價格突破基準價立即執行

📈 買進邏輯:
   - MACD交叉時記錄基準價
   - 觀察期間內價格更低 → 基準價往下調整
   - 價格回升突破基準價 → 立即買進

📉 賣出邏輯:
   - MACD交叉時記錄基準價  
   - 觀察期間內價格更高 → 基準價往上調整
   - 價格回跌跌破基準價 → 立即賣出

🎯 當前狀態: {self.statistics['position_status']}"""
        
        if self.statistics.get('is_observing', False):
            dynamic_text += f"""
🔍 正在觀察中:
   - 觀察開始時間: {self.statistics.get('observation_start_time', 'N/A')}
   - 動態買價: {self.statistics.get('dynamic_buy_price', 'N/A')}
   - 動態賣價: {self.statistics.get('dynamic_sell_price', 'N/A')}"""
        
        # 更新動態狀態文本框
        self.dynamic_text.delete(1.0, tk.END)
        self.dynamic_text.insert(1.0, dynamic_text)
    
    def update_position_status(self):
        """更新持倉狀態指示器"""
        if self.statistics is None:
            return
        
        status_text = f"當前狀態: {self.statistics['position_status']}"
        if self.statistics['position_status'] == '空倉':
            status_text += f" | 下一交易: 買{self.statistics['next_trade_sequence']}"
        else:
            status_text += f" | 下一交易: 賣{self.statistics['next_trade_sequence']}"
        
        if self.statistics.get('is_observing', False):
            status_text += " | 🔍 觀察中"
        
        self.position_label.config(text=status_text)
    
    def analyze_signals(self):
        """手動分析信號"""
        if self.current_data is None:
            messagebox.showwarning("警告", "沒有數據可分析")
            return
        
        self.update_statistics()
        self.update_dynamic_status()
        messagebox.showinfo("分析完成", "動態追蹤交易信號分析已更新")
    
    def save_data(self):
        """導出數據到CSV文件"""
        if self.current_data is None:
            messagebox.showwarning("警告", "沒有數據可導出")
            return
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AImax/data/dynamic_macd_7day_backtest_{timestamp}.csv"
            
            # 準備導出數據
            export_df = self.current_data.copy()
            export_df['datetime_str'] = export_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 選擇要導出的欄位
            export_columns = ['datetime_str', 'close', 'macd_hist', 'macd', 'macd_signal', 
                            'volume', 'trading_signal', 'signal_type', 'trade_sequence', 
                            'position_status', 'signal_valid', 'dynamic_buy_price', 
                            'dynamic_sell_price', 'is_observing']
            export_df = export_df[export_columns]
            
            # 重命名欄位
            export_df.columns = ['時間', '價格', '柱狀圖', 'MACD線', '信號線', 
                               '成交量', '交易信號', '信號類型', '交易序號', 
                               '持倉狀態', '信號有效性', '動態買價', '動態賣價', '觀察中']
            
            # 導出到CSV
            export_df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            # 同時導出統計信息
            stats_filename = f"AImax/data/dynamic_macd_statistics_{timestamp}.json"
            with open(stats_filename, 'w', encoding='utf-8') as f:
                json.dump(self.statistics, f, ensure_ascii=False, indent=2, default=str)
            
            messagebox.showinfo("導出成功", f"數據已導出到:\n{filename}\n{stats_filename}")
            
        except Exception as e:
            messagebox.showerror("導出失敗", f"導出數據時發生錯誤: {e}")
    
    def on_item_double_click(self, event):
        """處理表格項目雙擊事件"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            
            detail_text = f"""
動態追蹤交易信號詳情:
時間: {values[0]}
價格: {values[1]} TWD
柱狀圖: {values[2]}
MACD線: {values[3]}
信號線: {values[4]}
成交量: {values[5]}
交易信號: {values[6]}
持倉狀態: {values[7]}
動態買價: {values[8]}
動態賣價: {values[9]}
觀察中: {values[10]}

動態追蹤策略規則:
🟢 買進: MACD交叉 → 記錄基準價 → 動態調整 → 價格回升突破時買進
🔴 賣出: MACD交叉 → 記錄基準價 → 動態調整 → 價格回跌跌破時賣出
⚪ 持有: 不符合買進或賣出條件

順序性交易: 買1→賣1→買2→賣2→買3→賣3...
觀察時間: {self.observation_hours} 小時
            """.strip()
            
            messagebox.showinfo("數據詳情", detail_text)
    
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
        print("🚀 啟動動態追蹤MACD回測分析器...")
        print("📋 動態基準價調整 + 順序性交易邏輯")
        print("🎯 基於已驗證的LiveMACDService計算邏輯")
        
        app = DynamicMACDBacktestGUI()
        app.run()
    except Exception as e:
        print(f"❌ 程序運行錯誤: {e}")

if __name__ == "__main__":
    main()