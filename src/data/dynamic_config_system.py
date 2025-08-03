#!/usr/bin/env python3
"""
交易對動態配置系統
實現任務1.3: 創建TradingPairConfig數據模型、熱更新機制、配置模板和審計功能
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
import hashlib
import copy

logger = logging.getLogger(__name__)

class ConfigChangeType(Enum):
    """配置變更類型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ROLLBACK = "rollback"

class ValidationLevel(Enum):
    """驗證級別"""
    BASIC = "basic"
    STRICT = "strict"
    CUSTOM = "custom"

@dataclass
class TradingPairConfig:
    """交易對配置數據模型"""
    pair: str
    enabled: bool = True
    
    # 基本交易參數
    min_order_size: float = 0.001
    max_order_size: float = 10.0
    price_precision: int = 2
    volume_precision: int = 6
    
    # 風險管理參數
    max_position_size: float = 0.1  # 最大倉位比例
    stop_loss_percent: float = 0.08  # 止損百分比
    take_profit_percent: float = 0.15  # 止盈百分比
    
    # 數據更新參數
    update_interval: int = 60  # 秒
    data_retention_days: int = 30
    
    # 策略參數
    allowed_strategies: List[str] = field(default_factory=lambda: ["grid", "dca", "ai_signal"])
    strategy_weights: Dict[str, float] = field(default_factory=lambda: {"grid": 0.4, "dca": 0.3, "ai_signal": 0.3})
    
    # 技術指標參數
    technical_indicators: Dict[str, Any] = field(default_factory=lambda: {
        "rsi_period": 14,
        "macd_fast": 12,
        "macd_slow": 26,
        "bollinger_period": 20
    })
    
    # 元數據
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    
    def validate(self, level: ValidationLevel = ValidationLevel.BASIC) -> List[str]:
        """驗證配置參數"""
        errors = []
        
        # 基本驗證
        if not self.pair or not isinstance(self.pair, str):
            errors.append("交易對名稱不能為空")
        
        if self.min_order_size <= 0:
            errors.append("最小訂單大小必須大於0")
            
        if self.max_order_size <= self.min_order_size:
            errors.append("最大訂單大小必須大於最小訂單大小")
        
        if not 0 < self.max_position_size <= 1:
            errors.append("最大倉位比例必須在0-1之間")
        
        # 嚴格驗證
        if level in [ValidationLevel.STRICT, ValidationLevel.CUSTOM]:
            if self.stop_loss_percent <= 0 or self.stop_loss_percent > 0.5:
                errors.append("止損百分比必須在0-50%之間")
                
            if self.take_profit_percent <= 0 or self.take_profit_percent > 1.0:
                errors.append("止盈百分比必須在0-100%之間")
                
            if sum(self.strategy_weights.values()) != 1.0:
                errors.append("策略權重總和必須等於1.0")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingPairConfig':
        """從字典創建配置"""
        # 處理datetime字段
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    def get_hash(self) -> str:
        """獲取配置哈希值"""
        config_str = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.md5(config_str.encode()).hexdigest()

@dataclass
class ConfigChangeRecord:
    """配置變更記錄"""
    id: str
    pair: str
    change_type: ConfigChangeType
    old_config: Optional[Dict[str, Any]]
    new_config: Optional[Dict[str, Any]]
    timestamp: datetime
    user: str = "system"
    reason: str = ""
    rollback_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'id': self.id,
            'pair': self.pair,
            'change_type': self.change_type.value,
            'old_config': self.old_config,
            'new_config': self.new_config,
            'timestamp': self.timestamp.isoformat(),
            'user': self.user,
            'reason': self.reason,
            'rollback_id': self.rollback_id
        }

