#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主視窗 - AImax AI交易系統的主要用戶界面
提供現代化的GUI界面，整合狀態面板、控制面板和日誌面板
"""

import sys
from typing import Optional, Dict, Any
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QMenuBar, QStatusBar, QToolBar,
    QLabel, QPushButton, QTextEdit, QFrame,
    QGridLayout, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QAction, QIcon, QFont, QPalette, QColor

from .ai_connector import AIConnector
from .status_sync_manager import StatusSyncManager
from .error_recovery_system import ErrorRecovery, ErrorType
from .diagnostic_system import DiagnosticSystem, DiagnosticDialog


class StatusPanel(QFrame):
    """狀態面板 - 顯示AI和交易狀態"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border: 1px solid #555;
                border-radius: 8px;
                margin: 5px;
            }
            QLabel {
                color: white;
                font-size: 12px;
                padding: 5px;
            }
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        self.setup_ui()
        
        # 狀態更新定時器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # 每秒更新
    
    def setup_ui(self):
        """設置UI組件"""
        layout = QVBoxLayout()
        
        # AI狀態組
        ai_group = QGroupBox("AI系統狀態")
        ai_layout = QGridLayout()
        
        self.ai_status_label = QLabel("未連接")
        self.ai_count_label = QLabel("0/5")
        self.ai_decision_label = QLabel("等待中...")
        self.ai_confidence_label = QLabel("0%")
        
        ai_layout.addWidget(QLabel("連接狀態:"), 0, 0)
        ai_layout.addWidget(self.ai_status_label, 0, 1)
        ai_layout.addWidget(QLabel("活躍AI:"), 1, 0)
        ai_layout.addWidget(self.ai_count_label, 1, 1)
        ai_layout.addWidget(QLabel("最新決策:"), 2, 0)
        ai_layout.addWidget(self.ai_decision_label, 2, 1)
        ai_layout.addWidget(QLabel("信心度:"), 3, 0)
        ai_layout.addWidget(self.ai_confidence_label, 3, 1)
        
        ai_group.setLayout(ai_layout)
        
        # 交易狀態組
        trading_group = QGroupBox("交易狀態")
        trading_layout = QGridLayout()
        
        self.trading_status_label = QLabel("停止")
        self.balance_label = QLabel("$0.00")
        self.profit_loss_label = QLabel("$0.00")
        self.active_orders_label = QLabel("0")
        
        trading_layout.addWidget(QLabel("交易狀態:"), 0, 0)
        trading_layout.addWidget(self.trading_status_label, 0, 1)
        trading_layout.addWidget(QLabel("帳戶餘額:"), 1, 0)
        trading_layout.addWidget(self.balance_label, 1, 1)
        trading_layout.addWidget(QLabel("損益:"), 2, 0)
        trading_layout.addWidget(self.profit_loss_label, 2, 1)
        trading_layout.addWidget(QLabel("活躍訂單:"), 3, 0)
        trading_layout.addWidget(self.active_orders_label, 3, 1)
        
        trading_group.setLayout(trading_layout)
        
        # 系統資訊組
        system_group = QGroupBox("系統資訊")
        system_layout = QGridLayout()
        
        self.uptime_label = QLabel("00:00:00")
        self.last_update_label = QLabel("從未")
        self.memory_usage_label = QLabel("0 MB")
        
        system_layout.addWidget(QLabel("運行時間:"), 0, 0)
        system_layout.addWidget(self.uptime_label, 0, 1)
        system_layout.addWidget(QLabel("最後更新:"), 1, 0)
        system_layout.addWidget(self.last_update_label, 1, 1)
        system_layout.addWidget(QLabel("記憶體使用:"), 2, 0)
        system_layout.addWidget(self.memory_usage_label, 2, 1)
        
        system_group.setLayout(system_layout)
        
        # 添加到主佈局
        layout.addWidget(ai_group)
        layout.addWidget(trading_group)
        layout.addWidget(system_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # 記錄啟動時間
        self.start_time = datetime.now()
    
    def update_status(self):
        """更新狀態顯示"""
        try:
            # 更新運行時間
            uptime = datetime.now() - self.start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.uptime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # 更新最後更新時間
            self.last_update_label.setText(datetime.now().strftime("%H:%M:%S"))
            
            # 更新記憶體使用（簡化版）
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_usage_label.setText(f"{memory_mb:.1f} MB")
            
        except Exception as e:
            # 如果psutil不可用，顯示基本資訊
            self.memory_usage_label.setText("N/A")
    
    def update_ai_status(self, status_data: Dict[str, Any]):
        """更新AI狀態"""
        try:
            self.ai_status_label.setText(status_data.get('status', '未知'))
            self.ai_count_label.setText(f"{status_data.get('active_count', 0)}/5")
            self.ai_decision_label.setText(status_data.get('last_decision', '等待中...'))
            self.ai_confidence_label.setText(f"{status_data.get('confidence', 0):.1f}%")
            
            # 根據狀態設置顏色
            status = status_data.get('status', '')
            if status == '已連接':
                self.ai_status_label.setStyleSheet("color: #4CAF50;")  # 綠色
            elif status == '連接中':
                self.ai_status_label.setStyleSheet("color: #FF9800;")  # 橙色
            else:
                self.ai_status_label.setStyleSheet("color: #F44336;")  # 紅色
                
        except Exception as e:
            print(f"更新AI狀態失敗: {e}")
    
    def update_trading_status(self, trading_data: Dict[str, Any]):
        """更新交易狀態"""
        try:
            self.trading_status_label.setText(trading_data.get('status', '停止'))
            self.balance_label.setText(f"${trading_data.get('balance', 0):.2f}")
            
            profit_loss = trading_data.get('profit_loss', 0)
            self.profit_loss_label.setText(f"${profit_loss:.2f}")
            
            # 根據損益設置顏色
            if profit_loss > 0:
                self.profit_loss_label.setStyleSheet("color: #4CAF50;")  # 綠色
            elif profit_loss < 0:
                self.profit_loss_label.setStyleSheet("color: #F44336;")  # 紅色
            else:
                self.profit_loss_label.setStyleSheet("color: white;")
            
            self.active_orders_label.setText(str(trading_data.get('active_orders', 0)))
            
            # 根據交易狀態設置顏色
            status = trading_data.get('status', '')
            if status == '運行中':
                self.trading_status_label.setStyleSheet("color: #4CAF50;")  # 綠色
            elif status == '暫停':
                self.trading_status_label.setStyleSheet("color: #FF9800;")  # 橙色
            else:
                self.trading_status_label.setStyleSheet("color: #F44336;")  # 紅色
                
        except Exception as e:
            print(f"更新交易狀態失敗: {e}")


class ControlPanel(QFrame):
    """控制面板 - 提供交易控制功能"""
    
    start_trading = pyqtSignal()
    stop_trading = pyqtSignal()
    strategy_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border: 1px solid #555;
                border-radius: 8px;
                margin: 5px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        self.setup_ui()
        self.trading_active = False
    
    def setup_ui(self):
        """設置UI組件"""
        layout = QVBoxLayout()
        
        # 交易控制組
        control_group = QGroupBox("交易控制")
        control_layout = QVBoxLayout()
        
        # 啟動/停止按鈕
        self.start_stop_button = QPushButton("啟動交易")
        self.start_stop_button.clicked.connect(self.toggle_trading)
        
        # 緊急停止按鈕
        self.emergency_stop_button = QPushButton("緊急停止")
        self.emergency_stop_button.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        self.emergency_stop_button.clicked.connect(self.emergency_stop)
        
        control_layout.addWidget(self.start_stop_button)
        control_layout.addWidget(self.emergency_stop_button)
        control_group.setLayout(control_layout)
        
        # 策略選擇組
        strategy_group = QGroupBox("策略選擇")
        strategy_layout = QVBoxLayout()
        
        self.dca_button = QPushButton("DCA策略")
        self.grid_button = QPushButton("網格策略")
        self.arbitrage_button = QPushButton("套利策略")
        self.auto_button = QPushButton("AI自動選擇")
        
        # 設置策略按鈕為切換模式
        for button in [self.dca_button, self.grid_button, self.arbitrage_button, self.auto_button]:
            button.setCheckable(True)
            button.clicked.connect(self.on_strategy_selected)
        
        # 預設選擇AI自動選擇
        self.auto_button.setChecked(True)
        self.current_strategy = "auto"
        
        strategy_layout.addWidget(self.dca_button)
        strategy_layout.addWidget(self.grid_button)
        strategy_layout.addWidget(self.arbitrage_button)
        strategy_layout.addWidget(self.auto_button)
        strategy_group.setLayout(strategy_layout)
        
        # 快速操作組
        quick_group = QGroupBox("快速操作")
        quick_layout = QVBoxLayout()
        
        self.refresh_button = QPushButton("刷新狀態")
        self.settings_button = QPushButton("系統設置")
        self.logs_button = QPushButton("查看日誌")
        
        self.refresh_button.clicked.connect(self.refresh_status)
        self.settings_button.clicked.connect(self.open_settings)
        self.logs_button.clicked.connect(self.show_logs)
        
        quick_layout.addWidget(self.refresh_button)
        quick_layout.addWidget(self.settings_button)
        quick_layout.addWidget(self.logs_button)
        quick_group.setLayout(quick_layout)
        
        # 添加到主佈局
        layout.addWidget(control_group)
        layout.addWidget(strategy_group)
        layout.addWidget(quick_group)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def toggle_trading(self):
        """切換交易狀態"""
        if self.trading_active:
            self.stop_trading.emit()
            self.trading_active = False
            self.start_stop_button.setText("啟動交易")
            self.start_stop_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        else:
            self.start_trading.emit()
            self.trading_active = True
            self.start_stop_button.setText("停止交易")
            self.start_stop_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
    
    def emergency_stop(self):
        """緊急停止"""
        if self.trading_active:
            self.stop_trading.emit()
            self.trading_active = False
            self.start_stop_button.setText("啟動交易")
            self.start_stop_button.setStyleSheet("")
            
            # 顯示確認訊息
            QMessageBox.information(self, "緊急停止", "所有交易已緊急停止！")
    
    def on_strategy_selected(self):
        """策略選擇處理"""
        sender = self.sender()
        
        # 取消其他按鈕的選中狀態
        for button in [self.dca_button, self.grid_button, self.arbitrage_button, self.auto_button]:
            if button != sender:
                button.setChecked(False)
        
        # 確保至少有一個被選中
        if not sender.isChecked():
            sender.setChecked(True)
            return
        
        # 確定當前策略
        if sender == self.dca_button:
            self.current_strategy = "dca"
        elif sender == self.grid_button:
            self.current_strategy = "grid"
        elif sender == self.arbitrage_button:
            self.current_strategy = "arbitrage"
        else:
            self.current_strategy = "auto"
        
        self.strategy_changed.emit(self.current_strategy)
    
    def refresh_status(self):
        """刷新狀態"""
        # 這裡可以觸發狀態更新
        print("刷新系統狀態...")
    
    def open_settings(self):
        """打開設置"""
        QMessageBox.information(self, "設置", "設置功能將在後續版本中實現")
    
    def show_logs(self):
        """顯示日誌"""
        # 這裡可以切換到日誌面板或打開日誌視窗
        print("顯示系統日誌...")


class LogPanel(QFrame):
    """日誌面板 - 顯示系統日誌和訊息"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border: 1px solid #555;
                border-radius: 8px;
                margin: 5px;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                padding: 5px;
            }
        """)
        
        self.max_lines = 1000  # 最大日誌行數
        self.setup_ui()
    
    def setup_ui(self):
        """設置UI組件"""
        layout = QVBoxLayout()
        
        # 標題
        title_label = QLabel("系統日誌")
        layout.addWidget(title_label)
        
        # 日誌文本區域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 控制按鈕
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("清除日誌")
        self.save_button = QPushButton("保存日誌")
        
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)
        
        self.save_button.setStyleSheet(self.clear_button.styleSheet())
        
        self.clear_button.clicked.connect(self.clear_logs)
        self.save_button.clicked.connect(self.save_logs)
        
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 添加初始日誌
        self.add_log("系統啟動", "INFO")
    
    def add_log(self, message: str, level: str = "INFO"):
        """添加日誌訊息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 根據日誌級別設置顏色
        color_map = {
            "INFO": "#ffffff",
            "WARNING": "#ffeb3b",
            "ERROR": "#f44336",
            "SUCCESS": "#4caf50",
            "DEBUG": "#9e9e9e"
        }
        
        color = color_map.get(level, "#ffffff")
        
        # 格式化日誌訊息
        formatted_message = f'<span style="color: {color}">[{timestamp}] [{level}] {message}</span>'
        
        # 添加到文本區域
        self.log_text.append(formatted_message)
        
        # 限制日誌行數
        if self.log_text.document().lineCount() > self.max_lines:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.LineUnderCursor)
            cursor.removeSelectedText()
        
        # 自動滾動到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """清除日誌"""
        self.log_text.clear()
        self.add_log("日誌已清除", "INFO")
    
    def save_logs(self):
        """保存日誌"""
        try:
            from PyQt6.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "保存日誌", 
                f"aimax_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    # 移除HTML標籤，只保存純文本
                    plain_text = self.log_text.toPlainText()
                    f.write(plain_text)
                
                self.add_log(f"日誌已保存到: {filename}", "SUCCESS")
                
        except Exception as e:
            self.add_log(f"保存日誌失敗: {str(e)}", "ERROR")


class MainWindow(QMainWindow):
    """主視窗類別"""
    
    def __init__(self, ai_components: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.ai_components = ai_components or {}
        
        # 設置視窗屬性
        self.setWindowTitle("AImax AI交易系統 v2.0")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(800, 600)
        
        # 設置視窗樣式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #252526;
            }
            QMenuBar {
                background-color: #2d2d30;
                color: white;
                border-bottom: 1px solid #555;
            }
            QMenuBar::item {
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #0078d4;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
                border-top: 1px solid #555;
            }
        """)
        
        # 初始化組件
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_status_bar()
        
        # 初始化AI連接器
        self.ai_connector = AIConnector(self.ai_components)
        
        # 初始化狀態同步管理器
        self.status_sync_manager = StatusSyncManager(self.ai_connector)
        
        # 初始化錯誤恢復系統
        self.error_recovery = ErrorRecovery(self.ai_connector, self)
        
        # 初始化診斷系統
        self.diagnostic_system = DiagnosticSystem(self.ai_connector, self.error_recovery)
        
        self.setup_connections()
        
        # 啟動後初始化
        QTimer.singleShot(100, self.post_init)
    
    def setup_ui(self):
        """設置用戶界面"""
        # 創建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 創建主佈局
        main_layout = QHBoxLayout()
        
        # 創建分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側面板（狀態和控制）
        left_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 創建面板
        self.status_panel = StatusPanel()
        self.control_panel = ControlPanel()
        self.log_panel = LogPanel()
        
        # 添加到左側分割器
        left_splitter.addWidget(self.status_panel)
        left_splitter.addWidget(self.control_panel)
        left_splitter.setSizes([300, 200])  # 設置初始大小比例
        
        # 添加到主分割器
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(self.log_panel)
        main_splitter.setSizes([400, 800])  # 設置初始大小比例
        
        # 設置佈局
        main_layout.addWidget(main_splitter)
        central_widget.setLayout(main_layout)
    
    def setup_menu_bar(self):
        """設置菜單欄"""
        menubar = self.menuBar()
        
        # 文件菜單
        file_menu = menubar.addMenu('文件')
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 視圖菜單
        view_menu = menubar.addMenu('視圖')
        
        refresh_action = QAction('刷新', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_all)
        view_menu.addAction(refresh_action)
        
        # 工具菜單
        tools_menu = menubar.addMenu('工具')
        
        settings_action = QAction('設置', self)
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)
        
        diagnostic_action = QAction('系統診斷', self)
        diagnostic_action.triggered.connect(self.open_diagnostic_dialog)
        tools_menu.addAction(diagnostic_action)
        
        # 幫助菜單
        help_menu = menubar.addMenu('幫助')
        
        about_action = QAction('關於', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """設置狀態欄"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("系統已啟動，等待AI連接...")
        
        # 添加永久狀態指示器
        self.connection_status = QLabel("未連接")
        self.connection_status.setStyleSheet("color: #f44336; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.connection_status)
    
    def setup_connections(self):
        """設置信號連接"""
        # 控制面板信號
        self.control_panel.start_trading.connect(self.start_trading)
        self.control_panel.stop_trading.connect(self.stop_trading)
        self.control_panel.strategy_changed.connect(self.change_strategy)
        
        # AI連接器信號
        self.ai_connector.status_updated.connect(self.on_ai_status_updated)
        self.ai_connector.trading_status_updated.connect(self.on_trading_status_updated)
        self.ai_connector.log_message.connect(self.log_panel.add_log)
        
        # 狀態同步管理器信號
        self.status_sync_manager.ai_status_synced.connect(self.status_panel.update_ai_status)
        self.status_sync_manager.trading_status_synced.connect(self.status_panel.update_trading_status)
        self.status_sync_manager.balance_updated.connect(self.on_balance_updated)
        self.status_sync_manager.system_metrics_updated.connect(self.on_system_metrics_updated)
        self.status_sync_manager.sync_error.connect(self.on_sync_error)
        
        # 錯誤恢復系統信號
        self.error_recovery.error_detected.connect(self.on_error_detected)
        self.error_recovery.recovery_started.connect(self.on_recovery_started)
        self.error_recovery.recovery_completed.connect(self.on_recovery_completed)
        self.error_recovery.fallback_mode_activated.connect(self.on_fallback_mode_activated)
        
        # 診斷系統信號
        self.diagnostic_system.diagnostic_collected.connect(self.on_diagnostic_collected)
        self.diagnostic_system.report_generated.connect(self.on_report_generated)
    
    def post_init(self):
        """啟動後初始化"""
        self.log_panel.add_log("主視窗初始化完成", "SUCCESS")
        
        # 嘗試連接AI系統
        if self.ai_components:
            self.log_panel.add_log("開始連接AI系統...", "INFO")
            self.ai_connector.connect_to_ai_system()
        else:
            self.log_panel.add_log("AI組件未載入，運行在演示模式", "WARNING")
        
        # 啟動狀態同步
        self.status_sync_manager.start_sync()
        self.log_panel.add_log("狀態同步管理器已啟動", "SUCCESS")
        
        # 啟動診斷系統
        self.diagnostic_system.start_auto_diagnostics(10)  # 每10分鐘自動診斷
        self.log_panel.add_log("診斷系統已啟動", "SUCCESS")
    
    def start_trading(self):
        """啟動交易"""
        self.log_panel.add_log("用戶請求啟動交易", "INFO")
        if self.ai_connector.start_trading():
            self.status_bar.showMessage("交易已啟動")
            self.log_panel.add_log("交易啟動成功", "SUCCESS")
        else:
            self.log_panel.add_log("交易啟動失敗", "ERROR")
    
    def stop_trading(self):
        """停止交易"""
        self.log_panel.add_log("用戶請求停止交易", "INFO")
        if self.ai_connector.stop_trading():
            self.status_bar.showMessage("交易已停止")
            self.log_panel.add_log("交易停止成功", "SUCCESS")
        else:
            self.log_panel.add_log("交易停止失敗", "ERROR")
    
    def change_strategy(self, strategy: str):
        """更改策略"""
        self.log_panel.add_log(f"用戶選擇策略: {strategy}", "INFO")
        self.ai_connector.set_strategy(strategy)
    
    def on_ai_status_updated(self, status_data: Dict[str, Any]):
        """AI狀態更新處理"""
        self.status_panel.update_ai_status(status_data)
        
        # 更新連接狀態
        if status_data.get('connected', False):
            self.connection_status.setText("已連接")
            self.connection_status.setStyleSheet("color: #4caf50; font-weight: bold;")
            self.status_bar.showMessage("AI系統已連接")
        else:
            self.connection_status.setText("未連接")
            self.connection_status.setStyleSheet("color: #f44336; font-weight: bold;")
    
    def on_trading_status_updated(self, trading_data: Dict[str, Any]):
        """交易狀態更新處理"""
        self.status_panel.update_trading_status(trading_data)
    
    def on_balance_updated(self, balance: float):
        """餘額更新處理"""
        self.log_panel.add_log(f"餘額變化: ${balance:.2f}", "INFO")
        self.status_bar.showMessage(f"餘額更新: ${balance:.2f}")
    
    def on_system_metrics_updated(self, metrics: Dict[str, Any]):
        """系統指標更新處理"""
        try:
            # 更新狀態欄顯示系統資訊
            cpu_usage = metrics.get('cpu_usage', 0)
            memory_usage = metrics.get('memory_usage', 0)
            
            if cpu_usage > 80 or memory_usage > 80:
                self.log_panel.add_log(f"系統資源使用率較高 - CPU: {cpu_usage:.1f}%, 記憶體: {memory_usage:.1f}%", "WARNING")
                
        except Exception as e:
            self.log_panel.add_log(f"處理系統指標更新失敗: {str(e)}", "ERROR")
    
    def on_sync_error(self, error: str):
        """同步錯誤處理"""
        self.log_panel.add_log(f"同步錯誤: {error}", "ERROR")
        
        # 添加到診斷系統
        self.diagnostic_system.classify_and_add_error(
            f"狀態同步錯誤: {error}",
            "status_sync_manager"
        )
        
        # 觸發錯誤恢復
        self.error_recovery.handle_error(
            ErrorType.SYSTEM_ERROR,
            f"狀態同步錯誤: {error}",
            "status_sync_manager",
            "medium"
        )
    
    def on_error_detected(self, error_event):
        """錯誤檢測處理"""
        self.log_panel.add_log(
            f"檢測到錯誤: [{error_event.error_type.value}] {error_event.message}",
            "ERROR"
        )
    
    def on_recovery_started(self, error_type: str, action: str):
        """恢復開始處理"""
        self.log_panel.add_log(f"開始錯誤恢復: {error_type} -> {action}", "INFO")
        self.status_bar.showMessage(f"正在恢復: {action}")
    
    def on_recovery_completed(self, success: bool, message: str):
        """恢復完成處理"""
        level = "SUCCESS" if success else "ERROR"
        self.log_panel.add_log(f"恢復完成: {message}", level)
        
        if success:
            self.status_bar.showMessage("系統恢復成功")
        else:
            self.status_bar.showMessage("系統恢復失敗")
    
    def on_fallback_mode_activated(self, reason: str):
        """降級模式激活處理"""
        self.log_panel.add_log(f"系統進入降級模式: {reason}", "WARNING")
        self.status_bar.showMessage("系統運行在降級模式")
        
        # 更新連接狀態顯示
        self.connection_status.setText("降級模式")
        self.connection_status.setStyleSheet("color: #ff9800; font-weight: bold;")
    
    def on_diagnostic_collected(self, diagnostic_info):
        """診斷資訊收集處理"""
        # 根據診斷級別決定是否顯示在日誌中
        if diagnostic_info.level in ['WARNING', 'ERROR', 'CRITICAL']:
            level_map = {
                'WARNING': 'WARNING',
                'ERROR': 'ERROR', 
                'CRITICAL': 'ERROR'
            }
            self.log_panel.add_log(
                f"[診斷] {diagnostic_info.message}",
                level_map[diagnostic_info.level]
            )
    
    def on_report_generated(self, report_path: str):
        """診斷報告生成處理"""
        self.log_panel.add_log(f"診斷報告已生成: {report_path}", "SUCCESS")
        self.status_bar.showMessage(f"診斷報告已保存: {report_path}")
    
    def open_diagnostic_dialog(self):
        """打開診斷對話框"""
        try:
            dialog = DiagnosticDialog(self.diagnostic_system, self)
            dialog.exec()
        except Exception as e:
            self.log_panel.add_log(f"打開診斷對話框失敗: {str(e)}", "ERROR")
    
    def refresh_all(self):
        """刷新所有狀態"""
        self.log_panel.add_log("刷新所有狀態", "INFO")
        self.ai_connector.refresh_status()
    
    def open_settings(self):
        """打開設置"""
        QMessageBox.information(self, "設置", "設置功能將在後續版本中實現")
    
    def show_about(self):
        """顯示關於對話框"""
        QMessageBox.about(self, "關於 AImax", 
                         "AImax AI交易系統 v2.0\n\n"
                         "一個基於人工智能的自動交易系統\n"
                         "支援多種交易策略和風險管理\n\n"
                         "© 2025 AImax Team")
    
    def closeEvent(self, event):
        """視窗關閉事件"""
        self.log_panel.add_log("用戶請求關閉系統", "INFO")
        
        # 如果交易正在運行，詢問用戶
        if self.control_panel.trading_active:
            reply = QMessageBox.question(
                self, '確認關閉', 
                '交易正在運行中，確定要關閉系統嗎？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            else:
                # 停止交易
                self.stop_trading()
        
        # 清理資源
        self.diagnostic_system.cleanup()
        self.error_recovery.cleanup()
        self.status_sync_manager.cleanup()
        self.ai_connector.cleanup()
        self.log_panel.add_log("系統正在關閉...", "INFO")
        
        event.accept()


if __name__ == "__main__":
    # 測試主視窗
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 創建測試用的AI組件
    test_components = {
        'ai_manager': None,
        'trade_executor': None,
        'risk_manager': None,
        'system_integrator': None
    }
    
    window = MainWindow(test_components)
    window.show()
    
    sys.exit(app.exec())