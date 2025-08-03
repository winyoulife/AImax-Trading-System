#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實時監控儀表板GUI - 任務7.2的可視化界面
提供多交易對的實時價格、持倉顯示和績效指標可視化
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget,
        QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
        QGroupBox, QProgressBar, QTextEdit, QScrollArea, QFrame,
        QApplication, QMainWindow, QStatusBar, QSplitter
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QFont, QColor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt5 未安裝，將使用文本模式")

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from src.monitoring.realtime_performance_monitor import (
        RealTimePerformanceMonitor, 
        create_realtime_performance_monitor
    )
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    print("⚠️ 實時監控模塊不可用，將使用模擬模式")

logger = logging.getLogger(__name__)

class RealTimePriceWidget(QWidget if PYQT_AVAILABLE else object):
    """實時價格顯示組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
            self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        if not PYQT_AVAILABLE:
            return
        
        layout = QVBoxLayout(self)
        
        # 標題
        title_label = QLabel("實時價格監控")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # 價格表格
        self.price_table = QTableWidget()
        self.price_table.setColumnCount(8)
        self.price_table.setHorizontalHeaderLabels([
            "交易對", "當前價格", "24h變化", "變化%", "24h成交量", 
            "24h最高", "24h最低", "買賣價差"
        ])
        
        # 設置表格屬性
        self.price_table.setAlternatingRowColors(True)
        header = self.price_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(self.price_table)
    
    def update_prices(self, prices_data: Dict[str, Any]):
        """更新價格顯示"""
        if not PYQT_AVAILABLE:
            return
        
        try:
            pairs = list(prices_data.keys())
            self.price_table.setRowCount(len(pairs))
            
            for row, pair in enumerate(pairs):
                price_info = prices_data[pair]
                if not price_info:
                    continue
                
                # 交易對
                self.price_table.setItem(row, 0, QTableWidgetItem(pair))
                
                # 當前價格
                price_item = QTableWidgetItem(f"{price_info.price:,.2f}")
                price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.price_table.setItem(row, 1, price_item)
                
                # 24h變化
                change_item = QTableWidgetItem(f"{price_info.change_24h:+,.2f}")
                change_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if price_info.change_24h > 0:
                    change_item.setBackground(QColor(200, 255, 200))
                elif price_info.change_24h < 0:
                    change_item.setBackground(QColor(255, 200, 200))
                self.price_table.setItem(row, 2, change_item)
                
                # 變化百分比
                percent_item = QTableWidgetItem(f"{price_info.change_percent_24h:+.2f}%")
                percent_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if price_info.change_percent_24h > 0:
                    percent_item.setBackground(QColor(200, 255, 200))
                elif price_info.change_percent_24h < 0:
                    percent_item.setBackground(QColor(255, 200, 200))
                self.price_table.setItem(row, 3, percent_item)
                
                # 24h成交量
                volume_item = QTableWidgetItem(f"{price_info.volume_24h:,.0f}")
                volume_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.price_table.setItem(row, 4, volume_item)
                
                # 24h最高
                high_item = QTableWidgetItem(f"{price_info.high_24h:,.2f}")
                high_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.price_table.setItem(row, 5, high_item)
                
                # 24h最低
                low_item = QTableWidgetItem(f"{price_info.low_24h:,.2f}")
                low_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.price_table.setItem(row, 6, low_item)
                
                # 買賣價差
                spread_item = QTableWidgetItem(f"{price_info.spread:,.2f}")
                spread_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.price_table.setItem(row, 7, spread_item)
                
        except Exception as e:
            logger.error(f"❌ 更新價格顯示失敗: {e}")

class PositionWidget(QWidget if PYQT_AVAILABLE else object):
    """持倉信息顯示組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
            self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        if not PYQT_AVAILABLE:
            return
        
        layout = QVBoxLayout(self)
        
        # 標題
        title_label = QLabel("持倉監控")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # 持倉表格
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(9)
        self.position_table.setHorizontalHeaderLabels([
            "交易對", "倉位大小", "入場價格", "當前價格", "未實現盈虧", 
            "收益率", "持倉時間", "策略類型", "AI信心度"
        ])
        
        # 設置表格屬性
        self.position_table.setAlternatingRowColors(True)
        header = self.position_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(self.position_table)
    
    def update_positions(self, positions_data: Dict[str, Any]):
        """更新持倉顯示"""
        if not PYQT_AVAILABLE:
            return
        
        try:
            positions = [pos for pos in positions_data.values() if pos is not None]
            self.position_table.setRowCount(len(positions))
            
            for row, position in enumerate(positions):
                # 交易對
                self.position_table.setItem(row, 0, QTableWidgetItem(position.pair))
                
                # 倉位大小
                size_item = QTableWidgetItem(f"{position.size:.4f}")
                size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.position_table.setItem(row, 1, size_item)
                
                # 入場價格
                entry_item = QTableWidgetItem(f"{position.entry_price:,.2f}")
                entry_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.position_table.setItem(row, 2, entry_item)
                
                # 當前價格
                current_item = QTableWidgetItem(f"{position.current_price:,.2f}")
                current_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.position_table.setItem(row, 3, current_item)
                
                # 未實現盈虧
                pnl_item = QTableWidgetItem(f"{position.unrealized_pnl:+,.0f}")
                pnl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if position.unrealized_pnl > 0:
                    pnl_item.setBackground(QColor(200, 255, 200))
                elif position.unrealized_pnl < 0:
                    pnl_item.setBackground(QColor(255, 200, 200))
                self.position_table.setItem(row, 4, pnl_item)
                
                # 收益率
                return_item = QTableWidgetItem(f"{position.unrealized_return:+.2%}")
                return_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if position.unrealized_return > 0:
                    return_item.setBackground(QColor(200, 255, 200))
                elif position.unrealized_return < 0:
                    return_item.setBackground(QColor(255, 200, 200))
                self.position_table.setItem(row, 5, return_item)
                
                # 持倉時間
                holding_hours = position.holding_time.total_seconds() / 3600
                time_item = QTableWidgetItem(f"{holding_hours:.1f}h")
                time_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.position_table.setItem(row, 6, time_item)
                
                # 策略類型
                self.position_table.setItem(row, 7, QTableWidgetItem(position.strategy_type))
                
                # AI信心度
                confidence_item = QTableWidgetItem(f"{position.ai_confidence:.1%}")
                confidence_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if position.ai_confidence >= 0.7:
                    confidence_item.setBackground(QColor(200, 255, 200))
                elif position.ai_confidence >= 0.5:
                    confidence_item.setBackground(QColor(255, 255, 200))
                else:
                    confidence_item.setBackground(QColor(255, 200, 200))
                self.position_table.setItem(row, 8, confidence_item)
                
        except Exception as e:
            logger.error(f"❌ 更新持倉顯示失敗: {e}")