class ConfigTemplate:
    """配置模板管理"""
    
    def __init__(self):
        self.templates = {
            'conservative': TradingPairConfig(
                pair="TEMPLATE",
                max_position_size=0.05,
                stop_loss_percent=0.05,
                take_profit_percent=0.10,
                strategy_weights={"grid": 0.6, "dca": 0.4, "ai_signal": 0.0}
            ),
            'balanced': TradingPairConfig(
                pair="TEMPLATE",
                max_position_size=0.1,
                stop_loss_percent=0.08,
                take_profit_percent=0.15,
                strategy_weights={"grid": 0.4, "dca": 0.3, "ai_signal": 0.3}
            ),
            'aggressive': TradingPairConfig(
                pair="TEMPLATE",
                max_position_size=0.2,
                stop_loss_percent=0.12,
                take_profit_percent=0.25,
                strategy_weights={"grid": 0.2, "dca": 0.2, "ai_signal": 0.6}
            )
        }
    
    def get_template(self, template_name: str) -> Optional[TradingPairConfig]:
        """獲取配置模板"""
        return self.templates.get(template_name)
    
    def create_config_from_template(self, pair: str, template_name: str) -> Optional[TradingPairConfig]:
        """從模板創建配置"""
        template = self.get_template(template_name)
        if template:
            config = copy.deepcopy(template)
            config.pair = pair
            config.created_at = datetime.now()
            config.updated_at = datetime.now()
            return config
        return None


