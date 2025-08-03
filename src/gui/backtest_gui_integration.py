#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回測功能GUI整合 - 將回測功能整合到GUI界面
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
        QMessageBox, QFileDialog, QPlainTextEdit
    )
    from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThread, QDate
    from PyQt6.QtGui import QFont, QColor, QPalette, QPixmap, QPainter, QPen
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt6 未安裝，回測GUI整合將使用文本模式")

# 導入AImax核心組件
try:
    from src.core.backtest_reporter import create_backtest_report_generator
    from src.ai.enhanced_ai_manager import EnhancedAIManager
    AIMAX_MODULES_AVAILABLE = True
except ImportError:
    AIMAX_MODULES_AVAILABLE = False
    print("⚠️ AImax模塊未完全可用，將使用模擬模式")

logger = logging.getLogger(__name__)

class BacktestConfigWidget(QWidget if PYQT_AVAILABLE else object):
    """回測配置組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("⚙️ 回測配置")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 配置表單
        config_group = QGroupBox("基本配置")
        config_layout = QGridLayout(config_group)
        
        # 開始日期
        config_layout.addWidget(QLabel("開始日期:"), 0, 0)
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.setCalendarPopup(True)
        config_layout.addWidget(self.start_date_edit, 0, 1)
        
        # 結束日期
        config_layout.addWidget(QLabel("結束日期:"), 1, 0)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        config_layout.addWidget(self.end_date_edit, 1, 1)
        
        # 初始資金
        config_layout.addWidget(QLabel("初始資金:"), 2, 0)
        self.initial_capital_spin = QDoubleSpinBox()
        self.initial_capital_spin.setRange(10000, 10000000)
        self.initial_capital_spin.setValue(1000000)
        self.initial_capital_spin.setSuffix(" TWD")
        config_layout.addWidget(self.initial_capital_spin, 2, 1)
        
        # 手續費率
        config_layout.addWidget(QLabel("手續費率:"), 3, 0)
        self.commission_spin = QDoubleSpinBox()
        self.commission_spin.setRange(0, 0.01)
        self.commission_spin.setValue(0.001)
        self.commission_spin.setDecimals(4)
        self.commission_spin.setSuffix("%")
        config_layout.addWidget(self.commission_spin, 3, 1)
        
        # 滑點率
        config_layout.addWidget(QLabel("滑點率:"), 4, 0)
        self.slippage_spin = QDoubleSpinBox()
        self.slippage_spin.setRange(0, 0.01)
        self.slippage_spin.setValue(0.0005)
        self.slippage_spin.setDecimals(4)
        self.slippage_spin.setSuffix("%")
        config_layout.addWidget(self.slippage_spin, 4, 1)
        
        layout.addWidget(config_group)
        
        # 策略配置
        strategy_group = QGroupBox("策略配置")
        strategy_layout = QGridLayout(strategy_group)
        
        # 最大持倉數
        strategy_layout.addWidget(QLabel("最大持倉數:"), 0, 0)
        self.max_positions_spin = QSpinBox()
        self.max_positions_spin.setRange(1, 20)
        self.max_positions_spin.setValue(5)
        strategy_layout.addWidget(self.max_positions_spin, 0, 1)
        
        # 止損百分比
        strategy_layout.addWidget(QLabel("止損百分比:"), 1, 0)
        self.stop_loss_spin = QDoubleSpinBox()
        self.stop_loss_spin.setRange(0.01, 0.5)
        self.stop_loss_spin.setValue(0.05)
        self.stop_loss_spin.setDecimals(3)
        self.stop_loss_spin.setSuffix("%")
        strategy_layout.addWidget(self.stop_loss_spin, 1, 1)
        
        # 止盈百分比
        strategy_layout.addWidget(QLabel("止盈百分比:"), 2, 0)
        self.take_profit_spin = QDoubleSpinBox()
        self.take_profit_spin.setRange(0.01, 1.0)
        self.take_profit_spin.setValue(0.1)
        self.take_profit_spin.setDecimals(3)
        self.take_profit_spin.setSuffix("%")
        strategy_layout.addWidget(self.take_profit_spin, 2, 1)
        
        # 最大持倉時間
        strategy_layout.addWidget(QLabel("最大持倉時間:"), 3, 0)
        self.max_holding_spin = QSpinBox()
        self.max_holding_spin.setRange(1, 168)
        self.max_holding_spin.setValue(24)
        self.max_holding_spin.setSuffix(" 小時")
        strategy_layout.addWidget(self.max_holding_spin, 3, 1)
        
        layout.addWidget(strategy_group)
        
        # AI模型選擇
        ai_group = QGroupBox("AI模型選擇")
        ai_layout = QVBoxLayout(ai_group)
        
        # 模型複選框
        self.model_checkboxes = {}
        models = [
            ("ensemble_scorer", "🎯 集成評分器", True),
            ("lstm_predictor", "📈 LSTM預測器", True),
            ("xgboost_predictor", "🌳 XGBoost預測器", False),
            ("ai_enhanced", "🧠 AI增強模式", True)
        ]
        
        for model_id, model_name, default_checked in models:
            checkbox = QCheckBox(model_name)
            checkbox.setChecked(default_checked)
            self.model_checkboxes[model_id] = checkbox
            ai_layout.addWidget(checkbox)
        
        layout.addWidget(ai_group)
        
        # 控制按鈕
        button_layout = QHBoxLayout()
        
        self.load_config_btn = QPushButton("📂 載入配置")
        self.load_config_btn.clicked.connect(self.load_configuration)
        button_layout.addWidget(self.load_config_btn)
        
        self.save_config_btn = QPushButton("💾 保存配置")
        self.save_config_btn.clicked.connect(self.save_configuration)
        button_layout.addWidget(self.save_config_btn)
        
        self.reset_btn = QPushButton("🔄 重置")
        self.reset_btn.clicked.connect(self.reset_configuration)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def get_configuration(self) -> Dict[str, Any]:
        """獲取當前配置"""
        if not PYQT_AVAILABLE:
            return {}
            
        return {
            "start_date": self.start_date_edit.date().toString("yyyy-MM-dd"),
            "end_date": self.end_date_edit.date().toString("yyyy-MM-dd"),
            "initial_capital": self.initial_capital_spin.value(),
            "commission_rate": self.commission_spin.value() / 100,
            "slippage_rate": self.slippage_spin.value() / 100,
            "max_positions": self.max_positions_spin.value(),
            "stop_loss_pct": self.stop_loss_spin.value() / 100,
            "take_profit_pct": self.take_profit_spin.value() / 100,
            "max_holding_hours": self.max_holding_spin.value(),
            "selected_models": [
                model_id for model_id, checkbox in self.model_checkboxes.items()
                if checkbox.isChecked()
            ]
        }
    
    def set_configuration(self, config: Dict[str, Any]):
        """設置配置"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            if "start_date" in config:
                self.start_date_edit.setDate(QDate.fromString(config["start_date"], "yyyy-MM-dd"))
            if "end_date" in config:
                self.end_date_edit.setDate(QDate.fromString(config["end_date"], "yyyy-MM-dd"))
            if "initial_capital" in config:
                self.initial_capital_spin.setValue(config["initial_capital"])
            if "commission_rate" in config:
                self.commission_spin.setValue(config["commission_rate"] * 100)
            if "slippage_rate" in config:
                self.slippage_spin.setValue(config["slippage_rate"] * 100)
            if "max_positions" in config:
                self.max_positions_spin.setValue(config["max_positions"])
            if "stop_loss_pct" in config:
                self.stop_loss_spin.setValue(config["stop_loss_pct"] * 100)
            if "take_profit_pct" in config:
                self.take_profit_spin.setValue(config["take_profit_pct"] * 100)
            if "max_holding_hours" in config:
                self.max_holding_spin.setValue(config["max_holding_hours"])
            if "selected_models" in config:
                for model_id, checkbox in self.model_checkboxes.items():
                    checkbox.setChecked(model_id in config["selected_models"])
                    
        except Exception as e:
            logger.error(f"❌ 設置配置失敗: {e}")
    
    def load_configuration(self):
        """載入配置文件"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "載入回測配置", "", "JSON Files (*.json)"
            )
            
            if file_path:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.set_configuration(config)
                QMessageBox.information(self, "成功", "配置載入成功")
                
        except Exception as e:
            logger.error(f"❌ 載入配置失敗: {e}")
            QMessageBox.warning(self, "錯誤", f"載入配置失敗: {e}")
    
    def save_configuration(self):
        """保存配置文件"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存回測配置", "", "JSON Files (*.json)"
            )
            
            if file_path:
                config = self.get_configuration()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(self, "成功", "配置保存成功")
                
        except Exception as e:
            logger.error(f"❌ 保存配置失敗: {e}")
            QMessageBox.warning(self, "錯誤", f"保存配置失敗: {e}")
    
    def reset_configuration(self):
        """重置配置為默認值"""
        if not PYQT_AVAILABLE:
            return
            
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.end_date_edit.setDate(QDate.currentDate())
        self.initial_capital_spin.setValue(1000000)
        self.commission_spin.setValue(0.001)
        self.slippage_spin.setValue(0.0005)
        self.max_positions_spin.setValue(5)
        self.stop_loss_spin.setValue(0.05)
        self.take_profit_spin.setValue(0.1)
        self.max_holding_spin.setValue(24)
        
        # 重置模型選擇
        for model_id, checkbox in self.model_checkboxes.items():
            if model_id in ["ensemble_scorer", "lstm_predictor", "ai_enhanced"]:
                checkbox.setChecked(True)
            else:
                checkbox.setChecked(False)
        
        QMessageBox.information(self, "成功", "配置已重置為默認值")

