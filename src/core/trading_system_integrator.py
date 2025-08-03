#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易系統整合器 - 整合AI決策、風險管理、交易執行和倉位管理
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import json

# 導入各個組件
from ..ai.ai_manager import AICollaborationManager, CollaborativeDecision
from ..trading.trade_executor import TradeExecutor
from ..trading.risk_manager import RiskManager
from ..trading.position_manager import PositionManager
from ..data.market_enhancer import MarketDataEnhancer

logger = logging.getLogger(__name__)

@dataclass
class TradingSystemStatus:
    """交易系統狀態"""
    is_active: bool
    last_decision_time: Optional[datetime]
    total_trades: int
    successful_trades: int
    current_balance: float
    total_pnl: float
    active_positions: int
    risk_level: str
    ai_performance: Dict[str, Any]

@dataclass
class TradingCycle:
    """交易週期記錄"""
    cycle_id: str
    start_time: datetime
    end_time: Optional[datetime]
    market_data: Dict[str, Any]
    ai_decision: Optional[CollaborativeDecision]
    risk_assessment: Optional[Dict[str, Any]]
    trade_result: Optional[Dict[str, Any]]
    position_actions: List[Dict[str, Any]]
    cycle_pnl: float
    success: bool
    error_message: Optional[str] = None

class TradingSystemIntegrator:
    """交易系統整合器"""
    
    def __init__(self, initial_balance: float = 100000.0, 
                 config_path: str = "config/trading_system.json"):
        """
        初始化交易系統整合器
        
        Args:
            initial_balance: 初始資金
            config_path: 系統配置文件路徑
        """
        self.initial_balance = initial_balance
        self.config = self._load_config(config_path)
        
        # 初始化各個組件
        self.ai_manager = AICollaborationManager()
        self.trade_executor = TradeExecutor(initial_balance)
        self.risk_manager = RiskManager(initial_balance)
        self.position_manager = PositionManager()
        self.market_enhancer = MarketDataEnhancer()
        
        # 系統狀態
        self.is_active = False
        self.emergency_stop = False
        self.trading_cycles = []
        
        # 系統統計
        self.system_stats = {
            'total_cycles': 0,
            'successful_cycles': 0,
            'total_ai_decisions': 0,
            'trades_executed': 0,
            'trades_blocked_by_risk': 0,
            'emergency_stops': 0,
            'average_cycle_time': 0.0,
            'system_uptime': datetime.now()
        }
        
        logger.info("🚀 交易系統整合器初始化完成")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """載入系統配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"✅ 載入系統配置: {config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ 載入系統配置失敗: {e}")
            # 返回默認配置
            return {
                'trading_interval': 60,  # 60秒交易週期
                'max_daily_trades': 50,
                'enable_auto_trading': True,
                'enable_risk_management': True,
                'enable_position_management': True,
                'emergency_stop_conditions': {
                    'max_daily_loss': 0.10,
                    'max_consecutive_losses': 10,
                    'system_error_threshold': 5
                }
            }
    
    async def start_trading_system(self):
        """啟動交易系統"""
        try:
            logger.info("🚀 啟動交易系統...")
            
            # 系統自檢
            system_check = await self._perform_system_check()
            if not system_check['passed']:
                raise Exception(f"系統自檢失敗: {system_check['errors']}")
            
            self.is_active = True
            self.emergency_stop = False
            
            logger.info("✅ 交易系統啟動成功")
            
            # 開始主交易循環
            await self._main_trading_loop()
            
        except Exception as e:
            logger.error(f"❌ 交易系統啟動失敗: {e}")
            self.is_active = False
            raise
    
    async def stop_trading_system(self, reason: str = "manual"):
        """停止交易系統"""
        try:
            logger.info(f"🛑 停止交易系統 - 原因: {reason}")
            
            self.is_active = False
            
            # 關閉所有活躍倉位（如果需要）
            if reason == "emergency":
                await self._emergency_close_all_positions()
            
            logger.info("✅ 交易系統已停止")
            
        except Exception as e:
            logger.error(f"❌ 停止交易系統失敗: {e}")
    
    async def _perform_system_check(self) -> Dict[str, Any]:
        """執行系統自檢"""
        try:
            logger.info("🔍 執行系統自檢...")
            
            errors = []
            
            # 檢查AI系統
            try:
                ai_status = self.ai_manager.get_ai_status()
                if ai_status['models_configured'] == 0:
                    errors.append("AI模型未配置")
            except Exception as e:
                errors.append(f"AI系統檢查失敗: {e}")
            
            # 檢查交易執行器
            try:
                account_status = self.trade_executor.get_account_status()
                if account_status['available_balance'] <= 0:
                    errors.append("可用資金不足")
            except Exception as e:
                errors.append(f"交易執行器檢查失敗: {e}")
            
            # 檢查風險管理器
            try:
                risk_summary = self.risk_manager.get_risk_summary()
                if risk_summary.get('current_drawdown', 0) > 0.2:
                    errors.append("當前回撤過大")
            except Exception as e:
                errors.append(f"風險管理器檢查失敗: {e}")
            
            # 檢查市場數據
            try:
                # 這裡應該檢查市場數據連接
                pass
            except Exception as e:
                errors.append(f"市場數據檢查失敗: {e}")
            
            result = {
                'passed': len(errors) == 0,
                'errors': errors,
                'timestamp': datetime.now()
            }
            
            if result['passed']:
                logger.info("✅ 系統自檢通過")
            else:
                logger.error(f"❌ 系統自檢失敗: {errors}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 系統自檢異常: {e}")
            return {'passed': False, 'errors': [str(e)], 'timestamp': datetime.now()}
    
    async def _main_trading_loop(self):
        """主交易循環"""
        try:
            logger.info("🔄 開始主交易循環")
            
            while self.is_active and not self.emergency_stop:
                try:
                    # 執行一個交易週期
                    cycle_result = await self._execute_trading_cycle()
                    
                    # 檢查緊急停止條件
                    if await self._check_emergency_stop_conditions():
                        await self.stop_trading_system("emergency")
                        break
                    
                    # 等待下一個週期
                    await asyncio.sleep(self.config.get('trading_interval', 60))
                    
                except Exception as e:
                    logger.error(f"❌ 交易週期執行失敗: {e}")
                    self.system_stats['emergency_stops'] += 1
                    
                    # 如果連續錯誤過多，觸發緊急停止
                    if self.system_stats['emergency_stops'] >= 5:
                        await self.stop_trading_system("too_many_errors")
                        break
                    
                    # 短暫等待後繼續
                    await asyncio.sleep(10)
            
            logger.info("🏁 主交易循環結束")
            
        except Exception as e:
            logger.error(f"❌ 主交易循環異常: {e}")
            await self.stop_trading_system("system_error")
    
    async def _execute_trading_cycle(self) -> TradingCycle:
        """執行一個完整的交易週期"""
        cycle_start = datetime.now()
        cycle_id = f"CYCLE_{cycle_start.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            logger.info(f"🔄 開始交易週期: {cycle_id}")
            
            # 1. 獲取和增強市場數據
            market_data = await self._get_enhanced_market_data()
            
            # 2. AI協作分析
            ai_decision = await self.ai_manager.analyze_market_collaboratively(market_data)
            
            # 3. 更新倉位狀態
            position_actions = self.position_manager.update_positions(market_data['current_price'])
            
            # 4. 執行倉位相關動作（止損/止盈）
            for action in position_actions:
                if action['action'] == 'close_position':
                    close_result = self.position_manager.close_position(
                        action['position'], action['price'], action['reason']
                    )
                    # 更新風險管理器
                    self.risk_manager.add_trade_record(close_result)
            
            # 5. 風險評估
            account_status = self.trade_executor.get_account_status()
            risk_assessment = await self.risk_manager.assess_trade_risk(
                ai_decision.__dict__, market_data, account_status
            )
            
            # 6. 執行交易決策
            trade_result = None
            if risk_assessment['approved'] and ai_decision.final_decision != 'HOLD':
                trade_result = await self.trade_executor.execute_ai_decision(
                    ai_decision.__dict__, market_data
                )
                
                # 如果交易成功，創建倉位
                if trade_result.get('status') == 'filled':
                    position = self.position_manager.create_position(
                        trade_result, ai_decision.__dict__
                    )
                    # 更新風險管理器
                    self.risk_manager.add_trade_record(trade_result)
            
            # 7. 創建週期記錄
            cycle = TradingCycle(
                cycle_id=cycle_id,
                start_time=cycle_start,
                end_time=datetime.now(),
                market_data=market_data,
                ai_decision=ai_decision,
                risk_assessment=risk_assessment,
                trade_result=trade_result,
                position_actions=position_actions,
                cycle_pnl=self._calculate_cycle_pnl(trade_result, position_actions),
                success=True
            )
            
            # 8. 更新統計
            self._update_system_stats(cycle)
            
            # 9. 記錄週期
            self.trading_cycles.append(cycle)
            
            # 保持週期記錄在合理範圍內
            if len(self.trading_cycles) > 1000:
                self.trading_cycles = self.trading_cycles[-1000:]
            
            logger.info(f"✅ 交易週期完成: {cycle_id}")
            return cycle
            
        except Exception as e:
            logger.error(f"❌ 交易週期執行失敗 ({cycle_id}): {e}")
            
            # 創建失敗的週期記錄
            cycle = TradingCycle(
                cycle_id=cycle_id,
                start_time=cycle_start,
                end_time=datetime.now(),
                market_data={},
                ai_decision=None,
                risk_assessment=None,
                trade_result=None,
                position_actions=[],
                cycle_pnl=0.0,
                success=False,
                error_message=str(e)
            )
            
            self.trading_cycles.append(cycle)
            return cycle
    
    async def _get_enhanced_market_data(self) -> Dict[str, Any]:
        """獲取增強的市場數據"""
        try:
            # 這裡應該調用市場數據增強器
            # 暫時返回模擬數據
            return {
                'current_price': 1500000,
                'price_change_1m': 0.5,
                'price_change_5m': 1.2,
                'volume_ratio': 1.1,
                'volatility_level': '中',
                'technical_indicators': {
                    'rsi': 65,
                    'macd': '金叉',
                    'ema_trend': '上升'
                },
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取市場數據失敗: {e}")
            raise
    
    def _calculate_cycle_pnl(self, trade_result: Optional[Dict[str, Any]], 
                           position_actions: List[Dict[str, Any]]) -> float:
        """計算週期盈虧"""
        try:
            cycle_pnl = 0.0
            
            # 新交易的盈虧（通常為0，因為剛開倉）
            if trade_result and 'pnl' in trade_result:
                cycle_pnl += trade_result['pnl']
            
            # 倉位關閉的盈虧
            for action in position_actions:
                if action['action'] == 'close_position' and 'pnl' in action:
                    cycle_pnl += action.get('pnl', 0)
            
            return cycle_pnl
            
        except Exception as e:
            logger.error(f"❌ 計算週期盈虧失敗: {e}")
            return 0.0
    
    def _update_system_stats(self, cycle: TradingCycle):
        """更新系統統計"""
        try:
            self.system_stats['total_cycles'] += 1
            
            if cycle.success:
                self.system_stats['successful_cycles'] += 1
            
            if cycle.ai_decision:
                self.system_stats['total_ai_decisions'] += 1
            
            if cycle.trade_result and cycle.trade_result.get('status') == 'filled':
                self.system_stats['trades_executed'] += 1
            
            if cycle.risk_assessment and not cycle.risk_assessment.get('approved', True):
                self.system_stats['trades_blocked_by_risk'] += 1
            
            # 更新平均週期時間
            if cycle.end_time:
                cycle_time = (cycle.end_time - cycle.start_time).total_seconds()
                total_time = (self.system_stats['average_cycle_time'] * 
                             (self.system_stats['total_cycles'] - 1) + cycle_time)
                self.system_stats['average_cycle_time'] = total_time / self.system_stats['total_cycles']
            
        except Exception as e:
            logger.error(f"❌ 更新系統統計失敗: {e}")
    
    async def _check_emergency_stop_conditions(self) -> bool:
        """檢查緊急停止條件"""
        try:
            emergency_conditions = self.config.get('emergency_stop_conditions', {})
            
            # 檢查每日虧損限制
            account_status = self.trade_executor.get_account_status()
            daily_loss_ratio = abs(account_status.get('daily_pnl', 0)) / self.initial_balance
            
            if daily_loss_ratio > emergency_conditions.get('max_daily_loss', 0.10):
                logger.critical(f"🚨 觸發緊急停止: 每日虧損 {daily_loss_ratio:.1%} 超過限制")
                return True
            
            # 檢查連續虧損
            recent_cycles = self.trading_cycles[-10:]  # 最近10個週期
            consecutive_losses = 0
            for cycle in reversed(recent_cycles):
                if cycle.cycle_pnl < 0:
                    consecutive_losses += 1
                else:
                    break
            
            if consecutive_losses >= emergency_conditions.get('max_consecutive_losses', 10):
                logger.critical(f"🚨 觸發緊急停止: 連續虧損 {consecutive_losses} 次")
                return True
            
            # 檢查系統錯誤
            if self.system_stats['emergency_stops'] >= emergency_conditions.get('system_error_threshold', 5):
                logger.critical(f"🚨 觸發緊急停止: 系統錯誤過多")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 檢查緊急停止條件失敗: {e}")
            return True  # 出錯時保守處理
    
    async def _emergency_close_all_positions(self):
        """緊急關閉所有倉位"""
        try:
            logger.warning("⚠️ 執行緊急關閉所有倉位")
            
            active_positions = self.position_manager.get_active_positions()
            
            for position_summary in active_positions:
                # 模擬市場價格關閉
                current_price = position_summary['current_price']
                
                # 找到對應的倉位對象
                for position in self.position_manager.positions:
                    if position.position_id == position_summary['position_id']:
                        close_result = self.position_manager.close_position(
                            position, current_price, "emergency_stop"
                        )
                        logger.info(f"🚨 緊急關閉倉位: {position.position_id}")
                        break
            
            logger.info("✅ 所有倉位已緊急關閉")
            
        except Exception as e:
            logger.error(f"❌ 緊急關閉倉位失敗: {e}")
    
    def get_system_status(self) -> TradingSystemStatus:
        """獲取系統狀態"""
        try:
            account_status = self.trade_executor.get_account_status()
            position_stats = self.position_manager.get_position_stats()
            risk_summary = self.risk_manager.get_risk_summary()
            ai_performance = self.ai_manager.get_performance_stats()
            
            last_decision_time = None
            if self.trading_cycles:
                last_cycle = self.trading_cycles[-1]
                if last_cycle.ai_decision:
                    last_decision_time = last_cycle.ai_decision.timestamp
            
            return TradingSystemStatus(
                is_active=self.is_active,
                last_decision_time=last_decision_time,
                total_trades=self.system_stats['trades_executed'],
                successful_trades=account_status.get('execution_stats', {}).get('successful_trades', 0),
                current_balance=account_status.get('total_equity', 0),
                total_pnl=position_stats.get('total_pnl', 0),
                active_positions=position_stats.get('active_positions', 0),
                risk_level=risk_summary.get('current_drawdown', 0),
                ai_performance=ai_performance
            )
            
        except Exception as e:
            logger.error(f"❌ 獲取系統狀態失敗: {e}")
            return TradingSystemStatus(
                is_active=False,
                last_decision_time=None,
                total_trades=0,
                successful_trades=0,
                current_balance=0,
                total_pnl=0,
                active_positions=0,
                risk_level="UNKNOWN",
                ai_performance={}
            )
    
    def get_recent_cycles(self, limit: int = 10) -> List[TradingCycle]:
        """獲取最近的交易週期"""
        return self.trading_cycles[-limit:]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """獲取系統統計"""
        return self.system_stats.copy()


# 創建全局交易系統整合器實例
def create_trading_system(initial_balance: float = 100000.0) -> TradingSystemIntegrator:
    """創建交易系統整合器實例"""
    return TradingSystemIntegrator(initial_balance)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_trading_system():
        """測試交易系統整合器"""
        print("🧪 測試交易系統整合器...")
        
        # 創建交易系統
        trading_system = create_trading_system(100000.0)
        
        # 獲取系統狀態
        status = trading_system.get_system_status()
        print(f"📊 系統狀態: 活躍={status.is_active}, 餘額={status.current_balance:,.0f}")
        
        # 執行一個交易週期測試
        try:
            cycle = await trading_system._execute_trading_cycle()
            print(f"✅ 測試週期完成: {cycle.cycle_id}")
            print(f"   成功: {cycle.success}")
            print(f"   AI決策: {cycle.ai_decision.final_decision if cycle.ai_decision else 'None'}")
            print(f"   週期盈虧: {cycle.cycle_pnl:+,.0f} TWD")
        except Exception as e:
            print(f"❌ 測試週期失敗: {e}")
        
        # 獲取系統統計
        stats = trading_system.get_system_stats()
        print(f"\n📈 系統統計:")
        print(f"   總週期: {stats['total_cycles']}")
        print(f"   成功週期: {stats['successful_cycles']}")
        print(f"   AI決策: {stats['total_ai_decisions']}")
        print(f"   執行交易: {stats['trades_executed']}")
    
    # 運行測試
    asyncio.run(test_trading_system())