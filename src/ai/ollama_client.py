#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama AI客戶端 - 用於本地AI推理和交易分析
整合到AImax系統中
"""

import ollama
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AIAnalysisResult:
    """AI分析結果"""
    analysis: str
    confidence: float
    reasoning: List[str]
    recommendation: str
    risk_level: str
    timestamp: datetime

class OllamaAIClient:
    """Ollama AI客戶端 - 專為AImax系統優化"""
    
    def __init__(self, model_name: str = "llama2:7b"):
        """
        初始化Ollama客戶端
        
        Args:
            model_name: 使用的AI模型名稱
        """
        self.model_name = model_name
        self.client = None
        self.is_connected = False
        
        # 針對AImax系統優化的提示詞模板
        self.system_prompts = {
            "market_scanner": """你是專業的市場掃描員。快速分析市場數據，識別交易機會。保持簡潔，專注關鍵信號。""",
            
            "deep_analyst": """你是資深技術分析師。基於市場數據進行技術分析，評估指標，提供簡潔的中文分析報告。""",
            
            "decision_maker": """你是交易決策者。基於分析報告做出交易決策：BUY、SELL或HOLD。提供清晰的中文決策理由。"""
        }
        
        self.logger = logging.getLogger(f"{__name__}.OllamaAIClient")
        self.logger.info(f"🤖 初始化Ollama AI客戶端，模型: {model_name}")
    
    def connect(self) -> bool:
        """連接到Ollama服務"""
        try:
            self.client = ollama.Client()
            
            # 測試連接
            models = self.client.list()
            
            # 檢查模型是否可用
            available_models = [model['name'] for model in models['models']]
            
            if self.model_name not in available_models:
                self.logger.error(f"❌ 模型 {self.model_name} 不可用")
                self.logger.info(f"可用模型: {available_models}")
                return False
            
            self.is_connected = True
            self.logger.info(f"✅ 成功連接到Ollama，模型: {self.model_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 連接Ollama失敗: {str(e)}")
            self.is_connected = False
            return False
    
    def analyze_market_data(self, market_data: Dict[str, Any], role: str = "market_scanner") -> AIAnalysisResult:
        """
        分析市場數據 - 支持AImax三AI角色
        
        Args:
            market_data: 市場數據字典
            role: AI角色 (market_scanner, deep_analyst, decision_maker)
            
        Returns:
            AIAnalysisResult: AI分析結果
        """
        if not self.is_connected:
            if not self.connect():
                raise ConnectionError("無法連接到Ollama服務")
        
        try:
            # 構建針對不同角色的分析提示詞
            market_prompt = self._build_role_specific_prompt(market_data, role)
            
            # 調用AI分析
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'system',
                        'content': self.system_prompts.get(role, self.system_prompts["market_scanner"])
                    },
                    {
                        'role': 'user',
                        'content': market_prompt
                    }
                ],
                options={
                    'temperature': 0.3 if role == "market_scanner" else 0.2 if role == "deep_analyst" else 0.1,
                    'top_p': 0.9,
                    'num_predict': 200 if role == "market_scanner" else 400 if role == "deep_analyst" else 300
                }
            )
            
            analysis_text = response['message']['content']
            
            # 解析AI回應
            result = self._parse_analysis_response(analysis_text, role)
            
            self.logger.info(f"✅ {role} AI分析完成: {result.recommendation}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ {role} AI分析失敗: {str(e)}")
            # 返回默認結果
            return AIAnalysisResult(
                analysis="分析失敗",
                confidence=0.0,
                reasoning=["AI分析服務不可用"],
                recommendation="HOLD",
                risk_level="HIGH",
                timestamp=datetime.now()
            )
    
    def _build_role_specific_prompt(self, market_data: Dict[str, Any], role: str) -> str:
        """構建針對不同AI角色的提示詞"""
        base_data = f"""
