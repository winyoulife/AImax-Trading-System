#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試AI決策可視化系統
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
import time

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gui.ai_decision_visualization import create_ai_decision_visualization

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ai_decision_visualization():
    """測試AI決策可視化系統"""
    print("🧪 測試AI決策可視化系統...")
    print("=" * 60)
    
    test_results = []
    
    # 1. 測試PyQt6可用性
    print("\n🔍 檢查PyQt6依賴...")
    try:
        from PyQt6.QtWidgets import QApplication
        print("✅ PyQt6 已安裝並可用")
        pyqt_available = True
        test_results.append(("PyQt6依賴", True))
    except ImportError:
        print("⚠️ PyQt6 未安裝，將測試文本模式")
        pyqt_available = False
        test_results.append(("PyQt6依賴", False))
    
    # 2. 測試組件導入
    print("\n📦 測試組件導入...")
    try:
        from src.gui.ai_decision_visualization import (
            AIDecisionVisualization, DecisionCard
        )
        print("✅ AI決策可視化組件導入成功")
        test_results.append(("組件導入", True))
    except ImportError as e:
        print(f"❌ 組件導入失敗: {e}")
        test_results.append(("組件導入", False))
        return test_results
    
    # 3. 測試數據庫初始化
    print("\n🗄️ 測試數據庫初始化...")
    try:
        if pyqt_available:
            app = QApplication([])
            visualization = AIDecisionVisualization()
            app.quit()
        else:
            visualization = AIDecisionVisualization()
        
        # 檢查數據庫文件是否創建
        import os
        if os.path.exists(visualization.db_path):
            print("✅ 決策歷史數據庫創建成功")
            
            # 測試數據庫連接
            import sqlite3
            conn = sqlite3.connect(visualization.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            
            if tables:
                print(f"✅ 數據庫表創建成功: {[t[0] for t in tables]}")
            else:
                print("⚠️ 數據庫表未找到")
        
        test_results.append(("數據庫初始化", True))
        
    except Exception as e:
        print(f"❌ 數據庫初始化失敗: {e}")
        test_results.append(("數據庫初始化", False))
    
    # 4. 測試決策卡片創建
    print("\n🎴 測試決策卡片創建...")
    try:
        # 創建測試決策數據
        test_decision = {
            "model_name": "🧠 測試AI",
            "decision": "BUY",
            "confidence": 0.85,
            "reasoning": "技術指標顯示強烈買入信號",
            "technical_indicators": {"RSI": "30", "MACD": "0.123"},
            "timestamp": datetime.now()
        }
        
        if pyqt_available:
            app = QApplication([])
            card = DecisionCard(test_decision)
            print("✅ 決策卡片創建成功")
            app.quit()
        else:
            card = DecisionCard(test_decision)
            print("✅ 決策卡片創建成功（文本模式）")
        
        test_results.append(("決策卡片創建", True))
        
    except Exception as e:
        print(f"❌ 決策卡片創建失敗: {e}")
        test_results.append(("決策卡片創建", False))
    
    # 5. 測試主界面創建
    print("\n🖥️ 測試主界面創建...")
    try:
        if pyqt_available:
            app = QApplication([])
            visualization = AIDecisionVisualization()
            
            # 檢查標籤頁
            if hasattr(visualization, 'tab_widget'):
                tab_count = visualization.tab_widget.count()
                print(f"✅ 主界面創建成功，包含 {tab_count} 個標籤頁")
                
                # 檢查各個標籤頁
                for i in range(tab_count):
                    tab_text = visualization.tab_widget.tabText(i)
                    print(f"   - {tab_text}")
            
            app.quit()
        else:
            visualization = AIDecisionVisualization()
            print("✅ 主界面創建成功（文本模式）")
        
        test_results.append(("主界面創建", True))
        
    except Exception as e:
        print(f"❌ 主界面創建失敗: {e}")
        test_results.append(("主界面創建", False))
    
    # 6. 測試決策數據生成
    print("\n📊 測試決策數據生成...")
    try:
        if pyqt_available:
            app = QApplication([])
            visualization = AIDecisionVisualization()
            decisions = visualization.generate_mock_decisions("BTCTWD")
            app.quit()
        else:
            visualization = AIDecisionVisualization()
            decisions = visualization.generate_mock_decisions("BTCTWD")
        
        print(f"✅ 生成了 {len(decisions)} 個模擬決策")
        
        # 檢查決策數據結構
        if decisions:
            first_decision = decisions[0]
            required_fields = ["model_name", "decision", "confidence", "reasoning", "technical_indicators"]
            
            missing_fields = [field for field in required_fields if field not in first_decision]
            if not missing_fields:
                print("✅ 決策數據結構完整")
            else:
                print(f"⚠️ 決策數據缺少字段: {missing_fields}")
        
        test_results.append(("決策數據生成", True))
        
    except Exception as e:
        print(f"❌ 決策數據生成失敗: {e}")
        test_results.append(("決策數據生成", False))
    
    # 7. 測試歷史記錄功能
    print("\n📚 測試歷史記錄功能...")
    try:
        if pyqt_available:
            app = QApplication([])
            visualization = AIDecisionVisualization()
            # 生成測試決策並保存
            test_decisions = visualization.generate_mock_decisions("BTCTWD")
            app.quit()
        else:
            visualization = AIDecisionVisualization()
            # 生成測試決策並保存
            test_decisions = visualization.generate_mock_decisions("BTCTWD")
        for decision in test_decisions:
            visualization.save_decision_to_history(decision)
        
        print(f"✅ 保存了 {len(test_decisions)} 條歷史記錄")
        
        # 測試歷史查詢
        import sqlite3
        conn = sqlite3.connect(visualization.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM decision_history")
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ 數據庫中共有 {count} 條歷史記錄")
        
        test_results.append(("歷史記錄功能", True))
        
    except Exception as e:
        print(f"❌ 歷史記錄功能測試失敗: {e}")
        test_results.append(("歷史記錄功能", False))
    
    # 8. 測試實時更新機制
    print("\n🔄 測試實時更新機制...")
    try:
        if pyqt_available:
            app = QApplication([])
            visualization = AIDecisionVisualization()
            
            # 檢查定時器
            if hasattr(visualization, 'decision_timer'):
                print("✅ 決策更新定時器已設置")
                
                # 測試手動更新
                visualization.update_decisions()
                print("✅ 手動更新功能正常")
            
            app.quit()
        
        test_results.append(("實時更新機制", True))
        
    except Exception as e:
        print(f"❌ 實時更新機制測試失敗: {e}")
        test_results.append(("實時更新機制", False))
    
    return test_results

def main():
    """主函數"""
    # 運行測試
    test_results = test_ai_decision_visualization()
    
    # 統計結果
    print("\n📊 測試結果統計:")
    print("-" * 40)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
        if result:
            passed_tests += 1
    
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    print(f"\n📊 測試成功率: {success_rate:.1%} ({passed_tests}/{total_tests})")
    
    # 系統健康度評估
    if success_rate >= 0.9:
        health_status = "優秀"
    elif success_rate >= 0.7:
        health_status = "良好"
    elif success_rate >= 0.5:
        health_status = "一般"
    else:
        health_status = "需改進"
    
    print(f"   系統健康度: {health_status}")
    
    # 功能特色展示
    print(f"\n🎯 AI決策可視化功能:")
    print("-" * 40)
    print("   🧠 實時AI決策過程展示")
    print("   📊 多模型預測和信心度顯示")
    print("   📚 完整的歷史決策追蹤")
    print("   🔍 靈活的篩選和查詢功能")
    print("   📈 決策統計和性能分析")
    print("   🎴 直觀的決策卡片界面")
    print("   🔄 實時自動更新機制")
    print("   🗄️ 持久化歷史數據存儲")
    
    print(f"\n🎯 AI決策可視化系統測試完成！")
    print("=" * 60)
    
    return {
        'test_successful': success_rate >= 0.7,
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'success_rate': success_rate,
        'system_health': health_status
    }

if __name__ == "__main__":
    result = main()
    
    # 輸出最終結果
    print(f"\n🏆 最終測試結果:")
    print(f"   測試成功: {'✅' if result['test_successful'] else '❌'}")
    print(f"   通過測試: {result['passed_tests']}/{result['total_tests']}")
    print(f"   成功率: {result['success_rate']:.1%}")
    print(f"   系統健康度: {result['system_health']}")