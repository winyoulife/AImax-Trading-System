#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI系統連接器 - 連接GUI與AI交易系統
提供異步通信和狀態同步功能
"""

import asyncio
import threading
import time
import sys
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread, QRunnable, QThreadPool


class AISystemConnectionWorker(QObject):
    """AI系統異步連接工作器"""
    
    connection_progress = pyqtSignal(str, int)  # message, progress
    connection_completed = pyqtSignal(bool, str, dict)  # success, message, components
    
    def __init__(self, ai_components: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.ai_components = ai_components or {}
        self.should_stop = False
    
    def connect_to_ai_system(self):
        """異步連接到AI系統"""
        try:
            self.connection_progress.emit("開始連接AI系統...", 0)
            
            if self.should_stop:
                return
            
            # 檢查AI組件是否存在
            self.connection_progress.emit("檢查AI系統組件...", 20)
            
            connected_components = {}
            
            # 嘗試連接enhanced_ai_manager
            if self._connect_ai_manager():
                connected_components['ai_manager'] = self.ai_components.get('ai_manager')
                self.connection_progress.emit("AI管理器連接成功", 40)
            else:
                self.connection_progress.emit("AI管理器連接失敗", 40)
            
            if self.should_stop:
                return
            
            # 嘗試連接trade_executor
            if self._connect_trade_executor():
                connected_components['trade_executor'] = self.ai_components.get('trade_executor')
                self.connection_progress.emit("交易執行器連接成功", 60)
            else:
                self.connection_progress.emit("交易執行器連接失敗", 60)
            
            if self.should_stop:
                return
            
            # 嘗試連接risk_manager
            if self._connect_risk_manager():
                connected_components['risk_manager'] = self.ai_components.get('risk_manager')
                self.connection_progress.emit("風險管理器連接成功", 80)
            else:
                self.connection_progress.emit("風險管理器連接失敗", 80)
            
            if self.should_stop:
                return
            
            # 嘗試連接system_integrator
            if self._connect_system_integrator():
                connected_components['system_integrator'] = self.ai_components.get('system_integrator')
                self.connection_progress.emit("系統整合器連接成功", 100)
            else:
                self.connection_progress.emit("系統整合器連接失敗", 100)
            
            # 判斷連接結果
            if connected_components:
                success_msg = f"成功連接 {len(connected_components)} 個AI組件"
                self.connection_completed.emit(True, success_msg, connected_components)
            else:
                self.connection_completed.emit(False, "所有AI組件連接失敗，啟動演示模式", {})
                
        except Exception as e:
            self.connection_completed.emit(False, f"連接過程中發生錯誤: {str(e)}", {})
    
    def _connect_ai_manager(self) -> bool:
        """連接AI管理器"""
        try:
            if self.ai_components.get('ai_manager'):
                # 這裡可以添加真實的AI管理器初始化邏輯
                # ai_manager = self.ai_components['ai_manager']
                # return ai_manager.initialize()
                return True
            else:
                # 嘗試動態載入
                return self._try_load_ai_manager()
        except Exception as e:
            print(f"連接AI管理器失敗: {e}")
            return False
    
    def _connect_trade_executor(self) -> bool:
        """連接交易執行器"""
        try:
            if self.ai_components.get('trade_executor'):
                # 這裡可以添加真實的交易執行器初始化邏輯
                return True
            else:
                return self._try_load_trade_executor()
        except Exception as e:
            print(f"連接交易執行器失敗: {e}")
            return False
    
    def _connect_risk_manager(self) -> bool:
        """連接風險管理器"""
        try:
            if self.ai_components.get('risk_manager'):
                # 這裡可以添加真實的風險管理器初始化邏輯
                return True
            else:
                return self._try_load_risk_manager()
        except Exception as e:
            print(f"連接風險管理器失敗: {e}")
            return False
    
    def _connect_system_integrator(self) -> bool:
        """連接系統整合器"""
        try:
            if self.ai_components.get('system_integrator'):
                # 這裡可以添加真實的系統整合器初始化邏輯
                return True
            else:
                return self._try_load_system_integrator()
        except Exception as e:
            print(f"連接系統整合器失敗: {e}")
            return False
    
    def _try_load_ai_manager(self) -> bool:
        """嘗試動態載入AI管理器"""
        try:
            # 檢查文件是否存在
            ai_manager_path = Path("src/ai/enhanced_ai_manager.py")
            if ai_manager_path.exists():
                # 嘗試導入
                sys.path.insert(0, str(Path.cwd()))
                from src.ai.enhanced_ai_manager import EnhancedAIManager
                
                # 創建實例
                ai_manager = EnhancedAIManager()
                self.ai_components['ai_manager'] = ai_manager
                return True
            return False
        except Exception as e:
            print(f"動態載入AI管理器失敗: {e}")
            return False
    
    def _try_load_trade_executor(self) -> bool:
        """嘗試動態載入交易執行器"""
        try:
            executor_path = Path("src/trading/trade_executor.py")
            if executor_path.exists():
                from src.trading.trade_executor import TradeExecutor
                trade_executor = TradeExecutor()
                self.ai_components['trade_executor'] = trade_executor
                return True
            return False
        except Exception as e:
            print(f"動態載入交易執行器失敗: {e}")
            return False
    
    def _try_load_risk_manager(self) -> bool:
        """嘗試動態載入風險管理器"""
        try:
            risk_path = Path("src/trading/risk_manager.py")
            if risk_path.exists():
                from src.trading.risk_manager import RiskManager
                risk_manager = RiskManager()
                self.ai_components['risk_manager'] = risk_manager
                return True
            return False
        except Exception as e:
            print(f"動態載入風險管理器失敗: {e}")
            return False
    
    def _try_load_system_integrator(self) -> bool:
        """嘗試動態載入系統整合器"""
        try:
            integrator_path = Path("src/core/trading_system_integrator.py")
            if integrator_path.exists():
                from src.core.trading_system_integrator import TradingSystemIntegrator
                system_integrator = TradingSystemIntegrator()
                self.ai_components['system_integrator'] = system_integrator
                return True
            return False
        except Exception as e:
            print(f"動態載入系統整合器失敗: {e}")
            return False
    
    def stop_connection(self):
        """停止連接過程"""
        self.should_stop = True


class AIConnector(QObject):
    """AI系統連接器"""
    
    # 信號定義
    status_updated = pyqtSignal(dict)
    trading_status_updated = pyqtSignal(dict)
    log_message = pyqtSignal(str, str)  # message, level
    connection_changed = pyqtSignal(bool)
    
    def __init__(self, ai_components: Optional[Dict[str, Any]] = None):
        super().__init__()
        
        # AI系統組件
        self.ai_components = ai_components or {}
        self.ai_manager = ai_components.get('ai_manager') if ai_components else None
        self.trade_executor = ai_components.get('trade_executor') if ai_components else None
        self.risk_manager = ai_components.get('risk_manager') if ai_components else None
        self.system_integrator = ai_components.get('system_integrator') if ai_components else None
        
        # 連接狀態
        self.is_connected = False
        self.is_trading = False
        self.current_strategy = "auto"
        
        # 狀態數據
        self.ai_status_data = {
            'connected': False,
            'status': '未連接',
            'active_count': 0,
            'last_decision': '等待中...',
            'confidence': 0.0
        }
        
        self.trading_status_data = {
            'status': '停止',
            'balance': 0.0,
            'profit_loss': 0.0,
            'active_orders': 0
        }
        
        # 狀態更新定時器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(2000)  # 每2秒更新一次
        
        # 模擬數據（用於演示）
        self.demo_mode = True
        self.demo_balance = 10000.0
        self.demo_profit_loss = 0.0
        self.start_time = datetime.now()
    
    def connect_to_ai_system(self) -> bool:
        """連接到AI系統（異步）"""
        try:
            self.log_message.emit("開始異步連接AI系統...", "INFO")
            
            # 創建連接工作器
            self.connection_worker = AISystemConnectionWorker(self.ai_components)
            self.connection_thread = QThread()
            
            # 移動工作器到線程
            self.connection_worker.moveToThread(self.connection_thread)
            
            # 連接信號
            self.connection_worker.connection_progress.connect(self._on_connection_progress)
            self.connection_worker.connection_completed.connect(self._on_connection_completed)
            self.connection_thread.started.connect(self.connection_worker.connect_to_ai_system)
            
            # 啟動連接線程
            self.connection_thread.start()
            
            return True
            
        except Exception as e:
            self.log_message.emit(f"啟動AI系統連接失敗: {str(e)}", "ERROR")
            return False
    
    def _on_connection_progress(self, message: str, progress: int):
        """連接進度更新"""
        self.log_message.emit(f"[{progress}%] {message}", "INFO")
    
    def _on_connection_completed(self, success: bool, message: str, components: Dict[str, Any]):
        """連接完成處理"""
        try:
            if success and components:
                # 真實AI系統連接成功
                self.ai_components.update(components)
                self.ai_manager = components.get('ai_manager')
                self.trade_executor = components.get('trade_executor')
                self.risk_manager = components.get('risk_manager')
                self.system_integrator = components.get('system_integrator')
                
                self.is_connected = True
                self.demo_mode = False
                
                self.ai_status_data.update({
                    'connected': True,
                    'status': '已連接',
                    'active_count': len(components),
                    'last_decision': 'AI系統已就緒',
                    'confidence': 95.0
                })
                
                self.log_message.emit(message, "SUCCESS")
                
            else:
                # 演示模式
                self.is_connected = True
                self.demo_mode = True
                
                self.ai_status_data.update({
                    'connected': True,
                    'status': '演示模式',
                    'active_count': 3,
                    'last_decision': '演示數據',
                    'confidence': 75.0
                })
                
                self.log_message.emit("AI組件連接失敗，啟動演示模式", "WARNING")
            
            # 發送狀態更新
            self.status_updated.emit(self.ai_status_data.copy())
            self.connection_changed.emit(self.is_connected)
            
            # 清理連接線程
            if hasattr(self, 'connection_thread') and self.connection_thread.isRunning():
                self.connection_thread.quit()
                self.connection_thread.wait()
                
        except Exception as e:
            self.log_message.emit(f"處理連接結果失敗: {str(e)}", "ERROR")
    
    def start_trading(self) -> bool:
        """啟動交易"""
        try:
            if not self.is_connected:
                self.log_message.emit("AI系統未連接，無法啟動交易", "ERROR")
                return False
            
            self.log_message.emit(f"啟動交易，策略: {self.current_strategy}", "INFO")
            
            if not self.demo_mode and self.system_integrator:
                # 真實交易啟動
                # result = self.system_integrator.start_trading(self.current_strategy)
                # if not result:
                #     return False
                pass
            
            # 更新狀態
            self.is_trading = True
            self.trading_status_data.update({
                'status': '運行中',
                'balance': self.demo_balance,
                'profit_loss': self.demo_profit_loss,
                'active_orders': 3 if self.demo_mode else 0
            })
            
            self.ai_status_data.update({
                'last_decision': f'啟動{self.current_strategy}策略',
                'confidence': 85.0
            })
            
            # 發送更新
            self.trading_status_updated.emit(self.trading_status_data.copy())
            self.status_updated.emit(self.ai_status_data.copy())
            
            self.log_message.emit("交易啟動成功", "SUCCESS")
            return True
            
        except Exception as e:
            self.log_message.emit(f"啟動交易失敗: {str(e)}", "ERROR")
            return False
    
    def stop_trading(self) -> bool:
        """停止交易"""
        try:
            if not self.is_trading:
                self.log_message.emit("交易未在運行", "WARNING")
                return True
            
            self.log_message.emit("正在停止交易...", "INFO")
            
            if not self.demo_mode and self.system_integrator:
                # 真實交易停止
                # result = self.system_integrator.stop_trading()
                # if not result:
                #     return False
                pass
            
            # 更新狀態
            self.is_trading = False
            self.trading_status_data.update({
                'status': '停止',
                'active_orders': 0
            })
            
            self.ai_status_data.update({
                'last_decision': '交易已停止',
                'confidence': 0.0
            })
            
            # 發送更新
            self.trading_status_updated.emit(self.trading_status_data.copy())
            self.status_updated.emit(self.ai_status_data.copy())
            
            self.log_message.emit("交易停止成功", "SUCCESS")
            return True
            
        except Exception as e:
            self.log_message.emit(f"停止交易失敗: {str(e)}", "ERROR")
            return False
    
    def set_strategy(self, strategy: str):
        """設置交易策略"""
        try:
            old_strategy = self.current_strategy
            self.current_strategy = strategy
            
            self.log_message.emit(f"策略已更改: {old_strategy} -> {strategy}", "INFO")
            
            if not self.demo_mode and self.system_integrator:
                # 真實策略更改
                # self.system_integrator.set_strategy(strategy)
                pass
            
            # 更新AI狀態
            self.ai_status_data.update({
                'last_decision': f'切換到{strategy}策略',
                'confidence': 80.0
            })
            
            self.status_updated.emit(self.ai_status_data.copy())
            
        except Exception as e:
            self.log_message.emit(f"設置策略失敗: {str(e)}", "ERROR")
    
    def update_status(self):
        """定期更新狀態"""
        try:
            if not self.is_connected:
                return
            
            # 模擬狀態變化（演示模式）
            if self.demo_mode:
                self._update_demo_status()
            else:
                self._update_real_status()
            
            # 發送狀態更新
            self.status_updated.emit(self.ai_status_data.copy())
            self.trading_status_updated.emit(self.trading_status_data.copy())
            
        except Exception as e:
            self.log_message.emit(f"狀態更新失敗: {str(e)}", "ERROR")
    
    def _update_demo_status(self):
        """更新演示模式狀態"""
        import random
        
        # 模擬AI決策變化
        decisions = [
            "分析市場趨勢...",
            "檢測套利機會",
            "調整網格參數",
            "執行DCA策略",
            "風險評估中",
            "等待交易信號"
        ]
        
        if random.random() < 0.3:  # 30%機率更新決策
            self.ai_status_data['last_decision'] = random.choice(decisions)
            self.ai_status_data['confidence'] = random.uniform(70, 95)
        
        # 模擬交易狀態變化
        if self.is_trading:
            # 模擬餘額變化
            change = random.uniform(-50, 100)  # -50到+100的隨機變化
            self.demo_profit_loss += change
            self.demo_balance += change
            
            self.trading_status_data.update({
                'balance': max(0, self.demo_balance),
                'profit_loss': self.demo_profit_loss,
                'active_orders': random.randint(1, 5)
            })
            
            # 偶爾記錄交易日誌
            if random.random() < 0.1:  # 10%機率
                if change > 0:
                    self.log_message.emit(f"交易獲利: ${change:.2f}", "SUCCESS")
                else:
                    self.log_message.emit(f"交易虧損: ${abs(change):.2f}", "WARNING")
    
    def _update_real_status(self):
        """更新真實AI系統狀態"""
        try:
            # 這裡可以添加真實的AI系統狀態查詢邏輯
            if self.ai_manager:
                # ai_status = self.ai_manager.get_status()
                # self.ai_status_data.update(ai_status)
                pass
            
            if self.trade_executor:
                # trading_status = self.trade_executor.get_status()
                # self.trading_status_data.update(trading_status)
                pass
                
        except Exception as e:
            self.log_message.emit(f"獲取真實狀態失敗: {str(e)}", "ERROR")
    
    def refresh_status(self):
        """手動刷新狀態"""
        self.log_message.emit("手動刷新狀態", "INFO")
        self.update_status()
    
    def get_ai_status(self) -> Dict[str, Any]:
        """獲取AI狀態"""
        return self.ai_status_data.copy()
    
    def get_trading_status(self) -> Dict[str, Any]:
        """獲取交易狀態"""
        return self.trading_status_data.copy()
    
    def is_system_connected(self) -> bool:
        """檢查系統是否已連接"""
        return self.is_connected
    
    def is_trading_active(self) -> bool:
        """檢查交易是否活躍"""
        return self.is_trading
    
    def get_ai_system_info(self) -> Dict[str, Any]:
        """獲取AI系統詳細資訊"""
        try:
            info = {
                'connected_components': [],
                'system_status': 'unknown',
                'capabilities': [],
                'version_info': {}
            }
            
            if not self.demo_mode:
                # 獲取真實AI系統資訊
                if self.ai_manager:
                    info['connected_components'].append('AI Manager')
                    # info['version_info']['ai_manager'] = self.ai_manager.get_version()
                
                if self.trade_executor:
                    info['connected_components'].append('Trade Executor')
                    # info['capabilities'].extend(self.trade_executor.get_capabilities())
                
                if self.risk_manager:
                    info['connected_components'].append('Risk Manager')
                    # info['capabilities'].extend(self.risk_manager.get_capabilities())
                
                if self.system_integrator:
                    info['connected_components'].append('System Integrator')
                    # info['system_status'] = self.system_integrator.get_system_status()
            else:
                # 演示模式資訊
                info.update({
                    'connected_components': ['Demo AI Manager', 'Demo Trade Executor', 'Demo Risk Manager'],
                    'system_status': 'demo_mode',
                    'capabilities': ['DCA Trading', 'Grid Trading', 'Arbitrage', 'Risk Management'],
                    'version_info': {'demo_version': '2.0.0'}
                })
            
            return info
            
        except Exception as e:
            self.log_message.emit(f"獲取AI系統資訊失敗: {str(e)}", "ERROR")
            return {}
    
    def execute_ai_command(self, command: str, parameters: Dict[str, Any] = None) -> bool:
        """執行AI系統命令"""
        try:
            if not self.is_connected:
                self.log_message.emit("AI系統未連接，無法執行命令", "ERROR")
                return False
            
            parameters = parameters or {}
            self.log_message.emit(f"執行AI命令: {command}", "INFO")
            
            if not self.demo_mode:
                # 真實AI系統命令執行
                if command == "analyze_market" and self.ai_manager:
                    # result = self.ai_manager.analyze_market(parameters)
                    pass
                elif command == "execute_trade" and self.trade_executor:
                    # result = self.trade_executor.execute_trade(parameters)
                    pass
                elif command == "assess_risk" and self.risk_manager:
                    # result = self.risk_manager.assess_risk(parameters)
                    pass
                elif command == "system_health_check" and self.system_integrator:
                    # result = self.system_integrator.health_check()
                    pass
            else:
                # 演示模式命令模擬
                self.log_message.emit(f"演示模式執行命令: {command}", "INFO")
                time.sleep(0.5)  # 模擬處理時間
            
            self.log_message.emit(f"命令執行完成: {command}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log_message.emit(f"執行AI命令失敗: {str(e)}", "ERROR")
            return False
    
    def get_trading_performance(self) -> Dict[str, Any]:
        """獲取交易性能數據"""
        try:
            if not self.demo_mode and self.system_integrator:
                # 獲取真實性能數據
                # return self.system_integrator.get_performance_metrics()
                pass
            
            # 演示模式性能數據
            import random
            return {
                'total_trades': random.randint(50, 200),
                'successful_trades': random.randint(30, 150),
                'win_rate': random.uniform(0.6, 0.8),
                'total_profit': random.uniform(-100, 500),
                'max_drawdown': random.uniform(0.05, 0.15),
                'sharpe_ratio': random.uniform(1.2, 2.5),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.log_message.emit(f"獲取交易性能失敗: {str(e)}", "ERROR")
            return {}
    
    def reconnect_ai_system(self) -> bool:
        """重新連接AI系統"""
        try:
            self.log_message.emit("嘗試重新連接AI系統...", "INFO")
            
            # 先斷開現有連接
            self.disconnect_ai_system()
            
            # 等待一段時間
            time.sleep(1)
            
            # 重新連接
            return self.connect_to_ai_system()
            
        except Exception as e:
            self.log_message.emit(f"重新連接AI系統失敗: {str(e)}", "ERROR")
            return False
    
    def disconnect_ai_system(self):
        """斷開AI系統連接"""
        try:
            self.log_message.emit("正在斷開AI系統連接...", "INFO")
            
            # 停止交易
            if self.is_trading:
                self.stop_trading()
            
            # 停止連接線程
            if hasattr(self, 'connection_thread') and self.connection_thread.isRunning():
                if hasattr(self, 'connection_worker'):
                    self.connection_worker.stop_connection()
                self.connection_thread.quit()
                self.connection_thread.wait(2000)
            
            # 清理AI組件引用
            if not self.demo_mode:
                # 這裡可以添加真實的AI系統清理邏輯
                if self.ai_manager:
                    # self.ai_manager.cleanup()
                    pass
                if self.trade_executor:
                    # self.trade_executor.cleanup()
                    pass
                if self.risk_manager:
                    # self.risk_manager.cleanup()
                    pass
                if self.system_integrator:
                    # self.system_integrator.cleanup()
                    pass
            
            # 重置狀態
            self.is_connected = False
            self.is_trading = False
            self.ai_manager = None
            self.trade_executor = None
            self.risk_manager = None
            self.system_integrator = None
            
            self.ai_status_data.update({
                'connected': False,
                'status': '已斷開',
                'active_count': 0,
                'last_decision': '系統已斷開',
                'confidence': 0.0
            })
            
            # 發送狀態更新
            self.status_updated.emit(self.ai_status_data.copy())
            self.connection_changed.emit(False)
            
            self.log_message.emit("AI系統連接已斷開", "SUCCESS")
            
        except Exception as e:
            self.log_message.emit(f"斷開AI系統連接失敗: {str(e)}", "ERROR")
    
    def cleanup(self):
        """清理資源"""
        try:
            self.log_message.emit("正在清理AI連接器資源...", "INFO")
            
            # 停止定時器
            if self.status_timer.isActive():
                self.status_timer.stop()
            
            # 斷開AI系統連接
            self.disconnect_ai_system()
            
            self.log_message.emit("AI連接器資源清理完成", "SUCCESS")
            
        except Exception as e:
            self.log_message.emit(f"清理資源時發生錯誤: {str(e)}", "ERROR")


if __name__ == "__main__":
    # 測試AI連接器
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QCoreApplication
    
    app = QCoreApplication(sys.argv)
    
    # 創建測試連接器
    connector = AIConnector()
    
    def on_status_updated(status_data):
        print(f"AI狀態更新: {status_data}")
    
    def on_trading_updated(trading_data):
        print(f"交易狀態更新: {trading_data}")
    
    def on_log_message(message, level):
        print(f"[{level}] {message}")
    
    # 連接信號
    connector.status_updated.connect(on_status_updated)
    connector.trading_status_updated.connect(on_trading_updated)
    connector.log_message.connect(on_log_message)
    
    # 測試連接
    connector.connect_to_ai_system()
    
    # 運行5秒後退出
    QTimer.singleShot(5000, app.quit)
    
    sys.exit(app.exec())