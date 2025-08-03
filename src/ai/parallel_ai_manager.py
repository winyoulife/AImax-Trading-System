#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
並行AI管理器 - 優化AI推理速度的並行處理版本
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import ollama

logger = logging.getLogger(__name__)

@dataclass
class ParallelAIResponse:
    """並行AI回應數據結構"""
    ai_role: str
    model_name: str
    response: str
    confidence: float
    processing_time: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    parallel_execution: bool = True

@dataclass
class OptimizedDecision:
    """優化後的協作決策結果"""
    final_decision: str  # BUY, SELL, HOLD
    confidence: float
    consensus_level: float
    ai_responses: List[ParallelAIResponse]
    reasoning: str
    risk_level: str
    timestamp: datetime
    total_processing_time: float
    parallel_efficiency: float  # 並行效率比率

class ParallelAIManager:
    """並行AI管理器 - 優化版本"""
    
    def __init__(self, config_path: str = "config/ai_models_qwen7b.json"):
        """
        初始化並行AI管理器
        
        Args:
            config_path: AI模型配置文件路徑
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # 創建多個Ollama客戶端實例以支持並行
        self.ollama_clients = [ollama.Client() for _ in range(3)]
        
        # AI模型配置
        self.models = self.config["ai_models"]
        self.collaboration_settings = self.config["collaboration_settings"]
        
        # 性能統計
        self.performance_stats = {
            "total_decisions": 0,
            "successful_decisions": 0,
            "parallel_decisions": 0,
            "average_processing_time": 0.0,
            "average_parallel_efficiency": 0.0,
            "speed_improvement": 0.0,
            "ai_availability": {
                "market_scanner": True,
                "deep_analyst": True,
                "decision_maker": True
            }
        }
        
        # 線程池執行器
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        logger.info("🚀 並行AI管理器初始化完成")
    
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
    
    async def analyze_market_parallel(self, market_data: Dict[str, Any]) -> OptimizedDecision:
        """
        並行分析市場數據 - 優化版本
        
        Args:
            market_data: 市場數據
            
        Returns:
            OptimizedDecision: 優化後的協作決策結果
        """
        start_time = time.time()
        
        try:
            logger.info("🚀 開始並行AI協作市場分析")
            
            # 檢查是否啟用並行處理
            if self.collaboration_settings.get("enable_parallel_processing", True):
                # 並行執行所有AI分析
                ai_responses = await self._run_parallel_analysis(market_data)
                parallel_execution = True
            else:
                # 順序執行（回退模式）
                ai_responses = await self._run_sequential_analysis(market_data)
                parallel_execution = False
            
            # 生成最終協作決策
            collaborative_decision = self._synthesize_optimized_decision(ai_responses, start_time)
            
            # 計算並行效率
            if parallel_execution:
                collaborative_decision.parallel_efficiency = self._calculate_parallel_efficiency(ai_responses)
            else:
                collaborative_decision.parallel_efficiency = 1.0
            
            # 更新性能統計
            processing_time = time.time() - start_time
            self._update_performance_stats(collaborative_decision, processing_time, parallel_execution)
            
            logger.info(f"✅ 並行AI分析完成: {collaborative_decision.final_decision} (耗時: {processing_time:.2f}s)")
            return collaborative_decision
            
        except Exception as e:
            logger.error(f"❌ 並行AI分析失敗: {e}")
            return self._create_fallback_decision(str(e), time.time() - start_time)
    
    async def _run_parallel_analysis(self, market_data: Dict[str, Any]) -> List[ParallelAIResponse]:
        """並行執行AI分析"""
        try:
            # 創建並行任務
            tasks = []
            
            # 任務1: 市場掃描員
            scanner_task = asyncio.create_task(
                self._run_ai_model_async(
                    "market_scanner", 
                    self._build_scanner_prompt(market_data),
                    0  # 使用第一個客戶端
                )
            )
            tasks.append(scanner_task)
            
            # 任務2: 深度分析師（可以並行，因為不依賴掃描員結果）
            analyst_task = asyncio.create_task(
                self._run_ai_model_async(
                    "deep_analyst", 
                    self._build_analyst_prompt_independent(market_data),
                    1  # 使用第二個客戶端
                )
            )
            tasks.append(analyst_task)
            
            # 等待前兩個任務完成
            scanner_response, analyst_response = await asyncio.gather(*tasks)
            
            # 任務3: 最終決策者（需要前兩個結果）
            decision_task = asyncio.create_task(
                self._run_ai_model_async(
                    "decision_maker",
                    self._build_decision_prompt(market_data, scanner_response, analyst_response),
                    2  # 使用第三個客戶端
                )
            )
            
            decision_response = await decision_task
            
            return [scanner_response, analyst_response, decision_response]
            
        except Exception as e:
            logger.error(f"❌ 並行分析執行失敗: {e}")
            raise
    
    async def _run_sequential_analysis(self, market_data: Dict[str, Any]) -> List[ParallelAIResponse]:
        """順序執行AI分析（回退模式）"""
        try:
            responses = []
            
            # 順序執行
            scanner_response = await self._run_ai_model_async(
                "market_scanner", 
                self._build_scanner_prompt(market_data),
                0
            )
            responses.append(scanner_response)
            
            analyst_response = await self._run_ai_model_async(
                "deep_analyst", 
                self._build_analyst_prompt(market_data, scanner_response),
                0
            )
            responses.append(analyst_response)
            
            decision_response = await self._run_ai_model_async(
                "decision_maker",
                self._build_decision_prompt(market_data, scanner_response, analyst_response),
                0
            )
            responses.append(decision_response)
            
            # 標記為非並行執行
            for response in responses:
                response.parallel_execution = False
            
            return responses
            
        except Exception as e:
            logger.error(f"❌ 順序分析執行失敗: {e}")
            raise
    
    async def _run_ai_model_async(self, model_role: str, prompt: str, client_index: int) -> ParallelAIResponse:
        """異步運行AI模型"""
        start_time = time.time()
        
        try:
            model_config = self.models[model_role]
            client = self.ollama_clients[client_index]
            
            # 在線程池中執行AI調用以避免阻塞
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                self.executor,
                self._call_ai_model_sync,
                client,
                model_config["model_name"],
                model_config["system_prompt"],
                prompt,
                model_config["max_tokens"],
                model_config["temperature"]
            )
            
            processing_time = time.time() - start_time
            
            return ParallelAIResponse(
                ai_role=model_role,
                model_name=model_config["model_name"],
                response=response,
                confidence=self._extract_confidence(response),
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=True,
                parallel_execution=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ AI模型執行失敗 ({model_role}): {e}")
            
            return ParallelAIResponse(
                ai_role=model_role,
                model_name=model_config["model_name"],
                response="",
                confidence=0.0,
                processing_time=processing_time,
                timestamp=datetime.now(),
                success=False,
                error_message=str(e),
                parallel_execution=True
            )
    
    def _call_ai_model_sync(self, client: ollama.Client, model_name: str, 
                           system_prompt: str, user_prompt: str, 
                           max_tokens: int, temperature: float) -> str:
        """同步調用AI模型（在線程池中執行）"""
        try:
            response = client.chat(
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
            logger.error(f"❌ 同步AI模型調用失敗 ({model_name}): {e}")
            raise
    
    def _build_scanner_prompt(self, market_data: Dict[str, Any]) -> str:
        """構建市場掃描員提示詞"""
        if 'ai_formatted_data' in market_data:
            formatted_data = market_data['ai_formatted_data']
        else:
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
    
    def _build_analyst_prompt_independent(self, market_data: Dict[str, Any]) -> str:
        """構建獨立的深度分析師提示詞（不依賴掃描員結果）"""
        return f"""
