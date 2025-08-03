#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
數據驗證和清洗模組 - 確保AI獲得高質量的市場數據
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MarketDataValidator:
    """市場數據驗證器"""
    
    def __init__(self):
        """初始化數據驗證器"""
        self.validation_rules = {
            'price_range': (100000, 10000000),  # BTC/TWD合理價格範圍
            'volume_range': (0, 1000000000),    # 合理成交量範圍
            'price_change_limit': 0.2,          # 單次價格變化限制 (20%)
            'missing_data_threshold': 0.1,      # 缺失數據閾值 (10%)
            'outlier_std_threshold': 3.0        # 異常值標準差閾值
        }
        
        self.data_quality_stats = {
            'total_validations': 0,
            'passed_validations': 0,
            'failed_validations': 0,
            'data_quality_score': 1.0
        }
        
        logger.info("🔍 數據驗證器初始化完成")
    
    def validate_market_data(self, market_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        驗證市場數據質量
        
        Args:
            market_data: 市場數據字典
            
        Returns:
            (is_valid, validation_report): 驗證結果和報告
        """
        try:
            self.data_quality_stats['total_validations'] += 1
            
            validation_report = {
                'timestamp': datetime.now(),
                'overall_valid': True,
                'issues': [],
                'warnings': [],
                'quality_score': 1.0,
                'data_completeness': 1.0,
                'data_consistency': 1.0,
                'data_accuracy': 1.0
            }
            
            # 基礎數據完整性檢查
            completeness_score = self._check_data_completeness(market_data, validation_report)
            
            # 數據一致性檢查
            consistency_score = self._check_data_consistency(market_data, validation_report)
            
            # 數據準確性檢查
            accuracy_score = self._check_data_accuracy(market_data, validation_report)
            
            # 計算總體質量分數
            validation_report['data_completeness'] = completeness_score
            validation_report['data_consistency'] = consistency_score
            validation_report['data_accuracy'] = accuracy_score
            validation_report['quality_score'] = (completeness_score + consistency_score + accuracy_score) / 3
            
            # 判斷是否通過驗證
            validation_report['overall_valid'] = (
                validation_report['quality_score'] >= 0.7 and
                len(validation_report['issues']) == 0
            )
            
            # 更新統計
            if validation_report['overall_valid']:
                self.data_quality_stats['passed_validations'] += 1
            else:
                self.data_quality_stats['failed_validations'] += 1
            
            self.data_quality_stats['data_quality_score'] = (
                self.data_quality_stats['passed_validations'] / 
                self.data_quality_stats['total_validations']
            )
            
            logger.info(f"✅ 數據驗證完成，質量分數: {validation_report['quality_score']:.2f}")
            return validation_report['overall_valid'], validation_report
            
        except Exception as e:
            logger.error(f"❌ 數據驗證失敗: {e}")
            return False, {'error': str(e)}
    
    def _check_data_completeness(self, market_data: Dict[str, Any], report: Dict[str, Any]) -> float:
        """檢查數據完整性"""
        try:
            required_fields = [
                'current_price', 'timestamp', 'volume_24h',
                'high_24h', 'low_24h', 'open_24h'
            ]
            
            missing_fields = []
            for field in required_fields:
                if field not in market_data or market_data[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                report['issues'].append(f"缺失必要字段: {missing_fields}")
                return 0.5
            
            # 檢查數值字段是否為有效數字
            numeric_fields = ['current_price', 'volume_24h', 'high_24h', 'low_24h', 'open_24h']
            invalid_numeric = []
            
            for field in numeric_fields:
                if field in market_data:
                    try:
                        value = float(market_data[field])
                        if np.isnan(value) or np.isinf(value):
                            invalid_numeric.append(field)
                    except (ValueError, TypeError):
                        invalid_numeric.append(field)
            
            if invalid_numeric:
                report['warnings'].append(f"無效數值字段: {invalid_numeric}")
                return 0.8
            
            return 1.0
            
        except Exception as e:
            logger.error(f"❌ 完整性檢查失敗: {e}")
            return 0.0
    
    def _check_data_consistency(self, market_data: Dict[str, Any], report: Dict[str, Any]) -> float:
        """檢查數據一致性"""
        try:
            consistency_score = 1.0
            
            # 檢查價格邏輯一致性
            if all(field in market_data for field in ['current_price', 'high_24h', 'low_24h']):
                current_price = float(market_data['current_price'])
                high_24h = float(market_data['high_24h'])
                low_24h = float(market_data['low_24h'])
                
                if not (low_24h <= current_price <= high_24h):
                    report['issues'].append(f"價格不一致: 當前價格 {current_price} 不在24小時範圍 [{low_24h}, {high_24h}]")
                    consistency_score -= 0.3
                
                if high_24h <= low_24h:
                    report['issues'].append(f"價格邏輯錯誤: 最高價 {high_24h} <= 最低價 {low_24h}")
                    consistency_score -= 0.5
            
            # 檢查時間戳一致性
            if 'timestamp' in market_data:
                timestamp = market_data['timestamp']
                if isinstance(timestamp, datetime):
                    time_diff = abs((datetime.now() - timestamp).total_seconds())
                    if time_diff > 300:  # 超過5分鐘
                        report['warnings'].append(f"數據時間戳過舊: {time_diff:.0f}秒前")
                        consistency_score -= 0.1
            
            # 檢查技術指標一致性
            if 'rsi' in market_data:
                rsi = market_data['rsi']
                if not (0 <= rsi <= 100):
                    report['issues'].append(f"RSI值異常: {rsi}")
                    consistency_score -= 0.2
            
            return max(0.0, consistency_score)
            
        except Exception as e:
            logger.error(f"❌ 一致性檢查失敗: {e}")
            return 0.0
    
    def _check_data_accuracy(self, market_data: Dict[str, Any], report: Dict[str, Any]) -> float:
        """檢查數據準確性"""
        try:
            accuracy_score = 1.0
            
            # 檢查價格範圍合理性
            if 'current_price' in market_data:
                price = float(market_data['current_price'])
                min_price, max_price = self.validation_rules['price_range']
                
                if not (min_price <= price <= max_price):
                    report['issues'].append(f"價格超出合理範圍: {price} (範圍: {min_price}-{max_price})")
                    accuracy_score -= 0.5
            
            # 檢查成交量合理性
            if 'volume_24h' in market_data:
                volume = float(market_data['volume_24h'])
                min_vol, max_vol = self.validation_rules['volume_range']
                
                if not (min_vol <= volume <= max_vol):
                    report['warnings'].append(f"成交量異常: {volume}")
                    accuracy_score -= 0.1
            
            # 檢查價格變化合理性
            if all(field in market_data for field in ['price_change_1m', 'price_change_5m']):
                change_1m = abs(float(market_data.get('price_change_1m', 0)))
                change_5m = abs(float(market_data.get('price_change_5m', 0)))
                
                limit = self.validation_rules['price_change_limit'] * 100
                
                if change_1m > limit:
                    report['warnings'].append(f"1分鐘價格變化過大: {change_1m:.2f}%")
                    accuracy_score -= 0.1
                
                if change_5m > limit:
                    report['warnings'].append(f"5分鐘價格變化過大: {change_5m:.2f}%")
                    accuracy_score -= 0.1
            
            return max(0.0, accuracy_score)
            
        except Exception as e:
            logger.error(f"❌ 準確性檢查失敗: {e}")
            return 0.0
    
    def clean_market_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗市場數據
        
        Args:
            market_data: 原始市場數據
            
        Returns:
            清洗後的市場數據
        """
        try:
            cleaned_data = market_data.copy()
            
            # 處理缺失值
            cleaned_data = self._handle_missing_values(cleaned_data)
            
            # 處理異常值
            cleaned_data = self._handle_outliers(cleaned_data)
            
            # 標準化數據格式
            cleaned_data = self._standardize_data_format(cleaned_data)
            
            # 添加數據質量標記
            cleaned_data['data_quality'] = 'cleaned'
            cleaned_data['cleaning_timestamp'] = datetime.now()
            
            logger.info("✅ 數據清洗完成")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"❌ 數據清洗失敗: {e}")
            return market_data
    
    def _handle_missing_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理缺失值"""
        try:
            # 為缺失的數值字段提供默認值
            defaults = {
                'current_price': 0,
                'volume_24h': 0,
                'price_change_1m': 0,
                'price_change_5m': 0,
                'rsi': 50,
                'volume_ratio': 1.0
            }
            
            for field, default_value in defaults.items():
                if field not in data or data[field] is None:
                    data[field] = default_value
                    logger.warning(f"⚠️ 字段 {field} 缺失，使用默認值 {default_value}")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ 處理缺失值失敗: {e}")
            return data
    
    def _handle_outliers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理異常值"""
        try:
            # 價格異常值處理
            if 'current_price' in data:
                price = float(data['current_price'])
                min_price, max_price = self.validation_rules['price_range']
                
                if price < min_price:
                    data['current_price'] = min_price
                    logger.warning(f"⚠️ 價格過低，調整為最小值: {min_price}")
                elif price > max_price:
                    data['current_price'] = max_price
                    logger.warning(f"⚠️ 價格過高，調整為最大值: {max_price}")
            
            # RSI異常值處理
            if 'rsi' in data:
                rsi = float(data['rsi'])
                if rsi < 0:
                    data['rsi'] = 0
                elif rsi > 100:
                    data['rsi'] = 100
            
            # 成交量異常值處理
            if 'volume_ratio' in data:
                ratio = float(data['volume_ratio'])
                if ratio < 0:
                    data['volume_ratio'] = 0
                elif ratio > 10:  # 限制最大10倍
                    data['volume_ratio'] = 10
            
            return data
            
        except Exception as e:
            logger.error(f"❌ 處理異常值失敗: {e}")
            return data
    
    def _standardize_data_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """標準化數據格式"""
        try:
            # 確保數值字段為float類型
            numeric_fields = [
                'current_price', 'volume_24h', 'high_24h', 'low_24h', 'open_24h',
                'price_change_1m', 'price_change_5m', 'rsi', 'volume_ratio'
            ]
            
            for field in numeric_fields:
                if field in data and data[field] is not None:
                    try:
                        data[field] = float(data[field])
                    except (ValueError, TypeError):
                        logger.warning(f"⚠️ 無法轉換字段 {field} 為數值")
            
            # 確保時間戳格式
            if 'timestamp' in data and not isinstance(data['timestamp'], datetime):
                try:
                    if isinstance(data['timestamp'], str):
                        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                    else:
                        data['timestamp'] = datetime.now()
                except:
                    data['timestamp'] = datetime.now()
            
            return data
            
        except Exception as e:
            logger.error(f"❌ 標準化數據格式失敗: {e}")
            return data
    
    def validate_klines_data(self, klines_data: Dict[str, pd.DataFrame]) -> Tuple[bool, Dict[str, Any]]:
        """
        驗證K線數據質量
        
        Args:
            klines_data: K線數據字典
            
        Returns:
            (is_valid, validation_report): 驗證結果和報告
        """
        try:
            validation_report = {
                'timestamp': datetime.now(),
                'overall_valid': True,
                'timeframe_reports': {},
                'issues': [],
                'warnings': []
            }
            
            for timeframe, df in klines_data.items():
                if df is None or df.empty:
                    validation_report['issues'].append(f"{timeframe} 數據為空")
                    continue
                
                # 檢查必要列
                required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    validation_report['issues'].append(f"{timeframe} 缺失列: {missing_columns}")
                    continue
                
                # 檢查數據完整性
                null_counts = df.isnull().sum()
                if null_counts.sum() > 0:
                    validation_report['warnings'].append(f"{timeframe} 存在空值: {null_counts.to_dict()}")
                
                # 檢查價格邏輯
                invalid_prices = (df['high'] < df['low']) | (df['high'] < df['open']) | (df['high'] < df['close']) | \
                                (df['low'] > df['open']) | (df['low'] > df['close'])
                
                if invalid_prices.any():
                    validation_report['issues'].append(f"{timeframe} 存在價格邏輯錯誤")
                
                # 檢查時間序列
                if not df['timestamp'].is_monotonic_increasing:
                    validation_report['warnings'].append(f"{timeframe} 時間序列不是遞增的")
                
                validation_report['timeframe_reports'][timeframe] = {
                    'rows': len(df),
                    'null_values': null_counts.sum(),
                    'time_range': f"{df['timestamp'].min()} - {df['timestamp'].max()}"
                }
            
            validation_report['overall_valid'] = len(validation_report['issues']) == 0
            
            return validation_report['overall_valid'], validation_report
            
        except Exception as e:
            logger.error(f"❌ K線數據驗證失敗: {e}")
            return False, {'error': str(e)}
    
    def get_data_quality_stats(self) -> Dict[str, Any]:
        """獲取數據質量統計"""
        return self.data_quality_stats.copy()
    
    def format_validation_report(self, report: Dict[str, Any]) -> str:
        """格式化驗證報告"""
        try:
            if 'error' in report:
                return f"❌ 驗證錯誤: {report['error']}"
            
            formatted = f"""
🔍 數據質量驗證報告 ({report['timestamp'].strftime('%H:%M:%S')})

📊 總體評估: {'✅ 通過' if report['overall_valid'] else '❌ 未通過'}
📈 質量分數: {report.get('quality_score', 0):.1%}

📋 詳細評分:
- 數據完整性: {report.get('data_completeness', 0):.1%}
- 數據一致性: {report.get('data_consistency', 0):.1%}
- 數據準確性: {report.get('data_accuracy', 0):.1%}

⚠️ 問題 ({len(report.get('issues', []))}):
{chr(10).join(f"  • {issue}" for issue in report.get('issues', []))}

💡 警告 ({len(report.get('warnings', []))}):
{chr(10).join(f"  • {warning}" for warning in report.get('warnings', []))}
"""
            
            return formatted.strip()
            
        except Exception as e:
            logger.error(f"❌ 格式化驗證報告失敗: {e}")
            return "驗證報告格式化失敗"


# 創建全局數據驗證器實例
def create_data_validator() -> MarketDataValidator:
    """創建數據驗證器實例"""
    return MarketDataValidator()


# 測試代碼
if __name__ == "__main__":
    print("🧪 測試數據驗證器...")
    
    # 創建測試數據
    test_data = {
        'current_price': 1500000,
        'timestamp': datetime.now(),
        'volume_24h': 1000000,
        'high_24h': 1520000,
        'low_24h': 1480000,
        'open_24h': 1490000,
        'price_change_1m': 0.5,
        'price_change_5m': 1.2,
        'rsi': 65,
        'volume_ratio': 1.2
    }
    
    # 測試驗證器
    validator = create_data_validator()
    is_valid, report = validator.validate_market_data(test_data)
    
    print(f"✅ 驗證結果: {'通過' if is_valid else '失敗'}")
    print(validator.format_validation_report(report))
    
    # 測試數據清洗
    cleaned_data = validator.clean_market_data(test_data)
    print(f"✅ 數據清洗完成，字段數量: {len(cleaned_data)}")