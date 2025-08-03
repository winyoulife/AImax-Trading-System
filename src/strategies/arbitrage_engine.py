#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
套利策略引擎 - 整合套利機會識別、執行和風險控制的完整套利系統
支持跨交易所套利、三角套利、統計套利等多種套利策略
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

try:
    from .arbitrage_opportunity_detector import (
        ArbitrageOpportunityDetector, ArbitrageConfig, ArbitrageType, 
        ArbitrageOpportunity, OpportunityStatus
    )
except ImportError:
    from arbitrage_opportunity_detector import (
        ArbitrageOpportunityDetector, ArbitrageConfig, ArbitrageType, 
        ArbitrageOpportunity, OpportunityStatus
    )

logger = logging.getLogger(__name__)

class ArbitrageEngineStatus(Enum):
    """套利引擎狀態"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

@dataclass
class ArbitrageExecutionResult:
    """套利執行結果"""
    opportunity_id: str
    execution_id: str
    success: bool
    executed_steps: List[Dict[str, Any]]
    actual_profit: float
    execution_time: float
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ArbitrageEngineConfig:
    """套利引擎配置"""
    # 基礎配置
    enabled: bool = True
    auto_execution: bool = False  # 是否自動執行套利
    max_concurrent_arbitrages: int = 3
    
    # 套利配置
    arbitrage_config: ArbitrageConfig = field(default_factory=lambda: ArbitrageConfig(
        enabled_types=[ArbitrageType.CROSS_EXCHANGE, ArbitrageType.TRIANGULAR],
        min_profit_percentage=0.005,
        max_capital_per_trade=50000,
        exchanges=["binance", "max"],
        trading_pairs=["BTCTWD", "ETHTWD", "USDTTWD"]
    ))
    
    # 執行配置
    execution_timeout: int = 30  # 執行超時時間(秒)
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # 風險控制
    max_daily_loss: float = 5000  # 每日最大虧損
    max_position_size: float = 100000  # 最大倉位
    emergency_stop_loss: float = 0.02  # 緊急止損比例

class ArbitrageEngine:
    """套利策略引擎"""
    
    def __init__(self, config: ArbitrageEngineConfig):
        self.config = config
        self.status = ArbitrageEngineStatus.STOPPED
        
        # 初始化套利機會檢測器
        self.opportunity_detector = ArbitrageOpportunityDetector(config.arbitrage_config)
        
        # 執行狀態
        self.active_executions: Dict[str, ArbitrageExecutionResult] = {}
        self.execution_history: List[ArbitrageExecutionResult] = []
        
        # 統計數據
        self.engine_stats = {
            'total_opportunities_detected': 0,
            'total_executions_attempted': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'success_rate': 0.0,
            'avg_execution_time': 0.0,
            'daily_profit': 0.0,
            'daily_loss': 0.0
        }
        
        # 風險控制
        self.daily_loss = 0.0
        self.daily_profit = 0.0
        self.current_positions: Dict[str, float] = {}  # {pair: position_size}
        
        logger.info("🔄 套利策略引擎初始化完成")
        logger.info(f"   自動執行: {'啟用' if config.auto_execution else '禁用'}")
        logger.info(f"   最大並發: {config.max_concurrent_arbitrages}")
        logger.info(f"   支持策略: {[t.value for t in config.arbitrage_config.enabled_types]}")
    
    async def start(self):
        """啟動套利引擎"""
        if self.status == ArbitrageEngineStatus.RUNNING:
            logger.warning("⚠️ 套利引擎已在運行中")
            return
        
        try:
            self.status = ArbitrageEngineStatus.STARTING
            logger.info("🚀 啟動套利策略引擎...")
            
            # 啟動機會檢測器
            await self.opportunity_detector.start_monitoring()
            
            # 啟動主循環
            self.status = ArbitrageEngineStatus.RUNNING
            
            # 啟動引擎主循環
            engine_tasks = [
                self._opportunity_monitoring_loop(),
                self._execution_monitoring_loop(),
                self._risk_monitoring_loop()
            ]
            
            await asyncio.gather(*engine_tasks)
            
        except Exception as e:
            logger.error(f"❌ 套利引擎啟動失敗: {e}")
            self.status = ArbitrageEngineStatus.ERROR
            raise
    
    async def stop(self):
        """停止套利引擎"""
        logger.info("🛑 停止套利策略引擎...")
        
        self.status = ArbitrageEngineStatus.STOPPED
        
        # 停止機會檢測器
        await self.opportunity_detector.stop_monitoring()
        
        # 等待所有執行完成
        await self._wait_for_executions_complete()
        
        logger.info("✅ 套利策略引擎已停止")
    
    async def pause(self):
        """暫停套利引擎"""
        if self.status == ArbitrageEngineStatus.RUNNING:
            self.status = ArbitrageEngineStatus.PAUSED
            logger.info("⏸️ 套利策略引擎已暫停")
    
    async def resume(self):
        """恢復套利引擎"""
        if self.status == ArbitrageEngineStatus.PAUSED:
            self.status = ArbitrageEngineStatus.RUNNING
            logger.info("▶️ 套利策略引擎已恢復")
    
    async def _opportunity_monitoring_loop(self):
        """機會監控循環"""
        while self.status in [ArbitrageEngineStatus.RUNNING, ArbitrageEngineStatus.PAUSED]:
            try:
                if self.status == ArbitrageEngineStatus.RUNNING:
                    # 獲取新的套利機會
                    opportunities = self.opportunity_detector.get_active_opportunities()
                    
                    # 處理新機會
                    for opportunity in opportunities:
                        await self._process_opportunity(opportunity)
                    
                    # 更新統計
                    self.engine_stats['total_opportunities_detected'] = len(
                        self.opportunity_detector.opportunity_history
                    )
                
                await asyncio.sleep(1.0)  # 每秒檢查一次
                
            except Exception as e:
                logger.error(f"❌ 機會監控循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _execution_monitoring_loop(self):
        """執行監控循環"""
        while self.status in [ArbitrageEngineStatus.RUNNING, ArbitrageEngineStatus.PAUSED]:
            try:
                if self.status == ArbitrageEngineStatus.RUNNING:
                    # 監控活躍執行
                    await self._monitor_active_executions()
                    
                    # 清理完成的執行
                    await self._cleanup_completed_executions()
                
                await asyncio.sleep(0.5)  # 更頻繁的執行監控
                
            except Exception as e:
                logger.error(f"❌ 執行監控循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _risk_monitoring_loop(self):
        """風險監控循環"""
        while self.status in [ArbitrageEngineStatus.RUNNING, ArbitrageEngineStatus.PAUSED]:
            try:
                # 檢查風險限制
                await self._check_risk_limits()
                
                # 更新統計
                self._update_engine_stats()
                
                await asyncio.sleep(5.0)  # 每5秒檢查一次風險
                
            except Exception as e:
                logger.error(f"❌ 風險監控循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_opportunity(self, opportunity: ArbitrageOpportunity):
        """處理套利機會"""
        try:
            # 檢查是否已在處理
            if opportunity.opportunity_id in self.active_executions:
                return
            
            # 檢查並發限制
            if len(self.active_executions) >= self.config.max_concurrent_arbitrages:
                logger.debug(f"⚠️ 達到最大並發限制，跳過機會: {opportunity.opportunity_id}")
                return
            
            # 風險檢查
            if not await self._risk_check_opportunity(opportunity):
                logger.debug(f"⚠️ 風險檢查未通過，跳過機會: {opportunity.opportunity_id}")
                return
            
            # 記錄機會
            logger.info(f"🎯 處理套利機會: {opportunity.arbitrage_type.value}")
            logger.info(f"   機會ID: {opportunity.opportunity_id}")
            logger.info(f"   預期利潤: {opportunity.expected_profit:.2f} TWD ({opportunity.profit_percentage:.2%})")
            logger.info(f"   風險分數: {opportunity.risk_score:.2f}")
            logger.info(f"   信心度: {opportunity.confidence:.2f}")
            
            # 自動執行檢查
            if self.config.auto_execution:
                await self._execute_arbitrage(opportunity)
            else:
                logger.info(f"   ℹ️ 自動執行已禁用，需要手動確認")
            
        except Exception as e:
            logger.error(f"❌ 處理套利機會失敗: {e}")
    
    async def _risk_check_opportunity(self, opportunity: ArbitrageOpportunity) -> bool:
        """風險檢查套利機會"""
        try:
            # 檢查每日虧損限制
            if self.daily_loss >= self.config.max_daily_loss:
                logger.warning(f"⚠️ 已達每日最大虧損限制: {self.daily_loss:.2f}")
                return False
            
            # 檢查倉位限制
            total_position = sum(abs(pos) for pos in self.current_positions.values())
            if total_position + opportunity.required_capital > self.config.max_position_size:
                logger.warning(f"⚠️ 超過最大倉位限制: {total_position + opportunity.required_capital:.2f}")
                return False
            
            # 檢查機會風險分數
            if opportunity.risk_score > self.config.arbitrage_config.max_risk_score:
                logger.warning(f"⚠️ 機會風險分數過高: {opportunity.risk_score:.2f}")
                return False
            
            # 檢查機會是否過期
            if datetime.now() > opportunity.expiry_time:
                logger.warning(f"⚠️ 套利機會已過期: {opportunity.opportunity_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 風險檢查失敗: {e}")
            return False
    
    async def _execute_arbitrage(self, opportunity: ArbitrageOpportunity):
        """執行套利"""
        execution_id = f"exec_{opportunity.opportunity_id}_{int(datetime.now().timestamp())}"
        
        try:
            logger.info(f"🚀 開始執行套利: {execution_id}")
            
            # 創建執行結果記錄
            execution_result = ArbitrageExecutionResult(
                opportunity_id=opportunity.opportunity_id,
                execution_id=execution_id,
                success=False,
                executed_steps=[],
                actual_profit=0.0,
                execution_time=0.0
            )
            
            # 添加到活躍執行
            self.active_executions[execution_id] = execution_result
            
            start_time = datetime.now()
            
            # 執行套利步驟
            success = await self._execute_arbitrage_steps(opportunity, execution_result)
            
            # 計算執行時間
            execution_time = (datetime.now() - start_time).total_seconds()
            execution_result.execution_time = execution_time
            execution_result.success = success
            
            # 更新統計
            self.engine_stats['total_executions_attempted'] += 1
            
            if success:
                self.engine_stats['successful_executions'] += 1
                self.engine_stats['total_profit'] += execution_result.actual_profit
                self.daily_profit += execution_result.actual_profit
                
                logger.info(f"✅ 套利執行成功: {execution_id}")
                logger.info(f"   實際利潤: {execution_result.actual_profit:.2f} TWD")
                logger.info(f"   執行時間: {execution_time:.2f} 秒")
            else:
                self.engine_stats['failed_executions'] += 1
                loss = abs(execution_result.actual_profit) if execution_result.actual_profit < 0 else 0
                self.engine_stats['total_loss'] += loss
                self.daily_loss += loss
                
                logger.warning(f"❌ 套利執行失敗: {execution_id}")
                if execution_result.error_message:
                    logger.warning(f"   錯誤信息: {execution_result.error_message}")
            
            # 更新機會狀態
            opportunity.status = OpportunityStatus.EXECUTED if success else OpportunityStatus.CANCELLED
            
        except Exception as e:
            logger.error(f"❌ 套利執行異常: {e}")
            execution_result.success = False
            execution_result.error_message = str(e)
            
            self.engine_stats['failed_executions'] += 1
        
        finally:
            # 移動到歷史記錄
            if execution_id in self.active_executions:
                self.execution_history.append(self.active_executions[execution_id])
                del self.active_executions[execution_id]
            
            # 保持歷史記錄在合理範圍內
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-500:]
    
    async def _execute_arbitrage_steps(self, opportunity: ArbitrageOpportunity, 
                                     execution_result: ArbitrageExecutionResult) -> bool:
        """執行套利步驟"""
        try:
            total_profit = 0.0
            
            for i, step in enumerate(opportunity.execution_path):
                logger.info(f"   執行步驟 {i+1}/{len(opportunity.execution_path)}: {step.get('action', 'unknown')}")
                
                # 模擬執行步驟
                step_result = await self._execute_single_step(step)
                
                execution_result.executed_steps.append({
                    'step_index': i,
                    'step_config': step,
                    'result': step_result,
                    'timestamp': datetime.now().isoformat()
                })
                
                if not step_result.get('success', False):
                    execution_result.error_message = step_result.get('error', 'Unknown error')
                    return False
                
                # 累計利潤
                step_profit = step_result.get('profit', 0.0)
                total_profit += step_profit
                
                logger.info(f"      步驟結果: {'成功' if step_result.get('success') else '失敗'}")
                logger.info(f"      步驟利潤: {step_profit:.2f} TWD")
            
            execution_result.actual_profit = total_profit
            
            # 檢查總利潤是否符合預期
            expected_profit = opportunity.expected_profit
            profit_deviation = abs(total_profit - expected_profit) / expected_profit if expected_profit > 0 else 0
            
            if profit_deviation > 0.5:  # 如果實際利潤偏離預期超過50%
                logger.warning(f"⚠️ 實際利潤偏離預期: 預期 {expected_profit:.2f}, 實際 {total_profit:.2f}")
            
            return total_profit > 0  # 只要有正利潤就算成功
            
        except Exception as e:
            logger.error(f"❌ 執行套利步驟失敗: {e}")
            execution_result.error_message = str(e)
            return False
    
    async def _execute_single_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """執行單個套利步驟 (模擬)"""
        try:
            action = step.get('action', 'unknown')
            exchange = step.get('exchange', 'unknown')
            pair = step.get('pair', 'unknown')
            price = step.get('price', 0.0)
            volume = step.get('volume', 0.0)
            
            # 模擬執行延遲
            await asyncio.sleep(0.1)
            
            # 模擬執行結果
            import random
            
            # 90%成功率
            success = random.random() > 0.1
            
            if success:
                # 模擬滑點和手續費
                slippage = random.uniform(-0.001, 0.001)  # ±0.1%滑點
                fee_rate = 0.001  # 0.1%手續費
                
                actual_price = price * (1 + slippage)
                
                if action == 'buy':
                    cost = actual_price * volume * (1 + fee_rate)
                    profit = -cost  # 買入是成本
                else:  # sell
                    revenue = actual_price * volume * (1 - fee_rate)
                    profit = revenue  # 賣出是收入
                
                return {
                    'success': True,
                    'action': action,
                    'exchange': exchange,
                    'pair': pair,
                    'executed_price': actual_price,
                    'executed_volume': volume,
                    'profit': profit,
                    'slippage': slippage,
                    'fee': actual_price * volume * fee_rate
                }
            else:
                return {
                    'success': False,
                    'error': f'執行失敗: {action} {pair} @ {exchange}',
                    'profit': 0.0
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'profit': 0.0
            }
    
    async def _monitor_active_executions(self):
        """監控活躍執行"""
        try:
            current_time = datetime.now()
            timeout_executions = []
            
            for execution_id, execution in self.active_executions.items():
                # 檢查執行超時
                execution_duration = (current_time - execution.timestamp).total_seconds()
                
                if execution_duration > self.config.execution_timeout:
                    timeout_executions.append(execution_id)
                    execution.success = False
                    execution.error_message = "執行超時"
                    
                    logger.warning(f"⚠️ 套利執行超時: {execution_id}")
            
            # 處理超時執行
            for execution_id in timeout_executions:
                if execution_id in self.active_executions:
                    self.execution_history.append(self.active_executions[execution_id])
                    del self.active_executions[execution_id]
                    
                    self.engine_stats['failed_executions'] += 1
            
        except Exception as e:
            logger.error(f"❌ 監控活躍執行失敗: {e}")
    
    async def _cleanup_completed_executions(self):
        """清理完成的執行"""
        # 這個方法在當前實現中主要用於未來擴展
        pass
    
    async def _check_risk_limits(self):
        """檢查風險限制"""
        try:
            # 檢查每日虧損限制
            if self.daily_loss >= self.config.max_daily_loss:
                logger.warning(f"⚠️ 達到每日最大虧損限制，暫停套利引擎")
                await self.pause()
            
            # 檢查緊急止損
            if self.engine_stats['total_loss'] > 0:
                loss_ratio = self.engine_stats['total_loss'] / (
                    self.engine_stats['total_profit'] + self.engine_stats['total_loss']
                )
                
                if loss_ratio > self.config.emergency_stop_loss:
                    logger.error(f"🚨 觸發緊急止損，停止套利引擎")
                    await self.stop()
            
        except Exception as e:
            logger.error(f"❌ 檢查風險限制失敗: {e}")
    
    def _update_engine_stats(self):
        """更新引擎統計"""
        try:
            total_executions = self.engine_stats['total_executions_attempted']
            
            if total_executions > 0:
                self.engine_stats['success_rate'] = (
                    self.engine_stats['successful_executions'] / total_executions
                )
            
            # 計算平均執行時間
            if self.execution_history:
                total_time = sum(exec.execution_time for exec in self.execution_history[-100:])
                count = min(len(self.execution_history), 100)
                self.engine_stats['avg_execution_time'] = total_time / count
            
            # 重置每日統計 (簡化版本)
            current_hour = datetime.now().hour
            if current_hour == 0:  # 每天午夜重置
                self.daily_profit = 0.0
                self.daily_loss = 0.0
            
        except Exception as e:
            logger.error(f"❌ 更新引擎統計失敗: {e}")
    
    async def _wait_for_executions_complete(self):
        """等待所有執行完成"""
        timeout = 30  # 30秒超時
        start_time = datetime.now()
        
        while self.active_executions and (datetime.now() - start_time).total_seconds() < timeout:
            logger.info(f"⏳ 等待 {len(self.active_executions)} 個套利執行完成...")
            await asyncio.sleep(1.0)
        
        if self.active_executions:
            logger.warning(f"⚠️ 仍有 {len(self.active_executions)} 個執行未完成，強制停止")
            # 強制移動到歷史記錄
            for execution in self.active_executions.values():
                execution.success = False
                execution.error_message = "引擎停止時強制終止"
                self.execution_history.append(execution)
            
            self.active_executions.clear()
    
    # 公共接口方法
    
    async def manual_detect_opportunities(self) -> List[ArbitrageOpportunity]:
        """手動檢測套利機會"""
        return await self.opportunity_detector.manual_detect_opportunities()
    
    async def manual_execute_opportunity(self, opportunity_id: str) -> bool:
        """手動執行套利機會"""
        try:
            opportunity = self.opportunity_detector.get_opportunity_by_id(opportunity_id)
            
            if not opportunity:
                logger.error(f"❌ 未找到套利機會: {opportunity_id}")
                return False
            
            if not await self._risk_check_opportunity(opportunity):
                logger.error(f"❌ 風險檢查未通過: {opportunity_id}")
                return False
            
            await self._execute_arbitrage(opportunity)
            return True
            
        except Exception as e:
            logger.error(f"❌ 手動執行套利失敗: {e}")
            return False
    
    def get_engine_status(self) -> Dict[str, Any]:
        """獲取引擎狀態"""
        return {
            'status': self.status.value,
            'config': {
                'enabled': self.config.enabled,
                'auto_execution': self.config.auto_execution,
                'max_concurrent_arbitrages': self.config.max_concurrent_arbitrages,
                'enabled_types': [t.value for t in self.config.arbitrage_config.enabled_types]
            },
            'active_executions': len(self.active_executions),
            'execution_history_count': len(self.execution_history),
            'stats': self.engine_stats.copy(),
            'risk_status': {
                'daily_loss': self.daily_loss,
                'daily_profit': self.daily_profit,
                'current_positions': self.current_positions.copy(),
                'max_daily_loss': self.config.max_daily_loss,
                'max_position_size': self.config.max_position_size
            },
            'detector_stats': self.opportunity_detector.get_detection_stats()
        }
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取執行歷史"""
        try:
            recent_executions = self.execution_history[-limit:] if limit > 0 else self.execution_history
            
            return [
                {
                    'execution_id': exec.execution_id,
                    'opportunity_id': exec.opportunity_id,
                    'success': exec.success,
                    'actual_profit': exec.actual_profit,
                    'execution_time': exec.execution_time,
                    'executed_steps_count': len(exec.executed_steps),
                    'error_message': exec.error_message,
                    'timestamp': exec.timestamp.isoformat()
                }
                for exec in recent_executions
            ]
            
        except Exception as e:
            logger.error(f"❌ 獲取執行歷史失敗: {e}")
            return []


