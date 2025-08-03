#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
乾淨版1小時MACD回測GUI - 只保留最佳策略
基於improved_macd_backtest_gui.py，移除多餘的時間框架
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# 設置編碼
try:
    import locale
    locale.setlocale(locale.LC_ALL, 'zh_TW.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Chinese_Taiwan.65001')
    except:
        pass

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import threading
from datetime import datetime, timedelta
import json
import pandas as pd

# 導入核心模組
from src.data.live_macd_service import LiveMACDService
from src.core.improved_trading_signals import detect_improved_trading_signals

# 導入Telegram通知模組
from src.notifications.telegram_service import initialize_telegram_service, get_telegram_service
from config.telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, NOTIFICATION_SETTINGS

class CleanMACDBacktestGUI:
    """乾淨版1小時MACD回測GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("1小時MACD回測分析器 - 乾淨版 (含Telegram通知)")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # 數據存儲
        self.hourly_data = None
        self.hourly_statistics = None
        
        # 初始化Telegram服務
        self.telegram_service = None
        self.init_telegram()
        
        # 設置樣式
        self.setup_styles()
        
        # 創建界面
        self.create_widgets()
        
        # 初始化完成後載入數據
        self.data_loaded = False
        self.root.after(500, self.initial_load)
    
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
                               text="📈 1小時MACD回測分析器 - 最佳策略版", 
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
        
        # Telegram測試按鈕
        telegram_btn = ttk.Button(control_frame, text="📱 測試Telegram", 
                                command=self.test_telegram, style='Custom.TButton')
        telegram_btn.pack(side='left', padx=5)
        
        # 發送回測總結按鈕
        summary_btn = ttk.Button(control_frame, text="📊 發送總結", 
                               command=self.send_backtest_summary, style='Custom.TButton')
        summary_btn.pack(side='left', padx=5)
        
        # 狀態標籤
        self.status_label = ttk.Label(control_frame, text="準備就緒", style='Data.TLabel')
        self.status_label.pack(side='right', padx=5)
        
        # 主要內容區域
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 1小時MACD策略區域
        macd_frame = tk.LabelFrame(main_frame, text="1小時MACD策略 (最佳表現)", 
                                  bg='#f0f0f0', fg='#000080', font=('Arial', 12, 'bold'))
        macd_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 統計信息
        self.stats_text = tk.Text(macd_frame, height=6, bg='#ffffff', fg='#006400',
                                 font=('Consolas', 10), wrap='word')
        self.stats_text.pack(fill='x', padx=5, pady=5)
        
        # 交易表格
        table_frame = tk.Frame(macd_frame)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 表格欄位
        columns = ('時間', '價格', '柱狀圖', 'MACD線', '信號線', '交易信號', '持倉狀態', '序號')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # 設置欄位標題和寬度
        self.tree.heading('時間', text='時間')
        self.tree.heading('價格', text='價格')
        self.tree.heading('柱狀圖', text='柱狀圖')
        self.tree.heading('MACD線', text='MACD線')
        self.tree.heading('信號線', text='信號線')
        self.tree.heading('交易信號', text='交易信號')
        self.tree.heading('持倉狀態', text='持倉狀態')
        self.tree.heading('序號', text='序號')
        
        self.tree.column('時間', width=140)
        self.tree.column('價格', width=100)
        self.tree.column('柱狀圖', width=80)
        self.tree.column('MACD線', width=80)
        self.tree.column('信號線', width=80)
        self.tree.column('交易信號', width=200)
        self.tree.column('持倉狀態', width=80)
        self.tree.column('序號', width=60)
        
        # 滾動條
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 設置標籤顏色
        self.tree.tag_configure('buy_signal', background='#ccffcc')  # 淡綠色
        self.tree.tag_configure('sell_signal', background='#ffcccc')  # 淡紅色
        self.tree.tag_configure('normal', background='#ffffff')
    
    def init_telegram(self):
        """初始化Telegram服務"""
        try:
            self.telegram_service = initialize_telegram_service(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            
            # 測試連接
            if self.telegram_service.test_connection():
                print("✅ Telegram服務初始化成功")
            else:
                print("⚠️ Telegram連接測試失敗")
                
        except Exception as e:
            print(f"❌ Telegram服務初始化失敗: {e}")
            self.telegram_service = None
    
    def initial_load(self):
        """初始載入數據"""
        if not self.data_loaded:
            self.data_loaded = True
            self.load_data()
    
    def load_data(self):
        """載入1小時MACD數據"""
        def load_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                data = loop.run_until_complete(self.get_hourly_data())
                if data is not None:
                    self.hourly_data, self.hourly_statistics = data
                    self.root.after(0, self.update_table)
                    self.root.after(0, self.update_statistics)
            finally:
                loop.close()
        
        thread = threading.Thread(target=load_thread)
        thread.daemon = True
        thread.start()
    
    async def get_hourly_data(self):
        """獲取1小時MACD數據"""
        try:
            self.update_status("正在獲取1小時MACD數據...")
            
            service = LiveMACDService()
            
            # 獲取更多數據以獲得更好的回測結果
            klines = await service._fetch_klines("btctwd", "60", 1000)
            
            if klines is None:
                self.update_status("❌ 無法獲取歷史數據")
                await service.close()
                return None
            
            # 計算MACD
            macd_df = service._calculate_macd(klines, 12, 26, 9)
            
            if macd_df is None:
                self.update_status("❌ 無法計算MACD")
                await service.close()
                return None
            
            # 獲取最近500筆數據進行回測
            df = macd_df.tail(500).reset_index(drop=True)
            
            self.update_status("🎯 正在檢測1小時MACD交易信號...")
            
            # 應用MACD交易信號檢測
            df_with_signals, statistics = detect_improved_trading_signals(df)
            
            self.update_status(f"✅ 成功分析 {len(df_with_signals)} 筆數據，檢測到 {statistics['buy_count']} 個買進信號，{statistics['sell_count']} 個賣出信號")
            await service.close()
            return df_with_signals, statistics
            
        except Exception as e:
            self.update_status(f"❌ 獲取數據失敗: {e}")
            return None
    
    def update_table(self):
        """更新交易表格"""
        if self.hourly_data is None:
            return
        
        # 清空現有數據
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 從最新到最舊排序
        df_sorted = self.hourly_data.sort_values('timestamp', ascending=False)
        
        # 只顯示有交易信號的數據，並發送Telegram通知
        for _, row in df_sorted.iterrows():
            if row['signal_type'] in ['buy', 'sell']:
                datetime_str = row['datetime'].strftime('%Y-%m-%d %H:%M')
                price = f"{row['close']:,.0f}"
                hist = f"{row['macd_hist']:.2f}"
                macd = f"{row['macd']:.2f}"
                signal = f"{row['macd_signal']:.2f}"
                trading_signal = row['trading_signal']
                position_status = row['position_status']
                sequence = row['trade_sequence']
                
                # 根據交易信號設置標籤
                if row['signal_type'] == 'buy':
                    tag = 'buy_signal'
                elif row['signal_type'] == 'sell':
                    tag = 'sell_signal'
                else:
                    tag = 'normal'
                
                self.tree.insert('', 'end', 
                               values=(datetime_str, price, hist, macd, signal, 
                                     trading_signal, position_status, sequence), 
                               tags=(tag,))
                
                # 發送交易信號通知（僅最新的信號）
                if _ == df_sorted.index[0]:  # 只為最新的信號發送通知
                    self.send_trading_signal_notification(row.to_dict())
    
    def update_statistics(self):
        """更新統計信息"""
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
        
        # 計算信號頻率
        total_signals = self.hourly_statistics['buy_count'] + self.hourly_statistics['sell_count']
        signal_freq = (total_signals / len(self.hourly_data)) * 100 if len(self.hourly_data) > 0 else 0
        
        # 計算勝率
        win_rate = 0
        if self.hourly_statistics['complete_pairs'] > 0:
            winning_trades = sum(1 for pair in self.hourly_statistics.get('trade_pairs', []) 
                               if pair.get('profit', 0) > 0)
            win_rate = (winning_trades / self.hourly_statistics['complete_pairs']) * 100
        
        stats_text = f"""📊 1小時MACD策略統計 (最佳表現):
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
💵 總盈虧: {self.hourly_statistics['total_profit']:,.0f} TWD
📊 平均盈虧: {self.hourly_statistics['average_profit']:,.0f} TWD
🎯 勝率: {win_rate:.1f}%
⏱️ 平均持倉時間: {self.hourly_statistics['average_hold_time']:.1f} 小時"""
        
        # 更新統計文本框
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
    
    def save_data(self):
        """導出數據到CSV文件"""
        if self.hourly_data is None:
            messagebox.showwarning("警告", "沒有數據可導出")
            return
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AImax/data/clean_macd_backtest_{timestamp}.csv"
            
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
            stats_filename = f"AImax/data/clean_macd_statistics_{timestamp}.json"
            with open(stats_filename, 'w', encoding='utf-8') as f:
                json.dump(self.hourly_statistics, f, ensure_ascii=False, indent=2, default=str)
            
            messagebox.showinfo("導出成功", f"數據已導出到:\n{filename}\n{stats_filename}")
            
        except Exception as e:
            error_msg = str(e)
            messagebox.showerror("導出失敗", f"導出數據時發生錯誤: {error_msg}")
    
    def test_telegram(self):
        """測試Telegram連接"""
        if self.telegram_service:
            if self.telegram_service.test_connection():
                messagebox.showinfo("Telegram測試", "✅ Telegram連接測試成功！")
            else:
                messagebox.showerror("Telegram測試", "❌ Telegram連接測試失敗！")
        else:
            messagebox.showerror("Telegram測試", "❌ Telegram服務未初始化！")
    
    def send_backtest_summary(self):
        """發送回測總結到Telegram"""
        if not self.telegram_service:
            messagebox.showerror("錯誤", "Telegram服務未初始化！")
            return
        
        if not self.hourly_statistics:
            messagebox.showerror("錯誤", "沒有回測數據可發送！")
            return
        
        try:
            if self.telegram_service.send_backtest_summary(self.hourly_statistics):
                messagebox.showinfo("發送成功", "✅ 回測總結已發送到Telegram！")
            else:
                messagebox.showerror("發送失敗", "❌ 發送回測總結失敗！")
        except Exception as e:
            messagebox.showerror("發送錯誤", f"發送時發生錯誤: {e}")
    
    def send_trading_signal_notification(self, signal_data):
        """發送交易信號通知"""
        if not self.telegram_service or not NOTIFICATION_SETTINGS.get('send_trading_signals', False):
            return
        
        try:
            macd_data = {
                'hist': signal_data.get('macd_hist', 0),
                'macd': signal_data.get('macd', 0),
                'signal': signal_data.get('macd_signal', 0)
            }
            
            additional_info = f"📋 交易信號: {signal_data.get('trading_signal', '')}"
            
            self.telegram_service.send_trading_signal(
                signal_type=signal_data.get('signal_type', ''),
                price=signal_data.get('close', 0),
                sequence=signal_data.get('trade_sequence', 0),
                macd_data=macd_data,
                additional_info=additional_info
            )
        except Exception as e:
            print(f"發送交易信號通知失敗: {e}")
    
    def update_status(self, message):
        """更新狀態標籤"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
        
        # 發送系統狀態通知（僅重要狀態）
        if self.telegram_service and NOTIFICATION_SETTINGS.get('send_system_status', False):
            if any(keyword in message for keyword in ['成功', '失敗', '錯誤', '完成']):
                try:
                    self.telegram_service.send_system_status(message)
                except:
                    pass  # 靜默失敗，避免影響主程序
    
    def run(self):
        """運行GUI"""
        self.root.mainloop()

def main():
    """主函數"""
    try:
        print("啟動乾淨版1小時MACD回測分析器...")
        print("專注於最佳表現的策略")
        
        app = CleanMACDBacktestGUI()
        app.run()
    except Exception as e:
        print(f"程序運行錯誤: {e}")

if __name__ == "__main__":
    main()