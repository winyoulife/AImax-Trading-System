#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAX交易所配置
根據MAX官方手續費標準設定
"""

# MAX交易所手續費結構 (2025年最新)
MAX_EXCHANGE_CONFIG = {
    # 現貨交易手續費
    'spot_trading_fees': {
        'maker_fee': 0.0005,  # 0.05% (掛單手續費)
        'taker_fee': 0.0015,  # 0.15% (吃單手續費)
        'default_fee': 0.0015  # 預設使用taker費率 (較保守)
    },
    
    # 提領手續費
    'withdrawal_fees': {
        'BTC': 0.0005,  # 0.0005 BTC
        'ETH': 0.01,    # 0.01 ETH
        'USDT': 15.0,   # 15 USDT
        'TWD': 15.0     # 15 TWD
    },
    
    # 最小交易量
    'minimum_order_size': {
        'BTCTWD': 100.0,    # 100 TWD
        'BTCUSDT': 10.0,    # 10 USDT
        'ETHTWD': 100.0,    # 100 TWD
        'ETHUSDT': 10.0     # 10 USDT
    },
    
    # 價格精度
    'price_precision': {
        'BTCTWD': 0,     # 整數
        'BTCUSDT': 2,    # 小數點後2位
        'ETHTWD': 0,     # 整數
        'ETHUSDT': 2     # 小數點後2位
    },
    
    # 數量精度
    'quantity_precision': {
        'BTCTWD': 6,     # 小數點後6位
        'BTCUSDT': 6,    # 小數點後6位
        'ETHTWD': 6,     # 小數點後6位
        'ETHUSDT': 6     # 小數點後6位
    },
    
    # API限制
    'api_limits': {
        'requests_per_second': 10,
        'requests_per_minute': 600,
        'max_orders_per_second': 5
    },
    
    # 模擬交易設定
    'simulation_config': {
        'initial_balance_twd': 100000.0,  # 10萬台幣
        'max_position_size': 0.1,         # 最大10%資金單筆交易
        'slippage_rate': 0.0005,          # 0.05%滑點
        'use_taker_fee': True             # 使用taker手續費率
    }
}

def get_trading_fee(order_type='taker'):
    """獲取交易手續費率"""
    if order_type == 'maker':
        return MAX_EXCHANGE_CONFIG['spot_trading_fees']['maker_fee']
    else:
        return MAX_EXCHANGE_CONFIG['spot_trading_fees']['taker_fee']

def get_minimum_order_size(symbol='BTCTWD'):
    """獲取最小交易量"""
    return MAX_EXCHANGE_CONFIG['minimum_order_size'].get(symbol, 100.0)

def calculate_trading_cost(amount, symbol='BTCTWD', order_type='taker'):
    """計算交易成本 (含手續費)"""
    fee_rate = get_trading_fee(order_type)
    fee_amount = amount * fee_rate
    total_cost = amount + fee_amount
    
    return {
        'amount': amount,
        'fee_rate': fee_rate,
        'fee_amount': fee_amount,
        'total_cost': total_cost
    }

# MAX交易所官方手續費說明
MAX_FEE_INFO = """
MAX交易所手續費結構 (2025年最新):

📊 現貨交易手續費:
- Maker (掛單): 0.05%
- Taker (吃單): 0.15%

💰 提領手續費:
- BTC: 0.0005 BTC
- ETH: 0.01 ETH  
- USDT: 15 USDT
- TWD: 15 TWD

📏 最小交易量:
- BTC/TWD: 100 TWD
- BTC/USDT: 10 USDT

⚠️ 注意事項:
1. 手續費會從交易金額中扣除
2. 模擬交易使用較保守的Taker費率 (0.15%)
3. 實際交易時可能因市場條件產生滑點
"""

if __name__ == "__main__":
    print("MAX交易所配置資訊:")
    print("=" * 50)
    print(MAX_FEE_INFO)
    
    # 測試計算
    test_amount = 10000  # 1萬台幣
    cost_info = calculate_trading_cost(test_amount)
    print(f"\n💰 交易成本計算範例 (1萬台幣):")
    print(f"交易金額: {cost_info['amount']:,.0f} TWD")
    print(f"手續費率: {cost_info['fee_rate']:.2%}")
    print(f"手續費: {cost_info['fee_amount']:,.0f} TWD")
    print(f"總成本: {cost_info['total_cost']:,.0f} TWD")