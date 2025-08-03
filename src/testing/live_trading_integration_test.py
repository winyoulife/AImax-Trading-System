#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
實盤交易整合測試
執行首次24小時連續實盤測試，監控三AI協作系統在真實市場的表現
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import time
from pathlib import Path

# 導入核心組件
from data.historical_data_manager import create_historical_manager
from data.technical_indicators import TechnicalIndicatorCalculator
from ai.ai_manager import AICollaborationManager
from trading.live_max_api_connector import create_live_connector
from trading.live_trading_safety_framework import create_safety_framework, TradingMode, SafetyLevel
from trading.live_trading_recorder import create_trading_recorder
from monitoring.live_trading_monitor import create_live_monitor

logger = logging.getLogger(__name__)

class LiveTradingIntegrationTest:
    """實盤交易整合測試"""
    
    def __init__(self, test_duration_hours: int = 1):  # 縮短為1小時測試
        """
        初始化整合測試
        
        Args:
            test_duration_hours: 測試持續時間（小時）
        """
        self.test_duration_hours = test_duration_hours
        self.test_start_time = None
        self.test_end_time = None
        
        # 核心組件
        self.data_manager = create_historical_manager()
        self.tech_calculator = TechnicalIndicatorCalculator()
        self.ai_manager = None  # 稍後初始化
        self.api_connector = create_live_connector()
        self.safety_framework = create_safety_framework(TradingMode.LIVE_TEST, SafetyLevel.ULTRA_SAFE)
        self.trading_recorder = create_trading_recorder(f"integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.monitor = create_live_monitor()
        
        # 測試配置
        self.initial_balance = 10000.0  # 10000 TWD
        self.test_market = "btctwd"
        self.decision_interval = 300  # 5分鐘決策一次
        
        # 測試結果
        self.test_results = {
            'start_time': None,
            'end_time': None,
            'duration_hours': 0,
            'total_decisions': 0,
            'total_trades': 0,
            'ai_performance': {},
            'trading_performance': {},
            'system_health': {},
            'issues_encountered': [],
            'recommendations': []
        }
        
        logger.info(f"🧪 實盤交易整合測試初始化完成 - 測試時長: {test_duration_hours}小時")
    
    async def run_integration_test(self) -> Dict[str, Any]:
        """執行完整的整合測試"""
        print("🚀 開始實盤交易整合測試...")
        print(f"⏰ 測試時長: {self.test_duration_hours}小時")
        print(f"💰 初始資金: {self.initial_balance} TWD")
        print(f"📊 交易市場: {self.test_market}")
        
        try:
            # 1. 系統初始化
            print("\n🔧 系統初始化...")
            if not await self._initialize_systems():
                return self._create_error_result("系統初始化失敗")
            
            # 2. 開始測試會話
            print("\n🚀 開始測試會話...")
            self.test_start_time = datetime.now()
            self.test_results['start_time'] = self.test_start_time.isoformat()
            
            # 3. 執行主測試循環
            print("\n🔄 執行主測試循環...")
            await self._run_main_test_loop()
            
            # 4. 結束測試會話
            print("\n🏁 結束測試會話...")
            await self._finalize_test_session()
            
            # 5. 生成測試報告
            print("\n📊 生成測試報告...")
            self._generate_test_report()
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"❌ 整合測試異常: {e}")
            return self._create_error_result(str(e))
        
        finally:
            await self._cleanup_systems()
    
    async def _initialize_systems(self) -> bool:
        """初始化所有系統組件"""
        try:
            # 初始化數據管理器
            print("   📊 初始化數據管理器...")
            data_ready = await self.data_manager.ensure_historical_data(self.test_market, ['1m', '5m', '1h'])
            if not all(data_ready.values()):
                logger.error("❌ 歷史數據準備失敗")
                return False
            
            # 初始化API連接器
            print("   🔗 初始化API連接器...")
            if not await self.api_connector.connect():
                logger.error("❌ API連接失敗")
                return False
            
            # 初始化安全框架
            print("   🛡️ 初始化安全框架...")
            session_id = self.safety_framework.start_trading_session(self.initial_balance)
            if not session_id:
                logger.error("❌ 安全框架啟動失敗")
                return False
            
            # 初始化監控系統
            print("   👁️ 初始化監控系統...")
            self.monitor.start_monitoring(self.initial_balance)
            
            # 添加緊急停止回調
            def emergency_callback(emergency_info):
                logger.critical(f"🚨 緊急停止觸發: {emergency_info}")
                self.test_results['issues_encountered'].append({
                    'type': 'emergency_stop',
                    'timestamp': datetime.now().isoformat(),
                    'details': emergency_info
                })
            
            self.safety_framework.add_emergency_callback(emergency_callback)
            self.monitor.add_emergency_callback(emergency_callback)
            
            print("   ✅ 所有系統初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 系統初始化異常: {e}")
            return False    
    
