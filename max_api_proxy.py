#!/usr/bin/env python3
"""
MAX API 代理服務器
解決前端 CORS 跨域問題
"""

import requests
import json
from flask import Flask, jsonify, render_template_string
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_API_URL = 'https://max-api.maicoin.com/api/v2/tickers/btctwd'

@app.route('/api/btc-price')
def get_btc_price():
    """獲取 BTC/TWD 價格的代理端點"""
    try:
        logger.info("正在從 MAX API 獲取 BTC/TWD 價格...")
        
        # 請求 MAX API
        response = requests.get(MAX_API_URL, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"MAX API 響應: {data}")
        
        # 驗證數據格式
        if not data.get('ticker') or not data['ticker'].get('last'):
            raise ValueError("MAX API 返回無效的價格數據")
        
        price = float(data['ticker']['last'])
        
        # 返回格式化的響應
        result = {
            'success': True,
            'price': price,
            'formatted_price': f"NT${price:,.0f}",
            'timestamp': data.get('at'),
            'source': 'MAX API',
            'raw_data': data
        }
        
        logger.info(f"成功獲取價格: NT${price:,.0f}")
        return jsonify(result)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"MAX API 請求失敗: {e}")
        return jsonify({
            'success': False,
            'error': f'MAX API 連線失敗: {str(e)}',
            'timestamp': None
        }), 500
        
    except ValueError as e:
        logger.error(f"數據格式錯誤: {e}")
        return jsonify({
            'success': False,
            'error': f'數據格式錯誤: {str(e)}',
            'timestamp': None
        }), 500
        
    except Exception as e:
        logger.error(f"未知錯誤: {e}")
        return jsonify({
            'success': False,
            'error': f'服務器錯誤: {str(e)}',
            'timestamp': None
        }), 500

@app.route('/test')
def test_api():
    """測試端點"""
    return jsonify({
        'message': 'MAX API 代理服務器運行正常',
        'endpoints': {
            'btc_price': '/api/btc-price'
        }
    })

@app.route('/')
def index():
    """簡單的測試頁面"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>MAX API 代理測試</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>MAX API 代理服務器</h1>
        <p>服務器運行正常</p>
        <button onclick="testAPI()">測試 BTC 價格 API</button>
        <div id="result"></div>
        
        <script>
        async function testAPI() {
            try {
                const response = await fetch('/api/btc-price');
                const data = await response.json();
                document.getElementById('result').innerHTML = 
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            } catch (error) {
                document.getElementById('result').innerHTML = 
                    '<p style="color: red;">錯誤: ' + error.message + '</p>';
            }
        }
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

if __name__ == '__main__':
    print("🚀 啟動 MAX API 代理服務器...")
    print("📡 代理端點: http://localhost:5000/api/btc-price")
    print("🧪 測試頁面: http://localhost:5000/")
    app.run(host='0.0.0.0', port=5000, debug=True)