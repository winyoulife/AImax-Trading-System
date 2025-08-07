"""
AImax 交易數據管理器
負責處理所有交易相關的數據存儲、檢索和管理
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz


class TradingDataManager:
    """交易數據管理器"""
    
    def __init__(self, base_path: str = "data"):
        self.base_path = base_path
        self.taipei_tz = pytz.timezone('Asia/Taipei')
        self._ensure_directories()
    
    def _ensure_directories(self):
        """確保所有必要的目錄存在"""
        directories = [
            f"{self.base_path}/trading",
            f"{self.base_path}/monitoring", 
            f"{self.base_path}/states",
            f"{self.base_path}/analytics",
            f"{self.base_path}/backups",
            f"{self.base_path}/keep_alive",
            "logs/trading",
            "logs/system",
            "logs/errors"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def save_trading_execution(self, execution_data: Dict[str, Any]) -> bool:
        """保存交易執行記錄"""
        try:
            now = datetime.now()
            taipei_time = now.astimezone(self.taipei_tz)
            today = taipei_time.strftime('%Y-%m-%d')
            
            # 添加時間戳
            execution_data.update({
                'timestamp': now.isoformat(),
                'taipei_time': taipei_time.isoformat(),
                'execution_id': f"{today}_{now.strftime('%H%M%S')}_{os.getpid()}"
            })
            
            # 保存到每日執行日誌（JSONL格式）
            log_file = f"{self.base_path}/trading/execution_log_{today}.jsonl"
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(execution_data, ensure_ascii=False) + '\n')
            
            # 更新最新執行記錄
            with open(f"{self.base_path}/trading/latest_execution.json", 'w', encoding='utf-8') as f:
                json.dump(execution_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self._log_error(f"保存交易執行記錄失敗: {str(e)}")
            return False
    
    def get_trading_executions(self, date: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """獲取交易執行記錄"""
        try:
            if date is None:
                date = datetime.now().astimezone(self.taipei_tz).strftime('%Y-%m-%d')
            
            log_file = f"{self.base_path}/trading/execution_log_{date}.jsonl"
            
            if not os.path.exists(log_file):
                return []
            
            executions = []
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        executions.append(json.loads(line.strip()))
            
            # 按時間戳排序（最新的在前）
            executions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            if limit:
                executions = executions[:limit]
            
            return executions
            
        except Exception as e:
            self._log_error(f"獲取交易執行記錄失敗: {str(e)}")
            return []
    
    def update_trading_state(self, state_updates: Dict[str, Any]) -> bool:
        """更新交易狀態"""
        try:
            state_file = f"{self.base_path}/states/current_trading_state.json"
            
            # 讀取當前狀態
            if os.path.exists(state_file):
                with open(state_file, 'r', encoding='utf-8') as f:
                    current_state = json.load(f)
            else:
                current_state = self._get_default_trading_state()
            
            # 更新狀態
            current_state['last_updated'] = datetime.now().isoformat()
            
            # 深度合併更新
            self._deep_update(current_state, state_updates)
            
            # 保存更新後的狀態
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(current_state, f, indent=2, ensure_ascii=False)
            
            # 創建狀態歷史記錄
            history_file = f"{self.base_path}/states/state_history_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
            history_entry = {
                'timestamp': datetime.now().isoformat(),
                'updates': state_updates,
                'full_state': current_state
            }
            
            with open(history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(history_entry, ensure_ascii=False) + '\n')
            
            return True
            
        except Exception as e:
            self._log_error(f"更新交易狀態失敗: {str(e)}")
            return False
    
    def get_trading_state(self) -> Dict[str, Any]:
        """獲取當前交易狀態"""
        try:
            state_file = f"{self.base_path}/states/current_trading_state.json"
            
            if os.path.exists(state_file):
                with open(state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 返回默認狀態
                default_state = self._get_default_trading_state()
                self.update_trading_state(default_state)
                return default_state
                
        except Exception as e:
            self._log_error(f"獲取交易狀態失敗: {str(e)}")
            return self._get_default_trading_state()
    
    def save_price_data(self, price_data: Dict[str, Any]) -> bool:
        """保存價格數據"""
        try:
            now = datetime.now()
            taipei_time = now.astimezone(self.taipei_tz)
            today = taipei_time.strftime('%Y-%m-%d')
            
            # 添加時間戳
            price_data.update({
                'timestamp': now.isoformat(),
                'taipei_time': taipei_time.isoformat()
            })
            
            # 保存到每日價格歷史
            history_file = f"{self.base_path}/trading/price_history_{today}.jsonl"
            with open(history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(price_data, ensure_ascii=False) + '\n')
            
            # 更新最新價格
            with open(f"{self.base_path}/monitoring/last_price.json", 'w', encoding='utf-8') as f:
                json.dump(price_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self._log_error(f"保存價格數據失敗: {str(e)}")
            return False
    
    def get_price_history(self, date: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """獲取價格歷史"""
        try:
            if date is None:
                date = datetime.now().astimezone(self.taipei_tz).strftime('%Y-%m-%d')
            
            history_file = f"{self.base_path}/trading/price_history_{date}.jsonl"
            
            if not os.path.exists(history_file):
                return []
            
            prices = []
            with open(history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        prices.append(json.loads(line.strip()))
            
            # 按時間戳排序（最新的在前）
            prices.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            if limit:
                prices = prices[:limit]
            
            return prices
            
        except Exception as e:
            self._log_error(f"獲取價格歷史失敗: {str(e)}")
            return []
    
    def calculate_daily_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """計算每日統計數據"""
        try:
            if date is None:
                date = datetime.now().astimezone(self.taipei_tz).strftime('%Y-%m-%d')
            
            executions = self.get_trading_executions(date)
            
            stats = {
                'date': date,
                'total_executions': len(executions),
                'high_volatility_executions': 0,
                'medium_volatility_executions': 0,
                'low_volatility_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'average_confidence': 0.0,
                'total_profit_loss': 0.0,
                'execution_times': [],
                'volatility_distribution': {},
                'last_updated': datetime.now().isoformat()
            }
            
            if executions:
                total_confidence = 0
                
                for execution in executions:
                    # 統計波動性分布
                    volatility = execution.get('volatility_level', 'unknown')
                    if volatility == 'high':
                        stats['high_volatility_executions'] += 1
                    elif volatility == 'medium':
                        stats['medium_volatility_executions'] += 1
                    elif volatility == 'low':
                        stats['low_volatility_executions'] += 1
                    
                    # 統計成功/失敗
                    if execution.get('status') == 'success':
                        stats['successful_executions'] += 1
                    elif execution.get('status') == 'failed':
                        stats['failed_executions'] += 1
                    
                    # 累計信心度
                    confidence = execution.get('confidence', 0.85)
                    total_confidence += confidence
                    
                    # 累計盈虧
                    pnl = execution.get('profit_loss', 0.0)
                    stats['total_profit_loss'] += pnl
                    
                    # 記錄執行時間
                    if 'taipei_time' in execution:
                        stats['execution_times'].append(execution['taipei_time'])
                
                # 計算平均信心度
                stats['average_confidence'] = total_confidence / len(executions)
                
                # 計算勝率
                if stats['successful_executions'] + stats['failed_executions'] > 0:
                    stats['win_rate'] = stats['successful_executions'] / (stats['successful_executions'] + stats['failed_executions'])
                else:
                    stats['win_rate'] = 0.0
            
            # 保存統計數據
            stats_file = f"{self.base_path}/analytics/daily_stats_{date}.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            return stats
            
        except Exception as e:
            self._log_error(f"計算每日統計失敗: {str(e)}")
            return {}
    
    def backup_data(self, backup_type: str = "full") -> Dict[str, Any]:
        """備份數據"""
        try:
            now = datetime.now()
            backup_dir = f"{self.base_path}/backups/{now.strftime('%Y-%m-%d_%H-%M-%S')}"
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_result = {
                'timestamp': now.isoformat(),
                'backup_type': backup_type,
                'status': 'success',
                'files_backed_up': [],
                'backup_size_bytes': 0
            }
            
            # 要備份的目錄和文件
            backup_sources = [
                f"{self.base_path}/states/",
                f"{self.base_path}/trading/",
                f"{self.base_path}/analytics/",
                f"{self.base_path}/monitoring/",
            ]
            
            for source in backup_sources:
                if os.path.exists(source):
                    dest = os.path.join(backup_dir, os.path.basename(source.rstrip('/')))
                    
                    if os.path.isdir(source):
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(source, dest)
                    
                    backup_result['files_backed_up'].append(source)
            
            # 計算備份大小
            for root, dirs, files in os.walk(backup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    backup_result['backup_size_bytes'] += os.path.getsize(file_path)
            
            # 保存備份元數據
            metadata = {
                'created': now.isoformat(),
                'backup_type': backup_type,
                'total_files': len(backup_result['files_backed_up']),
                'size_bytes': backup_result['backup_size_bytes'],
                'size_mb': round(backup_result['backup_size_bytes'] / (1024 * 1024), 2)
            }
            
            with open(os.path.join(backup_dir, 'backup_metadata.json'), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return backup_result
            
        except Exception as e:
            self._log_error(f"數據備份失敗: {str(e)}")
            return {'status': 'failed', 'error': str(e)}
    
    def _get_default_trading_state(self) -> Dict[str, Any]:
        """獲取默認交易狀態"""
        return {
            'schema_version': '1.0',
            'last_updated': datetime.now().isoformat(),
            'trading_status': {
                'is_active': True,
                'current_strategy': 'smart_balanced_83.3_percent',
                'execution_mode': 'high_frequency',
                'last_execution': None,
                'next_scheduled': None,
                'total_executions_today': 0,
                'consecutive_failures': 0
            },
            'market_data': {
                'current_btc_price': 0.0,
                'last_price_update': None,
                'price_change_24h': 0.0,
                'volatility_level': 'unknown',
                'market_trend': 'neutral'
            },
            'performance_metrics': {
                'daily_win_rate': 0.0,
                'total_trades': 0,
                'successful_trades': 0,
                'failed_trades': 0,
                'average_confidence': 0.85,
                'total_profit_loss': 0.0
            },
            'system_health': {
                'github_actions_status': 'active',
                'api_connectivity': 'unknown',
                'data_integrity': 'good',
                'last_health_check': None,
                'resource_usage': {
                    'actions_minutes_used': 0,
                    'storage_mb_used': 0,
                    'api_calls_today': 0
                }
            }
        }
    
    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """深度更新字典"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def _log_error(self, error_message: str):
        """記錄錯誤"""
        try:
            error_log = {
                'timestamp': datetime.now().isoformat(),
                'error': error_message,
                'component': 'TradingDataManager'
            }
            
            today = datetime.now().strftime('%Y-%m-%d')
            error_file = f"logs/errors/data_manager_errors_{today}.jsonl"
            
            with open(error_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_log, ensure_ascii=False) + '\n')
                
        except Exception:
            # 如果連錯誤記錄都失敗了，就只能忽略
            pass


