#!/usr/bin/env python3
"""
改進的 MAX MACD 計算器

基於真實 MAX 參考數據的 MACD 計算器，提供驗證和持續改進功能
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import json
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MACDData:
    """MACD 數據結構"""
    timestamp: str
    price: float
    histogram: float
    macd_line: float
    signal_line: float
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp,
            'price': self.price,
            'histogram': self.histogram,
            'macd_line': self.macd_line,
            'signal_line': self.signal_line
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MACDData':
        return cls(
            timestamp=data['timestamp'],
            price=data['price'],
            histogram=data['histogram'],
            macd_line=data['macd_line'],
            signal_line=data['signal_line']
        )

@dataclass
class ValidationResult:
    """驗證結果"""
    timestamp: str
    calculated: MACDData
    reference: MACDData
    histogram_diff: float
    macd_diff: float
    signal_diff: float
    accuracy: float

class ImprovedMaxMACDCalculator:
    """改進的 MAX MACD 計算器"""
    
    def __init__(self, fast_period=12, slow_period=26, signal_period=9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        # 載入真實的 MAX 參考數據
        self.reference_data = self._load_reference_data()
        
        logger.info(f"MAX MACD Calculator 初始化完成，載入 {len(self.reference_data)} 個參考數據點")
    
    def _load_reference_data(self) -> Dict[str, MACDData]:
        """載入真實的 MAX 參考數據"""
        reference_data = {
            '2025-07-30 05:00': MACDData('2025-07-30 05:00', 3520000.0, -2877.2, -3124.9, -247.7),
            '2025-07-30 06:00': MACDData('2025-07-30 06:00', 3519738.5, -2160.4, -2948.2, -787.8),
            '2025-07-30 07:00': MACDData('2025-07-30 07:00', 3519738.5, -1317.1, -2434.1, -1117.1),
            '2025-07-30 08:00': MACDData('2025-07-30 08:00', 3520000.0, -1059.5, -2441.4, -1381.9),
            '2025-07-30 09:00': MACDData('2025-07-30 09:00', 3520000.0, -756.2, -2327.2, -1571.0),
            '2025-07-30 10:00': MACDData('2025-07-30 10:00', 3520945.1, -83.9, -1675.8, -1592.0),
            '2025-07-30 11:00': MACDData('2025-07-30 11:00', 3522000.0, 731.6, -677.4, -1409.0),
        }
        return reference_data
    
    def calculate_ema(self, prices: List[float], period: int, 
                     alpha_multiplier: float = 1.0, init_method: str = 'sma') -> List[float]:
        """計算 EMA"""
        if len(prices) < period:
            return []
        
        alpha = (2.0 / (period + 1)) * alpha_multiplier
        ema_values = []
        
        if init_method == 'sma':
            # 使用 SMA 初始化
            sma = sum(prices[:period]) / period
            ema_values.append(sma)
            start_idx = period
        elif init_method == 'first':
            # 使用第一個值初始化
            ema_values.append(prices[0])
            start_idx = 1
        else:
            raise ValueError(f"不支持的初始化方法: {init_method}")
        
        # 計算後續的 EMA 值
        for i in range(start_idx, len(prices)):
            ema = alpha * prices[i] + (1 - alpha) * ema_values[-1]
            ema_values.append(ema)
        
        return ema_values
    
    def calculate_macd(self, prices: List[float], timestamps: List[str] = None,
                      alpha_multiplier: float = 1.0, init_method: str = 'sma') -> Tuple[List[float], List[float], List[float]]:
        """計算 MACD 指標"""
        if len(prices) < self.slow_period + self.signal_period:
            logger.warning(f"價格數據不足，需要至少 {self.slow_period + self.signal_period} 個數據點")
            return [], [], []
        
        # 計算快線和慢線 EMA
        fast_ema = self.calculate_ema(prices, self.fast_period, alpha_multiplier, init_method)
        slow_ema = self.calculate_ema(prices, self.slow_period, alpha_multiplier, init_method)
        
        # 計算 MACD 線
        macd_line = []
        min_len = min(len(fast_ema), len(slow_ema))
        
        for i in range(min_len):
            macd_value = fast_ema[i] - slow_ema[i]
            macd_line.append(round(macd_value, 1))
        
        # 計算信號線
        signal_line = self.calculate_ema(macd_line, self.signal_period, alpha_multiplier, init_method)
        signal_line = [round(x, 1) for x in signal_line]
        
        # 計算柱狀圖
        histogram = []
        signal_start = len(macd_line) - len(signal_line)
        
        for i in range(len(signal_line)):
            hist_value = macd_line[i + signal_start] - signal_line[i]
            histogram.append(round(hist_value, 1))
        
        return macd_line[signal_start:], signal_line, histogram
    
    def validate_against_reference(self, prices: List[float], timestamps: List[str],
                                 alpha_multiplier: float = 1.0, init_method: str = 'sma') -> Dict:
        """使用參考數據驗證計算結果"""
        macd_line, signal_line, histogram = self.calculate_macd(
            prices, timestamps, alpha_multiplier, init_method
        )
        
        validation_results = []
        total_error = 0
        valid_comparisons = 0
        
        # 為每個參考數據點進行驗證
        for timestamp, reference in self.reference_data.items():
            if timestamp in timestamps:
                timestamp_index = timestamps.index(timestamp)
                result_index = timestamp_index - (len(timestamps) - len(histogram))
                
                if 0 <= result_index < len(histogram):
                    calculated = MACDData(
                        timestamp=timestamp,
                        price=reference.price,
                        histogram=histogram[result_index],
                        macd_line=macd_line[result_index],
                        signal_line=signal_line[result_index]
                    )
                    
                    # 計算誤差
                    hist_error = abs(calculated.histogram - reference.histogram)
                    macd_error = abs(calculated.macd_line - reference.macd_line)
                    signal_error = abs(calculated.signal_line - reference.signal_line)
                    
                    total_error += hist_error + macd_error + signal_error
                    valid_comparisons += 1
                    
                    # 計算準確率
                    total_ref = abs(reference.histogram) + abs(reference.macd_line) + abs(reference.signal_line)
                    accuracy = max(0, 1 - ((hist_error + macd_error + signal_error) / total_ref)) if total_ref > 0 else 0
                    
                    validation_results.append(ValidationResult(
                        timestamp=timestamp,
                        calculated=calculated,
                        reference=reference,
                        histogram_diff=hist_error,
                        macd_diff=macd_error,
                        signal_diff=signal_error,
                        accuracy=accuracy
                    ))
        
        # 計算總體準確率
        overall_accuracy = sum(result.accuracy for result in validation_results) / len(validation_results) if validation_results else 0
        avg_error = total_error / valid_comparisons if valid_comparisons > 0 else float('inf')
        
        return {
            'overall_accuracy': overall_accuracy,
            'avg_error': avg_error,
            'valid_comparisons': valid_comparisons,
            'validation_results': validation_results,
            'parameters': {
                'alpha_multiplier': alpha_multiplier,
                'init_method': init_method
            }
        }
    
    def find_best_parameters(self, prices: List[float], timestamps: List[str]) -> Dict:
        """尋找最佳參數組合"""
        logger.info("開始尋找最佳參數組合...")
        
        alpha_multipliers = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
        init_methods = ['sma', 'first']
        
        best_result = None
        best_accuracy = 0
        
        for alpha_mult in alpha_multipliers:
            for init_method in init_methods:
                try:
                    result = self.validate_against_reference(prices, timestamps, alpha_mult, init_method)
                    
                    if result['overall_accuracy'] > best_accuracy:
                        best_accuracy = result['overall_accuracy']
                        best_result = result
                        
                    logger.info(f"Alpha={alpha_mult:.1f}, Init={init_method}: 準確率={result['overall_accuracy']:.2%}")
                    
                except Exception as e:
                    logger.warning(f"參數組合 Alpha={alpha_mult:.1f}, Init={init_method} 測試失敗: {e}")
        
        if best_result:
            logger.info(f"最佳參數: Alpha={best_result['parameters']['alpha_multiplier']:.1f}, "
                       f"Init={best_result['parameters']['init_method']}, "
                       f"準確率={best_result['overall_accuracy']:.2%}")
        
        return best_result
    
    def generate_validation_report(self, validation_result: Dict) -> str:
        """生成驗證報告"""
        report = []
        report.append("MAX MACD 計算器驗證報告")
        report.append("=" * 50)
        report.append(f"總體準確率: {validation_result['overall_accuracy']:.2%}")
        report.append(f"平均誤差: {validation_result['avg_error']:.1f}")
        report.append(f"有效比較: {validation_result['valid_comparisons']} 個")
        report.append(f"參數設置: Alpha={validation_result['parameters']['alpha_multiplier']:.1f}, "
                     f"Init={validation_result['parameters']['init_method']}")
        report.append("")
        
        report.append("詳細比較結果:")
        report.append("-" * 80)
        report.append(f"{'時間':15s} {'參考柱狀':>10s} {'計算柱狀':>10s} {'參考MACD':>10s} {'計算MACD':>10s} "
                     f"{'參考信號':>10s} {'計算信號':>10s} {'準確率':>8s}")
        report.append("-" * 80)
        
        for result in validation_result['validation_results']:
            ref = result.reference
            calc = result.calculated
            
            report.append(f"{result.timestamp:15s} "
                         f"{ref.histogram:10.1f} {calc.histogram:10.1f} "
                         f"{ref.macd_line:10.1f} {calc.macd_line:10.1f} "
                         f"{ref.signal_line:10.1f} {calc.signal_line:10.1f} "
                         f"{result.accuracy:7.1%}")
        
        return "\\n".join(report)
    
    def add_reference_data(self, timestamp: str, price: float, histogram: float, 
                          macd_line: float, signal_line: float):
        """添加新的參考數據"""
        self.reference_data[timestamp] = MACDData(
            timestamp=timestamp,
            price=price,
            histogram=histogram,
            macd_line=macd_line,
            signal_line=signal_line
        )
        logger.info(f"添加新的參考數據: {timestamp}")
    
    def save_reference_data(self, filename: str = 'max_reference_data.json'):
        """保存參考數據"""
        data = {timestamp: macd_data.to_dict() for timestamp, macd_data in self.reference_data.items()}
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"參考數據已保存到: {filename}")
    
    def load_reference_data(self, filename: str):
        """從文件載入參考數據"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for timestamp, values in data.items():
                self.reference_data[timestamp] = MACDData.from_dict(values)
            
            logger.info(f"從 {filename} 載入了 {len(data)} 個參考數據點")
        except Exception as e:
            logger.error(f"載入參考數據失敗: {e}")

