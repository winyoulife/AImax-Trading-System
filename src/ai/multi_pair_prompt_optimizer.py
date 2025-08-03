#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易對AI提示詞優化器 - 優化五AI協作系統適應多交易對場景
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class MultiPairContext:
    """多交易對上下文信息"""
    total_pairs: int
    active_pairs: List[str]
    market_conditions: str  # 'bull', 'bear', 'sideways'
    correlation_matrix: Dict[str, Dict[str, float]]
    global_risk_level: float
    available_capital: float

class MultiPairPromptOptimizer:
    """多交易對AI提示詞優化器"""
    
    def __init__(self):
        # 交易對特性配置
        self.pair_characteristics = {
            'BTCTWD': {
                'volatility_level': 'medium',
                'liquidity': 'high',
                'correlation_leader': True,
                'market_cap_tier': 'tier1'
            },
            'ETHTWD': {
                'volatility_level': 'medium-high',
                'liquidity': 'high',
                'correlation_leader': False,
                'market_cap_tier': 'tier1'
            },
            'LTCTWD': {
                'volatility_level': 'medium',
                'liquidity': 'medium',
                'correlation_leader': False,
                'market_cap_tier': 'tier2'
            },
            'BCHTWD': {
                'volatility_level': 'high',
                'liquidity': 'medium',
                'correlation_leader': False,
                'market_cap_tier': 'tier2'
            }
        }
        
        # 多交易對分析重點
        self.multi_pair_focus_areas = {
            'correlation_analysis': '交易對間相關性分析',
            'cross_pair_signals': '跨交易對信號確認',
            'portfolio_risk': '組合風險評估',
            'resource_allocation': '資源分配優化',
            'execution_priority': '執行優先級排序'
        }
        
        logger.info("🎯 多交易對AI提示詞優化器初始化完成")
    
    def get_optimized_scanner_prompt(self, pair: str, market_data: Dict[str, Any], 
                                   multi_pair_context: MultiPairContext) -> str:
        """獲取優化的市場掃描員提示詞 - 多交易對版本"""
        
        pair_char = self.pair_characteristics.get(pair, {})
        correlation_info = self._get_correlation_info(pair, multi_pair_context)
        
        return f"""你是專業的多交易對市場掃描員，負責在多交易對環境中快速識別交易機會和市場信號。

🎯 多交易對掃描任務：
當前分析交易對: {pair}
總監控交易對: {multi_pair_context.total_pairs} 個 ({', '.join(multi_pair_context.active_pairs)})
全局市場條件: {multi_pair_context.market_conditions}
全局風險水平: {multi_pair_context.global_risk_level:.2f}

📊 {pair} 特性分析：
- 波動率等級: {pair_char.get('volatility_level', 'unknown')}
- 流動性水平: {pair_char.get('liquidity', 'unknown')}
- 市場領導性: {'是' if pair_char.get('correlation_leader', False) else '否'}
- 市場層級: {pair_char.get('market_cap_tier', 'unknown')}

🔗 相關性分析：
{correlation_info}

📈 當前市場數據：
- 當前價格: {market_data.get('current_price', 'N/A')} TWD
- 1分鐘變化: {market_data.get('price_change_1m', 'N/A')}%
- 5分鐘變化: {market_data.get('price_change_5m', 'N/A')}%
- 成交量比率: {market_data.get('volume_ratio', 'N/A')}x
- RSI: {market_data.get('rsi', 'N/A')}
- MACD: {market_data.get('macd', 'N/A')}
- 布林帶位置: {market_data.get('bollinger_position', 'N/A')}
- 波動率: {market_data.get('volatility', 'N/A')}

🎯 多交易對掃描重點：
1. 單一交易對信號強度評估
2. 跨交易對信號確認分析
3. 相關性影響評估
4. 全局市場環境適應性
5. 多交易對資源競爭考量

請提供多交易對環境下的掃描分析：

1. 單對信號評估 (強烈看漲/看漲/中性/看跌/強烈看跌)
2. 跨對信號確認 (確認/部分確認/無確認/矛盾)
3. 相關性影響 (正面/中性/負面)
4. 全局適應性 (高/中/低)
5. 資源競爭度 (高/中/低)
6. 多對環境建議 (優先BUY/BUY/HOLD/SELL/優先SELL)
7. 多對信心度 (0-100)

格式要求：
單對信號: [評估結果]
跨對確認: [確認狀態]
相關性影響: [影響評估]
全局適應性: [適應程度]
資源競爭: [競爭程度]
多對建議: [操作建議]
多對信心度: [數字]
"""
    
    def get_optimized_analyst_prompt(self, pair: str, market_data: Dict[str, Any],
                                   scanner_response: str, multi_pair_context: MultiPairContext) -> str:
        """獲取優化的深度分析師提示詞 - 多交易對版本"""
        
        pair_char = self.pair_characteristics.get(pair, {})
        correlation_analysis = self._get_detailed_correlation_analysis(pair, multi_pair_context)
        
        return f"""你是專業的多交易對深度技術分析師，擅長在多交易對環境中進行複雜的技術分析和市場結構分析。

🎯 多交易對分析環境：
當前分析: {pair}
組合環境: {multi_pair_context.total_pairs} 個交易對
市場狀態: {multi_pair_context.market_conditions}
可用資金: {multi_pair_context.available_capital:,.0f} TWD

📊 市場掃描員多交易對報告：
{scanner_response}

🔍 {pair} 深度特性：
- 技術分析複雜度: {self._get_analysis_complexity(pair_char)}
- 多時間框架重要性: {self._get_timeframe_importance(pair_char)}
- 技術指標敏感度: {self._get_indicator_sensitivity(pair_char)}

🔗 多交易對相關性深度分析：
{correlation_analysis}

📈 詳細技術數據：
- 當前價格: {market_data.get('current_price', 'N/A')} TWD
- RSI: {market_data.get('rsi', 'N/A')}
- MACD線: {market_data.get('macd', 'N/A')}
- MACD信號線: {market_data.get('macd_signal', 'N/A')}
- 布林帶上軌: {market_data.get('bollinger_upper', 'N/A')}
- 布林帶下軌: {market_data.get('bollinger_lower', 'N/A')}
- 布林帶位置: {market_data.get('bollinger_position', 'N/A')}
- SMA10: {market_data.get('sma_10', 'N/A')}
- SMA20: {market_data.get('sma_20', 'N/A')}
- EMA10: {market_data.get('ema_10', 'N/A')}
- EMA20: {market_data.get('ema_20', 'N/A')}

🎯 多交易對深度分析要求：
1. 單一交易對技術指標綜合分析
2. 多交易對技術指標比較分析
3. 跨交易對支撐阻力位關聯分析
4. 多交易對市場結構一致性分析
5. 組合技術形態識別
6. 多時間框架跨交易對確認
7. 多交易對技術面強弱排序
8. 組合風險技術面評估

請提供多交易對環境下的深度技術分析：

1. 單對技術評估 (強烈看漲/看漲/中性/看跌/強烈看跌)
2. 多對技術比較 (相對強勢/相對中性/相對弱勢)
3. 跨對技術確認 (強確認/弱確認/無確認/矛盾)
4. 組合技術風險 (低/中/高)
5. 技術優先級 (最高/高/中/低)
6. 多對技術建議 (強烈推薦/推薦/中性/不推薦/強烈不推薦)
7. 多對技術信心度 (0-100)

請提供詳細的多交易對技術分析報告。
"""
    
    def get_optimized_trend_prompt(self, pair: str, market_data: Dict[str, Any],
                                 scanner_response: str, multi_pair_context: MultiPairContext) -> str:
        """獲取優化的趨勢分析師提示詞 - 多交易對版本"""
        
        trend_leadership = self._analyze_trend_leadership(pair, multi_pair_context)
        
        return f"""你是專業的多交易對市場趨勢分析師，專注於在多交易對環境中識別和分析市場趨勢的方向和強度。

🎯 多交易對趨勢分析環境：
當前分析: {pair}
組合規模: {multi_pair_context.total_pairs} 個交易對
全局趨勢: {multi_pair_context.market_conditions}
趨勢領導性: {trend_leadership}

📊 市場掃描員趨勢初判：
{scanner_response}

🔍 多交易對趨勢相關數據：
- 價格趨勢斜率: {market_data.get('price_trend_slope', 'N/A')}
- 價格趨勢方向: {market_data.get('price_trend', 'N/A')}
- 成交量趨勢斜率: {market_data.get('volume_trend_slope', 'N/A')}
- 成交量趨勢方向: {market_data.get('volume_trend', 'N/A')}
- 波動率: {market_data.get('volatility', 'N/A')}
- 波動率水平: {market_data.get('volatility_level', 'N/A')}

🔗 多交易對趨勢關聯分析：
{self._get_trend_correlation_analysis(pair, multi_pair_context)}

🎯 多交易對趨勢分析重點：
1. 單一交易對趨勢識別和強度評估
2. 多交易對趨勢一致性分析
3. 趨勢領導-跟隨關係識別
4. 跨交易對趨勢確認信號
5. 組合趨勢風險評估
6. 多交易對趨勢交易機會排序

請進行多交易對環境下的趨勢分析：

1. 單對趨勢評估 (強烈上升/上升/橫盤/下降/強烈下降)
2. 趨勢強度等級 (極強/強/中/弱/極弱)
3. 多對趨勢一致性 (高度一致/部分一致/不一致/矛盾)
4. 趨勢領導地位 (領導者/跟隨者/獨立/滯後)
5. 跨對趨勢確認 (強確認/弱確認/無確認/反向)
6. 組合趨勢風險 (低/中/高)
7. 趨勢交易優先級 (最高/高/中/低)
8. 多對趨勢建議 (強烈順勢/順勢/觀望/逆勢/強烈逆勢)
9. 多對趨勢確信度 (0-100)

格式要求：
單對趨勢: [方向和強度]
趨勢一致性: [一致程度]
領導地位: [領導關係]
跨對確認: [確認狀態]
組合風險: [風險等級]
交易優先級: [優先級別]
多對建議: [操作建議]
趨勢確信度: [數字]
"""
    
    def get_optimized_risk_prompt(self, pair: str, market_data: Dict[str, Any],
                                scanner_response: str, analyst_response: str,
                                trend_response: str, multi_pair_context: MultiPairContext) -> str:
        """獲取優化的風險評估AI提示詞 - 多交易對版本"""
        
        portfolio_risk_factors = self._analyze_portfolio_risk_factors(pair, multi_pair_context)
        
        return f"""你是專業的多交易對交易風險評估專家，專門負責在多交易對環境中評估交易風險和制定風險控制策略。

🎯 多交易對風險評估環境：
當前評估: {pair}
組合規模: {multi_pair_context.total_pairs} 個交易對
全局風險: {multi_pair_context.global_risk_level:.2f}
可用資金: {multi_pair_context.available_capital:,.0f} TWD

📊 前序AI分析報告：
市場掃描: {scanner_response}
技術分析: {analyst_response}
趨勢分析: {trend_response}

🔍 多交易對風險因素分析：
{portfolio_risk_factors}

📈 風險評估數據：
- 當前價格: {market_data.get('current_price', 'N/A')} TWD
- 波動率: {market_data.get('volatility', 'N/A')}
- 流動性指標: {market_data.get('volume_ratio', 'N/A')}x
- 價差百分比: {market_data.get('spread_pct', 'N/A')}%

🎯 多交易對風險評估要求：
1. 單一交易對風險評估
2. 多交易對組合風險分析
3. 相關性風險評估
4. 流動性風險分析
5. 集中度風險評估
6. 資金分配風險評估
7. 執行風險評估
8. 系統性風險評估

請進行全面的多交易對風險評估：

1. 單對風險等級 (極低/低/中/高/極高)
2. 組合風險等級 (極低/低/中/高/極高)
3. 相關性風險 (低/中/高)
4. 流動性風險 (低/中/高)
5. 集中度風險 (低/中/高)
6. 資金分配風險 (低/中/高)
7. 建議倉位大小 (0-30%)
8. 建議止損位 (百分比)
9. 風險收益比 (比率)
10. 多對風險建議 (可接受/謹慎接受/不建議/強烈不建議)
11. 風險評估信心度 (0-100)

格式要求：
單對風險: [風險等級]
組合風險: [風險等級]
相關性風險: [風險程度]
流動性風險: [風險程度]
集中度風險: [風險程度]
資金風險: [風險程度]
建議倉位: [百分比]
建議止損: [百分比]
風險收益比: [比率]
風險建議: [建議結果]
風險信心度: [數字]
"""
    
    def get_optimized_decision_prompt(self, pair: str, market_data: Dict[str, Any],
                                    scanner_response: str, analyst_response: str,
                                    trend_response: str, risk_response: str,
                                    multi_pair_context: MultiPairContext) -> str:
        """獲取優化的最終決策者提示詞 - 多交易對版本"""
        
        decision_priority = self._calculate_decision_priority(pair, multi_pair_context)
        resource_competition = self._analyze_resource_competition(pair, multi_pair_context)
        
        return f"""你是多交易對環境下的最終交易決策制定者，負責綜合所有AI的分析結果，在多交易對競爭環境中做出最優的交易決策。

🎯 多交易對決策環境：
當前決策: {pair}
組合環境: {multi_pair_context.total_pairs} 個交易對競爭
決策優先級: {decision_priority}
資源競爭度: {resource_competition}
可用資金: {multi_pair_context.available_capital:,.0f} TWD

📊 五AI協作分析報告：
🔍 市場掃描: {scanner_response}
📈 技術分析: {analyst_response}
📊 趨勢分析: {trend_response}
⚠️ 風險評估: {risk_response}

🔗 多交易對決策考量：
{self._get_multi_pair_decision_factors(pair, multi_pair_context)}

🎯 多交易對決策原則：
1. 全局資源配置優化
2. 多交易對風險分散
3. 相關性風險控制
4. 執行優先級管理
5. 組合收益最大化
6. 動態風險調整

請做出多交易對環境下的最終決策：

1. 單對決策評估 (強烈BUY/BUY/HOLD/SELL/強烈SELL)
2. 多對環境適應性 (優秀/良好/一般/較差/不適合)
3. 資源分配建議 (優先分配/正常分配/延後分配/不分配)
4. 執行優先級 (最高/高/中/低/最低)
5. 建議倉位大小 (0-30%)
6. 建議止損位 (百分比)
7. 建議止盈位 (百分比)
8. 持有期預期 (短期/中期/長期)
9. 多對最終決策 (BUY/SELL/HOLD)
10. 決策信心度 (0-100)
11. 決策理由 (簡要說明)

格式要求：
單對評估: [決策評估]
環境適應: [適應程度]
資源分配: [分配建議]
執行優先級: [優先級別]
建議倉位: [百分比]
建議止損: [百分比]
建議止盈: [百分比]
持有期: [期限]
最終決策: [BUY/SELL/HOLD]
決策信心: [數字]
決策理由: [理由說明]
"""
    
    def _get_correlation_info(self, pair: str, context: MultiPairContext) -> str:
        """獲取相關性信息"""
        if not context.correlation_matrix or pair not in context.correlation_matrix:
            return "相關性數據不可用"
        
        correlations = context.correlation_matrix[pair]
        info_lines = []
        
        for other_pair, corr in correlations.items():
            if other_pair != pair:
                corr_level = self._classify_correlation(corr)
                info_lines.append(f"- 與{other_pair}: {corr:.2f} ({corr_level})")
        
        return "\\n".join(info_lines) if info_lines else "無其他交易對相關性數據"
    
    def _classify_correlation(self, correlation: float) -> str:
        """分類相關性強度"""
        abs_corr = abs(correlation)
        if abs_corr >= 0.8:
            return "強相關"
        elif abs_corr >= 0.5:
            return "中等相關"
        elif abs_corr >= 0.3:
            return "弱相關"
        else:
            return "無相關"
    
    def _get_detailed_correlation_analysis(self, pair: str, context: MultiPairContext) -> str:
        """獲取詳細相關性分析"""
        if not context.correlation_matrix or pair not in context.correlation_matrix:
            return "詳細相關性分析不可用"
        
        correlations = context.correlation_matrix[pair]
        analysis_lines = []
        
        # 分析相關性對技術分析的影響
        high_corr_pairs = [p for p, c in correlations.items() if p != pair and abs(c) >= 0.7]
        if high_corr_pairs:
            analysis_lines.append(f"高相關交易對: {', '.join(high_corr_pairs)}")
            analysis_lines.append("技術分析需考慮聯動效應")
        
        # 分析獨立性
        low_corr_pairs = [p for p, c in correlations.items() if p != pair and abs(c) < 0.3]
        if low_corr_pairs:
            analysis_lines.append(f"獨立性較強: {', '.join(low_corr_pairs)}")
            analysis_lines.append("可作為分散化配置選項")
        
        return "\\n".join(analysis_lines) if analysis_lines else "相關性分析完成"
    
    def _get_analysis_complexity(self, pair_char: Dict[str, Any]) -> str:
        """獲取分析複雜度"""
        volatility = pair_char.get('volatility_level', 'medium')
        if volatility == 'high':
            return "高複雜度"
        elif volatility == 'medium-high':
            return "中高複雜度"
        else:
            return "中等複雜度"
    
    def _get_timeframe_importance(self, pair_char: Dict[str, Any]) -> str:
        """獲取時間框架重要性"""
        if pair_char.get('correlation_leader', False):
            return "多時間框架關鍵"
        else:
            return "中短期框架重點"
    
    def _get_indicator_sensitivity(self, pair_char: Dict[str, Any]) -> str:
        """獲取指標敏感度"""
        volatility = pair_char.get('volatility_level', 'medium')
        if volatility == 'high':
            return "高敏感度"
        else:
            return "中等敏感度"
    
    def _analyze_trend_leadership(self, pair: str, context: MultiPairContext) -> str:
        """分析趨勢領導性"""
        pair_char = self.pair_characteristics.get(pair, {})
        if pair_char.get('correlation_leader', False):
            return "趨勢領導者"
        else:
            return "趨勢跟隨者"
    
    def _get_trend_correlation_analysis(self, pair: str, context: MultiPairContext) -> str:
        """獲取趨勢相關性分析"""
        return f"在{context.market_conditions}市場環境下，{pair}的趨勢分析需要考慮與其他{context.total_pairs-1}個交易對的聯動關係。"
    
    def _analyze_portfolio_risk_factors(self, pair: str, context: MultiPairContext) -> str:
        """分析組合風險因素"""
        risk_factors = []
        
        # 相關性風險
        if context.correlation_matrix and pair in context.correlation_matrix:
            high_corr_count = sum(1 for p, c in context.correlation_matrix[pair].items() 
                                if p != pair and abs(c) >= 0.7)
            if high_corr_count > 0:
                risk_factors.append(f"高相關性風險: {high_corr_count}個高相關交易對")
        
        # 集中度風險
        if context.total_pairs <= 2:
            risk_factors.append("集中度風險: 交易對數量較少")
        
        # 全局風險
        if context.global_risk_level > 0.7:
            risk_factors.append("全局風險偏高")
        
        return "\\n".join([f"- {factor}" for factor in risk_factors]) if risk_factors else "風險因素在可控範圍內"
    
    def _calculate_decision_priority(self, pair: str, context: MultiPairContext) -> str:
        """計算決策優先級"""
        pair_char = self.pair_characteristics.get(pair, {})
        
        # 基於市場層級和領導性計算優先級
        if pair_char.get('market_cap_tier') == 'tier1' and pair_char.get('correlation_leader', False):
            return "最高優先級"
        elif pair_char.get('market_cap_tier') == 'tier1':
            return "高優先級"
        else:
            return "中等優先級"
    
    def _analyze_resource_competition(self, pair: str, context: MultiPairContext) -> str:
        """分析資源競爭度"""
        if context.total_pairs <= 2:
            return "低競爭"
        elif context.total_pairs <= 4:
            return "中等競爭"
        else:
            return "高競爭"
    
    def _get_multi_pair_decision_factors(self, pair: str, context: MultiPairContext) -> str:
        """獲取多交易對決策因素"""
        factors = []
        
        # 資源分配因素
        capital_per_pair = context.available_capital / context.total_pairs
        factors.append(f"平均可用資金: {capital_per_pair:,.0f} TWD")
        
        # 相關性因素
        if context.correlation_matrix and pair in context.correlation_matrix:
            avg_corr = sum(abs(c) for p, c in context.correlation_matrix[pair].items() if p != pair) / max(1, context.total_pairs - 1)
            factors.append(f"平均相關性: {avg_corr:.2f}")
        
        # 市場環境因素
        factors.append(f"全局市場: {context.market_conditions}")
        
        return "\\n".join([f"- {factor}" for factor in factors])