# 使用示例和測試函數
if __name__ == "__main__":
    # 創建數據管理器實例
    data_manager = TradingDataManager()
    
    # 測試保存交易執行記錄
    execution_data = {
        'strategy': 'smart_balanced_83.3_percent',
        'btc_price': 3425000,
        'volatility_level': 'high',
        'signal': 'buy',
        'confidence': 0.90,
        'status': 'success',
        'profit_loss': 150.0
    }
    
    success = data_manager.save_trading_execution(execution_data)
    print(f"保存交易執行記錄: {'成功' if success else '失敗'}")
    
    # 測試獲取交易記錄
    executions = data_manager.get_trading_executions(limit=5)
    print(f"獲取到 {len(executions)} 條交易記錄")
    
    # 測試更新交易狀態
    state_updates = {
        'market_data': {
            'current_btc_price': 3425000,
            'volatility_level': 'high'
        },
        'trading_status': {
            'total_executions_today': 1
        }
    }
    
    success = data_manager.update_trading_state(state_updates)
    print(f"更新交易狀態: {'成功' if success else '失敗'}")
    
    # 測試計算每日統計
    stats = data_manager.calculate_daily_stats()
    print(f"每日統計: {stats.get('total_executions', 0)} 次執行")
    
    print("✅ 數據管理器測試完成")