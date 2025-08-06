#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax 錯誤處理系統測試腳本 - 任務9實現
測試錯誤處理、網路重試、頻率限制、交易回滾和系統恢復功能
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

from src.error_handling.error_handler import error_handler, with_retry, with_circuit_breaker, handle_errors
from src.error_handling.network_handler import network_handler, safe_request, check_connectivity
from src.error_handling.rate_limiter import rate_limiter, rate_limited, check_api_limit
from src.error_handling.transaction_rollback import transaction_manager, transactional
from src.error_handling.system_recovery import system_recovery_manager, start_system_monitoring

def test_error_handler():
    """測試錯誤處理器"""
    print("🧪 測試錯誤處理器...")
    
    @with_retry(max_retries=3, base_delay=1.0)
    def flaky_function(success_rate=0.3):
        """模擬不穩定的函數"""
        import random
        if random.random() < success_rate:
            return "Success!"
        else:
            raise Exception("Random failure")
    
    try:
        result = flaky_function(success_rate=0.8)
        print(f"✅ 重試機制測試成功: {result}")
    except Exception as e:
        print(f"❌ 重試機制測試失敗: {e}")
    
    # 測試熔斷器
    @with_circuit_breaker('test_service', failure_threshold=3)
    def unreliable_service():
        """模擬不可靠的服務"""
        raise Exception("Service unavailable")
    
    print("\n🔌 測試熔斷器...")
    for i in range(5):
        try:
            unreliable_service()
        except Exception as e:
            print(f"嘗試 {i+1}: {e}")
    
    # 顯示錯誤統計
    stats = error_handler.get_error_statistics()
    print(f"\n📊 錯誤統計: {stats}")

def test_network_handler():
    """測試網路處理器"""
    print("\n🌐 測試網路處理器...")
    
    # 測試網路連接檢查
    connectivity = check_connectivity()
    print(f"網路連接狀態: {'✅ 正常' if connectivity else '❌ 異常'}")
    
    # 測試安全請求
    print("\n📡 測試HTTP請求...")
    response = safe_request('https://httpbin.org/status/200')
    if response:
        print(f"✅ HTTP請求成功: {response.status_code}")
    else:
        print("❌ HTTP請求失敗")
    
    # 測試特定端點
    test_result = network_handler.test_specific_endpoint('https://api.github.com')
    print(f"GitHub API測試: {'✅ 成功' if test_result['success'] else '❌ 失敗'}")
    
    # 顯示連接統計
    stats = network_handler.get_connection_stats()
    print(f"連接統計: {stats}")

def test_rate_limiter():
    """測試頻率限制器"""
    print("\n⏱️ 測試頻率限制器...")
    
    # 設置測試API限制
    rate_limiter.set_rate_limit('test_api', {
        'requests_per_minute': 5,
        'requests_per_hour': 100
    })
    
    @rate_limited('test_api')
    def api_call(call_id):
        """模擬API調用"""
        print(f"📞 API調用 {call_id}")
        return f"Result {call_id}"
    
    # 快速調用多次測試頻率限制
    print("快速調用API測試頻率限制...")
    for i in range(8):
        try:
            result = api_call(i+1)
            print(f"  {result}")
        except Exception as e:
            print(f"  ❌ 調用 {i+1} 失敗: {e}")
        
        time.sleep(0.5)
    
    # 顯示API使用統計
    usage = rate_limiter.get_api_stats('test_api')
    print(f"\nAPI使用統計: {usage}")

def test_transaction_rollback():
    """測試交易回滾機制"""
    print("\n🔄 測試交易回滾機制...")
    
    # 創建測試交易
    transaction_id = transaction_manager.create_transaction(
        'test_trading', '測試交易回滾機制'
    )
    
    # 添加交易步驟
    transaction_manager.add_step(
        transaction_id, '買入BTC', 'buy_btc',
        {'symbol': 'BTCUSDT', 'quantity': 0.001, 'price': 50000},
        'buy_order', {'order_type': 'market'}
    )
    
    transaction_manager.add_step(
        transaction_id, '更新餘額', 'update_balance',
        {'old_balance': 10000, 'new_balance': 9950, 'change': -50},
        'balance_update'
    )
    
    transaction_manager.add_step(
        transaction_id, '發送通知', 'send_notification',
        {'message': '交易完成', 'user_id': 'test_user'},
        'notification_send'
    )
    
    # 執行交易
    result = transaction_manager.execute_transaction(transaction_id)
    print(f"交易執行結果: {result}")
    
    # 顯示交易狀態
    status = transaction_manager.get_transaction_status(transaction_id)
    print(f"交易狀態: {status}")
    
    # 顯示統計
    stats = transaction_manager.get_statistics()
    print(f"交易統計: {stats}")

