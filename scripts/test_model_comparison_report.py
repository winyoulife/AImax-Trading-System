#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試模型比較報告系統
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
import numpy as np
import json

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.model_validation_report import create_model_validation_report_generator

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_comprehensive_test_data(num_samples: int = 30) -> tuple:
    """生成綜合測試數據"""
    test_data = []
    ground_truth = []
    
    np.random.seed(42)  # 確保結果可重現
    
    for i in range(num_samples):
        # 生成多樣化的市場數據
        base_price = 1500000 + np.random.normal(0, 200000)
        price_change = np.random.normal(0, 3)  # 更大的價格變化範圍
        volume_ratio = max(0.3, np.random.lognormal(0, 0.5))  # 更大的成交量變化
        
        # 根據市場條件生成相應的AI數據和真實標籤
        if price_change > 2:
            ai_data = "強勢上漲信號，多項技術指標確認看漲趨勢"
            true_signal = "BUY"
        elif price_change > 0.5:
            ai_data = "溫和上漲信號，市場情緒偏樂觀"
            true_signal = "BUY" if np.random.random() > 0.3 else "HOLD"
        elif price_change < -2:
            ai_data = "強勢下跌信號，技術指標顯示看跌"
            true_signal = "SELL"
        elif price_change < -0.5:
            ai_data = "溫和下跌信號，市場情緒偏悲觀"
            true_signal = "SELL" if np.random.random() > 0.3 else "HOLD"
        else:
            ai_data = "市場橫盤整理，技術指標中性"
            true_signal = "HOLD"
        
        # 添加一些噪音使數據更真實
        if np.random.random() < 0.1:  # 10%的噪音
            true_signal = np.random.choice(['BUY', 'SELL', 'HOLD'])
        
        market_data = {
            'current_price': base_price,
            'price_change_1m': price_change,
            'volume_ratio': volume_ratio,
            'ai_formatted_data': ai_data,
            'volume': max(100, np.random.poisson(1000)),
            'timestamp': datetime.now()
        }
        
        test_data.append(market_data)
        ground_truth.append(true_signal)
    
    return test_data, ground_truth

