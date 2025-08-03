#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化版實盤測試結果分析
"""

import json
import os
from datetime import datetime
from pathlib import Path

def analyze_live_test_results():
    """分析實盤測試結果"""
    print("🔍 AImax 實盤測試結果分析")
    print("=" * 40)
    
    try:
        # 載入最新的測試結果
        test_dir = Path("AImax/logs/integration_tests")
        if not test_dir.exists():
            print("❌ 未找到測試結果目錄")
            return
        
        test_files = list(test_dir.glob("*.json"))
        if not test_files:
            print("❌ 未找到測試結果文件")
            return
        
        latest_test = max(test_files, key=lambda x: x.stat().st_mtime)
        print(f"📄 分析文件: {latest_test.name}")
        
        with open(latest_test, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        
        # 分析測試結果
        print("\n📊 測試概覽:")
        print(f"   開始時間: {test_data.get('start_time', 'N/A')}")
        print(f"   結束時間: {test_data.get('end_time', 'N/A')}")
        print(f"   AI決策次數: {len(test_data.get('decisions', []))}")
        print(f"   執行交易次數: {len(test_data.get('trades', []))}")
        
        # 分析AI決策
        decisions = test_data.get('decisions', [])
        if decisions:
            print(f"\n🧠 AI決策分析:")
            buy_decisions = [d for d in decisions if d['decision'] == 'BUY']
            sell_decisions = [d for d in decisions if d['decision'] == 'SELL']
            hold_decisions = [d for d in decisions if d['decision'] == 'HOLD']
            
            print(f"   買入決策: {len(buy_decisions)} 次")
            print(f"   賣出決策: {len(sell_decisions)} 次")
            print(f"   觀望決策: {len(hold_decisions)} 次")
            
            # 計算平均信心度
            avg_confidence = sum(d['confidence'] for d in decisions) / len(decisions)
            print(f"   平均信心度: {avg_confidence:.1%}")
        
        # 分析交易執行
        trades = test_data.get('trades', [])
        if trades:
            print(f"\n💰 交易執行分析:")
            buy_trades = [t for t in trades if t['side'] == 'buy']
            sell_trades = [t for t in trades if t['side'] == 'sell']
            
            print(f"   買入交易: {len(buy_trades)} 筆")
            print(f"   賣出交易: {len(sell_trades)} 筆")
            
            # 計算平均交易金額
            if trades:
                avg_volume = sum(t['volume'] for t in trades) / len(trades)
                avg_price = sum(t['price'] for t in trades) / len(trades)
                print(f"   平均交易量: {avg_volume:.6f} BTC")
                print(f"   平均交易價格: {avg_price:.0f} TWD")
        
        # 檢查問題
        issues = test_data.get('issues', [])
        if issues:
            print(f"\n⚠️ 遇到的問題:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ 測試過程無問題")
        
        # 生成性能評估
        print(f"\n📈 性能評估:")
        
        # 決策效率
        total_decisions = len(decisions)
        trading_decisions = len([d for d in decisions if d['decision'] in ['BUY', 'SELL']])
        if total_decisions > 0:
            decision_rate = trading_decisions / total_decisions
            print(f"   交易決策率: {decision_rate:.1%}")
        
        # 系統穩定性
        error_count = len(issues)
        if error_count == 0:
            print(f"   系統穩定性: 優秀 (無錯誤)")
        elif error_count <= 2:
            print(f"   系統穩定性: 良好 ({error_count}個問題)")
        else:
            print(f"   系統穩定性: 需改進 ({error_count}個問題)")
        
        # AI表現
        if avg_confidence > 0.7:
            print(f"   AI信心度: 優秀 ({avg_confidence:.1%})")
        elif avg_confidence > 0.5:
            print(f"   AI信心度: 良好 ({avg_confidence:.1%})")
        else:
            print(f"   AI信心度: 需改進 ({avg_confidence:.1%})")
        
        # 生成建議
        print(f"\n💡 改進建議:")
        
        if avg_confidence < 0.6:
            print("   - 優化AI提示詞，提高決策信心度")
        
        if decision_rate < 0.3:
            print("   - 調整決策閾值，增加交易機會")
        
        if error_count > 0:
            print("   - 加強錯誤處理機制")
        
        if len(trades) == 0:
            print("   - 檢查交易執行邏輯，確保能夠執行交易")
        
        if not any([avg_confidence < 0.6, decision_rate < 0.3, error_count > 0, len(trades) == 0]):
            print("   - 系統運行良好，可以考慮增加測試時間或交易頻率")
        
        # 保存分析結果
        analysis_dir = Path("AImax/logs/performance_analysis")
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        analysis_result = {
            'analysis_time': datetime.now().isoformat(),
            'test_file': str(latest_test),
            'summary': {
                'total_decisions': total_decisions,
                'trading_decisions': trading_decisions,
                'total_trades': len(trades),
                'avg_confidence': avg_confidence if decisions else 0,
                'error_count': error_count,
                'decision_rate': decision_rate if total_decisions > 0 else 0
            },
            'recommendations': []
        }
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        analysis_file = analysis_dir / f"analysis_{timestamp}.json"
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 分析結果已保存至: {analysis_file}")
        print(f"\n🎉 性能分析完成！")
        
        return analysis_result
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        return None

if __name__ == "__main__":
    analyze_live_test_results()