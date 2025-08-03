#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
診斷系統 - 收集和分析系統診斷資訊
提供錯誤分類、友好訊息顯示和診斷資訊收集功能
"""

import os
import sys
import time
import json
import platform
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QTabWidget, QWidget


@dataclass
class DiagnosticInfo:
    """診斷資訊"""
    timestamp: datetime
    category: str
    level: str  # INFO, WARNING, ERROR, CRITICAL
    message: str
    details: Dict[str, Any]
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class SystemDiagnostics:
    """系統診斷收集器"""
    
    @staticmethod
    def collect_system_info() -> Dict[str, Any]:
        """收集系統資訊"""
        try:
            info = {
                'platform': {
                    'system': platform.system(),
                    'release': platform.release(),
                    'version': platform.version(),
                    'machine': platform.machine(),
                    'processor': platform.processor(),
                    'architecture': platform.architecture(),
                },
                'python': {
                    'version': sys.version,
                    'executable': sys.executable,
                    'path': sys.path[:5],  # 只取前5個路徑
                },
                'environment': {
                    'cwd': os.getcwd(),
                    'user': os.environ.get('USER', os.environ.get('USERNAME', 'unknown')),
                    'home': os.environ.get('HOME', os.environ.get('USERPROFILE', 'unknown')),
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # 添加記憶體資訊
            try:
                import psutil
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                info['resources'] = {
                    'memory': {
                        'total': memory.total,
                        'available': memory.available,
                        'percent': memory.percent,
                        'used': memory.used,
                        'free': memory.free
                    },
                    'disk': {
                        'total': disk.total,
                        'used': disk.used,
                        'free': disk.free,
                        'percent': (disk.used / disk.total) * 100
                    },
                    'cpu_count': psutil.cpu_count(),
                    'cpu_percent': psutil.cpu_percent(interval=1)
                }
            except ImportError:
                info['resources'] = {'error': 'psutil not available'}
            
            return info
            
        except Exception as e:
            return {'error': f'Failed to collect system info: {str(e)}'}
    
    @staticmethod
    def collect_application_info() -> Dict[str, Any]:
        """收集應用程式資訊"""
        try:
            from PyQt6.QtWidgets import QApplication
            
            info = {
                'qt_version': '6.x',
                'application_name': 'AImax AI Trading System',
                'version': '2.0',
                'startup_time': datetime.now().isoformat(),
            }
            
            # 如果QApplication存在，收集更多資訊
            if QApplication.instance():
                app = QApplication.instance()
                info.update({
                    'app_name': app.applicationName(),
                    'app_version': app.applicationVersion(),
                    'organization_name': app.organizationName(),
                    'organization_domain': app.organizationDomain(),
                })
            
            return info
            
        except Exception as e:
            return {'error': f'Failed to collect application info: {str(e)}'}
    
    @staticmethod
    def collect_ai_system_info(ai_connector=None) -> Dict[str, Any]:
        """收集AI系統資訊"""
        try:
            if not ai_connector:
                return {'status': 'no_connector', 'message': 'AI connector not available'}
            
            info = {
                'connected': ai_connector.is_system_connected(),
                'demo_mode': getattr(ai_connector, 'demo_mode', True),
                'ai_status': ai_connector.get_ai_status(),
                'trading_status': ai_connector.get_trading_status(),
                'system_info': ai_connector.get_ai_system_info(),
            }
            
            return info
            
        except Exception as e:
            return {'error': f'Failed to collect AI system info: {str(e)}'}
    
    @staticmethod
    def collect_error_logs(error_recovery=None) -> Dict[str, Any]:
        """收集錯誤日誌"""
        try:
            if not error_recovery:
                return {'status': 'no_error_recovery', 'message': 'Error recovery system not available'}
            
            stats = error_recovery.get_error_statistics()
            recent_errors = []
            
            # 獲取最近的錯誤
            for error in error_recovery.error_history[-10:]:  # 最近10個錯誤
                recent_errors.append({
                    'timestamp': error.timestamp.isoformat(),
                    'type': error.error_type.value,
                    'message': error.message,
                    'component': error.component,
                    'severity': error.severity
                })
            
            return {
                'statistics': stats,
                'recent_errors': recent_errors,
                'fallback_mode': error_recovery.is_in_fallback_mode
            }
            
        except Exception as e:
            return {'error': f'Failed to collect error logs: {str(e)}'}


class ErrorClassifier:
    """錯誤分類器"""
    
    ERROR_PATTERNS = {
        'connection': {
            'keywords': ['connection', 'connect', 'network', 'timeout', 'unreachable'],
            'friendly_message': '網路連接問題，請檢查網路設定',
            'suggestions': [
                '檢查網路連接',
                '重新啟動應用程式',
                '聯繫技術支援'
            ]
        },
        'memory': {
            'keywords': ['memory', 'ram', 'out of memory', 'allocation'],
            'friendly_message': '記憶體不足，請關閉其他應用程式',
            'suggestions': [
                '關閉不必要的應用程式',
                '重新啟動系統',
                '增加系統記憶體'
            ]
        },
        'permission': {
            'keywords': ['permission', 'access denied', 'forbidden', 'unauthorized'],
            'friendly_message': '權限不足，請以管理員身份運行',
            'suggestions': [
                '以管理員身份運行',
                '檢查文件權限',
                '聯繫系統管理員'
            ]
        },
        'file': {
            'keywords': ['file not found', 'no such file', 'directory', 'path'],
            'friendly_message': '文件或目錄不存在',
            'suggestions': [
                '檢查文件路徑',
                '重新安裝應用程式',
                '恢復缺失文件'
            ]
        },
        'ai_system': {
            'keywords': ['ai', 'model', 'prediction', 'inference', 'ollama'],
            'friendly_message': 'AI系統錯誤，正在嘗試恢復',
            'suggestions': [
                '等待系統自動恢復',
                '重新啟動AI服務',
                '檢查AI模型文件'
            ]
        },
        'trading': {
            'keywords': ['trading', 'order', 'balance', 'exchange', 'api'],
            'friendly_message': '交易系統錯誤，請檢查交易設定',
            'suggestions': [
                '檢查API密鑰',
                '驗證帳戶餘額',
                '聯繫交易所客服'
            ]
        }
    }
    
    @classmethod
    def classify_error(cls, error_message: str) -> Dict[str, Any]:
        """分類錯誤並提供友好訊息"""
        error_message_lower = error_message.lower()
        
        for category, info in cls.ERROR_PATTERNS.items():
            if any(keyword in error_message_lower for keyword in info['keywords']):
                return {
                    'category': category,
                    'friendly_message': info['friendly_message'],
                    'suggestions': info['suggestions'],
                    'original_message': error_message
                }
        
        # 未分類的錯誤
        return {
            'category': 'unknown',
            'friendly_message': '發生未知錯誤，請聯繫技術支援',
            'suggestions': [
                '重新啟動應用程式',
                '檢查系統日誌',
                '聯繫技術支援'
            ],
            'original_message': error_message
        }


class DiagnosticSystem(QObject):
    """診斷系統主類"""
    
    diagnostic_collected = pyqtSignal(object)  # DiagnosticInfo
    report_generated = pyqtSignal(str)  # 報告路徑
    
    def __init__(self, ai_connector=None, error_recovery=None):
        super().__init__()
        
        self.ai_connector = ai_connector
        self.error_recovery = error_recovery
        
        # 診斷資訊歷史
        self.diagnostic_history: List[DiagnosticInfo] = []
        self.max_history_size = 500
        
        # 自動診斷定時器
        self.auto_diagnostic_timer = QTimer()
        self.auto_diagnostic_timer.timeout.connect(self.run_auto_diagnostics)
        
    def start_auto_diagnostics(self, interval_minutes: int = 10):
        """開始自動診斷"""
        try:
            self.auto_diagnostic_timer.start(int(interval_minutes * 60 * 1000))  # 轉換為毫秒
            self.add_diagnostic(
                'system',
                'INFO',
                f'自動診斷已啟動，間隔 {interval_minutes} 分鐘',
                {'interval': interval_minutes}
            )
        except Exception as e:
            print(f"啟動自動診斷失敗: {e}")
    
    def stop_auto_diagnostics(self):
        """停止自動診斷"""
        try:
            if self.auto_diagnostic_timer.isActive():
                self.auto_diagnostic_timer.stop()
                self.add_diagnostic(
                    'system',
                    'INFO',
                    '自動診斷已停止',
                    {}
                )
        except Exception as e:
            print(f"停止自動診斷失敗: {e}")
    
    def run_auto_diagnostics(self):
        """運行自動診斷"""
        try:
            # 收集系統資訊
            system_info = SystemDiagnostics.collect_system_info()
            
            # 檢查資源使用情況
            if 'resources' in system_info and 'error' not in system_info['resources']:
                memory_percent = system_info['resources']['memory']['percent']
                disk_percent = system_info['resources']['disk']['percent']
                cpu_percent = system_info['resources']['cpu_percent']
                
                # 記憶體警告
                if memory_percent > 85:
                    self.add_diagnostic(
                        'resource',
                        'WARNING',
                        f'記憶體使用率過高: {memory_percent:.1f}%',
                        {'memory_percent': memory_percent}
                    )
                
                # 磁碟警告
                if disk_percent > 90:
                    self.add_diagnostic(
                        'resource',
                        'WARNING',
                        f'磁碟使用率過高: {disk_percent:.1f}%',
                        {'disk_percent': disk_percent}
                    )
                
                # CPU警告
                if cpu_percent > 90:
                    self.add_diagnostic(
                        'resource',
                        'WARNING',
                        f'CPU使用率過高: {cpu_percent:.1f}%',
                        {'cpu_percent': cpu_percent}
                    )
            
            # 檢查AI系統狀態
            if self.ai_connector:
                if not self.ai_connector.is_system_connected():
                    self.add_diagnostic(
                        'ai_system',
                        'ERROR',
                        'AI系統未連接',
                        {'connected': False}
                    )
            
        except Exception as e:
            self.add_diagnostic(
                'system',
                'ERROR',
                f'自動診斷失敗: {str(e)}',
                {'error': str(e)}
            )
    
    def add_diagnostic(self, category: str, level: str, message: str, 
                      details: Dict[str, Any], source: str = ""):
        """添加診斷資訊"""
        try:
            diagnostic = DiagnosticInfo(
                timestamp=datetime.now(),
                category=category,
                level=level,
                message=message,
                details=details,
                source=source
            )
            
            # 添加到歷史記錄
            self.diagnostic_history.append(diagnostic)
            
            # 限制歷史記錄大小
            if len(self.diagnostic_history) > self.max_history_size:
                self.diagnostic_history.pop(0)
            
            # 發送信號
            self.diagnostic_collected.emit(diagnostic)
            
        except Exception as e:
            print(f"添加診斷資訊失敗: {e}")
    
    def classify_and_add_error(self, error_message: str, source: str = ""):
        """分類錯誤並添加診斷資訊"""
        try:
            classification = ErrorClassifier.classify_error(error_message)
            
            self.add_diagnostic(
                classification['category'],
                'ERROR',
                classification['friendly_message'],
                {
                    'original_message': error_message,
                    'suggestions': classification['suggestions'],
                    'classification': classification['category']
                },
                source
            )
            
        except Exception as e:
            print(f"分類錯誤失敗: {e}")
    
    def generate_diagnostic_report(self, save_path: Optional[str] = None) -> str:
        """生成診斷報告"""
        try:
            # 收集所有診斷資訊
            report_data = {
                'report_info': {
                    'generated_at': datetime.now().isoformat(),
                    'version': '2.0',
                    'total_diagnostics': len(self.diagnostic_history)
                },
                'system_info': SystemDiagnostics.collect_system_info(),
                'application_info': SystemDiagnostics.collect_application_info(),
                'ai_system_info': SystemDiagnostics.collect_ai_system_info(self.ai_connector),
                'error_logs': SystemDiagnostics.collect_error_logs(self.error_recovery),
                'diagnostic_history': [diag.to_dict() for diag in self.diagnostic_history[-50:]]  # 最近50條
            }
            
            # 生成報告文件路徑
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = f"diagnostic_report_{timestamp}.json"
            
            # 保存報告
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.add_diagnostic(
                'system',
                'INFO',
                f'診斷報告已生成: {save_path}',
                {'report_path': save_path}
            )
            
            # 發送信號
            self.report_generated.emit(save_path)
            
            return save_path
            
        except Exception as e:
            error_msg = f"生成診斷報告失敗: {str(e)}"
            self.add_diagnostic('system', 'ERROR', error_msg, {'error': str(e)})
            return ""
    
    def get_diagnostic_summary(self, hours: int = 24) -> Dict[str, Any]:
        """獲取診斷摘要"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # 過濾指定時間範圍內的診斷
            recent_diagnostics = [
                diag for diag in self.diagnostic_history
                if diag.timestamp >= cutoff_time
            ]
            
            # 統計各類別和級別
            category_counts = {}
            level_counts = {}
            
            for diag in recent_diagnostics:
                category_counts[diag.category] = category_counts.get(diag.category, 0) + 1
                level_counts[diag.level] = level_counts.get(diag.level, 0) + 1
            
            return {
                'time_range_hours': hours,
                'total_diagnostics': len(recent_diagnostics),
                'category_counts': category_counts,
                'level_counts': level_counts,
                'latest_error': None if not recent_diagnostics else recent_diagnostics[-1].to_dict()
            }
            
        except Exception as e:
            return {'error': f'獲取診斷摘要失敗: {str(e)}'}
    
    def cleanup(self):
        """清理資源"""
        try:
            self.stop_auto_diagnostics()
            self.diagnostic_history.clear()
        except Exception as e:
            print(f"清理診斷系統失敗: {e}")


