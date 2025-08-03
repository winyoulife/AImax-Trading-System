#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略控制界面 - 任務7.3實現
實現多交易對策略的啟停控制和策略參數的動態調整界面
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
        QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
        QGroupBox, QProgressBar, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox,
        QTextEdit, QScrollArea, QFrame, QSplitter, QSlider, QApplication,
        QMainWindow, QStatusBar, QMessageBox, QDialog, QDialogButtonBox,
        QFormLayout, QLineEdit, QTreeWidget, QTreeWidgetItem
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
    from PyQt5.QtGui import QFont, QColor, QIcon
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt5 未安裝，將使用文本模式")

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    """策略類型"""
    GRID = "grid"                    # 網格交易
    DCA = "dca"                      # 定投策略
    ARBITRAGE = "arbitrage"          # 套利策略
    AI_SIGNAL = "ai_signal"          # AI信號策略
    CUSTOM = "custom"                # 自定義策略

class StrategyStatus(Enum):
    """策略狀態"""
    STOPPED = "stopped"              # 已停止
    RUNNING = "running"              # 運行中
    PAUSED = "paused"                # 已暫停
    ERROR = "error"                  # 錯誤狀態
    STARTING = "starting"            # 啟動中
    STOPPING = "stopping"            # 停止中

@dataclass
class StrategyConfig:
    """策略配置"""
    strategy_id: str
    pair: str
    strategy_type: StrategyType
    name: str
    description: str = ""
    
    # 通用參數
    enabled: bool = False
    auto_start: bool = False
    max_position_size: float = 0.1
    risk_level: float = 0.5
    
    # 網格策略參數
    grid_upper_price: float = 0.0
    grid_lower_price: float = 0.0
    grid_levels: int = 10
    grid_amount_per_level: float = 0.01
    
    # DCA策略參數
    dca_interval_hours: int = 24
    dca_amount: float = 1000.0
    dca_price_drop_threshold: float = 0.05
    
    # AI策略參數
    ai_confidence_threshold: float = 0.7
    ai_signal_timeout_minutes: int = 30
    
    # 風險控制參數
    stop_loss_percent: float = 0.1
    take_profit_percent: float = 0.2
    max_drawdown_percent: float = 0.15
    
    # 時間參數
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class StrategyState:
    """策略運行狀態"""
    strategy_id: str
    pair: str
    status: StrategyStatus
    
    # 運行統計
    start_time: Optional[datetime] = None
    last_signal_time: Optional[datetime] = None
    total_signals: int = 0
    executed_trades: int = 0
    pending_orders: int = 0
    
    # 績效統計
    total_pnl: float = 0.0
    win_rate: float = 0.0
    current_drawdown: float = 0.0
    
    # 錯誤信息
    last_error: str = ""
    error_count: int = 0
    
    # 更新時間
    last_update: datetime = field(default_factory=datetime.now)