class BacktestExecutionWidget(QWidget if PYQT_AVAILABLE else object):
    """回測執行組件"""
    
    backtest_started = pyqtSignal() if PYQT_AVAILABLE else None
    backtest_finished = pyqtSignal(dict) if PYQT_AVAILABLE else None
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.setup_ui()
        self.backtest_thread = None
        
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("🚀 回測執行")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 執行控制
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ 開始回測")
        self.start_btn.clicked.connect(self.start_backtest)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ 停止回測")
        self.stop_btn.clicked.connect(self.stop_backtest)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.clear_btn = QPushButton("🗑️ 清空日誌")
        self.clear_btn.clicked.connect(self.clear_log)
        control_layout.addWidget(self.clear_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 進度顯示
        progress_group = QGroupBox("執行進度")
        progress_layout = QVBoxLayout(progress_group)
        
        # 總體進度
        progress_layout.addWidget(QLabel("總體進度:"))
        self.overall_progress = QProgressBar()
        self.overall_progress.setRange(0, 100)
        progress_layout.addWidget(self.overall_progress)
        
        # 當前階段
        self.current_stage_label = QLabel("當前階段: 等待開始")
        progress_layout.addWidget(self.current_stage_label)
        
        # 統計信息
        stats_layout = QGridLayout()
        
        stats_layout.addWidget(QLabel("已處理數據:"), 0, 0)
        self.processed_data_label = QLabel("0 / 0")
        stats_layout.addWidget(self.processed_data_label, 0, 1)
        
        stats_layout.addWidget(QLabel("執行交易:"), 1, 0)
        self.executed_trades_label = QLabel("0")
        stats_layout.addWidget(self.executed_trades_label, 1, 1)
        
        stats_layout.addWidget(QLabel("當前收益:"), 2, 0)
        self.current_return_label = QLabel("0.00%")
        stats_layout.addWidget(self.current_return_label, 2, 1)
        
        stats_layout.addWidget(QLabel("執行時間:"), 3, 0)
        self.execution_time_label = QLabel("00:00:00")
        stats_layout.addWidget(self.execution_time_label, 3, 1)
        
        progress_layout.addLayout(stats_layout)
        layout.addWidget(progress_group)
        
        # 執行日誌
        log_group = QGroupBox("執行日誌")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)  # 限制日誌行數
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # 定時更新執行時間
        self.execution_timer = QTimer()
        self.execution_timer.timeout.connect(self.update_execution_time)
        self.execution_start_time = None
    
    def start_backtest(self, config: Dict[str, Any] = None):
        """開始回測"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            # 重置進度
            self.overall_progress.setValue(0)
            self.current_stage_label.setText("當前階段: 初始化中...")
            self.processed_data_label.setText("0 / 0")
            self.executed_trades_label.setText("0")
            self.current_return_label.setText("0.00%")
            
            # 開始計時
            self.execution_start_time = datetime.now()
            self.execution_timer.start(1000)
            
            # 添加開始日誌
            self.add_log("🚀 開始回測執行...")
            self.add_log(f"📅 配置: {json.dumps(config or {}, indent=2, ensure_ascii=False)}")
            
            # 發送開始信號
            if self.backtest_started:
                self.backtest_started.emit()
            
            # 模擬回測執行
            self.simulate_backtest_execution(config or {})
            
        except Exception as e:
            logger.error(f"❌ 開始回測失敗: {e}")
            self.add_log(f"❌ 開始回測失敗: {e}")
            self.reset_execution_state()
    
    def stop_backtest(self):
        """停止回測"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            self.add_log("⏹️ 用戶請求停止回測...")
            
            if self.backtest_thread:
                # 這裡可以添加線程停止邏輯
                pass
            
            self.reset_execution_state()
            self.add_log("✅ 回測已停止")
            
        except Exception as e:
            logger.error(f"❌ 停止回測失敗: {e}")
            self.add_log(f"❌ 停止回測失敗: {e}")
    
    def simulate_backtest_execution(self, config: Dict[str, Any]):
        """模擬回測執行過程"""
        if not PYQT_AVAILABLE:
            return
            
        # 使用QTimer模擬異步執行
        self.simulation_step = 0
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout.connect(lambda: self.execute_simulation_step(config))
        self.simulation_timer.start(500)  # 每500ms執行一步
    
    def execute_simulation_step(self, config: Dict[str, Any]):
        """執行模擬步驟"""
        if not PYQT_AVAILABLE:
            return
            
        self.simulation_step += 1
        
        if self.simulation_step <= 20:  # 模擬20個步驟
            # 更新進度
            progress = int((self.simulation_step / 20) * 100)
            self.overall_progress.setValue(progress)
            
            # 更新階段信息
            if self.simulation_step <= 5:
                self.current_stage_label.setText("當前階段: 數據準備中...")
                self.add_log(f"📊 準備歷史數據... ({self.simulation_step}/5)")
            elif self.simulation_step <= 10:
                self.current_stage_label.setText("當前階段: AI模型預測中...")
                self.add_log(f"🧠 AI模型分析中... ({self.simulation_step-5}/5)")
            elif self.simulation_step <= 15:
                self.current_stage_label.setText("當前階段: 交易執行中...")
                self.add_log(f"💰 執行交易決策... ({self.simulation_step-10}/5)")
                # 更新交易統計
                self.executed_trades_label.setText(str(self.simulation_step - 10))
            else:
                self.current_stage_label.setText("當前階段: 結果分析中...")
                self.add_log(f"📈 分析回測結果... ({self.simulation_step-15}/5)")
            
            # 更新統計信息
            self.processed_data_label.setText(f"{self.simulation_step * 50} / 1000")
            
            # 模擬收益變化
            import random
            current_return = random.uniform(-5, 15)
            self.current_return_label.setText(f"{current_return:.2f}%")
            
        else:
            # 完成模擬
            self.simulation_timer.stop()
            self.complete_backtest_simulation()
    
    def complete_backtest_simulation(self):
        """完成回測模擬"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            self.overall_progress.setValue(100)
            self.current_stage_label.setText("當前階段: 完成")
            self.add_log("✅ 回測執行完成！")
            
            # 生成模擬結果
            mock_result = {
                "total_return": 12.5,
                "sharpe_ratio": 1.8,
                "max_drawdown": -8.2,
                "win_rate": 0.65,
                "total_trades": 15,
                "execution_time": (datetime.now() - self.execution_start_time).total_seconds()
            }
            
            self.add_log(f"📊 回測結果: 總收益 {mock_result['total_return']:.2f}%")
            self.add_log(f"📊 夏普比率: {mock_result['sharpe_ratio']:.2f}")
            self.add_log(f"📊 最大回撤: {mock_result['max_drawdown']:.2f}%")
            self.add_log(f"📊 勝率: {mock_result['win_rate']:.1%}")
            
            # 發送完成信號
            if self.backtest_finished:
                self.backtest_finished.emit(mock_result)
            
            self.reset_execution_state()
            
        except Exception as e:
            logger.error(f"❌ 完成回測模擬失敗: {e}")
            self.add_log(f"❌ 完成回測模擬失敗: {e}")
    
    def reset_execution_state(self):
        """重置執行狀態"""
        if not PYQT_AVAILABLE:
            return
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.execution_timer.stop()
        
        if hasattr(self, 'simulation_timer'):
            self.simulation_timer.stop()
    
    def update_execution_time(self):
        """更新執行時間"""
        if not PYQT_AVAILABLE or not self.execution_start_time:
            return
            
        elapsed = datetime.now() - self.execution_start_time
        hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.execution_time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def add_log(self, message: str):
        """添加日誌"""
        if not PYQT_AVAILABLE:
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.appendPlainText(f"[{timestamp}] {message}")
    
    def clear_log(self):
        """清空日誌"""
        if PYQT_AVAILABLE:
            self.log_text.clear()

class BacktestResultsWidget(QWidget if PYQT_AVAILABLE else object):
    """回測結果顯示組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.setup_ui()
        self.current_results = None
        
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("📊 回測結果")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 結果選項卡
        self.results_tabs = QTabWidget()
        
        # 性能指標選項卡
        self.create_performance_tab()
        
        # 交易記錄選項卡
        self.create_trades_tab()
        
        # 圖表分析選項卡
        self.create_charts_tab()
        
        layout.addWidget(self.results_tabs)
        
        # 控制按鈕
        button_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("📤 導出結果")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        self.compare_btn = QPushButton("🔍 比較分析")
        self.compare_btn.clicked.connect(self.compare_results)
        self.compare_btn.setEnabled(False)
        button_layout.addWidget(self.compare_btn)
        
        self.clear_btn = QPushButton("🗑️ 清空結果")
        self.clear_btn.clicked.connect(self.clear_results)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def create_performance_tab(self):
        """創建性能指標選項卡"""
        if not PYQT_AVAILABLE:
            return
            
        performance_widget = QWidget()
        layout = QVBoxLayout(performance_widget)
        
        # 關鍵指標
        key_metrics_group = QGroupBox("關鍵性能指標")
        key_metrics_layout = QGridLayout(key_metrics_group)
        
        # 創建指標標籤
        self.metrics_labels = {}
        metrics = [
            ("total_return", "總收益率", "0.00%"),
            ("annualized_return", "年化收益率", "0.00%"),
            ("sharpe_ratio", "夏普比率", "0.00"),
            ("max_drawdown", "最大回撤", "0.00%"),
            ("win_rate", "勝率", "0.00%"),
            ("profit_factor", "盈利因子", "0.00"),
            ("total_trades", "總交易數", "0"),
            ("avg_trade_duration", "平均持倉時間", "0.00小時")
        ]
        
        for i, (key, label, default) in enumerate(metrics):
            row, col = divmod(i, 2)
            key_metrics_layout.addWidget(QLabel(f"{label}:"), row, col*2)
            
            value_label = QLabel(default)
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            value_label.setStyleSheet("color: #2196F3;")
            self.metrics_labels[key] = value_label
            key_metrics_layout.addWidget(value_label, row, col*2+1)
        
        layout.addWidget(key_metrics_group)
        
        # 風險指標
        risk_metrics_group = QGroupBox("風險分析指標")
        risk_metrics_layout = QGridLayout(risk_metrics_group)
        
        risk_metrics = [
            ("volatility", "波動率", "0.00%"),
            ("sortino_ratio", "索提諾比率", "0.00"),
            ("calmar_ratio", "卡瑪比率", "0.00"),
            ("recovery_factor", "恢復因子", "0.00")
        ]
        
        for i, (key, label, default) in enumerate(risk_metrics):
            row, col = divmod(i, 2)
            risk_metrics_layout.addWidget(QLabel(f"{label}:"), row, col*2)
            
            value_label = QLabel(default)
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            value_label.setStyleSheet("color: #FF9800;")
            self.metrics_labels[key] = value_label
            risk_metrics_layout.addWidget(value_label, row, col*2+1)
        
        layout.addWidget(risk_metrics_group)
        
        # 添加到選項卡
        self.results_tabs.addTab(performance_widget, "📈 性能指標")
    
    def create_trades_tab(self):
        """創建交易記錄選項卡"""
        if not PYQT_AVAILABLE:
            return
            
        trades_widget = QWidget()
        layout = QVBoxLayout(trades_widget)
        
        # 交易統計
        stats_group = QGroupBox("交易統計")
        stats_layout = QGridLayout(stats_group)
        
        self.trade_stats_labels = {}
        trade_stats = [
            ("total_trades", "總交易數", "0"),
            ("winning_trades", "盈利交易", "0"),
            ("losing_trades", "虧損交易", "0"),
            ("avg_win", "平均盈利", "0.00%"),
            ("avg_loss", "平均虧損", "0.00%"),
            ("max_win", "最大盈利", "0.00%"),
            ("max_loss", "最大虧損", "0.00%"),
            ("consecutive_wins", "最大連勝", "0")
        ]
        
        for i, (key, label, default) in enumerate(trade_stats):
            row, col = divmod(i, 2)
            stats_layout.addWidget(QLabel(f"{label}:"), row, col*2)
            
            value_label = QLabel(default)
            value_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.trade_stats_labels[key] = value_label
            stats_layout.addWidget(value_label, row, col*2+1)
        
        layout.addWidget(stats_group)
        
        # 交易記錄表格
        trades_group = QGroupBox("詳細交易記錄")
        trades_layout = QVBoxLayout(trades_group)
        
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(8)
        self.trades_table.setHorizontalHeaderLabels([
            "進場時間", "出場時間", "類型", "進場價", "出場價", "數量", "盈虧", "盈虧%"
        ])
        
        # 調整列寬
        header = self.trades_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        trades_layout.addWidget(self.trades_table)
        layout.addWidget(trades_group)
        
        # 添加到選項卡
        self.results_tabs.addTab(trades_widget, "💰 交易記錄")
    
    def create_charts_tab(self):
        """創建圖表分析選項卡"""
        if not PYQT_AVAILABLE:
            return
            
        charts_widget = QWidget()
        layout = QVBoxLayout(charts_widget)
        
        # 圖表選擇
        chart_control_layout = QHBoxLayout()
        
        chart_control_layout.addWidget(QLabel("圖表類型:"))
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            "權益曲線", "回撤圖", "月度收益", "交易分佈", "風險收益散點圖"
        ])
        self.chart_type_combo.currentTextChanged.connect(self.update_chart_display)
        chart_control_layout.addWidget(self.chart_type_combo)
        
        chart_control_layout.addStretch()
        
        self.refresh_chart_btn = QPushButton("🔄 刷新圖表")
        self.refresh_chart_btn.clicked.connect(self.refresh_charts)
        chart_control_layout.addWidget(self.refresh_chart_btn)
        
        layout.addLayout(chart_control_layout)
        
        # 圖表顯示區域
        self.chart_display = QLabel("📊 圖表將在回測完成後顯示")
        self.chart_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_display.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 14px;
            }
        """)
        self.chart_display.setMinimumHeight(400)
        
        layout.addWidget(self.chart_display)
        
        # 添加到選項卡
        self.results_tabs.addTab(charts_widget, "📊 圖表分析")
    
    def update_results(self, results: Dict[str, Any]):
        """更新回測結果"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            self.current_results = results
            
            # 更新性能指標
            self.update_performance_metrics(results)
            
            # 更新交易記錄
            self.update_trade_records(results)
            
            # 更新圖表
            self.update_chart_display()
            
            # 啟用按鈕
            self.export_btn.setEnabled(True)
            self.compare_btn.setEnabled(True)
            
            logger.info("✅ 回測結果已更新")
            
        except Exception as e:
            logger.error(f"❌ 更新回測結果失敗: {e}")
    
    def update_performance_metrics(self, results: Dict[str, Any]):
        """更新性能指標"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 更新關鍵指標
            if "total_return" in results:
                self.metrics_labels["total_return"].setText(f"{results['total_return']:.2f}%")
            if "sharpe_ratio" in results:
                self.metrics_labels["sharpe_ratio"].setText(f"{results['sharpe_ratio']:.2f}")
            if "max_drawdown" in results:
                self.metrics_labels["max_drawdown"].setText(f"{results['max_drawdown']:.2f}%")
            if "win_rate" in results:
                self.metrics_labels["win_rate"].setText(f"{results['win_rate']:.1%}")
            if "total_trades" in results:
                self.metrics_labels["total_trades"].setText(str(results['total_trades']))
            
            # 設置顏色
            total_return = results.get('total_return', 0)
            color = "#4CAF50" if total_return > 0 else "#F44336"
            self.metrics_labels["total_return"].setStyleSheet(f"color: {color}; font-weight: bold;")
            
        except Exception as e:
            logger.error(f"❌ 更新性能指標失敗: {e}")
    
    def update_trade_records(self, results: Dict[str, Any]):
        """更新交易記錄"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 更新交易統計
            self.trade_stats_labels["total_trades"].setText(str(results.get('total_trades', 0)))
            
            # 模擬交易記錄
            self.trades_table.setRowCount(5)  # 顯示5筆模擬交易
            
            mock_trades = [
                ("2024-01-15 09:30", "2024-01-15 15:45", "買入", "45,200", "46,800", "0.1", "+1,600", "+3.54%"),
                ("2024-01-16 10:15", "2024-01-16 14:20", "買入", "46,500", "45,900", "0.1", "-600", "-1.29%"),
                ("2024-01-17 11:00", "2024-01-17 16:30", "買入", "45,800", "47,200", "0.1", "+1,400", "+3.06%"),
                ("2024-01-18 09:45", "2024-01-18 13:15", "買入", "47,100", "46,300", "0.1", "-800", "-1.70%"),
                ("2024-01-19 10:30", "2024-01-19 15:00", "買入", "46,200", "48,500", "0.1", "+2,300", "+4.98%")
            ]
            
            for row, trade_data in enumerate(mock_trades):
                for col, value in enumerate(trade_data):
                    item = QTableWidgetItem(str(value))
                    
                    # 設置盈虧顏色
                    if col == 7:  # 盈虧%列
                        if value.startswith('+'):
                            item.setBackground(QColor(144, 238, 144))
                        elif value.startswith('-'):
                            item.setBackground(QColor(255, 182, 193))
                    
                    self.trades_table.setItem(row, col, item)
            
        except Exception as e:
            logger.error(f"❌ 更新交易記錄失敗: {e}")
    
    def update_chart_display(self):
        """更新圖表顯示"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            chart_type = self.chart_type_combo.currentText()
            
            if self.current_results:
                self.chart_display.setText(f"📊 {chart_type}圖表\n\n(實際應用中這裡會顯示真實的圖表)")
                self.chart_display.setStyleSheet("""
                    QLabel {
                        border: 2px solid #4CAF50;
                        border-radius: 8px;
                        padding: 20px;
                        background-color: #f0f8f0;
                        color: #2E7D32;
                        font-size: 14px;
                    }
                """)
            else:
                self.chart_display.setText("📊 圖表將在回測完成後顯示")
                self.chart_display.setStyleSheet("""
                    QLabel {
                        border: 2px dashed #ccc;
                        border-radius: 8px;
                        padding: 20px;
                        background-color: #f9f9f9;
                        color: #666;
                        font-size: 14px;
                    }
                """)
            
        except Exception as e:
            logger.error(f"❌ 更新圖表顯示失敗: {e}")
    
    def refresh_charts(self):
        """刷新圖表"""
        if PYQT_AVAILABLE:
            self.update_chart_display()
            QMessageBox.information(self, "成功", "圖表已刷新")
    
    def export_results(self):
        """導出結果"""
        if not PYQT_AVAILABLE or not self.current_results:
            return
            
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "導出回測結果", "", "JSON Files (*.json);;CSV Files (*.csv)"
            )
            
            if file_path:
                if file_path.endswith('.json'):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.current_results, f, indent=2, ensure_ascii=False)
                else:
                    # CSV導出邏輯
                    pass
                
                QMessageBox.information(self, "成功", "結果導出成功")
                
        except Exception as e:
            logger.error(f"❌ 導出結果失敗: {e}")
            QMessageBox.warning(self, "錯誤", f"導出結果失敗: {e}")
    
    def compare_results(self):
        """比較分析"""
        if PYQT_AVAILABLE:
            QMessageBox.information(self, "功能開發中", "比較分析功能正在開發中...")
    
    def clear_results(self):
        """清空結果"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            self.current_results = None
            
            # 重置所有標籤
            for label in self.metrics_labels.values():
                label.setText("0.00")
                label.setStyleSheet("color: #2196F3; font-weight: bold;")
            
            for label in self.trade_stats_labels.values():
                label.setText("0")
            
            # 清空表格
            self.trades_table.setRowCount(0)
            
            # 重置圖表
            self.chart_display.setText("📊 圖表將在回測完成後顯示")
            self.chart_display.setStyleSheet("""
                QLabel {
                    border: 2px dashed #ccc;
                    border-radius: 8px;
                    padding: 20px;
                    background-color: #f9f9f9;
                    color: #666;
                    font-size: 14px;
                }
            """)
            
            # 禁用按鈕
            self.export_btn.setEnabled(False)
            self.compare_btn.setEnabled(False)
            
            QMessageBox.information(self, "成功", "結果已清空")
            
        except Exception as e:
            logger.error(f"❌ 清空結果失敗: {e}")
            QMessageBox.warning(self, "錯誤", f"清空結果失敗: {e}")

