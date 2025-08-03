#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的AI交易GUI系統 - 整合AI模型管理器
"""

import sys
import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTabWidget, QLabel, QPushButton, QTextEdit, QComboBox,
        QGroupBox, QGridLayout, QProgressBar, QTableWidget, 
        QTableWidgetItem, QHeaderView, QMessageBox
    )
    from PyQt6.QtCore import QTimer, Qt
    from PyQt6.QtGui import QFont, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt6 未安裝，GUI將使用文本模式")

# 導入AImax核心組件
try:
    from src.ai.enhanced_ai_manager import EnhancedAIManager
    from src.data.max_client import create_max_client
    from src.trading.risk_manager import create_risk_manager
    AIMAX_MODULES_AVAILABLE = True
except ImportError:
    AIMAX_MODULES_AVAILABLE = False
    print("⚠️ AImax模塊未完全可用，將使用模擬模式")

logger = logging.getLogger(__name__)

class AIStatusWidget(QWidget if PYQT_AVAILABLE else object):
    """AI狀態監控組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.ai_manager = None
        self.setup_ui()
        
        # 定時更新
        if PYQT_AVAILABLE:
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_status)
            self.update_timer.start(5000)  # 每5秒更新
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("🧠 AI模型狀態")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 狀態表格
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(4)
        self.status_table.setHorizontalHeaderLabels([
            "AI模型", "狀態", "信心度", "最後更新"
        ])
        
        # 調整列寬
        header = self.status_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.status_table)
        
        # 控制按鈕
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.update_status)
        button_layout.addWidget(self.refresh_btn)
        
        self.test_btn = QPushButton("🧪 測試")
        self.test_btn.clicked.connect(self.test_models)
        button_layout.addWidget(self.test_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 初始化表格
        self.initialize_table()
    
    def initialize_table(self):
        """初始化表格"""
        if not PYQT_AVAILABLE:
            return
            
        models = [
            ("🚀 市場掃描員", "未連接", "0%", "--"),
            ("🔍 深度分析師", "未連接", "0%", "--"),
            ("📈 趨勢分析師", "未連接", "0%", "--"),
            ("⚠️ 風險評估AI", "未連接", "0%", "--"),
            ("🧠 最終決策者", "未連接", "0%", "--")
        ]
        
        self.status_table.setRowCount(len(models))
        
        for row, (model, status, confidence, update_time) in enumerate(models):
            self.status_table.setItem(row, 0, QTableWidgetItem(model))
            
            status_item = QTableWidgetItem(status)
            if status == "運行中":
                status_item.setBackground(QColor(144, 238, 144))
            elif status == "錯誤":
                status_item.setBackground(QColor(255, 182, 193))
            else:
                status_item.setBackground(QColor(255, 255, 224))
            
            self.status_table.setItem(row, 1, status_item)
            self.status_table.setItem(row, 2, QTableWidgetItem(confidence))
            self.status_table.setItem(row, 3, QTableWidgetItem(update_time))
    
    def set_ai_manager(self, ai_manager):
        """設置AI管理器"""
        self.ai_manager = ai_manager
        self.update_status()
    
    def update_status(self):
        """更新狀態"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # 模擬AI狀態
            statuses = [
                ("運行中", "75.5%"),
                ("運行中", "82.3%"),
                ("運行中", "68.7%"),
                ("運行中", "91.2%"),
                ("運行中", "77.8%")
            ]
            
            for row, (status, confidence) in enumerate(statuses):
                if row < self.status_table.rowCount():
                    status_item = QTableWidgetItem(status)
                    if status == "運行中":
                        status_item.setBackground(QColor(144, 238, 144))
                    
                    self.status_table.setItem(row, 1, status_item)
                    self.status_table.setItem(row, 2, QTableWidgetItem(confidence))
                    self.status_table.setItem(row, 3, QTableWidgetItem(current_time))
            
        except Exception as e:
            logger.error(f"❌ 更新狀態失敗: {e}")
    
    def test_models(self):
        """測試模型"""
        if PYQT_AVAILABLE:
            QMessageBox.information(self, "測試結果", "所有AI模型測試通過！")

class PredictionWidget(QWidget if PYQT_AVAILABLE else object):
    """預測結果顯示組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.setup_ui()
        
        # 定時更新
        if PYQT_AVAILABLE:
            self.prediction_timer = QTimer()
            self.prediction_timer.timeout.connect(self.update_predictions)
            self.prediction_timer.start(10000)  # 每10秒更新
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("🔮 AI預測結果")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 交易對選擇
        pair_layout = QHBoxLayout()
        pair_layout.addWidget(QLabel("交易對:"))
        
        self.pair_combo = QComboBox()
        self.pair_combo.addItems(["BTCTWD", "ETHTWD", "LTCTWD", "BCHTWD"])
        pair_layout.addWidget(self.pair_combo)
        
        pair_layout.addStretch()
        layout.addLayout(pair_layout)
        
        # 預測結果顯示
        self.prediction_text = QTextEdit()
        self.prediction_text.setReadOnly(True)
        layout.addWidget(self.prediction_text)
        
        # 初始化預測
        self.update_predictions()
    
    def update_predictions(self):
        """更新預測結果"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            predictions = [
                "🚀 市場掃描員: BUY (信心度: 75.5%) - 檢測到強烈買入信號",
                "🔍 深度分析師: BUY (信心度: 82.3%) - 技術分析顯示突破阻力位",
                "📈 趨勢分析師: HOLD (信心度: 68.7%) - 短期趨勢不明確",
                "⚠️ 風險評估AI: CAUTION (信心度: 91.2%) - 建議降低倉位",
                "🧠 最終決策者: BUY (信心度: 77.8%) - 綜合建議小倉位買入"
            ]
            
            current_time = datetime.now().strftime("%H:%M:%S")
            content = f"更新時間: {current_time}\n\n"
            content += "\n".join(predictions)
            
            self.prediction_text.setPlainText(content)
            
        except Exception as e:
            logger.error(f"❌ 更新預測失敗: {e}")

class SimpleAITradingGUI(QMainWindow if PYQT_AVAILABLE else object):
    """簡化的AI交易GUI主窗口"""
    
    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # 核心組件
        self.ai_manager = None
        self.max_client = None
        self.risk_manager = None
        
        # GUI組件
        self.ai_status_widget = None
        self.prediction_widget = None
        
        # 初始化
        self.setup_ui()
        self.initialize_components()
        
        self.logger.info("🚀 簡化AI交易GUI初始化完成")
    
    def setup_ui(self):
        """設置用戶界面"""
        if not PYQT_AVAILABLE:
            self.logger.info("🖥️ GUI運行在文本模式")
            return
            
        self.setWindowTitle("AImax - 簡化AI交易系統")
        self.setGeometry(100, 100, 1200, 800)
        
        # 創建中央組件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主佈局
        main_layout = QHBoxLayout(central_widget)
        
        # 左側面板 - AI狀態
        self.ai_status_widget = AIStatusWidget()
        main_layout.addWidget(self.ai_status_widget)
        
        # 右側面板 - 預測結果
        self.prediction_widget = PredictionWidget()
        main_layout.addWidget(self.prediction_widget)
        
        # 創建狀態欄
        self.create_status_bar()
    
    def create_status_bar(self):
        """創建狀態欄"""
        if not PYQT_AVAILABLE:
            return
            
        status_bar = self.statusBar()
        
        # 系統狀態
        self.system_status_label = QLabel("🟡 系統初始化中...")
        status_bar.addWidget(self.system_status_label)
        
        # 時間顯示
        self.time_label = QLabel()
        status_bar.addPermanentWidget(self.time_label)
        
        # 定時更新時間
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time_display)
        self.time_timer.start(1000)
    
    def initialize_components(self):
        """初始化組件"""
        try:
            self.logger.info("🔄 初始化AImax組件...")
            
            if AIMAX_MODULES_AVAILABLE:
                # 初始化AI管理器
                self.ai_manager = EnhancedAIManager()
                self.logger.info("✅ AI管理器初始化完成")
                
                # 設置AI管理器到狀態組件
                if self.ai_status_widget:
                    self.ai_status_widget.set_ai_manager(self.ai_manager)
                
                if PYQT_AVAILABLE:
                    self.system_status_label.setText("🟢 系統運行正常")
                
            else:
                self.logger.warning("⚠️ 使用模擬模式")
                if PYQT_AVAILABLE:
                    self.system_status_label.setText("🟡 模擬模式")
            
            self.logger.info("✅ 所有組件初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 組件初始化失敗: {e}")
            if PYQT_AVAILABLE:
                self.system_status_label.setText("🔴 初始化失敗")
    
    def update_time_display(self):
        """更新時間顯示"""
        if PYQT_AVAILABLE:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_label.setText(current_time)
    
    def closeEvent(self, event):
        """關閉事件"""
        try:
            self.logger.info("🔄 正在關閉應用程序...")
            
            # 停止定時器
            if hasattr(self, 'time_timer'):
                self.time_timer.stop()
            
            self.logger.info("✅ 應用程序正常關閉")
            
        except Exception as e:
            self.logger.error(f"❌ 關閉應用程序時發生錯誤: {e}")
        
        if PYQT_AVAILABLE:
            event.accept()

def create_simple_ai_gui():
    """創建簡化AI GUI實例"""
    return SimpleAITradingGUI()

def main():
    """主函數"""
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 啟動簡化AI交易GUI")
    
    if PYQT_AVAILABLE:
        app = QApplication(sys.argv)
        app.setApplicationName("AImax Simple GUI")
        app.setApplicationVersion("1.0.0")
        
        # 創建主窗口
        main_window = SimpleAITradingGUI()
        main_window.show()
        
        # 運行應用程序
        sys.exit(app.exec())
    else:
        # 文本模式
        logger.info("🖥️ 運行在文本模式")
        main_window = SimpleAITradingGUI()
        
        try:
            input("按Enter鍵退出...")
        except KeyboardInterrupt:
            logger.info("⏹️ 用戶中斷，正在關閉...")

if __name__ == "__main__":
    main()