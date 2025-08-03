"""
狀態管理器 - 管理GUI組件的狀態和數據持久化
"""
import logging
import json
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import pickle

@dataclass
class StateSnapshot:
    """狀態快照"""
    timestamp: datetime
    component_states: Dict[str, Dict[str, Any]]
    global_state: Dict[str, Any]
    version: str = "1.0"

class StateManager:
    """
    狀態管理器 - 負責管理組件狀態和數據持久化
    
    功能:
    - 追蹤和管理組件狀態
    - 提供狀態變化通知機制
    - 實現狀態的持久化存儲
    - 支持狀態快照和恢復
    """
    
    def __init__(self, state_file: str = "AImax/data/gui_state.json"):
        self.logger = logging.getLogger(__name__)
        self.state_file = Path(state_file)
        self.component_states: Dict[str, Dict[str, Any]] = {}
        self.global_state: Dict[str, Any] = {}
        self.state_listeners: Dict[str, List[Callable]] = {}
        self.global_listeners: List[Callable] = []
        self.lock = threading.RLock()
        self.auto_save = True
        self.save_interval = 30  # 秒
        self.last_save_time = datetime.now()
        
        # 狀態歷史（用於撤銷/重做）
        self.state_history: List[StateSnapshot] = []
        self.max_history_size = 50
        self.current_history_index = -1
        
        # 確保狀態文件目錄存在
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 載入已保存的狀態
        self._load_state()
    
    def set_component_state(self, component: str, state: Dict[str, Any], 
                           notify: bool = True, save: bool = None):
        """
        設置組件狀態
        
        Args:
            component: 組件名稱
            state: 狀態數據
            notify: 是否通知監聽者
            save: 是否自動保存（None表示使用全局設置）
        """
        with self.lock:
            old_state = self.component_states.get(component, {}).copy()
            
            # 更新狀態
            if component not in self.component_states:
                self.component_states[component] = {}
            
            self.component_states[component].update(state)
            
            # 記錄狀態變化
            self.logger.debug(f"🔄 組件 {component} 狀態更新: {list(state.keys())}")
            
            # 創建狀態快照
            if self._should_create_snapshot(component, old_state, state):
                self._create_state_snapshot()
            
            # 通知監聽者
            if notify:
                self._notify_state_change(component, old_state, state)
            
            # 自動保存
            if save is True or (save is None and self.auto_save):
                self._auto_save_if_needed()
    
    def get_component_state(self, component: str, key: str = None, 
                           default: Any = None) -> Any:
        """
        獲取組件狀態
        
        Args:
            component: 組件名稱
            key: 狀態鍵（None表示獲取整個狀態）
            default: 默認值
            
        Returns:
            狀態值或默認值
        """
        with self.lock:
            if component not in self.component_states:
                return default
            
            component_state = self.component_states[component]
            
            if key is None:
                return component_state.copy()
            else:
                return component_state.get(key, default)
    
    def update_component_state(self, component: str, key: str, value: Any,
                              notify: bool = True, save: bool = None):
        """
        更新組件狀態的單個鍵值
        
        Args:
            component: 組件名稱
            key: 狀態鍵
            value: 狀態值
            notify: 是否通知監聽者
            save: 是否自動保存
        """
        self.set_component_state(component, {key: value}, notify, save)
    
    def remove_component_state(self, component: str, key: str = None):
        """
        移除組件狀態
        
        Args:
            component: 組件名稱
            key: 狀態鍵（None表示移除整個組件狀態）
        """
        with self.lock:
            if component not in self.component_states:
                return
            
            if key is None:
                # 移除整個組件狀態
                del self.component_states[component]
                self.logger.info(f"🗑️ 移除組件 {component} 的所有狀態")
            else:
                # 移除特定鍵
                if key in self.component_states[component]:
                    del self.component_states[component][key]
                    self.logger.debug(f"🗑️ 移除組件 {component} 的狀態鍵: {key}")
            
            # 自動保存
            if self.auto_save:
                self._auto_save_if_needed()
    
    def set_global_state(self, key: str, value: Any, notify: bool = True, save: bool = None):
        """
        設置全局狀態
        
        Args:
            key: 狀態鍵
            value: 狀態值
            notify: 是否通知監聽者
            save: 是否自動保存
        """
        with self.lock:
            old_value = self.global_state.get(key)
            self.global_state[key] = value
            
            self.logger.debug(f"🌐 全局狀態更新: {key} = {value}")
            
            # 通知監聽者
            if notify and old_value != value:
                self._notify_global_state_change(key, old_value, value)
            
            # 自動保存
            if save is True or (save is None and self.auto_save):
                self._auto_save_if_needed()
    
    def get_global_state(self, key: str = None, default: Any = None) -> Any:
        """
        獲取全局狀態
        
        Args:
            key: 狀態鍵（None表示獲取所有全局狀態）
            default: 默認值
            
        Returns:
            狀態值或默認值
        """
        with self.lock:
            if key is None:
                return self.global_state.copy()
            else:
                return self.global_state.get(key, default)
    
    def subscribe_to_state_changes(self, component: str, 
                                  callback: Callable[[str, Dict[str, Any], Dict[str, Any]], None]):
        """
        訂閱組件狀態變化
        
        Args:
            component: 組件名稱
            callback: 回調函數 (component_name, old_state, new_state)
        """
        if component not in self.state_listeners:
            self.state_listeners[component] = []
        
        self.state_listeners[component].append(callback)
        self.logger.debug(f"📡 組件 {component} 添加狀態監聽器")
    
    def subscribe_to_global_state_changes(self, 
                                        callback: Callable[[str, Any, Any], None]):
        """
        訂閱全局狀態變化
        
        Args:
            callback: 回調函數 (key, old_value, new_value)
        """
        self.global_listeners.append(callback)
        self.logger.debug("📡 添加全局狀態監聽器")
    
    def unsubscribe_from_state_changes(self, component: str, callback: Callable):
        """
        取消訂閱組件狀態變化
        
        Args:
            component: 組件名稱
            callback: 回調函數
        """
        if component in self.state_listeners:
            try:
                self.state_listeners[component].remove(callback)
                self.logger.debug(f"📡 組件 {component} 移除狀態監聽器")
            except ValueError:
                pass
    
    def _notify_state_change(self, component: str, old_state: Dict[str, Any], 
                           new_state: Dict[str, Any]):
        """通知組件狀態變化"""
        if component in self.state_listeners:
            for callback in self.state_listeners[component]:
                try:
                    callback(component, old_state, new_state)
                except Exception as e:
                    self.logger.error(f"狀態變化回調執行失敗: {e}")
    
    def _notify_global_state_change(self, key: str, old_value: Any, new_value: Any):
        """通知全局狀態變化"""
        for callback in self.global_listeners:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                self.logger.error(f"全局狀態變化回調執行失敗: {e}")
    
    def _should_create_snapshot(self, component: str, old_state: Dict[str, Any], 
                               new_state: Dict[str, Any]) -> bool:
        """判斷是否應該創建狀態快照"""
        # 如果是重要狀態變化，創建快照
        important_keys = ['window_geometry', 'layout_state', 'user_preferences']
        
        for key in important_keys:
            if key in old_state or key in new_state:
                if old_state.get(key) != new_state.get(key):
                    return True
        
        return False
    
    def _create_state_snapshot(self):
        """創建狀態快照"""
        with self.lock:
            snapshot = StateSnapshot(
                timestamp=datetime.now(),
                component_states=self._deep_copy_dict(self.component_states),
                global_state=self._deep_copy_dict(self.global_state)
            )
            
            # 如果當前不在歷史末尾，清除後續歷史
            if self.current_history_index < len(self.state_history) - 1:
                self.state_history = self.state_history[:self.current_history_index + 1]
            
            # 添加新快照
            self.state_history.append(snapshot)
            self.current_history_index = len(self.state_history) - 1
            
            # 限制歷史大小
            if len(self.state_history) > self.max_history_size:
                self.state_history.pop(0)
                self.current_history_index -= 1
            
            self.logger.debug(f"📸 創建狀態快照，歷史大小: {len(self.state_history)}")
    
    def undo(self) -> bool:
        """
        撤銷到上一個狀態
        
        Returns:
            bool: 是否成功撤銷
        """
        with self.lock:
            if self.current_history_index <= 0:
                return False
            
            self.current_history_index -= 1
            snapshot = self.state_history[self.current_history_index]
            
            # 恢復狀態（不通知和保存）
            self.component_states = self._deep_copy_dict(snapshot.component_states)
            self.global_state = self._deep_copy_dict(snapshot.global_state)
            
            self.logger.info(f"↶ 撤銷到狀態快照: {snapshot.timestamp}")
            return True
    
    def redo(self) -> bool:
        """
        重做到下一個狀態
        
        Returns:
            bool: 是否成功重做
        """
        with self.lock:
            if self.current_history_index >= len(self.state_history) - 1:
                return False
            
            self.current_history_index += 1
            snapshot = self.state_history[self.current_history_index]
            
            # 恢復狀態（不通知和保存）
            self.component_states = self._deep_copy_dict(snapshot.component_states)
            self.global_state = self._deep_copy_dict(snapshot.global_state)
            
            self.logger.info(f"↷ 重做到狀態快照: {snapshot.timestamp}")
            return True
    
    def can_undo(self) -> bool:
        """檢查是否可以撤銷"""
        return self.current_history_index > 0
    
    def can_redo(self) -> bool:
        """檢查是否可以重做"""
        return self.current_history_index < len(self.state_history) - 1
    
    def save_state_to_file(self, filepath: str = None):
        """
        保存狀態到文件
        
        Args:
            filepath: 文件路徑（None表示使用默認路徑）
        """
        if filepath is None:
            filepath = self.state_file
        else:
            filepath = Path(filepath)
        
        try:
            with self.lock:
                state_data = {
                    "timestamp": datetime.now().isoformat(),
                    "component_states": self.component_states,
                    "global_state": self.global_state,
                    "version": "1.0"
                }
                
                # 確保目錄存在
                filepath.parent.mkdir(parents=True, exist_ok=True)
                
                # 保存到文件
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(state_data, f, indent=2, ensure_ascii=False, default=str)
                
                self.last_save_time = datetime.now()
                self.logger.debug(f"💾 狀態已保存到: {filepath}")
                
        except Exception as e:
            self.logger.error(f"❌ 保存狀態失敗: {e}")
    
    def load_state_from_file(self, filepath: str = None) -> bool:
        """
        從文件載入狀態
        
        Args:
            filepath: 文件路徑（None表示使用默認路徑）
            
        Returns:
            bool: 是否成功載入
        """
        if filepath is None:
            filepath = self.state_file
        else:
            filepath = Path(filepath)
        
        if not filepath.exists():
            self.logger.info(f"狀態文件不存在: {filepath}")
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            with self.lock:
                self.component_states = state_data.get("component_states", {})
                self.global_state = state_data.get("global_state", {})
                
                self.logger.info(f"📂 狀態已從文件載入: {filepath}")
                self.logger.info(f"載入了 {len(self.component_states)} 個組件狀態")
                
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 載入狀態失敗: {e}")
            return False
    
    def _load_state(self):
        """載入已保存的狀態"""
        self.load_state_from_file()
    
    def _auto_save_if_needed(self):
        """如果需要則自動保存"""
        if not self.auto_save:
            return
        
        now = datetime.now()
        if (now - self.last_save_time).total_seconds() >= self.save_interval:
            self.save_state_to_file()
    
    def _deep_copy_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """深拷貝字典"""
        try:
            return json.loads(json.dumps(data, default=str))
        except:
            # 如果JSON序列化失敗，使用pickle
            return pickle.loads(pickle.dumps(data))
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        獲取狀態摘要
        
        Returns:
            Dict: 狀態摘要信息
        """
        with self.lock:
            return {
                "component_count": len(self.component_states),
                "global_state_keys": list(self.global_state.keys()),
                "history_size": len(self.state_history),
                "can_undo": self.can_undo(),
                "can_redo": self.can_redo(),
                "last_save_time": self.last_save_time.isoformat(),
                "auto_save_enabled": self.auto_save
            }
    
    def clear_all_state(self):
        """清空所有狀態"""
        with self.lock:
            self.component_states.clear()
            self.global_state.clear()
            self.state_history.clear()
            self.current_history_index = -1
            
            self.logger.info("🗑️ 所有狀態已清空")
            
            if self.auto_save:
                self.save_state_to_file()
    
    def export_state(self, filepath: str) -> bool:
        """
        導出狀態到指定文件
        
        Args:
            filepath: 導出文件路徑
            
        Returns:
            bool: 是否成功導出
        """
        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "component_states": self.component_states,
                "global_state": self.global_state,
                "state_summary": self.get_state_summary(),
                "version": "1.0"
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"📤 狀態已導出到: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 導出狀態失敗: {e}")
            return False
    
    def import_state(self, filepath: str) -> bool:
        """
        從指定文件導入狀態
        
        Args:
            filepath: 導入文件路徑
            
        Returns:
            bool: 是否成功導入
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            with self.lock:
                # 備份當前狀態
                self._create_state_snapshot()
                
                # 導入新狀態
                self.component_states = import_data.get("component_states", {})
                self.global_state = import_data.get("global_state", {})
                
                self.logger.info(f"📥 狀態已從文件導入: {filepath}")
                
                # 自動保存
                if self.auto_save:
                    self.save_state_to_file()
                
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 導入狀態失敗: {e}")
            return False