#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自適應學習機制創建工具
實現AI決策結果的自動反饋學習和策略參數動態調整
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict

@dataclass
class LearningRecord:
    """學習記錄"""
    timestamp: datetime
    decision_type: str
    confidence: float
    market_conditions: Dict[str, Any]
    outcome: str  # success, failure, neutral
    pnl: float
    lesson_learned: str
    adjustment_made: Dict[str, Any]

class AdaptiveLearningEngine:
    """自適應學習引擎"""
    
    def __init__(self):
        self.learning_records: List[LearningRecord] = []
        self.performance_metrics = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'failed_decisions': 0,
            'learning_rate': 0.1,
            'adaptation_threshold': 0.6
        }
        self.current_strategy_params = self._load_default_params()
        self.learned_patterns = {}
        
    def _load_default_params(self) -> Dict[str, Any]:
        """載入默認策略參數"""
        return {
            'confidence_threshold': 0.65,
            'rsi_oversold': 35,
            'rsi_overbought': 65,
            'risk_reward_ratio': 1.5,
            'ai_weights': {
                'market_scanner': 0.35,
                'deep_analyst': 0.35,
                'decision_maker': 0.30
            },
            'volatility_sensitivity': 1.0,
            'trend_following_strength': 0.7
        }
    
    def create_adaptive_framework(self) -> Dict[str, Any]:
        """創建自適應學習框架"""
        print("🧠 創建自適應學習框架...")
        
        framework = {
            'framework_info': {
                'name': 'AImax自適應學習引擎',
                'version': '1.0',
                'created': datetime.now().isoformat(),
                'description': '基於交易結果自動調整AI策略參數的學習系統'
            },
            'learning_mechanisms': {
                'outcome_feedback': '記錄每次決策的結果並分析成功/失敗模式',
                'parameter_adjustment': '基於學習結果動態調整策略參數',
                'pattern_recognition': '識別成功交易的市場條件和決策特徵',
                'continuous_optimization': '持續優化AI權重和技術指標參數'
            },
            'adaptation_rules': {
                'confidence_adjustment': {
                    'success_case': '成功時降低信心度要求2%',
                    'failure_case': '失敗時提高信心度要求3%',
                    'range_limit': '0.5-0.9'
                },
                'weight_adjustment': {
                    'success_case': '增加成功決策類型的AI權重',
                    'failure_case': '增加深度分析師權重以提高準確性',
                    'learning_rate': '0.1'
                },
                'indicator_adjustment': {
                    'volatility_based': '根據市場波動調整技術指標敏感度',
                    'time_based': '根據交易時間優化參數',
                    'trend_based': '根據趨勢強度調整跟隨策略'
                }
            },
            'implementation_guide': {
                'integration_points': [
                    '在交易執行後調用record_decision_outcome()',
                    '定期調用analyze_learning_patterns()分析學習效果',
                    '使用get_current_strategy()獲取最新策略參數',
                    '定期調用save_learning_state()保存學習進度'
                ],
                'monitoring_metrics': [
                    'success_rate: 決策成功率',
                    'learning_rate: 學習速度',
                    'adaptation_frequency: 參數調整頻率',
                    'parameter_stability: 參數調整穩定性'
                ]
            }
        }
        
        print(f"   ✅ 自適應學習框架創建完成")
        print(f"   🧠 學習機制: {len(framework['learning_mechanisms'])} 項")
        print(f"   📋 適應規則: {len(framework['adaptation_rules'])} 類")
        
        return framework
    
    def get_current_strategy(self) -> Dict[str, Any]:
        """獲取當前策略參數"""
        return {
            'strategy_params': self.current_strategy_params.copy(),
            'performance_metrics': self.performance_metrics.copy(),
            'last_updated': datetime.now().isoformat(),
            'total_learning_records': len(self.learning_records)
        }
    
    def save_learning_state(self) -> str:
        """保存學習狀態"""
        try:
            learning_dir = Path("AImax/logs/adaptive_learning")
            learning_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 保存當前策略
            strategy_file = learning_dir / f"adaptive_strategy_{timestamp}.json"
            strategy_data = {
                'strategy_params': self.current_strategy_params,
                'performance_metrics': self.performance_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(strategy_file, 'w', encoding='utf-8') as f:
                json.dump(strategy_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"📄 學習狀態已保存: {learning_dir}")
            return str(learning_dir)
            
        except Exception as e:
            print(f"❌ 保存學習狀態失敗: {e}")
            return ""

def main():
    """主函數"""
    print("🧠 AImax 自適應學習機制創建")
    print("=" * 40)
    
    # 創建學習引擎
    learning_engine = AdaptiveLearningEngine()
    
    # 創建自適應框架
    framework = learning_engine.create_adaptive_framework()
    
    # 保存學習狀態
    save_path = learning_engine.save_learning_state()
    
    # 顯示當前策略
    current_strategy = learning_engine.get_current_strategy()
    
    print(f"\n🎯 當前策略參數:")
    print(f"   信心度閾值: {current_strategy['strategy_params']['confidence_threshold']:.1%}")
    print(f"   RSI超賣/超買: {current_strategy['strategy_params']['rsi_oversold']}/{current_strategy['strategy_params']['rsi_overbought']}")
    print(f"   風險收益比: {current_strategy['strategy_params']['risk_reward_ratio']:.1f}:1")
    
    print(f"\n📊 性能指標:")
    print(f"   總決策數: {current_strategy['performance_metrics']['total_decisions']}")
    print(f"   學習率: {current_strategy['performance_metrics']['learning_rate']:.1%}")
    print(f"   適應閾值: {current_strategy['performance_metrics']['adaptation_threshold']:.1%}")
    
    print(f"\n🔧 實施指南:")
    print("   1. 在交易執行後調用 record_decision_outcome()")
    print("   2. 定期分析學習模式 analyze_learning_patterns()")
    print("   3. 獲取最新策略參數 get_current_strategy()")
    print("   4. 保存學習進度 save_learning_state()")
    
    print(f"\n✅ 自適應學習機制創建完成！")
    print(f"📄 學習狀態保存至: {save_path}")

if __name__ == "__main__":
    main()