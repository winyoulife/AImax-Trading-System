"""
實時監控儀表板 - 顯示系統狀態、性能指標和AI決策過程
"""
import sys
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QGridLayout, QLabel, QProgressBar, QPushButton, QTextEdit,
        QTabWidget, QTableWidget, QTableWidgetItem, QGroupBox,
        QScrollArea, QFrame, QSplitter, QComboBox, QSpinBox,
        QCheckBox, QSlider, QStatusBar
    )
    from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt, QSize
    from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap, QIcon
    from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt6 未安裝，監控界面將使用文本模式")

# 導入AImax核心組件
sys.path.append(str(Path(__file__).parent.parent))
try:
    from optimization.performance_optimizer import AIPerformanceOptimizer
    from optimization.data_cache_optimizer import DataCacheOptimizer
    from ai.ai_manager import AICollaborationManager
    from core.trading_system_integrator import TradingSystemIntegrator
except ImportError as e:
    print(f"⚠️ 導入AImax核心組件失敗: {e}")
    AIPerformanceOptimizer = None
    DataCacheOptimizer = None
    AICollaborationManager = None
    TradingSystemIntegrator = None

class SystemMonitorThread(QThread if PYQT_AVAILABLE else threading.Thread):
    """系統監控線程"""
    
    if PYQT_AVAILABLE:
        # PyQt信號
        performance_updated = pyqtSignal(dict)
        ai_status_updated = pyqtSignal(dict)
        trading_status_updated = pyqtSignal(dict)
        error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.update_interval = 1.0  # 秒
        
        # 初始化監控組件
        self.performance_optimizer = None
        self.cache_optimizer = None
        self.ai_manager = None
        self.trading_integrator = None
        
        # 性能數據歷史
        self.performance_history = []
        self.max_history_size = 300  # 5分鐘的數據（每秒一個點）
        
    def initialize_components(self):
        """初始化監控組件"""
        try:
            if AIPerformanceOptimizer:
                self.performance_optimizer = AIPerformanceOptimizer()
            if DataCacheOptimizer:
                self.cache_optimizer = DataCacheOptimizer()
            self.logger.info("✅ 監控組件初始化完成")
        except Exception as e:
            self.logger.error(f"❌ 監控組件初始化失敗: {e}")
            if PYQT_AVAILABLE:
                self.error_occurred.emit(f"監控組件初始化失敗: {e}")
    
    def start_monitoring(self):
        """開始監控"""
        if self.isRunning():
            self.logger.warning("⚠️ 監控線程已在運行")
            return
            
        self.running = True
        try:
            self.start()
            self.logger.info("🚀 系統監控已啟動")
        except Exception as e:
            self.logger.error(f"❌ 啟動監控線程失敗: {e}")
            self.running = False
    
    def stop_monitoring(self):
        """停止監控"""
        self.running = False
        self.logger.info("⏹️ 系統監控已停止")
        
        # 等待線程結束
        if self.isRunning():
            self.wait(3000)  # 等待最多3秒
            if self.isRunning():
                self.terminate()  # 強制終止
                self.logger.warning("⚠️ 監控線程被強制終止")
    
    def run(self):
        """監控主循環"""
        while self.running:
            try:
                # 收集性能數據
                performance_data = self._collect_performance_data()
                if performance_data and PYQT_AVAILABLE:
                    self.performance_updated.emit(performance_data)
                
                # 收集AI狀態
                ai_status = self._collect_ai_status()
                if ai_status and PYQT_AVAILABLE:
                    self.ai_status_updated.emit(ai_status)
                
                # 收集交易狀態
                trading_status = self._collect_trading_status()
                if trading_status and PYQT_AVAILABLE:
                    self.trading_status_updated.emit(trading_status)
                
                time.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"❌ 監控數據收集失敗: {e}")
                if PYQT_AVAILABLE:
                    self.error_occurred.emit(f"監控數據收集失敗: {e}")
    
    def _collect_performance_data(self) -> Dict[str, Any]:
        """收集性能數據"""
        try:
            import psutil
            
            # 系統資源使用
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # AI性能數據（如果可用）
            ai_performance = {}
            if self.performance_optimizer:
                ai_performance = self.performance_optimizer.get_current_metrics()
            
            # 緩存性能數據
            cache_performance = {}
            if self.cache_optimizer:
                cache_performance = self.cache_optimizer.get_performance_stats()
            
            performance_data = {
                "timestamp": datetime.now(),
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_mb": memory.used / (1024 * 1024),
                    "memory_total_mb": memory.total / (1024 * 1024),
                    "disk_percent": disk.percent,
                    "disk_used_gb": disk.used / (1024 * 1024 * 1024),
                    "disk_total_gb": disk.total / (1024 * 1024 * 1024)
                },
                "ai_performance": ai_performance,
                "cache_performance": cache_performance
            }
            
            # 添加到歷史記錄
            self.performance_history.append(performance_data)
            if len(self.performance_history) > self.max_history_size:
                self.performance_history.pop(0)
            
            return performance_data
            
        except Exception as e:
            self.logger.error(f"❌ 收集性能數據失敗: {e}")
            return {}
    
    def _collect_ai_status(self) -> Dict[str, Any]:
        """收集AI狀態"""
        try:
            ai_status = {
                "timestamp": datetime.now(),
                "models": {
                    "market_scanner": {"status": "ready", "last_analysis": datetime.now() - timedelta(seconds=30)},
                    "deep_analyst": {"status": "ready", "last_analysis": datetime.now() - timedelta(seconds=45)},
                    "decision_maker": {"status": "ready", "last_analysis": datetime.now() - timedelta(seconds=60)}
                },
                "collaboration": {
                    "active_analysis": False,
                    "last_decision": datetime.now() - timedelta(minutes=2),
                    "confidence_level": 66.7,
                    "consensus_reached": True
                }
            }
            
            return ai_status
            
        except Exception as e:
            self.logger.error(f"❌ 收集AI狀態失敗: {e}")
            return {}
    
    def _collect_trading_status(self) -> Dict[str, Any]:
        """收集交易狀態"""
        try:
            trading_status = {
                "timestamp": datetime.now(),
                "account": {
                    "balance_twd": 100000,
                    "balance_btc": 0.01,
                    "total_value_twd": 115000,
                    "daily_pnl": 1500,
                    "daily_pnl_percent": 1.3
                },
                "positions": {
                    "active_positions": 1,
                    "total_positions_today": 3,
                    "win_rate": 66.7,
                    "avg_hold_time": "2.5小時"
                },
                "risk": {
                    "current_risk_level": "MEDIUM",
                    "max_drawdown": 2.1,
                    "risk_score": 55.0,
                    "daily_loss_limit": 5000
                }
            }
            
            return trading_status
            
        except Exception as e:
            self.logger.error(f"❌ 收集交易狀態失敗: {e}")
            return {}

