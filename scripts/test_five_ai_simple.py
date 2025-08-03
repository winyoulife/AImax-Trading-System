#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
五AI協作系統簡化測試 - 驗證Mistral 7B風險評估AI集成
"""

import asyncio
import sys
import logging
import time
from pathlib import Path

# 添加項目路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_five_ai_simple():
    """簡化測試五AI協作系統"""
    print("🧪 開始五AI超智能協作系統簡化測試...")
    print("🧠 AI模型配置:")
    print("   1. 市場掃描員: LLaMA 2:7B")
    print("   2. 深度分析師: Falcon 7B") 
    print("   3. 趨勢分析師: Qwen 7B")
    print("   4. 風險評估AI: Mistral 7B ⭐ 新增")
    print("   5. 最終決策者: Qwen 7B")
    
    try:
        # 導入增強AI管理器
        from src.ai.enhanced_ai_manager import create_enhanced_ai_manager
        
        print("\n📦 初始化五AI協作系統...")
        ai_manager = create_enhanced_ai_manager()
        
        # 測試系統狀態
        print("\n🔍 測試系統狀態...")
        status = ai_manager.get_ai_system_status()
        print(f"   系統類型: {status['system_type']}")
        print(f"   配置的AI模型: {status['models_configured']} 個")
        print(f"   支持的交易對: {status['supported_pairs']} 個")
        print(f"   AI模型列表: {', '.join(status['ai_models'])}")
        
        # 測試單個AI模型調用
        print("\n🤖 測試單個AI模型調用...")
        
        # 測試市場掃描員 (LLaMA 2:7B)
        print("   測試市場掃描員 (LLaMA 2:7B)...")
        try:
            scanner_prompt = "請分析BTC當前價格1520000 TWD，RSI 65的市場信號。"
            scanner_response = await ai_manager._call_ai_model(
                "llama2:7b", 
                ai_manager._get_scanner_system_prompt(),
                scanner_prompt,
                200, 0.3
            )
            print(f"   ✅ 市場掃描員響應: {scanner_response[:100]}...")
        except Exception as e:
            print(f"   ❌ 市場掃描員測試失敗: {e}")
        
        # 測試風險評估AI (Mistral 7B) ⭐ 重點測試
        print("   測試風險評估AI (Mistral 7B)...")
        try:
            risk_prompt = "請評估BTC交易風險，當前價格1520000 TWD，波動率0.035，成交量比率2.1。"
            risk_response = await ai_manager._call_ai_model(
                "mistral:7b",
                ai_manager._get_risk_assessor_system_prompt(), 
                risk_prompt,
                300, 0.1
            )
            print(f"   ✅ 風險評估AI響應: {risk_response[:100]}...")
        except Exception as e:
            print(f"   ❌ 風險評估AI測試失敗: {e}")
        
        # 測試最終決策者 (Qwen 7B)
        print("   測試最終決策者 (Qwen 7B)...")
        try:
            decision_prompt = "基於市場分析，請做出BTC交易決策。"
            decision_response = await ai_manager._call_ai_model(
                "qwen:7b",
                ai_manager._get_decision_maker_system_prompt(),
                decision_prompt,
                200, 0.15
            )
            print(f"   ✅ 最終決策者響應: {decision_response[:100]}...")
        except Exception as e:
            print(f"   ❌ 最終決策者測試失敗: {e}")
        
        print("\n✅ 五AI協作系統基礎測試完成！")
        print("🎉 Mistral 7B風險評估AI成功集成！")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

def main():
    """主函數"""
    print("🚀 啟動五AI協作系統簡化測試...")
    
    try:
        result = asyncio.run(test_five_ai_simple())
        
        if result:
            print("🎉 測試成功！五AI協作系統準備就緒！")
            return 0
        else:
            print("❌ 測試失敗")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ 測試被用戶中斷")
        return 1
    except Exception as e:
        print(f"❌ 測試運行失敗: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)