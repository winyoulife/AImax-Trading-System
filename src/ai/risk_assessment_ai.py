#!/usr/bin/env python3
"""
風險評估AI模型
實現任務2.1: 部署風險評估AI模型
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd

try:
    from ..data.multi_pair_data_manager import MultiPairDataManager
    from ..data.dynamic_config_system import get_dynamic_config_manager
except ImportError:
    # 用於直接運行測試
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from data.multi_pair_data_manager import MultiPairDataManager
    from data.dynamic_config_system import get_dynamic_config_manager

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """風險等級"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class RiskType(Enum):
    """風險類型"""
    MARKET_RISK = "market_risk"          # 市場風險
    LIQUIDITY_RISK = "liquidity_risk"    # 流動性風險
    VOLATILITY_RISK = "volatility_risk"  # 波動性風險
    CORRELATION_RISK = "correlation_risk" # 相關性風險
    POSITION_RISK = "position_risk"      # 倉位風險
    TECHNICAL_RISK = "technical_risk"    # 技術風險

@dataclass
class RiskMetrics:
    """風險指標"""
    pair: str
    timestamp: datetime
    
    # 基本風險指標
    volatility: float           # 波動率
    var_95: float              # 95%置信度VaR
    max_drawdown: float        # 最大回撤
    sharpe_ratio: float        # 夏普比率
    
    # 市場風險指標
    beta: float                # 貝塔係數
    correlation_btc: float     # 與BTC相關性
    liquidity_score: float     # 流動性評分
    
    # 技術風險指標
    rsi: float                 # RSI指標
    macd_signal: str           # MACD信號
    bollinger_position: float  # 布林帶位置
    
    # 綜合風險評估
    overall_risk_level: RiskLevel
    risk_score: float          # 0-100風險評分
    confidence: float          # 評估信心度

@dataclass
class RiskAssessmentResult:
    """風險評估結果"""
    pair: str
    timestamp: datetime
    
    # 風險指標
    risk_metrics: RiskMetrics
    
    # 風險分析
    risk_factors: Dict[RiskType, float]  # 各類風險因子
    risk_warnings: List[str]             # 風險警告
    risk_recommendations: List[str]      # 風險建議
    
    # 倉位建議
    recommended_position_size: float     # 建議倉位大小
    max_position_size: float            # 最大倉位限制
    stop_loss_suggestion: float         # 建議止損位
    
    # AI評估
    ai_confidence: float                # AI信心度
    assessment_reasoning: str           # 評估推理
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'pair': self.pair,
            'timestamp': self.timestamp.isoformat(),
            'risk_metrics': asdict(self.risk_metrics),
            'risk_factors': {k.value: v for k, v in self.risk_factors.items()},
            'risk_warnings': self.risk_warnings,
            'risk_recommendations': self.risk_recommendations,
            'recommended_position_size': self.recommended_position_size,
            'max_position_size': self.max_position_size,
            'stop_loss_suggestion': self.stop_loss_suggestion,
            'ai_confidence': self.ai_confidence,
            'assessment_reasoning': self.assessment_reasoning
        }

