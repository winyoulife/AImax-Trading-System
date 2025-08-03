#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
即時1小時MACD監控GUI - 結合回測和即時監控
每小時自動更新數據，檢測新的交易信號
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
import time
import numpy as np

# 導入核心模組
from src.data.live_macd_service import LiveMACDService
from src.core.improved_trading_signals import detect_improved_trading_signals
from src.notifications.telegram_service import TelegramService, initialize_telegram_service

class LiveMACDMonitorGUI:
    """即時1小時MACD監控GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("即時1小時MACD監控器 - 回測+即時監控")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # 數據存儲
        self.hourly_data = None
        self.hourly_statistics = None
        self.last_update_time = None
        self.monitoring_active = False
        self.update_timer = None
        self.last_signal_sequence = 0  # 記錄最後一個信號序號，避免重複通知
        
        # Telegram服務 - 預設用戶配置
        self.telegram_service = None
        self.telegram_enabled = False
        self.auto_setup_telegram()
        
        # 設置樣式
        self.setup_styles()
        
        # 創建界面
        self.create_widgets()
        
        # 初始載入
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
        
        style.configure('Live.TButton',
                       background='#90EE90',
                       foreground='#000000',
                       font=('Arial', 10, 'bold'))
        
        style.configure('Stop.TButton',
                       background='#FFB6C1',
                       foreground='#000000',
                       font=('Arial', 10, 'bold'))
    
    def create_widgets(self):
        """創建GUI組件"""
        # 主標題
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(fill='x', padx=10, pady=5)
        
        title_label = ttk.Label(title_frame, 
                               text="📈 即時1小時MACD監控器 - 回測+即時監控", 
                               style='Title.TLabel')
        title_label.pack(side='left')
        
        # 控制面板
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # 左側按鈕
        left_buttons = tk.Frame(control_frame, bg='#f0f0f0')
        left_buttons.pack(side='left')
        
        refresh_btn = ttk.Button(left_buttons, text="🔄 手動更新", 
                               command=self.manual_update, style='Custom.TButton')
        refresh_btn.pack(side='left', padx=5)
        
        self.monitor_btn = ttk.Button(left_buttons, text="🟢 開始即時監控", 
                                    command=self.toggle_monitoring, style='Live.TButton')
        self.monitor_btn.pack(side='left', padx=5)
        
        save_btn = ttk.Button(left_buttons, text="💾 導出數據", 
                            command=self.save_data, style='Custom.TButton')
        save_btn.pack(side='left', padx=5)
        
        telegram_btn = ttk.Button(left_buttons, text="📱 設置Telegram", 
                                command=self.setup_telegram, style='Custom.TButton')
        telegram_btn.pack(side='left', padx=5)
        
        # 右側狀態信息
        right_status = tk.Frame(control_frame, bg='#f0f0f0')
        right_status.pack(side='right')
        
        self.status_label = ttk.Label(right_status, text="準備就緒", style='Data.TLabel')
        self.status_label.pack(side='right', padx=5)
        
        self.last_update_label = ttk.Label(right_status, text="", style='Data.TLabel')
        self.last_update_label.pack(side='right', padx=10)
        
        # 監控狀態面板
        monitor_frame = tk.Frame(self.root, bg='#f0f0f0')
        monitor_frame.pack(fill='x', padx=10, pady=5)
        
        monitor_info_frame = tk.LabelFrame(monitor_frame, text="即時監控狀態", 
                                         bg='#f0f0f0', fg='#800080', font=('Arial', 10, 'bold'))
        monitor_info_frame.pack(fill='x', padx=5, pady=2)
        
        self.monitor_status_text = tk.Text(monitor_info_frame, height=3, bg='#fff8dc', fg='#800080',
                                         font=('Consolas', 9), wrap='word')
        self.monitor_status_text.pack(fill='x', padx=5, pady=3)
        
        # 主要內容區域
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 1小時MACD策略區域
        macd_frame = tk.LabelFrame(main_frame, text="1小時MACD策略 - 即時監控", 
                                  bg='#f0f0f0', fg='#000080', font=('Arial', 12, 'bold'))
        macd_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 統計信息
        self.stats_text = tk.Text(macd_frame, height=7, bg='#ffffff', fg='#006400',
                                 font=('Consolas', 10), wrap='word')
        self.stats_text.pack(fill='x', padx=5, pady=5)
        
        # 交易表格
        table_frame = tk.Frame(macd_frame)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 表格欄位
        columns = ('時間', '價格', '柱狀圖', 'MACD線', '信號線', '交易信號', '持倉狀態', '序號')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=18)
        
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
        self.tree.tag_configure('latest', background='#ffffcc')  # 最新數據用黃色
        self.tree.tag_configure('normal', background='#ffffff')
    
    def initial_load(self):
        """初始載入數據"""
        if not self.data_loaded:
            self.data_loaded = True
            self.load_data()
    
    def manual_update(self):
        """手動更新數據"""
        self.load_data()
    
    def toggle_monitoring(self):
        """切換即時監控狀態"""
        if not self.monitoring_active:
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def start_monitoring(self):
        """開始即時監控"""
        self.monitoring_active = True
        self.monitor_btn.config(text="🔴 停止監控", style='Stop.TButton')
        self.update_monitor_status("🟢 即時監控已啟動 - 每小時自動更新")
        self.schedule_next_update()
    
    def stop_monitoring(self):
        """停止即時監控"""
        self.monitoring_active = False
        self.monitor_btn.config(text="🟢 開始即時監控", style='Live.TButton')
        self.update_monitor_status("⚪ 即時監控已停止")
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
            self.update_timer = None
    
    def schedule_next_update(self):
        """安排下次更新"""
        if not self.monitoring_active:
            return
        
        # 計算到下個整點小時的時間
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        seconds_until_next_hour = (next_hour - now).total_seconds()
        
        # 轉換為毫秒
        ms_until_next_hour = int(seconds_until_next_hour * 1000)
        
        # 安排更新
        self.update_timer = self.root.after(ms_until_next_hour, self.auto_update)
        
        # 更新狀態顯示
        next_update_str = next_hour.strftime('%H:%M')
        self.update_monitor_status(f"🟢 即時監控中 - 下次更新: {next_update_str}")
    
    def auto_update(self):
        """自動更新"""
        if self.monitoring_active:
            self.update_monitor_status("🔄 正在自動更新數據...")
            self.load_data()
            # 安排下次更新
            self.schedule_next_update()
    
    def load_data(self):
        """載入1小時MACD數據"""
        def load_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                data = loop.run_until_complete(self.get_hourly_data())
                if data is not None:
                    self.hourly_data, self.hourly_statistics = data
                    self.last_update_time = datetime.now()
                    self.root.after(0, self.update_table)
                    self.root.after(0, self.update_statistics)
                    self.root.after(0, self.update_last_update_display)
                    
                    # 檢查是否有新信號
                    self.root.after(0, self.check_new_signals)
            finally:
                loop.close()
        
        thread = threading.Thread(target=load_thread)
        thread.daemon = True
        thread.start()
    
    async def get_hourly_data(self):
        """獲取1小時MACD數據"""
        try:
            self.update_status("正在獲取最新1小時MACD數據...")
            
            service = LiveMACDService()
            
            # 獲取更多數據以獲得更好的分析結果
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
            
            # 獲取最近500筆數據進行分析
            df = macd_df.tail(500).reset_index(drop=True)
            
            self.update_status("🎯 正在分析1小時MACD交易信號...")
            
            # 應用MACD交易信號檢測
            df_with_signals, statistics = detect_improved_trading_signals(df)
            
            self.update_status(f"✅ 數據更新完成 - {len(df_with_signals)} 筆數據，{statistics['buy_count']} 買進，{statistics['sell_count']} 賣出")
            await service.close()
            return df_with_signals, statistics
            
        except Exception as e:
            self.update_status(f"❌ 獲取數據失敗: {e}")
            return None
    
    def check_new_signals(self):
        """檢查是否有新的交易信號"""
        if self.hourly_data is None or len(self.hourly_data) == 0:
            return
        
        # 獲取最新的信號
        latest_row = self.hourly_data.iloc[-1]
        
        if latest_row['signal_type'] in ['buy', 'sell'] and latest_row['trade_sequence'] > self.last_signal_sequence:
            signal_type = '買進' if latest_row['signal_type'] == 'buy' else '賣出'
            price = latest_row['close']
            time_str = latest_row['datetime'].strftime('%Y-%m-%d %H:%M')
            sequence = latest_row['trade_sequence']
            
            # 更新最後信號序號
            self.last_signal_sequence = sequence
            
            # 進行詳細信號分析
            analysis = self.analyze_signal_details(latest_row)
            
            # 顯示新信號通知
            notification = f"🚨 新{signal_type}信號！\n時間: {time_str}\n價格: {price:,.0f} TWD\n序號: {sequence}\n{analysis['summary']}"
            self.update_monitor_status(notification)
            
            # 發送Telegram通知
            if self.telegram_enabled and self.telegram_service:
                self.send_telegram_signal_notification(latest_row, analysis)
            
            # 控制台輸出
            print(f"[{datetime.now()}] {notification}")
    
    def analyze_signal_details(self, signal_row):
        """詳細分析交易信號"""
        analysis = {
            'summary': '',
            'strength': '',
            'risk_level': '',
            'recommendation': '',
            'technical_details': {}
        }
        
        try:
            # 獲取MACD數據
            macd_hist = signal_row['macd_hist']
            macd_line = signal_row['macd']
            signal_line = signal_row['macd_signal']
            price = signal_row['close']
            
            # 計算信號強度
            hist_abs = abs(macd_hist)
            if hist_abs > 50:
                strength = "強"
                strength_emoji = "🔥"
            elif hist_abs > 20:
                strength = "中"
                strength_emoji = "⚡"
            else:
                strength = "弱"
                strength_emoji = "💫"
            
            analysis['strength'] = f"{strength_emoji} {strength}"
            
            # 分析趨勢
            if signal_row['signal_type'] == 'buy':
                # 買進信號分析
                if macd_hist > 0:
                    trend_status = "MACD柱狀圖轉正，動能增強"
                else:
                    trend_status = "MACD柱狀圖仍為負，但開始收斂"
                
                # 風險評估
                if macd_line < -100:
                    risk_level = "🟢 低風險 - 深度超賣反彈"
                elif macd_line < -50:
                    risk_level = "🟡 中風險 - 超賣區域"
                else:
                    risk_level = "🔴 高風險 - 高位買進"
                    
            else:
                # 賣出信號分析
                if macd_hist < 0:
                    trend_status = "MACD柱狀圖轉負，動能減弱"
                else:
                    trend_status = "MACD柱狀圖仍為正，但開始收斂"
                
                # 風險評估
                if macd_line > 100:
                    risk_level = "🟢 低風險 - 高位超買回調"
                elif macd_line > 50:
                    risk_level = "🟡 中風險 - 超買區域"
                else:
                    risk_level = "🔴 高風險 - 低位賣出"
            
            analysis['risk_level'] = risk_level
            analysis['technical_details'] = {
                'trend_status': trend_status,
                'macd_divergence': abs(macd_line - signal_line),
                'histogram_momentum': macd_hist
            }
            
            # 生成建議
            if "低風險" in risk_level and "強" in strength:
                recommendation = "💎 優質信號，建議執行"
            elif "中風險" in risk_level:
                recommendation = "⚖️ 謹慎觀察，適量操作"
            else:
                recommendation = "⚠️ 高風險信號，建議觀望"
            
            analysis['recommendation'] = recommendation
            
            # 生成摘要
            analysis['summary'] = f"信號強度: {analysis['strength']}\n{risk_level}\n{recommendation}"
            
        except Exception as e:
            analysis['summary'] = f"分析錯誤: {str(e)}"
            
        return analysis
    
    def setup_telegram(self):
        """設置Telegram通知"""
        dialog = TelegramSetupDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            bot_token, chat_id = dialog.result
            try:
                self.telegram_service = initialize_telegram_service(bot_token, chat_id)
                
                # 測試連接
                if self.telegram_service.test_connection():
                    self.telegram_enabled = True
                    messagebox.showinfo("成功", "Telegram通知設置成功！")
                    self.update_monitor_status("✅ Telegram通知已啟用")
                else:
                    messagebox.showerror("錯誤", "Telegram連接測試失敗，請檢查設置")
                    
            except Exception as e:
                messagebox.showerror("錯誤", f"Telegram設置失敗: {str(e)}")
    
    def send_telegram_signal_notification(self, signal_row, analysis):
        """發送Telegram信號通知"""
        try:
            macd_data = {
                'hist': signal_row['macd_hist'],
                'macd': signal_row['macd'],
                'signal': signal_row['macd_signal']
            }
            
            # 構建詳細信息
            additional_info = f"""
