#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易對監控界面
提供多個交易對的統一監控和管理界面
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QFrame,
        QGridLayout, QGroupBox, QProgressBar, QComboBox, QCheckBox,
        QScrollArea, QMessageBox, QMenu, QAction, QToolButton, QSpacerItem,
        QSizePolicy, QTextEdit, QSlider, QSpinBox
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QThread
    from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPainter, QBrush
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt5 未安裝，多交易對監控將使用文本模式")

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)

class PairMonitorCard(QFrame if PYQT_AVAILABLE else object):
    """單個交易對監控卡片"""
    
    if PYQT_AVAILABLE:
        pair_selected = pyqtSignal(str)  # 交易對選中信號
        pair_action = pyqtSignal(str, str)  # 交易對操作信號 (pair, action)
    
    def __init__(self, pair: str, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.pair = pair
        self.is_active = False
        self.is_selected = False
        
        # 數據
        self.price_data = {
            'current_price': 0.0,
            'price_change': 0.0,
            'price_change_percent': 0.0,
            'volume_24h': 0.0,
            'high_24h': 0.0,
            'low_24h': 0.0
        }
        
        self.trading_data = {
            'position_count': 0,
            'total_position_size': 0.0,
            'unrealized_pnl': 0.0,
            'realized_pnl': 0.0,
            'ai_confidence': 0.0,
            'risk_score': 0.0,
            'strategy_active': False
        }
        
        if PYQT_AVAILABLE:
            self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        if not PYQT_AVAILABLE:
            return
            
        self.setFrameStyle(QFrame.StyledPanel)
        self.setFixedSize(280, 200)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # 標題行
        title_layout = QHBoxLayout()
        
        # 交易對名稱
        self.pair_label = QLabel(self.pair)
        self.pair_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_layout.addWidget(self.pair_label)
        
        title_layout.addStretch()
        
        # 狀態指示器
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 16))
        self.update_status_color()
        title_layout.addWidget(self.status_indicator)
        
        # 操作按鈕
        self.menu_button = QToolButton()
        self.menu_button.setText("⋮")
        self.menu_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.menu_button.setPopupMode(QToolButton.InstantPopup)
        self.create_context_menu()
        title_layout.addWidget(self.menu_button)
        
        layout.addLayout(title_layout)
        
        # 價格信息
        price_layout = QVBoxLayout()
        
        self.price_label = QLabel("$0.00")
        self.price_label.setFont(QFont("Arial", 16, QFont.Bold))
        price_layout.addWidget(self.price_label)
        
        self.change_label = QLabel("0.00 (0.00%)")
        self.change_label.setFont(QFont("Arial", 10))
        price_layout.addWidget(self.change_label)
        
        layout.addLayout(price_layout)
        
        # 交易信息
        trading_layout = QGridLayout()
        trading_layout.setSpacing(3)
        
        # 倉位數量
        trading_layout.addWidget(QLabel("倉位:"), 0, 0)
        self.position_label = QLabel("0")
        self.position_label.setFont(QFont("Arial", 9, QFont.Bold))
        trading_layout.addWidget(self.position_label, 0, 1)
        
        # 未實現盈虧
        trading_layout.addWidget(QLabel("盈虧:"), 1, 0)
        self.pnl_label = QLabel("$0.00")
        self.pnl_label.setFont(QFont("Arial", 9, QFont.Bold))
        trading_layout.addWidget(self.pnl_label, 1, 1)
        
        # AI信心度
        trading_layout.addWidget(QLabel("AI:"), 0, 2)
        self.ai_label = QLabel("0%")
        self.ai_label.setFont(QFont("Arial", 9, QFont.Bold))
        trading_layout.addWidget(self.ai_label, 0, 3)
        
        # 風險分數
        trading_layout.addWidget(QLabel("風險:"), 1, 2)
        self.risk_label = QLabel("0.0")
        self.risk_label.setFont(QFont("Arial", 9, QFont.Bold))
        trading_layout.addWidget(self.risk_label, 1, 3)
        
        layout.addLayout(trading_layout)
        
        # 進度條 (AI信心度可視化)
        self.confidence_bar = QProgressBar()
        self.confidence_bar.setMaximum(100)
        self.confidence_bar.setTextVisible(False)
        self.confidence_bar.setFixedHeight(6)
        layout.addWidget(self.confidence_bar)
        
        layout.addStretch()
        
    def create_context_menu(self):
        """創建右鍵菜單"""
        if not PYQT_AVAILABLE:
            return
            
        menu = QMenu(self)
        
        # 查看詳情
        view_action = QAction("查看詳情", self)
        view_action.triggered.connect(lambda: self.pair_action.emit(self.pair, "view"))
        menu.addAction(view_action)
        
        # 開始交易
        start_action = QAction("開始交易", self)
        start_action.triggered.connect(lambda: self.pair_action.emit(self.pair, "start"))
        menu.addAction(start_action)
        
        # 停止交易
        stop_action = QAction("停止交易", self)
        stop_action.triggered.connect(lambda: self.pair_action.emit(self.pair, "stop"))
        menu.addAction(stop_action)
        
        menu.addSeparator()
        
        # 平倉所有
        close_action = QAction("平倉所有", self)
        close_action.triggered.connect(lambda: self.pair_action.emit(self.pair, "close_all"))
        menu.addAction(close_action)
        
        # 調整配置
        config_action = QAction("調整配置", self)
        config_action.triggered.connect(lambda: self.pair_action.emit(self.pair, "config"))
        menu.addAction(config_action)
        
        self.menu_button.setMenu(menu)
    
    def update_price_data(self, data: Dict[str, Any]):
        """更新價格數據"""
        self.price_data.update(data)
        
        if not PYQT_AVAILABLE:
            return
        
        # 更新價格顯示
        price = self.price_data['current_price']
        if self.pair.endswith('TWD'):
            self.price_label.setText(f"${price:,.0f}")
        else:
            self.price_label.setText(f"${price:.4f}")
        
        # 更新變化顯示
        change = self.price_data['price_change']
        change_percent = self.price_data['price_change_percent']
        
        if change >= 0:
            self.change_label.setText(f"+{change:.2f} (+{change_percent:.2f}%)")
            self.change_label.setStyleSheet("color: #00C851;")
        else:
            self.change_label.setText(f"{change:.2f} ({change_percent:.2f}%)")
            self.change_label.setStyleSheet("color: #FF4444;")
    
    def update_trading_data(self, data: Dict[str, Any]):
        """更新交易數據"""
        self.trading_data.update(data)
        
        # 更新活躍狀態（在GUI和文本模式下都需要）
        self.is_active = self.trading_data['strategy_active']
        self.update_status_color()
        
        if not PYQT_AVAILABLE:
            return
        
        # 更新倉位數量
        self.position_label.setText(str(self.trading_data['position_count']))
        
        # 更新盈虧
        pnl = self.trading_data['unrealized_pnl']
        if pnl >= 0:
            self.pnl_label.setText(f"+${pnl:,.0f}")
            self.pnl_label.setStyleSheet("color: #00C851;")
        else:
            self.pnl_label.setText(f"-${abs(pnl):,.0f}")
            self.pnl_label.setStyleSheet("color: #FF4444;")
        
        # 更新AI信心度
        confidence = self.trading_data['ai_confidence'] * 100
        self.ai_label.setText(f"{confidence:.0f}%")
        self.confidence_bar.setValue(int(confidence))
        
        # 更新風險分數
        risk = self.trading_data['risk_score']
        self.risk_label.setText(f"{risk:.1f}")
        
        if risk <= 0.3:
            self.risk_label.setStyleSheet("color: #00C851;")
        elif risk <= 0.6:
            self.risk_label.setStyleSheet("color: #FFBB33;")
        else:
            self.risk_label.setStyleSheet("color: #FF4444;")
    
    def update_status_color(self):
        """更新狀態指示器顏色"""
        # 在文本模式下，狀態已經通過 is_active 屬性更新，無需GUI操作
        if not PYQT_AVAILABLE:
            return
            
        if self.is_active:
            self.status_indicator.setStyleSheet("color: #00C851;")  # 綠色
        else:
            self.status_indicator.setStyleSheet("color: #757575;")  # 灰色
    
    def set_selected(self, selected: bool):
        """設置選中狀態"""
        if not PYQT_AVAILABLE:
            return
            
        self.is_selected = selected
        if selected:
            self.setStyleSheet("""
                PairMonitorCard {
                    border: 2px solid #2196F3;
                    background-color: #E3F2FD;
                }
            """)
        else:
            self.setStyleSheet("""
                PairMonitorCard {
                    border: 1px solid #E0E0E0;
                    background-color: white;
                }
                PairMonitorCard:hover {
                    border: 1px solid #2196F3;
                    background-color: #F5F5F5;
                }
            """)
    
    def mousePressEvent(self, event):
        """鼠標點擊事件"""
        if not PYQT_AVAILABLE:
            return
            
        if event.button() == Qt.LeftButton:
            self.pair_selected.emit(self.pair)
        super().mousePressEvent(event)

