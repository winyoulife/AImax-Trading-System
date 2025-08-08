#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 AImax 真實交易系統 GUI
基於真實MAX API的桌面交易介面
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

from trading.real_max_client import RealMaxClient

class RealTradingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 AImax 真實交易系統")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2c3e50')
        
        # 初始化MAX客戶端
        self.max_client = RealMaxClient()
        
        # 數據變量
        self.current_price = tk.StringVar(value="載入中...")
        self.bid_price = tk.StringVar(value="--")
        self.ask_price = tk.StringVar(value="--")
        self.high_24h = tk.StringVar(value="--")
        self.low_24h = tk.StringVar(value="--")
        self.volume_24h = tk.StringVar(value="--")
        self.api_status = tk.StringVar(value="檢查中...")
        
        # 帳戶數據 (需要API Key)
        self.twd_balance = tk.StringVar(value="需要API Key")
        self.btc_balance = tk.StringVar(value="需要API Key")
        self.total_value = tk.StringVar(value="需要API Key")
        
        # 創建界面
        self.create_widgets()
        
        # 啟動數據更新線程
        self.running = True
        self.update_thread = threading.Thread(target=self.update_data_loop, daemon=True)
        self.update_thread.start()
        
        # 綁定關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """創建GUI組件"""
        
        # 主標題
        title_frame = tk.Frame(self.root, bg='#34495e', height=80)
        title_frame.pack(fill='x', padx=10, pady=5)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🎯 AImax 真實交易系統", 
            font=('Microsoft JhengHei', 20, 'bold'),
            bg='#34495e', 
            fg='white'
        )
        title_label.pack(pady=20)
        
        # API狀態
        status_frame = tk.Frame(self.root, bg='#2c3e50')
        status_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(
            status_frame, 
            text="📡 MAX API 狀態:", 
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#2c3e50', 
            fg='white'
        ).pack(side='left')
        
        self.status_label = tk.Label(
            status_frame, 
            textvariable=self.api_status,
            font=('Microsoft JhengHei', 12),
            bg='#2c3e50', 
            fg='#e74c3c'
        )
        self.status_label.pack(side='left', padx=10)
        
        # 主要內容區域
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 左側：價格信息
        left_frame = tk.LabelFrame(
            main_frame, 
            text="📊 市場數據", 
            font=('Microsoft JhengHei', 14, 'bold'),
            bg='#34495e', 
            fg='white',
            bd=2,
            relief='groove'
        )
        left_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        self.create_price_section(left_frame)
        
        # 右側：帳戶信息
        right_frame = tk.LabelFrame(
            main_frame, 
            text="💰 帳戶信息", 
            font=('Microsoft JhengHei', 14, 'bold'),
            bg='#34495e', 
            fg='white',
            bd=2,
            relief='groove'
        )
        right_frame.pack(side='right', fill='both', expand=True, padx=5)
        
        self.create_account_section(right_frame)
        
        # 底部：日誌和控制
        bottom_frame = tk.Frame(self.root, bg='#2c3e50')
        bottom_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.create_log_section(bottom_frame)
        self.create_control_section(bottom_frame)
    
    def create_price_section(self, parent):
        """創建價格信息區域"""
        
        # BTC當前價格
        price_frame = tk.Frame(parent, bg='#34495e')
        price_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(
            price_frame, 
            text="₿ BTC 當前價格:", 
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#34495e', 
            fg='white'
        ).pack(anchor='w')
        
        self.price_label = tk.Label(
            price_frame, 
            textvariable=self.current_price,
            font=('Microsoft JhengHei', 18, 'bold'),
            bg='#34495e', 
            fg='#f39c12'
        )
        self.price_label.pack(anchor='w', pady=5)
        
        # 買賣價
        spread_frame = tk.Frame(parent, bg='#34495e')
        spread_frame.pack(fill='x', padx=10, pady=5)
        
        # 買價
        bid_frame = tk.Frame(spread_frame, bg='#34495e')
        bid_frame.pack(side='left', fill='x', expand=True)
        
        tk.Label(
            bid_frame, 
            text="🟢 買價:", 
            font=('Microsoft JhengHei', 10),
            bg='#34495e', 
            fg='white'
        ).pack(anchor='w')
        
        tk.Label(
            bid_frame, 
            textvariable=self.bid_price,
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#34495e', 
            fg='#27ae60'
        ).pack(anchor='w')
        
        # 賣價
        ask_frame = tk.Frame(spread_frame, bg='#34495e')
        ask_frame.pack(side='right', fill='x', expand=True)
        
        tk.Label(
            ask_frame, 
            text="🔴 賣價:", 
            font=('Microsoft JhengHei', 10),
            bg='#34495e', 
            fg='white'
        ).pack(anchor='e')
        
        tk.Label(
            ask_frame, 
            textvariable=self.ask_price,
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#34495e', 
            fg='#e74c3c'
        ).pack(anchor='e')
        
        # 24小時統計
        stats_frame = tk.LabelFrame(
            parent, 
            text="📈 24小時統計", 
            font=('Microsoft JhengHei', 11, 'bold'),
            bg='#34495e', 
            fg='white'
        )
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        # 高低價
        high_low_frame = tk.Frame(stats_frame, bg='#34495e')
        high_low_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(
            high_low_frame, 
            text="📊 最高:", 
            font=('Microsoft JhengHei', 10),
            bg='#34495e', 
            fg='white'
        ).pack(side='left')
        
        tk.Label(
            high_low_frame, 
            textvariable=self.high_24h,
            font=('Microsoft JhengHei', 10, 'bold'),
            bg='#34495e', 
            fg='#e67e22'
        ).pack(side='left', padx=10)
        
        tk.Label(
            high_low_frame, 
            text="📉 最低:", 
            font=('Microsoft JhengHei', 10),
            bg='#34495e', 
            fg='white'
        ).pack(side='right')
        
        tk.Label(
            high_low_frame, 
            textvariable=self.low_24h,
            font=('Microsoft JhengHei', 10, 'bold'),
            bg='#34495e', 
            fg='#3498db'
        ).pack(side='right', padx=10)
        
        # 成交量
        volume_frame = tk.Frame(stats_frame, bg='#34495e')
        volume_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Label(
            volume_frame, 
            text="📊 成交量:", 
            font=('Microsoft JhengHei', 10),
            bg='#34495e', 
            fg='white'
        ).pack(side='left')
        
        tk.Label(
            volume_frame, 
            textvariable=self.volume_24h,
            font=('Microsoft JhengHei', 10, 'bold'),
            bg='#34495e', 
            fg='#9b59b6'
        ).pack(side='left', padx=10)
    
    def create_account_section(self, parent):
        """創建帳戶信息區域"""
        
        # TWD餘額
        twd_frame = tk.Frame(parent, bg='#34495e')
        twd_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(
            twd_frame, 
            text="💵 TWD 餘額:", 
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#34495e', 
            fg='white'
        ).pack(anchor='w')
        
        tk.Label(
            twd_frame, 
            textvariable=self.twd_balance,
            font=('Microsoft JhengHei', 16, 'bold'),
            bg='#34495e', 
            fg='#f39c12'
        ).pack(anchor='w', pady=5)
        
        # BTC持倉
        btc_frame = tk.Frame(parent, bg='#34495e')
        btc_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(
            btc_frame, 
            text="₿ BTC 持倉:", 
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#34495e', 
            fg='white'
        ).pack(anchor='w')
        
        tk.Label(
            btc_frame, 
            textvariable=self.btc_balance,
            font=('Microsoft JhengHei', 16, 'bold'),
            bg='#34495e', 
            fg='#e67e22'
        ).pack(anchor='w', pady=5)
        
        # 總資產
        total_frame = tk.Frame(parent, bg='#34495e')
        total_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(
            total_frame, 
            text="💰 總資產價值:", 
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#34495e', 
            fg='white'
        ).pack(anchor='w')
        
        tk.Label(
            total_frame, 
            textvariable=self.total_value,
            font=('Microsoft JhengHei', 16, 'bold'),
            bg='#34495e', 
            fg='#27ae60'
        ).pack(anchor='w', pady=5)
        
        # API Key設置按鈕
        api_frame = tk.Frame(parent, bg='#34495e')
        api_frame.pack(fill='x', padx=10, pady=20)
        
        tk.Button(
            api_frame,
            text="🔑 設置 API Key",
            font=('Microsoft JhengHei', 11, 'bold'),
            bg='#3498db',
            fg='white',
            command=self.setup_api_key,
            relief='raised',
            bd=2
        ).pack(fill='x')
    
    def create_log_section(self, parent):
        """創建日誌區域"""
        log_frame = tk.LabelFrame(
            parent, 
            text="📝 系統日誌", 
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#34495e', 
            fg='white'
        )
        log_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            font=('Consolas', 9),
            bg='#2c3e50',
            fg='#ecf0f1',
            insertbackground='white'
        )
        self.log_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 添加初始日誌
        self.add_log("🎯 AImax 真實交易系統啟動")
        self.add_log("📡 正在連接MAX API...")
    
    def create_control_section(self, parent):
        """創建控制區域"""
        control_frame = tk.LabelFrame(
            parent, 
            text="🎮 系統控制", 
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='#34495e', 
            fg='white'
        )
        control_frame.pack(side='right', fill='y', padx=5)
        
        # 刷新按鈕
        tk.Button(
            control_frame,
            text="🔄 刷新數據",
            font=('Microsoft JhengHei', 11, 'bold'),
            bg='#27ae60',
            fg='white',
            command=self.manual_refresh,
            relief='raised',
            bd=2,
            width=15
        ).pack(pady=10, padx=10)
        
        # 測試連接按鈕
        tk.Button(
            control_frame,
            text="🧪 測試連接",
            font=('Microsoft JhengHei', 11, 'bold'),
            bg='#f39c12',
            fg='white',
            command=self.test_connection,
            relief='raised',
            bd=2,
            width=15
        ).pack(pady=10, padx=10)
        
        # 查看交易記錄按鈕
        tk.Button(
            control_frame,
            text="📋 交易記錄",
            font=('Microsoft JhengHei', 11, 'bold'),
            bg='#9b59b6',
            fg='white',
            command=self.show_trades,
            relief='raised',
            bd=2,
            width=15
        ).pack(pady=10, padx=10)
        
        # 關於按鈕
        tk.Button(
            control_frame,
            text="ℹ️ 關於系統",
            font=('Microsoft JhengHei', 11, 'bold'),
            bg='#34495e',
            fg='white',
            command=self.show_about,
            relief='raised',
            bd=2,
            width=15
        ).pack(pady=10, padx=10)
    
    def add_log(self, message):
        """添加日誌消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
    
    def update_data_loop(self):
        """數據更新循環"""
        while self.running:
            try:
                self.update_market_data()
                time.sleep(30)  # 每30秒更新一次
            except Exception as e:
                self.add_log(f"❌ 數據更新錯誤: {e}")
                time.sleep(60)  # 錯誤時等待更長時間
    
    def update_market_data(self):
        """更新市場數據"""
        try:
            # 獲取價格數據
            ticker_result = self.max_client.get_ticker('btctwd')
            
            if ticker_result['success']:
                data = ticker_result['data']
                
                # 更新價格顯示
                self.current_price.set(f"NT$ {data['last_price']:,.0f}")
                self.bid_price.set(f"NT$ {data['bid_price']:,.0f}")
                self.ask_price.set(f"NT$ {data['ask_price']:,.0f}")
                self.high_24h.set(f"NT$ {data['high_24h']:,.0f}")
                self.low_24h.set(f"NT$ {data['low_24h']:,.0f}")
                self.volume_24h.set(f"{data['volume_24h']:.4f} BTC")
                
                # 更新API狀態
                self.api_status.set("✅ 連接正常")
                self.status_label.config(fg='#27ae60')
                
                self.add_log(f"📊 價格更新: NT$ {data['last_price']:,.0f}")
                
            else:
                raise Exception(ticker_result['error'])
                
        except Exception as e:
            self.api_status.set(f"❌ 連接失敗: {str(e)}")
            self.status_label.config(fg='#e74c3c')
            self.add_log(f"❌ 更新失敗: {e}")
    
    def manual_refresh(self):
        """手動刷新數據"""
        self.add_log("🔄 手動刷新數據...")
        threading.Thread(target=self.update_market_data, daemon=True).start()
    
    def test_connection(self):
        """測試API連接"""
        self.add_log("🧪 測試MAX API連接...")
        
        def test():
            try:
                result = self.max_client.get_ticker('btctwd')
                if result['success']:
                    price = result['data']['last_price']
                    self.add_log(f"✅ 連接測試成功: BTC價格 NT$ {price:,.0f}")
                    messagebox.showinfo("連接測試", f"✅ MAX API連接正常\n當前BTC價格: NT$ {price:,.0f}")
                else:
                    self.add_log(f"❌ 連接測試失敗: {result['error']}")
                    messagebox.showerror("連接測試", f"❌ 連接失敗\n錯誤: {result['error']}")
            except Exception as e:
                self.add_log(f"❌ 連接測試異常: {e}")
                messagebox.showerror("連接測試", f"❌ 測試異常\n錯誤: {e}")
        
        threading.Thread(target=test, daemon=True).start()
    
    def setup_api_key(self):
        """設置API Key"""
        messagebox.showinfo(
            "設置 API Key", 
            "🔑 API Key 設置功能\n\n" +
            "要使用帳戶功能，請:\n" +
            "1. 登入MAX交易所\n" +
            "2. 申請API Key和Secret Key\n" +
            "3. 在代碼中設置認證信息\n\n" +
            "設置後可以查看:\n" +
            "• 真實帳戶餘額\n" +
            "• 真實BTC持倉\n" +
            "• 真實交易記錄"
        )
    
    def show_trades(self):
        """顯示交易記錄"""
        self.add_log("📋 查看交易記錄...")
        
        def get_trades():
            try:
                result = self.max_client.get_my_trades('btctwd', limit=10)
                if result['success']:
                    trades = result['data']['trades']
                    if trades:
                        trade_info = "📋 最近交易記錄:\n\n"
                        for trade in trades[:5]:
                            trade_info += f"• {trade['side'].upper()}: NT$ {trade['price']:,.0f} × {trade['volume']:.6f}\n"
                        messagebox.showinfo("交易記錄", trade_info)
                    else:
                        messagebox.showinfo("交易記錄", "📋 暫無交易記錄")
                else:
                    messagebox.showwarning("交易記錄", f"需要API Key才能查看交易記錄\n錯誤: {result['error']}")
            except Exception as e:
                messagebox.showerror("交易記錄", f"❌ 獲取交易記錄失敗\n錯誤: {e}")
        
        threading.Thread(target=get_trades, daemon=True).start()
    
    def show_about(self):
        """顯示關於信息"""
        about_text = """🎯 AImax 真實交易系統 v1.0

📊 功能特色:
• 連接台灣MAX交易所
• 實時BTC價格監控
• 真實市場數據
• 為10萬台幣實戰準備

🔧 技術特點:
• 100%真實數據
• 30秒自動更新
• 專業交易界面
• 安全API整合

🎯 使用目的:
為真實交易做準備，不再使用模擬數據！

© 2025 AImax Trading System"""
        
        messagebox.showinfo("關於系統", about_text)
    
    def on_closing(self):
        """關閉程序"""
        self.running = False
        self.add_log("🔄 正在關閉系統...")
        self.root.after(100, self.root.destroy)

def main():
    """主函數"""
    print("🎯 啟動 AImax 真實交易系統 GUI")
    print("=" * 50)
    
    root = tk.Tk()
    app = RealTradingGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n🔄 用戶中斷，正在關閉...")
    except Exception as e:
        print(f"❌ 程序錯誤: {e}")
    finally:
        print("👋 AImax 真實交易系統已關閉")

if __name__ == "__main__":
    main()