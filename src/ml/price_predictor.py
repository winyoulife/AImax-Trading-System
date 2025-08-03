#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LSTM價格預測器 - 使用深度學習進行時間序列價格預測
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import pickle

# 深度學習庫
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("⚠️ TensorFlow未安裝，請運行: pip install tensorflow")

logger = logging.getLogger(__name__)

class LSTMPricePredictor:
    """LSTM價格預測器"""
    
    def __init__(self, model_dir: str = "AImax/models"):
        """
        初始化LSTM價格預測器
        
        Args:
            model_dir: 模型保存目錄
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # 模型配置
        self.config = {
            'sequence_length': 60,  # 使用60個時間點預測下一個
            'features': ['close', 'volume', 'high', 'low'],  # 使用的特徵
            'prediction_horizon': 1,  # 預測未來1個時間點
            'lstm_units': [50, 50],  # LSTM層單元數
            'dropout_rate': 0.2,
            'batch_size': 32,
            'epochs': 100,
            'validation_split': 0.2,
            'learning_rate': 0.001
        }
        
        # 模型組件
        self.model = None
        self.scaler = None
        self.feature_scalers = {}
        self.training_history = None
        
        # 驗證指標
        self.validation_metrics = {}
        self.prediction_errors = []
        self.confidence_intervals = {}
        
        logger.info("🧠 LSTM價格預測器初始化完成")
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        準備LSTM訓練數據
        
        Args:
            df: 包含價格數據的DataFrame
            
        Returns:
            X_train, X_test, y_train, y_test
        """
        try:
            logger.info("📊 準備LSTM訓練數據...")
            
            # 選擇特徵列
            feature_data = df[self.config['features']].values
            
            # 標準化特徵
            if self.scaler is None:
                self.scaler = MinMaxScaler()
                scaled_data = self.scaler.fit_transform(feature_data)
            else:
                scaled_data = self.scaler.transform(feature_data)
            
            # 創建序列數據
            X, y = self._create_sequences(scaled_data)
            
            # 分割訓練和測試數據
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            logger.info(f"✅ 數據準備完成: 訓練集 {X_train.shape}, 測試集 {X_test.shape}")
            return X_train, X_test, y_train, y_test
            
        except Exception as e:
            logger.error(f"❌ 數據準備失敗: {e}")
            return None, None, None, None
    
    def _create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """創建LSTM序列數據"""
        try:
            X, y = [], []
            seq_len = self.config['sequence_length']
            
            for i in range(seq_len, len(data)):
                X.append(data[i-seq_len:i])
                y.append(data[i, 0])  # 預測收盤價
            
            return np.array(X), np.array(y)
            
        except Exception as e:
            logger.error(f"❌ 創建序列數據失敗: {e}")
            return np.array([]), np.array([])
    
    def build_model(self) -> bool:
        """構建LSTM模型"""
        try:
            if not TENSORFLOW_AVAILABLE:
                logger.error("❌ TensorFlow未安裝，無法構建模型")
                return False
            
            logger.info("🏗️ 構建LSTM模型...")
            
            model = Sequential()
            
            # 第一個LSTM層
            model.add(LSTM(
                units=self.config['lstm_units'][0],
                return_sequences=True,
                input_shape=(self.config['sequence_length'], len(self.config['features']))
            ))
            model.add(Dropout(self.config['dropout_rate']))
            model.add(BatchNormalization())
            
            # 第二個LSTM層
            model.add(LSTM(
                units=self.config['lstm_units'][1],
                return_sequences=False
            ))
            model.add(Dropout(self.config['dropout_rate']))
            model.add(BatchNormalization())
            
            # 輸出層
            model.add(Dense(units=1))
            
            # 編譯模型
            model.compile(
                optimizer=Adam(learning_rate=self.config['learning_rate']),
                loss='mse',
                metrics=['mae']
            )
            
            self.model = model
            logger.info("✅ LSTM模型構建完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 構建LSTM模型失敗: {e}")
            return False
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray = None, y_val: np.ndarray = None) -> bool:
        """
        訓練LSTM模型
        
        Args:
            X_train: 訓練特徵
            y_train: 訓練標籤
            X_val: 驗證特徵
            y_val: 驗證標籤
            
        Returns:
            訓練是否成功
        """
        try:
            if not TENSORFLOW_AVAILABLE or self.model is None:
                logger.error("❌ 模型未準備好，無法訓練")
                return False
            
            logger.info("🚀 開始訓練LSTM模型...")
            
            # 準備回調函數
            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-7
                )
            ]
            
            # 訓練模型
            if X_val is not None and y_val is not None:
                validation_data = (X_val, y_val)
            else:
                validation_data = None
            
            history = self.model.fit(
                X_train, y_train,
                batch_size=self.config['batch_size'],
                epochs=self.config['epochs'],
                validation_split=self.config['validation_split'] if validation_data is None else 0,
                validation_data=validation_data,
                callbacks=callbacks,
                verbose=1
            )
            
            self.training_history = history.history
            logger.info("✅ LSTM模型訓練完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ LSTM模型訓練失敗: {e}")
            return False
    
    def predict(self, X: np.ndarray) -> Optional[np.ndarray]:
        """
        使用LSTM模型進行預測
        
        Args:
            X: 輸入特徵
            
        Returns:
            預測結果
        """
        try:
            if not TENSORFLOW_AVAILABLE or self.model is None:
                logger.error("❌ 模型未準備好，無法預測")
                return None
            
            # 進行預測
            predictions = self.model.predict(X, verbose=0)
            
            # 反標準化預測結果
            if self.scaler is not None:
                # 創建與原始特徵相同形狀的數組進行反標準化
                dummy_features = np.zeros((len(predictions), len(self.config['features'])))
                dummy_features[:, 0] = predictions.flatten()  # 收盤價在第一列
                
                inverse_scaled = self.scaler.inverse_transform(dummy_features)
                predictions = inverse_scaled[:, 0].reshape(-1, 1)
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ LSTM預測失敗: {e}")
            return None
    
    def predict_single(self, sequence: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        預測單個序列的下一個價格
        
        Args:
            sequence: 輸入序列
            
        Returns:
            預測結果字典
        """
        try:
            if sequence.shape != (self.config['sequence_length'], len(self.config['features'])):
                logger.error(f"❌ 輸入序列形狀錯誤: {sequence.shape}")
                return None
            
            # 標準化輸入
            if self.scaler is not None:
                sequence_scaled = self.scaler.transform(sequence)
            else:
                sequence_scaled = sequence
            
            # 預測
            X_input = sequence_scaled.reshape(1, self.config['sequence_length'], len(self.config['features']))
            prediction = self.predict(X_input)
            
            if prediction is not None:
                predicted_price = float(prediction[0, 0])
                
                # 計算信心度（基於訓練歷史）
                confidence = self._calculate_prediction_confidence(sequence_scaled)
                
                return {
                    'predicted_price': predicted_price,
                    'confidence': confidence,
                    'timestamp': datetime.now().isoformat(),
                    'model_type': 'LSTM'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 單次預測失敗: {e}")
            return None
    
    def _calculate_prediction_confidence(self, sequence: np.ndarray) -> float:
        """計算預測信心度"""
        try:
            # 基於訓練歷史計算信心度
            if self.training_history is None:
                return 0.5
            
            # 使用驗證損失作為信心度指標
            val_loss = self.training_history.get('val_loss', [1.0])
            final_val_loss = val_loss[-1] if val_loss else 1.0
            
            # 將損失轉換為信心度 (損失越小，信心度越高)
            confidence = max(0.1, min(0.9, 1.0 / (1.0 + final_val_loss)))
            
            return confidence
            
        except Exception as e:
            logger.error(f"❌ 計算預測信心度失敗: {e}")
            return 0.5
    
    # ==================== 模型驗證功能 ====================
    
    def validate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """
        驗證LSTM模型性能
        
        Args:
            X_test: 測試特徵
            y_test: 測試標籤
            
        Returns:
            驗證結果字典
        """
        try:
            if not TENSORFLOW_AVAILABLE or self.model is None:
                logger.error("❌ 模型未準備好，無法驗證")
                return {'success': False, 'error': 'Model not ready'}
            
            logger.info("🔍 開始LSTM模型驗證...")
            
            # 進行預測
            predictions = self.predict(X_test)
            if predictions is None:
                return {'success': False, 'error': 'Prediction failed'}
            
            # 反標準化真實值
            y_true = self._inverse_transform_target(y_test)
            y_pred = predictions.flatten()
            
            # 計算基本指標
            mse = mean_squared_error(y_true, y_pred)
            mae = mean_absolute_error(y_true, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_true, y_pred)
            
            # 計算方向準確率
            direction_accuracy = self._calculate_direction_accuracy(y_true, y_pred)
            
            # 計算預測穩定性
            stability_score = self._calculate_prediction_stability(predictions)
            
            # 計算不同時間窗口的有效性
            time_window_effectiveness = self._test_time_window_effectiveness(X_test, y_test)
            
            # 計算信心區間
            confidence_intervals = self._calculate_confidence_intervals(y_true, y_pred)
            
            # 模型收斂性檢查
            convergence_check = self._check_model_convergence()
            
            # 保存驗證指標
            self.validation_metrics = {
                'mse': float(mse),
                'mae': float(mae),
                'rmse': float(rmse),
                'r2_score': float(r2),
                'direction_accuracy': direction_accuracy,
                'stability_score': stability_score,
                'time_window_effectiveness': time_window_effectiveness,
                'confidence_intervals': confidence_intervals,
                'convergence_check': convergence_check,
                'validation_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ LSTM模型驗證完成")
            logger.info(f"   RMSE: {rmse:.2f}")
            logger.info(f"   MAE: {mae:.2f}")
            logger.info(f"   R²: {r2:.4f}")
            logger.info(f"   方向準確率: {direction_accuracy:.2%}")
            logger.info(f"   穩定性分數: {stability_score:.4f}")
            
            return {
                'success': True,
                'metrics': self.validation_metrics,
                'summary': {
                    'overall_score': self._calculate_overall_score(),
                    'strengths': self._identify_model_strengths(),
                    'weaknesses': self._identify_model_weaknesses(),
                    'recommendations': self._generate_improvement_recommendations()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ LSTM模型驗證失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    def _inverse_transform_target(self, y: np.ndarray) -> np.ndarray:
        """反標準化目標值"""
        try:
            if self.scaler is None:
                return y
            
            # 創建與原始特徵相同形狀的數組進行反標準化
            dummy_features = np.zeros((len(y), len(self.config['features'])))
            dummy_features[:, 0] = y.flatten()  # 收盤價在第一列
            
            inverse_scaled = self.scaler.inverse_transform(dummy_features)
            return inverse_scaled[:, 0]
            
        except Exception as e:
            logger.error(f"❌ 反標準化目標值失敗: {e}")
            return y
    
    def _calculate_direction_accuracy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """計算方向預測準確率"""
        try:
            if len(y_true) < 2 or len(y_pred) < 2:
                return 0.0
            
            # 計算真實和預測的方向變化
            true_directions = np.diff(y_true) > 0
            pred_directions = np.diff(y_pred) > 0
            
            # 計算方向一致性
            correct_directions = np.sum(true_directions == pred_directions)
            total_directions = len(true_directions)
            
            return correct_directions / total_directions if total_directions > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ 計算方向準確率失敗: {e}")
            return 0.0
    
    def _calculate_prediction_stability(self, predictions: np.ndarray) -> float:
        """計算預測穩定性"""
        try:
            if len(predictions) < 2:
                return 0.0
            
            # 計算預測值的變化率
            pred_changes = np.diff(predictions.flatten())
            
            # 計算穩定性分數（變化率的標準差越小，穩定性越高）
            stability = 1.0 / (1.0 + np.std(pred_changes))
            
            return float(stability)
            
        except Exception as e:
            logger.error(f"❌ 計算預測穩定性失敗: {e}")
            return 0.0
    
    def _test_time_window_effectiveness(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """測試不同時間窗口的預測有效性"""
        try:
            effectiveness = {}
            
            # 測試不同長度的時間窗口
            window_sizes = [10, 30, 60, 100]
            
            for window_size in window_sizes:
                if len(X_test) > window_size:
                    # 取最近的window_size個樣本
                    X_window = X_test[-window_size:]
                    y_window = y_test[-window_size:]
                    
                    # 預測
                    pred_window = self.predict(X_window)
                    if pred_window is not None:
                        y_true_window = self._inverse_transform_target(y_window)
                        y_pred_window = pred_window.flatten()
                        
                        # 計算該窗口的R²分數
                        r2_window = r2_score(y_true_window, y_pred_window)
                        effectiveness[f'window_{window_size}'] = float(r2_window)
            
            return effectiveness
            
        except Exception as e:
            logger.error(f"❌ 測試時間窗口有效性失敗: {e}")
            return {}
    
    def _calculate_confidence_intervals(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """計算預測信心區間"""
        try:
            # 計算預測誤差
            errors = y_true - y_pred
            
            # 計算不同百分位的誤差
            percentiles = [5, 25, 50, 75, 95]
            intervals = {}
            
            for p in percentiles:
                intervals[f'percentile_{p}'] = float(np.percentile(np.abs(errors), p))
            
            # 計算標準誤差
            intervals['standard_error'] = float(np.std(errors))
            intervals['mean_absolute_error'] = float(np.mean(np.abs(errors)))
            
            return intervals
            
        except Exception as e:
            logger.error(f"❌ 計算信心區間失敗: {e}")
            return {}
    
    def _check_model_convergence(self) -> Dict[str, Any]:
        """檢查模型收斂性"""
        try:
            if self.training_history is None:
                return {'converged': False, 'reason': 'No training history'}
            
            train_loss = self.training_history.get('loss', [])
            val_loss = self.training_history.get('val_loss', [])
            
            if not train_loss or not val_loss:
                return {'converged': False, 'reason': 'Incomplete training history'}
            
            # 檢查損失是否收斂
            recent_train_loss = train_loss[-10:] if len(train_loss) >= 10 else train_loss
            recent_val_loss = val_loss[-10:] if len(val_loss) >= 10 else val_loss
            
            # 計算最近損失的變化趨勢
            train_trend = np.polyfit(range(len(recent_train_loss)), recent_train_loss, 1)[0]
            val_trend = np.polyfit(range(len(recent_val_loss)), recent_val_loss, 1)[0]
            
            # 檢查過擬合
            final_train_loss = train_loss[-1]
            final_val_loss = val_loss[-1]
            overfitting_ratio = final_val_loss / final_train_loss if final_train_loss > 0 else float('inf')
            
            converged = (
                abs(train_trend) < 0.001 and  # 訓練損失趨於穩定
                abs(val_trend) < 0.001 and    # 驗證損失趨於穩定
                overfitting_ratio < 2.0       # 沒有嚴重過擬合
            )
            
            return {
                'converged': converged,
                'train_trend': float(train_trend),
                'val_trend': float(val_trend),
                'overfitting_ratio': float(overfitting_ratio),
                'final_train_loss': float(final_train_loss),
                'final_val_loss': float(final_val_loss),
                'epochs_trained': len(train_loss)
            }
            
        except Exception as e:
            logger.error(f"❌ 檢查模型收斂性失敗: {e}")
            return {'converged': False, 'error': str(e)}
    
    def _calculate_overall_score(self) -> float:
        """計算模型整體評分"""
        try:
            if not self.validation_metrics:
                return 0.0
            
            # 權重配置
            weights = {
                'r2_score': 0.3,
                'direction_accuracy': 0.25,
                'stability_score': 0.2,
                'convergence': 0.15,
                'mae_normalized': 0.1
            }
            
            score = 0.0
            
            # R²分數 (0-1, 越高越好)
            r2 = self.validation_metrics.get('r2_score', 0)
            score += max(0, r2) * weights['r2_score']
            
            # 方向準確率 (0-1, 越高越好)
            direction_acc = self.validation_metrics.get('direction_accuracy', 0)
            score += direction_acc * weights['direction_accuracy']
            
            # 穩定性分數 (0-1, 越高越好)
            stability = self.validation_metrics.get('stability_score', 0)
            score += stability * weights['stability_score']
            
            # 收斂性 (布爾值轉換為分數)
            convergence = self.validation_metrics.get('convergence_check', {})
            convergence_score = 1.0 if convergence.get('converged', False) else 0.0
            score += convergence_score * weights['convergence']
            
            # 標準化MAE (越小越好，需要反轉)
            mae = self.validation_metrics.get('mae', float('inf'))
            mae_normalized = max(0, 1.0 - mae / 10000)  # 假設10000為最大可接受MAE
            score += mae_normalized * weights['mae_normalized']
            
            return min(1.0, max(0.0, score))
            
        except Exception as e:
            logger.error(f"❌ 計算整體評分失敗: {e}")
            return 0.0
    
    def _identify_model_strengths(self) -> List[str]:
        """識別模型優勢"""
        try:
            strengths = []
            
            if not self.validation_metrics:
                return strengths
            
            # 檢查各項指標
            r2 = self.validation_metrics.get('r2_score', 0)
            if r2 > 0.7:
                strengths.append(f"優秀的擬合度 (R² = {r2:.3f})")
            elif r2 > 0.5:
                strengths.append(f"良好的擬合度 (R² = {r2:.3f})")
            
            direction_acc = self.validation_metrics.get('direction_accuracy', 0)
            if direction_acc > 0.6:
                strengths.append(f"良好的方向預測能力 ({direction_acc:.1%})")
            
            stability = self.validation_metrics.get('stability_score', 0)
            if stability > 0.8:
                strengths.append(f"預測結果穩定 (穩定性: {stability:.3f})")
            
            convergence = self.validation_metrics.get('convergence_check', {})
            if convergence.get('converged', False):
                strengths.append("模型收斂良好")
            
            mae = self.validation_metrics.get('mae', float('inf'))
            if mae < 1000:
                strengths.append(f"預測誤差較小 (MAE: {mae:.0f})")
            
            return strengths
            
        except Exception as e:
            logger.error(f"❌ 識別模型優勢失敗: {e}")
            return []
    
    def _identify_model_weaknesses(self) -> List[str]:
        """識別模型弱點"""
        try:
            weaknesses = []
            
            if not self.validation_metrics:
                return weaknesses
            
            # 檢查各項指標
            r2 = self.validation_metrics.get('r2_score', 0)
            if r2 < 0.3:
                weaknesses.append(f"擬合度較差 (R² = {r2:.3f})")
            
            direction_acc = self.validation_metrics.get('direction_accuracy', 0)
            if direction_acc < 0.5:
                weaknesses.append(f"方向預測能力不足 ({direction_acc:.1%})")
            
            stability = self.validation_metrics.get('stability_score', 0)
            if stability < 0.5:
                weaknesses.append(f"預測結果不穩定 (穩定性: {stability:.3f})")
            
            convergence = self.validation_metrics.get('convergence_check', {})
            if not convergence.get('converged', False):
                weaknesses.append("模型收斂性問題")
            
            overfitting_ratio = convergence.get('overfitting_ratio', 1.0)
            if overfitting_ratio > 2.0:
                weaknesses.append(f"可能存在過擬合 (比率: {overfitting_ratio:.2f})")
            
            mae = self.validation_metrics.get('mae', 0)
            if mae > 5000:
                weaknesses.append(f"預測誤差較大 (MAE: {mae:.0f})")
            
            return weaknesses
            
        except Exception as e:
            logger.error(f"❌ 識別模型弱點失敗: {e}")
            return []
    
    def _generate_improvement_recommendations(self) -> List[str]:
        """生成改進建議"""
        try:
            recommendations = []
            
            if not self.validation_metrics:
                return recommendations
            
            # 基於弱點生成建議
            weaknesses = self._identify_model_weaknesses()
            
            if any("擬合度較差" in w for w in weaknesses):
                recommendations.append("考慮增加LSTM層數或單元數")
                recommendations.append("嘗試調整序列長度參數")
                recommendations.append("增加更多相關特徵")
            
            if any("方向預測能力不足" in w for w in weaknesses):
                recommendations.append("考慮使用分類模型輔助方向預測")
                recommendations.append("增加技術指標特徵")
            
            if any("不穩定" in w for w in weaknesses):
                recommendations.append("增加Dropout層或調整Dropout率")
                recommendations.append("使用BatchNormalization")
                recommendations.append("減少學習率")
            
            if any("收斂性問題" in w for w in weaknesses):
                recommendations.append("調整學習率和優化器參數")
                recommendations.append("增加訓練epochs")
                recommendations.append("使用學習率調度器")
            
            if any("過擬合" in w for w in weaknesses):
                recommendations.append("增加正則化")
                recommendations.append("使用更多訓練數據")
                recommendations.append("減少模型複雜度")
            
            if any("誤差較大" in w for w in weaknesses):
                recommendations.append("檢查數據質量和預處理")
                recommendations.append("嘗試不同的特徵工程方法")
                recommendations.append("考慮集成多個模型")
            
            # 通用建議
            if not recommendations:
                recommendations.append("模型表現良好，可考慮微調超參數進一步優化")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ 生成改進建議失敗: {e}")
            return []
    
    def get_validation_report(self) -> Dict[str, Any]:
        """獲取完整的驗證報告"""
        try:
            if not self.validation_metrics:
                return {'error': 'No validation metrics available'}
            
            overall_score = self._calculate_overall_score()
            strengths = self._identify_model_strengths()
            weaknesses = self._identify_model_weaknesses()
            recommendations = self._generate_improvement_recommendations()
            
            return {
                'model_type': 'LSTM',
                'validation_timestamp': self.validation_metrics.get('validation_timestamp'),
                'overall_score': overall_score,
                'performance_grade': self._get_performance_grade(overall_score),
                'detailed_metrics': self.validation_metrics,
                'analysis': {
                    'strengths': strengths,
                    'weaknesses': weaknesses,
                    'recommendations': recommendations
                },
                'model_config': self.config.copy()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取驗證報告失敗: {e}")
            return {'error': str(e)}
    
    def _get_performance_grade(self, score: float) -> str:
        """根據分數獲取性能等級"""
        if score >= 0.9:
            return "優秀 (A)"
        elif score >= 0.8:
            return "良好 (B)"
        elif score >= 0.7:
            return "中等 (C)"
        elif score >= 0.6:
            return "及格 (D)"
        else:
            return "需要改進 (F)"
    
    def save_model(self, market: str) -> bool:
        """保存模型"""
        try:
            if not TENSORFLOW_AVAILABLE or self.model is None:
                logger.error("❌ 模型未準備好，無法保存")
                return False
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存Keras模型
            model_file = self.model_dir / f"{market}_lstm_model_{timestamp}.h5"
            self.model.save(model_file)
            
            # 保存標準化器
            scaler_file = self.model_dir / f"{market}_lstm_scaler_{timestamp}.pkl"
            with open(scaler_file, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            # 保存配置和歷史
            config_file = self.model_dir / f"{market}_lstm_config_{timestamp}.json"
            config_data = {
                'config': self.config,
                'training_history': self.training_history,
                'validation_metrics': self.validation_metrics,
                'timestamp': timestamp
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 LSTM模型已保存: {model_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存LSTM模型失敗: {e}")
            return False
    
    def load_model(self, market: str) -> bool:
        """載入模型"""
        try:
            if not TENSORFLOW_AVAILABLE:
                logger.error("❌ TensorFlow未安裝，無法載入模型")
                return False
            
            # 查找最新的模型文件
            model_files = list(self.model_dir.glob(f"{market}_lstm_model_*.h5"))
            if not model_files:
                logger.warning(f"⚠️ 沒有找到 {market} 的LSTM模型文件")
                return False
            
            latest_model_file = max(model_files, key=lambda x: x.stat().st_mtime)
            timestamp = latest_model_file.stem.split('_')[-1]
            
            # 載入模型
            self.model = load_model(latest_model_file)
            
            # 載入標準化器
            scaler_file = self.model_dir / f"{market}_lstm_scaler_{timestamp}.pkl"
            if scaler_file.exists():
                with open(scaler_file, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            # 載入配置
            config_file = self.model_dir / f"{market}_lstm_config_{timestamp}.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.config.update(config_data.get('config', {}))
                    self.training_history = config_data.get('training_history')
                    self.validation_metrics = config_data.get('validation_metrics', {})
            
            logger.info(f"✅ LSTM模型載入成功: {latest_model_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 載入LSTM模型失敗: {e}")
            return False


def create_lstm_predictor(model_dir: str = "AImax/models") -> LSTMPricePredictor:
    """創建LSTM價格預測器實例"""
    return LSTMPricePredictor(model_dir)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_lstm_predictor():
        """測試LSTM價格預測器"""
        print("🧪 測試LSTM價格預測器...")
        
        if not TENSORFLOW_AVAILABLE:
            print("❌ TensorFlow未安裝，無法測試")
            return
        
        predictor = create_lstm_predictor()
        
        try:
            # 生成模擬數據進行測試
            dates = pd.date_range(start='2024-01-01', periods=1000, freq='5T')
            np.random.seed(42)
            
            # 模擬價格數據
            base_price = 1500000
            price_changes = np.random.normal(0, 0.001, 1000)
            prices = [base_price]
            
            for change in price_changes[1:]:
                new_price = prices[-1] * (1 + change)
                prices.append(new_price)
            
            # 創建DataFrame
            df = pd.DataFrame({
                'timestamp': dates,
                'close': prices,
                'high': [p * 1.001 for p in prices],
                'low': [p * 0.999 for p in prices],
                'volume': np.random.uniform(100, 1000, 1000)
            })
            
            print(f"✅ 生成測試數據: {len(df)} 條記錄")
            
            # 準備數據
            X_train, X_test, y_train, y_test = predictor.prepare_data(df)
            
            if X_train is not None:
                print(f"✅ 數據準備成功")
                
                # 構建模型
                if predictor.build_model():
                    print("✅ 模型構建成功")
                    
                    # 訓練模型（使用較少的epochs進行測試）
                    predictor.config['epochs'] = 5
                    if predictor.train(X_train, y_train, X_test, y_test):
                        print("✅ 模型訓練成功")
                        
                        # 測試預測
                        predictions = predictor.predict(X_test[:5])
                        if predictions is not None:
                            print(f"✅ 預測測試成功: {predictions.flatten()[:3]}")
                        
                        # 測試單次預測
                        test_sequence = X_test[0]
                        single_pred = predictor.predict_single(test_sequence)
                        if single_pred:
                            print(f"✅ 單次預測成功: {single_pred}")
                        
                        # 測試保存模型
                        if predictor.save_model("test"):
                            print("✅ 模型保存成功")
                
            else:
                print("❌ 數據準備失敗")
                
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
    
    # 運行測試
    asyncio.run(test_lstm_predictor())