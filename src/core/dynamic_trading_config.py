#!/usr/bin/env python3
"""
動態價格追蹤 MACD 交易系統 - 配置管理
管理系統的所有配置參數和設置
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json
import os
from datetime import timedelta

@dataclass
class TrackingWindowConfig:
    """追蹤窗口配置"""
    buy_window_hours: float = 4.0          # 買入追蹤窗口時間（小時）
    sell_window_hours: float = 4.0         # 賣出追蹤窗口時間（小時）
    min_window_minutes: float = 30.0       # 最小窗口時間（分鐘）
    max_window_hours: float = 12.0         # 最大窗口時間（小時）
    max_concurrent_windows: int = 20       # 最大並發窗口數
    
    def get_buy_window_duration(self) -> timedelta:
        """獲取買入窗口持續時間"""
        return timedelta(hours=self.buy_window_hours)
    
    def get_sell_window_duration(self) -> timedelta:
        """獲取賣出窗口持續時間"""
        return timedelta(hours=self.sell_window_hours)
    
    def validate(self) -> bool:
        """驗證配置有效性"""
        return (
            self.min_window_minutes <= self.buy_window_hours * 60 <= self.max_window_hours * 60 and
            self.min_window_minutes <= self.sell_window_hours * 60 <= self.max_window_hours * 60
        )

@dataclass
class ExtremeDetectionConfig:
    """極值檢測配置"""
    reversal_threshold: float = 0.5        # 反轉檢測閾值（%）
    min_improvement: float = 0.1           # 最小改善幅度（%）
    confirmation_periods: int = 2          # 反轉確認週期數
    sensitivity: float = 0.5               # 檢測敏感度（0-1）
    volume_weight: float = 0.3             # 成交量權重（0-1）
    trend_periods: int = 3                 # 趨勢分析週期
    noise_filter: float = 0.1              # 噪音過濾閾值（%）
    
    def validate(self) -> bool:
        """驗證配置有效性"""
        return (
            0.1 <= self.reversal_threshold <= 5.0 and
            0.0 <= self.min_improvement <= 2.0 and
            1 <= self.confirmation_periods <= 5 and
            0.1 <= self.sensitivity <= 1.0 and
            0.0 <= self.volume_weight <= 1.0 and
            1 <= self.trend_periods <= 10 and
            0.0 <= self.noise_filter <= 1.0
        )

@dataclass
class RiskControlConfig:
    """風險控制配置"""
    risk_threshold: float = 2.0            # 風險控制閾值（%）
    max_loss_threshold: float = 1.0        # 最大損失閾值（%）
    volatility_threshold: float = 5.0      # 波動率閾值（%）
    emergency_stop: bool = True            # 緊急停止開關
    max_concurrent_windows: int = 5        # 最大並發窗口數
    
    def validate(self) -> bool:
        """驗證配置有效性"""
        return (
            0.5 <= self.risk_threshold <= 10.0 and
            0.1 <= self.max_loss_threshold <= 5.0 and
            1.0 <= self.volatility_threshold <= 20.0 and
            1 <= self.max_concurrent_windows <= 20
        )

@dataclass
class PerformanceConfig:
    """性能配置"""
    update_interval_seconds: float = 60.0  # 更新間隔（秒）
    data_retention_hours: int = 168        # 數據保留時間（小時，7天）
    max_price_history: int = 1000          # 最大價格歷史記錄數
    enable_caching: bool = True            # 啟用緩存
    cache_size: int = 1000                 # 緩存大小
    parallel_processing: bool = True       # 並行處理
    
    def validate(self) -> bool:
        """驗證配置有效性"""
        return (
            10.0 <= self.update_interval_seconds <= 300.0 and
            24 <= self.data_retention_hours <= 720 and
            100 <= self.max_price_history <= 10000 and
            100 <= self.cache_size <= 10000
        )

@dataclass
class UIConfig:
    """用戶界面配置"""
    auto_refresh: bool = True              # 自動刷新
    refresh_interval_seconds: int = 30     # 刷新間隔（秒）
    show_tracking_details: bool = True     # 顯示追蹤詳情
    highlight_improvements: bool = True    # 高亮改善項目
    chart_update_realtime: bool = False    # 實時圖表更新
    max_display_records: int = 500         # 最大顯示記錄數
    
    def validate(self) -> bool:
        """驗證配置有效性"""
        return (
            5 <= self.refresh_interval_seconds <= 300 and
            100 <= self.max_display_records <= 2000
        )

@dataclass
class DynamicTradingConfig:
    """動態交易系統主配置"""
    # 子配置
    window_config: TrackingWindowConfig = field(default_factory=TrackingWindowConfig)
    detection_config: ExtremeDetectionConfig = field(default_factory=ExtremeDetectionConfig)
    risk_config: RiskControlConfig = field(default_factory=RiskControlConfig)
    performance_config: PerformanceConfig = field(default_factory=PerformanceConfig)
    ui_config: UIConfig = field(default_factory=UIConfig)
    
    # 系統設置
    enable_dynamic_tracking: bool = True   # 啟用動態追蹤
    debug_mode: bool = False               # 調試模式
    log_level: str = "INFO"                # 日誌級別
    config_version: str = "1.0"            # 配置版本
    
    def validate_all(self) -> Dict[str, bool]:
        """驗證所有配置"""
        return {
            'window_config': self.window_config.validate(),
            'detection_config': self.detection_config.validate(),
            'risk_config': self.risk_config.validate(),
            'performance_config': self.performance_config.validate(),
            'ui_config': self.ui_config.validate()
        }
    
    def is_valid(self) -> bool:
        """檢查整體配置是否有效"""
        validation_results = self.validate_all()
        return all(validation_results.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'window_config': {
                'buy_window_hours': self.window_config.buy_window_hours,
                'sell_window_hours': self.window_config.sell_window_hours,
                'min_window_minutes': self.window_config.min_window_minutes,
                'max_window_hours': self.window_config.max_window_hours
            },
            'detection_config': {
                'reversal_threshold': self.detection_config.reversal_threshold,
                'min_improvement': self.detection_config.min_improvement,
                'confirmation_periods': self.detection_config.confirmation_periods,
                'sensitivity': self.detection_config.sensitivity,
                'volume_weight': self.detection_config.volume_weight,
                'trend_periods': self.detection_config.trend_periods,
                'noise_filter': self.detection_config.noise_filter
            },
            'risk_config': {
                'risk_threshold': self.risk_config.risk_threshold,
                'max_loss_threshold': self.risk_config.max_loss_threshold,
                'volatility_threshold': self.risk_config.volatility_threshold,
                'emergency_stop': self.risk_config.emergency_stop,
                'max_concurrent_windows': self.risk_config.max_concurrent_windows
            },
            'performance_config': {
                'update_interval_seconds': self.performance_config.update_interval_seconds,
                'data_retention_hours': self.performance_config.data_retention_hours,
                'max_price_history': self.performance_config.max_price_history,
                'enable_caching': self.performance_config.enable_caching,
                'cache_size': self.performance_config.cache_size,
                'parallel_processing': self.performance_config.parallel_processing
            },
            'ui_config': {
                'auto_refresh': self.ui_config.auto_refresh,
                'refresh_interval_seconds': self.ui_config.refresh_interval_seconds,
                'show_tracking_details': self.ui_config.show_tracking_details,
                'highlight_improvements': self.ui_config.highlight_improvements,
                'chart_update_realtime': self.ui_config.chart_update_realtime,
                'max_display_records': self.ui_config.max_display_records
            },
            'system': {
                'enable_dynamic_tracking': self.enable_dynamic_tracking,
                'debug_mode': self.debug_mode,
                'log_level': self.log_level,
                'config_version': self.config_version
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DynamicTradingConfig':
        """從字典創建配置"""
        config = cls()
        
        # 更新窗口配置
        if 'window_config' in data:
            wc = data['window_config']
            config.window_config = TrackingWindowConfig(
                buy_window_hours=wc.get('buy_window_hours', 4.0),
                sell_window_hours=wc.get('sell_window_hours', 4.0),
                min_window_minutes=wc.get('min_window_minutes', 30.0),
                max_window_hours=wc.get('max_window_hours', 12.0)
            )
        
        # 更新檢測配置
        if 'detection_config' in data:
            dc = data['detection_config']
            config.detection_config = ExtremeDetectionConfig(
                reversal_threshold=dc.get('reversal_threshold', 0.5),
                min_improvement=dc.get('min_improvement', 0.1),
                confirmation_periods=dc.get('confirmation_periods', 2),
                sensitivity=dc.get('sensitivity', 0.5),
                volume_weight=dc.get('volume_weight', 0.3),
                trend_periods=dc.get('trend_periods', 3),
                noise_filter=dc.get('noise_filter', 0.1)
            )
        
        # 更新風險配置
        if 'risk_config' in data:
            rc = data['risk_config']
            config.risk_config = RiskControlConfig(
                risk_threshold=rc.get('risk_threshold', 2.0),
                max_loss_threshold=rc.get('max_loss_threshold', 1.0),
                volatility_threshold=rc.get('volatility_threshold', 5.0),
                emergency_stop=rc.get('emergency_stop', True),
                max_concurrent_windows=rc.get('max_concurrent_windows', 5)
            )
        
        # 更新性能配置
        if 'performance_config' in data:
            pc = data['performance_config']
            config.performance_config = PerformanceConfig(
                update_interval_seconds=pc.get('update_interval_seconds', 60.0),
                data_retention_hours=pc.get('data_retention_hours', 168),
                max_price_history=pc.get('max_price_history', 1000),
                enable_caching=pc.get('enable_caching', True),
                cache_size=pc.get('cache_size', 1000),
                parallel_processing=pc.get('parallel_processing', True)
            )
        
        # 更新 UI 配置
        if 'ui_config' in data:
            uc = data['ui_config']
            config.ui_config = UIConfig(
                auto_refresh=uc.get('auto_refresh', True),
                refresh_interval_seconds=uc.get('refresh_interval_seconds', 30),
                show_tracking_details=uc.get('show_tracking_details', True),
                highlight_improvements=uc.get('highlight_improvements', True),
                chart_update_realtime=uc.get('chart_update_realtime', False),
                max_display_records=uc.get('max_display_records', 500)
            )
        
        # 更新系統設置
        if 'system' in data:
            sc = data['system']
            config.enable_dynamic_tracking = sc.get('enable_dynamic_tracking', True)
            config.debug_mode = sc.get('debug_mode', False)
            config.log_level = sc.get('log_level', "INFO")
            config.config_version = sc.get('config_version', "1.0")
        
        return config

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = "AImax/config/dynamic_trading_config.json"):
        self.config_file = config_file
        self.config = DynamicTradingConfig()
        self._ensure_config_dir()
    
    def _ensure_config_dir(self):
        """確保配置目錄存在"""
        config_dir = os.path.dirname(self.config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
    
    def load_config(self) -> DynamicTradingConfig:
        """載入配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.config = DynamicTradingConfig.from_dict(data)
                
                # 驗證配置
                if not self.config.is_valid():
                    print("⚠️ 配置驗證失敗，使用默認配置")
                    self.config = DynamicTradingConfig()
            else:
                print("📝 配置文件不存在，創建默認配置")
                self.save_config()
                
        except Exception as e:
            print(f"❌ 載入配置失敗: {e}")
            print("🔄 使用默認配置")
            self.config = DynamicTradingConfig()
        
        return self.config
    
    def save_config(self) -> bool:
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ 保存配置失敗: {e}")
            return False
    
    def update_config(self, **kwargs) -> bool:
        """更新配置"""
        try:
            # 更新窗口配置
            if 'buy_window_hours' in kwargs:
                self.config.window_config.buy_window_hours = kwargs['buy_window_hours']
            if 'sell_window_hours' in kwargs:
                self.config.window_config.sell_window_hours = kwargs['sell_window_hours']
            
            # 更新檢測配置
            if 'reversal_threshold' in kwargs:
                self.config.detection_config.reversal_threshold = kwargs['reversal_threshold']
            if 'sensitivity' in kwargs:
                self.config.detection_config.sensitivity = kwargs['sensitivity']
            
            # 更新風險配置
            if 'risk_threshold' in kwargs:
                self.config.risk_config.risk_threshold = kwargs['risk_threshold']
            
            # 驗證更新後的配置
            if not self.config.is_valid():
                print("⚠️ 更新後的配置無效")
                return False
            
            return self.save_config()
            
        except Exception as e:
            print(f"❌ 更新配置失敗: {e}")
            return False
    
    def get_config(self) -> DynamicTradingConfig:
        """獲取當前配置"""
        return self.config
    
    def reset_to_default(self) -> bool:
        """重置為默認配置"""
        self.config = DynamicTradingConfig()
        return self.save_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """獲取配置摘要"""
        return {
            'window_settings': {
                'buy_window_hours': self.config.window_config.buy_window_hours,
                'sell_window_hours': self.config.window_config.sell_window_hours
            },
            'detection_settings': {
                'reversal_threshold': self.config.detection_config.reversal_threshold,
                'sensitivity': self.config.detection_config.sensitivity
            },
            'risk_settings': {
                'risk_threshold': self.config.risk_config.risk_threshold,
                'emergency_stop': self.config.risk_config.emergency_stop
            },
            'system_settings': {
                'dynamic_tracking_enabled': self.config.enable_dynamic_tracking,
                'debug_mode': self.config.debug_mode
            }
        }

# 全局配置管理器實例
config_manager = ConfigManager()

# 便捷函數
def get_config() -> DynamicTradingConfig:
    """獲取全局配置"""
    return config_manager.get_config()

def load_config() -> DynamicTradingConfig:
    """載入全局配置"""
    return config_manager.load_config()

def save_config() -> bool:
    """保存全局配置"""
    return config_manager.save_config()

def update_config(**kwargs) -> bool:
    """更新全局配置"""
    return config_manager.update_config(**kwargs)