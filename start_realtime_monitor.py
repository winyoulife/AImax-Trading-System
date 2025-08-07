#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 實時監控Web服務器
提供實時監控面板的Web界面和API服務
"""

import sys
import os
import json
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS

# 添加項目路徑
sys.path.append(str(Path(__file__).parent))

from src.monitoring.realtime_monitor import realtime_monitor
from src.logging.structured_logger import structured_logger, LogCategory

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建Flask應用
app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
CORS(app)

# 配置
app.config['SECRET_KEY'] = 'aimax-realtime-monitor-2024'

@app.route('/')
def index():
    """主頁 - 重定向到監控面板"""
    return send_from_directory('static', 'realtime-monitor.html')

@app.route('/monitor')
def monitor_dashboard():
    """監控面板頁面"""
    return send_from_directory('static', 'realtime-monitor.html')

@app.route('/api/monitoring/status')
def get_monitoring_status():
    """獲取當前監控狀態"""
    try:
        status = realtime_monitor.get_current_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"獲取監控狀態失敗: {e}")
        return jsonify({
            'error': str(e),
            'health_score': 0,
            'system_status': 'error',
            'system_metrics': {
                'cpu_percent': 0,
                'memory_percent': 0,
                'uptime_hours': 0,
                'active_threads': 0
            },
            'trading_metrics': {
                'active_strategies': 0,
                'total_strategies': 0,
                'current_balance': 0,
                'daily_pnl': 0
            },
            'alerts': {
                'total_active': 0,
                'recent_alerts': []
            },
            'monitoring_active': False
        }), 500

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """啟動實時監控"""
    try:
        realtime_monitor.start_monitoring()
        structured_logger.info(LogCategory.SYSTEM, "通過Web API啟動實時監控")
        return jsonify({
            'success': True,
            'message': '實時監控已啟動'
        })
    except Exception as e:
        logger.error(f"啟動監控失敗: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """停止實時監控"""
    try:
        realtime_monitor.stop_monitoring()
        structured_logger.info(LogCategory.SYSTEM, "通過Web API停止實時監控")
        return jsonify({
            'success': True,
            'message': '實時監控已停止'
        })
    except Exception as e:
        logger.error(f"停止監控失敗: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/monitoring/history')
def get_monitoring_history():
    """獲取監控歷史數據"""
    try:
        hours = request.args.get('hours', 1, type=int)
        history = realtime_monitor.get_metrics_history(hours)
        return jsonify(history)
    except Exception as e:
        logger.error(f"獲取監控歷史失敗: {e}")
        return jsonify({
            'error': str(e),
            'system_metrics': [],
            'trading_metrics': [],
            'data_points': 0,
            'time_range_hours': hours
        }), 500

@app.route('/api/monitoring/acknowledge/<int:alert_index>', methods=['POST'])
def acknowledge_alert(alert_index):
    """確認警告"""
    try:
        success = realtime_monitor.acknowledge_alert(alert_index)
        if success:
            return jsonify({
                'success': True,
                'message': '警告已確認'
            })
        else:
            return jsonify({
                'success': False,
                'error': '無效的警告索引'
            }), 400
    except Exception as e:
        logger.error(f"確認警告失敗: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/monitoring/summary')
def get_monitoring_summary():
    """獲取監控摘要"""
    try:
        summary = realtime_monitor.get_system_summary()
        return jsonify({
            'summary': summary,
            'timestamp': realtime_monitor.get_current_status()['timestamp']
        })
    except Exception as e:
        logger.error(f"獲取監控摘要失敗: {e}")
        return jsonify({
            'error': str(e),
            'summary': '獲取摘要失敗',
            'timestamp': None
        }), 500

@app.route('/api/monitoring/config', methods=['GET', 'POST'])
def monitoring_config():
    """監控配置管理"""
    if request.method == 'GET':
        try:
            return jsonify({
                'config': realtime_monitor.config,
                'success': True
            })
        except Exception as e:
            logger.error(f"獲取監控配置失敗: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    elif request.method == 'POST':
        try:
            new_config = request.get_json()
            if new_config:
                # 更新配置（這裡可以添加配置驗證）
                realtime_monitor.config.update(new_config)
                structured_logger.info(LogCategory.SYSTEM, "監控配置已更新", config=new_config)
                return jsonify({
                    'success': True,
                    'message': '配置已更新',
                    'config': realtime_monitor.config
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '無效的配置數據'
                }), 400
        except Exception as e:
            logger.error(f"更新監控配置失敗: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@app.route('/health')
def health_check():
    """健康檢查端點"""
    try:
        status = realtime_monitor.get_current_status()
        return jsonify({
            'status': 'healthy',
            'monitoring_active': status['monitoring_active'],
            'health_score': status['health_score'],
            'timestamp': status['timestamp']
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404錯誤處理"""
    return jsonify({
        'error': '頁面未找到',
        'message': '請檢查URL是否正確'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500錯誤處理"""
    return jsonify({
        'error': '內部服務器錯誤',
        'message': '請稍後重試或聯繫管理員'
    }), 500

def main():
    """主函數"""
    print("🚀 啟動 AImax 實時監控Web服務器...")
    print("=" * 50)
    
    # 初始化監控器
    try:
        structured_logger.info(LogCategory.SYSTEM, "初始化實時監控Web服務器")
        
        # 顯示服務信息
        print(f"📊 監控面板: http://localhost:5000/monitor")
        print(f"🔍 API狀態: http://localhost:5000/api/monitoring/status")
        print(f"💊 健康檢查: http://localhost:5000/health")
        print(f"📋 監控摘要: http://localhost:5000/api/monitoring/summary")
        print("=" * 50)
        
        # 啟動Flask應用
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # 生產環境設為False
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n⏹️ 用戶中斷，正在關閉服務器...")
        realtime_monitor.stop_monitoring()
        structured_logger.info(LogCategory.SYSTEM, "實時監控Web服務器已關閉")
    except Exception as e:
        print(f"❌ 啟動服務器失敗: {e}")
        structured_logger.error(LogCategory.SYSTEM, f"啟動Web服務器失敗: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())