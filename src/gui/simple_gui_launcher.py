#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化GUI啟動器 - 管理異步啟動流程
確保GUI能夠穩定啟動，避免卡死問題
"""

import sys
import asyncio
import threading
import time
from typing import Optional, Callable, Dict, Any
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread

from .dependency_checker import DependencyChecker
from .splash_screen import SplashScreen, SimpleSplashScreen


class AISystemLoader(QObject):
    """AI系統載入器"""
    
    progress_updated = pyqtSignal(int, str)
    loading_completed = pyqtSignal(bool, str, object)
    
    def __init__(self):
        super().__init__()
        self.ai_manager = None
        self.trade_executor = None
        self.risk_manager = None
        self.system_integrator = None
        self.loading_cancelled = False
    
    def load_ai_system(self):
        """載入AI系統組件"""
        try:
            self.progress_updated.emit(10, "檢查AI系統模組...")
            
            if self.loading_cancelled:
                return
            
            # 載入AI管理器
            self.progress_updated.emit(30, "載入AI管理器...")
            try:
                from src.ai.enhanced_ai_manager import EnhancedAIManager
                self.ai_manager = EnhancedAIManager()
                time.sleep(0.2)  # 模擬載入時間
            except Exception as e:
                self.loading_completed.emit(False, f"AI管理器載入失敗: {str(e)}", None)
                return
            
            if self.loading_cancelled:
                return
            
            # 載入交易執行器
            self.progress_updated.emit(50, "載入交易執行器...")
            try:
                from src.trading.trade_executor import TradeExecutor
                self.trade_executor = TradeExecutor()
                time.sleep(0.2)
            except Exception as e:
                self.loading_completed.emit(False, f"交易執行器載入失敗: {str(e)}", None)
                return
            
            if self.loading_cancelled:
                return
            
            # 載入風險管理器
            self.progress_updated.emit(70, "載入風險管理器...")
            try:
                from src.trading.risk_manager import RiskManager
                self.risk_manager = RiskManager()
                time.sleep(0.2)
            except Exception as e:
                self.loading_completed.emit(False, f"風險管理器載入失敗: {str(e)}", None)
                return
            
            if self.loading_cancelled:
                return
            
            # 載入系統整合器
            self.progress_updated.emit(90, "載入系統整合器...")
            try:
                from src.core.trading_system_integrator import TradingSystemIntegrator
                self.system_integrator = TradingSystemIntegrator()
                time.sleep(0.2)
            except Exception as e:
                self.loading_completed.emit(False, f"系統整合器載入失敗: {str(e)}", None)
                return
            
            if self.loading_cancelled:
                return
            
            # 創建系統組件字典
            ai_components = {
                'ai_manager': self.ai_manager,
                'trade_executor': self.trade_executor,
                'risk_manager': self.risk_manager,
                'system_integrator': self.system_integrator
            }
            
            self.progress_updated.emit(100, "AI系統載入完成！")
            self.loading_completed.emit(True, "AI系統載入成功", ai_components)
            
        except Exception as e:
            self.loading_completed.emit(False, f"AI系統載入失敗: {str(e)}", None)
    
    def cancel_loading(self):
        """取消載入"""
        self.loading_cancelled = True


class SimpleGUILauncher(QObject):
    """簡化GUI啟動器"""
    
    gui_ready = pyqtSignal(object)  # 發送主視窗對象
    launch_failed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.app = None
        self.splash_screen = None
        self.main_window = None
        self.ai_components = None
        self.dependency_checker = DependencyChecker()
        
        # AI系統載入器
        self.ai_loader_thread = QThread()
        self.ai_loader = AISystemLoader()
        self.ai_loader.moveToThread(self.ai_loader_thread)
        
        # 連接信號
        self.ai_loader.progress_updated.connect(self.on_loading_progress)
        self.ai_loader.loading_completed.connect(self.on_ai_loading_completed)
        self.ai_loader_thread.started.connect(self.ai_loader.load_ai_system)
    
    def create_application(self) -> bool:
        """創建QApplication"""
        try:
            if QApplication.instance() is None:
                self.app = QApplication(sys.argv)
                self.app.setApplicationName("AImax AI交易系統")
                self.app.setApplicationVersion("2.0")
                
                # 設置應用程式樣式
                self.app.setStyleSheet("""
                    QApplication {
                        font-family: "Microsoft YaHei", "Arial", sans-serif;
                        font-size: 10pt;
                    }
                """)
            else:
                self.app = QApplication.instance()
            
            return True
        except Exception as e:
            print(f"創建應用程式失敗: {e}")
            return False
    
    def check_dependencies(self) -> bool:
        """檢查系統依賴"""
        try:
            results = self.dependency_checker.check_all_dependencies()
            
            if not results['overall_status']:
                # 顯示依賴問題
                error_msg = self.dependency_checker.generate_installation_guide(results)
                self.show_error_dialog("依賴檢查失敗", error_msg)
                return False
            
            return True
        except Exception as e:
            self.show_error_dialog("依賴檢查錯誤", f"檢查依賴時發生錯誤: {str(e)}")
            return False
    
    def show_error_dialog(self, title: str, message: str):
        """顯示錯誤對話框"""
        try:
            if self.app:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle(title)
                msg_box.setText(message)
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()
        except Exception as e:
            print(f"顯示錯誤對話框失敗: {e}")
            print(f"{title}: {message}")
    
    def create_splash_screen(self) -> bool:
        """創建啟動畫面"""
        try:
            # 嘗試創建完整的啟動畫面
            try:
                self.splash_screen = SplashScreen()
                self.splash_screen.loading_finished.connect(self.on_splash_finished)
                return True
            except Exception as e:
                print(f"創建完整啟動畫面失敗，使用簡化版: {e}")
                
                # 使用簡化版啟動畫面
                self.splash_screen = SimpleSplashScreen()
                return True
                
        except Exception as e:
            print(f"創建啟動畫面失敗: {e}")
            return False
    
    def launch_gui(self) -> bool:
        """啟動GUI"""
        try:
            # 1. 創建應用程式
            if not self.create_application():
                return False
            
            # 2. 檢查依賴
            if not self.check_dependencies():
                return False
            
            # 3. 創建啟動畫面
            if not self.create_splash_screen():
                return False
            
            # 4. 顯示啟動畫面
            self.splash_screen.show()
            
            # 5. 開始載入AI系統
            if hasattr(self.splash_screen, 'start_loading'):
                # 完整版啟動畫面
                self.splash_screen.start_loading()
            else:
                # 簡化版啟動畫面
                self.splash_screen.update_status("載入AI系統...")
                QTimer.singleShot(500, self.start_ai_loading)
            
            return True
            
        except Exception as e:
            self.launch_failed.emit(f"GUI啟動失敗: {str(e)}")
            return False
    
    def start_ai_loading(self):
        """開始載入AI系統"""
        try:
            self.ai_loader_thread.start()
        except Exception as e:
            self.on_ai_loading_completed(False, f"啟動AI載入失敗: {str(e)}", None)
    
    def on_loading_progress(self, progress: int, message: str):
        """載入進度更新"""
        if hasattr(self.splash_screen, 'update_progress'):
            self.splash_screen.update_progress(progress, message)
        elif hasattr(self.splash_screen, 'update_status'):
            self.splash_screen.update_status(message)
    
    def on_splash_finished(self, success: bool, message: str):
        """啟動畫面完成"""
        if success:
            self.start_ai_loading()
        else:
            self.launch_failed.emit(message)
    
    def on_ai_loading_completed(self, success: bool, message: str, components: Optional[Dict]):
        """AI系統載入完成"""
        try:
            if success and components:
                self.ai_components = components
                self.create_main_window()
            else:
                self.launch_failed.emit(message)
                
        except Exception as e:
            self.launch_failed.emit(f"處理AI載入結果失敗: {str(e)}")
    
    def create_main_window(self):
        """創建主視窗"""
        try:
            # 導入交易主視窗
            from .trading_main_window import TradingMainWindow
            
            self.main_window = TradingMainWindow()
            
            # 關閉啟動畫面
            if self.splash_screen:
                self.splash_screen.close()
            
            # 顯示主視窗
            self.main_window.show()
            
            # 發送GUI準備完成信號
            self.gui_ready.emit(self.main_window)
            
        except Exception as e:
            self.launch_failed.emit(f"創建主視窗失敗: {str(e)}")
    
    def create_temporary_window(self):
        """創建臨時視窗（用於測試）"""
        try:
            from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
            
            class TemporaryWindow(QMainWindow):
                def __init__(self):
                    super().__init__()
                    self.setWindowTitle("AImax AI交易系統 - 臨時界面")
                    self.setGeometry(100, 100, 800, 600)
                    
                    central_widget = QWidget()
                    layout = QVBoxLayout()
                    
                    label = QLabel("✅ GUI啟動成功！\n\n主視窗正在開發中...")
                    label.setStyleSheet("""
                        QLabel {
                            font-size: 16px;
                            padding: 20px;
                            text-align: center;
                        }
                    """)
                    
                    layout.addWidget(label)
                    central_widget.setLayout(layout)
                    self.setCentralWidget(central_widget)
            
            self.main_window = TemporaryWindow()
            
            # 關閉啟動畫面
            if self.splash_screen:
                self.splash_screen.close()
            
            # 顯示臨時視窗
            self.main_window.show()
            
            # 發送GUI準備完成信號
            self.gui_ready.emit(self.main_window)
            
        except Exception as e:
            self.launch_failed.emit(f"創建臨時視窗失敗: {str(e)}")
    
    def cleanup(self):
        """清理資源"""
        try:
            if self.ai_loader_thread.isRunning():
                self.ai_loader.cancel_loading()
                self.ai_loader_thread.quit()
                self.ai_loader_thread.wait(2000)
            
            if self.splash_screen:
                self.splash_screen.close()
                
        except Exception as e:
            print(f"清理資源時發生錯誤: {e}")


if __name__ == "__main__":
    # 測試GUI啟動器
    launcher = SimpleGUILauncher()
    
    def on_gui_ready(main_window):
        print("✅ GUI啟動成功！")
    
    def on_launch_failed(error_message):
        print(f"❌ GUI啟動失敗: {error_message}")
        sys.exit(1)
    
    launcher.gui_ready.connect(on_gui_ready)
    launcher.launch_failed.connect(on_launch_failed)
    
    if launcher.launch_gui():
        sys.exit(launcher.app.exec())
    else:
        print("❌ 無法啟動GUI")
        sys.exit(1)