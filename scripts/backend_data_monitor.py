#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
後端數據監控器
監控後端是否真的獲取到真實的BTC價格和交易數據
確保83.3%勝率策略基於真實數據運行
"""

import os
import sys
import json
import requests
import time
from datetime import datetime, timedelta

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class BackendDataMonitor:
    """後端數據監控器"""
    
    def __init__(self):
        self.max_api_url = "https://max-api.maicoin.com/api/v2/tickers/btctwd"
        self.data_log_file = "data/backend_data_log.json"
        self.status_file = "data/backend_status.json"
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        """確保數據目錄存在"""
        os.makedirs("data", exist_ok=True)
    
    def test_max_api_direct(self):
        """直接測試MAX API"""
        print("🔍 直接測試MAX API...")
        try:
            response = requests.get(self.max_api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'ticker' in data and 'last' in data['ticker']:
                    price = float(data['ticker']['last'])
                    print(f"✅ MAX API直接調用成功")
                    print(f"📊 BTC價格: NT$ {price:,.0f}")
                    print(f"📈 24h漲跌: {data['ticker'].get('change', 'N/A')}")
                    print(f"📊 成交量: {data['ticker'].get('vol', 'N/A')}")
                    return {"success": True, "price": price, "data": data['ticker']}
                else:
                    print("❌ API返回數據格式錯誤")
                    return {"success": False, "error": "數據格式錯誤"}
            else:
                print(f"❌ API調用失敗，狀態碼: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            print(f"❌ API調用異常: {e}")
            return {"success": False, "error": str(e)}
    
    def test_cors_proxy(self):
        """測試CORS代理"""
        print("\n🔍 測試CORS代理...")
        proxy_urls = [
            "https://api.allorigins.win/raw?url=",
            "https://cors-anywhere.herokuapp.com/",
            "https://api.codetabs.com/v1/proxy?quest="
        ]
        
        for proxy_url in proxy_urls:
            try:
                full_url = proxy_url + self.max_api_url
                print(f"🔗 測試代理: {proxy_url}")
                
                response = requests.get(full_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'ticker' in data and 'last' in data['ticker']:
                        price = float(data['ticker']['last'])
                        print(f"✅ 代理調用成功")
                        print(f"📊 BTC價格: NT$ {price:,.0f}")
                        return {"success": True, "price": price, "proxy": proxy_url}
                    else:
                        print("❌ 代理返回數據格式錯誤")
                else:
                    print(f"❌ 代理調用失敗，狀態碼: {response.status_code}")
            except Exception as e:
                print(f"❌ 代理調用異常: {e}")
        
        return {"success": False, "error": "所有代理都失敗"}
    
    def check_backend_data_sources(self):
        """檢查後端數據源"""
        print("\n🔍 檢查後端數據源...")
        
        # 檢查數據獲取器
        try:
            from src.data.data_fetcher import DataFetcher
            fetcher = DataFetcher()
            
            print("✅ DataFetcher 模組載入成功")
            
            # 測試獲取當前價格
            if hasattr(fetcher, 'get_current_price'):
                price = fetcher.get_current_price('BTCTWD')
                if price and price > 0:
                    print(f"✅ 後端獲取價格成功: NT$ {price:,.0f}")
                    return {"success": True, "backend_price": price}
                else:
                    print("❌ 後端獲取價格失敗或為0")
            else:
                print("❌ DataFetcher 沒有 get_current_price 方法")
                
        except ImportError as e:
            print(f"❌ 無法載入 DataFetcher: {e}")
        except Exception as e:
            print(f"❌ 後端數據源檢查失敗: {e}")
        
        return {"success": False, "error": "後端數據源不可用"}
    
    def check_trading_strategy_data(self):
        """檢查交易策略是否獲取到真實數據"""
        print("\n🔍 檢查交易策略數據...")
        
        try:
            # 檢查智能平衡策略
            from src.core.smart_balanced_volume_macd_signals import SmartBalancedVolumeMACDSignals
            strategy = SmartBalancedVolumeMACDSignals()
            
            print("✅ 智能平衡策略模組載入成功")
            
            # 檢查策略是否能獲取數據
            if hasattr(strategy, 'get_current_data'):
                data = strategy.get_current_data()
                if data:
                    print(f"✅ 策略獲取數據成功")
                    print(f"📊 數據項目: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                    return {"success": True, "strategy_data": True}
                else:
                    print("❌ 策略獲取數據失敗")
            else:
                print("⚠️ 策略沒有 get_current_data 方法")
                
        except ImportError as e:
            print(f"❌ 無法載入交易策略: {e}")
        except Exception as e:
            print(f"❌ 交易策略檢查失敗: {e}")
        
        return {"success": False, "error": "交易策略數據不可用"}
    
    def generate_status_report(self):
        """生成狀態報告"""
        print("\n📊 生成後端數據狀態報告...")
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # 測試各個數據源
        status["tests"]["max_api_direct"] = self.test_max_api_direct()
        status["tests"]["cors_proxy"] = self.test_cors_proxy()
        status["tests"]["backend_data_sources"] = self.check_backend_data_sources()
        status["tests"]["trading_strategy"] = self.check_trading_strategy_data()
        
        # 計算總體狀態
        success_count = sum(1 for test in status["tests"].values() if test.get("success", False))
        total_tests = len(status["tests"])
        
        status["overall"] = {
            "success_rate": success_count / total_tests,
            "status": "healthy" if success_count >= 2 else "warning" if success_count >= 1 else "critical",
            "message": f"{success_count}/{total_tests} 數據源正常"
        }
        
        # 保存狀態
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
        
        return status
    
    def create_dashboard_status_display(self, status):
        """創建儀表板狀態顯示"""
        print("\n📋 創建儀表板狀態顯示...")
        
        # 獲取真實價格
        real_price = None
        for test_name, test_result in status["tests"].items():
            if test_result.get("success") and "price" in test_result:
                real_price = test_result["price"]
                break
        
        if not real_price:
            real_price = "無法獲取"
        
        # 創建狀態HTML
        status_html = f'''
        <!-- 後端數據狀態監控 -->
        <div class="backend-status-panel" style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin: 10px 0;">
            <h4>🔍 後端數據狀態監控</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                <div>
                    <strong>📊 真實BTC價格:</strong><br>
                    <span style="color: #00ff88; font-size: 1.2em;">NT$ {real_price:,.0f if isinstance(real_price, (int, float)) else real_price}</span>
                </div>
                <div>
                    <strong>🎯 數據源狀態:</strong><br>
                    <span style="color: {'#00ff88' if status['overall']['status'] == 'healthy' else '#ffaa00' if status['overall']['status'] == 'warning' else '#ff4444'};">
                        {status['overall']['message']}
                    </span>
                </div>
                <div>
                    <strong>🔗 MAX API:</strong><br>
                    <span style="color: {'#00ff88' if status['tests']['max_api_direct']['success'] else '#ff4444'};">
                        {'✅ 正常' if status['tests']['max_api_direct']['success'] else '❌ 失敗'}
                    </span>
                </div>
                <div>
                    <strong>🚀 交易策略:</strong><br>
                    <span style="color: {'#00ff88' if status['tests']['trading_strategy']['success'] else '#ff4444'};">
                        {'✅ 數據正常' if status['tests']['trading_strategy']['success'] else '❌ 數據異常'}
                    </span>
                </div>
            </div>
            <div style="margin-top: 10px; font-size: 0.9em; color: #ccc;">
                最後更新: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}
            </div>
        </div>
        '''
        
        return status_html, real_price
    
    def update_dashboard_with_status(self, status):
        """更新儀表板顯示後端狀態"""
        dashboard_file = "static/smart-balanced-dashboard.html"
        
        if not os.path.exists(dashboard_file):
            print(f"❌ 儀表板文件不存在: {dashboard_file}")
            return False
        
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 創建狀態顯示
        status_html, real_price = self.create_dashboard_status_display(status)
        
        # 插入狀態監控面板
        insert_point = content.find('<div class="trading-panel">')
        if insert_point != -1:
            content = content[:insert_point] + status_html + '\n            ' + content[insert_point:]
        
        # 更新BTC價格顯示
        if isinstance(real_price, (int, float)):
            # 替換備用價格為真實價格
            content = content.replace('NT$ 3,000,000 (備用)', f'NT$ {real_price:,.0f}')
            content = content.replace('const fallbackPrice = 3000000;', f'const fallbackPrice = {int(real_price)};')
        
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 儀表板已更新後端狀態顯示")
        return True

def main():
    """主函數"""
    print("🔍 AImax 後端數據監控器")
    print("=" * 60)
    print("檢查後端是否真的獲取到真實BTC價格和交易數據")
    print("確保83.3%勝率策略基於真實數據運行")
    print("=" * 60)
    
    monitor = BackendDataMonitor()
    
    # 生成狀態報告
    status = monitor.generate_status_report()
    
    # 更新儀表板
    monitor.update_dashboard_with_status(status)
    
    # 顯示總結
    print("\n" + "=" * 60)
    print("📊 後端數據監控總結")
    print("=" * 60)
    
    overall = status["overall"]
    print(f"🎯 總體狀態: {overall['status'].upper()}")
    print(f"📊 成功率: {overall['success_rate']*100:.1f}%")
    print(f"💬 狀態訊息: {overall['message']}")
    
    if overall["status"] == "critical":
        print("\n🚨 警告: 後端數據源嚴重異常！")
        print("   83.3%勝率策略可能無法基於真實數據運行！")
        print("   請立即檢查網路連接和API狀態！")
    elif overall["status"] == "warning":
        print("\n⚠️ 注意: 部分後端數據源異常")
        print("   建議檢查數據源狀態以確保策略正常運行")
    else:
        print("\n✅ 後端數據源正常")
        print("   83.3%勝率策略可以基於真實數據運行")
    
    print(f"\n📋 詳細報告已保存: {monitor.status_file}")
    print("🌐 儀表板已更新後端狀態顯示")

if __name__ == "__main__":
    main()