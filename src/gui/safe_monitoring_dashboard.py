"""
線程安全的監控儀表板 - 修復版本
"""
import sys
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import time

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QGridLayout, QLabel, QProgressBar, QPushButton, QTextEdit,
        QTabWidget, QGroupBox, QStatusBar
    )
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt6 未安裝，監控界面將使用文本模式")

class SafePerformanceWidget(QWidget if PYQT_AVAILABLE else object):
    """線程安全的性能監控組件"""
    
    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setup_ui()
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 系統資源組
        system_group = QGroupBox("系統資源")
        system_layout = QGridLayout(system_group)
        
        # CPU使用率
        system_layout.addWidget(QLabel("CPU使用率:"), 0, 0)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_label = QLabel("0%")
        system_layout.addWidget(self.cpu_progress, 0, 1)
        system_layout.addWidget(self.cpu_label, 0, 2)
        
        # 內存使用率
        system_layout.addWidget(QLabel("內存使用率:"), 1, 0)
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_label = QLabel("0%")
        system_layout.addWidget(self.memory_progress, 1, 1)
        system_layout.addWidget(self.memory_label, 1, 2)
        
        layout.addWidget(system_group)
        
        # 監控日誌
        log_group = QGroupBox("監控日誌")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
    
    def update_performance_data(self, cpu_percent: float, memory_percent: float, memory_used_mb: float):
        """更新性能數據 - 線程安全"""
        if not PYQT_AVAILABLE:
            print(f"🔄 性能更新: CPU {cpu_percent:.1f}%, 內存 {memory_percent:.1f}%")
            return
        
        try:
            # 更新CPU
            self.cpu_progress.setValue(int(cpu_percent))
            self.cpu_label.setText(f"{cpu_percent:.1f}%")
            
            # 更新內存
            self.memory_progress.setValue(int(memory_percent))
            self.memory_label.setText(f"{memory_percent:.1f}% ({memory_used_mb:.0f}MB)")
            
            # 添加日誌
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_text = f"[{timestamp}] CPU: {cpu_percent:.1f}%, 內存: {memory_percent:.1f}%"
            self.log_text.append(log_text)
            
            # 限制日誌長度
            if self.log_text.document().lineCount() > 50:
                cursor = self.log_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                cursor.select(cursor.SelectionType.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()
            
        except Exception as e:
            self.logger.error(f"❌ 更新性能數據失敗: {e}")

class SafeAIStatusWidget(QWidget if PYQT_AVAILABLE else object):
    """線程安全的AI狀態監控組件"""
    
    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setup_ui()
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # AI模型狀態
        models_group = QGroupBox("AI模型狀態")
        models_layout = QGridLayout(models_group)
        
        # 表頭
        models_layout.addWidget(QLabel("模型"), 0, 0)
        models_layout.addWidget(QLabel("狀態"), 0, 1)
        
        # 三個AI模型
        models_layout.addWidget(QLabel("🚀 市場掃描員"), 1, 0)
        self.scanner_status = QLabel("就緒")
        self.scanner_status.setStyleSheet("color: green;")
        models_layout.addWidget(self.scanner_status, 1, 1)
        
        models_layout.addWidget(QLabel("🔍 深度分析師"), 2, 0)
        self.analyst_status = QLabel("就緒")
        self.analyst_status.setStyleSheet("color: green;")
        models_layout.addWidget(self.analyst_status, 2, 1)
        
        models_layout.addWidget(QLabel("🧠 最終決策者"), 3, 0)
        self.decision_status = QLabel("就緒")
        self.decision_status.setStyleSheet("color: green;")
        models_layout.addWidget(self.decision_status, 3, 1)
        
        layout.addWidget(models_group)
        
        # AI協作狀態
        collab_group = QGroupBox("AI協作狀態")
        collab_layout = QGridLayout(collab_group)
        
        collab_layout.addWidget(QLabel("信心度:"), 0, 0)
        self.confidence_progress = QProgressBar()
        self.confidence_progress.setRange(0, 100)
        self.confidence_progress.setValue(67)  # 默認值
        self.confidence_label = QLabel("67%")
        collab_layout.addWidget(self.confidence_progress, 0, 1)
        collab_layout.addWidget(self.confidence_label, 0, 2)
        
        layout.addWidget(collab_group)
    
    def update_ai_status(self, confidence: float = 67.0):
        """更新AI狀態 - 線程安全"""
        if not PYQT_AVAILABLE:
            print(f"🤖 AI狀態: 信心度 {confidence:.1f}%")
            return
        
        try:
            self.confidence_progress.setValue(int(confidence))
            self.confidence_label.setText(f"{confidence:.1f}%")
        except Exception as e:
            self.logger.error(f"❌ 更新AI狀態失敗: {e}")

class SafeMonitoringDashboard(QMainWindow if PYQT_AVAILABLE else object):
    """線程安全的監控儀表板"""
    
    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        self.logger = logging.getLogger(__name__)
        self.monitoring_active = False
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """設置用戶界面"""
        if not PYQT_AVAILABLE:
            self.logger.info("🖥️ 監控儀表板運行在文本模式")
            return
            
        self.setWindowTitle("AImax 安全監控儀表板")
        self.setGeometry(100, 100, 1000, 700)
        
        # 中央組件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主佈局
        main_layout = QHBoxLayout(central_widget)
        
        # 左側控制面板
        left_panel = QWidget()
        left_panel.setMaximumWidth(200)
        left_layout = QVBoxLayout(left_panel)
        
        # 控制按鈕
        self.start_button = QPushButton("🚀 開始監控")
        self.start_button.clicked.connect(self.start_monitoring)
        left_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏹️ 停止監控")
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        left_layout.addWidget(self.stop_button)
        
        # 系統狀態
        left_layout.addWidget(QLabel("系統狀態:"))
        self.system_status = QLabel("🔴 未啟動")
        left_layout.addWidget(self.system_status)
        
        # 自動退出按鈕
        self.exit_button = QPushButton("❌ 安全退出")
        self.exit_button.clicked.connect(self.safe_exit)
        left_layout.addWidget(self.exit_button)
        
        left_layout.addStretch()
        main_layout.addWidget(left_panel)
        
        # 右側監控區域
        content_area = QTabWidget()
        
        # 性能監控標籤
        self.performance_widget = SafePerformanceWidget()
        content_area.addTab(self.performance_widget, "📊 性能監控")
        
        # AI狀態標籤
        self.ai_status_widget = SafeAIStatusWidget()
        content_area.addTab(self.ai_status_widget, "🤖 AI狀態")
        
        main_layout.addWidget(content_area)
        
        # 狀態欄
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備就緒")
        
        # 設置樣式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
    
    def setup_timer(self):
        """設置定時器 - 在主線程中運行，避免線程問題"""
        if not PYQT_AVAILABLE:
            return
            
        # 監控定時器
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_monitoring_data)
        self.monitor_timer.setInterval(2000)  # 2秒更新一次
        
        # 自動退出定時器（5分鐘）
        self.auto_exit_timer = QTimer()
        self.auto_exit_timer.setSingleShot(True)
        self.auto_exit_timer.timeout.connect(self.auto_exit)
        self.auto_exit_timer.start(300000)  # 5分鐘
    
    def update_monitoring_data(self):
        """更新監控數據 - 在主線程中運行"""
        try:
            import psutil
            
            # 收集系統數據
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # 更新性能組件
            self.performance_widget.update_performance_data(
                cpu_percent, 
                memory.percent, 
                memory.used / (1024 * 1024)
            )
            
            # 更新AI狀態（模擬數據）
            import random
            confidence = 60 + random.random() * 20  # 60-80%
            self.ai_status_widget.update_ai_status(confidence)
            
            # 更新狀態欄
            if PYQT_AVAILABLE:
                self.status_bar.showMessage(
                    f"監控中 - CPU: {cpu_percent:.1f}%, 內存: {memory.percent:.1f}%"
                )
            
        except Exception as e:
            self.logger.error(f"❌ 更新監控數據失敗: {e}")
            if PYQT_AVAILABLE:
                self.status_bar.showMessage(f"監控錯誤: {e}")
    
    def start_monitoring(self):
        """開始監控"""
        if self.monitoring_active:
            return
            
        try:
            self.monitoring_active = True
            
            if PYQT_AVAILABLE:
                self.monitor_timer.start()
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.system_status.setText("🟢 監控中")
                self.status_bar.showMessage("監控已啟動")
            
            self.logger.info("🚀 安全監控已啟動")
            
        except Exception as e:
            self.logger.error(f"❌ 啟動監控失敗: {e}")
            self.monitoring_active = False
    
    def stop_monitoring(self):
        """停止監控"""
        try:
            self.monitoring_active = False
            
            if PYQT_AVAILABLE:
                self.monitor_timer.stop()
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.system_status.setText("🔴 已停止")
                self.status_bar.showMessage("監控已停止")
            
            self.logger.info("⏹️ 安全監控已停止")
            
        except Exception as e:
            self.logger.error(f"❌ 停止監控失敗: {e}")
    
    def safe_exit(self):
        """安全退出"""
        try:
            self.stop_monitoring()
            
            if PYQT_AVAILABLE:
                self.status_bar.showMessage("正在安全退出...")
                # 延遲退出，確保清理完成
                QTimer.singleShot(500, self.close)
            
            self.logger.info("🚪 安全退出中...")
            
        except Exception as e:
            self.logger.error(f"❌ 安全退出失敗: {e}")
    
    def auto_exit(self):
        """自動退出"""
        self.logger.info("⏰ 5分鐘自動退出觸發")
        if PYQT_AVAILABLE:
            self.status_bar.showMessage("自動退出中...")
        self.safe_exit()
    
    def closeEvent(self, event):
        """關閉事件"""
        self.stop_monitoring()
        if PYQT_AVAILABLE:
            event.accept()

def main():
    """主函數"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if PYQT_AVAILABLE:
        app = QApplication(sys.argv)
        dashboard = SafeMonitoringDashboard()
        dashboard.show()
        
        print("✅ 安全監控儀表板已啟動")
        print("💡 這個版本完全線程安全，不會卡住")
        print("⏰ 程序將在5分鐘後自動退出")
        print("💡 按 Ctrl+C 或點擊 '安全退出' 可隨時退出")
        
        sys.exit(app.exec())
    else:
        # 文本模式
        print("📝 文本模式監控")
        dashboard = SafeMonitoringDashboard()
        
        try:
            import psutil
            for i in range(60):  # 運行60次
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"CPU: {cpu_percent:.1f}%, 內存: {memory.percent:.1f}%")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ 用戶中斷")
        
        print("✅ 文本模式監控完成")

if __name__ == "__main__":
    main()