#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
動態倉位管理系統 - 基於AI信心度和市場條件的智能倉位調整
整合全局風險管理，實現多交易對的統一倉位控制
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import math
import numpy as np

logger = logging.getLogger(__name__)

class PositionAdjustmentReason(Enum):
    """倉位調整原因"""
    AI_CONFIDENCE_CHANGE = "ai_confidence_change"
    MARKET_VOLATILITY = "market_volatility"
    RISK_LIMIT_BREACH = "risk_limit_breach"
    CORRELATION_RISK = "correlation_risk"
    PROFIT_TAKING = "profit_taking"
    LOSS_CUTTING = "loss_cutting"
    EMERGENCY_REDUCTION = "emergency_reduction"

class PositionSizeMode(Enum):
    """倉位大小模式"""
    CONSERVATIVE = "conservative"  # 保守模式
    BALANCED = "balanced"         # 平衡模式
    AGGRESSIVE = "aggressive"     # 激進模式
    ADAPTIVE = "adaptive"         # 自適應模式

@dataclass
class DynamicPositionConfig:
    """動態倉位配置"""
    # 基礎配置
    base_position_size: float = 0.02        # 基礎倉位大小 (2%)
    max_position_size: float = 0.05         # 最大單倉位 (5%)
    max_total_exposure: float = 0.15        # 最大總敞口 (15%)
    
    # AI信心度調整參數
    min_confidence_threshold: float = 0.6   # 最低信心度閾值
    confidence_multiplier: float = 1.5      # 信心度乘數
    high_confidence_threshold: float = 0.8  # 高信心度閾值
    
    # 市場條件調整參數
    volatility_adjustments: Dict[str, float] = field(default_factory=lambda: {
        'low': 1.2,      # 低波動率時增加倉位
        'medium': 1.0,   # 中等波動率保持不變
        'high': 0.7,     # 高波動率時減少倉位
        'extreme': 0.4   # 極端波動率時大幅減少
    })
    
    # 風險調整參數
    risk_score_adjustments: Dict[str, float] = field(default_factory=lambda: {
        'very_low': 1.3,   # 極低風險
        'low': 1.1,        # 低風險
        'medium': 1.0,     # 中等風險
        'high': 0.8,       # 高風險
        'very_high': 0.5   # 極高風險
    })
    
    # 相關性調整參數
    correlation_threshold: float = 0.7      # 相關性閾值
    correlation_penalty: float = 0.8        # 相關性懲罰係數
    
    # 時間調整參數
    position_decay_hours: float = 24.0      # 倉位衰減時間
    decay_factor: float = 0.95              # 衰減係數

@dataclass
class PositionMetrics:
    """倉位指標"""
    pair: str
    current_size: float
    target_size: float
    ai_confidence: float
    risk_score: float
    market_volatility: str
    correlation_risk: float
    holding_duration: timedelta
    unrealized_pnl: float
    unrealized_return: float
    last_adjustment: datetime
    adjustment_count: int = 0

