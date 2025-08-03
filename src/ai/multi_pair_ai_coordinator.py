#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易對AI決策協調器 - 實現全局AI決策協調和資源分配
基於五AI超智能協作系統的多交易對決策協調
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict

try:
    from .enhanced_ai_manager import EnhancedAIManager, MultiPairDecision, EnhancedAIResponse
except ImportError:
    from enhanced_ai_manager import EnhancedAIManager, MultiPairDecision, EnhancedAIResponse

logger = logging.getLogger(__name__)

class DecisionPriority(Enum):
    """決策優先級"""
    CRITICAL = 1    # 緊急決策
    HIGH = 2        # 高優先級
    NORMAL = 3      # 正常優先級
    LOW = 4         # 低優先級

@dataclass
class GlobalDecisionContext:
    """全局決策上下文"""
    total_pairs: int
    active_pairs: List[str]
    market_conditions: str  # 'bull', 'bear', 'sideways'
    global_risk_level: float  # 0-1
    available_capital: float
    max_concurrent_trades: int
    correlation_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)

@dataclass
class DecisionConflict:
    """決策衝突"""
    pair1: str
    pair2: str
    conflict_type: str  # 'resource', 'correlation', 'risk'
    severity: float  # 0-1
    resolution_strategy: str

@dataclass
class CoordinatedDecision:
    """協調後的決策"""
    pair: str
    original_decision: MultiPairDecision
    coordinated_decision: str  # BUY, SELL, HOLD
    priority: DecisionPriority
    allocated_capital: float
    execution_order: int
    coordination_reason: str
    global_impact_score: float

