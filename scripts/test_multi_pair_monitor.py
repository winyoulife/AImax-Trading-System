#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易對監控界面測試腳本
測試多交易對監控界面的功能和性能
"""

import sys
import os
import logging
import time
from datetime import datetime
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('AImax/logs/multi_pair_monitor_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def test_multi_pair_monitor():
    """測試多交易對監控界面"""
    
    logger.info("🧪 開始測試多交易對監控界面")
    
    test_results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_details": []
    }
    
    try:
        # 測試1: 導入模塊
        logger.info("📦 測試1: 導入多交易對監控模塊")
        test_results["total_tests"] += 1
        
        try:
            from src.gui.multi_pair_monitor import (
                MultiPairMonitor, 
                PairMonitorCard, 
                MultiPairSummaryWidget
            )
            logger.info("✅ 模塊導入成功")
            test_results["passed_tests"] += 1
            test_results["test_details"].append({
                "test": "模塊導入",
                "status": "通過",
                "details": "所有核心類成功導入"
            })
        except Exception as e:
            logger.error(f"❌ 模塊導入失敗: {e}")
            test_results["failed_tests"] += 1
            test_results["test_details"].append({
                "test": "模塊導入",
                "status": "失敗",
                "details": str(e)
            })
            return test_results
        
        # 測試2: 創建監控界面實例
        logger.info("🏗️ 測試2: 創建多交易對監控界面實例")
        test_results["total_tests"] += 1
        
        try:
            monitor = MultiPairMonitor()
            logger.info("✅ 監控界面實例創建成功")
            test_results["passed_tests"] += 1
            test_results["test_details"].append({
                "test": "實例創建",
                "status": "通過",
                "details": "MultiPairMonitor實例創建成功"
            })
        except Exception as e:
            logger.error(f"❌ 實例創建失敗: {e}")
            test_results["failed_tests"] += 1
            test_results["test_details"].append({
                "test": "實例創建",
                "status": "失敗",
                "details": str(e)
            })
            return test_results
        
        # 測試3: 檢查默認交易對
        logger.info("📋 測試3: 檢查默認監控交易對")
        test_results["total_tests"] += 1
        
        try:
            expected_pairs = ["BTCTWD", "ETHTWD", "USDTTWD", "LTCTWD", "BCHTWD"]
            actual_pairs = monitor.monitored_pairs
            
            if actual_pairs == expected_pairs:
                logger.info(f"✅ 默認交易對正確: {actual_pairs}")
                test_results["passed_tests"] += 1
                test_results["test_details"].append({
                    "test": "默認交易對",
                    "status": "通過",
                    "details": f"監控{len(actual_pairs)}個交易對"
                })
            else:
                logger.warning(f"⚠️ 默認交易對不匹配: 期望{expected_pairs}, 實際{actual_pairs}")
                test_results["failed_tests"] += 1
                test_results["test_details"].append({
                    "test": "默認交易對",
                    "status": "失敗",
                    "details": f"期望{expected_pairs}, 實際{actual_pairs}"
                })
        except Exception as e:
            logger.error(f"❌ 檢查默認交易對失敗: {e}")
            test_results["failed_tests"] += 1
            test_results["test_details"].append({
                "test": "默認交易對",
                "status": "失敗",
                "details": str(e)
            })
        
        # 測試4: 測試交易對卡片創建
        logger.info("🎴 測試4: 測試交易對卡片創建")
        test_results["total_tests"] += 1
        
        try:
            card = PairMonitorCard("BTCTWD")
            
            # 檢查卡片屬性
            assert card.pair == "BTCTWD"
            assert card.is_active == False
            assert card.is_selected == False
            assert isinstance(card.price_data, dict)
            assert isinstance(card.trading_data, dict)
            
            logger.info("✅ 交易對卡片創建成功")
            test_results["passed_tests"] += 1
            test_results["test_details"].append({
                "test": "卡片創建",
                "status": "通過",
                "details": "PairMonitorCard創建並初始化成功"
            })
        except Exception as e:
            logger.error(f"❌ 交易對卡片創建失敗: {e}")
            test_results["failed_tests"] += 1
            test_results["test_details"].append({
                "test": "卡片創建",
                "status": "失敗",
                "details": str(e)
            })
        
        # 測試5: 測試數據更新功能
        logger.info("🔄 測試5: 測試數據更新功能")
        test_results["total_tests"] += 1
        
        try:
            # 測試價格數據更新
            price_data = {
                'current_price': 1500000.0,
                'price_change': 50000.0,
                'price_change_percent': 3.45,
                'volume_24h': 1000000.0,
                'high_24h': 1550000.0,
                'low_24h': 1450000.0
            }
            
            card.update_price_data(price_data)
            
            # 檢查數據是否更新
            assert card.price_data['current_price'] == 1500000.0
            assert card.price_data['price_change'] == 50000.0
            
            # 測試交易數據更新
            trading_data = {
                'position_count': 3,
                'total_position_size': 50000.0,
                'unrealized_pnl': 15000.0,
                'realized_pnl': 5000.0,
                'ai_confidence': 0.75,
                'risk_score': 0.3,
                'strategy_active': True
            }
            
            card.update_trading_data(trading_data)
            
            # 檢查數據是否更新
            assert card.trading_data['position_count'] == 3
            assert card.trading_data['ai_confidence'] == 0.75
            
            # 調試信息
            logger.info(f"調試: strategy_active = {trading_data['strategy_active']}")
            logger.info(f"調試: card.is_active = {card.is_active}")
            
            assert card.is_active == True
            
            logger.info("✅ 數據更新功能正常")
            test_results["passed_tests"] += 1
            test_results["test_details"].append({
                "test": "數據更新",
                "status": "通過",
                "details": "價格和交易數據更新功能正常"
            })
        except Exception as e:
            logger.error(f"❌ 數據更新功能測試失敗: {e}")
            test_results["failed_tests"] += 1
            test_results["test_details"].append({
                "test": "數據更新",
                "status": "失敗",
                "details": str(e)
            })
            import traceback
            logger.error(f"詳細錯誤: {traceback.format_exc()}")
        
        # 測試6: 測試摘要部件
        logger.info("📊 測試6: 測試多交易對摘要部件")
        test_results["total_tests"] += 1
        
        try:
            summary_widget = MultiPairSummaryWidget()
            
            # 測試摘要數據更新
            summary_data = {
                'active_pairs': 3,
                'total_pairs': 5,
                'total_positions': 12,
                'total_capital': 500000,
                'total_pnl': 25000,
                'risk_level': 'medium',
                'utilization_rate': 0.65,
                'daily_var': 30000,
                'max_drawdown': 0.08,
                'avg_confidence': 0.72,
                'accuracy_rate': 0.85
            }
            
            summary_widget.update_summary(summary_data)
            
            logger.info("✅ 摘要部件功能正常")
            test_results["passed_tests"] += 1
            test_results["test_details"].append({
                "test": "摘要部件",
                "status": "通過",
                "details": "MultiPairSummaryWidget功能正常"
            })
        except Exception as e:
            logger.error(f"❌ 摘要部件測試失敗: {e}")
            test_results["failed_tests"] += 1
            test_results["test_details"].append({
                "test": "摘要部件",
                "status": "失敗",
                "details": str(e)
            })
        
        # 測試7: 測試交易對設置功能
        logger.info("⚙️ 測試7: 測試交易對設置功能")
        test_results["total_tests"] += 1
        
        try:
            new_pairs = ["BTCTWD", "ETHTWD", "ADATWD"]
            monitor.set_monitored_pairs(new_pairs)
            
            assert monitor.monitored_pairs == new_pairs
            
            logger.info(f"✅ 交易對設置功能正常: {new_pairs}")
            test_results["passed_tests"] += 1
            test_results["test_details"].append({
                "test": "交易對設置",
                "status": "通過",
                "details": f"成功設置{len(new_pairs)}個交易對"
            })
        except Exception as e:
            logger.error(f"❌ 交易對設置功能測試失敗: {e}")
            test_results["failed_tests"] += 1
            test_results["test_details"].append({
                "test": "交易對設置",
                "status": "失敗",
                "details": str(e)
            })
        
        # 測試8: 測試模擬數據更新
        logger.info("🎲 測試8: 測試模擬數據更新")
        test_results["total_tests"] += 1
        
        try:
            # 重置為原始交易對
            monitor.set_monitored_pairs(["BTCTWD", "ETHTWD", "USDTTWD", "LTCTWD", "BCHTWD"])
            
            # 執行數據更新
            monitor.update_data()
            
            logger.info("✅ 模擬數據更新成功")
            test_results["passed_tests"] += 1
            test_results["test_details"].append({
                "test": "模擬數據更新",
                "status": "通過",
                "details": "模擬數據生成和更新功能正常"
            })
        except Exception as e:
            logger.error(f"❌ 模擬數據更新失敗: {e}")
            test_results["failed_tests"] += 1
            test_results["test_details"].append({
                "test": "模擬數據更新",
                "status": "失敗",
                "details": str(e)
            })
        
        # 測試9: 測試選中功能
        logger.info("🎯 測試9: 測試交易對選中功能")
        test_results["total_tests"] += 1
        
        try:
            # 模擬選中事件
            monitor.on_pair_selected("BTCTWD")
            
            assert monitor.get_selected_pair() == "BTCTWD"
            
            logger.info("✅ 交易對選中功能正常")
            test_results["passed_tests"] += 1
            test_results["test_details"].append({
                "test": "選中功能",
                "status": "通過",
                "details": "交易對選中和狀態管理正常"
            })
        except Exception as e:
            logger.error(f"❌ 交易對選中功能測試失敗: {e}")
            test_results["failed_tests"] += 1
            test_results["test_details"].append({
                "test": "選中功能",
                "status": "失敗",
                "details": str(e)
            })
        
        # 測試10: 測試操作功能
        logger.info("🔧 測試10: 測試交易對操作功能")
        test_results["total_tests"] += 1
        
        try:
            # 測試各種操作
            operations = ["view", "start", "stop", "close_all", "config"]
            
            for operation in operations:
                monitor.on_pair_action("BTCTWD", operation)
            
            logger.info("✅ 交易對操作功能正常")
            test_results["passed_tests"] += 1
            test_results["test_details"].append({
                "test": "操作功能",
                "status": "通過",
                "details": f"測試了{len(operations)}種操作"
            })
        except Exception as e:
            logger.error(f"❌ 交易對操作功能測試失敗: {e}")
            test_results["failed_tests"] += 1
            test_results["test_details"].append({
                "test": "操作功能",
                "status": "失敗",
                "details": str(e)
            })
        
    except Exception as e:
        logger.error(f"❌ 測試過程中發生未預期錯誤: {e}")
        test_results["failed_tests"] += 1
        test_results["test_details"].append({
            "test": "整體測試",
            "status": "失敗",
            "details": f"未預期錯誤: {str(e)}"
        })
    
    return test_results

def generate_test_report(test_results: dict):
    """生成測試報告"""
    
    logger.info("📋 生成測試報告")
    
    # 計算成功率
    success_rate = (test_results["passed_tests"] / test_results["total_tests"]) * 100 if test_results["total_tests"] > 0 else 0
    
    # 創建報告
    report = {
        "test_name": "多交易對監控界面測試",
        "test_time": datetime.now().isoformat(),
        "summary": {
            "total_tests": test_results["total_tests"],
            "passed_tests": test_results["passed_tests"],
            "failed_tests": test_results["failed_tests"],
            "success_rate": f"{success_rate:.1f}%"
        },
        "test_details": test_results["test_details"],
        "system_info": {
            "python_version": sys.version,
            "platform": sys.platform
        }
    }
    
    # 保存報告
    report_file = f"AImax/logs/multi_pair_monitor_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 測試報告已保存: {report_file}")
    except Exception as e:
        logger.error(f"❌ 保存測試報告失敗: {e}")
    
    return report

def main():
    """主函數"""
    
    logger.info("🚀 啟動多交易對監控界面測試")
    
    try:
        # 確保日誌目錄存在
        os.makedirs("AImax/logs", exist_ok=True)
        
        # 執行測試
        test_results = test_multi_pair_monitor()
        
        # 生成報告
        report = generate_test_report(test_results)
        
        # 輸出測試結果
        logger.info("=" * 60)
        logger.info("📊 多交易對監控界面測試結果")
        logger.info("=" * 60)
        logger.info(f"總測試數: {test_results['total_tests']}")
        logger.info(f"通過測試: {test_results['passed_tests']}")
        logger.info(f"失敗測試: {test_results['failed_tests']}")
        logger.info(f"成功率: {report['summary']['success_rate']}")
        
        # 詳細結果
        logger.info("\n📋 詳細測試結果:")
        for detail in test_results["test_details"]:
            status_icon = "✅" if detail["status"] == "通過" else "❌"
            logger.info(f"{status_icon} {detail['test']}: {detail['status']} - {detail['details']}")
        
        # 總結
        if test_results["failed_tests"] == 0:
            logger.info("\n🎉 所有測試通過！多交易對監控界面功能完整")
        else:
            logger.warning(f"\n⚠️ 有 {test_results['failed_tests']} 個測試失敗，需要檢查和修復")
        
        logger.info("✅ 多交易對監控界面測試完成")
        
        return test_results["failed_tests"] == 0
        
    except Exception as e:
        logger.error(f"❌ 測試執行失敗: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)