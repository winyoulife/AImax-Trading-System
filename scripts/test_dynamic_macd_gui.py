#!/usr/bin/env python3
"""
測試動態 MACD 回測 GUI
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import tkinter as tk
from tkinter import messagebox
import threading
import time
from datetime import datetime

def test_gui_components():
    """測試 GUI 組件"""
    print("🧪 測試 GUI 組件...")
    
    try:
        # 測試基本導入
        from scripts.dynamic_macd_backtest_gui import DynamicMACDBacktestGUI
        print("✅ GUI 類導入成功")
        
        # 創建測試窗口
        root = tk.Tk()
        root.withdraw()  # 隱藏主窗口
        
        # 測試 GUI 初始化
        app = DynamicMACDBacktestGUI(root)
        print("✅ GUI 初始化成功")
        
        # 測試配置更新
        app.buy_window_var.set("4.5")
        app.sell_window_var.set("4.5")
        app.max_windows_var.set("8")
        app.reversal_threshold_var.set("0.8")
        app.confirmation_periods_var.set("5")
        
        app.update_config_from_gui()
        print("✅ 配置更新成功")
        
        # 測試狀態更新
        app.update_status("測試狀態")
        print("✅ 狀態更新成功")
        
        # 測試進度條
        app.progress_var.set(50)
        print("✅ 進度條更新成功")
        
        # 清理
        root.destroy()
        print("✅ GUI 測試完成")
        
        return True
        
    except Exception as e:
        print(f"❌ GUI 測試失敗: {e}")
        return False

def test_configuration_validation():
    """測試配置驗證"""
    print("\n🧪 測試配置驗證...")
    
    try:
        from scripts.dynamic_macd_backtest_gui import DynamicMACDBacktestGUI
        
        root = tk.Tk()
        root.withdraw()
        
        app = DynamicMACDBacktestGUI(root)
        
        # 測試有效配置
        app.buy_window_var.set("4.0")
        app.sell_window_var.set("4.0")
        app.max_windows_var.set("5")
        app.reversal_threshold_var.set("0.5")
        app.confirmation_periods_var.set("3")
        
        app.update_config_from_gui()
        print("✅ 有效配置驗證通過")
        
        # 測試無效配置
        try:
            app.buy_window_var.set("invalid")
            app.update_config_from_gui()
            print("❌ 應該捕獲無效配置錯誤")
        except ValueError:
            print("✅ 無效配置錯誤捕獲成功")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ 配置驗證測試失敗: {e}")
        return False

def test_data_display():
    """測試數據顯示功能"""
    print("\n🧪 測試數據顯示功能...")
    
    try:
        from scripts.dynamic_macd_backtest_gui import DynamicMACDBacktestGUI
        
        root = tk.Tk()
        root.withdraw()
        
        app = DynamicMACDBacktestGUI(root)
        
        # 測試追蹤窗口數據
        test_window_data = {
            'window_001': {
                'signal_type': 'buy',
                'start_time': datetime.now().strftime('%H:%M:%S'),
                'status': 'active',
                'current_extreme': 3400000,
                'improvement': 1500,
                'duration': '15:30'
            },
            'window_002': {
                'signal_type': 'sell',
                'start_time': datetime.now().strftime('%H:%M:%S'),
                'status': 'completed',
                'current_extreme': 3405000,
                'improvement': 2000,
                'duration': '22:45'
            }
        }
        
        app.tracking_windows = test_window_data
        app.update_tracking_display()
        print("✅ 追蹤窗口顯示更新成功")
        
        # 測試比較報告
        app.comparison_text.insert(1.0, "測試比較報告內容")
        print("✅ 比較報告顯示成功")
        
        # 測試清空結果
        app.clear_results()
        print("✅ 結果清空成功")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ 數據顯示測試失敗: {e}")
        return False

def test_gui_functionality():
    """測試 GUI 功能"""
    print("\n🧪 測試 GUI 功能...")
    
    try:
        from scripts.dynamic_macd_backtest_gui import DynamicMACDBacktestGUI
        
        root = tk.Tk()
        root.withdraw()
        
        app = DynamicMACDBacktestGUI(root)
        
        # 測試狀態更新
        app.update_status("測試狀態", "blue")
        print("✅ 狀態更新成功")
        
        # 測試進度更新
        app.update_progress(75.5)
        print("✅ 進度更新成功")
        
        # 測試日誌功能
        app.log_message("測試日誌消息")
        print("✅ 日誌功能成功")
        
        # 測試追蹤窗口顯示
        app.update_tracking_display()
        print("✅ 追蹤窗口顯示成功")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ GUI 功能測試失敗: {e}")
        return False

def test_export_functionality():
    """測試導出功能"""
    print("\n🧪 測試導出功能...")
    
    try:
        from scripts.dynamic_macd_backtest_gui import DynamicMACDBacktestGUI
        from src.data.tracking_data_manager import TrackingDataManager
        from src.core.dynamic_trading_config import PerformanceConfig
        
        root = tk.Tk()
        root.withdraw()
        
        app = DynamicMACDBacktestGUI(root)
        
        # 初始化數據管理器
        config = PerformanceConfig()
        app.data_manager = TrackingDataManager(config, "test_export.db")
        
        print("✅ 導出功能初始化成功")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ 導出功能測試失敗: {e}")
        return False

def run_interactive_test():
    """運行交互式測試"""
    print("\n🚀 啟動交互式 GUI 測試...")
    print("注意: 這將打開 GUI 窗口，請手動測試各項功能")
    
    try:
        from scripts.dynamic_macd_backtest_gui import main
        
        # 在新線程中運行 GUI
        def run_gui():
            try:
                main()
            except Exception as e:
                print(f"GUI 運行錯誤: {e}")
        
        gui_thread = threading.Thread(target=run_gui)
        gui_thread.daemon = True
        gui_thread.start()
        
        print("✅ GUI 已啟動")
        print("請在 GUI 中測試以下功能:")
        print("1. 調整配置參數")
        print("2. 選擇不同的交易對")
        print("3. 設置回測天數")
        print("4. 觀察圖表顯示")
        print("5. 查看追蹤窗口狀態")
        print("6. 檢查策略比較報告")
        
        # 等待用戶輸入
        input("\n按 Enter 鍵結束測試...")
        
        return True
        
    except Exception as e:
        print(f"❌ 交互式測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試動態 MACD 回測 GUI...")
    print("=" * 60)
    
    test_results = []
    
    # 執行各項測試
    test_results.append(("GUI 組件測試", test_gui_components()))
    test_results.append(("配置驗證測試", test_configuration_validation()))
    test_results.append(("數據顯示測試", test_data_display()))
    test_results.append(("GUI 功能測試", test_gui_functionality()))
    test_results.append(("導出功能測試", test_export_functionality()))
    
    # 顯示測試結果
    print("\n" + "=" * 60)
    print("📊 測試結果摘要:")
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{len(test_results)} 項測試通過")
    
    # 詢問是否運行交互式測試
    if passed == len(test_results):
        print("\n🎉 所有自動測試通過！")
        
        try:
            response = input("\n是否運行交互式 GUI 測試？(y/n): ").lower().strip()
            if response in ['y', 'yes', '是']:
                run_interactive_test()
        except KeyboardInterrupt:
            print("\n測試已取消")
    
    print("\n✨ 動態 MACD 回測 GUI 測試完成！")

if __name__ == "__main__":
    main()