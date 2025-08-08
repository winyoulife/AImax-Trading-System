#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎯 真實交易系統後端服務器
提供MAX API數據給前端儀表板
"""

from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import sys

# 添加src目錄到路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from trading.real_max_client import RealMaxClient

app = Flask(__name__)
CORS(app)

# 初始化MAX客戶端
max_client = RealMaxClient()

@app.route('/')
def index():
    """主頁面"""
    return send_from_directory('static', 'real-trading-dashboard.html')

@app.route('/api/max/ticker')
def get_ticker():
    """獲取BTC實時價格"""
    try:
        result = max_client.get_ticker('btctwd')
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/max/recent-trades')
def get_recent_trades():
    """獲取最近交易記錄"""
    try:
        result = max_client.get_recent_trades('btctwd', limit=10)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/max/orderbook')
def get_orderbook():
    """獲取訂單簿"""
    try:
        result = max_client.get_orderbook('btctwd', limit=5)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/max/account')
def get_account():
    """獲取帳戶信息 (需要API Key)"""
    try:
        result = max_client.get_account_info()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/max/my-trades')
def get_my_trades():
    """獲取我的交易記錄 (需要API Key)"""
    try:
        result = max_client.get_my_trades('btctwd', limit=50)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status')
def get_status():
    """獲取系統狀態"""
    try:
        # 測試MAX API連接
        ticker_result = max_client.get_ticker('btctwd')
        
        return jsonify({
            'success': True,
            'data': {
                'server_status': 'running',
                'max_api_status': 'connected' if ticker_result['success'] else 'disconnected',
                'last_update': ticker_result['data']['timestamp'] if ticker_result['success'] else None,
                'features': {
                    'real_time_price': True,
                    'market_data': True,
                    'account_info': bool(max_client.api_key),
                    'trading': bool(max_client.api_key and max_client.secret_key)
                }
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🎯 啟動 AImax 真實交易系統")
    print("=" * 50)
    print("📡 連接台灣MAX交易所...")
    
    # 測試API連接
    test_result = max_client.get_ticker('btctwd')
    if test_result['success']:
        price = test_result['data']['last_price']
        print(f"✅ MAX API連接成功")
        print(f"📊 當前BTC價格: NT$ {price:,.0f}")
    else:
        print(f"❌ MAX API連接失敗: {test_result['error']}")
    
    print("\n🌐 服務器信息:")
    print("   • 本地地址: http://localhost:5000")
    print("   • 儀表板: http://localhost:5000")
    print("   • API狀態: http://localhost:5000/api/status")
    print("\n🔑 注意:")
    print("   • 當前使用公開API (不需要API Key)")
    print("   • 要查看帳戶和交易記錄需要設置API Key")
    print("   • 準備好後可以開始真實交易測試")
    
    print("\n🚀 啟動服務器...")
    app.run(debug=True, host='0.0.0.0', port=5000)