#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化多交易對GUI系統 - 擴展GUI支持多交易對顯示
"""

import sys
import os
import logging
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
import json

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTextEdit, QGroupBox, QCheckBox, QSpinBox, QApplication,
        QMainWindow, QStatusBar, QMessageBox
    )
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt5 未安裝，將使用文本模式")

logger = logging.getLogger(__name__)

@dataclass
class PairDisplayData:
    """交易對顯示數據"""
    pair: str
    price: float = 0.0
    change_24h: float = 0.0
    volume_24h: float = 0.0
    position_size: float = 0.0
    target_position: float = 0.0
    unrealized_pnl: float = 0.0
    ai_confidence: float = 0.0
    risk_score: float = 0.0
    status: str = "inactive"
    strategy_active: bool = False
    last_update: datetime = None

class SimpleMultiPairGUI(QMainWindow if PYQT_AVAILABLE else object):
    """簡化多交易對GUI主窗口"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        
        # 數據管理
        self.pairs_data: List[PairDisplayData] = []
        self.selected_pair: Optional[str] = None
        
        # 定時器
        self.update_timer = None
        
        if PYQT_AVAILABLE:
            self.init_ui()
            self.setup_timer()
    
    def init_ui(self):
        """初始化UI"""
        if not PYQT_AVAILABLE:
            return
        
        self.setWindowTitle("AImax 簡化多交易對監控系統")
        self.setGeometry(100, 100, 1000, 700)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 主標題
        title_label = QLabel("AImax 簡化多交易對監控系統")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2E86AB; margin: 10px; padding: 10px;")
        layout.addWidget(title_label)
        
        # 交易對信息顯示
        self.pairs_info_text = QTextEdit()
        self.pairs_info_text.setReadOnly(True)
        self.pairs_info_text.setMaximumHeight(400)
        layout.addWidget(self.pairs_info_text)
        
        # 統計信息
        stats_widget = self.create_stats_widget()
        layout.addWidget(stats_widget)
        
        # 控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # 狀態欄
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("系統就緒")
    
    def create_stats_widget(self):
        """創建統計信息組件"""
        if not PYQT_AVAILABLE:
            return QWidget()
        
        stats_group = QGroupBox("統計信息")
        layout = QHBoxLayout(stats_group)
        
        self.total_pairs_label = QLabel("總交易對: 0")
        self.active_pairs_label = QLabel("活躍: 0")
        self.total_pnl_label = QLabel("總盈虧: 0")
        self.avg_confidence_label = QLabel("平均信心度: 0%")
        
        layout.addWidget(self.total_pairs_label)
        layout.addWidget(self.active_pairs_label)
        layout.addWidget(self.total_pnl_label)
        layout.addWidget(self.avg_confidence_label)
        layout.addStretch()
        
        return stats_group
    
    def create_control_panel(self):
        """創建控制面板"""
        if not PYQT_AVAILABLE:
            return QWidget()
        
        panel = QGroupBox("系統控制")
        layout = QHBoxLayout(panel)
        
        # 自動更新控制
        self.auto_update_checkbox = QCheckBox("自動更新")
        self.auto_update_checkbox.setChecked(True)
        self.auto_update_checkbox.toggled.connect(self.toggle_auto_update)
        layout.addWidget(self.auto_update_checkbox)
        
        # 更新間隔
        layout.addWidget(QLabel("更新間隔(秒):"))
        self.update_interval_spinbox = QSpinBox()
        self.update_interval_spinbox.setRange(1, 60)
        self.update_interval_spinbox.setValue(5)
        self.update_interval_spinbox.valueChanged.connect(self.update_timer_interval)
        layout.addWidget(self.update_interval_spinbox)
        
        # 手動更新按鈕
        self.manual_update_button = QPushButton("立即更新")
        self.manual_update_button.clicked.connect(self.manual_update)
        layout.addWidget(self.manual_update_button)
        
        # 系統控制按鈕
        self.start_trading_button = QPushButton("啟動交易")
        self.stop_trading_button = QPushButton("停止交易")
        
        self.start_trading_button.clicked.connect(self.start_trading)
        self.stop_trading_button.clicked.connect(self.stop_trading)
        
        layout.addWidget(self.start_trading_button)
        layout.addWidget(self.stop_trading_button)
        
        layout.addStretch()
        
        # 系統狀態指示器
        self.system_status_label = QLabel("系統狀態: 就緒")
        layout.addWidget(self.system_status_label)
        
        return panel
    
    def setup_timer(self):
        """設置定時器"""
        if not PYQT_AVAILABLE:
            return
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.update_timer.start(5000)  # 5秒間隔
    
    def toggle_auto_update(self, enabled: bool):
        """切換自動更新"""
        if not PYQT_AVAILABLE:
            return
        
        if enabled:
            self.update_timer.start()
            logger.info("✅ 啟用自動更新")
            self.update_system_status("自動更新已啟用")
        else:
            self.update_timer.stop()
            logger.info("⏸️ 禁用自動更新")
            self.update_system_status("自動更新已禁用")
    
    def update_timer_interval(self, interval: int):
        """更新定時器間隔"""
        if not PYQT_AVAILABLE:
            return
        
        self.update_timer.setInterval(interval * 1000)
        logger.info(f"⏰ 更新間隔設置為 {interval} 秒")
    
    def update_data(self):
        """更新數據"""
        try:
            # 生成示例數據
            new_pairs_data = self.generate_sample_data()
            
            # 更新內部數據
            self.pairs_data = new_pairs_data
            
            # 更新UI顯示
            self.update_display()
            self.update_statistics()
            
            # 更新狀態
            timestamp = datetime.now().strftime("%H:%M:%S")
            if PYQT_AVAILABLE:
                self.status_bar.showMessage(f"[{timestamp}] 數據已更新 - {len(new_pairs_data)} 個交易對")
            
            logger.debug(f"📊 更新了 {len(new_pairs_data)} 個交易對數據")
            
        except Exception as e:
            logger.error(f"❌ 更新數據失敗: {e}")
            if PYQT_AVAILABLE:
                self.status_bar.showMessage(f"數據更新失敗: {e}")
    
    def update_display(self):
        """更新顯示"""
        if not PYQT_AVAILABLE:
            return
        
        try:
            # 構建顯示文本
            display_text = "多交易對監控信息:\n\n"
            
            for data in self.pairs_data:
                display_text += f"交易對: {data.pair}\n"
                display_text += f"  價格: {data.price:,.2f}\n"
                display_text += f"  24h變化: {data.change_24h:+.2f}%\n"
                display_text += f"  倉位: {data.position_size:.4f} -> {data.target_position:.4f}\n"
                display_text += f"  盈虧: {data.unrealized_pnl:+,.0f}\n"
                display_text += f"  AI信心度: {data.ai_confidence:.1%}\n"
                display_text += f"  風險分數: {data.risk_score:.1%}\n"
                display_text += f"  狀態: {data.status}\n"
                display_text += f"  策略: {'活躍' if data.strategy_active else '未活躍'}\n"
                display_text += "-" * 50 + "\n"
            
            self.pairs_info_text.setPlainText(display_text)
            
        except Exception as e:
            logger.error(f"❌ 更新顯示失敗: {e}")
    
    def update_statistics(self):
        """更新統計信息"""
        if not PYQT_AVAILABLE:
            return
        
        try:
            total_pairs = len(self.pairs_data)
            active_pairs = sum(1 for data in self.pairs_data if data.status == "active")
            
            total_pnl = sum(data.unrealized_pnl for data in self.pairs_data)
            
            avg_confidence = (sum(data.ai_confidence for data in self.pairs_data) / total_pairs * 100) if total_pairs > 0 else 0
            
            self.total_pairs_label.setText(f"總交易對: {total_pairs}")
            self.active_pairs_label.setText(f"活躍: {active_pairs}")
            self.total_pnl_label.setText(f"總盈虧: {total_pnl:+,.0f}")
            self.avg_confidence_label.setText(f"平均信心度: {avg_confidence:.1f}%")
            
            # 設置盈虧顏色
            if total_pnl > 0:
                self.total_pnl_label.setStyleSheet("color: #00AA00; font-weight: bold;")
            elif total_pnl < 0:
                self.total_pnl_label.setStyleSheet("color: #CC0000; font-weight: bold;")
            else:
                self.total_pnl_label.setStyleSheet("color: #666666;")
            
        except Exception as e:
            logger.error(f"❌ 更新統計信息失敗: {e}")
    
    def generate_sample_data(self) -> List[PairDisplayData]:
        """生成示例數據"""
        import random
        
        pairs = ["BTCTWD", "ETHTWD", "LTCTWD", "BCHTWD", "ADATWD", "DOTTWD"]
        sample_data = []
        
        for pair in pairs:
            # 使用哈希確保數據一致性
            seed = hash(pair + str(datetime.now().hour))
            random.seed(seed)
            
            data = PairDisplayData(
                pair=pair,
                price=random.uniform(10000, 2000000),
                change_24h=random.uniform(-15, 15),
                volume_24h=random.uniform(1000000, 100000000),
                position_size=random.uniform(0, 0.1),
                target_position=random.uniform(0, 0.1),
                unrealized_pnl=random.uniform(-100000, 100000),
                ai_confidence=random.uniform(0.3, 0.95),
                risk_score=random.uniform(0.1, 0.9),
                status=random.choice(["active", "inactive", "warning", "error"]),
                strategy_active=random.choice([True, False]),
                last_update=datetime.now()
            )
            sample_data.append(data)
        
        return sample_data
    
    def manual_update(self):
        """手動更新"""
        logger.info("🔄 執行手動更新")
        self.update_data()
    
    def on_pair_selected(self, pair: str):
        """交易對選中事件"""
        self.selected_pair = pair
        logger.info(f"📌 選中交易對: {pair}")
        if PYQT_AVAILABLE:
            self.status_bar.showMessage(f"已選中交易對: {pair}")
    
    def toggle_strategy(self, pair: str):
        """切換策略狀態"""
        try:
            # 查找對應的交易對數據
            for data in self.pairs_data:
                if data.pair == pair:
                    data.strategy_active = not data.strategy_active
                    status = "啟動" if data.strategy_active else "停止"
                    logger.info(f"🔄 {pair} 策略已{status}")
                    
                    if PYQT_AVAILABLE:
                        self.status_bar.showMessage(f"{pair} 策略已{status}")
                    break
            
            # 更新顯示
            self.update_display()
            
        except Exception as e:
            logger.error(f"❌ 切換策略失敗: {e}")
    
    def start_trading(self):
        """啟動交易"""
        logger.info("🚀 啟動交易系統")
        self.update_system_status("交易系統運行中")
        if PYQT_AVAILABLE:
            self.status_bar.showMessage("交易系統已啟動")
    
    def stop_trading(self):
        """停止交易"""
        logger.info("⏹️ 停止交易系統")
        self.update_system_status("交易系統已停止")
        if PYQT_AVAILABLE:
            self.status_bar.showMessage("交易系統已停止")
    
    def update_system_status(self, status: str):
        """更新系統狀態"""
        if PYQT_AVAILABLE:
            self.system_status_label.setText(f"系統狀態: {status}")
    
    def get_current_data(self) -> List[PairDisplayData]:
        """獲取當前數據"""
        return self.pairs_data.copy()

# 創建應用程序實例
def create_simple_multi_pair_gui() -> SimpleMultiPairGUI:
    """創建簡化多交易對GUI實例"""
    return SimpleMultiPairGUI()

# 測試代碼
if __name__ == "__main__":
    def test_simple_gui():
        """測試簡化GUI"""
        print("🧪 測試簡化多交易對GUI系統...")
        
        if PYQT_AVAILABLE:
            app = QApplication(sys.argv)
            
            # 創建主窗口
            main_window = create_simple_multi_pair_gui()
            main_window.show()
            
            print("✅ GUI模式: 簡化多交易對GUI系統已啟動")
            sys.exit(app.exec_())
        else:
            # 非GUI模式測試
            gui = create_simple_multi_pair_gui()
            
            # 測試數據生成
            sample_data = gui.generate_sample_data()
            
            print(f"✅ 非GUI模式: 生成了 {len(sample_data)} 個交易對數據")
            for data in sample_data:
                print(f"   {data.pair}: 價格={data.price:.0f}, 信心度={data.ai_confidence:.1%}, 風險={data.risk_score:.1%}")
            
            print("✅ 簡化多交易對GUI系統測試完成")
    
    # 運行測試
    test_simple_gui()