async def test_model_comparison_report():
    """測試模型比較報告系統"""
    print("🧪 測試模型比較報告系統...")
    print("=" * 60)
    
    # 創建報告生成器
    print("\n📊 初始化報告生成器...")
    report_generator = create_model_validation_report_generator("AImax/reports")
    
    # 生成測試數據
    print("\n📊 生成測試數據...")
    test_data, ground_truth = generate_comprehensive_test_data(30)
    print(f"   生成了 {len(test_data)} 個測試樣本")
    print(f"   真實標籤分佈: {dict(zip(*np.unique(ground_truth, return_counts=True)))}")
    
    # 顯示部分測試數據
    print(f"\n📋 測試數據樣本:")
    for i in range(3):
        data = test_data[i]
        truth = ground_truth[i]
        print(f"   樣本 {i+1}: 價格變化 {data['price_change_1m']:+.2f}%, 真實標籤 {truth}")
    
    # 執行模型驗證和比較
    print(f"\n🔍 執行模型驗證和比較...")
    validation_result = await report_generator.validate_all_models(test_data, ground_truth)
    
    if not validation_result['success']:
        print(f"❌ 模型驗證失敗: {validation_result.get('error', 'Unknown error')}")
        return {
            'test_successful': False,
            'models_validated': 0,
            'best_model': 'none',
            'average_accuracy': 0.0,
            'reports_saved': 0,
            'test_success_rate': 0.0,
            'system_health': '失敗'
        }
    
    print(f"✅ 模型驗證成功")
    
    # 顯示驗證結果摘要
    print(f"\n📈 驗證結果摘要:")
    print("-" * 40)
    models_validated = validation_result['models_validated']
    print(f"   成功驗證的模型數: {len(models_validated)}")
    print(f"   驗證的模型: {', '.join(models_validated)}")
    
    # 顯示比較分析結果
    comparison_analysis = validation_result['comparison_analysis']
    print(f"\n🏆 模型比較分析:")
    print("-" * 40)
    print(f"   最佳綜合模型: {comparison_analysis.best_overall_model}")
    print(f"   最佳準確率模型: {comparison_analysis.best_accuracy_model}")
    print(f"   最佳穩定性模型: {comparison_analysis.best_stability_model}")
    print(f"   最佳速度模型: {comparison_analysis.best_speed_model}")
    
    # 顯示模型排名
    print(f"\n📊 模型排名:")
    model_rankings = comparison_analysis.model_rankings
    for model, rank in sorted(model_rankings.items(), key=lambda x: x[1]):
        print(f"   第 {rank} 名: {model}")
    
    # 顯示性能矩陣
    print(f"\n📋 性能矩陣:")
    performance_matrix = comparison_analysis.performance_matrix
    
    # 創建表格標題
    metrics = ['accuracy', 'f1_score', 'confidence_avg', 'stability_score', 'success_rate', 'overall_score']
    print(f"   {'模型名稱':<20} " + " ".join([f"{m:<12}" for m in metrics]))
    print(f"   {'-'*20} " + " ".join([f"{'-'*12}" for _ in metrics]))
    
    # 顯示每個模型的性能數據
    for model_name, model_data in performance_matrix.items():
        row = f"   {model_name:<20}"
        for metric in metrics:
            value = model_data.get(metric, 0)
            if metric in ['accuracy', 'f1_score', 'confidence_avg', 'stability_score', 'success_rate', 'overall_score']:
                row += f" {value:<12.3f}"
            else:
                row += f" {value:<12.2f}"
        print(row)
    
    # 顯示建議
    print(f"\n💡 模型選擇建議:")
    recommendations = comparison_analysis.recommendations
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    # 顯示比較摘要
    print(f"\n📝 比較摘要:")
    print(f"   {comparison_analysis.comparison_summary}")
    
    # 顯示統一報告的關鍵信息
    unified_report = validation_result['unified_report']
    print(f"\n📊 統一報告摘要:")
    print("-" * 40)
    
    exec_summary = unified_report['executive_summary']
    print(f"   報告生成時間: {unified_report['report_metadata']['generated_at']}")
    print(f"   評估模型數: {exec_summary['model_count']}")
    print(f"   平均準確率: {exec_summary['average_accuracy']:.2%}")
    print(f"   主要建議: {exec_summary['top_recommendation']}")
    
    # 顯示統計摘要
    if 'statistical_summary' in unified_report:
        stats = unified_report['statistical_summary']
        print(f"\n📈 統計摘要:")
        
        if 'accuracy_stats' in stats:
            acc_stats = stats['accuracy_stats']
            print(f"   準確率統計:")
            print(f"     平均值: {acc_stats['mean']:.3f}")
            print(f"     標準差: {acc_stats['std']:.3f}")
            print(f"     範圍: {acc_stats['min']:.3f} - {acc_stats['max']:.3f}")
        
        if 'performance_stats' in stats:
            perf_stats = stats['performance_stats']
            print(f"   性能統計:")
            print(f"     平均處理時間: {perf_stats['avg_processing_time']:.3f}秒")
            print(f"     最快模型: {perf_stats['fastest_model']}")
            print(f"     最慢模型: {perf_stats['slowest_model']}")
    
    # 顯示詳細驗證結果
    print(f"\n🔍 詳細驗證結果:")
    detailed_results = unified_report['detailed_results']
    
    for model_name, details in detailed_results.items():
        print(f"\n   📊 {model_name}:")
        print(f"     模型類型: {details['model_type']}")
        
        metrics = details['metrics']
        print(f"     性能指標:")
        print(f"       準確率: {metrics.get('accuracy', 0):.3f}")
        print(f"       F1分數: {metrics.get('f1_score', 0):.3f}")
        print(f"       平均信心度: {metrics.get('confidence_avg', 0):.3f}")
        print(f"       穩定性分數: {metrics.get('stability_score', 0):.3f}")
        print(f"       成功率: {metrics.get('success_rate', 0):.3f}")
        
        processing_info = details['processing_info']
        print(f"     處理信息:")
        print(f"       處理時間: {processing_info['processing_time']:.3f}秒")
        print(f"       預測數量: {processing_info['predictions_count']}")
        print(f"       平均信心度: {processing_info['average_confidence']:.3f}")
        
        # 顯示預測分佈
        if 'prediction_distribution' in metrics:
            pred_dist = metrics['prediction_distribution']
            print(f"     預測分佈: {pred_dist}")
    
    # 顯示模型選擇指南
    if 'recommendations' in unified_report and 'model_selection_guide' in unified_report['recommendations']:
        guide = unified_report['recommendations']['model_selection_guide']
        print(f"\n🎯 模型選擇指南:")
        for scenario, recommendation in guide.items():
            print(f"   {scenario}: {recommendation}")
    
    # 顯示優化建議
    if 'recommendations' in unified_report and 'optimization_suggestions' in unified_report['recommendations']:
        opt_suggestions = unified_report['recommendations']['optimization_suggestions']
        if opt_suggestions:
            print(f"\n🔧 優化建議:")
            for i, suggestion in enumerate(opt_suggestions, 1):
                print(f"   {i}. {suggestion}")
    
    # 保存報告
    print(f"\n💾 保存報告...")
    saved_files = report_generator.save_report(unified_report)
    
    if 'error' not in saved_files:
        print(f"✅ 報告保存成功:")
        for format_type, file_path in saved_files.items():
            print(f"   {format_type.upper()}: {file_path}")
    else:
        print(f"❌ 報告保存失敗: {saved_files['error']}")
    
    # 測試模型性能歷史功能
    print(f"\n📚 測試模型性能歷史...")
    history = report_generator.get_model_performance_history()
    
    if 'error' not in history:
        print(f"✅ 成功獲取 {len(history)} 個模型的性能歷史")
        for model_name in history.keys():
            print(f"   - {model_name}")
    else:
        print(f"❌ 獲取歷史失敗: {history['error']}")
    
    # 測試圖表數據生成
    if 'charts' in unified_report and unified_report['charts']:
        charts = unified_report['charts']
        print(f"\n📊 圖表數據生成:")
        print(f"   可用圖表類型: {list(charts.keys())}")
        
        if 'radar_chart' in charts:
            print(f"   雷達圖數據: {len(charts['radar_chart'])} 個模型")
        
        if 'bar_chart' in charts:
            print(f"   柱狀圖數據: {len(charts['bar_chart'])} 個指標")
    
    # 計算測試成功率
    print(f"\n🎯 測試結果統計:")
    print("-" * 40)
    
    total_tests = 8  # 總測試項目數
    passed_tests = 0
    
    # 檢查各項測試結果
    test_results = [
        ("模型驗證", validation_result['success']),
        ("比較分析", len(comparison_analysis.model_rankings) > 0),
        ("統一報告生成", 'executive_summary' in unified_report),
        ("性能矩陣", len(performance_matrix) > 0),
        ("建議生成", len(recommendations) > 0),
        ("統計摘要", 'statistical_summary' in unified_report),
        ("報告保存", 'error' not in saved_files),
        ("歷史記錄", 'error' not in history)
    ]
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
        if result:
            passed_tests += 1
    
    success_rate = passed_tests / total_tests
    print(f"\n📊 測試成功率: {success_rate:.1%} ({passed_tests}/{total_tests})")
    
    # 系統健康度評估
    if success_rate >= 0.9:
        health_status = "優秀"
    elif success_rate >= 0.7:
        health_status = "良好"
    elif success_rate >= 0.5:
        health_status = "一般"
    else:
        health_status = "需改進"
    
    print(f"   系統健康度: {health_status}")
    
    print(f"\n🎯 模型比較報告系統測試完成！")
    print("=" * 60)
    
    return {
        'test_successful': validation_result['success'],
        'models_validated': len(models_validated),
        'best_model': comparison_analysis.best_overall_model,
        'average_accuracy': exec_summary['average_accuracy'],
        'reports_saved': len(saved_files),
        'test_success_rate': success_rate,
        'system_health': health_status
    }

if __name__ == "__main__":
    # 運行測試
    result = asyncio.run(test_model_comparison_report())
    
    # 輸出最終測試結果
    print(f"\n🏆 最終測試結果:")
    print(f"   測試成功: {'✅' if result['test_successful'] else '❌'}")
    print(f"   驗證模型數: {result['models_validated']}")
    print(f"   最佳模型: {result['best_model']}")
    print(f"   平均準確率: {result['average_accuracy']:.2%}")
    print(f"   報告保存數: {result['reports_saved']}")
    print(f"   測試成功率: {result['test_success_rate']:.1%}")
    print(f"   系統健康度: {result['system_health']}")