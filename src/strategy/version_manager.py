#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 策略版本管理系統 - 任務12實現
實現策略版本控制、回滾和歷史管理功能
"""

import sys
import os
import json
import logging
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.strategy.strategy_config_manager import StrategyConfig, strategy_config_manager

logger = logging.getLogger(__name__)

@dataclass
class VersionInfo:
    """版本信息"""
    version: str
    created_at: datetime
    description: str
    changes: List[str] = field(default_factory=list)
    author: str = "system"
    is_stable: bool = False
    performance_metrics: Dict[str, float] = field(default_factory=dict)

@dataclass
class VersionHistory:
    """版本歷史記錄"""
    strategy_id: str
    strategy_name: str
    versions: List[VersionInfo] = field(default_factory=list)
    current_version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

class StrategyVersionManager:
    """策略版本管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.versions_dir = self.project_root / "config" / "strategy_versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        
        self.version_histories: Dict[str, VersionHistory] = {}
        self.load_all_version_histories()
    
    def create_version(self, strategy_id: str, description: str = "", 
                      changes: List[str] = None, author: str = "system") -> str:
        """創建新版本"""
        strategy = strategy_config_manager.get_strategy(strategy_id)
        if not strategy:
            logger.error(f"❌ 策略不存在: {strategy_id}")
            return ""
        
        # 獲取或創建版本歷史
        if strategy_id not in self.version_histories:
            self.version_histories[strategy_id] = VersionHistory(
                strategy_id=strategy_id,
                strategy_name=strategy.strategy_name
            )
        
        version_history = self.version_histories[strategy_id]
        
        # 生成新版本號
        new_version = self._generate_next_version(version_history.current_version)
        
        # 創建版本信息
        version_info = VersionInfo(
            version=new_version,
            created_at=datetime.now(),
            description=description,
            changes=changes or [],
            author=author,
            performance_metrics=strategy.performance_metrics.copy()
        )
        
        # 保存當前策略配置為版本快照
        self._save_version_snapshot(strategy_id, new_version, strategy)
        
        # 更新版本歷史
        version_history.versions.append(version_info)
        version_history.current_version = new_version
        version_history.last_updated = datetime.now()
        
        # 更新策略版本
        strategy.version = new_version
        strategy.updated_at = datetime.now()
        strategy_config_manager.save_strategy(strategy_id)
        
        # 保存版本歷史
        self.save_version_history(strategy_id)
        
        logger.info(f"📝 創建策略版本: {strategy.strategy_name} v{new_version}")
        return new_version
    
    def rollback_to_version(self, strategy_id: str, target_version: str) -> bool:
        """回滾到指定版本"""
        if strategy_id not in self.version_histories:
            logger.error(f"❌ 策略版本歷史不存在: {strategy_id}")
            return False
        
        version_history = self.version_histories[strategy_id]
        
        # 檢查目標版本是否存在
        target_version_info = None
        for version_info in version_history.versions:
            if version_info.version == target_version:
                target_version_info = version_info
                break
        
        if not target_version_info:
            logger.error(f"❌ 目標版本不存在: {target_version}")
            return False
        
        # 載入版本快照
        snapshot_strategy = self._load_version_snapshot(strategy_id, target_version)
        if not snapshot_strategy:
            logger.error(f"❌ 無法載入版本快照: {target_version}")
            return False
        
        # 創建回滾前的備份版本
        current_strategy = strategy_config_manager.get_strategy(strategy_id)
        if current_strategy:
            backup_version = f"{current_strategy.version}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._save_version_snapshot(strategy_id, backup_version, current_strategy)
            
            # 添加備份版本信息
            backup_info = VersionInfo(
                version=backup_version,
                created_at=datetime.now(),
                description=f"回滾前自動備份 (從 v{current_strategy.version} 回滾到 v{target_version})",
                author="system"
            )
            version_history.versions.append(backup_info)
        
        # 執行回滾
        snapshot_strategy.version = target_version
        snapshot_strategy.updated_at = datetime.now()
        
        # 更新策略配置管理器中的策略
        strategy_config_manager.strategies[strategy_id] = snapshot_strategy
        strategy_config_manager.save_strategy(strategy_id)
        
        # 更新版本歷史
        version_history.current_version = target_version
        version_history.last_updated = datetime.now()
        self.save_version_history(strategy_id)
        
        logger.info(f"🔄 策略回滾成功: {snapshot_strategy.strategy_name} -> v{target_version}")
        return True
    
    def get_version_history(self, strategy_id: str) -> Optional[VersionHistory]:
        """獲取版本歷史"""
        return self.version_histories.get(strategy_id)
    
    def get_version_info(self, strategy_id: str, version: str) -> Optional[VersionInfo]:
        """獲取特定版本信息"""
        version_history = self.version_histories.get(strategy_id)
        if not version_history:
            return None
        
        for version_info in version_history.versions:
            if version_info.version == version:
                return version_info
        
        return None
    
    def compare_versions(self, strategy_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """比較兩個版本的差異"""
        snapshot1 = self._load_version_snapshot(strategy_id, version1)
        snapshot2 = self._load_version_snapshot(strategy_id, version2)
        
        if not snapshot1 or not snapshot2:
            return {'error': '無法載入版本快照'}
        
        differences = {
            'version_comparison': f"{version1} vs {version2}",
            'timestamp': datetime.now().isoformat(),
            'differences': {}
        }
        
        # 比較MACD配置
        macd_diff = self._compare_configs(
            snapshot1.macd_config.__dict__,
            snapshot2.macd_config.__dict__
        )
        if macd_diff:
            differences['differences']['macd_config'] = macd_diff
        
        # 比較風險配置
        risk_diff = self._compare_configs(
            snapshot1.risk_config.__dict__,
            snapshot2.risk_config.__dict__
        )
        if risk_diff:
            differences['differences']['risk_config'] = risk_diff
        
        # 比較交易限額
        limits_diff = self._compare_configs(
            snapshot1.trading_limits.__dict__,
            snapshot2.trading_limits.__dict__
        )
        if limits_diff:
            differences['differences']['trading_limits'] = limits_diff
        
        # 比較性能指標
        perf_diff = self._compare_configs(
            snapshot1.performance_metrics,
            snapshot2.performance_metrics
        )
        if perf_diff:
            differences['differences']['performance_metrics'] = perf_diff
        
        return differences
    
    def mark_version_as_stable(self, strategy_id: str, version: str) -> bool:
        """標記版本為穩定版本"""
        version_info = self.get_version_info(strategy_id, version)
        if not version_info:
            logger.error(f"❌ 版本不存在: {version}")
            return False
        
        # 取消其他版本的穩定標記
        version_history = self.version_histories[strategy_id]
        for v_info in version_history.versions:
            v_info.is_stable = False
        
        # 標記當前版本為穩定
        version_info.is_stable = True
        version_info.description += " [穩定版本]"
        
        self.save_version_history(strategy_id)
        
        logger.info(f"✅ 標記穩定版本: v{version}")
        return True
    
    def get_stable_version(self, strategy_id: str) -> Optional[str]:
        """獲取穩定版本"""
        version_history = self.version_histories.get(strategy_id)
        if not version_history:
            return None
        
        for version_info in version_history.versions:
            if version_info.is_stable:
                return version_info.version
        
        return None
    
    def cleanup_old_versions(self, strategy_id: str, keep_count: int = 10) -> int:
        """清理舊版本（保留最新的N個版本）"""
        version_history = self.version_histories.get(strategy_id)
        if not version_history:
            return 0
        
        # 按創建時間排序
        sorted_versions = sorted(
            version_history.versions,
            key=lambda x: x.created_at,
            reverse=True
        )
        
        # 保留穩定版本和最新版本
        versions_to_keep = []
        versions_to_remove = []
        
        for i, version_info in enumerate(sorted_versions):
            if (i < keep_count or 
                version_info.is_stable or 
                version_info.version == version_history.current_version):
                versions_to_keep.append(version_info)
            else:
                versions_to_remove.append(version_info)
        
        # 刪除舊版本快照
        removed_count = 0
        for version_info in versions_to_remove:
            snapshot_file = self.versions_dir / strategy_id / f"{version_info.version}.json"
            if snapshot_file.exists():
                snapshot_file.unlink()
                removed_count += 1
        
        # 更新版本歷史
        version_history.versions = versions_to_keep
        self.save_version_history(strategy_id)
        
        logger.info(f"🧹 清理舊版本: 刪除了 {removed_count} 個版本")
        return removed_count
    
    def export_version(self, strategy_id: str, version: str) -> Optional[Dict[str, Any]]:
        """導出特定版本"""
        snapshot = self._load_version_snapshot(strategy_id, version)
        if not snapshot:
            return None
        
        version_info = self.get_version_info(strategy_id, version)
        
        export_data = {
            'strategy_id': strategy_id,
            'version': version,
            'version_info': {
                'created_at': version_info.created_at.isoformat() if version_info else None,
                'description': version_info.description if version_info else "",
                'changes': version_info.changes if version_info else [],
                'author': version_info.author if version_info else "unknown",
                'is_stable': version_info.is_stable if version_info else False
            },
            'strategy_config': strategy_config_manager.export_strategy(strategy_id),
            'export_time': datetime.now().isoformat()
        }
        
        return export_data
    
    def _generate_next_version(self, current_version: str) -> str:
        """生成下一個版本號"""
        try:
            parts = current_version.split('.')
            if len(parts) == 3:
                major, minor, patch = map(int, parts)
                patch += 1
                return f"{major}.{minor}.{patch}"
            else:
                return f"{current_version}.1"
        except:
            return "1.0.1"
    
    def _save_version_snapshot(self, strategy_id: str, version: str, strategy: StrategyConfig):
        """保存版本快照"""
        strategy_version_dir = self.versions_dir / strategy_id
        strategy_version_dir.mkdir(exist_ok=True)
        
        snapshot_file = strategy_version_dir / f"{version}.json"
        
        # 導出策略配置
        snapshot_data = strategy_config_manager.export_strategy(strategy_id)
        if snapshot_data:
            snapshot_data['snapshot_version'] = version
            snapshot_data['snapshot_time'] = datetime.now().isoformat()
            
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
    
    def _load_version_snapshot(self, strategy_id: str, version: str) -> Optional[StrategyConfig]:
        """載入版本快照"""
        snapshot_file = self.versions_dir / strategy_id / f"{version}.json"
        
        if not snapshot_file.exists():
            return None
        
        try:
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)
            
            # 使用導入功能重建策略配置
            temp_strategy_id = strategy_config_manager.import_strategy(snapshot_data, f"temp_{version}")
            if temp_strategy_id:
                temp_strategy = strategy_config_manager.get_strategy(temp_strategy_id)
                
                # 恢復原始ID和版本
                if temp_strategy:
                    temp_strategy.strategy_id = strategy_id
                    temp_strategy.version = version
                    
                    # 清理臨時策略
                    strategy_config_manager.delete_strategy(temp_strategy_id)
                    
                    return temp_strategy
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 載入版本快照失敗: {e}")
            return None
    
    def _compare_configs(self, config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
        """比較兩個配置的差異"""
        differences = {}
        
        all_keys = set(config1.keys()) | set(config2.keys())
        
        for key in all_keys:
            value1 = config1.get(key)
            value2 = config2.get(key)
            
            if value1 != value2:
                differences[key] = {
                    'old_value': value1,
                    'new_value': value2
                }
        
        return differences
    
    def save_version_history(self, strategy_id: str):
        """保存版本歷史"""
        if strategy_id not in self.version_histories:
            return
        
        version_history = self.version_histories[strategy_id]
        history_file = self.versions_dir / f"{strategy_id}_history.json"
        
        # 轉換為可序列化的格式
        history_data = {
            'strategy_id': version_history.strategy_id,
            'strategy_name': version_history.strategy_name,
            'current_version': version_history.current_version,
            'created_at': version_history.created_at.isoformat(),
            'last_updated': version_history.last_updated.isoformat(),
            'versions': [
                {
                    'version': v.version,
                    'created_at': v.created_at.isoformat(),
                    'description': v.description,
                    'changes': v.changes,
                    'author': v.author,
                    'is_stable': v.is_stable,
                    'performance_metrics': v.performance_metrics
                }
                for v in version_history.versions
            ]
        }
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, ensure_ascii=False)
    
    def load_all_version_histories(self):
        """載入所有版本歷史"""
        if not self.versions_dir.exists():
            return
        
        for history_file in self.versions_dir.glob("*_history.json"):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                version_history = VersionHistory(
                    strategy_id=history_data['strategy_id'],
                    strategy_name=history_data['strategy_name'],
                    current_version=history_data['current_version'],
                    created_at=datetime.fromisoformat(history_data['created_at']),
                    last_updated=datetime.fromisoformat(history_data['last_updated'])
                )
                
                # 載入版本信息
                for v_data in history_data['versions']:
                    version_info = VersionInfo(
                        version=v_data['version'],
                        created_at=datetime.fromisoformat(v_data['created_at']),
                        description=v_data['description'],
                        changes=v_data.get('changes', []),
                        author=v_data.get('author', 'system'),
                        is_stable=v_data.get('is_stable', False),
                        performance_metrics=v_data.get('performance_metrics', {})
                    )
                    version_history.versions.append(version_info)
                
                self.version_histories[version_history.strategy_id] = version_history
                
            except Exception as e:
                logger.error(f"❌ 載入版本歷史失敗 {history_file}: {e}")
        
        logger.info(f"📚 載入了 {len(self.version_histories)} 個策略的版本歷史")

# 全局版本管理器實例
version_manager = StrategyVersionManager()

# 便捷函數
def create_strategy_version(strategy_id: str, description: str = "", changes: List[str] = None) -> str:
    """創建策略版本"""
    return version_manager.create_version(strategy_id, description, changes)

def rollback_strategy(strategy_id: str, target_version: str) -> bool:
    """回滾策略版本"""
    return version_manager.rollback_to_version(strategy_id, target_version)

def get_strategy_versions(strategy_id: str) -> Optional[VersionHistory]:
    """獲取策略版本歷史"""
    return version_manager.get_version_history(strategy_id)