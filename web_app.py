#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 雲端交易系統 Web 控制面板
帶有安全身份驗證的私有交易控制界面
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import hashlib
import secrets
import json
import os
import sys
from datetime import datetime, timedelta
import threading
import time

# 添加項目路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.trading.safe_trading_manager import SafeTradingManager
from src.core.ultimate_optimized_volume_macd_signals import UltimateOptimizedVolumeEnhancedMACDSignals
from src.data.data_fetcher import DataFetcher

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)  # 隨機生成安全密鑰
CORS(app)

# 安全配置
ADMIN_USERNAME = "lovejk1314"
ADMIN_PASSWORD_HASH = "898535a8764bb8b3ccfebd1c2ac92163adafb69300370881a7beaa2dda7af4ae"  # "Ichen5978" 的 SHA256

class WebTradingController:
    """Web交易控制器"""
    
    def __init__(self):
        self.trading_manager = SafeTradingManager()
        self.signal_detector = UltimateOptimizedVolumeEnhancedMACDSignals()
        self.data_fetcher = DataFetcher()
        self.is_running = False
        self.last_update = datetime.now()
        
    def get_system_status(self):
        """獲取系統狀態"""
        try:
            status = self.trading_manager.get_status()
            current_price = self.data_fetcher.get_current_price("BTCUSDT")
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_running": self.is_running,
                "trading_active": status.get("is_running", False),
                "current_price": current_price,
                "daily_pnl": status.get("daily_pnl", 0),
                "total_trades": status.get("total_trades_today", 0),
                "emergency_stop": status.get("emergency_stop", False),
                "last_signal": status.get("last_signal", "無"),
                "position": status.get("current_position", "無持倉")
            }
        except Exception as e:
            return {"error": str(e)}
    
    def start_trading(self):
        """啟動交易"""
        try:
            self.trading_manager.start_trading()
            self.is_running = True
            return {"success": True, "message": "交易系統已啟動"}
        except Exception as e:
            return {"success": False, "message": f"啟動失敗: {str(e)}"}
    
    def stop_trading(self):
        """停止交易"""
        try:
            self.trading_manager.stop_trading()
            self.is_running = False
            return {"success": True, "message": "交易系統已停止"}
        except Exception as e:
            return {"success": False, "message": f"停止失敗: {str(e)}"}
    
    def emergency_stop(self):
        """緊急停止"""
        try:
            self.trading_manager.emergency_stop_trading()
            self.is_running = False
            return {"success": True, "message": "緊急停止已執行"}
        except Exception as e:
            return {"success": False, "message": f"緊急停止失敗: {str(e)}"}

# 初始化控制器
controller = WebTradingController()

def hash_password(password):
    """密碼哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_auth():
    """檢查身份驗證"""
    return session.get('authenticated', False)

@app.route('/')
def index():
    """主頁"""
    if not check_auth():
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登入頁面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and hash_password(password) == ADMIN_PASSWORD_HASH:
            session['authenticated'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='帳號或密碼錯誤')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """登出"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/status')
def api_status():
    """API: 獲取系統狀態"""
    if not check_auth():
        return jsonify({"error": "未授權"}), 401
    
    return jsonify(controller.get_system_status())

@app.route('/api/start', methods=['POST'])
def api_start():
    """API: 啟動交易"""
    if not check_auth():
        return jsonify({"error": "未授權"}), 401
    
    return jsonify(controller.start_trading())

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """API: 停止交易"""
    if not check_auth():
        return jsonify({"error": "未授權"}), 401
    
    return jsonify(controller.stop_trading())

@app.route('/api/emergency', methods=['POST'])
def api_emergency():
    """API: 緊急停止"""
    if not check_auth():
        return jsonify({"error": "未授權"}), 401
    
    return jsonify(controller.emergency_stop())

if __name__ == '__main__':
    # 創建模板目錄
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("🚀 AImax 雲端交易系統啟動中...")
    print(f"📱 Web控制面板: http://localhost:5000")
    print(f"🔐 專屬帳號: {ADMIN_USERNAME}")
    print("🔑 專屬密碼: Ichen5978")
    print("✅ 已設置專屬密碼！")
    
    app.run(host='0.0.0.0', port=5000, debug=False)