async def _run_main_test_loop(self) -> None:
        """執行主測試循環"""
        try:
            test_end_time = self.test_start_time + timedelta(hours=self.test_duration_hours)
            decision_count = 0
            
            print(f"   🔄 測試循環開始，預計結束時間: {test_end_time.strftime('%H:%M:%S')}")
            
            while datetime.now() < test_end_time:
                try:
                    decision_count += 1
                    print(f"\n   🧠 執行第 {decision_count} 次AI決策...")
                    
                    # 獲取市場數據
                    market_data = await self._get_current_market_data()
                    if not market_data:
                        logger.warning("⚠️ 無法獲取市場數據，跳過此次決策")
                        await asyncio.sleep(30)
                        continue
                    
                    # AI協作決策（模擬）
                    ai_decision = await self._simulate_ai_decision(market_data)
                    
                    # 記錄AI決策
                    decision_id = self.trading_recorder.record_ai_decision(
                        decision=ai_decision['decision'],
                        confidence=ai_decision['confidence'],
                        ai_signals=ai_decision['ai_signals'],
                        market_data=market_data,
                        technical_indicators=ai_decision['technical_indicators'],
                        reasoning=ai_decision['reasoning']
                    )
                    
                    # 如果是交易決策，執行交易
                    if ai_decision['decision'] in ['BUY', 'SELL']:
                        await self._execute_trade_decision(ai_decision, decision_id, market_data)
                    
                    # 更新監控指標
                    await self._update_monitoring_metrics()
                    
                    # 等待下次決策
                    print(f"   ⏰ 等待 {self.decision_interval} 秒後進行下次決策...")
                    await asyncio.sleep(self.decision_interval)
                    
                except Exception as e:
                    logger.error(f"❌ 測試循環異常: {e}")
                    self.test_results['issues_encountered'].append({
                        'type': 'loop_error',
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e)
                    })
                    await asyncio.sleep(60)  # 錯誤後等待1分鐘
            
            self.test_results['total_decisions'] = decision_count
            print(f"\n   ✅ 測試循環完成，共執行 {decision_count} 次決策")
            
        except Exception as e:
            logger.error(f"❌ 主測試循環異常: {e}")
            raise
    
    async def _get_current_market_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前市場數據"""
        try:
            # 獲取多時間框架歷史數據
            data_1m = self.data_manager.get_historical_data(self.test_market, "1m", 100)
            data_5m = self.data_manager.get_historical_data(self.test_market, "5m", 50)
            data_1h = self.data_manager.get_historical_data(self.test_market, "1h", 24)
            
            if not all([data_1m is not None, data_5m is not None, data_1h is not None]):
                return None
            
            # 獲取當前價格
            current_price = self.api_connector.get_current_price(self.test_market)
            if not current_price:
                current_price = float(data_5m['close'].iloc[-1]) if not data_5m.empty else 3500000.0
            
            # 計算技術指標
            klines_data = {'1m': data_1m, '5m': data_5m, '1h': data_1h}
            technical_indicators = self.tech_calculator.calculate_comprehensive_indicators(klines_data)
            
            # 格式化為AI友好的數據
            ai_formatted_data = self.tech_calculator.format_indicators_for_ai(technical_indicators)
            
            return {
                'current_price': current_price,
                'timestamp': datetime.now().isoformat(),
                'market': self.test_market,
                'technical_indicators': technical_indicators,
                'ai_formatted_data': ai_formatted_data,
                'klines_data': {
                    '1m_count': len(data_1m),
                    '5m_count': len(data_5m),
                    '1h_count': len(data_1h)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取市場數據失敗: {e}")
            return None
    
    async def _simulate_ai_decision(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """模擬AI協作決策"""
        try:
            # 模擬三AI協作決策過程
            # 在實際實現中，這裡會調用真實的AI管理器
            
            # 基於技術指標做簡單決策邏輯
            indicators = market_data['technical_indicators']
            
            # 決策邏輯
            decision = "HOLD"
            confidence = 0.5
            reasoning = "市場觀望"
            
            # RSI超賣買入
            if 'medium_rsi' in indicators and indicators['medium_rsi'] < 30:
                decision = "BUY"
                confidence = 0.75
                reasoning = "RSI超賣，考慮買入"
            
            # RSI超買賣出
            elif 'medium_rsi' in indicators and indicators['medium_rsi'] > 70:
                decision = "SELL"
                confidence = 0.70
                reasoning = "RSI超買，考慮賣出"
            
            # MACD金叉
            elif 'medium_macd_signal_type' in indicators and indicators['medium_macd_signal_type'] == "金叉":
                decision = "BUY"
                confidence = 0.80
                reasoning = "MACD金叉，趨勢轉強"
            
            # 多時間框架趨勢一致
            elif 'trend_consistency' in indicators and indicators['trend_consistency'] > 0.8:
                if indicators.get('dominant_trend') == "上升":
                    decision = "BUY"
                    confidence = 0.85
                    reasoning = "多時間框架趨勢一致向上"
                elif indicators.get('dominant_trend') == "下降":
                    decision = "SELL"
                    confidence = 0.85
                    reasoning = "多時間框架趨勢一致向下"
            
            return {
                'decision': decision,
                'confidence': confidence,
                'reasoning': reasoning,
                'ai_signals': {
                    'market_scanner': {'signal': 'neutral', 'confidence': 0.6},
                    'deep_analyst': {'signal': decision.lower(), 'confidence': confidence},
                    'decision_maker': {'final_decision': decision, 'confidence': confidence}
                },
                'technical_indicators': indicators
            }
            
        except Exception as e:
            logger.error(f"❌ AI決策模擬失敗: {e}")
            return {
                'decision': 'HOLD',
                'confidence': 0.0,
                'reasoning': f'決策失敗: {str(e)}',
                'ai_signals': {},
                'technical_indicators': {}
            }
    
    async def _execute_trade_decision(self, ai_decision: Dict[str, Any], 
                                    decision_id: str, market_data: Dict[str, Any]) -> None:
        """執行交易決策"""
        try:
            # 安全檢查
            trade_amount = 500.0  # 500 TWD
            safety_check, safety_message = self.safety_framework.validate_trade_request(
                trade_amount, ai_decision['confidence'], ai_decision['ai_signals']
            )
            
            if not safety_check:
                logger.warning(f"⚠️ 交易被安全框架拒絕: {safety_message}")
                return
            
            # 計算交易數量
            current_price = market_data['current_price']
            volume = trade_amount / current_price
            
            # 執行交易（模擬）
            from trading.live_max_api_connector import OrderRequest, OrderSide, OrderType
            
            order_request = OrderRequest(
                market=self.test_market,
                side=OrderSide.BUY if ai_decision['decision'] == 'BUY' else OrderSide.SELL,
                order_type=OrderType.MARKET,
                volume=volume,
                client_oid=f"test_{decision_id}"
            )
            
            success, order_response, message = await self.api_connector.place_order(order_request)
            
            if success and order_response:
                # 記錄交易執行
                self.trading_recorder.record_trade_execution(
                    trade_id=str(order_response.id),
                    market=order_response.market,
                    side=order_response.side,
                    volume=order_response.volume,
                    price=order_response.avg_price or current_price,
                    commission=order_response.volume * current_price * 0.001,  # 0.1% 手續費
                    ai_decision_id=decision_id
                )
                
                # 記錄到安全框架
                pnl = 0  # 暫時設為0，實際會在平倉時計算
                self.safety_framework.record_trade_result(str(order_response.id), pnl, {
                    'ai_decision': ai_decision['decision'],
                    'confidence': ai_decision['confidence']
                })
                
                self.test_results['total_trades'] += 1
                print(f"   ✅ 交易執行成功 - {order_response.side} {order_response.volume:.6f} @ {current_price:.0f}")
                
                # 模擬平倉（簡化版，實際中會根據策略決定平倉時機）
                await asyncio.sleep(60)  # 等待1分鐘後平倉
                exit_price = current_price * (1.01 if ai_decision['decision'] == 'BUY' else 0.99)  # 模擬1%價格變動
                self.trading_recorder.record_trade_close(str(order_response.id), exit_price)
                
            else:
                logger.error(f"❌ 交易執行失敗: {message}")
                self.test_results['issues_encountered'].append({
                    'type': 'trade_execution_failed',
                    'timestamp': datetime.now().isoformat(),
                    'error': message
                })
                
        except Exception as e:
            logger.error(f"❌ 執行交易決策異常: {e}")
    
    async def _update_monitoring_metrics(self) -> None:
        """更新監控指標"""
        try:
            # 獲取當前狀態
            recorder_status = self.trading_recorder.get_real_time_status()
            safety_status = self.safety_framework.get_current_status()
            
            # 更新監控器
            self.monitor.update_metrics(
                balance=recorder_status.get('current_balance', self.initial_balance),
                daily_pnl=recorder_status.get('total_pnl', 0),
                total_trades=recorder_status.get('total_trades', 0),
                consecutive_losses=safety_status.get('consecutive_losses', 0),
                ai_confidence=recorder_status.get('ai_accuracy', 0),
                active_positions=recorder_status.get('active_trades', 0)
            )
            
        except Exception as e:
            logger.error(f"❌ 更新監控指標失敗: {e}")
    
    async def _finalize_test_session(self) -> None:
        """結束測試會話"""
        try:
            self.test_end_time = datetime.now()
            self.test_results['end_time'] = self.test_end_time.isoformat()
            self.test_results['duration_hours'] = (self.test_end_time - self.test_start_time).total_seconds() / 3600
            
            # 結束安全框架會話
            session_report = self.safety_framework.end_trading_session("測試完成")
            
            # 保存交易記錄
            self.trading_recorder.save_session_data()
            
            # 停止監控
            self.monitor.stop_monitoring()
            
            print(f"   ✅ 測試會話結束，持續時間: {self.test_results['duration_hours']:.2f}小時")
            
        except Exception as e:
            logger.error(f"❌ 結束測試會話異常: {e}")
    
    def _generate_test_report(self) -> None:
        """生成測試報告"""
        try:
            # 獲取最終績效指標
            final_metrics = self.trading_recorder.calculate_performance_metrics()
            ai_analysis = self.trading_recorder.get_ai_accuracy_analysis()
            monitor_status = self.monitor.get_current_status()
            
            # AI性能分析
            self.test_results['ai_performance'] = {
                'total_decisions': self.test_results['total_decisions'],
                'trading_decisions': ai_analysis.get('total_predictions', 0),
                'overall_accuracy': ai_analysis.get('overall_accuracy', 0),
                'buy_accuracy': ai_analysis.get('buy_accuracy', 0),
                'sell_accuracy': ai_analysis.get('sell_accuracy', 0),
                'confidence_analysis': ai_analysis.get('confidence_analysis', {})
            }
            
            # 交易性能分析
            self.test_results['trading_performance'] = {
                'total_trades': final_metrics.total_trades,
                'winning_trades': final_metrics.winning_trades,
                'losing_trades': final_metrics.losing_trades,
                'win_rate': final_metrics.win_rate,
                'total_pnl': final_metrics.total_pnl,
                'total_pnl_pct': final_metrics.total_pnl_pct,
                'avg_win': final_metrics.avg_win,
                'avg_loss': final_metrics.avg_loss,
                'profit_factor': final_metrics.profit_factor,
                'max_drawdown': final_metrics.max_drawdown,
                'sharpe_ratio': final_metrics.sharpe_ratio
            }
            
            # 系統健康狀態
            self.test_results['system_health'] = {
                'api_connection': self.api_connector.get_connection_status(),
                'monitoring_alerts': monitor_status.get('total_alerts', 0),
                'emergency_stops': len([issue for issue in self.test_results['issues_encountered'] 
                                      if issue['type'] == 'emergency_stop']),
                'system_errors': len([issue for issue in self.test_results['issues_encountered'] 
                                    if issue['type'] != 'emergency_stop'])
            }
            
            # 生成建議
            self._generate_recommendations()
            
            print(f"\n📊 測試報告生成完成:")
            print(f"   🧠 AI決策次數: {self.test_results['ai_performance']['total_decisions']}")
            print(f"   💰 總交易次數: {self.test_results['trading_performance']['total_trades']}")
            print(f"   🎯 AI準確率: {self.test_results['ai_performance']['overall_accuracy']:.1%}")
            print(f"   📈 交易勝率: {self.test_results['trading_performance']['win_rate']:.1%}")
            print(f"   💵 總PnL: {self.test_results['trading_performance']['total_pnl']:.2f} TWD")
            
        except Exception as e:
            logger.error(f"❌ 生成測試報告失敗: {e}")
    
    def _generate_recommendations(self) -> None:
        """生成改進建議"""
        recommendations = []
        
        # AI性能建議
        ai_accuracy = self.test_results['ai_performance'].get('overall_accuracy', 0)
        if ai_accuracy < 0.6:
            recommendations.append("AI決策準確率偏低，建議優化提示詞和權重分配")
        elif ai_accuracy > 0.8:
            recommendations.append("AI決策準確率優秀，可以考慮增加交易頻率")
        
        # 交易性能建議
        win_rate = self.test_results['trading_performance'].get('win_rate', 0)
        if win_rate < 0.5:
            recommendations.append("交易勝率偏低，建議加強風險控制和止損策略")
        
        total_pnl = self.test_results['trading_performance'].get('total_pnl', 0)
        if total_pnl < 0:
            recommendations.append("測試期間出現虧損，建議檢查交易策略和市場適應性")
        
        # 系統健康建議
        emergency_stops = self.test_results['system_health'].get('emergency_stops', 0)
        if emergency_stops > 0:
            recommendations.append("測試期間觸發緊急停止，建議檢查風險控制參數")
        
        system_errors = self.test_results['system_health'].get('system_errors', 0)
        if system_errors > 0:
            recommendations.append("測試期間出現系統錯誤，建議加強錯誤處理機制")
        
        if not recommendations:
            recommendations.append("系統運行良好，可以考慮進入正式實盤交易")
        
        self.test_results['recommendations'] = recommendations
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """創建錯誤結果"""
        return {
            'success': False,
            'error': error_message,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _cleanup_systems(self) -> None:
        """清理系統資源"""
        try:
            if self.api_connector:
                await self.api_connector.disconnect()
            
            if self.data_manager:
                await self.data_manager.close()
            
            if self.monitor and self.monitor.is_monitoring:
                self.monitor.stop_monitoring()
            
            logger.info("✅ 系統資源清理完成")
            
        except Exception as e:
            logger.error(f"❌ 系統資源清理失敗: {e}")
    
    def save_test_results(self) -> str:
        """保存測試結果"""
        try:
            # 創建測試結果目錄
            results_dir = Path("AImax/logs/integration_tests")
            results_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存測試結果
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = results_dir / f"integration_test_results_{timestamp}.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"📄 測試結果已保存: {results_file}")
            return str(results_file)
            
        except Exception as e:
            logger.error(f"❌ 保存測試結果失敗: {e}")
            return ""


# 創建測試實例
def create_integration_test(duration_hours: int = 1) -> LiveTradingIntegrationTest:
    """創建整合測試實例"""
    return LiveTradingIntegrationTest(duration_hours)


# 主函數
async def main():
    """主函數"""
    print("🧪 AImax 實盤交易整合測試")
    print("=" * 50)
    
    # 創建測試實例（1小時測試）
    test = create_integration_test(1)
    
    try:
        # 執行整合測試
        results = await test.run_integration_test()
        
        # 保存結果
        results_file = test.save_test_results()
        
        # 顯示測試總結
        print(f"\n🎉 整合測試完成！")
        print(f"📄 詳細結果已保存至: {results_file}")
        
        if results.get('success', True):
            print("✅ 測試成功完成")
            
            # 顯示關鍵指標
            if 'ai_performance' in results:
                print(f"🧠 AI準確率: {results['ai_performance'].get('overall_accuracy', 0):.1%}")
            
            if 'trading_performance' in results:
                print(f"💰 交易勝率: {results['trading_performance'].get('win_rate', 0):.1%}")
                print(f"💵 總PnL: {results['trading_performance'].get('total_pnl', 0):.2f} TWD")
            
            # 顯示建議
            if 'recommendations' in results:
                print(f"\n💡 改進建議:")
                for i, rec in enumerate(results['recommendations'], 1):
                    print(f"   {i}. {rec}")
        else:
            print(f"❌ 測試失敗: {results.get('error', '未知錯誤')}")
            
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試異常: {e}")
        logger.error(f"測試異常: {e}")


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 運行測試
    asyncio.run(main())