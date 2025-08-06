#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 交易策略配置管理器 - 任務12實現
實現MACD參數動態配置、交易限額風險控制、策略版本管理
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import copy

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    """策略類型枚舉"""
    MACD = "macd"
    VOLUME_MACD = "volume_macd"
    TRAILING_STOP = "trailing_stop"
    MULTI_TIMEFRAME = "multi_timeframe"
    CUSTOM = "custom"

class RiskLevel(Enum):
    """風險等級枚舉"""
    CONSERVATIVE = "conservative"  # 保守
    MODERATE = "moderate"         # 適中
    AGGRESSIVE = "aggressive"     # 激進
    CUSTOM = "custom"            # 自定義

@dataclass
class MACDConfig:
    """MACD策略配置"""
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9
    min_confidence: float = 0.85
    volume_threshold: float = 1.5
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    enable_volume_filter: bool = True
    enable_rsi_filter: bool = True

@dataclass
class RiskConfig:
    """風險控制配置"""
    max_position_size: float = 0.1      # 最大倉位比例
    max_daily_trades: int = 10          # 每日最大交易次數
    stop_loss_pct: float = 0.05         # 止損百分比
    take_profit_pct: float = 0.10       # 止盈百分比
    max_drawdown_pct: float = 0.15      # 最大回撤百分比
    min_balance_usdt: float = 100.0     # 最小餘額要求
    cooldown_minutes: int = 30          # 交易冷卻時間
    enable_trailing_stop: bool = True   # 啟用追蹤止損

@dataclass
class TradingLimits:
    """交易限額配置"""
    min_trade_amount: float = 10.0      # 最小交易金額
    max_trade_amount: float = 1000.0    # 最大交易金額
    daily_loss_limit: float = 500.0     # 每日虧損限額
    weekly_loss_limit: float = 2000.0   # 每週虧損限額
    monthly_loss_limit: float = 5000.0  # 每月虧損限額
    max_open_positions: int = 3         # 最大開倉數量
    allowed_symbols: List[str] = field(default_factory=lambda: ['BTCUSDT', 'ETHUSDT'])

@dataclass
class StrategyConfig:
    """完整策略配置"""
    strategy_id: str
    strategy_name: str
    strategy_type: StrategyType
    version: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    description: str = ""
    
    # 策略參數
    macd_config: MACDConfig = field(default_factory=MACDConfig)
    risk_config: RiskConfig = field(default_factory=RiskConfig)
    trading_limits: TradingLimits = field(default_factory=TradingLimits)
    
    # 回測結果
    backtest_results: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    # 自定義參數
    custom_params: Dict[str, Any] = field(default_factory=dict)

