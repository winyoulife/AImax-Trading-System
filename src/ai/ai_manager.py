#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI協作管理器 - 統一管理三個AI模型的協作
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

import ollama

logger = logging.getLogger(__name__)

@dataclass
class AIResponse:
    """AI回應數據結構"""
    ai_role: str
    model_name: str
    response: str
    confidence: float
    processing_time: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None

@dataclass
class CollaborativeDecision:
    """協作決策結果"""
    final_decision: str  # BUY, SELL, HOLD
    confidence: float
    consensus_level: float
    ai_responses: List[AIResponse]
    reasoning: str
    risk_level: str
    timestamp: datetime

class AICollaborationManager:
    """AI協作管理器"""
    
    def __init__(self, config_path: str = "config/ai_models.json"):
        """
        初始化AI協作管理器
        
        Args:
            config_path: AI模型配置文件路徑
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.ollama_client = ollama.Client()
        
        # AI模型配置
        self.models = self.config["ai_models"]
        self.collaboration_settings = self.config["collaboration_settings"]
        self.fallback_settings = self.config["fallback_settings"]
        
        # 性能統計
        self.performance_stats = {
            "total_decisions": 0,
            "successful_decisions": 0,
            "average_processing_time": 0.0,
            "ai_availability": {
                "market_scanner": True,
                "deep_analyst": True,
                "decision_maker": True
            }
        }
        
        logger.info("🤖 AI協作管理器初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """載入AI模型配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"✅ 載入AI配置: {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ 載入AI配置失敗: {e}")
            raise
    
    async def analyze_market_collaboratively(self, market_data: Dict[str, Any]) -> CollaborativeDecision:
        """
        協作分析市場數據
        
        Args:
            market_data: 市場數據
            
        Returns:
            CollaborativeDecision: 協作決策結果
        """
        start_time = datetime.now()
        
        try:
            logger.info("🚀 開始AI協作市場分析")
            
            # 階段1: 市場掃描員快速掃描
            scanner_response = await self._run_market_scanner(market_data)
            
            # 階段2: 深度分析師詳細分析
            analyst_response = await self._run_deep_analyst(market_data, scanner_response)
            
            # 階段3: 最終決策者做出決策
            decision_response = await self._run_decision_maker(
                market_data, scanner_response, analyst_response
            )
            
            # 綜合所有AI的回應
            ai_responses = [scanner_response, analyst_response, decision_response]
            
            # 生成最終協作決策
            collaborative_decision = self._synthesize_decision(ai_responses)
            
            # 更新性能統計
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_stats(collaborative_decision, processing_time)
            
            logger.info(f"✅ AI協作分析完成: {collaborative_decision.final_decision}")
            return collaborative_decision
            
        except Exception as e:
            logger.error(f"❌ AI協作分析失敗: {e}")
            return self._create_fallback_decision(str(e))
    
    async def _run_market_scanner(self, market_data: Dict[str, Any]) -> AIResponse:
        """運行市場掃描員"""
        start_time = datetime.now()
        
        try:
            model_config = self.models["market_scanner"]
            
            prompt = self._build_scanner_prompt(market_data)
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=model_config["system_prompt"],
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AIResponse(
                ai_role="market_scanner",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True
            )
            
        except Exception as e:
            logger.error(f"❌ 市場掃描員執行失敗: {e}")
            return AIResponse(
                ai_role="market_scanner",
                model_name=model_config["model_name"],
                response="",
                confidence=0.0,
                processing_time=0.0,
                timestamp=datetime.now(),
                success=False,
                error_message=str(e)
            )
    
    async def _run_deep_analyst(self, market_data: Dict[str, Any], scanner_response: AIResponse) -> AIResponse:
        """運行深度分析師"""
        start_time = datetime.now()
        
        try:
            model_config = self.models["deep_analyst"]
            
            prompt = self._build_analyst_prompt(market_data, scanner_response)
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=model_config["system_prompt"],
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AIResponse(
                ai_role="deep_analyst",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True
            )
            
        except Exception as e:
            logger.error(f"❌ 深度分析師執行失敗: {e}")
            return AIResponse(
                ai_role="deep_analyst",
                model_name=model_config["model_name"],
                response="",
                confidence=0.0,
                processing_time=0.0,
                timestamp=datetime.now(),
                success=False,
                error_message=str(e)
            )
    
    async def _run_decision_maker(self, market_data: Dict[str, Any], 
                                scanner_response: AIResponse, 
                                analyst_response: AIResponse) -> AIResponse:
        """運行最終決策者"""
        start_time = datetime.now()
        
        try:
            model_config = self.models["decision_maker"]
            
            prompt = self._build_decision_prompt(market_data, scanner_response, analyst_response)
            
            response = await self._call_ai_model(
                model_name=model_config["model_name"],
                system_prompt=model_config["system_prompt"],
                user_prompt=prompt,
                max_tokens=model_config["max_tokens"],
                temperature=model_config["temperature"]
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AIResponse(
                ai_role="decision_maker",
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True
            )
            
        except Exception as e:
            logger.error(f"❌ 最終決策者執行失敗: {e}")
            return AIResponse(
                ai_role="decision_maker",
                model_name=model_config["model_name"],
                response="",
                confidence=0.0,
                processing_time=0.0,
                timestamp=datetime.now(),
                success=False,
                error_message=str(e)
            )
    
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
    
    def _build_scanner_prompt(self, market_data: Dict[str, Any]) -> str:
        """構建市場掃描員提示詞"""
        # 如果有AI格式化的數據，直接使用
        if 'ai_formatted_data' in market_data:
            formatted_data = market_data['ai_formatted_data']
        else:
            # 回退到基本格式
            formatted_data = f"""
市場數據：
- 當前價格: {market_data.get('current_price', 'N/A')} TWD
- 1分鐘變化: {market_data.get('price_change_1m', 'N/A')}%
- 5分鐘變化: {market_data.get('price_change_5m', 'N/A')}%
- 成交量比率: {market_data.get('volume_ratio', 'N/A')}x
- RSI: {market_data.get('rsi', 'N/A')}
- MACD: {market_data.get('macd_trend', 'N/A')}
"""
        
        return f"""
你是專業的加密貨幣市場掃描員，負責快速識別交易機會。

{formatted_data}

請基於以上數據進行快速分析：

1. 市場評估 (看漲/看跌/中性)
2. 關鍵信號識別 (列出2-3個最重要的信號)
3. 機會等級 (高/中/低)
4. 信心度 (0-100)
5. 建議操作 (BUY/SELL/HOLD)

要求：
- 保持簡潔，專注於最關鍵的信號
- 優先考慮技術指標組合
- 注意成交量和價格的配合
- 給出明確的數字信心度

格式：
市場評估: [看漲/看跌/中性]
關鍵信號: [信號1, 信號2, 信號3]
機會等級: [高/中/低]
建議操作: [BUY/SELL/HOLD]
信心度: [0-100數字]
"""
    
    def _build_analyst_prompt(self, market_data: Dict[str, Any], scanner_response: AIResponse) -> str:
        """構建深度分析師提示詞"""
        return f"""
基於市場掃描員的初步分析，請進行深度技術分析：

市場掃描員報告：
{scanner_response.response}

詳細市場數據：
- 當前價格: {market_data.get('current_price', 'N/A')} TWD
- 價格變化: {market_data.get('price_changes', {})}
- 技術指標: {market_data.get('technical_indicators', {})}
- 成交量分析: {market_data.get('volume_analysis', {})}

請提供：
1. 技術指標分析
2. 支撐阻力位分析
3. 風險評估
4. 詳細交易建議
5. 信心度 (0-100)

請提供專業的技術分析報告。
"""
    
    def _build_decision_prompt(self, market_data: Dict[str, Any], 
                             scanner_response: AIResponse, 
                             analyst_response: AIResponse) -> str:
        """構建最終決策者提示詞"""
        return f"""
基於市場掃描員和深度分析師的報告，請做出最終交易決策：

市場掃描員報告：
{scanner_response.response}

深度分析師報告：
{analyst_response.response}

請綜合分析並提供：
1. 最終決策: BUY/SELL/HOLD
2. 決策理由
3. 建議倉位大小 (%)
4. 止損點
5. 目標價位
6. 信心度 (0-100)

請做出明確的交易決策。
"""
    
    def _extract_confidence(self, response: str) -> float:
        """從AI回應中提取信心度"""
        try:
            # 簡化版本：尋找信心度數字
            import re
            confidence_match = re.search(r'信心度[：:]\s*(\d+)', response)
            if confidence_match:
                return float(confidence_match.group(1)) / 100.0
            
            # 如果找不到明確的信心度，根據回應內容估算
            if "強烈" in response or "確信" in response:
                return 0.8
            elif "可能" in response or "建議" in response:
                return 0.6
            else:
                return 0.5
                
        except Exception:
            return 0.5
    
    def _synthesize_decision(self, ai_responses: List[AIResponse]) -> CollaborativeDecision:
        """綜合AI回應生成最終決策"""
        try:
            # 提取決策
            decisions = []
            confidences = []
            
            for response in ai_responses:
                if response.success:
                    decision = self._extract_decision(response.response)
                    decisions.append(decision)
                    confidences.append(response.confidence)
            
            # 計算共識水平
            consensus_level = self._calculate_consensus(decisions)
            
            # 確定最終決策
            final_decision = self._determine_final_decision(decisions, confidences)
            
            # 計算整體信心度
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # 生成推理說明
            reasoning = self._generate_reasoning(ai_responses, final_decision)
            
            # 評估風險等級
            risk_level = self._assess_risk_level(ai_responses, overall_confidence)
            
            return CollaborativeDecision(
                final_decision=final_decision,
                confidence=overall_confidence,
                consensus_level=consensus_level,
                ai_responses=ai_responses,
                reasoning=reasoning,
                risk_level=risk_level,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ 決策綜合失敗: {e}")
            return self._create_fallback_decision(str(e))
    
    def _extract_decision(self, response: str) -> str:
        """從AI回應中提取決策"""
        response_upper = response.upper()
        
        if "BUY" in response_upper and "SELL" not in response_upper:
            return "BUY"
        elif "SELL" in response_upper and "BUY" not in response_upper:
            return "SELL"
        else:
            return "HOLD"
    
    def _calculate_consensus(self, decisions: List[str]) -> float:
        """計算AI間的共識水平"""
        if not decisions:
            return 0.0
        
        # 計算最常見決策的比例
        from collections import Counter
        decision_counts = Counter(decisions)
        most_common_count = decision_counts.most_common(1)[0][1]
        
        return most_common_count / len(decisions)
    
    def _determine_final_decision(self, decisions: List[str], confidences: List[float]) -> str:
        """確定最終決策"""
        if not decisions:
            return "HOLD"
        
        # 加權投票
        decision_weights = {}
        for decision, confidence in zip(decisions, confidences):
            if decision not in decision_weights:
                decision_weights[decision] = 0
            decision_weights[decision] += confidence
        
        # 返回權重最高的決策
        return max(decision_weights, key=decision_weights.get)
    
    def _generate_reasoning(self, ai_responses: List[AIResponse], final_decision: str) -> str:
        """生成決策推理說明"""
        reasoning_parts = []
        
        for response in ai_responses:
            if response.success:
                reasoning_parts.append(f"{response.ai_role}: {response.response[:100]}...")
        
        reasoning = f"最終決策: {final_decision}\n\n" + "\n\n".join(reasoning_parts)
        return reasoning
    
    def _assess_risk_level(self, ai_responses: List[AIResponse], confidence: float) -> str:
        """評估風險等級"""
        if confidence >= 0.8:
            return "LOW"
        elif confidence >= 0.6:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _create_fallback_decision(self, error_message: str) -> CollaborativeDecision:
        """創建備用決策"""
        return CollaborativeDecision(
            final_decision="HOLD",
            confidence=0.0,
            consensus_level=0.0,
            ai_responses=[],
            reasoning=f"系統錯誤，採用保守策略: {error_message}",
            risk_level="HIGH",
            timestamp=datetime.now()
        )
    
    def _update_performance_stats(self, decision: CollaborativeDecision, processing_time: float):
        """更新性能統計"""
        self.performance_stats["total_decisions"] += 1
        
        if decision.confidence > 0.5:
            self.performance_stats["successful_decisions"] += 1
        
        # 更新平均處理時間
        total_time = (self.performance_stats["average_processing_time"] * 
                     (self.performance_stats["total_decisions"] - 1) + processing_time)
        self.performance_stats["average_processing_time"] = total_time / self.performance_stats["total_decisions"]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取性能統計"""
        return self.performance_stats.copy()
    
    def get_ai_status(self) -> Dict[str, Any]:
        """獲取AI狀態"""
        return {
            "models_configured": len(self.models),
            "collaboration_enabled": self.collaboration_settings["enable_parallel_processing"],
            "fallback_enabled": self.fallback_settings["enable_fallback"],
            "performance_stats": self.get_performance_stats()
        }


# 創建全局AI管理器實例
def create_ai_manager(config_path: str = "config/ai_models.json") -> AICollaborationManager:
    """創建AI協作管理器實例"""
    return AICollaborationManager(config_path)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_ai_collaboration():
        """測試AI協作功能"""
        print("🧪 測試AI協作系統...")
        
        # 創建AI管理器
        ai_manager = create_ai_manager()
        
        # 模擬市場數據
        test_market_data = {
            "current_price": 1500000,
            "price_change_1m": 0.5,
            "price_change_5m": 1.2,
            "volume": 1000000,
            "volume_change": 25,
            "technical_indicators": {
                "rsi": 65,
                "macd": "金叉"
            }
        }
        
        # 執行協作分析
        decision = await ai_manager.analyze_market_collaboratively(test_market_data)
        
        print(f"✅ 協作決策完成:")
        print(f"最終決策: {decision.final_decision}")
        print(f"信心度: {decision.confidence:.2f}")
        print(f"共識水平: {decision.consensus_level:.2f}")
        print(f"風險等級: {decision.risk_level}")
        
        # 顯示性能統計
        stats = ai_manager.get_performance_stats()
        print(f"\n📊 性能統計:")
        print(f"總決策次數: {stats['total_decisions']}")
        print(f"成功決策次數: {stats['successful_decisions']}")
        print(f"平均處理時間: {stats['average_processing_time']:.2f}秒")
    
    # 運行測試
    asyncio.run(test_ai_collaboration())