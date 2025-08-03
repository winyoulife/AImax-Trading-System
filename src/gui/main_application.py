"""
AImax 主GUI應用程序 - 整合所有GUI組件
"""
import sys
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import threading

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QMenuBar, QMenu, QStatusBar, QSplitter, QTabWidget, QMessageBox,
        QDialog, QDialogButtonBox, QTextEdit, QLabel, QPushButton,
        QSystemTrayIcon, QStyle, QProgressDialog
    )
    from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThread
    from PyQt6.QtGui import QAction, QIcon, QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt6 未安裝，GUI將使用文本模式")

# 導入GUI組件
from .component_manager import ComponentManager, ComponentStatus
from .error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
from .state_manager import StateManager
from .monitoring_dashboard import MonitoringDashboard

# 導入AImax核心組件
sys.path.append(str(Path(__file__).parent.parent))

class InitializationDialog(QDialog if PYQT_AVAILABLE else object):
    """初始化進度對話框"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        self.setWindowTitle("AImax 系統初始化")
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout(self)
        
        self.status_label = QLabel("準備初始化...")
        layout.addWidget(self.status_label)
        
        self.progress_text = QTextEdit()
        self.progress_text.setMaximumHeight(100)
        self.progress_text.setReadOnly(True)
        layout.addWidget(self.progress_text)
        
        # 按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def update_progress(self, current: int, total: int, message: str):
        """更新進度"""
        if not PYQT_AVAILABLE:
            print(f"初始化進度: {current}/{total} - {message}")
            return
            
        self.status_label.setText(f"初始化進度: {current}/{total}")
        self.progress_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

class ErrorDialog(QDialog if PYQT_AVAILABLE else object):
    """錯誤顯示對話框"""
    
    def __init__(self, title: str, message: str, details: str = None, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.title = title
        self.message = message
        self.details = details
        self.setup_ui()
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            print(f"錯誤: {self.title}\n{self.message}")
            if self.details:
                print(f"詳情: {self.details}")
            return
            
        self.setWindowTitle(self.title)
        self.setModal(True)
        self.resize(500, 300)
        
        layout = QVBoxLayout(self)
        
        # 錯誤消息
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # 詳細信息
        if self.details:
            details_text = QTextEdit()
            details_text.setPlainText(self.details)
            details_text.setReadOnly(True)
            layout.addWidget(details_text)
        
        # 按鈕
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Retry
        )
        button_box.accepted.connect(self.accept)
        button_box.button(QDialogButtonBox.StandardButton.Retry).clicked.connect(
            lambda: self.done(2)  # 返回2表示重試
        )
        layout.addWidget(button_box)

class ModernAITradingGUI(QMainWindow if PYQT_AVAILABLE else object):
    """
    現代化AI交易系統GUI主窗口
    
    功能:
    - 整合所有GUI組件
    - 提供統一的用戶界面
    - 管理組件生命週期
    - 處理系統錯誤和狀態
    """
    
    def __init__(self):
        if PYQT_AVAILABLE:
            super().__init__()
        
        self.logger = logging.getLogger(__name__)
        
        # 核心管理器
        self.component_manager = ComponentManager()
        self.error_handler = ErrorHandler(self)
        self.state_manager = StateManager()
        
        # GUI組件
        self.monitoring_dashboard = None
        self.system_tray = None
        
        # 初始化狀態
        self.initialization_complete = False
        self.shutdown_in_progress = False
        
        # 設置GUI
        self.setup_ui()
        self.setup_system_tray()
        self.register_components()
        
        # 載入保存的狀態
        self.load_application_state()
        
        self.logger.info("🚀 AImax GUI主窗口初始化完成")
    
    def setup_ui(self):
        """設置用戶界面"""
        if not PYQT_AVAILABLE:
            self.logger.info("🖥️ GUI運行在文本模式")
            return
            
        self.setWindowTitle("AImax - 多AI協作交易系統")
        self.setGeometry(100, 100, 1400, 900)
        
        # 設置應用程序圖標
        self.setWindowIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        # 創建菜單欄
        self.create_menu_bar()
        
        # 創建中央組件
        self.create_central_widget()
        
        # 創建狀態欄
        self.create_status_bar()
        
        # 設置樣式
        self.apply_modern_style()
    
    def create_menu_bar(self):
        """創建菜單欄"""
        if not PYQT_AVAILABLE:
            return
            
        menubar = self.menuBar()
        
        # 文件菜單
        file_menu = menubar.addMenu('文件')
        
        # 導出狀態
        export_action = QAction('導出狀態', self)
        export_action.triggered.connect(self.export_application_state)
        file_menu.addAction(export_action)
        
        # 導入狀態
        import_action = QAction('導入狀態', self)
        import_action.triggered.connect(self.import_application_state)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 系統菜單
        system_menu = menubar.addMenu('系統')
        
        # 重啟組件
        restart_action = QAction('重啟所有組件', self)
        restart_action.triggered.connect(self.restart_all_components)
        system_menu.addAction(restart_action)
        
        # 系統診斷
        diagnostic_action = QAction('系統診斷', self)
        diagnostic_action.triggered.connect(self.show_system_diagnostic)
        system_menu.addAction(diagnostic_action)
        
        # 錯誤報告
        error_report_action = QAction('錯誤報告', self)
        error_report_action.triggered.connect(self.show_error_report)
        system_menu.addAction(error_report_action)
        
        # 幫助菜單
        help_menu = menubar.addMenu('幫助')
        
        # 關於
        about_action = QAction('關於 AImax', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_central_widget(self):
        """創建中央組件"""
        if not PYQT_AVAILABLE:
            return
            
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主佈局
        main_layout = QVBoxLayout(central_widget)
        
        # 創建標籤頁
        self.tab_widget = QTabWidget()
        
        # 監控儀表板標籤
        self.monitoring_dashboard = MonitoringDashboard()
        self.tab_widget.addTab(self.monitoring_dashboard, "📊 實時監控")
        
        # 系統狀態標籤
        self.system_status_widget = self.create_system_status_widget()
        self.tab_widget.addTab(self.system_status_widget, "🔧 系統狀態")
        
        main_layout.addWidget(self.tab_widget)
    
    def create_system_status_widget(self) -> QWidget:
        """創建系統狀態組件"""
        if not PYQT_AVAILABLE:
            return None
            
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 組件狀態顯示
        self.component_status_text = QTextEdit()
        self.component_status_text.setReadOnly(True)
        layout.addWidget(QLabel("組件狀態:"))
        layout.addWidget(self.component_status_text)
        
        # 控制按鈕
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("🔄 刷新狀態")
        refresh_button.clicked.connect(self.refresh_component_status)
        button_layout.addWidget(refresh_button)
        
        restart_button = QPushButton("🔄 重啟組件")
        restart_button.clicked.connect(self.restart_all_components)
        button_layout.addWidget(restart_button)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def create_status_bar(self):
        """創建狀態欄"""
        if not PYQT_AVAILABLE:
            return
            
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 系統狀態指示器
        self.system_status_label = QLabel("🔴 系統未初始化")
        self.status_bar.addWidget(self.system_status_label)
        
        # 組件計數
        self.component_count_label = QLabel("組件: 0/0")
        self.status_bar.addPermanentWidget(self.component_count_label)
        
        # 時間顯示
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)
        
        # 定時更新時間
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time_display)
        self.time_timer.start(1000)  # 每秒更新
    
    def setup_system_tray(self):
        """設置系統托盤"""
        if not PYQT_AVAILABLE or not QSystemTrayIcon.isSystemTrayAvailable():
            return
            
        self.system_tray = QSystemTrayIcon(self)
        self.system_tray.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        # 托盤菜單
        tray_menu = QMenu()
        
        show_action = tray_menu.addAction("顯示主窗口")
        show_action.triggered.connect(self.show)
        
        tray_menu.addSeparator()
        
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self.close)
        
        self.system_tray.setContextMenu(tray_menu)
        self.system_tray.activated.connect(self.tray_icon_activated)
        
        self.system_tray.show()
    
    def register_components(self):
        """註冊GUI組件"""
        try:
            # 註冊核心組件（無依賴）
            self.component_manager.register_component(
                "error_handler", 
                type(self.error_handler),
                dependencies=[]
            )
            
            self.component_manager.register_component(
                "state_manager",
                type(self.state_manager),
                dependencies=[]
            )
            
            # 註冊監控組件（依賴核心組件）
            if self.monitoring_dashboard:
                self.component_manager.register_component(
                    "monitoring_dashboard",
                    type(self.monitoring_dashboard),
                    dependencies=["error_handler", "state_manager"]
                )
            
            # 設置進度回調
            if PYQT_AVAILABLE:
                self.component_manager.set_progress_callback(self.on_initialization_progress)
            
            self.logger.info("✅ GUI組件註冊完成")
            
        except Exception as e:
            self.logger.error(f"❌ 組件註冊失敗: {e}")
            self.error_handler.handle_exception(
                e, "component_registration", 
                ErrorCategory.INITIALIZATION, 
                ErrorSeverity.HIGH
            )
    
    def initialize_application(self):
        """初始化應用程序"""
        if not PYQT_AVAILABLE:
            self.logger.info("🚀 開始初始化應用程序（文本模式）")
            success = self.component_manager.initialize_components()
            if success:
                self.initialization_complete = True
                self.logger.info("✅ 應用程序初始化完成")
            else:
                self.logger.error("❌ 應用程序初始化失敗")
            return success
        
        # 顯示初始化對話框
        init_dialog = InitializationDialog(self)
        init_dialog.show()
        
        # 在後台線程中初始化
        def init_worker():
            try:
                success = self.component_manager.initialize_components()
                
                if success:
                    self.initialization_complete = True
                    self.system_status_label.setText("🟢 系統運行正常")
                    self.logger.info("✅ 應用程序初始化完成")
                else:
                    self.system_status_label.setText("🟡 系統部分功能不可用")
                    self.logger.warning("⚠️ 應用程序初始化部分失敗")
                
                # 關閉初始化對話框
                init_dialog.accept()
                
                # 更新組件狀態顯示
                self.refresh_component_status()
                
            except Exception as e:
                self.logger.error(f"❌ 初始化過程中發生錯誤: {e}")
                self.error_handler.handle_exception(
                    e, "application_initialization",
                    ErrorCategory.INITIALIZATION,
                    ErrorSeverity.CRITICAL
                )
                init_dialog.reject()
        
        # 啟動初始化線程
        init_thread = threading.Thread(target=init_worker)
        init_thread.daemon = True
        init_thread.start()
        
        return init_dialog.exec() == QDialog.DialogCode.Accepted
    
    def on_initialization_progress(self, current: int, total: int, message: str):
        """初始化進度回調"""
        if PYQT_AVAILABLE:
            self.component_count_label.setText(f"組件: {current}/{total}")
        
        self.logger.info(f"初始化進度: {current}/{total} - {message}")
    
    def show_error_dialog(self, message: str, details: str = None):
        """顯示錯誤對話框"""
        if not PYQT_AVAILABLE:
            print(f"錯誤: {message}")
            if details:
                print(f"詳情: {details}")
            return
        
        dialog = ErrorDialog("系統錯誤", message, details, self)
        result = dialog.exec()
        
        if result == 2:  # 重試
            self.restart_all_components()
    
    def restart_all_components(self):
        """重啟所有組件"""
        try:
            self.logger.info("🔄 開始重啟所有組件...")
            
            if PYQT_AVAILABLE:
                self.system_status_label.setText("🟡 重啟中...")
            
            # 關閉現有組件
            self.component_manager.shutdown_all_components()
            
            # 重新初始化
            success = self.component_manager.initialize_components()
            
            if success:
                if PYQT_AVAILABLE:
                    self.system_status_label.setText("🟢 系統運行正常")
                self.logger.info("✅ 所有組件重啟成功")
            else:
                if PYQT_AVAILABLE:
                    self.system_status_label.setText("🔴 重啟失敗")
                self.logger.error("❌ 組件重啟失敗")
            
            self.refresh_component_status()
            
        except Exception as e:
            self.logger.error(f"❌ 重啟組件時發生錯誤: {e}")
            self.error_handler.handle_exception(
                e, "component_restart",
                ErrorCategory.RUNTIME,
                ErrorSeverity.HIGH
            )
    
    def refresh_component_status(self):
        """刷新組件狀態顯示"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            report = self.component_manager.get_initialization_report()
            
            status_text = f"組件狀態報告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            status_text += "=" * 50 + "\n\n"
            
            status_text += f"總組件數: {report['total_components']}\n"
            status_text += f"就緒組件: {report['ready_components']}\n"
            status_text += f"失敗組件: {report['failed_components']}\n"
            status_text += f"禁用組件: {report['disabled_components']}\n\n"
            
            status_text += "組件詳情:\n"
            status_text += "-" * 30 + "\n"
            
            for name, details in report['component_details'].items():
                status_icon = {
                    'ready': '🟢',
                    'error': '🔴',
                    'disabled': '🟡',
                    'initializing': '🔵',
                    'retrying': '🟠'
                }.get(details['status'], '⚪')
                
                status_text += f"{status_icon} {name}: {details['status']}\n"
                
                if details['last_error']:
                    status_text += f"   錯誤: {details['last_error']}\n"
                
                if details['retry_count'] > 0:
                    status_text += f"   重試次數: {details['retry_count']}\n"
                
                status_text += "\n"
            
            self.component_status_text.setPlainText(status_text)
            
        except Exception as e:
            self.logger.error(f"❌ 刷新組件狀態失敗: {e}")
    
    def show_system_diagnostic(self):
        """顯示系統診斷"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            diagnostic_info = {
                "系統時間": datetime.now().isoformat(),
                "初始化狀態": "完成" if self.initialization_complete else "未完成",
                "組件管理器": self.component_manager.get_initialization_report(),
                "狀態管理器": self.state_manager.get_state_summary(),
                "錯誤統計": self.error_handler.get_error_statistics()
            }
            
            dialog = QDialog(self)
            dialog.setWindowTitle("系統診斷")
            dialog.resize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(json.dumps(diagnostic_info, indent=2, ensure_ascii=False))
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            button_box.accepted.connect(dialog.accept)
            layout.addWidget(button_box)
            
            dialog.exec()
            
        except Exception as e:
            self.logger.error(f"❌ 顯示系統診斷失敗: {e}")
    
    def show_error_report(self):
        """顯示錯誤報告"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            error_report = self.error_handler.generate_error_report()
            
            dialog = QDialog(self)
            dialog.setWindowTitle("錯誤報告")
            dialog.resize(700, 500)
            
            layout = QVBoxLayout(dialog)
            
            text_edit = QTextEdit()
            text_edit.setPlainText(error_report)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            button_layout = QHBoxLayout()
            
            clear_button = QPushButton("清空錯誤日誌")
            clear_button.clicked.connect(self.error_handler.clear_error_log)
            clear_button.clicked.connect(dialog.accept)
            button_layout.addWidget(clear_button)
            
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
            button_box.accepted.connect(dialog.accept)
            button_layout.addWidget(button_box)
            
            layout.addLayout(button_layout)
            
            dialog.exec()
            
        except Exception as e:
            self.logger.error(f"❌ 顯示錯誤報告失敗: {e}")
    
    def show_about(self):
        """顯示關於對話框"""
        if not PYQT_AVAILABLE:
            return
            
        about_text = """
        <h2>AImax - 多AI協作交易系統</h2>
        <p><b>版本:</b> 1.0.0</p>
        <p><b>開發時間:</b> 2025年1月</p>
        
        <h3>核心特色:</h3>
        <ul>
        <li>🚀 三AI專業分工協作</li>
        <li>⚡ 超短線交易能力</li>
        <li>🛡️ 多層風險控制</li>
        <li>📊 實時性能監控</li>
        <li>🔧 智能錯誤恢復</li>
        </ul>
        
        <h3>AI團隊:</h3>
        <ul>
        <li>🚀 市場掃描員 (llama2:7b)</li>
        <li>🔍 深度分析師 (qwen:7b)</li>
        <li>🧠 最終決策者 (qwen:7b)</li>
        </ul>
        
        <p><i>讓AI為你交易，讓智慧創造財富！</i></p>
        """
        
        QMessageBox.about(self, "關於 AImax", about_text)
    
    def load_application_state(self):
        """載入應用程序狀態"""
        try:
            # 載入窗口幾何
            if PYQT_AVAILABLE:
                geometry = self.state_manager.get_global_state("window_geometry")
                if geometry:
                    self.restoreGeometry(geometry)
            
            self.logger.info("✅ 應用程序狀態載入完成")
            
        except Exception as e:
            self.logger.error(f"❌ 載入應用程序狀態失敗: {e}")
    
    def save_application_state(self):
        """保存應用程序狀態"""
        try:
            # 保存窗口幾何
            if PYQT_AVAILABLE:
                self.state_manager.set_global_state("window_geometry", self.saveGeometry())
            
            # 保存其他狀態
            self.state_manager.set_global_state("last_close_time", datetime.now().isoformat())
            
            self.logger.info("✅ 應用程序狀態保存完成")
            
        except Exception as e:
            self.logger.error(f"❌ 保存應用程序狀態失敗: {e}")
    
    def export_application_state(self):
        """導出應用程序狀態"""
        if not PYQT_AVAILABLE:
            return
            
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "導出狀態", "aimax_state.json", "JSON files (*.json)"
        )
        
        if filename:
            if self.state_manager.export_state(filename):
                QMessageBox.information(self, "成功", f"狀態已導出到: {filename}")
            else:
                QMessageBox.warning(self, "失敗", "導出狀態失敗")
    
    def import_application_state(self):
        """導入應用程序狀態"""
        if not PYQT_AVAILABLE:
            return
            
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getOpenFileName(
            self, "導入狀態", "", "JSON files (*.json)"
        )
        
        if filename:
            if self.state_manager.import_state(filename):
                QMessageBox.information(self, "成功", "狀態導入成功，重啟應用程序以生效")
            else:
                QMessageBox.warning(self, "失敗", "導入狀態失敗")
    
    def update_time_display(self):
        """更新時間顯示"""
        if PYQT_AVAILABLE:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.time_label.setText(current_time)
    
    def tray_icon_activated(self, reason):
        """系統托盤圖標激活"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def apply_modern_style(self):
        """應用現代化樣式"""
        if not PYQT_AVAILABLE:
            return
            
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #e1e1e1;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #4CAF50;
        }
        
        QStatusBar {
            background-color: #e1e1e1;
            border-top: 1px solid #c0c0c0;
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
        
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        """
        
        self.setStyleSheet(style)
    
    def closeEvent(self, event):
        """關閉事件"""
        if self.shutdown_in_progress:
            event.accept()
            return
        
        self.shutdown_in_progress = True
        
        try:
            # 保存應用程序狀態
            self.save_application_state()
            
            # 關閉所有組件
            self.component_manager.shutdown_all_components()
            
            # 隱藏系統托盤
            if self.system_tray:
                self.system_tray.hide()
            
            self.logger.info("✅ 應用程序正常關閉")
            
        except Exception as e:
            self.logger.error(f"❌ 關閉應用程序時發生錯誤: {e}")
        
        event.accept()

def main():
    """主函數"""
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('AImax/logs/gui.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("🚀 啟動 AImax GUI應用程序")
    
    if PYQT_AVAILABLE:
        app = QApplication(sys.argv)
        app.setApplicationName("AImax")
        app.setApplicationVersion("1.0.0")
        
        # 創建主窗口
        main_window = ModernAITradingGUI()
        
        # 初始化應用程序
        if main_window.initialize_application():
            main_window.show()
            sys.exit(app.exec())
        else:
            logger.error("❌ 應用程序初始化失敗")
            sys.exit(1)
    else:
        # 文本模式
        logger.info("🖥️ 運行在文本模式")
        main_window = ModernAITradingGUI()
        
        if main_window.initialize_application():
            logger.info("✅ 文本模式應用程序運行成功")
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("⏹️ 用戶中斷，正在關閉...")
        else:
            logger.error("❌ 文本模式應用程序初始化失敗")

if __name__ == "__main__":
    main()