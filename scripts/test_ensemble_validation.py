#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試集成評分器驗證功能
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
import numpy as np

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.ensemble_scorer import create_ensemble_scorer

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_test_data(num_samples: int = 50) -> tuple:
    """生成測試數據"""
    test_data = []
    ground_truth = []
    
    np.random.seed(42)  # 確保結果可重現
    
    for i in range(num_samples):
        # 生成模擬市場數據
        base_price = 1500000 + np.random.normal(0, 100000)
        price_change = np.random.normal(0, 2)  # -2% 到 +2% 的價格變化
        volume_ratio = max(0.5, np.random.lognormal(0, 0.3))  # 成交量比率
        
        # 生成AI格式化數據
        if price_change > 1:
            ai_data = "市場顯示上漲趨勢，技術指標看漲"
            true_signal = "BUY"
        elif price_change < -1:
            ai_data = "市場顯示下跌趨勢，技術指標看跌"
            true_signal = "SELL"
        else:
            ai_data = "市場橫盤整理，技術指標中性"
            true_signal = "HOLD"
        
        market_data = {
            'current_price': base_price,
            'price_change_1m': price_change,
            'volume_ratio': volume_ratio,
            'ai_formatted_data': ai_data
        }
        
        test_data.append(market_data)
        ground_truth.append(true_signal)
    
    return test_data, ground_truth