class MultiPairSummaryWidget(QWidget if PYQT_AVAILABLE else object):
    """多交易對摘要部件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
            self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 總體統計
        stats_group = QGroupBox("總體統計")
        stats_layout = QGridLayout(stats_group)
        
        # 活躍交易對
        stats_layout.addWidget(QLabel("活躍交易對:"), 0, 0)
        self.active_pairs_label = QLabel("0/0")
        self.active_pairs_label.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.active_pairs_label, 0, 1)
        
        # 總倉位數
        stats_layout.addWidget(QLabel("總倉位數:"), 1, 0)
        self.total_positions_label = QLabel("0")
        self.total_positions_label.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.total_positions_label, 1, 1)
        
        # 總投入資金
        stats_layout.addWidget(QLabel("投入資金:"), 0, 2)
        self.total_capital_label = QLabel("$0")
        self.total_capital_label.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.total_capital_label, 0, 3)
        
        # 總盈虧
        stats_layout.addWidget(QLabel("總盈虧:"), 1, 2)
        self.total_pnl_label = QLabel("$0")
        self.total_pnl_label.setFont(QFont("Arial", 12, QFont.Bold))
        stats_layout.addWidget(self.total_pnl_label, 1, 3)
        
        layout.addWidget(stats_group)
        
        # 風險指標
        risk_group = QGroupBox("風險指標")
        risk_layout = QGridLayout(risk_group)
        
        # 整體風險等級
        risk_layout.addWidget(QLabel("風險等級:"), 0, 0)
        self.risk_level_label = QLabel("低")
        self.risk_level_label.setFont(QFont("Arial", 12, QFont.Bold))
        risk_layout.addWidget(self.risk_level_label, 0, 1)
        
        # 資金利用率
        risk_layout.addWidget(QLabel("資金利用率:"), 1, 0)
        self.utilization_label = QLabel("0%")
        self.utilization_label.setFont(QFont("Arial", 12, QFont.Bold))
        risk_layout.addWidget(self.utilization_label, 1, 1)
        
        # VaR
        risk_layout.addWidget(QLabel("日VaR:"), 0, 2)
        self.var_label = QLabel("$0")
        self.var_label.setFont(QFont("Arial", 12, QFont.Bold))
        risk_layout.addWidget(self.var_label, 0, 3)
        
        # 最大回撤
        risk_layout.addWidget(QLabel("最大回撤:"), 1, 2)
        self.drawdown_label = QLabel("0%")
        self.drawdown_label.setFont(QFont("Arial", 12, QFont.Bold))
        risk_layout.addWidget(self.drawdown_label, 1, 3)
        
        layout.addWidget(risk_group)
        
        # AI指標
        ai_group = QGroupBox("AI指標")
        ai_layout = QGridLayout(ai_group)
        
        # 平均信心度
        ai_layout.addWidget(QLabel("平均信心度:"), 0, 0)
        self.avg_confidence_label = QLabel("0%")
        self.avg_confidence_label.setFont(QFont("Arial", 12, QFont.Bold))
        ai_layout.addWidget(self.avg_confidence_label, 0, 1)
        
        # 決策準確率
        ai_layout.addWidget(QLabel("決策準確率:"), 1, 0)
        self.accuracy_label = QLabel("0%")
        self.accuracy_label.setFont(QFont("Arial", 12, QFont.Bold))
        ai_layout.addWidget(self.accuracy_label, 1, 1)
        
        layout.addWidget(ai_group)
        
        layout.addStretch()
    
    def update_summary(self, data: Dict[str, Any]):
        """更新摘要數據"""
        if not PYQT_AVAILABLE:
            return
            
        # 更新統計數據
        self.active_pairs_label.setText(f"{data.get('active_pairs', 0)}/{data.get('total_pairs', 0)}")
        self.total_positions_label.setText(str(data.get('total_positions', 0)))
        self.total_capital_label.setText(f"${data.get('total_capital', 0):,.0f}")
        
        # 更新盈虧
        total_pnl = data.get('total_pnl', 0)
        if total_pnl >= 0:
            self.total_pnl_label.setText(f"+${total_pnl:,.0f}")
            self.total_pnl_label.setStyleSheet("color: #00C851;")
        else:
            self.total_pnl_label.setText(f"-${abs(total_pnl):,.0f}")
            self.total_pnl_label.setStyleSheet("color: #FF4444;")
        
        # 更新風險指標
        risk_level = data.get('risk_level', 'low')
        self.risk_level_label.setText(risk_level.upper())
        
        if risk_level == 'low':
            self.risk_level_label.setStyleSheet("color: #00C851;")
        elif risk_level == 'medium':
            self.risk_level_label.setStyleSheet("color: #FFBB33;")
        else:
            self.risk_level_label.setStyleSheet("color: #FF4444;")
        
        self.utilization_label.setText(f"{data.get('utilization_rate', 0):.1%}")
        self.var_label.setText(f"${data.get('daily_var', 0):,.0f}")
        self.drawdown_label.setText(f"{data.get('max_drawdown', 0):.1%}")
        
        # 更新AI指標
        self.avg_confidence_label.setText(f"{data.get('avg_confidence', 0):.1%}")
        self.accuracy_label.setText(f"{data.get('accuracy_rate', 0):.1%}")

class MultiPairMonitor(QWidget if PYQT_AVAILABLE else object):
    """多交易對監控主界面"""
    
    if PYQT_AVAILABLE:
        pair_selected = pyqtSignal(str)  # 交易對選中信號
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        
        # 數據
        self.monitored_pairs = ["BTCTWD", "ETHTWD", "USDTTWD", "LTCTWD", "BCHTWD"]
        self.pair_cards = {}  # {pair: PairMonitorCard}
        self.selected_pair = None
        
        # 定時器
        if PYQT_AVAILABLE:
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_data)
        
        if PYQT_AVAILABLE:
            self.init_ui()
        
        logger.info("📊 多交易對監控界面初始化完成")
    
    def init_ui(self):
        """初始化界面"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 標題和控制欄
        header_layout = QHBoxLayout()
        
        title_label = QLabel("多交易對監控")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 刷新按鈕
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.refresh_data)
        header_layout.addWidget(self.refresh_button)
        
        # 自動刷新開關
        self.auto_refresh_checkbox = QCheckBox("自動刷新")
        self.auto_refresh_checkbox.setChecked(True)
        self.auto_refresh_checkbox.toggled.connect(self.toggle_auto_refresh)
        header_layout.addWidget(self.auto_refresh_checkbox)
        
        # 刷新間隔
        header_layout.addWidget(QLabel("間隔:"))
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(1, 60)
        self.refresh_interval_spin.setValue(5)
        self.refresh_interval_spin.setSuffix("秒")
        self.refresh_interval_spin.valueChanged.connect(self.update_refresh_interval)
        header_layout.addWidget(self.refresh_interval_spin)
        
        layout.addLayout(header_layout)
        
        # 摘要部件
        self.summary_widget = MultiPairSummaryWidget()
        layout.addWidget(self.summary_widget)
        
        # 分隔線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 交易對卡片區域
        cards_label = QLabel("交易對監控")
        cards_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(cards_label)
        
        # 滾動區域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 卡片容器
        cards_widget = QWidget()
        self.cards_layout = QGridLayout(cards_widget)
        self.cards_layout.setSpacing(10)
        
        # 創建交易對卡片
        self.create_pair_cards()
        
        scroll_area.setWidget(cards_widget)
        layout.addWidget(scroll_area)
        
        # 啟動自動刷新
        self.toggle_auto_refresh(True)
    
    def create_pair_cards(self):
        """創建交易對卡片"""
        if not PYQT_AVAILABLE:
            return
            
        row, col = 0, 0
        max_cols = 4  # 每行最多4個卡片
        
        for pair in self.monitored_pairs:
            card = PairMonitorCard(pair)
            card.pair_selected.connect(self.on_pair_selected)
            card.pair_action.connect(self.on_pair_action)
            
            self.pair_cards[pair] = card
            self.cards_layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # 添加彈性空間
        self.cards_layout.setRowStretch(row + 1, 1)
        self.cards_layout.setColumnStretch(max_cols, 1)
    
    def on_pair_selected(self, pair: str):
        """交易對選中事件"""
        # 更新選中狀態
        if PYQT_AVAILABLE:
            for p, card in self.pair_cards.items():
                card.set_selected(p == pair)
            self.pair_selected.emit(pair)
        
        self.selected_pair = pair
        logger.info(f"📊 選中交易對: {pair}")
    
    def on_pair_action(self, pair: str, action: str):
        """交易對操作事件"""
        logger.info(f"📊 交易對操作: {pair} - {action}")
        
        if action == "view":
            self.view_pair_details(pair)
        elif action == "start":
            self.start_pair_trading(pair)
        elif action == "stop":
            self.stop_pair_trading(pair)
        elif action == "close_all":
            self.close_all_positions(pair)
        elif action == "config":
            self.configure_pair(pair)
    
    def view_pair_details(self, pair: str):
        """查看交易對詳情"""
        if PYQT_AVAILABLE:
            QMessageBox.information(self, "交易對詳情", f"查看 {pair} 的詳細信息")
    
    def start_pair_trading(self, pair: str):
        """開始交易對交易"""
        if not PYQT_AVAILABLE:
            return
            
        reply = QMessageBox.question(
            self, "確認操作", 
            f"確定要開始 {pair} 的交易嗎？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info(f"🚀 開始 {pair} 交易")
    
    def stop_pair_trading(self, pair: str):
        """停止交易對交易"""
        if not PYQT_AVAILABLE:
            return
            
        reply = QMessageBox.question(
            self, "確認操作", 
            f"確定要停止 {pair} 的交易嗎？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info(f"🛑 停止 {pair} 交易")
    
    def close_all_positions(self, pair: str):
        """平倉所有倉位"""
        if not PYQT_AVAILABLE:
            return
            
        reply = QMessageBox.question(
            self, "確認操作", 
            f"確定要平倉 {pair} 的所有倉位嗎？\n這個操作不可撤銷！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info(f"📉 平倉 {pair} 所有倉位")
    
    def configure_pair(self, pair: str):
        """配置交易對"""
        if PYQT_AVAILABLE:
            QMessageBox.information(self, "交易對配置", f"配置 {pair} 的交易參數")
    
    def toggle_auto_refresh(self, enabled: bool):
        """切換自動刷新"""
        if not PYQT_AVAILABLE:
            return
            
        if enabled:
            interval = self.refresh_interval_spin.value() * 1000
            self.update_timer.start(interval)
            logger.info(f"🔄 啟動自動刷新，間隔: {interval/1000}秒")
        else:
            self.update_timer.stop()
            logger.info("⏸️ 停止自動刷新")
    
    def update_refresh_interval(self, value: int):
        """更新刷新間隔"""
        if PYQT_AVAILABLE and self.update_timer.isActive():
            self.update_timer.start(value * 1000)
    
    def refresh_data(self):
        """手動刷新數據"""
        logger.info("🔄 手動刷新多交易對數據")
        self.update_data()
    
    def update_data(self):
        """更新數據"""
        try:
            # 模擬數據更新
            import random
            
            # 更新摘要數據
            summary_data = {
                'active_pairs': random.randint(2, 5),
                'total_pairs': len(self.monitored_pairs),
                'total_positions': random.randint(5, 20),
                'total_capital': random.randint(100000, 500000),
                'total_pnl': random.randint(-50000, 100000),
                'risk_level': random.choice(['low', 'medium', 'high']),
                'utilization_rate': random.uniform(0.3, 0.8),
                'daily_var': random.randint(10000, 50000),
                'max_drawdown': random.uniform(0.01, 0.1),
                'avg_confidence': random.uniform(0.4, 0.9),
                'accuracy_rate': random.uniform(0.6, 0.9)
            }
            
            if PYQT_AVAILABLE:
                self.summary_widget.update_summary(summary_data)
            
            # 更新各個交易對卡片
            for pair, card in self.pair_cards.items():
                # 模擬價格數據
                base_price = {
                    "BTCTWD": 1500000,
                    "ETHTWD": 100000,
                    "USDTTWD": 31.5,
                    "LTCTWD": 3000,
                    "BCHTWD": 15000
                }.get(pair, 10000)
                
                price_change = random.uniform(-0.05, 0.05)
                current_price = base_price * (1 + price_change)
                
                price_data = {
                    'current_price': current_price,
                    'price_change': base_price * price_change,
                    'price_change_percent': price_change * 100,
                    'volume_24h': random.uniform(1000000, 10000000),
                    'high_24h': current_price * 1.02,
                    'low_24h': current_price * 0.98
                }
                
                # 模擬交易數據
                trading_data = {
                    'position_count': random.randint(0, 5),
                    'total_position_size': random.uniform(10000, 100000),
                    'unrealized_pnl': random.uniform(-20000, 50000),
                    'realized_pnl': random.uniform(-10000, 30000),
                    'ai_confidence': random.uniform(0.3, 0.9),
                    'risk_score': random.uniform(0.1, 0.8),
                    'strategy_active': random.choice([True, False])
                }
                
                card.update_price_data(price_data)
                card.update_trading_data(trading_data)
            
        except Exception as e:
            logger.error(f"❌ 更新多交易對數據失敗: {e}")
    
    def get_selected_pair(self) -> Optional[str]:
        """獲取當前選中的交易對"""
        return self.selected_pair
    
    def set_monitored_pairs(self, pairs: List[str]):
        """設置監控的交易對"""
        self.monitored_pairs = pairs
        
        if PYQT_AVAILABLE:
            # 清除現有卡片
            for card in self.pair_cards.values():
                card.deleteLater()
            self.pair_cards.clear()
            
            # 重新創建卡片
            self.create_pair_cards()
        
        logger.info(f"📊 更新監控交易對: {pairs}")

# 使用示例
if __name__ == "__main__":
    import sys
    
    if PYQT_AVAILABLE:
        from PyQt5.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        
        # 創建多交易對監控界面
        monitor = MultiPairMonitor()
        monitor.show()
        
        # 連接信號
        def on_pair_selected(pair):
            print(f"選中交易對: {pair}")
        
        monitor.pair_selected.connect(on_pair_selected)
        
        sys.exit(app.exec_())
    else:
        print("📊 多交易對監控界面 - 文本模式")
        monitor = MultiPairMonitor()
        print("✅ 多交易對監控界面初始化完成")