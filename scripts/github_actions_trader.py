#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions 專用交易腳本
執行85%勝率終極優化策略的模擬交易
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
import logging

# 添加項目路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.clean_ultimate_signals import UltimateOptimizedVolumeEnhancedMACDSignals
from src.trading.simulation_manager import SimulationTradingManager
from src.data.simple_data_fetcher import DataFetcher

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubActionsTrader:
    """GitHub Actions 交易執行器"""
    
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.strategy = UltimateOptimizedVolumeEnhancedMACDSignals()
        self.simulation_manager = SimulationTradingManager()
        
    def run_trading_cycle(self):
        """執行一個完整的交易週期"""
        try:
            logger.info("🚀 開始執行AImax智能交易週期")
            logger.info("🎯 策略: 終極優化MACD (目標勝率85%+)")
            logger.info("🔄 模式: 雲端模擬交易")
            
            # 1. 獲取市場數據
            logger.info("📊 獲取BTC市場數據...")
            current_price = self.data_fetcher.get_current_price('BTCUSDT')
            logger.info(f"💰 BTC當前價格: ${current_price:,.2f}")
            
            # 獲取歷史數據用於技術分析
            df = self.data_fetcher.get_historical_data('BTCUSDT', '1h', 100)
            logger.info(f"📈 獲取歷史數據: {len(df)} 條記錄")
            
            # 2. 執行技術分析
            logger.info("🔍 執行終極優化技術分析...")
            signals = self.strategy.detect_signals(df)
            logger.info(f"🎯 檢測到 {len(signals)} 個交易信號")
            
            # 3. 處理交易信號
            executed_trades = 0
            for signal in signals[-3:]:  # 處理最近3個信號
                if signal['action'] in ['buy', 'sell']:
                    logger.info(f"📈 發現{signal['action'].upper()}信號:")
                    logger.info(f"   價格: ${signal['price']:.2f}")
                    logger.info(f"   信號強度: {signal['confidence']:.2%}")
                    logger.info(f"   預期勝率: 85%+")
                    
                    # 執行模擬交易
                    result = self.simulation_manager.execute_simulation_trade(signal)
                    
                    if result['success']:
                        executed_trades += 1
                        trade = result['trade']
                        logger.info(f"✅ 模擬交易執行成功:")
                        logger.info(f"   動作: {trade['action'].upper()}")
                        logger.info(f"   數量: {trade['quantity']:.6f}")
                        logger.info(f"   金額: ${trade['amount']:.2f}")
                        logger.info(f"   餘額: ${trade['balance_after']:.2f}")
                    else:
                        logger.warning(f"⚠️ 模擬交易跳過: {result['reason']}")
            
            # 4. 生成交易報告
            logger.info("📊 生成交易性能報告...")
            report = self.simulation_manager.get_performance_report()
            print(report)
            
            # 5. 保存執行狀態
            self.save_execution_status(executed_trades, current_price)
            
            logger.info(f"✅ 交易週期完成，執行了 {executed_trades} 筆模擬交易")
            return True
            
        except Exception as e:
            logger.error(f"❌ 交易週期執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def save_execution_status(self, executed_trades: int, current_price: float):
        """保存執行狀態"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'system_status': 'running',
                'trading_mode': 'simulation',
                'strategy': 'ultimate_optimized_85%_winrate',
                'current_btc_price': current_price,
                'executed_trades_this_cycle': executed_trades,
                'last_execution': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                'github_actions': True,
                'next_execution': '5 minutes'
            }
            
            # 確保目錄存在
            os.makedirs('data/simulation', exist_ok=True)
            
            # 保存狀態
            with open('data/simulation/execution_status.json', 'w') as f:
                json.dump(status, f, indent=2)
                
            logger.info("✅ 執行狀態已保存")
            
        except Exception as e:
            logger.error(f"❌ 保存執行狀態失敗: {e}")

def main():
    """主函數"""
    print("=" * 60)
    print("🤖 AImax 智能交易系統 - GitHub Actions")
    print("=" * 60)
    print(f"⏰ 執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("🎯 策略: 終極優化MACD (85%勝率)")
    print("🔄 模式: 雲端模擬交易")
    print("=" * 60)
    
    try:
        trader = GitHubActionsTrader()
        success = trader.run_trading_cycle()
        
        if success:
            print("\n✅ 交易系統執行成功")
            print("🔄 下次執行: 5分鐘後")
            return 0
        else:
            print("\n❌ 交易系統執行失敗")
            return 1
            
    except Exception as e:
        print(f"\n💥 系統異常: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())