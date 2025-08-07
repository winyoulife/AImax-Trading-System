#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
詳細獲利分析：深入比較兩種交易策略
"""

import os
import sys
import json
from datetime import datetime

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def detailed_profit_analysis():
    """詳細獲利分析"""
    print("🔍 詳細獲利分析報告")
    print("=" * 70)
    
    # 分析結果摘要
    print("📊 核心發現:")
    print("-" * 50)
    print("🚨 重要發現：允許重複買入策略在特定情況下確實可能獲利更高！")
    print()
    
    # 數據對比
    print("📈 數據對比:")
    print(f"{'策略類型':<20} {'理論獲利':<15} {'獲利率':<10} {'風險等級':<10}")
    print("-" * 60)
    print(f"{'允許重複買入':<20} {'897 TWD':<15} {'44.87%':<10} {'高':<10}")
    print(f"{'一買一賣':<20} {'1,011 TWD':<15} {'1.02%':<10} {'低':<10}")
    print()
    
    # 深入分析
    print("🤔 深入分析:")
    print("=" * 70)
    
    print("1️⃣ 為什麼重複買入策略獲利更高？")
    print("   • 第二次買入價格 $50,000 遠低於第一次 $94,840")
    print("   • 平均成本降至 $65,479，形成成本攤平效果")
    print("   • 當前價格 $95,000 > 平均成本，產生可觀獲利")
    print("   • 持有更多BTC (0.030544 vs 0.010544)")
    print()
    
    print("2️⃣ 但這種獲利有什麼問題？")
    print("   🚨 這是「未實現獲利」，存在重大風險：")
    print("   • 如果BTC跌破 $65,479，立即轉為虧損")
    print("   • 資金全部鎖定在BTC，無法靈活調配")
    print("   • 第二次買入可能是錯誤信號（價格 $50,000 異常）")
    print("   • 無法確定何時賣出，可能錯過最佳時機")
    print()
    
    print("3️⃣ 一買一賣策略的優勢？")
    print("   ✅ 這是「已實現獲利」，風險已控制：")
    print("   • 1,011 TWD 已經到手，不受市場波動影響")
    print("   • 資金可以立即投入下一個機會")
    print("   • 符合專業交易的風險管理原則")
    print("   • 可以持續複利增長")
    print()
    
    # 情境分析
    print("📊 不同市場情境分析:")
    print("=" * 70)
    
    scenarios = [
        {"name": "牛市情境", "btc_price": 120000, "description": "BTC大幅上漲"},
        {"name": "震盪情境", "btc_price": 95000, "description": "BTC維持當前價格"},
        {"name": "熊市情境", "btc_price": 60000, "description": "BTC大幅下跌"},
        {"name": "崩盤情境", "btc_price": 40000, "description": "BTC嚴重下跌"}
    ]
    
    print(f"{'情境':<12} {'BTC價格':<10} {'重複買入獲利':<15} {'一買一賣獲利':<15} {'優勢策略':<10}")
    print("-" * 70)
    
    for scenario in scenarios:
        price = scenario["btc_price"]
        
        # 重複買入策略獲利
        total_btc = 0.030544
        total_cost = 2000 + 30  # 包含手續費
        sell_value = total_btc * price
        fee = sell_value * 0.0015
        net_proceeds = sell_value - fee
        repeat_profit = net_proceeds - total_cost
        
        # 一買一賣策略（已實現獲利 + 可能的新交易）
        realized_profit = 1011  # 已實現
        # 假設可以進行更多交易週期
        additional_cycles = 2  # 假設可以完成2個額外週期
        estimated_profit = realized_profit + (realized_profit * additional_cycles * 0.8)  # 80%成功率
        
        better_strategy = "重複買入" if repeat_profit > estimated_profit else "一買一賣"
        
        print(f"{scenario['name']:<12} ${price:<9,} {repeat_profit:<14,.0f} {estimated_profit:<14,.0f} {better_strategy:<10}")
    
    print()
    
    # 風險分析
    print("⚠️ 風險分析:")
    print("=" * 70)
    
    print("🔴 重複買入策略風險:")
    print("• 集中度風險：100%資金集中在BTC")
    print("• 時機風險：無法確定最佳賣出時機")
    print("• 流動性風險：資金完全鎖定")
    print("• 心理風險：容易因貪婪錯過賣點")
    print("• 機會成本：錯過其他投資機會")
    print()
    
    print("🟢 一買一賣策略風險:")
    print("• 機會成本：可能錯過大幅上漲")
    print("• 頻繁交易：手續費成本較高")
    print("• 時機要求：需要精準的進出場判斷")
    print()
    
    # 最終建議
    print("💡 最終建議:")
    print("=" * 70)
    
    print("基於83.3%勝率策略的特性，我的建議是：")
    print()
    print("🎯 堅持「一買一賣」策略，理由如下：")
    print()
    print("1. 🛡️ 風險管理優先")
    print("   • 已實現獲利 > 未實現獲利")
    print("   • 風險可控，不會因市場波動全盤皆輸")
    print()
    print("2. 📈 複利效應")
    print("   • 1.02% × 多次交易 > 44.87% × 一次交易")
    print("   • 假設每月2次交易，年化收益可達 24%+")
    print()
    print("3. 🎲 概率優勢")
    print("   • 83.3%勝率 × 頻繁交易 = 穩定獲利")
    print("   • 重複買入依賴單次大獲利，風險過高")
    print()
    print("4. 💼 專業標準")
    print("   • 符合量化交易的風險管理原則")
    print("   • 可持續、可複製的交易模式")
    print()
    
    print("🚀 優化建議:")
    print("• 提高交易頻率，增加獲利機會")
    print("• 設定動態獲利目標（2-5%）")
    print("• 嚴格執行止損策略")
    print("• 持續監控市場，抓住最佳時機")
    print()
    
    print("📊 結論：")
    print("雖然重複買入在特定情況下獲利更高，但「一買一賣」策略")
    print("在風險控制、資金效率、可持續性方面都更優秀，")
    print("更適合你的83.3%勝率量化交易系統！")
    
    print("\n" + "=" * 70)
    print("🔍 詳細獲利分析完成")

if __name__ == "__main__":
    detailed_profit_analysis()