async def test_ensemble_validation():
    """測試集成評分器驗證功能"""
    print("🧪 測試集成評分器驗證功能...")
    print("=" * 60)
    
    # 創建集成評分器
    scorer = create_ensemble_scorer()
    
    # 生成測試數據
    print("\n📊 生成測試數據...")
    test_data, ground_truth = generate_test_data(50)
    print(f"   生成了 {len(test_data)} 個測試樣本")
    print(f"   真實標籤分佈: {dict(zip(*np.unique(ground_truth, return_counts=True)))}")
    
    # 執行集成評分器驗證
    print("\n🔍 執行集成評分器驗證...")
    validation_result = scorer.validate_ensemble(test_data, ground_truth)
    
    if not validation_result['success']:
        print(f"❌ 驗證失敗: {validation_result.get('error', 'Unknown error')}")
        return
    
    # 顯示驗證結果
    metrics = validation_result['validation_metrics']
    summary = validation_result['summary']
    
    print("\n📈 驗證結果摘要:")
    print("-" * 40)
    print(f"✅ 總體評分: {summary['overall_score']:.3f}")
    print(f"   預測成功率: {metrics['success_rate']:.2%}")
    print(f"   預測數量: {metrics['prediction_count']}")
    print(f"   模型一致性: {metrics['model_agreement']:.3f}")
    
    # 分數統計
    score_stats = metrics['score_statistics']
    print(f"\n📊 分數統計:")
    print(f"   平均分數: {score_stats['mean']:.1f}")
    print(f"   標準差: {score_stats['std']:.1f}")
    print(f"   分數範圍: {score_stats['min']:.1f} - {score_stats['max']:.1f}")
    print(f"   中位數: {score_stats['median']:.1f}")
    
    # 信號分佈
    signal_dist = metrics['signal_distribution']
    print(f"\n📡 信號分佈:")
    for signal, count in signal_dist['counts'].items():
        percentage = signal_dist['percentages'][signal]
        print(f"   {signal}: {count} ({percentage:.1%})")
    print(f"   信號多樣性: {signal_dist['diversity']} 種")
    
    # 信心度分析
    confidence_analysis = metrics['confidence_analysis']
    print(f"\n🎯 信心度分析:")
    conf_stats = confidence_analysis['statistics']
    print(f"   平均信心度: {conf_stats['mean']:.1f}%")
    print(f"   信心度標準差: {conf_stats['std']:.1f}%")
    
    conf_dist = confidence_analysis['percentages']
    print(f"   高信心度 (≥80%): {conf_dist['high_confidence']:.1%}")
    print(f"   中信心度 (60-80%): {conf_dist['medium_confidence']:.1%}")
    print(f"   低信心度 (<60%): {conf_dist['low_confidence']:.1%}")
    
    # 組件一致性
    component_consistency = metrics['component_consistency']
    print(f"\n🔧 組件一致性分析:")
    print(f"   整體一致性: {component_consistency['overall_consistency']:.3f}")
    
    for component, comp_metrics in component_consistency['component_metrics'].items():
        print(f"   {component}:")
        print(f"     平均分數: {comp_metrics['mean']:.1f}")
        print(f"     標準差: {comp_metrics['std']:.1f}")
        print(f"     一致性分數: {comp_metrics['consistency_score']:.3f}")
    
    # 組件間相關性
    correlations = component_consistency['correlations']
    if correlations:
        print(f"   組件間相關性:")
        for pair, corr in correlations.items():
            print(f"     {pair}: {corr:.3f}")
    
    # 權重有效性
    weight_effectiveness = metrics['weight_effectiveness']
    print(f"\n⚖️ 權重有效性分析:")
    print(f"   有效性分數: {weight_effectiveness['effectiveness_score']:.3f}")
    
    contributions = weight_effectiveness['component_contributions']
    for component, contrib in contributions.items():
        print(f"   {component}:")
        print(f"     當前權重: {contrib['weight']:.3f}")
        print(f"     與最終分數相關性: {contrib['correlation_with_final']:.3f}")
        print(f"     平均貢獻: {contrib['average_contribution']:.1f}")
    
    weight_balance = weight_effectiveness['weight_balance']
    print(f"   權重平衡性:")
    print(f"     標準化熵: {weight_balance['normalized_entropy']:.3f}")
    print(f"     平衡分數: {weight_balance['balance_score']:.3f}")
    
    # 預測穩定性
    stability = metrics['prediction_stability']
    if stability:
        print(f"\n📈 預測穩定性分析:")
        
        score_stability = stability['score_stability']
        print(f"   分數穩定性:")
        print(f"     平均變化: {score_stability['mean_change']:.1f}")
        print(f"     最大變化: {score_stability['max_change']:.1f}")
        print(f"     穩定性分數: {score_stability['stability_score']:.3f}")
        
        signal_stability = stability['signal_stability']
        print(f"   信號穩定性:")
        print(f"     信號變化次數: {signal_stability['change_count']}")
        print(f"     變化率: {signal_stability['change_rate']:.1%}")
        print(f"     穩定性分數: {signal_stability['stability_score']:.3f}")
        
        confidence_stability = stability['confidence_stability']
        print(f"   信心度穩定性:")
        print(f"     平均變化: {confidence_stability['mean_change']:.1f}%")
        print(f"     穩定性分數: {confidence_stability['stability_score']:.3f}")
    
    # 準確性指標 (如果有真實標籤)
    if 'accuracy_metrics' in metrics:
        accuracy = metrics['accuracy_metrics']
        print(f"\n🎯 準確性指標:")
        print(f"   總體準確率: {accuracy['accuracy']:.2%}")
        print(f"   正確預測數: {accuracy['correct_predictions']}")
        print(f"   總預測數: {accuracy['total_predictions']}")
        print(f"   宏平均F1分數: {accuracy['macro_f1']:.3f}")
        
        print(f"   各類別性能:")
        for label, metrics_data in accuracy['precision_recall'].items():
            print(f"     {label}:")
            print(f"       精確率: {metrics_data['precision']:.3f}")
            print(f"       召回率: {metrics_data['recall']:.3f}")
            print(f"       F1分數: {metrics_data['f1_score']:.3f}")
            print(f"       支持數: {metrics_data['support']}")
    
    # 權重優化建議
    weight_optimization = metrics['weight_optimization']
    if 'final_recommendation' in weight_optimization:
        final_rec = weight_optimization['final_recommendation']
        print(f"\n🔧 權重優化建議:")
        print(f"   建議信心度: {final_rec['confidence']:.3f}")
        print(f"   使用的優化方法數: {final_rec['optimization_methods_used']}")
        
        print(f"   當前權重:")
        for component, weight in final_rec['current_weights'].items():
            print(f"     {component}: {weight:.3f}")
        
        print(f"   建議權重:")
        for component, weight in final_rec['recommended_weights'].items():
            print(f"     {component}: {weight:.3f}")
        
        print(f"   權重變化:")
        for component, change in final_rec['weight_changes'].items():
            if abs(change) > 0.01:  # 只顯示顯著變化
                print(f"     {component}: {change:+.3f}")
    
    # 衝突解決機制評估
    conflict_resolution = metrics['conflict_resolution']
    if conflict_resolution:
        print(f"\n⚔️ 衝突解決機制評估:")
        print(f"   總預測數: {conflict_resolution['total_predictions']}")
        print(f"   衝突案例數: {conflict_resolution['conflict_cases']}")
        print(f"   解決有效性: {conflict_resolution['resolution_effectiveness']:.3f}")
        
        conflict_types = conflict_resolution['conflict_types']
        print(f"   衝突類型:")
        print(f"     高分歧: {conflict_types['high_disagreement']}")
        print(f"     混合信號: {conflict_types['mixed_signals']}")
        print(f"     低信心度: {conflict_types['low_confidence']}")
        
        if 'resolution_strategies' in conflict_resolution:
            strategies = conflict_resolution['resolution_strategies']
            print(f"   解決策略效果:")
            for strategy, data in strategies.items():
                if data['used'] > 0:
                    print(f"     {strategy}: 使用{data['used']}次, 有效率{data['effectiveness_rate']:.2%}")
    
    # 可靠性評估
    reliability = metrics['reliability_assessment']
    if reliability:
        print(f"\n🛡️ 可靠性評估:")
        print(f"   總體可靠性分數: {reliability['overall_score']:.3f}")
        print(f"   總體評估: {reliability['overall_assessment']}")
        print(f"   可靠性等級: {reliability['reliability_level']}")
        
        print(f"   各因子評分:")
        for factor, data in reliability['factor_scores'].items():
            print(f"     {factor}: {data['score']:.3f} ({data['assessment']})")
        
        print(f"   改進建議:")
        for rec in reliability['recommendations']:
            print(f"     - {rec}")
    
    # 系統優勢和弱點
    print(f"\n💪 系統優勢:")
    for strength in summary['strengths']:
        print(f"   ✅ {strength}")
    
    print(f"\n⚠️ 系統弱點:")
    for weakness in summary['weaknesses']:
        print(f"   ❌ {weakness}")
    
    print(f"\n🔧 改進建議:")
    for recommendation in summary['recommendations']:
        print(f"   💡 {recommendation}")
    
    # 測試權重優化功能
    print(f"\n🔧 測試權重優化功能...")
    if 'final_recommendation' in weight_optimization and weight_optimization['final_recommendation']['confidence'] > 0.5:
        new_weights = weight_optimization['final_recommendation']['recommended_weights']
        print(f"   嘗試應用優化權重...")
        
        if scorer.update_weights(new_weights):
            print(f"   ✅ 權重更新成功")
            
            # 重新驗證以查看改進效果
            print(f"   🔄 使用新權重重新驗證...")
            new_validation = scorer.validate_ensemble(test_data[:20], ground_truth[:20])  # 使用較小樣本快速測試
            
            if new_validation['success']:
                new_score = new_validation['summary']['overall_score']
                old_score = summary['overall_score']
                improvement = new_score - old_score
                
                print(f"   📊 權重優化效果:")
                print(f"     原始總體評分: {old_score:.3f}")
                print(f"     優化後評分: {new_score:.3f}")
                print(f"     改進幅度: {improvement:+.3f}")
                
                if improvement > 0:
                    print(f"   ✅ 權重優化有效，系統性能提升")
                else:
                    print(f"   ⚠️ 權重優化效果不明顯")
        else:
            print(f"   ❌ 權重更新失敗")
    else:
        print(f"   ⚠️ 權重優化建議信心度不足，跳過測試")
    
    print(f"\n🎯 集成評分器驗證測試完成！")
    print("=" * 60)
    
    return {
        'validation_successful': validation_result['success'],
        'overall_score': summary['overall_score'],
        'success_rate': metrics['success_rate'],
        'model_agreement': metrics['model_agreement'],
        'accuracy': metrics.get('accuracy_metrics', {}).get('accuracy', 0),
        'reliability_score': reliability.get('overall_score', 0) if reliability else 0
    }

if __name__ == "__main__":
    # 運行測試
    result = asyncio.run(test_ensemble_validation())
    
    # 輸出最終測試結果
    print(f"\n🏆 最終測試結果:")
    print(f"   驗證成功: {'✅' if result['validation_successful'] else '❌'}")
    print(f"   總體評分: {result['overall_score']:.3f}")
    print(f"   預測成功率: {result['success_rate']:.2%}")
    print(f"   模型一致性: {result['model_agreement']:.3f}")
    if result['accuracy'] > 0:
        print(f"   預測準確率: {result['accuracy']:.2%}")
    print(f"   可靠性分數: {result['reliability_score']:.3f}")
    
    # 評估系統健康度
    if result['overall_score'] > 0.8:
        health_status = "優秀"
    elif result['overall_score'] > 0.6:
        health_status = "良好"
    elif result['overall_score'] > 0.4:
        health_status = "一般"
    else:
        health_status = "需改進"
    
    print(f"   系統健康度: {health_status}")