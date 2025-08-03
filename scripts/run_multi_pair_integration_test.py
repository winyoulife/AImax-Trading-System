#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易對系統整合測試執行腳本 - 任務8.1
"""

import sys
import os
import json
import time
from datetime import datetime

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def main():
    """主函數"""
    print("🚀 啟動多交易對系統整合測試")
    print("=" * 60)
    
    try:
        # 導入測試模塊
        from src.testing.multi_pair_system_integration_test import run_multi_pair_integration_test
        
        print("✅ 測試模塊導入成功")
        
        # 執行整合測試
        print("\n🧪 開始執行多交易對系統整合測試...")
        start_time = time.time()
        
        result = run_multi_pair_integration_test()
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # 分析測試結果
        print("\n📊 測試結果分析")
        print("-" * 40)
        
        if 'test_summary' in result:
            summary = result['test_summary']
            print(f"總測試數: {summary['total_tests']}")
            print(f"通過測試: {summary['passed_tests']}")
            print(f"失敗測試: {summary['failed_tests']}")
            print(f"成功率: {summary['success_rate']:.1%}")
            print(f"總耗時: {summary['total_duration']:.2f}秒")
        
        if 'system_performance' in result:
            performance = result['system_performance']
            print(f"\n🔧 系統性能指標")
            print(f"測試交易對數: {performance['tested_pairs']}")
            print(f"平均響應時間: {performance['avg_response_time']:.2f}秒")
            print(f"策略衝突數: {performance['total_conflicts']}")
            print(f"風險控制有效性: {performance['control_effectiveness']:.1%}")
            print(f"系統穩定率: {performance['stability_rate']:.1%}")
        
        # 顯示測試詳情
        if 'test_results' in result:
            print(f"\n📋 測試項目詳情")
            for i, test in enumerate(result['test_results'], 1):
                status = "✅ PASSED" if test['success'] else "❌ FAILED"
                print(f"{i}. {test['test_name']}: {status} ({test['duration']:.2f}s)")
                if not test['success'] and test['error_message']:
                    print(f"   錯誤: {test['error_message']}")
        
        # 顯示建議
        if 'recommendations' in result:
            print(f"\n💡 改進建議")
            for i, rec in enumerate(result['recommendations'], 1):
                print(f"{i}. {rec}")
        
        # 顯示整體評估
        if 'overall_assessment' in result:
            print(f"\n🎯 整體評估: {result['overall_assessment']}")
        
        # 保存詳細報告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"AImax/logs/multi_pair_integration_test_report_{timestamp}.json"
        
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 詳細測試報告已保存: {report_file}")
        
        # 判斷測試是否成功
        success_rate = result.get('test_summary', {}).get('success_rate', 0)
        if success_rate >= 0.8:
            print("\n🎉 多交易對系統整合測試成功完成！")
            print("✅ 系統已準備好進入下一階段開發")
            return True
        else:
            print(f"\n⚠️ 測試成功率 {success_rate:.1%} 低於預期")
            print("❌ 建議先解決發現的問題再繼續")
            return False
            
    except ImportError as e:
        print(f"❌ 模塊導入失敗: {e}")
        print("請確保所有依賴模塊都已正確安裝")
        return False
        
    except Exception as e:
        print(f"❌ 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)