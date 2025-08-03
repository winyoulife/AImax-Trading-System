#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 交易主視窗
現代化的AI交易系統GUI界面，包含狀態面板、控制面板、圖表顯示等
"""

import sys
from typing import Dict, Any, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QProgressBar, QFrame, QSplitter,
    QTabWidget, QGroupBox, QTableWidget, QTableWidgetItem,
    QStatusBar, QMenuBar, QToolBar, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPixmap, QIcon, QAction


class TradingMainWindow(QMainWindow):
    """AImax 交易主視窗"""
    
    # 信號定義
    trading_started = pyqtSignal()
    trading_stopped = pyqtSignal()
    strategy_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # 視窗基本設置
        self.setWindowTitle("AImax AI交易系統 v2.0")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 800)
        
        # 狀態變數
        self.is_trading = False
        self.current_strategy = "智能網格"
        self.ai_status = {"AI1": "待機", "AI2": "待機", "AI3": "待機", "AI4": "待機", "AI5": "待機"}
        self.account_balance = 10000.0
        self.start_time = datetime.now()
        
        # 初始化UI
        self.init_ui()
        self.init_menu_bar()
        self.init_tool_bar()
        self.init_status_bar()
        
        # 啟動更新定時器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(1000)  # 每秒更新
        
    def init_ui(self):
        """初始化用戶界面"""
        # 創建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主佈局
        main_layout = QHBoxLayout(central_widget)
        
        # 創建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左側面板 (狀態和控制)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右側面板 (圖表和日誌)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 設置分割比例
        splitter.setSizes([400, 1000])    def cr
eate_left_panel(self) -> QWidget:
        """創建左側控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # AI狀態面板
        ai_group = self.create_ai_status_panel()
        layout.addWidget(ai_group)
        
        # 交易狀態面板
        trading_group = self.create_trading_status_panel()
        layout.addWidget(trading_group)
        
        # 系統資訊面板
        system_group = self.create_system_info_panel()
        layout.addWidget(system_group)
        
        # 交易控制面板
        control_group = self.create_control_panel()
        layout.addWidget(control_group)
        
        # 策略選擇面板
        strategy_group = self.create_strategy_panel()
        layout.addWidget(strategy_group)
        
        layout.addStretch()  # 添加彈性空間
        return panel
    
    def create_ai_status_panel(self) -> QGroupBox:
        """創建AI狀態面板"""
        group = QGroupBox("🤖 AI系統狀態")
        group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout = QVBoxLayout(group)
        
        # AI狀態顯示
        self.ai_status_labels = {}
        for ai_name in ["AI1", "AI2", "AI3", "AI4", "AI5"]:
            frame = QFrame()
            frame.setFrameStyle(QFrame.Shape.Box)
            frame_layout = QHBoxLayout(frame)
            
            name_label = QLabel(f"{ai_name}:")
            name_label.setMinimumWidth(40)
            
            status_label = QLabel("待機")
            status_label.setStyleSheet("color: orange; font-weight: bold;")
            
            frame_layout.addWidget(name_label)
            frame_layout.addWidget(status_label)
            frame_layout.addStretch()
            
            self.ai_status_labels[ai_name] = status_label
            layout.addWidget(frame)
        
        return group
    
    def create_trading_status_panel(self) -> QGroupBox:
        """創建交易狀態面板"""
        group = QGroupBox("📊 交易狀態")
        group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout = QGridLayout(group)
        
        # 帳戶餘額
        layout.addWidget(QLabel("帳戶餘額:"), 0, 0)
        self.balance_label = QLabel(f"${self.account_balance:,.2f}")
        self.balance_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.balance_label, 0, 1)
        
        # 今日盈虧
        layout.addWidget(QLabel("今日盈虧:"), 1, 0)
        self.pnl_label = QLabel("$0.00")
        self.pnl_label.setStyleSheet("color: gray; font-weight: bold;")
        layout.addWidget(self.pnl_label, 1, 1)
        
        # 持倉數量
        layout.addWidget(QLabel("持倉數量:"), 2, 0)
        self.positions_label = QLabel("0")
        layout.addWidget(self.positions_label, 2, 1)
        
        # 交易狀態
        layout.addWidget(QLabel("交易狀態:"), 3, 0)
        self.trading_status_label = QLabel("停止")
        self.trading_status_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.trading_status_label, 3, 1)
        
        return group    def c