# 創建全局優化器實例
def create_multi_pair_prompt_optimizer() -> MultiPairPromptOptimizer:
    """創建多交易對提示詞優化器實例"""
    return MultiPairPromptOptimizer()


# 測試代碼
if __name__ == "__main__":
    print("🧪 測試多交易對AI提示詞優化器...")
    
    optimizer = create_multi_pair_prompt_optimizer()
    
    # 測試上下文
    test_context = MultiPairContext(
        total_pairs=4,
        active_pairs=['BTCTWD', 'ETHTWD', 'LTCTWD', 'BCHTWD'],
        market_conditions='sideways',
        correlation_matrix={
            'BTCTWD': {'BTCTWD': 1.0, 'ETHTWD': 0.7, 'LTCTWD': 0.5, 'BCHTWD': 0.6},
            'ETHTWD': {'BTCTWD': 0.7, 'ETHTWD': 1.0, 'LTCTWD': 0.4, 'BCHTWD': 0.5}
        },
        global_risk_level=0.5,
        available_capital=100000.0
    )
    
    # 測試市場數據
    test_market_data = {
        'current_price': 3482629,
        'price_change_1m': 0.0,
        'price_change_5m': 0.07,
        'volume_ratio': 0.3,
        'rsi': 82.3,
        'volatility': 0.025
    }
    
    # 測試掃描員提示詞
    scanner_prompt = optimizer.get_optimized_scanner_prompt('BTCTWD', test_market_data, test_context)
    print("✅ 掃描員提示詞優化完成")
    
    print("🎉 多交易對AI提示詞優化器測試完成！")