class DiagnosticDialog(QDialog):
    """診斷對話框"""
    
    def __init__(self, diagnostic_system: DiagnosticSystem, parent=None):
        super().__init__(parent)
        self.diagnostic_system = diagnostic_system
        self.setWindowTitle("系統診斷")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        """設置UI"""
        layout = QVBoxLayout()
        
        # 創建標籤頁
        tab_widget = QTabWidget()
        
        # 系統資訊標籤頁
        system_tab = QWidget()
        system_layout = QVBoxLayout()
        
        self.system_info_text = QTextEdit()
        self.system_info_text.setReadOnly(True)
        system_layout.addWidget(QLabel("系統資訊:"))
        system_layout.addWidget(self.system_info_text)
        
        system_tab.setLayout(system_layout)
        tab_widget.addTab(system_tab, "系統資訊")
        
        # 診斷歷史標籤頁
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        history_layout.addWidget(QLabel("診斷歷史:"))
        history_layout.addWidget(self.history_text)
        
        history_tab.setLayout(history_layout)
        tab_widget.addTab(history_tab, "診斷歷史")
        
        # 錯誤分析標籤頁
        error_tab = QWidget()
        error_layout = QVBoxLayout()
        
        self.error_analysis_text = QTextEdit()
        self.error_analysis_text.setReadOnly(True)
        error_layout.addWidget(QLabel("錯誤分析:"))
        error_layout.addWidget(self.error_analysis_text)
        
        error_tab.setLayout(error_layout)
        tab_widget.addTab(error_tab, "錯誤分析")
        
        layout.addWidget(tab_widget)
        
        # 按鈕
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self.refresh_data)
        
        export_button = QPushButton("導出報告")
        export_button.clicked.connect(self.export_report)
        
        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.close)
        
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(export_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 初始載入數據
        self.refresh_data()
    
    def refresh_data(self):
        """刷新數據"""
        try:
            # 系統資訊
            system_info = SystemDiagnostics.collect_system_info()
            self.system_info_text.setPlainText(json.dumps(system_info, indent=2, ensure_ascii=False))
            
            # 診斷歷史
            history_text = ""
            for diag in self.diagnostic_system.diagnostic_history[-20:]:  # 最近20條
                history_text += f"[{diag.timestamp.strftime('%H:%M:%S')}] [{diag.level}] [{diag.category}] {diag.message}\n"
            
            self.history_text.setPlainText(history_text)
            
            # 錯誤分析
            summary = self.diagnostic_system.get_diagnostic_summary(24)
            self.error_analysis_text.setPlainText(json.dumps(summary, indent=2, ensure_ascii=False))
            
        except Exception as e:
            print(f"刷新診斷數據失敗: {e}")
    
    def export_report(self):
        """導出報告"""
        try:
            report_path = self.diagnostic_system.generate_diagnostic_report()
            if report_path:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "導出成功", f"診斷報告已保存到: {report_path}")
        except Exception as e:
            print(f"導出報告失敗: {e}")


if __name__ == "__main__":
    # 測試診斷系統
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 創建診斷系統
    diagnostic_system = DiagnosticSystem()
    
    def on_diagnostic_collected(diagnostic_info):
        print(f"診斷收集: [{diagnostic_info.level}] {diagnostic_info.message}")
    
    def on_report_generated(report_path):
        print(f"報告生成: {report_path}")
    
    # 連接信號
    diagnostic_system.diagnostic_collected.connect(on_diagnostic_collected)
    diagnostic_system.report_generated.connect(on_report_generated)
    
    # 添加測試診斷
    diagnostic_system.add_diagnostic(
        'test',
        'INFO',
        '測試診斷資訊',
        {'test_data': 'test_value'}
    )
    
    # 測試錯誤分類
    diagnostic_system.classify_and_add_error("Connection timeout error", "network")
    
    # 生成報告
    diagnostic_system.generate_diagnostic_report()
    
    # 顯示診斷對話框
    dialog = DiagnosticDialog(diagnostic_system)
    dialog.show()
    
    sys.exit(app.exec())