class DynamicConfigManager:
    """動態配置管理器"""
    
    def __init__(self, config_dir: str = "config/trading_pairs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.configs: Dict[str, TradingPairConfig] = {}
        self.change_history: List[ConfigChangeRecord] = []
        self.template_manager = ConfigTemplate()
        
        # 線程安全
        self._lock = threading.RLock()
        
        # 配置文件路徑
        self.config_file = self.config_dir / "configs.json"
        self.history_file = self.config_dir / "change_history.json"
        
        # 加載現有配置
        self._load_configs()
        self._load_history()
        
        logger.info("🔧 動態配置管理器初始化完成")
    
    def create_config(self, pair: str, template_name: str = "balanced", 
                     custom_params: Optional[Dict[str, Any]] = None) -> bool:
        """創建新的交易對配置"""
        with self._lock:
            try:
                if pair in self.configs:
                    logger.warning(f"⚠️ 交易對 {pair} 配置已存在")
                    return False
                
                # 從模板創建配置
                config = self.template_manager.create_config_from_template(pair, template_name)
                if not config:
                    logger.error(f"❌ 無效的模板名稱: {template_name}")
                    return False
                
                # 應用自定義參數
                if custom_params:
                    for key, value in custom_params.items():
                        if hasattr(config, key):
                            setattr(config, key, value)
                
                # 驗證配置
                errors = config.validate(ValidationLevel.STRICT)
                if errors:
                    logger.error(f"❌ 配置驗證失敗: {errors}")
                    return False
                
                # 保存配置
                self.configs[pair] = config
                
                # 記錄變更
                self._record_change(
                    pair=pair,
                    change_type=ConfigChangeType.CREATE,
                    old_config=None,
                    new_config=config.to_dict(),
                    reason=f"從模板 {template_name} 創建配置"
                )
                
                # 持久化
                self._save_configs()
                
                logger.info(f"✅ 成功創建 {pair} 配置")
                return True
                
            except Exception as e:
                logger.error(f"❌ 創建配置失敗: {e}")
                return False
    
    def update_config(self, pair: str, updates: Dict[str, Any], 
                     reason: str = "手動更新") -> bool:
        """更新交易對配置"""
        with self._lock:
            try:
                if pair not in self.configs:
                    logger.error(f"❌ 交易對 {pair} 配置不存在")
                    return False
                
                old_config = copy.deepcopy(self.configs[pair])
                
                # 應用更新
                for key, value in updates.items():
                    if hasattr(self.configs[pair], key):
                        setattr(self.configs[pair], key, value)
                    else:
                        logger.warning(f"⚠️ 忽略無效參數: {key}")
                
                # 更新元數據
                self.configs[pair].updated_at = datetime.now()
                self.configs[pair].version += 1
                
                # 驗證更新後的配置
                errors = self.configs[pair].validate(ValidationLevel.STRICT)
                if errors:
                    # 回滾更改
                    self.configs[pair] = old_config
                    logger.error(f"❌ 配置驗證失敗，已回滾: {errors}")
                    return False
                
                # 記錄變更
                self._record_change(
                    pair=pair,
                    change_type=ConfigChangeType.UPDATE,
                    old_config=old_config.to_dict(),
                    new_config=self.configs[pair].to_dict(),
                    reason=reason
                )
                
                # 持久化
                self._save_configs()
                
                logger.info(f"✅ 成功更新 {pair} 配置")
                return True
                
            except Exception as e:
                logger.error(f"❌ 更新配置失敗: {e}")
                return False
    
    def get_config(self, pair: str) -> Optional[TradingPairConfig]:
        """獲取交易對配置"""
        with self._lock:
            return self.configs.get(pair)
    
    def get_all_configs(self) -> Dict[str, TradingPairConfig]:
        """獲取所有配置"""
        with self._lock:
            return copy.deepcopy(self.configs)
    
    def delete_config(self, pair: str, reason: str = "手動刪除") -> bool:
        """刪除交易對配置"""
        with self._lock:
            try:
                if pair not in self.configs:
                    logger.error(f"❌ 交易對 {pair} 配置不存在")
                    return False
                
                old_config = self.configs[pair].to_dict()
                del self.configs[pair]
                
                # 記錄變更
                self._record_change(
                    pair=pair,
                    change_type=ConfigChangeType.DELETE,
                    old_config=old_config,
                    new_config=None,
                    reason=reason
                )
                
                # 持久化
                self._save_configs()
                
                logger.info(f"✅ 成功刪除 {pair} 配置")
                return True
                
            except Exception as e:
                logger.error(f"❌ 刪除配置失敗: {e}")
                return False
    
    def rollback_config(self, pair: str, change_id: str) -> bool:
        """回滾配置到指定變更"""
        with self._lock:
            try:
                # 查找變更記錄
                target_change = None
                for change in self.change_history:
                    if change.id == change_id and change.pair == pair:
                        target_change = change
                        break
                
                if not target_change:
                    logger.error(f"❌ 未找到變更記錄: {change_id}")
                    return False
                
                # 獲取回滾目標配置
                if target_change.change_type == ConfigChangeType.CREATE:
                    # 創建操作的回滾是刪除
                    if pair in self.configs:
                        old_config = self.configs[pair].to_dict()
                        del self.configs[pair]
                        
                        self._record_change(
                            pair=pair,
                            change_type=ConfigChangeType.ROLLBACK,
                            old_config=old_config,
                            new_config=None,
                            reason=f"回滾創建操作 {change_id}",
                            rollback_id=change_id
                        )
                elif target_change.change_type in [ConfigChangeType.UPDATE, ConfigChangeType.DELETE]:
                    # 更新/刪除操作的回滾是恢復舊配置
                    if target_change.old_config:
                        old_config = self.configs.get(pair)
                        old_config_dict = old_config.to_dict() if old_config else None
                        
                        self.configs[pair] = TradingPairConfig.from_dict(target_change.old_config)
                        
                        self._record_change(
                            pair=pair,
                            change_type=ConfigChangeType.ROLLBACK,
                            old_config=old_config_dict,
                            new_config=target_change.old_config,
                            reason=f"回滾到變更 {change_id} 之前的狀態",
                            rollback_id=change_id
                        )
                
                # 持久化
                self._save_configs()
                
                logger.info(f"✅ 成功回滾 {pair} 配置到變更 {change_id}")
                return True
                
            except Exception as e:
                logger.error(f"❌ 回滾配置失敗: {e}")
                return False
    
    def get_change_history(self, pair: Optional[str] = None, 
                          limit: int = 50) -> List[ConfigChangeRecord]:
        """獲取配置變更歷史"""
        with self._lock:
            history = self.change_history
            
            if pair:
                history = [change for change in history if change.pair == pair]
            
            # 按時間倒序排列
            history.sort(key=lambda x: x.timestamp, reverse=True)
            
            return history[:limit]
    
    def auto_optimize_config(self, pair: str, performance_data: Dict[str, float]) -> bool:
        """基於性能數據自動優化配置"""
        with self._lock:
            try:
                if pair not in self.configs:
                    logger.error(f"❌ 交易對 {pair} 配置不存在")
                    return False
                
                config = self.configs[pair]
                old_config = copy.deepcopy(config)
                
                # 基於性能數據調整參數
                win_rate = performance_data.get('win_rate', 0.5)
                avg_profit = performance_data.get('avg_profit', 0.0)
                max_drawdown = performance_data.get('max_drawdown', 0.0)
                
                # 優化邏輯
                if win_rate < 0.4:  # 勝率過低
                    config.stop_loss_percent = min(config.stop_loss_percent * 0.8, 0.05)
                    config.take_profit_percent = max(config.take_profit_percent * 1.2, 0.20)
                elif win_rate > 0.7:  # 勝率很高
                    config.take_profit_percent = min(config.take_profit_percent * 0.9, 0.12)
                
                if max_drawdown > 0.15:  # 回撤過大
                    config.max_position_size = max(config.max_position_size * 0.8, 0.02)
                elif max_drawdown < 0.05:  # 回撤很小
                    config.max_position_size = min(config.max_position_size * 1.1, 0.2)
                
                # 驗證優化後的配置
                errors = config.validate(ValidationLevel.STRICT)
                if errors:
                    self.configs[pair] = old_config
                    logger.error(f"❌ 自動優化驗證失敗: {errors}")
                    return False
                
                # 更新元數據
                config.updated_at = datetime.now()
                config.version += 1
                
                # 記錄變更
                self._record_change(
                    pair=pair,
                    change_type=ConfigChangeType.UPDATE,
                    old_config=old_config.to_dict(),
                    new_config=config.to_dict(),
                    reason=f"自動優化 - 勝率:{win_rate:.2f}, 回撤:{max_drawdown:.2f}"
                )
                
                # 持久化
                self._save_configs()
                
                logger.info(f"✅ 成功自動優化 {pair} 配置")
                return True
                
            except Exception as e:
                logger.error(f"❌ 自動優化配置失敗: {e}")
                return False
    
    def _record_change(self, pair: str, change_type: ConfigChangeType,
                      old_config: Optional[Dict[str, Any]], 
                      new_config: Optional[Dict[str, Any]],
                      reason: str, rollback_id: Optional[str] = None):
        """記錄配置變更"""
        change_id = f"{pair}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.change_history)}"
        
        change_record = ConfigChangeRecord(
            id=change_id,
            pair=pair,
            change_type=change_type,
            old_config=old_config,
            new_config=new_config,
            timestamp=datetime.now(),
            reason=reason,
            rollback_id=rollback_id
        )
        
        self.change_history.append(change_record)
        
        # 保持歷史記錄在合理範圍內
        if len(self.change_history) > 1000:
            self.change_history = self.change_history[-500:]
        
        # 持久化歷史記錄
        self._save_history()
    
    def _load_configs(self):
        """加載配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for pair, config_data in data.items():
                    self.configs[pair] = TradingPairConfig.from_dict(config_data)
                
                logger.info(f"✅ 加載 {len(self.configs)} 個交易對配置")
            else:
                logger.info("📝 配置文件不存在，將創建新文件")
                
        except Exception as e:
            logger.error(f"❌ 加載配置文件失敗: {e}")
    
    def _save_configs(self):
        """保存配置文件"""
        try:
            data = {}
            for pair, config in self.configs.items():
                data[pair] = config.to_dict()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            logger.error(f"❌ 保存配置文件失敗: {e}")
    
    def _load_history(self):
        """加載變更歷史"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for record_data in data:
                    record = ConfigChangeRecord(
                        id=record_data['id'],
                        pair=record_data['pair'],
                        change_type=ConfigChangeType(record_data['change_type']),
                        old_config=record_data.get('old_config'),
                        new_config=record_data.get('new_config'),
                        timestamp=datetime.fromisoformat(record_data['timestamp']),
                        user=record_data.get('user', 'system'),
                        reason=record_data.get('reason', ''),
                        rollback_id=record_data.get('rollback_id')
                    )
                    self.change_history.append(record)
                
                logger.info(f"✅ 加載 {len(self.change_history)} 條變更記錄")
                
        except Exception as e:
            logger.error(f"❌ 加載變更歷史失敗: {e}")
    
    def _save_history(self):
        """保存變更歷史"""
        try:
            data = [record.to_dict() for record in self.change_history]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            logger.error(f"❌ 保存變更歷史失敗: {e}")


# 全局配置管理器實例
_config_manager = None

def get_dynamic_config_manager() -> DynamicConfigManager:
    """獲取全局動態配置管理器實例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = DynamicConfigManager()
    return _config_manager