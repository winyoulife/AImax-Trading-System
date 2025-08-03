#!/usr/bin/env python3
"""
動態價格追蹤 MACD 交易系統 - 價格極值檢測器
實現智能的價格極值點檢測和反轉信號識別
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict
import logging
from dataclasses import dataclass

from .dynamic_trading_data_structures import PricePoint, SignalType
from .dynamic_trading_config import ExtremeDetectionConfig

logger = logging.getLogger(__name__)

@dataclass
class ReversalSignal:
    """反轉信號數據結構"""
    timestamp: datetime
    price: float
    strength: float  # 反轉強度 (0-1)
    confidence: float  # 信心度 (0-1)
    volume_confirmation: bool  # 成交量確認
    reason: str  # 檢測原因

class ExtremePointDetector:
    """價格極值點檢測器"""
    
    def __init__(self, config: ExtremeDetectionConfig):
        self.config = config
        self.price_history: List[PricePoint] = []
        self.current_extreme: Optional[PricePoint] = None
        self.signal_type: Optional[SignalType] = None
        
    def reset(self, signal_type: SignalType):
        """重置檢測器狀態"""
        self.price_history.clear()
        self.current_extreme = None
        self.signal_type = signal_type
        logger.debug(f"重置極值檢測器，信號類型: {signal_type.value}")
    
    def add_price_point(self, price_point: PricePoint) -> bool:
        """
        添加新的價格點並檢測極值
        
        Args:
            price_point: 新的價格點
            
        Returns:
            是否檢測到新的極值點
        """
        try:
            self.price_history.append(price_point)
            
            # 限制歷史記錄長度
            if len(self.price_history) > self.config.trend_periods * 10:
                self.price_history = self.price_history[-self.config.trend_periods * 5:]
            
            # 檢測是否為新的極值點
            is_new_extreme = self._is_new_extreme(price_point)
            
            if is_new_extreme:
                self.current_extreme = price_point
                price_point.is_extreme = True
                logger.debug(f"檢測到新極值點: {price_point.price:,.0f} at {price_point.timestamp}")
            
            return is_new_extreme
            
        except Exception as e:
            logger.error(f"添加價格點失敗: {e}")
            return False
    
    def _is_new_extreme(self, price_point: PricePoint) -> bool:
        """判斷是否為新的極值點"""
        if not self.signal_type:
            return False
        
        if self.signal_type == SignalType.BUY:
            # 買入信號：尋找更低的價格
            if not self.current_extreme:
                return True
            return price_point.price < self.current_extreme.price
        else:
            # 賣出信號：尋找更高的價格
            if not self.current_extreme:
                return True
            return price_point.price > self.current_extreme.price
    
    def detect_price_reversal(self) -> Optional[ReversalSignal]:
        """
        檢測價格反轉信號
        
        Returns:
            反轉信號或 None
        """
        try:
            if len(self.price_history) < self.config.confirmation_periods + 1:
                return None
            
            if not self.current_extreme:
                return None
            
            # 獲取最近的價格點
            recent_points = self.price_history[-self.config.confirmation_periods:]
            extreme_point = self.current_extreme
            
            # 檢測反轉條件
            reversal_detected = self._check_reversal_conditions(recent_points, extreme_point)
            
            if not reversal_detected:
                return None
            
            # 計算反轉強度
            strength = self._calculate_reversal_strength(recent_points, extreme_point)
            
            # 計算信心度
            confidence = self._calculate_confidence(recent_points, extreme_point)
            
            # 檢查成交量確認
            volume_confirmation = self._check_volume_confirmation(recent_points)
            
            # 生成反轉信號
            reversal_signal = ReversalSignal(
                timestamp=recent_points[-1].timestamp,
                price=recent_points[-1].price,
                strength=strength,
                confidence=confidence,
                volume_confirmation=volume_confirmation,
                reason=self._get_reversal_reason(recent_points, extreme_point)
            )
            
            logger.info(f"檢測到價格反轉: {reversal_signal.reason}, 強度: {strength:.2f}")
            return reversal_signal
            
        except Exception as e:
            logger.error(f"檢測價格反轉失敗: {e}")
            return None
    
    def _check_reversal_conditions(self, recent_points: List[PricePoint], 
                                 extreme_point: PricePoint) -> bool:
        """檢查反轉條件"""
        if self.signal_type == SignalType.BUY:
            # 買入信號：檢查價格是否開始上漲
            return self._check_upward_reversal(recent_points, extreme_point)
        else:
            # 賣出信號：檢查價格是否開始下跌
            return self._check_downward_reversal(recent_points, extreme_point)
    
    def _check_upward_reversal(self, recent_points: List[PricePoint], 
                             extreme_point: PricePoint) -> bool:
        """檢查向上反轉（買入後價格上漲）"""
        # 檢查連續上漲
        consecutive_up = 0
        for i in range(1, len(recent_points)):
            if recent_points[i].price > recent_points[i-1].price:
                consecutive_up += 1
            else:
                consecutive_up = 0
        
        # 檢查反彈幅度
        current_price = recent_points[-1].price
        price_change_pct = ((current_price - extreme_point.price) / extreme_point.price) * 100
        
        return (consecutive_up >= self.config.confirmation_periods - 1 and 
                price_change_pct >= self.config.reversal_threshold)
    
    def _check_downward_reversal(self, recent_points: List[PricePoint], 
                               extreme_point: PricePoint) -> bool:
        """檢查向下反轉（賣出後價格下跌）"""
        # 檢查連續下跌
        consecutive_down = 0
        for i in range(1, len(recent_points)):
            if recent_points[i].price < recent_points[i-1].price:
                consecutive_down += 1
            else:
                consecutive_down = 0
        
        # 檢查回落幅度
        current_price = recent_points[-1].price
        price_change_pct = ((extreme_point.price - current_price) / extreme_point.price) * 100
        
        return (consecutive_down >= self.config.confirmation_periods - 1 and 
                price_change_pct >= self.config.reversal_threshold)
    
    def _calculate_reversal_strength(self, recent_points: List[PricePoint], 
                                   extreme_point: PricePoint) -> float:
        """計算反轉強度"""
        try:
            current_price = recent_points[-1].price
            
            if self.signal_type == SignalType.BUY:
                # 買入：計算從低點的反彈強度
                price_change = current_price - extreme_point.price
                max_possible_change = extreme_point.price * 0.05  # 假設最大反彈5%
            else:
                # 賣出：計算從高點的回落強度
                price_change = extreme_point.price - current_price
                max_possible_change = extreme_point.price * 0.05  # 假設最大回落5%
            
            # 標準化到 0-1 範圍
            strength = min(price_change / max_possible_change, 1.0) if max_possible_change > 0 else 0.0
            return max(0.0, strength)
            
        except Exception as e:
            logger.error(f"計算反轉強度失敗: {e}")
            return 0.0
    
    def _calculate_confidence(self, recent_points: List[PricePoint], 
                            extreme_point: PricePoint) -> float:
        """計算信心度"""
        try:
            confidence_factors = []
            
            # 因子1: 趨勢一致性
            trend_consistency = self._calculate_trend_consistency(recent_points)
            confidence_factors.append(trend_consistency)
            
            # 因子2: 價格變化幅度
            price_change_factor = self._calculate_price_change_factor(recent_points, extreme_point)
            confidence_factors.append(price_change_factor)
            
            # 因子3: 時間因子（較新的數據權重更高）
            time_factor = self._calculate_time_factor(recent_points)
            confidence_factors.append(time_factor)
            
            # 加權平均
            weights = [0.4, 0.4, 0.2]  # 趨勢和價格變化更重要
            confidence = sum(f * w for f, w in zip(confidence_factors, weights))
            
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            logger.error(f"計算信心度失敗: {e}")
            return 0.5
    
    def _calculate_trend_consistency(self, recent_points: List[PricePoint]) -> float:
        """計算趨勢一致性"""
        if len(recent_points) < 2:
            return 0.0
        
        expected_direction = 1 if self.signal_type == SignalType.BUY else -1
        consistent_moves = 0
        total_moves = len(recent_points) - 1
        
        for i in range(1, len(recent_points)):
            price_change = recent_points[i].price - recent_points[i-1].price
            if (price_change > 0 and expected_direction > 0) or (price_change < 0 and expected_direction < 0):
                consistent_moves += 1
        
        return consistent_moves / total_moves if total_moves > 0 else 0.0
    
    def _calculate_price_change_factor(self, recent_points: List[PricePoint], 
                                     extreme_point: PricePoint) -> float:
        """計算價格變化因子"""
        current_price = recent_points[-1].price
        price_change_pct = abs(current_price - extreme_point.price) / extreme_point.price * 100
        
        # 將價格變化百分比映射到 0-1 範圍
        # 假設 2% 的變化為滿分
        return min(price_change_pct / 2.0, 1.0)
    
    def _calculate_time_factor(self, recent_points: List[PricePoint]) -> float:
        """計算時間因子"""
        if len(recent_points) < 2:
            return 1.0
        
        # 較新的數據點權重更高
        total_weight = 0
        weighted_sum = 0
        
        for i, point in enumerate(recent_points):
            weight = (i + 1) / len(recent_points)  # 線性增加權重
            total_weight += weight
            weighted_sum += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 1.0
    
    def _check_volume_confirmation(self, recent_points: List[PricePoint]) -> bool:
        """檢查成交量確認"""
        try:
            if len(recent_points) < 2:
                return False
            
            # 計算平均成交量
            volumes = [point.volume for point in recent_points]
            avg_volume = sum(volumes) / len(volumes)
            
            # 檢查最近的成交量是否高於平均值
            recent_volume = recent_points[-1].volume
            volume_increase = (recent_volume - avg_volume) / avg_volume if avg_volume > 0 else 0
            
            # 成交量增加超過閾值視為確認
            return volume_increase > 0.2  # 20% 增加
            
        except Exception as e:
            logger.error(f"檢查成交量確認失敗: {e}")
            return False
    
    def _get_reversal_reason(self, recent_points: List[PricePoint], 
                           extreme_point: PricePoint) -> str:
        """獲取反轉原因描述"""
        current_price = recent_points[-1].price
        
        if self.signal_type == SignalType.BUY:
            change_pct = ((current_price - extreme_point.price) / extreme_point.price) * 100
            return f"價格從低點 {extreme_point.price:,.0f} 反彈 {change_pct:.2f}%"
        else:
            change_pct = ((extreme_point.price - current_price) / extreme_point.price) * 100
            return f"價格從高點 {extreme_point.price:,.0f} 回落 {change_pct:.2f}%"
    
    def get_current_extreme(self) -> Optional[PricePoint]:
        """獲取當前極值點"""
        return self.current_extreme
    
    def is_valid_extreme(self, price_point: PricePoint) -> bool:
        """驗證極值點有效性"""
        try:
            # 基本驗證
            if price_point.price <= 0 or price_point.volume < 0:
                return False
            
            # 噪音過濾
            if self.current_extreme:
                price_change_pct = abs(price_point.price - self.current_extreme.price) / self.current_extreme.price * 100
                if price_change_pct < self.config.noise_filter:
                    return False
            
            # 成交量驗證（可選）
            if self.config.volume_weight > 0:
                if len(self.price_history) >= 2:
                    avg_volume = sum(p.volume for p in self.price_history[-2:]) / 2
                    if price_point.volume < avg_volume * 0.5:  # 成交量過低
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"驗證極值點失敗: {e}")
            return False
    
    def get_detection_summary(self) -> Dict:
        """獲取檢測摘要"""
        return {
            'signal_type': self.signal_type.value if self.signal_type else None,
            'price_history_count': len(self.price_history),
            'current_extreme': {
                'price': self.current_extreme.price if self.current_extreme else None,
                'timestamp': self.current_extreme.timestamp if self.current_extreme else None,
                'is_extreme': self.current_extreme.is_extreme if self.current_extreme else False
            } if self.current_extreme else None,
            'config': {
                'reversal_threshold': self.config.reversal_threshold,
                'confirmation_periods': self.config.confirmation_periods,
                'sensitivity': self.config.sensitivity
            }
        }

# 工具函數
def create_extreme_detector(config: Optional[ExtremeDetectionConfig] = None) -> ExtremePointDetector:
    """創建極值檢測器"""
    if config is None:
        config = ExtremeDetectionConfig()
    return ExtremePointDetector(config)

def detect_extremes_in_series(prices: List[float], volumes: List[float], 
                            timestamps: List[datetime], 
                            signal_type: SignalType,
                            config: Optional[ExtremeDetectionConfig] = None) -> List[PricePoint]:
    """在價格序列中檢測極值點"""
    detector = create_extreme_detector(config)
    detector.reset(signal_type)
    
    extreme_points = []
    
    for price, volume, timestamp in zip(prices, volumes, timestamps):
        point = PricePoint(
            timestamp=timestamp,
            price=price,
            volume=volume
        )
        
        if detector.add_price_point(point) and point.is_extreme:
            extreme_points.append(point)
    
    return extreme_points