class RiskAssessmentAI:
    """風險評估AI模型"""
    
    def __init__(self, model_name: str = "qwen2.5:7b"):
        self.model_name = model_name
        self.data_manager = None
        self.config_manager = get_dynamic_config_manager()
        
        # 風險評估參數
        self.risk_thresholds = {
            RiskLevel.VERY_LOW: (0, 20),
            RiskLevel.LOW: (20, 40),
            RiskLevel.MEDIUM: (40, 60),
            RiskLevel.HIGH: (60, 80),
            RiskLevel.VERY_HIGH: (80, 100)
        }
        
        # 風險權重配置
        self.risk_weights = {
            RiskType.MARKET_RISK: 0.25,
            RiskType.LIQUIDITY_RISK: 0.15,
            RiskType.VOLATILITY_RISK: 0.20,
            RiskType.CORRELATION_RISK: 0.15,
            RiskType.POSITION_RISK: 0.15,
            RiskType.TECHNICAL_RISK: 0.10
        }
        
        logger.info(f"🤖 風險評估AI初始化完成 - 模型: {model_name}")
    
    def set_data_manager(self, data_manager: MultiPairDataManager):
        """設置數據管理器"""
        self.data_manager = data_manager
        logger.info("📊 風險評估AI已連接數據管理器")
    
    async def assess_risk(self, pair: str, timeframe: str = '5m', 
                         lookback_periods: int = 100) -> RiskAssessmentResult:
        """評估交易對風險"""
        try:
            logger.info(f"🔍 開始評估 {pair} 風險...")
            
            # 獲取市場數據
            market_data = await self._get_market_data(pair, timeframe, lookback_periods)
            if market_data.empty:
                raise ValueError(f"無法獲取 {pair} 的市場數據")
            
            # 計算風險指標
            risk_metrics = self._calculate_risk_metrics(pair, market_data)
            
            # 分析各類風險因子
            risk_factors = self._analyze_risk_factors(pair, market_data, risk_metrics)
            
            # 生成風險警告和建議
            risk_warnings, risk_recommendations = self._generate_risk_insights(
                pair, risk_metrics, risk_factors
            )
            
            # 計算倉位建議
            position_suggestions = self._calculate_position_suggestions(
                pair, risk_metrics, risk_factors
            )
            
            # AI推理評估
            ai_assessment = await self._ai_risk_reasoning(
                pair, risk_metrics, risk_factors, market_data
            )
            
            # 構建評估結果
            result = RiskAssessmentResult(
                pair=pair,
                timestamp=datetime.now(),
                risk_metrics=risk_metrics,
                risk_factors=risk_factors,
                risk_warnings=risk_warnings,
                risk_recommendations=risk_recommendations,
                recommended_position_size=position_suggestions['recommended'],
                max_position_size=position_suggestions['max_allowed'],
                stop_loss_suggestion=position_suggestions['stop_loss'],
                ai_confidence=ai_assessment['confidence'],
                assessment_reasoning=ai_assessment['reasoning']
            )
            
            logger.info(f"✅ {pair} 風險評估完成 - 風險等級: {risk_metrics.overall_risk_level.value}")
            return result
            
        except Exception as e:
            logger.error(f"❌ {pair} 風險評估失敗: {e}")
            raise  
  
    async def _get_market_data(self, pair: str, timeframe: str, 
                              periods: int) -> pd.DataFrame:
        """獲取市場數據"""
        try:
            if self.data_manager:
                # 從數據管理器獲取數據
                data = self.data_manager.get_multi_pair_historical_data(
                    pairs=[pair],
                    timeframe=timeframe,
                    limit=periods
                )
                return data.get(pair, pd.DataFrame())
            else:
                # 模擬數據用於測試
                dates = pd.date_range(end=datetime.now(), periods=periods, freq='5T')
                np.random.seed(42)
                
                base_price = 1500000 if 'BTC' in pair else 75000
                price_changes = np.random.normal(0, 0.02, periods)
                prices = base_price * np.cumprod(1 + price_changes)
                
                return pd.DataFrame({
                    'timestamp': dates,
                    'open': prices * (1 + np.random.normal(0, 0.001, periods)),
                    'high': prices * (1 + np.abs(np.random.normal(0, 0.005, periods))),
                    'low': prices * (1 - np.abs(np.random.normal(0, 0.005, periods))),
                    'close': prices,
                    'volume': np.random.uniform(0.5, 2.0, periods)
                })
                
        except Exception as e:
            logger.error(f"❌ 獲取 {pair} 市場數據失敗: {e}")
            return pd.DataFrame()
    
    def _calculate_risk_metrics(self, pair: str, data: pd.DataFrame) -> RiskMetrics:
        """計算風險指標"""
        try:
            prices = data['close'].values
            returns = np.diff(np.log(prices))
            
            # 基本風險指標
            volatility = np.std(returns) * np.sqrt(252)  # 年化波動率
            var_95 = np.percentile(returns, 5)  # 95% VaR
            
            # 計算最大回撤
            cumulative = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = np.min(drawdown)
            
            # 夏普比率
            mean_return = np.mean(returns)
            sharpe_ratio = mean_return / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
            
            # 技術指標
            rsi = self._calculate_rsi(prices)
            macd_signal = self._calculate_macd_signal(prices)
            bollinger_position = self._calculate_bollinger_position(prices)
            
            # 市場風險指標（簡化計算）
            beta = 1.0  # 簡化為1.0，實際應與市場指數計算
            correlation_btc = 0.8 if 'BTC' not in pair else 1.0  # 簡化
            liquidity_score = min(np.mean(data['volume']) / 1.0, 100)  # 簡化流動性評分
            
            # 計算綜合風險評分
            risk_score = self._calculate_overall_risk_score(
                volatility, abs(var_95), abs(max_drawdown), 
                abs(sharpe_ratio), rsi, liquidity_score
            )
            
            # 確定風險等級
            overall_risk_level = self._determine_risk_level(risk_score)
            
            return RiskMetrics(
                pair=pair,
                timestamp=datetime.now(),
                volatility=volatility,
                var_95=var_95,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                beta=beta,
                correlation_btc=correlation_btc,
                liquidity_score=liquidity_score,
                rsi=rsi,
                macd_signal=macd_signal,
                bollinger_position=bollinger_position,
                overall_risk_level=overall_risk_level,
                risk_score=risk_score,
                confidence=0.85  # 基於數據質量的信心度
            )
            
        except Exception as e:
            logger.error(f"❌ 計算 {pair} 風險指標失敗: {e}")
            raise
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """計算RSI指標"""
        try:
            if len(prices) < period + 1:
                return 50.0
            
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi
            
        except Exception:
            return 50.0
    
    def _calculate_macd_signal(self, prices: np.ndarray) -> str:
        """計算MACD信號"""
        try:
            if len(prices) < 26:
                return "neutral"
            
            # 簡化的MACD計算
            ema_12 = self._calculate_ema(prices, 12)
            ema_26 = self._calculate_ema(prices, 26)
            
            macd_line = ema_12[-1] - ema_26[-1]
            macd_prev = ema_12[-2] - ema_26[-2] if len(ema_12) > 1 else macd_line
            
            if macd_line > 0 and macd_line > macd_prev:
                return "bullish"
            elif macd_line < 0 and macd_line < macd_prev:
                return "bearish"
            else:
                return "neutral"
                
        except Exception:
            return "neutral"
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """計算指數移動平均"""
        alpha = 2 / (period + 1)
        ema = np.zeros_like(prices)
        ema[0] = prices[0]
        
        for i in range(1, len(prices)):
            ema[i] = alpha * prices[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    def _calculate_bollinger_position(self, prices: np.ndarray, period: int = 20) -> float:
        """計算布林帶位置"""
        try:
            if len(prices) < period:
                return 0.5
            
            recent_prices = prices[-period:]
            mean_price = np.mean(recent_prices)
            std_price = np.std(recent_prices)
            
            current_price = prices[-1]
            upper_band = mean_price + 2 * std_price
            lower_band = mean_price - 2 * std_price
            
            if upper_band == lower_band:
                return 0.5
            
            position = (current_price - lower_band) / (upper_band - lower_band)
            return max(0, min(1, position))
            
        except Exception:
            return 0.5
    
    def _calculate_overall_risk_score(self, volatility: float, var_95: float, 
                                    max_drawdown: float, sharpe_ratio: float,
                                    rsi: float, liquidity_score: float) -> float:
        """計算綜合風險評分"""
        try:
            # 標準化各項指標到0-100分
            vol_score = min(volatility * 100, 100)  # 波動率評分
            var_score = min(var_95 * 1000, 100)    # VaR評分
            dd_score = min(abs(max_drawdown) * 100, 100)  # 回撤評分
            
            # RSI極端值風險
            rsi_risk = 0
            if rsi > 80 or rsi < 20:
                rsi_risk = min(abs(rsi - 50), 30)
            
            # 流動性風險（流動性越低風險越高）
            liquidity_risk = max(0, 50 - liquidity_score)
            
            # 夏普比率風險（負值或過低表示風險高）
            sharpe_risk = max(0, 30 - sharpe_ratio * 10) if sharpe_ratio < 3 else 0
            
            # 加權計算總風險評分
            total_score = (
                vol_score * 0.3 +
                var_score * 0.2 +
                dd_score * 0.2 +
                rsi_risk * 0.1 +
                liquidity_risk * 0.1 +
                sharpe_risk * 0.1
            )
            
            return min(100, max(0, total_score))
            
        except Exception as e:
            logger.error(f"❌ 計算風險評分失敗: {e}")
            return 50.0
    
    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """確定風險等級"""
        for level, (min_score, max_score) in self.risk_thresholds.items():
            if min_score <= risk_score < max_score:
                return level
        return RiskLevel.VERY_HIGH    

    def _analyze_risk_factors(self, pair: str, data: pd.DataFrame, 
                            metrics: RiskMetrics) -> Dict[RiskType, float]:
        """分析各類風險因子"""
        try:
            risk_factors = {}
            
            # 市場風險
            market_risk = min(100, metrics.volatility * 50 + abs(metrics.var_95) * 200)
            risk_factors[RiskType.MARKET_RISK] = market_risk
            
            # 流動性風險
            liquidity_risk = max(0, 100 - metrics.liquidity_score)
            risk_factors[RiskType.LIQUIDITY_RISK] = liquidity_risk
            
            # 波動性風險
            volatility_risk = min(100, metrics.volatility * 100)
            risk_factors[RiskType.VOLATILITY_RISK] = volatility_risk
            
            # 相關性風險
            correlation_risk = abs(metrics.correlation_btc) * 50  # 高相關性增加系統性風險
            risk_factors[RiskType.CORRELATION_RISK] = correlation_risk
            
            # 倉位風險（基於配置）
            config = self.config_manager.get_config(pair)
            if config:
                position_risk = config.max_position_size * 100  # 倉位越大風險越高
            else:
                position_risk = 50  # 默認中等風險
            risk_factors[RiskType.POSITION_RISK] = position_risk
            
            # 技術風險
            technical_risk = 0
            if metrics.rsi > 80:  # 超買
                technical_risk += 30
            elif metrics.rsi < 20:  # 超賣
                technical_risk += 20
            
            if metrics.bollinger_position > 0.9:  # 接近上軌
                technical_risk += 20
            elif metrics.bollinger_position < 0.1:  # 接近下軌
                technical_risk += 15
            
            risk_factors[RiskType.TECHNICAL_RISK] = min(100, technical_risk)
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"❌ 分析 {pair} 風險因子失敗: {e}")
            return {risk_type: 50.0 for risk_type in RiskType}
    
    def _generate_risk_insights(self, pair: str, metrics: RiskMetrics, 
                              risk_factors: Dict[RiskType, float]) -> Tuple[List[str], List[str]]:
        """生成風險警告和建議"""
        warnings = []
        recommendations = []
        
        try:
            # 基於風險等級生成警告
            if metrics.overall_risk_level == RiskLevel.VERY_HIGH:
                warnings.append(f"{pair} 風險極高，建議暫停交易")
                recommendations.append("立即減少倉位或停止新開倉")
            elif metrics.overall_risk_level == RiskLevel.HIGH:
                warnings.append(f"{pair} 風險較高，需要謹慎操作")
                recommendations.append("降低倉位大小，加強風險控制")
            
            # 基於具體風險因子生成建議
            if risk_factors[RiskType.VOLATILITY_RISK] > 70:
                warnings.append("市場波動性過高")
                recommendations.append("縮小止損距離，降低單筆風險")
            
            if risk_factors[RiskType.LIQUIDITY_RISK] > 60:
                warnings.append("流動性不足")
                recommendations.append("避免大額交易，分批進出場")
            
            if metrics.rsi > 80:
                warnings.append("技術指標顯示超買")
                recommendations.append("考慮減倉或等待回調")
            elif metrics.rsi < 20:
                warnings.append("技術指標顯示超賣")
                recommendations.append("可考慮逢低建倉，但需控制倉位")
            
            if abs(metrics.max_drawdown) > 0.15:
                warnings.append("歷史最大回撤過大")
                recommendations.append("檢討策略參數，加強止損設置")
            
            # 如果沒有特殊風險，給出正面建議
            if not warnings:
                recommendations.append("當前風險水平可接受，可正常交易")
            
            return warnings, recommendations
            
        except Exception as e:
            logger.error(f"❌ 生成 {pair} 風險洞察失敗: {e}")
            return ["風險分析異常"], ["建議人工檢查"]
    
    def _calculate_position_suggestions(self, pair: str, metrics: RiskMetrics, 
                                      risk_factors: Dict[RiskType, float]) -> Dict[str, float]:
        """計算倉位建議"""
        try:
            # 基礎倉位大小（基於風險等級）
            base_position = {
                RiskLevel.VERY_LOW: 0.15,
                RiskLevel.LOW: 0.12,
                RiskLevel.MEDIUM: 0.08,
                RiskLevel.HIGH: 0.05,
                RiskLevel.VERY_HIGH: 0.02
            }.get(metrics.overall_risk_level, 0.08)
            
            # 基於波動率調整
            volatility_adjustment = max(0.5, 1 - metrics.volatility)
            adjusted_position = base_position * volatility_adjustment
            
            # 基於流動性調整
            liquidity_adjustment = min(1.0, metrics.liquidity_score / 50)
            final_position = adjusted_position * liquidity_adjustment
            
            # 獲取配置限制
            config = self.config_manager.get_config(pair)
            if config:
                max_allowed = config.max_position_size
                stop_loss_base = config.stop_loss_percent
            else:
                max_allowed = 0.1
                stop_loss_base = 0.08
            
            # 確保不超過配置限制
            recommended_position = min(final_position, max_allowed)
            
            # 基於風險調整止損
            risk_multiplier = 1 + (metrics.risk_score / 100)
            suggested_stop_loss = stop_loss_base * risk_multiplier
            
            return {
                'recommended': round(recommended_position, 4),
                'max_allowed': max_allowed,
                'stop_loss': round(suggested_stop_loss, 4)
            }
            
        except Exception as e:
            logger.error(f"❌ 計算 {pair} 倉位建議失敗: {e}")
            return {
                'recommended': 0.05,
                'max_allowed': 0.1,
                'stop_loss': 0.08
            }
    
    async def _ai_risk_reasoning(self, pair: str, metrics: RiskMetrics, 
                               risk_factors: Dict[RiskType, float], 
                               data: pd.DataFrame) -> Dict[str, Any]:
        """AI風險推理評估"""
        try:
            # 構建風險分析提示詞
            prompt = self._build_risk_assessment_prompt(pair, metrics, risk_factors, data)
            
            # 調用AI模型進行推理（這裡模擬AI響應）
            ai_response = await self._call_ai_model(prompt)
            
            # 解析AI響應
            reasoning = ai_response.get('reasoning', '基於技術指標和風險因子的綜合分析')
            confidence = ai_response.get('confidence', 0.75)
            
            return {
                'reasoning': reasoning,
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"❌ AI風險推理失敗: {e}")
            return {
                'reasoning': '風險評估基於量化指標計算',
                'confidence': 0.6
            }
    
    def _build_risk_assessment_prompt(self, pair: str, metrics: RiskMetrics, 
                                    risk_factors: Dict[RiskType, float], 
                                    data: pd.DataFrame) -> str:
        """構建風險評估提示詞"""
        try:
            current_price = data['close'].iloc[-1] if not data.empty else 0
            price_change = ((data['close'].iloc[-1] / data['close'].iloc[-2] - 1) * 100 
                          if len(data) > 1 else 0)
            
            prompt = f"""
你是一個專業的加密貨幣風險評估專家。請分析以下交易對的風險狀況：

交易對: {pair}
當前價格: {current_price:,.2f}
24小時變化: {price_change:+.2f}%

風險指標:
- 波動率: {metrics.volatility:.4f} ({metrics.volatility*100:.2f}%)
- VaR(95%): {metrics.var_95:.4f}
- 最大回撤: {metrics.max_drawdown:.4f} ({metrics.max_drawdown*100:.2f}%)
- 夏普比率: {metrics.sharpe_ratio:.2f}
- RSI: {metrics.rsi:.1f}
- MACD信號: {metrics.macd_signal}
- 布林帶位置: {metrics.bollinger_position:.2f}
- 流動性評分: {metrics.liquidity_score:.1f}

風險因子分析:
- 市場風險: {risk_factors[RiskType.MARKET_RISK]:.1f}/100
- 流動性風險: {risk_factors[RiskType.LIQUIDITY_RISK]:.1f}/100
- 波動性風險: {risk_factors[RiskType.VOLATILITY_RISK]:.1f}/100
- 相關性風險: {risk_factors[RiskType.CORRELATION_RISK]:.1f}/100
- 倉位風險: {risk_factors[RiskType.POSITION_RISK]:.1f}/100
- 技術風險: {risk_factors[RiskType.TECHNICAL_RISK]:.1f}/100

綜合風險等級: {metrics.overall_risk_level.value}
風險評分: {metrics.risk_score:.1f}/100

請提供:
1. 風險評估的詳細推理
2. 主要風險點識別
3. 交易建議
4. 評估信心度(0-1)

請以JSON格式回應，包含reasoning和confidence字段。
"""
            return prompt
            
        except Exception as e:
            logger.error(f"❌ 構建風險評估提示詞失敗: {e}")
            return f"請評估{pair}的交易風險"
    
    async def _call_ai_model(self, prompt: str) -> Dict[str, Any]:
        """調用AI模型（模擬實現）"""
        try:
            # 這裡應該調用實際的AI模型API（如Ollama）
            # 目前使用模擬響應
            await asyncio.sleep(0.1)  # 模擬AI處理時間
            
            # 模擬AI響應
            return {
                'reasoning': '基於當前市場數據和技術指標，該交易對呈現中等風險水平。波動率處於合理範圍，但需要關注流動性變化和技術指標信號。建議採用適中的倉位管理策略。',
                'confidence': 0.78
            }
            
        except Exception as e:
            logger.error(f"❌ 調用AI模型失敗: {e}")
            return {
                'reasoning': '風險評估基於量化模型計算',
                'confidence': 0.6
            }  
  
    async def assess_multi_pair_risk(self, pairs: List[str], 
                                   timeframe: str = '5m') -> Dict[str, RiskAssessmentResult]:
        """評估多個交易對的風險"""
        try:
            logger.info(f"🔍 開始評估 {len(pairs)} 個交易對的風險...")
            
            results = {}
            
            # 並行評估多個交易對
            tasks = []
            for pair in pairs:
                task = self.assess_risk(pair, timeframe)
                tasks.append(task)
            
            # 等待所有評估完成
            assessments = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果
            for i, assessment in enumerate(assessments):
                pair = pairs[i]
                if isinstance(assessment, Exception):
                    logger.error(f"❌ {pair} 風險評估失敗: {assessment}")
                else:
                    results[pair] = assessment
            
            # 分析交易對間的相關性風險
            correlation_analysis = self._analyze_cross_pair_correlation(results)
            
            # 更新相關性風險
            for pair, result in results.items():
                if pair in correlation_analysis:
                    result.risk_factors[RiskType.CORRELATION_RISK] = correlation_analysis[pair]
            
            logger.info(f"✅ 完成 {len(results)} 個交易對的風險評估")
            return results
            
        except Exception as e:
            logger.error(f"❌ 多交易對風險評估失敗: {e}")
            return {}
    
    def _analyze_cross_pair_correlation(self, results: Dict[str, RiskAssessmentResult]) -> Dict[str, float]:
        """分析交易對間相關性風險"""
        try:
            correlation_risks = {}
            
            pairs = list(results.keys())
            
            for pair in pairs:
                correlation_risk = 0
                
                # 計算與其他交易對的相關性風險
                for other_pair in pairs:
                    if pair != other_pair:
                        # 簡化的相關性計算（實際應基於價格數據）
                        if 'BTC' in pair and 'BTC' in other_pair:
                            correlation_risk += 20  # BTC相關對風險較高
                        elif pair[:3] == other_pair[:3]:  # 同一基礎貨幣
                            correlation_risk += 15
                        else:
                            correlation_risk += 5  # 基礎相關性
                
                correlation_risks[pair] = min(100, correlation_risk)
            
            return correlation_risks
            
        except Exception as e:
            logger.error(f"❌ 分析交叉相關性失敗: {e}")
            return {}
    
    def get_portfolio_risk_summary(self, assessments: Dict[str, RiskAssessmentResult]) -> Dict[str, Any]:
        """獲取組合風險摘要"""
        try:
            if not assessments:
                return {}
            
            # 計算組合風險指標
            total_pairs = len(assessments)
            risk_levels = [result.risk_metrics.overall_risk_level for result in assessments.values()]
            risk_scores = [result.risk_metrics.risk_score for result in assessments.values()]
            
            # 風險等級分布
            risk_distribution = {}
            for level in RiskLevel:
                count = sum(1 for r in risk_levels if r == level)
                risk_distribution[level.value] = count
            
            # 平均風險指標
            avg_risk_score = np.mean(risk_scores)
            max_risk_score = np.max(risk_scores)
            min_risk_score = np.min(risk_scores)
            
            # 高風險交易對
            high_risk_pairs = [
                result.pair for result in assessments.values()
                if result.risk_metrics.overall_risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]
            ]
            
            # 組合建議倉位
            total_recommended_position = sum(
                result.recommended_position_size for result in assessments.values()
            )
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_pairs': total_pairs,
                'risk_distribution': risk_distribution,
                'average_risk_score': round(avg_risk_score, 2),
                'max_risk_score': round(max_risk_score, 2),
                'min_risk_score': round(min_risk_score, 2),
                'high_risk_pairs': high_risk_pairs,
                'total_recommended_position': round(total_recommended_position, 4),
                'portfolio_risk_level': self._determine_portfolio_risk_level(avg_risk_score),
                'diversification_score': self._calculate_diversification_score(assessments)
            }
            
        except Exception as e:
            logger.error(f"❌ 生成組合風險摘要失敗: {e}")
            return {}
    
    def _determine_portfolio_risk_level(self, avg_risk_score: float) -> str:
        """確定組合風險等級"""
        if avg_risk_score < 30:
            return "低風險"
        elif avg_risk_score < 50:
            return "中低風險"
        elif avg_risk_score < 70:
            return "中等風險"
        elif avg_risk_score < 85:
            return "中高風險"
        else:
            return "高風險"
    
    def _calculate_diversification_score(self, assessments: Dict[str, RiskAssessmentResult]) -> float:
        """計算分散化評分"""
        try:
            if len(assessments) < 2:
                return 0.0
            
            # 基於交易對數量的基礎分散化
            pair_count_score = min(len(assessments) / 6, 1.0) * 40
            
            # 基於風險等級分散的評分
            risk_levels = [result.risk_metrics.overall_risk_level for result in assessments.values()]
            unique_risk_levels = len(set(risk_levels))
            risk_diversity_score = (unique_risk_levels / len(RiskLevel)) * 30
            
            # 基於相關性的分散化評分
            correlation_score = 30  # 簡化為固定值
            
            total_score = pair_count_score + risk_diversity_score + correlation_score
            return round(min(100, total_score), 2)
            
        except Exception:
            return 50.0


