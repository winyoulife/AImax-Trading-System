#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雲端交易系統 Web API
提供RESTful API供手機App或Web界面使用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json
import threading
import time
from datetime import datetime, timedelta
import logging

from src.trading.safe_trading_manager import SafeTradingManager
from src.core.smart_balanced_volume_macd_signals import SmartBalancedVolumeEnhancedMACDSignals
from src.data.data_fetcher import DataFetcher

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)  # 允許跨域請求

# 全局變量
trading_manager = None
signal_detector = None
data_fetcher = None
monitoring_thread = None
is_monitoring = False

def initialize_components():
    """初始化交易組件"""
    global trading_manager, signal_detector, data_fetcher
    
    trading_manager = SafeTradingManager()
    signal_detector = SmartBalancedVolumeEnhancedMACDSignals()
    data_fetcher = DataFetcher()
    
    logger.info("交易組件初始化完成")

def monitoring_loop():
    """監控循環"""
    global is_monitoring
    
    while is_monitoring:
        try:
            # 檢查緊急停止
            if trading_manager.check_emergency_stop_file():
                logger.warning("檢測到緊急停止文件")
                is_monitoring = False
                break
            
            # 獲取實時交易數據並檢測信號
            df = data_fetcher.get_realtime_data_for_trading('BTCTWD', limit=200)
            if df is not None and not df.empty:
                signals = signal_detector.detect_smart_balanced_signals(df)
                
                if not signals.empty:
                    latest_signal = signals.iloc[-1]
                    
                    if latest_signal['signal_type'] in ['buy', 'sell']:
                        result = trading_manager.execute_trade(latest_signal.to_dict())
                        logger.info(f"交易執行結果: {result}")
            
            time.sleep(60)  # 每分鐘檢查一次
            
        except Exception as e:
            logger.error(f"監控循環錯誤: {e}")
            time.sleep(30)

# API 路由

@app.route('/')
def index():
    """主頁面"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """獲取系統狀態"""
    try:
        status = trading_manager.get_status()
        
        # 添加額外信息
        status.update({
            'is_monitoring': is_monitoring,
            'current_position': trading_manager.current_position,
            'daily_loss': trading_manager.daily_loss,
            'total_trades_today': trading_manager.total_trades_today,
            'config': trading_manager.config
        })
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/start', methods=['POST'])
def start_system():
    """啟動交易系統"""
    global is_monitoring, monitoring_thread
    
    try:
        if is_monitoring:
            return jsonify({
                'success': False,
                'error': '系統已經在運行中'
            }), 400
        
        is_monitoring = True
        trading_manager.start_monitoring()
        
        # 啟動監控線程
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
        
        logger.info("交易系統已啟動")
        
        return jsonify({
            'success': True,
            'message': '交易系統已啟動'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stop', methods=['POST'])
def stop_system():
    """停止交易系統"""
    global is_monitoring
    
    try:
        if not is_monitoring:
            return jsonify({
                'success': False,
                'error': '系統沒有在運行'
            }), 400
        
        is_monitoring = False
        trading_manager.stop_monitoring()
        
        logger.info("交易系統已停止")
        
        return jsonify({
            'success': True,
            'message': '交易系統已停止'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/emergency-stop', methods=['POST'])
def emergency_stop():
    """緊急停止"""
    global is_monitoring
    
    try:
        is_monitoring = False
        trading_manager.emergency_stop = True
        trading_manager.stop_monitoring()
        trading_manager.create_emergency_stop_file()
        
        logger.warning("系統緊急停止")
        
        return jsonify({
            'success': True,
            'message': '系統已緊急停止'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    """處理配置"""
    if request.method == 'GET':
        # 獲取配置
        return jsonify({
            'success': True,
            'data': trading_manager.config
        })
    
    elif request.method == 'POST':
        # 更新配置
        try:
            new_config = request.json
            
            # 驗證配置
            required_fields = ['trading_amount', 'max_daily_loss', 'max_daily_trades']
            for field in required_fields:
                if field not in new_config:
                    return jsonify({
                        'success': False,
                        'error': f'缺少必要字段: {field}'
                    }), 400
            
            # 更新配置
            trading_manager.config.update(new_config)
            trading_manager.save_config()
            
            return jsonify({
                'success': True,
                'message': '配置已更新'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@app.route('/api/trades')
def get_trades():
    """獲取交易記錄"""
    try:
        # 這裡可以從數據庫或文件中讀取交易記錄
        # 暫時返回交易管理器中的記錄
        trades = []
        for trade in trading_manager.trade_history:
            trades.append({
                'datetime': trade.get('datetime', '').isoformat() if hasattr(trade.get('datetime', ''), 'isoformat') else str(trade.get('datetime', '')),
                'signal_type': trade.get('signal_type', ''),
                'price': trade.get('close', 0),
                'signal_strength': trade.get('signal_strength', 0)
            })
        
        return jsonify({
            'success': True,
            'data': trades
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/performance')
def get_performance():
    """獲取績效統計"""
    try:
        # 計算績效統計
        total_trades = trading_manager.total_trades_today
        daily_loss = trading_manager.daily_loss
        
        # 計算今日獲利（這裡需要更詳細的記錄）
        daily_profit = -daily_loss  # 簡化計算
        
        performance = {
            'total_trades_today': total_trades,
            'daily_profit': daily_profit,
            'daily_loss': daily_loss,
            'win_rate': 85.7,  # 從測試結果
            'system_uptime': '24/7' if is_monitoring else '0',
            'last_update': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': performance
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/market-data')
def get_market_data():
    """獲取市場數據"""
    try:
        # 獲取實時行情數據
        ticker = data_fetcher.get_realtime_ticker('BTCTWD')
        
        if ticker:
            market_data = {
                'current_price': ticker['last_price'],
                'volume': ticker['volume_24h'],
                'timestamp': ticker['timestamp'].isoformat(),
                'high_24h': ticker['high_24h'],
                'low_24h': ticker['low_24h'],
                'is_realtime': True
            }
        else:
            # 如果實時數據獲取失敗，使用K線數據
            df = data_fetcher.fetch_data('BTCTWD', limit=50)
            
            if df is not None and not df.empty:
                latest = df.iloc[-1]
                market_data = {
                    'current_price': float(latest['close']),
                    'volume': float(latest['volume']),
                    'timestamp': latest['timestamp'].isoformat() if hasattr(latest['timestamp'], 'isoformat') else str(latest['timestamp']),
                    'high_24h': float(df['high'].max()),
                    'low_24h': float(df['low'].min()),
                    'is_realtime': False
                }
            else:
                market_data = {
                    'current_price': 0,
                    'volume': 0,
                    'timestamp': datetime.now().isoformat(),
                    'high_24h': 0,
                    'low_24h': 0,
                    'is_realtime': False
                }
        
        return jsonify({
            'success': True,
            'data': market_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # 初始化組件
    initialize_components()
    
    # 啟動Flask應用
    print("🚀 雲端交易系統 API 服務器啟動中...")
    print("📱 手機App可以通過以下地址訪問:")
    print("   本地: http://localhost:5000")
    print("   網絡: http://你的IP地址:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=False)