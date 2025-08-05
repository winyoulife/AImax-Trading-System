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
import time
# 移除 websockets 依賴，專注於 REST API

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MAX API 官方端點 (根據官方文檔)
MAX_API_BASE = 'https://max-api.maicoin.com'
MAX_API_TICKER_URL = f'{MAX_API_BASE}/api/v2/tickers/btctwd'
MAX_API_PUBLIC_TRADES_URL = f'{MAX_API_BASE}/api/v2/trades'

# MAX WebSocket 端點
MAX_WEBSOCKET_URL = 'wss://max-stream.maicoin.com/ws'

# 請求標頭 (根據官方建議)
HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'AImax-Trading-System/3.0',
    'Content-Type': 'application/json'
}

# 全局變量存儲最新價格數據
latest_price_data = {
    'price': None,
    'timestamp': None,
    'source': 'none'
}

@app.route('/api/btc-price')
def get_btc_price():
    """獲取 BTC/TWD 價格的代理端點 (根據 MAX 官方 API 文檔)"""
    try:
        logger.info("正在從 MAX API 獲取 BTC/TWD 價格...")
        
        # 使用官方推薦的請求方式
        response = requests.get(
            MAX_API_TICKER_URL, 
            headers=HEADERS,
            timeout=15,
            verify=True  # 驗證 SSL 證書
        )
        
        # 檢查 HTTP 狀態碼
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f"HTTP {response.status_code}: {response.text}")
        
        # 解析 JSON 響應
        data = response.json()
        logger.info(f"MAX API 原始響應: {json.dumps(data, indent=2)}")
        
        # 根據實際 MAX API 響應格式驗證
        # 實際格式: {"at": timestamp, "last": "price", "buy": "price", "sell": "price", ...}
        if not isinstance(data, dict):
            raise ValueError("MAX API 響應不是有效的 JSON 對象")
        
        # 檢查必要字段
        if 'at' not in data:
            raise ValueError("MAX API 響應缺少時間戳字段 'at'")
            
        if 'last' not in data:
            raise ValueError("MAX API 響應缺少 'last' 價格字段")
        
        # 解析價格 (可能是字符串或數字)
        try:
            price = float(data['last'])
        except (ValueError, TypeError) as e:
            raise ValueError(f"無法解析價格 '{data['last']}': {e}")
        
        # 驗證價格合理性 (BTC/TWD 應該在合理範圍內)
        if price <= 0 or price > 10000000:  # 0 到 1000萬 TWD
            raise ValueError(f"價格 {price} 超出合理範圍")
        
        # 獲取其他有用信息
        buy_price = float(data.get('buy', 0)) if data.get('buy') else None
        sell_price = float(data.get('sell', 0)) if data.get('sell') else None
        volume = float(data.get('vol', 0)) if data.get('vol') else None
        open_price = float(data.get('open', 0)) if data.get('open') else None
        high_price = float(data.get('high', 0)) if data.get('high') else None
        low_price = float(data.get('low', 0)) if data.get('low') else None
        
        # 返回格式化的響應
        result = {
            'success': True,
            'price': price,
            'formatted_price': f"NT${price:,.0f}",
            'buy_price': buy_price,
            'sell_price': sell_price,
            'volume': volume,
            'open_price': open_price,
            'high_price': high_price,
            'low_price': low_price,
            'timestamp': data['at'],
            'source': 'MAX API v2',
            'api_url': MAX_API_TICKER_URL,
            'request_time': time.time(),
            'raw_data': data
        }
        
        # 更新全局價格數據
        latest_price_data.update({
            'price': price,
            'timestamp': data['at'],
            'source': 'REST API'
        })
        
        logger.info(f"✅ 成功獲取 BTC/TWD 價格: {result['formatted_price']}")
        logger.info(f"   買價: {buy_price}, 賣價: {sell_price}, 成交量: {volume}")
        
        return jsonify(result)
        
    except requests.exceptions.Timeout as e:
        error_msg = f"MAX API 請求超時: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': 'timeout',
            'timestamp': time.time()
        }), 504
        
    except requests.exceptions.ConnectionError as e:
        error_msg = f"無法連接到 MAX API: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': 'connection',
            'timestamp': time.time()
        }), 503
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"MAX API HTTP 錯誤: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': 'http',
            'timestamp': time.time()
        }), 502
        
    except ValueError as e:
        error_msg = f"MAX API 數據格式錯誤: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': 'data_format',
            'timestamp': time.time()
        }), 422
        
    except Exception as e:
        error_msg = f"未知錯誤: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': 'unknown',
            'timestamp': time.time()
        }), 500

@app.route('/api/test-connection')
def test_max_connection():
    """測試 MAX API 連接狀態"""
    try:
        # 測試基本連接
        response = requests.get(MAX_API_BASE, headers=HEADERS, timeout=10)
        base_status = response.status_code
        
        # 測試 ticker API
        ticker_response = requests.get(MAX_API_TICKER_URL, headers=HEADERS, timeout=10)
        ticker_status = ticker_response.status_code
        
        return jsonify({
            'success': True,
            'max_api_base': {
                'url': MAX_API_BASE,
                'status': base_status,
                'accessible': base_status == 200
            },
            'ticker_api': {
                'url': MAX_API_TICKER_URL,
                'status': ticker_status,
                'accessible': ticker_status == 200
            },
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/test')
def test_api():
    """測試端點"""
    return jsonify({
        'message': 'MAX API 代理服務器運行正常',
        'version': '3.0',
        'endpoints': {
            'btc_price': '/api/btc-price',
            'test_connection': '/api/test-connection'
        },
        'max_api_info': {
            'base_url': MAX_API_BASE,
            'ticker_url': MAX_API_TICKER_URL,
            'documentation': 'https://max.maicoin.com/documents/api'
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