#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DCA市場適應性機制 - 實現智能DCA策略的市場適應性調整
支持動態頻率調整、智能加減倉、風險控制和多交易對協調
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
import numpy as np

logger = logging.getLogger(__name__)

class MarketRegime(Enum):
    """市場狀態"""
    BULL_MARKET = "bull_market"        # 牛市
    BEAR_MARKET = "bear_market"        # 熊市
    SIDEWAYS_MARKET = "sideways_market" # 震盪市
    VOLATILE_MARKET = "volatile_market" # 高波動市場
    CRASH_MARKET = "crash_market"      # 崩盤市場

class AdaptationAction(Enum):
    """適應性動作"""
    INCREASE_FREQUENCY = "increase_frequency"    # 增加頻率
    DECREASE_FREQUENCY = "decrease_frequency"    # 降低頻率
    INCREASE_AMOUNT = "increase_amount"          # 增加金額
    DECREASE_AMOUNT = "decrease_amount"          # 減少金額
    PAUSE_STRATEGY = "pause_strategy"            # 暫停策略
    RESUME_STRATEGY = "resume_strategy"          # 恢復策略
    EMERGENCY_STOP = "emergency_stop"            # 緊急停止

@dataclass
class MarketCondition:
    """市場條件"""
    pair: str
    timestamp: datetime
    current_price: float
    price_change_1h: float
    price_change_24h: float
    price_change_7d: float
    price_change_30d: float
    volatility_1d: float
    volatility_7d: float
    volume_ratio: float
    rsi_14: float
    market_regime: MarketRegime
    trend_strength: float
    support_level: float
    resistance_level: float

@dataclass
class AdaptationRule:
    """適應性規則"""
    rule_id: str
    name: str
    condition: str                    # 觸發條件
    action: AdaptationAction         # 執行動作
    priority: int                    # 優先級 (1-10)
    cooldown_hours: int              # 冷卻時間
    max_adjustments_per_day: int     # 每日最大調整次數
    enabled: bool = True

@dataclass
class AdaptationEvent:
    """適應性事件"""
    event_id: str
    timestamp: datetime
    pair: str
    rule_id: str
    action: AdaptationAction
    reason: str
    old_value: Any
    new_value: Any
    confidence: float
    success: bool

