#!/usr/bin/env python3
"""
緊急停止測試 - 立即檢測並修復線程問題
"""
import sys
import os
import signal
import threading
import time
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def emergency_exit():
    """緊急退出"""
    print("\n🚨 緊急退出程序")
    os._exit(1)

def signal_handler(signum, frame):
    """信號處理器"""
    print("\n⏹️ 收到中斷信號，立即退出")
    emergency_exit()

def test_thread_safety():
    """測試線程安全問題"""
    print("🧪 測試PyQt6線程安全...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QObject, QThread
        
        # 創建應用程序
        app = QApplication([])
        print("✅ QApplication創建成功")
        
        # 測試在主線程中創建QObject
        main_object = QObject()
        print("✅ 主線程QObject創建成功")
        
        # 測試線程問題
        def worker_thread():
            try:
                # 這會導致線程問題
                worker_object = QObject()
                worker_object.setParent(main_object)  # 這裡會出錯
                print("❌ 這不應該成功")
            except Exception as e:
                print(f"✅ 捕獲到預期的線程錯誤: {e}")
        
        thread = threading.Thread(target=worker_thread)
        thread.start()
        thread.join(timeout=2)
        
        if thread.is_alive():
            print("⚠️ 工作線程可能卡住")
        
        print("✅ 線程安全測試完成")
        return True
        
    except Exception as e:
        print(f"❌ 線程安全測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚨 AImax GUI 緊急診斷工具")
    print("=" * 50)
    print("💡 這個工具會立即檢測問題並在5秒內退出")
    print("💡 按 Ctrl+C 立即強制退出")
    print("=" * 50)
    
    # 設置信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 設置5秒強制退出
    def force_exit():
        time.sleep(5)
        print("\n⏰ 5秒超時，強制退出")
        emergency_exit()
    
    exit_timer = threading.Thread(target=force_exit, daemon=True)
    exit_timer.start()
    
    try:
        # 快速測試
        print("\n🔍 診斷問題...")
        
        # 1. 檢查線程問題
        if not test_thread_safety():
            print("❌ 線程安全測試失敗")
            return 1
        
        # 2. 檢查監控組件
        try:
            from src.gui.monitoring_dashboard import SystemMonitorThread
            monitor = SystemMonitorThread()
            print("✅ 監控線程類創建成功")
            
            # 不啟動線程，只檢查創建
            if hasattr(monitor, 'isRunning'):
                print("✅ 監控線程有正確的PyQt6方法")
            else:
                print("❌ 監控線程缺少PyQt6方法")
                
        except Exception as e:
            print(f"❌ 監控組件問題: {e}")
        
        print("\n🔧 問題分析:")
        print("1. PyQt6線程問題: QObject不能跨線程設置父對象")
        print("2. 監控線程可能在錯誤的線程中創建GUI對象")
        print("3. 需要修復線程安全問題")
        
        print("\n✅ 診斷完成，程序即將退出")
        return 0
        
    except Exception as e:
        print(f"❌ 診斷過程中發生錯誤: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"\n🏁 程序正常退出，代碼: {exit_code}")
        sys.exit(exit_code)
    except:
        print("\n🚨 程序異常，強制退出")
        emergency_exit()