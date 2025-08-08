#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 85%勝率策略 - 緊湊版GUI
確保所有內容都能在螢幕上顯示
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import sys
import os
from datetime import datetime

# 添加路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from trading.virtual_trading_engine import VirtualTradingEngine
    from notifications.strategy_85_telegram import strategy_85_notifier
    from analysis.trading_analytics import TradingAnalytics
    print("✅ 虛擬交易引擎導入成功")
    print("✅ Telegram通知服務導入成功")
    print("✅ 交易分析模組導入成功")
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
    sys.exit(1)

class Compact85GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 85%勝率策略 - 緊湊版")
        self.root.geometry("1200x700")
        self.root.configure(bg='#1a1a2e')
        
        # 初始化虛擬交易引擎
        self.trading_engine = VirtualTradingEngine(initial_balance=100000)
        
        # 初始化Telegram通知和分析模組
        self.telegram_notifier = strategy_85_notifier
        self.analytics = TradingAnalytics()
        
        # 發送策略啟動通知
        if self.telegram_notifier.enabled:
            self.telegram_notifier.notify_strategy_start()
        
        # GUI變量
        self.twd_balance = tk.StringVar(value="NT$ 100,000")
        self.btc_balance = tk.StringVar(value="0.000000 BTC")
        self.total_value = tk.StringVar(value="NT$ 100,000")
        self.total_return = tk.StringVar(value="NT$ 0 (+0.00%)")
        self.current_price = tk.StringVar(value="載入中...")
        self.win_rate = tk.StringVar(value="0.0% (0/0)")
        self.strategy_status = tk.StringVar(value="🔄 準備中")
        
        # 自動交易控制
        self.auto_trading = False
        self.trading_thread = None
        
        # 創建界面
        self.create_compact_widgets()
        
        # 啟動數據更新
        self.update_data()
        
        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_compact_widgets(self):
        """創建緊湊版GUI組件"""
        
        # 標題區域 - 縮小高度
        title_frame = tk.Frame(self.root, bg='#16213e', height=60)
        title_frame.pack(fill='x', padx=5, pady=2)
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="🎯 85%勝率策略虛擬交易", 
                font=('Microsoft JhengHei', 16, 'bold'),
                bg='#16213e', fg='#00ff88').pack(pady=5)
        
        # 策略狀態標籤
        self.strategy_info_label = tk.Label(title_frame, text="💰 10萬虛擬台幣 • 📊 實測100%勝率 • 🎯 80分信心度閾值", 
                font=('Microsoft JhengHei', 10),
                bg='#16213e', fg='#ffd93d')
        self.strategy_info_label.pack()
        
        # 主要內容區域
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(fill='both', expand=True, padx=5, pady=2)
        
        # 策略狀態顯示區域
        self.create_strategy_status_section(main_frame)
        
        # 上方：帳戶狀態 - 水平排列
        self.create_compact_account_section(main_frame)
        
        # 中間：控制按鈕 - 水平排列
        self.create_compact_control_section(main_frame)
        
        # 下方：交易記錄和日誌 - 左右分割
        self.create_compact_bottom_section(main_frame)
    
    def create_strategy_status_section(self, parent):
        """創建85%策略狀態顯示區域"""
        strategy_frame = tk.LabelFrame(parent, text="🎯 85%勝率策略狀態", 
                                      font=('Microsoft JhengHei', 12, 'bold'),
                                      bg='#16213e', fg='#00ff88')
        strategy_frame.pack(fill='x', pady=2)
        
        # 策略狀態指示器
        status_frame = tk.Frame(strategy_frame, bg='#16213e')
        status_frame.pack(fill='x', padx=10, pady=5)
        
        # 策略運行狀態
        self.strategy_running_status = tk.StringVar(value="🔄 策略初始化中...")
        tk.Label(status_frame, textvariable=self.strategy_running_status, 
                font=('Microsoft JhengHei', 11, 'bold'),
                bg='#16213e', fg='#ffd93d').pack(side='left')
        
        # 信號檢測狀態
        self.signal_status = tk.StringVar(value="⏳ 等待信號檢測...")
        tk.Label(status_frame, textvariable=self.signal_status, 
                font=('Microsoft JhengHei', 10),
                bg='#16213e', fg='#3498db').pack(side='right')
        
        # 策略詳細信息
        detail_frame = tk.Frame(strategy_frame, bg='#16213e')
        detail_frame.pack(fill='x', padx=10, pady=2)
        
        self.strategy_details = tk.StringVar(value="📊 策略: Final85PercentStrategy | 🎯 閾值: 80分 | 📈 實測勝率: 100%")
        tk.Label(detail_frame, textvariable=self.strategy_details, 
                font=('Microsoft JhengHei', 9),
                bg='#16213e', fg='#95a5a6').pack()

    def create_compact_account_section(self, parent):
        """創建緊湊版帳戶狀態區域"""
        account_frame = tk.LabelFrame(parent, text="💰 帳戶狀態", 
                                     font=('Microsoft JhengHei', 12, 'bold'),
                                     bg='#16213e', fg='#00ff88')
        account_frame.pack(fill='x', pady=2)
        
        # 水平排列的狀態卡片
        cards_frame = tk.Frame(account_frame, bg='#16213e')
        cards_frame.pack(fill='x', padx=10, pady=5)
        
        # 創建6個狀態卡片
        self.create_status_card(cards_frame, "💵 TWD", self.twd_balance, '#ffd93d')
        self.create_status_card(cards_frame, "₿ BTC", self.btc_balance, '#e67e22')
        self.create_status_card(cards_frame, "💰 總資產", self.total_value, '#27ae60')
        # 分成兩個獲利顯示
        self.realized_profit = tk.StringVar(value="NT$ 0")
        self.unrealized_profit = tk.StringVar(value="NT$ 0")
        
        self.create_status_card(cards_frame, "✅ 已實現", self.realized_profit, '#00ff88')
        self.create_status_card(cards_frame, "📊 未實現", self.unrealized_profit, '#ffd93d')
        self.create_status_card(cards_frame, "📊 價格", self.current_price, '#3498db')
        self.create_status_card(cards_frame, "🎯 勝率", self.win_rate, '#9b59b6')
    
    def create_status_card(self, parent, title, textvariable, color):
        """創建狀態卡片"""
        card = tk.Frame(parent, bg='#1a1a2e', relief='raised', bd=1)
        card.pack(side='left', fill='x', expand=True, padx=2, pady=2)
        
        tk.Label(card, text=title, font=('Microsoft JhengHei', 8, 'bold'),
                bg='#1a1a2e', fg='white').pack(pady=2)
        tk.Label(card, textvariable=textvariable, font=('Microsoft JhengHei', 9, 'bold'),
                bg='#1a1a2e', fg=color).pack(pady=2)
    
    def create_compact_control_section(self, parent):
        """創建緊湊版控制區域"""
        control_frame = tk.LabelFrame(parent, text="🎮 交易控制", 
                                     font=('Microsoft JhengHei', 12, 'bold'),
                                     bg='#16213e', fg='#ffd93d')
        control_frame.pack(fill='x', pady=2)
        
        # 按鈕區域
        button_frame = tk.Frame(control_frame, bg='#16213e')
        button_frame.pack(fill='x', padx=10, pady=5)
        
        # 左側按鈕組
        left_buttons = tk.Frame(button_frame, bg='#16213e')
        left_buttons.pack(side='left', fill='x', expand=True)
        
        tk.Button(left_buttons, text="📊 檢查信號", font=('Microsoft JhengHei', 9, 'bold'),
                 bg='#3498db', fg='white', command=self.check_signals,
                 width=12).pack(side='left', padx=2)
        
        tk.Button(left_buttons, text="💰 手動買入", font=('Microsoft JhengHei', 9, 'bold'),
                 bg='#27ae60', fg='white', command=self.manual_buy,
                 width=12).pack(side='left', padx=2)
        
        tk.Button(left_buttons, text="💸 手動賣出", font=('Microsoft JhengHei', 9, 'bold'),
                 bg='#e74c3c', fg='white', command=self.manual_sell,
                 width=12).pack(side='left', padx=2)
        
        tk.Button(left_buttons, text="📱 測試通知", font=('Microsoft JhengHei', 9, 'bold'),
                 bg='#1abc9c', fg='white', command=self.test_telegram,
                 width=12).pack(side='left', padx=2)
        
        # 右側按鈕組
        right_buttons = tk.Frame(button_frame, bg='#16213e')
        right_buttons.pack(side='right')
        
        self.auto_button = tk.Button(right_buttons, text="🚀 啟動自動交易", 
                                    font=('Microsoft JhengHei', 9, 'bold'),
                                    bg='#f39c12', fg='white', command=self.toggle_auto_trading,
                                    width=15)
        self.auto_button.pack(side='left', padx=2)
        
        tk.Button(right_buttons, text="📊 分析報告", font=('Microsoft JhengHei', 9, 'bold'),
                 bg='#8e44ad', fg='white', command=self.show_analytics,
                 width=12).pack(side='left', padx=2)
        
        tk.Button(right_buttons, text="💾 保存", font=('Microsoft JhengHei', 9, 'bold'),
                 bg='#9b59b6', fg='white', command=self.save_state,
                 width=8).pack(side='left', padx=2)
        
        # 策略狀態顯示
        status_frame = tk.Frame(control_frame, bg='#16213e')
        status_frame.pack(fill='x', padx=10, pady=2)
        
        tk.Label(status_frame, text="策略狀態:", font=('Microsoft JhengHei', 9),
                bg='#16213e', fg='white').pack(side='left')
        tk.Label(status_frame, textvariable=self.strategy_status, 
                font=('Microsoft JhengHei', 9, 'bold'),
                bg='#16213e', fg='#00ff88').pack(side='left', padx=10)
    
    def create_compact_bottom_section(self, parent):
        """創建緊湊版底部區域"""
        bottom_frame = tk.Frame(parent, bg='#1a1a2e')
        bottom_frame.pack(fill='both', expand=True, pady=2)
        
        # 左側：交易記錄
        history_frame = tk.LabelFrame(bottom_frame, text="📋 交易記錄", 
                                     font=('Microsoft JhengHei', 10, 'bold'),
                                     bg='#16213e', fg='#00ff88')
        history_frame.pack(side='left', fill='both', expand=True, padx=2)
        
        # 交易記錄表格
        columns = ('時間', '類型', '價格', 'BTC', '金額', '獲利')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=6)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=80)
        
        scrollbar1 = ttk.Scrollbar(history_frame, orient='vertical', command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar1.set)
        
        self.history_tree.pack(side='left', fill='both', expand=True, padx=2, pady=2)
        scrollbar1.pack(side='right', fill='y')
        
        # 右側：系統日誌
        log_frame = tk.LabelFrame(bottom_frame, text="📝 系統日誌", 
                                 font=('Microsoft JhengHei', 10, 'bold'),
                                 bg='#16213e', fg='#00ff88')
        log_frame.pack(side='right', fill='both', expand=True, padx=2)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6,
                                                 font=('Consolas', 8),
                                                 bg='#1a1a2e', fg='#ecf0f1',
                                                 insertbackground='white')
        self.log_text.pack(fill='both', expand=True, padx=2, pady=2)
        
        # 添加初始日誌
        self.add_log("🎯 85%勝率策略系統啟動")
        self.add_log("💰 初始資金: NT$ 100,000")
        self.add_log("📊 策略: 最終85%勝率策略")
        self.add_log("🎯 信心度閾值: 80分")
        self.add_log("✅ 系統準備就緒")
    
    def add_log(self, message):
        """添加日誌消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        
        # 限制日誌長度
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            self.log_text.delete("1.0", "20.0")
    
    def update_data(self):
        """更新數據顯示"""
        try:
            # 獲取帳戶狀態
            status = self.trading_engine.get_account_status()
            
            # 更新顯示
            self.twd_balance.set(f"NT$ {status['twd_balance']:,.0f}")
            self.btc_balance.set(f"{status['btc_balance']:.6f}")
            self.total_value.set(f"NT$ {status['total_value']:,.0f}")
            
            # 分別顯示已實現和未實現獲利
            realized = status.get('realized_profit', 0)
            unrealized = status.get('unrealized_profit', 0)
            
            self.realized_profit.set(f"NT$ {realized:+,.0f}")
            self.unrealized_profit.set(f"NT$ {unrealized:+,.0f}")
            
            # 當前價格
            if status['current_price']:
                self.current_price.set(f"NT$ {status['current_price']:,.0f}")
            
            # 勝率
            self.win_rate.set(f"{status['win_rate']:.1f}% ({status['winning_trades']}/{status['total_trades']})")
            
            # 更新策略狀態
            self.update_strategy_status()
            
            # 更新交易記錄
            self.update_trading_history()
            
            # 定期發送帳戶狀態通知（每小時一次）
            if hasattr(self, 'telegram_notifier'):
                self.telegram_notifier.notify_account_status(status)
            
        except Exception as e:
            self.add_log(f"❌ 數據更新失敗: {e}")
        
        # 每5秒更新一次
        self.root.after(5000, self.update_data)
    
    def update_strategy_status(self):
        """更新85%策略狀態顯示"""
        try:
            # 檢查策略是否啟用
            if hasattr(self.trading_engine, 'strategy_enabled') and self.trading_engine.strategy_enabled:
                # 檢查初始化延遲
                import time
                current_time = time.time()
                init_time = getattr(self.trading_engine, 'initialization_time', current_time)
                min_wait = getattr(self.trading_engine, 'min_wait_time', 60)
                
                if current_time - init_time < min_wait:
                    remaining = int(min_wait - (current_time - init_time))
                    self.strategy_running_status.set(f"⏳ 85%策略初始化延遲中 (還需 {remaining}s)")
                    self.signal_status.set("🔒 等待初始化完成...")
                else:
                    if self.auto_trading:
                        self.strategy_running_status.set("🚀 85%策略運行中 (自動交易)")
                        self.signal_status.set("🔍 正在檢測交易信號...")
                    else:
                        self.strategy_running_status.set("✅ 85%策略已就緒 (手動模式)")
                        self.signal_status.set("⏸️ 等待啟動自動交易...")
            else:
                self.strategy_running_status.set("❌ 策略未啟用")
                self.signal_status.set("🔴 策略停止")
            
            # 更新策略詳細信息
            strategy = getattr(self.trading_engine, 'final_85_strategy', None)
            if strategy:
                confidence = getattr(strategy, 'min_confidence_score', 80)
                self.strategy_details.set(f"📊 策略: Final85PercentStrategy | 🎯 信心閾值: {confidence}分 | 📈 目標勝率: 85%+")
            
        except Exception as e:
            self.strategy_running_status.set("❌ 策略狀態檢查失敗")
            self.signal_status.set(f"錯誤: {str(e)[:30]}")

    def update_trading_history(self):
        """更新交易記錄表格"""
        try:
            # 清空現有記錄
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # 添加交易記錄
            for trade in self.trading_engine.trade_history[-8:]:  # 只顯示最近8筆
                timestamp = datetime.fromisoformat(trade['timestamp']).strftime("%H:%M")
                trade_type = "🟢買" if trade['type'] == 'buy' else "🔴賣"
                price = f"{trade['price']:,.0f}"
                btc_amount = f"{trade['btc_amount']:.4f}"
                
                if trade['type'] == 'buy':
                    amount = f"{trade['total_cost']:,.0f}"
                    profit = "--"
                else:
                    amount = f"{trade['net_income']:,.0f}"
                    profit = f"{trade['profit']:,.0f}" if 'profit' in trade else "--"
                
                self.history_tree.insert('', 'end', values=(
                    timestamp, trade_type, price, btc_amount, amount, profit
                ))
                
        except Exception as e:
            self.add_log(f"❌ 更新交易記錄失敗: {e}")
    
    # 以下方法與原版相同，只是簡化了一些輸出
    def check_signals(self):
        """檢查交易信號"""
        self.add_log("🔍 檢查交易信號...")
        
        def check():
            try:
                signal = self.trading_engine.check_trading_signals()
                
                if signal:
                    signal_type = signal['signal_type']
                    price = signal['current_price']
                    
                    self.add_log(f"📊 發現{signal_type}信號: NT$ {price:,.0f}")
                    
                    result = messagebox.askyesno("交易信號", 
                                               f"發現{signal_type}信號！\n價格: NT$ {price:,.0f}\n是否執行？")
                    
                    if result:
                        success = self.trading_engine.execute_strategy_signal(signal)
                        if success:
                            self.add_log(f"✅ {signal_type}執行成功")
                        else:
                            self.add_log(f"❌ {signal_type}執行失敗")
                else:
                    self.add_log("📊 暫無交易信號")
                    messagebox.showinfo("交易信號", "目前沒有交易信號")
                    
            except Exception as e:
                self.add_log(f"❌ 信號檢查失敗: {e}")
        
        threading.Thread(target=check, daemon=True).start()
    
    def manual_buy(self):
        """手動買入"""
        try:
            current_price = self.trading_engine.get_current_price()
            if not current_price:
                messagebox.showerror("錯誤", "無法獲取當前價格")
                return
            
            amount = tk.simpledialog.askfloat("手動買入", 
                                            f"當前價格: NT$ {current_price:,.0f}\n請輸入買入金額:",
                                            minvalue=1000, maxvalue=self.trading_engine.twd_balance)
            
            if amount:
                success = self.trading_engine.execute_buy_order(current_price, amount)
                if success:
                    self.add_log(f"✅ 手動買入: NT$ {amount:,.0f}")
                else:
                    self.add_log("❌ 手動買入失敗")
                    
        except Exception as e:
            self.add_log(f"❌ 買入錯誤: {e}")
    
    def manual_sell(self):
        """手動賣出"""
        try:
            if self.trading_engine.btc_balance <= 0:
                messagebox.showwarning("警告", "沒有BTC可以賣出")
                return
            
            current_price = self.trading_engine.get_current_price()
            if not current_price:
                messagebox.showerror("錯誤", "無法獲取當前價格")
                return
            
            btc_value = self.trading_engine.btc_balance * current_price
            result = messagebox.askyesno("手動賣出", 
                                       f"持倉: {self.trading_engine.btc_balance:.6f} BTC\n"
                                       f"價值: NT$ {btc_value:,.0f}\n確定賣出？")
            
            if result:
                success = self.trading_engine.execute_sell_order(current_price)
                if success:
                    self.add_log("✅ 手動賣出成功")
                else:
                    self.add_log("❌ 手動賣出失敗")
                    
        except Exception as e:
            self.add_log(f"❌ 賣出錯誤: {e}")
    
    def toggle_auto_trading(self):
        """切換自動交易"""
        if not self.auto_trading:
            self.auto_trading = True
            self.auto_button.config(text="⏹️ 停止自動交易", bg='#e74c3c')
            self.strategy_status.set("🚀 自動交易運行中")
            self.add_log("🚀 自動交易已啟動")
            
            self.trading_thread = threading.Thread(target=self.auto_trading_loop, daemon=True)
            self.trading_thread.start()
        else:
            self.auto_trading = False
            self.auto_button.config(text="🚀 啟動自動交易", bg='#f39c12')
            self.strategy_status.set("⏸️ 自動交易已停止")
            self.add_log("⏸️ 自動交易已停止")
    
    def auto_trading_loop(self):
        """自動交易循環"""
        while self.auto_trading:
            try:
                self.add_log("🔄 執行85%勝率策略循環...")
                status = self.trading_engine.run_strategy_cycle()
                
                if status.get('signal_executed'):
                    signal = status.get('last_signal')
                    if signal:
                        signal_type = signal['signal_type']
                        strategy_name = signal.get('strategy', '85%策略')
                        signal_strength = signal.get('signal_strength', 0) * 100
                        
                        self.add_log(f"🎯 85%策略執行{signal_type}信號")
                        self.add_log(f"📊 信號強度: {signal_strength:.1f}分 | 策略: {strategy_name}")
                        
                        if 'validation_info' in signal:
                            self.add_log(f"✅ 驗證: {signal['validation_info']}")
                        
                        # 發送Telegram通知
                        self.telegram_notifier.notify_signal_detected(signal)
                        
                        # 如果有交易執行，發送交易通知
                        if signal_type in ['buy', 'sell']:
                            current_price = signal.get('current_price', 0)
                            if signal_type == 'buy':
                                amount = self.trading_engine.min_trade_amount
                                btc_amount = amount / current_price if current_price > 0 else 0
                                self.telegram_notifier.notify_trade_executed('buy', current_price, amount, btc_amount)
                            else:
                                btc_amount = self.trading_engine.btc_balance
                                amount = btc_amount * current_price
                                # 計算獲利（簡化版）
                                last_trade = self.trading_engine.trade_history[-1] if self.trading_engine.trade_history else None
                                profit = last_trade.get('profit', 0) if last_trade else 0
                                self.telegram_notifier.notify_trade_executed('sell', current_price, amount, btc_amount, profit)
                else:
                    self.add_log("📊 85%策略檢測中，暫無符合80分閾值的信號")
                
                # 顯示當前策略狀態
                current_price = status.get('current_price', 0)
                if current_price:
                    self.add_log(f"💰 當前BTC價格: NT$ {current_price:,.0f}")
                
                # 等待5分鐘
                self.add_log("⏰ 等待5分鐘後進行下次策略檢測...")
                for i in range(300):
                    if not self.auto_trading:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.add_log(f"❌ 85%策略執行錯誤: {e}")
                time.sleep(60)
    
    def test_telegram(self):
        """測試Telegram通知"""
        try:
            if self.telegram_notifier.enabled:
                success = self.telegram_notifier.test_connection()
                if success:
                    self.add_log("✅ Telegram通知測試成功")
                    messagebox.showinfo("測試成功", "Telegram通知發送成功！")
                else:
                    self.add_log("❌ Telegram通知測試失敗")
                    messagebox.showerror("測試失敗", "Telegram通知發送失敗")
            else:
                self.add_log("⚠️ Telegram通知未配置")
                messagebox.showwarning("未配置", "Telegram通知功能未配置\n請檢查config/telegram_config.py")
        except Exception as e:
            self.add_log(f"❌ Telegram測試錯誤: {e}")
            messagebox.showerror("錯誤", f"測試過程中發生錯誤：{e}")
    
    def show_analytics(self):
        """顯示交易分析報告"""
        try:
            # 更新分析數據
            self.analytics.update_trade_history(self.trading_engine.trade_history)
            
            # 生成報告
            report = self.analytics.generate_report()
            
            # 創建新窗口顯示報告
            analytics_window = tk.Toplevel(self.root)
            analytics_window.title("📊 85%策略交易分析報告")
            analytics_window.geometry("800x600")
            analytics_window.configure(bg='#1a1a2e')
            
            # 報告文本區域
            text_frame = tk.Frame(analytics_window, bg='#1a1a2e')
            text_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            report_text = scrolledtext.ScrolledText(text_frame, 
                                                   font=('Consolas', 10),
                                                   bg='#2c3e50', fg='#ecf0f1',
                                                   wrap='word')
            report_text.pack(fill='both', expand=True)
            report_text.insert('1.0', report)
            report_text.config(state='disabled')
            
            # 按鈕區域
            button_frame = tk.Frame(analytics_window, bg='#1a1a2e')
            button_frame.pack(fill='x', padx=10, pady=5)
            
            tk.Button(button_frame, text="📱 發送到Telegram", 
                     font=('Microsoft JhengHei', 10, 'bold'),
                     bg='#1abc9c', fg='white', 
                     command=lambda: self.send_report_to_telegram(report)).pack(side='left', padx=5)
            
            tk.Button(button_frame, text="💾 保存報告", 
                     font=('Microsoft JhengHei', 10, 'bold'),
                     bg='#3498db', fg='white', 
                     command=lambda: self.save_report(report)).pack(side='left', padx=5)
            
            tk.Button(button_frame, text="🔄 刷新", 
                     font=('Microsoft JhengHei', 10, 'bold'),
                     bg='#f39c12', fg='white', 
                     command=lambda: self.refresh_analytics(analytics_window)).pack(side='left', padx=5)
            
            tk.Button(button_frame, text="❌ 關閉", 
                     font=('Microsoft JhengHei', 10, 'bold'),
                     bg='#e74c3c', fg='white', 
                     command=analytics_window.destroy).pack(side='right', padx=5)
            
            self.add_log("📊 分析報告已生成")
            
        except Exception as e:
            self.add_log(f"❌ 分析報告錯誤: {e}")
            messagebox.showerror("錯誤", f"生成分析報告時發生錯誤：{e}")
    
    def send_report_to_telegram(self, report: str):
        """發送報告到Telegram"""
        try:
            if self.telegram_notifier.enabled:
                # 分割長報告（Telegram有字數限制）
                max_length = 4000
                if len(report) > max_length:
                    parts = [report[i:i+max_length] for i in range(0, len(report), max_length)]
                    for i, part in enumerate(parts):
                        success = self.telegram_notifier.send_message(f"📊 分析報告 ({i+1}/{len(parts)})\n\n{part}")
                        if not success:
                            messagebox.showerror("發送失敗", f"報告第{i+1}部分發送失敗")
                            return
                else:
                    success = self.telegram_notifier.send_message(report)
                    if not success:
                        messagebox.showerror("發送失敗", "報告發送失敗")
                        return
                
                messagebox.showinfo("發送成功", "分析報告已發送到Telegram！")
                self.add_log("📱 分析報告已發送到Telegram")
            else:
                messagebox.showwarning("未配置", "Telegram通知功能未配置")
        except Exception as e:
            messagebox.showerror("錯誤", f"發送報告時發生錯誤：{e}")
    
    def save_report(self, report: str):
        """保存報告到文件"""
        try:
            import os
            from datetime import datetime
            
            os.makedirs('reports', exist_ok=True)
            filename = f"reports/85_strategy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            
            messagebox.showinfo("保存成功", f"報告已保存到：{filename}")
            self.add_log(f"💾 分析報告已保存: {filename}")
        except Exception as e:
            messagebox.showerror("保存失敗", f"保存報告時發生錯誤：{e}")
    
    def refresh_analytics(self, window):
        """刷新分析窗口"""
        window.destroy()
        self.show_analytics()

    def save_state(self):
        """保存交易狀態"""
        try:
            filepath = self.trading_engine.save_state()
            if filepath:
                self.add_log(f"💾 狀態已保存")
                messagebox.showinfo("保存成功", f"狀態已保存")
            else:
                self.add_log("❌ 保存失敗")
                
        except Exception as e:
            self.add_log(f"❌ 保存錯誤: {e}")
    
    def on_closing(self):
        """關閉程序"""
        if self.auto_trading:
            self.auto_trading = False
            time.sleep(1)
        
        self.add_log("🔄 正在關閉...")
        self.save_state()
        self.root.after(100, self.root.destroy)

def main():
    """主函數"""
    print("🎯 啟動85%勝率策略緊湊版GUI...")
    
    root = tk.Tk()
    
    # 導入tkinter.simpledialog
    import tkinter.simpledialog
    tk.simpledialog = tkinter.simpledialog
    
    app = Compact85GUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🔄 用戶中斷，正在關閉...")
    except Exception as e:
        print(f"❌ 程序錯誤: {e}")
    finally:
        print("👋 85%勝率策略GUI已關閉")

if __name__ == "__main__":
    main()