class DCAMarketAdaptation:
    """DCA市場適應性機制"""
    
    def __init__(self, ai_coordinator=None):
        self.ai_coordinator = ai_coordinator
        
        # 適應性配置
        self.adaptation_config = {
            'volatility_threshold_high': 0.08,      # 高波動閾值
            'volatility_threshold_low': 0.02,       # 低波動閾值
            'crash_threshold': -0.15,               # 崩盤閾值
            'bull_threshold': 0.20,                 # 牛市閾值
            'bear_threshold': -0.20,                # 熊市閾值
            'max_frequency_adjustment': 0.5,        # 最大頻率調整
            'max_amount_adjustment': 2.0,           # 最大金額調整
            'emergency_stop_threshold': -0.30,      # 緊急停止閾值
            'adaptation_sensitivity': 0.7           # 適應性敏感度
        }
        
        # 適應性規則
        self.adaptation_rules = self._initialize_adaptation_rules()
        
        # 歷史記錄
        self.adaptation_history: List[AdaptationEvent] = []
        self.market_conditions_history: List[MarketCondition] = []
        
        # 統計數據
        self.adaptation_stats = {
            'total_adaptations': 0,
            'successful_adaptations': 0,
            'frequency_adjustments': 0,
            'amount_adjustments': 0,
            'emergency_stops': 0,
            'avg_adaptation_confidence': 0.0
        }
        
        logger.info("🔄 DCA市場適應性機制初始化完成")
    
    def _initialize_adaptation_rules(self) -> List[AdaptationRule]:
        """初始化適應性規則"""
        rules = [
            # 熊市加倉規則
            AdaptationRule(
                rule_id="bear_market_increase",
                name="熊市加倉策略",
                condition="market_regime == BEAR_MARKET and price_change_7d < -0.10",
                action=AdaptationAction.INCREASE_AMOUNT,
                priority=8,
                cooldown_hours=24,
                max_adjustments_per_day=2
            ),
            
            # 牛市減倉規則
            AdaptationRule(
                rule_id="bull_market_decrease",
                name="牛市減倉策略", 
                condition="market_regime == BULL_MARKET and price_change_7d > 0.15",
                action=AdaptationAction.DECREASE_AMOUNT,
                priority=7,
                cooldown_hours=12,
                max_adjustments_per_day=3
            ),
            
            # 高波動增頻規則
            AdaptationRule(
                rule_id="high_volatility_increase_freq",
                name="高波動增加頻率",
                condition="volatility_7d > 0.08 and market_regime in [VOLATILE_MARKET, BEAR_MARKET]",
                action=AdaptationAction.INCREASE_FREQUENCY,
                priority=6,
                cooldown_hours=6,
                max_adjustments_per_day=4
            ),
            
            # 低波動降頻規則
            AdaptationRule(
                rule_id="low_volatility_decrease_freq",
                name="低波動降低頻率",
                condition="volatility_7d < 0.02 and market_regime == SIDEWAYS_MARKET",
                action=AdaptationAction.DECREASE_FREQUENCY,
                priority=4,
                cooldown_hours=24,
                max_adjustments_per_day=1
            ),
            
            # 崩盤緊急加倉規則
            AdaptationRule(
                rule_id="crash_emergency_increase",
                name="崩盤緊急加倉",
                condition="price_change_24h < -0.15 and market_regime == CRASH_MARKET",
                action=AdaptationAction.INCREASE_AMOUNT,
                priority=10,
                cooldown_hours=1,
                max_adjustments_per_day=10
            ),
            
            # 極端下跌緊急停止規則
            AdaptationRule(
                rule_id="extreme_drop_emergency_stop",
                name="極端下跌緊急停止",
                condition="price_change_24h < -0.30",
                action=AdaptationAction.EMERGENCY_STOP,
                priority=10,
                cooldown_hours=24,
                max_adjustments_per_day=1
            ),
            
            # RSI超賣加倉規則
            AdaptationRule(
                rule_id="rsi_oversold_increase",
                name="RSI超賣加倉",
                condition="rsi_14 < 25 and price_change_7d < -0.05",
                action=AdaptationAction.INCREASE_AMOUNT,
                priority=7,
                cooldown_hours=12,
                max_adjustments_per_day=2
            ),
            
            # RSI超買減倉規則
            AdaptationRule(
                rule_id="rsi_overbought_decrease",
                name="RSI超買減倉",
                condition="rsi_14 > 75 and price_change_7d > 0.10",
                action=AdaptationAction.DECREASE_AMOUNT,
                priority=6,
                cooldown_hours=8,
                max_adjustments_per_day=3
            )
        ]
        
        return rules    

    async def analyze_market_adaptation(self, pair: str, market_data: Dict[str, Any], 
                                      current_dca_config: Dict[str, Any]) -> Dict[str, Any]:
        """分析市場適應性調整需求"""
        logger.info(f"🔄 開始DCA市場適應性分析: {pair}")
        
        try:
            # 階段1: 分析市場條件
            market_condition = self._analyze_market_condition(pair, market_data)
            
            # 階段2: 評估適應性規則
            triggered_rules = self._evaluate_adaptation_rules(market_condition)
            
            # 階段3: 生成適應性建議
            adaptation_recommendations = self._generate_adaptation_recommendations(
                triggered_rules, market_condition, current_dca_config
            )
            
            # 階段4: 風險評估
            risk_assessment = self._assess_adaptation_risks(
                adaptation_recommendations, market_condition
            )
            
            # 階段5: 最終決策
            final_adaptations = self._make_final_adaptation_decisions(
                adaptation_recommendations, risk_assessment
            )
            
            # 更新歷史記錄
            self._update_adaptation_history(market_condition, final_adaptations)
            
            logger.info(f"✅ DCA市場適應性分析完成: {len(final_adaptations)} 個調整建議")
            
            return {
                'pair': pair,
                'market_condition': market_condition,
                'triggered_rules': len(triggered_rules),
                'adaptations': final_adaptations,
                'risk_level': risk_assessment.get('overall_risk', 0.5),
                'confidence': risk_assessment.get('confidence', 0.5)
            }
            
        except Exception as e:
            logger.error(f"❌ DCA市場適應性分析失敗: {e}")
            return {
                'pair': pair,
                'error': str(e),
                'adaptations': [],
                'risk_level': 0.8,
                'confidence': 0.3
            }
    
    def _analyze_market_condition(self, pair: str, market_data: Dict[str, Any]) -> MarketCondition:
        """分析市場條件"""
        try:
            # 提取市場數據
            current_price = market_data.get('current_price', 0)
            price_change_1h = market_data.get('price_change_1h', 0)
            price_change_24h = market_data.get('price_change_24h', 0)
            price_change_7d = market_data.get('price_change_7d', 0)
            price_change_30d = market_data.get('price_change_30d', 0)
            volatility_1d = market_data.get('volatility', 0.02)
            volatility_7d = market_data.get('volatility_7d', volatility_1d)
            volume_ratio = market_data.get('volume_ratio', 1.0)
            rsi_14 = market_data.get('rsi_14', 50)
            
            # 計算趨勢強度
            trend_strength = self._calculate_trend_strength(
                price_change_1h, price_change_24h, price_change_7d, price_change_30d
            )
            
            # 識別市場狀態
            market_regime = self._identify_market_regime(
                price_change_7d, price_change_30d, volatility_7d, trend_strength
            )
            
            # 計算支撐阻力位
            support_level = current_price * (1 - volatility_7d * 2)
            resistance_level = current_price * (1 + volatility_7d * 2)
            
            return MarketCondition(
                pair=pair,
                timestamp=datetime.now(),
                current_price=current_price,
                price_change_1h=price_change_1h,
                price_change_24h=price_change_24h,
                price_change_7d=price_change_7d,
                price_change_30d=price_change_30d,
                volatility_1d=volatility_1d,
                volatility_7d=volatility_7d,
                volume_ratio=volume_ratio,
                rsi_14=rsi_14,
                market_regime=market_regime,
                trend_strength=trend_strength,
                support_level=support_level,
                resistance_level=resistance_level
            )
            
        except Exception as e:
            logger.error(f"❌ 分析市場條件失敗: {e}")
            # 返回默認市場條件
            return MarketCondition(
                pair=pair,
                timestamp=datetime.now(),
                current_price=market_data.get('current_price', 0),
                price_change_1h=0,
                price_change_24h=0,
                price_change_7d=0,
                price_change_30d=0,
                volatility_1d=0.02,
                volatility_7d=0.02,
                volume_ratio=1.0,
                rsi_14=50,
                market_regime=MarketRegime.SIDEWAYS_MARKET,
                trend_strength=0.0,
                support_level=0,
                resistance_level=0
            )
    
    def _calculate_trend_strength(self, change_1h: float, change_24h: float, 
                                change_7d: float, change_30d: float) -> float:
        """計算趨勢強度"""
        try:
            # 計算各時間框架的權重
            weights = [0.1, 0.3, 0.4, 0.2]  # 1h, 24h, 7d, 30d
            changes = [change_1h, change_24h, change_7d, change_30d]
            
            # 計算加權平均變化
            weighted_change = sum(w * c for w, c in zip(weights, changes))
            
            # 計算趨勢一致性
            positive_count = sum(1 for c in changes if c > 0)
            negative_count = sum(1 for c in changes if c < 0)
            consistency = max(positive_count, negative_count) / len(changes)
            
            # 綜合趨勢強度
            trend_strength = abs(weighted_change) * consistency
            
            return min(1.0, trend_strength * 10)  # 歸一化到0-1
            
        except Exception as e:
            logger.error(f"❌ 計算趨勢強度失敗: {e}")
            return 0.0
    
    def _identify_market_regime(self, change_7d: float, change_30d: float, 
                              volatility: float, trend_strength: float) -> MarketRegime:
        """識別市場狀態"""
        try:
            # 崩盤市場 - 使用7天變化作為崩盤判斷
            if change_7d < self.adaptation_config['crash_threshold']:
                return MarketRegime.CRASH_MARKET
            
            # 高波動市場
            if volatility > self.adaptation_config['volatility_threshold_high']:
                return MarketRegime.VOLATILE_MARKET
            
            # 牛市
            if (change_30d > self.adaptation_config['bull_threshold'] and 
                change_7d > 0.05 and trend_strength > 0.6):
                return MarketRegime.BULL_MARKET
            
            # 熊市
            if (change_30d < self.adaptation_config['bear_threshold'] and 
                change_7d < -0.05 and trend_strength > 0.6):
                return MarketRegime.BEAR_MARKET
            
            # 震盪市場
            return MarketRegime.SIDEWAYS_MARKET
            
        except Exception as e:
            logger.error(f"❌ 識別市場狀態失敗: {e}")
            return MarketRegime.SIDEWAYS_MARKET
    
    def _evaluate_adaptation_rules(self, market_condition: MarketCondition) -> List[AdaptationRule]:
        """評估適應性規則"""
        triggered_rules = []
        
        try:
            for rule in self.adaptation_rules:
                if not rule.enabled:
                    continue
                
                # 檢查冷卻時間
                if self._is_rule_in_cooldown(rule.rule_id):
                    continue
                
                # 檢查每日調整次數限制
                if self._check_daily_adjustment_limit(rule.rule_id, rule.max_adjustments_per_day):
                    continue
                
                # 評估規則條件
                if self._evaluate_rule_condition(rule, market_condition):
                    triggered_rules.append(rule)
            
            # 按優先級排序
            triggered_rules.sort(key=lambda x: x.priority, reverse=True)
            
            logger.debug(f"🔍 觸發 {len(triggered_rules)} 個適應性規則")
            
        except Exception as e:
            logger.error(f"❌ 評估適應性規則失敗: {e}")
        
        return triggered_rules
    
    def _evaluate_rule_condition(self, rule: AdaptationRule, 
                               market_condition: MarketCondition) -> bool:
        """評估規則條件"""
        try:
            # 創建評估上下文
            context = {
                'market_regime': market_condition.market_regime,
                'price_change_1h': market_condition.price_change_1h,
                'price_change_24h': market_condition.price_change_24h,
                'price_change_7d': market_condition.price_change_7d,
                'price_change_30d': market_condition.price_change_30d,
                'volatility_1d': market_condition.volatility_1d,
                'volatility_7d': market_condition.volatility_7d,
                'rsi_14': market_condition.rsi_14,
                'trend_strength': market_condition.trend_strength,
                'BEAR_MARKET': MarketRegime.BEAR_MARKET,
                'BULL_MARKET': MarketRegime.BULL_MARKET,
                'SIDEWAYS_MARKET': MarketRegime.SIDEWAYS_MARKET,
                'VOLATILE_MARKET': MarketRegime.VOLATILE_MARKET,
                'CRASH_MARKET': MarketRegime.CRASH_MARKET
            }
            
            # 安全評估條件
            try:
                result = eval(rule.condition, {"__builtins__": {}}, context)
                return bool(result)
            except Exception as eval_error:
                logger.warning(f"⚠️ 規則條件評估錯誤 {rule.rule_id}: {eval_error}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 評估規則條件失敗: {e}")
            return False
    
    def _is_rule_in_cooldown(self, rule_id: str) -> bool:
        """檢查規則是否在冷卻期"""
        try:
            # 查找最近的執行記錄
            recent_events = [
                event for event in self.adaptation_history[-100:]
                if event.rule_id == rule_id and event.success
            ]
            
            if not recent_events:
                return False
            
            # 獲取規則的冷卻時間
            rule = next((r for r in self.adaptation_rules if r.rule_id == rule_id), None)
            if not rule:
                return False
            
            # 檢查最近執行時間
            last_execution = max(recent_events, key=lambda x: x.timestamp)
            cooldown_end = last_execution.timestamp + timedelta(hours=rule.cooldown_hours)
            
            return datetime.now() < cooldown_end
            
        except Exception as e:
            logger.error(f"❌ 檢查規則冷卻期失敗: {e}")
            return True  # 安全起見，返回True
    
    def _check_daily_adjustment_limit(self, rule_id: str, max_per_day: int) -> bool:
        """檢查每日調整次數限制"""
        try:
            today = datetime.now().date()
            
            # 統計今日執行次數
            today_executions = [
                event for event in self.adaptation_history
                if (event.rule_id == rule_id and 
                    event.success and 
                    event.timestamp.date() == today)
            ]
            
            return len(today_executions) >= max_per_day
            
        except Exception as e:
            logger.error(f"❌ 檢查每日調整限制失敗: {e}")
            return True  # 安全起見，返回True
    
    def _generate_adaptation_recommendations(self, triggered_rules: List[AdaptationRule],
                                           market_condition: MarketCondition,
                                           current_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成適應性建議"""
        recommendations = []
        
        try:
            for rule in triggered_rules:
                recommendation = self._create_adaptation_recommendation(
                    rule, market_condition, current_config
                )
                if recommendation:
                    recommendations.append(recommendation)
            
            logger.debug(f"💡 生成 {len(recommendations)} 個適應性建議")
            
        except Exception as e:
            logger.error(f"❌ 生成適應性建議失敗: {e}")
        
        return recommendations
    
    def _create_adaptation_recommendation(self, rule: AdaptationRule,
                                        market_condition: MarketCondition,
                                        current_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """創建適應性建議"""
        try:
            recommendation = {
                'rule_id': rule.rule_id,
                'rule_name': rule.name,
                'action': rule.action,
                'priority': rule.priority,
                'confidence': 0.7,  # 默認信心度
                'reason': f"觸發規則: {rule.name}",
                'old_value': None,
                'new_value': None,
                'adjustment_factor': 1.0
            }
            
            # 根據動作類型計算具體調整
            if rule.action == AdaptationAction.INCREASE_AMOUNT:
                adjustment_factor = self._calculate_amount_adjustment_factor(
                    market_condition, increase=True
                )
                current_amount = current_config.get('base_amount', 5000)
                new_amount = current_amount * adjustment_factor
                
                recommendation.update({
                    'old_value': current_amount,
                    'new_value': min(new_amount, current_amount * self.adaptation_config['max_amount_adjustment']),
                    'adjustment_factor': adjustment_factor,
                    'confidence': min(0.9, 0.5 + market_condition.trend_strength * 0.4)
                })
                
            elif rule.action == AdaptationAction.DECREASE_AMOUNT:
                adjustment_factor = self._calculate_amount_adjustment_factor(
                    market_condition, increase=False
                )
                current_amount = current_config.get('base_amount', 5000)
                new_amount = current_amount * adjustment_factor
                
                recommendation.update({
                    'old_value': current_amount,
                    'new_value': max(new_amount, current_amount * 0.5),  # 最少減半
                    'adjustment_factor': adjustment_factor,
                    'confidence': min(0.8, 0.5 + market_condition.trend_strength * 0.3)
                })
                
            elif rule.action == AdaptationAction.INCREASE_FREQUENCY:
                current_hours = self._get_frequency_hours(current_config.get('frequency', 'daily'))
                new_hours = max(1, current_hours * (1 - self.adaptation_config['max_frequency_adjustment']))
                
                recommendation.update({
                    'old_value': current_hours,
                    'new_value': new_hours,
                    'confidence': 0.6
                })
                
            elif rule.action == AdaptationAction.DECREASE_FREQUENCY:
                current_hours = self._get_frequency_hours(current_config.get('frequency', 'daily'))
                new_hours = current_hours * (1 + self.adaptation_config['max_frequency_adjustment'])
                
                recommendation.update({
                    'old_value': current_hours,
                    'new_value': min(new_hours, 168),  # 最多一週一次
                    'confidence': 0.5
                })
                
            elif rule.action == AdaptationAction.EMERGENCY_STOP:
                recommendation.update({
                    'old_value': 'active',
                    'new_value': 'stopped',
                    'confidence': 0.9,
                    'reason': f"緊急停止: {rule.name} - 市場條件惡化"
                })
            
            return recommendation
            
        except Exception as e:
            logger.error(f"❌ 創建適應性建議失敗: {e}")
            return None
    
    def _calculate_amount_adjustment_factor(self, market_condition: MarketCondition, 
                                          increase: bool) -> float:
        """計算金額調整因子"""
        try:
            base_factor = 1.0
            
            if increase:
                # 增加金額的因子計算
                if market_condition.market_regime == MarketRegime.CRASH_MARKET:
                    base_factor = 1.8  # 崩盤時大幅增加
                elif market_condition.market_regime == MarketRegime.BEAR_MARKET:
                    base_factor = 1.5  # 熊市時適度增加
                elif market_condition.rsi_14 < 30:
                    base_factor = 1.3  # RSI超賣時增加
                else:
                    base_factor = 1.2  # 默認小幅增加
                
                # 基於波動率調整
                if market_condition.volatility_7d > 0.08:
                    base_factor *= 1.1
                
            else:
                # 減少金額的因子計算
                if market_condition.market_regime == MarketRegime.BULL_MARKET:
                    base_factor = 0.7  # 牛市時減少
                elif market_condition.rsi_14 > 70:
                    base_factor = 0.8  # RSI超買時減少
                else:
                    base_factor = 0.9  # 默認小幅減少
            
            # 限制調整範圍
            if increase:
                return min(base_factor, self.adaptation_config['max_amount_adjustment'])
            else:
                return max(base_factor, 1.0 / self.adaptation_config['max_amount_adjustment'])
                
        except Exception as e:
            logger.error(f"❌ 計算金額調整因子失敗: {e}")
            return 1.0
    
    def _get_frequency_hours(self, frequency: str) -> int:
        """獲取頻率對應的小時數"""
        frequency_map = {
            'hourly': 1,
            'daily': 24,
            'weekly': 168,
            'monthly': 720
        }
        return frequency_map.get(frequency, 24)
    
    def _assess_adaptation_risks(self, recommendations: List[Dict[str, Any]], 
                               market_condition: MarketCondition) -> Dict[str, Any]:
        """評估適應性風險"""
        try:
            if not recommendations:
                return {'overall_risk': 0.3, 'confidence': 0.7, 'risks': []}
            
            risks = []
            risk_scores = []
            
            for rec in recommendations:
                risk_score = 0.5  # 基礎風險
                
                # 評估動作風險
                if rec['action'] == AdaptationAction.EMERGENCY_STOP:
                    risk_score = 0.2  # 緊急停止風險較低
                elif rec['action'] in [AdaptationAction.INCREASE_AMOUNT, AdaptationAction.DECREASE_AMOUNT]:
                    adjustment_ratio = rec.get('new_value', 1) / max(rec.get('old_value', 1), 1)
                    if adjustment_ratio > 1.5 or adjustment_ratio < 0.7:
                        risk_score = 0.7  # 大幅調整風險較高
                    else:
                        risk_score = 0.4  # 適度調整風險較低
                
                # 基於市場條件調整風險
                if market_condition.volatility_7d > 0.1:
                    risk_score += 0.2  # 高波動增加風險
                
                if market_condition.trend_strength < 0.3:
                    risk_score += 0.1  # 趨勢不明確增加風險
                
                risk_scores.append(min(1.0, risk_score))
                
                if risk_score > 0.6:
                    risks.append(f"{rec['rule_name']}: 調整幅度較大")
            
            overall_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.5
            confidence = max(0.3, 1.0 - overall_risk)
            
            return {
                'overall_risk': overall_risk,
                'confidence': confidence,
                'risks': risks,
                'risk_scores': risk_scores
            }
            
        except Exception as e:
            logger.error(f"❌ 評估適應性風險失敗: {e}")
            return {'overall_risk': 0.8, 'confidence': 0.3, 'risks': ['風險評估失敗']}
    
    def _make_final_adaptation_decisions(self, recommendations: List[Dict[str, Any]], 
                                       risk_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """制定最終適應性決策"""
        try:
            final_adaptations = []
            overall_risk = risk_assessment.get('overall_risk', 0.5)
            
            # 如果整體風險過高，只執行高優先級和低風險的調整
            if overall_risk > 0.7:
                logger.warning("⚠️ 整體風險較高，僅執行關鍵調整")
                recommendations = [
                    rec for rec in recommendations 
                    if rec['priority'] >= 8 or rec['action'] == AdaptationAction.EMERGENCY_STOP
                ]
            
            for i, rec in enumerate(recommendations):
                # 檢查個別風險
                individual_risk = risk_assessment.get('risk_scores', [0.5])[i] if i < len(risk_assessment.get('risk_scores', [])) else 0.5
                
                if individual_risk > 0.8:
                    logger.warning(f"⚠️ 跳過高風險調整: {rec['rule_name']}")
                    continue
                
                # 調整信心度
                adjusted_confidence = rec['confidence'] * (1.0 - individual_risk * 0.3)
                rec['confidence'] = max(0.3, adjusted_confidence)
                
                # 添加風險信息
                rec['risk_score'] = individual_risk
                rec['approved'] = True
                
                final_adaptations.append(rec)
            
            logger.info(f"✅ 最終批准 {len(final_adaptations)} 個適應性調整")
            
            return final_adaptations
            
        except Exception as e:
            logger.error(f"❌ 制定最終適應性決策失敗: {e}")
            return []
    
    def _update_adaptation_history(self, market_condition: MarketCondition, 
                                 adaptations: List[Dict[str, Any]]):
        """更新適應性歷史"""
        try:
            # 更新市場條件歷史
            self.market_conditions_history.append(market_condition)
            if len(self.market_conditions_history) > 1000:
                self.market_conditions_history = self.market_conditions_history[-500:]
            
            # 更新適應性事件歷史
            for adaptation in adaptations:
                event = AdaptationEvent(
                    event_id=f"adapt_{int(datetime.now().timestamp())}_{adaptation['rule_id']}",
                    timestamp=datetime.now(),
                    pair=market_condition.pair,
                    rule_id=adaptation['rule_id'],
                    action=adaptation['action'],
                    reason=adaptation['reason'],
                    old_value=adaptation.get('old_value'),
                    new_value=adaptation.get('new_value'),
                    confidence=adaptation['confidence'],
                    success=adaptation.get('approved', False)
                )
                
                self.adaptation_history.append(event)
            
            # 保持歷史記錄在合理範圍內
            if len(self.adaptation_history) > 1000:
                self.adaptation_history = self.adaptation_history[-500:]
            
            # 更新統計
            self._update_adaptation_stats()
            
        except Exception as e:
            logger.error(f"❌ 更新適應性歷史失敗: {e}")
    
    def _update_adaptation_stats(self):
        """更新適應性統計"""
        try:
            if not self.adaptation_history:
                return
            
            recent_events = self.adaptation_history[-100:]  # 最近100個事件
            
            self.adaptation_stats.update({
                'total_adaptations': len(self.adaptation_history),
                'successful_adaptations': sum(1 for e in recent_events if e.success),
                'frequency_adjustments': sum(1 for e in recent_events 
                                           if e.action in [AdaptationAction.INCREASE_FREQUENCY, 
                                                         AdaptationAction.DECREASE_FREQUENCY]),
                'amount_adjustments': sum(1 for e in recent_events 
                                        if e.action in [AdaptationAction.INCREASE_AMOUNT, 
                                                      AdaptationAction.DECREASE_AMOUNT]),
                'emergency_stops': sum(1 for e in recent_events 
                                     if e.action == AdaptationAction.EMERGENCY_STOP),
                'avg_adaptation_confidence': sum(e.confidence for e in recent_events) / len(recent_events) if recent_events else 0.0
            })
            
        except Exception as e:
            logger.error(f"❌ 更新適應性統計失敗: {e}")


# 創建DCA市場適應性機制實例
def create_dca_market_adaptation(ai_coordinator=None) -> DCAMarketAdaptation:
    """創建DCA市場適應性機制實例"""
    return DCAMarketAdaptation(ai_coordinator)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_dca_adaptation():
        """測試DCA市場適應性機制"""
        print("🧪 測試DCA市場適應性機制...")
        
        adaptation = create_dca_market_adaptation()
        
        test_market_data = {
            'current_price': 3200000,
            'price_change_1h': -0.03,
            'price_change_24h': -0.12,
            'price_change_7d': -0.18,
            'price_change_30d': -0.25,
            'volatility': 0.08,
            'volatility_7d': 0.10,
            'volume_ratio': 1.5,
            'rsi_14': 28
        }
        
        current_config = {
            'base_amount': 5000,
            'frequency': 'daily'
        }
        
        result = await adaptation.analyze_market_adaptation(
            "BTCTWD", test_market_data, current_config
        )
        
        print(f"✅ 適應性分析結果:")
        print(f"   市場狀態: {result['market_condition'].market_regime.value}")
        print(f"   觸發規則: {result['triggered_rules']} 個")
        print(f"   適應性調整: {len(result['adaptations'])} 個")
        print(f"   風險水平: {result['risk_level']:.2f}")
        print(f"   信心度: {result['confidence']:.2f}")
        
        for adaptation_rec in result['adaptations']:
            print(f"   - {adaptation_rec['rule_name']}: {adaptation_rec['action'].value}")
            print(f"     調整: {adaptation_rec.get('old_value')} -> {adaptation_rec.get('new_value')}")
            print(f"     信心度: {adaptation_rec['confidence']:.2f}")
        
        print("🎉 DCA市場適應性機制測試完成！")
    
    asyncio.run(test_dca_adaptation())