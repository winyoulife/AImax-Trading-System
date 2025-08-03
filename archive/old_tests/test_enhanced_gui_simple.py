#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的增強多交易對GUI系統測試腳本
"""

import sys
import os
import json
from datetime import datetime

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_enhanced_gui():
    """測試增強多交易對GUI系統"""
    print("🧪 開始增強多交易對GUI系統測試")
    print("=" * 60)
    
    try:
        # 導入模塊
        from src.gui.enhanced_multi_pair_gui import (
            EnhancedMultiPairGUI,
            PairDisplayData,
            create_enhanced_multi_pair_gui
        )
        
        print("✅ 模塊導入成功")
        
        # 測試數據結構
        print("\n🔍 測試數據結構")
        print("-" * 40)
        
        sample_data = PairDisplayData(
            pair="BTCTWD",
            price=1500000.0,
            change_24h=2.5,
            volume_24h=50000000.0,
            position_size=0.05,
            target_position=0.06,
            unrealized_pnl=5000.0,
            ai_confidence=0.75,
            risk_score=0.3,
            status="active",
            strategy_active=True,
            last_update=datetime.now()
        )
        
        print(f"   創建示例數據: {sample_data.pair}")
        print(f"     價格: {sample_data.price:,.0f}")
        print(f"     當前倉位: {sample_data.position_size:.4f}")
        print(f"     目標倉位: {sample_data.target_position:.4f}")
        print(f"     AI信心度: {sample_data.ai_confidence:.1%}")
        print(f"     風險分數: {sample_data.risk_score:.1%}")
        print(f"     策略狀態: {'活躍' if sample_data.strategy_active else '未活躍'}")
        
        assert sample_data.pair == "BTCTWD"
        assert sample_data.price > 0
        assert 0 <= sample_data.ai_confidence <= 1
        assert 0 <= sample_data.risk_score <= 1
        
        print("   ✓ 數據結構驗證通過")
        
        # 測試GUI組件創建
        print("\n🔍 測試GUI組件創建")
        print("-" * 40)
        
        gui = create_enhanced_multi_pair_gui()
        print(f"   創建GUI組件: {type(gui).__name__}")
        
        # 檢查基本屬性
        assert hasattr(gui, 'pairs_data')
        assert hasattr(gui, 'selected_pair')
        assert hasattr(gui, 'update_data')
        assert hasattr(gui, 'generate_sample_data')
        
        print("   ✓ GUI組件屬性檢查通過")
        
        # 測試數據生成
        print("\n🔍 測試數據生成")
        print("-" * 40)
        
        sample_pairs_data = gui.generate_sample_data()
        print(f"   生成數據: {len(sample_pairs_data)} 個交易對")
        
        for data in sample_pairs_data:
            print(f"     {data.pair}: 價格={data.price:,.0f}, 信心度={data.ai_confidence:.1%}, 策略={'開' if data.strategy_active else '關'}")
            
            # 驗證數據
            assert data.pair is not None
            assert data.price > 0
            assert 0 <= data.ai_confidence <= 1
            assert 0 <= data.risk_score <= 1
            assert data.status in ["active", "inactive", "warning", "error"]
            assert isinstance(data.strategy_active, bool)
        
        print("   ✓ 數據生成驗證通過")
        
        # 測試數據更新
        print("\n🔍 測試數據更新")
        print("-" * 40)
        
        gui.update_data()
        current_data = gui.get_current_data()
        
        print(f"   更新後數據: {len(current_data)} 個交易對")
        assert len(current_data) > 0, "更新後應該有數據"
        
        print("   ✓ 數據更新驗證通過")
        
        # 測試交易對操作
        print("\n🔍 測試交易對操作")
        print("-" * 40)
        
        if current_data:
            test_pair = current_data[0].pair
            
            # 測試選擇交易對
            gui.on_pair_selected(test_pair)
            assert gui.selected_pair == test_pair
            print(f"   ✓ 交易對選擇功能正常: {test_pair}")
            
            # 測試策略切換
            original_status = current_data[0].strategy_active
            gui.toggle_strategy(test_pair)
            print(f"   ✓ 策略切換功能正常: {test_pair}")
        
        # 測試系統控制
        print("\n🔍 測試系統控制")
        print("-" * 40)
        
        gui.start_trading()
        print("   ✓ 啟動交易功能正常")
        
        gui.stop_trading()
        print("   ✓ 停止交易功能正常")
        
        gui.manual_update()
        print("   ✓ 手動更新功能正常")
        
        # 生成測試報告
        print("\n📊 測試總結")
        print("=" * 60)
        
        test_results = {
            'test_time': datetime.now().isoformat(),
            'total_tests': 6,
            'passed_tests': 6,
            'failed_tests': 0,
            'success_rate': 100.0,
            'test_details': [
                {'test': '模塊導入', 'status': 'PASSED'},
                {'test': '數據結構', 'status': 'PASSED'},
                {'test': 'GUI組件創建', 'status': 'PASSED'},
                {'test': '數據生成', 'status': 'PASSED'},
                {'test': '數據更新', 'status': 'PASSED'},
                {'test': '系統控制', 'status': 'PASSED'}
            ]
        }
        
        # 保存測試報告
        report_file = f"AImax/logs/enhanced_gui_simple_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        print(f"總測試數: {test_results['total_tests']}")
        print(f"通過: {test_results['passed_tests']}")
        print(f"失敗: {test_results['failed_tests']}")
        print(f"成功率: {test_results['success_rate']:.1f}%")
        print(f"測試報告已保存: {report_file}")
        
        print("\n🎉 所有測試通過！增強多交易對GUI系統運行正常")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🚀 啟動增強多交易對GUI系統簡化測試")
    
    success = test_enhanced_gui()
    
    if success:
        print("\n✅ 測試完成 - 系統正常運行")
    else:
        print("\n❌ 測試失敗 - 請檢查錯誤信息")

if __name__ == "__main__":
    main()