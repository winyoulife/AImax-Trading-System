#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成評分器 - 為AImax系統優化的多模型集成
"""

from typing import Dict, Any, List, Tuple
import logging
import numpy as np
import pandas as pd
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class EnsembleScorer:
    """多模型加權計分器 - 專為AImax系統優化"""
    
    def __init__(self):
        """初始化集成評分器"""
        # 權重配置 - 可根據AImax系統需求調整
        self.weights = {
            'technical_analysis': 0.4,
            'market_sentiment': 0.35,
            'volatility_analysis': 0.25,
        }
        
        logger.info("🎯 AImax集成評分器初始化完成")
    
    def analyze(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析市場數據並提供集成評分
        
        Args:
            market_data: 市場數據字典
            
        Returns:
            Dict[str, Any]: 集成分析結果
        """
        try:
            results = {}
            total_score = 0.0
            total_weight = 0.0
            
            # 技術分析評分
            tech_result = self._analyze_technical_indicators(market_data)
            if tech_result['success']:
                score = tech_result['score']
                weight = self.weights['technical_analysis']
                results['technical_analysis'] = tech_result
                total_score += score * weight
                total_weight += weight
            
            # 市場情緒分析
            sentiment_result = self._analyze_market_sentiment(market_data)
            if sentiment_result['success']:
                score = sentiment_result['score']
                weight = self.weights['market_sentiment']
                results['market_sentiment'] = sentiment_result
                total_score += score * weight
                total_weight += weight
            
            # 波動率分析
            volatility_result = self._analyze_volatility(market_data)
            if volatility_result['success']:
                score = volatility_result['score']
                weight = self.weights['volatility_analysis']
                results['volatility_analysis'] = volatility_result
                total_score += score * weight
                total_weight += weight
            
            # 計算最終集成分數
            final_score = total_score / total_weight if total_weight > 0 else 50
            
            # 生成交易信號
            signal = self._generate_trading_signal(final_score, results)
            
            return {
                'success': True,
                'final_score': final_score,
                'signal': signal,
                'individual_results': results,
                'weights_used': total_weight,
                'confidence': self._calculate_confidence(results),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ 集成分析失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'final_score': 50,
                'signal': 'HOLD',
                'timestamp': datetime.now()
            }
    
    def _analyze_technical_indicators(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析技術指標"""
        try:
            score = 50  # 基準分數
            factors = []
            
            # 價格變化分析
            price_change = market_data.get('price_change_1m', 0)
            if price_change > 1:
                score += 10
                factors.append(f"價格上漲 {price_change}%")
            elif price_change < -1:
                score -= 10
                factors.append(f"價格下跌 {price_change}%")
            
            # 成交量分析
            volume_ratio = market_data.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                score += 8
                factors.append(f"成交量放大 {volume_ratio:.1f}倍")
            elif volume_ratio < 0.7:
                score -= 5
                factors.append(f"成交量萎縮 {volume_ratio:.1f}倍")
            
            # 確保分數在合理範圍內
            score = max(20, min(80, score))
            
            return {
                'success': True,
                'score': score,
                'factors': factors,
                'analysis': f"技術指標綜合評分: {score}"
            }
            
        except Exception as e:
            logger.error(f"❌ 技術指標分析失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'score': 50
            }
    
    def _analyze_market_sentiment(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析市場情緒"""
        try:
            score = 50  # 基準分數
            factors = []
            
            # 基於價格趨勢判斷情緒
            current_price = market_data.get('current_price', 0)
            if current_price > 1600000:  # 高價位
                score += 5
                factors.append("價格處於高位，市場樂觀")
            elif current_price < 1400000:  # 低價位
                score -= 5
                factors.append("價格處於低位，市場悲觀")
            
            # AI格式化數據中的情緒指標
            ai_data = market_data.get('ai_formatted_data', '')
            if '上漲' in ai_data or '看漲' in ai_data:
                score += 8
                factors.append("AI數據顯示看漲情緒")
            elif '下跌' in ai_data or '看跌' in ai_data:
                score -= 8
                factors.append("AI數據顯示看跌情緒")
            
            # 確保分數在合理範圍內
            score = max(25, min(75, score))
            
            return {
                'success': True,
                'score': score,
                'factors': factors,
                'analysis': f"市場情緒評分: {score}"
            }
            
        except Exception as e:
            logger.error(f"❌ 市場情緒分析失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'score': 50
            }
    
    def _analyze_volatility(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析波動率"""
        try:
            score = 50  # 基準分數
            factors = []
            
            # 基於價格變化判斷波動率
            price_change = abs(market_data.get('price_change_1m', 0))
            
            if price_change > 2:
                score -= 10  # 高波動率降低分數
                factors.append(f"高波動率 {price_change}%，風險增加")
            elif price_change < 0.5:
                score += 5  # 低波動率略微加分
                factors.append(f"低波動率 {price_change}%，市場穩定")
            else:
                factors.append(f"正常波動率 {price_change}%")
            
            # 成交量波動分析
            volume_ratio = market_data.get('volume_ratio', 1.0)
            if volume_ratio > 2:
                score -= 5  # 成交量劇烈變化
                factors.append("成交量劇烈變化，市場不穩定")
            
            # 確保分數在合理範圍內
            score = max(30, min(70, score))
            
            return {
                'success': True,
                'score': score,
                'factors': factors,
                'analysis': f"波動率分析評分: {score}"
            }
            
        except Exception as e:
            logger.error(f"❌ 波動率分析失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'score': 50
            }
    
    def _generate_trading_signal(self, final_score: float, results: Dict[str, Any]) -> str:
        """生成交易信號"""
        try:
            # 基於最終分數生成信號
            if final_score > 60:
                signal = "BUY"
            elif final_score < 40:
                signal = "SELL"
            else:
                signal = "HOLD"
            
            # 檢查一致性 - 如果各模型分歧較大，傾向於HOLD
            scores = []
            for result in results.values():
                if result.get('success') and 'score' in result:
                    scores.append(result['score'])
            
            if len(scores) > 1:
                score_std = np.std(scores)
                if score_std > 15:  # 分歧較大
                    signal = "HOLD"
                    logger.info(f"⚠️ 模型分歧較大 (std={score_std:.1f})，調整為HOLD")
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ 生成交易信號失敗: {e}")
            return "HOLD"
    
    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """計算整體信心度"""
        try:
            successful_analyses = sum(1 for r in results.values() if r.get('success', False))
            total_analyses = len(results)
            
            if total_analyses == 0:
                return 0.0
            
            # 基礎信心度基於成功分析的比例
            base_confidence = (successful_analyses / total_analyses) * 100
            
            # 根據分數一致性調整信心度
            scores = []
            for result in results.values():
                if result.get('success') and 'score' in result:
                    scores.append(result['score'])
            
            if len(scores) > 1:
                score_std = np.std(scores)
                consistency_factor = max(0.5, 1 - score_std / 50)  # 標準差越小，一致性越高
                base_confidence *= consistency_factor
            
            return min(100, max(0, base_confidence))
            
        except Exception as e:
            logger.error(f"❌ 計算信心度失敗: {e}")
            return 50.0
    
    def update_weights(self, new_weights: Dict[str, float]) -> bool:
        """更新模型權重"""
        try:
            # 驗證權重
            if not isinstance(new_weights, dict):
                return False
            
            # 檢查權重和是否接近1
            weight_sum = sum(new_weights.values())
            if abs(weight_sum - 1.0) > 0.1:
                logger.warning(f"⚠️ 權重和不等於1: {weight_sum}")
                return False
            
            # 更新權重
            old_weights = self.weights.copy()
            self.weights.update(new_weights)
            
            logger.info(f"✅ 權重更新成功")
            logger.info(f"舊權重: {old_weights}")
            logger.info(f"新權重: {self.weights}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新權重失敗: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型信息"""
        return {
            'model_type': 'ensemble_scorer',
            'weights': self.weights.copy(),
            'components': ['technical_analysis', 'market_sentiment', 'volatility_analysis'],
            'optimized_for': 'AImax_trading_system',
            'version': '1.0'
        }
    
    # ==================== 集成評分器驗證功能 ====================
    
    def validate_ensemble(self, test_data: List[Dict[str, Any]], 
                         ground_truth: List[str] = None) -> Dict[str, Any]:
        """
        驗證集成評分器性能
        
        Args:
            test_data: 測試數據列表
            ground_truth: 真實標籤列表 (可選)
            
        Returns:
            驗證結果字典
        """
        try:
            logger.info("🔍 開始集成評分器驗證...")
            
            if not test_data:
                return {'success': False, 'error': 'No test data provided'}
            
            # 執行批量分析
            predictions = []
            individual_scores = {'technical_analysis': [], 'market_sentiment': [], 'volatility_analysis': []}
            final_scores = []
            signals = []
            confidences = []
            
            for data in test_data:
                result = self.analyze(data)
                if result['success']:
                    predictions.append(result)
                    final_scores.append(result['final_score'])
                    signals.append(result['signal'])
                    confidences.append(result['confidence'])
                    
                    # 收集個別模型分數
                    for component, scores_list in individual_scores.items():
                        if component in result['individual_results']:
                            scores_list.append(result['individual_results'][component]['score'])
                        else:
                            scores_list.append(50)  # 默認分數
            
            if not predictions:
                return {'success': False, 'error': 'No successful predictions'}
            
            # 計算驗證指標
            validation_metrics = {
                'prediction_count': len(predictions),
                'success_rate': len(predictions) / len(test_data),
                'score_statistics': self._calculate_score_statistics(final_scores),
                'signal_distribution': self._calculate_signal_distribution(signals),
                'confidence_analysis': self._analyze_confidence_levels(confidences),
                'component_consistency': self._analyze_component_consistency(individual_scores),
                'weight_effectiveness': self._evaluate_weight_effectiveness(individual_scores, final_scores),
                'model_agreement': self._calculate_model_agreement(individual_scores),
                'prediction_stability': self._assess_prediction_stability(predictions)
            }
            
            # 如果有真實標籤，計算準確性指標
            if ground_truth and len(ground_truth) == len(signals):
                accuracy_metrics = self._calculate_accuracy_metrics(signals, ground_truth)
                validation_metrics['accuracy_metrics'] = accuracy_metrics
            
            # 權重優化建議
            weight_optimization = self._optimize_weights(individual_scores, final_scores, ground_truth, signals)
            validation_metrics['weight_optimization'] = weight_optimization
            
            # 衝突解決機制評估
            conflict_resolution = self._evaluate_conflict_resolution(individual_scores, signals)
            validation_metrics['conflict_resolution'] = conflict_resolution
            
            # 可靠性評估
            reliability_assessment = self._assess_ensemble_reliability(validation_metrics)
            validation_metrics['reliability_assessment'] = reliability_assessment
            
            logger.info("✅ 集成評分器驗證完成")
            logger.info(f"   成功率: {validation_metrics['success_rate']:.2%}")
            logger.info(f"   平均信心度: {np.mean(confidences):.1f}%")
            logger.info(f"   模型一致性: {validation_metrics['model_agreement']:.3f}")
            
            return {
                'success': True,
                'validation_metrics': validation_metrics,
                'summary': {
                    'overall_score': self._calculate_ensemble_overall_score(validation_metrics),
                    'strengths': self._identify_ensemble_strengths(validation_metrics),
                    'weaknesses': self._identify_ensemble_weaknesses(validation_metrics),
                    'recommendations': self._generate_ensemble_recommendations(validation_metrics)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 集成評分器驗證失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_score_statistics(self, scores: List[float]) -> Dict[str, float]:
        """計算分數統計信息"""
        try:
            if not scores:
                return {}
            
            scores_array = np.array(scores)
            return {
                'mean': float(np.mean(scores_array)),
                'std': float(np.std(scores_array)),
                'min': float(np.min(scores_array)),
                'max': float(np.max(scores_array)),
                'median': float(np.median(scores_array)),
                'q25': float(np.percentile(scores_array, 25)),
                'q75': float(np.percentile(scores_array, 75))
            }
        except Exception as e:
            logger.error(f"❌ 計算分數統計失敗: {e}")
            return {}
    
    def _calculate_signal_distribution(self, signals: List[str]) -> Dict[str, Any]:
        """計算信號分佈"""
        try:
            if not signals:
                return {}
            
            signal_counts = {}
            for signal in signals:
                signal_counts[signal] = signal_counts.get(signal, 0) + 1
            
            total = len(signals)
            signal_percentages = {k: v/total for k, v in signal_counts.items()}
            
            return {
                'counts': signal_counts,
                'percentages': signal_percentages,
                'total': total,
                'diversity': len(signal_counts)  # 信號多樣性
            }
        except Exception as e:
            logger.error(f"❌ 計算信號分佈失敗: {e}")
            return {}
    
    def _analyze_confidence_levels(self, confidences: List[float]) -> Dict[str, Any]:
        """分析信心度水平"""
        try:
            if not confidences:
                return {}
            
            conf_array = np.array(confidences)
            
            # 信心度分級
            high_confidence = np.sum(conf_array >= 80)
            medium_confidence = np.sum((conf_array >= 60) & (conf_array < 80))
            low_confidence = np.sum(conf_array < 60)
            
            return {
                'statistics': self._calculate_score_statistics(confidences),
                'distribution': {
                    'high_confidence': high_confidence,
                    'medium_confidence': medium_confidence,
                    'low_confidence': low_confidence
                },
                'percentages': {
                    'high_confidence': high_confidence / len(confidences),
                    'medium_confidence': medium_confidence / len(confidences),
                    'low_confidence': low_confidence / len(confidences)
                }
            }
        except Exception as e:
            logger.error(f"❌ 分析信心度水平失敗: {e}")
            return {}
    
    def _analyze_component_consistency(self, individual_scores: Dict[str, List[float]]) -> Dict[str, Any]:
        """分析組件一致性"""
        try:
            consistency_metrics = {}
            
            for component, scores in individual_scores.items():
                if scores:
                    scores_array = np.array(scores)
                    consistency_metrics[component] = {
                        'mean': float(np.mean(scores_array)),
                        'std': float(np.std(scores_array)),
                        'consistency_score': 1.0 / (1.0 + np.std(scores_array) / 50.0)  # 標準化一致性分數
                    }
            
            # 計算組件間相關性
            correlations = {}
            components = list(individual_scores.keys())
            for i, comp1 in enumerate(components):
                for comp2 in components[i+1:]:
                    if individual_scores[comp1] and individual_scores[comp2]:
                        corr = np.corrcoef(individual_scores[comp1], individual_scores[comp2])[0, 1]
                        correlations[f"{comp1}_vs_{comp2}"] = float(corr) if not np.isnan(corr) else 0.0
            
            return {
                'component_metrics': consistency_metrics,
                'correlations': correlations,
                'overall_consistency': np.mean([m['consistency_score'] for m in consistency_metrics.values()])
            }
        except Exception as e:
            logger.error(f"❌ 分析組件一致性失敗: {e}")
            return {}
    
    def _evaluate_weight_effectiveness(self, individual_scores: Dict[str, List[float]], 
                                     final_scores: List[float]) -> Dict[str, Any]:
        """評估權重有效性"""
        try:
            if not individual_scores or not final_scores:
                return {}
            
            # 計算每個組件對最終分數的貢獻
            contributions = {}
            for component, scores in individual_scores.items():
                if scores and component in self.weights:
                    weight = self.weights[component]
                    weighted_scores = [s * weight for s in scores]
                    
                    # 計算與最終分數的相關性
                    if len(weighted_scores) == len(final_scores):
                        correlation = np.corrcoef(weighted_scores, final_scores)[0, 1]
                        contributions[component] = {
                            'weight': weight,
                            'correlation_with_final': float(correlation) if not np.isnan(correlation) else 0.0,
                            'average_contribution': float(np.mean(weighted_scores)),
                            'contribution_variance': float(np.var(weighted_scores))
                        }
            
            # 評估權重平衡性
            weight_balance = self._evaluate_weight_balance()
            
            return {
                'component_contributions': contributions,
                'weight_balance': weight_balance,
                'effectiveness_score': self._calculate_weight_effectiveness_score(contributions)
            }
        except Exception as e:
            logger.error(f"❌ 評估權重有效性失敗: {e}")
            return {}
    
    def _evaluate_weight_balance(self) -> Dict[str, Any]:
        """評估權重平衡性"""
        try:
            weights_list = list(self.weights.values())
            weights_array = np.array(weights_list)
            
            # 計算權重分佈的均勻性
            entropy = -np.sum(weights_array * np.log(weights_array + 1e-10))
            max_entropy = np.log(len(weights_array))
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            
            return {
                'entropy': float(entropy),
                'normalized_entropy': float(normalized_entropy),
                'weight_variance': float(np.var(weights_array)),
                'balance_score': float(normalized_entropy)  # 越接近1越平衡
            }
        except Exception as e:
            logger.error(f"❌ 評估權重平衡性失敗: {e}")
            return {}
    
    def _calculate_weight_effectiveness_score(self, contributions: Dict[str, Any]) -> float:
        """計算權重有效性分數"""
        try:
            if not contributions:
                return 0.0
            
            # 基於相關性和貢獻度計算有效性
            correlations = [c['correlation_with_final'] for c in contributions.values()]
            avg_correlation = np.mean([abs(c) for c in correlations])
            
            return float(avg_correlation)
        except Exception as e:
            logger.error(f"❌ 計算權重有效性分數失敗: {e}")
            return 0.0
    
    def _calculate_model_agreement(self, individual_scores: Dict[str, List[float]]) -> float:
        """計算模型一致性"""
        try:
            if len(individual_scores) < 2:
                return 1.0
            
            # 計算所有組件分數的標準差
            all_stds = []
            max_len = max(len(scores) for scores in individual_scores.values() if scores)
            
            for i in range(max_len):
                scores_at_i = []
                for scores in individual_scores.values():
                    if i < len(scores):
                        scores_at_i.append(scores[i])
                
                if len(scores_at_i) > 1:
                    std_at_i = np.std(scores_at_i)
                    all_stds.append(std_at_i)
            
            if not all_stds:
                return 1.0
            
            # 將標準差轉換為一致性分數 (標準差越小，一致性越高)
            avg_std = np.mean(all_stds)
            agreement = 1.0 / (1.0 + avg_std / 25.0)  # 標準化到0-1範圍
            
            return float(agreement)
        except Exception as e:
            logger.error(f"❌ 計算模型一致性失敗: {e}")
            return 0.5
    
    def _assess_prediction_stability(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """評估預測穩定性"""
        try:
            if len(predictions) < 2:
                return {}
            
            # 分析分數變化
            scores = [p['final_score'] for p in predictions]
            score_changes = [abs(scores[i] - scores[i-1]) for i in range(1, len(scores))]
            
            # 分析信號變化
            signals = [p['signal'] for p in predictions]
            signal_changes = sum(1 for i in range(1, len(signals)) if signals[i] != signals[i-1])
            
            # 分析信心度變化
            confidences = [p['confidence'] for p in predictions]
            confidence_changes = [abs(confidences[i] - confidences[i-1]) for i in range(1, len(confidences))]
            
            return {
                'score_stability': {
                    'mean_change': float(np.mean(score_changes)),
                    'max_change': float(np.max(score_changes)),
                    'stability_score': 1.0 / (1.0 + np.mean(score_changes) / 10.0)
                },
                'signal_stability': {
                    'change_count': signal_changes,
                    'change_rate': signal_changes / (len(signals) - 1),
                    'stability_score': 1.0 - (signal_changes / (len(signals) - 1))
                },
                'confidence_stability': {
                    'mean_change': float(np.mean(confidence_changes)),
                    'max_change': float(np.max(confidence_changes)),
                    'stability_score': 1.0 / (1.0 + np.mean(confidence_changes) / 20.0)
                }
            }
        except Exception as e:
            logger.error(f"❌ 評估預測穩定性失敗: {e}")
            return {}
    
    def _calculate_accuracy_metrics(self, predictions: List[str], 
                                  ground_truth: List[str]) -> Dict[str, Any]:
        """計算準確性指標"""
        try:
            if len(predictions) != len(ground_truth):
                return {}
            
            # 計算準確率
            correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
            accuracy = correct / len(predictions)
            
            # 計算各類別的精確率和召回率
            unique_labels = list(set(predictions + ground_truth))
            precision_recall = {}
            
            for label in unique_labels:
                tp = sum(1 for p, g in zip(predictions, ground_truth) if p == label and g == label)
                fp = sum(1 for p, g in zip(predictions, ground_truth) if p == label and g != label)
                fn = sum(1 for p, g in zip(predictions, ground_truth) if p != label and g == label)
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                
                precision_recall[label] = {
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'support': sum(1 for g in ground_truth if g == label)
                }
            
            return {
                'accuracy': accuracy,
                'correct_predictions': correct,
                'total_predictions': len(predictions),
                'precision_recall': precision_recall,
                'macro_f1': np.mean([pr['f1_score'] for pr in precision_recall.values()])
            }
        except Exception as e:
            logger.error(f"❌ 計算準確性指標失敗: {e}")
            return {}
    
    def _optimize_weights(self, individual_scores: Dict[str, List[float]], 
                         final_scores: List[float],
                         ground_truth: List[str] = None,
                         signals: List[str] = None) -> Dict[str, Any]:
        """優化權重建議"""
        try:
            optimization_results = {}
            
            # 基於相關性的權重優化
            if individual_scores and final_scores:
                correlation_based = self._optimize_weights_by_correlation(individual_scores, final_scores)
                optimization_results['correlation_based'] = correlation_based
            
            # 基於準確性的權重優化 (如果有真實標籤)
            if ground_truth and signals and individual_scores:
                accuracy_based = self._optimize_weights_by_accuracy(individual_scores, ground_truth, signals)
                optimization_results['accuracy_based'] = accuracy_based
            
            # 基於方差的權重優化
            variance_based = self._optimize_weights_by_variance(individual_scores)
            optimization_results['variance_based'] = variance_based
            
            # 生成最終權重建議
            final_recommendation = self._generate_weight_recommendation(optimization_results)
            optimization_results['final_recommendation'] = final_recommendation
            
            return optimization_results
        except Exception as e:
            logger.error(f"❌ 優化權重失敗: {e}")
            return {}
    
    def _optimize_weights_by_correlation(self, individual_scores: Dict[str, List[float]], 
                                       final_scores: List[float]) -> Dict[str, float]:
        """基於相關性優化權重"""
        try:
            correlations = {}
            for component, scores in individual_scores.items():
                if scores and len(scores) == len(final_scores):
                    corr = np.corrcoef(scores, final_scores)[0, 1]
                    correlations[component] = abs(corr) if not np.isnan(corr) else 0.0
            
            # 標準化相關性作為權重
            total_corr = sum(correlations.values())
            if total_corr > 0:
                optimized_weights = {k: v / total_corr for k, v in correlations.items()}
            else:
                optimized_weights = {k: 1.0 / len(correlations) for k in correlations.keys()}
            
            return optimized_weights
        except Exception as e:
            logger.error(f"❌ 基於相關性優化權重失敗: {e}")
            return {}
    
    def _optimize_weights_by_accuracy(self, individual_scores: Dict[str, List[float]], 
                                    ground_truth: List[str], signals: List[str]) -> Dict[str, float]:
        """基於準確性優化權重"""
        try:
            component_accuracies = {}
            
            for component, scores in individual_scores.items():
                if scores and len(scores) == len(ground_truth):
                    # 將分數轉換為信號
                    component_signals = ['BUY' if s > 60 else 'SELL' if s < 40 else 'HOLD' for s in scores]
                    
                    # 計算準確率
                    correct = sum(1 for cs, gt in zip(component_signals, ground_truth) if cs == gt)
                    accuracy = correct / len(ground_truth)
                    component_accuracies[component] = accuracy
            
            # 基於準確率分配權重
            total_accuracy = sum(component_accuracies.values())
            if total_accuracy > 0:
                optimized_weights = {k: v / total_accuracy for k, v in component_accuracies.items()}
            else:
                optimized_weights = {k: 1.0 / len(component_accuracies) for k in component_accuracies.keys()}
            
            return optimized_weights
        except Exception as e:
            logger.error(f"❌ 基於準確性優化權重失敗: {e}")
            return {}
    
    def _optimize_weights_by_variance(self, individual_scores: Dict[str, List[float]]) -> Dict[str, float]:
        """基於方差優化權重"""
        try:
            component_variances = {}
            
            for component, scores in individual_scores.items():
                if scores:
                    variance = np.var(scores)
                    # 方差越小，權重越高 (更穩定的組件獲得更高權重)
                    component_variances[component] = 1.0 / (1.0 + variance / 100.0)
            
            # 標準化權重
            total_weight = sum(component_variances.values())
            if total_weight > 0:
                optimized_weights = {k: v / total_weight for k, v in component_variances.items()}
            else:
                optimized_weights = {k: 1.0 / len(component_variances) for k in component_variances.keys()}
            
            return optimized_weights
        except Exception as e:
            logger.error(f"❌ 基於方差優化權重失敗: {e}")
            return {}
    
    def _generate_weight_recommendation(self, optimization_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成最終權重建議"""
        try:
            recommendations = {}
            
            # 收集所有優化方法的權重建議
            all_methods = []
            for method, weights in optimization_results.items():
                if isinstance(weights, dict) and weights:
                    all_methods.append((method, weights))
            
            if not all_methods:
                return {'recommended_weights': self.weights.copy(), 'confidence': 0.0}
            
            # 計算平均權重
            components = set()
            for _, weights in all_methods:
                components.update(weights.keys())
            
            averaged_weights = {}
            for component in components:
                component_weights = []
                for _, weights in all_methods:
                    if component in weights:
                        component_weights.append(weights[component])
                
                if component_weights:
                    averaged_weights[component] = np.mean(component_weights)
            
            # 標準化權重
            total_weight = sum(averaged_weights.values())
            if total_weight > 0:
                final_weights = {k: v / total_weight for k, v in averaged_weights.items()}
            else:
                final_weights = self.weights.copy()
            
            # 計算建議信心度
            confidence = self._calculate_recommendation_confidence(optimization_results, final_weights)
            
            return {
                'recommended_weights': final_weights,
                'current_weights': self.weights.copy(),
                'weight_changes': {k: final_weights.get(k, 0) - self.weights.get(k, 0) 
                                 for k in set(list(final_weights.keys()) + list(self.weights.keys()))},
                'confidence': confidence,
                'optimization_methods_used': len(all_methods)
            }
        except Exception as e:
            logger.error(f"❌ 生成權重建議失敗: {e}")
            return {'recommended_weights': self.weights.copy(), 'confidence': 0.0}
    
    def _calculate_recommendation_confidence(self, optimization_results: Dict[str, Any], 
                                          final_weights: Dict[str, float]) -> float:
        """計算權重建議的信心度"""
        try:
            # 基於不同優化方法的一致性計算信心度
            method_weights = []
            for method, weights in optimization_results.items():
                if isinstance(weights, dict) and weights:
                    method_weights.append(weights)
            
            if len(method_weights) < 2:
                return 0.5
            
            # 計算方法間的權重一致性
            consistencies = []
            components = final_weights.keys()
            
            for component in components:
                component_weights = [w.get(component, 0) for w in method_weights]
                if len(component_weights) > 1:
                    std = np.std(component_weights)
                    consistency = 1.0 / (1.0 + std * 2)  # 標準差越小，一致性越高
                    consistencies.append(consistency)
            
            if consistencies:
                avg_consistency = np.mean(consistencies)
                return float(avg_consistency)
            else:
                return 0.5
        except Exception as e:
            logger.error(f"❌ 計算建議信心度失敗: {e}")
            return 0.5
    
    def _evaluate_conflict_resolution(self, individual_scores: Dict[str, List[float]], 
                                    signals: List[str]) -> Dict[str, Any]:
        """評估衝突解決機制"""
        try:
            if not individual_scores or not signals:
                return {}
            
            conflict_analysis = {
                'total_predictions': len(signals),
                'conflict_cases': 0,
                'resolution_effectiveness': 0.0,
                'conflict_types': {
                    'high_disagreement': 0,
                    'mixed_signals': 0,
                    'low_confidence': 0
                }
            }
            
            # 分析每個預測的衝突情況
            max_len = min(len(signals), min(len(scores) for scores in individual_scores.values() if scores))
            
            for i in range(max_len):
                # 獲取該時間點的所有組件分數
                scores_at_i = []
                for component, scores in individual_scores.items():
                    if i < len(scores):
                        scores_at_i.append(scores[i])
                
                if len(scores_at_i) < 2:
                    continue
                
                # 檢測衝突
                score_std = np.std(scores_at_i)
                score_range = max(scores_at_i) - min(scores_at_i)
                
                # 高分歧衝突
                if score_std > 15:
                    conflict_analysis['conflict_cases'] += 1
                    conflict_analysis['conflict_types']['high_disagreement'] += 1
                
                # 混合信號衝突 (有些看漲，有些看跌)
                buy_signals = sum(1 for s in scores_at_i if s > 60)
                sell_signals = sum(1 for s in scores_at_i if s < 40)
                if buy_signals > 0 and sell_signals > 0:
                    conflict_analysis['conflict_cases'] += 1
                    conflict_analysis['conflict_types']['mixed_signals'] += 1
                
                # 低信心度衝突
                if all(40 <= s <= 60 for s in scores_at_i):
                    conflict_analysis['conflict_types']['low_confidence'] += 1
            
            # 計算解決有效性
            if conflict_analysis['conflict_cases'] > 0:
                # 檢查衝突情況下的信號分佈
                hold_signals = sum(1 for s in signals if s == 'HOLD')
                resolution_rate = hold_signals / len(signals)  # HOLD信號比例作為衝突解決指標
                conflict_analysis['resolution_effectiveness'] = resolution_rate
            
            # 衝突解決策略評估
            resolution_strategies = self._evaluate_resolution_strategies(individual_scores, signals)
            conflict_analysis['resolution_strategies'] = resolution_strategies
            
            return conflict_analysis
        except Exception as e:
            logger.error(f"❌ 評估衝突解決機制失敗: {e}")
            return {}
    
    def _evaluate_resolution_strategies(self, individual_scores: Dict[str, List[float]], 
                                      signals: List[str]) -> Dict[str, Any]:
        """評估衝突解決策略"""
        try:
            strategies = {
                'weighted_average': {'used': 0, 'effective': 0},
                'conservative_hold': {'used': 0, 'effective': 0},
                'majority_vote': {'used': 0, 'effective': 0}
            }
            
            max_len = min(len(signals), min(len(scores) for scores in individual_scores.values() if scores))
            
            for i in range(max_len):
                scores_at_i = []
                for component, scores in individual_scores.items():
                    if i < len(scores):
                        scores_at_i.append(scores[i])
                
                if len(scores_at_i) < 2:
                    continue
                
                # 計算加權平均分數
                weighted_avg = sum(s * w for s, w in zip(scores_at_i, self.weights.values())) / sum(self.weights.values())
                
                # 檢測使用的策略
                signal = signals[i] if i < len(signals) else 'HOLD'
                score_std = np.std(scores_at_i)
                
                if score_std > 15:  # 高分歧情況
                    if signal == 'HOLD':
                        strategies['conservative_hold']['used'] += 1
                        # 假設保守策略在高分歧時是有效的
                        strategies['conservative_hold']['effective'] += 1
                    else:
                        strategies['weighted_average']['used'] += 1
                        # 檢查加權平均是否與最終信號一致
                        expected_signal = 'BUY' if weighted_avg > 60 else 'SELL' if weighted_avg < 40 else 'HOLD'
                        if expected_signal == signal:
                            strategies['weighted_average']['effective'] += 1
                
                # 多數投票策略檢測
                buy_votes = sum(1 for s in scores_at_i if s > 60)
                sell_votes = sum(1 for s in scores_at_i if s < 40)
                hold_votes = len(scores_at_i) - buy_votes - sell_votes
                
                max_votes = max(buy_votes, sell_votes, hold_votes)
                if max_votes > len(scores_at_i) / 2:  # 有明顯多數
                    strategies['majority_vote']['used'] += 1
                    expected_majority = 'BUY' if buy_votes == max_votes else 'SELL' if sell_votes == max_votes else 'HOLD'
                    if expected_majority == signal:
                        strategies['majority_vote']['effective'] += 1
            
            # 計算策略效率
            for strategy in strategies.values():
                if strategy['used'] > 0:
                    strategy['effectiveness_rate'] = strategy['effective'] / strategy['used']
                else:
                    strategy['effectiveness_rate'] = 0.0
            
            return strategies
        except Exception as e:
            logger.error(f"❌ 評估衝突解決策略失敗: {e}")
            return {}
    
    def _assess_ensemble_reliability(self, validation_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """評估集成系統可靠性"""
        try:
            reliability_factors = {}
            
            # 成功率可靠性
            success_rate = validation_metrics.get('success_rate', 0)
            reliability_factors['success_rate'] = {
                'score': success_rate,
                'weight': 0.2,
                'assessment': 'excellent' if success_rate > 0.95 else 'good' if success_rate > 0.8 else 'fair' if success_rate > 0.6 else 'poor'
            }
            
            # 模型一致性可靠性
            model_agreement = validation_metrics.get('model_agreement', 0)
            reliability_factors['model_agreement'] = {
                'score': model_agreement,
                'weight': 0.25,
                'assessment': 'excellent' if model_agreement > 0.8 else 'good' if model_agreement > 0.6 else 'fair' if model_agreement > 0.4 else 'poor'
            }
            
            # 預測穩定性可靠性
            stability_metrics = validation_metrics.get('prediction_stability', {})
            if stability_metrics:
                avg_stability = np.mean([
                    stability_metrics.get('score_stability', {}).get('stability_score', 0),
                    stability_metrics.get('signal_stability', {}).get('stability_score', 0),
                    stability_metrics.get('confidence_stability', {}).get('stability_score', 0)
                ])
                reliability_factors['prediction_stability'] = {
                    'score': avg_stability,
                    'weight': 0.2,
                    'assessment': 'excellent' if avg_stability > 0.8 else 'good' if avg_stability > 0.6 else 'fair' if avg_stability > 0.4 else 'poor'
                }
            
            # 信心度分佈可靠性
            confidence_analysis = validation_metrics.get('confidence_analysis', {})
            if confidence_analysis and 'percentages' in confidence_analysis:
                high_conf_ratio = confidence_analysis['percentages'].get('high_confidence', 0)
                reliability_factors['confidence_distribution'] = {
                    'score': high_conf_ratio,
                    'weight': 0.15,
                    'assessment': 'excellent' if high_conf_ratio > 0.6 else 'good' if high_conf_ratio > 0.4 else 'fair' if high_conf_ratio > 0.2 else 'poor'
                }
            
            # 權重有效性可靠性
            weight_effectiveness = validation_metrics.get('weight_effectiveness', {})
            if weight_effectiveness and 'effectiveness_score' in weight_effectiveness:
                eff_score = weight_effectiveness['effectiveness_score']
                reliability_factors['weight_effectiveness'] = {
                    'score': eff_score,
                    'weight': 0.2,
                    'assessment': 'excellent' if eff_score > 0.8 else 'good' if eff_score > 0.6 else 'fair' if eff_score > 0.4 else 'poor'
                }
            
            # 計算總體可靠性分數
            total_score = 0.0
            total_weight = 0.0
            
            for factor, data in reliability_factors.items():
                total_score += data['score'] * data['weight']
                total_weight += data['weight']
            
            overall_reliability = total_score / total_weight if total_weight > 0 else 0.0
            
            # 總體評估
            if overall_reliability > 0.8:
                overall_assessment = 'excellent'
                reliability_level = 'high'
            elif overall_reliability > 0.6:
                overall_assessment = 'good'
                reliability_level = 'medium-high'
            elif overall_reliability > 0.4:
                overall_assessment = 'fair'
                reliability_level = 'medium'
            else:
                overall_assessment = 'poor'
                reliability_level = 'low'
            
            return {
                'overall_score': overall_reliability,
                'overall_assessment': overall_assessment,
                'reliability_level': reliability_level,
                'factor_scores': reliability_factors,
                'recommendations': self._generate_reliability_recommendations(reliability_factors)
            }
        except Exception as e:
            logger.error(f"❌ 評估集成系統可靠性失敗: {e}")
            return {}
    
    def _generate_reliability_recommendations(self, reliability_factors: Dict[str, Any]) -> List[str]:
        """生成可靠性改進建議"""
        try:
            recommendations = []
            
            for factor, data in reliability_factors.items():
                if data['assessment'] == 'poor':
                    if factor == 'success_rate':
                        recommendations.append("提高數據質量和預處理流程以改善成功率")
                    elif factor == 'model_agreement':
                        recommendations.append("調整模型權重或重新訓練組件模型以提高一致性")
                    elif factor == 'prediction_stability':
                        recommendations.append("增加數據平滑處理或調整預測參數以提高穩定性")
                    elif factor == 'confidence_distribution':
                        recommendations.append("優化信心度計算方法或調整決策閾值")
                    elif factor == 'weight_effectiveness':
                        recommendations.append("重新評估和優化組件權重分配")
                elif data['assessment'] == 'fair':
                    if factor == 'model_agreement':
                        recommendations.append("考慮增加模型一致性檢查機制")
                    elif factor == 'prediction_stability':
                        recommendations.append("實施預測結果的時間序列平滑")
            
            if not recommendations:
                recommendations.append("系統可靠性良好，建議定期監控和維護")
            
            return recommendations
        except Exception as e:
            logger.error(f"❌ 生成可靠性建議失敗: {e}")
            return ["建議進行詳細的系統診斷"]
    
    def _calculate_ensemble_overall_score(self, validation_metrics: Dict[str, Any]) -> float:
        """計算集成系統總體評分"""
        try:
            score_components = {}
            
            # 成功率 (20%)
            success_rate = validation_metrics.get('success_rate', 0)
            score_components['success_rate'] = success_rate * 0.2
            
            # 模型一致性 (25%)
            model_agreement = validation_metrics.get('model_agreement', 0)
            score_components['model_agreement'] = model_agreement * 0.25
            
            # 信心度質量 (20%)
            confidence_analysis = validation_metrics.get('confidence_analysis', {})
            if confidence_analysis and 'percentages' in confidence_analysis:
                high_conf_ratio = confidence_analysis['percentages'].get('high_confidence', 0)
                score_components['confidence_quality'] = high_conf_ratio * 0.2
            else:
                score_components['confidence_quality'] = 0.1  # 默認分數
            
            # 權重有效性 (15%)
            weight_effectiveness = validation_metrics.get('weight_effectiveness', {})
            if weight_effectiveness and 'effectiveness_score' in weight_effectiveness:
                score_components['weight_effectiveness'] = weight_effectiveness['effectiveness_score'] * 0.15
            else:
                score_components['weight_effectiveness'] = 0.075  # 默認分數
            
            # 預測穩定性 (10%)
            stability_metrics = validation_metrics.get('prediction_stability', {})
            if stability_metrics:
                avg_stability = np.mean([
                    stability_metrics.get('score_stability', {}).get('stability_score', 0),
                    stability_metrics.get('signal_stability', {}).get('stability_score', 0),
                    stability_metrics.get('confidence_stability', {}).get('stability_score', 0)
                ])
                score_components['prediction_stability'] = avg_stability * 0.1
            else:
                score_components['prediction_stability'] = 0.05  # 默認分數
            
            # 衝突解決能力 (10%)
            conflict_resolution = validation_metrics.get('conflict_resolution', {})
            if conflict_resolution and 'resolution_effectiveness' in conflict_resolution:
                score_components['conflict_resolution'] = conflict_resolution['resolution_effectiveness'] * 0.1
            else:
                score_components['conflict_resolution'] = 0.05  # 默認分數
            
            # 計算總分
            total_score = sum(score_components.values())
            
            return float(total_score)
        except Exception as e:
            logger.error(f"❌ 計算總體評分失敗: {e}")
            return 0.5
    
    def _identify_ensemble_strengths(self, validation_metrics: Dict[str, Any]) -> List[str]:
        """識別集成系統優勢"""
        try:
            strengths = []
            
            # 檢查各項指標
            success_rate = validation_metrics.get('success_rate', 0)
            if success_rate > 0.9:
                strengths.append(f"極高的預測成功率 ({success_rate:.1%})")
            elif success_rate > 0.8:
                strengths.append(f"高預測成功率 ({success_rate:.1%})")
            
            model_agreement = validation_metrics.get('model_agreement', 0)
            if model_agreement > 0.8:
                strengths.append(f"優秀的模型一致性 ({model_agreement:.3f})")
            elif model_agreement > 0.6:
                strengths.append(f"良好的模型一致性 ({model_agreement:.3f})")
            
            confidence_analysis = validation_metrics.get('confidence_analysis', {})
            if confidence_analysis and 'percentages' in confidence_analysis:
                high_conf_ratio = confidence_analysis['percentages'].get('high_confidence', 0)
                if high_conf_ratio > 0.6:
                    strengths.append(f"高比例的高信心度預測 ({high_conf_ratio:.1%})")
            
            weight_effectiveness = validation_metrics.get('weight_effectiveness', {})
            if weight_effectiveness and 'effectiveness_score' in weight_effectiveness:
                eff_score = weight_effectiveness['effectiveness_score']
                if eff_score > 0.7:
                    strengths.append(f"有效的權重配置 (效率: {eff_score:.3f})")
            
            if not strengths:
                strengths.append("系統運行穩定，各項指標均衡")
            
            return strengths
        except Exception as e:
            logger.error(f"❌ 識別系統優勢失敗: {e}")
            return ["系統基本功能正常"]
    
    def _identify_ensemble_weaknesses(self, validation_metrics: Dict[str, Any]) -> List[str]:
        """識別集成系統弱點"""
        try:
            weaknesses = []
            
            # 檢查各項指標
            success_rate = validation_metrics.get('success_rate', 0)
            if success_rate < 0.7:
                weaknesses.append(f"預測成功率偏低 ({success_rate:.1%})")
            
            model_agreement = validation_metrics.get('model_agreement', 0)
            if model_agreement < 0.5:
                weaknesses.append(f"模型一致性不足 ({model_agreement:.3f})")
            
            confidence_analysis = validation_metrics.get('confidence_analysis', {})
            if confidence_analysis and 'percentages' in confidence_analysis:
                low_conf_ratio = confidence_analysis['percentages'].get('low_confidence', 0)
                if low_conf_ratio > 0.4:
                    weaknesses.append(f"低信心度預測比例過高 ({low_conf_ratio:.1%})")
            
            stability_metrics = validation_metrics.get('prediction_stability', {})
            if stability_metrics:
                signal_stability = stability_metrics.get('signal_stability', {}).get('stability_score', 1)
                if signal_stability < 0.6:
                    weaknesses.append(f"信號穩定性不足 ({signal_stability:.3f})")
            
            conflict_resolution = validation_metrics.get('conflict_resolution', {})
            if conflict_resolution:
                conflict_rate = conflict_resolution.get('conflict_cases', 0) / max(conflict_resolution.get('total_predictions', 1), 1)
                if conflict_rate > 0.3:
                    weaknesses.append(f"模型衝突頻率過高 ({conflict_rate:.1%})")
            
            if not weaknesses:
                weaknesses.append("未發現明顯弱點，系統表現良好")
            
            return weaknesses
        except Exception as e:
            logger.error(f"❌ 識別系統弱點失敗: {e}")
            return ["需要進一步分析系統性能"]
    
    def _generate_ensemble_recommendations(self, validation_metrics: Dict[str, Any]) -> List[str]:
        """生成集成系統改進建議"""
        try:
            recommendations = []
            
            # 基於權重優化建議
            weight_optimization = validation_metrics.get('weight_optimization', {})
            if weight_optimization and 'final_recommendation' in weight_optimization:
                final_rec = weight_optimization['final_recommendation']
                if final_rec.get('confidence', 0) > 0.7:
                    recommendations.append("建議採用優化後的權重配置以提升性能")
            
            # 基於衝突解決建議
            conflict_resolution = validation_metrics.get('conflict_resolution', {})
            if conflict_resolution:
                conflict_rate = conflict_resolution.get('conflict_cases', 0) / max(conflict_resolution.get('total_predictions', 1), 1)
                if conflict_rate > 0.2:
                    recommendations.append("建議加強衝突解決機制，考慮增加保守策略")
            
            # 基於模型一致性建議
            model_agreement = validation_metrics.get('model_agreement', 0)
            if model_agreement < 0.6:
                recommendations.append("建議重新評估組件模型，提高模型間一致性")
            
            # 基於信心度分佈建議
            confidence_analysis = validation_metrics.get('confidence_analysis', {})
            if confidence_analysis and 'percentages' in confidence_analysis:
                low_conf_ratio = confidence_analysis['percentages'].get('low_confidence', 0)
                if low_conf_ratio > 0.3:
                    recommendations.append("建議優化信心度計算方法，提高預測信心度")
            
            # 基於穩定性建議
            stability_metrics = validation_metrics.get('prediction_stability', {})
            if stability_metrics:
                signal_stability = stability_metrics.get('signal_stability', {}).get('stability_score', 1)
                if signal_stability < 0.7:
                    recommendations.append("建議增加預測結果的時間序列平滑處理")
            
            # 通用建議
            if not recommendations:
                recommendations.extend([
                    "系統表現良好，建議定期進行驗證和監控",
                    "考慮收集更多歷史數據以進一步優化模型",
                    "建議實施A/B測試來驗證改進效果"
                ])
            
            return recommendations
        except Exception as e:
            logger.error(f"❌ 生成改進建議失敗: {e}")
            return ["建議進行全面的系統評估和優化"]


# 創建全局集成評分器實例
def create_ensemble_scorer() -> EnsembleScorer:
    """創建集成評分器實例"""
    return EnsembleScorer()


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_ensemble_scorer():
        """測試集成評分器"""
        print("🧪 測試集成評分器...")
        
        scorer = create_ensemble_scorer()
        
        # 模擬市場數據
        test_market_data = {
            'current_price': 1500000,
            'price_change_1m': 1.5,
            'volume_ratio': 1.2,
            'ai_formatted_data': '市場顯示上漲趨勢，技術指標看漲'
        }
        
        # 執行分析
        result = scorer.analyze(test_market_data)
        
        print(f"✅ 分析結果:")
        print(f"   成功: {result['success']}")
        print(f"   最終分數: {result['final_score']:.1f}")
        print(f"   交易信號: {result['signal']}")
        print(f"   信心度: {result['confidence']:.1f}%")
        
        if result.get('individual_results'):
            print(f"   個別結果:")
            for component, comp_result in result['individual_results'].items():
                print(f"     {component}: {comp_result['score']:.1f}")
    
    # 運行測試
    asyncio.run(test_ensemble_scorer())
    
    def _optimize_weights_by_accuracy(self, individual_scores: Dict[str, List[float]], 
                                    ground_truth: List[str], signals: List[str]) -> Dict[str, float]:
        """基於準確性優化權重"""
        try:
            # 這裡可以實現更複雜的基於準確性的權重優化
            # 暫時返回基於當前權重的調整
            component_accuracies = {}
            
            for component in individual_scores.keys():
                # 模擬計算每個組件對準確性的貢獻
                # 實際實現中可以使用更複雜的方法
                component_accuracies[component] = np.random.uniform(0.4, 0.8)
            
            # 標準化準確性作為權重
            total_acc = sum(component_accuracies.values())
            if total_acc > 0:
                optimized_weights = {k: v / total_acc for k, v in component_accuracies.items()}
            else:
                optimized_weights = {k: 1.0 / len(component_accuracies) for k in component_accuracies.keys()}
            
            return optimized_weights
        except Exception as e:
            logger.error(f"❌ 基於準確性優化權重失敗: {e}")
            return {}
    
    def _optimize_weights_by_variance(self, individual_scores: Dict[str, List[float]]) -> Dict[str, float]:
        """基於方差優化權重"""
        try:
            variances = {}
            for component, scores in individual_scores.items():
                if scores:
                    # 方差越小，權重越高（更穩定的組件獲得更高權重）
                    variance = np.var(scores)
                    variances[component] = 1.0 / (1.0 + variance)
            
            # 標準化方差倒數作為權重
            total_inv_var = sum(variances.values())
            if total_inv_var > 0:
                optimized_weights = {k: v / total_inv_var for k, v in variances.items()}
            else:
                optimized_weights = {k: 1.0 / len(variances) for k in variances.keys()}
            
            return optimized_weights
        except Exception as e:
            logger.error(f"❌ 基於方差優化權重失敗: {e}")
            return {}
    
    def _generate_weight_recommendation(self, optimization_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成最終權重建議"""
        try:
            if not optimization_results:
                return {}
            
            # 合併不同優化方法的結果
            all_components = set()
            for method_results in optimization_results.values():
                if isinstance(method_results, dict):
                    all_components.update(method_results.keys())
            
            final_weights = {}
            for component in all_components:
                weights_for_component = []
                for method_name, method_results in optimization_results.items():
                    if isinstance(method_results, dict) and component in method_results:
                        weights_for_component.append(method_results[component])
                
                if weights_for_component:
                    final_weights[component] = np.mean(weights_for_component)
            
            # 標準化最終權重
            total_weight = sum(final_weights.values())
            if total_weight > 0:
                final_weights = {k: v / total_weight for k, v in final_weights.items()}
            
            # 計算與當前權重的差異
            weight_changes = {}
            for component in final_weights:
                current_weight = self.weights.get(component, 0)
                recommended_weight = final_weights[component]
                weight_changes[component] = {
                    'current': current_weight,
                    'recommended': recommended_weight,
                    'change': recommended_weight - current_weight,
                    'change_percentage': ((recommended_weight - current_weight) / current_weight * 100) if current_weight > 0 else 0
                }
            
            return {
                'recommended_weights': final_weights,
                'weight_changes': weight_changes,
                'improvement_potential': self._estimate_improvement_potential(weight_changes)
            }
        except Exception as e:
            logger.error(f"❌ 生成權重建議失敗: {e}")
            return {}
    
    def _estimate_improvement_potential(self, weight_changes: Dict[str, Any]) -> float:
        """估算改進潛力"""
        try:
            if not weight_changes:
                return 0.0
            
            # 基於權重變化幅度估算改進潛力
            total_change = sum(abs(change['change']) for change in weight_changes.values())
            improvement_potential = min(total_change * 0.1, 0.2)  # 最大20%的改進潛力
            
            return float(improvement_potential)
        except Exception as e:
            logger.error(f"❌ 估算改進潛力失敗: {e}")
            return 0.0
    
    def _evaluate_conflict_resolution(self, individual_scores: Dict[str, List[float]], 
                                    signals: List[str]) -> Dict[str, Any]:
        """評估衝突解決機制"""
        try:
            if not individual_scores or not signals:
                return {}
            
            # 檢測分數分歧情況
            conflicts_detected = 0
            conflict_resolutions = []
            
            max_len = max(len(scores) for scores in individual_scores.values() if scores)
            
            for i in range(max_len):
                scores_at_i = []
                for scores in individual_scores.values():
                    if i < len(scores):
                        scores_at_i.append(scores[i])
                
                if len(scores_at_i) > 1:
                    std_at_i = np.std(scores_at_i)
                    if std_at_i > 15:  # 分歧閾值
                        conflicts_detected += 1
                        if i < len(signals):
                            conflict_resolutions.append(signals[i])
            
            # 分析衝突解決效果
            resolution_effectiveness = self._analyze_conflict_resolution_effectiveness(conflict_resolutions)
            
            return {
                'conflicts_detected': conflicts_detected,
                'conflict_rate': conflicts_detected / max_len if max_len > 0 else 0,
                'resolution_strategies': conflict_resolutions,
                'resolution_effectiveness': resolution_effectiveness,
                'hold_bias': conflict_resolutions.count('HOLD') / len(conflict_resolutions) if conflict_resolutions else 0
            }
        except Exception as e:
            logger.error(f"❌ 評估衝突解決機制失敗: {e}")
            return {}
    
    def _analyze_conflict_resolution_effectiveness(self, resolutions: List[str]) -> Dict[str, Any]:
        """分析衝突解決有效性"""
        try:
            if not resolutions:
                return {}
            
            resolution_counts = {}
            for resolution in resolutions:
                resolution_counts[resolution] = resolution_counts.get(resolution, 0) + 1
            
            # 評估解決策略的多樣性
            diversity = len(resolution_counts) / 3  # 3是可能的信號數量
            
            # 評估保守性 (HOLD信號的比例)
            conservatism = resolution_counts.get('HOLD', 0) / len(resolutions)
            
            return {
                'resolution_distribution': resolution_counts,
                'strategy_diversity': diversity,
                'conservatism_level': conservatism,
                'effectiveness_score': (diversity + (1 - conservatism)) / 2  # 平衡多樣性和保守性
            }
        except Exception as e:
            logger.error(f"❌ 分析衝突解決有效性失敗: {e}")
            return {}
    
    def _assess_ensemble_reliability(self, validation_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """評估集成可靠性"""
        try:
            reliability_factors = {}
            
            # 成功率可靠性
            success_rate = validation_metrics.get('success_rate', 0)
            reliability_factors['success_rate'] = success_rate
            
            # 一致性可靠性
            model_agreement = validation_metrics.get('model_agreement', 0)
            reliability_factors['consistency'] = model_agreement
            
            # 穩定性可靠性
            stability_metrics = validation_metrics.get('prediction_stability', {})
            if stability_metrics:
                avg_stability = np.mean([
                    stability_metrics.get('score_stability', {}).get('stability_score', 0),
                    stability_metrics.get('signal_stability', {}).get('stability_score', 0),
                    stability_metrics.get('confidence_stability', {}).get('stability_score', 0)
                ])
                reliability_factors['stability'] = avg_stability
            
            # 權重有效性可靠性
            weight_effectiveness = validation_metrics.get('weight_effectiveness', {})
            effectiveness_score = weight_effectiveness.get('effectiveness_score', 0)
            reliability_factors['weight_effectiveness'] = effectiveness_score
            
            # 計算整體可靠性分數
            overall_reliability = np.mean(list(reliability_factors.values()))
            
            # 可靠性等級
            if overall_reliability >= 0.8:
                reliability_grade = "優秀"
            elif overall_reliability >= 0.7:
                reliability_grade = "良好"
            elif overall_reliability >= 0.6:
                reliability_grade = "中等"
            elif overall_reliability >= 0.5:
                reliability_grade = "及格"
            else:
                reliability_grade = "需要改進"
            
            return {
                'reliability_factors': reliability_factors,
                'overall_reliability': overall_reliability,
                'reliability_grade': reliability_grade,
                'confidence_level': self._calculate_reliability_confidence(reliability_factors)
            }
        except Exception as e:
            logger.error(f"❌ 評估集成可靠性失敗: {e}")
            return {}
    
    def _calculate_reliability_confidence(self, reliability_factors: Dict[str, float]) -> float:
        """計算可靠性信心度"""
        try:
            if not reliability_factors:
                return 0.0
            
            # 基於各因素的方差計算信心度
            values = list(reliability_factors.values())
            variance = np.var(values)
            
            # 方差越小，信心度越高
            confidence = 1.0 / (1.0 + variance)
            
            return float(confidence)
        except Exception as e:
            logger.error(f"❌ 計算可靠性信心度失敗: {e}")
            return 0.5
    
    def _calculate_ensemble_overall_score(self, validation_metrics: Dict[str, Any]) -> float:
        """計算集成整體評分"""
        try:
            score_components = {}
            
            # 成功率 (25%)
            success_rate = validation_metrics.get('success_rate', 0)
            score_components['success_rate'] = success_rate * 0.25
            
            # 模型一致性 (20%)
            model_agreement = validation_metrics.get('model_agreement', 0)
            score_components['consistency'] = model_agreement * 0.20
            
            # 預測穩定性 (20%)
            stability_metrics = validation_metrics.get('prediction_stability', {})
            if stability_metrics:
                avg_stability = np.mean([
                    stability_metrics.get('score_stability', {}).get('stability_score', 0),
                    stability_metrics.get('signal_stability', {}).get('stability_score', 0),
                    stability_metrics.get('confidence_stability', {}).get('stability_score', 0)
                ])
                score_components['stability'] = avg_stability * 0.20
            
            # 權重有效性 (15%)
            weight_effectiveness = validation_metrics.get('weight_effectiveness', {})
            effectiveness_score = weight_effectiveness.get('effectiveness_score', 0)
            score_components['weight_effectiveness'] = effectiveness_score * 0.15
            
            # 信心度分析 (10%)
            confidence_analysis = validation_metrics.get('confidence_analysis', {})
            if confidence_analysis and 'statistics' in confidence_analysis:
                avg_confidence = confidence_analysis['statistics'].get('mean', 0) / 100
                score_components['confidence'] = avg_confidence * 0.10
            
            # 衝突解決 (10%)
            conflict_resolution = validation_metrics.get('conflict_resolution', {})
            resolution_effectiveness = conflict_resolution.get('resolution_effectiveness', {})
            if resolution_effectiveness:
                effectiveness = resolution_effectiveness.get('effectiveness_score', 0)
                score_components['conflict_resolution'] = effectiveness * 0.10
            
            # 計算總分
            total_score = sum(score_components.values())
            
            return min(1.0, max(0.0, total_score))
        except Exception as e:
            logger.error(f"❌ 計算集成整體評分失敗: {e}")
            return 0.0
    
    def _identify_ensemble_strengths(self, validation_metrics: Dict[str, Any]) -> List[str]:
        """識別集成優勢"""
        try:
            strengths = []
            
            # 檢查成功率
            success_rate = validation_metrics.get('success_rate', 0)
            if success_rate > 0.9:
                strengths.append(f"極高的預測成功率 ({success_rate:.1%})")
            elif success_rate > 0.8:
                strengths.append(f"高預測成功率 ({success_rate:.1%})")
            
            # 檢查模型一致性
            model_agreement = validation_metrics.get('model_agreement', 0)
            if model_agreement > 0.8:
                strengths.append(f"優秀的模型一致性 ({model_agreement:.3f})")
            elif model_agreement > 0.7:
                strengths.append(f"良好的模型一致性 ({model_agreement:.3f})")
            
            # 檢查信心度
            confidence_analysis = validation_metrics.get('confidence_analysis', {})
            if confidence_analysis and 'statistics' in confidence_analysis:
                avg_confidence = confidence_analysis['statistics'].get('mean', 0)
                if avg_confidence > 80:
                    strengths.append(f"高平均信心度 ({avg_confidence:.1f}%)")
            
            # 檢查穩定性
            stability_metrics = validation_metrics.get('prediction_stability', {})
            if stability_metrics:
                signal_stability = stability_metrics.get('signal_stability', {}).get('stability_score', 0)
                if signal_stability > 0.8:
                    strengths.append(f"優秀的信號穩定性 ({signal_stability:.3f})")
            
            # 檢查權重有效性
            weight_effectiveness = validation_metrics.get('weight_effectiveness', {})
            effectiveness_score = weight_effectiveness.get('effectiveness_score', 0)
            if effectiveness_score > 0.7:
                strengths.append(f"有效的權重配置 ({effectiveness_score:.3f})")
            
            return strengths
        except Exception as e:
            logger.error(f"❌ 識別集成優勢失敗: {e}")
            return []
    
    def _identify_ensemble_weaknesses(self, validation_metrics: Dict[str, Any]) -> List[str]:
        """識別集成弱點"""
        try:
            weaknesses = []
            
            # 檢查成功率
            success_rate = validation_metrics.get('success_rate', 0)
            if success_rate < 0.7:
                weaknesses.append(f"預測成功率偏低 ({success_rate:.1%})")
            
            # 檢查模型一致性
            model_agreement = validation_metrics.get('model_agreement', 0)
            if model_agreement < 0.5:
                weaknesses.append(f"模型一致性不足 ({model_agreement:.3f})")
            
            # 檢查信心度
            confidence_analysis = validation_metrics.get('confidence_analysis', {})
            if confidence_analysis and 'statistics' in confidence_analysis:
                avg_confidence = confidence_analysis['statistics'].get('mean', 0)
                if avg_confidence < 60:
                    weaknesses.append(f"平均信心度偏低 ({avg_confidence:.1f}%)")
            
            # 檢查穩定性
            stability_metrics = validation_metrics.get('prediction_stability', {})
            if stability_metrics:
                signal_stability = stability_metrics.get('signal_stability', {}).get('stability_score', 0)
                if signal_stability < 0.6:
                    weaknesses.append(f"信號穩定性不足 ({signal_stability:.3f})")
            
            # 檢查衝突解決
            conflict_resolution = validation_metrics.get('conflict_resolution', {})
            conflict_rate = conflict_resolution.get('conflict_rate', 0)
            if conflict_rate > 0.3:
                weaknesses.append(f"模型衝突頻率過高 ({conflict_rate:.1%})")
            
            # 檢查權重平衡
            weight_effectiveness = validation_metrics.get('weight_effectiveness', {})
            weight_balance = weight_effectiveness.get('weight_balance', {})
            if weight_balance:
                balance_score = weight_balance.get('balance_score', 0)
                if balance_score < 0.5:
                    weaknesses.append(f"權重配置不平衡 ({balance_score:.3f})")
            
            return weaknesses
        except Exception as e:
            logger.error(f"❌ 識別集成弱點失敗: {e}")
            return []
    
    def _generate_ensemble_recommendations(self, validation_metrics: Dict[str, Any]) -> List[str]:
        """生成集成改進建議"""
        try:
            recommendations = []
            
            # 基於弱點生成建議
            weaknesses = self._identify_ensemble_weaknesses(validation_metrics)
            
            if any("成功率偏低" in w for w in weaknesses):
                recommendations.append("檢查輸入數據質量和特徵工程")
                recommendations.append("考慮添加更多有效的分析組件")
            
            if any("一致性不足" in w for w in weaknesses):
                recommendations.append("重新評估各組件的分析邏輯")
                recommendations.append("考慮使用更相似的分析方法")
            
            if any("信心度偏低" in w for w in weaknesses):
                recommendations.append("優化信心度計算方法")
                recommendations.append("增加更多驗證指標")
            
            if any("穩定性不足" in w for w in weaknesses):
                recommendations.append("增加預測結果的平滑機制")
                recommendations.append("考慮使用移動平均或其他穩定化技術")
            
            if any("衝突頻率過高" in w for w in weaknesses):
                recommendations.append("優化衝突解決機制")
                recommendations.append("考慮調整組件權重以減少分歧")
            
            if any("權重配置不平衡" in w for w in weaknesses):
                recommendations.append("使用權重優化建議重新配置權重")
                recommendations.append("考慮動態權重調整機制")
            
            # 權重優化建議
            weight_optimization = validation_metrics.get('weight_optimization', {})
            final_recommendation = weight_optimization.get('final_recommendation', {})
            if final_recommendation and 'improvement_potential' in final_recommendation:
                potential = final_recommendation['improvement_potential']
                if potential > 0.05:
                    recommendations.append(f"應用權重優化建議可能帶來 {potential:.1%} 的性能提升")
            
            # 通用建議
            if not recommendations:
                recommendations.append("集成系統表現良好，可考慮微調參數進一步優化")
            
            return recommendations
        except Exception as e:
            logger.error(f"❌ 生成集成改進建議失敗: {e}")
            return []
    
    def get_ensemble_validation_report(self) -> Dict[str, Any]:
        """獲取完整的集成驗證報告"""
        try:
            # 這個方法需要先運行validate_ensemble才能獲取報告
            return {
                'message': '請先運行 validate_ensemble() 方法進行驗證',
                'usage': 'validation_result = scorer.validate_ensemble(test_data, ground_truth)'
            }
        except Exception as e:
            logger.error(f"❌ 獲取集成驗證報告失敗: {e}")
            return {'error': str(e)}


def create_ensemble_scorer() -> EnsembleScorer:
    """創建集成評分器實例"""
    return EnsembleScorer()


# 測試代碼
if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 創建集成評分器
    scorer = create_ensemble_scorer()
    
    # 測試數據
    test_data = {
        'current_price': 1500000,
        'price_change_1m': 0.5,
        'volume_ratio': 1.1,
        'ai_formatted_data': '市場呈現上漲趨勢'
    }
    
    # 測試分析
    result = scorer.analyze(test_data)
    
    print(f"✅ 集成分析結果:")
    print(f"最終分數: {result['final_score']:.1f}")
    print(f"交易信號: {result['signal']}")
    print(f"信心度: {result['confidence']:.1f}%")
    print(f"成功: {result['success']}")