📊 <b>信號分析</b>:
{analysis['summary']}

🔍 <b>技術細節</b>:
• {analysis['technical_details'].get('trend_status', '')}
• MACD背離度: {analysis['technical_details'].get('macd_divergence', 0):.2f}
• 柱狀圖動能: {analysis['technical_details'].get('histogram_momentum', 0):.2f}

💡 <b>操作建議</b>: {analysis['recommendation']}
            """.strip()
            
            self.telegram_service.send_trading_signal(
                signal_row['signal_type'],
                signal_row['close'],
                signal_row['trade_sequence'],
                macd_data,
                additional_info
            )
            
        except Exception as e:
            print(f"發送Telegram通知失敗: {e}")
    
    def auto_setup_telegram(self):
        """自動設置用戶的Telegram配置"""
        try:
            # 用戶的Telegram設置
            bot_token = "7323086952:AAE5fkQp8n98TOYnPpj2KPyrCI6hX5R2n2I"
            chat_id = "8164385222"
            
            self.telegram_service = initialize_telegram_service(bot_token, chat_id)
            self.telegram_enabled = True
            
            print("✅ Telegram通知已自動啟用")
            
        except Exception as e:
            print(f"⚠️ Telegram自動設置失敗: {e}")
            self.telegram_enabled = False
    
    def update_table(self):
        """更新交易表格"""
        if self.hourly_data is None:
            return
        
        # 清空現有數據
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 從最新到最舊排序
        df_sorted = self.hourly_data.sort_values('timestamp', ascending=False)
        
        # 只顯示有交易信號的數據
        for i, (_, row) in enumerate(df_sorted.iterrows()):
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
                
                # 最新的信號用特殊顏色標記
                if i == 0:  # 最新的一筆
                    tag = 'latest'
                
                self.tree.insert('', 'end', 
                               values=(datetime_str, price, hist, macd, signal, 
                                     trading_signal, position_status, sequence), 
                               tags=(tag,))
    
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
        
        # 監控狀態
        monitor_status = "🟢 即時監控中" if self.monitoring_active else "⚪ 手動模式"
        
        stats_text = f"""📊 1小時MACD策略統計 - {monitor_status}:
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
    
    def update_last_update_display(self):
        """更新最後更新時間顯示"""
        if self.last_update_time:
            update_str = self.last_update_time.strftime('%H:%M:%S')
            self.last_update_label.config(text=f"最後更新: {update_str}")
    
    def update_monitor_status(self, message):
        """更新監控狀態"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        status_message = f"[{timestamp}] {message}"
        
        self.monitor_status_text.delete(1.0, tk.END)
        self.monitor_status_text.insert(1.0, status_message)
    
    def save_data(self):
        """導出數據到CSV文件"""
        if self.hourly_data is None:
            messagebox.showwarning("警告", "沒有數據可導出")
            return
        
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"AImax/data/live_macd_monitor_{timestamp}.csv"
            
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
            stats_filename = f"AImax/data/live_macd_statistics_{timestamp}.json"
            with open(stats_filename, 'w', encoding='utf-8') as f:
                json.dump(self.hourly_statistics, f, ensure_ascii=False, indent=2, default=str)
            
            messagebox.showinfo("導出成功", f"數據已導出到:\n{filename}\n{stats_filename}")
            
        except Exception as e:
            error_msg = str(e)
            messagebox.showerror("導出失敗", f"導出數據時發生錯誤: {error_msg}")
    
    def update_status(self, message):
        """更新狀態標籤"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def on_closing(self):
        """關閉程序時的清理工作"""
        if self.monitoring_active:
            self.stop_monitoring()
        self.root.destroy()
    
    def run(self):
        """運行GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

class TelegramSetupDialog:
    """Telegram設置對話框"""
    
    def __init__(self, parent):
        self.result = None
        
        # 創建對話框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Telegram通知設置")
        self.dialog.geometry("500x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中顯示
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.create_widgets()
    
    def create_widgets(self):
        """創建對話框組件"""
        # 標題
        title_label = tk.Label(self.dialog, text="📱 Telegram通知設置", 
                              font=('Arial', 14, 'bold'), fg='#000080')
        title_label.pack(pady=10)
        
        # 說明
        info_text = """