class MultiPairAICoordinator:
    """多交易對AI決策協調器"""
    
    def __init__(self, ai_manager: EnhancedAIManager):
        self.ai_manager = ai_manager
        
        # 協調配置
        self.max_concurrent_positions = 3
        self.max_total_risk_exposure = 0.15  # 15%總風險敞口
        self.correlation_threshold = 0.7  # 相關性閾值
        self.min_confidence_threshold = 0.6  # 最小信心度閾值
        
        # 決策協調規則
        self.coordination_rules = {
            'risk_diversification': True,
            'correlation_control': True,
            'capital_allocation': True,
            'priority_management': True,
            'conflict_resolution': True
        }
        
        # 全局狀態追蹤
        self.global_context = GlobalDecisionContext(
            total_pairs=0,
            active_pairs=[],
            market_conditions='sideways',
            global_risk_level=0.5,
            available_capital=100000.0,  # 預設10萬TWD
            max_concurrent_trades=3
        )
        
        # 決策歷史和統計
        self.decision_history: List[CoordinatedDecision] = []
        self.conflict_history: List[DecisionConflict] = []
        self.coordination_stats = {
            'total_coordinations': 0,
            'conflicts_resolved': 0,
            'capital_efficiency': 0.0,
            'risk_adjusted_return': 0.0
        }
        
        logger.info("🎯 多交易對AI決策協調器初始化完成")
    
    async def coordinate_multi_pair_decisions(self, 
                                            multi_pair_data: Dict[str, Dict[str, Any]],
                                            global_context: Optional[GlobalDecisionContext] = None) -> Dict[str, CoordinatedDecision]:
        """
        協調多交易對AI決策
        
        Args:
            multi_pair_data: 多交易對市場數據
            global_context: 全局決策上下文
            
        Returns:
            Dict[str, CoordinatedDecision]: 協調後的決策
        """
        logger.info(f"🎯 開始多交易對AI決策協調: {len(multi_pair_data)} 個交易對")
        
        # 更新全局上下文
        if global_context:
            self.global_context = global_context
        else:
            self._update_global_context(multi_pair_data)
        
        try:
            # 階段1: 獲取原始AI決策
            logger.info("📊 階段1: 獲取五AI原始決策...")
            raw_decisions = await self.ai_manager.analyze_multi_pair_market(multi_pair_data)
            
            # 階段2: 分析決策衝突
            logger.info("⚔️ 階段2: 分析決策衝突...")
            conflicts = self._analyze_decision_conflicts(raw_decisions)
            
            # 階段3: 全局風險評估
            logger.info("⚠️ 階段3: 全局風險評估...")
            global_risk_assessment = self._assess_global_risk(raw_decisions)
            
            # 階段4: 資源分配優化
            logger.info("💰 階段4: 資源分配優化...")
            resource_allocation = self._optimize_resource_allocation(raw_decisions, global_risk_assessment)
            
            # 階段5: 決策優先級排序
            logger.info("📋 階段5: 決策優先級排序...")
            prioritized_decisions = self._prioritize_decisions(raw_decisions, resource_allocation)
            
            # 階段6: 衝突解決和最終協調
            logger.info("🔧 階段6: 衝突解決和最終協調...")
            coordinated_decisions = self._resolve_conflicts_and_coordinate(
                prioritized_decisions, conflicts, resource_allocation
            )
            
            # 更新統計和歷史
            self._update_coordination_stats(coordinated_decisions, conflicts)
            
            logger.info(f"✅ 多交易對AI決策協調完成: {len(coordinated_decisions)} 個協調決策")
            
            return coordinated_decisions
            
        except Exception as e:
            logger.error(f"❌ 多交易對AI決策協調失敗: {e}")
            # 返回備用決策
            return self._create_fallback_coordinated_decisions(multi_pair_data)
    
    def _update_global_context(self, multi_pair_data: Dict[str, Dict[str, Any]]):
        """更新全局決策上下文"""
        try:
            self.global_context.total_pairs = len(multi_pair_data)
            self.global_context.active_pairs = list(multi_pair_data.keys())
            
            # 分析全局市場條件
            avg_volatility = np.mean([
                data.get('volatility', 0.02) for data in multi_pair_data.values()
            ])
            
            avg_trend = np.mean([
                data.get('price_trend_slope', 0) for data in multi_pair_data.values()
            ])
            
            # 判斷市場條件
            if avg_trend > 0.01 and avg_volatility < 0.05:
                self.global_context.market_conditions = 'bull'
            elif avg_trend < -0.01 and avg_volatility > 0.05:
                self.global_context.market_conditions = 'bear'
            else:
                self.global_context.market_conditions = 'sideways'
            
            # 計算全局風險水平
            self.global_context.global_risk_level = min(1.0, avg_volatility * 10)
            
            # 計算交易對相關性矩陣
            self._calculate_correlation_matrix(multi_pair_data)
            
            logger.debug(f"🌍 全局上下文更新: {self.global_context.market_conditions} 市場, "
                        f"風險水平 {self.global_context.global_risk_level:.2f}")
            
        except Exception as e:
            logger.error(f"❌ 更新全局上下文失敗: {e}")
    
    def _calculate_correlation_matrix(self, multi_pair_data: Dict[str, Dict[str, Any]]):
        """計算交易對相關性矩陣"""
        try:
            pairs = list(multi_pair_data.keys())
            correlation_matrix = {}
            
            for pair1 in pairs:
                correlation_matrix[pair1] = {}
                for pair2 in pairs:
                    if pair1 == pair2:
                        correlation_matrix[pair1][pair2] = 1.0
                    else:
                        # 基於價格變化和波動率計算簡化相關性
                        data1 = multi_pair_data[pair1]
                        data2 = multi_pair_data[pair2]
                        
                        # 簡化相關性計算
                        price_corr = self._calculate_price_correlation(data1, data2)
                        vol_corr = self._calculate_volatility_correlation(data1, data2)
                        
                        # 綜合相關性
                        correlation = (price_corr + vol_corr) / 2
                        correlation_matrix[pair1][pair2] = correlation
            
            self.global_context.correlation_matrix = correlation_matrix
            
        except Exception as e:
            logger.error(f"❌ 計算相關性矩陣失敗: {e}")
            # 設置默認相關性
            pairs = list(multi_pair_data.keys())
            self.global_context.correlation_matrix = {
                pair1: {pair2: 0.3 if pair1 != pair2 else 1.0 for pair2 in pairs}
                for pair1 in pairs
            }
    
    def _calculate_price_correlation(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> float:
        """計算價格相關性"""
        try:
            # 基於價格變化計算相關性
            change1 = data1.get('price_change_5m', 0)
            change2 = data2.get('price_change_5m', 0)
            
            # 簡化相關性：同向變化為正相關，反向為負相關
            if change1 * change2 > 0:
                return min(0.8, abs(change1 + change2) / 10)
            else:
                return max(-0.5, -(abs(change1 - change2) / 10))
                
        except Exception:
            return 0.3  # 默認中等相關性
    
    def _calculate_volatility_correlation(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> float:
        """計算波動率相關性"""
        try:
            vol1 = data1.get('volatility', 0.02)
            vol2 = data2.get('volatility', 0.02)
            
            # 波動率相似度
            vol_diff = abs(vol1 - vol2)
            return max(0.0, 1.0 - vol_diff * 10)
            
        except Exception:
            return 0.3
    
    def _analyze_decision_conflicts(self, raw_decisions: Dict[str, MultiPairDecision]) -> List[DecisionConflict]:
        """分析決策衝突"""
        conflicts = []
        
        try:
            pairs = list(raw_decisions.keys())
            
            for i, pair1 in enumerate(pairs):
                for pair2 in pairs[i+1:]:
                    decision1 = raw_decisions[pair1]
                    decision2 = raw_decisions[pair2]
                    
                    # 檢查資源衝突
                    resource_conflict = self._check_resource_conflict(decision1, decision2)
                    if resource_conflict:
                        conflicts.append(resource_conflict)
                    
                    # 檢查相關性衝突
                    correlation_conflict = self._check_correlation_conflict(pair1, pair2, decision1, decision2)
                    if correlation_conflict:
                        conflicts.append(correlation_conflict)
                    
                    # 檢查風險衝突
                    risk_conflict = self._check_risk_conflict(decision1, decision2)
                    if risk_conflict:
                        conflicts.append(risk_conflict)
            
            logger.info(f"⚔️ 發現 {len(conflicts)} 個決策衝突")
            
        except Exception as e:
            logger.error(f"❌ 分析決策衝突失敗: {e}")
        
        return conflicts
    
    def _check_resource_conflict(self, decision1: MultiPairDecision, decision2: MultiPairDecision) -> Optional[DecisionConflict]:
        """檢查資源衝突"""
        try:
            # 如果兩個決策都要求大量資源
            if (decision1.final_decision in ['BUY'] and decision1.position_size > 0.1 and
                decision2.final_decision in ['BUY'] and decision2.position_size > 0.1):
                
                total_required = decision1.position_size + decision2.position_size
                if total_required > self.max_total_risk_exposure:
                    return DecisionConflict(
                        pair1=decision1.pair,
                        pair2=decision2.pair,
                        conflict_type='resource',
                        severity=min(1.0, total_required / self.max_total_risk_exposure - 1),
                        resolution_strategy='reduce_position_sizes'
                    )
            
        except Exception as e:
            logger.error(f"❌ 檢查資源衝突失敗: {e}")
        
        return None
    
    def _check_correlation_conflict(self, pair1: str, pair2: str, 
                                  decision1: MultiPairDecision, decision2: MultiPairDecision) -> Optional[DecisionConflict]:
        """檢查相關性衝突"""
        try:
            # 獲取相關性
            correlation = self.global_context.correlation_matrix.get(pair1, {}).get(pair2, 0.3)
            
            # 如果高度相關且決策相同，可能存在過度集中風險
            if (abs(correlation) > self.correlation_threshold and
                decision1.final_decision == decision2.final_decision and
                decision1.final_decision in ['BUY', 'SELL']):
                
                return DecisionConflict(
                    pair1=pair1,
                    pair2=pair2,
                    conflict_type='correlation',
                    severity=abs(correlation),
                    resolution_strategy='diversify_positions'
                )
                
        except Exception as e:
            logger.error(f"❌ 檢查相關性衝突失敗: {e}")
        
        return None
    
    def _check_risk_conflict(self, decision1: MultiPairDecision, decision2: MultiPairDecision) -> Optional[DecisionConflict]:
        """檢查風險衝突"""
        try:
            # 如果兩個決策都是高風險
            if (decision1.risk_score > 0.7 and decision2.risk_score > 0.7 and
                decision1.final_decision in ['BUY', 'SELL'] and decision2.final_decision in ['BUY', 'SELL']):
                
                return DecisionConflict(
                    pair1=decision1.pair,
                    pair2=decision2.pair,
                    conflict_type='risk',
                    severity=(decision1.risk_score + decision2.risk_score) / 2,
                    resolution_strategy='reduce_risk_exposure'
                )
                
        except Exception as e:
            logger.error(f"❌ 檢查風險衝突失敗: {e}")
        
        return None 
   
    def _assess_global_risk(self, raw_decisions: Dict[str, MultiPairDecision]) -> Dict[str, Any]:
        """評估全局風險"""
        try:
            total_risk_exposure = 0.0
            active_positions = 0
            high_risk_pairs = []
            
            for pair, decision in raw_decisions.items():
                if decision.final_decision in ['BUY', 'SELL']:
                    risk_contribution = decision.position_size * decision.risk_score
                    total_risk_exposure += risk_contribution
                    active_positions += 1
                    
                    if decision.risk_score > 0.7:
                        high_risk_pairs.append(pair)
            
            # 計算風險分散度
            risk_diversification = 1.0 - (len(high_risk_pairs) / max(1, len(raw_decisions)))
            
            # 計算資源利用率
            resource_utilization = total_risk_exposure / self.max_total_risk_exposure
            
            global_risk_assessment = {
                'total_risk_exposure': total_risk_exposure,
                'active_positions': active_positions,
                'high_risk_pairs': high_risk_pairs,
                'risk_diversification': risk_diversification,
                'resource_utilization': resource_utilization,
                'risk_level': min(1.0, total_risk_exposure / self.max_total_risk_exposure),
                'recommendations': []
            }
            
            # 生成風險建議
            if resource_utilization > 0.8:
                global_risk_assessment['recommendations'].append('減少整體倉位規模')
            
            if len(high_risk_pairs) > 2:
                global_risk_assessment['recommendations'].append('降低高風險交易對數量')
            
            if risk_diversification < 0.5:
                global_risk_assessment['recommendations'].append('增加風險分散化')
            
            logger.info(f"⚠️ 全局風險評估: 風險敞口 {total_risk_exposure:.2%}, "
                       f"活躍倉位 {active_positions}, 風險水平 {global_risk_assessment['risk_level']:.2f}")
            
            return global_risk_assessment
            
        except Exception as e:
            logger.error(f"❌ 全局風險評估失敗: {e}")
            return {
                'total_risk_exposure': 0.05,
                'risk_level': 0.5,
                'recommendations': ['系統錯誤，採用保守策略']
            }
    
    def _optimize_resource_allocation(self, raw_decisions: Dict[str, MultiPairDecision], 
                                    global_risk_assessment: Dict[str, Any]) -> Dict[str, float]:
        """優化資源分配"""
        try:
            resource_allocation = {}
            available_capital = self.global_context.available_capital
            total_required_capital = 0.0
            
            # 計算總需求資本
            for pair, decision in raw_decisions.items():
                if decision.final_decision in ['BUY', 'SELL']:
                    required_capital = decision.position_size * available_capital
                    total_required_capital += required_capital
            
            # 如果需求超過可用資本，按比例分配
            if total_required_capital > available_capital:
                allocation_ratio = available_capital / total_required_capital
                logger.info(f"💰 資源不足，按比例分配: {allocation_ratio:.2f}")
            else:
                allocation_ratio = 1.0
            
            # 基於信心度和風險調整分配
            for pair, decision in raw_decisions.items():
                if decision.final_decision in ['BUY', 'SELL']:
                    base_allocation = decision.position_size * available_capital * allocation_ratio
                    
                    # 信心度調整
                    confidence_multiplier = decision.confidence
                    
                    # 風險調整
                    risk_multiplier = max(0.1, 1.0 - decision.risk_score)
                    
                    # 最終分配
                    final_allocation = base_allocation * confidence_multiplier * risk_multiplier
                    resource_allocation[pair] = min(final_allocation, available_capital * 0.3)  # 單個交易對最多30%
                else:
                    resource_allocation[pair] = 0.0
            
            logger.info(f"💰 資源分配完成: {len(resource_allocation)} 個交易對")
            
            return resource_allocation
            
        except Exception as e:
            logger.error(f"❌ 資源分配優化失敗: {e}")
            return {pair: 0.0 for pair in raw_decisions.keys()}
    
    def _prioritize_decisions(self, raw_decisions: Dict[str, MultiPairDecision], 
                            resource_allocation: Dict[str, float]) -> Dict[str, Tuple[MultiPairDecision, DecisionPriority]]:
        """決策優先級排序"""
        try:
            prioritized_decisions = {}
            
            for pair, decision in raw_decisions.items():
                # 計算優先級分數
                priority_score = self._calculate_priority_score(decision, resource_allocation.get(pair, 0))
                
                # 確定優先級
                if priority_score >= 0.8:
                    priority = DecisionPriority.CRITICAL
                elif priority_score >= 0.6:
                    priority = DecisionPriority.HIGH
                elif priority_score >= 0.4:
                    priority = DecisionPriority.NORMAL
                else:
                    priority = DecisionPriority.LOW
                
                prioritized_decisions[pair] = (decision, priority)
            
            logger.info(f"📋 決策優先級排序完成")
            
            return prioritized_decisions
            
        except Exception as e:
            logger.error(f"❌ 決策優先級排序失敗: {e}")
            return {pair: (decision, DecisionPriority.NORMAL) for pair, decision in raw_decisions.items()}
    
    def _calculate_priority_score(self, decision: MultiPairDecision, allocated_capital: float) -> float:
        """計算優先級分數"""
        try:
            # 基礎分數：信心度
            base_score = decision.confidence
            
            # 風險調整：低風險加分
            risk_adjustment = max(0, 1.0 - decision.risk_score) * 0.3
            
            # 資本分配調整：高分配加分
            capital_adjustment = min(0.2, allocated_capital / self.global_context.available_capital)
            
            # 市場條件調整
            market_adjustment = 0.0
            if self.global_context.market_conditions == 'bull' and decision.final_decision == 'BUY':
                market_adjustment = 0.1
            elif self.global_context.market_conditions == 'bear' and decision.final_decision == 'SELL':
                market_adjustment = 0.1
            
            # 綜合分數
            priority_score = base_score + risk_adjustment + capital_adjustment + market_adjustment
            
            return min(1.0, priority_score)
            
        except Exception as e:
            logger.error(f"❌ 計算優先級分數失敗: {e}")
            return 0.5
    
    def _resolve_conflicts_and_coordinate(self, 
                                        prioritized_decisions: Dict[str, Tuple[MultiPairDecision, DecisionPriority]],
                                        conflicts: List[DecisionConflict],
                                        resource_allocation: Dict[str, float]) -> Dict[str, CoordinatedDecision]:
        """解決衝突並生成最終協調決策"""
        try:
            coordinated_decisions = {}
            execution_order = 1
            
            # 按優先級排序
            sorted_pairs = sorted(prioritized_decisions.items(), 
                                key=lambda x: x[1][1].value)  # 按優先級值排序（數字越小優先級越高）
            
            # 處理每個決策
            for pair, (decision, priority) in sorted_pairs:
                # 檢查是否涉及衝突
                pair_conflicts = [c for c in conflicts if c.pair1 == pair or c.pair2 == pair]
                
                # 應用衝突解決策略
                coordinated_decision_action, coordination_reason = self._apply_conflict_resolution(
                    decision, pair_conflicts, priority
                )
                
                # 計算全局影響分數
                global_impact_score = self._calculate_global_impact_score(decision, pair_conflicts)
                
                # 創建協調決策
                coordinated_decision = CoordinatedDecision(
                    pair=pair,
                    original_decision=decision,
                    coordinated_decision=coordinated_decision_action,
                    priority=priority,
                    allocated_capital=resource_allocation.get(pair, 0),
                    execution_order=execution_order,
                    coordination_reason=coordination_reason,
                    global_impact_score=global_impact_score
                )
                
                coordinated_decisions[pair] = coordinated_decision
                
                if coordinated_decision_action in ['BUY', 'SELL']:
                    execution_order += 1
            
            logger.info(f"🔧 衝突解決和協調完成: {len(coordinated_decisions)} 個協調決策")
            
            return coordinated_decisions
            
        except Exception as e:
            logger.error(f"❌ 衝突解決和協調失敗: {e}")
            return {}
    
    def _apply_conflict_resolution(self, decision: MultiPairDecision, 
                                 conflicts: List[DecisionConflict], 
                                 priority: DecisionPriority) -> Tuple[str, str]:
        """應用衝突解決策略"""
        try:
            if not conflicts:
                return decision.final_decision, "無衝突，保持原決策"
            
            # 分析衝突嚴重程度
            max_severity = max(c.severity for c in conflicts)
            conflict_types = [c.conflict_type for c in conflicts]
            
            # 高優先級決策的處理
            if priority in [DecisionPriority.CRITICAL, DecisionPriority.HIGH]:
                if max_severity < 0.7:
                    return decision.final_decision, f"高優先級決策，輕微衝突可接受 (嚴重度: {max_severity:.2f})"
                else:
                    # 嚴重衝突，降級處理
                    if decision.final_decision in ['BUY', 'SELL']:
                        return 'HOLD', f"高優先級但嚴重衝突，改為觀望 (嚴重度: {max_severity:.2f})"
            
            # 資源衝突處理
            if 'resource' in conflict_types:
                if decision.confidence > 0.8:
                    return decision.final_decision, "高信心度決策，接受資源衝突"
                else:
                    return 'HOLD', "資源衝突且信心度不足，改為觀望"
            
            # 相關性衝突處理
            if 'correlation' in conflict_types:
                if decision.final_decision == 'BUY':
                    return 'HOLD', "相關性衝突，避免過度集中風險"
                else:
                    return decision.final_decision, "賣出決策，相關性衝突影響較小"
            
            # 風險衝突處理
            if 'risk' in conflict_types:
                return 'HOLD', "風險衝突，採用保守策略"
            
            # 默認處理
            return 'HOLD', f"多重衝突，採用保守策略 (衝突類型: {', '.join(conflict_types)})"
            
        except Exception as e:
            logger.error(f"❌ 應用衝突解決策略失敗: {e}")
            return 'HOLD', "系統錯誤，採用保守策略"
    
    def _calculate_global_impact_score(self, decision: MultiPairDecision, 
                                     conflicts: List[DecisionConflict]) -> float:
        """計算全局影響分數"""
        try:
            # 基礎影響：基於倉位大小和信心度
            base_impact = decision.position_size * decision.confidence
            
            # 衝突影響：衝突越多影響越大
            conflict_impact = len(conflicts) * 0.1
            
            # 風險影響：高風險決策影響更大
            risk_impact = decision.risk_score * 0.2
            
            # 綜合影響分數
            global_impact = base_impact + conflict_impact + risk_impact
            
            return min(1.0, global_impact)
            
        except Exception as e:
            logger.error(f"❌ 計算全局影響分數失敗: {e}")
            return 0.5
    
    def _update_coordination_stats(self, coordinated_decisions: Dict[str, CoordinatedDecision], 
                                 conflicts: List[DecisionConflict]):
        """更新協調統計"""
        try:
            self.coordination_stats['total_coordinations'] += 1
            self.coordination_stats['conflicts_resolved'] += len(conflicts)
            
            # 計算資本效率
            total_allocated = sum(d.allocated_capital for d in coordinated_decisions.values())
            self.coordination_stats['capital_efficiency'] = total_allocated / self.global_context.available_capital
            
            # 更新決策歷史
            self.decision_history.extend(coordinated_decisions.values())
            self.conflict_history.extend(conflicts)
            
            # 保持歷史記錄在合理範圍內
            if len(self.decision_history) > 1000:
                self.decision_history = self.decision_history[-500:]
            
            if len(self.conflict_history) > 500:
                self.conflict_history = self.conflict_history[-250:]
            
        except Exception as e:
            logger.error(f"❌ 更新協調統計失敗: {e}")
    
    def _create_fallback_coordinated_decisions(self, multi_pair_data: Dict[str, Dict[str, Any]]) -> Dict[str, CoordinatedDecision]:
        """創建備用協調決策"""
        fallback_decisions = {}
        
        for i, pair in enumerate(multi_pair_data.keys(), 1):
            # 創建保守的備用決策
            fallback_decision = CoordinatedDecision(
                pair=pair,
                original_decision=None,
                coordinated_decision='HOLD',
                priority=DecisionPriority.LOW,
                allocated_capital=0.0,
                execution_order=i,
                coordination_reason='系統錯誤，採用保守策略',
                global_impact_score=0.0
            )
            
            fallback_decisions[pair] = fallback_decision
        
        return fallback_decisions
    
    def get_coordination_status(self) -> Dict[str, Any]:
        """獲取協調狀態"""
        try:
            return {
                'global_context': {
                    'total_pairs': self.global_context.total_pairs,
                    'active_pairs': self.global_context.active_pairs,
                    'market_conditions': self.global_context.market_conditions,
                    'global_risk_level': self.global_context.global_risk_level,
                    'available_capital': self.global_context.available_capital
                },
                'coordination_rules': self.coordination_rules,
                'coordination_stats': self.coordination_stats,
                'recent_decisions': len(self.decision_history),
                'recent_conflicts': len(self.conflict_history),
                'system_health': 'healthy' if self.coordination_stats['total_coordinations'] > 0 else 'initializing'
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取協調狀態失敗: {e}")
            return {'error': str(e)}
    
    def update_coordination_rules(self, new_rules: Dict[str, bool]):
        """更新協調規則"""
        try:
            self.coordination_rules.update(new_rules)
            logger.info(f"🔧 協調規則已更新: {new_rules}")
            
        except Exception as e:
            logger.error(f"❌ 更新協調規則失敗: {e}")
    
    def get_decision_history(self, limit: int = 50) -> List[CoordinatedDecision]:
        """獲取決策歷史"""
        return self.decision_history[-limit:]
    
    def get_conflict_history(self, limit: int = 20) -> List[DecisionConflict]:
        """獲取衝突歷史"""
        return self.conflict_history[-limit:]


# 創建多交易對AI協調器實例
def create_multi_pair_ai_coordinator(ai_manager: EnhancedAIManager) -> MultiPairAICoordinator:
    """創建多交易對AI協調器實例"""
    return MultiPairAICoordinator(ai_manager)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_coordinator():
        """測試多交易對AI協調器"""
        print("🧪 測試多交易對AI協調器...")
        
        # 這裡需要實際的AI管理器實例進行測試
        # 由於依賴較多，實際測試應該在集成環境中進行
        print("✅ 多交易對AI協調器測試需要在集成環境中進行")
    
    # 運行測試
    asyncio.run(test_coordinator())