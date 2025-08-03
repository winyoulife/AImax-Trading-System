#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試增強風險控制系統
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.trading.risk_manager import create_risk_manager, RiskLevel, RiskAction

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_enhanced_risk_control():
    """測試增強風險控制系統"""
    print("🧪 測試增強風險控制系統...")
    print("=" * 60)
    
    # 創建風險管理器
    risk_manager = create_risk_manager(100000.0)
    
    # 測試場景1：高信心度交易
    print("\n📊 測試場景1：高信心度交易")
    print("-" * 40)
    
    ai_decision_high_confidence = {
        'final_decision': 'BUY',
        'confidence': 0.85,
        'reasoning': '強烈看漲信號，多個指標確認'
    }
    
    market_data_normal = {
        'current_price': 1500000,
        'volatility_level': '中',
        'price_trend': '強勢上漲',
        'price_change_24h': 0.05
    }
    
    account_status_healthy = {
        'total_equity': 100000,
        'available_balance': 95000,
        'margin_used': 5000,
        'positions_count': 1
    }
    
    risk_assessment_1 = await risk_manager.assess_trade_risk(
        ai_decision_high_confidence, market_data_normal, account_status_healthy
    )
    
    print(f"✅ 高信心度交易結果:")
    print(f"   風險等級: {risk_assessment_1['overall_risk_level']}")
    print(f"   建議動作: {risk_assessment_1['recommended_action']}")
    print(f"   風險分數: {risk_assessment_1['risk_score']:.1f}")
    print(f"   是否批准: {risk_assessment_1['approved']}")
    print(f"   信心度調整: {risk_assessment_1['confidence_adjustment']['confidence_category']}")
    print(f"   智能倉位大小: {risk_assessment_1['intelligent_position_size']['size_ratio']:.2%}")
    
    if risk_assessment_1['dynamic_stops']['stop_loss']:
        stop_loss = risk_assessment_1['dynamic_stops']['stop_loss']
        print(f"   動態止損: {stop_loss['price']:.0f} ({stop_loss['ratio']:.2%})")
    
    # 測試場景2：低信心度交易
    print("\n📊 測試場景2：低信心度交易")
    print("-" * 40)
    
    ai_decision_low_confidence = {
        'final_decision': 'BUY',
        'confidence': 0.35,  # 低信心度
        'reasoning': '信號不明確，存在不確定性'
    }
    
    risk_assessment_2 = await risk_manager.assess_trade_risk(
        ai_decision_low_confidence, market_data_normal, account_status_healthy
    )
    
    print(f"✅ 低信心度交易結果:")
    print(f"   風險等級: {risk_assessment_2['overall_risk_level']}")
    print(f"   建議動作: {risk_assessment_2['recommended_action']}")
    print(f"   風險分數: {risk_assessment_2['risk_score']:.1f}")
    print(f"   是否批准: {risk_assessment_2['approved']}")
    print(f"   信心度調整: {risk_assessment_2['confidence_adjustment']['confidence_category']}")
    print(f"   智能倉位大小: {risk_assessment_2['intelligent_position_size']['size_ratio']:.2%}")
    
    if risk_assessment_2.get('violations'):
        print(f"   風險違規:")
        for violation in risk_assessment_2['violations']:
            print(f"     - {violation['message']}")
    
    # 測試場景3：高波動市場交易
    print("\n📊 測試場景3：高波動市場交易")
    print("-" * 40)
    
    market_data_high_volatility = {
        'current_price': 1500000,
        'volatility_level': '高',
        'price_trend': '震盪',
        'price_change_24h': 0.15  # 24小時變化15%
    }
    
    ai_decision_medium = {
        'final_decision': 'BUY',
        'confidence': 0.65,
        'reasoning': '中等信心度交易'
    }
    
    risk_assessment_3 = await risk_manager.assess_trade_risk(
        ai_decision_medium, market_data_high_volatility, account_status_healthy
    )
    
    print(f"✅ 高波動市場交易結果:")
    print(f"   風險等級: {risk_assessment_3['overall_risk_level']}")
    print(f"   建議動作: {risk_assessment_3['recommended_action']}")
    print(f"   風險分數: {risk_assessment_3['risk_score']:.1f}")
    print(f"   是否批准: {risk_assessment_3['approved']}")
    print(f"   異常檢測: {risk_assessment_3['anomaly_detection']['anomaly_type']}")
    print(f"   智能倉位大小: {risk_assessment_3['intelligent_position_size']['size_ratio']:.2%}")
    
    if risk_assessment_3['dynamic_stops']['stop_loss']:
        stop_loss = risk_assessment_3['dynamic_stops']['stop_loss']
        print(f"   動態止損: {stop_loss['price']:.0f} ({stop_loss['ratio']:.2%}, {stop_loss['type']})")
    
    # 測試場景4：賬戶虧損狀態
    print("\n📊 測試場景4：賬戶虧損狀態")
    print("-" * 40)
    
    account_status_loss = {
        'total_equity': 85000,  # 虧損15%
        'available_balance': 80000,
        'margin_used': 5000,
        'positions_count': 2
    }
    
    # 添加一些虧損交易歷史
    for i in range(3):
        risk_manager.add_trade_record({
            'pnl': -2000,
            'duration': 30,
            'status': 'closed'
        })
    
    risk_assessment_4 = await risk_manager.assess_trade_risk(
        ai_decision_medium, market_data_normal, account_status_loss
    )
    
    print(f"✅ 賬戶虧損狀態交易結果:")
    print(f"   風險等級: {risk_assessment_4['overall_risk_level']}")
    print(f"   建議動作: {risk_assessment_4['recommended_action']}")
    print(f"   風險分數: {risk_assessment_4['risk_score']:.1f}")
    print(f"   是否批准: {risk_assessment_4['approved']}")
    print(f"   當前回撤: {risk_assessment_4['risk_metrics']['current_drawdown']:.2%}")
    print(f"   智能倉位大小: {risk_assessment_4['intelligent_position_size']['size_ratio']:.2%}")
    
    if risk_assessment_4.get('violations'):
        print(f"   風險違規:")
        for violation in risk_assessment_4['violations']:
            print(f"     - {violation['message']}")
    
    # 測試場景5：異常交易檢測
    print("\n📊 測試場景5：異常交易檢測")
    print("-" * 40)
    
    # 模擬頻繁交易
    for i in range(12):
        risk_manager.add_trade_record({
            'pnl': -100,
            'duration': 5,
            'status': 'closed'
        })
    
    ai_decision_large = {
        'final_decision': 'BUY',
        'confidence': 0.25,  # 極低信心度但要大額交易
        'reasoning': '異常交易測試'
    }
    
    risk_assessment_5 = await risk_manager.assess_trade_risk(
        ai_decision_large, market_data_high_volatility, account_status_loss
    )
    
    print(f"✅ 異常交易檢測結果:")
    print(f"   風險等級: {risk_assessment_5['overall_risk_level']}")
    print(f"   建議動作: {risk_assessment_5['recommended_action']}")
    print(f"   風險分數: {risk_assessment_5['risk_score']:.1f}")
    print(f"   是否批准: {risk_assessment_5['approved']}")
    print(f"   異常檢測: {risk_assessment_5['anomaly_detection']['is_anomalous']}")
    print(f"   異常類型: {risk_assessment_5['anomaly_detection']['anomaly_type']}")
    print(f"   異常分數: {risk_assessment_5['anomaly_detection']['anomaly_score']:.2f}")
    
    if risk_assessment_5.get('violations'):
        print(f"   風險違規:")
        for violation in risk_assessment_5['violations']:
            print(f"     - {violation['message']}")
    
    # 測試動態風險參數調整
    print("\n📊 動態風險參數調整測試")
    print("-" * 40)
    
    print("調整前的動態參數:")
    for key, value in risk_manager.dynamic_risk_params.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.3f}")
        else:
            print(f"   {key}: {value}")
    
    # 獲取風險摘要
    print("\n📊 風險管理摘要")
    print("-" * 40)
    
    risk_summary = risk_manager.get_risk_summary()
    print(f"✅ 風險管理摘要:")
    print(f"   當前餘額: {risk_summary['current_balance']:,.0f}")
    print(f"   峰值餘額: {risk_summary['peak_balance']:,.0f}")
    print(f"   當前回撤: {risk_summary['current_drawdown']:.2%}")
    print(f"   日盈虧: {risk_summary['daily_pnl']:,.0f}")
    print(f"   勝率: {risk_summary['win_rate']:.1%}")
    print(f"   總警報數: {risk_summary['risk_stats']['total_alerts']}")
    print(f"   嚴重警報數: {risk_summary['risk_stats']['critical_alerts']}")
    print(f"   交易阻止數: {risk_summary['risk_stats']['trades_blocked']}")
    print(f"   當前風險分數: {risk_summary['risk_stats']['risk_score']:.1f}")
    
    # 測試結果統計
    print("\n📊 測試結果統計")
    print("-" * 40)
    
    test_results = [
        ("高信心度交易", risk_assessment_1['approved']),
        ("低信心度交易", risk_assessment_2['approved']),
        ("高波動市場交易", risk_assessment_3['approved']),
        ("賬戶虧損狀態", risk_assessment_4['approved']),
        ("異常交易檢測", risk_assessment_5['approved'])
    ]
    
    approved_count = sum(1 for _, approved in test_results if approved)
    total_tests = len(test_results)
    
    print(f"✅ 測試完成:")
    print(f"   總測試數: {total_tests}")
    print(f"   批准交易數: {approved_count}")
    print(f"   阻止交易數: {total_tests - approved_count}")
    print(f"   風險控制有效性: {(total_tests - approved_count) / total_tests * 100:.1f}%")
    
    for test_name, approved in test_results:
        status = "✅ 批准" if approved else "❌ 阻止"
        print(f"   {test_name}: {status}")
    
    print("\n🎯 增強風險控制系統測試完成！")
    print("=" * 60)
    
    return {
        'total_tests': total_tests,
        'approved_count': approved_count,
        'blocked_count': total_tests - approved_count,
        'risk_control_effectiveness': (total_tests - approved_count) / total_tests,
        'test_results': test_results,
        'risk_summary': risk_summary
    }

if __name__ == "__main__":
    # 運行測試
    result = asyncio.run(test_enhanced_risk_control())
    
    # 輸出最終結果
    print(f"\n🏆 最終測試結果:")
    print(f"   風險控制有效性: {result['risk_control_effectiveness']:.1%}")
    print(f"   系統健康度: {'優秀' if result['risk_control_effectiveness'] > 0.6 else '良好' if result['risk_control_effectiveness'] > 0.4 else '需改進'}")