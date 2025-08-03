#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版AI增強DCA時機選擇器
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TimingSignal(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    WAIT = "wait"
    SKIP = "skip"

class MarketPhase(Enum):
    ACCUMULATION = "accumulation"
    MARKUP = "markup"
    DISTRIBUTION = "distribution"
    MARKDOWN = "markdown"

@dataclass
class TimingAnalysis:
    pair: str
    timestamp: datetime
    signal: TimingSignal
    confidence: float
    market_phase: MarketPhase
    recommended_amount_multiplier: float
    reasoning: str
    risk_assessment: float
    opportunity_score: float

class SimpleAIDCATiming:
    """簡化版AI增強DCA時機選擇器"""
    
    def __init__(self, ai_coordinator=None):
        self.ai_coordinator = ai_coordinator
        self.timing_history = []
        logger.info("🎯 簡化版AI增強DCA時機選擇器初始化完成")
    
    async def analyze_dca_timing(self, pair: str, market_data: Dict[str, Any], 
                               current_dca_config: Dict[str, Any]) -> TimingAnalysis:
        """分析DCA投資時機"""
        logger.info(f"🎯 開始AI增強DCA時機分析: {pair}")
        
        try:
            # 技術指標分析
            rsi = market_data.get('rsi_14', 50)
            price_change_24h = market_data.get('price_change_24h', 0)
            price_change_7d = market_data.get('price_change_7d', 0)
            volatility = market_data.get('volatility', 0.02)
            
            # 市場階段識別
            if price_change_7d < -0.1 and rsi < 40:
                market_phase = MarketPhase.MARKDOWN
            elif price_change_7d < -0.05 and rsi < 50:
                market_phase = MarketPhase.ACCUMULATION
            elif price_change_7d > 0.05 and rsi > 50:
                market_phase = MarketPhase.MARKUP
            else:
                market_phase = MarketPhase.ACCUMULATION
            
            # 風險機會評估
            risk_score = min(1.0, abs(price_change_24h) * 10 + volatility * 20) / 2
            opportunity_score = 0.5
            
            if price_change_7d < -0.05:
                opportunity_score = min(1.0, abs(price_change_7d) * 5)
            
            # 決策邏輯
            if rsi < 30 and price_change_24h < -0.05:
                signal = TimingSignal.STRONG_BUY
                amount_multiplier = 1.8
                confidence = 0.8
                reasoning = "RSI超賣且價格大跌，強烈買入機會"
            elif rsi < 40 and price_change_24h < -0.02:
                signal = TimingSignal.BUY
                amount_multiplier = 1.3
                confidence = 0.7
                reasoning = "RSI偏低且價格下跌，買入機會"
            elif rsi > 70 or price_change_24h > 0.05:
                signal = TimingSignal.WAIT
                amount_multiplier = 0.5
                confidence = 0.6
                reasoning = "RSI超買或價格大漲，等待回調"
            else:
                signal = TimingSignal.NEUTRAL
                amount_multiplier = 1.0
                confidence = 0.5
                reasoning = "市場中性，正常DCA投資"
            
            # 創建分析結果
            timing_analysis = TimingAnalysis(
                pair=pair,
                timestamp=datetime.now(),
                signal=signal,
                confidence=confidence,
                market_phase=market_phase,
                recommended_amount_multiplier=amount_multiplier,
                reasoning=reasoning,
                risk_assessment=risk_score,
                opportunity_score=opportunity_score
            )
            
            # 更新歷史
            self.timing_history.append(timing_analysis)
            if len(self.timing_history) > 100:
                self.timing_history = self.timing_history[-50:]
            
            logger.info(f"✅ DCA時機分析完成: {signal.value} (信心度: {confidence:.2f})")
            
            return timing_analysis
            
        except Exception as e:
            logger.error(f"❌ DCA時機分析失敗: {e}")
            return TimingAnalysis(
                pair=pair,
                timestamp=datetime.now(),
                signal=TimingSignal.NEUTRAL,
                confidence=0.5,
                market_phase=MarketPhase.ACCUMULATION,
                recommended_amount_multiplier=1.0,
                reasoning="系統錯誤，採用保守策略",
                risk_assessment=0.5,
                opportunity_score=0.5
            )
    
    def get_timing_performance(self) -> Dict[str, Any]:
        """獲取時機性能統計"""
        if not self.timing_history:
            return {
                'total_analyses': 0,
                'avg_confidence': 0.0,
                'signal_distribution': {}
            }
        
        signal_counts = {}
        for analysis in self.timing_history:
            signal = analysis.signal.value
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
        
        avg_confidence = sum(t.confidence for t in self.timing_history) / len(self.timing_history)
        
        return {
            'total_analyses': len(self.timing_history),
            'avg_confidence': avg_confidence,
            'signal_distribution': signal_counts
        }
    
    def get_timing_recommendations(self, pair: str) -> Dict[str, Any]:
        """獲取時機建議"""
        recent_analyses = [a for a in self.timing_history[-10:] if a.pair == pair]
        
        if not recent_analyses:
            return {
                'recommendation': '無足夠歷史數據',
                'suggested_frequency': 'daily',
                'suggested_amount_adjustment': 1.0
            }
        
        recent_signals = [a.signal for a in recent_analyses]
        strong_buy_count = sum(1 for s in recent_signals if s == TimingSignal.STRONG_BUY)
        buy_count = sum(1 for s in recent_signals if s == TimingSignal.BUY)
        
        if strong_buy_count >= 2:
            return {
                'recommendation': '市場呈現強烈買入機會，建議增加投資',
                'suggested_frequency': 'daily',
                'suggested_amount_adjustment': 1.5
            }
        elif buy_count >= 3:
            return {
                'recommendation': '市場呈現買入機會，建議正常投資',
                'suggested_frequency': 'daily',
                'suggested_amount_adjustment': 1.2
            }
        else:
            return {
                'recommendation': '市場中性，建議正常DCA投資',
                'suggested_frequency': 'daily',
                'suggested_amount_adjustment': 1.0
            }


def create_simple_ai_dca_timing(ai_coordinator=None):
    """創建簡化版AI增強DCA時機選擇器"""
    return SimpleAIDCATiming(ai_coordinator)


# 測試代碼
if __name__ == "__main__":
    async def test():
        timing_selector = create_simple_ai_dca_timing()
        
        test_data = {
            'rsi_14': 35,
            'price_change_24h': -0.05,
            'price_change_7d': -0.08,
            'volatility': 0.06
        }
        
        result = await timing_selector.analyze_dca_timing("BTCTWD", test_data, {})
        
        print(f"信號: {result.signal.value}")
        print(f"信心度: {result.confidence:.2f}")
        print(f"市場階段: {result.market_phase.value}")
        print(f"建議倍數: {result.recommended_amount_multiplier:.2f}")
        print(f"理由: {result.reasoning}")
    
    asyncio.run(test())