class PerformanceWidget(QWidget if PYQT_AVAILABLE else object):
    """績效指標顯示組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
            self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        if not PYQT_AVAILABLE:
            return
        
        layout = QVBoxLayout(self)
        
        # 標題
        title_label = QLabel("績效分析")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # 績效表格
        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(10)
        self.performance_table.setHorizontalHeaderLabels([
            "交易對", "總收益", "年化收益率", "夏普比率", "最大回撤", 
            "勝率", "盈利因子", "波動率", "總交易數", "連續盈利"
        ])
        
        # 設置表格屬性
        self.performance_table.setAlternatingRowColors(True)
        header = self.performance_table.horizontalHeader()
        header.setStretchLastSection(True)
        
        layout.addWidget(self.performance_table)
    
    def update_performance(self, performance_data: Dict[str, Any]):
        """更新績效顯示"""
        if not PYQT_AVAILABLE:
            return
        
        try:
            metrics_list = [metrics for metrics in performance_data.values() if metrics is not None]
            self.performance_table.setRowCount(len(metrics_list))
            
            for row, metrics in enumerate(metrics_list):
                # 交易對
                self.performance_table.setItem(row, 0, QTableWidgetItem(metrics.pair))
                
                # 總收益
                return_item = QTableWidgetItem(f"{metrics.total_return:+,.0f}")
                return_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if metrics.total_return > 0:
                    return_item.setBackground(QColor(200, 255, 200))
                elif metrics.total_return < 0:
                    return_item.setBackground(QColor(255, 200, 200))
                self.performance_table.setItem(row, 1, return_item)
                
                # 年化收益率
                annual_item = QTableWidgetItem(f"{metrics.annualized_return:+.2%}")
                annual_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.performance_table.setItem(row, 2, annual_item)
                
                # 夏普比率
                sharpe_item = QTableWidgetItem(f"{metrics.sharpe_ratio:.2f}")
                sharpe_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if metrics.sharpe_ratio > 1.0:
                    sharpe_item.setBackground(QColor(200, 255, 200))
                elif metrics.sharpe_ratio > 0.5:
                    sharpe_item.setBackground(QColor(255, 255, 200))
                self.performance_table.setItem(row, 3, sharpe_item)
                
                # 最大回撤
                drawdown_item = QTableWidgetItem(f"{metrics.max_drawdown:.2%}")
                drawdown_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if metrics.max_drawdown > 0.2:
                    drawdown_item.setBackground(QColor(255, 200, 200))
                elif metrics.max_drawdown > 0.1:
                    drawdown_item.setBackground(QColor(255, 255, 200))
                self.performance_table.setItem(row, 4, drawdown_item)
                
                # 勝率
                winrate_item = QTableWidgetItem(f"{metrics.win_rate:.1%}")
                winrate_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if metrics.win_rate > 0.6:
                    winrate_item.setBackground(QColor(200, 255, 200))
                elif metrics.win_rate > 0.4:
                    winrate_item.setBackground(QColor(255, 255, 200))
                self.performance_table.setItem(row, 5, winrate_item)
                
                # 盈利因子
                profit_item = QTableWidgetItem(f"{metrics.profit_factor:.2f}")
                profit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if metrics.profit_factor > 1.5:
                    profit_item.setBackground(QColor(200, 255, 200))
                elif metrics.profit_factor > 1.0:
                    profit_item.setBackground(QColor(255, 255, 200))
                self.performance_table.setItem(row, 6, profit_item)
                
                # 波動率
                vol_item = QTableWidgetItem(f"{metrics.volatility:.2%}")
                vol_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.performance_table.setItem(row, 7, vol_item)
                
                # 總交易數
                trades_item = QTableWidgetItem(f"{metrics.total_trades}")
                trades_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.performance_table.setItem(row, 8, trades_item)
                
                # 連續盈利
                consecutive_item = QTableWidgetItem(f"{metrics.consecutive_wins}")
                consecutive_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.performance_table.setItem(row, 9, consecutive_item)
                
        except Exception as e:
            logger.error(f"❌ 更新績效顯示失敗: {e}")

class AIDecisionWidget(QWidget if PYQT_AVAILABLE else object):
    """AI決策可視化組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
            self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        if not PYQT_AVAILABLE:
            return
        
        layout = QVBoxLayout(self)
        
        # 標題
        title_label = QLabel("AI決策監控")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # AI決策顯示區域
        self.ai_text = QTextEdit()
        self.ai_text.setReadOnly(True)
        self.ai_text.setMaximumHeight(300)
        layout.addWidget(self.ai_text)
    
    def update_ai_decisions(self, ai_data: Dict[str, Any]):
        """更新AI決策顯示"""
        if not PYQT_AVAILABLE:
            return
        
        try:
            display_text = "AI決策過程監控:\n\n"
            
            for pair, pair_data in ai_data.get("pairs", {}).items():
                display_text += f"交易對: {pair}\n"
                display_text += f"  策略狀態: {'活躍' if pair_data.get('strategy_active', False) else '未活躍'}\n"
                display_text += f"  平均信心度: {pair_data.get('avg_confidence', 0):.1%}\n"
                display_text += f"  執行率: {pair_data.get('execution_rate', 0):.1%}\n"
                display_text += f"  總決策數: {pair_data.get('total_decisions', 0)}\n"
                
                # 最近決策
                recent_decisions = pair_data.get("recent_decisions", [])
                if recent_decisions:
                    display_text += "  最近決策:\n"
                    for decision in recent_decisions[:3]:  # 顯示最近3個決策
                        timestamp = decision.get("timestamp", "")
                        if isinstance(timestamp, str):
                            try:
                                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                time_str = dt.strftime("%H:%M:%S")
                            except:
                                time_str = timestamp
                        else:
                            time_str = str(timestamp)
                        
                        display_text += f"    [{time_str}] {decision.get('decision', 'N/A')} "
                        display_text += f"(信心度: {decision.get('confidence', 0):.1%}, "
                        display_text += f"執行: {'是' if decision.get('executed', False) else '否'})\n"
                
                display_text += "-" * 50 + "\n"
            
            self.ai_text.setPlainText(display_text)
            
        except Exception as e:
            logger.error(f"❌ 更新AI決策顯示失敗: {e}")

