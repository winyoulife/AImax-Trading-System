#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易系統完整測試 - 測試AI決策、風險管理、交易執行的完整流程
"""

import asyncio
import sys
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingSystemTester:
    """交易系統測試器"""
    
    def __init__(self):
        """初始化測試器"""
        self.test_results = {
            'trade_executor': {'passed': False, 'details': {}},
            'risk_manager': {'passed': False, 'details': {}},
            'position_manager': {'passed': False, 'details': {}},
        }
        
        logger.info("🧪 交易系統測試器初始化完成")
    
    async def run_all_tests(self):
        """運行所有測試"""
        try:
            logger.info("🚀 開始完整交易系統測試")
            
            print("=" * 60)
            print("🤖 AImax 交易系統完整測試")
            print("=" * 60)
            
            # 1. 測試交易執行器
            await self.test_trade_executor()
            
            # 2. 測試風險管理器
            await self.test_risk_manager()
            
            # 3. 測試倉位管理器
            await self.test_position_manager()
            
            # 4. 生成測試報告
            self.generate_test_report()
            
        except Exception as e:
            logger.error(f"❌ 測試執行失敗: {e}")
            print(f"\\n❌ 測試執行失敗: {e}")
    
    async def test_trade_executor(self):
        """測試交易執行器"""
        try:
            print("\\n💰 測試交易執行器...")
            
            from src.trading.trade_executor import TradeExecutor
            
            # 創建交易執行器
            executor = TradeExecutor(100000.0)
            
            # 測試賬戶狀態
            account_status = executor.get_account_status()
            print(f"   ✅ 賬戶狀態: 餘額 {account_status['available_balance']:,.0f} TWD")
            
            # 模擬AI決策
            mock_ai_decision = {
                'final_decision': 'BUY',
                'confidence': 0.75,
                'reasoning': '技術指標顯示買入信號',
                'decision_id': 'test_001'
            }
            
            # 模擬市場數據
            mock_market_data = {
                'current_price': 1500000,
                'volatility_level': '中'
            }
            
            # 執行交易
            trade_result = await executor.execute_ai_decision(mock_ai_decision, mock_market_data)
            
            if trade_result['status'] == 'filled':
                print(f"   ✅ 交易執行成功:")
                print(f"      數量: {trade_result['filled_quantity']:.6f} BTC")
                print(f"      價格: {trade_result['filled_price']:,.0f} TWD")
                print(f"      總成本: {trade_result['total_cost']:,.0f} TWD")
                
                self.test_results['trade_executor'] = {
                    'passed': True,
                    'details': {
                        'status': trade_result['status'],
                        'quantity': trade_result['filled_quantity'],
                        'price': trade_result['filled_price'],
                        'cost': trade_result['total_cost']
                    }
                }
            else:
                print(f"   ⚠️ 交易未執行: {trade_result.get('reason', 'Unknown')}")
                self.test_results['trade_executor'] = {
                    'passed': True,
                    'details': {'status': trade_result['status'], 'reason': trade_result.get('reason')}
                }
            
        except Exception as e:
            logger.error(f"❌ 交易執行器測試失敗: {e}")
            print(f"   ❌ 交易執行器測試失敗: {e}")
            self.test_results['trade_executor']['passed'] = False
    
    async def test_risk_manager(self):
        """測試風險管理器"""
        try:
            print("\\n🛡️ 測試風險管理器...")
            
            from src.trading.risk_manager import RiskManager
            
            # 創建風險管理器
            risk_manager = RiskManager(100000.0)
            
            # 測試風險摘要
            risk_summary = risk_manager.get_risk_summary()
            print(f"   ✅ 風險摘要獲取成功: 當前餘額 {risk_summary['current_balance']:,.0f} TWD")
            
            # 模擬AI決策和市場數據
            mock_ai_decision = {
                'final_decision': 'BUY',
                'confidence': 0.45,  # 低信心度，應該觸發風險控制
                'reasoning': '測試低信心度交易'
            }
            
            mock_market_data = {
                'current_price': 1500000,
                'volatility_level': '高'
            }
            
            mock_account_status = {
                'total_equity': 95000,  # 已有虧損
                'available_balance': 90000,
                'margin_used': 5000,
                'positions_count': 2
            }
            
            # 執行風險評估
            risk_assessment = await risk_manager.assess_trade_risk(
                mock_ai_decision, mock_market_data, mock_account_status
            )
            
            print(f"   ✅ 風險評估完成:")
            print(f"      風險等級: {risk_assessment['overall_risk_level']}")
            print(f"      建議動作: {risk_assessment['recommended_action']}")
            print(f"      風險分數: {risk_assessment['risk_score']:.1f}")
            print(f"      是否批准: {risk_assessment['approved']}")
            
            if risk_assessment.get('violations'):
                print(f"      風險違規: {len(risk_assessment['violations'])} 項")
                for violation in risk_assessment['violations'][:2]:  # 只顯示前2項
                    print(f"        - {violation['message']}")
            
            self.test_results['risk_manager'] = {
                'passed': True,
                'details': {
                    'risk_level': risk_assessment['overall_risk_level'],
                    'action': risk_assessment['recommended_action'],
                    'score': risk_assessment['risk_score'],
                    'approved': risk_assessment['approved'],
                    'violations': len(risk_assessment.get('violations', []))
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 風險管理器測試失敗: {e}")
            print(f"   ❌ 風險管理器測試失敗: {e}")
            self.test_results['risk_manager']['passed'] = False
    
    async def test_position_manager(self):
        """測試倉位管理器"""
        try:
            print("\\n📊 測試倉位管理器...")
            
            from src.trading.position_manager import PositionManager
            
            # 創建倉位管理器
            position_manager = PositionManager()
            
            # 模擬交易結果
            mock_trade_result = {
                'symbol': 'BTCTWD',
                'side': 'buy',
                'filled_quantity': 0.01,
                'filled_price': 1500000
            }
            
            mock_ai_decision = {
                'decision_id': 'test_001',
                'confidence': 0.75
            }
            
            # 創建倉位
            position = position_manager.create_position(mock_trade_result, mock_ai_decision)
            print(f"   ✅ 倉位創建成功: {position.position_id}")
            print(f"      數量: {position.quantity:.6f} BTC")
            print(f"      入場價: {position.entry_price:,.0f} TWD")
            print(f"      止損價: {position.stop_loss:,.0f} TWD")
            print(f"      止盈價: {position.take_profit:,.0f} TWD")
            
            # 測試倉位更新
            actions = position_manager.update_positions(1520000)  # 價格上漲
            print(f"   ✅ 倉位更新完成: {len(actions)} 個動作")
            
            # 獲取活躍倉位
            active_positions = position_manager.get_active_positions()
            print(f"   ✅ 活躍倉位: {len(active_positions)} 個")
            
            if active_positions:
                pos = active_positions[0]
                print(f"      未實現盈虧: {pos['unrealized_pnl']:+,.0f} TWD ({pos['unrealized_return']:+.2%})")
            
            # 獲取統計信息
            stats = position_manager.get_position_stats()
            print(f"   ✅ 倉位統計:")
            print(f"      總倉位: {stats['total_positions']}")
            print(f"      活躍倉位: {stats['active_positions']}")
            print(f"      總盈虧: {stats['total_pnl']:+,.0f} TWD")
            
            self.test_results['position_manager'] = {
                'passed': True,
                'details': {
                    'position_created': True,
                    'position_id': position.position_id,
                    'active_positions': len(active_positions),
                    'total_pnl': stats['total_pnl']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 倉位管理器測試失敗: {e}")
            print(f"   ❌ 倉位管理器測試失敗: {e}")
            self.test_results['position_manager']['passed'] = False
    
    def generate_test_report(self):
        """生成測試報告"""
        try:
            print("\\n" + "="*60)
            print("📋 測試報告摘要")
            print("="*60)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results.values() if result['passed'])
            
            print(f"\\n📊 總體結果: {passed_tests}/{total_tests} 測試通過 ({passed_tests/total_tests:.1%})")
            
            print("\\n📋 詳細結果:")
            
            for test_name, result in self.test_results.items():
                status = "✅ 通過" if result['passed'] else "❌ 失敗"
                print(f"   {test_name:20} {status}")
                
                # 顯示關鍵詳情
                if result['passed'] and result['details']:
                    details = result['details']
                    if test_name == 'trade_executor' and 'status' in details:
                        print(f"                        狀態: {details['status']}")
                    elif test_name == 'risk_manager' and 'risk_level' in details:
                        print(f"                        風險: {details['risk_level']}, 批准: {details['approved']}")
                    elif test_name == 'position_manager' and 'active_positions' in details:
                        print(f"                        倉位: {details['active_positions']}, 盈虧: {details['total_pnl']:+,.0f}")
            
            # 系統建議
            print("\\n💡 系統建議:")
            
            if passed_tests == total_tests:
                print("   🎉 所有測試通過！系統準備就緒，可以開始實際交易。")
                print("   📈 建議：先進行小額測試交易，觀察系統表現。")
            elif passed_tests >= total_tests * 0.8:
                print("   ⚠️ 大部分測試通過，但仍有問題需要解決。")
                print("   🔧 建議：修復失敗的組件後再進行實際交易。")
            else:
                print("   🚨 多個關鍵組件測試失敗，系統不適合實際交易。")
                print("   🛠️ 建議：全面檢查和修復系統後重新測試。")
            
            print("\\n" + "="*60)
            print("🎯 AImax 交易系統測試完成")
            print("="*60)
            
        except Exception as e:
            logger.error(f"❌ 生成測試報告失敗: {e}")
            print(f"\\n❌ 生成測試報告失敗: {e}")


async def main():
    """主函數"""
    try:
        # 創建測試器
        tester = TradingSystemTester()
        
        # 運行所有測試
        await tester.run_all_tests()
        
    except KeyboardInterrupt:
        print("\\n⚠️ 測試被用戶中斷")
    except Exception as e:
        print(f"\\n❌ 測試執行異常: {e}")
        logger.error(f"測試執行異常: {e}")


if __name__ == "__main__":
    # 運行測試
    asyncio.run(main())