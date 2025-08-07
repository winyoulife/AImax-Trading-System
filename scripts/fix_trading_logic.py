#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正交易邏輯 - 清理錯誤的重複買入記錄
確保嚴格執行一買一賣的配對邏輯
"""

import os
import json
import sys
from datetime import datetime

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_trading_data():
    """修正交易數據"""
    print("🔧 開始修正交易邏輯...")
    print("=" * 50)
    
    # 1. 檢查當前交易記錄
    trades_file = "data/simulation/trades.jsonl"
    trades = []
    
    if os.path.exists(trades_file):
        print(f"📋 讀取交易記錄: {trades_file}")
        with open(trades_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    trades.append(json.loads(line.strip()))
        
        print(f"📊 發現 {len(trades)} 筆交易記錄")
        for i, trade in enumerate(trades, 1):
            print(f"  {i}. {trade.get('timestamp', '')[:16]} - {trade.get('action', '')} - {trade.get('quantity', 0):.6f} - {trade.get('amount', 0):.0f} TWD")
    
    # 2. 分析問題
    buy_trades = [t for t in trades if t.get('action') == 'buy']
    sell_trades = [t for t in trades if t.get('action') == 'sell']
    
    print(f"\n📈 買入交易: {len(buy_trades)} 筆")
    print(f"📉 賣出交易: {len(sell_trades)} 筆")
    
    if len(buy_trades) > 1 and len(sell_trades) == 0:
        print("\n🚨 發現問題: 有多筆買入但無賣出，違反一買一賣邏輯")
        
        # 3. 修正策略：保留第一筆買入，移除其他
        print("\n🔧 修正策略: 保留第一筆買入，移除重複買入")
        
        corrected_trades = [buy_trades[0]]  # 只保留第一筆買入
        
        print(f"✅ 修正後交易記錄: {len(corrected_trades)} 筆")
        for i, trade in enumerate(corrected_trades, 1):
            print(f"  {i}. {trade.get('timestamp', '')[:16]} - {trade.get('action', '')} - {trade.get('quantity', 0):.6f} - {trade.get('amount', 0):.0f} TWD")
        
        # 4. 備份原始數據
        backup_file = f"data/simulation/trades_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        print(f"\n💾 備份原始數據到: {backup_file}")
        
        os.makedirs(os.path.dirname(backup_file), exist_ok=True)
        with open(backup_file, 'w', encoding='utf-8') as f:
            for trade in trades:
                f.write(json.dumps(trade, ensure_ascii=False) + '\n')
        
        # 5. 寫入修正後的數據
        print(f"\n✍️ 寫入修正後的交易記錄")
        with open(trades_file, 'w', encoding='utf-8') as f:
            for trade in corrected_trades:
                f.write(json.dumps(trade, ensure_ascii=False) + '\n')
        
        # 6. 修正投資組合狀態
        portfolio_file = "data/simulation/portfolio_state.json"
        if os.path.exists(portfolio_file):
            print(f"\n📊 修正投資組合狀態: {portfolio_file}")
            
            with open(portfolio_file, 'r', encoding='utf-8') as f:
                portfolio = json.load(f)
            
            # 重新計算正確的狀態
            first_trade = corrected_trades[0]
            
            # 計算正確的成本 (包含手續費)
            trade_amount = first_trade.get('amount', 1000.0)
            fee_rate = 0.0015  # MAX手續費 0.15%
            fee_amount = trade_amount * fee_rate
            total_cost = trade_amount + fee_amount
            quantity = first_trade.get('quantity', 0)
            
            portfolio.update({
                'balance': 100000.0 - total_cost,  # 初始資金 - 買入成本
                'positions': {'BTCTWD': quantity},
                'total_trades': 1,
                'last_update': datetime.now().isoformat()
            })
            
            with open(portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(portfolio, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 投資組合狀態已修正:")
            print(f"  💰 餘額: {portfolio['balance']:,.0f} TWD")
            print(f"  💼 持倉: {portfolio['positions']['BTCTWD']:.6f} BTC")
        
        print("\n🎉 交易邏輯修正完成！")
        print("\n📋 修正摘要:")
        print(f"  • 移除了 {len(buy_trades) - 1} 筆重複買入記錄")
        print(f"  • 保留了 1 筆正確的買入記錄")
        print(f"  • 等待策略產生賣出信號以完成交易週期")
        print(f"  • 修正後將嚴格執行一買一賣邏輯")
        
    else:
        print("\n✅ 交易記錄邏輯正確，無需修正")
    
    print("\n" + "=" * 50)
    print("🔧 交易邏輯修正完成")

if __name__ == "__main__":
    fix_trading_data()