class RealTimeMonitoringDashboard(QMainWindow if PYQT_AVAILABLE else object):
    """實時監控儀表板主窗口"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        
        # 監控系統
        self.monitor = None
        self.update_timer = None
        
        if PYQT_AVAILABLE:
            self.init_ui()
            self.init_monitor()
            self.setup_timer()
    
    def init_ui(self):
        """初始化UI"""
        if not PYQT_AVAILABLE:
            return
        
        self.setWindowTitle("AImax 實時監控儀表板")
        self.setGeometry(100, 100, 1400, 900)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 主標題
        title_label = QLabel("AImax 實時監控和績效分析儀表板")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2E86AB; margin: 15px; padding: 10px;")
        layout.addWidget(title_label)
        
        # 標籤頁
        self.tab_widget = QTabWidget()
        
        # 實時價格標籤頁
        self.price_widget = RealTimePriceWidget()
        self.tab_widget.addTab(self.price_widget, "實時價格")
        
        # 持倉監控標籤頁
        self.position_widget = PositionWidget()
        self.tab_widget.addTab(self.position_widget, "持倉監控")
        
        # 績效分析標籤頁
        self.performance_widget = PerformanceWidget()
        self.tab_widget.addTab(self.performance_widget, "績效分析")
        
        # AI決策標籤頁
        self.ai_widget = AIDecisionWidget()
        self.tab_widget.addTab(self.ai_widget, "AI決策")
        
        layout.addWidget(self.tab_widget)
        
        # 控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # 狀態欄
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("系統就緒")
    
    def create_control_panel(self):
        """創建控制面板"""
        if not PYQT_AVAILABLE:
            return QWidget()
        
        panel = QGroupBox("監控控制")
        layout = QHBoxLayout(panel)
        
        # 啟動/停止監控按鈕
        self.start_button = QPushButton("啟動監控")
        self.stop_button = QPushButton("停止監控")
        
        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)
        
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        
        # 手動刷新按鈕
        self.refresh_button = QPushButton("立即刷新")
        self.refresh_button.clicked.connect(self.manual_refresh)
        layout.addWidget(self.refresh_button)
        
        layout.addStretch()
        
        # 狀態指示器
        self.monitor_status_label = QLabel("監控狀態: 未啟動")
        layout.addWidget(self.monitor_status_label)
        
        return panel
    
    def init_monitor(self):
        """初始化監控系統"""
        try:
            if MONITOR_AVAILABLE:
                self.monitor = create_realtime_performance_monitor()
                logger.info("✅ 實時監控系統初始化成功")
            else:
                logger.warning("⚠️ 監控系統不可用，使用模擬模式")
        except Exception as e:
            logger.error(f"❌ 初始化監控系統失敗: {e}")
    
    def setup_timer(self):
        """設置定時器"""
        if not PYQT_AVAILABLE:
            return
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(2000)  # 2秒更新間隔
    
    def start_monitoring(self):
        """啟動監控"""
        try:
            if self.monitor:
                self.monitor.start_monitoring()
                self.monitor_status_label.setText("監控狀態: 運行中")
                self.status_bar.showMessage("實時監控已啟動")
                logger.info("🚀 實時監控已啟動")
            else:
                self.status_bar.showMessage("監控系統不可用")
        except Exception as e:
            logger.error(f"❌ 啟動監控失敗: {e}")
            self.status_bar.showMessage(f"啟動監控失敗: {e}")
    
    def stop_monitoring(self):
        """停止監控"""
        try:
            if self.monitor:
                self.monitor.stop_monitoring()
                self.monitor_status_label.setText("監控狀態: 已停止")
                self.status_bar.showMessage("實時監控已停止")
                logger.info("⏹️ 實時監控已停止")
        except Exception as e:
            logger.error(f"❌ 停止監控失敗: {e}")
    
    def manual_refresh(self):
        """手動刷新"""
        logger.info("🔄 執行手動刷新")
        self.update_display()
    
    def update_display(self):
        """更新顯示"""
        try:
            if not self.monitor:
                return
            
            # 獲取實時摘要
            summary = self.monitor.get_real_time_summary()
            
            if summary and "pairs_data" in summary:
                pairs_data = summary["pairs_data"]
                
                # 更新實時價格
                prices = {pair: data.get("price") for pair, data in pairs_data.items()}
                self.price_widget.update_prices(prices)
                
                # 更新持倉信息
                positions = {pair: data.get("position") for pair, data in pairs_data.items()}
                self.position_widget.update_positions(positions)
                
                # 更新績效指標
                performance = {pair: data.get("performance") for pair, data in pairs_data.items()}
                self.performance_widget.update_performance(performance)
            
            # 更新AI決策
            ai_data = self.monitor.get_ai_decision_visualization()
            self.ai_widget.update_ai_decisions(ai_data)
            
            # 更新狀態欄
            timestamp = datetime.now().strftime("%H:%M:%S")
            active_positions = len([pos for pos in summary.get("pairs_data", {}).values() 
                                 if pos.get("position") is not None]) if summary else 0
            self.status_bar.showMessage(f"[{timestamp}] 活躍倉位: {active_positions}")
            
        except Exception as e:
            logger.error(f"❌ 更新顯示失敗: {e}")
    
    def closeEvent(self, event):
        """關閉事件"""
        if self.monitor:
            self.monitor.stop_monitoring()
        event.accept()

# 創建儀表板實例
def create_realtime_monitoring_dashboard() -> RealTimeMonitoringDashboard:
    """創建實時監控儀表板實例"""
    return RealTimeMonitoringDashboard()

# 測試代碼
if __name__ == "__main__":
    def test_dashboard():
        """測試儀表板"""
        print("🧪 測試實時監控儀表板...")
        
        if PYQT_AVAILABLE:
            app = QApplication(sys.argv)
            
            # 創建儀表板
            dashboard = create_realtime_monitoring_dashboard()
            dashboard.show()
            
            print("✅ GUI模式: 實時監控儀表板已啟動")
            sys.exit(app.exec_())
        else:
            print("✅ 非GUI模式: 儀表板測試完成")
    
    # 運行測試
    test_dashboard()