#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
啟動畫面 - 顯示系統載入進度和狀態
提供友好的用戶體驗，避免黑屏等待
"""

import sys
from typing import Optional
from PyQt6.QtWidgets import (QApplication, QSplashScreen, QLabel, 
                            QProgressBar, QVBoxLayout, QWidget, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QPalette


class LoadingWorker(QObject):
    """載入工作線程"""
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.should_stop = False
    
    def start_loading(self):
        """開始載入過程"""
        try:
            # 模擬載入步驟
            steps = [
                (10, "檢查系統依賴..."),
                (25, "初始化GUI組件..."),
                (40, "連接AI系統..."),
                (60, "載入交易模組..."),
                (80, "準備用戶界面..."),
                (100, "啟動完成！")
            ]
            
            for progress, message in steps:
                if self.should_stop:
                    break
                    
                self.progress_updated.emit(progress, message)
                
                # 模擬載入時間
                import time
                time.sleep(0.3)
            
            if not self.should_stop:
                self.finished.emit(True, "系統啟動成功")
            
        except Exception as e:
            self.finished.emit(False, f"啟動失敗: {str(e)}")
    
    def stop(self):
        """停止載入"""
        self.should_stop = True


class SplashScreen(QSplashScreen):
    """自定義啟動畫面"""
    
    loading_finished = pyqtSignal(bool, str)
    
    def __init__(self, parent=None):
        # 創建啟動畫面背景
        pixmap = self.create_splash_pixmap()
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        
        self.setWindowFlags(
            Qt.WindowType.SplashScreen | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # 設置UI組件
        self.setup_ui()
        
        # 載入工作線程
        self.loading_thread = QThread()
        self.loading_worker = LoadingWorker()
        self.loading_worker.moveToThread(self.loading_thread)
        
        # 連接信號
        self.loading_worker.progress_updated.connect(self.update_progress)
        self.loading_worker.finished.connect(self.on_loading_finished)
        self.loading_thread.started.connect(self.loading_worker.start_loading)
        
        # 自動關閉定時器（防止卡死）
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.on_timeout)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.start(10000)  # 10秒超時
    
    def create_splash_pixmap(self) -> QPixmap:
        """創建啟動畫面背景圖片"""
        width, height = 400, 300
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(45, 45, 48))  # 深色背景
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 繪製標題
        painter.setPen(QColor(255, 255, 255))
        title_font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.drawText(50, 80, "AImax")
        
        # 繪製副標題
        subtitle_font = QFont("Arial", 12)
        painter.setFont(subtitle_font)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(50, 110, "AI交易系統")
        
        # 繪製版本信息
        version_font = QFont("Arial", 10)
        painter.setFont(version_font)
        painter.setPen(QColor(150, 150, 150))
        painter.drawText(50, 130, "版本 2.0 - GUI修復版")
        
        # 繪製裝飾線條
        painter.setPen(QColor(0, 150, 255))
        painter.drawLine(50, 150, 350, 150)
        
        painter.end()
        return pixmap
    
    def setup_ui(self):
        """設置UI組件"""
        # 創建進度條和狀態標籤
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                background-color: #333;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #0096FF;
                border-radius: 3px;
            }
        """)
        
        self.status_label = QLabel("正在啟動系統...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                padding: 5px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 設置位置（相對於啟動畫面）
        self.progress_bar.setGeometry(50, 200, 300, 25)
        self.status_label.setGeometry(50, 230, 300, 30)
        
        # 將組件添加到啟動畫面
        self.progress_bar.setParent(self)
        self.status_label.setParent(self)
    
    def start_loading(self):
        """開始載入過程"""
        self.show()
        self.loading_thread.start()
    
    def update_progress(self, value: int, message: str):
        """更新進度"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        
        # 更新啟動畫面顯示
        self.showMessage(
            message, 
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
            QColor(255, 255, 255)
        )
        
        # 處理事件確保UI更新
        QApplication.processEvents()
    
    def on_loading_finished(self, success: bool, message: str):
        """載入完成處理"""
        self.timeout_timer.stop()
        
        if success:
            self.update_progress(100, "啟動完成！")
            QTimer.singleShot(500, self.close_splash)  # 延遲關閉
        else:
            self.update_progress(0, f"啟動失敗: {message}")
            QTimer.singleShot(3000, self.close_splash)  # 顯示錯誤後關閉
        
        self.loading_finished.emit(success, message)
    
    def on_timeout(self):
        """超時處理"""
        self.loading_worker.stop()
        self.update_progress(0, "啟動超時，請檢查系統狀態")
        self.loading_finished.emit(False, "啟動超時")
        QTimer.singleShot(2000, self.close_splash)
    
    def close_splash(self):
        """關閉啟動畫面"""
        try:
            if self.loading_thread.isRunning():
                self.loading_worker.stop()
                self.loading_thread.quit()
                self.loading_thread.wait(1000)  # 等待1秒
            
            self.close()
        except Exception as e:
            print(f"關閉啟動畫面時發生錯誤: {e}")
            self.close()
    
    def mousePressEvent(self, event):
        """點擊事件處理"""
        # 防止用戶點擊關閉啟動畫面
        pass
    
    def keyPressEvent(self, event):
        """按鍵事件處理"""
        # 允許ESC鍵關閉
        if event.key() == Qt.Key.Key_Escape:
            self.close_splash()
        else:
            super().keyPressEvent(event)


class SimpleSplashScreen(QWidget):
    """簡化版啟動畫面（備用方案）"""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(300, 150)
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d30;
                border: 2px solid #0096FF;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        
        title = QLabel("AImax AI交易系統")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status = QLabel("正在啟動...")
        self.status.setStyleSheet("""
            QLabel {
                color: #ccc;
                font-size: 12px;
                padding: 5px;
            }
        """)
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(self.status)
        self.setLayout(layout)
        
        # 居中顯示
        self.center_on_screen()
    
    def center_on_screen(self):
        """將視窗居中顯示"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def update_status(self, message: str):
        """更新狀態訊息"""
        self.status.setText(message)
        QApplication.processEvents()


if __name__ == "__main__":
    # 測試啟動畫面
    app = QApplication(sys.argv)
    
    splash = SplashScreen()
    splash.start_loading()
    
    def on_finished(success, message):
        print(f"載入完成: {success}, {message}")
        app.quit()
    
    splash.loading_finished.connect(on_finished)
    
    sys.exit(app.exec())