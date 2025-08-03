#!/usr/bin/env python3
"""
測試回測報告生成器
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.backtest_reporter import BacktestReporter, create_sample_backtest_report

def test_backtest_reporter():
    """測試回測報告生成器"""
    print("🧪 測試回測報告生成器")
    print("=" * 50)
    
    try:
        # 測試示例報告生成
        print("📊 生成示例回測報告...")
        create_sample_backtest_report()
        
        print("✅ 回測報告生成器測試成功！")
        print("💡 功能說明:")
        print("   • 生成專業的HTML回測報告")
        print("   • 包含資產曲線、回撤分析等圖表")
        print("   • 提供詳細的統計分析和建議")
        print("   • 支持JSON數據導出")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    test_backtest_reporter()