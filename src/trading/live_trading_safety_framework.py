#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實盤測試安全框架 - 確保實盤測試期間的資金安全
包含小額測試模式、專用風險控制、實時監控和緊急停止機制
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import threading
import time

logger = logging.getLogger(__name__)

class TradingMode(Enum):
    """交易模式"""
    SIMULATION = "simulation"      # 模擬模式
    LIVE_TEST = "live_test"       # 實盤測試模式
    LIVE_FULL = "live_full"       # 完整實盤模式

class SafetyLevel(Enum):
    """安全等級"""
    ULTRA_SAFE = "ultra_safe"     # 超安全模式
    SAFE = "safe"                 # 安全模式
    NORMAL = "normal"             # 正常模式

@dataclass
class SafetyLimits:
    """安全限制配置"""
    max_single_trade_twd: float = 1000.0      # 單筆交易上限 (TWD)
    max_daily_loss_pct: float = 5.0           # 每日最大虧損百分比
    max_total_position_pct: float = 10.0      # 最大總倉位百分比
    max_consecutive_losses: int = 3            # 最大連續虧損次數
    min_confidence_threshold: float = 0.7     # 最小信心度閾值
    emergency_stop_loss_pct: float = 2.0      # 緊急止損百分比
    max_trades_per_hour: int = 5              # 每小時最大交易次數
    cooldown_after_loss_minutes: int = 30     # 虧損後冷卻時間(分鐘)

@dataclass
class TradingSession:
    """交易會話"""
    session_id: str
    start_time: datetime
    mode: TradingMode
    safety_level: SafetyLevel
    initial_balance: float
    current_balance: float
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    consecutive_losses: int = 0
    daily_pnl: float = 0.0
    last_trade_time: Optional[datetime] = None
    is_active: bool = True
    emergency_stopped: bool = False

