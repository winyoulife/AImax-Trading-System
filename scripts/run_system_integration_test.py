#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
運行系統整合測試腳本
"""

import sys
import os
import logging
from datetime import datetime
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.testing.system_integration_test import create_system_integration_test

def main():
    """主函數"""
    print("🚀 AImax系統整合測試")
    print("=" * 60)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 設置日誌
    log_dir = Path("AImax/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'system_integration_test.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # 創建測試實例
        print("\n🔧 初始化測試環境...")
        test_runner = create_system_integration_test()
        
        # 運行所有測試
        print("\n🧪 開始執行系統整合測試...")
        results = test_runner.run_all_tests()
        
        if results.get('success', False):
            # 顯示測試結果
            print("\n" + "=" * 60)
            print("🎯 系統整合測試完成！")
            print("=" * 60)
            
            # 基本統計
            total_tests = results.get('total_tests', 0)
            passed_tests = results.get('passed_tests', 0)
            success_rate = results.get('success_rate', 0)
            test_duration = results.get('test_duration', 0)
            system_health = results.get('system_health', '未知')
            
            print(f"\n📊 測試統計:")
            print(f"   總測試數: {total_tests}")
            print(f"   通過測試: {passed_tests}")
            print(f"   失敗測試: {total_tests - passed_tests}")
            print(f"   成功率: {success_rate:.1%}")
            print(f"   測試時長: {test_duration:.2f}秒")
            print(f"   系統健康度: {system_health}")
            
            # 詳細結果
            if 'detailed_results' in results:
                print(f"\n📋 詳細測試結果:")
                print("-" * 40)
                
                for category, category_results in results['detailed_results'].items():
                    print(f"\n🔍 {category}:")
                    
                    if isinstance(category_results, dict):
                        for test_name, result in category_results.items():
                            if isinstance(result, bool):
                                status = "✅ 通過" if result else "❌ 失敗"
                            elif isinstance(result, (int, float)) and not isinstance(result, bool):
                                status = f"📊 {result:.3f}" if isinstance(result, float) else f"📊 {result}"
                            else:
                                status = f"📊 {result}"
                            
                            print(f"   {test_name}: {status}")
            
            # 生成測試報告
            print(f"\n📄 生成測試報告...")
            report = test_runner.generate_test_report(results)
            
            # 保存報告
            reports_dir = Path("AImax/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存Markdown報告
            report_path = reports_dir / f"system_integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"   Markdown報告: {report_path}")
            
            # 保存JSON結果
            json_path = reports_dir / f"system_integration_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import json
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            print(f"   JSON結果: {json_path}")
            
            # 系統建議
            print(f"\n💡 系統建議:")
            if success_rate >= 0.95:
                print("   🏆 系統運行優秀，所有組件協作良好！")
            elif success_rate >= 0.85:
                print("   ✅ 系統運行良好，建議關注失敗的測試項目。")
            elif success_rate >= 0.70:
                print("   ⚠️ 系統運行一般，建議檢查和修復失敗的組件。")
            else:
                print("   🚨 系統需要改進，請優先修復關鍵組件問題。")
            
            print(f"\n🎯 測試完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            return 0
            
        else:
            print(f"\n❌ 系統整合測試失敗:")
            print(f"   錯誤信息: {results.get('error', '未知錯誤')}")
            return 1
        
    except Exception as e:
        logger.error(f"❌ 測試執行失敗: {e}")
        print(f"\n❌ 測試執行失敗: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)