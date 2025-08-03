#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI啟動器演示腳本
展示依賴檢查、啟動畫面和GUI啟動流程
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """主演示函數"""
    print("🚀 AImax GUI啟動器演示")
    print("=" * 40)
    
    try:
        from src.gui.simple_gui_launcher import SimpleGUILauncher
        
        # 創建啟動器
        launcher = SimpleGUILauncher()
        
        # 設置回調函數
        def on_gui_ready(main_window):
            print("✅ GUI啟動成功！主視窗已顯示")
            print("📝 注意：這是臨時界面，主視窗將在後續任務中完善")
        
        def on_launch_failed(error_message):
            print(f"❌ GUI啟動失敗: {error_message}")
            sys.exit(1)
        
        # 連接信號
        launcher.gui_ready.connect(on_gui_ready)
        launcher.launch_failed.connect(on_launch_failed)
        
        # 啟動GUI
        print("正在啟動GUI...")
        if launcher.launch_gui():
            print("🎯 啟動流程已開始，請查看啟動畫面")
            
            # 運行應用程式
            exit_code = launcher.app.exec()
            
            # 清理資源
            launcher.cleanup()
            
            print("👋 GUI已關閉")
            sys.exit(exit_code)
        else:
            print("❌ 無法啟動GUI")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷啟動")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 演示過程中發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()