#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
風險管理器 - 多層風險控制系統
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """風險等級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskAction(Enum):
    """風險控制動作"""
    ALLOW = "allow"
    REDUCE = "reduce"
    BLOCK = "block"
    EMERGENCY_STOP = "emergency_stop"

@dataclass
class RiskMetrics:
    """風險指標"""
    max_drawdown: float
    current_drawdown: float
    daily_pnl: float
    weekly_pnl: float
    win_rate: float
    avg_trade_duration: float
    position_concentration: float
    leverage_ratio: float
    volatility_exposure: float

@dataclass
class RiskRule:
    """風險規則"""
    name: str
    description: str
    threshold: float
    action: RiskAction
    enabled: bool = True

@dataclass
class RiskAlert:
    """風險警報"""
    alert_id: str
    risk_type: str
    level: RiskLevel
    message: str
    current_value: float
    threshold: float
    timestamp: datetime
    action_taken: Optional[str] = None

class RiskManager:
    """風險管理器"""
    
    def __init__(self, initial_balance: float = 100000.0):
        """
        初始化風險管理器
        
        Args:
            initial_balance: 初始資金
        """
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.peak_balance = initial_balance
        
        # 風險規則配置
        self.risk_rules = self._initialize_risk_rules()
        
        # 風險統計
        self.risk_stats = {
            'total_alerts': 0,
            'critical_alerts': 0,
            'emergency_stops': 0,
            'trades_blocked': 0,
            'risk_score': 0.0
        }
        
        # 交易歷史記錄
        self.trade_history = []
        self.daily_pnl_history = []
        self.risk_alerts = []
        
        # 動態風險參數
        self.dynamic_risk_params = {
            'volatility_multiplier': 1.0,
            'confidence_threshold': 0.6,
            'max_position_size': 0.05,
            'stop_loss_ratio': 0.02,
            'daily_loss_limit': 0.05
        }
        
        logger.info("🛡️ 風險管理器初始化完成")
    
    def _initialize_risk_rules(self) -> List[RiskRule]:
        """初始化風險規則"""
        return [
            # 資金管理規則
            RiskRule("最大單筆交易", "單筆交易不超過總資金5%", 0.05, RiskAction.BLOCK),
            RiskRule("最大總倉位", "總倉位不超過總資金30%", 0.30, RiskAction.REDUCE),
            RiskRule("最大回撤", "最大回撤不超過10%", 0.10, RiskAction.EMERGENCY_STOP),
            RiskRule("日虧損限制", "單日虧損不超過5%", 0.05, RiskAction.BLOCK),
            RiskRule("週虧損限制", "單週虧損不超過15%", 0.15, RiskAction.EMERGENCY_STOP),
            
            # 交易頻率規則
            RiskRule("最大持倉數", "同時持倉不超過3個", 3, RiskAction.BLOCK),
            RiskRule("連續虧損", "連續虧損不超過5次", 5, RiskAction.REDUCE),
            RiskRule("日交易次數", "單日交易不超過20次", 20, RiskAction.BLOCK),
            
            # 市場風險規則
            RiskRule("高波動限制", "高波動期間降低倉位", 0.05, RiskAction.REDUCE),
            RiskRule("低信心度", "AI信心度過低時阻止交易", 0.5, RiskAction.BLOCK),
            RiskRule("異常價格", "價格異常波動時暫停交易", 0.1, RiskAction.BLOCK),
        ]
    
    async def assess_trade_risk(self, ai_decision: Dict[str, Any], 
                              market_data: Dict[str, Any],
                              account_status: Dict[str, Any]) -> Dict[str, Any]:
        """
        評估交易風險 - 增強版本
        
        Args:
            ai_decision: AI決策
            market_data: 市場數據
            account_status: 賬戶狀態
            
        Returns:
            風險評估結果
        """
        try:
            logger.info("🔍 開始增強風險評估...")
            
            # 更新當前狀態
            self._update_current_status(account_status)
            
            # 計算風險指標
            risk_metrics = self._calculate_risk_metrics(account_status, market_data)
            
            # 基於AI信心度的動態風險調整
            confidence_adjustment = self._calculate_confidence_based_adjustment(ai_decision)
            
            # 檢查異常交易模式
            anomaly_detection = self._detect_trading_anomalies(ai_decision, market_data, account_status)
            
            # 智能倉位大小計算
            intelligent_position_size = self._calculate_intelligent_position_size(
                ai_decision, market_data, account_status, risk_metrics
            )
            
            # 動態止損止盈計算
            dynamic_stops = self._calculate_dynamic_stops(ai_decision, market_data, risk_metrics)
            
            # 檢查所有風險規則
            risk_violations = []
            overall_risk_level = RiskLevel.LOW
            recommended_action = RiskAction.ALLOW
            
            for rule in self.risk_rules:
                if not rule.enabled:
                    continue
                
                violation = self._check_enhanced_risk_rule(
                    rule, ai_decision, market_data, account_status, 
                    risk_metrics, confidence_adjustment
                )
                
                if violation:
                    risk_violations.append(violation)
                    
                    # 更新整體風險等級和建議動作
                    if violation['action'] == RiskAction.EMERGENCY_STOP:
                        overall_risk_level = RiskLevel.CRITICAL
                        recommended_action = RiskAction.EMERGENCY_STOP
                    elif violation['action'] == RiskAction.BLOCK and recommended_action != RiskAction.EMERGENCY_STOP:
                        overall_risk_level = RiskLevel.HIGH
                        recommended_action = RiskAction.BLOCK
                    elif violation['action'] == RiskAction.REDUCE and recommended_action == RiskAction.ALLOW:
                        overall_risk_level = RiskLevel.MEDIUM
                        recommended_action = RiskAction.REDUCE
            
            # 添加異常檢測結果
            if anomaly_detection['is_anomalous']:
                risk_violations.append({
                    'rule': '異常交易檢測',
                    'current_value': anomaly_detection['anomaly_score'],
                    'threshold': anomaly_detection['threshold'],
                    'action': RiskAction.BLOCK,
                    'message': f"檢測到異常交易模式: {anomaly_detection['anomaly_type']}"
                })
                if recommended_action == RiskAction.ALLOW:
                    recommended_action = RiskAction.BLOCK
                    overall_risk_level = RiskLevel.HIGH
            
            # 動態調整風險參數
            self._adjust_enhanced_risk_params(risk_metrics, market_data, ai_decision)
            
            # 生成增強風險評估結果
            risk_assessment = {
                'overall_risk_level': overall_risk_level.value,
                'recommended_action': recommended_action.value,
                'risk_score': self._calculate_enhanced_risk_score(risk_metrics, risk_violations, confidence_adjustment),
                'risk_metrics': risk_metrics.__dict__,
                'violations': risk_violations,
                'dynamic_params': self.dynamic_risk_params.copy(),
                'confidence_adjustment': confidence_adjustment,
                'intelligent_position_size': intelligent_position_size,
                'dynamic_stops': dynamic_stops,
                'anomaly_detection': anomaly_detection,
                'assessment_time': datetime.now(),
                'approved': recommended_action in [RiskAction.ALLOW, RiskAction.REDUCE]
            }
            
            # 記錄風險警報
            if risk_violations:
                self._record_risk_alerts(risk_violations, overall_risk_level)
            
            # 更新統計
            self._update_risk_stats(risk_assessment)
            
            logger.info(f"✅ 增強風險評估完成: {overall_risk_level.value} - {recommended_action.value}")
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"❌ 增強風險評估失敗: {e}")
            return {
                'overall_risk_level': RiskLevel.CRITICAL.value,
                'recommended_action': RiskAction.EMERGENCY_STOP.value,
                'approved': False,
                'error': str(e)
            }
    
    def _update_current_status(self, account_status: Dict[str, Any]):
        """更新當前狀態"""
        try:
            self.current_balance = account_status.get('total_equity', self.current_balance)
            self.peak_balance = max(self.peak_balance, self.current_balance)
            
        except Exception as e:
            logger.error(f"❌ 更新當前狀態失敗: {e}")
    
    def _calculate_risk_metrics(self, account_status: Dict[str, Any], 
                              market_data: Dict[str, Any]) -> RiskMetrics:
        """計算風險指標"""
        try:
            # 計算回撤
            current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
            max_drawdown = max(current_drawdown, 
                             max([dd.get('drawdown', 0) for dd in self.daily_pnl_history[-30:]], default=0))
            
            # 計算盈虧
            daily_pnl = self._calculate_daily_pnl()
            weekly_pnl = self._calculate_weekly_pnl()
            
            # 計算勝率
            win_rate = self._calculate_win_rate()
            
            # 計算平均交易時間
            avg_trade_duration = self._calculate_avg_trade_duration()
            
            # 計算倉位集中度
            position_concentration = self._calculate_position_concentration(account_status)
            
            # 計算槓桿比率
            leverage_ratio = account_status.get('margin_used', 0) / max(account_status.get('total_equity', 1), 1)
            
            # 計算波動率暴露
            volatility_exposure = self._calculate_volatility_exposure(market_data, account_status)
            
            return RiskMetrics(
                max_drawdown=max_drawdown,
                current_drawdown=current_drawdown,
                daily_pnl=daily_pnl,
                weekly_pnl=weekly_pnl,
                win_rate=win_rate,
                avg_trade_duration=avg_trade_duration,
                position_concentration=position_concentration,
                leverage_ratio=leverage_ratio,
                volatility_exposure=volatility_exposure
            )
            
        except Exception as e:
            logger.error(f"❌ 計算風險指標失敗: {e}")
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    def _calculate_confidence_based_adjustment(self, ai_decision: Dict[str, Any]) -> Dict[str, Any]:
        """基於AI信心度的動態風險調整"""
        try:
            confidence = ai_decision.get('confidence', 0.5)
            
            # 信心度調整係數
            if confidence >= 0.8:
                # 高信心度：適度放寬風險限制
                adjustment = {
                    'position_size_multiplier': 1.2,
                    'stop_loss_multiplier': 1.1,
                    'risk_tolerance_multiplier': 1.15,
                    'confidence_category': 'high'
                }
            elif confidence >= 0.6:
                # 中等信心度：標準風險控制
                adjustment = {
                    'position_size_multiplier': 1.0,
                    'stop_loss_multiplier': 1.0,
                    'risk_tolerance_multiplier': 1.0,
                    'confidence_category': 'medium'
                }
            elif confidence >= 0.4:
                # 低信心度：收緊風險控制
                adjustment = {
                    'position_size_multiplier': 0.7,
                    'stop_loss_multiplier': 0.8,
                    'risk_tolerance_multiplier': 0.8,
                    'confidence_category': 'low'
                }
            else:
                # 極低信心度：嚴格風險控制
                adjustment = {
                    'position_size_multiplier': 0.5,
                    'stop_loss_multiplier': 0.6,
                    'risk_tolerance_multiplier': 0.6,
                    'confidence_category': 'very_low'
                }
            
            adjustment['confidence_score'] = confidence
            return adjustment
            
        except Exception as e:
            logger.error(f"❌ 計算信心度調整失敗: {e}")
            return {
                'position_size_multiplier': 0.8,
                'stop_loss_multiplier': 0.8,
                'risk_tolerance_multiplier': 0.8,
                'confidence_category': 'default',
                'confidence_score': 0.5
            }
    
    def _detect_trading_anomalies(self, ai_decision: Dict[str, Any], 
                                market_data: Dict[str, Any],
                                account_status: Dict[str, Any]) -> Dict[str, Any]:
        """檢測異常交易模式"""
        try:
            anomaly_score = 0.0
            anomaly_types = []
            
            # 1. 檢測頻繁交易異常
            recent_trades = [t for t in self.trade_history 
                           if t.get('timestamp', datetime.now()) >= datetime.now() - timedelta(hours=1)]
            if len(recent_trades) > 10:  # 1小時內超過10筆交易
                anomaly_score += 0.3
                anomaly_types.append('頻繁交易')
            
            # 2. 檢測連續虧損後的大額交易
            recent_losses = [t for t in self.trade_history[-5:] if t.get('pnl', 0) < 0]
            if len(recent_losses) >= 3:  # 連續3筆虧損
                proposed_size = self._calculate_trade_size_ratio(ai_decision, market_data, account_status)
                if proposed_size > self.dynamic_risk_params['max_position_size'] * 1.5:
                    anomaly_score += 0.4
                    anomaly_types.append('虧損後大額交易')
            
            # 3. 檢測極端市場條件下的交易
            volatility_level = market_data.get('volatility_level', '中')
            if volatility_level == '高' and ai_decision.get('final_decision') != 'HOLD':
                price_change = market_data.get('price_change_24h', 0)
                if abs(price_change) > 0.1:  # 24小時價格變化超過10%
                    anomaly_score += 0.2
                    anomaly_types.append('極端市場條件交易')
            
            # 4. 檢測信心度與決策不匹配
            confidence = ai_decision.get('confidence', 0.5)
            decision = ai_decision.get('final_decision', 'HOLD')
            if decision in ['BUY', 'SELL'] and confidence < 0.3:
                anomaly_score += 0.3
                anomaly_types.append('低信心度強決策')
            
            # 5. 檢測賬戶狀態異常
            current_drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
            if current_drawdown > 0.08 and ai_decision.get('final_decision') != 'HOLD':  # 回撤超過8%還要交易
                anomaly_score += 0.4
                anomaly_types.append('高回撤期間交易')
            
            return {
                'is_anomalous': anomaly_score > 0.5,
                'anomaly_score': anomaly_score,
                'anomaly_type': ', '.join(anomaly_types) if anomaly_types else '無異常',
                'threshold': 0.5,
                'detected_patterns': anomaly_types
            }
            
        except Exception as e:
            logger.error(f"❌ 檢測交易異常失敗: {e}")
            return {
                'is_anomalous': False,
                'anomaly_score': 0.0,
                'anomaly_type': '檢測失敗',
                'threshold': 0.5,
                'detected_patterns': []
            }
    
    def _calculate_intelligent_position_size(self, ai_decision: Dict[str, Any],
                                           market_data: Dict[str, Any],
                                           account_status: Dict[str, Any],
                                           risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """智能倉位大小計算"""
        try:
            if ai_decision.get('final_decision') == 'HOLD':
                return {
                    'recommended_size': 0.0,
                    'size_ratio': 0.0,
                    'reasoning': '持有決策，無需倉位',
                    'risk_adjusted': True
                }
            
            # 基礎倉位大小
            base_size_ratio = self.dynamic_risk_params['max_position_size']
            
            # 信心度調整
            confidence = ai_decision.get('confidence', 0.5)
            confidence_multiplier = min(confidence / 0.6, 1.5)  # 最大1.5倍
            
            # 風險調整
            risk_multiplier = 1.0
            
            # 基於回撤調整
            if risk_metrics.current_drawdown > 0.05:
                risk_multiplier *= (1 - risk_metrics.current_drawdown)
            
            # 基於勝率調整
            if risk_metrics.win_rate < 0.4:
                risk_multiplier *= 0.8
            elif risk_metrics.win_rate > 0.6:
                risk_multiplier *= 1.1
            
            # 基於波動率調整
            volatility_level = market_data.get('volatility_level', '中')
            volatility_multipliers = {'低': 1.1, '中': 1.0, '高': 0.7}
            risk_multiplier *= volatility_multipliers.get(volatility_level, 1.0)
            
            # 基於市場趨勢調整
            price_trend = market_data.get('price_trend', '橫盤')
            if price_trend == '強勢上漲' and ai_decision.get('final_decision') == 'BUY':
                risk_multiplier *= 1.1
            elif price_trend == '強勢下跌' and ai_decision.get('final_decision') == 'SELL':
                risk_multiplier *= 1.1
            
            # 計算最終倉位大小
            final_size_ratio = base_size_ratio * confidence_multiplier * risk_multiplier
            
            # 應用硬性限制
            max_allowed = min(0.1, self.dynamic_risk_params['max_position_size'] * 2)  # 最大不超過10%
            final_size_ratio = min(final_size_ratio, max_allowed)
            final_size_ratio = max(final_size_ratio, 0.005)  # 最小0.5%
            
            # 計算實際金額
            available_balance = account_status.get('available_balance', 0)
            recommended_amount = available_balance * final_size_ratio
            
            return {
                'recommended_size': recommended_amount,
                'size_ratio': final_size_ratio,
                'base_ratio': base_size_ratio,
                'confidence_multiplier': confidence_multiplier,
                'risk_multiplier': risk_multiplier,
                'reasoning': f'信心度{confidence:.1%} × 風險調整{risk_multiplier:.2f} = {final_size_ratio:.1%}',
                'risk_adjusted': True,
                'max_allowed': max_allowed
            }
            
        except Exception as e:
            logger.error(f"❌ 計算智能倉位大小失敗: {e}")
            return {
                'recommended_size': 0.0,
                'size_ratio': 0.0,
                'reasoning': '計算失敗，建議暫停交易',
                'risk_adjusted': False
            }
    
    def _calculate_dynamic_stops(self, ai_decision: Dict[str, Any],
                               market_data: Dict[str, Any],
                               risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """計算動態止損止盈"""
        try:
            if ai_decision.get('final_decision') == 'HOLD':
                return {
                    'stop_loss': None,
                    'take_profit': None,
                    'reasoning': '持有決策，無需設置止損止盈'
                }
            
            current_price = market_data.get('current_price', 0)
            if current_price <= 0:
                return {
                    'stop_loss': None,
                    'take_profit': None,
                    'reasoning': '價格數據無效'
                }
            
            # 基礎止損比例
            base_stop_loss_ratio = self.dynamic_risk_params['stop_loss_ratio']
            
            # 基於信心度調整止損
            confidence = ai_decision.get('confidence', 0.5)
            if confidence >= 0.8:
                stop_loss_ratio = base_stop_loss_ratio * 1.2  # 高信心度，放寬止損
            elif confidence >= 0.6:
                stop_loss_ratio = base_stop_loss_ratio
            else:
                stop_loss_ratio = base_stop_loss_ratio * 0.8  # 低信心度，收緊止損
            
            # 基於波動率調整
            volatility_level = market_data.get('volatility_level', '中')
            if volatility_level == '高':
                stop_loss_ratio *= 1.5  # 高波動率，放寬止損
            elif volatility_level == '低':
                stop_loss_ratio *= 0.8  # 低波動率，收緊止損
            
            # 基於歷史表現調整
            if risk_metrics.win_rate > 0.6:
                stop_loss_ratio *= 1.1  # 勝率高，稍微放寬
            elif risk_metrics.win_rate < 0.4:
                stop_loss_ratio *= 0.9  # 勝率低，稍微收緊
            
            # 計算止損止盈價格
            decision = ai_decision.get('final_decision')
            
            if decision == 'BUY':
                stop_loss_price = current_price * (1 - stop_loss_ratio)
                take_profit_price = current_price * (1 + stop_loss_ratio * 2)  # 風險收益比1:2
            elif decision == 'SELL':
                stop_loss_price = current_price * (1 + stop_loss_ratio)
                take_profit_price = current_price * (1 - stop_loss_ratio * 2)
            else:
                return {
                    'stop_loss': None,
                    'take_profit': None,
                    'reasoning': '未知決策類型'
                }
            
            # 跟蹤止損設置
            trailing_stop_enabled = confidence > 0.7 and volatility_level != '高'
            
            return {
                'stop_loss': {
                    'price': stop_loss_price,
                    'ratio': stop_loss_ratio,
                    'type': 'trailing' if trailing_stop_enabled else 'fixed'
                },
                'take_profit': {
                    'price': take_profit_price,
                    'ratio': stop_loss_ratio * 2,
                    'type': 'fixed'
                },
                'risk_reward_ratio': 2.0,
                'reasoning': f'基於信心度{confidence:.1%}和波動率{volatility_level}的動態止損',
                'confidence_adjusted': True,
                'volatility_adjusted': True
            }
            
        except Exception as e:
            logger.error(f"❌ 計算動態止損失敗: {e}")
            return {
                'stop_loss': None,
                'take_profit': None,
                'reasoning': f'計算失敗: {e}'
            }
    
    def _check_enhanced_risk_rule(self, rule: RiskRule, ai_decision: Dict[str, Any],
                                market_data: Dict[str, Any], account_status: Dict[str, Any],
                                risk_metrics: RiskMetrics, confidence_adjustment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """檢查增強版風險規則"""
        try:
            violation = None
            
            # 應用信心度調整
            risk_tolerance_multiplier = confidence_adjustment.get('risk_tolerance_multiplier', 1.0)
            adjusted_threshold = rule.threshold * risk_tolerance_multiplier
            
            if rule.name == "最大單筆交易":
                trade_size_ratio = self._calculate_trade_size_ratio(ai_decision, market_data, account_status)
                # 應用信心度調整
                position_multiplier = confidence_adjustment.get('position_size_multiplier', 1.0)
                effective_threshold = adjusted_threshold * position_multiplier
                
                if trade_size_ratio > effective_threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': trade_size_ratio,
                        'threshold': effective_threshold,
                        'original_threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"單筆交易比例 {trade_size_ratio:.1%} 超過調整後限制 {effective_threshold:.1%} (信心度調整: {confidence_adjustment['confidence_category']})"
                    }
            
            elif rule.name == "最大總倉位":
                if risk_metrics.leverage_ratio > adjusted_threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': risk_metrics.leverage_ratio,
                        'threshold': adjusted_threshold,
                        'original_threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"總倉位比例 {risk_metrics.leverage_ratio:.1%} 超過調整後限制 {adjusted_threshold:.1%}"
                    }
            
            elif rule.name == "最大回撤":
                if risk_metrics.current_drawdown > adjusted_threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': risk_metrics.current_drawdown,
                        'threshold': adjusted_threshold,
                        'original_threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"當前回撤 {risk_metrics.current_drawdown:.1%} 超過調整後限制 {adjusted_threshold:.1%}"
                    }
            
            elif rule.name == "日虧損限制":
                daily_loss_ratio = abs(min(risk_metrics.daily_pnl, 0)) / self.initial_balance
                if daily_loss_ratio > adjusted_threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': daily_loss_ratio,
                        'threshold': adjusted_threshold,
                        'original_threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"日虧損比例 {daily_loss_ratio:.1%} 超過調整後限制 {adjusted_threshold:.1%}"
                    }
            
            elif rule.name == "最大持倉數":
                positions_count = account_status.get('positions_count', 0)
                if ai_decision.get('final_decision') == 'BUY' and positions_count >= rule.threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': positions_count,
                        'threshold': rule.threshold,
                        'original_threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"持倉數量 {positions_count} 已達上限 {rule.threshold}"
                    }
            
            elif rule.name == "低信心度":
                confidence = ai_decision.get('confidence', 0)
                # 動態調整信心度閾值
                dynamic_threshold = max(rule.threshold, self.dynamic_risk_params['confidence_threshold'])
                if confidence < dynamic_threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': confidence,
                        'threshold': dynamic_threshold,
                        'original_threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"AI信心度 {confidence:.1%} 低於動態要求 {dynamic_threshold:.1%}"
                    }
            
            elif rule.name == "高波動限制":
                volatility_level = market_data.get('volatility_level', '中')
                if volatility_level == '高' and risk_metrics.volatility_exposure > adjusted_threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': risk_metrics.volatility_exposure,
                        'threshold': adjusted_threshold,
                        'original_threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"高波動期間，波動率暴露 {risk_metrics.volatility_exposure:.1%} 過高"
                    }
            
            # 新增：連續虧損檢查
            elif rule.name == "連續虧損":
                recent_trades = self.trade_history[-int(rule.threshold):]
                consecutive_losses = 0
                for trade in reversed(recent_trades):
                    if trade.get('pnl', 0) < 0:
                        consecutive_losses += 1
                    else:
                        break
                
                if consecutive_losses >= rule.threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': consecutive_losses,
                        'threshold': rule.threshold,
                        'original_threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"連續虧損 {consecutive_losses} 次，達到限制 {rule.threshold} 次"
                    }
            
            # 新增：日交易次數檢查
            elif rule.name == "日交易次數":
                today = datetime.now().date()
                daily_trades_count = sum(1 for t in self.trade_history 
                                       if t.get('timestamp', datetime.now()).date() == today)
                
                if ai_decision.get('final_decision') != 'HOLD' and daily_trades_count >= rule.threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': daily_trades_count,
                        'threshold': rule.threshold,
                        'original_threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"日交易次數 {daily_trades_count} 已達上限 {rule.threshold}"
                    }
            
            return violation
            
        except Exception as e:
            logger.error(f"❌ 檢查增強風險規則失敗 ({rule.name}): {e}")
            return None
    
    def _adjust_enhanced_risk_params(self, risk_metrics: RiskMetrics, 
                                   market_data: Dict[str, Any],
                                   ai_decision: Dict[str, Any]):
        """增強版動態風險參數調整"""
        try:
            # 基於回撤的動態調整
            if risk_metrics.current_drawdown > 0.08:  # 回撤超過8%
                self.dynamic_risk_params['max_position_size'] *= 0.6
                self.dynamic_risk_params['confidence_threshold'] = min(0.8, self.dynamic_risk_params['confidence_threshold'] + 0.15)
                self.dynamic_risk_params['daily_loss_limit'] *= 0.8
            elif risk_metrics.current_drawdown > 0.05:  # 回撤超過5%
                self.dynamic_risk_params['max_position_size'] *= 0.8
                self.dynamic_risk_params['confidence_threshold'] = min(0.75, self.dynamic_risk_params['confidence_threshold'] + 0.1)
            
            # 基於勝率的動態調整
            if risk_metrics.win_rate < 0.3:  # 勝率低於30%
                self.dynamic_risk_params['confidence_threshold'] = min(0.8, self.dynamic_risk_params['confidence_threshold'] + 0.1)
                self.dynamic_risk_params['stop_loss_ratio'] *= 0.8
                self.dynamic_risk_params['max_position_size'] *= 0.7
            elif risk_metrics.win_rate > 0.7:  # 勝率高於70%
                self.dynamic_risk_params['confidence_threshold'] = max(0.5, self.dynamic_risk_params['confidence_threshold'] - 0.05)
                self.dynamic_risk_params['max_position_size'] = min(0.08, self.dynamic_risk_params['max_position_size'] * 1.1)
            
            # 基於波動率的動態調整
            volatility_level = market_data.get('volatility_level', '中')
            if volatility_level == '高':
                self.dynamic_risk_params['volatility_multiplier'] = 0.6
                self.dynamic_risk_params['max_position_size'] *= 0.7
                self.dynamic_risk_params['stop_loss_ratio'] *= 1.3
            elif volatility_level == '低':
                self.dynamic_risk_params['volatility_multiplier'] = 1.3
                self.dynamic_risk_params['max_position_size'] = min(0.08, self.dynamic_risk_params['max_position_size'] * 1.1)
                self.dynamic_risk_params['stop_loss_ratio'] *= 0.9
            else:  # 中等波動率
                self.dynamic_risk_params['volatility_multiplier'] = 1.0
            
            # 基於AI信心度歷史的調整
            confidence = ai_decision.get('confidence', 0.5)
            if confidence < 0.4:  # 當前信心度很低
                self.dynamic_risk_params['confidence_threshold'] = min(0.7, self.dynamic_risk_params['confidence_threshold'] + 0.05)
            
            # 基於市場趨勢的調整
            price_trend = market_data.get('price_trend', '橫盤')
            if price_trend in ['強勢上漲', '強勢下跌']:
                # 強趨勢市場，可以適度放寬限制
                self.dynamic_risk_params['max_position_size'] = min(0.08, self.dynamic_risk_params['max_position_size'] * 1.05)
            elif price_trend == '震盪':
                # 震盪市場，收緊控制
                self.dynamic_risk_params['max_position_size'] *= 0.9
                self.dynamic_risk_params['stop_loss_ratio'] *= 0.9
            
            # 確保參數在合理範圍內
            self.dynamic_risk_params['max_position_size'] = max(0.005, min(self.dynamic_risk_params['max_position_size'], 0.1))
            self.dynamic_risk_params['confidence_threshold'] = max(0.4, min(self.dynamic_risk_params['confidence_threshold'], 0.85))
            self.dynamic_risk_params['stop_loss_ratio'] = max(0.01, min(self.dynamic_risk_params['stop_loss_ratio'], 0.05))
            self.dynamic_risk_params['daily_loss_limit'] = max(0.02, min(self.dynamic_risk_params['daily_loss_limit'], 0.08))
            self.dynamic_risk_params['volatility_multiplier'] = max(0.5, min(self.dynamic_risk_params['volatility_multiplier'], 1.5))
            
            logger.info(f"🔧 動態風險參數已調整: 最大倉位{self.dynamic_risk_params['max_position_size']:.1%}, 信心度閾值{self.dynamic_risk_params['confidence_threshold']:.1%}")
            
        except Exception as e:
            logger.error(f"❌ 調整增強風險參數失敗: {e}")
    
    def _calculate_enhanced_risk_score(self, risk_metrics: RiskMetrics, 
                                     violations: List[Dict[str, Any]],
                                     confidence_adjustment: Dict[str, Any]) -> float:
        """計算增強版風險分數 (0-100, 越高越危險)"""
        try:
            score = 0.0
            
            # 回撤風險 (25%)
            score += risk_metrics.current_drawdown * 250
            
            # 虧損風險 (20%)
            daily_loss_ratio = abs(min(risk_metrics.daily_pnl, 0)) / self.initial_balance
            score += daily_loss_ratio * 200
            
            # 倉位風險 (15%)
            score += risk_metrics.leverage_ratio * 150
            
            # 波動率風險 (15%)
            score += risk_metrics.volatility_exposure * 150
            
            # 信心度風險 (10%)
            confidence_score = confidence_adjustment.get('confidence_score', 0.5)
            confidence_risk = max(0, (0.6 - confidence_score) / 0.6) * 100  # 信心度低於60%開始計分
            score += confidence_risk
            
            # 違規風險 (10%)
            violation_score = len(violations) * 8
            critical_violations = sum(1 for v in violations if v.get('action') == RiskAction.EMERGENCY_STOP)
            high_violations = sum(1 for v in violations if v.get('action') == RiskAction.BLOCK)
            violation_score += critical_violations * 25 + high_violations * 15
            score += min(violation_score, 100)
            
            # 勝率風險 (5%)
            if risk_metrics.win_rate < 0.4:
                win_rate_risk = (0.4 - risk_metrics.win_rate) / 0.4 * 50
                score += win_rate_risk
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"❌ 計算增強風險分數失敗: {e}")
            return 60.0  # 返回中等風險分數
    
    def _check_risk_rule(self, rule: RiskRule, ai_decision: Dict[str, Any],
                        market_data: Dict[str, Any], account_status: Dict[str, Any],
                        risk_metrics: RiskMetrics) -> Optional[Dict[str, Any]]:
        """檢查單個風險規則"""
        try:
            violation = None
            
            if rule.name == "最大單筆交易":
                trade_size_ratio = self._calculate_trade_size_ratio(ai_decision, market_data, account_status)
                if trade_size_ratio > rule.threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': trade_size_ratio,
                        'threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"單筆交易比例 {trade_size_ratio:.1%} 超過限制 {rule.threshold:.1%}"
                    }
            
            elif rule.name == "最大總倉位":
                if risk_metrics.leverage_ratio > rule.threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': risk_metrics.leverage_ratio,
                        'threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"總倉位比例 {risk_metrics.leverage_ratio:.1%} 超過限制 {rule.threshold:.1%}"
                    }
            
            elif rule.name == "最大回撤":
                if risk_metrics.current_drawdown > rule.threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': risk_metrics.current_drawdown,
                        'threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"當前回撤 {risk_metrics.current_drawdown:.1%} 超過限制 {rule.threshold:.1%}"
                    }
            
            elif rule.name == "日虧損限制":
                daily_loss_ratio = abs(min(risk_metrics.daily_pnl, 0)) / self.initial_balance
                if daily_loss_ratio > rule.threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': daily_loss_ratio,
                        'threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"日虧損比例 {daily_loss_ratio:.1%} 超過限制 {rule.threshold:.1%}"
                    }
            
            elif rule.name == "最大持倉數":
                positions_count = account_status.get('positions_count', 0)
                if ai_decision.get('final_decision') == 'BUY' and positions_count >= rule.threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': positions_count,
                        'threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"持倉數量 {positions_count} 已達上限 {rule.threshold}"
                    }
            
            elif rule.name == "低信心度":
                confidence = ai_decision.get('confidence', 0)
                if confidence < rule.threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': confidence,
                        'threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"AI信心度 {confidence:.1%} 低於要求 {rule.threshold:.1%}"
                    }
            
            elif rule.name == "高波動限制":
                volatility_level = market_data.get('volatility_level', '中')
                if volatility_level == '高' and risk_metrics.volatility_exposure > rule.threshold:
                    violation = {
                        'rule': rule.name,
                        'current_value': risk_metrics.volatility_exposure,
                        'threshold': rule.threshold,
                        'action': rule.action,
                        'message': f"高波動期間，波動率暴露 {risk_metrics.volatility_exposure:.1%} 過高"
                    }
            
            return violation
            
        except Exception as e:
            logger.error(f"❌ 檢查風險規則失敗 ({rule.name}): {e}")
            return None
    
    def _calculate_trade_size_ratio(self, ai_decision: Dict[str, Any],
                                  market_data: Dict[str, Any],
                                  account_status: Dict[str, Any]) -> float:
        """計算交易大小比例"""
        try:
            if ai_decision.get('final_decision') == 'HOLD':
                return 0.0
            
            confidence = ai_decision.get('confidence', 0.6)
            current_price = market_data.get('current_price', 1)
            available_balance = account_status.get('available_balance', 0)
            
            # 模擬倉位計算邏輯
            base_position_ratio = self.dynamic_risk_params['max_position_size']
            confidence_multiplier = min(confidence / 0.6, 1.5)
            position_ratio = base_position_ratio * confidence_multiplier
            
            return position_ratio
            
        except Exception as e:
            logger.error(f"❌ 計算交易大小比例失敗: {e}")
            return 0.0
    
    def _calculate_daily_pnl(self) -> float:
        """計算日盈虧"""
        try:
            today = datetime.now().date()
            daily_trades = [t for t in self.trade_history 
                          if t.get('timestamp', datetime.now()).date() == today]
            
            return sum(t.get('pnl', 0) for t in daily_trades)
            
        except Exception as e:
            logger.error(f"❌ 計算日盈虧失敗: {e}")
            return 0.0
    
    def _calculate_weekly_pnl(self) -> float:
        """計算週盈虧"""
        try:
            week_ago = datetime.now() - timedelta(days=7)
            weekly_trades = [t for t in self.trade_history 
                           if t.get('timestamp', datetime.now()) >= week_ago]
            
            return sum(t.get('pnl', 0) for t in weekly_trades)
            
        except Exception as e:
            logger.error(f"❌ 計算週盈虧失敗: {e}")
            return 0.0
    
    def _calculate_win_rate(self) -> float:
        """計算勝率"""
        try:
            if not self.trade_history:
                return 0.0
            
            profitable_trades = sum(1 for t in self.trade_history if t.get('pnl', 0) > 0)
            total_trades = len(self.trade_history)
            
            return profitable_trades / total_trades if total_trades > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ 計算勝率失敗: {e}")
            return 0.0
    
    def _calculate_avg_trade_duration(self) -> float:
        """計算平均交易時間"""
        try:
            if not self.trade_history:
                return 0.0
            
            durations = [t.get('duration', 0) for t in self.trade_history if 'duration' in t]
            
            return sum(durations) / len(durations) if durations else 0.0
            
        except Exception as e:
            logger.error(f"❌ 計算平均交易時間失敗: {e}")
            return 0.0
    
    def _calculate_position_concentration(self, account_status: Dict[str, Any]) -> float:
        """計算倉位集中度"""
        try:
            positions_count = account_status.get('positions_count', 0)
            if positions_count == 0:
                return 0.0
            
            # 簡化計算：假設倉位均勻分布
            return 1.0 / positions_count if positions_count > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ 計算倉位集中度失敗: {e}")
            return 0.0
    
    def _calculate_volatility_exposure(self, market_data: Dict[str, Any],
                                     account_status: Dict[str, Any]) -> float:
        """計算波動率暴露"""
        try:
            volatility_level = market_data.get('volatility_level', '中')
            positions_count = account_status.get('positions_count', 0)
            
            # 簡化計算
            volatility_multiplier = {'低': 0.5, '中': 1.0, '高': 2.0}.get(volatility_level, 1.0)
            exposure = (positions_count / 10) * volatility_multiplier
            
            return min(exposure, 1.0)
            
        except Exception as e:
            logger.error(f"❌ 計算波動率暴露失敗: {e}")
            return 0.0
    
    def _adjust_dynamic_risk_params(self, risk_metrics: RiskMetrics, 
                                  market_data: Dict[str, Any]):
        """動態調整風險參數"""
        try:
            # 基於回撤調整
            if risk_metrics.current_drawdown > 0.05:  # 回撤超過5%
                self.dynamic_risk_params['max_position_size'] *= 0.8
                self.dynamic_risk_params['confidence_threshold'] += 0.1
            
            # 基於勝率調整
            if risk_metrics.win_rate < 0.4:  # 勝率低於40%
                self.dynamic_risk_params['confidence_threshold'] += 0.05
                self.dynamic_risk_params['stop_loss_ratio'] *= 0.8
            
            # 基於波動率調整
            volatility_level = market_data.get('volatility_level', '中')
            if volatility_level == '高':
                self.dynamic_risk_params['volatility_multiplier'] = 0.7
                self.dynamic_risk_params['max_position_size'] *= 0.8
            elif volatility_level == '低':
                self.dynamic_risk_params['volatility_multiplier'] = 1.2
            
            # 確保參數在合理範圍內
            self.dynamic_risk_params['max_position_size'] = max(0.01, 
                min(self.dynamic_risk_params['max_position_size'], 0.1))
            self.dynamic_risk_params['confidence_threshold'] = max(0.5, 
                min(self.dynamic_risk_params['confidence_threshold'], 0.9))
            
        except Exception as e:
            logger.error(f"❌ 調整動態風險參數失敗: {e}")
    
    def _calculate_risk_score(self, risk_metrics: RiskMetrics, 
                            violations: List[Dict[str, Any]]) -> float:
        """計算風險分數 (0-100, 越高越危險)"""
        try:
            score = 0.0
            
            # 回撤風險 (30%)
            score += risk_metrics.current_drawdown * 300
            
            # 虧損風險 (25%)
            daily_loss_ratio = abs(min(risk_metrics.daily_pnl, 0)) / self.initial_balance
            score += daily_loss_ratio * 250
            
            # 倉位風險 (20%)
            score += risk_metrics.leverage_ratio * 200
            
            # 波動率風險 (15%)
            score += risk_metrics.volatility_exposure * 150
            
            # 違規風險 (10%)
            violation_score = len(violations) * 10
            critical_violations = sum(1 for v in violations if v.get('action') == RiskAction.EMERGENCY_STOP)
            violation_score += critical_violations * 20
            score += violation_score
            
            return min(score, 100.0)
            
        except Exception as e:
            logger.error(f"❌ 計算風險分數失敗: {e}")
            return 50.0
    
    def _record_risk_alerts(self, violations: List[Dict[str, Any]], 
                          risk_level: RiskLevel):
        """記錄風險警報"""
        try:
            for violation in violations:
                alert = RiskAlert(
                    alert_id=f"RISK_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.risk_alerts)}",
                    risk_type=violation['rule'],
                    level=risk_level,
                    message=violation['message'],
                    current_value=violation['current_value'],
                    threshold=violation['threshold'],
                    timestamp=datetime.now(),
                    action_taken=violation['action'].value
                )
                
                self.risk_alerts.append(alert)
                
                # 記錄日誌
                if risk_level == RiskLevel.CRITICAL:
                    logger.critical(f"🚨 嚴重風險警報: {alert.message}")
                elif risk_level == RiskLevel.HIGH:
                    logger.warning(f"⚠️ 高風險警報: {alert.message}")
                else:
                    logger.info(f"ℹ️ 風險提醒: {alert.message}")
            
        except Exception as e:
            logger.error(f"❌ 記錄風險警報失敗: {e}")
    
    def _update_risk_stats(self, risk_assessment: Dict[str, Any]):
        """更新風險統計"""
        try:
            self.risk_stats['total_alerts'] += len(risk_assessment.get('violations', []))
            
            if risk_assessment['overall_risk_level'] == RiskLevel.CRITICAL.value:
                self.risk_stats['critical_alerts'] += 1
            
            if risk_assessment['recommended_action'] == RiskAction.EMERGENCY_STOP.value:
                self.risk_stats['emergency_stops'] += 1
            
            if risk_assessment['recommended_action'] == RiskAction.BLOCK.value:
                self.risk_stats['trades_blocked'] += 1
            
            self.risk_stats['risk_score'] = risk_assessment.get('risk_score', 0)
            
        except Exception as e:
            logger.error(f"❌ 更新風險統計失敗: {e}")
    
    def add_trade_record(self, trade_result: Dict[str, Any]):
        """添加交易記錄"""
        try:
            trade_record = {
                'timestamp': datetime.now(),
                'pnl': trade_result.get('pnl', 0),
                'duration': trade_result.get('duration', 0),
                'status': trade_result.get('status', 'unknown')
            }
            
            self.trade_history.append(trade_record)
            
            # 保持歷史記錄在合理範圍內
            if len(self.trade_history) > 1000:
                self.trade_history = self.trade_history[-1000:]
            
        except Exception as e:
            logger.error(f"❌ 添加交易記錄失敗: {e}")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """獲取風險摘要"""
        try:
            recent_alerts = [alert for alert in self.risk_alerts 
                           if alert.timestamp >= datetime.now() - timedelta(hours=24)]
            
            return {
                'current_balance': self.current_balance,
                'peak_balance': self.peak_balance,
                'current_drawdown': (self.peak_balance - self.current_balance) / self.peak_balance,
                'daily_pnl': self._calculate_daily_pnl(),
                'weekly_pnl': self._calculate_weekly_pnl(),
                'win_rate': self._calculate_win_rate(),
                'risk_stats': self.risk_stats.copy(),
                'dynamic_params': self.dynamic_risk_params.copy(),
                'recent_alerts_count': len(recent_alerts),
                'active_rules_count': sum(1 for rule in self.risk_rules if rule.enabled)
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取風險摘要失敗: {e}")
            return {}


# 創建全局風險管理器實例
def create_risk_manager(initial_balance: float = 100000.0) -> RiskManager:
    """創建風險管理器實例"""
    return RiskManager(initial_balance)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_risk_manager():
        """測試風險管理器"""
        print("🧪 測試風險管理器...")
        
        risk_manager = create_risk_manager(100000.0)
        
        # 模擬AI決策
        ai_decision = {
            'final_decision': 'BUY',
            'confidence': 0.45,  # 低信心度，應該觸發風險規則
            'reasoning': '測試低信心度交易'
        }
        
        # 模擬市場數據
        market_data = {
            'current_price': 1500000,
            'volatility_level': '高'
        }
        
        # 模擬賬戶狀態
        account_status = {
            'total_equity': 95000,  # 已有虧損
            'available_balance': 90000,
            'margin_used': 5000,
            'positions_count': 2
        }
        
        # 風險評估
        risk_assessment = await risk_manager.assess_trade_risk(
            ai_decision, market_data, account_status
        )
        
        print(f"✅ 風險評估結果:")
        print(f"   風險等級: {risk_assessment['overall_risk_level']}")
        print(f"   建議動作: {risk_assessment['recommended_action']}")
        print(f"   風險分數: {risk_assessment['risk_score']:.1f}")
        print(f"   是否批准: {risk_assessment['approved']}")
        
        if risk_assessment.get('violations'):
            print(f"   風險違規:")
            for violation in risk_assessment['violations']:
                print(f"     - {violation['message']}")
        
        # 顯示風險摘要
        risk_summary = risk_manager.get_risk_summary()
        print(f"\n📊 風險摘要: {risk_summary}")
    
    # 運行測試
    asyncio.run(test_risk_manager())