#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實時監控和績效分析系統 - 任務7.2實現
建立多交易對的實時價格和持倉顯示，實現績效指標計算和可視化監控
"""

import sys
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
import threading
import time

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from src.trading.dynamic_position_manager import DynamicPositionManager
    from src.monitoring.simple_risk_monitor import SimpleRiskMonitor
    AIMAX_MODULES_AVAILABLE = True
except ImportError:
    AIMAX_MODULES_AVAILABLE = False
    print("⚠️ AImax模塊未完全可用，將使用模擬模式")

logger = logging.getLogger(__name__)

class PerformanceMetricType(Enum):
    """績效指標類型"""
    RETURN = "return"                    # 收益率
    SHARPE_RATIO = "sharpe_ratio"       # 夏普比率
    MAX_DRAWDOWN = "max_drawdown"       # 最大回撤
    WIN_RATE = "win_rate"               # 勝率
    PROFIT_FACTOR = "profit_factor"     # 盈利因子
    VOLATILITY = "volatility"           # 波動率
    CALMAR_RATIO = "calmar_ratio"       # 卡瑪比率
    SORTINO_RATIO = "sortino_ratio"     # 索提諾比率

@dataclass
class RealTimePrice:
    """實時價格數據"""
    pair: str
    price: float
    change_24h: float
    change_percent_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime
    bid: float = 0.0
    ask: float = 0.0
    spread: float = 0.0

@dataclass
class PositionInfo:
    """持倉信息"""
    pair: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_return: float
    holding_time: timedelta
    strategy_type: str
    ai_confidence: float
    risk_score: float
    last_update: datetime

@dataclass
class PerformanceMetrics:
    """績效指標"""
    pair: str
    total_return: float = 0.0
    annualized_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    volatility: float = 0.0
    calmar_ratio: float = 0.0
    sortino_ratio: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    last_update: datetime = None

@dataclass
class StrategyStatus:
    """策略執行狀態"""
    pair: str
    strategy_name: str
    is_active: bool
    start_time: datetime
    last_signal_time: datetime
    signals_count: int
    executed_trades: int
    pending_orders: int
    ai_decisions: List[Dict[str, Any]] = field(default_factory=list)
    performance: PerformanceMetrics = None
    error_count: int = 0
    last_error: str = ""

class RealTimePerformanceMonitor:
    """實時監控和績效分析系統"""
    
    def __init__(self):
        # 數據存儲
        self.real_time_prices: Dict[str, RealTimePrice] = {}
        self.positions: Dict[str, PositionInfo] = {}
        self.performance_metrics: Dict[str, PerformanceMetrics] = {}
        self.strategy_statuses: Dict[str, StrategyStatus] = {}
        
        # 歷史數據存儲
        self.price_history: Dict[str, List[RealTimePrice]] = {}
        self.pnl_history: Dict[str, List[Tuple[datetime, float]]] = {}
        self.trade_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # 監控配置
        self.monitored_pairs = ["BTCTWD", "ETHTWD", "LTCTWD", "BCHTWD", "ADATWD", "DOTTWD"]
        self.update_interval = 1.0  # 1秒更新間隔
        self.history_retention_hours = 24  # 保留24小時歷史數據
        
        # 監控狀態
        self.is_monitoring = False
        self.monitor_thread = None
        self.last_update_time = None
        
        # 系統組件
        self.position_manager = None
        self.risk_monitor = None
        
        # 初始化系統組件
        self.init_components()
        
        logger.info("📊 實時監控和績效分析系統初始化完成")
    
    def init_components(self):
        """初始化系統組件"""
        try:
            if AIMAX_MODULES_AVAILABLE:
                self.position_manager = DynamicPositionManager()
                self.risk_monitor = SimpleRiskMonitor()
                logger.info("✅ 系統組件初始化成功")
            else:
                logger.warning("⚠️ 使用模擬模式")
        except Exception as e:
            logger.error(f"❌ 初始化系統組件失敗: {e}")
    
    def start_monitoring(self):
        """啟動實時監控"""
        if self.is_monitoring:
            logger.warning("⚠️ 監控已經在運行中")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("🚀 實時監控已啟動")
    
    def stop_monitoring(self):
        """停止實時監控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        
        logger.info("⏹️ 實時監控已停止")
    
    def _monitoring_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                start_time = time.time()
                
                # 更新實時數據
                self.update_real_time_data()
                
                # 更新績效指標
                self.update_performance_metrics()
                
                # 清理過期數據
                self.cleanup_expired_data()
                
                # 記錄更新時間
                self.last_update_time = datetime.now()
                
                # 控制更新頻率
                elapsed = time.time() - start_time
                sleep_time = max(0, self.update_interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"❌ 監控循環錯誤: {e}")
                time.sleep(1.0)  # 錯誤時短暫暫停
    
    def update_real_time_data(self):
        """更新實時數據"""
        try:
            # 更新實時價格數據
            for pair in self.monitored_pairs:
                price_data = self.generate_real_time_price(pair)
                self.real_time_prices[pair] = price_data
                
                # 保存價格歷史
                if pair not in self.price_history:
                    self.price_history[pair] = []
                self.price_history[pair].append(price_data)
            
            # 更新持倉信息
            self.update_position_info()
            
            # 更新策略狀態
            self.update_strategy_status()
            
        except Exception as e:
            logger.error(f"❌ 更新實時數據失敗: {e}")
    
    def generate_real_time_price(self, pair: str) -> RealTimePrice:
        """生成實時價格數據（模擬）"""
        import random
        
        # 基礎價格
        base_prices = {
            "BTCTWD": 1500000,
            "ETHTWD": 100000,
            "LTCTWD": 3000,
            "BCHTWD": 15000,
            "ADATWD": 20,
            "DOTTWD": 200
        }
        
        base_price = base_prices.get(pair, 10000)
        
        # 添加隨機波動
        current_time = datetime.now()
        seed = hash(pair + str(current_time.minute * 60 + current_time.second))
        random.seed(seed)
        
        price_change = random.uniform(-0.02, 0.02)  # ±2%波動
        current_price = base_price * (1 + price_change)
        
        # 24小時變化
        change_24h = random.uniform(-0.1, 0.1)  # ±10%
        change_percent_24h = change_24h * 100
        
        # 其他數據
        volume_24h = random.uniform(1000000, 100000000)
        high_24h = current_price * random.uniform(1.01, 1.05)
        low_24h = current_price * random.uniform(0.95, 0.99)
        
        # 買賣價差
        spread_percent = random.uniform(0.001, 0.005)  # 0.1%-0.5%
        spread = current_price * spread_percent
        bid = current_price - spread / 2
        ask = current_price + spread / 2
        
        return RealTimePrice(
            pair=pair,
            price=current_price,
            change_24h=change_24h * base_price,
            change_percent_24h=change_percent_24h,
            volume_24h=volume_24h,
            high_24h=high_24h,
            low_24h=low_24h,
            timestamp=current_time,
            bid=bid,
            ask=ask,
            spread=spread
        )
    
    def update_position_info(self):
        """更新持倉信息"""
        try:
            for pair in self.monitored_pairs:
                if pair in self.real_time_prices:
                    current_price = self.real_time_prices[pair].price
                    
                    # 模擬持倉數據
                    import random
                    random.seed(hash(pair + str(datetime.now().hour)))
                    
                    if random.random() > 0.3:  # 70%概率有持倉
                        entry_price = current_price * random.uniform(0.95, 1.05)
                        size = random.uniform(0.01, 0.1)
                        
                        unrealized_pnl = (current_price - entry_price) * size
                        unrealized_return = (current_price - entry_price) / entry_price
                        
                        holding_time = timedelta(hours=random.uniform(1, 48))
                        
                        position = PositionInfo(
                            pair=pair,
                            size=size,
                            entry_price=entry_price,
                            current_price=current_price,
                            unrealized_pnl=unrealized_pnl,
                            unrealized_return=unrealized_return,
                            holding_time=holding_time,
                            strategy_type=random.choice(["grid", "dca", "arbitrage"]),
                            ai_confidence=random.uniform(0.4, 0.9),
                            risk_score=random.uniform(0.1, 0.8),
                            last_update=datetime.now()
                        )
                        
                        self.positions[pair] = position
                        
                        # 保存盈虧歷史
                        if pair not in self.pnl_history:
                            self.pnl_history[pair] = []
                        self.pnl_history[pair].append((datetime.now(), unrealized_pnl))
                    
        except Exception as e:
            logger.error(f"❌ 更新持倉信息失敗: {e}")
    
    def update_strategy_status(self):
        """更新策略執行狀態"""
        try:
            for pair in self.monitored_pairs:
                import random
                random.seed(hash(pair + str(datetime.now().minute)))
                
                if pair not in self.strategy_statuses:
                    # 創建新的策略狀態
                    strategy_status = StrategyStatus(
                        pair=pair,
                        strategy_name=random.choice(["智能網格", "AI-DCA", "套利策略"]),
                        is_active=random.choice([True, False]),
                        start_time=datetime.now() - timedelta(hours=random.uniform(1, 24)),
                        last_signal_time=datetime.now() - timedelta(minutes=random.uniform(1, 60)),
                        signals_count=random.randint(10, 100),
                        executed_trades=random.randint(5, 50),
                        pending_orders=random.randint(0, 5),
                        performance=self.performance_metrics.get(pair),
                        error_count=random.randint(0, 3),
                        last_error="" if random.random() > 0.2 else "模擬錯誤信息"
                    )
                    
                    # 添加AI決策歷史
                    for i in range(random.randint(3, 8)):
                        ai_decision = {
                            "timestamp": datetime.now() - timedelta(minutes=random.uniform(5, 120)),
                            "decision": random.choice(["買入", "賣出", "持有", "觀望"]),
                            "confidence": random.uniform(0.4, 0.95),
                            "reasoning": f"基於技術分析和市場條件的AI決策 #{i+1}",
                            "executed": random.choice([True, False])
                        }
                        strategy_status.ai_decisions.append(ai_decision)
                    
                    self.strategy_statuses[pair] = strategy_status
                else:
                    # 更新現有狀態
                    status = self.strategy_statuses[pair]
                    if random.random() > 0.8:  # 20%概率更新信號
                        status.last_signal_time = datetime.now()
                        status.signals_count += 1
                        
                        # 添加新的AI決策
                        new_decision = {
                            "timestamp": datetime.now(),
                            "decision": random.choice(["買入", "賣出", "持有", "觀望"]),
                            "confidence": random.uniform(0.4, 0.95),
                            "reasoning": f"實時AI決策更新",
                            "executed": random.choice([True, False])
                        }
                        status.ai_decisions.append(new_decision)
                        
                        # 保持最近10個決策
                        if len(status.ai_decisions) > 10:
                            status.ai_decisions = status.ai_decisions[-10:]
                    
        except Exception as e:
            logger.error(f"❌ 更新策略狀態失敗: {e}")
    
    def update_performance_metrics(self):
        """更新績效指標"""
        try:
            for pair in self.monitored_pairs:
                if pair in self.pnl_history and len(self.pnl_history[pair]) > 1:
                    metrics = self.calculate_performance_metrics(pair)
                    self.performance_metrics[pair] = metrics
                    
                    # 更新策略狀態中的績效
                    if pair in self.strategy_statuses:
                        self.strategy_statuses[pair].performance = metrics
                        
        except Exception as e:
            logger.error(f"❌ 更新績效指標失敗: {e}")
    
    def calculate_performance_metrics(self, pair: str) -> PerformanceMetrics:
        """計算績效指標"""
        try:
            if pair not in self.pnl_history or len(self.pnl_history[pair]) < 2:
                return PerformanceMetrics(pair=pair, last_update=datetime.now())
            
            # 獲取盈虧數據
            pnl_data = [pnl for _, pnl in self.pnl_history[pair]]
            returns = np.diff(pnl_data)
            
            if len(returns) == 0:
                return PerformanceMetrics(pair=pair, last_update=datetime.now())
            
            # 基本統計
            total_return = pnl_data[-1] - pnl_data[0] if len(pnl_data) > 1 else 0
            
            # 年化收益率（假設252個交易日）
            if len(pnl_data) > 1:
                periods = len(pnl_data)
                annualized_return = (total_return / abs(pnl_data[0])) * (252 / periods) if pnl_data[0] != 0 else 0
            else:
                annualized_return = 0
            
            # 波動率
            volatility = np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0
            
            # 夏普比率（假設無風險利率為2%）
            risk_free_rate = 0.02
            sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
            
            # 最大回撤
            cumulative_returns = np.cumsum(returns)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = cumulative_returns - running_max
            max_drawdown = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0
            
            # 卡瑪比率
            calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 0
            
            # 下行波動率（用於索提諾比率）
            negative_returns = returns[returns < 0]
            downside_volatility = np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 1 else 0
            
            # 索提諾比率
            sortino_ratio = (annualized_return - risk_free_rate) / downside_volatility if downside_volatility > 0 else 0
            
            # 交易統計（模擬）
            import random
            random.seed(hash(pair + str(datetime.now().hour)))
            
            total_trades = random.randint(10, 100)
            winning_trades = int(total_trades * random.uniform(0.4, 0.7))
            losing_trades = total_trades - winning_trades
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            avg_win = random.uniform(1000, 5000)
            avg_loss = random.uniform(-3000, -500)
            profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else 0
            
            largest_win = avg_win * random.uniform(1.5, 3.0)
            largest_loss = avg_loss * random.uniform(1.5, 3.0)
            
            consecutive_wins = random.randint(1, 8)
            consecutive_losses = random.randint(1, 5)
            
            return PerformanceMetrics(
                pair=pair,
                total_return=total_return,
                annualized_return=annualized_return,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                win_rate=win_rate,
                profit_factor=profit_factor,
                volatility=volatility,
                calmar_ratio=calmar_ratio,
                sortino_ratio=sortino_ratio,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                avg_win=avg_win,
                avg_loss=avg_loss,
                largest_win=largest_win,
                largest_loss=largest_loss,
                consecutive_wins=consecutive_wins,
                consecutive_losses=consecutive_losses,
                last_update=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ 計算績效指標失敗: {e}")
            return PerformanceMetrics(pair=pair, last_update=datetime.now())
    
    def cleanup_expired_data(self):
        """清理過期數據"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.history_retention_hours)
            
            # 清理價格歷史
            for pair in self.price_history:
                self.price_history[pair] = [
                    price for price in self.price_history[pair]
                    if price.timestamp > cutoff_time
                ]
            
            # 清理盈虧歷史
            for pair in self.pnl_history:
                self.pnl_history[pair] = [
                    (timestamp, pnl) for timestamp, pnl in self.pnl_history[pair]
                    if timestamp > cutoff_time
                ]
                
        except Exception as e:
            logger.error(f"❌ 清理過期數據失敗: {e}")
    
    def get_real_time_summary(self) -> Dict[str, Any]:
        """獲取實時監控摘要"""
        try:
            summary = {
                "monitoring_status": "active" if self.is_monitoring else "inactive",
                "last_update": self.last_update_time.isoformat() if self.last_update_time else None,
                "monitored_pairs": len(self.monitored_pairs),
                "active_positions": len(self.positions),
                "total_unrealized_pnl": sum(pos.unrealized_pnl for pos in self.positions.values()),
                "active_strategies": sum(1 for status in self.strategy_statuses.values() if status.is_active),
                "total_signals": sum(status.signals_count for status in self.strategy_statuses.values()),
                "total_trades": sum(status.executed_trades for status in self.strategy_statuses.values()),
                "pairs_data": {}
            }
            
            # 添加每個交易對的詳細信息
            for pair in self.monitored_pairs:
                pair_data = {
                    "price": self.real_time_prices.get(pair),
                    "position": self.positions.get(pair),
                    "performance": self.performance_metrics.get(pair),
                    "strategy_status": self.strategy_statuses.get(pair)
                }
                summary["pairs_data"][pair] = pair_data
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ 獲取實時監控摘要失敗: {e}")
            return {}
    
    def get_performance_report(self, pair: str = None) -> Dict[str, Any]:
        """獲取績效報告"""
        try:
            if pair:
                # 單個交易對報告
                if pair not in self.performance_metrics:
                    return {"error": f"交易對 {pair} 沒有績效數據"}
                
                metrics = self.performance_metrics[pair]
                return {
                    "pair": pair,
                    "metrics": metrics,
                    "price_history": self.price_history.get(pair, [])[-100:],  # 最近100個價格點
                    "pnl_history": self.pnl_history.get(pair, [])[-100:],      # 最近100個盈虧點
                    "strategy_status": self.strategy_statuses.get(pair)
                }
            else:
                # 全部交易對報告
                report = {
                    "summary": {
                        "total_pairs": len(self.monitored_pairs),
                        "active_pairs": len(self.positions),
                        "total_unrealized_pnl": sum(pos.unrealized_pnl for pos in self.positions.values()),
                        "best_performer": None,
                        "worst_performer": None,
                        "avg_return": 0.0,
                        "total_trades": sum(status.executed_trades for status in self.strategy_statuses.values())
                    },
                    "pairs": {}
                }
                
                # 找出最佳和最差表現者
                returns = []
                for pair, metrics in self.performance_metrics.items():
                    returns.append((pair, metrics.total_return))
                
                if returns:
                    returns.sort(key=lambda x: x[1], reverse=True)
                    report["summary"]["best_performer"] = returns[0]
                    report["summary"]["worst_performer"] = returns[-1]
                    report["summary"]["avg_return"] = sum(r[1] for r in returns) / len(returns)
                
                # 添加每個交易對的詳細信息
                for pair in self.monitored_pairs:
                    report["pairs"][pair] = {
                        "metrics": self.performance_metrics.get(pair),
                        "current_position": self.positions.get(pair),
                        "strategy_status": self.strategy_statuses.get(pair)
                    }
                
                return report
                
        except Exception as e:
            logger.error(f"❌ 獲取績效報告失敗: {e}")
            return {"error": str(e)}
    
    def get_ai_decision_visualization(self) -> Dict[str, Any]:
        """獲取AI決策過程可視化數據"""
        try:
            visualization_data = {
                "timestamp": datetime.now().isoformat(),
                "pairs": {}
            }
            
            for pair, status in self.strategy_statuses.items():
                if status.ai_decisions:
                    # 最近的AI決策
                    recent_decisions = sorted(status.ai_decisions, key=lambda x: x["timestamp"], reverse=True)[:5]
                    
                    # 決策統計
                    decision_counts = {}
                    confidence_levels = []
                    execution_rate = 0
                    
                    for decision in status.ai_decisions:
                        decision_type = decision["decision"]
                        decision_counts[decision_type] = decision_counts.get(decision_type, 0) + 1
                        confidence_levels.append(decision["confidence"])
                        if decision["executed"]:
                            execution_rate += 1
                    
                    execution_rate = execution_rate / len(status.ai_decisions) if status.ai_decisions else 0
                    avg_confidence = sum(confidence_levels) / len(confidence_levels) if confidence_levels else 0
                    
                    visualization_data["pairs"][pair] = {
                        "recent_decisions": recent_decisions,
                        "decision_distribution": decision_counts,
                        "avg_confidence": avg_confidence,
                        "execution_rate": execution_rate,
                        "total_decisions": len(status.ai_decisions),
                        "strategy_active": status.is_active,
                        "last_signal_time": status.last_signal_time.isoformat() if status.last_signal_time else None
                    }
            
            return visualization_data
            
        except Exception as e:
            logger.error(f"❌ 獲取AI決策可視化數據失敗: {e}")
            return {"error": str(e)}

# 創建實時監控實例
def create_realtime_performance_monitor() -> RealTimePerformanceMonitor:
    """創建實時監控和績效分析實例"""
    return RealTimePerformanceMonitor()

# 測試代碼
if __name__ == "__main__":
    def test_realtime_monitor():
        """測試實時監控系統"""
        print("🧪 測試實時監控和績效分析系統...")
        
        # 創建監控實例
        monitor = create_realtime_performance_monitor()
        
        # 啟動監控
        monitor.start_monitoring()
        
        try:
            # 運行5秒
            time.sleep(5)
            
            # 獲取實時摘要
            summary = monitor.get_real_time_summary()
            print(f"📊 實時摘要: 監控 {summary.get('monitored_pairs', 0)} 個交易對")
            print(f"   活躍倉位: {summary.get('active_positions', 0)}")
            print(f"   總未實現盈虧: {summary.get('total_unrealized_pnl', 0):+,.0f}")
            print(f"   活躍策略: {summary.get('active_strategies', 0)}")
            
            # 獲取績效報告
            report = monitor.get_performance_report()
            print(f"📈 績效報告: 總交易對 {report.get('summary', {}).get('total_pairs', 0)}")
            print(f"   平均收益率: {report.get('summary', {}).get('avg_return', 0):+.2f}")
            
            # 獲取AI決策可視化
            ai_viz = monitor.get_ai_decision_visualization()
            print(f"🧠 AI決策可視化: {len(ai_viz.get('pairs', {}))} 個交易對有AI決策數據")
            
            print("✅ 實時監控系統測試完成")
            
        finally:
            # 停止監控
            monitor.stop_monitoring()
    
    # 運行測試
    test_realtime_monitor()