# 創建套利引擎實例
def create_arbitrage_engine(config: ArbitrageEngineConfig) -> ArbitrageEngine:
    """創建套利引擎實例"""
    return ArbitrageEngine(config)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_arbitrage_engine():
        """測試套利引擎"""
        print("🧪 測試套利策略引擎...")
        
        # 創建配置
        config = ArbitrageEngineConfig(
            auto_execution=True,
            max_concurrent_arbitrages=2,
            arbitrage_config=ArbitrageConfig(
                enabled_types=[ArbitrageType.CROSS_EXCHANGE, ArbitrageType.TRIANGULAR],
                min_profit_percentage=0.002,
                exchanges=["binance", "max"],
                trading_pairs=["BTCTWD", "ETHTWD", "USDTTWD"]
            )
        )
        
        # 創建引擎
        engine = create_arbitrage_engine(config)
        
        try:
            # 手動檢測機會
            print("\n🔍 手動檢測套利機會...")
            opportunities = await engine.manual_detect_opportunities()
            
            print(f"✅ 檢測結果: 發現 {len(opportunities)} 個套利機會")
            
            for i, opp in enumerate(opportunities[:3], 1):
                print(f"   機會 {i}: {opp.arbitrage_type.value}")
                print(f"      預期利潤: {opp.expected_profit:.2f} TWD ({opp.profit_percentage:.2%})")
                print(f"      風險分數: {opp.risk_score:.2f}")
            
            # 手動執行第一個機會
            if opportunities:
                print(f"\n🚀 手動執行第一個套利機會...")
                success = await engine.manual_execute_opportunity(opportunities[0].opportunity_id)
                print(f"   執行結果: {'成功' if success else '失敗'}")
            
            # 獲取引擎狀態
            status = engine.get_engine_status()
            print(f"\n📊 引擎狀態:")
            print(f"   狀態: {status['status']}")
            print(f"   總執行次數: {status['stats']['total_executions_attempted']}")
            print(f"   成功次數: {status['stats']['successful_executions']}")
            print(f"   成功率: {status['stats']['success_rate']:.1%}")
            print(f"   總利潤: {status['stats']['total_profit']:.2f} TWD")
            
            # 獲取執行歷史
            history = engine.get_execution_history(5)
            print(f"\n📜 執行歷史 (最近5次):")
            for i, exec in enumerate(history, 1):
                print(f"   {i}. {exec['execution_id']}")
                print(f"      成功: {'是' if exec['success'] else '否'}")
                print(f"      利潤: {exec['actual_profit']:.2f} TWD")
                print(f"      執行時間: {exec['execution_time']:.2f} 秒")
            
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
        
        print("🎉 套利策略引擎測試完成！")
    
    # 運行測試
    asyncio.run(test_arbitrage_engine())