class StrategyConfigDialog(QDialog if PYQT_AVAILABLE else object):
    """策略配置對話框"""
    
    def __init__(self, config: StrategyConfig = None, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        
        self.config = config or StrategyConfig(
            strategy_id="",
            pair="BTCTWD",
            strategy_type=StrategyType.GRID,
            name="新策略"
        )
        
        if PYQT_AVAILABLE:
            self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        if not PYQT_AVAILABLE:
            return
        
        self.setWindowTitle("策略配置")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # 基本信息
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit(self.config.name)
        self.pair_combo = QComboBox()
        self.pair_combo.addItems(["BTCTWD", "ETHTWD", "LTCTWD", "BCHTWD", "ADATWD", "DOTTWD"])
        self.pair_combo.setCurrentText(self.config.pair)
        
        self.strategy_type_combo = QComboBox()
        self.strategy_type_combo.addItems(["網格交易", "定投策略", "套利策略", "AI信號策略"])
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlainText(self.config.description)
        
        basic_layout.addRow("策略名稱:", self.name_edit)
        basic_layout.addRow("交易對:", self.pair_combo)
        basic_layout.addRow("策略類型:", self.strategy_type_combo)
        basic_layout.addRow("描述:", self.description_edit)
        
        layout.addWidget(basic_group)
        
        # 通用參數
        general_group = QGroupBox("通用參數")
        general_layout = QFormLayout(general_group)
        
        self.enabled_checkbox = QCheckBox()
        self.enabled_checkbox.setChecked(self.config.enabled)
        
        self.auto_start_checkbox = QCheckBox()
        self.auto_start_checkbox.setChecked(self.config.auto_start)
        
        self.max_position_spinbox = QDoubleSpinBox()
        self.max_position_spinbox.setRange(0.001, 1.0)
        self.max_position_spinbox.setDecimals(3)
        self.max_position_spinbox.setValue(self.config.max_position_size)
        
        self.risk_level_slider = QSlider(Qt.Horizontal)
        self.risk_level_slider.setRange(1, 10)
        self.risk_level_slider.setValue(int(self.config.risk_level * 10))
        self.risk_level_label = QLabel(f"{self.config.risk_level:.1f}")
        
        risk_layout = QHBoxLayout()
        risk_layout.addWidget(self.risk_level_slider)
        risk_layout.addWidget(self.risk_level_label)
        
        general_layout.addRow("啟用策略:", self.enabled_checkbox)
        general_layout.addRow("自動啟動:", self.auto_start_checkbox)
        general_layout.addRow("最大倉位:", self.max_position_spinbox)
        general_layout.addRow("風險等級:", risk_layout)
        
        layout.addWidget(general_group)
        
        # 策略特定參數
        self.strategy_params_group = QGroupBox("策略參數")
        self.strategy_params_layout = QFormLayout(self.strategy_params_group)
        
        self.create_strategy_params()
        layout.addWidget(self.strategy_params_group)
        
        # 風險控制參數
        risk_group = QGroupBox("風險控制")
        risk_layout = QFormLayout(risk_group)
        
        self.stop_loss_spinbox = QDoubleSpinBox()
        self.stop_loss_spinbox.setRange(0.01, 0.5)
        self.stop_loss_spinbox.setDecimals(3)
        self.stop_loss_spinbox.setValue(self.config.stop_loss_percent)
        self.stop_loss_spinbox.setSuffix("%")
        
        self.take_profit_spinbox = QDoubleSpinBox()
        self.take_profit_spinbox.setRange(0.01, 1.0)
        self.take_profit_spinbox.setDecimals(3)
        self.take_profit_spinbox.setValue(self.config.take_profit_percent)
        self.take_profit_spinbox.setSuffix("%")
        
        self.max_drawdown_spinbox = QDoubleSpinBox()
        self.max_drawdown_spinbox.setRange(0.05, 0.5)
        self.max_drawdown_spinbox.setDecimals(3)
        self.max_drawdown_spinbox.setValue(self.config.max_drawdown_percent)
        self.max_drawdown_spinbox.setSuffix("%")
        
        risk_layout.addRow("止損百分比:", self.stop_loss_spinbox)
        risk_layout.addRow("止盈百分比:", self.take_profit_spinbox)
        risk_layout.addRow("最大回撤:", self.max_drawdown_spinbox)
        
        layout.addWidget(risk_group)
        
        # 按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 連接信號
        self.risk_level_slider.valueChanged.connect(self.update_risk_level_label)
        self.strategy_type_combo.currentTextChanged.connect(self.on_strategy_type_changed)
    
    def create_strategy_params(self):
        """創建策略特定參數"""
        if not PYQT_AVAILABLE:
            return
        
        # 清空現有參數
        for i in reversed(range(self.strategy_params_layout.count())):
            self.strategy_params_layout.itemAt(i).widget().setParent(None)
        
        strategy_type = self.strategy_type_combo.currentText()
        
        if strategy_type == "網格交易":
            self.create_grid_params()
        elif strategy_type == "定投策略":
            self.create_dca_params()
        elif strategy_type == "AI信號策略":
            self.create_ai_params()
    
    def create_grid_params(self):
        """創建網格策略參數"""
        if not PYQT_AVAILABLE:
            return
        
        self.grid_upper_spinbox = QDoubleSpinBox()
        self.grid_upper_spinbox.setRange(1, 10000000)
        self.grid_upper_spinbox.setValue(self.config.grid_upper_price or 1600000)
        
        self.grid_lower_spinbox = QDoubleSpinBox()
        self.grid_lower_spinbox.setRange(1, 10000000)
        self.grid_lower_spinbox.setValue(self.config.grid_lower_price or 1400000)
        
        self.grid_levels_spinbox = QSpinBox()
        self.grid_levels_spinbox.setRange(3, 50)
        self.grid_levels_spinbox.setValue(self.config.grid_levels)
        
        self.grid_amount_spinbox = QDoubleSpinBox()
        self.grid_amount_spinbox.setRange(0.001, 1.0)
        self.grid_amount_spinbox.setDecimals(3)
        self.grid_amount_spinbox.setValue(self.config.grid_amount_per_level)
        
        self.strategy_params_layout.addRow("網格上限價格:", self.grid_upper_spinbox)
        self.strategy_params_layout.addRow("網格下限價格:", self.grid_lower_spinbox)
        self.strategy_params_layout.addRow("網格層數:", self.grid_levels_spinbox)
        self.strategy_params_layout.addRow("每層金額:", self.grid_amount_spinbox)
    
    def create_dca_params(self):
        """創建DCA策略參數"""
        if not PYQT_AVAILABLE:
            return
        
        self.dca_interval_spinbox = QSpinBox()
        self.dca_interval_spinbox.setRange(1, 168)  # 1小時到1週
        self.dca_interval_spinbox.setValue(self.config.dca_interval_hours)
        self.dca_interval_spinbox.setSuffix(" 小時")
        
        self.dca_amount_spinbox = QDoubleSpinBox()
        self.dca_amount_spinbox.setRange(100, 100000)
        self.dca_amount_spinbox.setValue(self.config.dca_amount)
        
        self.dca_threshold_spinbox = QDoubleSpinBox()
        self.dca_threshold_spinbox.setRange(0.01, 0.5)
        self.dca_threshold_spinbox.setDecimals(3)
        self.dca_threshold_spinbox.setValue(self.config.dca_price_drop_threshold)
        self.dca_threshold_spinbox.setSuffix("%")
        
        self.strategy_params_layout.addRow("投資間隔:", self.dca_interval_spinbox)
        self.strategy_params_layout.addRow("每次金額:", self.dca_amount_spinbox)
        self.strategy_params_layout.addRow("觸發跌幅:", self.dca_threshold_spinbox)
    
    def create_ai_params(self):
        """創建AI策略參數"""
        if not PYQT_AVAILABLE:
            return
        
        self.ai_confidence_spinbox = QDoubleSpinBox()
        self.ai_confidence_spinbox.setRange(0.1, 1.0)
        self.ai_confidence_spinbox.setDecimals(2)
        self.ai_confidence_spinbox.setValue(self.config.ai_confidence_threshold)
        
        self.ai_timeout_spinbox = QSpinBox()
        self.ai_timeout_spinbox.setRange(5, 180)
        self.ai_timeout_spinbox.setValue(self.config.ai_signal_timeout_minutes)
        self.ai_timeout_spinbox.setSuffix(" 分鐘")
        
        self.strategy_params_layout.addRow("AI信心度閾值:", self.ai_confidence_spinbox)
        self.strategy_params_layout.addRow("信號超時時間:", self.ai_timeout_spinbox)
    
    def update_risk_level_label(self, value):
        """更新風險等級標籤"""
        if PYQT_AVAILABLE:
            self.risk_level_label.setText(f"{value/10:.1f}")
    
    def on_strategy_type_changed(self):
        """策略類型改變事件"""
        self.create_strategy_params()
    
    def get_config(self) -> StrategyConfig:
        """獲取配置"""
        if not PYQT_AVAILABLE:
            return self.config
        
        # 更新基本信息
        self.config.name = self.name_edit.text()
        self.config.pair = self.pair_combo.currentText()
        self.config.description = self.description_edit.toPlainText()
        
        # 更新通用參數
        self.config.enabled = self.enabled_checkbox.isChecked()
        self.config.auto_start = self.auto_start_checkbox.isChecked()
        self.config.max_position_size = self.max_position_spinbox.value()
        self.config.risk_level = self.risk_level_slider.value() / 10.0
        
        # 更新策略特定參數
        strategy_type = self.strategy_type_combo.currentText()
        if strategy_type == "網格交易":
            self.config.strategy_type = StrategyType.GRID
            self.config.grid_upper_price = self.grid_upper_spinbox.value()
            self.config.grid_lower_price = self.grid_lower_spinbox.value()
            self.config.grid_levels = self.grid_levels_spinbox.value()
            self.config.grid_amount_per_level = self.grid_amount_spinbox.value()
        elif strategy_type == "定投策略":
            self.config.strategy_type = StrategyType.DCA
            self.config.dca_interval_hours = self.dca_interval_spinbox.value()
            self.config.dca_amount = self.dca_amount_spinbox.value()
            self.config.dca_price_drop_threshold = self.dca_threshold_spinbox.value()
        elif strategy_type == "AI信號策略":
            self.config.strategy_type = StrategyType.AI_SIGNAL
            self.config.ai_confidence_threshold = self.ai_confidence_spinbox.value()
            self.config.ai_signal_timeout_minutes = self.ai_timeout_spinbox.value()
        
        # 更新風險控制參數
        self.config.stop_loss_percent = self.stop_loss_spinbox.value()
        self.config.take_profit_percent = self.take_profit_spinbox.value()
        self.config.max_drawdown_percent = self.max_drawdown_spinbox.value()
        
        self.config.updated_at = datetime.now()
        
        return self.config

class StrategyControlWidget(QWidget if PYQT_AVAILABLE else object):
    """策略控制主組件"""
    
    if PYQT_AVAILABLE:
        strategy_started = pyqtSignal(str)  # strategy_id
        strategy_stopped = pyqtSignal(str)  # strategy_id
        strategy_configured = pyqtSignal(str)  # strategy_id
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        
        # 策略管理
        self.strategies: Dict[str, StrategyConfig] = {}
        self.strategy_states: Dict[str, StrategyState] = {}
        
        # 監控定時器
        self.update_timer = None
        
        if PYQT_AVAILABLE:
            self.init_ui()
            self.setup_timer()
            self.load_sample_strategies()
    
    def init_ui(self):
        """初始化UI"""
        if not PYQT_AVAILABLE:
            return
        
        layout = QVBoxLayout(self)
        
        # 標題
        title_label = QLabel("策略控制中心")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 工具欄
        toolbar_layout = QHBoxLayout()
        
        self.add_strategy_button = QPushButton("添加策略")
        self.start_all_button = QPushButton("啟動全部")
        self.stop_all_button = QPushButton("停止全部")
        self.refresh_button = QPushButton("刷新狀態")
        
        self.add_strategy_button.clicked.connect(self.add_strategy)
        self.start_all_button.clicked.connect(self.start_all_strategies)
        self.stop_all_button.clicked.connect(self.stop_all_strategies)
        self.refresh_button.clicked.connect(self.refresh_status)
        
        toolbar_layout.addWidget(self.add_strategy_button)
        toolbar_layout.addWidget(self.start_all_button)
        toolbar_layout.addWidget(self.stop_all_button)
        toolbar_layout.addWidget(self.refresh_button)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 策略表格
        self.strategy_table = QTableWidget()
        self.strategy_table.setColumnCount(10)
        self.strategy_table.setHorizontalHeaderLabels([
            "策略名稱", "交易對", "類型", "狀態", "運行時間", 
            "總盈虧", "勝率", "信號數", "操作", "配置"
        ])
        
        # 設置表格屬性
        self.strategy_table.setAlternatingRowColors(True)
        self.strategy_table.setSelectionBehavior(QTableWidget.SelectRows)
        header = self.strategy_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(self.strategy_table)
        
        # 狀態統計
        stats_layout = QHBoxLayout()
        
        self.total_strategies_label = QLabel("總策略: 0")
        self.running_strategies_label = QLabel("運行中: 0")
        self.total_pnl_label = QLabel("總盈虧: 0")
        self.avg_win_rate_label = QLabel("平均勝率: 0%")
        
        stats_layout.addWidget(self.total_strategies_label)
        stats_layout.addWidget(self.running_strategies_label)
        stats_layout.addWidget(self.total_pnl_label)
        stats_layout.addWidget(self.avg_win_rate_label)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
    
    def setup_timer(self):
        """設置定時器"""
        if not PYQT_AVAILABLE:
            return
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_strategy_states)
        self.update_timer.start(3000)  # 3秒更新間隔
    
    def load_sample_strategies(self):
        """加載示例策略"""
        try:
            # 創建示例策略
            sample_strategies = [
                StrategyConfig(
                    strategy_id="grid_btc_001",
                    pair="BTCTWD",
                    strategy_type=StrategyType.GRID,
                    name="BTC網格策略",
                    description="BTC網格交易策略",
                    enabled=True,
                    grid_upper_price=1600000,
                    grid_lower_price=1400000,
                    grid_levels=10,
                    grid_amount_per_level=0.01
                ),
                StrategyConfig(
                    strategy_id="dca_eth_001",
                    pair="ETHTWD",
                    strategy_type=StrategyType.DCA,
                    name="ETH定投策略",
                    description="ETH定期投資策略",
                    enabled=False,
                    dca_interval_hours=24,
                    dca_amount=5000,
                    dca_price_drop_threshold=0.05
                ),
                StrategyConfig(
                    strategy_id="ai_ltc_001",
                    pair="LTCTWD",
                    strategy_type=StrategyType.AI_SIGNAL,
                    name="LTC AI策略",
                    description="基於AI信號的LTC交易策略",
                    enabled=True,
                    ai_confidence_threshold=0.75,
                    ai_signal_timeout_minutes=30
                )
            ]
            
            for strategy in sample_strategies:
                self.strategies[strategy.strategy_id] = strategy
                
                # 創建對應的狀態
                state = StrategyState(
                    strategy_id=strategy.strategy_id,
                    pair=strategy.pair,
                    status=StrategyStatus.RUNNING if strategy.enabled else StrategyStatus.STOPPED
                )
                
                if strategy.enabled:
                    state.start_time = datetime.now() - timedelta(hours=2)
                    state.total_signals = 15
                    state.executed_trades = 8
                    state.total_pnl = 2500.0
                    state.win_rate = 0.625
                
                self.strategy_states[strategy.strategy_id] = state
            
            self.update_strategy_table()
            logger.info(f"✅ 加載了 {len(sample_strategies)} 個示例策略")
            
        except Exception as e:
            logger.error(f"❌ 加載示例策略失敗: {e}")
    
    def add_strategy(self):
        """添加新策略"""
        if not PYQT_AVAILABLE:
            return
        
        try:
            dialog = StrategyConfigDialog()
            if dialog.exec_() == QDialog.Accepted:
                config = dialog.get_config()
                config.strategy_id = f"{config.strategy_type.value}_{config.pair}_{len(self.strategies)+1:03d}"
                
                self.strategies[config.strategy_id] = config
                
                # 創建策略狀態
                state = StrategyState(
                    strategy_id=config.strategy_id,
                    pair=config.pair,
                    status=StrategyStatus.STOPPED
                )
                self.strategy_states[config.strategy_id] = state
                
                self.update_strategy_table()
                
                if self.strategy_configured:
                    self.strategy_configured.emit(config.strategy_id)
                
                logger.info(f"✅ 添加新策略: {config.name}")
                
        except Exception as e:
            logger.error(f"❌ 添加策略失敗: {e}")
            if PYQT_AVAILABLE:
                QMessageBox.warning(self, "錯誤", f"添加策略失敗: {e}")
    
    def start_strategy(self, strategy_id: str):
        """啟動策略"""
        try:
            if strategy_id in self.strategy_states:
                state = self.strategy_states[strategy_id]
                state.status = StrategyStatus.RUNNING
                state.start_time = datetime.now()
                state.last_update = datetime.now()
                
                self.update_strategy_table()
                
                if self.strategy_started:
                    self.strategy_started.emit(strategy_id)
                
                logger.info(f"🚀 啟動策略: {strategy_id}")
                
        except Exception as e:
            logger.error(f"❌ 啟動策略失敗: {e}")
    
    def stop_strategy(self, strategy_id: str):
        """停止策略"""
        try:
            if strategy_id in self.strategy_states:
                state = self.strategy_states[strategy_id]
                state.status = StrategyStatus.STOPPED
                state.last_update = datetime.now()
                
                self.update_strategy_table()
                
                if self.strategy_stopped:
                    self.strategy_stopped.emit(strategy_id)
                
                logger.info(f"⏹️ 停止策略: {strategy_id}")
                
        except Exception as e:
            logger.error(f"❌ 停止策略失敗: {e}")
    
    def configure_strategy(self, strategy_id: str):
        """配置策略"""
        if not PYQT_AVAILABLE:
            return
        
        try:
            if strategy_id in self.strategies:
                config = self.strategies[strategy_id]
                dialog = StrategyConfigDialog(config)
                
                if dialog.exec_() == QDialog.Accepted:
                    updated_config = dialog.get_config()
                    self.strategies[strategy_id] = updated_config
                    
                    self.update_strategy_table()
                    
                    if self.strategy_configured:
                        self.strategy_configured.emit(strategy_id)
                    
                    logger.info(f"⚙️ 配置策略: {updated_config.name}")
                    
        except Exception as e:
            logger.error(f"❌ 配置策略失敗: {e}")
            if PYQT_AVAILABLE:
                QMessageBox.warning(self, "錯誤", f"配置策略失敗: {e}")
    
    def start_all_strategies(self):
        """啟動所有策略"""
        try:
            started_count = 0
            for strategy_id, config in self.strategies.items():
                if config.enabled and self.strategy_states[strategy_id].status == StrategyStatus.STOPPED:
                    self.start_strategy(strategy_id)
                    started_count += 1
            
            logger.info(f"🚀 批量啟動了 {started_count} 個策略")
            
        except Exception as e:
            logger.error(f"❌ 批量啟動策略失敗: {e}")
    
    def stop_all_strategies(self):
        """停止所有策略"""
        try:
            stopped_count = 0
            for strategy_id, state in self.strategy_states.items():
                if state.status == StrategyStatus.RUNNING:
                    self.stop_strategy(strategy_id)
                    stopped_count += 1
            
            logger.info(f"⏹️ 批量停止了 {stopped_count} 個策略")
            
        except Exception as e:
            logger.error(f"❌ 批量停止策略失敗: {e}")
    
    def refresh_status(self):
        """刷新狀態"""
        logger.info("🔄 刷新策略狀態")
        self.update_strategy_states()
    
    def update_strategy_states(self):
        """更新策略狀態"""
        try:
            import random
            
            for strategy_id, state in self.strategy_states.items():
                if state.status == StrategyStatus.RUNNING:
                    # 模擬狀態更新
                    if random.random() > 0.8:  # 20%概率更新
                        state.total_signals += random.randint(0, 2)
                        if random.random() > 0.6:  # 40%概率執行交易
                            state.executed_trades += 1
                            pnl_change = random.uniform(-500, 1000)
                            state.total_pnl += pnl_change
                            
                            # 更新勝率
                            if state.executed_trades > 0:
                                win_trades = int(state.executed_trades * state.win_rate)
                                if pnl_change > 0:
                                    win_trades += 1
                                state.win_rate = win_trades / state.executed_trades
                        
                        state.last_update = datetime.now()
            
            self.update_strategy_table()
            self.update_statistics()
            
        except Exception as e:
            logger.error(f"❌ 更新策略狀態失敗: {e}")
    
    def update_strategy_table(self):
        """更新策略表格"""
        if not PYQT_AVAILABLE:
            return
        
        try:
            self.strategy_table.setRowCount(len(self.strategies))
            
            for row, (strategy_id, config) in enumerate(self.strategies.items()):
                state = self.strategy_states.get(strategy_id)
                if not state:
                    continue
                
                # 策略名稱
                self.strategy_table.setItem(row, 0, QTableWidgetItem(config.name))
                
                # 交易對
                self.strategy_table.setItem(row, 1, QTableWidgetItem(config.pair))
                
                # 類型
                type_map = {
                    StrategyType.GRID: "網格",
                    StrategyType.DCA: "定投",
                    StrategyType.ARBITRAGE: "套利",
                    StrategyType.AI_SIGNAL: "AI信號"
                }
                self.strategy_table.setItem(row, 2, QTableWidgetItem(type_map.get(config.strategy_type, "未知")))
                
                # 狀態
                status_item = QTableWidgetItem(state.status.value)
                if state.status == StrategyStatus.RUNNING:
                    status_item.setBackground(QColor(200, 255, 200))
                elif state.status == StrategyStatus.ERROR:
                    status_item.setBackground(QColor(255, 200, 200))
                elif state.status == StrategyStatus.PAUSED:
                    status_item.setBackground(QColor(255, 255, 200))
                self.strategy_table.setItem(row, 3, status_item)
                
                # 運行時間
                if state.start_time and state.status == StrategyStatus.RUNNING:
                    runtime = datetime.now() - state.start_time
                    hours = int(runtime.total_seconds() // 3600)
                    minutes = int((runtime.total_seconds() % 3600) // 60)
                    runtime_text = f"{hours}h {minutes}m"
                else:
                    runtime_text = "--"
                self.strategy_table.setItem(row, 4, QTableWidgetItem(runtime_text))
                
                # 總盈虧
                pnl_item = QTableWidgetItem(f"{state.total_pnl:+,.0f}")
                pnl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if state.total_pnl > 0:
                    pnl_item.setBackground(QColor(200, 255, 200))
                elif state.total_pnl < 0:
                    pnl_item.setBackground(QColor(255, 200, 200))
                self.strategy_table.setItem(row, 5, pnl_item)
                
                # 勝率
                winrate_item = QTableWidgetItem(f"{state.win_rate:.1%}")
                winrate_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.strategy_table.setItem(row, 6, winrate_item)
                
                # 信號數
                signals_item = QTableWidgetItem(f"{state.total_signals}")
                signals_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.strategy_table.setItem(row, 7, signals_item)
                
                # 操作按鈕
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(2, 2, 2, 2)
                
                if state.status == StrategyStatus.RUNNING:
                    stop_button = QPushButton("停止")
                    stop_button.clicked.connect(lambda checked, sid=strategy_id: self.stop_strategy(sid))
                    action_layout.addWidget(stop_button)
                else:
                    start_button = QPushButton("啟動")
                    start_button.clicked.connect(lambda checked, sid=strategy_id: self.start_strategy(sid))
                    action_layout.addWidget(start_button)
                
                self.strategy_table.setCellWidget(row, 8, action_widget)
                
                # 配置按鈕
                config_button = QPushButton("配置")
                config_button.clicked.connect(lambda checked, sid=strategy_id: self.configure_strategy(sid))
                self.strategy_table.setCellWidget(row, 9, config_button)
            
        except Exception as e:
            logger.error(f"❌ 更新策略表格失敗: {e}")
    
    def update_statistics(self):
        """更新統計信息"""
        if not PYQT_AVAILABLE:
            return
        
        try:
            total_strategies = len(self.strategies)
            running_strategies = sum(1 for state in self.strategy_states.values() 
                                   if state.status == StrategyStatus.RUNNING)
            
            total_pnl = sum(state.total_pnl for state in self.strategy_states.values())
            
            win_rates = [state.win_rate for state in self.strategy_states.values() 
                        if state.executed_trades > 0]
            avg_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0
            
            self.total_strategies_label.setText(f"總策略: {total_strategies}")
            self.running_strategies_label.setText(f"運行中: {running_strategies}")
            self.total_pnl_label.setText(f"總盈虧: {total_pnl:+,.0f}")
            self.avg_win_rate_label.setText(f"平均勝率: {avg_win_rate:.1%}")
            
            # 設置盈虧顏色
            if total_pnl > 0:
                self.total_pnl_label.setStyleSheet("color: #00AA00; font-weight: bold;")
            elif total_pnl < 0:
                self.total_pnl_label.setStyleSheet("color: #CC0000; font-weight: bold;")
            else:
                self.total_pnl_label.setStyleSheet("color: #666666;")
            
        except Exception as e:
            logger.error(f"❌ 更新統計信息失敗: {e}")
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """獲取策略摘要"""
        try:
            return {
                "total_strategies": len(self.strategies),
                "running_strategies": sum(1 for state in self.strategy_states.values() 
                                        if state.status == StrategyStatus.RUNNING),
                "total_pnl": sum(state.total_pnl for state in self.strategy_states.values()),
                "total_signals": sum(state.total_signals for state in self.strategy_states.values()),
                "total_trades": sum(state.executed_trades for state in self.strategy_states.values()),
                "strategies": {
                    strategy_id: {
                        "config": config,
                        "state": self.strategy_states.get(strategy_id)
                    }
                    for strategy_id, config in self.strategies.items()
                }
            }
        except Exception as e:
            logger.error(f"❌ 獲取策略摘要失敗: {e}")
            return {}

# 創建策略控制實例
def create_strategy_control_panel() -> StrategyControlWidget:
    """創建策略控制面板實例"""
    return StrategyControlWidget()

# 測試代碼
if __name__ == "__main__":
    def test_strategy_control():
        """測試策略控制系統"""
        print("🧪 測試策略控制系統...")
        
        if PYQT_AVAILABLE:
            app = QApplication(sys.argv)
            
            # 創建策略控制面板
            control_panel = create_strategy_control_panel()
            
            # 創建主窗口
            main_window = QMainWindow()
            main_window.setWindowTitle("AImax 策略控制中心")
            main_window.setCentralWidget(control_panel)
            main_window.setGeometry(100, 100, 1200, 700)
            main_window.show()
            
            print("✅ GUI模式: 策略控制系統已啟動")
            sys.exit(app.exec_())
        else:
            # 非GUI模式測試
            control_panel = create_strategy_control_panel()
            
            # 測試基本功能
            summary = control_panel.get_strategy_summary()
            print(f"✅ 非GUI模式: 策略摘要包含 {summary.get('total_strategies', 0)} 個策略")
            
            print("✅ 策略控制系統測試完成")
    
    # 運行測試
    test_strategy_control()