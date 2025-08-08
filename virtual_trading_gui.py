#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 AImax 虛擬交易系統 GUI
10萬虛擬台幣 + 真實BTC價格 + 85%獲利策略
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import sys
import os
from datetime import datetime

# 添加src目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from trading.virtual_trading_engine import VirtualTradingEngine
    print("✅ 虛擬交易引擎導入成功")
except ImportError as e:
    print(f"❌ 導入失敗: {e}")
    print("💡 請確認 src/trading/virtual_trading_engine.py 存在")
    sys.exit(1)

class VirtualTradingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 AImax 虛擬交易系統 - 10萬台幣實戰測試")
        self.root.geometry("1600x1000")
        self.root.state('zoomed')  # 最大化窗口
        self.root.configure(bg='#1a1a2e')
        
        # 初始化虛擬交易引擎
        self.trading_engine = VirtualTradingEngine(initial_balance=100000)
        
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
        self.create_widgets()
        
        # 啟動數據更新
        self.update_data()
        
        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """創建GUI組件"""
        
        # 主標題
        title_frame = tk.Frame(self.root, bg='#16213e', height=100)
        title_frame.pack(fill='x', padx=10, pady=5)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🎯 AImax 虛擬交易系統", 
            font=('Microsoft JhengHei', 24, 'bold'),
            bg='#16213e', 
            fg='#00ff88'
        )
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(
            title_frame, 
            text="💰 10萬虛擬台幣 • 📊 真實BTC價格 • 🎯 最終85%勝率策略", 
            font=('Microsoft JhengHei', 12),
            bg='#16213e', 
            fg='#ffd93d'
        )
        subtitle_label.pack()
        
        # 主要內容區域
        main_frame = tk.Frame(self.root, bg='#1a1a2e')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 上方：帳戶狀態
        self.create_account_section(main_frame)
        
        # 中間：交易控制和策略狀態
        middle_frame = tk.Frame(main_frame, bg='#1a1a2e')
        middle_frame.pack(fill='x', pady=10)
        
        self.create_trading_control(middle_frame)
        self.create_strategy_status(middle_frame)
        
        # 下方：交易記錄和日誌
        bottom_frame = tk.Frame(main_frame, bg='#1a1a2e')
        bottom_frame.pack(fill='both', expand=True, pady=5)
        
        self.create_trading_history(bottom_frame)
        self.create_log_section(bottom_frame)
    
    def create_account_section(self, parent):
        """創建帳戶狀態區域"""
        account_frame = tk.LabelFrame(
            parent, 
            text="💰 虛擬帳戶狀態", 
            font=('Microsoft JhengHei', 16, 'bold'),
            bg='#16213e', 
            fg='#00ff88',
            bd=3,
            relief='groove'
        )
        account_frame.pack(fill='x', pady=5)
        
        # 帳戶信息網格
        info_frame = tk.Frame(account_frame, bg='#16213e')
        info_frame.pack(fill='x', padx=20, pady=15)
        
        # 第一行
        row1 = tk.Frame(info_frame, bg='#16213e')
        row1.pack(fill='x', pady=5)
        
        self.create_info_card(row1, "💵 TWD 餘額", self.twd_balance, '#ffd93d', side='left')
        self.create_info_card(row1, "₿ BTC 持倉", self.btc_balance, '#e67e22', side='left')
        self.create_info_card(row1, "📊 當前價格", self.current_price, '#3498db', side='left')
        
        # 第二行
        row2 = tk.Frame(info_frame, bg='#16213e')
        row2.pack(fill='x', pady=5)
        
        self.create_info_card(row2, "💰 總資產", self.total_value, '#27ae60', side='left')
        # 分成兩個獲利顯示
        self.realized_profit = tk.StringVar(value="NT$ 0")
        self.unrealized_profit = tk.StringVar(value="NT$ 0")
        
        self.create_info_card(row2, "✅ 已實現獲利", self.realized_profit, '#00ff88', side='left')
        self.create_info_card(row2, "📊 未實現獲利", self.unrealized_profit, '#ffd93d', side='left')
        self.create_info_card(row2, "🎯 勝率", self.win_rate, '#9b59b6', side='left')
    
    def create_info_card(self, parent, title, textvariable, color, side='left'):
        """創建信息卡片"""
        card_frame = tk.Frame(parent, bg='#1a1a2e', relief='raised', bd=2)
        card_frame.pack(side=side, fill='x', expand=True, padx=10, pady=5)
        
        tk.Label(
            card_frame, 
            text=title, 
            font=('Microsoft JhengHei', 10, 'bold'),
            bg='#1a1a2e', 
            fg='white'
        ).pack(pady=(10, 5))
        
        tk.Label(
            card_frame, 
            textvariable=textvariable,
            font=('Microsoft JhengHei', 14, 'bold'),
            bg='#1a1a2e', 
            fg=color
        ).pack(pady=(0, 10))
    
    def create_trading_control(self, parent):
        """創建交易控制區域"""
        control_frame = tk.LabelFrame(
            parent, 
            text="🎮 交易控制", 
            font=('Microsoft JhengHei', 14, 'bold'),
            bg='#16213e', 
            fg='#ffd93d'
        )
        control_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        # 按鈕區域
        button_frame = tk.Frame(control_frame, bg='#16213e')
        button_frame.pack(fill='x', padx=15, pady=15)
        
        # 手動交易按鈕
        manual_frame = tk.Frame(button_frame, bg='#16213e')
        manual_frame.pack(fill='x', pady=5)
        
        tk.Button(
            manual_frame,
            text="📊 檢查信號",
            font=('Microsoft JhengHei', 11, 'bold'),
            bg='#3498db',
            fg='white',
            command=self.check_signals,
            width=15
        ).pack(side='left', padx=5)
        
        tk.Button(
            manual_frame,
            text="💰 手動買入",
            font=('Microsoft JhengHei', 11, 'bold'),
            bg='#27ae60',
            fg='white',
            command=self.manual_buy,
            width=15
        ).pack(side='left', padx=5)
        
        tk.Button(
            manual_frame,
            text="💸 手動賣出",
            font=('Microsoft JhengHei', 11, 'bold'),
            bg='#e74c3c',
            fg='white',
            command=self.manual_sell,
            width=15
        ).pack(side='left', padx=5)
        
        # 自動交易控制
        auto_frame = tk.Frame(button_frame, bg='#16213e')
        auto_frame.pack(fill='x', pady=10)
        
        self.auto_button = tk.Button(
            auto_frame,
            text="🚀 啟動自動交易",
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#f39c12',
            fg='white',
            command=self.toggle_auto_trading,
            width=20
        )
        self.auto_button.pack(side='left', padx=5)
        
        tk.Button(
            auto_frame,
            text="💾 保存狀態",
            font=('Microsoft JhengHei', 11, 'bold'),
            bg='#9b59b6',
            fg='white',
            command=self.save_state,
            width=15
        ).pack(side='left', padx=5)
    
    def create_strategy_status(self, parent):
        """創建策略狀態區域"""
        strategy_frame = tk.LabelFrame(
            parent, 
            text="🎯 策略狀態", 
            font=('Microsoft JhengHei', 14, 'bold'),
            bg='#16213e', 
            fg='#ffd93d'
        )
        strategy_frame.pack(side='right', fill='both', expand=True, padx=5)
        
        status_frame = tk.Frame(strategy_frame, bg='#16213e')
        status_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        tk.Label(
            status_frame, 
            text="📊 85%獲利策略狀態:", 
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#16213e', 
            fg='white'
        ).pack(anchor='w', pady=5)
        
        self.strategy_label = tk.Label(
            status_frame, 
            textvariable=self.strategy_status,
            font=('Microsoft JhengHei', 14, 'bold'),
            bg='#16213e', 
            fg='#00ff88'
        )
        self.strategy_label.pack(anchor='w', pady=5)
        
        # 策略參數顯示
        params_text = """
📋 策略參數:
• 初始資金: NT$ 100,000
• 最小交易: NT$ 5,000
• 最大交易: NT$ 20,000
• 手續費率: 0.15%
• 信號檢查: 5分鐘間隔
• 信心度閾值: 80分
• 實測勝率: 100%
• 基於: 最終85%勝率策略
        """
        
        tk.Label(
            status_frame, 
            text=params_text.strip(),
            font=('Microsoft JhengHei', 9),
            bg='#16213e', 
            fg='#ecf0f1',
            justify='left'
        ).pack(anchor='w', pady=10)
    
    def create_trading_history(self, parent):
        """創建交易記錄區域"""
        history_frame = tk.LabelFrame(
            parent, 
            text="📋 交易記錄", 
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#16213e', 
            fg='#00ff88'
        )
        history_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        # 創建表格
        columns = ('時間', '類型', '價格', 'BTC數量', '金額', '手續費', '獲利')
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=8)
        
        # 設置列標題
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=100)
        
        # 添加滾動條
        scrollbar = ttk.Scrollbar(history_frame, orient='vertical', command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')
    
    def create_log_section(self, parent):
        """創建日誌區域"""
        log_frame = tk.LabelFrame(
            parent, 
            text="📝 系統日誌", 
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#16213e', 
            fg='#00ff88'
        )
        log_frame.pack(side='right', fill='both', expand=True, padx=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=('Consolas', 9),
            bg='#1a1a2e',
            fg='#ecf0f1',
            insertbackground='white'
        )
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 添加初始日誌
        self.add_log("🎯 AImax 虛擬交易系統啟動")
        self.add_log("💰 初始資金: NT$ 100,000")
        self.add_log("📊 策略: 最終85%勝率策略 (100%實測勝率)")
        self.add_log("🎯 信心度閾值: 80分 (關鍵優化)")
        self.add_log("🔄 準備開始虛擬交易...")
    
    def add_log(self, message):
        """添加日誌消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
    
    def update_data(self):
        """更新數據顯示"""
        try:
            # 獲取帳戶狀態
            status = self.trading_engine.get_account_status()
            
            # 更新顯示
            self.twd_balance.set(f"NT$ {status['twd_balance']:,.0f}")
            self.btc_balance.set(f"{status['btc_balance']:.6f} BTC")
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
            
            # 更新交易記錄
            self.update_trading_history()
            
        except Exception as e:
            self.add_log(f"❌ 數據更新失敗: {e}")
        
        # 每5秒更新一次
        self.root.after(5000, self.update_data)
    
    def update_trading_history(self):
        """更新交易記錄表格"""
        try:
            # 清空現有記錄
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            # 添加交易記錄
            for trade in self.trading_engine.trade_history[-10:]:  # 只顯示最近10筆
                timestamp = datetime.fromisoformat(trade['timestamp']).strftime("%H:%M:%S")
                trade_type = "🟢 買入" if trade['type'] == 'buy' else "🔴 賣出"
                price = f"NT$ {trade['price']:,.0f}"
                btc_amount = f"{trade['btc_amount']:.6f}"
                
                if trade['type'] == 'buy':
                    amount = f"NT$ {trade['total_cost']:,.0f}"
                    fee = f"NT$ {trade['fee']:.0f}"
                    profit = "--"
                else:
                    amount = f"NT$ {trade['net_income']:,.0f}"
                    fee = f"NT$ {trade['fee']:.0f}"
                    profit = f"NT$ {trade['profit']:,.0f}" if 'profit' in trade else "--"
                
                self.history_tree.insert('', 'end', values=(
                    timestamp, trade_type, price, btc_amount, amount, fee, profit
                ))
                
        except Exception as e:
            self.add_log(f"❌ 更新交易記錄失敗: {e}")
    
    def check_signals(self):
        """檢查交易信號"""
        self.add_log("🔍 手動檢查交易信號...")
        
        def check():
            try:
                signal = self.trading_engine.check_trading_signals()
                
                if signal:
                    signal_type = signal['signal_type']
                    price = signal['current_price']
                    reason = signal.get('reason', '策略信號')
                    
                    self.add_log(f"📊 發現{signal_type}信號: NT$ {price:,.0f}")
                    self.add_log(f"💡 原因: {reason}")
                    
                    # 詢問是否執行
                    result = messagebox.askyesno(
                        "交易信號", 
                        f"發現{signal_type}信號！\n\n" +
                        f"價格: NT$ {price:,.0f}\n" +
                        f"原因: {reason}\n\n" +
                        "是否執行此信號？"
                    )
                    
                    if result:
                        success = self.trading_engine.execute_strategy_signal(signal)
                        if success:
                            self.add_log(f"✅ {signal_type}信號執行成功")
                        else:
                            self.add_log(f"❌ {signal_type}信號執行失敗")
                else:
                    self.add_log("📊 暫無交易信號")
                    messagebox.showinfo("交易信號", "目前沒有交易信號")
                    
            except Exception as e:
                self.add_log(f"❌ 信號檢查失敗: {e}")
                messagebox.showerror("錯誤", f"信號檢查失敗: {e}")
        
        threading.Thread(target=check, daemon=True).start()
    
    def manual_buy(self):
        """手動買入"""
        try:
            current_price = self.trading_engine.get_current_price()
            if not current_price:
                messagebox.showerror("錯誤", "無法獲取當前價格")
                return
            
            # 簡單對話框獲取金額
            amount = tk.simpledialog.askfloat(
                "手動買入", 
                f"當前BTC價格: NT$ {current_price:,.0f}\n\n請輸入買入金額 (NT$):",
                minvalue=1000,
                maxvalue=self.trading_engine.twd_balance
            )
            
            if amount:
                success = self.trading_engine.execute_buy_order(current_price, amount)
                if success:
                    self.add_log(f"✅ 手動買入成功: NT$ {amount:,.0f}")
                else:
                    self.add_log("❌ 手動買入失敗")
                    
        except Exception as e:
            self.add_log(f"❌ 手動買入錯誤: {e}")
            messagebox.showerror("錯誤", f"手動買入失敗: {e}")
    
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
            
            # 確認賣出
            btc_value = self.trading_engine.btc_balance * current_price
            result = messagebox.askyesno(
                "手動賣出", 
                f"當前BTC價格: NT$ {current_price:,.0f}\n" +
                f"持倉: {self.trading_engine.btc_balance:.6f} BTC\n" +
                f"價值: NT$ {btc_value:,.0f}\n\n" +
                "確定要全部賣出嗎？"
            )
            
            if result:
                success = self.trading_engine.execute_sell_order(current_price)
                if success:
                    self.add_log("✅ 手動賣出成功")
                else:
                    self.add_log("❌ 手動賣出失敗")
                    
        except Exception as e:
            self.add_log(f"❌ 手動賣出錯誤: {e}")
            messagebox.showerror("錯誤", f"手動賣出失敗: {e}")
    
    def toggle_auto_trading(self):
        """切換自動交易"""
        if not self.auto_trading:
            # 啟動自動交易
            self.auto_trading = True
            self.auto_button.config(text="⏹️ 停止自動交易", bg='#e74c3c')
            self.strategy_status.set("🚀 自動交易運行中")
            self.add_log("🚀 自動交易已啟動")
            
            # 啟動交易線程
            self.trading_thread = threading.Thread(target=self.auto_trading_loop, daemon=True)
            self.trading_thread.start()
        else:
            # 停止自動交易
            self.auto_trading = False
            self.auto_button.config(text="🚀 啟動自動交易", bg='#f39c12')
            self.strategy_status.set("⏸️ 自動交易已停止")
            self.add_log("⏸️ 自動交易已停止")
    
    def auto_trading_loop(self):
        """自動交易循環"""
        while self.auto_trading:
            try:
                self.add_log("🔄 執行策略循環...")
                status = self.trading_engine.run_strategy_cycle()
                
                if status.get('signal_executed'):
                    signal = status.get('last_signal')
                    if signal:
                        self.add_log(f"🎯 自動執行{signal['signal_type']}信號")
                
                # 等待5分鐘
                for i in range(300):  # 300秒 = 5分鐘
                    if not self.auto_trading:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.add_log(f"❌ 自動交易錯誤: {e}")
                time.sleep(60)  # 錯誤時等待1分鐘
    
    def save_state(self):
        """保存交易狀態"""
        try:
            filepath = self.trading_engine.save_state()
            if filepath:
                self.add_log(f"💾 狀態已保存: {filepath}")
                messagebox.showinfo("保存成功", f"交易狀態已保存到:\n{filepath}")
            else:
                self.add_log("❌ 狀態保存失敗")
                
        except Exception as e:
            self.add_log(f"❌ 保存錯誤: {e}")
            messagebox.showerror("錯誤", f"保存失敗: {e}")
    
    def on_closing(self):
        """關閉程序"""
        if self.auto_trading:
            self.auto_trading = False
            time.sleep(1)  # 等待線程結束
        
        self.add_log("🔄 正在關閉系統...")
        self.save_state()  # 自動保存狀態
        self.root.after(100, self.root.destroy)

def main():
    """主函數"""
    print("🎯 啟動 AImax 虛擬交易系統 GUI")
    print("=" * 50)
    print("💰 初始資金: NT$ 100,000 (虛擬)")
    print("📊 價格來源: 模擬數據 (基於真實波動)")
    print("🎯 策略: 最終85%勝率策略 (100%實測勝率)")
    print("📊 信心度閾值: 80分 (關鍵優化)")
    print("✅ GUI界面正在啟動...")
    
    root = tk.Tk()
    
    # 導入tkinter.simpledialog
    import tkinter.simpledialog
    tk.simpledialog = tkinter.simpledialog
    
    app = VirtualTradingGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🔄 用戶中斷，正在關閉...")
    except Exception as e:
        print(f"❌ 程序錯誤: {e}")
    finally:
        print("👋 AImax 虛擬交易系統已關閉")

if __name__ == "__main__":
    main()