市場數據：
- 當前價格: {market_data.get('current_price', 'N/A')} TWD
- 價格變化: {market_data.get('price_change_1m', 'N/A')}%
- 成交量比率: {market_data.get('volume_ratio', 'N/A')}
- AI格式化數據: {market_data.get('ai_formatted_data', 'N/A')}
"""
        
        if role == "market_scanner":
            return f"""
{base_data}

作為市場掃描員，請快速識別：
1. 關鍵市場信號
2. 交易機會 (BUY/SELL/HOLD)
3. 信心度 (0-100)
保持簡潔明確。
"""
        
        elif role == "deep_analyst":
            return f"""
{base_data}

作為深度分析師，請提供：
1. 詳細技術分析
2. 市場趨勢評估
3. 風險等級 (LOW/MEDIUM/HIGH)
4. 分析理由
"""
        
        elif role == "decision_maker":
            return f"""
{base_data}

作為最終決策者，請提供：
1. 最終交易決策 (BUY/SELL/HOLD)
2. 決策信心度
3. 清晰的決策理由
4. 風險評估
"""
        
        return base_data
    
    def _parse_analysis_response(self, response_text: str, role: str) -> AIAnalysisResult:
        """解析AI分析回應 - 針對不同角色優化"""
        lines = response_text.strip().split('\n')
        
        # 提取關鍵信息
        analysis = response_text
        confidence = 70.0  # 默認值
        recommendation = "HOLD"  # 默認值
        risk_level = "MEDIUM"  # 默認值
        reasoning = [response_text]
        
        # 根據角色調整解析邏輯
        for line in lines:
            line = line.strip().lower()
            
            # 提取交易建議
            if 'buy' in line and 'sell' not in line:
                recommendation = "BUY"
            elif 'sell' in line and 'buy' not in line:
                recommendation = "SELL"
            elif 'hold' in line:
                recommendation = "HOLD"
            
            # 提取風險等級
            if 'high risk' in line or '高風險' in line:
                risk_level = "HIGH"
            elif 'low risk' in line or '低風險' in line:
                risk_level = "LOW"
            elif 'medium risk' in line or '中風險' in line:
                risk_level = "MEDIUM"
            
            # 提取信心度
            if '信心度' in line or 'confidence' in line:
                import re
                numbers = re.findall(r'\d+', line)
                if numbers:
                    confidence = min(100, max(0, float(numbers[0])))
        
        # 根據角色調整默認信心度
        if role == "market_scanner":
            confidence = min(confidence, 80)  # 掃描員信心度上限80
        elif role == "deep_analyst":
            confidence = min(confidence + 10, 90)  # 分析師信心度+10
        elif role == "decision_maker":
            confidence = min(confidence + 5, 95)  # 決策者信心度+5
        
        return AIAnalysisResult(
            analysis=analysis,
            confidence=confidence,
            reasoning=reasoning,
            recommendation=recommendation,
            risk_level=risk_level,
            timestamp=datetime.now()
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型信息"""
        return {
            "model_name": self.model_name,
            "is_connected": self.is_connected,
            "capabilities": ["market_scanning", "deep_analysis", "decision_making"],
            "optimized_for": "AImax_trading_system"
        }


def create_ollama_client(model_name: str = "llama2:7b") -> OllamaAIClient:
    """創建Ollama AI客戶端"""
    return OllamaAIClient(model_name)


# 測試代碼
if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO)
    
    # 創建客戶端
    ai_client = create_ollama_client()
    
    # 測試連接
    if ai_client.connect():
        print("✅ Ollama連接成功")
        
        # 測試三AI角色分析
        test_market_data = {
            "current_price": 1500000,
            "price_change_1m": 0.5,
            "volume_ratio": 1.1,
            "ai_formatted_data": "測試數據"
        }
        
        roles = ["market_scanner", "deep_analyst", "decision_maker"]
        for role in roles:
            result = ai_client.analyze_market_data(test_market_data, role)
            print(f"🤖 {role}: {result.recommendation} (信心度: {result.confidence}%)")
        
    else:
        print("❌ Ollama連接失敗")