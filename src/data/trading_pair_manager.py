#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易對管理器 - 動態配置和管理多個交易對
實現熱更新、配置驗證和自動參數優化
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import asyncio

try:
    from .multi_pair_max_client import TradingPairConfig, MultiPairMAXClient
except ImportError:
    # 用於直接運行測試
    from multi_pair_max_client import TradingPairConfig, MultiPairMAXClient

logger = logging.getLogger(__name__)

@dataclass
class TradingPairTemplate:
    """交易對配置模板"""
    base_currency: str
    quote_currency: str
    default_min_order_size: float
    default_max_position_size: float
    default_risk_weight: float
    market_cap_tier: str  # 'large', 'medium', 'small'
    volatility_tier: str  # 'low', 'medium', 'high'

class TradingPairManager:
    """交易對管理器"""
    
    def __init__(self, config_file: str = "AImax/configs/trading_pairs.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 交易對配置
        self.pair_configs: Dict[str, TradingPairConfig] = {}
        self.pair_templates: Dict[str, TradingPairTemplate] = {}
        
        # 配置歷史和審計
        self.config_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
        
        # 自動優化設置
        self.auto_optimization_enabled = True
        self.optimization_interval = 3600  # 1小時
        self.last_optimization = datetime.now()
        
        # 初始化默認模板
        self._initialize_default_templates()
        
        # 載入配置
        self.load_configuration()
        
        logger.info("⚙️ 交易對管理器初始化完成")
    
    def _initialize_default_templates(self):
        """初始化默認交易對模板"""
        templates = {
            'BTC': TradingPairTemplate(
                base_currency='BTC',
                quote_currency='TWD',
                default_min_order_size=0.0001,
                default_max_position_size=0.01,
                default_risk_weight=0.4,
                market_cap_tier='large',
                volatility_tier='medium'
            ),
            'ETH': TradingPairTemplate(
                base_currency='ETH',
                quote_currency='TWD',
                default_min_order_size=0.001,
                default_max_position_size=0.1,
                default_risk_weight=0.3,
                market_cap_tier='large',
                volatility_tier='medium'
            ),
            'LTC': TradingPairTemplate(
                base_currency='LTC',
                quote_currency='TWD',
                default_min_order_size=0.01,
                default_max_position_size=1.0,
                default_risk_weight=0.2,
                market_cap_tier='medium',
                volatility_tier='medium'
            ),
            'BCH': TradingPairTemplate(
                base_currency='BCH',
                quote_currency='TWD',
                default_min_order_size=0.001,
                default_max_position_size=0.1,
                default_risk_weight=0.1,
                market_cap_tier='medium',
                volatility_tier='high'
            )
        }
        
        self.pair_templates.update(templates)
        logger.info(f"📋 初始化 {len(templates)} 個交易對模板")
    
    def create_pair_from_template(self, base_currency: str, 
                                 custom_params: Optional[Dict[str, Any]] = None) -> TradingPairConfig:
        """從模板創建交易對配置"""
        if base_currency not in self.pair_templates:
            raise ValueError(f"未找到 {base_currency} 的模板")
        
        template = self.pair_templates[base_currency]
        pair_symbol = f"{template.base_currency}{template.quote_currency}"
        
        # 基於模板創建配置
        config = TradingPairConfig(
            pair=pair_symbol,
            min_order_size=template.default_min_order_size,
            max_position_size=template.default_max_position_size,
            risk_weight=template.default_risk_weight,
            enabled=True,
            api_rate_limit=0.1,
            max_retries=3,
            timeout=10,
            precision=0,
            tick_size=1.0,
            min_notional=100.0 if template.market_cap_tier == 'large' else 50.0
        )
        
        # 應用自定義參數
        if custom_params:
            for key, value in custom_params.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        # 根據市場特性調整參數
        config = self._adjust_config_by_market_tier(config, template)
        
        logger.info(f"🔧 從模板創建交易對配置: {pair_symbol}")
        return config
    
    def _adjust_config_by_market_tier(self, config: TradingPairConfig, 
                                    template: TradingPairTemplate) -> TradingPairConfig:
        """根據市場層級調整配置"""
        # 根據波動率調整API限制
        if template.volatility_tier == 'high':
            config.api_rate_limit = 0.05  # 更頻繁的更新
            config.max_retries = 5
        elif template.volatility_tier == 'low':
            config.api_rate_limit = 0.2   # 較少的更新
            config.max_retries = 2
        
        # 根據市值調整風險權重
        if template.market_cap_tier == 'small':
            config.risk_weight *= 0.5  # 小市值降低權重
            config.max_position_size *= 0.5
        elif template.market_cap_tier == 'large':
            config.risk_weight *= 1.2  # 大市值可以增加權重
        
        return config
    
    def add_trading_pair(self, config: TradingPairConfig, 
                        save_immediately: bool = True) -> bool:
        """添加交易對配置"""
        try:
            # 驗證配置
            if not self._validate_config(config):
                return False
            
            # 記錄配置變更
            self._record_config_change('add', config.pair, asdict(config))
            
            # 添加配置
            self.pair_configs[config.pair] = config
            
            if save_immediately:
                self.save_configuration()
            
            logger.info(f"➕ 添加交易對配置: {config.pair}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 添加交易對配置失敗: {e}")
            return False
    
    def update_trading_pair(self, pair: str, updates: Dict[str, Any], 
                          save_immediately: bool = True) -> bool:
        """更新交易對配置"""
        try:
            if pair not in self.pair_configs:
                logger.error(f"❌ 交易對 {pair} 不存在")
                return False
            
            old_config = asdict(self.pair_configs[pair])
            
            # 應用更新
            for key, value in updates.items():
                if hasattr(self.pair_configs[pair], key):
                    setattr(self.pair_configs[pair], key, value)
                else:
                    logger.warning(f"⚠️ 未知配置項: {key}")
            
            # 驗證更新後的配置
            if not self._validate_config(self.pair_configs[pair]):
                # 回滾配置
                self.pair_configs[pair] = TradingPairConfig(**old_config)
                return False
            
            # 記錄配置變更
            self._record_config_change('update', pair, updates, old_config)
            
            if save_immediately:
                self.save_configuration()
            
            logger.info(f"🔄 更新交易對配置: {pair}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新交易對配置失敗: {e}")
            return False
    
    def remove_trading_pair(self, pair: str, save_immediately: bool = True) -> bool:
        """移除交易對配置"""
        try:
            if pair not in self.pair_configs:
                logger.error(f"❌ 交易對 {pair} 不存在")
                return False
            
            old_config = asdict(self.pair_configs[pair])
            
            # 記錄配置變更
            self._record_config_change('remove', pair, None, old_config)
            
            # 移除配置
            del self.pair_configs[pair]
            
            if save_immediately:
                self.save_configuration()
            
            logger.info(f"➖ 移除交易對配置: {pair}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 移除交易對配置失敗: {e}")
            return False
    
    def _validate_config(self, config: TradingPairConfig) -> bool:
        """驗證交易對配置"""
        try:
            # 基本驗證
            if not config.pair or len(config.pair) < 6:
                logger.error("❌ 交易對名稱無效")
                return False
            
            if config.min_order_size <= 0:
                logger.error("❌ 最小訂單大小必須大於0")
                return False
            
            if config.max_position_size <= 0:
                logger.error("❌ 最大倉位大小必須大於0")
                return False
            
            if not 0 < config.risk_weight <= 1:
                logger.error("❌ 風險權重必須在0-1之間")
                return False
            
            if config.api_rate_limit < 0.01:
                logger.error("❌ API限流間隔過短")
                return False
            
            if config.timeout <= 0:
                logger.error("❌ 超時時間必須大於0")
                return False
            
            # 邏輯驗證
            if config.min_order_size >= config.max_position_size:
                logger.error("❌ 最小訂單大小不能大於等於最大倉位大小")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置驗證失敗: {e}")
            return False
    
    def _record_config_change(self, action: str, pair: str, 
                            new_config: Optional[Dict[str, Any]] = None,
                            old_config: Optional[Dict[str, Any]] = None):
        """記錄配置變更"""
        change_record = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'pair': pair,
            'new_config': new_config,
            'old_config': old_config
        }
        
        self.config_history.append(change_record)
        
        # 限制歷史記錄大小
        if len(self.config_history) > self.max_history_size:
            self.config_history = self.config_history[-self.max_history_size:]
    
    def get_config_history(self, pair: Optional[str] = None, 
                          limit: int = 10) -> List[Dict[str, Any]]:
        """獲取配置變更歷史"""
        history = self.config_history
        
        if pair:
            history = [h for h in history if h['pair'] == pair]
        
        return history[-limit:] if limit > 0 else history
    
    def rollback_config(self, pair: str, steps: int = 1) -> bool:
        """回滾配置到之前的版本"""
        try:
            # 查找該交易對的歷史記錄
            pair_history = [h for h in self.config_history if h['pair'] == pair]
            
            if len(pair_history) < steps:
                logger.error(f"❌ 沒有足夠的歷史記錄進行回滾")
                return False
            
            # 獲取目標配置
            target_record = pair_history[-(steps + 1)]
            
            if target_record['action'] == 'remove':
                # 如果目標是移除操作，則移除當前配置
                return self.remove_trading_pair(pair)
            elif target_record['old_config']:
                # 恢復到舊配置
                old_config = target_record['old_config']
                config = TradingPairConfig(**old_config)
                self.pair_configs[pair] = config
                self.save_configuration()
                
                logger.info(f"🔄 回滾交易對配置: {pair} (回滾 {steps} 步)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 配置回滾失敗: {e}")
            return False
    
    def optimize_configurations(self, market_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """基於市場數據自動優化配置"""
        if not self.auto_optimization_enabled:
            return {'status': 'disabled'}
        
        # 檢查優化間隔
        time_since_last = (datetime.now() - self.last_optimization).total_seconds()
        if time_since_last < self.optimization_interval:
            return {'status': 'too_soon', 'next_optimization_in': self.optimization_interval - time_since_last}
        
        optimization_results = {
            'timestamp': datetime.now().isoformat(),
            'optimized_pairs': [],
            'recommendations': []
        }
        
        try:
            for pair, config in self.pair_configs.items():
                if pair in market_data:
                    data = market_data[pair]
                    
                    # 基於波動率調整API限流
                    volatility = data.get('volatility', 0.02)
                    if volatility > 0.05 and config.api_rate_limit > 0.05:
                        # 高波動率，增加更新頻率
                        new_rate_limit = max(0.05, config.api_rate_limit * 0.8)
                        self.update_trading_pair(pair, {'api_rate_limit': new_rate_limit}, False)
                        optimization_results['optimized_pairs'].append(f"{pair}: 降低API限流至 {new_rate_limit}")
                    
                    # 基於交易量調整風險權重
                    volume_ratio = data.get('volume_ratio', 1.0)
                    if volume_ratio > 2.0 and config.risk_weight < 0.8:
                        # 高交易量，可以適當增加權重
                        new_weight = min(0.8, config.risk_weight * 1.1)
                        self.update_trading_pair(pair, {'risk_weight': new_weight}, False)
                        optimization_results['optimized_pairs'].append(f"{pair}: 增加風險權重至 {new_weight:.3f}")
                    
                    # 基於API延遲調整超時設置
                    api_latency = data.get('api_latency', 1.0)
                    if api_latency > 5.0 and config.timeout < 15:
                        # 高延遲，增加超時時間
                        new_timeout = min(15, int(api_latency * 2))
                        self.update_trading_pair(pair, {'timeout': new_timeout}, False)
                        optimization_results['optimized_pairs'].append(f"{pair}: 增加超時至 {new_timeout}秒")
            
            # 保存所有優化
            if optimization_results['optimized_pairs']:
                self.save_configuration()
            
            self.last_optimization = datetime.now()
            
            logger.info(f"🔧 自動優化完成，優化了 {len(optimization_results['optimized_pairs'])} 個配置")
            
        except Exception as e:
            logger.error(f"❌ 自動優化失敗: {e}")
            optimization_results['error'] = str(e)
        
        return optimization_results
    
    def save_configuration(self):
        """保存配置到文件"""
        try:
            config_data = {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0',
                'pairs': {pair: asdict(config) for pair, config in self.pair_configs.items()},
                'templates': {name: asdict(template) for name, template in self.pair_templates.items()},
                'settings': {
                    'auto_optimization_enabled': self.auto_optimization_enabled,
                    'optimization_interval': self.optimization_interval
                }
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 配置已保存: {self.config_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存配置失敗: {e}")
    
    def load_configuration(self):
        """從文件載入配置"""
        try:
            if not self.config_file.exists():
                # 創建默認配置
                self._create_default_configuration()
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 載入交易對配置
            if 'pairs' in config_data:
                for pair, config_dict in config_data['pairs'].items():
                    config = TradingPairConfig(**config_dict)
                    self.pair_configs[pair] = config
            
            # 載入模板
            if 'templates' in config_data:
                for name, template_dict in config_data['templates'].items():
                    template = TradingPairTemplate(**template_dict)
                    self.pair_templates[name] = template
            
            # 載入設置
            if 'settings' in config_data:
                settings = config_data['settings']
                self.auto_optimization_enabled = settings.get('auto_optimization_enabled', True)
                self.optimization_interval = settings.get('optimization_interval', 3600)
            
            logger.info(f"📂 配置已載入: {len(self.pair_configs)} 個交易對")
            
        except Exception as e:
            logger.error(f"❌ 載入配置失敗: {e}")
            self._create_default_configuration()
    
    def _create_default_configuration(self):
        """創建默認配置"""
        logger.info("🔧 創建默認交易對配置...")
        
        # 創建默認交易對
        for base_currency in ['BTC', 'ETH', 'LTC', 'BCH']:
            config = self.create_pair_from_template(base_currency)
            self.pair_configs[config.pair] = config
        
        # 保存默認配置
        self.save_configuration()
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """獲取配置摘要"""
        enabled_pairs = [pair for pair, config in self.pair_configs.items() if config.enabled]
        disabled_pairs = [pair for pair, config in self.pair_configs.items() if not config.enabled]
        
        total_risk_weight = sum(config.risk_weight for config in self.pair_configs.values() if config.enabled)
        
        return {
            'total_pairs': len(self.pair_configs),
            'enabled_pairs': enabled_pairs,
            'disabled_pairs': disabled_pairs,
            'enabled_count': len(enabled_pairs),
            'disabled_count': len(disabled_pairs),
            'total_risk_weight': total_risk_weight,
            'auto_optimization': self.auto_optimization_enabled,
            'last_optimization': self.last_optimization.isoformat(),
            'config_file': str(self.config_file)
        }


# 創建全局交易對管理器實例
def create_trading_pair_manager() -> TradingPairManager:
    """創建交易對管理器實例"""
    return TradingPairManager()


# 測試代碼
if __name__ == "__main__":
    def test_trading_pair_manager():
        """測試交易對管理器"""
        print("🧪 測試交易對管理器...")
        
        manager = create_trading_pair_manager()
        
        # 顯示配置摘要
        summary = manager.get_configuration_summary()
        print(f"📊 配置摘要: {summary}")
        
        # 測試添加自定義交易對
        custom_config = manager.create_pair_from_template('BTC', {
            'risk_weight': 0.5,
            'api_rate_limit': 0.05
        })
        
        print(f"🔧 自定義配置: {custom_config}")
        
        # 測試配置更新
        success = manager.update_trading_pair('BTCTWD', {
            'risk_weight': 0.6,
            'enabled': True
        })
        print(f"🔄 更新結果: {success}")
        
        # 顯示配置歷史
        history = manager.get_config_history(limit=5)
        print(f"📜 配置歷史: {len(history)} 條記錄")
        
        print("✅ 交易對管理器測試完成")
    
    # 運行測試
    test_trading_pair_manager()