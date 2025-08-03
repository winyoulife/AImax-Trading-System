#!/usr/bin/env python3
"""
完全精確的MAX MACD計算器
基於深度分析找到的最佳算法
"""

import pandas as pd
import numpy as np

class ExactMaxMACDCalculator:
    """完全精確的MAX MACD計算器"""
    
    @staticmethod
    def calculate_custom_ema(series, period, alpha_multiplier=1.0, init_method='first'):
        """
        自定義EMA計算 - 與MAX完全匹配的方法
        
        Args:
            series: 價格序列
            period: EMA週期
            alpha_multiplier: alpha乘數 (默認1.0)
            init_method: 初始化方法 ('first', 'sma', 'zero')
        """
        alpha = (2.0 / (period + 1)) * alpha_multiplier
        result = pd.Series(index=series.index, dtype=float)
        
        if init_method == 'first':
            result.iloc[0] = series.iloc[0]
        elif init_method == 'sma':
            if len(series) >= period:
                result.iloc[period-1] = series.iloc[:period].mean()
                # 填充前面的NaN
                for i in range(period-1):
                    result.iloc[i] = np.nan
            else:
                result.iloc[0] = series.iloc[0]
        elif init_method == 'zero':
            result.iloc[0] = 0
        
        start_idx = period if init_method == 'sma' and len(series) >= period else 1
        
        for i in range(start_idx, len(series)):
            if pd.isna(result.iloc[i-1]):
                result.iloc[i] = series.iloc[i]
            else:
                result.iloc[i] = alpha * series.iloc[i] + (1 - alpha) * result.iloc[i-1]
        
        return result
    
    @staticmethod
    def calculate_exact_macd(df):
        """
        計算與MAX完全匹配的MACD
        
        基於深度分析的最佳配置:
        - 價格源: close
        - 參數: (12.0, 26.0, 9.0)
        - Alpha乘數: 1.0
        - 初始化: first value
        """
        # 使用收盤價
        price_series = df['close']
        
        # 計算快速和慢速EMA
        exp1 = ExactMaxMACDCalculator.calculate_custom_ema(
            price_series, 12.0, 1.0, 'first'
        )
        exp2 = ExactMaxMACDCalculator.calculate_custom_ema(
            price_series, 26.0, 1.0, 'first'
        )
        
        # 計算MACD線
        macd = exp1 - exp2
        
        # 計算信號線
        macd_signal = ExactMaxMACDCalculator.calculate_custom_ema(
            macd, 9.0, 1.0, 'first'
        )
        
        # 計算柱狀圖
        macd_hist = macd - macd_signal
        
        return macd, macd_signal, macd_hist
    
    @staticmethod
    def add_exact_macd_to_dataframe(df):
        """
        將精確的MACD指標添加到DataFrame中
        """
        df = df.copy()
        
        # 計算MACD
        macd, macd_signal, macd_hist = ExactMaxMACDCalculator.calculate_exact_macd(df)
        
        # 添加到DataFrame
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
        
        return df
    
    @staticmethod
    def validate_against_max_data(df, max_reference_data):
        """
        驗證計算結果與MAX參考數據的匹配度
        
        Args:
            df: 包含MACD數據的DataFrame
            max_reference_data: MAX參考數據列表
            
        Returns:
            驗證結果字典
        """
        if df.empty or not max_reference_data:
            return {'accuracy': 0, 'avg_error': float('inf'), 'details': []}
        
        total_error = 0
        valid_comparisons = 0
        details = []
        
        for ref in max_reference_data:
            # 找到對應時間點的數據
            matching_rows = df[df['timestamp'] == ref['timestamp']] if 'timestamp' in df.columns else pd.DataFrame()
            
            if matching_rows.empty:
                continue
            
            row = matching_rows.iloc[0]
            
            # 計算誤差
            hist_error = abs(row['macd_hist'] - ref['histogram'])
            macd_error = abs(row['macd'] - ref['macd'])
            signal_error = abs(row['macd_signal'] - ref['signal'])
            
            total_error += hist_error + macd_error + signal_error
            valid_comparisons += 1
            
            details.append({
                'timestamp': ref['timestamp'],
                'datetime': ref.get('datetime', 'Unknown'),
                'our_histogram': row['macd_hist'],
                'max_histogram': ref['histogram'],
                'our_macd': row['macd'],
                'max_macd': ref['macd'],
                'our_signal': row['macd_signal'],
                'max_signal': ref['signal'],
                'histogram_error': hist_error,
                'macd_error': macd_error,
                'signal_error': signal_error,
                'total_error': hist_error + macd_error + signal_error
            })
        
        if valid_comparisons > 0:
            avg_error = total_error / valid_comparisons
            accuracy = max(0, 100 - avg_error / 50)  # 轉換為百分比
        else:
            avg_error = float('inf')
            accuracy = 0
        
        return {
            'accuracy': accuracy,
            'avg_error': avg_error,
            'valid_comparisons': valid_comparisons,
            'details': details
        }
    
    @staticmethod
    def get_latest_macd_summary(df):
        """
        獲取最新的MACD摘要信息
        """
        if df.empty or 'macd' not in df.columns:
            return {}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # 判斷趨勢
        hist_trend = "上升" if latest['macd_hist'] > prev['macd_hist'] else "下降"
        macd_trend = "上升" if latest['macd'] > prev['macd'] else "下降"
        signal_trend = "上升" if latest['macd_signal'] > prev['macd_signal'] else "下降"
        
        # 判斷金叉死叉
        signal_type = "無明顯信號"
        if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
            signal_type = "金叉 (買入信號)"
        elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
            signal_type = "死叉 (賣出信號)"
        
        return {
            'latest_datetime': latest.get('datetime', None),
            'latest_price': latest.get('close', 0),
            'latest_histogram': latest['macd_hist'],
            'latest_macd': latest['macd'],
            'latest_signal': latest['macd_signal'],
            'histogram_trend': hist_trend,
            'macd_trend': macd_trend,
            'signal_trend': signal_trend,
            'signal_type': signal_type,
            'position': '零軸上方' if latest['macd'] > 0 else '零軸下方'
        }

# 便利函數
def calculate_exact_max_macd(prices_df):
    """
    便利函數：為包含價格數據的DataFrame計算精確的MAX MACD
    
    Args:
        prices_df: 包含'close'列的DataFrame
        
    Returns:
        添加了MACD列的DataFrame
    """
    return ExactMaxMACDCalculator.add_exact_macd_to_dataframe(prices_df)

def get_exact_macd_values(prices_df):
    """
    便利函數：獲取精確的MACD值
    
    Args:
        prices_df: 包含'close'列的DataFrame
        
    Returns:
        (macd, macd_signal, macd_histogram) 的元組
    """
    return ExactMaxMACDCalculator.calculate_exact_macd(prices_df)