def create_sample_price_data(reference_data: Dict[str, MACDData], num_history_points: int = 50) -> Tuple[List[float], List[str]]:
    """創建示例價格數據用於測試"""
    # 提取參考價格
    ref_prices = [data.price for data in reference_data.values()]
    ref_timestamps = list(reference_data.keys())
    
    # 創建歷史價格數據
    base_price = 3500000
    prices = []
    timestamps = []
    
    # 生成歷史數據
    start_time = datetime.strptime(ref_timestamps[0], '%Y-%m-%d %H:%M') - timedelta(hours=num_history_points)
    
    for i in range(num_history_points):
        # 模擬價格變化
        progress = i / num_history_points
        target_price = ref_prices[0]
        
        # 添加隨機波動
        noise = np.random.normal(0, 5000)
        price = base_price + (target_price - base_price) * progress + noise
        prices.append(price)
        
        # 生成時間戳
        timestamp = start_time + timedelta(hours=i)
        timestamps.append(timestamp.strftime('%Y-%m-%d %H:%M'))
    
    # 添加參考數據
    for timestamp, data in reference_data.items():
        prices.append(data.price)
        timestamps.append(timestamp)
    
    return prices, timestamps

# 便利函數
def test_max_macd_calculator():
    """測試 MAX MACD 計算器"""
    calculator = ImprovedMaxMACDCalculator()
    
    # 創建測試數據
    prices, timestamps = create_sample_price_data(calculator.reference_data)
    
    print(f"測試數據: {len(prices)} 個價格點")
    print(f"參考數據: {len(calculator.reference_data)} 個")
    print()
    
    # 尋找最佳參數
    best_result = calculator.find_best_parameters(prices, timestamps)
    
    if best_result:
        # 生成報告
        report = calculator.generate_validation_report(best_result)
        print(report)
        
        # 保存結果
        with open('max_macd_validation_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("\\n報告已保存到: max_macd_validation_report.txt")
        
        return best_result
    else:
        print("未找到有效的參數組合")
        return None

if __name__ == "__main__":
    test_max_macd_calculator()