你是資深的加密貨幣技術分析師，請對當前市場進行深度技術分析：

市場數據：
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
    
    def _build_analyst_prompt(self, market_data: Dict[str, Any], scanner_response: ParallelAIResponse) -> str:
        """構建深度分析師提示詞（基於掃描員結果）"""
        return f"""
基於市場掃描員的初步分析，請進行深度技術分析：

市場掃描員報告：
{scanner_response.response if scanner_response.success else "掃描員分析失敗"}

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
                             scanner_response: ParallelAIResponse, 
                             analyst_response: ParallelAIResponse) -> str:
        """構建最終決策者提示詞"""
        return f"""
基於市場掃描員和深度分析師的報告，請做出最終交易決策：

市場掃描員報告：
{scanner_response.response if scanner_response.success else "掃描員分析失敗"}

深度分析師報告：
{analyst_response.response if analyst_response.success else "分析師分析失敗"}

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
            import re
            confidence_match = re.search(r'信心度[：:]\s*(\d+)', response)
            if confidence_match:
                return float(confidence_match.group(1)) / 100.0
            
            if "強烈" in response or "確信" in response:
                return 0.8
            elif "可能" in response or "建議" in response:
                return 0.6
            else:
                return 0.5
                
        except Exception:
            return 0.5
    
    def _synthesize_optimized_decision(self, ai_responses: List[ParallelAIResponse], 
                                     start_time: float) -> OptimizedDecision:
        """綜合AI回應生成優化決策"""
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
            
            # 計算總處理時間
            total_processing_time = time.time() - start_time
            
            return OptimizedDecision(
                final_decision=final_decision,
                confidence=overall_confidence,
                consensus_level=consensus_level,
                ai_responses=ai_responses,
                reasoning=reasoning,
                risk_level=risk_level,
                timestamp=datetime.now(),
                total_processing_time=total_processing_time,
                parallel_efficiency=0.0  # 將在外部計算
            )
            
        except Exception as e:
            logger.error(f"❌ 優化決策綜合失敗: {e}")
            return self._create_fallback_decision(str(e), time.time() - start_time)
    
    def _calculate_parallel_efficiency(self, ai_responses: List[ParallelAIResponse]) -> float:
        """計算並行效率"""
        try:
            if not ai_responses:
                return 1.0
            
            # 計算順序執行時間（所有AI處理時間之和）
            sequential_time = sum(response.processing_time for response in ai_responses)
            
            # 計算並行執行時間（最長的AI處理時間）
            parallel_time = max(response.processing_time for response in ai_responses)
            
            # 計算效率比率
            if parallel_time > 0:
                efficiency = sequential_time / parallel_time
                return min(efficiency, len(ai_responses))  # 理論最大效率是AI數量
            else:
                return 1.0
                
        except Exception as e:
            logger.error(f"❌ 計算並行效率失敗: {e}")
            return 1.0
    
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
        
        return max(decision_weights, key=decision_weights.get)
    
    def _generate_reasoning(self, ai_responses: List[ParallelAIResponse], final_decision: str) -> str:
        """生成決策推理說明"""
        reasoning_parts = []
        
        for response in ai_responses:
            if response.success:
                reasoning_parts.append(f"{response.ai_role}: {response.response[:100]}...")
        
        reasoning = f"最終決策: {final_decision}\n\n" + "\n\n".join(reasoning_parts)
        return reasoning
    
    def _assess_risk_level(self, ai_responses: List[ParallelAIResponse], confidence: float) -> str:
        """評估風險等級"""
        if confidence >= 0.8:
            return "LOW"
        elif confidence >= 0.6:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _create_fallback_decision(self, error_message: str, processing_time: float) -> OptimizedDecision:
        """創建備用決策"""
        return OptimizedDecision(
            final_decision="HOLD",
            confidence=0.0,
            consensus_level=0.0,
            ai_responses=[],
            reasoning=f"系統錯誤，採用保守策略: {error_message}",
            risk_level="HIGH",
            timestamp=datetime.now(),
            total_processing_time=processing_time,
            parallel_efficiency=1.0
        )
    
    def _update_performance_stats(self, decision: OptimizedDecision, 
                                processing_time: float, parallel_execution: bool):
        """更新性能統計"""
        self.performance_stats["total_decisions"] += 1
        
        if decision.confidence > 0.5:
            self.performance_stats["successful_decisions"] += 1
        
        if parallel_execution:
            self.performance_stats["parallel_decisions"] += 1
            
            # 更新平均並行效率
            total_efficiency = (self.performance_stats["average_parallel_efficiency"] * 
                              (self.performance_stats["parallel_decisions"] - 1) + 
                              decision.parallel_efficiency)
            self.performance_stats["average_parallel_efficiency"] = total_efficiency / self.performance_stats["parallel_decisions"]
        
        # 更新平均處理時間
        total_time = (self.performance_stats["average_processing_time"] * 
                     (self.performance_stats["total_decisions"] - 1) + processing_time)
        self.performance_stats["average_processing_time"] = total_time / self.performance_stats["total_decisions"]
        
        # 計算速度提升
        if self.performance_stats["parallel_decisions"] > 0:
            parallel_avg = self.performance_stats["average_processing_time"]
            sequential_avg = parallel_avg * self.performance_stats["average_parallel_efficiency"]
            if parallel_avg > 0:
                self.performance_stats["speed_improvement"] = (sequential_avg - parallel_avg) / parallel_avg
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取性能統計"""
        return self.performance_stats.copy()
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """獲取優化報告"""
        stats = self.get_performance_stats()
        
        return {
            "optimization_summary": {
                "total_decisions": stats["total_decisions"],
                "parallel_decisions": stats["parallel_decisions"],
                "parallel_ratio": stats["parallel_decisions"] / max(stats["total_decisions"], 1),
                "average_processing_time": stats["average_processing_time"],
                "average_parallel_efficiency": stats["average_parallel_efficiency"],
                "speed_improvement": stats["speed_improvement"]
            },
            "performance_metrics": {
                "decisions_per_minute": 60 / max(stats["average_processing_time"], 1),
                "theoretical_max_efficiency": 3.0,  # 3個AI並行
                "actual_efficiency": stats["average_parallel_efficiency"],
                "efficiency_utilization": stats["average_parallel_efficiency"] / 3.0
            },
            "recommendations": self._generate_optimization_recommendations(stats)
        }
    
    def _generate_optimization_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """生成優化建議"""
        recommendations = []
        
        if stats["average_parallel_efficiency"] < 2.0:
            recommendations.append("考慮優化AI模型調用的並行度")
        
        if stats["average_processing_time"] > 30:
            recommendations.append("考慮使用更快的AI模型或減少token數量")
        
        if stats["speed_improvement"] < 0.5:
            recommendations.append("並行處理效果不明顯，檢查系統瓶頸")
        
        if not recommendations:
            recommendations.append("系統性能良好，繼續保持當前配置")
        
        return recommendations
    
    def __del__(self):
        """清理資源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)


