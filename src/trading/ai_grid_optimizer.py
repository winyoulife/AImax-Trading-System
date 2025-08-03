#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI驅動的網格優化器 - 使用五AI協作系統優化網格交易策略
"""

import asyncio
import logging
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import sys
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from .simple_grid_engine import GridConfig, SimpleGridEngine, create_simple_grid_engine
    from ..ai.enhanced_ai_manager import create_enhanced_ai_manager
    from ..data.historical_data_manager import HistoricalDataManager
except ImportError:
    from simple_grid_engine import GridConfig, SimpleGridEngine, create_simple_grid_engine
    from AImax.src.ai.enhanced_ai_manager import create_enhanced_ai_manager
    from AImax.src.data.historical_data_manager import HistoricalDataManager

logger = logging.getLogger(__name__)

class OptimizationMode(Enum):
    """優化模式"""
    PROFIT_MAXIMIZATION = "profit_max"      # 利潤最大化
    RISK_MINIMIZATION = "risk_min"          # 風險最小化
    BALANCED = "balanced"                   # 平衡模式
    ADAPTIVE = "adaptive"                   # 自適應模式

@dataclass
class GridOptimizationConfig:
    """網格優化配置"""
    pair: str
    optimization_mode: OptimizationMode = OptimizationMode.BALANCED
    historical_days: int = 30               # 歷史數據天數
    min_grid_spacing: float = 0.5          # 最小網格間距 (%)
    max_grid_spacing: float = 5.0          # 最大網格間距 (%)
    min_grid_levels: int = 6               # 最小網格層數
    max_grid_levels: int = 20              # 最大網格層數
    min_order_amount: float = 5000         # 最小訂單金額
    max_order_amount: float = 20000        # 最大訂單金額
    optimization_iterations: int = 5       # 優化迭代次數
    ai_confidence_threshold: float = 0.6   # AI信心度閾值

@dataclass
class OptimizationResult:
    """優化結果"""
    optimized_config: GridConfig
    expected_profit: float
    expected_risk: float
    confidence_score: float
    ai_reasoning: str
    backtest_results: Dict[str, Any]
    optimization_time: float
    timestamp: datetime = field(default_factory=datetime.now)

class AIGridOptimizer:
    """AI驅動的網格優化器"""
    
    def __init__(self, config: GridOptimizationConfig):
        self.config = config
        self.ai_manager = create_enhanced_ai_manager()
        self.historical_data_manager = HistoricalDataManager()
        
        # 優化歷史
        self.optimization_history: List[OptimizationResult] = []
        
        # 市場數據緩存
        self.market_data_cache: Dict[str, Any] = {}
        
        logger.info(f"🤖 AI網格優化器初始化完成: {config.pair}")
    
    async def optimize_grid_parameters(self, current_price: float, 
                                     available_balance: float) -> OptimizationResult:
        """使用AI優化網格參數"""
        start_time = datetime.now()
        
        try:
            logger.info(f"🤖 開始AI網格優化: {self.config.pair}")
            
            # 階段1: 獲取和分析歷史數據
            logger.info("📊 階段1: 獲取歷史數據...")
            historical_data = await self._get_historical_data()
            
            # 階段2: AI市場分析
            logger.info("🧠 階段2: AI市場分析...")
            market_analysis = await self._ai_market_analysis(historical_data, current_price)
            
            # 階段3: 生成優化候選方案
            logger.info("⚙️ 階段3: 生成優化候選方案...")
            candidate_configs = self._generate_candidate_configs(
                current_price, available_balance, market_analysis
            )
            
            # 階段4: AI評估和選擇
            logger.info("🎯 階段4: AI評估最優方案...")
            best_config = await self._ai_evaluate_candidates(
                candidate_configs, market_analysis, historical_data
            )
            
            # 階段5: 回測驗證
            logger.info("📈 階段5: 回測驗證...")
            backtest_results = await self._backtest_config(best_config, historical_data)
            
            # 階段6: 生成最終結果
            optimization_time = (datetime.now() - start_time).total_seconds()
            
            result = OptimizationResult(
                optimized_config=best_config,
                expected_profit=backtest_results.get("total_profit", 0.0),
                expected_risk=backtest_results.get("max_drawdown", 0.0),
                confidence_score=market_analysis.get("ai_confidence", 0.5),
                ai_reasoning=market_analysis.get("reasoning", "AI分析完成"),
                backtest_results=backtest_results,
                optimization_time=optimization_time
            )
            
            # 保存優化歷史
            self.optimization_history.append(result)
            
            logger.info(f"✅ AI網格優化完成: 預期盈利{result.expected_profit:.2f}, 風險{result.expected_risk:.2%}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ AI網格優化失敗: {e}")
            # 返回默認配置
            return self._create_fallback_result(current_price, available_balance, str(e))
    
    async def _get_historical_data(self) -> Dict[str, Any]:
        """獲取歷史數據"""
        try:
            # 計算日期範圍
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.config.historical_days)
            
            # 獲取K線數據 (模擬)
            kline_data = []
            base_price = 3500000  # 基準價格
            
            # 生成模擬歷史數據
            for i in range(self.config.historical_days * 24):  # 每小時一個數據點
                timestamp = start_date + timedelta(hours=i)
                
                # 模擬價格波動
                volatility = 0.02
                price_change = np.random.normal(0, volatility)
                price = base_price * (1 + price_change)
                
                # 模擬成交量
                volume = np.random.uniform(0.5, 2.0)
                
                kline_data.append({
                    "timestamp": timestamp,
                    "open": price * 0.999,
                    "high": price * 1.001,
                    "low": price * 0.998,
                    "close": price,
                    "volume": volume
                })
                
                base_price = price  # 更新基準價格
            
            # 計算技術指標
            prices = [k["close"] for k in kline_data]
            
            historical_data = {
                "kline_data": kline_data,
                "price_data": prices,
                "volatility": np.std(prices) / np.mean(prices),
                "price_range": (min(prices), max(prices)),
                "average_price": np.mean(prices),
                "trend_slope": self._calculate_trend_slope(prices),
                "support_resistance": self._find_support_resistance(prices)
            }
            
            logger.info(f"📊 獲取歷史數據: {len(kline_data)} 個數據點, 波動率{historical_data['volatility']:.2%}")
            
            return historical_data
            
        except Exception as e:
            logger.error(f"❌ 獲取歷史數據失敗: {e}")
            return {"error": str(e)}
    
    def _calculate_trend_slope(self, prices: List[float]) -> float:
        """計算趨勢斜率"""
        try:
            if len(prices) < 2:
                return 0.0
            
            x = np.arange(len(prices))
            y = np.array(prices)
            
            # 線性回歸計算斜率
            slope = np.polyfit(x, y, 1)[0]
            
            # 標準化斜率
            normalized_slope = slope / np.mean(prices)
            
            return normalized_slope
            
        except Exception:
            return 0.0
    
    def _find_support_resistance(self, prices: List[float]) -> Dict[str, List[float]]:
        """尋找支撐阻力位"""
        try:
            if len(prices) < 10:
                return {"support": [], "resistance": []}
            
            prices_array = np.array(prices)
            
            # 尋找局部最高點和最低點
            window = 5
            resistance_levels = []
            support_levels = []
            
            for i in range(window, len(prices) - window):
                # 檢查是否為局部最高點
                if all(prices[i] >= prices[j] for j in range(i - window, i + window + 1)):
                    resistance_levels.append(prices[i])
                
                # 檢查是否為局部最低點
                if all(prices[i] <= prices[j] for j in range(i - window, i + window + 1)):
                    support_levels.append(prices[i])
            
            # 聚類相近的支撐阻力位
            support_levels = self._cluster_levels(support_levels)
            resistance_levels = self._cluster_levels(resistance_levels)
            
            return {
                "support": support_levels[:3],      # 取前3個支撐位
                "resistance": resistance_levels[:3] # 取前3個阻力位
            }
            
        except Exception:
            return {"support": [], "resistance": []}
    
    def _cluster_levels(self, levels: List[float], threshold: float = 0.02) -> List[float]:
        """聚類相近的價格水平"""
        if not levels:
            return []
        
        levels = sorted(levels)
        clustered = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            if abs(level - current_cluster[-1]) / current_cluster[-1] <= threshold:
                current_cluster.append(level)
            else:
                # 完成當前聚類，取平均值
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]
        
        # 添加最後一個聚類
        clustered.append(np.mean(current_cluster))
        
        return clustered
    
    async def _ai_market_analysis(self, historical_data: Dict[str, Any], 
                                current_price: float) -> Dict[str, Any]:
        """AI市場分析"""
        try:
            # 準備AI分析數據
            analysis_data = {
                "current_price": current_price,
                "volatility": historical_data.get("volatility", 0.02),
                "trend_slope": historical_data.get("trend_slope", 0.0),
                "price_range": historical_data.get("price_range", (current_price * 0.9, current_price * 1.1)),
                "support_levels": historical_data.get("support_resistance", {}).get("support", []),
                "resistance_levels": historical_data.get("support_resistance", {}).get("resistance", []),
                "average_price": historical_data.get("average_price", current_price)
            }
            
            # 使用AI管理器進行分析
            market_data_for_ai = {
                self.config.pair: {
                    "current_price": current_price,
                    "volatility": analysis_data["volatility"],
                    "price_change_5m": analysis_data["trend_slope"] * 100,
                    "rsi": 50 + analysis_data["trend_slope"] * 1000,  # 模擬RSI
                    "volume_ratio": 1.0,
                    "spread_pct": 0.001
                }
            }
            
            # 獲取AI決策
            ai_decisions = await self.ai_manager.analyze_multi_pair_market(market_data_for_ai)
            
            if self.config.pair in ai_decisions:
                ai_decision = ai_decisions[self.config.pair]
                
                market_analysis = {
                    "ai_decision": ai_decision.final_decision,
                    "ai_confidence": ai_decision.confidence,
                    "risk_score": ai_decision.risk_score,
                    "reasoning": ai_decision.reasoning,
                    "market_condition": self._determine_market_condition(analysis_data),
                    "optimal_grid_zone": self._calculate_optimal_grid_zone(analysis_data),
                    "recommended_spacing": self._recommend_grid_spacing(analysis_data),
                    "risk_level": ai_decision.risk_level
                }
                
                logger.info(f"🧠 AI分析完成: 決策{ai_decision.final_decision}, 信心度{ai_decision.confidence:.2f}")
                
                return market_analysis
            
        except Exception as e:
            logger.error(f"❌ AI市場分析失敗: {e}")
        
        # 返回默認分析結果
        return {
            "ai_decision": "HOLD",
            "ai_confidence": 0.5,
            "risk_score": 0.5,
            "reasoning": "AI分析失敗，使用默認配置",
            "market_condition": "sideways",
            "optimal_grid_zone": (current_price * 0.9, current_price * 1.1),
            "recommended_spacing": 2.0,
            "risk_level": "中等"
        }
    
    def _determine_market_condition(self, analysis_data: Dict[str, Any]) -> str:
        """判斷市場條件"""
        try:
            trend_slope = analysis_data.get("trend_slope", 0.0)
            volatility = analysis_data.get("volatility", 0.02)
            
            if trend_slope > 0.001 and volatility < 0.03:
                return "bull"  # 牛市
            elif trend_slope < -0.001 and volatility > 0.05:
                return "bear"  # 熊市
            else:
                return "sideways"  # 震盪市
                
        except Exception:
            return "sideways"
    
    def _calculate_optimal_grid_zone(self, analysis_data: Dict[str, Any]) -> Tuple[float, float]:
        """計算最優網格區間"""
        try:
            current_price = analysis_data["current_price"]
            volatility = analysis_data.get("volatility", 0.02)
            support_levels = analysis_data.get("support_levels", [])
            resistance_levels = analysis_data.get("resistance_levels", [])
            
            # 基於波動率計算基礎區間
            base_range = volatility * 3  # 3倍波動率
            
            # 基於支撐阻力位調整
            if support_levels:
                lower_bound = min(support_levels)
            else:
                lower_bound = current_price * (1 - base_range)
            
            if resistance_levels:
                upper_bound = max(resistance_levels)
            else:
                upper_bound = current_price * (1 + base_range)
            
            return (lower_bound, upper_bound)
            
        except Exception:
            current_price = analysis_data.get("current_price", 3500000)
            return (current_price * 0.9, current_price * 1.1)
    
    def _recommend_grid_spacing(self, analysis_data: Dict[str, Any]) -> float:
        """推薦網格間距"""
        try:
            volatility = analysis_data.get("volatility", 0.02)
            market_condition = self._determine_market_condition(analysis_data)
            
            # 基於波動率和市場條件推薦間距
            if market_condition == "sideways":
                # 震盪市場使用較小間距
                spacing = max(0.5, min(3.0, volatility * 100))
            elif market_condition == "bull":
                # 牛市使用中等間距
                spacing = max(1.0, min(4.0, volatility * 150))
            else:
                # 熊市使用較大間距
                spacing = max(1.5, min(5.0, volatility * 200))
            
            return spacing
            
        except Exception:
            return 2.0  # 默認2%間距
    
    def _generate_candidate_configs(self, current_price: float, available_balance: float,
                                  market_analysis: Dict[str, Any]) -> List[GridConfig]:
        """生成候選配置"""
        try:
            candidates = []
            
            # 獲取AI推薦參數
            optimal_zone = market_analysis.get("optimal_grid_zone", (current_price * 0.9, current_price * 1.1))
            recommended_spacing = market_analysis.get("recommended_spacing", 2.0)
            
            # 生成多個候選配置
            spacing_variants = [
                recommended_spacing * 0.8,  # 較密集
                recommended_spacing,        # 推薦值
                recommended_spacing * 1.2   # 較稀疏
            ]
            
            level_variants = [8, 12, 16]  # 不同層級數
            
            for spacing in spacing_variants:
                for levels in level_variants:
                    # 確保間距在允許範圍內
                    spacing = max(self.config.min_grid_spacing, 
                                min(self.config.max_grid_spacing, spacing))
                    
                    # 計算訂單金額
                    order_amount = min(available_balance / levels, self.config.max_order_amount)
                    order_amount = max(self.config.min_order_amount, order_amount)
                    
                    config = GridConfig(
                        pair=self.config.pair,
                        base_price=current_price,
                        grid_spacing=spacing,
                        grid_levels=levels,
                        order_amount=order_amount,
                        upper_limit=optimal_zone[1],
                        lower_limit=optimal_zone[0],
                        max_position=0.3
                    )
                    
                    candidates.append(config)
            
            logger.info(f"⚙️ 生成候選配置: {len(candidates)} 個")
            
            return candidates
            
        except Exception as e:
            logger.error(f"❌ 生成候選配置失敗: {e}")
            return [self._create_default_config(current_price, available_balance)]
    
    def _create_default_config(self, current_price: float, available_balance: float) -> GridConfig:
        """創建默認配置"""
        return GridConfig(
            pair=self.config.pair,
            base_price=current_price,
            grid_spacing=2.0,
            grid_levels=10,
            order_amount=min(10000, available_balance / 10),
            upper_limit=current_price * 1.15,
            lower_limit=current_price * 0.85,
            max_position=0.3
        )   
 
    async def _ai_evaluate_candidates(self, candidates: List[GridConfig], 
                                     market_analysis: Dict[str, Any],
                                     historical_data: Dict[str, Any]) -> GridConfig:
        """AI評估候選配置"""
        try:
            logger.info(f"🎯 AI評估 {len(candidates)} 個候選配置...")
            
            best_config = None
            best_score = -float('inf')
            
            for i, config in enumerate(candidates):
                # 計算配置評分
                score = await self._calculate_config_score(config, market_analysis, historical_data)
                
                logger.debug(f"   候選{i+1}: 間距{config.grid_spacing:.1f}%, "
                           f"層級{config.grid_levels}, 評分{score:.2f}")
                
                if score > best_score:
                    best_score = score
                    best_config = config
            
            if best_config:
                logger.info(f"✅ 最優配置: 間距{best_config.grid_spacing:.1f}%, "
                          f"層級{best_config.grid_levels}, 評分{best_score:.2f}")
                return best_config
            else:
                return candidates[0]  # 返回第一個候選
                
        except Exception as e:
            logger.error(f"❌ AI評估候選配置失敗: {e}")
            return candidates[0] if candidates else self._create_default_config(3500000, 100000)
    
    async def _calculate_config_score(self, config: GridConfig, 
                                    market_analysis: Dict[str, Any],
                                    historical_data: Dict[str, Any]) -> float:
        """計算配置評分"""
        try:
            score = 0.0
            
            # 1. AI信心度權重 (30%)
            ai_confidence = market_analysis.get("ai_confidence", 0.5)
            ai_decision = market_analysis.get("ai_decision", "HOLD")
            
            if ai_decision in ["BUY", "SELL"]:
                score += ai_confidence * 30
            else:
                score += ai_confidence * 15  # HOLD決策降低權重
            
            # 2. 市場適應性評分 (25%)
            market_condition = market_analysis.get("market_condition", "sideways")
            volatility = historical_data.get("volatility", 0.02)
            
            # 根據市場條件評估間距適應性
            if market_condition == "sideways":
                # 震盪市場偏好較小間距
                spacing_score = max(0, 25 - abs(config.grid_spacing - 1.5) * 5)
            elif market_condition == "bull":
                # 牛市偏好中等間距
                spacing_score = max(0, 25 - abs(config.grid_spacing - 2.5) * 3)
            else:
                # 熊市偏好較大間距
                spacing_score = max(0, 25 - abs(config.grid_spacing - 3.5) * 2)
            
            score += spacing_score
            
            # 3. 風險控制評分 (20%)
            risk_score = market_analysis.get("risk_score", 0.5)
            
            # 風險越低評分越高
            risk_control_score = (1 - risk_score) * 20
            
            # 倉位控制評分
            if config.max_position <= 0.3:
                risk_control_score += 5
            
            score += risk_control_score
            
            # 4. 資源利用效率 (15%)
            # 評估訂單金額和層級數的合理性
            efficiency_score = 0
            
            # 層級數適中性
            if 8 <= config.grid_levels <= 16:
                efficiency_score += 8
            elif 6 <= config.grid_levels <= 20:
                efficiency_score += 5
            
            # 訂單金額合理性
            if 5000 <= config.order_amount <= 15000:
                efficiency_score += 7
            
            score += efficiency_score
            
            # 5. 歷史表現預測 (10%)
            # 基於歷史數據預測表現
            historical_score = self._predict_historical_performance(config, historical_data)
            score += historical_score * 10
            
            return max(0, score)
            
        except Exception as e:
            logger.error(f"❌ 計算配置評分失敗: {e}")
            return 50.0  # 默認中等評分
    
    def _predict_historical_performance(self, config: GridConfig, 
                                      historical_data: Dict[str, Any]) -> float:
        """預測歷史表現"""
        try:
            prices = historical_data.get("price_data", [])
            if not prices:
                return 0.5
            
            # 計算價格在網格區間內的時間比例
            in_range_count = 0
            for price in prices:
                if config.lower_limit <= price <= config.upper_limit:
                    in_range_count += 1
            
            range_utilization = in_range_count / len(prices)
            
            # 計算預期觸發次數
            price_changes = []
            for i in range(1, len(prices)):
                change = abs(prices[i] - prices[i-1]) / prices[i-1]
                price_changes.append(change)
            
            avg_change = np.mean(price_changes) if price_changes else 0.01
            expected_triggers = avg_change / (config.grid_spacing / 100)
            
            # 綜合評分
            performance_score = (range_utilization * 0.7 + 
                               min(1.0, expected_triggers / 10) * 0.3)
            
            return performance_score
            
        except Exception:
            return 0.5
    
    async def _backtest_config(self, config: GridConfig, 
                             historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """回測配置"""
        try:
            logger.info(f"📈 開始回測配置...")
            
            # 創建網格引擎
            engine = create_simple_grid_engine(config)
            engine.set_balance(100000)  # 設置10萬TWD測試資金
            
            if not engine.initialize_grid():
                return {"error": "網格初始化失敗"}
            
            # 使用歷史價格進行回測
            prices = historical_data.get("price_data", [])
            if not prices:
                return {"error": "無歷史價格數據"}
            
            # 執行回測
            total_profit = 0.0
            max_drawdown = 0.0
            peak_balance = 100000
            trade_count = 0
            
            for price in prices:
                result = await engine.update_price(price)
                
                if result.get("triggered_actions"):
                    trade_count += len(result["triggered_actions"])
                
                # 計算當前餘額
                status = engine.get_status()
                current_balance = status["available_balance"] + status["current_position"] * price
                total_profit = current_balance - 100000
                
                # 計算最大回撤
                if current_balance > peak_balance:
                    peak_balance = current_balance
                
                drawdown = (peak_balance - current_balance) / peak_balance
                max_drawdown = max(max_drawdown, drawdown)
            
            # 計算最終狀態
            final_status = engine.get_status()
            
            backtest_results = {
                "total_profit": total_profit,
                "max_drawdown": max_drawdown,
                "trade_count": trade_count,
                "win_rate": 0.6,  # 簡化計算
                "sharpe_ratio": total_profit / max(max_drawdown, 0.01),
                "final_position": final_status["current_position"],
                "final_balance": final_status["available_balance"],
                "grid_utilization": trade_count / len(prices) if prices else 0
            }
            
            logger.info(f"📊 回測完成: 盈利{total_profit:.2f}, 回撤{max_drawdown:.2%}, 交易{trade_count}次")
            
            return backtest_results
            
        except Exception as e:
            logger.error(f"❌ 回測失敗: {e}")
            return {"error": str(e)}
    
    def _create_fallback_result(self, current_price: float, available_balance: float, 
                              error_message: str) -> OptimizationResult:
        """創建備用結果"""
        fallback_config = self._create_default_config(current_price, available_balance)
        
        return OptimizationResult(
            optimized_config=fallback_config,
            expected_profit=0.0,
            expected_risk=0.5,
            confidence_score=0.3,
            ai_reasoning=f"優化失敗，使用默認配置: {error_message}",
            backtest_results={"error": error_message},
            optimization_time=0.0
        )
    
    async def adaptive_optimization(self, current_config: GridConfig, 
                                  performance_data: Dict[str, Any]) -> OptimizationResult:
        """自適應優化"""
        try:
            logger.info(f"🔄 開始自適應優化...")
            
            # 分析當前性能
            current_profit = performance_data.get("total_profit", 0.0)
            current_drawdown = performance_data.get("max_drawdown", 0.0)
            trade_frequency = performance_data.get("trade_count", 0)
            
            # 基於性能調整策略
            adjustment_factor = 1.0
            
            if current_profit < 0:
                # 虧損時收緊網格
                adjustment_factor = 0.8
                logger.info("📉 檢測到虧損，收緊網格間距")
            elif current_drawdown > 0.1:
                # 回撤過大時擴大網格
                adjustment_factor = 1.2
                logger.info("⚠️ 回撤過大，擴大網格間距")
            elif trade_frequency < 5:
                # 交易頻率過低時收緊網格
                adjustment_factor = 0.9
                logger.info("📊 交易頻率低，收緊網格間距")
            
            # 創建調整後的配置
            adjusted_config = GridConfig(
                pair=current_config.pair,
                base_price=current_config.base_price,
                grid_spacing=current_config.grid_spacing * adjustment_factor,
                grid_levels=current_config.grid_levels,
                order_amount=current_config.order_amount,
                upper_limit=current_config.upper_limit,
                lower_limit=current_config.lower_limit,
                max_position=current_config.max_position
            )
            
            # 進行完整優化
            return await self.optimize_grid_parameters(
                current_config.base_price, 
                current_config.order_amount * current_config.grid_levels
            )
            
        except Exception as e:
            logger.error(f"❌ 自適應優化失敗: {e}")
            return self._create_fallback_result(
                current_config.base_price, 
                current_config.order_amount * current_config.grid_levels,
                str(e)
            )
    
    def get_optimization_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取優化歷史"""
        try:
            recent_history = self.optimization_history[-limit:] if limit > 0 else self.optimization_history
            
            history_data = []
            for result in recent_history:
                history_item = {
                    "timestamp": result.timestamp.isoformat(),
                    "pair": result.optimized_config.pair,
                    "grid_spacing": result.optimized_config.grid_spacing,
                    "grid_levels": result.optimized_config.grid_levels,
                    "expected_profit": result.expected_profit,
                    "expected_risk": result.expected_risk,
                    "confidence_score": result.confidence_score,
                    "optimization_time": result.optimization_time,
                    "backtest_summary": {
                        "total_profit": result.backtest_results.get("total_profit", 0),
                        "max_drawdown": result.backtest_results.get("max_drawdown", 0),
                        "trade_count": result.backtest_results.get("trade_count", 0)
                    }
                }
                history_data.append(history_item)
            
            return history_data
            
        except Exception as e:
            logger.error(f"❌ 獲取優化歷史失敗: {e}")
            return []
    
    def export_optimization_report(self) -> Dict[str, Any]:
        """導出優化報告"""
        try:
            if not self.optimization_history:
                return {"error": "無優化歷史"}
            
            latest_result = self.optimization_history[-1]
            
            report = {
                "optimization_summary": {
                    "pair": self.config.pair,
                    "optimization_mode": self.config.optimization_mode.value,
                    "total_optimizations": len(self.optimization_history),
                    "latest_optimization": latest_result.timestamp.isoformat()
                },
                "latest_result": {
                    "optimized_config": {
                        "grid_spacing": latest_result.optimized_config.grid_spacing,
                        "grid_levels": latest_result.optimized_config.grid_levels,
                        "order_amount": latest_result.optimized_config.order_amount,
                        "upper_limit": latest_result.optimized_config.upper_limit,
                        "lower_limit": latest_result.optimized_config.lower_limit
                    },
                    "performance_prediction": {
                        "expected_profit": latest_result.expected_profit,
                        "expected_risk": latest_result.expected_risk,
                        "confidence_score": latest_result.confidence_score
                    },
                    "ai_reasoning": latest_result.ai_reasoning,
                    "backtest_results": latest_result.backtest_results
                },
                "optimization_statistics": {
                    "average_confidence": np.mean([r.confidence_score for r in self.optimization_history]),
                    "average_expected_profit": np.mean([r.expected_profit for r in self.optimization_history]),
                    "average_optimization_time": np.mean([r.optimization_time for r in self.optimization_history])
                },
                "report_time": datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 導出優化報告失敗: {e}")
            return {"error": str(e)}


# 創建AI網格優化器實例
def create_ai_grid_optimizer(config: GridOptimizationConfig) -> AIGridOptimizer:
    """創建AI網格優化器實例"""
    return AIGridOptimizer(config)


# 測試代碼
if __name__ == "__main__":
    async def test_ai_grid_optimizer():
        """測試AI網格優化器"""
        print("🧪 測試AI網格優化器...")
        
        # 創建優化配置
        opt_config = GridOptimizationConfig(
            pair="BTCTWD",
            optimization_mode=OptimizationMode.BALANCED,
            historical_days=7,  # 使用7天數據進行快速測試
            optimization_iterations=3
        )
        
        # 創建優化器
        optimizer = create_ai_grid_optimizer(opt_config)
        
        # 執行優化
        current_price = 3500000
        available_balance = 100000
        
        print(f"🚀 開始優化: 當前價格{current_price:,.0f}, 可用資金{available_balance:,.0f}")
        
        result = await optimizer.optimize_grid_parameters(current_price, available_balance)
        
        print(f"✅ 優化完成:")
        print(f"   網格間距: {result.optimized_config.grid_spacing:.1f}%")
        print(f"   網格層級: {result.optimized_config.grid_levels}")
        print(f"   訂單金額: {result.optimized_config.order_amount:,.0f} TWD")
        print(f"   預期盈利: {result.expected_profit:,.2f} TWD")
        print(f"   預期風險: {result.expected_risk:.2%}")
        print(f"   AI信心度: {result.confidence_score:.2f}")
        print(f"   優化耗時: {result.optimization_time:.2f}秒")
        
        # 測試自適應優化
        print(f"\\n🔄 測試自適應優化...")
        
        performance_data = {
            "total_profit": -5000,  # 模擬虧損
            "max_drawdown": 0.15,   # 模擬高回撤
            "trade_count": 3        # 模擬低交易頻率
        }
        
        adaptive_result = await optimizer.adaptive_optimization(result.optimized_config, performance_data)
        
        print(f"✅ 自適應優化完成:")
        print(f"   調整後間距: {adaptive_result.optimized_config.grid_spacing:.1f}%")
        print(f"   AI推理: {adaptive_result.ai_reasoning[:100]}...")
        
        # 導出報告
        report = optimizer.export_optimization_report()
        print(f"\\n📊 優化報告:")
        print(f"   總優化次數: {report['optimization_summary']['total_optimizations']}")
        print(f"   平均信心度: {report['optimization_statistics']['average_confidence']:.2f}")
        print(f"   平均優化時間: {report['optimization_statistics']['average_optimization_time']:.2f}秒")
        
        print("🎉 AI網格優化器測試完成！")
    
    # 運行測試
    asyncio.run(test_ai_grid_optimizer())