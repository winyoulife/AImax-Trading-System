#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型驗證報告系統 - 統一的模型性能比較和選擇建議
"""

import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# 導入相關模塊
try:
    from ..ml.price_predictor import create_lstm_predictor
    from ..ml.ensemble_scorer import create_ensemble_scorer
    from ..data.historical_data_manager import create_historical_data_manager
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False
    print("⚠️ 部分模塊未完全可用")

logger = logging.getLogger(__name__)

@dataclass
class ModelPerformanceMetrics:
    """模型性能指標"""
    model_name: str
    model_type: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confidence_avg: float
    confidence_std: float
    prediction_count: int
    success_rate: float
    processing_time: float
    memory_usage: float
    stability_score: float
    reliability_score: float
    last_updated: str

@dataclass
class ModelComparisonResult:
    """模型比較結果"""
    best_overall_model: str
    best_accuracy_model: str
    best_stability_model: str
    best_speed_model: str
    model_rankings: Dict[str, int]
    performance_matrix: Dict[str, Dict[str, float]]
    recommendations: List[str]
    comparison_summary: str

class ModelValidationReportGenerator:
    """模型驗證報告生成器"""
    
    def __init__(self, output_dir: str = "AImax/reports"):
        """
        初始化報告生成器
        
        Args:
            output_dir: 報告輸出目錄
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 模型性能數據存儲
        self.model_metrics = {}
        self.validation_history = []
        self.comparison_results = None
        
        # 報告配置
        self.report_config = {
            'include_charts': True,
            'include_detailed_analysis': True,
            'include_recommendations': True,
            'chart_style': 'seaborn',
            'output_formats': ['json', 'html', 'pdf']
        }
        
        logger.info("📊 模型驗證報告生成器初始化完成")
    
    async def validate_all_models(self, test_data: List[Dict[str, Any]], 
                                ground_truth: List[str] = None) -> Dict[str, Any]:
        """
        驗證所有可用模型
        
        Args:
            test_data: 測試數據
            ground_truth: 真實標籤
            
        Returns:
            所有模型的驗證結果
        """
        try:
            logger.info("🔍 開始驗證所有模型...")
            
            if not MODULES_AVAILABLE:
                logger.warning("⚠️ 使用模擬模式進行驗證 (部分模塊不可用)")
            
            validation_results = {}
            
            # 1. 驗證LSTM價格預測器
            lstm_result = await self._validate_lstm_model(test_data, ground_truth)
            if lstm_result['success']:
                validation_results['lstm_predictor'] = lstm_result
                logger.info("✅ LSTM模型驗證完成")
            else:
                logger.warning(f"⚠️ LSTM模型驗證失敗: {lstm_result.get('error')}")
            
            # 2. 驗證集成評分器
            ensemble_result = await self._validate_ensemble_model(test_data, ground_truth)
            if ensemble_result['success']:
                validation_results['ensemble_scorer'] = ensemble_result
                logger.info("✅ 集成評分器驗證完成")
            else:
                logger.warning(f"⚠️ 集成評分器驗證失敗: {ensemble_result.get('error')}")
            
            # 3. 驗證其他可用模型 (如果有的話)
            # 這裡可以添加更多模型的驗證
            
            if not validation_results:
                return {'success': False, 'error': 'No models successfully validated'}
            
            # 4. 生成模型比較分析
            comparison_analysis = self._generate_model_comparison(validation_results)
            
            # 5. 更新模型性能指標
            self._update_model_metrics(validation_results)
            
            # 6. 生成統一報告
            unified_report = self._generate_unified_report(validation_results, comparison_analysis)
            
            logger.info(f"✅ 所有模型驗證完成: {len(validation_results)} 個模型")
            
            return {
                'success': True,
                'validation_results': validation_results,
                'comparison_analysis': comparison_analysis,
                'unified_report': unified_report,
                'models_validated': list(validation_results.keys()),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 模型驗證失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _validate_lstm_model(self, test_data: List[Dict[str, Any]], 
                                 ground_truth: List[str] = None) -> Dict[str, Any]:
        """驗證LSTM模型"""
        try:
            if not MODULES_AVAILABLE:
                # 模擬LSTM模型驗證結果
                return self._simulate_lstm_validation(test_data, ground_truth)
            
            # 創建LSTM預測器
            lstm_predictor = create_lstm_predictor()
            
            # 準備LSTM測試數據
            lstm_test_data = []
            for data in test_data:
                # 轉換為LSTM所需的格式
                lstm_data = {
                    'prices': [data.get('current_price', 1500000)],
                    'volumes': [data.get('volume', 1000)],
                    'timestamps': [datetime.now()]
                }
                lstm_test_data.append(lstm_data)
            
            # 執行LSTM驗證
            start_time = datetime.now()
            predictions = []
            confidences = []
            
            for data in lstm_test_data:
                try:
                    # 調用LSTM預測
                    if hasattr(lstm_predictor, 'validate_model'):
                        result = await lstm_predictor.validate_model(data)
                    else:
                        # 如果沒有驗證方法，使用預測方法
                        result = await lstm_predictor.predict_price_trend(data)
                    
                    if result.get('success'):
                        predictions.append(result.get('prediction', 'HOLD'))
                        confidences.append(result.get('confidence', 0.5))
                    else:
                        predictions.append('HOLD')
                        confidences.append(0.0)
                        
                except Exception as e:
                    logger.warning(f"LSTM預測失敗: {e}")
                    predictions.append('HOLD')
                    confidences.append(0.0)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 計算性能指標
            metrics = self._calculate_model_metrics(
                'LSTM Price Predictor', 'deep_learning',
                predictions, ground_truth, confidences, processing_time
            )
            
            return {
                'success': True,
                'model_name': 'LSTM Price Predictor',
                'model_type': 'deep_learning',
                'predictions': predictions,
                'confidences': confidences,
                'metrics': metrics,
                'processing_time': processing_time,
                'validation_details': {
                    'test_samples': len(test_data),
                    'successful_predictions': len([p for p in predictions if p != 'HOLD']),
                    'average_confidence': np.mean(confidences) if confidences else 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ LSTM模型驗證失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    def _simulate_lstm_validation(self, test_data: List[Dict[str, Any]], 
                                ground_truth: List[str] = None) -> Dict[str, Any]:
        """模擬LSTM模型驗證結果"""
        try:
            logger.info("🔄 使用模擬LSTM模型進行驗證...")
            
            predictions = []
            confidences = []
            
            # 模擬LSTM預測邏輯
            for data in test_data:
                price_change = data.get('price_change_1m', 0)
                
                # 基於價格變化的簡單預測邏輯
                if price_change > 1.5:
                    pred = 'BUY'
                    conf = min(0.9, 0.6 + abs(price_change) * 0.1)
                elif price_change < -1.5:
                    pred = 'SELL'
                    conf = min(0.9, 0.6 + abs(price_change) * 0.1)
                else:
                    pred = 'HOLD'
                    conf = 0.5 + np.random.normal(0, 0.1)
                
                # 添加一些隨機性
                if np.random.random() < 0.1:  # 10%的隨機性
                    pred = np.random.choice(['BUY', 'SELL', 'HOLD'])
                    conf = np.random.uniform(0.3, 0.8)
                
                predictions.append(pred)
                confidences.append(max(0.1, min(0.95, conf)))
            
            processing_time = len(test_data) * 0.02  # 模擬處理時間
            
            # 計算性能指標
            metrics = self._calculate_model_metrics(
                'LSTM Price Predictor (Simulated)', 'deep_learning',
                predictions, ground_truth, confidences, processing_time
            )
            
            return {
                'success': True,
                'model_name': 'LSTM Price Predictor (Simulated)',
                'model_type': 'deep_learning',
                'predictions': predictions,
                'confidences': confidences,
                'metrics': metrics,
                'processing_time': processing_time,
                'validation_details': {
                    'test_samples': len(test_data),
                    'successful_predictions': len([p for p in predictions if p != 'HOLD']),
                    'average_confidence': np.mean(confidences) if confidences else 0.0,
                    'simulation_note': 'This is a simulated LSTM model for testing purposes'
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 模擬LSTM驗證失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _validate_ensemble_model(self, test_data: List[Dict[str, Any]], 
                                     ground_truth: List[str] = None) -> Dict[str, Any]:
        """驗證集成評分器模型"""
        try:
            if not MODULES_AVAILABLE:
                # 模擬集成評分器驗證結果
                return self._simulate_ensemble_validation(test_data, ground_truth)
            
            # 創建集成評分器
            ensemble_scorer = create_ensemble_scorer()
            
            # 執行集成評分器驗證
            start_time = datetime.now()
            
            # 使用集成評分器的內建驗證方法
            validation_result = ensemble_scorer.validate_ensemble(test_data, ground_truth)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if not validation_result['success']:
                return {'success': False, 'error': validation_result.get('error')}
            
            # 提取關鍵指標
            validation_metrics = validation_result['validation_metrics']
            
            # 生成預測結果
            predictions = []
            confidences = []
            
            for data in test_data:
                result = ensemble_scorer.analyze(data)
                if result['success']:
                    predictions.append(result['signal'])
                    confidences.append(result['confidence'])
                else:
                    predictions.append('HOLD')
                    confidences.append(0.0)
            
            # 計算統一的性能指標
            metrics = self._calculate_model_metrics(
                'Ensemble Scorer', 'ensemble',
                predictions, ground_truth, confidences, processing_time
            )
            
            # 添加集成特定指標
            metrics.update({
                'model_agreement': validation_metrics.get('model_agreement', 0),
                'weight_effectiveness': validation_metrics.get('weight_effectiveness', {}).get('effectiveness_score', 0),
                'reliability_score': validation_metrics.get('reliability_assessment', {}).get('overall_score', 0)
            })
            
            return {
                'success': True,
                'model_name': 'Ensemble Scorer',
                'model_type': 'ensemble',
                'predictions': predictions,
                'confidences': confidences,
                'metrics': metrics,
                'processing_time': processing_time,
                'validation_details': validation_metrics,
                'ensemble_specific': {
                    'component_count': 3,
                    'weight_optimization': validation_metrics.get('weight_optimization', {}),
                    'conflict_resolution': validation_metrics.get('conflict_resolution', {})
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 集成評分器驗證失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    def _simulate_ensemble_validation(self, test_data: List[Dict[str, Any]], 
                                    ground_truth: List[str] = None) -> Dict[str, Any]:
        """模擬集成評分器驗證結果"""
        try:
            logger.info("🔄 使用模擬集成評分器進行驗證...")
            
            predictions = []
            confidences = []
            
            # 模擬集成評分器預測邏輯
            for data in test_data:
                price_change = data.get('price_change_1m', 0)
                volume_ratio = data.get('volume_ratio', 1.0)
                ai_data = data.get('ai_formatted_data', '')
                
                # 多因子綜合評分
                score = 50  # 基準分數
                
                # 價格變化因子
                if price_change > 1:
                    score += min(15, price_change * 5)
                elif price_change < -1:
                    score -= min(15, abs(price_change) * 5)
                
                # 成交量因子
                if volume_ratio > 1.2:
                    score += 5
                elif volume_ratio < 0.8:
                    score -= 3
                
                # AI數據因子
                if '上漲' in ai_data or '看漲' in ai_data:
                    score += 8
                elif '下跌' in ai_data or '看跌' in ai_data:
                    score -= 8
                
                # 生成預測和信心度
                if score > 60:
                    pred = 'BUY'
                    conf = min(0.95, 0.6 + (score - 60) / 100)
                elif score < 40:
                    pred = 'SELL'
                    conf = min(0.95, 0.6 + (40 - score) / 100)
                else:
                    pred = 'HOLD'
                    conf = 0.5 + np.random.normal(0, 0.1)
                
                # 添加一些隨機性
                if np.random.random() < 0.05:  # 5%的隨機性
                    pred = np.random.choice(['BUY', 'SELL', 'HOLD'])
                    conf = np.random.uniform(0.4, 0.9)
                
                predictions.append(pred)
                confidences.append(max(0.1, min(0.95, conf)))
            
            processing_time = len(test_data) * 0.03  # 模擬處理時間
            
            # 計算性能指標
            metrics = self._calculate_model_metrics(
                'Ensemble Scorer (Simulated)', 'ensemble',
                predictions, ground_truth, confidences, processing_time
            )
            
            # 添加模擬的集成特定指標
            metrics.update({
                'model_agreement': 0.85 + np.random.normal(0, 0.05),
                'weight_effectiveness': 0.75 + np.random.normal(0, 0.1),
                'reliability_score': 0.80 + np.random.normal(0, 0.08)
            })
            
            # 模擬驗證詳情
            validation_details = {
                'prediction_count': len(predictions),
                'success_rate': 1.0,
                'model_agreement': metrics['model_agreement'],
                'simulation_note': 'This is a simulated ensemble scorer for testing purposes'
            }
            
            return {
                'success': True,
                'model_name': 'Ensemble Scorer (Simulated)',
                'model_type': 'ensemble',
                'predictions': predictions,
                'confidences': confidences,
                'metrics': metrics,
                'processing_time': processing_time,
                'validation_details': validation_details,
                'ensemble_specific': {
                    'component_count': 3,
                    'weight_optimization': {'simulated': True},
                    'conflict_resolution': {'simulated': True}
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 模擬集成評分器驗證失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_model_metrics(self, model_name: str, model_type: str,
                               predictions: List[str], ground_truth: List[str] = None,
                               confidences: List[float] = None,
                               processing_time: float = 0.0) -> Dict[str, Any]:
        """計算統一的模型性能指標"""
        try:
            metrics = {
                'model_name': model_name,
                'model_type': model_type,
                'prediction_count': len(predictions),
                'processing_time': processing_time,
                'predictions_per_second': len(predictions) / max(processing_time, 0.001)
            }
            
            # 信心度統計
            if confidences:
                metrics.update({
                    'confidence_avg': np.mean(confidences),
                    'confidence_std': np.std(confidences),
                    'confidence_min': np.min(confidences),
                    'confidence_max': np.max(confidences),
                    'high_confidence_ratio': sum(1 for c in confidences if c > 0.8) / len(confidences)
                })
            else:
                metrics.update({
                    'confidence_avg': 0.0,
                    'confidence_std': 0.0,
                    'confidence_min': 0.0,
                    'confidence_max': 0.0,
                    'high_confidence_ratio': 0.0
                })
            
            # 預測分佈
            prediction_counts = {}
            for pred in predictions:
                prediction_counts[pred] = prediction_counts.get(pred, 0) + 1
            
            metrics['prediction_distribution'] = prediction_counts
            metrics['prediction_diversity'] = len(prediction_counts)
            
            # 如果有真實標籤，計算準確性指標
            if ground_truth and len(ground_truth) == len(predictions):
                accuracy_metrics = self._calculate_accuracy_metrics(predictions, ground_truth)
                metrics.update(accuracy_metrics)
            else:
                # 默認準確性指標
                metrics.update({
                    'accuracy': 0.0,
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1_score': 0.0,
                    'macro_f1': 0.0
                })
            
            # 穩定性評估
            stability_score = self._calculate_stability_score(predictions, confidences)
            metrics['stability_score'] = stability_score
            
            # 成功率
            successful_predictions = sum(1 for p in predictions if p != 'HOLD')
            metrics['success_rate'] = successful_predictions / len(predictions) if predictions else 0.0
            
            # 內存使用估算 (簡化)
            metrics['memory_usage_mb'] = len(predictions) * 0.1  # 估算值
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ 計算模型指標失敗: {e}")
            return {}
    
    def _calculate_accuracy_metrics(self, predictions: List[str], 
                                  ground_truth: List[str]) -> Dict[str, float]:
        """計算準確性指標"""
        try:
            if len(predictions) != len(ground_truth):
                return {}
            
            # 總體準確率
            correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
            accuracy = correct / len(predictions)
            
            # 各類別指標
            unique_labels = list(set(predictions + ground_truth))
            class_metrics = {}
            
            for label in unique_labels:
                tp = sum(1 for p, g in zip(predictions, ground_truth) if p == label and g == label)
                fp = sum(1 for p, g in zip(predictions, ground_truth) if p == label and g != label)
                fn = sum(1 for p, g in zip(predictions, ground_truth) if p != label and g == label)
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                
                class_metrics[label] = {
                    'precision': precision,
                    'recall': recall,
                    'f1_score': f1,
                    'support': sum(1 for g in ground_truth if g == label)
                }
            
            # 宏平均
            macro_precision = np.mean([m['precision'] for m in class_metrics.values()])
            macro_recall = np.mean([m['recall'] for m in class_metrics.values()])
            macro_f1 = np.mean([m['f1_score'] for m in class_metrics.values()])
            
            return {
                'accuracy': accuracy,
                'precision': macro_precision,
                'recall': macro_recall,
                'f1_score': macro_f1,
                'macro_f1': macro_f1,
                'class_metrics': class_metrics,
                'correct_predictions': correct,
                'total_predictions': len(predictions)
            }
            
        except Exception as e:
            logger.error(f"❌ 計算準確性指標失敗: {e}")
            return {}
    
    def _calculate_stability_score(self, predictions: List[str], 
                                 confidences: List[float] = None) -> float:
        """計算穩定性分數"""
        try:
            if len(predictions) < 2:
                return 1.0
            
            # 預測變化穩定性
            prediction_changes = sum(1 for i in range(1, len(predictions)) 
                                   if predictions[i] != predictions[i-1])
            prediction_stability = 1.0 - (prediction_changes / (len(predictions) - 1))
            
            # 信心度穩定性
            confidence_stability = 1.0
            if confidences and len(confidences) > 1:
                confidence_changes = [abs(confidences[i] - confidences[i-1]) 
                                    for i in range(1, len(confidences))]
                avg_change = np.mean(confidence_changes)
                confidence_stability = 1.0 / (1.0 + avg_change)
            
            # 綜合穩定性分數
            stability_score = (prediction_stability + confidence_stability) / 2
            
            return float(stability_score)
            
        except Exception as e:
            logger.error(f"❌ 計算穩定性分數失敗: {e}")
            return 0.5
    
    def _generate_model_comparison(self, validation_results: Dict[str, Any]) -> ModelComparisonResult:
        """生成模型比較分析"""
        try:
            logger.info("📊 生成模型比較分析...")
            
            if len(validation_results) < 2:
                logger.warning("⚠️ 模型數量不足，無法進行有效比較")
                return ModelComparisonResult(
                    best_overall_model=list(validation_results.keys())[0] if validation_results else 'none',
                    best_accuracy_model='none',
                    best_stability_model='none',
                    best_speed_model='none',
                    model_rankings={},
                    performance_matrix={},
                    recommendations=['需要更多模型進行比較'],
                    comparison_summary='模型��量不足'
                )
            
            # 提取所有模型的關鍵指標
            models_data = {}
            for model_name, result in validation_results.items():
                if result['success']:
                    metrics = result['metrics']
                    models_data[model_name] = {
                        'accuracy': metrics.get('accuracy', 0),
                        'f1_score': metrics.get('f1_score', 0),
                        'confidence_avg': metrics.get('confidence_avg', 0),
                        'stability_score': metrics.get('stability_score', 0),
                        'processing_time': metrics.get('processing_time', float('inf')),
                        'predictions_per_second': metrics.get('predictions_per_second', 0),
                        'success_rate': metrics.get('success_rate', 0),
                        'reliability_score': metrics.get('reliability_score', 0)
                    }
            
            if not models_data:
                return ModelComparisonResult(
                    best_overall_model='none',
                    best_accuracy_model='none',
                    best_stability_model='none',
                    best_speed_model='none',
                    model_rankings={},
                    performance_matrix={},
                    recommendations=['所有模型驗證失敗'],
                    comparison_summary='無有效模型數據'
                )
            
            # 找出各項最佳模型
            best_accuracy_model = max(models_data.keys(), 
                                    key=lambda x: models_data[x]['accuracy'])
            best_stability_model = max(models_data.keys(), 
                                     key=lambda x: models_data[x]['stability_score'])
            best_speed_model = max(models_data.keys(), 
                                 key=lambda x: models_data[x]['predictions_per_second'])
            
            # 計算綜合評分
            overall_scores = {}
            for model_name, data in models_data.items():
                # 綜合評分權重
                weights = {
                    'accuracy': 0.25,
                    'f1_score': 0.20,
                    'confidence_avg': 0.15,
                    'stability_score': 0.15,
                    'success_rate': 0.15,
                    'speed_score': 0.10  # 基於predictions_per_second的標準化分數
                }
                
                # 標準化速度分數
                max_speed = max(d['predictions_per_second'] for d in models_data.values())
                speed_score = data['predictions_per_second'] / max_speed if max_speed > 0 else 0
                
                # 計算加權總分
                overall_score = (
                    data['accuracy'] * weights['accuracy'] +
                    data['f1_score'] * weights['f1_score'] +
                    data['confidence_avg'] * weights['confidence_avg'] +
                    data['stability_score'] * weights['stability_score'] +
                    data['success_rate'] * weights['success_rate'] +
                    speed_score * weights['speed_score']
                )
                
                overall_scores[model_name] = overall_score
            
            best_overall_model = max(overall_scores.keys(), key=lambda x: overall_scores[x])
            
            # 生成排名
            model_rankings = {}
            sorted_models = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
            for rank, (model_name, score) in enumerate(sorted_models, 1):
                model_rankings[model_name] = rank
            
            # 生成性能矩陣
            performance_matrix = models_data.copy()
            for model_name in performance_matrix:
                performance_matrix[model_name]['overall_score'] = overall_scores[model_name]
            
            # 生成建議
            recommendations = self._generate_model_recommendations(
                models_data, best_overall_model, best_accuracy_model, 
                best_stability_model, best_speed_model
            )
            
            # 生成比較摘要
            comparison_summary = self._generate_comparison_summary(
                models_data, best_overall_model, model_rankings
            )
            
            return ModelComparisonResult(
                best_overall_model=best_overall_model,
                best_accuracy_model=best_accuracy_model,
                best_stability_model=best_stability_model,
                best_speed_model=best_speed_model,
                model_rankings=model_rankings,
                performance_matrix=performance_matrix,
                recommendations=recommendations,
                comparison_summary=comparison_summary
            )
            
        except Exception as e:
            logger.error(f"❌ 生成模型比較分析失敗: {e}")
            return ModelComparisonResult(
                best_overall_model='error',
                best_accuracy_model='error',
                best_stability_model='error',
                best_speed_model='error',
                model_rankings={},
                performance_matrix={},
                recommendations=[f'比較分析失敗: {e}'],
                comparison_summary='分析過程中發生錯誤'
            )
    
    def _generate_model_recommendations(self, models_data: Dict[str, Dict[str, float]],
                                      best_overall: str, best_accuracy: str,
                                      best_stability: str, best_speed: str) -> List[str]:
        """生成模型選擇建議"""
        try:
            recommendations = []
            
            # 總體最佳模型建議
            overall_score = models_data[best_overall]['accuracy']
            if overall_score > 0.8:
                recommendations.append(f"🏆 推薦使用 {best_overall} 作為主要模型 (綜合評分最高)")
            elif overall_score > 0.6:
                recommendations.append(f"✅ {best_overall} 表現良好，可作為主要模型")
            else:
                recommendations.append(f"⚠️ {best_overall} 表現一般，建議進一步優化")
            
            # 特定場景建議
            if best_accuracy != best_overall:
                acc_score = models_data[best_accuracy]['accuracy']
                if acc_score > models_data[best_overall]['accuracy'] + 0.1:
                    recommendations.append(f"🎯 對於準確性要求高的場景，建議使用 {best_accuracy}")
            
            if best_stability != best_overall:
                stab_score = models_data[best_stability]['stability_score']
                if stab_score > models_data[best_overall]['stability_score'] + 0.1:
                    recommendations.append(f"🔒 對於穩定性要求高的場景，建議使用 {best_stability}")
            
            if best_speed != best_overall:
                speed_score = models_data[best_speed]['predictions_per_second']
                if speed_score > models_data[best_overall]['predictions_per_second'] * 1.5:
                    recommendations.append(f"⚡ 對於實時性要求高的場景，建議使用 {best_speed}")
            
            # 模型組合建議
            if len(models_data) >= 2:
                top_models = sorted(models_data.items(), 
                                  key=lambda x: x[1]['accuracy'] + x[1]['stability_score'], 
                                  reverse=True)[:2]
                recommendations.append(f"🔄 考慮組合使用 {top_models[0][0]} 和 {top_models[1][0]} 以提升整體性能")
            
            # 改進建議
            for model_name, data in models_data.items():
                if data['accuracy'] < 0.5:
                    recommendations.append(f"📈 {model_name} 準確率偏低，建議重新訓練或調整參數")
                if data['stability_score'] < 0.6:
                    recommendations.append(f"⚖️ {model_name} 穩定性不足，建議增加數據平滑處理")
                if data['confidence_avg'] < 0.6:
                    recommendations.append(f"🎯 {model_name} 信心度偏低，建議優化信心度計算方法")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ 生成模型建議失敗: {e}")
            return [f"建議生成失敗: {e}"]
    
    def _generate_comparison_summary(self, models_data: Dict[str, Dict[str, float]],
                                   best_overall: str, model_rankings: Dict[str, int]) -> str:
        """生成比較摘要"""
        try:
            summary_parts = []
            
            # 基本信息
            model_count = len(models_data)
            summary_parts.append(f"本次比較涵蓋 {model_count} 個模型")
            
            # 最佳模型信息
            best_data = models_data[best_overall]
            summary_parts.append(f"綜合表現最佳的模型是 {best_overall}")
            summary_parts.append(f"其準確率為 {best_data['accuracy']:.2%}，穩定性分數為 {best_data['stability_score']:.3f}")
            
            # 性能分佈
            accuracies = [data['accuracy'] for data in models_data.values()]
            avg_accuracy = np.mean(accuracies)
            summary_parts.append(f"所有模型的平均準確率為 {avg_accuracy:.2%}")
            
            # 性能差異
            max_accuracy = max(accuracies)
            min_accuracy = min(accuracies)
            if max_accuracy - min_accuracy > 0.2:
                summary_parts.append("模型間性能差異較大，建議選擇性能較好的模型")
            else:
                summary_parts.append("模型間性能差異較小，可根據具體需求選擇")
            
            # 排名信息
            ranking_text = "模型排名: " + ", ".join([f"{model}(第{rank}名)" 
                                                  for model, rank in sorted(model_rankings.items(), 
                                                                          key=lambda x: x[1])])
            summary_parts.append(ranking_text)
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"❌ 生成比較摘要失敗: {e}")
            return f"摘要生成失敗: {e}"
    
    def _update_model_metrics(self, validation_results: Dict[str, Any]):
        """更新模型性能指標存儲"""
        try:
            for model_name, result in validation_results.items():
                if result['success']:
                    metrics = result['metrics']
                    
                    # 創建性能指標對象
                    performance_metrics = ModelPerformanceMetrics(
                        model_name=model_name,
                        model_type=result.get('model_type', 'unknown'),
                        accuracy=metrics.get('accuracy', 0),
                        precision=metrics.get('precision', 0),
                        recall=metrics.get('recall', 0),
                        f1_score=metrics.get('f1_score', 0),
                        confidence_avg=metrics.get('confidence_avg', 0),
                        confidence_std=metrics.get('confidence_std', 0),
                        prediction_count=metrics.get('prediction_count', 0),
                        success_rate=metrics.get('success_rate', 0),
                        processing_time=metrics.get('processing_time', 0),
                        memory_usage=metrics.get('memory_usage_mb', 0),
                        stability_score=metrics.get('stability_score', 0),
                        reliability_score=metrics.get('reliability_score', 0),
                        last_updated=datetime.now().isoformat()
                    )
                    
                    self.model_metrics[model_name] = performance_metrics
            
            # 添加到歷史記錄
            self.validation_history.append({
                'timestamp': datetime.now().isoformat(),
                'models_validated': list(validation_results.keys()),
                'validation_summary': {
                    model: result['success'] for model, result in validation_results.items()
                }
            })
            
            logger.info(f"✅ 模型性能指標已更新: {len(self.model_metrics)} 個模型")
            
        except Exception as e:
            logger.error(f"❌ 更新模型指標失敗: {e}")
    
    def _generate_unified_report(self, validation_results: Dict[str, Any], 
                               comparison_analysis: ModelComparisonResult) -> Dict[str, Any]:
        """生成統一報告"""
        try:
            # 報告基本信息
            report = {
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'report_version': '1.0',
                    'models_evaluated': len(validation_results),
                    'successful_validations': sum(1 for r in validation_results.values() if r['success']),
                    'generator': 'AImax Model Validation Report System'
                },
                
                # 執行摘要
                'executive_summary': {
                    'best_overall_model': comparison_analysis.best_overall_model,
                    'model_count': len(validation_results),
                    'average_accuracy': np.mean([r['metrics'].get('accuracy', 0) 
                                               for r in validation_results.values() if r['success']]),
                    'top_recommendation': comparison_analysis.recommendations[0] if comparison_analysis.recommendations else 'No recommendations',
                    'comparison_summary': comparison_analysis.comparison_summary
                },
                
                # 詳細驗證結果
                'detailed_results': {},
                
                # 模型比較分析
                'comparison_analysis': asdict(comparison_analysis),
                
                # 性能矩陣
                'performance_matrix': comparison_analysis.performance_matrix,
                
                # 建議和結論
                'recommendations': {
                    'primary_recommendations': comparison_analysis.recommendations,
                    'model_selection_guide': self._generate_selection_guide(comparison_analysis),
                    'optimization_suggestions': self._generate_optimization_suggestions(validation_results)
                },
                
                # 統計摘要
                'statistical_summary': self._generate_statistical_summary(validation_results),
                
                # 圖表數據 (如果啟用)
                'charts': self._generate_chart_data(validation_results, comparison_analysis) if self.report_config['include_charts'] else None
            }
            
            # 添加詳細結果
            for model_name, result in validation_results.items():
                if result['success']:
                    report['detailed_results'][model_name] = {
                        'model_type': result.get('model_type', 'unknown'),
                        'metrics': result['metrics'],
                        'validation_details': result.get('validation_details', {}),
                        'processing_info': {
                            'processing_time': result.get('processing_time', 0),
                            'predictions_count': len(result.get('predictions', [])),
                            'average_confidence': np.mean(result.get('confidences', [0]))
                        }
                    }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 生成統一報告失敗: {e}")
            return {'error': str(e)}
    
    def _generate_selection_guide(self, comparison_analysis: ModelComparisonResult) -> Dict[str, str]:
        """生成模型選擇指南"""
        try:
            guide = {}
            
            # 不同場景的模型選擇建議
            guide['high_accuracy_scenario'] = f"需要高準確率時選擇: {comparison_analysis.best_accuracy_model}"
            guide['high_stability_scenario'] = f"需要高穩定性時選擇: {comparison_analysis.best_stability_model}"
            guide['high_speed_scenario'] = f"需要高速度時選擇: {comparison_analysis.best_speed_model}"
            guide['balanced_scenario'] = f"平衡考慮時選擇: {comparison_analysis.best_overall_model}"
            
            # 模型組合建議
            if len(comparison_analysis.model_rankings) >= 2:
                top_2_models = sorted(comparison_analysis.model_rankings.items(), key=lambda x: x[1])[:2]
                guide['ensemble_recommendation'] = f"集成使用: {top_2_models[0][0]} + {top_2_models[1][0]}"
            
            return guide
            
        except Exception as e:
            logger.error(f"❌ 生成選擇指南失敗: {e}")
            return {}
    
    def _generate_optimization_suggestions(self, validation_results: Dict[str, Any]) -> List[str]:
        """生成優化建議"""
        try:
            suggestions = []
            
            for model_name, result in validation_results.items():
                if not result['success']:
                    suggestions.append(f"{model_name}: 修復驗證失敗問題")
                    continue
                
                metrics = result['metrics']
                
                # 準確率優化建議
                if metrics.get('accuracy', 0) < 0.6:
                    suggestions.append(f"{model_name}: 提升準確率 - 考慮增加訓練數據或調整模型參數")
                
                # 穩定性優化建議
                if metrics.get('stability_score', 0) < 0.7:
                    suggestions.append(f"{model_name}: 提升穩定性 - 考慮增加數據平滑或正則化")
                
                # 信心度優化建議
                if metrics.get('confidence_avg', 0) < 0.6:
                    suggestions.append(f"{model_name}: 提升信心度 - 優化信心度計算方法")
                
                # 速度優化建議
                if metrics.get('processing_time', 0) > 1.0:
                    suggestions.append(f"{model_name}: 提升處理速度 - 考慮模型壓縮或並行處理")
            
            # 通用建議
            if len(validation_results) < 3:
                suggestions.append("考慮增加更多模型以提供更多選擇")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"❌ 生成優化建議失敗: {e}")
            return []
    
    def _generate_statistical_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成統計摘要"""
        try:
            successful_results = [r for r in validation_results.values() if r['success']]
            
            if not successful_results:
                return {'error': 'No successful validations'}
            
            # 收集所有指標
            accuracies = [r['metrics'].get('accuracy', 0) for r in successful_results]
            confidences = [r['metrics'].get('confidence_avg', 0) for r in successful_results]
            stabilities = [r['metrics'].get('stability_score', 0) for r in successful_results]
            processing_times = [r['metrics'].get('processing_time', 0) for r in successful_results]
            
            return {
                'model_count': len(successful_results),
                'accuracy_stats': {
                    'mean': np.mean(accuracies),
                    'std': np.std(accuracies),
                    'min': np.min(accuracies),
                    'max': np.max(accuracies),
                    'median': np.median(accuracies)
                },
                'confidence_stats': {
                    'mean': np.mean(confidences),
                    'std': np.std(confidences),
                    'min': np.min(confidences),
                    'max': np.max(confidences)
                },
                'stability_stats': {
                    'mean': np.mean(stabilities),
                    'std': np.std(stabilities),
                    'min': np.min(stabilities),
                    'max': np.max(stabilities)
                },
                'performance_stats': {
                    'avg_processing_time': np.mean(processing_times),
                    'total_processing_time': np.sum(processing_times),
                    'fastest_model': min(successful_results, key=lambda x: x['metrics'].get('processing_time', float('inf')))['model_name'],
                    'slowest_model': max(successful_results, key=lambda x: x['metrics'].get('processing_time', 0))['model_name']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 生成統計摘要失敗: {e}")
            return {'error': str(e)}
    
    def _generate_chart_data(self, validation_results: Dict[str, Any], 
                           comparison_analysis: ModelComparisonResult) -> Dict[str, Any]:
        """生成圖表數據"""
        try:
            chart_data = {}
            
            successful_results = {k: v for k, v in validation_results.items() if v['success']}
            
            if not successful_results:
                return {'error': 'No data for charts'}
            
            # 模型性能比較雷達圖數據
            radar_data = {}
            for model_name, result in successful_results.items():
                metrics = result['metrics']
                radar_data[model_name] = {
                    'accuracy': metrics.get('accuracy', 0),
                    'stability': metrics.get('stability_score', 0),
                    'confidence': metrics.get('confidence_avg', 0),
                    'speed': min(1.0, metrics.get('predictions_per_second', 0) / 100),  # 標準化
                    'success_rate': metrics.get('success_rate', 0)
                }
            
            chart_data['radar_chart'] = radar_data
            
            # 性能分佈柱狀圖數據
            bar_data = {}
            metrics_to_plot = ['accuracy', 'stability_score', 'confidence_avg', 'success_rate']
            
            for metric in metrics_to_plot:
                bar_data[metric] = {
                    model_name: result['metrics'].get(metric, 0)
                    for model_name, result in successful_results.items()
                }
            
            chart_data['bar_chart'] = bar_data
            
            # 處理時間比較
            processing_time_data = {
                model_name: result['metrics'].get('processing_time', 0)
                for model_name, result in successful_results.items()
            }
            chart_data['processing_time_chart'] = processing_time_data
            
            # 模型排名餅圖數據
            ranking_data = comparison_analysis.model_rankings
            chart_data['ranking_pie'] = ranking_data
            
            return chart_data
            
        except Exception as e:
            logger.error(f"❌ 生成圖表數據失敗: {e}")
            return {'error': str(e)}
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> Dict[str, str]:
        """保存報告到文件"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"model_validation_report_{timestamp}"
            
            saved_files = {}
            
            # 保存JSON格式
            if 'json' in self.report_config['output_formats']:
                json_path = self.output_dir / f"{filename}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)
                saved_files['json'] = str(json_path)
                logger.info(f"✅ JSON報告已保存: {json_path}")
            
            # 保存HTML格式 (簡化版)
            if 'html' in self.report_config['output_formats']:
                html_path = self.output_dir / f"{filename}.html"
                html_content = self._generate_html_report(report)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                saved_files['html'] = str(html_path)
                logger.info(f"✅ HTML報告已保存: {html_path}")
            
            return saved_files
            
        except Exception as e:
            logger.error(f"❌ 保存報告失敗: {e}")
            return {'error': str(e)}
    
    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """生成HTML格式報告"""
        try:
            html_template = f"""
            <!DOCTYPE html>
            <html lang="zh-TW">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>AImax 模型驗證報告</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                    .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                    .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }}
                    .recommendation {{ background-color: #e8f5e8; padding: 10px; margin: 5px 0; border-radius: 3px; }}
                    table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🤖 AImax 模型驗證報告</h1>
                    <p>生成時間: {report['report_metadata']['generated_at']}</p>
                    <p>評估模型數: {report['report_metadata']['models_evaluated']}</p>
                </div>
                
                <div class="section">
                    <h2>📊 執行摘要</h2>
                    <div class="metric">最佳模型: {report['executive_summary']['best_overall_model']}</div>
                    <div class="metric">平均準確率: {report['executive_summary']['average_accuracy']:.2%}</div>
                    <p>{report['executive_summary']['comparison_summary']}</p>
                </div>
                
                <div class="section">
                    <h2>🏆 模型排名</h2>
                    <table>
                        <tr><th>排名</th><th>模型名稱</th><th>綜合評分</th></tr>
            """
            
            # 添加模型排名表格
            if 'model_rankings' in report['comparison_analysis']:
                rankings = report['comparison_analysis']['model_rankings']
                performance_matrix = report['comparison_analysis']['performance_matrix']
                
                for model, rank in sorted(rankings.items(), key=lambda x: x[1]):
                    score = performance_matrix.get(model, {}).get('overall_score', 0)
                    html_template += f"<tr><td>{rank}</td><td>{model}</td><td>{score:.3f}</td></tr>"
            
            html_template += """
                    </table>
                </div>
                
                <div class="section">
                    <h2>💡 建議</h2>
            """
            
            # 添加建議
            if 'recommendations' in report and 'primary_recommendations' in report['recommendations']:
                for rec in report['recommendations']['primary_recommendations']:
                    html_template += f'<div class="recommendation">{rec}</div>'
            
            html_template += """
                </div>
            </body>
            </html>
            """
            
            return html_template
            
        except Exception as e:
            logger.error(f"❌ 生成HTML報告失敗: {e}")
            return f"<html><body><h1>報告生成失敗</h1><p>{e}</p></body></html>"
    
    def get_model_performance_history(self, model_name: str = None) -> Dict[str, Any]:
        """獲取模型性能歷史"""
        try:
            if model_name:
                if model_name in self.model_metrics:
                    return {model_name: asdict(self.model_metrics[model_name])}
                else:
                    return {'error': f'Model {model_name} not found'}
            else:
                return {name: asdict(metrics) for name, metrics in self.model_metrics.items()}
                
        except Exception as e:
            logger.error(f"❌ 獲取模型歷史失敗: {e}")
            return {'error': str(e)}


# 創建全局報告生成器實例
def create_model_validation_report_generator(output_dir: str = "AImax/reports") -> ModelValidationReportGenerator:
    """創建模型驗證報告生成器實例"""
    return ModelValidationReportGenerator(output_dir)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_model_validation_report():
        """測試模型驗證報告系統"""
        print("🧪 測試模型驗證報告系統...")
        
        # 創建報告生成器
        report_generator = create_model_validation_report_generator()
        
        # 生成測試數據
        test_data = []
        ground_truth = []
        
        for i in range(20):
            test_data.append({
                'current_price': 1500000 + np.random.normal(0, 50000),
                'price_change_1m': np.random.normal(0, 1),
                'volume_ratio': max(0.5, np.random.lognormal(0, 0.2)),
                'ai_formatted_data': '測試數據'
            })
            ground_truth.append(np.random.choice(['BUY', 'SELL', 'HOLD']))
        
        # 執行模型驗證
        validation_result = await report_generator.validate_all_models(test_data, ground_truth)
        
        if validation_result['success']:
            print("✅ 模型驗證成功")
            print(f"   驗證模型數: {len(validation_result['models_validated'])}")
            print(f"   最佳模型: {validation_result['comparison_analysis'].best_overall_model}")
            
            # 保存報告
            saved_files = report_generator.save_report(validation_result['unified_report'])
            print(f"   報告已保存: {list(saved_files.keys())}")
        else:
            print(f"❌ 模型驗證失敗: {validation_result.get('error')}")
    
    # 運行測試
    asyncio.run(test_model_validation_report())