class StrategyConfigManager:
    """策略配置管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config" / "strategies"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.strategies: Dict[str, StrategyConfig] = {}
        self.active_strategy_id: Optional[str] = None
        
        # 預設策略模板
        self.strategy_templates = {
            RiskLevel.CONSERVATIVE: {
                'macd_config': MACDConfig(
                    min_confidence=0.90,
                    volume_threshold=2.0,
                    enable_volume_filter=True,
                    enable_rsi_filter=True
                ),
                'risk_config': RiskConfig(
                    max_position_size=0.05,
                    max_daily_trades=5,
                    stop_loss_pct=0.03,
                    take_profit_pct=0.06,
                    max_drawdown_pct=0.10
                ),
                'trading_limits': TradingLimits(
                    max_trade_amount=500.0,
                    daily_loss_limit=200.0,
                    max_open_positions=2
                )
            },
            RiskLevel.MODERATE: {
                'macd_config': MACDConfig(
                    min_confidence=0.85,
                    volume_threshold=1.5,
                    enable_volume_filter=True,
                    enable_rsi_filter=True
                ),
                'risk_config': RiskConfig(
                    max_position_size=0.10,
                    max_daily_trades=10,
                    stop_loss_pct=0.05,
                    take_profit_pct=0.10,
                    max_drawdown_pct=0.15
                ),
                'trading_limits': TradingLimits(
                    max_trade_amount=1000.0,
                    daily_loss_limit=500.0,
                    max_open_positions=3
                )
            },
            RiskLevel.AGGRESSIVE: {
                'macd_config': MACDConfig(
                    min_confidence=0.75,
                    volume_threshold=1.2,
                    enable_volume_filter=False,
                    enable_rsi_filter=False
                ),
                'risk_config': RiskConfig(
                    max_position_size=0.20,
                    max_daily_trades=20,
                    stop_loss_pct=0.08,
                    take_profit_pct=0.15,
                    max_drawdown_pct=0.25
                ),
                'trading_limits': TradingLimits(
                    max_trade_amount=2000.0,
                    daily_loss_limit=1000.0,
                    max_open_positions=5
                )
            }
        }
        
        self.load_all_strategies()
    
    def create_strategy(self, strategy_name: str, strategy_type: StrategyType, 
                       risk_level: RiskLevel = RiskLevel.MODERATE,
                       description: str = "") -> str:
        """創建新策略"""
        strategy_id = self._generate_strategy_id(strategy_name)
        
        # 使用模板創建策略
        template = self.strategy_templates.get(risk_level, self.strategy_templates[RiskLevel.MODERATE])
        
        strategy_config = StrategyConfig(
            strategy_id=strategy_id,
            strategy_name=strategy_name,
            strategy_type=strategy_type,
            version="1.0.0",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            description=description,
            macd_config=copy.deepcopy(template['macd_config']),
            risk_config=copy.deepcopy(template['risk_config']),
            trading_limits=copy.deepcopy(template['trading_limits'])
        )
        
        self.strategies[strategy_id] = strategy_config
        self.save_strategy(strategy_id)
        
        logger.info(f"📝 創建策略: {strategy_name} ({strategy_id})")
        return strategy_id
    
    def update_strategy(self, strategy_id: str, updates: Dict[str, Any]) -> bool:
        """更新策略配置"""
        if strategy_id not in self.strategies:
            logger.error(f"❌ 策略不存在: {strategy_id}")
            return False
        
        strategy = self.strategies[strategy_id]
        
        # 創建新版本
        old_version = strategy.version
        strategy.version = self._increment_version(old_version)
        strategy.updated_at = datetime.now()
        
        # 更新配置
        for key, value in updates.items():
            if hasattr(strategy, key):
                if key in ['macd_config', 'risk_config', 'trading_limits']:
                    # 更新嵌套配置
                    config_obj = getattr(strategy, key)
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if hasattr(config_obj, sub_key):
                                setattr(config_obj, sub_key, sub_value)
                else:
                    setattr(strategy, key, value)
        
        self.save_strategy(strategy_id)
        logger.info(f"📝 更新策略: {strategy.strategy_name} ({old_version} -> {strategy.version})")
        
        return True
    
    def get_strategy(self, strategy_id: str) -> Optional[StrategyConfig]:
        """獲取策略配置"""
        return self.strategies.get(strategy_id)
    
    def get_active_strategy(self) -> Optional[StrategyConfig]:
        """獲取當前活躍策略"""
        if self.active_strategy_id:
            return self.strategies.get(self.active_strategy_id)
        return None
    
    def set_active_strategy(self, strategy_id: str) -> bool:
        """設置活躍策略"""
        if strategy_id not in self.strategies:
            logger.error(f"❌ 策略不存在: {strategy_id}")
            return False
        
        # 停用其他策略
        for sid, strategy in self.strategies.items():
            strategy.is_active = (sid == strategy_id)
        
        self.active_strategy_id = strategy_id
        self.save_all_strategies()
        
        strategy_name = self.strategies[strategy_id].strategy_name
        logger.info(f"✅ 設置活躍策略: {strategy_name} ({strategy_id})")
        
        return True
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """刪除策略"""
        if strategy_id not in self.strategies:
            logger.error(f"❌ 策略不存在: {strategy_id}")
            return False
        
        strategy_name = self.strategies[strategy_id].strategy_name
        
        # 如果是活躍策略，需要先停用
        if self.active_strategy_id == strategy_id:
            self.active_strategy_id = None
        
        # 刪除策略文件
        config_file = self.config_dir / f"{strategy_id}.json"
        if config_file.exists():
            config_file.unlink()
        
        del self.strategies[strategy_id]
        
        logger.info(f"🗑️ 刪除策略: {strategy_name} ({strategy_id})")
        return True
    
    def list_strategies(self) -> List[Dict[str, Any]]:
        """列出所有策略"""
        strategy_list = []
        
        for strategy_id, strategy in self.strategies.items():
            strategy_info = {
                'strategy_id': strategy_id,
                'strategy_name': strategy.strategy_name,
                'strategy_type': strategy.strategy_type.value,
                'version': strategy.version,
                'is_active': strategy.is_active,
                'created_at': strategy.created_at.isoformat(),
                'updated_at': strategy.updated_at.isoformat(),
                'description': strategy.description,
                'performance': strategy.performance_metrics
            }
            strategy_list.append(strategy_info)
        
        # 按創建時間排序
        strategy_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        return strategy_list
    
    def clone_strategy(self, source_strategy_id: str, new_name: str) -> Optional[str]:
        """克隆策略"""
        if source_strategy_id not in self.strategies:
            logger.error(f"❌ 源策略不存在: {source_strategy_id}")
            return None
        
        source_strategy = self.strategies[source_strategy_id]
        new_strategy_id = self._generate_strategy_id(new_name)
        
        # 深拷貝源策略
        cloned_strategy = copy.deepcopy(source_strategy)
        cloned_strategy.strategy_id = new_strategy_id
        cloned_strategy.strategy_name = new_name
        cloned_strategy.version = "1.0.0"
        cloned_strategy.created_at = datetime.now()
        cloned_strategy.updated_at = datetime.now()
        cloned_strategy.is_active = False
        cloned_strategy.description = f"克隆自: {source_strategy.strategy_name}"
        
        # 清空回測結果
        cloned_strategy.backtest_results = {}
        cloned_strategy.performance_metrics = {}
        
        self.strategies[new_strategy_id] = cloned_strategy
        self.save_strategy(new_strategy_id)
        
        logger.info(f"📋 克隆策略: {new_name} ({new_strategy_id}) <- {source_strategy.strategy_name}")
        return new_strategy_id
    
    def validate_strategy_config(self, strategy_id: str) -> Dict[str, Any]:
        """驗證策略配置"""
        if strategy_id not in self.strategies:
            return {'valid': False, 'errors': ['策略不存在']}
        
        strategy = self.strategies[strategy_id]
        errors = []
        warnings = []
        
        # 驗證MACD參數
        macd = strategy.macd_config
        if macd.fast_period >= macd.slow_period:
            errors.append("MACD快線週期必須小於慢線週期")
        
        if macd.signal_period <= 0:
            errors.append("MACD信號線週期必須大於0")
        
        if not (0.0 <= macd.min_confidence <= 1.0):
            errors.append("最小信心度必須在0-1之間")
        
        # 驗證風險控制
        risk = strategy.risk_config
        if risk.max_position_size > 1.0:
            errors.append("最大倉位比例不能超過100%")
        
        if risk.stop_loss_pct >= risk.take_profit_pct:
            warnings.append("止損比例建議小於止盈比例")
        
        if risk.max_drawdown_pct > 0.5:
            warnings.append("最大回撤比例過高，建議不超過50%")
        
        # 驗證交易限額
        limits = strategy.trading_limits
        if limits.min_trade_amount >= limits.max_trade_amount:
            errors.append("最小交易金額必須小於最大交易金額")
        
        if limits.daily_loss_limit > limits.weekly_loss_limit:
            warnings.append("每日虧損限額建議小於每週限額")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'validation_time': datetime.now().isoformat()
        }
    
    def export_strategy(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """導出策略配置"""
        if strategy_id not in self.strategies:
            return None
        
        strategy = self.strategies[strategy_id]
        
        # 轉換為可序列化的字典
        export_data = {
            'strategy_id': strategy.strategy_id,
            'strategy_name': strategy.strategy_name,
            'strategy_type': strategy.strategy_type.value,
            'version': strategy.version,
            'created_at': strategy.created_at.isoformat(),
            'updated_at': strategy.updated_at.isoformat(),
            'description': strategy.description,
            'macd_config': asdict(strategy.macd_config),
            'risk_config': asdict(strategy.risk_config),
            'trading_limits': asdict(strategy.trading_limits),
            'custom_params': strategy.custom_params,
            'export_time': datetime.now().isoformat()
        }
        
        return export_data
    
    def import_strategy(self, import_data: Dict[str, Any], new_name: Optional[str] = None) -> Optional[str]:
        """導入策略配置"""
        try:
            strategy_name = new_name or import_data['strategy_name']
            strategy_id = self._generate_strategy_id(strategy_name)
            
            # 創建策略配置
            strategy_config = StrategyConfig(
                strategy_id=strategy_id,
                strategy_name=strategy_name,
                strategy_type=StrategyType(import_data['strategy_type']),
                version="1.0.0",  # 重置版本
                created_at=datetime.now(),
                updated_at=datetime.now(),
                description=import_data.get('description', ''),
                is_active=False
            )
            
            # 導入配置
            if 'macd_config' in import_data:
                strategy_config.macd_config = MACDConfig(**import_data['macd_config'])
            
            if 'risk_config' in import_data:
                strategy_config.risk_config = RiskConfig(**import_data['risk_config'])
            
            if 'trading_limits' in import_data:
                strategy_config.trading_limits = TradingLimits(**import_data['trading_limits'])
            
            if 'custom_params' in import_data:
                strategy_config.custom_params = import_data['custom_params']
            
            self.strategies[strategy_id] = strategy_config
            self.save_strategy(strategy_id)
            
            logger.info(f"📥 導入策略: {strategy_name} ({strategy_id})")
            return strategy_id
            
        except Exception as e:
            logger.error(f"❌ 導入策略失敗: {e}")
            return None
    
    def save_strategy(self, strategy_id: str):
        """保存單個策略到文件"""
        if strategy_id not in self.strategies:
            return
        
        strategy = self.strategies[strategy_id]
        config_file = self.config_dir / f"{strategy_id}.json"
        
        # 轉換為可序列化的格式
        strategy_data = {
            'strategy_id': strategy.strategy_id,
            'strategy_name': strategy.strategy_name,
            'strategy_type': strategy.strategy_type.value,
            'version': strategy.version,
            'created_at': strategy.created_at.isoformat(),
            'updated_at': strategy.updated_at.isoformat(),
            'is_active': strategy.is_active,
            'description': strategy.description,
            'macd_config': asdict(strategy.macd_config),
            'risk_config': asdict(strategy.risk_config),
            'trading_limits': asdict(strategy.trading_limits),
            'backtest_results': strategy.backtest_results,
            'performance_metrics': strategy.performance_metrics,
            'custom_params': strategy.custom_params
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(strategy_data, f, indent=2, ensure_ascii=False)
    
    def save_all_strategies(self):
        """保存所有策略"""
        for strategy_id in self.strategies:
            self.save_strategy(strategy_id)
        
        # 保存活躍策略信息
        meta_file = self.config_dir / "meta.json"
        meta_data = {
            'active_strategy_id': self.active_strategy_id,
            'last_updated': datetime.now().isoformat()
        }
        
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(meta_data, f, indent=2, ensure_ascii=False)
    
    def load_all_strategies(self):
        """載入所有策略"""
        if not self.config_dir.exists():
            return
        
        # 載入策略文件
        for config_file in self.config_dir.glob("*.json"):
            if config_file.name == "meta.json":
                continue
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    strategy_data = json.load(f)
                
                strategy_config = self._load_strategy_from_data(strategy_data)
                if strategy_config:
                    self.strategies[strategy_config.strategy_id] = strategy_config
                    
            except Exception as e:
                logger.error(f"❌ 載入策略配置失敗 {config_file}: {e}")
        
        # 載入元數據
        meta_file = self.config_dir / "meta.json"
        if meta_file.exists():
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                
                self.active_strategy_id = meta_data.get('active_strategy_id')
                
            except Exception as e:
                logger.error(f"❌ 載入元數據失敗: {e}")
        
        logger.info(f"📚 載入了 {len(self.strategies)} 個策略配置")
    
    def _load_strategy_from_data(self, data: Dict[str, Any]) -> Optional[StrategyConfig]:
        """從數據創建策略配置對象"""
        try:
            strategy_config = StrategyConfig(
                strategy_id=data['strategy_id'],
                strategy_name=data['strategy_name'],
                strategy_type=StrategyType(data['strategy_type']),
                version=data['version'],
                created_at=datetime.fromisoformat(data['created_at']),
                updated_at=datetime.fromisoformat(data['updated_at']),
                is_active=data.get('is_active', False),
                description=data.get('description', '')
            )
            
            # 載入配置
            if 'macd_config' in data:
                strategy_config.macd_config = MACDConfig(**data['macd_config'])
            
            if 'risk_config' in data:
                strategy_config.risk_config = RiskConfig(**data['risk_config'])
            
            if 'trading_limits' in data:
                strategy_config.trading_limits = TradingLimits(**data['trading_limits'])
            
            strategy_config.backtest_results = data.get('backtest_results', {})
            strategy_config.performance_metrics = data.get('performance_metrics', {})
            strategy_config.custom_params = data.get('custom_params', {})
            
            return strategy_config
            
        except Exception as e:
            logger.error(f"❌ 解析策略數據失敗: {e}")
            return None
    
    def _generate_strategy_id(self, strategy_name: str) -> str:
        """生成策略ID"""
        import hashlib
        import uuid
        
        # 使用策略名稱和時間戳生成唯一ID
        content = f"{strategy_name}_{datetime.now().isoformat()}_{uuid.uuid4()}"
        strategy_id = hashlib.md5(content.encode()).hexdigest()[:12]
        
        return f"strategy_{strategy_id}"
    
    def _increment_version(self, version: str) -> str:
        """增加版本號"""
        try:
            parts = version.split('.')
            if len(parts) == 3:
                major, minor, patch = map(int, parts)
                patch += 1
                return f"{major}.{minor}.{patch}"
            else:
                return f"{version}.1"
        except:
            return "1.0.1"
    
    def get_strategy_statistics(self) -> Dict[str, Any]:
        """獲取策略統計信息"""
        total_strategies = len(self.strategies)
        active_strategies = len([s for s in self.strategies.values() if s.is_active])
        
        # 按類型統計
        type_stats = {}
        for strategy in self.strategies.values():
            strategy_type = strategy.strategy_type.value
            type_stats[strategy_type] = type_stats.get(strategy_type, 0) + 1
        
        # 按風險等級統計（基於最大倉位大小）
        risk_stats = {'conservative': 0, 'moderate': 0, 'aggressive': 0}
        for strategy in self.strategies.values():
            max_pos = strategy.risk_config.max_position_size
            if max_pos <= 0.05:
                risk_stats['conservative'] += 1
            elif max_pos <= 0.15:
                risk_stats['moderate'] += 1
            else:
                risk_stats['aggressive'] += 1
        
        return {
            'total_strategies': total_strategies,
            'active_strategies': active_strategies,
            'inactive_strategies': total_strategies - active_strategies,
            'strategy_types': type_stats,
            'risk_distribution': risk_stats,
            'active_strategy_id': self.active_strategy_id,
            'last_updated': datetime.now().isoformat()
        }

# 全局策略配置管理器實例
strategy_config_manager = StrategyConfigManager()

# 便捷函數
def get_active_strategy() -> Optional[StrategyConfig]:
    """獲取當前活躍策略"""
    return strategy_config_manager.get_active_strategy()

def create_strategy(name: str, strategy_type: StrategyType, risk_level: RiskLevel = RiskLevel.MODERATE) -> str:
    """創建新策略"""
    return strategy_config_manager.create_strategy(name, strategy_type, risk_level)

def update_strategy_config(strategy_id: str, updates: Dict[str, Any]) -> bool:
    """更新策略配置"""
    return strategy_config_manager.update_strategy(strategy_id, updates)

def set_active_strategy(strategy_id: str) -> bool:
    """設置活躍策略"""
    return strategy_config_manager.set_active_strategy(strategy_id)