class LiveTradingSafetyFramework:
    """實盤交易安全框架"""
    
    def __init__(self, mode: TradingMode = TradingMode.LIVE_TEST, 
                 safety_level: SafetyLevel = SafetyLevel.ULTRA_SAFE):
        """
        初始化安全框架
        
        Args:
            mode: 交易模式
            safety_level: 安全等級
        """
        self.mode = mode
        self.safety_level = safety_level
        self.limits = self._get_safety_limits()
        self.session: Optional[TradingSession] = None
        self.trade_history: List[Dict[str, Any]] = []
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.emergency_callbacks: List[callable] = []
        
        # 交易頻率控制
        self.recent_trades: List[datetime] = []
        self.last_loss_time: Optional[datetime] = None
        
        logger.info(f"🛡️ 實盤交易安全框架初始化完成 - 模式: {mode.value}, 安全等級: {safety_level.value}")
    
    def _get_safety_limits(self) -> SafetyLimits:
        """根據安全等級獲取安全限制"""
        if self.safety_level == SafetyLevel.ULTRA_SAFE:
            return SafetyLimits(
                max_single_trade_twd=500.0,
                max_daily_loss_pct=2.0,
                max_total_position_pct=5.0,
                max_consecutive_losses=2,
                min_confidence_threshold=0.8,
                emergency_stop_loss_pct=1.5,
                max_trades_per_hour=3,
                cooldown_after_loss_minutes=60
            )
        elif self.safety_level == SafetyLevel.SAFE:
            return SafetyLimits(
                max_single_trade_twd=1000.0,
                max_daily_loss_pct=5.0,
                max_total_position_pct=10.0,
                max_consecutive_losses=3,
                min_confidence_threshold=0.7,
                emergency_stop_loss_pct=2.0,
                max_trades_per_hour=5,
                cooldown_after_loss_minutes=30
            )
        else:  # NORMAL
            return SafetyLimits()
    
    def start_trading_session(self, initial_balance: float) -> str:
        """開始交易會話"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.session = TradingSession(
            session_id=session_id,
            start_time=datetime.now(),
            mode=self.mode,
            safety_level=self.safety_level,
            initial_balance=initial_balance,
            current_balance=initial_balance
        )
        
        # 開始監控
        self.start_monitoring()
        
        logger.info(f"🚀 交易會話開始 - ID: {session_id}, 初始資金: {initial_balance} TWD")
        return session_id
    
    def validate_trade_request(self, trade_amount: float, confidence: float, 
                             ai_signals: Dict[str, Any]) -> Tuple[bool, str]:
        """
        驗證交易請求
        
        Args:
            trade_amount: 交易金額 (TWD)
            confidence: AI信心度
            ai_signals: AI信號
            
        Returns:
            (是否允許交易, 原因)
        """
        if not self.session or not self.session.is_active:
            return False, "交易會話未激活"
        
        if self.session.emergency_stopped:
            return False, "緊急停止狀態"
        
        # 檢查單筆交易限制
        if trade_amount > self.limits.max_single_trade_twd:
            return False, f"單筆交易金額超限 ({trade_amount} > {self.limits.max_single_trade_twd})"
        
        # 檢查信心度
        if confidence < self.limits.min_confidence_threshold:
            return False, f"AI信心度不足 ({confidence} < {self.limits.min_confidence_threshold})"
        
        # 檢查連續虧損
        if self.session.consecutive_losses >= self.limits.max_consecutive_losses:
            return False, f"連續虧損次數超限 ({self.session.consecutive_losses})"
        
        # 檢查每日虧損限制
        daily_loss_pct = abs(self.session.daily_pnl) / self.session.initial_balance * 100
        if self.session.daily_pnl < 0 and daily_loss_pct >= self.limits.max_daily_loss_pct:
            return False, f"每日虧損超限 ({daily_loss_pct:.1f}% >= {self.limits.max_daily_loss_pct}%)"
        
        # 檢查交易頻率
        if not self._check_trading_frequency():
            return False, "交易頻率超限"
        
        # 檢查冷卻時間
        if not self._check_cooldown_period():
            remaining_minutes = self._get_remaining_cooldown_minutes()
            return False, f"虧損後冷卻期，剩餘 {remaining_minutes} 分鐘"
        
        # 檢查倉位限制
        current_position_pct = self._calculate_current_position_percentage()
        if current_position_pct >= self.limits.max_total_position_pct:
            return False, f"總倉位超限 ({current_position_pct:.1f}% >= {self.limits.max_total_position_pct}%)"
        
        return True, "交易請求通過驗證"
    
    def record_trade_result(self, trade_id: str, pnl: float, 
                          trade_details: Dict[str, Any]) -> None:
        """記錄交易結果"""
        if not self.session:
            return
        
        # 更新會話統計
        self.session.total_trades += 1
        self.session.current_balance += pnl
        self.session.daily_pnl += pnl
        self.session.last_trade_time = datetime.now()
        
        if pnl > 0:
            self.session.winning_trades += 1
            self.session.consecutive_losses = 0
        else:
            self.session.losing_trades += 1
            self.session.consecutive_losses += 1
            self.last_loss_time = datetime.now()
        
        # 記錄交易歷史
        trade_record = {
            'trade_id': trade_id,
            'timestamp': datetime.now().isoformat(),
            'pnl': pnl,
            'balance_after': self.session.current_balance,
            'consecutive_losses': self.session.consecutive_losses,
            'details': trade_details
        }
        self.trade_history.append(trade_record)
        
        # 檢查是否需要緊急停止
        self._check_emergency_conditions()
        
        logger.info(f"📊 交易記錄更新 - ID: {trade_id}, PnL: {pnl:.2f}, 餘額: {self.session.current_balance:.2f}")
    
    def _check_trading_frequency(self) -> bool:
        """檢查交易頻率"""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        # 清理過期記錄
        self.recent_trades = [t for t in self.recent_trades if t > one_hour_ago]
        
        # 檢查頻率限制
        if len(self.recent_trades) >= self.limits.max_trades_per_hour:
            return False
        
        # 添加當前交易時間
        self.recent_trades.append(now)
        return True
    
    def _check_cooldown_period(self) -> bool:
        """檢查冷卻期"""
        if not self.last_loss_time:
            return True
        
        cooldown_end = self.last_loss_time + timedelta(minutes=self.limits.cooldown_after_loss_minutes)
        return datetime.now() >= cooldown_end
    
    def _get_remaining_cooldown_minutes(self) -> int:
        """獲取剩餘冷卻時間"""
        if not self.last_loss_time:
            return 0
        
        cooldown_end = self.last_loss_time + timedelta(minutes=self.limits.cooldown_after_loss_minutes)
        remaining = cooldown_end - datetime.now()
        return max(0, int(remaining.total_seconds() / 60))
    
    def _calculate_current_position_percentage(self) -> float:
        """計算當前倉位百分比"""
        # 這裡應該根據實際持倉計算
        # 暫時返回0，實際實現時需要連接到倉位管理器
        return 0.0
    
    def _check_emergency_conditions(self) -> None:
        """檢查緊急停止條件"""
        if not self.session:
            return
        
        emergency_reasons = []
        
        # 檢查緊急止損
        total_loss_pct = (self.session.initial_balance - self.session.current_balance) / self.session.initial_balance * 100
        if total_loss_pct >= self.limits.emergency_stop_loss_pct:
            emergency_reasons.append(f"緊急止損觸發 ({total_loss_pct:.1f}% >= {self.limits.emergency_stop_loss_pct}%)")
        
        # 檢查連續虧損
        if self.session.consecutive_losses >= self.limits.max_consecutive_losses:
            emergency_reasons.append(f"連續虧損超限 ({self.session.consecutive_losses})")
        
        # 檢查每日虧損
        daily_loss_pct = abs(self.session.daily_pnl) / self.session.initial_balance * 100
        if self.session.daily_pnl < 0 and daily_loss_pct >= self.limits.max_daily_loss_pct:
            emergency_reasons.append(f"每日虧損超限 ({daily_loss_pct:.1f}%)")
        
        if emergency_reasons:
            self.trigger_emergency_stop(emergency_reasons)
    
    def trigger_emergency_stop(self, reasons: List[str]) -> None:
        """觸發緊急停止"""
        if not self.session:
            return
        
        self.session.emergency_stopped = True
        self.session.is_active = False
        
        emergency_info = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session.session_id,
            'reasons': reasons,
            'final_balance': self.session.current_balance,
            'total_loss': self.session.initial_balance - self.session.current_balance,
            'total_trades': self.session.total_trades
        }
        
        # 執行緊急回調
        for callback in self.emergency_callbacks:
            try:
                callback(emergency_info)
            except Exception as e:
                logger.error(f"❌ 緊急回調執行失敗: {e}")
        
        # 保存緊急停止記錄
        self._save_emergency_record(emergency_info)
        
        logger.critical(f"🚨 緊急停止觸發 - 原因: {', '.join(reasons)}")
    
    def add_emergency_callback(self, callback: callable) -> None:
        """添加緊急停止回調"""
        self.emergency_callbacks.append(callback)
    
    def start_monitoring(self) -> None:
        """開始實時監控"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("👁️ 實時監控已啟動")
    
    def stop_monitoring(self) -> None:
        """停止實時監控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("👁️ 實時監控已停止")
    
    def _monitoring_loop(self) -> None:
        """監控循環"""
        while self.monitoring_active and self.session:
            try:
                # 檢查會話狀態
                if not self.session.is_active:
                    break
                
                # 定期檢查緊急條件
                self._check_emergency_conditions()
                
                # 檢查會話超時 (24小時)
                if datetime.now() - self.session.start_time > timedelta(hours=24):
                    self.end_trading_session("會話超時")
                    break
                
                time.sleep(10)  # 每10秒檢查一次
                
            except Exception as e:
                logger.error(f"❌ 監控循環錯誤: {e}")
                time.sleep(30)
    
    def end_trading_session(self, reason: str = "正常結束") -> Dict[str, Any]:
        """結束交易會話"""
        if not self.session:
            return {}
        
        self.session.is_active = False
        self.stop_monitoring()
        
        # 生成會話報告
        session_report = {
            'session_id': self.session.session_id,
            'start_time': self.session.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration_hours': (datetime.now() - self.session.start_time).total_seconds() / 3600,
            'mode': self.session.mode.value,
            'safety_level': self.session.safety_level.value,
            'reason': reason,
            'initial_balance': self.session.initial_balance,
            'final_balance': self.session.current_balance,
            'total_pnl': self.session.current_balance - self.session.initial_balance,
            'total_trades': self.session.total_trades,
            'winning_trades': self.session.winning_trades,
            'losing_trades': self.session.losing_trades,
            'win_rate': self.session.winning_trades / max(1, self.session.total_trades),
            'emergency_stopped': self.session.emergency_stopped,
            'trade_history': self.trade_history
        }
        
        # 保存會話報告
        self._save_session_report(session_report)
        
        logger.info(f"📋 交易會話結束 - {reason}, 總PnL: {session_report['total_pnl']:.2f}")
        return session_report
    
    def get_current_status(self) -> Dict[str, Any]:
        """獲取當前狀態"""
        if not self.session:
            return {'status': 'no_active_session'}
        
        return {
            'session_id': self.session.session_id,
            'is_active': self.session.is_active,
            'emergency_stopped': self.session.emergency_stopped,
            'mode': self.session.mode.value,
            'safety_level': self.session.safety_level.value,
            'current_balance': self.session.current_balance,
            'daily_pnl': self.session.daily_pnl,
            'total_trades': self.session.total_trades,
            'consecutive_losses': self.session.consecutive_losses,
            'remaining_cooldown_minutes': self._get_remaining_cooldown_minutes(),
            'limits': {
                'max_single_trade_twd': self.limits.max_single_trade_twd,
                'max_daily_loss_pct': self.limits.max_daily_loss_pct,
                'max_consecutive_losses': self.limits.max_consecutive_losses,
                'min_confidence_threshold': self.limits.min_confidence_threshold
            }
        }
    
    def _save_session_report(self, report: Dict[str, Any]) -> None:
        """保存會話報告"""
        try:
            import os
            os.makedirs('AImax/logs/trading_sessions', exist_ok=True)
            
            filename = f"AImax/logs/trading_sessions/{report['session_id']}_report.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"📄 會話報告已保存: {filename}")
            
        except Exception as e:
            logger.error(f"❌ 保存會話報告失敗: {e}")
    
    def _save_emergency_record(self, emergency_info: Dict[str, Any]) -> None:
        """保存緊急停止記錄"""
        try:
            import os
            os.makedirs('AImax/logs/emergency_stops', exist_ok=True)
            
            filename = f"AImax/logs/emergency_stops/{emergency_info['session_id']}_emergency.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(emergency_info, f, ensure_ascii=False, indent=2, default=str)
            
            logger.critical(f"🚨 緊急停止記錄已保存: {filename}")
            
        except Exception as e:
            logger.error(f"❌ 保存緊急停止記錄失敗: {e}")


# 創建全局安全框架實例
def create_safety_framework(mode: TradingMode = TradingMode.LIVE_TEST,
                           safety_level: SafetyLevel = SafetyLevel.ULTRA_SAFE) -> LiveTradingSafetyFramework:
    """創建安全框架實例"""
    return LiveTradingSafetyFramework(mode, safety_level)


# 測試代碼
if __name__ == "__main__":
    import time
    
    def emergency_callback(emergency_info):
        print(f"🚨 緊急停止回調: {emergency_info}")
    
    # 測試安全框架
    print("🧪 測試實盤交易安全框架...")
    
    framework = create_safety_framework(TradingMode.LIVE_TEST, SafetyLevel.ULTRA_SAFE)
    framework.add_emergency_callback(emergency_callback)
    
    # 開始交易會話
    session_id = framework.start_trading_session(10000.0)  # 10000 TWD
    
    # 測試交易驗證
    print("\n📊 測試交易驗證...")
    
    # 正常交易
    valid, reason = framework.validate_trade_request(300.0, 0.85, {'signal': 'buy'})
    print(f"正常交易 (300 TWD, 85%信心): {'✅ 通過' if valid else '❌ 拒絕'} - {reason}")
    
    # 超額交易
    valid, reason = framework.validate_trade_request(1000.0, 0.85, {'signal': 'buy'})
    print(f"超額交易 (1000 TWD, 85%信心): {'✅ 通過' if valid else '❌ 拒絕'} - {reason}")
    
    # 低信心度交易
    valid, reason = framework.validate_trade_request(300.0, 0.6, {'signal': 'buy'})
    print(f"低信心交易 (300 TWD, 60%信心): {'✅ 通過' if valid else '❌ 拒絕'} - {reason}")
    
    # 模擬一些交易
    print("\n💰 模擬交易結果...")
    framework.record_trade_result("trade_001", -100.0, {'type': 'loss'})
    framework.record_trade_result("trade_002", -150.0, {'type': 'loss'})
    
    # 檢查狀態
    status = framework.get_current_status()
    print(f"\n📊 當前狀態:")
    print(f"   餘額: {status['current_balance']} TWD")
    print(f"   連續虧損: {status['consecutive_losses']}次")
    print(f"   冷卻時間: {status['remaining_cooldown_minutes']}分鐘")
    
    # 等待一段時間後結束
    time.sleep(2)
    report = framework.end_trading_session("測試完成")
    
    print(f"\n📋 會話報告:")
    print(f"   總交易: {report['total_trades']}筆")
    print(f"   總PnL: {report['total_pnl']:.2f} TWD")
    print(f"   勝率: {report['win_rate']:.1%}")