class DynamicPositionManager:
    """動態倉位管理系統"""
    
    def __init__(self, config: DynamicPositionConfig = None):
        self.config = config or DynamicPositionConfig()
        
        # 倉位追蹤
        self.active_positions: Dict[str, PositionMetrics] = {}
        self.position_history: List[Dict[str, Any]] = []
        
        # 市場數據緩存
        self.market_data_cache: Dict[str, Dict[str, Any]] = {}
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        
        # 調整統計
        self.adjustment_stats = {
            'total_adjustments': 0,
            'size_increases': 0,
            'size_decreases': 0,
            'emergency_reductions': 0,
            'avg_adjustment_size': 0.0,
            'successful_adjustments': 0,
            'failed_adjustments': 0
        }
        
        # 風險控制狀態
        self.risk_alerts: List[Dict[str, Any]] = []
        self.emergency_mode: bool = False
        
        logger.info("💰 動態倉位管理系統初始化完成")
        logger.info(f"   基礎倉位大小: {self.config.base_position_size:.1%}")
        logger.info(f"   最大單倉位: {self.config.max_position_size:.1%}")
        logger.info(f"   最大總敞口: {self.config.max_total_exposure:.1%}")
    
    async def calculate_optimal_position_size(self, pair: str, ai_analysis: Dict[str, Any], 
                                            market_data: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """計算最優倉位大小"""
        try:
            # 提取關鍵指標
            ai_confidence = ai_analysis.get('confidence', 0.5)
            risk_score = ai_analysis.get('risk_score', 0.5)
            market_volatility = market_data.get('volatility_level', 'medium')
            
            # 基礎倉位大小
            base_size = self.config.base_position_size
            
            # AI信心度調整
            confidence_adjustment = await self._calculate_confidence_adjustment(ai_confidence)
            
            # 市場波動率調整
            volatility_adjustment = self._calculate_volatility_adjustment(market_volatility)
            
            # 風險分數調整
            risk_adjustment = self._calculate_risk_adjustment(risk_score)
            
            # 相關性風險調整
            correlation_adjustment = await self._calculate_correlation_adjustment(pair)
            
            # 當前倉位數量調整
            position_count_adjustment = self._calculate_position_count_adjustment()
            
            # 時間衰減調整
            time_adjustment = await self._calculate_time_adjustment(pair)
            
            # 綜合計算目標倉位
            target_size = (base_size * 
                          confidence_adjustment * 
                          volatility_adjustment * 
                          risk_adjustment * 
                          correlation_adjustment * 
                          position_count_adjustment * 
                          time_adjustment)
            
            # 應用限制
            target_size = min(target_size, self.config.max_position_size)
            target_size = max(target_size, 0.0)
            
            # 檢查總敞口限制
            current_total_exposure = sum(pos.current_size for pos in self.active_positions.values())
            available_exposure = self.config.max_total_exposure - current_total_exposure
            target_size = min(target_size, available_exposure)
            
            # 計算調整詳情
            adjustment_details = {
                'base_size': base_size,
                'confidence_adjustment': confidence_adjustment,
                'volatility_adjustment': volatility_adjustment,
                'risk_adjustment': risk_adjustment,
                'correlation_adjustment': correlation_adjustment,
                'position_count_adjustment': position_count_adjustment,
                'time_adjustment': time_adjustment,
                'final_target_size': target_size,
                'ai_confidence': ai_confidence,
                'risk_score': risk_score,
                'market_volatility': market_volatility
            }
            
            logger.debug(f"📊 {pair} 倉位計算: {target_size:.3%} (信心度: {ai_confidence:.1%})")
            
            return target_size, adjustment_details
            
        except Exception as e:
            logger.error(f"❌ 計算最優倉位大小失敗: {e}")
            return self.config.base_position_size, {}
    
    async def _calculate_confidence_adjustment(self, confidence: float) -> float:
        """計算信心度調整係數"""
        try:
            if confidence < self.config.min_confidence_threshold:
                # 信心度過低，大幅減少倉位
                return 0.3
            elif confidence > self.config.high_confidence_threshold:
                # 高信心度，增加倉位
                return min(self.config.confidence_multiplier, 2.0)
            else:
                # 線性調整
                normalized_confidence = (confidence - self.config.min_confidence_threshold) / \
                                      (self.config.high_confidence_threshold - self.config.min_confidence_threshold)
                return 0.5 + normalized_confidence * 0.8
                
        except Exception as e:
            logger.error(f"❌ 計算信心度調整失敗: {e}")
            return 1.0
    
    def _calculate_volatility_adjustment(self, volatility_level: str) -> float:
        """計算波動率調整係數"""
        try:
            return self.config.volatility_adjustments.get(volatility_level, 1.0)
        except Exception as e:
            logger.error(f"❌ 計算波動率調整失敗: {e}")
            return 1.0
    
    def _calculate_risk_adjustment(self, risk_score: float) -> float:
        """計算風險調整係數"""
        try:
            if risk_score <= 0.2:
                risk_level = 'very_low'
            elif risk_score <= 0.4:
                risk_level = 'low'
            elif risk_score <= 0.6:
                risk_level = 'medium'
            elif risk_score <= 0.8:
                risk_level = 'high'
            else:
                risk_level = 'very_high'
            
            return self.config.risk_score_adjustments.get(risk_level, 1.0)
            
        except Exception as e:
            logger.error(f"❌ 計算風險調整失敗: {e}")
            return 1.0
    
    async def _calculate_correlation_adjustment(self, pair: str) -> float:
        """計算相關性調整係數"""
        try:
            if not self.active_positions or pair not in self.correlation_matrix:
                return 1.0
            
            # 計算與現有倉位的平均相關性
            correlations = []
            for existing_pair in self.active_positions.keys():
                if existing_pair != pair and existing_pair in self.correlation_matrix.get(pair, {}):
                    correlation = abs(self.correlation_matrix[pair][existing_pair])
                    correlations.append(correlation)
            
            if not correlations:
                return 1.0
            
            avg_correlation = sum(correlations) / len(correlations)
            
            # 如果平均相關性過高，減少倉位
            if avg_correlation > self.config.correlation_threshold:
                penalty = (avg_correlation - self.config.correlation_threshold) / \
                         (1.0 - self.config.correlation_threshold)
                return 1.0 - penalty * (1.0 - self.config.correlation_penalty)
            
            return 1.0
            
        except Exception as e:
            logger.error(f"❌ 計算相關性調整失敗: {e}")
            return 1.0
    
    def _calculate_position_count_adjustment(self) -> float:
        """計算倉位數量調整係數"""
        try:
            position_count = len(self.active_positions)
            
            # 倉位數量越多，新倉位越小
            if position_count == 0:
                return 1.0
            elif position_count <= 2:
                return 0.9
            elif position_count <= 4:
                return 0.8
            else:
                return 0.7
                
        except Exception as e:
            logger.error(f"❌ 計算倉位數量調整失敗: {e}")
            return 1.0
    
    async def _calculate_time_adjustment(self, pair: str) -> float:
        """計算時間衰減調整係數"""
        try:
            if pair not in self.active_positions:
                return 1.0
            
            position = self.active_positions[pair]
            hours_held = position.holding_duration.total_seconds() / 3600
            
            # 持倉時間越長，倉位逐漸衰減
            if hours_held > self.config.position_decay_hours:
                decay_periods = hours_held / self.config.position_decay_hours
                return self.config.decay_factor ** decay_periods
            
            return 1.0
            
        except Exception as e:
            logger.error(f"❌ 計算時間調整失敗: {e}")
            return 1.0
    
    async def adjust_position(self, pair: str, ai_analysis: Dict[str, Any], 
                            market_data: Dict[str, Any]) -> Dict[str, Any]:
        """調整倉位"""
        try:
            # 計算目標倉位大小
            target_size, calculation_details = await self.calculate_optimal_position_size(
                pair, ai_analysis, market_data
            )
            
            # 獲取當前倉位
            current_position = self.active_positions.get(pair)
            current_size = current_position.current_size if current_position else 0.0
            
            # 計算調整幅度
            size_change = target_size - current_size
            adjustment_ratio = abs(size_change) / max(current_size, 0.001)
            
            # 判斷是否需要調整
            min_adjustment_threshold = 0.001  # 0.1%
            if abs(size_change) < min_adjustment_threshold:
                return {
                    'action': 'no_adjustment',
                    'pair': pair,
                    'current_size': current_size,
                    'target_size': target_size,
                    'reason': 'adjustment_too_small'
                }
            
            # 確定調整原因
            adjustment_reason = self._determine_adjustment_reason(
                ai_analysis, market_data, current_size, target_size
            )
            
            # 執行倉位調整
            adjustment_result = await self._execute_position_adjustment(
                pair, current_size, target_size, adjustment_reason, calculation_details
            )
            
            # 更新倉位記錄
            await self._update_position_metrics(pair, target_size, ai_analysis, market_data)
            
            # 記錄調整統計
            self._update_adjustment_stats(size_change, adjustment_result['success'])
            
            logger.info(f"💰 {pair} 倉位調整: {current_size:.3%} → {target_size:.3%} ({adjustment_reason.value})")
            
            return adjustment_result
            
        except Exception as e:
            logger.error(f"❌ 調整倉位失敗: {e}")
            return {
                'action': 'adjustment_failed',
                'pair': pair,
                'error': str(e),
                'success': False
            }
    
    def _determine_adjustment_reason(self, ai_analysis: Dict[str, Any], 
                                   market_data: Dict[str, Any], 
                                   current_size: float, target_size: float) -> PositionAdjustmentReason:
        """確定調整原因"""
        try:
            ai_confidence = ai_analysis.get('confidence', 0.5)
            risk_score = ai_analysis.get('risk_score', 0.5)
            market_volatility = market_data.get('volatility_level', 'medium')
            
            # 緊急減倉
            if self.emergency_mode or risk_score > 0.9:
                return PositionAdjustmentReason.EMERGENCY_REDUCTION
            
            # AI信心度變化
            if target_size > current_size and ai_confidence > 0.8:
                return PositionAdjustmentReason.AI_CONFIDENCE_CHANGE
            elif target_size < current_size and ai_confidence < 0.4:
                return PositionAdjustmentReason.AI_CONFIDENCE_CHANGE
            
            # 市場波動率
            if market_volatility in ['high', 'extreme'] and target_size < current_size:
                return PositionAdjustmentReason.MARKET_VOLATILITY
            
            # 風險限制
            if risk_score > 0.7 and target_size < current_size:
                return PositionAdjustmentReason.RISK_LIMIT_BREACH
            
            # 默認原因
            return PositionAdjustmentReason.AI_CONFIDENCE_CHANGE
            
        except Exception as e:
            logger.error(f"❌ 確定調整原因失敗: {e}")
            return PositionAdjustmentReason.AI_CONFIDENCE_CHANGE
    
    async def _execute_position_adjustment(self, pair: str, current_size: float, 
                                         target_size: float, reason: PositionAdjustmentReason,
                                         calculation_details: Dict[str, Any]) -> Dict[str, Any]:
        """執行倉位調整"""
        try:
            size_change = target_size - current_size
            
            # 模擬執行調整（實際實現中會調用交易執行器）
            success = True  # 假設調整成功
            
            adjustment_result = {
                'action': 'position_adjusted',
                'pair': pair,
                'previous_size': current_size,
                'new_size': target_size,
                'size_change': size_change,
                'adjustment_ratio': abs(size_change) / max(current_size, 0.001),
                'reason': reason.value,
                'calculation_details': calculation_details,
                'timestamp': datetime.now(),
                'success': success
            }
            
            # 記錄調整歷史
            self.position_history.append(adjustment_result.copy())
            
            return adjustment_result
            
        except Exception as e:
            logger.error(f"❌ 執行倉位調整失敗: {e}")
            return {
                'action': 'adjustment_failed',
                'pair': pair,
                'error': str(e),
                'success': False
            }
    
    async def _update_position_metrics(self, pair: str, new_size: float, 
                                     ai_analysis: Dict[str, Any], 
                                     market_data: Dict[str, Any]):
        """更新倉位指標"""
        try:
            current_time = datetime.now()
            
            if pair in self.active_positions:
                # 更新現有倉位
                position = self.active_positions[pair]
                position.current_size = new_size
                position.target_size = new_size
                position.ai_confidence = ai_analysis.get('confidence', 0.5)
                position.risk_score = ai_analysis.get('risk_score', 0.5)
                position.market_volatility = market_data.get('volatility_level', 'medium')
                position.last_adjustment = current_time
                position.adjustment_count += 1
                
                # 更新持倉時間
                if hasattr(position, 'entry_time'):
                    position.holding_duration = current_time - position.entry_time
                else:
                    position.holding_duration = timedelta(0)
            else:
                # 創建新倉位記錄
                position = PositionMetrics(
                    pair=pair,
                    current_size=new_size,
                    target_size=new_size,
                    ai_confidence=ai_analysis.get('confidence', 0.5),
                    risk_score=ai_analysis.get('risk_score', 0.5),
                    market_volatility=market_data.get('volatility_level', 'medium'),
                    correlation_risk=0.0,
                    holding_duration=timedelta(0),
                    unrealized_pnl=0.0,
                    unrealized_return=0.0,
                    last_adjustment=current_time,
                    adjustment_count=1
                )
                self.active_positions[pair] = position
            
        except Exception as e:
            logger.error(f"❌ 更新倉位指標失敗: {e}")
    
    def _update_adjustment_stats(self, size_change: float, success: bool):
        """更新調整統計"""
        try:
            self.adjustment_stats['total_adjustments'] += 1
            
            if success:
                self.adjustment_stats['successful_adjustments'] += 1
                
                if size_change > 0:
                    self.adjustment_stats['size_increases'] += 1
                else:
                    self.adjustment_stats['size_decreases'] += 1
                
                # 更新平均調整幅度
                total_successful = self.adjustment_stats['successful_adjustments']
                current_avg = self.adjustment_stats['avg_adjustment_size']
                self.adjustment_stats['avg_adjustment_size'] = (
                    (current_avg * (total_successful - 1) + abs(size_change)) / total_successful
                )
            else:
                self.adjustment_stats['failed_adjustments'] += 1
                
        except Exception as e:
            logger.error(f"❌ 更新調整統計失敗: {e}")
    
    async def emergency_risk_reduction(self, risk_threshold: float = 0.5) -> Dict[str, Any]:
        """緊急風險減倉"""
        try:
            logger.warning("🚨 觸發緊急風險減倉機制")
            self.emergency_mode = True
            
            reduction_results = []
            
            for pair, position in self.active_positions.items():
                if position.current_size > 0:
                    # 減倉50%或更多
                    reduction_ratio = max(0.5, risk_threshold)
                    new_size = position.current_size * (1 - reduction_ratio)
                    
                    # 執行減倉
                    result = await self._execute_position_adjustment(
                        pair, position.current_size, new_size,
                        PositionAdjustmentReason.EMERGENCY_REDUCTION, {}
                    )
                    
                    reduction_results.append(result)
                    
                    # 更新倉位
                    position.current_size = new_size
                    position.target_size = new_size
                    position.last_adjustment = datetime.now()
                    
                    self.adjustment_stats['emergency_reductions'] += 1
            
            logger.warning(f"🚨 緊急減倉完成，影響 {len(reduction_results)} 個倉位")
            
            return {
                'action': 'emergency_reduction_completed',
                'affected_positions': len(reduction_results),
                'reduction_results': reduction_results,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ 緊急風險減倉失敗: {e}")
            return {
                'action': 'emergency_reduction_failed',
                'error': str(e)
            }
        finally:
            # 30分鐘後解除緊急模式
            await asyncio.sleep(1800)
            self.emergency_mode = False
            logger.info("✅ 緊急模式已解除")
    
    def get_position_summary(self) -> Dict[str, Any]:
        """獲取倉位摘要"""
        try:
            total_exposure = sum(pos.current_size for pos in self.active_positions.values())
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.active_positions.values())
            
            # 計算風險指標
            avg_confidence = np.mean([pos.ai_confidence for pos in self.active_positions.values()]) if self.active_positions else 0.0
            avg_risk_score = np.mean([pos.risk_score for pos in self.active_positions.values()]) if self.active_positions else 0.0
            
            # 倉位分布
            position_distribution = {}
            for pair, position in self.active_positions.items():
                position_distribution[pair] = {
                    'size': position.current_size,
                    'percentage': position.current_size / total_exposure if total_exposure > 0 else 0,
                    'confidence': position.ai_confidence,
                    'risk_score': position.risk_score,
                    'pnl': position.unrealized_pnl
                }
            
            return {
                'summary': {
                    'active_positions': len(self.active_positions),
                    'total_exposure': total_exposure,
                    'exposure_utilization': total_exposure / self.config.max_total_exposure,
                    'total_unrealized_pnl': total_unrealized_pnl,
                    'avg_ai_confidence': avg_confidence,
                    'avg_risk_score': avg_risk_score,
                    'emergency_mode': self.emergency_mode
                },
                'positions': position_distribution,
                'adjustment_stats': self.adjustment_stats.copy(),
                'risk_alerts': len(self.risk_alerts),
                'last_update': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取倉位摘要失敗: {e}")
            return {}
    
    def get_position_recommendations(self) -> List[Dict[str, Any]]:
        """獲取倉位建議"""
        try:
            recommendations = []
            
            for pair, position in self.active_positions.items():
                # 基於當前指標生成建議
                if position.ai_confidence < 0.4:
                    recommendations.append({
                        'pair': pair,
                        'action': 'reduce_position',
                        'reason': 'low_ai_confidence',
                        'current_confidence': position.ai_confidence,
                        'suggested_reduction': '30-50%'
                    })
                
                if position.risk_score > 0.8:
                    recommendations.append({
                        'pair': pair,
                        'action': 'reduce_position',
                        'reason': 'high_risk_score',
                        'current_risk': position.risk_score,
                        'suggested_reduction': '40-60%'
                    })
                
                if position.holding_duration.total_seconds() > 86400:  # 24小時
                    recommendations.append({
                        'pair': pair,
                        'action': 'review_position',
                        'reason': 'long_holding_period',
                        'holding_hours': position.holding_duration.total_seconds() / 3600,
                        'suggestion': 'consider_profit_taking_or_stop_loss'
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ 獲取倉位建議失敗: {e}")
            return []


# 創建動態倉位管理器實例
def create_dynamic_position_manager(config: DynamicPositionConfig = None) -> DynamicPositionManager:
    """創建動態倉位管理器實例"""
    return DynamicPositionManager(config)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_dynamic_position_manager():
        """測試動態倉位管理器"""
        print("🧪 測試動態倉位管理器...")
        
        # 創建管理器
        manager = create_dynamic_position_manager()
        
        # 模擬AI分析結果
        ai_analysis = {
            'confidence': 0.75,
            'risk_score': 0.3,
            'signal_strength': 0.8
        }
        
        # 模擬市場數據
        market_data = {
            'volatility_level': 'medium',
            'trend_strength': 0.6,
            'volume_profile': 'normal'
        }
        
        # 測試倉位計算
        target_size, details = await manager.calculate_optimal_position_size(
            'BTCTWD', ai_analysis, market_data
        )
        print(f"✅ 計算目標倉位: {target_size:.3%}")
        print(f"   計算詳情: {details}")
        
        # 測試倉位調整
        adjustment_result = await manager.adjust_position(
            'BTCTWD', ai_analysis, market_data
        )
        print(f"✅ 倉位調整結果: {adjustment_result}")
        
        # 測試多個交易對
        pairs = ['ETHTWD', 'LTCTWD']
        for pair in pairs:
            await manager.adjust_position(pair, ai_analysis, market_data)
        
        # 獲取倉位摘要
        summary = manager.get_position_summary()
        print(f"📊 倉位摘要: {summary}")
        
        # 獲取建議
        recommendations = manager.get_position_recommendations()
        print(f"💡 倉位建議: {recommendations}")
        
        print("✅ 動態倉位管理器測試完成")
    
    # 運行測試
    asyncio.run(test_dynamic_position_manager())