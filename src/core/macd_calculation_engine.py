#!/usr/bin/env python3
"""
MACD計算引擎核心
使用多種算法來找出與MAX交易所完全匹配的計算方法
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MACDResult:
    """MACD計算結果"""
    macd: float
    macd_signal: float
    macd_histogram: float
    method_name: str
    accuracy_score: float = 0.0

@dataclass
class MACDReference:
    """MAX參考數據"""
    timestamp: int
    datetime: datetime
    price: float
    histogram: float
    macd: float
    signal: float

class MACDCalculationEngine:
    """MACD計算引擎"""
    
    def __init__(self):
        self.max_reference_data = self._load_max_reference_data()
    
    def _load_max_reference_data(self) -> List[MACDReference]:
        """載入MAX參考數據"""
        # 根據你提供的MAX實際數據
        reference_data = [
            MACDReference(
                timestamp=1753822800,  # 2025-07-30 05:00
                datetime=datetime(2025, 7, 30, 5, 0),
                price=3507692.3,
                histogram=-2877.2,
                macd=-3124.9,
                signal=-247.7
            ),
            MACDReference(
                timestamp=1753819200,  # 2025-07-30 04:00
                datetime=datetime(2025, 7, 30, 4, 0),
                price=3507692.3,
                histogram=-3440.3,
                macd=-2968.7,
                signal=471.6
            ),
            MACDReference(
                timestamp=1753826400,  # 2025-07-30 06:00
                datetime=datetime(2025, 7, 30, 6, 0),
                price=3507692.3,
                histogram=-2160.4,
                macd=-2948.2,
                signal=-787.8
            ),
            MACDReference(
                timestamp=1753830000,  # 2025-07-30 07:00
                datetime=datetime(2025, 7, 30, 7, 0),
                price=3507692.3,
                histogram=-1431.7,
                macd=-2577.4,
                signal=-1145.7
            )
        ]
        return reference_data
    
    def calculate_traditional_macd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """方法1：傳統EMA計算（adjust=False）"""
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist
    
    def calculate_alpha_macd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """方法2：使用alpha參數的EMA計算"""
        alpha_12 = 2 / (12 + 1)  # 0.1538
        alpha_26 = 2 / (26 + 1)  # 0.0741
        alpha_9 = 2 / (9 + 1)    # 0.2
        
        exp1 = df['close'].ewm(alpha=alpha_12, adjust=False).mean()
        exp2 = df['close'].ewm(alpha=alpha_26, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(alpha=alpha_9, adjust=False).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist
    
    def calculate_adjusted_macd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """方法3：使用adjust=True的EMA計算"""
        exp1 = df['close'].ewm(span=12, adjust=True).mean()
        exp2 = df['close'].ewm(span=26, adjust=True).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=9, adjust=True).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist
    
    def calculate_custom_ema_macd(self, df: pd.DataFrame, fast=12, slow=26, signal=9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """方法4：自定義參數的MACD計算"""
        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist
    
    def calculate_smoothed_macd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """方法5：使用額外平滑的MACD計算"""
        # 先計算基本MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        
        # 對MACD進行額外平滑
        macd_smoothed = macd.ewm(span=3, adjust=False).mean()
        macd_signal = macd_smoothed.ewm(span=9, adjust=False).mean()
        macd_hist = macd_smoothed - macd_signal
        return macd_smoothed, macd_signal, macd_hist
    
    def calculate_weighted_macd(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """方法6：使用加權移動平均的MACD"""
        # 使用不同的權重計算
        weights_12 = np.arange(1, 13)
        weights_26 = np.arange(1, 27)
        
        exp1 = df['close'].rolling(window=12).apply(lambda x: np.average(x, weights=weights_12), raw=True)
        exp2 = df['close'].rolling(window=26).apply(lambda x: np.average(x, weights=weights_26), raw=True)
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist
    
    def calculate_all_methods(self, df: pd.DataFrame) -> Dict[str, Tuple[pd.Series, pd.Series, pd.Series]]:
        """計算所有方法的MACD"""
        methods = {
            'traditional': self.calculate_traditional_macd,
            'alpha': self.calculate_alpha_macd,
            'adjusted': self.calculate_adjusted_macd,
            'custom_11_25_8': lambda df: self.calculate_custom_ema_macd(df, 11, 25, 8),
            'custom_13_27_10': lambda df: self.calculate_custom_ema_macd(df, 13, 27, 10),
            'smoothed': self.calculate_smoothed_macd,
            'weighted': self.calculate_weighted_macd,
        }
        
        results = {}
        for name, method in methods.items():
            try:
                macd, signal, hist = method(df)
                results[name] = (macd, signal, hist)
            except Exception as e:
                print(f"方法 {name} 計算失敗: {e}")
                continue
        
        return results
    
    def validate_against_max(self, df: pd.DataFrame, method_results: Dict[str, Tuple[pd.Series, pd.Series, pd.Series]]) -> Dict[str, float]:
        """驗證計算結果與MAX參考數據的匹配度"""
        accuracy_scores = {}
        
        for method_name, (macd, signal, hist) in method_results.items():
            total_error = 0
            valid_comparisons = 0
            
            for ref in self.max_reference_data:
                # 找到對應時間點的數據
                matching_rows = df[df['timestamp'] == ref.timestamp]
                if matching_rows.empty:
                    continue
                
                idx = matching_rows.index[0]
                if idx >= len(macd) or pd.isna(macd.iloc[idx]):
                    continue
                
                # 計算誤差
                hist_error = abs(hist.iloc[idx] - ref.histogram)
                macd_error = abs(macd.iloc[idx] - ref.macd)
                signal_error = abs(signal.iloc[idx] - ref.signal)
                
                # 總誤差（加權）
                total_error += hist_error * 0.4 + macd_error * 0.3 + signal_error * 0.3
                valid_comparisons += 1
            
            if valid_comparisons > 0:
                avg_error = total_error / valid_comparisons
                # 轉換為準確度分數（誤差越小，分數越高）
                accuracy_scores[method_name] = max(0, 100 - avg_error / 10)
            else:
                accuracy_scores[method_name] = 0
        
        return accuracy_scores
    
    def find_best_algorithm(self, df: pd.DataFrame) -> Tuple[str, Dict[str, float]]:
        """找出最佳算法"""
        print("=== 開始MACD算法比較測試 ===")
        
        # 計算所有方法
        method_results = self.calculate_all_methods(df)
        
        # 驗證準確度
        accuracy_scores = self.validate_against_max(df, method_results)
        
        # 找出最佳方法
        best_method = max(accuracy_scores.items(), key=lambda x: x[1])
        
        print(f"\n=== 算法準確度排名 ===")
        sorted_scores = sorted(accuracy_scores.items(), key=lambda x: x[1], reverse=True)
        for i, (method, score) in enumerate(sorted_scores, 1):
            print(f"{i}. {method}: {score:.2f}%")
        
        print(f"\n🏆 最佳算法: {best_method[0]} (準確度: {best_method[1]:.2f}%)")
        
        return best_method[0], accuracy_scores
    
    def get_detailed_comparison(self, df: pd.DataFrame, method_name: str) -> None:
        """獲取詳細比較結果"""
        method_results = self.calculate_all_methods(df)
        
        if method_name not in method_results:
            print(f"方法 {method_name} 不存在")
            return
        
        macd, signal, hist = method_results[method_name]
        
        print(f"\n=== {method_name} 方法詳細比較 ===")
        print("時間\t\t\tMAX柱狀圖\t我們柱狀圖\t差異\t\tMAX MACD\t我們MACD\t差異")
        print("-" * 100)
        
        for ref in self.max_reference_data:
            matching_rows = df[df['timestamp'] == ref.timestamp]
            if matching_rows.empty:
                continue
            
            idx = matching_rows.index[0]
            if idx >= len(macd) or pd.isna(macd.iloc[idx]):
                continue
            
            our_hist = hist.iloc[idx]
            our_macd = macd.iloc[idx]
            our_signal = signal.iloc[idx]
            
            hist_diff = our_hist - ref.histogram
            macd_diff = our_macd - ref.macd
            
            print(f"{ref.datetime.strftime('%Y-%m-%d %H:%M')}\t"
                  f"{ref.histogram:.1f}\t\t{our_hist:.1f}\t\t{hist_diff:+.1f}\t\t"
                  f"{ref.macd:.1f}\t\t{our_macd:.1f}\t\t{macd_diff:+.1f}")
    
    def reverse_engineer_parameters(self, df: pd.DataFrame) -> Dict[str, any]:
        """反向工程MAX的參數"""
        print("\n=== 開始反向工程MAX參數 ===")
        
        best_params = None
        best_score = 0
        
        # 測試不同的參數組合
        param_combinations = [
            {'fast': 12, 'slow': 26, 'signal': 9, 'adjust': False},
            {'fast': 12, 'slow': 26, 'signal': 9, 'adjust': True},
            {'fast': 11, 'slow': 25, 'signal': 8, 'adjust': False},
            {'fast': 13, 'slow': 27, 'signal': 10, 'adjust': False},
            {'fast': 12, 'slow': 26, 'signal': 9, 'adjust': False, 'smooth': 2},
            {'fast': 12, 'slow': 26, 'signal': 9, 'adjust': False, 'smooth': 3},
        ]
        
        for params in param_combinations:
            try:
                # 計算MACD
                if 'smooth' in params:
                    exp1 = df['close'].ewm(span=params['fast'], adjust=params['adjust']).mean()
                    exp2 = df['close'].ewm(span=params['slow'], adjust=params['adjust']).mean()
                    macd = exp1 - exp2
                    macd = macd.ewm(span=params['smooth'], adjust=False).mean()  # 額外平滑
                    signal = macd.ewm(span=params['signal'], adjust=params['adjust']).mean()
                else:
                    exp1 = df['close'].ewm(span=params['fast'], adjust=params['adjust']).mean()
                    exp2 = df['close'].ewm(span=params['slow'], adjust=params['adjust']).mean()
                    macd = exp1 - exp2
                    signal = macd.ewm(span=params['signal'], adjust=params['adjust']).mean()
                
                hist = macd - signal
                
                # 計算準確度
                total_error = 0
                valid_comparisons = 0
                
                for ref in self.max_reference_data:
                    matching_rows = df[df['timestamp'] == ref.timestamp]
                    if matching_rows.empty:
                        continue
                    
                    idx = matching_rows.index[0]
                    if idx >= len(macd) or pd.isna(macd.iloc[idx]):
                        continue
                    
                    hist_error = abs(hist.iloc[idx] - ref.histogram)
                    macd_error = abs(macd.iloc[idx] - ref.macd)
                    signal_error = abs(signal.iloc[idx] - ref.signal)
                    
                    total_error += hist_error + macd_error + signal_error
                    valid_comparisons += 1
                
                if valid_comparisons > 0:
                    avg_error = total_error / valid_comparisons
                    score = max(0, 1000 - avg_error)  # 分數越高越好
                    
                    print(f"參數 {params}: 平均誤差 {avg_error:.2f}, 分數 {score:.2f}")
                    
                    if score > best_score:
                        best_score = score
                        best_params = params.copy()
            
            except Exception as e:
                print(f"參數 {params} 測試失敗: {e}")
        
        print(f"\n🎯 最佳參數: {best_params}")
        print(f"🏆 最佳分數: {best_score:.2f}")
        
        return best_params if best_params else {'fast': 12, 'slow': 26, 'signal': 9, 'adjust': False}