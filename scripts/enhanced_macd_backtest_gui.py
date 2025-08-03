#!/usr/bin/env python3
"""
增強版MACD回測GUI查看器
基於exact_macd_gui.py，增加7天歷史回測和交易信號檢測功能
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

# 直接使用已驗證的LiveMACDService
from src.data.live_macd_service import LiveMACDService

class EnhancedMACDBacktestGUI:
    """增強版MACD回測GUI - 7天歷史數據 + 交易信號檢測"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("增強版MACD回測分析器 - 7天歷史數據 + 交易信號")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # 數據存儲
        self.current_data = None
        self.reference_data = self._load_reference_data()
        
        # 設置樣式
        self.setup_styles()
        
        # 創建界面
        self.create_widgets()
        
        # 自動載入數據
        self.load_data()
    
    def _load_reference_data(self):
        """載入用戶提供的參考數據"""
        return [
            {'timestamp': '2025-07-30 06:00', 'macd': -2948.2, 'signal': -787.8, 'histogram': -2160.4},
            {'timestamp': '2025-07-30 07:00', 'macd': -2434.1, 'signal': -1117.1, 'histogram': -1317.1},
            {'timestamp': '2025-07-30 08:00', 'macd': -2441.4, 'signal': -1381.9, 'histogram': -1059.5},
            {'timestamp': '2025-07-30 09:00', 'macd': -2327.2, 'signal': -1571.0, 'histogram': -756.2}
        ]
    
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
    
    def create_widgets(self):
        """創建GUI組件"""
        # 主標題
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(fill='x', padx=10, pady=5)
        
        title_label = ttk.Label(title_frame, 
                               text="📈 增強版MACD回測分析器 - 7天歷史數據 + 交易信號檢測", 
                               style='Title.TLabel')
        title_label.pack(side='left')
        
        # 控制面板
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(fill='x', padx=10, pady=5)
        
        refresh_btn = ttk.Button(control_frame, text="🔄 重新載入", 
                               command=self.load_data, style='Custom.TButton')
        refresh_btn.pack(side='left', padx=5)
        
        save_btn = ttk.Button(control_frame, text="💾 導出數據", 
                            command=self.save_data, style='Custom.TButton')
        save_btn.pack(side='left', padx=5)
        
        signal_btn = ttk.Button(control_frame, text="🎯 分析信號", 
                              command=self.analyze_signals, style='Custom.TButton')
        signal_btn.pack(side='left', padx=5)
        
        # 狀態標籤
        self.status_label = ttk.Label(control_frame, text="準備就緒", style='Data.TLabel')
        self.status_label.pack(side='right', padx=5)
        
        # 信號統計區域
        stats_frame = tk.LabelFrame(self.root, text="交易信號統計", 
                                   bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=4, bg='#ffffff', fg='#006400',
                                 font=('Consolas', 9), wrap='word')
        self.stats_text.pack(fill='x', padx=5, pady=5)
        
        # 數據表格區域
        table_frame = tk.LabelFrame(self.root, text="MACD 7天歷史回測數據", 
                                  bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 創建表格 (增加交易信號欄)
        columns = ('時間', '價格', '柱狀圖', 'MACD線', '信號線', '成交量', '交易信號')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=25)
        
        # 設置列標題和寬度
        self.tree.heading('時間', text='時間')
        self.tree.heading('價格', text='價格 (TWD)')
        self.tree.heading('柱狀圖', text='柱狀圖')
        self.tree.heading('MACD線', text='MACD線')
        self.tree.heading('信號線', text='信號線')
        self.tree.heading('成交量', text='成交量')
        self.tree.heading('交易信號', text='交易信號')
        
        self.tree.column('時間', width=140)
        self.tree.column('價格', width=100)
        self.tree.column('柱狀圖', width=100)
        self.tree.column('MACD線', width=100)
        self.tree.column('信號線', width=100)
        self.tree.column('成交量', width=120)
        self.tree.column('交易信號', width=120)
        
        # 添加滾動條
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 打包表格和滾動條
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 綁定雙擊事件
        self.tree.bind('<Double-1>', self.on_item_double_click)
    
    def load_data(self):
        """載入數據（在後台線程中執行）"""
        def load_thread():
            # 使用asyncio運行異步數據獲取
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                data = loop.run_until_complete(self.get_7day_macd_data())
                if data is not None:
                    self.current_data = data
                    self.root.after(0, self.update_table)
                    self.root.after(0, self.auto_analyze_signals)
            finally:
                loop.close()
        
        # 在後台線程中執行，避免阻塞GUI
        thread = threading.Thread(target=load_thread)
        thread.daemon = True
        thread.start()
    
    async def get_7day_macd_data(self):
        """獲取7天的MACD歷史數據"""
        try:
            self.update_status("正在獲取7天歷史數據...")
            
            # 直接使用已驗證的LiveMACDService
            service = LiveMACDService()
            
            # 獲取7天的數據 (7天 * 24小時 = 168筆數據，加上計算MACD需要的額外數據)
            # 使用更大的limit確保獲得足夠的歷史數據
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
            
            # 添加交易信號檢測
            df = self.detect_trading_signals(df)
            
            self.update_status(f"✅ 成功獲取 {len(df)} 筆7天歷史數據")
            await service.close()
            return df
            
        except Exception as e:
            self.update_status(f"❌ 獲取數據失敗: {e}")
            return None
    
    def detect_trading_signals(self, df):
        """檢測交易信號"""
        if len(df) < 2:
            return df
        
        # 初始化信號欄
        df['trading_signal'] = '持有'
        df['signal_type'] = 'hold'
        
        for i in range(1, len(df)):
            current = df.iloc[i]
            previous = df.iloc[i-1]
            
            # 買進信號：MACD柱為負，然後MACD線突然大於信號線
            if (previous['macd_hist'] < 0 and  # 前一個柱狀圖為負
                previous['macd'] <= previous['macd_signal'] and  # 前一個MACD <= 信號線
                current['macd'] > current['macd_signal']):  # 當前MACD > 信號線
                df.at[i, 'trading_signal'] = '🟢 買進'
                df.at[i, 'signal_type'] = 'buy'
            
            # 賣出信號：MACD柱為正，然後信號線突然大於MACD線
            elif (previous['macd_hist'] > 0 and  # 前一個柱狀圖為正
                  previous['macd'] >= previous['macd_signal'] and  # 前一個MACD >= 信號線
                  current['macd_signal'] > current['macd']):  # 當前信號線 > MACD
                df.at[i, 'trading_signal'] = '🔴 賣出'
                df.at[i, 'signal_type'] = 'sell'
            else:
                df.at[i, 'trading_signal'] = '⚪ 持有'
                df.at[i, 'signal_type'] = 'hold'
        
        return df
    
    def update_table(self):
        """更新表格數據"""
        if self.current_data is None:
            return
        
        # 清空現有數據
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 從最新到最舊排序
        df_sorted = self.current_data.sort_values('timestamp', ascending=False)
        
        # 插入新數據
        for _, row in df_sorted.iterrows():
            datetime_str = row['datetime'].strftime('%Y-%m-%d %H:%M')
            price = f"{row['close']:,.0f}"
            hist = f"{row['macd_hist']:.1f}"
            macd = f"{row['macd']:.1f}"
            signal = f"{row['macd_signal']:.1f}"
            volume = f"{row['volume']:,.0f}"
            trading_signal = row['trading_signal']
            
            # 根據交易信號設置標籤
            if row['signal_type'] == 'buy':
                tag = 'buy_signal'
            elif row['signal_type'] == 'sell':
                tag = 'sell_signal'
            else:
                tag = 'normal'
            
            self.tree.insert('', 'end', 
                           values=(datetime_str, price, hist, macd, signal, volume, trading_signal), 
                           tags=(tag,))
        
        # 設置標籤顏色
        self.tree.tag_configure('buy_signal', background='#ffcccc')  # 淡紅色
        self.tree.tag_configure('sell_signal', background='#ccffcc')  # 淡綠色
        self.tree.tag_configure('normal', background='#ffffff')
    
    def auto_analyze_signals(self):
        """自動分析交易信號統計"""
        if self.current_data is None:
            return
        
        # 統計信號
        buy_signals = len(self.current_data[self.current_data['signal_type'] == 'buy'])
        sell_signals = len(self.current_data[self.current_data['signal_type'] == 'sell'])
        hold_signals = len(self.current_data[self.current_data['signal_type'] == 'hold'])
        total_signals = len(self.current_data)
        
        # 計算信號頻率
        buy_freq = (buy_signals / total_signals) * 100 if total_signals > 0 else 0
        sell_freq = (sell_signals / total_signals) * 100 if total_signals > 0 else 0
        
        # 獲取最新信號
        latest_signal = self.current_data.iloc[-1]['trading_signal'] if len(self.current_data) > 0 else "無數據"
        
        # 計算時間範圍
        if len(self.current_data) > 0:
            start_time = self.current_data.iloc[0]['datetime'].strftime('%Y-%m-%d %H:%M')
            end_time = self.current_data.iloc[-1]['datetime'].strftime('%Y-%m-%d %H:%M')
            time_range = f"{start_time} 至 {end_time}"
        else:
            time_range = "無數據"
        
        stats_text = f"""📊 7天回測信號統計:
🟢 買進信號: {buy_signals} 次 ({buy_freq:.1f}%)
🔴 賣出信號: {sell_signals} 次 ({sell_freq:.1f}%)
⚪ 持有狀態: {hold_signals} 次
📈 最新信號: {latest_signal}
⏰ 數據範圍: {time_range}
📋 總數據點: {total_signals} 筆"""
        
        # 更新統計文本框
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
    
    def analyze_signals(self):
        """手動分析信號"""
        if self.current_data is None:
            messagebox.showwarning("警告", "沒有數據可分析")
            return
        
        self.auto_analyze_signals()
        messagebox.showinfo("分析完成", "交易信號分析已更新")
    
    def save_data(self):
        """導出數據到CSV文件"""
        if self.current_data is None:
            messagebox.showwarning("警告", "沒有數據可導出")
            return
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AImax/data/macd_7day_backtest_{timestamp}.csv"
            
            # 準備導出數據
            export_df = self.current_data.copy()
            export_df['datetime_str'] = export_df['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # 選擇要導出的欄位
            export_columns = ['datetime_str', 'close', 'macd_hist', 'macd', 'macd_signal', 
                            'volume', 'trading_signal', 'signal_type']
            export_df = export_df[export_columns]
            
            # 重命名欄位
            export_df.columns = ['時間', '價格', '柱狀圖', 'MACD線', '信號線', 
                               '成交量', '交易信號', '信號類型']
            
            # 導出到CSV
            export_df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            messagebox.showinfo("導出成功", f"數據已導出到: {filename}")
            
        except Exception as e:
            messagebox.showerror("導出失敗", f"導出數據時發生錯誤: {e}")
    
    def on_item_double_click(self, event):
        """處理表格項目雙擊事件"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            
            detail_text = f"""
數據詳情:
時間: {values[0]}
價格: {values[1]} TWD
柱狀圖: {values[2]}
MACD線: {values[3]}
信號線: {values[4]}
成交量: {values[5]}
交易信號: {values[6]}

信號說明:
🟢 買進: MACD柱為負時，MACD線突破信號線向上
🔴 賣出: MACD柱為正時，信號線突破MACD線向上
⚪ 持有: 無明確交易信號
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
        print("🚀 啟動增強版MACD回測分析器...")
        print("📋 7天歷史數據 + 交易信號檢測")
        print("🎯 基於已驗證的LiveMACDService計算邏輯")
        
        app = EnhancedMACDBacktestGUI()
        app.run()
    except Exception as e:
        print(f"❌ 程序運行錯誤: {e}")

if __name__ == "__main__":
    main()