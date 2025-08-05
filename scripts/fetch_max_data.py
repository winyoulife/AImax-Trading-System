#!/usr/bin/env python3
"""
MAX API 數據獲取腳本
用於 GitHub Actions 定期獲取 BTC/TWD 價格數據並生成靜態 JSON 文件
"""

import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import requests
from pathlib import Path

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MAXAPIFetcher:
    """MAX API 數據獲取器"""
    
    def __init__(self):
        self.api_url = "https://max-api.maicoin.com/api/v2/tickers/btctwd"
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 10
        
    def fetch_price_data(self) -> Optional[Dict[str, Any]]:
        """
        從 MAX API 獲取 BTC/TWD 價格數據
        
        Returns:
            Dict: 包含價格數據的字典，失敗時返回 None
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"嘗試獲取 MAX API 數據 (第 {attempt + 1} 次)")
                
                start_time = time.time()
                response = requests.get(
                    self.api_url,
                    timeout=self.timeout,
                    headers={
                        'User-Agent': 'AImax-Trading-System/3.0 (GitHub-Actions)',
                        'Accept': 'application/json'
                    }
                )
                response_time = int((time.time() - start_time) * 1000)
                
                logger.info(f"API 響應狀態: {response.status_code}, 響應時間: {response_time}ms")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info("成功獲取 MAX API 數據")
                    return self._process_api_data(data, response_time)
                else:
                    logger.warning(f"API 返回錯誤狀態碼: {response.status_code}")
                    if response.status_code >= 500 and attempt < self.max_retries - 1:
                        logger.info(f"服務器錯誤，{self.retry_delay} 秒後重試...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        break
                        
            except requests.exceptions.Timeout:
                logger.warning(f"API 請求超時 (第 {attempt + 1} 次)")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"API 請求失敗: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析失敗: {e}")
                break
                
            except Exception as e:
                logger.error(f"未預期的錯誤: {e}")
                break
        
        logger.error("所有重試都失敗了")
        return None
    
    def _process_api_data(self, raw_data: Dict[str, Any], response_time: int) -> Dict[str, Any]:
        """
        處理和驗證 API 數據
        
        Args:
            raw_data: 原始 API 響應數據
            response_time: API 響應時間（毫秒）
            
        Returns:
            Dict: 處理後的數據
        """
        try:
            # 驗證必要字段
            required_fields = ['last', 'buy', 'sell', 'vol', 'at']
            for field in required_fields:
                if field not in raw_data:
                    raise ValueError(f"缺少必要字段: {field}")
            
            # 解析價格數據
            price = float(raw_data['last'])
            buy_price = float(raw_data['buy'])
            sell_price = float(raw_data['sell'])
            volume = float(raw_data['vol'])
            
            # 驗證數據合理性
            if price <= 0 or buy_price <= 0 or sell_price <= 0:
                raise ValueError("價格數據無效（小於等於0）")
                
            if abs(buy_price - sell_price) / price > 0.1:  # 買賣價差超過10%
                logger.warning("買賣價差異常大，可能數據有問題")
            
            current_time = datetime.now(timezone.utc)
            
            processed_data = {
                "success": True,
                "data": {
                    "price": price,
                    "formatted_price": f"NT${price:,.0f}",
                    "buy_price": buy_price,
                    "sell_price": sell_price,
                    "volume": volume,
                    "timestamp": current_time.isoformat(),
                    "source": "MAX API v2"
                },
                "meta": {
                    "fetch_time": current_time.isoformat(),
                    "data_age_seconds": 0,
                    "api_response_time_ms": response_time,
                    "next_update_eta": self._calculate_next_update(current_time),
                    "version": "1.0"
                },
                "status": {
                    "code": 200,
                    "message": "success",
                    "last_error": None,
                    "consecutive_failures": 0
                },
                "raw_data": raw_data  # 保留原始數據用於調試
            }
            
            logger.info(f"數據處理完成 - 價格: NT${price:,.0f}")
            return processed_data
            
        except (ValueError, TypeError) as e:
            logger.error(f"數據處理失敗: {e}")
            raise
    
    def _calculate_next_update(self, current_time: datetime) -> str:
        """計算下次更新時間"""
        # 假設每5分鐘更新一次
        next_update = current_time.replace(second=0, microsecond=0)
        next_update = next_update.replace(minute=(next_update.minute // 5 + 1) * 5)
        return next_update.isoformat()
    
    def load_previous_data(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        加載上次成功的數據
        
        Args:
            file_path: JSON 文件路徑
            
        Returns:
            Dict: 上次的數據，如果不存在則返回 None
        """
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info("成功加載上次的數據")
                    return data
        except Exception as e:
            logger.warning(f"無法加載上次的數據: {e}")
        return None
    
    def create_fallback_data(self, previous_data: Optional[Dict[str, Any]], error_message: str) -> Dict[str, Any]:
        """
        創建降級數據
        
        Args:
            previous_data: 上次成功的數據
            error_message: 錯誤信息
            
        Returns:
            Dict: 降級數據
        """
        current_time = datetime.now(timezone.utc)
        
        if previous_data and previous_data.get("success"):
            # 使用上次成功的數據
            fallback_data = previous_data.copy()
            
            # 更新時間戳和狀態
            old_timestamp = datetime.fromisoformat(previous_data["data"]["timestamp"].replace('Z', '+00:00'))
            data_age = int((current_time - old_timestamp).total_seconds())
            
            fallback_data["meta"]["data_age_seconds"] = data_age
            fallback_data["meta"]["fetch_time"] = current_time.isoformat()
            fallback_data["status"]["last_error"] = error_message
            fallback_data["status"]["consecutive_failures"] = previous_data["status"].get("consecutive_failures", 0) + 1
            
            # 如果數據太舊，標記為過期
            if data_age > 1800:  # 30分鐘
                fallback_data["status"]["message"] = "stale_data"
                fallback_data["data"]["source"] = "MAX API v2 (cached - stale)"
            else:
                fallback_data["status"]["message"] = "using_cached_data"
                fallback_data["data"]["source"] = "MAX API v2 (cached)"
            
            logger.info(f"使用緩存數據，數據年齡: {data_age} 秒")
            return fallback_data
        else:
            # 沒有可用的歷史數據，創建錯誤響應
            return {
                "success": False,
                "error": {
                    "code": "API_UNAVAILABLE",
                    "message": error_message,
                    "timestamp": current_time.isoformat(),
                    "retry_after": 300
                },
                "meta": {
                    "fetch_time": current_time.isoformat(),
                    "version": "1.0"
                },
                "status": {
                    "code": 503,
                    "message": "service_unavailable",
                    "last_error": error_message,
                    "consecutive_failures": 1
                }
            }
    
    def save_data(self, data: Dict[str, Any], file_path: Path) -> bool:
        """
        保存數據到 JSON 文件
        
        Args:
            data: 要保存的數據
            file_path: 文件路徑
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 確保目錄存在
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存數據
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"數據已保存到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存數據失敗: {e}")
            return False

def main():
    """主函數"""
    logger.info("開始執行 MAX API 數據獲取任務")
    
    # 初始化獲取器
    fetcher = MAXAPIFetcher()
    
    # 設置文件路徑
    output_dir = Path("static/api")
    output_file = output_dir / "btc-price.json"
    
    # 加載上次的數據
    previous_data = fetcher.load_previous_data(output_file)
    
    # 獲取新數據
    new_data = fetcher.fetch_price_data()
    
    if new_data:
        # 成功獲取新數據
        success = fetcher.save_data(new_data, output_file)
        if success:
            logger.info("任務完成：成功獲取並保存新數據")
            return 0
        else:
            logger.error("任務失敗：無法保存數據")
            return 1
    else:
        # 獲取失敗，使用降級策略
        logger.warning("無法獲取新數據，使用降級策略")
        fallback_data = fetcher.create_fallback_data(
            previous_data, 
            "MAX API 暫時不可用"
        )
        
        success = fetcher.save_data(fallback_data, output_file)
        if success:
            logger.info("任務完成：使用降級數據")
            return 0
        else:
            logger.error("任務失敗：無法保存降級數據")
            return 1

if __name__ == "__main__":
    exit(main())