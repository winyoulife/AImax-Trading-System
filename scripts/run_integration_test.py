#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版實盤交易整合測試
執行首次實盤測試週期
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import asyncio
import logging
from datetime import datetime, timedelta
import json

# 導入核心組件
from data.historical_data_manager import create_historical_manager
from data.technical_indicators import TechnicalIndicatorCalculator
from trading.live_max_api_connector import create_live_connector, OrderRequest, OrderSide, OrderType
from trading.live_trading_safety_framework import create_safety_framework, TradingMode, SafetyLevel
from trading.live_trading_recorder import create_trading_recorder
from monitoring.live_trading_monitor import create_live_monitor

logger = logging.getLogger(__name__)

async def run_simple_integration_test():
    """執行簡化版整合測試"""
    print("🚀 AImax 實盤交易整合測試")
    print("=" * 40)
    
    # 初始化組件
    print("\n🔧 初始化系統組件...")
    
    data_manager = create_historical_manager()
    tech_calculator = TechnicalIndicatorCalculator()
    api_connector = create_live_connector()
    safety_framework = create_safety_framework(TradingMode.LIVE_TEST, SafetyLevel.ULTRA_SAFE)
    recorder = create_trading_recorder("integration_test")
    monitor = create_live_monitor()
    
    test_results = {
        'start_time': datetime.now().isoformat(),
        'decisions': [],
        'trades': [],
        'performance': {},
        'issues': []
    }
    
    try:
        # 1. 確保數據準備
        print("   📊 確保歷史數據...")
        data_status = await data_manager.ensure_historical_data("btctwd", ['1m', '5m', '1h'])
        print(f"   ✅ 數據狀態: {data_status}")
        
        # 2. 建立API連接
        print("   🔗 建立API連接...")
        connected = await api_connector.connect()
        print(f"   {'✅ 連接成功' if connected else '❌ 連接失敗'}")
        
        # 3. 啟動安全框架
        print("   🛡️ 啟動安全框架...")
        session_id = safety_framework.start_trading_session(10000.0)
        print(f"   ✅ 會話ID: {session_id}")
        
        # 4. 啟動監控
        print("   👁️ 啟動監控...")
        monitor.start_monitoring(10000.0)
        
        # 5. 執行測試循環（3次決策）
        print("\n🔄 執行測試決策循環...")
        
        for i in range(3):
            print(f"\n   🧠 第 {i+1} 次AI決策...")
            
            try:
                # 獲取市場數據
                data_5m = data_manager.get_historical_data("btctwd", "5m", 50)
                if data_5m is None or data_5m.empty:
                    print("   ⚠️ 無法獲取市場數據")
                    continue
                
                # 計算技術指標
                klines_data = {'5m': data_5m}
                indicators = tech_calculator.calculate_comprehensive_indicators(klines_data)
                
                current_price = api_connector.get_current_price("btctwd") or 3500000.0
                
                # 簡單決策邏輯
                decision = "HOLD"
                confidence = 0.5
                reasoning = "市場觀望"
                
                if 'medium_rsi' in indicators:
                    rsi = indicators['medium_rsi']
                    if rsi < 30:
                        decision = "BUY"
                        confidence = 0.75
                        reasoning = f"RSI超賣 ({rsi:.1f})"
                    elif rsi > 70:
                        decision = "SELL"
                        confidence = 0.70
                        reasoning = f"RSI超買 ({rsi:.1f})"
                
                print(f"   📊 決策: {decision} (信心度: {confidence:.1%}) - {reasoning}")
                
                # 記錄AI決策
                decision_id = recorder.record_ai_decision(
                    decision=decision,
                    confidence=confidence,
                    ai_signals={'test': True},
                    market_data={'current_price': current_price},
                    technical_indicators=indicators,
                    reasoning=reasoning
                )
                
                test_results['decisions'].append({
                    'decision': decision,
                    'confidence': confidence,
                    'reasoning': reasoning,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 如果是交易決策，執行交易
                if decision in ['BUY', 'SELL']:
                    print(f"   💰 執行交易決策...")
                    
                    # 安全檢查
                    trade_amount = 500.0
                    safety_check, safety_message = safety_framework.validate_trade_request(
                        trade_amount, confidence, {'test': True}
                    )
                    
                    if safety_check:
                        # 執行模擬交易
                        volume = trade_amount / current_price
                        
                        order_request = OrderRequest(
                            market="btctwd",
                            side=OrderSide.BUY if decision == 'BUY' else OrderSide.SELL,
                            order_type=OrderType.MARKET,
                            volume=volume
                        )
                        
                        success, order_response, message = await api_connector.place_order(order_request)
                        
                        if success and order_response:
                            print(f"   ✅ 交易成功 - ID: {order_response.id}")
                            
                            # 記錄交易
                            recorder.record_trade_execution(
                                trade_id=str(order_response.id),
                                market="btctwd",
                                side=order_response.side,
                                volume=order_response.volume,
                                price=order_response.avg_price or current_price,
                                commission=35.0,
                                ai_decision_id=decision_id
                            )
                            
                            test_results['trades'].append({
                                'trade_id': order_response.id,
                                'side': order_response.side,
                                'volume': order_response.volume,
                                'price': order_response.avg_price or current_price,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            # 模擬平倉
                            await asyncio.sleep(2)
                            exit_price = current_price * (1.01 if decision == 'BUY' else 0.99)
                            recorder.record_trade_close(str(order_response.id), exit_price)
                            
                        else:
                            print(f"   ❌ 交易失敗: {message}")
                            test_results['issues'].append(f"交易失敗: {message}")
                    else:
                        print(f"   ⚠️ 交易被拒絕: {safety_message}")
                        test_results['issues'].append(f"交易被拒絕: {safety_message}")
                
                # 更新監控
                status = recorder.get_real_time_status()
                monitor.update_metrics(
                    balance=status.get('current_balance', 10000),
                    daily_pnl=status.get('total_pnl', 0),
                    total_trades=status.get('total_trades', 0),
                    consecutive_losses=0,
                    ai_confidence=confidence
                )
                
                # 等待30秒
                if i < 2:  # 最後一次不等待
                    print("   ⏰ 等待30秒...")
                    await asyncio.sleep(30)
                
            except Exception as e:
                error_msg = f"決策循環 {i+1} 異常: {str(e)}"
                print(f"   ❌ {error_msg}")
                test_results['issues'].append(error_msg)
        
        # 6. 生成測試報告
        print("\n📊 生成測試報告...")
        
        final_metrics = recorder.calculate_performance_metrics()
        ai_analysis = recorder.get_ai_accuracy_analysis()
        
        test_results['performance'] = {
            'total_decisions': len(test_results['decisions']),
            'total_trades': final_metrics.total_trades,
            'win_rate': final_metrics.win_rate,
            'total_pnl': final_metrics.total_pnl,
            'ai_accuracy': final_metrics.ai_accuracy
        }
        
        test_results['end_time'] = datetime.now().isoformat()
        
        # 保存結果
        os.makedirs('AImax/logs/integration_tests', exist_ok=True)
        results_file = f"AImax/logs/integration_tests/simple_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        # 顯示結果
        print(f"\n🎉 測試完成！")
        print(f"📄 結果已保存至: {results_file}")
        print(f"\n📊 測試總結:")
        print(f"   🧠 AI決策次數: {test_results['performance']['total_decisions']}")
        print(f"   💰 總交易次數: {test_results['performance']['total_trades']}")
        print(f"   🎯 AI準確率: {test_results['performance']['ai_accuracy']:.1%}")
        print(f"   📈 交易勝率: {test_results['performance']['win_rate']:.1%}")
        print(f"   💵 總PnL: {test_results['performance']['total_pnl']:.2f} TWD")
        
        if test_results['issues']:
            print(f"\n⚠️ 遇到的問題:")
            for issue in test_results['issues']:
                print(f"   - {issue}")
        
        return test_results
        
    except Exception as e:
        print(f"\n❌ 測試異常: {e}")
        test_results['error'] = str(e)
        return test_results
        
    finally:
        # 清理資源
        print("\n🧹 清理系統資源...")
        
        try:
            if 'safety_framework' in locals():
                safety_framework.end_trading_session("測試完成")
            
            if 'monitor' in locals() and monitor.is_monitoring:
                monitor.stop_monitoring()
            
            if 'api_connector' in locals():
                await api_connector.disconnect()
            
            if 'data_manager' in locals():
                await data_manager.close()
            
            print("   ✅ 資源清理完成")
            
        except Exception as e:
            print(f"   ⚠️ 清理異常: {e}")


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 運行測試
    asyncio.run(run_simple_integration_test())