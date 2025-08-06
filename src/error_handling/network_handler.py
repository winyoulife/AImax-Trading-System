#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 網路連接處理模塊 - 任務9實現
處理網路連接失敗、超時和重試邏輯
"""

import sys
import os
import time
import requests
import socket
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import threading
from urllib.parse import urlparse
import json

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.error_handling.error_handler import error_handler, with_retry, with_circuit_breaker

logger = logging.getLogger(__name__)

class NetworkConnectionHandler:
    """網路連接處理器"""
    
    def __init__(self):
        self.connection_pool = {}
        self.connection_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'last_check_time': datetime.now()
        }
        
        # 網路配置
        self.config = {
            'timeout': 30,
            'max_retries': 3,
            'backoff_factor': 1.0,
            'status_forcelist': [500, 502, 503, 504],
            'user_agent': 'AImax-Trading-System/1.0'
        }
        
        # 健康檢查端點
        self.health_check_urls = [
            'https://api.github.com',
            'https://httpbin.org/status/200',
            'https://www.google.com'
        ]
    
    @with_retry(max_retries=3, base_delay=2.0)
    @with_circuit_breaker('network_request', failure_threshold=5)
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> requests.Response:
        """發送HTTP請求，包含重試和熔斷機制"""
        start_time = time.time()
        
        try:
            # 設置默認參數
            kwargs.setdefault('timeout', self.config['timeout'])
            kwargs.setdefault('headers', {}).update({
                'User-Agent': self.config['user_agent']
            })
            
            logger.info(f"🌐 發送 {method} 請求到 {url}")
            
            # 發送請求
            response = requests.request(method, url, **kwargs)
            
            # 更新統計
            self._update_stats(True, time.time() - start_time)
            
            # 檢查響應狀態
            if response.status_code in self.config['status_forcelist']:
                raise requests.exceptions.HTTPError(f"HTTP {response.status_code}: {response.reason}")
            
            logger.info(f"✅ 請求成功: {response.status_code}")
            return response
            
        except requests.exceptions.Timeout as e:
            self._update_stats(False, time.time() - start_time)
            logger.error(f"⏰ 請求超時: {url}")
            raise NetworkTimeoutError(f"Request timeout for {url}") from e
            
        except requests.exceptions.ConnectionError as e:
            self._update_stats(False, time.time() - start_time)
            logger.error(f"🔌 連接錯誤: {url}")
            raise NetworkConnectionError(f"Connection error for {url}") from e
            
        except requests.exceptions.HTTPError as e:
            self._update_stats(False, time.time() - start_time)
            logger.error(f"❌ HTTP錯誤: {e}")
            raise NetworkHTTPError(str(e)) from e
            
        except Exception as e:
            self._update_stats(False, time.time() - start_time)
            logger.error(f"💥 未知網路錯誤: {e}")
            raise NetworkError(f"Unknown network error: {str(e)}") from e
    
    def _update_stats(self, success: bool, response_time: float):
        """更新連接統計"""
        self.connection_stats['total_requests'] += 1
        
        if success:
            self.connection_stats['successful_requests'] += 1
        else:
            self.connection_stats['failed_requests'] += 1
        
        # 更新平均響應時間
        total_successful = self.connection_stats['successful_requests']
        if total_successful > 0:
            current_avg = self.connection_stats['average_response_time']
            self.connection_stats['average_response_time'] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
    
    def check_internet_connectivity(self) -> Dict[str, Any]:
        """檢查網路連接狀態"""
        logger.info("🔍 檢查網路連接狀態...")
        
        connectivity_results = {
            'connected': False,
            'checked_urls': [],
            'successful_checks': 0,
            'failed_checks': 0,
            'average_latency': 0.0,
            'timestamp': datetime.now()
        }
        
        total_latency = 0.0
        
        for url in self.health_check_urls:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                latency = time.time() - start_time
                
                if response.status_code == 200:
                    connectivity_results['successful_checks'] += 1
                    total_latency += latency
                    
                    connectivity_results['checked_urls'].append({
                        'url': url,
                        'status': 'success',
                        'latency': latency,
                        'status_code': response.status_code
                    })
                else:
                    connectivity_results['failed_checks'] += 1
                    connectivity_results['checked_urls'].append({
                        'url': url,
                        'status': 'failed',
                        'status_code': response.status_code
                    })
                    
            except Exception as e:
                connectivity_results['failed_checks'] += 1
                connectivity_results['checked_urls'].append({
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
        
        # 計算結果
        total_checks = len(self.health_check_urls)
        connectivity_results['connected'] = connectivity_results['successful_checks'] > 0
        
        if connectivity_results['successful_checks'] > 0:
            connectivity_results['average_latency'] = total_latency / connectivity_results['successful_checks']
        
        # 記錄結果
        if connectivity_results['connected']:
            logger.info(f"✅ 網路連接正常 ({connectivity_results['successful_checks']}/{total_checks} 成功)")
        else:
            logger.error(f"❌ 網路連接失敗 (0/{total_checks} 成功)")
        
        return connectivity_results
    
    def test_specific_endpoint(self, url: str, expected_status: int = 200) -> Dict[str, Any]:
        """測試特定端點的連接"""
        logger.info(f"🎯 測試端點: {url}")
        
        test_result = {
            'url': url,
            'success': False,
            'status_code': None,
            'response_time': 0.0,
            'error': None,
            'timestamp': datetime.now()
        }
        
        try:
            start_time = time.time()
            response = self.make_request(url)
            test_result['response_time'] = time.time() - start_time
            test_result['status_code'] = response.status_code
            
            if response.status_code == expected_status:
                test_result['success'] = True
                logger.info(f"✅ 端點測試成功: {url} ({response.status_code})")
            else:
                test_result['error'] = f"Unexpected status code: {response.status_code}"
                logger.warning(f"⚠️ 端點狀態碼異常: {url} ({response.status_code})")
                
        except Exception as e:
            test_result['error'] = str(e)
            test_result['response_time'] = time.time() - start_time
            logger.error(f"❌ 端點測試失敗: {url} - {str(e)}")
        
        return test_result
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """獲取連接統計"""
        success_rate = 0.0
        if self.connection_stats['total_requests'] > 0:
            success_rate = (self.connection_stats['successful_requests'] / 
                          self.connection_stats['total_requests'] * 100)
        
        return {
            'total_requests': self.connection_stats['total_requests'],
            'successful_requests': self.connection_stats['successful_requests'],
            'failed_requests': self.connection_stats['failed_requests'],
            'success_rate': success_rate,
            'average_response_time': self.connection_stats['average_response_time'],
            'last_check_time': self.connection_stats['last_check_time']
        }
    
    def reset_stats(self):
        """重置連接統計"""
        self.connection_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'last_check_time': datetime.now()
        }
        logger.info("📊 連接統計已重置")
    
    def configure_proxy(self, proxy_config: Dict[str, str]):
        """配置代理設置"""
        self.config['proxies'] = proxy_config
        logger.info(f"🔧 代理配置已更新: {proxy_config}")
    
    def set_timeout(self, timeout: int):
        """設置請求超時時間"""
        self.config['timeout'] = timeout
        logger.info(f"⏰ 請求超時設置為: {timeout}秒")

class NetworkMonitor:
    """網路監控器"""
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.network_handler = NetworkConnectionHandler()
        self.monitoring = False
        self.monitor_thread = None
        self.network_history = []
        
    def start_monitoring(self):
        """開始網路監控"""
        if self.monitoring:
            logger.warning("⚠️ 網路監控已在運行")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"🔍 網路監控已啟動，檢查間隔: {self.check_interval}秒")
    
    def stop_monitoring(self):
        """停止網路監控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 網路監控已停止")
    
    def _monitor_loop(self):
        """監控循環"""
        while self.monitoring:
            try:
                connectivity = self.network_handler.check_internet_connectivity()
                self.network_history.append(connectivity)
                
                # 保持歷史記錄在合理範圍內
                if len(self.network_history) > 100:
                    self.network_history = self.network_history[-50:]
                
                # 如果網路斷開，記錄錯誤
                if not connectivity['connected']:
                    error_handler._record_error(
                        error_type="NetworkConnectivityError",
                        error_message="Internet connectivity lost",
                        function_name="network_monitor",
                        context=connectivity
                    )
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ 網路監控錯誤: {e}")
                time.sleep(self.check_interval)
    
    def get_network_health(self) -> Dict[str, Any]:
        """獲取網路健康狀態"""
        if not self.network_history:
            return {'status': 'unknown', 'message': 'No monitoring data available'}
        
        recent_checks = self.network_history[-10:]  # 最近10次檢查
        connected_count = sum(1 for check in recent_checks if check['connected'])
        
        health_percentage = (connected_count / len(recent_checks)) * 100
        
        if health_percentage >= 90:
            status = 'excellent'
        elif health_percentage >= 70:
            status = 'good'
        elif health_percentage >= 50:
            status = 'fair'
        else:
            status = 'poor'
        
        return {
            'status': status,
            'health_percentage': health_percentage,
            'recent_checks': len(recent_checks),
            'connected_checks': connected_count,
            'last_check': self.network_history[-1] if self.network_history else None
        }

# 自定義網路異常類
class NetworkError(Exception):
    """基礎網路錯誤"""
    pass

class NetworkTimeoutError(NetworkError):
    """網路超時錯誤"""
    pass

class NetworkConnectionError(NetworkError):
    """網路連接錯誤"""
    pass

class NetworkHTTPError(NetworkError):
    """HTTP錯誤"""
    pass

# 全局網路處理器實例
network_handler = NetworkConnectionHandler()
network_monitor = NetworkMonitor()

# 便捷函數
def safe_request(url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
    """安全的HTTP請求函數"""
    try:
        return network_handler.make_request(url, method, **kwargs)
    except Exception as e:
        logger.error(f"❌ 請求失敗: {url} - {str(e)}")
        return None

def check_connectivity() -> bool:
    """檢查網路連接"""
    result = network_handler.check_internet_connectivity()
    return result['connected']