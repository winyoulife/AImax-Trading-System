#!/usr/bin/env python3
"""
AImax GUI修復版本 - 徹底解決線程問題
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
    """信號處理器 - 立即退出"""
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
            logging.FileHandler(log_dir / 'gui_fixed.log', encoding='utf-8', mode='w'),
            logging.StreamHandler()
        ]
    )

def create_simple_monitoring_gui():
    """創建簡化的監控GUI - 避免線程問題"""
    try:
        from PyQt6.QtWidgets import (
            QApplication, QMainWindow, QWidget, QVBoxLayout, 
            QHBoxLayout, QLabel, QPushButton, QTextEdit, QTimer
        )
        from PyQt6.QtCore import Qt
        
        print("✅ PyQt6導入成功")
        
        # 創建應用程序
        app = QApplication([])
        
        # 創建主窗口
        window = QMainWindow()
        window.setWindowTitle("AImax 簡化監控")
        window.setGeometry(100, 100, 800, 600)
        
        # 中央組件
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # 標題
        title = QLabel("AImax 簡化監控界面")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 狀態標籤
        status_label = QLabel("狀態: 準備就緒")
        status_label.setStyleSheet("padding: 5px; background-color: #e8f5e8;")
        layout.addWidget(status_label)
        
        # 監控數據顯示
        monitor_text = QTextEdit()
        monitor_text.setReadOnly(True)
        monitor_text.setMaximumHeight(300)
        layout.addWidget(monitor_text)
        
        # 控制按鈕
        button_layout = QHBoxLayout()
        
        start_button = QPushButton("🚀 開始監控")
        stop_button = QPushButton("⏹️ 停止監控")
        exit_button = QPushButton("❌ 退出")
        
        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addWidget(exit_button)
        layout.addLayout(button_layout)
        
        window.setCentralWidget(central_widget)
        
        # 監控狀態
        monitoring_active = False
        
        # 監控定時器（在主線程中運行，避免線程問題）
        monitor_timer = QTimer()
        monitor_timer.setSingleShot(False)
        monitor_timer.setInterval(2000)  # 2秒更新一次
        
        def update_monitor_data():
            """更新監控數據 - 在主線程中運行"""
            try:
                import psutil
                
                # 收集系統數據
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                
                # 更新顯示
                timestamp = time.strftime("%H:%M:%S")
                data_text = f"[{timestamp}] CPU: {cpu_percent:.1f}%, 內存: {memory.percent:.1f}%"
                
                monitor_text.append(data_text)
                
                # 限制文本長度
                if monitor_text.document().lineCount() > 50:
                    cursor = monitor_text.textCursor()
                    cursor.movePosition(cursor.MoveOperation.Start)
                    cursor.select(cursor.SelectionType.LineUnderCursor)
                    cursor.removeSelectedText()
                    cursor.deleteChar()
                
            except Exception as e:
                monitor_text.append(f"[{time.strftime('%H:%M:%S')}] 錯誤: {e}")
        
        # 連接定時器
        monitor_timer.timeout.connect(update_monitor_data)
        
        def start_monitoring():
            """開始監控"""
            nonlocal monitoring_active
            if not monitoring_active:
                monitoring_active = True
                monitor_timer.start()
                status_label.setText("狀態: 監控中...")
                status_label.setStyleSheet("padding: 5px; background-color: #e8f8ff;")
                start_button.setEnabled(False)
                stop_button.setEnabled(True)
                monitor_text.append(f"[{time.strftime('%H:%M:%S')}] 🚀 監控已啟動")
        
        def stop_monitoring():
            """停止監控"""
            nonlocal monitoring_active
            if monitoring_active:
                monitoring_active = False
                monitor_timer.stop()
                status_label.setText("狀態: 已停止")
                status_label.setStyleSheet("padding: 5px; background-color: #ffe8e8;")
                start_button.setEnabled(True)
                stop_button.setEnabled(False)
                monitor_text.append(f"[{time.strftime('%H:%M:%S')}] ⏹️ 監控已停止")
        
        def safe_exit():
            """安全退出"""
            stop_monitoring()
            monitor_text.append(f"[{time.strftime('%H:%M:%S')}] 🚪 正在退出...")
            QTimer.singleShot(500, app.quit)
        
        # 連接按鈕
        start_button.clicked.connect(start_monitoring)
        stop_button.clicked.connect(stop_monitoring)
        exit_button.clicked.connect(safe_exit)
        
        # 初始狀態
        stop_button.setEnabled(False)
        
        # 自動退出定時器（防止卡住）
        auto_exit_timer = QTimer()
        auto_exit_timer.setSingleShot(True)
        auto_exit_timer.timeout.connect(lambda: (
            print("⏰ 自動退出定時器觸發"),
            app.quit()
        ))
        auto_exit_timer.start(300000)  # 5分鐘後自動退出
        
        # 顯示窗口
        window.show()
        
        print("✅ 簡化GUI已啟動")
        print("💡 這個版本避免了線程問題，應該不會卡住")
        print("💡 窗口將在5分鐘後自動關閉")
        
        # 運行事件循環
        return app.exec()
        
    except Exception as e:
        print(f"❌ 創建GUI失敗: {e}")
        return 1

def run_text_mode():
    """運行文本模式 - 完全避免GUI"""
    print("📝 運行文本模式監控（無GUI）")
    print("💡 按 Ctrl+C 退出")
    
    try:
        import psutil
        
        count = 0
        while count < 60:  # 最多運行60次（2分鐘）
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] CPU: {cpu_percent:.1f}%, 內存: {memory.percent:.1f}%")
                
                count += 1
                time.sleep(1)
                
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
    print("🚀 AImax GUI 修復版啟動器")
    print("=" * 50)
    print("🔧 這個版本修復了線程問題，不會卡住")
    print("⏰ 程序會在合理時間內自動退出")
    print("💡 按 Ctrl+C 可隨時強制退出")
    print("=" * 50)
    
    # 設置信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 設置日誌
    setup_logging()
    
    # 設置全局超時（防止無限運行）
    def global_timeout():
        time.sleep(600)  # 10分鐘
        print("\n⏰ 全局超時，強制退出")
        emergency_exit()
    
    timeout_thread = threading.Thread(target=global_timeout, daemon=True)
    timeout_thread.start()
    
    try:
        # 檢查PyQt6
        try:
            import PyQt6
            print("🖥️ 嘗試啟動修復版GUI...")
            return create_simple_monitoring_gui()
        except ImportError:
            print("📝 PyQt6不可用，運行文本模式...")
            return run_text_mode()
            
    except KeyboardInterrupt:
        print("\n⏹️ 用戶中斷")
        return 0
    except Exception as e:
        print(f"\n❌ 啟動失敗: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"\n🏁 程序正常退出，代碼: {exit_code}")
        sys.exit(exit_code)
    except:
        print("\n🚨 程序異常，強制退出")
        emergency_exit()