# 創建全局並行AI管理器實例
def create_parallel_ai_manager(config_path: str = "config/ai_models_qwen7b.json") -> ParallelAIManager:
    """創建並行AI管理器實例"""
    return ParallelAIManager(config_path)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_parallel_ai():
        """測試並行AI功能"""
        print("🧪 測試並行AI系統...")
        
        # 創建並行AI管理器
        ai_manager = create_parallel_ai_manager()
        
        # 模擬市場數據
        test_market_data = {
            "current_price": 1500000,
            "price_change_1m": 0.5,
            "price_change_5m": 1.2,
            "volume_ratio": 1.1,
            "volatility_level": "中",
            "technical_indicators": {
                "rsi": 65,
                "macd": "金叉"
            }
        }
        
        # 執行並行分析
        start_time = time.time()
        decision = await ai_manager.analyze_market_parallel(test_market_data)
        end_time = time.time()
        
        print(f"✅ 並行決策完成:")
        print(f"最終決策: {decision.final_decision}")
        print(f"信心度: {decision.confidence:.2f}")
        print(f"共識水平: {decision.consensus_level:.2f}")
        print(f"風險等級: {decision.risk_level}")
        print(f"處理時間: {decision.total_processing_time:.2f}秒")
        print(f"並行效率: {decision.parallel_efficiency:.2f}x")
        
        # 顯示優化報告
        report = ai_manager.get_optimization_report()
        print(f"\n📊 優化報告:")
        print(f"平均處理時間: {report['optimization_summary']['average_processing_time']:.2f}秒")
        print(f"並行效率: {report['optimization_summary']['average_parallel_efficiency']:.2f}x")
        print(f"速度提升: {report['optimization_summary']['speed_improvement']:.1%}")
        print(f"建議: {report['recommendations']}")
    
    # 運行測試
    asyncio.run(test_parallel_ai())