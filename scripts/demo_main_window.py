#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主視窗演示腳本
展示完整的MainWindow功能，包括狀態面板、控制面板和日誌面板
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """主演示函數"""
    print("🚀 AImax 主視窗演示")
    print("=" * 40)
    print("功能特點:")
    print("✅ 現代化GUI設計")
    print("✅ 實時狀態監控")
    print("✅ 交易控制面板")
    print("✅ 系統日誌顯示")
    print("✅ AI系統整合")
    print("=" * 40)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        
        # 創建應用程式
        app = QApplication(sys.argv)
        
        # 創建模擬AI組件
        demo_components = {
            'ai_manager': 'Enhanced AI Manager (Demo)',
            'trade_executor': 'Trade Executor (Demo)',
            'risk_manager': 'Risk Manager (Demo)',
            'system_integrator': 'System Integrator (Demo)'
        }
        
        # 創建主視窗
        print("正在創建主視窗...")
        window = MainWindow(demo_components)
        
        # 顯示視窗
        window.show()
        
        print("✅ 主視窗已啟動！")
        print("\n📋 使用指南:")
        print("1. 左上角：AI和交易狀態實時顯示")
        print("2. 左下角：交易控制和策略選擇")
        print("3. 右側：系統日誌和訊息")
        print("4. 菜單欄：文件、視圖、工具、幫助")
        print("5. 狀態欄：連接狀態顯示")
        print("\n🎮 可以嘗試的操作:")
        print("- 點擊「啟動交易」按鈕")
        print("- 選擇不同的交易策略")
        print("- 查看實時狀態更新")
        print("- 使用菜單欄功能")
        print("- 觀察日誌訊息")
        print("\n關閉視窗以結束演示...")
        
        # 運行應用程式
        exit_code = app.exec()
        
        print("👋 演示結束")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷演示")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 演示過程中發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()