#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAX歷史資料庫完整性和數據品質驗證腳本
確保實盤測試前數據完全可靠
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
import logging
from typing import Dict, List, Tuple, Any

from data.historical_data_manager import create_historical_manager
from data.technical_indicators import TechnicalIndicatorCalculator

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HistoricalDataValidator:
    """歷史數據驗證器"""
    
    def __init__(self, db_path: str = "data/market_history.db"):
        self.db_path = db_path
        self.manager = create_historical_manager(db_path)
        self.tech_indicators = TechnicalIndicatorCalculator()
        
    async def run_full_validation(self) -> Dict[str, Any]:
        """執行完整的數據驗證"""
        print("🔍 開始MAX歷史資料庫完整性驗證...")
        
        validation_results = {
            'database_info': {},
            'data_integrity': {},
            'data_quality': {},
            'continuity_check': {},
            'technical_indicators': {},
            'auto_update_test': {},
            'summary': {}
        }
        
        try:
            # 1. 數據庫基本信息
            validation_results['database_info'] = await self._check_database_info()
            
            # 2. 數據完整性檢查
            validation_results['data_integrity'] = await self._check_data_integrity()
            
            # 3. 數據品質檢查
            validation_results['data_quality'] = await self._check_data_quality()
            
            # 4. 數據連續性檢查
            validation_results['continuity_check'] = await self._check_data_continuity()
            
            # 5. 技術指標計算測試
            validation_results['technical_indicators'] = await self._test_technical_indicators()
            
            # 6. 自動更新功能測試
            validation_results['auto_update_test'] = await self._test_auto_update()
            
            # 7. 生成總結報告
            validation_results['summary'] = self._generate_summary(validation_results)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ 驗證過程發生錯誤: {e}")
            validation_results['error'] = str(e)
            return validation_results
    
    async def _check_database_info(self) -> Dict[str, Any]:
        """檢查數據庫基本信息"""
        print("\n📊 檢查數據庫基本信息...")
        
        try:
            stats = self.manager.get_data_statistics("btctwd")
            
            info = {
                'database_path': stats.get('database_path', ''),
                'database_size_mb': stats.get('database_size_mb', 0),
                'timeframe_stats': stats.get('timeframe_stats', {}),
                'update_stats': stats.get('update_stats', {}),
                'total_records': sum(tf['count'] for tf in stats.get('timeframe_stats', {}).values())
            }
            
            print(f"   📁 數據庫路徑: {info['database_path']}")
            print(f"   💾 數據庫大小: {info['database_size_mb']:.2f} MB")
            print(f"   📈 總記錄數: {info['total_records']}")
            
            for timeframe, tf_stats in info['timeframe_stats'].items():
                print(f"   ⏰ {timeframe}: {tf_stats['count']}條記錄，覆蓋{tf_stats['coverage_hours']:.1f}小時")
            
            return info
            
        except Exception as e:
            logger.error(f"❌ 檢查數據庫信息失敗: {e}")
            return {'error': str(e)}
    
    async def _check_data_integrity(self) -> Dict[str, Any]:
        """檢查數據完整性"""
        print("\n🔍 檢查數據完整性...")
        
        integrity_results = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查重複記錄
                cursor.execute('''
                    SELECT market, timeframe, timestamp, COUNT(*) as count
                    FROM klines 
                    GROUP BY market, timeframe, timestamp
                    HAVING COUNT(*) > 1
                ''')
                duplicates = cursor.fetchall()
                integrity_results['duplicates'] = len(duplicates)
                
                # 檢查NULL值
                cursor.execute('''
                    SELECT COUNT(*) FROM klines 
                    WHERE open IS NULL OR high IS NULL OR low IS NULL 
                       OR close IS NULL OR volume IS NULL
                ''')
                null_count = cursor.fetchone()[0]
                integrity_results['null_values'] = null_count
                
                # 檢查異常價格數據
                cursor.execute('''
                    SELECT COUNT(*) FROM klines 
                    WHERE high < low OR open < 0 OR close < 0 
                       OR high < 0 OR low < 0 OR volume < 0
                ''')
                invalid_prices = cursor.fetchone()[0]
                integrity_results['invalid_prices'] = invalid_prices
                
                # 檢查價格合理性 (極端值)
                for timeframe in ['1m', '5m', '1h']:
                    cursor.execute('''
                        SELECT MIN(close), MAX(close), AVG(close), 
                               MIN(volume), MAX(volume), AVG(volume)
                        FROM klines 
                        WHERE market = 'btctwd' AND timeframe = ?
                    ''', (timeframe,))
                    
                    result = cursor.fetchone()
                    if result:
                        min_price, max_price, avg_price, min_vol, max_vol, avg_vol = result
                        integrity_results[f'{timeframe}_price_range'] = {
                            'min': min_price, 'max': max_price, 'avg': avg_price,
                            'price_volatility': (max_price - min_price) / avg_price if avg_price > 0 else 0
                        }
                        integrity_results[f'{timeframe}_volume_range'] = {
                            'min': min_vol, 'max': max_vol, 'avg': avg_vol
                        }
                
                print(f"   🔄 重複記錄: {integrity_results['duplicates']}條")
                print(f"   ❌ NULL值: {integrity_results['null_values']}條")
                print(f"   ⚠️ 異常價格: {integrity_results['invalid_prices']}條")
                
                return integrity_results
                
        except Exception as e:
            logger.error(f"❌ 數據完整性檢查失敗: {e}")
            return {'error': str(e)}
    
    async def _check_data_quality(self) -> Dict[str, Any]:
        """檢查數據品質"""
        print("\n📈 檢查數據品質...")
        
        quality_results = {}
        
        try:
            for timeframe in ['1m', '5m', '1h']:
                df = self.manager.get_historical_data("btctwd", timeframe, 100)
                
                if df is not None and not df.empty:
                    # 計算基本統計
                    quality_results[f'{timeframe}_stats'] = {
                        'count': len(df),
                        'price_std': df['close'].std(),
                        'volume_std': df['volume'].std(),
                        'price_mean': df['close'].mean(),
                        'volume_mean': df['volume'].mean()
                    }
                    
                    # 檢查價格跳躍
                    df['price_change'] = df['close'].pct_change()
                    extreme_changes = (abs(df['price_change']) > 0.1).sum()  # 10%以上變化
                    quality_results[f'{timeframe}_extreme_changes'] = extreme_changes
                    
                    # 檢查成交量異常
                    volume_median = df['volume'].median()
                    volume_outliers = (df['volume'] > volume_median * 10).sum()
                    quality_results[f'{timeframe}_volume_outliers'] = volume_outliers
                    
                    print(f"   ⏰ {timeframe}: {len(df)}條記錄，極端變化{extreme_changes}次，成交量異常{volume_outliers}次")
                
            return quality_results
            
        except Exception as e:
            logger.error(f"❌ 數據品質檢查失敗: {e}")
            return {'error': str(e)}
    
    async def _check_data_continuity(self) -> Dict[str, Any]:
        """檢查數據連續性"""
        print("\n🔗 檢查數據連續性...")
        
        continuity_results = {}
        
        try:
            for timeframe in ['1m', '5m', '1h']:
                df = self.manager.get_historical_data("btctwd", timeframe, 500)
                
                if df is not None and not df.empty:
                    # 計算時間間隔
                    df = df.sort_values('timestamp')
                    time_diffs = df['timestamp'].diff()
                    
                    # 預期間隔
                    expected_interval = {'1m': 60, '5m': 300, '1h': 3600}[timeframe]
                    expected_timedelta = timedelta(seconds=expected_interval)
                    
                    # 找出間隔異常的記錄
                    normal_intervals = (time_diffs == expected_timedelta).sum()
                    total_intervals = len(time_diffs) - 1  # 排除第一個NaN
                    
                    if total_intervals > 0:
                        continuity_rate = normal_intervals / total_intervals
                        gaps = total_intervals - normal_intervals
                        
                        continuity_results[f'{timeframe}_continuity'] = {
                            'total_intervals': total_intervals,
                            'normal_intervals': normal_intervals,
                            'gaps': gaps,
                            'continuity_rate': continuity_rate,
                            'time_range': {
                                'start': df['timestamp'].min().isoformat(),
                                'end': df['timestamp'].max().isoformat()
                            }
                        }
                        
                        print(f"   ⏰ {timeframe}: 連續性{continuity_rate:.1%}，間隔異常{gaps}次")
                
            return continuity_results
            
        except Exception as e:
            logger.error(f"❌ 數據連續性檢查失敗: {e}")
            return {'error': str(e)}
    
    async def _test_technical_indicators(self) -> Dict[str, Any]:
        """測試技術指標計算"""
        print("\n📊 測試技術指標計算...")
        
        indicator_results = {}
        
        try:
            # 獲取多時間框架測試數據
            data_1m = self.manager.get_historical_data("btctwd", "1m", 100)
            data_5m = self.manager.get_historical_data("btctwd", "5m", 100)
            data_1h = self.manager.get_historical_data("btctwd", "1h", 100)
            
            klines_data = {}
            if data_1m is not None and not data_1m.empty:
                klines_data['1m'] = data_1m
            if data_5m is not None and not data_5m.empty:
                klines_data['5m'] = data_5m
            if data_1h is not None and not data_1h.empty:
                klines_data['1h'] = data_1h
            
            if klines_data:
                # 測試技術指標計算
                indicators = self.tech_indicators.calculate_comprehensive_indicators(klines_data)
                
                indicator_results['total_indicators'] = len(indicators)
                indicator_results['calculated_indicators'] = list(indicators.keys())
                
                # 檢查關鍵指標
                key_indicators = ['short_rsi', 'medium_macd_signal', 'long_sma_20', 'trend_consistency']
                successful_key = 0
                
                for key_indicator in key_indicators:
                    if key_indicator in indicators:
                        successful_key += 1
                        print(f"   ✅ {key_indicator}: {indicators[key_indicator]}")
                    else:
                        print(f"   ❌ {key_indicator}: 未計算")
                
                indicator_results['key_indicators_success'] = successful_key
                indicator_results['key_indicators_total'] = len(key_indicators)
                indicator_results['success_rate'] = successful_key / len(key_indicators)
                
                print(f"   📊 總計算指標: {len(indicators)}個")
                print(f"   🎯 關鍵指標成功率: {successful_key}/{len(key_indicators)} ({indicator_results['success_rate']:.1%})")
                
            else:
                indicator_results['error'] = "無法獲取測試數據"
                
            return indicator_results
            
        except Exception as e:
            logger.error(f"❌ 技術指標測試失敗: {e}")
            return {'error': str(e)}
    
    async def _test_auto_update(self) -> Dict[str, Any]:
        """測試自動更新功能"""
        print("\n🔄 測試自動更新功能...")
        
        update_results = {}
        
        try:
            # 測試數據新鮮度檢查
            print("   🔍 測試數據新鮮度檢查...")
            
            for timeframe in ['1m', '5m', '1h']:
                needs_update, reason = self.manager._check_data_freshness("btctwd", timeframe)
                update_results[f'{timeframe}_freshness'] = {
                    'needs_update': needs_update,
                    'reason': reason
                }
                print(f"     ⏰ {timeframe}: {'需要更新' if needs_update else '數據新鮮'} - {reason}")
            
            # 測試數據確保功能
            print("   📥 測試數據確保功能...")
            ensure_results = await self.manager.ensure_historical_data("btctwd", ['1m', '5m', '1h'])
            
            update_results['ensure_results'] = ensure_results
            successful_updates = sum(1 for success in ensure_results.values() if success)
            
            print(f"   ✅ 成功更新: {successful_updates}/3 個時間框架")
            
            return update_results
            
        except Exception as e:
            logger.error(f"❌ 自動更新測試失敗: {e}")
            return {'error': str(e)}
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成驗證總結報告"""
        print("\n📋 生成驗證總結報告...")
        
        summary = {
            'overall_status': 'PASS',
            'critical_issues': [],
            'warnings': [],
            'recommendations': [],
            'data_readiness': True
        }
        
        try:
            # 檢查關鍵問題
            integrity = results.get('data_integrity', {})
            
            if integrity.get('duplicates', 0) > 0:
                summary['critical_issues'].append(f"發現{integrity['duplicates']}條重複記錄")
                summary['overall_status'] = 'FAIL'
                summary['data_readiness'] = False
            
            if integrity.get('null_values', 0) > 0:
                summary['critical_issues'].append(f"發現{integrity['null_values']}條NULL值記錄")
                summary['overall_status'] = 'FAIL'
                summary['data_readiness'] = False
            
            if integrity.get('invalid_prices', 0) > 0:
                summary['critical_issues'].append(f"發現{integrity['invalid_prices']}條異常價格記錄")
                summary['overall_status'] = 'FAIL'
                summary['data_readiness'] = False
            
            # 檢查警告
            continuity = results.get('continuity_check', {})
            for timeframe in ['1m', '5m', '1h']:
                continuity_info = continuity.get(f'{timeframe}_continuity', {})
                continuity_rate = continuity_info.get('continuity_rate', 1.0)
                
                if continuity_rate < 0.95:  # 95%連續性閾值
                    summary['warnings'].append(f"{timeframe}數據連續性僅{continuity_rate:.1%}")
                    if summary['overall_status'] == 'PASS':
                        summary['overall_status'] = 'WARNING'
            
            # 生成建議
            db_info = results.get('database_info', {})
            total_records = db_info.get('total_records', 0)
            
            if total_records < 1000:
                summary['recommendations'].append("建議增加歷史數據量以提高AI決策準確性")
            
            if summary['overall_status'] == 'PASS':
                summary['recommendations'].append("數據品質良好，可以開始實盤測試")
            
            # 輸出總結
            print(f"\n🎯 驗證總結:")
            print(f"   📊 整體狀態: {summary['overall_status']}")
            print(f"   📈 總記錄數: {total_records}")
            print(f"   🚀 實盤準備: {'✅ 就緒' if summary['data_readiness'] else '❌ 未就緒'}")
            
            if summary['critical_issues']:
                print(f"   🚨 關鍵問題:")
                for issue in summary['critical_issues']:
                    print(f"     - {issue}")
            
            if summary['warnings']:
                print(f"   ⚠️ 警告:")
                for warning in summary['warnings']:
                    print(f"     - {warning}")
            
            if summary['recommendations']:
                print(f"   💡 建議:")
                for rec in summary['recommendations']:
                    print(f"     - {rec}")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ 生成總結報告失敗: {e}")
            summary['error'] = str(e)
            summary['overall_status'] = 'ERROR'
            summary['data_readiness'] = False
            return summary
    
    async def close(self):
        """關閉連接"""
        await self.manager.close()


async def main():
    """主函數"""
    print("🚀 MAX歷史資料庫完整性和數據品質驗證")
    print("=" * 60)
    
    validator = HistoricalDataValidator()
    
    try:
        # 執行完整驗證
        results = await validator.run_full_validation()
        
        # 保存驗證結果
        import json
        with open('AImax/logs/data_validation_report.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 詳細報告已保存至: AImax/logs/data_validation_report.json")
        
        # 返回驗證狀態
        summary = results.get('summary', {})
        if summary.get('data_readiness', False):
            print("\n🎉 數據驗證通過！可以開始實盤測試！")
            return True
        else:
            print("\n⚠️ 數據驗證未通過，需要修復問題後再進行實盤測試")
            return False
            
    except Exception as e:
        logger.error(f"❌ 驗證過程發生錯誤: {e}")
        return False
        
    finally:
        await validator.close()


if __name__ == "__main__":
    # 創建日誌目錄
    os.makedirs('AImax/logs', exist_ok=True)
    
    # 運行驗證
    success = asyncio.run(main())
    
    if success:
        print("\n✅ 驗證完成，系統準備就緒！")
    else:
        print("\n❌ 驗證失敗，請檢查問題並修復")