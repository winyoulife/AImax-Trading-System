#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易主視窗測試腳本
測試新的交易GUI界面功能
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from src.gui.trading_main_window import TradingMainWindow


def test_trading_window():
    """測試交易主視窗"""
    print("🧪 測試交易主視窗")
    print("=" * 50)
    
    try:
        # 創建應用程式
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # 創建交易主視窗
        print("📋 創建交易主視窗...")
        window = TradingMainWindow()
        
        # 顯示視窗
        print("🖥️ 顯示視窗...")
        window.show()
        
        print("✅ 交易主視窗測試成功！")
        print("\n💡 功能說明:")
        print("   • 左側面板: AI狀態、交易狀態、系統資訊、控制面板、策略選擇")
        print("   • 右側面板: 價格圖表、交易記錄、系統日誌")
        print("   • 菜單欄: 文件、工具、幫助")
        print("   • 工具欄: 快速操作按鈕")
        print("   • 狀態欄: 系統狀態顯示")
        print("\n🎮 操作說明:")
        print("   • 點擊 '🚀 開始交易' 按鈕開始模擬交易")
        print("   • 選擇不同的交易策略")
        print("   • 查看實時更新的系統資訊")
        print("   • 關閉視窗退出程式")
        
        # 運行應用程式
        return app.exec()
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return 1


if __name__ == "__main__":
    exit_code = test_trading_window()
    sys.exit(exit_code)