# 全局風險評估AI實例
_risk_assessment_ai = None

def get_risk_assessment_ai() -> RiskAssessmentAI:
    """獲取全局風險評估AI實例"""
    global _risk_assessment_ai
    if _risk_assessment_ai is None:
        _risk_assessment_ai = RiskAssessmentAI()
    return _risk_assessment_ai


# 測試代碼
if __name__ == "__main__":
    async def test_risk_assessment_ai():
        """測試風險評估AI"""
        print("🧪 測試風險評估AI...")
        
        ai = RiskAssessmentAI()
        
        try:
            # 測試單個交易對風險評估
            print("📊 測試單個交易對風險評估...")
            result = await ai.assess_risk("BTCTWD")
            print(f"   風險等級: {result.risk_metrics.overall_risk_level.value}")
            print(f"   風險評分: {result.risk_metrics.risk_score:.1f}")
            print(f"   建議倉位: {result.recommended_position_size:.4f}")
            
            # 測試多交易對風險評估
            print("\n📊 測試多交易對風險評估...")
            pairs = ["BTCTWD", "ETHTWD", "LTCTWD"]
            results = await ai.assess_multi_pair_risk(pairs)
            
            for pair, assessment in results.items():
                print(f"   {pair}: {assessment.risk_metrics.overall_risk_level.value} ({assessment.risk_metrics.risk_score:.1f})")
            
            # 測試組合風險摘要
            print("\n📊 測試組合風險摘要...")
            summary = ai.get_portfolio_risk_summary(results)
            print(f"   組合風險等級: {summary.get('portfolio_risk_level')}")
            print(f"   平均風險評分: {summary.get('average_risk_score')}")
            print(f"   分散化評分: {summary.get('diversification_score')}")
            
            print("\n✅ 風險評估AI測試完成")
            
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
    
    # 運行測試
    asyncio.run(test_risk_assessment_ai())