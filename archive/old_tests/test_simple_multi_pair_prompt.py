#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡化的多交易對AI提示詞測試
"""

import sys
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_simple():
    """簡化測試"""
    print("🧪 簡化測試開始...")
    
    try:
        # 測試導入
        from src.ai.enhanced_ai_manager import create_enhanced_ai_manager
        from src.ai.multi_pair_prompt_optimizer import create_multi_pair_prompt_optimizer
        
        print("✅ 導入成功")
        
        # 測試初始化
        ai_manager = create_enhanced_ai_manager()
        prompt_optimizer = create_multi_pair_prompt_optimizer()
        
        print("✅ 初始化成功")
        
        # 檢查方法是否存在
        if hasattr(ai_manager, '_create_multi_pair_context'):
            print("✅ _create_multi_pair_context 方法存在")
        else:
            print("❌ _create_multi_pair_context 方法不存在")
            
        if hasattr(ai_manager, 'analyze_multi_pair_market'):
            print("✅ analyze_multi_pair_market 方法存在")
        else:
            print("❌ analyze_multi_pair_market 方法不存在")
            
        # 測試方法調用
        test_data = {
            "BTCTWD": {
                "current_price": 3482629,
                "volatility": 0.025
            }
        }
        
        context = ai_manager._create_multi_pair_context(test_data)
        print(f"✅ 上下文創建成功: {context.total_pairs} 個交易對")
        
        print("🎉 簡化測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple()
    sys.exit(0 if success else 1)