reate_system_info_panel(self) -> QGroupBox:
        """創建系統資訊面板"""
        group = QGroupBox("⚙️ 系統資訊")
        group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout = QGridLayout(group)
        
        # CPU使用率
        layout.addWidget(QLabel("CPU使用率:"), 0, 0)
        self.cpu_label = QLabel("0%")
        layout.addWidget(self.cpu_label, 0, 1)
        
        # 記憶體使用
        layout.addWidget(QLabel("記憶體:"), 1, 0)
        self.memory_label = QLabel("0MB")
        layout.addWidget(self.memory_label, 1, 1)
        
        # 網路狀態
        layout.addWidget(QLabel("網路狀態:"), 2, 0)
        self.network_label = QLabel("正常")
        self.network_label.setStyleSheet("color: green;")
        layout.addWidget(self.network_label, 2, 1)
        
        # 運行時間
        layout.addWidget(QLabel("運行時間:"), 3, 0)
        self.uptime_label = QLabel("00:00:00")
        layout.addWidget(self.uptime_label, 3, 1)
        
        return group
    
    def create_control_panel(self) -> QGroupBox:
        """創建交易控制面板"""
        group = QGroupBox("🎮 交易控制")
        group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout = QVBoxLayout(group)
        
        # 開始交易按鈕
        self.start_button = QPushButton("🚀 開始交易")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.start_button.clicked.connect(self.start_trading)
        layout.addWidget(self.start_button)
        
        # 停止交易按鈕
        self.stop_button = QPushButton("⏹️ 停止交易")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c1170a;
            }
        """)
        self.stop_button.clicked.connect(self.stop_trading)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)
        
        return group    def
 create_strategy_panel(self) -> QGroupBox:
        """創建策略選擇面板"""
        group = QGroupBox("📈 策略選擇")
        group.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        layout = QVBoxLayout(group)
        
        # 策略按鈕
        strategies = [
            ("🔄 智能網格", "智能網格"),
            ("📊 DCA定投", "DCA定投"),
            ("⚡ 套利交易", "套利交易"),
            ("🎯 趨勢跟蹤", "趨勢跟蹤"),
            ("🛡️ 風險對沖", "風險對沖")
        ]
        
        self.strategy_buttons = []
        for display_name, strategy_name in strategies:
            button = QPushButton(display_name)
            button.setCheckable(True)
            button.clicked.connect(lambda checked, name=strategy_name: self.select_strategy(name))
            
            if strategy_name == self.current_strategy:
                button.setChecked(True)
                button.setStyleSheet("background-color: #2196F3; color: white;")
            
            self.strategy_buttons.append((button, strategy_name))
            layout.addWidget(button)
        
        return group
    
    def create_right_panel(self) -> QWidget:
        """創建右側面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 創建標籤頁
        tab_widget = QTabWidget()
        
        # 圖表標籤頁
        chart_tab = self.create_chart_tab()
        tab_widget.addTab(chart_tab, "📈 價格圖表")
        
        # 交易記錄標籤頁
        trades_tab = self.create_trades_tab()
        tab_widget.addTab(trades_tab, "📋 交易記錄")
        
        # 系統日誌標籤頁
        log_tab = self.create_log_tab()
        tab_widget.addTab(log_tab, "📝 系統日誌")
        
        layout.addWidget(tab_widget)
        return panel
    
    def create_chart_tab(self) -> QWidget:
        """創建圖表標籤頁"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 圖表佔位符
        chart_placeholder = QLabel("📈 價格圖表\n\n(圖表功能開發中...)")
        chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_placeholder.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                font-size: 18px;
                color: #666;
                min-height: 400px;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(chart_placeholder)
        
        return widget    d
ef create_trades_tab(self) -> QWidget:
        """創建交易記錄標籤頁"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 交易記錄表格
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(6)
        self.trades_table.setHorizontalHeaderLabels([
            "時間", "交易對", "類型", "數量", "價格", "狀態"
        ])
        
        # 添加示例數據
        self.add_sample_trades()
        
        layout.addWidget(self.trades_table)
        return widget
    
    def create_log_tab(self) -> QWidget:
        """創建日誌標籤頁"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 日誌文本區域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        
        # 添加初始日誌
        self.add_log("系統啟動", "AImax AI交易系統已成功啟動")
        self.add_log("依賴檢查", "所有依賴檢查通過")
        self.add_log("AI系統", "5AI協作系統已就緒")
        
        layout.addWidget(self.log_text)
        return widget
    
    def init_menu_bar(self):
        """初始化菜單欄"""
        menubar = self.menuBar()
        
        # 文件菜單
        file_menu = menubar.addMenu("文件")
        
        # 導出設置
        export_action = QAction("導出設置", self)
        export_action.triggered.connect(self.export_settings)
        file_menu.addAction(export_action)
        
        # 導入設置
        import_action = QAction("導入設置", self)
        import_action.triggered.connect(self.import_settings)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜單
        tools_menu = menubar.addMenu("工具")
        
        # 系統診斷
        diagnostic_action = QAction("系統診斷", self)
        diagnostic_action.triggered.connect(self.show_diagnostic)
        tools_menu.addAction(diagnostic_action)
        
        # 性能監控
        performance_action = QAction("性能監控", self)
        performance_action.triggered.connect(self.show_performance)
        tools_menu.addAction(performance_action)
        
        # 幫助菜單
        help_menu = menubar.addMenu("幫助")
        
        # 關於
        about_action = QAction("關於", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)