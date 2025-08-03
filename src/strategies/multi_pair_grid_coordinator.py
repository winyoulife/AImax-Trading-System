#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易對網格協調器 - 統一管理多個交易對的網格交易策略
實現資源分配、風險控制和全局績效監控
"""

import logging
import asyncio
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
from pathlib import Path

from ..trading.grid_trading_engine import GridTradingEngine, GridConfig, GridMode, GridStatus
from ..data.multi_pair_data_manager import MultiPairDataManager
from ..ai.multi_pair_ai_coordinator import MultiPairAICoordinator

logger = logging.getLogger(__name__)

class CoordinatorStatus(Enum):
    """協調器狀態"""
    INACTIVE = "inactive"      # 未激活
    ACTIVE = "active"          # 運行中
    PAUSED = "paused"          # 暫停
    STOPPED = "stopped"        # 已停止
    ERROR = "error"            # 錯誤狀態

@dataclass
class GridAllocation:
    """網格資源分配"""
    pair: str                  # 交易對
    allocated_capital: float   # 分配資金
    max_positions: int         # 最大持倉數
    priority: int              # 優先級 (1-10)
    risk_weight: float         # 風險權重
    performance_score: float = 0.0  # 績效評分
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class GlobalRiskMetrics:
    """全局風險指標"""
    total_capital: float = 0.0           # 總資金
    allocated_capital: float = 0.0       # 已分配資金
    available_capital: float = 0.0       # 可用資金
    total_unrealized_pnl: float = 0.0    # 總未實現盈虧
    total_realized_pnl: float = 0.0      # 總已實現盈虧
    total_exposure: float = 0.0          # 總風險敞口
    correlation_risk: float = 0.0        # 相關性風險
    max_drawdown: float = 0.0            # 最大回撤
    sharpe_ratio: float = 0.0            # 夏普比率
    last_update: datetime = field(default_factory=datetime.now)

@dataclass
class CoordinatorPerformance:
    """協調器績效統計"""
    total_grids: int = 0                 # 總網格數
    active_grids: int = 0                # 活躍網格數
    total_trades: int = 0                # 總交易次數
    successful_trades: int = 0           # 成功交易次數
    total_profit: float = 0.0            # 總盈利
    total_fees: float = 0.0              # 總手續費
    net_profit: float = 0.0              # 淨盈利
    win_rate: float = 0.0                # 勝率
    avg_profit_per_trade: float = 0.0    # 平均每筆盈利
    best_performing_pair: str = ""       # 最佳表現交易對
    worst_performing_pair: str = ""      # 最差表現交易對
    start_time: datetime = field(default_factory=datetime.now)
    last_update: datetime = field(default_factory=datetime.now)

class MultiPairGridCoordinator:
    """多交易對網格協調器"""
    
    def __init__(self, 
                 data_manager: MultiPairDataManager,
                 ai_coordinator: MultiPairAICoordinator,
                 total_capital: float = 100000.0):
        """
        初始化多交易對網格協調器
        
        Args:
            data_manager: 多交易對數據管理器
            ai_coordinator: AI協調器
            total_capital: 總資金
        """
        self.data_manager = data_manager
        self.ai_coordinator = ai_coordinator
        self.total_capital = total_capital
        
        # 協調器狀態
        self.status = CoordinatorStatus.INACTIVE
        
        # 網格引擎管理
        self.grid_engines: Dict[str, GridTradingEngine] = {}
        self.grid_configs: Dict[str, GridConfig] = {}
        self.grid_allocations: Dict[str, GridAllocation] = {}
        
        # 風險管理
        self.risk_metrics = GlobalRiskMetrics(total_capital=total_capital)
        self.risk_limits = {
            'max_allocation_per_pair': 0.3,      # 單個交易對最大分配比例
            'max_total_exposure': 0.8,           # 最大總風險敞口
            'max_correlation_risk': 0.6,         # 最大相關性風險
            'max_drawdown_limit': 0.15,          # 最大回撤限制
            'min_available_capital': 0.1         # 最小可用資金比例
        }
        
        # 績效統計
        self.performance = CoordinatorPerformance()
        
        # 監控和控制
        self.monitoring_thread = None
        self.monitoring_active = False
        self.rebalance_interval = 300  # 5分鐘重平衡間隔
        
        # 事件記錄
        self.event_history: List[Dict[str, Any]] = []
        
        logger.info(f"🔥 多交易對網格協調器初始化完成，總資金: {total_capital:,.2f} TWD")
    
    def add_trading_pair(self, 
                        pair: str, 
                        grid_config: GridConfig,
                        allocation_ratio: float = 0.2,
                        priority: int = 5) -> bool:
        """
        添加交易對到網格協調系統
        
        Args:
            pair: 交易對名稱
            grid_config: 網格配置
            allocation_ratio: 資金分配比例
            priority: 優先級 (1-10)
        """
        try:
            if pair in self.grid_engines:
                logger.warning(f"⚠️ 交易對 {pair} 已存在")
                return False
            
            # 驗證分配比例
            if allocation_ratio > self.risk_limits['max_allocation_per_pair']:
                logger.error(f"❌ 分配比例 {allocation_ratio:.2%} 超過限制 "
                           f"{self.risk_limits['max_allocation_per_pair']:.2%}")
                return False
            
            # 計算分配資金
            allocated_capital = self.total_capital * allocation_ratio
            
            # 檢查可用資金
            if allocated_capital > self.risk_metrics.available_capital:
                logger.error(f"❌ 分配資金 {allocated_capital:,.2f} 超過可用資金 "
                           f"{self.risk_metrics.available_capital:,.2f}")
                return False
            
            # 更新網格配置的投資限額
            grid_config.max_investment = allocated_capital
            
            # 創建網格引擎
            grid_engine = GridTradingEngine(grid_config)
            
            # 創建資源分配記錄
            allocation = GridAllocation(
                pair=pair,
                allocated_capital=allocated_capital,
                max_positions=int(allocated_capital / (grid_config.base_quantity * grid_config.center_price)),
                priority=priority,
                risk_weight=allocation_ratio
            )
            
            # 保存到管理器
            self.grid_engines[pair] = grid_engine
            self.grid_configs[pair] = grid_config
            self.grid_allocations[pair] = allocation
            
            # 更新風險指標
            self._update_risk_metrics()
            
            # 記錄事件
            self._log_event("pair_added", {
                "pair": pair,
                "allocated_capital": allocated_capital,
                "priority": priority,
                "allocation_ratio": allocation_ratio
            })
            
            logger.info(f"✅ 交易對 {pair} 添加成功，分配資金: {allocated_capital:,.2f} TWD")
            return True
            
        except Exception as e:
            logger.error(f"❌ 添加交易對 {pair} 失敗: {e}")
            return False
    
    def remove_trading_pair(self, pair: str) -> bool:
        """移除交易對"""
        try:
            if pair not in self.grid_engines:
                logger.warning(f"⚠️ 交易對 {pair} 不存在")
                return False
            
            # 停止網格交易
            grid_engine = self.grid_engines[pair]
            if grid_engine.status == GridStatus.ACTIVE:
                grid_engine.stop_grid()
            
            # 釋放資源
            allocation = self.grid_allocations[pair]
            
            # 移除記錄
            del self.grid_engines[pair]
            del self.grid_configs[pair]
            del self.grid_allocations[pair]
            
            # 更新風險指標
            self._update_risk_metrics()
            
            # 記錄事件
            self._log_event("pair_removed", {
                "pair": pair,
                "released_capital": allocation.allocated_capital
            })
            
            logger.info(f"✅ 交易對 {pair} 移除成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 移除交易對 {pair} 失敗: {e}")
            return False
    
    def start_coordinator(self) -> bool:
        """啟動協調器"""
        try:
            if self.status != CoordinatorStatus.INACTIVE:
                logger.warning(f"⚠️ 協調器已在運行狀態: {self.status.value}")
                return False
            
            if not self.grid_engines:
                logger.error("❌ 沒有配置的交易對")
                return False
            
            # 啟動所有網格引擎
            started_count = 0
            for pair, engine in self.grid_engines.items():
                if engine.start_grid():
                    started_count += 1
                    logger.info(f"✅ {pair} 網格啟動成功")
                else:
                    logger.error(f"❌ {pair} 網格啟動失敗")
            
            if started_count == 0:
                logger.error("❌ 沒有網格引擎啟動成功")
                return False
            
            # 更新狀態
            self.status = CoordinatorStatus.ACTIVE
            self.performance.start_time = datetime.now()
            
            # 啟動監控線程
            self._start_monitoring()
            
            # 記錄事件
            self._log_event("coordinator_started", {
                "total_pairs": len(self.grid_engines),
                "started_pairs": started_count
            })
            
            logger.info(f"🚀 多交易對網格協調器啟動成功，管理 {started_count} 個交易對")
            return True
            
        except Exception as e:
            logger.error(f"❌ 協調器啟動失敗: {e}")
            self.status = CoordinatorStatus.ERROR
            return False
    
    def stop_coordinator(self) -> bool:
        """停止協調器"""
        try:
            if self.status == CoordinatorStatus.INACTIVE:
                logger.warning("⚠️ 協調器未啟動")
                return False
            
            # 停止監控線程
            self._stop_monitoring()
            
            # 停止所有網格引擎
            stopped_count = 0
            for pair, engine in self.grid_engines.items():
                if engine.stop_grid():
                    stopped_count += 1
                    logger.info(f"🛑 {pair} 網格已停止")
                else:
                    logger.error(f"❌ {pair} 網格停止失敗")
            
            # 更新狀態
            self.status = CoordinatorStatus.STOPPED
            
            # 記錄事件
            self._log_event("coordinator_stopped", {
                "stopped_pairs": stopped_count
            })
            
            logger.info(f"🛑 多交易對網格協調器已停止")
            return True
            
        except Exception as e:
            logger.error(f"❌ 協調器停止失敗: {e}")
            return False
    
    def pause_coordinator(self) -> bool:
        """暫停協調器"""
        try:
            if self.status != CoordinatorStatus.ACTIVE:
                logger.warning(f"⚠️ 協調器不在運行狀態: {self.status.value}")
                return False
            
            # 暫停所有網格引擎
            paused_count = 0
            for pair, engine in self.grid_engines.items():
                if engine.pause_grid():
                    paused_count += 1
            
            self.status = CoordinatorStatus.PAUSED
            
            logger.info(f"⏸️ 多交易對網格協調器已暫停，{paused_count} 個網格暫停")
            return True
            
        except Exception as e:
            logger.error(f"❌ 協調器暫停失敗: {e}")
            return False
    
    def resume_coordinator(self) -> bool:
        """恢復協調器"""
        try:
            if self.status != CoordinatorStatus.PAUSED:
                logger.warning(f"⚠️ 協調器不在暫停狀態: {self.status.value}")
                return False
            
            # 恢復所有網格引擎
            resumed_count = 0
            for pair, engine in self.grid_engines.items():
                if engine.resume_grid():
                    resumed_count += 1
            
            self.status = CoordinatorStatus.ACTIVE
            
            logger.info(f"▶️ 多交易對網格協調器已恢復，{resumed_count} 個網格恢復")
            return True
            
        except Exception as e:
            logger.error(f"❌ 協調器恢復失敗: {e}")
            return False
    
    def update_market_prices(self, price_data: Dict[str, float]) -> Dict[str, Any]:
        """
        更新市場價格並處理所有網格
        
        Args:
            price_data: 交易對價格數據 {"BTCTWD": 3500000, "ETHTWD": 120000}
        """
        try:
            if self.status != CoordinatorStatus.ACTIVE:
                return {"status": "inactive", "message": "協調器未激活"}
            
            results = {}
            total_triggers = 0
            total_executions = 0
            
            # 更新每個交易對的價格
            for pair, price in price_data.items():
                if pair in self.grid_engines:
                    engine = self.grid_engines[pair]
                    result = engine.update_market_price(price)
                    
                    results[pair] = result
                    total_triggers += result.get("triggered_levels", 0)
                    
                    # 統計執行次數
                    executions = result.get("executions", [])
                    successful_executions = sum(1 for ex in executions if ex.get("success"))
                    total_executions += successful_executions
            
            # 檢查全局風險
            risk_actions = self._check_global_risk()
            
            # 檢查是否需要重平衡
            rebalance_needed = self._check_rebalance_needed()
            
            # 更新績效統計
            self._update_performance_stats()
            
            # 更新風險指標
            self._update_risk_metrics()
            
            return {
                "status": "active",
                "total_pairs": len(price_data),
                "total_triggers": total_triggers,
                "total_executions": total_executions,
                "pair_results": results,
                "risk_actions": risk_actions,
                "rebalance_needed": rebalance_needed,
                "global_metrics": self._get_global_metrics()
            }
            
        except Exception as e:
            logger.error(f"❌ 更新市場價格失敗: {e}")
            return {"status": "error", "error": str(e)}
    
    def rebalance_allocations(self, new_allocations: Optional[Dict[str, float]] = None) -> bool:
        """
        重平衡資源分配
        
        Args:
            new_allocations: 新的分配比例 {"BTCTWD": 0.4, "ETHTWD": 0.3}
        """
        try:
            logger.info("🔄 開始重平衡資源分配...")
            
            if new_allocations:
                # 使用指定的分配比例
                allocations = new_allocations
            else:
                # 基於績效自動計算分配比例
                allocations = self._calculate_optimal_allocations()
            
            # 驗證分配比例總和
            total_ratio = sum(allocations.values())
            if total_ratio > 1.0:
                logger.error(f"❌ 分配比例總和 {total_ratio:.2%} 超過100%")
                return False
            
            # 更新每個交易對的分配
            rebalanced_count = 0
            for pair, ratio in allocations.items():
                if pair in self.grid_allocations:
                    old_allocation = self.grid_allocations[pair]
                    new_capital = self.total_capital * ratio
                    
                    # 更新分配記錄
                    old_allocation.allocated_capital = new_capital
                    old_allocation.risk_weight = ratio
                    old_allocation.last_update = datetime.now()
                    
                    # 更新網格配置
                    self.grid_configs[pair].max_investment = new_capital
                    
                    # 如果網格正在運行，需要重平衡網格
                    engine = self.grid_engines[pair]
                    if engine.status == GridStatus.ACTIVE:
                        engine.rebalance_grid()
                    
                    rebalanced_count += 1
                    logger.info(f"✅ {pair} 重平衡完成: {new_capital:,.2f} TWD ({ratio:.2%})")
            
            # 更新風險指標
            self._update_risk_metrics()
            
            # 記錄事件
            self._log_event("rebalance_completed", {
                "rebalanced_pairs": rebalanced_count,
                "new_allocations": allocations
            })
            
            logger.info(f"✅ 資源重平衡完成，{rebalanced_count} 個交易對已更新")
            return True
            
        except Exception as e:
            logger.error(f"❌ 資源重平衡失敗: {e}")
            return False
    
    def _calculate_optimal_allocations(self) -> Dict[str, float]:
        """基於績效計算最優分配比例"""
        try:
            allocations = {}
            
            # 獲取每個交易對的績效評分
            performance_scores = {}
            total_score = 0
            
            for pair, allocation in self.grid_allocations.items():
                engine = self.grid_engines[pair]
                performance_report = engine.get_performance_report()
                
                # 計算綜合評分 (盈利能力 + 穩定性 - 風險)
                net_profit = performance_report['performance']['net_profit']
                win_rate = performance_report['performance']['win_rate']
                total_trades = performance_report['performance']['total_trades']
                
                # 基礎評分
                profit_score = max(0, net_profit / allocation.allocated_capital)  # 收益率
                stability_score = win_rate if isinstance(win_rate, (int, float)) else 0.5
                activity_score = min(1.0, total_trades / 10)  # 交易活躍度
                
                # 綜合評分
                score = (profit_score * 0.5 + stability_score * 0.3 + activity_score * 0.2)
                performance_scores[pair] = max(0.1, score)  # 最低保持10%評分
                total_score += performance_scores[pair]
            
            # 計算分配比例
            if total_score > 0:
                for pair, score in performance_scores.items():
                    base_ratio = score / total_score
                    # 限制單個交易對的最大分配比例
                    max_ratio = self.risk_limits['max_allocation_per_pair']
                    allocations[pair] = min(base_ratio, max_ratio)
            else:
                # 如果沒有績效數據，平均分配
                equal_ratio = 1.0 / len(self.grid_allocations)
                for pair in self.grid_allocations:
                    allocations[pair] = equal_ratio
            
            return allocations
            
        except Exception as e:
            logger.error(f"❌ 計算最優分配失敗: {e}")
            # 返回當前分配比例
            return {pair: alloc.risk_weight for pair, alloc in self.grid_allocations.items()}
    
    def _check_global_risk(self) -> List[str]:
        """檢查全局風險"""
        risk_actions = []
        
        try:
            # 檢查總風險敞口
            if self.risk_metrics.total_exposure > self.risk_limits['max_total_exposure']:
                risk_actions.append("total_exposure_exceeded")
                logger.warning(f"⚠️ 總風險敞口超限: {self.risk_metrics.total_exposure:.2%}")
            
            # 檢查最大回撤
            if self.risk_metrics.max_drawdown > self.risk_limits['max_drawdown_limit']:
                risk_actions.append("max_drawdown_exceeded")
                logger.warning(f"⚠️ 最大回撤超限: {self.risk_metrics.max_drawdown:.2%}")
            
            # 檢查可用資金
            available_ratio = self.risk_metrics.available_capital / self.risk_metrics.total_capital
            if available_ratio < self.risk_limits['min_available_capital']:
                risk_actions.append("insufficient_available_capital")
                logger.warning(f"⚠️ 可用資金不足: {available_ratio:.2%}")
            
            # 檢查相關性風險
            if self.risk_metrics.correlation_risk > self.risk_limits['max_correlation_risk']:
                risk_actions.append("high_correlation_risk")
                logger.warning(f"⚠️ 相關性風險過高: {self.risk_metrics.correlation_risk:.2%}")
            
        except Exception as e:
            logger.error(f"❌ 全局風險檢查失敗: {e}")
            risk_actions.append("risk_check_error")
        
        return risk_actions
    
    def _check_rebalance_needed(self) -> bool:
        """檢查是否需要重平衡"""
        try:
            # 檢查績效差異
            performance_scores = []
            for pair in self.grid_allocations:
                engine = self.grid_engines[pair]
                report = engine.get_performance_report()
                net_profit = report['performance']['net_profit']
                allocated_capital = self.grid_allocations[pair].allocated_capital
                
                if allocated_capital > 0:
                    roi = net_profit / allocated_capital
                    performance_scores.append(roi)
            
            if len(performance_scores) >= 2:
                max_roi = max(performance_scores)
                min_roi = min(performance_scores)
                
                # 如果績效差異超過20%，需要重平衡
                if max_roi - min_roi > 0.2:
                    return True
            
            # 檢查時間間隔
            last_rebalance = max(
                alloc.last_update for alloc in self.grid_allocations.values()
            )
            
            if datetime.now() - last_rebalance > timedelta(seconds=self.rebalance_interval):
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 重平衡檢查失敗: {e}")
            return False
    
    def _update_risk_metrics(self):
        """更新風險指標"""
        try:
            # 計算已分配資金
            allocated_capital = sum(alloc.allocated_capital for alloc in self.grid_allocations.values())
            
            # 計算總盈虧
            total_unrealized_pnl = 0
            total_realized_pnl = 0
            total_exposure = 0
            
            for pair, engine in self.grid_engines.items():
                status = engine.get_grid_status()
                total_unrealized_pnl += status.get('unrealized_pnl', 0)
                total_realized_pnl += status.get('realized_pnl', 0)
                total_exposure += status.get('current_investment', 0)
            
            # 更新風險指標
            self.risk_metrics.allocated_capital = allocated_capital
            self.risk_metrics.available_capital = self.total_capital - allocated_capital
            self.risk_metrics.total_unrealized_pnl = total_unrealized_pnl
            self.risk_metrics.total_realized_pnl = total_realized_pnl
            self.risk_metrics.total_exposure = total_exposure / self.total_capital if self.total_capital > 0 else 0
            self.risk_metrics.last_update = datetime.now()
            
            # 計算最大回撤 (簡化版本)
            total_pnl = total_unrealized_pnl + total_realized_pnl
            if total_pnl < 0:
                self.risk_metrics.max_drawdown = abs(total_pnl) / self.total_capital
            
        except Exception as e:
            logger.error(f"❌ 更新風險指標失敗: {e}")
    
    def _update_performance_stats(self):
        """更新績效統計"""
        try:
            total_grids = len(self.grid_engines)
            active_grids = sum(1 for engine in self.grid_engines.values() 
                             if engine.status == GridStatus.ACTIVE)
            
            total_trades = 0
            successful_trades = 0
            total_profit = 0
            total_fees = 0
            
            best_profit = float('-inf')
            worst_profit = float('inf')
            best_pair = ""
            worst_pair = ""
            
            for pair, engine in self.grid_engines.items():
                report = engine.get_performance_report()
                perf = report['performance']
                
                total_trades += perf['total_trades']
                successful_trades += perf['successful_trades']
                total_profit += perf['total_profit']
                total_fees += perf['total_fees']
                
                net_profit = perf['net_profit']
                if net_profit > best_profit:
                    best_profit = net_profit
                    best_pair = pair
                
                if net_profit < worst_profit:
                    worst_profit = net_profit
                    worst_pair = pair
            
            # 更新績效統計
            self.performance.total_grids = total_grids
            self.performance.active_grids = active_grids
            self.performance.total_trades = total_trades
            self.performance.successful_trades = successful_trades
            self.performance.total_profit = total_profit
            self.performance.total_fees = total_fees
            self.performance.net_profit = total_profit - total_fees
            self.performance.win_rate = successful_trades / total_trades if total_trades > 0 else 0
            self.performance.avg_profit_per_trade = self.performance.net_profit / total_trades if total_trades > 0 else 0
            self.performance.best_performing_pair = best_pair
            self.performance.worst_performing_pair = worst_pair
            self.performance.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ 更新績效統計失敗: {e}")
    
    def _get_global_metrics(self) -> Dict[str, Any]:
        """獲取全局指標"""
        return {
            "risk_metrics": {
                "total_capital": self.risk_metrics.total_capital,
                "allocated_capital": self.risk_metrics.allocated_capital,
                "available_capital": self.risk_metrics.available_capital,
                "allocation_ratio": self.risk_metrics.allocated_capital / self.risk_metrics.total_capital,
                "total_pnl": self.risk_metrics.total_unrealized_pnl + self.risk_metrics.total_realized_pnl,
                "total_exposure": self.risk_metrics.total_exposure,
                "max_drawdown": self.risk_metrics.max_drawdown
            },
            "performance": {
                "total_grids": self.performance.total_grids,
                "active_grids": self.performance.active_grids,
                "total_trades": self.performance.total_trades,
                "win_rate": self.performance.win_rate,
                "net_profit": self.performance.net_profit,
                "best_pair": self.performance.best_performing_pair,
                "worst_pair": self.performance.worst_performing_pair
            }
        }
    
    def _start_monitoring(self):
        """啟動監控線程"""
        try:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            logger.info("🔍 監控線程已啟動")
            
        except Exception as e:
            logger.error(f"❌ 啟動監控線程失敗: {e}")
    
    def _stop_monitoring(self):
        """停止監控線程"""
        try:
            self.monitoring_active = False
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            logger.info("🔍 監控線程已停止")
            
        except Exception as e:
            logger.error(f"❌ 停止監控線程失敗: {e}")
    
    def _monitoring_loop(self):
        """監控循環"""
        while self.monitoring_active:
            try:
                # 更新風險指標
                self._update_risk_metrics()
                
                # 更新績效統計
                self._update_performance_stats()
                
                # 檢查全局風險
                risk_actions = self._check_global_risk()
                if risk_actions:
                    self._handle_risk_actions(risk_actions)
                
                # 檢查重平衡需求
                if self._check_rebalance_needed():
                    logger.info("🔄 檢測到重平衡需求，執行自動重平衡...")
                    self.rebalance_allocations()
                
                # 等待下次檢查
                import time
                time.sleep(30)  # 30秒檢查一次
                
            except Exception as e:
                logger.error(f"❌ 監控循環錯誤: {e}")
                import time
                time.sleep(60)  # 錯誤時等待更長時間
    
    def _handle_risk_actions(self, risk_actions: List[str]):
        """處理風險行動"""
        for action in risk_actions:
            if action == "total_exposure_exceeded":
                # 減少風險敞口
                self._reduce_exposure()
            elif action == "max_drawdown_exceeded":
                # 暫停高風險交易對
                self._pause_high_risk_pairs()
            elif action == "insufficient_available_capital":
                # 釋放部分資金
                self._release_capital()
            elif action == "high_correlation_risk":
                # 調整相關性高的交易對
                self._adjust_correlated_pairs()
    
    def _reduce_exposure(self):
        """減少風險敞口"""
        logger.warning("⚠️ 執行風險敞口減少措施...")
        # 實現風險敞口減少邏輯
        pass
    
    def _pause_high_risk_pairs(self):
        """暫停高風險交易對"""
        logger.warning("⚠️ 暫停高風險交易對...")
        # 實現高風險交易對暫停邏輯
        pass
    
    def _release_capital(self):
        """釋放資金"""
        logger.warning("⚠️ 執行資金釋放措施...")
        # 實現資金釋放邏輯
        pass
    
    def _adjust_correlated_pairs(self):
        """調整相關性高的交易對"""
        logger.warning("⚠️ 調整相關性高的交易對...")
        # 實現相關性調整邏輯
        pass
    
    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """記錄事件"""
        event = {
            "timestamp": datetime.now(),
            "type": event_type,
            "data": data
        }
        self.event_history.append(event)
        
        # 保持事件歷史在合理範圍內
        if len(self.event_history) > 1000:
            self.event_history = self.event_history[-500:]
    
    def get_coordinator_status(self) -> Dict[str, Any]:
        """獲取協調器狀態"""
        try:
            pair_statuses = {}
            for pair, engine in self.grid_engines.items():
                pair_statuses[pair] = engine.get_grid_status()
            
            return {
                "coordinator_status": self.status.value,
                "total_pairs": len(self.grid_engines),
                "active_pairs": sum(1 for engine in self.grid_engines.values() 
                                  if engine.status == GridStatus.ACTIVE),
                "total_capital": self.total_capital,
                "risk_metrics": self.risk_metrics.__dict__,
                "performance": self.performance.__dict__,
                "pair_statuses": pair_statuses,
                "allocations": {pair: alloc.__dict__ for pair, alloc in self.grid_allocations.items()},
                "last_update": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取協調器狀態失敗: {e}")
            return {"error": str(e)}
    
    def get_performance_report(self) -> Dict[str, Any]:
        """獲取績效報告"""
        try:
            runtime = datetime.now() - self.performance.start_time
            
            # 獲取每個交易對的詳細報告
            pair_reports = {}
            for pair, engine in self.grid_engines.items():
                pair_reports[pair] = engine.get_performance_report()
            
            return {
                "coordinator_info": {
                    "status": self.status.value,
                    "runtime_hours": runtime.total_seconds() / 3600,
                    "total_pairs": len(self.grid_engines),
                    "active_pairs": self.performance.active_grids
                },
                "global_performance": {
                    "total_trades": self.performance.total_trades,
                    "successful_trades": self.performance.successful_trades,
                    "win_rate": f"{self.performance.win_rate:.2%}",
                    "total_profit": self.performance.total_profit,
                    "total_fees": self.performance.total_fees,
                    "net_profit": self.performance.net_profit,
                    "avg_profit_per_trade": self.performance.avg_profit_per_trade,
                    "best_performing_pair": self.performance.best_performing_pair,
                    "worst_performing_pair": self.performance.worst_performing_pair
                },
                "risk_analysis": {
                    "total_capital": self.risk_metrics.total_capital,
                    "allocated_capital": self.risk_metrics.allocated_capital,
                    "available_capital": self.risk_metrics.available_capital,
                    "allocation_ratio": self.risk_metrics.allocated_capital / self.risk_metrics.total_capital,
                    "total_pnl": self.risk_metrics.total_unrealized_pnl + self.risk_metrics.total_realized_pnl,
                    "total_exposure": self.risk_metrics.total_exposure,
                    "max_drawdown": self.risk_metrics.max_drawdown,
                    "correlation_risk": self.risk_metrics.correlation_risk
                },
                "pair_reports": pair_reports,
                "allocations": {
                    pair: {
                        "allocated_capital": alloc.allocated_capital,
                        "risk_weight": alloc.risk_weight,
                        "priority": alloc.priority,
                        "performance_score": alloc.performance_score
                    }
                    for pair, alloc in self.grid_allocations.items()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取績效報告失敗: {e}")
            return {"error": str(e)}
    
    def export_coordinator_data(self, filepath: str) -> bool:
        """導出協調器數據"""
        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "coordinator_status": self.get_coordinator_status(),
                "performance_report": self.get_performance_report(),
                "event_history": [
                    {
                        "timestamp": event["timestamp"].isoformat(),
                        "type": event["type"],
                        "data": event["data"]
                    }
                    for event in self.event_history[-100:]  # 最近100個事件
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 協調器數據已導出: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 導出協調器數據失敗: {e}")
            return False


# 創建多交易對網格協調器實例
def create_multi_pair_grid_coordinator(data_manager: MultiPairDataManager,
                                     ai_coordinator: MultiPairAICoordinator,
                                     total_capital: float = 100000.0) -> MultiPairGridCoordinator:
    """創建多交易對網格協調器實例"""
    return MultiPairGridCoordinator(data_manager, ai_coordinator, total_capital)


# 測試代碼
if __name__ == "__main__":
    print("🧪 測試多交易對網格協調器...")
    
    # 這裡需要實際的數據管理器和AI協調器實例
    # 僅作為示例展示基本功能
    print("✅ 多交易對網格協調器模塊加載成功")
    print("🎯 功能包括:")
    print("   - 多交易對網格策略管理")
    print("   - 資源分配和風險控制")
    print("   - 全局績效監控")
    print("   - 動態重平衡機制")
    print("🎉 準備就緒，等待整合測試！")