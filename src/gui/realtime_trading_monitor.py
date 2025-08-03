#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實時交易監控 - 實時監控AI交易系統的交易活動和性能
"""

import sys
import os
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import numpy as np
import pandas as pd

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
        QPushButton, QTextEdit, QComboBox, QGroupBox, QGridLayout,
        QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
        QScrollArea, QFrame, QSplitter, QTreeWidget, QTreeWidgetItem,
        QSlider, QSpinBox, QCheckBox, QDateEdit, QDoubleSpinBox,
        QMessageBox, QFileDialog, QPlainTextEdit, QListWidget,
        QListWidgetItem, QDialog, QDialogButtonBox
    )
    from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThread, QDate
    from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QPen
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt6 未安裝，實時交易監控將使用文本模式")

# 導入AImax核心組件
try:
    from src.ai.enhanced_ai_manager import EnhancedAIManager
    from src.trading.risk_manager import create_risk_manager
    from src.data.max_client import create_max_client
    AIMAX_MODULES_AVAILABLE = True
except ImportError:
    AIMAX_MODULES_AVAILABLE = False
    print("⚠️ AImax模塊未完全可用，將使用模擬模式")

logger = logging.getLogger(__name__)

class TradingSignalWidget(QWidget if PYQT_AVAILABLE else object):
    """交易信號監控組件"""
    
    signal_received = pyqtSignal(dict) if PYQT_AVAILABLE else None
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.setup_ui()
        self.signal_history = []
        
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("📡 實時交易信號")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 當前信號顯示
        current_signal_group = QGroupBox("當前信號")
        current_layout = QGridLayout(current_signal_group)
        
        # 信號狀態
        current_layout.addWidget(QLabel("信號狀態:"), 0, 0)
        self.signal_status_label = QLabel("等待中...")
        self.signal_status_label.setStyleSheet("color: #666; font-weight: bold;")
        current_layout.addWidget(self.signal_status_label, 0, 1)
        
        # 交易對
        current_layout.addWidget(QLabel("交易對:"), 1, 0)
        self.trading_pair_label = QLabel("--")
        current_layout.addWidget(self.trading_pair_label, 1, 1)
        
        # 信號類型
        current_layout.addWidget(QLabel("信號類型:"), 2, 0)
        self.signal_type_label = QLabel("--")
        current_layout.addWidget(self.signal_type_label, 2, 1)
        
        # AI信心度
        current_layout.addWidget(QLabel("AI信心度:"), 3, 0)
        self.confidence_label = QLabel("--")
        current_layout.addWidget(self.confidence_label, 3, 1)
        
        # 建議價格
        current_layout.addWidget(QLabel("建議價格:"), 4, 0)
        self.suggested_price_label = QLabel("--")
        current_layout.addWidget(self.suggested_price_label, 4, 1)
        
        # 風險評級
        current_layout.addWidget(QLabel("風險評級:"), 5, 0)
        self.risk_level_label = QLabel("--")
        current_layout.addWidget(self.risk_level_label, 5, 1)
        
        layout.addWidget(current_signal_group)
        
        # 信號確認按鈕
        confirm_layout = QHBoxLayout()
        
        self.confirm_btn = QPushButton("✅ 確認執行")
        self.confirm_btn.clicked.connect(self.confirm_signal)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        confirm_layout.addWidget(self.confirm_btn)
        
        self.reject_btn = QPushButton("❌ 拒絕信號")
        self.reject_btn.clicked.connect(self.reject_signal)
        self.reject_btn.setEnabled(False)
        self.reject_btn.setStyleSheet("background-color: #F44336; color: white;")
        confirm_layout.addWidget(self.reject_btn)
        
        self.modify_btn = QPushButton("✏️ 修改參數")
        self.modify_btn.clicked.connect(self.modify_signal)
        self.modify_btn.setEnabled(False)
        confirm_layout.addWidget(self.modify_btn)
        
        confirm_layout.addStretch()
        layout.addLayout(confirm_layout)
        
        # 信號歷史
        history_group = QGroupBox("信號歷史")
        history_layout = QVBoxLayout(history_group)
        
        self.signal_history_list = QListWidget()
        history_layout.addWidget(self.signal_history_list)
        
        layout.addWidget(history_group)
        
        # 定時更新信號
        self.signal_timer = QTimer()
        self.signal_timer.timeout.connect(self.update_signals)
        self.signal_timer.start(5000)  # 每5秒檢查新信號
    
    def update_signals(self):
        """更新交易信號"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 模擬接收新信號
            import random
            
            if random.random() < 0.3:  # 30%機率產生新信號
                signal_data = self.generate_mock_signal()
                self.receive_signal(signal_data)
                
        except Exception as e:
            logger.error(f"❌ 更新交易信號失敗: {e}")
    
    def generate_mock_signal(self) -> Dict[str, Any]:
        """生成模擬交易信號"""
        import random
        
        pairs = ["BTCTWD", "ETHTWD", "LTCTWD", "BCHTWD"]
        signal_types = ["BUY", "SELL", "HOLD"]
        risk_levels = ["低", "中", "高"]
        
        return {
            "timestamp": datetime.now(),
            "trading_pair": random.choice(pairs),
            "signal_type": random.choice(signal_types),
            "confidence": random.uniform(60, 95),
            "suggested_price": random.uniform(40000, 50000),
            "risk_level": random.choice(risk_levels),
            "ai_reasoning": "基於技術分析和市場趨勢的AI決策",
            "stop_loss": random.uniform(38000, 42000),
            "take_profit": random.uniform(48000, 55000)
        }
    
    def receive_signal(self, signal_data: Dict[str, Any]):
        """接收新的交易信號"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 更新當前信號顯示
            self.signal_status_label.setText("🔴 新信號")
            self.signal_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            
            self.trading_pair_label.setText(signal_data["trading_pair"])
            self.signal_type_label.setText(signal_data["signal_type"])
            
            # 設置信號類型顏色
            signal_color = "#4CAF50" if signal_data["signal_type"] == "BUY" else "#F44336" if signal_data["signal_type"] == "SELL" else "#FF9800"
            self.signal_type_label.setStyleSheet(f"color: {signal_color}; font-weight: bold;")
            
            self.confidence_label.setText(f"{signal_data['confidence']:.1f}%")
            self.suggested_price_label.setText(f"{signal_data['suggested_price']:,.0f} TWD")
            self.risk_level_label.setText(signal_data["risk_level"])
            
            # 設置風險等級顏色
            risk_color = "#4CAF50" if signal_data["risk_level"] == "低" else "#FF9800" if signal_data["risk_level"] == "中" else "#F44336"
            self.risk_level_label.setStyleSheet(f"color: {risk_color}; font-weight: bold;")
            
            # 啟用確認按鈕
            self.confirm_btn.setEnabled(True)
            self.reject_btn.setEnabled(True)
            self.modify_btn.setEnabled(True)
            
            # 添加到歷史
            self.add_to_history(signal_data)
            
            # 發送信號
            if self.signal_received:
                self.signal_received.emit(signal_data)
            
            logger.info(f"📡 接收到新交易信號: {signal_data['signal_type']} {signal_data['trading_pair']}")
            
        except Exception as e:
            logger.error(f"❌ 處理交易信號失敗: {e}")
    
    def add_to_history(self, signal_data: Dict[str, Any]):
        """添加信號到歷史記錄"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            timestamp = signal_data["timestamp"].strftime("%H:%M:%S")
            signal_text = f"[{timestamp}] {signal_data['signal_type']} {signal_data['trading_pair']} - 信心度: {signal_data['confidence']:.1f}%"
            
            item = QListWidgetItem(signal_text)
            
            # 設置顏色
            if signal_data["signal_type"] == "BUY":
                item.setBackground(QColor(144, 238, 144))
            elif signal_data["signal_type"] == "SELL":
                item.setBackground(QColor(255, 182, 193))
            else:
                item.setBackground(QColor(255, 255, 224))
            
            self.signal_history_list.insertItem(0, item)
            
            # 限制歷史記錄數量
            if self.signal_history_list.count() > 50:
                self.signal_history_list.takeItem(50)
            
            # 保存到內部歷史
            self.signal_history.append(signal_data)
            if len(self.signal_history) > 100:
                self.signal_history.pop(0)
                
        except Exception as e:
            logger.error(f"❌ 添加信號歷史失敗: {e}")
    
    def confirm_signal(self):
        """確認執行信號"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            self.signal_status_label.setText("✅ 已確認")
            self.signal_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            # 禁用按鈕
            self.confirm_btn.setEnabled(False)
            self.reject_btn.setEnabled(False)
            self.modify_btn.setEnabled(False)
            
            QMessageBox.information(self, "信號確認", "交易信號已確認執行")
            logger.info("✅ 用戶確認執行交易信號")
            
        except Exception as e:
            logger.error(f"❌ 確認信號失敗: {e}")
    
    def reject_signal(self):
        """拒絕信號"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            self.signal_status_label.setText("❌ 已拒絕")
            self.signal_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            
            # 禁用按鈕
            self.confirm_btn.setEnabled(False)
            self.reject_btn.setEnabled(False)
            self.modify_btn.setEnabled(False)
            
            QMessageBox.information(self, "信號拒絕", "交易信號已拒絕")
            logger.info("❌ 用戶拒絕交易信號")
            
        except Exception as e:
            logger.error(f"❌ 拒絕信號失敗: {e}")
    
    def modify_signal(self):
        """修改信號參數"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 創建修改對話框
            dialog = QDialog(self)
            dialog.setWindowTitle("修改交易參數")
            dialog.setModal(True)
            dialog.resize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            # 參數表單
            form_layout = QGridLayout()
            
            # 交易數量
            form_layout.addWidget(QLabel("交易數量:"), 0, 0)
            quantity_spin = QDoubleSpinBox()
            quantity_spin.setRange(0.001, 10.0)
            quantity_spin.setValue(0.1)
            quantity_spin.setDecimals(3)
            form_layout.addWidget(quantity_spin, 0, 1)
            
            # 止損價格
            form_layout.addWidget(QLabel("止損價格:"), 1, 0)
            stop_loss_spin = QDoubleSpinBox()
            stop_loss_spin.setRange(10000, 100000)
            stop_loss_spin.setValue(40000)
            form_layout.addWidget(stop_loss_spin, 1, 1)
            
            # 止盈價格
            form_layout.addWidget(QLabel("止盈價格:"), 2, 0)
            take_profit_spin = QDoubleSpinBox()
            take_profit_spin.setRange(10000, 100000)
            take_profit_spin.setValue(50000)
            form_layout.addWidget(take_profit_spin, 2, 1)
            
            layout.addLayout(form_layout)
            
            # 按鈕
            button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                QMessageBox.information(self, "參數修改", "交易參數已修改")
                logger.info("✏️ 用戶修改交易參數")
            
        except Exception as e:
            logger.error(f"❌ 修改信號參數失敗: {e}")

class PositionMonitorWidget(QWidget if PYQT_AVAILABLE else object):
    """持倉監控組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.setup_ui()
        self.positions = []
        
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("💼 持倉監控")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 持倉統計
        stats_group = QGroupBox("持倉統計")
        stats_layout = QGridLayout(stats_group)
        
        # 總持倉價值
        stats_layout.addWidget(QLabel("總持倉價值:"), 0, 0)
        self.total_value_label = QLabel("0 TWD")
        self.total_value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        stats_layout.addWidget(self.total_value_label, 0, 1)
        
        # 未實現盈虧
        stats_layout.addWidget(QLabel("未實現盈虧:"), 1, 0)
        self.unrealized_pnl_label = QLabel("0 TWD")
        self.unrealized_pnl_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        stats_layout.addWidget(self.unrealized_pnl_label, 1, 1)
        
        # 持倉數量
        stats_layout.addWidget(QLabel("持倉數量:"), 2, 0)
        self.position_count_label = QLabel("0")
        stats_layout.addWidget(self.position_count_label, 2, 1)
        
        # 今日盈虧
        stats_layout.addWidget(QLabel("今日盈虧:"), 3, 0)
        self.daily_pnl_label = QLabel("0 TWD")
        self.daily_pnl_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        stats_layout.addWidget(self.daily_pnl_label, 3, 1)
        
        layout.addWidget(stats_group)
        
        # 持倉詳情表格
        positions_group = QGroupBox("持倉詳情")
        positions_layout = QVBoxLayout(positions_group)
        
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels([
            "交易對", "方向", "數量", "均價", "當前價", "盈虧", "盈虧%", "操作"
        ])
        
        # 調整列寬
        header = self.positions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        positions_layout.addWidget(self.positions_table)
        layout.addWidget(positions_group)
        
        # 控制按鈕
        control_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.clicked.connect(self.refresh_positions)
        control_layout.addWidget(self.refresh_btn)
        
        self.close_all_btn = QPushButton("🚫 全部平倉")
        self.close_all_btn.clicked.connect(self.close_all_positions)
        self.close_all_btn.setStyleSheet("background-color: #F44336; color: white;")
        control_layout.addWidget(self.close_all_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 定時更新持倉
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_positions)
        self.position_timer.start(3000)  # 每3秒更新
        
        # 初始化模擬持倉
        self.initialize_mock_positions()
    
    def initialize_mock_positions(self):
        """初始化模擬持倉"""
        import random
        
        mock_positions = [
            {
                "pair": "BTCTWD",
                "direction": "多頭",
                "quantity": 0.15,
                "avg_price": 45200,
                "current_price": 46800,
                "pnl": 240,
                "pnl_pct": 3.54
            },
            {
                "pair": "ETHTWD", 
                "direction": "多頭",
                "quantity": 2.5,
                "avg_price": 2850,
                "current_price": 2920,
                "pnl": 175,
                "pnl_pct": 2.46
            }
        ]
        
        self.positions = mock_positions
        self.update_position_display()
    
    def update_positions(self):
        """更新持倉數據"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 模擬價格變動
            import random
            
            for position in self.positions:
                # 模擬價格波動
                price_change = random.uniform(-0.02, 0.02)
                position["current_price"] *= (1 + price_change)
                
                # 重新計算盈虧
                if position["direction"] == "多頭":
                    position["pnl"] = (position["current_price"] - position["avg_price"]) * position["quantity"]
                else:
                    position["pnl"] = (position["avg_price"] - position["current_price"]) * position["quantity"]
                
                position["pnl_pct"] = (position["pnl"] / (position["avg_price"] * position["quantity"])) * 100
            
            self.update_position_display()
            
        except Exception as e:
            logger.error(f"❌ 更新持倉失敗: {e}")
    
    def update_position_display(self):
        """更新持倉顯示"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 更新統計信息
            total_value = sum(pos["current_price"] * pos["quantity"] for pos in self.positions)
            total_pnl = sum(pos["pnl"] for pos in self.positions)
            
            self.total_value_label.setText(f"{total_value:,.0f} TWD")
            self.unrealized_pnl_label.setText(f"{total_pnl:+,.0f} TWD")
            
            # 設置盈虧顏色
            pnl_color = "#4CAF50" if total_pnl >= 0 else "#F44336"
            self.unrealized_pnl_label.setStyleSheet(f"color: {pnl_color}; font-weight: bold;")
            
            self.position_count_label.setText(str(len(self.positions)))
            self.daily_pnl_label.setText(f"{total_pnl:+,.0f} TWD")
            self.daily_pnl_label.setStyleSheet(f"color: {pnl_color}; font-weight: bold;")
            
            # 更新持倉表格
            self.positions_table.setRowCount(len(self.positions))
            
            for row, position in enumerate(self.positions):
                self.positions_table.setItem(row, 0, QTableWidgetItem(position["pair"]))
                self.positions_table.setItem(row, 1, QTableWidgetItem(position["direction"]))
                self.positions_table.setItem(row, 2, QTableWidgetItem(f"{position['quantity']:.3f}"))
                self.positions_table.setItem(row, 3, QTableWidgetItem(f"{position['avg_price']:,.0f}"))
                self.positions_table.setItem(row, 4, QTableWidgetItem(f"{position['current_price']:,.0f}"))
                
                # 盈虧項目
                pnl_item = QTableWidgetItem(f"{position['pnl']:+,.0f}")
                pnl_color = "#4CAF50" if position["pnl"] >= 0 else "#F44336"
                pnl_item.setBackground(QColor(pnl_color))
                self.positions_table.setItem(row, 5, pnl_item)
                
                pnl_pct_item = QTableWidgetItem(f"{position['pnl_pct']:+.2f}%")
                pnl_pct_item.setBackground(QColor(pnl_color))
                self.positions_table.setItem(row, 6, pnl_pct_item)
                
                # 操作按鈕
                close_btn = QPushButton("平倉")
                close_btn.clicked.connect(lambda checked, r=row: self.close_position(r))
                close_btn.setStyleSheet("background-color: #FF9800; color: white;")
                self.positions_table.setCellWidget(row, 7, close_btn)
            
        except Exception as e:
            logger.error(f"❌ 更新持倉顯示失敗: {e}")
    
    def refresh_positions(self):
        """刷新持倉"""
        if PYQT_AVAILABLE:
            self.update_positions()
            QMessageBox.information(self, "刷新完成", "持倉數據已刷新")
    
    def close_position(self, row: int):
        """平倉指定持倉"""
        if not PYQT_AVAILABLE or row >= len(self.positions):
            return
            
        try:
            position = self.positions[row]
            
            reply = QMessageBox.question(
                self, "確認平倉", 
                f"確定要平倉 {position['pair']} 持倉嗎？\n"
                f"數量: {position['quantity']:.3f}\n"
                f"當前盈虧: {position['pnl']:+,.0f} TWD",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.positions.pop(row)
                self.update_position_display()
                QMessageBox.information(self, "平倉完成", "持倉已成功平倉")
                logger.info(f"✅ 平倉完成: {position['pair']}")
            
        except Exception as e:
            logger.error(f"❌ 平倉失敗: {e}")
            QMessageBox.warning(self, "錯誤", f"平倉失敗: {e}")
    
    def close_all_positions(self):
        """全部平倉"""
        if not PYQT_AVAILABLE or len(self.positions) == 0:
            return
            
        try:
            total_pnl = sum(pos["pnl"] for pos in self.positions)
            
            reply = QMessageBox.question(
                self, "確認全部平倉", 
                f"確定要平倉所有持倉嗎？\n"
                f"持倉數量: {len(self.positions)}\n"
                f"總盈虧: {total_pnl:+,.0f} TWD",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.positions.clear()
                self.update_position_display()
                QMessageBox.information(self, "平倉完成", "所有持倉已成功平倉")
                logger.info("✅ 全部平倉完成")
            
        except Exception as e:
            logger.error(f"❌ 全部平倉失敗: {e}")
            QMessageBox.warning(self, "錯誤", f"全部平倉失敗: {e}")

class TradingLogWidget(QWidget if PYQT_AVAILABLE else object):
    """交易日誌組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.setup_ui()
        self.log_entries = []
        
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 標題和控制
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 交易日誌")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 日誌級別過濾
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["全部", "信息", "警告", "錯誤", "交易"])
        self.log_level_combo.currentTextChanged.connect(self.filter_logs)
        header_layout.addWidget(self.log_level_combo)
        
        # 清空按鈕
        self.clear_btn = QPushButton("🗑️ 清空")
        self.clear_btn.clicked.connect(self.clear_logs)
        header_layout.addWidget(self.clear_btn)
        
        # 導出按鈕
        self.export_btn = QPushButton("📤 導出")
        self.export_btn.clicked.connect(self.export_logs)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # 日誌顯示區域
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)  # 限制日誌行數
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # 自動滾動到底部
        self.auto_scroll_checkbox = QCheckBox("自動滾動到底部")
        self.auto_scroll_checkbox.setChecked(True)
        layout.addWidget(self.auto_scroll_checkbox)
        
        # 初始化日誌
        self.add_log("系統啟動", "INFO", "交易監控系統已啟動")
    
    def add_log(self, category: str, level: str, message: str):
        """添加日誌條目"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = {
                "timestamp": timestamp,
                "category": category,
                "level": level,
                "message": message
            }
            
            self.log_entries.append(log_entry)
            
            # 限制日誌條目數量
            if len(self.log_entries) > 1000:
                self.log_entries.pop(0)
            
            # 格式化日誌文本
            level_icon = {
                "INFO": "ℹ️",
                "WARNING": "⚠️", 
                "ERROR": "❌",
                "TRADE": "💰"
            }.get(level, "📝")
            
            log_text = f"[{timestamp}] {level_icon} [{category}] {message}"
            
            # 添加到顯示區域
            self.log_text.appendPlainText(log_text)
            
            # 自動滾動
            if self.auto_scroll_checkbox.isChecked():
                scrollbar = self.log_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            
        except Exception as e:
            logger.error(f"❌ 添加日誌失敗: {e}")
    
    def filter_logs(self, level_filter: str):
        """過濾日誌"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            self.log_text.clear()
            
            for entry in self.log_entries:
                if level_filter == "全部" or entry["level"] == level_filter.upper():
                    level_icon = {
                        "INFO": "ℹ️",
                        "WARNING": "⚠️",
                        "ERROR": "❌", 
                        "TRADE": "💰"
                    }.get(entry["level"], "📝")
                    
                    log_text = f"[{entry['timestamp']}] {level_icon} [{entry['category']}] {entry['message']}"
                    self.log_text.appendPlainText(log_text)
            
        except Exception as e:
            logger.error(f"❌ 過濾日誌失敗: {e}")
    
    def clear_logs(self):
        """清空日誌"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            reply = QMessageBox.question(
                self, "確認清空", "確定要清空所有日誌嗎？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.log_entries.clear()
                self.log_text.clear()
                self.add_log("系統", "INFO", "日誌已清空")
            
        except Exception as e:
            logger.error(f"❌ 清空日誌失敗: {e}")
    
    def export_logs(self):
        """導出日誌"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "導出交易日誌", "", "Text Files (*.txt);;CSV Files (*.csv)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    if file_path.endswith('.csv'):
                        f.write("時間,類別,級別,消息\n")
                        for entry in self.log_entries:
                            f.write(f"{entry['timestamp']},{entry['category']},{entry['level']},{entry['message']}\n")
                    else:
                        for entry in self.log_entries:
                            f.write(f"[{entry['timestamp']}] [{entry['category']}] {entry['message']}\n")
                
                QMessageBox.information(self, "導出完成", "日誌已成功導出")
                
        except Exception as e:
            logger.error(f"❌ 導出日誌失敗: {e}")
            QMessageBox.warning(self, "錯誤", f"導出日誌失敗: {e}")

class EmergencyControlWidget(QWidget if PYQT_AVAILABLE else object):
    """緊急控制組件"""
    
    emergency_stop_triggered = pyqtSignal() if PYQT_AVAILABLE else None
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.setup_ui()
        self.emergency_active = False
        
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("🚨 緊急控制")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #F44336;")
        layout.addWidget(title)
        
        # 緊急停止按鈕
        self.emergency_stop_btn = QPushButton("🛑 緊急停止")
        self.emergency_stop_btn.clicked.connect(self.trigger_emergency_stop)
        self.emergency_stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        layout.addWidget(self.emergency_stop_btn)
        
        # 狀態顯示
        status_group = QGroupBox("系統狀態")
        status_layout = QGridLayout(status_group)
        
        # 交易狀態
        status_layout.addWidget(QLabel("交易狀態:"), 0, 0)
        self.trading_status_label = QLabel("🟢 正常運行")
        self.trading_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(self.trading_status_label, 0, 1)
        
        # AI狀態
        status_layout.addWidget(QLabel("AI狀態:"), 1, 0)
        self.ai_status_label = QLabel("🟢 正常運行")
        self.ai_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(self.ai_status_label, 1, 1)
        
        # 風險狀態
        status_layout.addWidget(QLabel("風險狀態:"), 2, 0)
        self.risk_status_label = QLabel("🟢 安全")
        self.risk_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(self.risk_status_label, 2, 1)
        
        # 連接狀態
        status_layout.addWidget(QLabel("連接狀態:"), 3, 0)
        self.connection_status_label = QLabel("🟢 已連接")
        self.connection_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(self.connection_status_label, 3, 1)
        
        layout.addWidget(status_group)
        
        # 快速操作
        quick_actions_group = QGroupBox("快速操作")
        quick_layout = QVBoxLayout(quick_actions_group)
        
        # 暫停交易
        self.pause_trading_btn = QPushButton("⏸️ 暫停交易")
        self.pause_trading_btn.clicked.connect(self.pause_trading)
        quick_layout.addWidget(self.pause_trading_btn)
        
        # 恢復交易
        self.resume_trading_btn = QPushButton("▶️ 恢復交易")
        self.resume_trading_btn.clicked.connect(self.resume_trading)
        self.resume_trading_btn.setEnabled(False)
        quick_layout.addWidget(self.resume_trading_btn)
        
        # 重新連接
        self.reconnect_btn = QPushButton("🔄 重新連接")
        self.reconnect_btn.clicked.connect(self.reconnect_system)
        quick_layout.addWidget(self.reconnect_btn)
        
        layout.addWidget(quick_actions_group)
        
        # 風險警報
        alert_group = QGroupBox("風險警報")
        alert_layout = QVBoxLayout(alert_group)
        
        self.alert_list = QListWidget()
        alert_layout.addWidget(self.alert_list)
        
        layout.addWidget(alert_group)
        
        # 定時檢查系統狀態
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_system_status)
        self.status_timer.start(2000)  # 每2秒檢查
    
    def trigger_emergency_stop(self):
        """觸發緊急停止"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            reply = QMessageBox.critical(
                self, "緊急停止確認", 
                "⚠️ 確定要執行緊急停止嗎？\n\n"
                "這將立即停止所有交易活動，\n"
                "平倉所有持倉，並斷開系統連接。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.emergency_active = True
                
                # 更新狀態
                self.trading_status_label.setText("🔴 緊急停止")
                self.trading_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
                
                self.ai_status_label.setText("🔴 已停止")
                self.ai_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
                
                self.risk_status_label.setText("🔴 緊急狀態")
                self.risk_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
                
                # 禁用緊急停止按鈕
                self.emergency_stop_btn.setEnabled(False)
                self.emergency_stop_btn.setText("🛑 已緊急停止")
                
                # 添加警報
                self.add_alert("緊急停止", "系統已執行緊急停止")
                
                # 發送信號
                if self.emergency_stop_triggered:
                    self.emergency_stop_triggered.emit()
                
                QMessageBox.information(self, "緊急停止", "系統已執行緊急停止")
                logger.critical("🚨 系統緊急停止已觸發")
            
        except Exception as e:
            logger.error(f"❌ 緊急停止失敗: {e}")
            QMessageBox.warning(self, "錯誤", f"緊急停止失敗: {e}")
    
    def pause_trading(self):
        """暫停交易"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            self.trading_status_label.setText("🟡 已暫停")
            self.trading_status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            
            self.pause_trading_btn.setEnabled(False)
            self.resume_trading_btn.setEnabled(True)
            
            self.add_alert("交易暫停", "交易活動已暫停")
            QMessageBox.information(self, "交易暫停", "交易活動已暫停")
            logger.info("⏸️ 交易已暫停")
            
        except Exception as e:
            logger.error(f"❌ 暫停交易失敗: {e}")
    
    def resume_trading(self):
        """恢復交易"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            self.trading_status_label.setText("🟢 正常運行")
            self.trading_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            self.pause_trading_btn.setEnabled(True)
            self.resume_trading_btn.setEnabled(False)
            
            self.add_alert("交易恢復", "交易活動已恢復")
            QMessageBox.information(self, "交易恢復", "交易活動已恢復")
            logger.info("▶️ 交易已恢復")
            
        except Exception as e:
            logger.error(f"❌ 恢復交易失敗: {e}")
    
    def reconnect_system(self):
        """重新連接系統"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            self.connection_status_label.setText("🟡 重新連接中...")
            self.connection_status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            
            # 模擬重新連接過程
            QTimer.singleShot(2000, self.on_reconnect_complete)
            
            logger.info("🔄 開始重新連接系統")
            
        except Exception as e:
            logger.error(f"❌ 重新連接失敗: {e}")
    
    def on_reconnect_complete(self):
        """重新連接完成"""
        if not PYQT_AVAILABLE:
            return
            
        self.connection_status_label.setText("🟢 已連接")
        self.connection_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        self.add_alert("連接恢復", "系統連接已恢復")
        QMessageBox.information(self, "重新連接", "系統連接已恢復")
        logger.info("✅ 系統重新連接完成")
    
    def check_system_status(self):
        """檢查系統狀態"""
        if not PYQT_AVAILABLE or self.emergency_active:
            return
            
        try:
            # 模擬狀態檢查
            import random
            
            # 隨機生成警報
            if random.random() < 0.05:  # 5%機率產生警報
                alert_types = [
                    ("價格異常", "檢測到異常價格波動"),
                    ("網絡延遲", "網絡連接延遲較高"),
                    ("資金不足", "可用資金不足警告"),
                    ("AI響應慢", "AI模型響應時間較長")
                ]
                
                alert_type, alert_message = random.choice(alert_types)
                self.add_alert(alert_type, alert_message)
            
        except Exception as e:
            logger.error(f"❌ 檢查系統狀態失敗: {e}")
    
    def add_alert(self, alert_type: str, message: str):
        """添加警報"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            alert_text = f"[{timestamp}] {alert_type}: {message}"
            
            item = QListWidgetItem(alert_text)
            
            # 設置警報顏色
            if "緊急" in alert_type or "停止" in alert_type:
                item.setBackground(QColor(255, 182, 193))
            elif "暫停" in alert_type or "延遲" in alert_type:
                item.setBackground(QColor(255, 255, 224))
            else:
                item.setBackground(QColor(144, 238, 144))
            
            self.alert_list.insertItem(0, item)
            
            # 限制警報數量
            if self.alert_list.count() > 20:
                self.alert_list.takeItem(20)
            
        except Exception as e:
            logger.error(f"❌ 添加警報失敗: {e}")

class RealtimeTradingMonitor(QWidget if PYQT_AVAILABLE else object):
    """實時交易監控主組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # 核心組件
        self.ai_manager = None
        self.risk_manager = None
        self.max_client = None
        
        # 子組件
        self.signal_widget = None
        self.position_widget = None
        self.log_widget = None
        self.emergency_widget = None
        
        self.setup_ui()
        self.initialize_components()
        self.connect_signals()
        
        self.logger.info("📡 實時交易監控組件初始化完成")
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            self.logger.info("🖥️ 實時交易監控運行在文本模式")
            return
            
        layout = QVBoxLayout(self)
        
        # 主標題
        main_title = QLabel("📡 實時交易監控中心")
        main_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(main_title)
        
        # 創建主分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側面板 - 信號和持倉
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 交易信號組件
        self.signal_widget = TradingSignalWidget()
        left_layout.addWidget(self.signal_widget)
        
        # 持倉監控組件
        self.position_widget = PositionMonitorWidget()
        left_layout.addWidget(self.position_widget)
        
        main_splitter.addWidget(left_panel)
        
        # 右側面板 - 日誌和控制
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 緊急控制組件
        self.emergency_widget = EmergencyControlWidget()
        right_layout.addWidget(self.emergency_widget)
        
        # 交易日誌組件
        self.log_widget = TradingLogWidget()
        right_layout.addWidget(self.log_widget)
        
        main_splitter.addWidget(right_panel)
        
        # 設置分割比例
        main_splitter.setSizes([700, 500])
        
        layout.addWidget(main_splitter)
        
        # 狀態欄
        self.create_status_bar(layout)
    
    def create_status_bar(self, parent_layout):
        """創建狀態欄"""
        if not PYQT_AVAILABLE:
            return
            
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_layout = QHBoxLayout(status_frame)
        
        # 系統狀態
        self.system_status_label = QLabel("🟢 系統正常")
        self.system_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(self.system_status_label)
        
        status_layout.addStretch()
        
        # 連接狀態
        self.connection_status_label = QLabel("🔗 已連接")
        status_layout.addWidget(self.connection_status_label)
        
        # 最後更新時間
        self.last_update_label = QLabel("最後更新: --")
        status_layout.addWidget(self.last_update_label)
        
        # 活躍交易數
        self.active_trades_label = QLabel("活躍交易: 0")
        status_layout.addWidget(self.active_trades_label)
        
        parent_layout.addWidget(status_frame)
        
        # 定時更新狀態欄
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(1000)  # 每秒更新
    
    def initialize_components(self):
        """初始化組件"""
        try:
            if AIMAX_MODULES_AVAILABLE:
                # 初始化AI管理器
                self.ai_manager = EnhancedAIManager()
                self.logger.info("✅ AI管理器初始化完成")
                
                # 初始化風險管理器
                self.risk_manager = create_risk_manager()
                self.logger.info("✅ 風險管理器初始化完成")
                
                # 初始化MAX客戶端
                self.max_client = create_max_client()
                self.logger.info("✅ MAX客戶端初始化完成")
                
            else:
                self.logger.warning("⚠️ 使用模擬模式")
            
        except Exception as e:
            self.logger.error(f"❌ 組件初始化失敗: {e}")
    
    def connect_signals(self):
        """連接信號"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 連接交易信號
            if self.signal_widget and hasattr(self.signal_widget, 'signal_received'):
                self.signal_widget.signal_received.connect(self.on_signal_received)
            
            # 連接緊急停止信號
            if self.emergency_widget and hasattr(self.emergency_widget, 'emergency_stop_triggered'):
                self.emergency_widget.emergency_stop_triggered.connect(self.on_emergency_stop)
            
            self.logger.info("✅ 信號連接完成")
            
        except Exception as e:
            self.logger.error(f"❌ 信號連接失敗: {e}")
    
    def on_signal_received(self, signal_data: Dict[str, Any]):
        """處理接收到的交易信號"""
        try:
            # 記錄到日誌
            if self.log_widget:
                self.log_widget.add_log(
                    "交易信號", "TRADE",
                    f"接收到 {signal_data['signal_type']} 信號: {signal_data['trading_pair']} "
                    f"(信心度: {signal_data['confidence']:.1f}%)"
                )
            
            # 更新狀態
            if PYQT_AVAILABLE:
                self.system_status_label.setText("🟡 處理信號中...")
                self.system_status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            
            self.logger.info(f"📡 處理交易信號: {signal_data}")
            
        except Exception as e:
            self.logger.error(f"❌ 處理交易信號失敗: {e}")
    
    def on_emergency_stop(self):
        """處理緊急停止"""
        try:
            # 記錄到日誌
            if self.log_widget:
                self.log_widget.add_log("緊急控制", "ERROR", "系統緊急停止已觸發")
            
            # 更新狀態
            if PYQT_AVAILABLE:
                self.system_status_label.setText("🔴 緊急停止")
                self.system_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            
            # 停止所有定時器
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
            
            self.logger.critical("🚨 緊急停止已觸發")
            
        except Exception as e:
            self.logger.error(f"❌ 處理緊急停止失敗: {e}")
    
    def update_status_bar(self):
        """更新狀態欄"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 更新最後更新時間
            current_time = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.setText(f"最後更新: {current_time}")
            
            # 更新活躍交易數
            if self.position_widget and hasattr(self.position_widget, 'positions'):
                active_count = len(self.position_widget.positions)
                self.active_trades_label.setText(f"活躍交易: {active_count}")
            
        except Exception as e:
            self.logger.error(f"❌ 更新狀態欄失敗: {e}")
    
    def start_monitoring(self):
        """開始監控"""
        try:
            if self.log_widget:
                self.log_widget.add_log("系統", "INFO", "開始實時交易監控")
            
            if PYQT_AVAILABLE:
                self.system_status_label.setText("🟢 監控中...")
                self.system_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            
            self.logger.info("🚀 實時交易監控已開始")
            
        except Exception as e:
            self.logger.error(f"❌ 開始監控失敗: {e}")
    
    def stop_monitoring(self):
        """停止監控"""
        try:
            if self.log_widget:
                self.log_widget.add_log("系統", "INFO", "停止實時交易監控")
            
            if PYQT_AVAILABLE:
                self.system_status_label.setText("🟡 已停止")
                self.system_status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
            
            # 停止定時器
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
            
            self.logger.info("⏹️ 實時交易監控已停止")
            
        except Exception as e:
            self.logger.error(f"❌ 停止監控失敗: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """獲取監控狀態"""
        try:
            status = {
                "system_running": True,
                "ai_connected": self.ai_manager is not None,
                "risk_manager_active": self.risk_manager is not None,
                "max_client_connected": self.max_client is not None,
                "active_positions": len(self.position_widget.positions) if self.position_widget else 0,
                "signal_count": len(self.signal_widget.signal_history) if self.signal_widget else 0,
                "log_entries": len(self.log_widget.log_entries) if self.log_widget else 0
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"❌ 獲取監控狀態失敗: {e}")
            return {}

def create_realtime_trading_monitor():
    """創建實時交易監控組件實例"""
    return RealtimeTradingMonitor()

def main():
    """主函數 - 用於測試"""
    import sys
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 啟動實時交易監控測試")
    
    if PYQT_AVAILABLE:
        from PyQt6.QtWidgets import QApplication, QMainWindow
        
        app = QApplication(sys.argv)
        app.setApplicationName("Realtime Trading Monitor Test")
        
        # 創建主窗口
        main_window = QMainWindow()
        main_window.setWindowTitle("實時交易監控測試")
        main_window.setGeometry(100, 100, 1600, 1000)
        
        # 創建實時交易監控組件
        monitor = RealtimeTradingMonitor()
        main_window.setCentralWidget(monitor)
        
        # 開始監控
        monitor.start_monitoring()
        
        main_window.show()
        
        # 運行應用程序
        sys.exit(app.exec())
    else:
        # 文本模式
        logger.info("🖥️ 運行在文本模式")
        monitor = RealtimeTradingMonitor()
        monitor.start_monitoring()
        
        try:
            input("按Enter鍵退出...")
        except KeyboardInterrupt:
            logger.info("⏹️ 用戶中斷，正在關閉...")
        finally:
            monitor.stop_monitoring()

if __name__ == "__main__":
    main()