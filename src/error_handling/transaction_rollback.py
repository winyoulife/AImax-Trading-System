#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 交易回滾機制 - 任務9實現
處理交易執行失敗的回滾和恢復操作
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import threading
import copy

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

class TransactionStatus(Enum):
    """交易狀態枚舉"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    COMPENSATED = "compensated"

class RollbackStrategy(Enum):
    """回滾策略枚舉"""
    IMMEDIATE = "immediate"      # 立即回滾
    DELAYED = "delayed"          # 延遲回滾
    COMPENSATING = "compensating" # 補償性回滾
    MANUAL = "manual"            # 手動回滾

@dataclass
class TransactionStep:
    """交易步驟"""
    step_id: str
    step_name: str
    function_name: str
    parameters: Dict[str, Any]
    rollback_function: Optional[str] = None
    rollback_parameters: Optional[Dict[str, Any]] = None
    status: TransactionStatus = TransactionStatus.PENDING
    executed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None

@dataclass
class Transaction:
    """交易記錄"""
    transaction_id: str
    transaction_type: str
    description: str
    steps: List[TransactionStep] = field(default_factory=list)
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rollback_strategy: RollbackStrategy = RollbackStrategy.IMMEDIATE
    max_retry_attempts: int = 3
    current_retry: int = 0
    context: Dict[str, Any] = field(default_factory=dict)

class TransactionManager:
    """交易管理器"""
    
    def __init__(self):
        self.transactions: Dict[str, Transaction] = {}
        self.rollback_handlers: Dict[str, callable] = {}
        self.lock = threading.Lock()
        
        # 配置
        self.config = {
            'auto_rollback_timeout': 300,  # 5分鐘後自動回滾
            'max_concurrent_transactions': 10,
            'rollback_retry_attempts': 3,
            'enable_compensation': True
        }
        
        # 統計
        self.stats = {
            'total_transactions': 0,
            'successful_transactions': 0,
            'failed_transactions': 0,
            'rolled_back_transactions': 0,
            'compensated_transactions': 0
        }
        
        self.setup_default_rollback_handlers()
    
    def setup_default_rollback_handlers(self):
        """設置默認回滾處理器"""
        self.register_rollback_handler('buy_order', self._rollback_buy_order)
        self.register_rollback_handler('sell_order', self._rollback_sell_order)
        self.register_rollback_handler('balance_update', self._rollback_balance_update)
        self.register_rollback_handler('position_update', self._rollback_position_update)
        self.register_rollback_handler('notification_send', self._rollback_notification)
    
    def register_rollback_handler(self, operation_type: str, handler: callable):
        """註冊回滾處理器"""
        self.rollback_handlers[operation_type] = handler
        logger.info(f"📝 註冊回滾處理器: {operation_type}")
    
    def create_transaction(self, transaction_type: str, description: str,
                          rollback_strategy: RollbackStrategy = RollbackStrategy.IMMEDIATE) -> str:
        """創建新交易"""
        transaction_id = self._generate_transaction_id()
        
        transaction = Transaction(
            transaction_id=transaction_id,
            transaction_type=transaction_type,
            description=description,
            rollback_strategy=rollback_strategy
        )
        
        with self.lock:
            self.transactions[transaction_id] = transaction
            self.stats['total_transactions'] += 1
        
        logger.info(f"🆕 創建交易: {transaction_id} - {description}")
        return transaction_id
    
    def add_step(self, transaction_id: str, step_name: str, function_name: str,
                parameters: Dict[str, Any], rollback_function: str = None,
                rollback_parameters: Dict[str, Any] = None) -> str:
        """添加交易步驟"""
        if transaction_id not in self.transactions:
            raise ValueError(f"交易不存在: {transaction_id}")
        
        step_id = f"{transaction_id}_{len(self.transactions[transaction_id].steps) + 1}"
        
        step = TransactionStep(
            step_id=step_id,
            step_name=step_name,
            function_name=function_name,
            parameters=parameters,
            rollback_function=rollback_function,
            rollback_parameters=rollback_parameters or {}
        )
        
        self.transactions[transaction_id].steps.append(step)
        logger.info(f"➕ 添加交易步驟: {step_id} - {step_name}")
        
        return step_id
    
    def execute_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """執行交易"""
        if transaction_id not in self.transactions:
            raise ValueError(f"交易不存在: {transaction_id}")
        
        transaction = self.transactions[transaction_id]
        
        if transaction.status != TransactionStatus.PENDING:
            raise ValueError(f"交易狀態無效: {transaction.status}")
        
        logger.info(f"🚀 開始執行交易: {transaction_id}")
        
        transaction.status = TransactionStatus.EXECUTING
        transaction.started_at = datetime.now()
        
        executed_steps = []
        
        try:
            for step in transaction.steps:
                step_result = self._execute_step(step)
                executed_steps.append(step)
                
                if not step_result['success']:
                    # 步驟失敗，觸發回滾
                    logger.error(f"❌ 步驟失敗: {step.step_id} - {step_result['error']}")
                    
                    rollback_result = self._rollback_transaction(transaction_id, executed_steps)
                    
                    return {
                        'success': False,
                        'transaction_id': transaction_id,
                        'failed_step': step.step_id,
                        'error': step_result['error'],
                        'rollback_result': rollback_result
                    }
            
            # 所有步驟成功
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.now()
            
            with self.lock:
                self.stats['successful_transactions'] += 1
            
            logger.info(f"✅ 交易執行成功: {transaction_id}")
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'executed_steps': len(executed_steps),
                'execution_time': (transaction.completed_at - transaction.started_at).total_seconds()
            }
        
        except Exception as e:
            logger.error(f"💥 交易執行異常: {transaction_id} - {str(e)}")
            
            transaction.status = TransactionStatus.FAILED
            
            rollback_result = self._rollback_transaction(transaction_id, executed_steps)
            
            with self.lock:
                self.stats['failed_transactions'] += 1
            
            return {
                'success': False,
                'transaction_id': transaction_id,
                'error': str(e),
                'rollback_result': rollback_result
            }
    
    def _execute_step(self, step: TransactionStep) -> Dict[str, Any]:
        """執行單個交易步驟"""
        logger.info(f"⚡ 執行步驟: {step.step_id} - {step.step_name}")
        
        step.status = TransactionStatus.EXECUTING
        step.executed_at = datetime.now()
        
        try:
            # 這裡應該調用實際的業務邏輯函數
            # 為了演示，我們模擬執行
            result = self._simulate_step_execution(step)
            
            step.status = TransactionStatus.COMPLETED
            step.result = result
            
            logger.info(f"✅ 步驟執行成功: {step.step_id}")
            
            return {
                'success': True,
                'result': result
            }
        
        except Exception as e:
            step.status = TransactionStatus.FAILED
            step.error = str(e)
            
            logger.error(f"❌ 步驟執行失敗: {step.step_id} - {str(e)}")
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def _simulate_step_execution(self, step: TransactionStep) -> Any:
        """模擬步驟執行（實際應用中應該調用真實的業務邏輯）"""
        function_name = step.function_name
        parameters = step.parameters
        
        # 模擬不同類型的操作
        if 'buy' in function_name.lower():
            return {
                'order_id': f"BUY_{datetime.now().timestamp()}",
                'symbol': parameters.get('symbol', 'BTCUSDT'),
                'quantity': parameters.get('quantity', 0.001),
                'price': parameters.get('price', 50000)
            }
        
        elif 'sell' in function_name.lower():
            return {
                'order_id': f"SELL_{datetime.now().timestamp()}",
                'symbol': parameters.get('symbol', 'BTCUSDT'),
                'quantity': parameters.get('quantity', 0.001),
                'price': parameters.get('price', 50000)
            }
        
        elif 'balance' in function_name.lower():
            return {
                'old_balance': parameters.get('old_balance', 10000),
                'new_balance': parameters.get('new_balance', 9950),
                'change': parameters.get('change', -50)
            }
        
        else:
            return {'status': 'completed', 'timestamp': datetime.now().isoformat()}
    
    def _rollback_transaction(self, transaction_id: str, executed_steps: List[TransactionStep]) -> Dict[str, Any]:
        """回滾交易"""
        logger.info(f"🔄 開始回滾交易: {transaction_id}")
        
        transaction = self.transactions[transaction_id]
        rollback_results = []
        
        # 按相反順序回滾已執行的步驟
        for step in reversed(executed_steps):
            if step.status == TransactionStatus.COMPLETED:
                rollback_result = self._rollback_step(step)
                rollback_results.append(rollback_result)
        
        transaction.status = TransactionStatus.ROLLED_BACK
        
        with self.lock:
            self.stats['rolled_back_transactions'] += 1
        
        logger.info(f"🔄 交易回滾完成: {transaction_id}")
        
        return {
            'transaction_id': transaction_id,
            'rolled_back_steps': len(rollback_results),
            'rollback_details': rollback_results
        }
    
    def _rollback_step(self, step: TransactionStep) -> Dict[str, Any]:
        """回滾單個步驟"""
        logger.info(f"↩️ 回滾步驟: {step.step_id}")
        
        try:
            if step.rollback_function:
                # 使用指定的回滾函數
                rollback_handler = self.rollback_handlers.get(step.rollback_function)
                
                if rollback_handler:
                    result = rollback_handler(step)
                    logger.info(f"✅ 步驟回滾成功: {step.step_id}")
                    
                    return {
                        'step_id': step.step_id,
                        'success': True,
                        'method': 'custom_handler',
                        'result': result
                    }
                else:
                    logger.warning(f"⚠️ 未找到回滾處理器: {step.rollback_function}")
            
            # 使用默認回滾邏輯
            result = self._default_rollback(step)
            
            return {
                'step_id': step.step_id,
                'success': True,
                'method': 'default',
                'result': result
            }
        
        except Exception as e:
            logger.error(f"❌ 步驟回滾失敗: {step.step_id} - {str(e)}")
            
            return {
                'step_id': step.step_id,
                'success': False,
                'error': str(e)
            }
    
    def _default_rollback(self, step: TransactionStep) -> Dict[str, Any]:
        """默認回滾邏輯"""
        # 根據步驟類型執行相應的回滾操作
        function_name = step.function_name.lower()
        
        if 'buy' in function_name:
            return {'action': 'cancel_buy_order', 'order_id': step.result.get('order_id')}
        elif 'sell' in function_name:
            return {'action': 'cancel_sell_order', 'order_id': step.result.get('order_id')}
        elif 'balance' in function_name:
            return {'action': 'restore_balance', 'original_balance': step.parameters.get('old_balance')}
        else:
            return {'action': 'generic_rollback', 'step_name': step.step_name}
    
    def _rollback_buy_order(self, step: TransactionStep) -> Dict[str, Any]:
        """回滾買入訂單"""
        order_id = step.result.get('order_id') if step.result else None
        
        if order_id:
            # 模擬取消訂單
            logger.info(f"🚫 取消買入訂單: {order_id}")
            return {'cancelled_order': order_id, 'status': 'cancelled'}
        
        return {'status': 'no_order_to_cancel'}
    
    def _rollback_sell_order(self, step: TransactionStep) -> Dict[str, Any]:
        """回滾賣出訂單"""
        order_id = step.result.get('order_id') if step.result else None
        
        if order_id:
            # 模擬取消訂單
            logger.info(f"🚫 取消賣出訂單: {order_id}")
            return {'cancelled_order': order_id, 'status': 'cancelled'}
        
        return {'status': 'no_order_to_cancel'}
    
    def _rollback_balance_update(self, step: TransactionStep) -> Dict[str, Any]:
        """回滾餘額更新"""
        old_balance = step.parameters.get('old_balance')
        
        if old_balance is not None:
            logger.info(f"💰 恢復餘額: {old_balance}")
            return {'restored_balance': old_balance, 'status': 'restored'}
        
        return {'status': 'no_balance_to_restore'}
    
    def _rollback_position_update(self, step: TransactionStep) -> Dict[str, Any]:
        """回滾倉位更新"""
        logger.info("📊 恢復倉位狀態")
        return {'status': 'position_restored'}
    
    def _rollback_notification(self, step: TransactionStep) -> Dict[str, Any]:
        """回滾通知發送"""
        logger.info("📢 發送回滾通知")
        return {'status': 'rollback_notification_sent'}
    
    def _generate_transaction_id(self) -> str:
        """生成交易ID"""
        import uuid
        return f"TXN_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """獲取交易狀態"""
        if transaction_id not in self.transactions:
            return {'error': 'Transaction not found'}
        
        transaction = self.transactions[transaction_id]
        
        return {
            'transaction_id': transaction_id,
            'type': transaction.transaction_type,
            'description': transaction.description,
            'status': transaction.status.value,
            'created_at': transaction.created_at.isoformat(),
            'started_at': transaction.started_at.isoformat() if transaction.started_at else None,
            'completed_at': transaction.completed_at.isoformat() if transaction.completed_at else None,
            'steps_count': len(transaction.steps),
            'completed_steps': len([s for s in transaction.steps if s.status == TransactionStatus.COMPLETED]),
            'failed_steps': len([s for s in transaction.steps if s.status == TransactionStatus.FAILED])
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取交易統計"""
        with self.lock:
            stats = self.stats.copy()
        
        if stats['total_transactions'] > 0:
            stats['success_rate'] = (stats['successful_transactions'] / stats['total_transactions']) * 100
            stats['rollback_rate'] = (stats['rolled_back_transactions'] / stats['total_transactions']) * 100
        else:
            stats['success_rate'] = 0.0
            stats['rollback_rate'] = 0.0
        
        return stats
    
    def cleanup_old_transactions(self, days: int = 7):
        """清理舊交易記錄"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        to_remove = []
        for transaction_id, transaction in self.transactions.items():
            if transaction.created_at < cutoff_date:
                to_remove.append(transaction_id)
        
        for transaction_id in to_remove:
            del self.transactions[transaction_id]
        
        logger.info(f"🧹 清理了 {len(to_remove)} 個舊交易記錄")

# 全局交易管理器實例
transaction_manager = TransactionManager()

# 便捷裝飾器
def transactional(transaction_type: str, description: str = "", 
                 rollback_strategy: RollbackStrategy = RollbackStrategy.IMMEDIATE):
    """交易裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 創建交易
            transaction_id = transaction_manager.create_transaction(
                transaction_type, description or func.__name__, rollback_strategy
            )
            
            # 添加步驟
            step_id = transaction_manager.add_step(
                transaction_id, func.__name__, func.__name__, 
                {'args': args, 'kwargs': kwargs}
            )
            
            try:
                # 執行函數
                result = func(*args, **kwargs)
                
                # 標記交易成功
                transaction = transaction_manager.transactions[transaction_id]
                transaction.status = TransactionStatus.COMPLETED
                transaction.completed_at = datetime.now()
                
                return result
                
            except Exception as e:
                # 執行回滾
                logger.error(f"❌ 交易函數失敗: {func.__name__} - {str(e)}")
                
                transaction_manager._rollback_transaction(transaction_id, 
                    [s for s in transaction_manager.transactions[transaction_id].steps 
                     if s.status == TransactionStatus.COMPLETED])
                
                raise e
        
        return wrapper
    return decorator