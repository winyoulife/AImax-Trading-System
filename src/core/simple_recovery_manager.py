#!/usr/bin/env python3
"""
簡化版動態恢復管理器 - 用於測試
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

class RecoveryState(Enum):
    """恢復狀態"""
    NORMAL = "normal"
    RECOVERING = "recovering"
    FAILED = "failed"
    COMPLETED = "completed"

class BackupType(Enum):
    """備份類型"""
    FULL = "full"
    INCREMENTAL = "incremental"
    EMERGENCY = "emergency"

@dataclass
class SystemSnapshot:
    """系統快照數據結構"""
    snapshot_id: str
    timestamp: datetime
    backup_type: BackupType
    components: Dict[str, Any]
    metadata: Dict[str, Any]
    file_path: Optional[str] = None

class SimpleRecoveryManager:
    """簡化版恢復管理器"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 恢復狀態
        self.recovery_state = RecoveryState.NORMAL
        self.recovery_progress = 0.0
        
        # 系統快照管理
        self.snapshots: List[SystemSnapshot] = []
        self.max_snapshots = 10
        
        # 組件註冊
        self.registered_components: Dict[str, Any] = {}
        
        # 設置日誌
        self.logger = logging.getLogger(f"{__name__}.SimpleRecoveryManager")
        self.logger.info("簡化版恢復管理器初始化完成")
    
    def register_component(self, name: str, component: Any):
        """註冊組件"""
        self.registered_components[name] = component
        self.logger.info(f"組件已註冊: {name}")
    
    def create_snapshot(self, backup_type: BackupType = BackupType.INCREMENTAL) -> SystemSnapshot:
        """創建系統快照"""
        snapshot_id = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now()
        
        # 收集組件數據
        components_data = {}
        for name, component in self.registered_components.items():
            try:
                if hasattr(component, 'get_state'):
                    components_data[name] = component.get_state()
                else:
                    components_data[name] = {"value": str(component)}
            except Exception as e:
                components_data[name] = {"error": str(e)}
        
        # 創建快照
        snapshot = SystemSnapshot(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            backup_type=backup_type,
            components=components_data,
            metadata={"timestamp": timestamp.isoformat()}
        )
        
        # 保存快照
        snapshot_file = self.backup_dir / f"{snapshot_id}.json"
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump({
                'snapshot_id': snapshot_id,
                'timestamp': timestamp.isoformat(),
                'backup_type': backup_type.value,
                'components': components_data,
                'metadata': snapshot.metadata
            }, f, indent=2, ensure_ascii=False)
        
        snapshot.file_path = str(snapshot_file)
        self.snapshots.append(snapshot)
        
        # 限制快照數量
        if len(self.snapshots) > self.max_snapshots:
            old_snapshot = self.snapshots.pop(0)
            self._cleanup_snapshot(old_snapshot)
        
        self.logger.info(f"系統快照已創建: {snapshot_id}")
        return snapshot
    
    def restore_from_snapshot(self, snapshot_id: str) -> bool:
        """從快照恢復系統"""
        try:
            self.recovery_state = RecoveryState.RECOVERING
            self.recovery_progress = 0.0
            
            # 查找快照
            snapshot = None
            for s in self.snapshots:
                if s.snapshot_id == snapshot_id:
                    snapshot = s
                    break
            
            if not snapshot:
                self.logger.error(f"找不到快照: {snapshot_id}")
                return False
            
            # 恢復組件
            total_components = len(snapshot.components)
            restored_components = 0
            
            for name, component_data in snapshot.components.items():
                try:
                    if name in self.registered_components:
                        component = self.registered_components[name]
                        if hasattr(component, 'restore_state'):
                            component.restore_state(component_data)
                        restored_components += 1
                        self.recovery_progress = (restored_components / total_components) * 100
                except Exception as e:
                    self.logger.error(f"恢復組件 {name} 失敗: {e}")
            
            self.recovery_state = RecoveryState.COMPLETED
            self.recovery_progress = 100.0
            
            self.logger.info(f"系統恢復完成: {restored_components}/{total_components} 組件已恢復")
            return True
            
        except Exception as e:
            self.logger.error(f"系統恢復失敗: {e}")
            self.recovery_state = RecoveryState.FAILED
            return False
    
    def _cleanup_snapshot(self, snapshot: SystemSnapshot):
        """清理快照文件"""
        try:
            if snapshot.file_path and Path(snapshot.file_path).exists():
                Path(snapshot.file_path).unlink()
                self.logger.info(f"已清理快照文件: {snapshot.snapshot_id}")
        except Exception as e:
            self.logger.error(f"清理快照文件失敗: {e}")
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """獲取恢復狀態"""
        return {
            "recovery_state": self.recovery_state.value,
            "recovery_progress": self.recovery_progress,
            "snapshots_count": len(self.snapshots),
            "registered_components": list(self.registered_components.keys())
        }
    
    def cleanup(self):
        """清理資源"""
        for snapshot in self.snapshots:
            self._cleanup_snapshot(snapshot)
        self.logger.info("恢復管理器資源清理完成")