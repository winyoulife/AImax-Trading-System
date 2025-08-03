#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實時交易記錄和分析系統
創建實時交易日誌、績效追蹤和AI決策準確率監控
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class AIDecisionRecord:
    """AI決策記錄"""
    timestamp: datetime
    market: str
    decision: str  # BUY, SELL, HOLD
    confidence: float
    ai_signals: Dict[str, Any]
    market_data: Dict[str, Any]
    technical_indicators: Dict[str, Any]
    reasoning: str
    
@dataclass
class TradeRecord:
    """交易記錄"""
    trade_id: str
    timestamp: datetime
    market: str
    side: str  # buy, sell
    volume: float
    entry_price: float
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    commission: float = 0.0
    status: str = "open"  # open, closed, cancelled
    ai_decision_id: Optional[str] = None
    
@dataclass
class PerformanceMetrics:
    """績效指標"""
    timestamp: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_pct: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    ai_accuracy: float

class LiveTradingRecorder:
    """實時交易記錄器"""
    
    def __init__(self, session_id: str = None):
        """
        初始化交易記錄器
        
        Args:
            session_id: 交易會話ID
        """
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 記錄存儲
        self.ai_decisions: List[AIDecisionRecord] = []
        self.trade_records: List[TradeRecord] = []
        self.performance_history: List[PerformanceMetrics] = []
        
        # 實時統計
        self.current_balance = 10000.0  # 初始資金
        self.initial_balance = 10000.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0
        
        # AI準確率追蹤
        self.ai_predictions: Dict[str, Dict[str, Any]] = {}  # decision_id -> prediction_data
        self.prediction_outcomes: List[Dict[str, Any]] = []
        
        # 創建日誌目錄
        self.log_dir = Path(f"AImax/logs/live_trading/{self.session_id}")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📊 實時交易記錄器初始化完成 - 會話: {self.session_id}")
    
    def record_ai_decision(self, decision: str, confidence: float, 
                          ai_signals: Dict[str, Any], market_data: Dict[str, Any],
                          technical_indicators: Dict[str, Any], reasoning: str,
                          market: str = "btctwd") -> str:
        """
        記錄AI決策
        
        Args:
            decision: 決策 (BUY/SELL/HOLD)
            confidence: 信心度
            ai_signals: AI信號
            market_data: 市場數據
            technical_indicators: 技術指標
            reasoning: 決策理由
            market: 市場
            
        Returns:
            決策記錄ID
        """
        try:
            decision_id = f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            ai_record = AIDecisionRecord(
                timestamp=datetime.now(),
                market=market,
                decision=decision,
                confidence=confidence,
                ai_signals=ai_signals,
                market_data=market_data,
                technical_indicators=technical_indicators,
                reasoning=reasoning
            )
            
            self.ai_decisions.append(ai_record)
            
            # 如果是交易決策，記錄預測
            if decision in ['BUY', 'SELL']:
                self.ai_predictions[decision_id] = {
                    'decision': decision,
                    'confidence': confidence,
                    'timestamp': datetime.now(),
                    'market_price': market_data.get('current_price', 0),
                    'prediction_verified': False
                }
            
            logger.info(f"🧠 AI決策記錄 - {decision} (信心度: {confidence:.1%})")
            return decision_id
            
        except Exception as e:
            logger.error(f"❌ 記錄AI決策失敗: {e}")
            return ""
    
    def record_trade_execution(self, trade_id: str, market: str, side: str,
                             volume: float, price: float, commission: float = 0.0,
                             ai_decision_id: str = None) -> None:
        """
        記錄交易執行
        
        Args:
            trade_id: 交易ID
            market: 市場
            side: 方向 (buy/sell)
            volume: 數量
            price: 價格
            commission: 手續費
            ai_decision_id: 關聯的AI決策ID
        """
        try:
            trade_record = TradeRecord(
                trade_id=trade_id,
                timestamp=datetime.now(),
                market=market,
                side=side,
                volume=volume,
                entry_price=price,
                commission=commission,
                ai_decision_id=ai_decision_id
            )
            
            self.trade_records.append(trade_record)
            self.total_trades += 1
            
            # 更新餘額
            if side == 'buy':
                cost = volume * price + commission
                self.current_balance -= cost
            else:  # sell
                revenue = volume * price - commission
                self.current_balance += revenue
            
            logger.info(f"💰 交易執行記錄 - {side.upper()} {volume} @ {price:.0f}")
            
        except Exception as e:
            logger.error(f"❌ 記錄交易執行失敗: {e}")
    
    def record_trade_close(self, trade_id: str, exit_price: float, 
                          exit_timestamp: datetime = None) -> None:
        """
        記錄交易平倉
        
        Args:
            trade_id: 交易ID
            exit_price: 平倉價格
            exit_timestamp: 平倉時間
        """
        try:
            # 找到對應的交易記錄
            trade_record = None
            for record in self.trade_records:
                if record.trade_id == trade_id and record.status == "open":
                    trade_record = record
                    break
            
            if not trade_record:
                logger.warning(f"⚠️ 未找到交易記錄: {trade_id}")
                return
            
            # 更新交易記錄
            trade_record.exit_price = exit_price
            trade_record.exit_timestamp = exit_timestamp or datetime.now()
            trade_record.status = "closed"
            
            # 計算�nl
            if trade_record.side == 'buy':
                pnl = (exit_price - trade_record.entry_price) * trade_record.volume
            else:  # sell
                pnl = (trade_record.entry_price - exit_price) * trade_record.volume
            
            pnl -= trade_record.commission  # 扣除手續費
            trade_record.pnl = pnl
            trade_record.pnl_pct = pnl / (trade_record.entry_price * trade_record.volume) * 100
            
            # 更新統計
            self.total_pnl += pnl
            if pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1
            
            # 驗證AI預測
            if trade_record.ai_decision_id:
                self._verify_ai_prediction(trade_record.ai_decision_id, pnl > 0)
            
            logger.info(f"📈 交易平倉記錄 - PnL: {pnl:.2f} ({trade_record.pnl_pct:.2f}%)")
            
        except Exception as e:
            logger.error(f"❌ 記錄交易平倉失敗: {e}")
    
    def _verify_ai_prediction(self, decision_id: str, was_profitable: bool) -> None:
        """驗證AI預測準確性"""
        try:
            if decision_id in self.ai_predictions:
                prediction = self.ai_predictions[decision_id]
                prediction['prediction_verified'] = True
                prediction['was_correct'] = was_profitable
                prediction['verification_time'] = datetime.now()
                
                # 記錄預測結果
                outcome = {
                    'decision_id': decision_id,
                    'predicted_direction': prediction['decision'],
                    'confidence': prediction['confidence'],
                    'was_correct': was_profitable,
                    'timestamp': prediction['timestamp']
                }
                self.prediction_outcomes.append(outcome)
                
                logger.info(f"🎯 AI預測驗證 - {'✅ 正確' if was_profitable else '❌ 錯誤'}")
                
        except Exception as e:
            logger.error(f"❌ 驗證AI預測失敗: {e}")
    
    def calculate_performance_metrics(self) -> PerformanceMetrics:
        """計算績效指標"""
        try:
            # 基本統計
            total_trades = len([t for t in self.trade_records if t.status == "closed"])
            winning_trades = len([t for t in self.trade_records if t.status == "closed" and t.pnl and t.pnl > 0])
            losing_trades = len([t for t in self.trade_records if t.status == "closed" and t.pnl and t.pnl <= 0])
            
            win_rate = winning_trades / max(1, total_trades)
            
            # PnL統計
            closed_trades = [t for t in self.trade_records if t.status == "closed" and t.pnl is not None]
            total_pnl = sum(t.pnl for t in closed_trades)
            total_pnl_pct = (self.current_balance - self.initial_balance) / self.initial_balance * 100
            
            # 平均盈虧
            winning_pnls = [t.pnl for t in closed_trades if t.pnl > 0]
            losing_pnls = [t.pnl for t in closed_trades if t.pnl <= 0]
            
            avg_win = np.mean(winning_pnls) if winning_pnls else 0
            avg_loss = np.mean(losing_pnls) if losing_pnls else 0
            
            # 盈虧比
            profit_factor = abs(sum(winning_pnls) / sum(losing_pnls)) if losing_pnls and sum(losing_pnls) != 0 else 0
            
            # 最大回撤
            balance_history = [self.initial_balance]
            running_balance = self.initial_balance
            
            for trade in sorted(closed_trades, key=lambda x: x.timestamp):
                running_balance += trade.pnl
                balance_history.append(running_balance)
            
            peak = self.initial_balance
            max_drawdown = 0
            for balance in balance_history:
                if balance > peak:
                    peak = balance
                drawdown = (peak - balance) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # 夏普比率（簡化版）
            if closed_trades:
                returns = [t.pnl_pct for t in closed_trades if t.pnl_pct is not None]
                if returns and len(returns) > 1:
                    sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
                else:
                    sharpe_ratio = 0
            else:
                sharpe_ratio = 0
            
            # AI準確率
            verified_predictions = [p for p in self.prediction_outcomes]
            ai_accuracy = np.mean([p['was_correct'] for p in verified_predictions]) if verified_predictions else 0
            
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                total_pnl=total_pnl,
                total_pnl_pct=total_pnl_pct,
                avg_win=avg_win,
                avg_loss=avg_loss,
                profit_factor=profit_factor,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                ai_accuracy=ai_accuracy
            )
            
            self.performance_history.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"❌ 計算績效指標失敗: {e}")
            return PerformanceMetrics(
                timestamp=datetime.now(),
                total_trades=0, winning_trades=0, losing_trades=0,
                win_rate=0, total_pnl=0, total_pnl_pct=0,
                avg_win=0, avg_loss=0, profit_factor=0,
                max_drawdown=0, sharpe_ratio=0, ai_accuracy=0
            )
    
    def get_ai_accuracy_analysis(self) -> Dict[str, Any]:
        """獲取AI準確率分析"""
        try:
            if not self.prediction_outcomes:
                return {'total_predictions': 0, 'accuracy': 0, 'confidence_analysis': {}}
            
            # 總體準確率
            total_predictions = len(self.prediction_outcomes)
            correct_predictions = sum(1 for p in self.prediction_outcomes if p['was_correct'])
            overall_accuracy = correct_predictions / total_predictions
            
            # 按信心度分析
            confidence_ranges = [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)]
            confidence_analysis = {}
            
            for min_conf, max_conf in confidence_ranges:
                range_predictions = [p for p in self.prediction_outcomes 
                                   if min_conf <= p['confidence'] < max_conf]
                
                if range_predictions:
                    range_accuracy = sum(1 for p in range_predictions if p['was_correct']) / len(range_predictions)
                    confidence_analysis[f"{min_conf:.1f}-{max_conf:.1f}"] = {
                        'count': len(range_predictions),
                        'accuracy': range_accuracy
                    }
            
            # 按決策類型分析
            buy_predictions = [p for p in self.prediction_outcomes if p['predicted_direction'] == 'BUY']
            sell_predictions = [p for p in self.prediction_outcomes if p['predicted_direction'] == 'SELL']
            
            buy_accuracy = sum(1 for p in buy_predictions if p['was_correct']) / len(buy_predictions) if buy_predictions else 0
            sell_accuracy = sum(1 for p in sell_predictions if p['was_correct']) / len(sell_predictions) if sell_predictions else 0
            
            return {
                'total_predictions': total_predictions,
                'correct_predictions': correct_predictions,
                'overall_accuracy': overall_accuracy,
                'buy_accuracy': buy_accuracy,
                'sell_accuracy': sell_accuracy,
                'confidence_analysis': confidence_analysis,
                'recent_accuracy': self._calculate_recent_accuracy()
            }
            
        except Exception as e:
            logger.error(f"❌ AI準確率分析失敗: {e}")
            return {}
    
    def _calculate_recent_accuracy(self, hours: int = 24) -> float:
        """計算最近N小時的AI準確率"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_predictions = [p for p in self.prediction_outcomes 
                                if p['timestamp'] > cutoff_time]
            
            if not recent_predictions:
                return 0.0
            
            correct_recent = sum(1 for p in recent_predictions if p['was_correct'])
            return correct_recent / len(recent_predictions)
            
        except Exception as e:
            logger.error(f"❌ 計算最近準確率失敗: {e}")
            return 0.0
    
    def save_session_data(self) -> str:
        """保存會話數據"""
        try:
            # 保存AI決策記錄
            ai_decisions_file = self.log_dir / "ai_decisions.json"
            with open(ai_decisions_file, 'w', encoding='utf-8') as f:
                decisions_data = [asdict(decision) for decision in self.ai_decisions]
                json.dump(decisions_data, f, ensure_ascii=False, indent=2, default=str)
            
            # 保存交易記錄
            trades_file = self.log_dir / "trade_records.json"
            with open(trades_file, 'w', encoding='utf-8') as f:
                trades_data = [asdict(trade) for trade in self.trade_records]
                json.dump(trades_data, f, ensure_ascii=False, indent=2, default=str)
            
            # 保存績效歷史
            performance_file = self.log_dir / "performance_history.json"
            with open(performance_file, 'w', encoding='utf-8') as f:
                performance_data = [asdict(perf) for perf in self.performance_history]
                json.dump(performance_data, f, ensure_ascii=False, indent=2, default=str)
            
            # 保存AI準確率分析
            ai_analysis_file = self.log_dir / "ai_accuracy_analysis.json"
            with open(ai_analysis_file, 'w', encoding='utf-8') as f:
                ai_analysis = self.get_ai_accuracy_analysis()
                json.dump(ai_analysis, f, ensure_ascii=False, indent=2, default=str)
            
            # 生成會話總結
            summary_file = self.log_dir / "session_summary.json"
            current_metrics = self.calculate_performance_metrics()
            
            summary = {
                'session_id': self.session_id,
                'start_time': self.ai_decisions[0].timestamp.isoformat() if self.ai_decisions else None,
                'end_time': datetime.now().isoformat(),
                'initial_balance': self.initial_balance,
                'final_balance': self.current_balance,
                'total_pnl': current_metrics.total_pnl,
                'total_pnl_pct': current_metrics.total_pnl_pct,
                'total_trades': current_metrics.total_trades,
                'win_rate': current_metrics.win_rate,
                'ai_accuracy': current_metrics.ai_accuracy,
                'max_drawdown': current_metrics.max_drawdown,
                'sharpe_ratio': current_metrics.sharpe_ratio
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"📄 會話數據已保存至: {self.log_dir}")
            return str(self.log_dir)
            
        except Exception as e:
            logger.error(f"❌ 保存會話數據失敗: {e}")
            return ""
    
    def get_real_time_status(self) -> Dict[str, Any]:
        """獲取實時狀態"""
        try:
            current_metrics = self.calculate_performance_metrics()
            ai_analysis = self.get_ai_accuracy_analysis()
            
            return {
                'session_id': self.session_id,
                'current_balance': self.current_balance,
                'total_pnl': current_metrics.total_pnl,
                'total_pnl_pct': current_metrics.total_pnl_pct,
                'total_trades': current_metrics.total_trades,
                'win_rate': current_metrics.win_rate,
                'ai_accuracy': current_metrics.ai_accuracy,
                'recent_ai_accuracy': ai_analysis.get('recent_accuracy', 0),
                'active_trades': len([t for t in self.trade_records if t.status == "open"]),
                'ai_decisions_count': len(self.ai_decisions),
                'last_decision_time': self.ai_decisions[-1].timestamp.isoformat() if self.ai_decisions else None,
                'performance_trend': self._get_performance_trend()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取實時狀態失敗: {e}")
            return {}
    
    def _get_performance_trend(self) -> str:
        """獲取績效趨勢"""
        try:
            if len(self.performance_history) < 2:
                return "insufficient_data"
            
            recent_pnl = self.performance_history[-1].total_pnl
            previous_pnl = self.performance_history[-2].total_pnl
            
            if recent_pnl > previous_pnl:
                return "improving"
            elif recent_pnl < previous_pnl:
                return "declining"
            else:
                return "stable"
                
        except Exception:
            return "unknown"


# 創建全局記錄器實例
def create_trading_recorder(session_id: str = None) -> LiveTradingRecorder:
    """創建交易記錄器實例"""
    return LiveTradingRecorder(session_id)


# 測試代碼
if __name__ == "__main__":
    print("🧪 測試實時交易記錄器...")
    
    # 創建記錄器
    recorder = create_trading_recorder("test_session")
    
    # 模擬AI決策和交易
    print("\n🧠 模擬AI決策...")
    decision_id = recorder.record_ai_decision(
        decision="BUY",
        confidence=0.75,
        ai_signals={'scanner': 'bullish', 'analyst': 'buy_signal'},
        market_data={'current_price': 3500000, 'volume': 1000},
        technical_indicators={'rsi': 45, 'macd': 'golden_cross'},
        reasoning="多時間框架趨勢一致，MACD金叉確認"
    )
    
    print("\n💰 模擬交易執行...")
    recorder.record_trade_execution(
        trade_id="trade_001",
        market="btctwd",
        side="buy",
        volume=0.001,
        price=3500000,
        commission=35.0,
        ai_decision_id=decision_id
    )
    
    print("\n📈 模擬交易平倉...")
    recorder.record_trade_close(
        trade_id="trade_001",
        exit_price=3550000
    )
    
    # 計算績效
    print("\n📊 計算績效指標...")
    metrics = recorder.calculate_performance_metrics()
    print(f"   總交易: {metrics.total_trades}")
    print(f"   勝率: {metrics.win_rate:.1%}")
    print(f"   總PnL: {metrics.total_pnl:.2f}")
    print(f"   AI準確率: {metrics.ai_accuracy:.1%}")
    
    # AI分析
    print("\n🎯 AI準確率分析...")
    ai_analysis = recorder.get_ai_accuracy_analysis()
    print(f"   總預測: {ai_analysis.get('total_predictions', 0)}")
    print(f"   整體準確率: {ai_analysis.get('overall_accuracy', 0):.1%}")
    
    # 保存數據
    print("\n💾 保存會話數據...")
    save_path = recorder.save_session_data()
    print(f"   數據已保存至: {save_path}")
    
    # 實時狀態
    print("\n📊 實時狀態:")
    status = recorder.get_real_time_status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    print("\n✅ 交易記錄器測試完成")