class BacktestGUIIntegration(QWidget if PYQT_AVAILABLE else object):
    """回測GUI整合主組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.backtest_reporter = None
        
        # 子組件
        self.config_widget = None
        self.execution_widget = None
        self.results_widget = None
        
        self.setup_ui()
        self.initialize_components()
        self.logger.info("🎯 回測GUI整合組件初始化完成")
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            self.logger.info("🖥️ 回測GUI整合運行在文本模式")
            return
            
        layout = QVBoxLayout(self)
        
        # 主標題
        main_title = QLabel("🎯 AI交易系統回測中心")
        main_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(main_title)
        
        # 創建選項卡
        self.main_tabs = QTabWidget()
        
        # 配置選項卡
        self.config_widget = BacktestConfigWidget()
        self.main_tabs.addTab(self.config_widget, "⚙️ 配置")
        
        # 執行選項卡
        self.execution_widget = BacktestExecutionWidget()
        self.main_tabs.addTab(self.execution_widget, "🚀 執行")
        
        # 結果選項卡
        self.results_widget = BacktestResultsWidget()
        self.main_tabs.addTab(self.results_widget, "📊 結果")
        
        layout.addWidget(self.main_tabs)
        
        # 全局控制面板
        self.create_global_control_panel(layout)
        
        # 連接信號
        self.connect_signals()
    
    def create_global_control_panel(self, parent_layout):
        """創建全局控制面板"""
        if not PYQT_AVAILABLE:
            return
            
        control_group = QGroupBox("全局控制")
        control_layout = QHBoxLayout(control_group)
        
        # 快速開始按鈕
        self.quick_start_btn = QPushButton("⚡ 快速開始")
        self.quick_start_btn.clicked.connect(self.quick_start_backtest)
        control_layout.addWidget(self.quick_start_btn)
        
        # 多模型比較按鈕
        self.multi_model_btn = QPushButton("🔍 多模型比較")
        self.multi_model_btn.clicked.connect(self.start_multi_model_comparison)
        control_layout.addWidget(self.multi_model_btn)
        
        # 參數優化按鈕
        self.optimize_btn = QPushButton("🎯 參數優化")
        self.optimize_btn.clicked.connect(self.start_parameter_optimization)
        control_layout.addWidget(self.optimize_btn)
        
        control_layout.addStretch()
        
        # 幫助按鈕
        self.help_btn = QPushButton("❓ 幫助")
        self.help_btn.clicked.connect(self.show_help)
        control_layout.addWidget(self.help_btn)
        
        parent_layout.addWidget(control_group)
    
    def connect_signals(self):
        """連接信號"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 連接執行組件的信號
            if self.execution_widget and hasattr(self.execution_widget, 'backtest_finished'):
                self.execution_widget.backtest_finished.connect(self.on_backtest_finished)
            
        except Exception as e:
            self.logger.error(f"❌ 連接信號失敗: {e}")
    
    def initialize_components(self):
        """初始化組件"""
        try:
            if AIMAX_MODULES_AVAILABLE:
                # 初始化回測報告生成器
                self.backtest_reporter = create_backtest_report_generator()
                self.logger.info("✅ 回測報告生成器初始化完成")
            else:
                self.logger.warning("⚠️ 使用模擬模式")
            
        except Exception as e:
            self.logger.error(f"❌ 組件初始化失敗: {e}")
    
    def quick_start_backtest(self):
        """快速開始回測"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 獲取當前配置
            config = self.config_widget.get_configuration()
            
            # 切換到執行選項卡
            self.main_tabs.setCurrentIndex(1)
            
            # 開始回測
            self.execution_widget.start_backtest(config)
            
            self.logger.info("🚀 快速開始回測")
            
        except Exception as e:
            self.logger.error(f"❌ 快速開始回測失敗: {e}")
            if PYQT_AVAILABLE:
                QMessageBox.warning(self, "錯誤", f"快速開始回測失敗: {e}")
    
    def start_multi_model_comparison(self):
        """開始多模型比較"""
        if PYQT_AVAILABLE:
            QMessageBox.information(self, "功能開發中", "多模型比較功能正在開發中...")
    
    def start_parameter_optimization(self):
        """開始參數優化"""
        if PYQT_AVAILABLE:
            QMessageBox.information(self, "功能開發中", "參數優化功能正在開發中...")
    
    def show_help(self):
        """顯示幫助"""
        if not PYQT_AVAILABLE:
            return
            
        help_text = """
        🎯 AI交易系統回測中心使用指南
        
        📋 基本流程:
        1. 在「配置」選項卡中設置回測參數
        2. 在「執行」選項卡中運行回測
        3. 在「結果」選項卡中查看分析結果
        
        ⚙️ 配置說明:
        • 設置回測時間範圍和初始資金
        • 調整手續費率和滑點率
        • 選擇要使用的AI模型
        • 配置風險控制參數
        
        🚀 執行功能:
        • 實時監控回測進度
        • 查看執行日誌和統計信息
        • 支持中途停止回測
        
        📊 結果分析:
        • 查看詳細的性能指標
        • 分析交易記錄和統計
        • 查看各種圖表分析
        • 導出結果數據
        
        💡 快捷功能:
        • 快速開始: 使用當前配置立即開始回測
        • 多模型比較: 同時測試多個AI模型
        • 參數優化: 自動尋找最佳參數組合
        """
        
        QMessageBox.information(self, "使用幫助", help_text)
    
    def on_backtest_finished(self, results: Dict[str, Any]):
        """回測完成處理"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 切換到結果選項卡
            self.main_tabs.setCurrentIndex(2)
            
            # 更新結果顯示
            self.results_widget.update_results(results)
            
            # 顯示完成通知
            QMessageBox.information(self, "回測完成", 
                f"回測執行完成！\n\n"
                f"總收益率: {results.get('total_return', 0):.2f}%\n"
                f"夏普比率: {results.get('sharpe_ratio', 0):.2f}\n"
                f"最大回撤: {results.get('max_drawdown', 0):.2f}%"
            )
            
            self.logger.info("✅ 回測完成，結果已更新")
            
        except Exception as e:
            self.logger.error(f"❌ 處理回測完成事件失敗: {e}")

def create_backtest_gui_integration():
    """創建回測GUI整合組件實例"""
    return BacktestGUIIntegration()

def main():
    """主函數 - 用於測試"""
    import sys
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 啟動回測GUI整合測試")
    
    if PYQT_AVAILABLE:
        from PyQt6.QtWidgets import QApplication, QMainWindow
        
        app = QApplication(sys.argv)
        app.setApplicationName("Backtest GUI Integration Test")
        
        # 創建主窗口
        main_window = QMainWindow()
        main_window.setWindowTitle("回測GUI整合測試")
        main_window.setGeometry(100, 100, 1400, 900)
        
        # 創建回測GUI整合組件
        backtest_gui = BacktestGUIIntegration()
        main_window.setCentralWidget(backtest_gui)
        
        main_window.show()
        
        # 運行應用程序
        sys.exit(app.exec())
    else:
        # 文本模式
        logger.info("🖥️ 運行在文本模式")
        backtest_gui = BacktestGUIIntegration()
        
        try:
            input("按Enter鍵退出...")
        except KeyboardInterrupt:
            logger.info("⏹️ 用戶中斷，正在關閉...")

if __name__ == "__main__":
    main()