設置Telegram通知以接收即時交易信號：

1. 創建Telegram Bot並獲取Bot Token
2. 獲取你的Chat ID
3. 填入下方表單並測試連接
        """.strip()
        
        info_label = tk.Label(self.dialog, text=info_text, justify='left', fg='#333333')
        info_label.pack(pady=5)
        
        # 輸入框架
        input_frame = tk.Frame(self.dialog)
        input_frame.pack(pady=20, padx=20, fill='x')
        
        # Bot Token
        tk.Label(input_frame, text="Bot Token:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
        self.token_entry = tk.Entry(input_frame, width=50, font=('Consolas', 9))
        self.token_entry.grid(row=0, column=1, pady=5, padx=(10, 0))
        
        # Chat ID
        tk.Label(input_frame, text="Chat ID:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='w', pady=5)
        self.chat_id_entry = tk.Entry(input_frame, width=50, font=('Consolas', 9))
        self.chat_id_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        
        # 按鈕框架
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        # 測試按鈕
        test_btn = tk.Button(button_frame, text="🔧 測試連接", 
                           command=self.test_connection, 
                           bg='#90EE90', font=('Arial', 10))
        test_btn.pack(side='left', padx=5)
        
        # 確定按鈕
        ok_btn = tk.Button(button_frame, text="✅ 確定", 
                         command=self.ok_clicked, 
                         bg='#87CEEB', font=('Arial', 10))
        ok_btn.pack(side='left', padx=5)
        
        # 取消按鈕
        cancel_btn = tk.Button(button_frame, text="❌ 取消", 
                             command=self.cancel_clicked, 
                             bg='#FFB6C1', font=('Arial', 10))
        cancel_btn.pack(side='left', padx=5)
    
    def test_connection(self):
        """測試Telegram連接"""
        bot_token = self.token_entry.get().strip()
        chat_id = self.chat_id_entry.get().strip()
        
        if not bot_token or not chat_id:
            messagebox.showwarning("警告", "請填入Bot Token和Chat ID")
            return
        
        try:
            # 創建臨時服務進行測試
            test_service = TelegramService(bot_token, chat_id)
            
            if test_service.test_connection():
                messagebox.showinfo("成功", "Telegram連接測試成功！")
            else:
                messagebox.showerror("失敗", "Telegram連接測試失敗，請檢查設置")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"測試連接時發生錯誤: {str(e)}")
    
    def ok_clicked(self):
        """確定按鈕點擊"""
        bot_token = self.token_entry.get().strip()
        chat_id = self.chat_id_entry.get().strip()
        
        if not bot_token or not chat_id:
            messagebox.showwarning("警告", "請填入Bot Token和Chat ID")
            return
        
        self.result = (bot_token, chat_id)
        self.dialog.destroy()
    
    def cancel_clicked(self):
        """取消按鈕點擊"""
        self.dialog.destroy()

def main():
    """主函數"""
    try:
        print("啟動即時1小時MACD監控器...")
        print("結合回測和即時監控功能")
        print("支援Telegram通知和詳細信號分析")
        
        app = LiveMACDMonitorGUI()
        app.run()
    except Exception as e:
        print(f"程序運行錯誤: {e}")

if __name__ == "__main__":
    main()