#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易控制面板
用於監控和控制智能平衡交易系統
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from src.trading.safe_trading_manager import SafeTradingManager
from src.core.smart_balanced_volume_macd_signals import SmartBalancedVolumeEnhancedMACDSignals
from src.data.data_fetcher import DataFetcher

class TradingControlPanel:
    """交易控制面板"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("智能平衡交易系統 - 控制面板")
        self.root.geometry("800x600")
        
        # 初始化組件
        self.trading_manager = SafeTradingManager()
        self.signal_detector = SmartBalancedVolumeEnhancedMACDSignals()
        self.data_fetcher = DataFetcher()
        
        # 監控線程
        self.monitoring_thread = None
        self.is_monitoring = False
        
        self.setup_ui()
        self.update_display()
        
        # 定期更新顯示
        self.root.after(1000, self.periodic_update)
    
    def setup_ui(self):
        """設置用戶界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 系統狀態區域
        status_frame = ttk.LabelFrame(main_frame, text="系統狀態", padding="10")
        status_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="系統狀態: 停止", font=("Arial", 12, "bold"))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.position_label = ttk.Label(status_frame, text="當前持倉: 無")
        self.position_label.grid(row=1, column=0, sticky=tk.W)
        
        self.daily_stats_label = ttk.Label(status_frame, text="今日統計: 交易0次, 虧損0 TWD")
        self.daily_stats_label.grid(row=2, column=0, sticky=tk.W)
        
        # 控制按鈕區域
        control_frame = ttk.LabelFrame(main_frame, text="系統控制", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.start_button = ttk.Button(control_frame, text="啟動系統", command=self.start_system)
        self.start_button.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="停止系統", command=self.stop_system)
        self.stop_button.grid(row=0, column=1, padx=(0, 5))
        
        self.emergency_button = ttk.Button(control_frame, text="🚨 緊急停止", command=self.emergency_stop)
        self.emergency_button.grid(row=0, column=2)
        self.emergency_button.configure(style="Emergency.TButton")
        
        # 配置區域
        config_frame = ttk.LabelFrame(main_frame, text="交易配置", padding="10")
        config_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N), padx=(5, 0))
        
        ttk.Label(config_frame, text="交易金額 (TWD):").grid(row=0, column=0, sticky=tk.W)
        self.amount_var = tk.StringVar(value=str(self.trading_manager.config["trading_amount"]))
        self.amount_entry = ttk.Entry(config_frame, textvariable=self.amount_var, width=15)
        self.amount_entry.grid(row=0, column=1, padx=(5, 0))
        
        ttk.Label(config_frame, text="每日最大虧損:").grid(row=1, column=0, sticky=tk.W)
        self.max_loss_var = tk.StringVar(value=str(self.trading_manager.config["max_daily_loss"]))
        self.max_loss_entry = ttk.Entry(config_frame, textvariable=self.max_loss_var, width=15)
        self.max_loss_entry.grid(row=1, column=1, padx=(5, 0))
        
        ttk.Label(config_frame, text="每日最大交易次數:").grid(row=2, column=0, sticky=tk.W)
        self.max_trades_var = tk.StringVar(value=str(self.trading_manager.config["max_daily_trades"]))
        self.max_trades_entry = ttk.Entry(config_frame, textvariable=self.max_trades_var, width=15)
        self.max_trades_entry.grid(row=2, column=1, padx=(5, 0))
        
        self.dry_run_var = tk.BooleanVar(value=self.trading_manager.config["dry_run"])
        self.dry_run_check = ttk.Checkbutton(config_frame, text="模擬交易模式", variable=self.dry_run_var)
        self.dry_run_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(config_frame, text="保存配置", command=self.save_config).grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        # 日誌區域
        log_frame = ttk.LabelFrame(main_frame, text="系統日誌", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # 創建日誌文本框和滾動條
        self.log_text = tk.Text(log_frame, height=15, width=80)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置網格權重
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # 設置緊急按鈕樣式
        style = ttk.Style()
        style.configure("Emergency.TButton", foreground="red")
    
    def log_message(self, message: str):
        """添加日誌消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # 限制日誌行數
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            self.log_text.delete("1.0", "2.0")
    
    def start_system(self):
        """啟動系統"""
        if self.is_monitoring:
            messagebox.showwarning("警告", "系統已經在運行中！")
            return
        
        # 保存當前配置
        self.save_config()
        
        # 啟動監控
        self.is_monitoring = True
        self.trading_manager.start_monitoring()
        
        # 啟動監控線程
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.log_message("🚀 智能平衡交易系統已啟動")
        self.update_buttons()
    
    def stop_system(self):
        """停止系統"""
        if not self.is_monitoring:
            messagebox.showwarning("警告", "系統沒有在運行！")
            return
        
        self.is_monitoring = False
        self.trading_manager.stop_monitoring()
        
        self.log_message("⏹️ 智能平衡交易系統已停止")
        self.update_buttons()
    
    def emergency_stop(self):
        """緊急停止"""
        result = messagebox.askyesno("緊急停止", "確定要緊急停止系統嗎？\n這將立即停止所有交易活動！")
        
        if result:
            self.is_monitoring = False
            self.trading_manager.emergency_stop = True
            self.trading_manager.stop_monitoring()
            self.trading_manager.create_emergency_stop_file()
            
            self.log_message("🚨 系統緊急停止！所有交易活動已暫停")
            self.update_buttons()
            
            # 如果有持倉，提醒用戶
            if self.trading_manager.current_position:
                messagebox.showwarning("注意", "系統檢測到當前有持倉！\n請手動檢查並處理持倉狀況。")
    
    def save_config(self):
        """保存配置"""
        try:
            self.trading_manager.config["trading_amount"] = int(self.amount_var.get())
            self.trading_manager.config["max_daily_loss"] = int(self.max_loss_var.get())
            self.trading_manager.config["max_daily_trades"] = int(self.max_trades_var.get())
            self.trading_manager.config["dry_run"] = self.dry_run_var.get()
            
            self.trading_manager.save_config()
            self.log_message("✅ 配置已保存")
            
        except ValueError as e:
            messagebox.showerror("錯誤", "配置值格式錯誤，請檢查輸入！")
    
    def monitoring_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                # 檢查緊急停止文件
                if self.trading_manager.check_emergency_stop_file():
                    self.log_message("🚨 檢測到緊急停止文件，系統停止")
                    self.is_monitoring = False
                    break
                
                # 獲取最新數據
                df = self.data_fetcher.fetch_data('BTCTWD', limit=200)
                if df is not None and not df.empty:
                    # 檢測信號
                    signals = self.signal_detector.detect_smart_balanced_signals(df)
                    
                    if not signals.empty:
                        latest_signal = signals.iloc[-1]
                        
                        # 只處理買賣信號，忽略被拒絕的信號
                        if latest_signal['signal_type'] in ['buy', 'sell']:
                            result = self.trading_manager.execute_trade(latest_signal.to_dict())
                            
                            if result["success"]:
                                self.log_message(f"✅ {result['message']}")
                            else:
                                self.log_message(f"❌ 交易失敗: {result['reason']}")
                
                # 等待下一次檢查
                time.sleep(60)  # 每分鐘檢查一次
                
            except Exception as e:
                self.log_message(f"❌ 監控循環錯誤: {e}")
                time.sleep(30)  # 錯誤時等待30秒
    
    def update_display(self):
        """更新顯示"""
        status = self.trading_manager.get_status()
        
        # 更新系統狀態
        if status.get("emergency_stop"):
            status_text = "系統狀態: 🚨 緊急停止"
            self.status_label.configure(foreground="red")
        elif status.get("is_running"):
            status_text = "系統狀態: 🟢 運行中"
            self.status_label.configure(foreground="green")
        else:
            status_text = "系統狀態: 🔴 停止"
            self.status_label.configure(foreground="red")
        
        self.status_label.configure(text=status_text)
        
        # 更新持倉信息
        if self.trading_manager.current_position:
            pos = self.trading_manager.current_position
            position_text = f"當前持倉: {pos['side'].upper()} {pos['amount']:.6f} BTC @ {pos['entry_price']:,.0f}"
        else:
            position_text = "當前持倉: 無"
        
        self.position_label.configure(text=position_text)
        
        # 更新每日統計
        daily_text = f"今日統計: 交易{self.trading_manager.total_trades_today}次, 虧損{self.trading_manager.daily_loss:,.0f} TWD"
        self.daily_stats_label.configure(text=daily_text)
    
    def update_buttons(self):
        """更新按鈕狀態"""
        if self.is_monitoring:
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
        else:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
    
    def periodic_update(self):
        """定期更新"""
        self.update_display()
        self.root.after(5000, self.periodic_update)  # 每5秒更新一次
    
    def run(self):
        """運行控制面板"""
        self.root.mainloop()

def main():
    """主函數"""
    app = TradingControlPanel()
    app.run()

if __name__ == "__main__":
    main()