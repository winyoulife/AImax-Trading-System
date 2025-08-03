#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
機器學習模型訓練器 - 使用提取的訓練數據訓練多種ML模型
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import pickle
import json

# 機器學習庫
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_recall_fscore_support
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️ scikit-learn未安裝，請運行: pip install scikit-learn")

from .training_data_extractor import create_training_data_extractor

logger = logging.getLogger(__name__)

class ModelTrainer:
    """機器學習模型訓練器"""
    
    def __init__(self, model_dir: str = "AImax/models"):
        """
        初始化模型訓練器
        
        Args:
            model_dir: 模型保存目錄
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.data_extractor = create_training_data_extractor()
        
        # 模型配置
        self.model_configs = {
            'random_forest': {
                'model': RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42
                ),
                'param_grid': {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, 15],
                    'min_samples_split': [2, 5, 10]
                }
            },
            'gradient_boosting': {
                'model': GradientBoostingClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42
                ),
                'param_grid': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.05, 0.1, 0.2],
                    'max_depth': [3, 6, 9]
                }
            },
            'logistic_regression': {
                'model': LogisticRegression(
                    random_state=42,
                    max_iter=1000
                ),
                'param_grid': {
                    'C': [0.1, 1.0, 10.0],
                    'penalty': ['l1', 'l2'],
                    'solver': ['liblinear']
                }
            }
        } if SKLEARN_AVAILABLE else {}
        
        # 特徵選擇配置
        self.feature_groups = {
            'price_features': ['open', 'high', 'low', 'close', 'volume'],
            'technical_features': [
                'rsi_7', 'rsi_14', 'rsi_21',
                'sma_5', 'sma_10', 'sma_20', 'sma_50',
                'ema_12', 'ema_26',
                'macd', 'macd_signal', 'macd_histogram',
                'bb_width', 'volume_ratio'
            ],
            'derived_features': [
                'price_change_1', 'price_change_5', 'price_change_15',
                'volatility_5', 'volatility_20',
                'momentum_5', 'momentum_10',
                'price_position_bb', 'price_vs_sma20'
            ],
            'time_features': ['hour', 'day_of_week', 'is_weekend']
        }
        
        logger.info("🤖 機器學習模型訓練器初始化完成")
    
    async def train_all_models(self, 
                             market: str = "btctwd",
                             days: int = 30,
                             target_column: str = "signal_3class") -> Dict[str, Any]:
        """
        訓練所有模型
        
        Args:
            market: 交易對
            days: 訓練數據天數
            target_column: 目標列名
            
        Returns:
            訓練結果字典
        """
        if not SKLEARN_AVAILABLE:
            logger.error("❌ scikit-learn未安裝，無法進行模型訓練")
            return {}
        
        try:
            logger.info(f"🚀 開始訓練所有模型: {market}, {days}天數據")
            
            # 步驟1: 提取訓練數據
            training_data = await self._prepare_training_data(market, days)
            if training_data is None:
                logger.error("❌ 無法獲取訓練數據")
                return {}
            
            # 步驟2: 準備特徵和標籤
            X, y, feature_names = self._prepare_features_and_labels(training_data, target_column)
            if X is None:
                logger.error("❌ 特徵準備失敗")
                return {}
            
            # 步驟3: 分割訓練和測試數據
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # 步驟4: 特徵標準化
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # 步驟5: 訓練所有模型
            results = {}
            for model_name, config in self.model_configs.items():
                logger.info(f"🔄 訓練模型: {model_name}")
                
                model_result = self._train_single_model(
                    model_name, config,
                    X_train_scaled, X_test_scaled, y_train, y_test,
                    feature_names
                )
                
                if model_result:
                    results[model_name] = model_result
            
            # 步驟6: 選擇最佳模型
            best_model_name = self._select_best_model(results)
            results['best_model'] = best_model_name
            results['scaler'] = scaler
            results['feature_names'] = feature_names
            results['training_info'] = {
                'market': market,
                'days': days,
                'target_column': target_column,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'features_count': len(feature_names),
                'timestamp': datetime.now().isoformat()
            }
            
            # 步驟7: 保存訓練結果
            self._save_training_results(results, market)
            
            logger.info(f"✅ 所有模型訓練完成，最佳模型: {best_model_name}")
            return results
            
        except Exception as e:
            logger.error(f"❌ 模型訓練失敗: {e}")
            return {}
    
    async def _prepare_training_data(self, market: str, days: int) -> Optional[pd.DataFrame]:
        """準備訓練數據"""
        try:
            logger.info("📊 準備訓練數據...")
            
            training_data = await self.data_extractor.extract_training_dataset(
                market=market,
                days=days,
                timeframe="5m"
            )
            
            if training_data is None or training_data.empty:
                logger.error("❌ 無法提取訓練數據")
                return None
            
            logger.info(f"✅ 訓練數據準備完成: {len(training_data)} 條記錄")
            return training_data
            
        except Exception as e:
            logger.error(f"❌ 準備訓練數據失敗: {e}")
            return None
    
    def _prepare_features_and_labels(self, 
                                   df: pd.DataFrame, 
                                   target_column: str) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[List[str]]]:
        """準備特徵和標籤"""
        try:
            logger.info("🔧 準備特徵和標籤...")
            
            # 選擇特徵列
            feature_columns = []
            for group_name, features in self.feature_groups.items():
                available_features = [f for f in features if f in df.columns]
                feature_columns.extend(available_features)
                logger.info(f"   {group_name}: {len(available_features)} 個特徵")
            
            # 檢查目標列
            if target_column not in df.columns:
                logger.error(f"❌ 目標列 {target_column} 不存在")
                return None, None, None
            
            # 提取特徵和標籤
            X = df[feature_columns].values
            y = df[target_column].values
            
            # 移除包含NaN的樣本
            valid_mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
            X = X[valid_mask]
            y = y[valid_mask]
            
            logger.info(f"✅ 特徵準備完成: {X.shape[0]} 樣本, {X.shape[1]} 特徵")
            logger.info(f"📊 標籤分佈: {np.bincount(y.astype(int))}")
            
            return X, y, feature_columns
            
        except Exception as e:
            logger.error(f"❌ 準備特徵和標籤失敗: {e}")
            return None, None, None
    
    def _train_single_model(self,
                          model_name: str,
                          config: Dict[str, Any],
                          X_train: np.ndarray,
                          X_test: np.ndarray,
                          y_train: np.ndarray,
                          y_test: np.ndarray,
                          feature_names: List[str]) -> Optional[Dict[str, Any]]:
        """訓練單個模型"""
        try:
            model = config['model']
            
            # 訓練模型
            model.fit(X_train, y_train)
            
            # 預測
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            
            # 計算性能指標
            train_accuracy = accuracy_score(y_train, y_pred_train)
            test_accuracy = accuracy_score(y_test, y_pred_test)
            
            # 交叉驗證
            cv_scores = cross_val_score(model, X_train, y_train, cv=5)
            
            # 分類報告
            classification_rep = classification_report(y_test, y_pred_test, output_dict=True)
            
            # 特徵重要性（如果模型支持）
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(zip(feature_names, model.feature_importances_))
                # 排序特徵重要性
                feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            
            result = {
                'model': model,
                'train_accuracy': train_accuracy,
                'test_accuracy': test_accuracy,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'classification_report': classification_rep,
                'confusion_matrix': confusion_matrix(y_test, y_pred_test).tolist(),
                'feature_importance': feature_importance
            }
            
            logger.info(f"✅ {model_name} 訓練完成 - 測試準確率: {test_accuracy:.4f}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 訓練 {model_name} 失敗: {e}")
            return None
    
    def _select_best_model(self, results: Dict[str, Any]) -> str:
        """選擇最佳模型"""
        try:
            best_model = None
            best_score = -1
            
            for model_name, result in results.items():
                if isinstance(result, dict) and 'test_accuracy' in result:
                    # 綜合評分：測試準確率 * 0.6 + 交叉驗證平均分 * 0.4
                    score = result['test_accuracy'] * 0.6 + result['cv_mean'] * 0.4
                    
                    if score > best_score:
                        best_score = score
                        best_model = model_name
            
            logger.info(f"🏆 最佳模型: {best_model} (綜合評分: {best_score:.4f})")
            return best_model or 'random_forest'
            
        except Exception as e:
            logger.error(f"❌ 選擇最佳模型失敗: {e}")
            return 'random_forest'
    
    def _save_training_results(self, results: Dict[str, Any], market: str):
        """保存訓練結果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存模型
            for model_name, result in results.items():
                if isinstance(result, dict) and 'model' in result:
                    model_file = self.model_dir / f"{market}_{model_name}_{timestamp}.joblib"
                    joblib.dump(result['model'], model_file)
                    logger.info(f"💾 模型已保存: {model_file}")
            
            # 保存標準化器
            if 'scaler' in results:
                scaler_file = self.model_dir / f"{market}_scaler_{timestamp}.joblib"
                joblib.dump(results['scaler'], scaler_file)
            
            # 保存訓練報告
            report = {
                'training_info': results.get('training_info', {}),
                'best_model': results.get('best_model'),
                'feature_names': results.get('feature_names', []),
                'model_performance': {}
            }
            
            for model_name, result in results.items():
                if isinstance(result, dict) and 'test_accuracy' in result:
                    report['model_performance'][model_name] = {
                        'test_accuracy': result['test_accuracy'],
                        'cv_mean': result['cv_mean'],
                        'cv_std': result['cv_std'],
                        'classification_report': result['classification_report']
                    }
            
            report_file = self.model_dir / f"{market}_training_report_{timestamp}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 訓練報告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存訓練結果失敗: {e}")
    
    def load_trained_model(self, market: str, model_name: str = None) -> Optional[Dict[str, Any]]:
        """載入訓練好的模型"""
        try:
            # 查找最新的模型文件
            if model_name is None:
                # 載入最新的最佳模型
                model_files = list(self.model_dir.glob(f"{market}_*_*.joblib"))
                if not model_files:
                    logger.warning(f"⚠️ 沒有找到 {market} 的模型文件")
                    return None
                
                latest_file = max(model_files, key=lambda x: x.stat().st_mtime)
                model = joblib.load(latest_file)
                
                # 載入對應的標準化器
                timestamp = latest_file.stem.split('_')[-1]
                scaler_file = self.model_dir / f"{market}_scaler_{timestamp}.joblib"
                scaler = joblib.load(scaler_file) if scaler_file.exists() else None
                
                return {
                    'model': model,
                    'scaler': scaler,
                    'model_file': str(latest_file)
                }
            else:
                # 載入指定模型
                model_files = list(self.model_dir.glob(f"{market}_{model_name}_*.joblib"))
                if not model_files:
                    logger.warning(f"⚠️ 沒有找到 {market} {model_name} 的模型文件")
                    return None
                
                latest_file = max(model_files, key=lambda x: x.stat().st_mtime)
                model = joblib.load(latest_file)
                
                return {'model': model, 'model_file': str(latest_file)}
                
        except Exception as e:
            logger.error(f"❌ 載入模型失敗: {e}")
            return None
    
    def predict(self, model_data: Dict[str, Any], features: np.ndarray) -> Optional[Dict[str, Any]]:
        """使用訓練好的模型進行預測"""
        try:
            model = model_data['model']
            scaler = model_data.get('scaler')
            
            # 標準化特徵
            if scaler is not None:
                features_scaled = scaler.transform(features.reshape(1, -1))
            else:
                features_scaled = features.reshape(1, -1)
            
            # 預測
            prediction = model.predict(features_scaled)[0]
            
            # 預測概率（如果模型支持）
            prediction_proba = None
            if hasattr(model, 'predict_proba'):
                prediction_proba = model.predict_proba(features_scaled)[0]
            
            return {
                'prediction': int(prediction),
                'prediction_proba': prediction_proba.tolist() if prediction_proba is not None else None,
                'confidence': float(max(prediction_proba)) if prediction_proba is not None else 0.5,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 模型預測失敗: {e}")
            return None


# 創建全局實例
def create_model_trainer(model_dir: str = "AImax/models") -> ModelTrainer:
    """創建模型訓練器實例"""
    return ModelTrainer(model_dir)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_model_trainer():
        """測試模型訓練器"""
        print("🧪 測試模型訓練器...")
        
        if not SKLEARN_AVAILABLE:
            print("❌ scikit-learn未安裝，無法測試")
            return
        
        trainer = create_model_trainer()
        
        try:
            # 訓練模型
            results = await trainer.train_all_models(
                market="btctwd",
                days=7,  # 測試用較少天數
                target_column="signal_3class"
            )
            
            if results:
                print(f"✅ 模型訓練成功!")
                print(f"🏆 最佳模型: {results.get('best_model')}")
                
                # 顯示各模型性能
                for model_name, result in results.items():
                    if isinstance(result, dict) and 'test_accuracy' in result:
                        print(f"   {model_name}: 測試準確率 {result['test_accuracy']:.4f}")
                
                # 測試模型載入和預測
                model_data = trainer.load_trained_model("btctwd")
                if model_data:
                    print("✅ 模型載入成功")
                    
                    # 模擬特徵進行預測測試
                    feature_count = len(results.get('feature_names', []))
                    if feature_count > 0:
                        test_features = np.random.randn(feature_count)
                        prediction = trainer.predict(model_data, test_features)
                        if prediction:
                            print(f"✅ 預測測試成功: {prediction}")
                
            else:
                print("❌ 模型訓練失敗")
                
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
    
    # 運行測試
    asyncio.run(test_model_trainer())