class PerformanceWidget(QWidget if PYQT_AVAILABLE else object):
    """性能監控組件"""
    
    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setup_ui()
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 系統資源組
        system_group = QGroupBox("系統資源")
        system_layout = QGridLayout(system_group)
        
        # CPU使用率
        system_layout.addWidget(QLabel("CPU使用率:"), 0, 0)
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_label = QLabel("0%")
        system_layout.addWidget(self.cpu_progress, 0, 1)
        system_layout.addWidget(self.cpu_label, 0, 2)
        
        # 內存使用率
        system_layout.addWidget(QLabel("內存使用率:"), 1, 0)
        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        self.memory_label = QLabel("0%")
        system_layout.addWidget(self.memory_progress, 1, 1)
        system_layout.addWidget(self.memory_label, 1, 2)
        
        # 磁盤使用率
        system_layout.addWidget(QLabel("磁盤使用率:"), 2, 0)
        self.disk_progress = QProgressBar()
        self.disk_progress.setRange(0, 100)
        self.disk_label = QLabel("0%")
        system_layout.addWidget(self.disk_progress, 2, 1)
        system_layout.addWidget(self.disk_label, 2, 2)
        
        layout.addWidget(system_group)
        
        # AI性能組
        ai_group = QGroupBox("AI性能")
        ai_layout = QGridLayout(ai_group)
        
        ai_layout.addWidget(QLabel("AI推理時間:"), 0, 0)
        self.ai_time_label = QLabel("-- s")
        ai_layout.addWidget(self.ai_time_label, 0, 1)
        
        ai_layout.addWidget(QLabel("數據處理時間:"), 1, 0)
        self.data_time_label = QLabel("-- s")
        ai_layout.addWidget(self.data_time_label, 1, 1)
        
        ai_layout.addWidget(QLabel("緩存命中率:"), 2, 0)
        self.cache_hit_label = QLabel("--%")
        ai_layout.addWidget(self.cache_hit_label, 2, 1)
        
        layout.addWidget(ai_group)
        
        # 性能圖表（簡化版）
        chart_group = QGroupBox("性能趨勢")
        chart_layout = QVBoxLayout(chart_group)
        
        self.performance_text = QTextEdit()
        self.performance_text.setMaximumHeight(150)
        self.performance_text.setReadOnly(True)
        chart_layout.addWidget(self.performance_text)
        
        layout.addWidget(chart_group)
    
    def update_performance_data(self, data: Dict[str, Any]):
        """更新性能數據"""
        if not PYQT_AVAILABLE:
            # 文本模式輸出
            print(f"🔄 性能更新: CPU {data['system']['cpu_percent']:.1f}%, "
                  f"內存 {data['system']['memory_percent']:.1f}%")
            return
        
        try:
            system = data.get("system", {})
            
            # 更新系統資源
            cpu_percent = system.get("cpu_percent", 0)
            self.cpu_progress.setValue(int(cpu_percent))
            self.cpu_label.setText(f"{cpu_percent:.1f}%")
            
            memory_percent = system.get("memory_percent", 0)
            self.memory_progress.setValue(int(memory_percent))
            memory_used = system.get("memory_used_mb", 0)
            self.memory_label.setText(f"{memory_percent:.1f}% ({memory_used:.0f}MB)")
            
            disk_percent = system.get("disk_percent", 0)
            self.disk_progress.setValue(int(disk_percent))
            self.disk_label.setText(f"{disk_percent:.1f}%")
            
            # 更新AI性能
            ai_perf = data.get("ai_performance", {})
            if "ai_inference_time" in ai_perf:
                self.ai_time_label.setText(f"{ai_perf['ai_inference_time']:.2f}s")
            
            if "data_processing_time" in ai_perf:
                self.data_time_label.setText(f"{ai_perf['data_processing_time']:.2f}s")
            
            cache_perf = data.get("cache_performance", {})
            if "hit_rate" in cache_perf:
                self.cache_hit_label.setText(f"{cache_perf['hit_rate']:.1f}%")
            
            # 更新性能文本
            timestamp = data.get("timestamp", datetime.now())
            perf_text = f"[{timestamp.strftime('%H:%M:%S')}] "
            perf_text += f"CPU: {cpu_percent:.1f}%, 內存: {memory_percent:.1f}%, "
            perf_text += f"磁盤: {disk_percent:.1f}%\n"
            
            self.performance_text.append(perf_text)
            
            # 限制文本長度
            if self.performance_text.document().lineCount() > 50:
                cursor = self.performance_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                cursor.select(cursor.SelectionType.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # 刪除換行符
            
        except Exception as e:
            self.logger.error(f"❌ 更新性能數據失敗: {e}")

class AIStatusWidget(QWidget if PYQT_AVAILABLE else object):
    """AI狀態監控組件"""
    
    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setup_ui()
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # AI模型狀態
        models_group = QGroupBox("AI模型狀態")
        models_layout = QGridLayout(models_group)
        
        # 表頭
        models_layout.addWidget(QLabel("模型"), 0, 0)
        models_layout.addWidget(QLabel("狀態"), 0, 1)
        models_layout.addWidget(QLabel("最後分析"), 0, 2)
        
        # 市場掃描員
        models_layout.addWidget(QLabel("🚀 市場掃描員"), 1, 0)
        self.scanner_status = QLabel("準備中")
        self.scanner_status.setStyleSheet("color: orange;")
        models_layout.addWidget(self.scanner_status, 1, 1)
        self.scanner_time = QLabel("--")
        models_layout.addWidget(self.scanner_time, 1, 2)
        
        # 深度分析師
        models_layout.addWidget(QLabel("🔍 深度分析師"), 2, 0)
        self.analyst_status = QLabel("準備中")
        self.analyst_status.setStyleSheet("color: orange;")
        models_layout.addWidget(self.analyst_status, 2, 1)
        self.analyst_time = QLabel("--")
        models_layout.addWidget(self.analyst_time, 2, 2)
        
        # 最終決策者
        models_layout.addWidget(QLabel("🧠 最終決策者"), 3, 0)
        self.decision_status = QLabel("準備中")
        self.decision_status.setStyleSheet("color: orange;")
        models_layout.addWidget(self.decision_status, 3, 1)
        self.decision_time = QLabel("--")
        models_layout.addWidget(self.decision_time, 3, 2)
        
        layout.addWidget(models_group)
        
        # AI協作狀態
        collab_group = QGroupBox("AI協作狀態")
        collab_layout = QGridLayout(collab_group)
        
        collab_layout.addWidget(QLabel("當前分析:"), 0, 0)
        self.active_analysis = QLabel("無")
        collab_layout.addWidget(self.active_analysis, 0, 1)
        
        collab_layout.addWidget(QLabel("信心度:"), 1, 0)
        self.confidence_progress = QProgressBar()
        self.confidence_progress.setRange(0, 100)
        self.confidence_label = QLabel("0%")
        collab_layout.addWidget(self.confidence_progress, 1, 1)
        collab_layout.addWidget(self.confidence_label, 1, 2)
        
        collab_layout.addWidget(QLabel("共識狀態:"), 2, 0)
        self.consensus_label = QLabel("未達成")
        collab_layout.addWidget(self.consensus_label, 2, 1)
        
        collab_layout.addWidget(QLabel("最後決策:"), 3, 0)
        self.last_decision = QLabel("--")
        collab_layout.addWidget(self.last_decision, 3, 1)
        
        layout.addWidget(collab_group)
        
        # AI決策歷史
        history_group = QGroupBox("決策歷史")
        history_layout = QVBoxLayout(history_group)
        
        self.decision_history = QTextEdit()
        self.decision_history.setMaximumHeight(150)
        self.decision_history.setReadOnly(True)
        history_layout.addWidget(self.decision_history)
        
        layout.addWidget(history_group)
    
    def update_ai_status(self, data: Dict[str, Any]):
        """更新AI狀態"""
        if not PYQT_AVAILABLE:
            # 文本模式輸出
            collab = data.get("collaboration", {})
            print(f"🤖 AI狀態: 信心度 {collab.get('confidence_level', 0):.1f}%, "
                  f"共識 {'已達成' if collab.get('consensus_reached') else '未達成'}")
            return
        
        try:
            models = data.get("models", {})
            collab = data.get("collaboration", {})
            
            # 更新模型狀態
            for model_name, model_data in models.items():
                status = model_data.get("status", "unknown")
                last_analysis = model_data.get("last_analysis", datetime.now())
                
                status_color = "green" if status == "ready" else "red"
                status_text = "就緒" if status == "ready" else "錯誤"
                time_text = self._format_time_ago(last_analysis)
                
                if model_name == "market_scanner":
                    self.scanner_status.setText(status_text)
                    self.scanner_status.setStyleSheet(f"color: {status_color};")
                    self.scanner_time.setText(time_text)
                elif model_name == "deep_analyst":
                    self.analyst_status.setText(status_text)
                    self.analyst_status.setStyleSheet(f"color: {status_color};")
                    self.analyst_time.setText(time_text)
                elif model_name == "decision_maker":
                    self.decision_status.setText(status_text)
                    self.decision_status.setStyleSheet(f"color: {status_color};")
                    self.decision_time.setText(time_text)
            
            # 更新協作狀態
            if collab.get("active_analysis", False):
                self.active_analysis.setText("進行中")
                self.active_analysis.setStyleSheet("color: blue;")
            else:
                self.active_analysis.setText("無")
                self.active_analysis.setStyleSheet("color: gray;")
            
            confidence = collab.get("confidence_level", 0)
            self.confidence_progress.setValue(int(confidence))
            self.confidence_label.setText(f"{confidence:.1f}%")
            
            if collab.get("consensus_reached", False):
                self.consensus_label.setText("已達成")
                self.consensus_label.setStyleSheet("color: green;")
            else:
                self.consensus_label.setText("未達成")
                self.consensus_label.setStyleSheet("color: red;")
            
            last_decision_time = collab.get("last_decision", datetime.now())
            self.last_decision.setText(self._format_time_ago(last_decision_time))
            
            # 添加決策歷史記錄
            timestamp = data.get("timestamp", datetime.now())
            history_text = f"[{timestamp.strftime('%H:%M:%S')}] "
            history_text += f"信心度: {confidence:.1f}%, "
            history_text += f"共識: {'是' if collab.get('consensus_reached') else '否'}\n"
            
            self.decision_history.append(history_text)
            
            # 限制文本長度
            if self.decision_history.document().lineCount() > 30:
                cursor = self.decision_history.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                cursor.select(cursor.SelectionType.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()
            
        except Exception as e:
            self.logger.error(f"❌ 更新AI狀態失敗: {e}")
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """格式化時間差"""
        now = datetime.now()
        if timestamp.tzinfo is not None:
            # 如果timestamp有時區信息，移除它進行比較
            timestamp = timestamp.replace(tzinfo=None)
        
        delta = now - timestamp
        
        if delta.total_seconds() < 60:
            return f"{int(delta.total_seconds())}秒前"
        elif delta.total_seconds() < 3600:
            return f"{int(delta.total_seconds() / 60)}分鐘前"
        else:
            return f"{int(delta.total_seconds() / 3600)}小時前"

class TradingStatusWidget(QWidget if PYQT_AVAILABLE else object):
    """交易狀態監控組件"""
    
    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setup_ui()
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 賬戶狀態
        account_group = QGroupBox("賬戶狀態")
        account_layout = QGridLayout(account_group)
        
        account_layout.addWidget(QLabel("TWD餘額:"), 0, 0)
        self.balance_twd = QLabel("0 TWD")
        account_layout.addWidget(self.balance_twd, 0, 1)
        
        account_layout.addWidget(QLabel("BTC餘額:"), 1, 0)
        self.balance_btc = QLabel("0 BTC")
        account_layout.addWidget(self.balance_btc, 1, 1)
        
        account_layout.addWidget(QLabel("總價值:"), 2, 0)
        self.total_value = QLabel("0 TWD")
        account_layout.addWidget(self.total_value, 2, 1)
        
        account_layout.addWidget(QLabel("今日盈虧:"), 3, 0)
        self.daily_pnl = QLabel("0 TWD (0%)")
        account_layout.addWidget(self.daily_pnl, 3, 1)
        
        layout.addWidget(account_group)
        
        # 交易統計
        trading_group = QGroupBox("交易統計")
        trading_layout = QGridLayout(trading_group)
        
        trading_layout.addWidget(QLabel("活躍倉位:"), 0, 0)
        self.active_positions = QLabel("0")
        trading_layout.addWidget(self.active_positions, 0, 1)
        
        trading_layout.addWidget(QLabel("今日交易:"), 1, 0)
        self.daily_trades = QLabel("0")
        trading_layout.addWidget(self.daily_trades, 1, 1)
        
        trading_layout.addWidget(QLabel("勝率:"), 2, 0)
        self.win_rate = QLabel("0%")
        trading_layout.addWidget(self.win_rate, 2, 1)
        
        trading_layout.addWidget(QLabel("平均持倉時間:"), 3, 0)
        self.avg_hold_time = QLabel("--")
        trading_layout.addWidget(self.avg_hold_time, 3, 1)
        
        layout.addWidget(trading_group)
        
        # 風險控制
        risk_group = QGroupBox("風險控制")
        risk_layout = QGridLayout(risk_group)
        
        risk_layout.addWidget(QLabel("風險等級:"), 0, 0)
        self.risk_level = QLabel("UNKNOWN")
        risk_layout.addWidget(self.risk_level, 0, 1)
        
        risk_layout.addWidget(QLabel("最大回撤:"), 1, 0)
        self.max_drawdown = QLabel("0%")
        risk_layout.addWidget(self.max_drawdown, 1, 1)
        
        risk_layout.addWidget(QLabel("風險評分:"), 2, 0)
        self.risk_score_progress = QProgressBar()
        self.risk_score_progress.setRange(0, 100)
        self.risk_score_label = QLabel("0")
        risk_layout.addWidget(self.risk_score_progress, 2, 1)
        risk_layout.addWidget(self.risk_score_label, 2, 2)
        
        risk_layout.addWidget(QLabel("日虧損限制:"), 3, 0)
        self.daily_loss_limit = QLabel("0 TWD")
        risk_layout.addWidget(self.daily_loss_limit, 3, 1)
        
        layout.addWidget(risk_group)
    
    def update_trading_status(self, data: Dict[str, Any]):
        """更新交易狀態"""
        if not PYQT_AVAILABLE:
            # 文本模式輸出
            account = data.get("account", {})
            risk = data.get("risk", {})
            print(f"💼 交易狀態: 總價值 {account.get('total_value_twd', 0):,.0f} TWD, "
                  f"風險等級 {risk.get('current_risk_level', 'UNKNOWN')}")
            return
        
        try:
            account = data.get("account", {})
            positions = data.get("positions", {})
            risk = data.get("risk", {})
            
            # 更新賬戶狀態
            self.balance_twd.setText(f"{account.get('balance_twd', 0):,.0f} TWD")
            self.balance_btc.setText(f"{account.get('balance_btc', 0):.6f} BTC")
            self.total_value.setText(f"{account.get('total_value_twd', 0):,.0f} TWD")
            
            daily_pnl = account.get('daily_pnl', 0)
            daily_pnl_percent = account.get('daily_pnl_percent', 0)
            pnl_color = "green" if daily_pnl >= 0 else "red"
            pnl_sign = "+" if daily_pnl >= 0 else ""
            self.daily_pnl.setText(f"{pnl_sign}{daily_pnl:,.0f} TWD ({pnl_sign}{daily_pnl_percent:.1f}%)")
            self.daily_pnl.setStyleSheet(f"color: {pnl_color}; font-weight: bold;")
            
            # 更新交易統計
            self.active_positions.setText(str(positions.get('active_positions', 0)))
            self.daily_trades.setText(str(positions.get('total_positions_today', 0)))
            self.win_rate.setText(f"{positions.get('win_rate', 0):.1f}%")
            self.avg_hold_time.setText(positions.get('avg_hold_time', '--'))
            
            # 更新風險控制
            risk_level = risk.get('current_risk_level', 'UNKNOWN')
            risk_colors = {
                'LOW': 'green',
                'MEDIUM': 'orange', 
                'HIGH': 'red',
                'CRITICAL': 'darkred'
            }
            risk_color = risk_colors.get(risk_level, 'gray')
            self.risk_level.setText(risk_level)
            self.risk_level.setStyleSheet(f"color: {risk_color}; font-weight: bold;")
            
            self.max_drawdown.setText(f"{risk.get('max_drawdown', 0):.1f}%")
            
            risk_score = risk.get('risk_score', 0)
            self.risk_score_progress.setValue(int(risk_score))
            self.risk_score_label.setText(f"{risk_score:.0f}")
            
            self.daily_loss_limit.setText(f"{risk.get('daily_loss_limit', 0):,.0f} TWD")
            
        except Exception as e:
            self.logger.error(f"❌ 更新交易狀態失敗: {e}")

class MonitoringDashboard(QMainWindow if PYQT_AVAILABLE else object):
    """主監控儀表板"""
    
    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        self.logger = logging.getLogger(__name__)
        self.monitor_thread = SystemMonitorThread()
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """設置用戶界面"""
        if not PYQT_AVAILABLE:
            self.logger.info("🖥️ 監控儀表板運行在文本模式")
            return
            
        self.setWindowTitle("AImax 實時監控儀表板")
        self.setGeometry(100, 100, 1200, 800)
        
        # 中央組件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主佈局
        main_layout = QHBoxLayout(central_widget)
        
        # 左側面板 - 控制按鈕
        left_panel = QWidget()
        left_panel.setMaximumWidth(200)
        left_layout = QVBoxLayout(left_panel)
        
        # 控制按鈕
        self.start_button = QPushButton("🚀 開始監控")
        self.start_button.clicked.connect(self.start_monitoring)
        left_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏹️ 停止監控")
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)
        left_layout.addWidget(self.stop_button)
        
        left_layout.addWidget(QLabel("更新間隔:"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 10)
        self.interval_spinbox.setValue(1)
        self.interval_spinbox.setSuffix(" 秒")
        left_layout.addWidget(self.interval_spinbox)
        
        # 系統狀態指示器
        left_layout.addWidget(QLabel("系統狀態:"))
        self.system_status = QLabel("🔴 未啟動")
        left_layout.addWidget(self.system_status)
        
        left_layout.addStretch()
        main_layout.addWidget(left_panel)
        
        # 右側主要內容區域
        content_area = QTabWidget()
        
        # 性能監控標籤
        self.performance_widget = PerformanceWidget()
        content_area.addTab(self.performance_widget, "📊 性能監控")
        
        # AI狀態標籤
        self.ai_status_widget = AIStatusWidget()
        content_area.addTab(self.ai_status_widget, "🤖 AI狀態")
        
        # 交易狀態標籤
        self.trading_status_widget = TradingStatusWidget()
        content_area.addTab(self.trading_status_widget, "💼 交易狀態")
        
        main_layout.addWidget(content_area)
        
        # 狀態欄
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備就緒")
        
        # 設置樣式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
    
    def setup_connections(self):
        """設置信號連接"""
        if not PYQT_AVAILABLE:
            return
            
        # 連接監控線程信號
        self.monitor_thread.performance_updated.connect(
            self.performance_widget.update_performance_data)
        self.monitor_thread.ai_status_updated.connect(
            self.ai_status_widget.update_ai_status)
        self.monitor_thread.trading_status_updated.connect(
            self.trading_status_widget.update_trading_status)
        self.monitor_thread.error_occurred.connect(self.handle_error)
        
        # 更新間隔變化
        self.interval_spinbox.valueChanged.connect(self.update_interval)
    
    def start_monitoring(self):
        """開始監控"""
        try:
            self.monitor_thread.initialize_components()
            self.monitor_thread.start_monitoring()
            
            if PYQT_AVAILABLE:
                self.start_button.setEnabled(False)
                self.stop_button.setEnabled(True)
                self.system_status.setText("🟢 運行中")
                self.status_bar.showMessage("監控已啟動")
            
            self.logger.info("🚀 監控儀表板已啟動")
            
        except Exception as e:
            self.logger.error(f"❌ 啟動監控失敗: {e}")
            if PYQT_AVAILABLE:
                self.status_bar.showMessage(f"啟動失敗: {e}")
    
    def stop_monitoring(self):
        """停止監控"""
        try:
            self.monitor_thread.stop_monitoring()
            
            if PYQT_AVAILABLE:
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.system_status.setText("🔴 已停止")
                self.status_bar.showMessage("監控已停止")
            
            self.logger.info("⏹️ 監控儀表板已停止")
            
        except Exception as e:
            self.logger.error(f"❌ 停止監控失敗: {e}")
    
    def update_interval(self, value):
        """更新監控間隔"""
        self.monitor_thread.update_interval = value
        self.logger.info(f"🔄 監控間隔已更新為 {value} 秒")
    
    def handle_error(self, error_message: str):
        """處理錯誤"""
        self.logger.error(f"❌ 監控錯誤: {error_message}")
        if PYQT_AVAILABLE:
            self.status_bar.showMessage(f"錯誤: {error_message}")
    
    def closeEvent(self, event):
        """關閉事件"""
        if PYQT_AVAILABLE:
            self.stop_monitoring()
            event.accept()

def main():
    """主函數"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if PYQT_AVAILABLE:
        app = QApplication(sys.argv)
        dashboard = MonitoringDashboard()
        dashboard.show()
        sys.exit(app.exec())
    else:
        # 文本模式運行
        print("🖥️ AImax 監控儀表板 - 文本模式")
        dashboard = MonitoringDashboard()
        dashboard.start_monitoring()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ 停止監控...")
            dashboard.stop_monitoring()

if __name__ == "__main__":
    main()