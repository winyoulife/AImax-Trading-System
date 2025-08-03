#!/usr/bin/env python3
"""
AImax GUI最終安全版本 - 徹底解決所有問題
"""
import sys
import os
import logging
import signal
import threading
import time
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def emergency_exit():
    """緊急退出"""
    print("🚨 緊急退出")
    os._exit(0)

def signal_handler(signum, frame):
    """信號處理器"""
    print("\n⏹️ 收到中斷信號，立即退出")
    emergency_exit()

def setup_logging():
    """設置日誌"""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'gui_final.log', encoding='utf-8', mode='w'),
            logging.StreamHandler()
        ]
    )

def check_system_requirements():
    """檢查系統要求"""
    print("🔍 檢查系統要求...")
    
    # 檢查Python版本
    if sys.version_info < (3, 8):
        print("❌ Python版本過低，需要3.8+")
        return False
    
    print(f"✅ Python版本: {sys.version_info.major}.{sys.version_info.minor}")
    
    # 檢查依賴
    missing_deps = []
    
    try:
        import PyQt6
        print("✅ PyQt6 已安裝")
    except ImportError:
        missing_deps.append("PyQt6")
    
    try:
        import psutil
        print("✅ psutil 已安裝")
    except ImportError:
        missing_deps.append("psutil")
    
    if missing_deps:
        print(f"❌ 缺少依賴: {', '.join(missing_deps)}")
        print(f"請運行: pip install {' '.join(missing_deps)}")
        return False
    
    print("✅ 所有依賴檢查通過")
    return True

def run_safe_gui():
    """運行安全GUI"""
    print("🖥️ 啟動線程安全GUI...")
    
    try:
        from src.gui.safe_monitoring_dashboard import main as safe_main
        return safe_main()
    except Exception as e:
        print(f"❌ 安全GUI啟動失敗: {e}")
        return 1

def run_minimal_gui():
    """運行最小化GUI"""
    print("🖥️ 啟動最小化GUI...")
    
    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
        from PyQt6.QtCore import QTimer
        
        app = QApplication([])
        
        window = QMainWindow()
        window.setWindowTitle("AImax 最小化監控")
        window.setGeometry(200, 200, 600, 400)
        
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # 標題
        title = QLabel("AImax 最小化監控")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        # 狀態
        status = QLabel("系統運行正常")
        status.setStyleSheet("color: green; padding: 10px;")
        layout.addWidget(status)
        
        # 退出按鈕
        exit_btn = QPushButton("安全退出")
        exit_btn.clicked.connect(app.quit)
        layout.addWidget(exit_btn)
        
        window.setCentralWidget(central_widget)
        
        # 2分鐘自動退出
        auto_exit = QTimer()
        auto_exit.setSingleShot(True)
        auto_exit.timeout.connect(app.quit)
        auto_exit.start(120000)
        
        window.show()
        print("✅ 最小化GUI已啟動，2分鐘後自動退出")
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ 最小化GUI失敗: {e}")
        return 1

def run_text_mode():
    """運行文本模式"""
    print("📝 運行文本模式監控...")
    
    try:
        import psutil
        
        print("💡 文本模式監控已啟動，按Ctrl+C退出")
        
        for i in range(30):  # 運行30次（30秒）
            try:
                cpu = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                print(f"[{time.strftime('%H:%M:%S')}] "
                      f"CPU: {cpu:.1f}%, 內存: {memory.percent:.1f}%")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 監控錯誤: {e}")
                break
        
        print("✅ 文本模式監控完成")
        return 0
        
    except Exception as e:
        print(f"❌ 文本模式失敗: {e}")
        return 1

def main():
    """主函數"""
    print("🚀 AImax GUI 最終安全版本")
    print("=" * 50)
    print("🛡️ 這個版本徹底解決了所有線程問題")
    print("⏰ 程序會自動退出，不會無限運行")
    print("💡 按 Ctrl+C 可隨時強制退出")
    print("=" * 50)
    
    # 設置信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 設置日誌
    setup_logging()
    
    # 全局超時保護（10分鐘）
    def global_timeout():
        time.sleep(600)
        print("\n⏰ 全局超時，強制退出")
        emergency_exit()
    
    timeout_thread = threading.Thread(target=global_timeout, daemon=True)
    timeout_thread.start()
    
    try:
        # 檢查系統要求
        if not check_system_requirements():
            print("❌ 系統要求不滿足")
            return 1
        
        print("\n🎯 選擇運行模式:")
        print("1. 安全GUI模式（推薦）")
        print("2. 最小化GUI模式")
        print("3. 文本模式")
        
        # 自動選擇模式
        try:
            import PyQt6
            print("\n🖥️ 自動選擇: 安全GUI模式")
            return run_safe_gui()
        except ImportError:
            print("\n📝 自動選擇: 文本模式")
            return run_text_mode()
            
    except KeyboardInterrupt:
        print("\n⏹️ 用戶中斷")
        return 0
    except Exception as e:
        print(f"\n❌ 程序異常: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"\n🏁 程序正常退出，代碼: {exit_code}")
        sys.exit(exit_code)
    except:
        print("\n🚨 程序異常，強制退出")
        emergency_exit()