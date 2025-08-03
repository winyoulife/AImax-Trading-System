#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import sys
import os

# 設置路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_gui():
    """簡單的GUI測試"""
    root = tk.Tk()
    root.title("Multi-Timeframe MACD Backtest")
    root.geometry("800x600")
    
    # 創建標籤
    label = ttk.Label(root, text="Multi-Timeframe MACD Backtest GUI Test")
    label.pack(pady=20)
    
    # 創建按鈕
    def on_test():
        print("Test button clicked!")
        
    test_btn = ttk.Button(root, text="Test", command=on_test)
    test_btn.pack(pady=10)
    
    # 創建文本框
    text_area = tk.Text(root, height=20, width=80)
    text_area.pack(pady=10, padx=10, fill='both', expand=True)
    
    # 插入測試文本
    test_text = """Multi-Timeframe MACD Backtest Test
    
This is a simple GUI test to verify that the interface works correctly.
    
Features:
- 1 Hour MACD Strategy
- 30 Minute MA Strategy  
- 15 Minute Dynamic Tracking
- 5 Minute Independent Tracking
    
Status: GUI Test Successful!"""
    
    text_area.insert('1.0', test_text)
    
    root.mainloop()

if __name__ == "__main__":
    test_gui()