def test_system_recovery():
    """測試系統恢復機制"""
    print("\n🔧 測試系統恢復機制...")
    
    # 運行健康檢查
    health_results = system_recovery_manager.run_health_checks()
    print("健康檢查結果:")
    for check_name, result in health_results.items():
        status = result.get('status', 'unknown')
        value = result.get('value', 0)
        print(f"  {check_name}: {status.value if hasattr(status, 'value') else status} ({value})")
    
    # 獲取系統狀態
    system_status = system_recovery_manager.get_system_status()
    print(f"\n系統狀態: {system_status}")
    
    # 啟動短期監控測試
    print("\n🔍 啟動短期系統監控測試...")
    start_system_monitoring()
    
    # 等待一段時間讓監控運行
    time.sleep(10)
    
    # 停止監控
    system_recovery_manager.stop_monitoring()
    
    # 獲取恢復歷史
    recovery_history = system_recovery_manager.get_recovery_history()
    if recovery_history:
        print(f"恢復歷史: {len(recovery_history)} 條記錄")
    else:
        print("沒有恢復歷史記錄")

def test_integrated_error_handling():
    """測試集成錯誤處理"""
    print("\n🎯 測試集成錯誤處理...")
    
    @handle_errors
    @with_retry(max_retries=2)
    @rate_limited('integrated_test')
    def complex_operation():
        """複雜操作，包含多種錯誤處理機制"""
        print("執行複雜操作...")
        
        # 模擬網路請求
        response = safe_request('https://httpbin.org/delay/1')
        if not response:
            raise Exception("網路請求失敗")
        
        # 模擬隨機失敗
        import random
        if random.random() < 0.3:
            raise Exception("隨機業務邏輯錯誤")
        
        return "複雜操作成功完成"
    
    try:
        result = complex_operation()
        print(f"✅ 集成測試成功: {result}")
    except Exception as e:
        print(f"❌ 集成測試失敗: {e}")

def generate_test_report():
    """生成測試報告"""
    print("\n📋 生成錯誤處理測試報告...")
    
    # 收集各模塊的統計信息
    error_stats = error_handler.get_error_statistics()
    network_stats = network_handler.get_connection_stats()
    transaction_stats = transaction_manager.get_statistics()
    system_status = system_recovery_manager.get_system_status()
    
    report = f"""
🛠️ AImax 錯誤處理系統測試報告
{'='*60}

📊 錯誤處理統計:
   總錯誤數: {error_stats.get('total_errors', 0)}
   已解決錯誤: {error_stats.get('resolved_errors', 0)}
   解決率: {error_stats.get('resolution_rate', 0):.1f}%
   最常見錯誤: {error_stats.get('most_common_error', 'None')}

🌐 網路連接統計:
   總請求數: {network_stats.get('total_requests', 0)}
   成功請求: {network_stats.get('successful_requests', 0)}
   成功率: {network_stats.get('success_rate', 0):.1f}%
   平均響應時間: {network_stats.get('average_response_time', 0):.3f}秒

💰 交易回滾統計:
   總交易數: {transaction_stats.get('total_transactions', 0)}
   成功交易: {transaction_stats.get('successful_transactions', 0)}
   回滾交易: {transaction_stats.get('rolled_back_transactions', 0)}
   成功率: {transaction_stats.get('success_rate', 0):.1f}%

🔧 系統恢復狀態:
   整體健康: {system_status.get('overall_health', 'unknown')}
   監控狀態: {'運行中' if system_status.get('monitoring_active', False) else '已停止'}
   連續失敗次數: {system_status.get('consecutive_failures', 0)}
   恢復進行中: {'是' if system_status.get('recovery_in_progress', False) else '否'}

{'='*60}
測試完成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    print(report)
    
    # 保存報告到文件
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    report_file = reports_dir / f"error_handling_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 報告已保存: {report_file}")

def main():
    """主測試函數"""
    print("🚀 AImax 錯誤處理系統完整測試")
    print("=" * 60)
    
    try:
        # 運行各項測試
        test_error_handler()
        test_network_handler()
        test_rate_limiter()
        test_transaction_rollback()
        test_system_recovery()
        test_integrated_error_handling()
        
        # 生成測試報告
        generate_test_report()
        
        print("\n🎉 所有錯誤處理測試完成！")
        
    except Exception as e:
        print(f"\n💥 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()