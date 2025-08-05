#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 簡化網頁監控面板
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import hashlib
import secrets
import json
import os
from datetime import datetime
import sys

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# 安全配置
ADMIN_USERNAME = "lovejk1314"
ADMIN_PASSWORD_HASH = "898535a8764bb8b3ccfebd1c2ac92163adafb69300370881a7beaa2dda7af4ae"  # "Ichen5978"

def hash_password(password):
    """密碼哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_auth():
    """檢查身份驗證"""
    return session.get('authenticated', False)

def get_system_status():
    """獲取系統狀態"""
    try:
        # 讀取執行狀態文件
        status_file = "data/simulation/execution_status.json"
        if os.path.exists(status_file):
            with open(status_file, 'r') as f:
                status = json.load(f)
            return status
        else:
            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": "unknown",
                "current_btc_price": 0,
                "last_execution": "未知"
            }
    except Exception as e:
        return {"error": str(e)}

def get_recent_trades():
    """獲取最近交易"""
    try:
        trades_file = "data/simulation/trades.jsonl"
        if os.path.exists(trades_file):
            with open(trades_file, 'r') as f:
                lines = f.readlines()
            
            trades = []
            for line in lines[-10:]:  # 最近10筆
                trade = json.loads(line.strip())
                trades.append(trade)
            
            return trades
        else:
            return []
    except Exception as e:
        return []

@app.route('/')
def index():
    """主頁"""
    if not check_auth():
        return redirect(url_for('login'))
    return render_template('simple_dashboard.html')

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
            return render_template('simple_login.html', error='帳號或密碼錯誤')
    
    return render_template('simple_login.html')

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
    
    status = get_system_status()
    trades = get_recent_trades()
    
    return jsonify({
        "status": status,
        "recent_trades": trades,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    # 創建模板目錄
    os.makedirs('templates', exist_ok=True)
    
    print("🚀 AImax 簡化網頁監控啟動中...")
    print(f"📱 網頁地址: http://localhost:5000")
    print(f"🔐 帳號: {ADMIN_USERNAME}")
    print("🔑 密碼: Ichen5978")
    
    app.run(host='0.0.0.0', port=5000, debug=False)