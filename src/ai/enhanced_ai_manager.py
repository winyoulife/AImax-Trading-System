#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強AI協作管理器 - 五AI超智能協作系統
支持多交易對的專業AI分工協作
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

import ollama

try:
    from .multi_pair_prompt_optimizer import create_multi_pair_prompt_optimizer, MultiPairContext
except ImportError:
    from multi_pair_prompt_optimizer import create_multi_pair_prompt_optimizer, MultiPairContext

logger = logging.getLogger(__name__)

@dataclass
class EnhancedAIResponse:
    """增強AI回應數據結構"""
    ai_role: str
    model_name: str
    response: str
    confidence: float
    processing_time: float
    timestamp: datetime
    success: bool
    pair: str  # 新增：交易對
    risk_score: float = 0.0  # 新增：風險評分
    error_message: Optional[str] = None

@dataclass
class MultiPairDecision:
    """多交易對協作決策結果"""
    pair: str
    final_decision: str  # BUY, SELL, HOLD
    confidence: float
    consensus_level: float
    ai_responses: List[EnhancedAIResponse]
    reasoning: str
    risk_level: str
    risk_score: float  # 新增：數值化風險評分
    position_size: float  # 新增：建議倉位大小
    timestamp: datetime

class EnhancedAIManager:
    """增強AI協作管理器 - 五AI系統"""
    
    def __init__(self, config_path: str = "config/ai_models.json"):
        self.config_path = Path(config_path)
        self.ollama_client = ollama.Client()
        
        # 五AI模型配置
        self.ai_models = {
            "market_scanner": {
                "model_name": "llama2:7b",
                "role": "快速市場信號識別",
                "weight": 0.15,
                "max_tokens": 300,
                "temperature": 0.3
            },
            "deep_analyst": {
                "model_name": "falcon:7b", 
                "role": "複雜技術分析專家",
                "weight": 0.25,
                "max_tokens": 500,
                "temperature": 0.2
            },
            "trend_analyst": {
                "model_name": "qwen:7b",
                "role": "市場趨勢判斷專家", 
                "weight": 0.20,
                "max_tokens": 400,
                "temperature": 0.25
            },
            "risk_assessor": {
                "model_name": "mistral:7b",
                "role": "實時風險控制專家",
                "weight": 0.25,
                "max_tokens": 400,
                "temperature": 0.1
            },
            "decision_maker": {
                "model_name": "qwen:7b",
                "role": "綜合決策制定者",
                "weight": 0.15,
                "max_tokens": 300,
                "temperature": 0.15
            }
        }
        
        # 多交易對設置
        self.supported_pairs = ['BTCTWD', 'ETHTWD', 'LTCTWD', 'BCHTWD']
        self.pair_specific_configs = {}
        
        # 多交易對提示詞優化器 ⭐ 新增
        self.prompt_optimizer = create_multi_pair_prompt_optimizer()
        
        # 性能統計
        self.performance_stats = {
            "total_decisions": 0,
            "successful_decisions": 0,
            "average_processing_time": 0.0,
            "ai_availability": {ai: True for ai in self.ai_models.keys()},
            "pair_stats": {pair: {"decisions": 0, "success_rate": 0.0} 
                          for pair in self.supported_pairs}
        }
        
        logger.info("🧠 增強AI協作管理器初始化完成 (五AI系統)")
    
    async def analyze_multi_pair_market(self, 
                                      multi_pair_data: Dict[str, Dict[str, Any]]) -> Dict[str, MultiPairDecision]:
        """
        多交易對協作分析 - 使用優化的多交易對提示詞
        
        Args:
            multi_pair_data: {pair: market_data} 格式的多交易對數據
            
        Returns:
            Dict[str, MultiPairDecision]: 每個交易對的決策結果
        """
        logger.info(f"🚀 開始五AI多交易對協作分析: {len(multi_pair_data)} 個交易對")
        
        # 創建多交易對上下文 ⭐ 新增
        multi_pair_context = self._create_multi_pair_context(multi_pair_data)
        
        decisions = {}
        
        # 並行分析所有交易對
        tasks = []
        for pair, market_data in multi_pair_data.items():
            if pair in self.supported_pairs:
                task = self._analyze_single_pair_with_context(pair, market_data, multi_pair_context)
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        for i, result in enumerate(results):
            pair = list(multi_pair_data.keys())[i]
            if isinstance(result, Exception):
                logger.error(f"❌ {pair} 分析失敗: {result}")
                decisions[pair] = self._create_fallback_decision(pair, str(result))
            else:
                decisions[pair] = result
        
        logger.info(f"✅ 多交易對分析完成: {len(decisions)} 個決策")
        return decisions
    
    async def _analyze_single_pair(self, pair: str, market_data: Dict[str, Any]) -> MultiPairDecision:
        """分析單個交易對"""
        start_time = datetime.now()
        
        try:
            logger.info(f"📊 開始分析 {pair}")
            
            # 階段1: 市場掃描員 (LLaMA 2:7B)
            scanner_response = await self._run_market_scanner(pair, market_data)
            
            # 階段2: 深度分析師 (Falcon 7B) 
            analyst_response = await self._run_deep_analyst(pair, market_data, scanner_response)
            
            # 階段3: 趋势分析師 (Qwen 7B)
            trend_response = await self._run_trend_analyst(pair, market_data, scanner_response)
            
            # 階段4: 風險評估AI (Mistral 7B) ⭐ 新增
            risk_response = await self._run_risk_assessor(pair, market_data, 
                                                        scanner_response, analyst_response, trend_response)
            
            # 階段5: 最終決策者 (Qwen 7B)
            decision_response = await self._run_decision_maker(pair, market_data,
                                                             scanner_response, analyst_response, 
                                                             trend_response, risk_response)
            
            # 綜合所有AI的回應
            ai_responses = [scanner_response, analyst_response, trend_response, 
                          risk_response, decision_response]
            
            # 生成最終協作決策
            collaborative_decision = self._synthesize_multi_pair_decision(pair, ai_responses)
            
            # 更新性能統計
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_stats(pair, collaborative_decision, processing_time)
            
            logger.info(f"✅ {pair} 分析完成: {collaborative_decision.final_decision} "
                       f"(信心度: {collaborative_decision.confidence:.2f})")
            
            return collaborative_decision
            
        except Exception as e:
            logger.error(f"❌ {pair} 分析失敗: {e}")
            return self._create_fallback_decision(pair, str(e))
    
    async def _run_market_scanner(self, pair: str, market_data: Dict[str, Any]) -> EnhancedAIResponse:
        """運行市場掃描員 (LLaMA 2:7B)"""
        start_time = datetime.now()
        
        try:
            model_config = self.ai_models["market_scanner"]
            
            prompt = self._build_scanner_prompt(pair, market_data)
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=self._get_scanner_system_prompt(),
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return EnhancedAIResponse(
                ai_role="market_scanner",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True,
                pair=pair
            )
            
        except Exception as e:
            logger.error(f"❌ {pair} 市場掃描員執行失敗: {e}")
            return self._create_error_response("market_scanner", pair, str(e))
    
    async def _run_deep_analyst(self, pair: str, market_data: Dict[str, Any], 
                              scanner_response: EnhancedAIResponse) -> EnhancedAIResponse:
        """運行深度分析師 (Falcon 7B)"""
        start_time = datetime.now()
        
        try:
            model_config = self.ai_models["deep_analyst"]
            
            prompt = self._build_analyst_prompt(pair, market_data, scanner_response)
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=self._get_analyst_system_prompt(),
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return EnhancedAIResponse(
                ai_role="deep_analyst",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True,
                pair=pair
            )
            
        except Exception as e:
            logger.error(f"❌ {pair} 深度分析師執行失敗: {e}")
            return self._create_error_response("deep_analyst", pair, str(e))
    
    async def _run_trend_analyst(self, pair: str, market_data: Dict[str, Any],
                               scanner_response: EnhancedAIResponse) -> EnhancedAIResponse:
        """運行趨勢分析師 (Qwen 7B)"""
        start_time = datetime.now()
        
        try:
            model_config = self.ai_models["trend_analyst"]
            
            prompt = self._build_trend_prompt(pair, market_data, scanner_response)
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=self._get_trend_system_prompt(),
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return EnhancedAIResponse(
                ai_role="trend_analyst",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True,
                pair=pair
            )
            
        except Exception as e:
            logger.error(f"❌ {pair} 趨勢分析師執行失敗: {e}")
            return self._create_error_response("trend_analyst", pair, str(e))
    
    async def _run_risk_assessor(self, pair: str, market_data: Dict[str, Any],
                               scanner_response: EnhancedAIResponse,
                               analyst_response: EnhancedAIResponse,
                               trend_response: EnhancedAIResponse) -> EnhancedAIResponse:
        """運行風險評估AI (Mistral 7B) ⭐ 新增核心功能"""
        start_time = datetime.now()
        
        try:
            model_config = self.ai_models["risk_assessor"]
            
            prompt = self._build_risk_assessment_prompt(pair, market_data, 
                                                      scanner_response, analyst_response, trend_response)
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=self._get_risk_assessor_system_prompt(),
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            risk_score = self._extract_risk_score(response)
            
            return EnhancedAIResponse(
                ai_role="risk_assessor",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True,
                pair=pair,
                risk_score=risk_score
            )
            
        except Exception as e:
            logger.error(f"❌ {pair} 風險評估AI執行失敗: {e}")
            return self._create_error_response("risk_assessor", pair, str(e))
    
    async def _run_decision_maker(self, pair: str, market_data: Dict[str, Any],
                                scanner_response: EnhancedAIResponse,
                                analyst_response: EnhancedAIResponse,
                                trend_response: EnhancedAIResponse,
                                risk_response: EnhancedAIResponse) -> EnhancedAIResponse:
        """運行最終決策者 (Qwen 7B)"""
        start_time = datetime.now()
        
        try:
            model_config = self.ai_models["decision_maker"]
            
            prompt = self._build_final_decision_prompt(pair, market_data,
                                                     scanner_response, analyst_response,
                                                     trend_response, risk_response)
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=self._get_decision_maker_system_prompt(),
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return EnhancedAIResponse(
                ai_role="decision_maker",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True,
                pair=pair
            )
            
        except Exception as e:
            logger.error(f"❌ {pair} 最終決策者執行失敗: {e}")
            return self._create_error_response("decision_maker", pair, str(e)) 
   
    async def _call_ai_model(self, model_name: str, system_prompt: str, 
                           user_prompt: str, max_tokens: int, temperature: float) -> str:
        """調用AI模型"""
        try:
            response = self.ollama_client.chat(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9
                }
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"❌ AI模型調用失敗 ({model_name}): {e}")
            raise
    
    def _get_scanner_system_prompt(self) -> str:
        """市場掃描員系統提示詞"""
        return """你是專業的加密貨幣市場掃描員，負責快速識別交易機會和市場信號。

你的職責：
1. 快速掃描市場數據，識別關鍵信號
2. 評估短期交易機會
3. 提供初步的市場方向判斷
4. 標記需要深度分析的重要信號

特點：
- 反應迅速，專注於即時信號
- 優先考慮技術指標組合
- 注意成交量和價格的配合
- 提供明確的數字化評估"""
    
    def _get_analyst_system_prompt(self) -> str:
        """深度分析師系統提示詞"""
        return """你是專業的加密貨幣深度技術分析師，擅長複雜的技術分析和市場結構分析。

你的職責：
1. 進行深度技術指標分析
2. 識別支撐阻力位和關鍵價位
3. 分析市場結構和形態
4. 評估技術面的強弱程度

特點：
- 分析深入，邏輯嚴謹
- 擅長多時間框架分析
- 重視技術指標的背離和確認
- 提供詳細的技術分析報告"""
    
    def _get_trend_system_prompt(self) -> str:
        """趨勢分析師系統提示詞"""
        return """你是專業的市場趨勢分析師，專注於識別和分析市場趨勢的方向和強度。

你的職責：
1. 判斷主要趨勢方向和強度
2. 識別趨勢轉折點和延續信號
3. 分析趨勢的可持續性
4. 評估趨勢中的回調和反彈機會

特點：
- 專注於趨勢識別和跟蹤
- 善於發現趨勢早期信號
- 重視趨勢的確認和驗證
- 提供趨勢強度的量化評估"""
    
    def _get_risk_assessor_system_prompt(self) -> str:
        """風險評估AI系統提示詞 ⭐ 核心新功能"""
        return """你是專業的交易風險評估專家，專門負責評估交易風險和制定風險控制策略。

你的職責：
1. 評估當前市場條件下的交易風險
2. 分析潛在的風險因素和風險點
3. 計算風險收益比和最大可接受損失
4. 提供風險控制建議和止損策略
5. 評估倉位大小和資金管理建議

風險評估要素：
- 市場波動率風險
- 流動性風險  
- 技術面風險
- 資金管理風險
- 系統性風險

特點：
- 保守謹慎，風險優先
- 量化風險評估
- 提供具體的風險控制措施
- 重視資金保護和風險管理"""
    
    def _get_decision_maker_system_prompt(self) -> str:
        """最終決策者系統提示詞"""
        return """你是最終交易決策制定者，負責綜合所有AI的分析結果，做出最終的交易決策。

你的職責：
1. 綜合市場掃描、技術分析、趨勢分析和風險評估
2. 權衡機會與風險，做出最終決策
3. 確定具體的交易參數（倉位、止損、目標）
4. 提供清晰的決策理由和執行計劃

決策原則：
- 風險控制優先於收益追求
- 基於數據和邏輯，避免情緒化決策
- 考慮多時間框架的一致性
- 確保決策的可執行性

特點：
- 綜合性強，決策明確
- 平衡風險與收益
- 提供具體的執行建議
- 決策邏輯清晰透明"""
    
    def _build_scanner_prompt(self, pair: str, market_data: Dict[str, Any]) -> str:
        """構建市場掃描員提示詞"""
        return f"""
交易對: {pair}

當前市場數據：
- 當前價格: {market_data.get('current_price', 'N/A')} TWD
- 1分鐘變化: {market_data.get('price_change_1m', 'N/A')}%
- 5分鐘變化: {market_data.get('price_change_5m', 'N/A')}%
- 15分鐘變化: {market_data.get('price_change_15m', 'N/A')}%
- 成交量比率: {market_data.get('volume_ratio', 'N/A')}x
- RSI: {market_data.get('rsi', 'N/A')}
- MACD: {market_data.get('macd', 'N/A')}
- 布林帶位置: {market_data.get('bollinger_position', 'N/A')}

請進行快速市場掃描分析：

1. 市場信號評估 (強烈看漲/看漲/中性/看跌/強烈看跌)
2. 關鍵技術信號 (列出2-3個最重要的信號)
3. 交易機會等級 (高/中/低)
4. 緊急程度 (立即/短期/觀察)
5. 初步建議 (BUY/SELL/HOLD)
6. 信心度 (0-100)

格式要求：
市場信號: [評估結果]
關鍵信號: [信號1, 信號2, 信號3]
機會等級: [高/中/低]
緊急程度: [立即/短期/觀察]
初步建議: [BUY/SELL/HOLD]
信心度: [數字]
"""
    
    def _build_analyst_prompt(self, pair: str, market_data: Dict[str, Any], 
                            scanner_response: EnhancedAIResponse) -> str:
        """構建深度分析師提示詞"""
        return f"""
交易對: {pair}

市場掃描員報告：
{scanner_response.response}

詳細技術數據：
- 當前價格: {market_data.get('current_price', 'N/A')} TWD
- RSI: {market_data.get('rsi', 'N/A')}
- MACD線: {market_data.get('macd', 'N/A')}
- MACD信號線: {market_data.get('macd_signal', 'N/A')}
- MACD柱狀圖: {market_data.get('macd_histogram', 'N/A')}
- 布林帶上軌: {market_data.get('bollinger_upper', 'N/A')}
- 布林帶下軌: {market_data.get('bollinger_lower', 'N/A')}
- 布林帶位置: {market_data.get('bollinger_position', 'N/A')}
- SMA10: {market_data.get('sma_10', 'N/A')}
- SMA20: {market_data.get('sma_20', 'N/A')}
- EMA10: {market_data.get('ema_10', 'N/A')}
- EMA20: {market_data.get('ema_20', 'N/A')}

請進行深度技術分析：

1. 技術指標綜合分析
2. 支撐阻力位識別
3. 市場結構分析
4. 技術形態識別
5. 多時間框架一致性
6. 技術面強弱評估
7. 分析結論和建議
8. 信心度 (0-100)

請提供詳細的技術分析報告。
"""
    
    def _build_trend_prompt(self, pair: str, market_data: Dict[str, Any],
                          scanner_response: EnhancedAIResponse) -> str:
        """構建趨勢分析師提示詞"""
        return f"""
交易對: {pair}

市場掃描員初步判斷：
{scanner_response.response}

趨勢相關數據：
- 價格趨勢斜率: {market_data.get('price_trend_slope', 'N/A')}
- 價格趨勢方向: {market_data.get('price_trend', 'N/A')}
- 成交量趨勢斜率: {market_data.get('volume_trend_slope', 'N/A')}
- 成交量趨勢方向: {market_data.get('volume_trend', 'N/A')}
- 波動率: {market_data.get('volatility', 'N/A')}
- 波動率水平: {market_data.get('volatility_level', 'N/A')}

請進行趨勢分析：

1. 主趨勢方向判斷 (強烈上升/上升/橫盤/下降/強烈下降)
2. 趨勢強度評估 (強/中/弱)
3. 趨勢可持續性分析
4. 趨勢轉折信號識別
5. 回調/反彈機會評估
6. 趨勢交易建議
7. 趨勢確信度 (0-100)

格式要求：
主趨勢: [方向和強度]
可持續性: [高/中/低]
轉折信號: [有/無 - 具體描述]
交易機會: [順勢/逆勢/觀望]
建議操作: [BUY/SELL/HOLD]
確信度: [數字]
"""
    
    def _build_risk_assessment_prompt(self, pair: str, market_data: Dict[str, Any],
                                    scanner_response: EnhancedAIResponse,
                                    analyst_response: EnhancedAIResponse,
                                    trend_response: EnhancedAIResponse) -> str:
        """構建風險評估AI提示詞 ⭐ 核心新功能"""
        return f"""
交易對: {pair}

市場掃描員報告：
{scanner_response.response}

深度分析師報告：
{analyst_response.response}

趨勢分析師報告：
{trend_response.response}

風險評估數據：
- 當前價格: {market_data.get('current_price', 'N/A')} TWD
- 波動率: {market_data.get('volatility', 'N/A')}
- 波動率水平: {market_data.get('volatility_level', 'N/A')}
- 成交量比率: {market_data.get('volume_ratio', 'N/A')}
- 價格跳躍比率: {market_data.get('price_jump_ratio', 'N/A')}
- 價格跳躍: {market_data.get('price_jump', 'N/A')}
- 買賣價差: {market_data.get('spread', 'N/A')} TWD
- 買賣價差百分比: {market_data.get('spread_pct', 'N/A')}%

請進行全面風險評估：

1. 市場風險評估
   - 波動率風險 (高/中/低)
   - 流動性風險 (高/中/低)
   - 價格跳躍風險 (高/中/低)

2. 技術面風險評估
   - 技術指標背離風險
   - 支撐阻力突破風險
   - 趨勢反轉風險

3. 交易風險評估
   - 建議最大倉位 (%)
   - 建議止損點 (價格)
   - 風險收益比 (1:X)
   - 最大可接受損失 (%)

4. 風險控制建議
   - 入場策略
   - 止損策略
   - 倉位管理
   - 風險監控要點

5. 綜合風險評級
   - 風險等級 (極高/高/中/低/極低)
   - 風險評分 (0-100, 100為最高風險)
   - 交易建議 (建議/謹慎/不建議)

格式要求：
市場風險: [波動率風險/流動性風險/跳躍風險]
技術風險: [背離風險/突破風險/反轉風險]
建議倉位: [百分比]
建議止損: [價格]
風險收益比: [1:X]
風險等級: [等級]
風險評分: [0-100數字]
交易建議: [建議/謹慎/不建議]
"""
    
    def _build_final_decision_prompt(self, pair: str, market_data: Dict[str, Any],
                                   scanner_response: EnhancedAIResponse,
                                   analyst_response: EnhancedAIResponse,
                                   trend_response: EnhancedAIResponse,
                                   risk_response: EnhancedAIResponse) -> str:
        """構建最終決策者提示詞"""
        return f"""
交易對: {pair}
當前價格: {market_data.get('current_price', 'N/A')} TWD

=== AI團隊分析報告 ===

市場掃描員 (LLaMA 2:7B):
{scanner_response.response}

深度分析師 (Falcon 7B):
{analyst_response.response}

趨勢分析師 (Qwen 7B):
{trend_response.response}

風險評估AI (Mistral 7B):
{risk_response.response}

=== 最終決策制定 ===

請綜合以上四個專業AI的分析，做出最終交易決策：

1. 決策綜合分析
   - 各AI觀點一致性評估
   - 關鍵分歧點識別
   - 決策權重分配

2. 最終交易決策
   - 交易方向: BUY/SELL/HOLD
   - 決策理由 (簡潔明確)
   - 執行緊急度: 立即/短期/觀察

3. 交易執行參數
   - 建議倉位大小: X%
   - 入場價格範圍: X-Y TWD
   - 止損價格: X TWD
   - 目標價格: X TWD
   - 持有時間預期: 短期/中期/長期

4. 決策信心度
   - 整體信心度: 0-100
   - 決策一致性: 0-100
   - 風險可控性: 0-100

格式要求：
最終決策: [BUY/SELL/HOLD]
決策理由: [簡潔說明]
執行緊急度: [立即/短期/觀察]
建議倉位: [百分比]
入場範圍: [價格範圍]
止損價格: [價格]
目標價格: [價格]
持有時間: [短期/中期/長期]
整體信心度: [數字]
決策一致性: [數字]
風險可控性: [數字]
"""
    
    def _extract_confidence(self, response: str) -> float:
        """從AI回應中提取信心度"""
        try:
            import re
            
            # 尋找各種信心度表達
            patterns = [
                r'信心度[：:]\s*(\d+)',
                r'確信度[：:]\s*(\d+)',
                r'整體信心度[：:]\s*(\d+)',
                r'confidence[：:]\s*(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    return float(match.group(1)) / 100.0
            
            # 基於關鍵詞估算信心度
            if any(word in response for word in ["強烈", "確信", "明確", "高度"]):
                return 0.8
            elif any(word in response for word in ["可能", "建議", "傾向"]):
                return 0.6
            elif any(word in response for word in ["謹慎", "觀察", "不確定"]):
                return 0.4
            else:
                return 0.5
                
        except Exception:
            return 0.5
    
    def _extract_risk_score(self, response: str) -> float:
        """從風險評估回應中提取風險評分"""
        try:
            import re
            
            # 尋找風險評分
            patterns = [
                r'風險評分[：:]\s*(\d+)',
                r'風險分數[：:]\s*(\d+)',
                r'risk[_\s]score[：:]\s*(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    return float(match.group(1)) / 100.0
            
            # 基於風險等級估算
            if "極高" in response or "very high" in response.lower():
                return 0.9
            elif "高" in response or "high" in response.lower():
                return 0.7
            elif "中" in response or "medium" in response.lower():
                return 0.5
            elif "低" in response or "low" in response.lower():
                return 0.3
            else:
                return 0.5
                
        except Exception:
            return 0.5
    
    def _extract_decision(self, response: str) -> str:
        """從AI回應中提取決策"""
        response_upper = response.upper()
        
        # 尋找明確的決策關鍵詞
        if "BUY" in response_upper and "SELL" not in response_upper:
            return "BUY"
        elif "SELL" in response_upper and "BUY" not in response_upper:
            return "SELL"
        elif "HOLD" in response_upper:
            return "HOLD"
        
        # 中文決策關鍵詞
        if "買入" in response and "賣出" not in response:
            return "BUY"
        elif "賣出" in response and "買入" not in response:
            return "SELL"
        elif "持有" in response or "觀望" in response:
            return "HOLD"
        
        return "HOLD"  # 默認保守決策
    
    def _extract_position_size(self, response: str) -> float:
        """從回應中提取建議倉位大小"""
        try:
            import re
            
            patterns = [
                r'建議倉位[：:]\s*(\d+(?:\.\d+)?)%',
                r'倉位大小[：:]\s*(\d+(?:\.\d+)?)%',
                r'position[_\s]size[：:]\s*(\d+(?:\.\d+)?)%',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    return float(match.group(1)) / 100.0
            
            return 0.1  # 默認10%倉位
            
        except Exception:
            return 0.1
    
    def _synthesize_multi_pair_decision(self, pair: str, 
                                      ai_responses: List[EnhancedAIResponse]) -> MultiPairDecision:
        """綜合多AI回應生成最終決策"""
        try:
            # 提取各AI的決策和信心度
            decisions = []
            confidences = []
            weights = []
            
            for response in ai_responses:
                if response.success:
                    decision = self._extract_decision(response.response)
                    decisions.append(decision)
                    confidences.append(response.confidence)
                    
                    # 獲取AI權重
                    ai_config = self.ai_models.get(response.ai_role, {})
                    weight = ai_config.get("weight", 0.2)
                    weights.append(weight)
            
            # 加權決策
            final_decision = self._weighted_decision(decisions, confidences, weights)
            
            # 計算整體信心度
            overall_confidence = sum(c * w for c, w in zip(confidences, weights)) / sum(weights) if weights else 0.0
            
            # 計算共識水平
            consensus_level = self._calculate_consensus(decisions)
            
            # 提取風險評分
            risk_score = 0.5
            for response in ai_responses:
                if response.ai_role == "risk_assessor" and response.success:
                    risk_score = response.risk_score
                    break
            
            # 提取建議倉位
            position_size = 0.1
            for response in ai_responses:
                if response.ai_role == "decision_maker" and response.success:
                    position_size = self._extract_position_size(response.response)
                    break
            
            # 生成推理說明
            reasoning = self._generate_multi_ai_reasoning(ai_responses, final_decision)
            
            # 評估風險等級
            risk_level = self._assess_risk_level_from_score(risk_score)
            
            return MultiPairDecision(
                pair=pair,
                final_decision=final_decision,
                confidence=overall_confidence,
                consensus_level=consensus_level,
                ai_responses=ai_responses,
                reasoning=reasoning,
                risk_level=risk_level,
                risk_score=risk_score,
                position_size=position_size,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ {pair} 決策綜合失敗: {e}")
            return self._create_fallback_decision(pair, str(e))    

    def _weighted_decision(self, decisions: List[str], confidences: List[float], 
                         weights: List[float]) -> str:
        """加權決策計算"""
        if not decisions:
            return "HOLD"
        
        decision_scores = {}
        
        for decision, confidence, weight in zip(decisions, confidences, weights):
            score = confidence * weight
            if decision not in decision_scores:
                decision_scores[decision] = 0
            decision_scores[decision] += score
        
        return max(decision_scores, key=decision_scores.get)
    
    def _calculate_consensus(self, decisions: List[str]) -> float:
        """計算AI間的共識水平"""
        if not decisions:
            return 0.0
        
        from collections import Counter
        decision_counts = Counter(decisions)
        most_common_count = decision_counts.most_common(1)[0][1]
        
        return most_common_count / len(decisions)
    
    def _assess_risk_level_from_score(self, risk_score: float) -> str:
        """根據風險評分評估風險等級"""
        if risk_score >= 0.8:
            return "VERY_HIGH"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        elif risk_score >= 0.2:
            return "LOW"
        else:
            return "VERY_LOW"
    
    def _generate_multi_ai_reasoning(self, ai_responses: List[EnhancedAIResponse], 
                                   final_decision: str) -> str:
        """生成多AI推理說明"""
        reasoning_parts = [f"五AI協作決策: {final_decision}\n"]
        
        for response in ai_responses:
            if response.success:
                role_name = {
                    "market_scanner": "市場掃描員",
                    "deep_analyst": "深度分析師", 
                    "trend_analyst": "趨勢分析師",
                    "risk_assessor": "風險評估AI",
                    "decision_maker": "最終決策者"
                }.get(response.ai_role, response.ai_role)
                
                # 提取關鍵信息
                key_info = response.response[:150] + "..." if len(response.response) > 150 else response.response
                reasoning_parts.append(f"{role_name} ({response.model_name}): {key_info}")
        
        return "\n\n".join(reasoning_parts)
    
    def _create_error_response(self, ai_role: str, pair: str, error_message: str) -> EnhancedAIResponse:
        """創建錯誤回應"""
        model_name = self.ai_models.get(ai_role, {}).get("model_name", "unknown")
        
        return EnhancedAIResponse(
            ai_role=ai_role,
            model_name=model_name,
            response="",
            confidence=0.0,
            processing_time=0.0,
            timestamp=datetime.now(),
            success=False,
            pair=pair,
            error_message=error_message
        )
    
    def _create_fallback_decision(self, pair: str, error_message: str) -> MultiPairDecision:
        """創建備用決策"""
        return MultiPairDecision(
            pair=pair,
            final_decision="HOLD",
            confidence=0.0,
            consensus_level=0.0,
            ai_responses=[],
            reasoning=f"系統錯誤，採用保守策略: {error_message}",
            risk_level="VERY_HIGH",
            risk_score=1.0,
            position_size=0.0,
            timestamp=datetime.now()
        )
    
    def _update_performance_stats(self, pair: str, decision: MultiPairDecision, processing_time: float):
        """更新性能統計"""
        # 更新全局統計
        self.performance_stats["total_decisions"] += 1
        
        if decision.confidence > 0.5:
            self.performance_stats["successful_decisions"] += 1
        
        # 更新平均處理時間
        total_time = (self.performance_stats["average_processing_time"] * 
                     (self.performance_stats["total_decisions"] - 1) + processing_time)
        self.performance_stats["average_processing_time"] = total_time / self.performance_stats["total_decisions"]
        
        # 更新交易對統計
        if pair in self.performance_stats["pair_stats"]:
            pair_stats = self.performance_stats["pair_stats"][pair]
            pair_stats["decisions"] += 1
            
            # 計算成功率
            if decision.confidence > 0.5:
                success_count = pair_stats["success_rate"] * (pair_stats["decisions"] - 1) + 1
            else:
                success_count = pair_stats["success_rate"] * (pair_stats["decisions"] - 1)
            
            pair_stats["success_rate"] = success_count / pair_stats["decisions"]
        
        # 更新AI可用性
        for response in decision.ai_responses:
            if response.ai_role in self.performance_stats["ai_availability"]:
                self.performance_stats["ai_availability"][response.ai_role] = response.success
    
    def get_enhanced_performance_stats(self) -> Dict[str, Any]:
        """獲取增強性能統計"""
        return {
            "system_info": {
                "ai_models_count": len(self.ai_models),
                "supported_pairs": self.supported_pairs,
                "total_decisions": self.performance_stats["total_decisions"],
                "success_rate": (self.performance_stats["successful_decisions"] / 
                               max(1, self.performance_stats["total_decisions"])),
                "average_processing_time": self.performance_stats["average_processing_time"]
            },
            "ai_availability": self.performance_stats["ai_availability"],
            "pair_performance": self.performance_stats["pair_stats"],
            "ai_models": {
                ai_role: {
                    "model_name": config["model_name"],
                    "role": config["role"],
                    "weight": config["weight"]
                }
                for ai_role, config in self.ai_models.items()
            }
        }
    
    def get_ai_system_status(self) -> Dict[str, Any]:
        """獲取AI系統狀態"""
        return {
            "system_type": "五AI超智能協作系統",
            "models_configured": len(self.ai_models),
            "supported_pairs": len(self.supported_pairs),
            "ai_models": list(self.ai_models.keys()),
            "performance_stats": self.get_enhanced_performance_stats(),
            "system_health": "healthy" if all(self.performance_stats["ai_availability"].values()) else "degraded"
        }


# 創建全局增強AI管理器實例
def create_enhanced_ai_manager(config_path: str = "config/ai_models.json") -> EnhancedAIManager:
    """創建增強AI協作管理器實例"""
    return EnhancedAIManager(config_path)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_enhanced_ai_system():
        """測試五AI協作系統"""
        print("🧪 測試五AI超智能協作系統...")
        
        # 創建增強AI管理器
        ai_manager = create_enhanced_ai_manager()
        
        # 模擬多交易對市場數據
        test_multi_pair_data = {
            "BTCTWD": {
                "current_price": 1500000,
                "price_change_1m": 0.5,
                "price_change_5m": 1.2,
                "price_change_15m": 2.1,
                "volume_ratio": 1.5,
                "rsi": 65,
                "macd": 0.02,
                "bollinger_position": 0.7,
                "volatility": 0.03,
                "spread": 100,
                "spread_pct": 0.01
            },
            "ETHTWD": {
                "current_price": 85000,
                "price_change_1m": -0.3,
                "price_change_5m": 0.8,
                "price_change_15m": 1.5,
                "volume_ratio": 1.2,
                "rsi": 45,
                "macd": -0.01,
                "bollinger_position": 0.3,
                "volatility": 0.04,
                "spread": 50,
                "spread_pct": 0.06
            }
        }
        
        # 執行多交易對協作分析
        decisions = await ai_manager.analyze_multi_pair_market(test_multi_pair_data)
        
        print(f"\n✅ 五AI協作分析完成，處理了 {len(decisions)} 個交易對:")
        
        for pair, decision in decisions.items():
            print(f"\n📊 {pair} 決策結果:")
            print(f"   最終決策: {decision.final_decision}")
            print(f"   信心度: {decision.confidence:.2f}")
            print(f"   共識水平: {decision.consensus_level:.2f}")
            print(f"   風險等級: {decision.risk_level}")
            print(f"   風險評分: {decision.risk_score:.2f}")
            print(f"   建議倉位: {decision.position_size:.1%}")
        
        # 顯示系統狀態
        status = ai_manager.get_ai_system_status()
        print(f"\n🤖 系統狀態:")
        print(f"   系統類型: {status['system_type']}")
        print(f"   AI模型數量: {status['models_configured']}")
        print(f"   支持交易對: {status['supported_pairs']}")
        print(f"   系統健康: {status['system_health']}")
    
    # 運行測試
    asyncio.run(test_enhanced_ai_system())
    
    def _generate_multi_ai_reasoning(self, ai_responses: List[EnhancedAIResponse], 
                                   final_decision: str) -> str:
        """生成多AI推理說明"""
        try:
            reasoning_parts = []
            
            for response in ai_responses:
                if response.success:
                    ai_name = {
                        "market_scanner": "市場掃描員",
                        "deep_analyst": "深度分析師",
                        "trend_analyst": "趨勢分析師", 
                        "risk_assessor": "風險評估AI",
                        "decision_maker": "最終決策者"
                    }.get(response.ai_role, response.ai_role)
                    
                    # 提取關鍵觀點
                    key_point = response.response[:100] + "..." if len(response.response) > 100 else response.response
                    reasoning_parts.append(f"{ai_name}: {key_point}")
            
            reasoning = f"五AI協作決策 -> {final_decision}\\n" + "\\n".join(reasoning_parts)
            return reasoning
            
        except Exception:
            return f"五AI協作決策: {final_decision}"
    
    def _assess_risk_level_from_score(self, risk_score: float) -> str:
        """根據風險評分評估風險等級"""
        if risk_score >= 0.8:
            return "極高"
        elif risk_score >= 0.6:
            return "高"
        elif risk_score >= 0.4:
            return "中"
        elif risk_score >= 0.2:
            return "低"
        else:
            return "極低"
    
    def _create_multi_pair_context(self, multi_pair_data: Dict[str, Dict[str, Any]]) -> MultiPairContext:
        """創建多交易對上下文 ⭐ 新增方法"""
        try:
            # 分析全局市場條件
            avg_volatility = sum(data.get('volatility', 0.02) for data in multi_pair_data.values()) / len(multi_pair_data)
            
            # 判斷市場條件
            if avg_volatility > 0.05:
                market_conditions = 'bear'
            elif avg_volatility < 0.02:
                market_conditions = 'bull'
            else:
                market_conditions = 'sideways'
            
            # 計算簡化的相關性矩陣
            correlation_matrix = {}
            pairs = list(multi_pair_data.keys())
            
            for pair1 in pairs:
                correlation_matrix[pair1] = {}
                for pair2 in pairs:
                    if pair1 == pair2:
                        correlation_matrix[pair1][pair2] = 1.0
                    else:
                        # 基於價格變化計算簡化相關性
                        change1 = multi_pair_data[pair1].get('price_change_5m', 0)
                        change2 = multi_pair_data[pair2].get('price_change_5m', 0)
                        
                        if change1 * change2 > 0:
                            correlation = min(0.8, abs(change1 + change2) / 10)
                        else:
                            correlation = max(-0.5, -(abs(change1 - change2) / 10))
                        
                        correlation_matrix[pair1][pair2] = correlation
            
            return MultiPairContext(
                total_pairs=len(multi_pair_data),
                active_pairs=list(multi_pair_data.keys()),
                market_conditions=market_conditions,
                correlation_matrix=correlation_matrix,
                global_risk_level=min(1.0, avg_volatility * 10),
                available_capital=100000.0  # 預設10萬TWD
            )
            
        except Exception as e:
            logger.error(f"❌ 創建多交易對上下文失敗: {e}")
            return MultiPairContext(
                total_pairs=len(multi_pair_data),
                active_pairs=list(multi_pair_data.keys()),
                market_conditions='sideways',
                correlation_matrix={},
                global_risk_level=0.5,
                available_capital=100000.0
            )
    
    async def _analyze_single_pair_with_context(self, pair: str, market_data: Dict[str, Any], 
                                              multi_pair_context: MultiPairContext) -> MultiPairDecision:
        """使用多交易對上下文分析單個交易對 ⭐ 新增方法"""
        start_time = datetime.now()
        
        try:
            logger.info(f"📊 開始分析 {pair}")
            
            # 階段1: 市場掃描員 (使用優化提示詞)
            scanner_response = await self._run_market_scanner_with_context(pair, market_data, multi_pair_context)
            
            # 階段2: 深度分析師 (使用優化提示詞)
            analyst_response = await self._run_deep_analyst_with_context(pair, market_data, scanner_response, multi_pair_context)
            
            # 階段3: 趨勢分析師 (使用優化提示詞)
            trend_response = await self._run_trend_analyst_with_context(pair, market_data, scanner_response, multi_pair_context)
            
            # 階段4: 風險評估AI (使用優化提示詞)
            risk_response = await self._run_risk_assessor_with_context(pair, market_data, 
                                                                    scanner_response, analyst_response, 
                                                                    trend_response, multi_pair_context)
            
            # 階段5: 最終決策者 (使用優化提示詞)
            decision_response = await self._run_decision_maker_with_context(pair, market_data,
                                                                          scanner_response, analyst_response, 
                                                                          trend_response, risk_response, 
                                                                          multi_pair_context)
            
            # 綜合所有AI的回應
            ai_responses = [scanner_response, analyst_response, trend_response, 
                          risk_response, decision_response]
            
            # 生成最終協作決策
            collaborative_decision = self._synthesize_multi_pair_decision(pair, ai_responses)
            
            # 更新性能統計
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_stats(pair, collaborative_decision, processing_time)
            
            logger.info(f"✅ {pair} 分析完成: {collaborative_decision.final_decision} "
                       f"(信心度: {collaborative_decision.confidence:.2f})")
            
            return collaborative_decision
            
        except Exception as e:
            logger.error(f"❌ {pair} 分析失敗: {e}")
            return self._create_fallback_decision(pair, str(e))
    
    async def _run_market_scanner_with_context(self, pair: str, market_data: Dict[str, Any], 
                                             multi_pair_context: MultiPairContext) -> EnhancedAIResponse:
        """運行市場掃描員 - 多交易對優化版本"""
        start_time = datetime.now()
        
        try:
            model_config = self.ai_models["market_scanner"]
            
            # 使用優化的多交易對提示詞
            prompt = self.prompt_optimizer.get_optimized_scanner_prompt(pair, market_data, multi_pair_context)
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=self._get_scanner_system_prompt(),
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return EnhancedAIResponse(
                ai_role="market_scanner",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True,
                pair=pair
            )
            
        except Exception as e:
            logger.error(f"❌ {pair} 市場掃描員執行失敗: {e}")
            return self._create_error_response("market_scanner", pair, str(e))
    
    async def _run_deep_analyst_with_context(self, pair: str, market_data: Dict[str, Any], 
                                           scanner_response: EnhancedAIResponse,
                                           multi_pair_context: MultiPairContext) -> EnhancedAIResponse:
        """運行深度分析師 - 多交易對優化版本"""
        start_time = datetime.now()
        
        try:
            model_config = self.ai_models["deep_analyst"]
            
            # 使用優化的多交易對提示詞
            prompt = self.prompt_optimizer.get_optimized_analyst_prompt(
                pair, market_data, scanner_response.response, multi_pair_context
            )
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=self._get_analyst_system_prompt(),
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return EnhancedAIResponse(
                ai_role="deep_analyst",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True,
                pair=pair
            )
            
        except Exception as e:
            logger.error(f"❌ {pair} 深度分析師執行失敗: {e}")
            return self._create_error_response("deep_analyst", pair, str(e))
    
    async def _run_trend_analyst_with_context(self, pair: str, market_data: Dict[str, Any],
                                            scanner_response: EnhancedAIResponse,
                                            multi_pair_context: MultiPairContext) -> EnhancedAIResponse:
        """運行趨勢分析師 - 多交易對優化版本"""
        start_time = datetime.now()
        
        try:
            model_config = self.ai_models["trend_analyst"]
            
            # 使用優化的多交易對提示詞
            prompt = self.prompt_optimizer.get_optimized_trend_prompt(
                pair, market_data, scanner_response.response, multi_pair_context
            )
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=self._get_trend_system_prompt(),
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return EnhancedAIResponse(
                ai_role="trend_analyst",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True,
                pair=pair
            )
            
        except Exception as e:
            logger.error(f"❌ {pair} 趨勢分析師執行失敗: {e}")
            return self._create_error_response("trend_analyst", pair, str(e))
    
    async def _run_risk_assessor_with_context(self, pair: str, market_data: Dict[str, Any],
                                            scanner_response: EnhancedAIResponse,
                                            analyst_response: EnhancedAIResponse,
                                            trend_response: EnhancedAIResponse,
                                            multi_pair_context: MultiPairContext) -> EnhancedAIResponse:
        """運行風險評估AI - 多交易對優化版本"""
        start_time = datetime.now()
        
        try:
            model_config = self.ai_models["risk_assessor"]
            
            # 使用優化的多交易對提示詞
            prompt = self.prompt_optimizer.get_optimized_risk_prompt(
                pair, market_data, scanner_response.response, analyst_response.response,
                trend_response.response, multi_pair_context
            )
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=self._get_risk_assessor_system_prompt(),
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            risk_score = self._extract_risk_score(response)
            
            return EnhancedAIResponse(
                ai_role="risk_assessor",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True,
                pair=pair,
                risk_score=risk_score
            )
            
        except Exception as e:
            logger.error(f"❌ {pair} 風險評估AI執行失敗: {e}")
            return self._create_error_response("risk_assessor", pair, str(e))
    
    async def _run_decision_maker_with_context(self, pair: str, market_data: Dict[str, Any],
                                             scanner_response: EnhancedAIResponse,
                                             analyst_response: EnhancedAIResponse,
                                             trend_response: EnhancedAIResponse,
                                             risk_response: EnhancedAIResponse,
                                             multi_pair_context: MultiPairContext) -> EnhancedAIResponse:
        """運行最終決策者 - 多交易對優化版本"""
        start_time = datetime.now()
        
        try:
            model_config = self.ai_models["decision_maker"]
            
            # 使用優化的多交易對提示詞
            prompt = self.prompt_optimizer.get_optimized_decision_prompt(
                pair, market_data, scanner_response.response, analyst_response.response,
                trend_response.response, risk_response.response, multi_pair_context
            )
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=self._get_decision_maker_system_prompt(),
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return EnhancedAIResponse(
                ai_role="decision_maker",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True,
                pair=pair
            )
            
        except Exception as e:
            logger.error(f"❌ {pair} 最終決策者執行失敗: {e}")
            return self._create_error_response("decision_maker", pair, str(e))
    
    def _update_performance_stats(self, pair: str, decision: MultiPairDecision, processing_time: float):
        """更新性能統計"""
        try:
            self.performance_stats["total_decisions"] += 1
            
            if decision.confidence > 0.6:
                self.performance_stats["successful_decisions"] += 1
            
            # 更新平均處理時間
            total_time = (self.performance_stats["average_processing_time"] * 
                         (self.performance_stats["total_decisions"] - 1) + processing_time)
            self.performance_stats["average_processing_time"] = total_time / self.performance_stats["total_decisions"]
            
            # 更新交易對統計
            if pair in self.performance_stats["pair_stats"]:
                pair_stats = self.performance_stats["pair_stats"][pair]
                pair_stats["decisions"] += 1
                pair_stats["success_rate"] = (pair_stats["success_rate"] * (pair_stats["decisions"] - 1) + 
                                            (1 if decision.confidence > 0.6 else 0)) / pair_stats["decisions"]
            
        except Exception as e:
            logger.error(f"❌ 更新性能統計失敗: {e}")
    
    def _create_error_response(self, ai_role: str, pair: str, error_message: str) -> EnhancedAIResponse:
        """創建錯誤回應"""
        return EnhancedAIResponse(
            ai_role=ai_role,
            model_name="error",
            response=f"AI執行錯誤: {error_message}",
            confidence=0.0,
            processing_time=0.0,
            timestamp=datetime.now(),
            success=False,
            pair=pair,
            error_message=error_message
        )
    
    def _create_fallback_decision(self, pair: str, error_message: str) -> MultiPairDecision:
        """創建備用決策"""
        return MultiPairDecision(
            pair=pair,
            final_decision="HOLD",
            confidence=0.0,
            consensus_level=0.0,
            ai_responses=[],
            reasoning=f"系統錯誤，採用保守策略: {error_message}",
            risk_level="未知",
            risk_score=0.5,
            position_size=0.0,
            timestamp=datetime.now()
        )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取性能統計"""
        return self.performance_stats.copy()
    
    def get_supported_pairs(self) -> List[str]:
        """獲取支持的交易對"""
        return self.supported_pairs.copy()


# 創建增強AI管理器實例
def create_enhanced_ai_manager(config_path: str = "config/ai_models.json") -> EnhancedAIManager:
    """創建增強AI管理器實例"""
    return EnhancedAIManager(config_path)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_enhanced_ai_manager():
        """測試增強AI管理器"""
        print("🧪 測試增強AI協作管理器...")
        
        manager = create_enhanced_ai_manager()
        
        # 測試數據
        test_data = {
            "BTCTWD": {
                "current_price": 1520000,
                "price_change_1m": 1.2,
                "price_change_5m": 2.5,
                "volume_ratio": 2.3,
                "rsi": 72,
                "macd": 0.03,
                "volatility": 0.045
            }
        }
        
        # 測試多交易對分析
        decisions = await manager.analyze_multi_pair_market(test_data)
        
        print(f"✅ 測試完成: {len(decisions)} 個決策")
        for pair, decision in decisions.items():
            print(f"   {pair}: {decision.final_decision} (信心度: {decision.confidence:.2f})")
    
    # 運行測試
    asyncio.run(test_enhanced_ai_manager())