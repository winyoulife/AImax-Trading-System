#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
歷史數據管理器 - 本地數據庫緩存系統
避免每次都重新獲取歷史數據，提升系統效率
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import asyncio
from pathlib import Path
import json

from .max_client import create_max_client

logger = logging.getLogger(__name__)

class HistoricalDataManager:
    """歷史數據管理器"""
    
    def __init__(self, db_path: str = "data/market_history.db"):
        """
        初始化歷史數據管理器
        
        Args:
            db_path: 數據庫文件路徑
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.max_client = create_max_client()
        
        # 數據更新配置
        self.update_config = {
            '1m': {'limit': 1440, 'update_interval': 60},      # 1天數據，每分鐘更新
            '5m': {'limit': 2016, 'update_interval': 300},     # 7天數據，每5分鐘更新
            '1h': {'limit': 720, 'update_interval': 3600},     # 30天數據，每小時更新
            '1d': {'limit': 365, 'update_interval': 86400}     # 1年數據，每天更新
        }
        
        # 初始化數據庫
        self._init_database()
        
        logger.info(f"📊 歷史數據管理器初始化完成，數據庫: {self.db_path}")
    
    def _init_database(self):
        """初始化數據庫表結構"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 創建K線數據表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS klines (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        market TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        open REAL NOT NULL,
                        high REAL NOT NULL,
                        low REAL NOT NULL,
                        close REAL NOT NULL,
                        volume REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(market, timeframe, timestamp)
                    )
                ''')
                
                # 創建索引
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_klines_market_timeframe_timestamp 
                    ON klines(market, timeframe, timestamp)
                ''')
                
                # 創建數據更新記錄表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS update_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        market TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        last_update TIMESTAMP NOT NULL,
                        records_count INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        UNIQUE(market, timeframe)
                    )
                ''')
                
                # 創建系統配置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info("✅ 數據庫表結構初始化完成")
                
        except Exception as e:
            logger.error(f"❌ 數據庫初始化失敗: {e}")
            raise
    
    async def ensure_historical_data(self, market: str = "btctwd", 
                                   timeframes: List[str] = None) -> Dict[str, bool]:
        """
        確保歷史數據完整性，如果缺失則自動獲取
        
        Args:
            market: 交易對
            timeframes: 時間框架列表，默認為 ['1m', '5m', '1h']
            
        Returns:
            各時間框架的數據狀態
        """
        if timeframes is None:
            timeframes = ['1m', '5m', '1h']
        
        results = {}
        
        try:
            logger.info(f"🔍 檢查歷史數據完整性: {market}")
            
            for timeframe in timeframes:
                logger.info(f"📊 檢查 {timeframe} 數據...")
                
                # 檢查數據是否需要更新
                needs_update, reason = self._check_data_freshness(market, timeframe)
                
                if needs_update:
                    logger.info(f"🔄 {reason}，開始更新 {timeframe} 數據...")
                    success = await self._update_timeframe_data(market, timeframe)
                    results[timeframe] = success
                else:
                    logger.info(f"✅ {timeframe} 數據已是最新")
                    results[timeframe] = True
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 確保歷史數據失敗: {e}")
            return {tf: False for tf in timeframes}
    
    def _check_data_freshness(self, market: str, timeframe: str) -> Tuple[bool, str]:
        """檢查數據新鮮度"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查更新記錄
                cursor.execute('''
                    SELECT last_update, records_count FROM update_log 
                    WHERE market = ? AND timeframe = ?
                ''', (market, timeframe))
                
                result = cursor.fetchone()
                
                if not result:
                    return True, "首次獲取數據"
                
                last_update, records_count = result
                last_update_time = datetime.fromisoformat(last_update)
                
                # 檢查是否需要更新
                update_interval = self.update_config[timeframe]['update_interval']
                time_since_update = (datetime.now() - last_update_time).total_seconds()
                
                if time_since_update > update_interval:
                    return True, f"數據過期 ({time_since_update/60:.1f}分鐘前)"
                
                # 檢查數據量是否足夠
                expected_records = self.update_config[timeframe]['limit']
                if records_count < expected_records * 0.8:  # 允許20%的容差
                    return True, f"數據量不足 ({records_count}/{expected_records})"
                
                return False, "數據已是最新"
                
        except Exception as e:
            logger.error(f"❌ 檢查數據新鮮度失敗: {e}")
            return True, "檢查失敗，強制更新"
    
    async def _update_timeframe_data(self, market: str, timeframe: str) -> bool:
        """更新特定時間框架的數據"""
        try:
            # 獲取配置
            config = self.update_config[timeframe]
            limit = config['limit']
            
            # 轉換時間框架格式
            period_map = {'1m': 1, '5m': 5, '1h': 60, '1d': 1440}
            period = period_map.get(timeframe, 1)
            
            logger.info(f"📥 從MAX API獲取 {timeframe} 數據 (limit: {limit})...")
            
            # 獲取數據
            klines_df = await self.max_client._get_recent_klines(market, period, limit)
            
            if klines_df is None or klines_df.empty:
                logger.error(f"❌ 獲取 {timeframe} 數據失敗")
                return False
            
            # 保存到數據庫
            saved_count = self._save_klines_data(market, timeframe, klines_df)
            
            # 更新記錄
            self._update_log_record(market, timeframe, saved_count, "success")
            
            logger.info(f"✅ {timeframe} 數據更新完成，保存 {saved_count} 條記錄")
            return True
            
        except Exception as e:
            logger.error(f"❌ 更新 {timeframe} 數據失敗: {e}")
            self._update_log_record(market, timeframe, 0, "failed")
            return False
    
    def _save_klines_data(self, market: str, timeframe: str, df: pd.DataFrame) -> int:
        """保存K線數據到數據庫"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                saved_count = 0
                
                for _, row in df.iterrows():
                    try:
                        # 轉換時間戳
                        if isinstance(row['timestamp'], pd.Timestamp):
                            timestamp = int(row['timestamp'].timestamp())
                        else:
                            timestamp = int(row['timestamp'])
                        
                        # 插入數據（使用 INSERT OR REPLACE 避免重複）
                        conn.execute('''
                            INSERT OR REPLACE INTO klines 
                            (market, timeframe, timestamp, open, high, low, close, volume)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            market, timeframe, timestamp,
                            float(row['open']), float(row['high']), 
                            float(row['low']), float(row['close']), 
                            float(row['volume'])
                        ))
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"⚠️ 保存單條記錄失敗: {e}")
                        continue
                
                conn.commit()
                return saved_count
                
        except Exception as e:
            logger.error(f"❌ 保存K線數據失敗: {e}")
            return 0
    
    def _update_log_record(self, market: str, timeframe: str, count: int, status: str):
        """更新日誌記錄"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO update_log 
                    (market, timeframe, last_update, records_count, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (market, timeframe, datetime.now().isoformat(), count, status))
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ 更新日誌記錄失敗: {e}")
    
    def get_historical_data(self, market: str = "btctwd", 
                          timeframe: str = "5m", 
                          limit: int = 100) -> Optional[pd.DataFrame]:
        """
        從數據庫獲取歷史數據
        
        Args:
            market: 交易對
            timeframe: 時間框架
            limit: 數據條數
            
        Returns:
            歷史數據DataFrame
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT timestamp, open, high, low, close, volume
                    FROM klines 
                    WHERE market = ? AND timeframe = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                '''
                
                df = pd.read_sql_query(query, conn, params=(market, timeframe, limit))
                
                if df.empty:
                    logger.warning(f"⚠️ 沒有找到 {market} {timeframe} 的歷史數據")
                    return None
                
                # 轉換時間戳
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                
                # 按時間正序排列
                df = df.sort_values('timestamp').reset_index(drop=True)
                
                logger.info(f"✅ 獲取歷史數據: {len(df)} 條 {timeframe} 記錄")
                return df
                
        except Exception as e:
            logger.error(f"❌ 獲取歷史數據失敗: {e}")
            return None
    
    def get_multiple_timeframes(self, market: str = "btctwd", 
                              timeframes: Dict[str, int] = None) -> Dict[str, pd.DataFrame]:
        """
        獲取多個時間框架的歷史數據
        
        Args:
            market: 交易對
            timeframes: 時間框架和數據量配置，如 {'1m': 100, '5m': 50, '1h': 24}
            
        Returns:
            各時間框架的數據字典
        """
        if timeframes is None:
            timeframes = {'1m': 100, '5m': 50, '1h': 24}
        
        results = {}
        
        for timeframe, limit in timeframes.items():
            df = self.get_historical_data(market, timeframe, limit)
            if df is not None:
                results[timeframe] = df
        
        logger.info(f"✅ 獲取多時間框架數據: {list(results.keys())}")
        return results
    
    def get_data_statistics(self, market: str = "btctwd") -> Dict[str, Any]:
        """獲取數據統計信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 獲取各時間框架的數據統計
                cursor.execute('''
                    SELECT timeframe, COUNT(*) as count, 
                           MIN(timestamp) as earliest, 
                           MAX(timestamp) as latest
                    FROM klines 
                    WHERE market = ?
                    GROUP BY timeframe
                ''', (market,))
                
                timeframe_stats = {}
                for row in cursor.fetchall():
                    timeframe, count, earliest, latest = row
                    timeframe_stats[timeframe] = {
                        'count': count,
                        'earliest': datetime.fromtimestamp(earliest).isoformat(),
                        'latest': datetime.fromtimestamp(latest).isoformat(),
                        'coverage_hours': (latest - earliest) / 3600
                    }
                
                # 獲取更新記錄
                cursor.execute('''
                    SELECT timeframe, last_update, status
                    FROM update_log 
                    WHERE market = ?
                ''', (market,))
                
                update_stats = {}
                for row in cursor.fetchall():
                    timeframe, last_update, status = row
                    update_stats[timeframe] = {
                        'last_update': last_update,
                        'status': status
                    }
                
                return {
                    'market': market,
                    'timeframe_stats': timeframe_stats,
                    'update_stats': update_stats,
                    'database_path': str(self.db_path),
                    'database_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                }
                
        except Exception as e:
            logger.error(f"❌ 獲取數據統計失敗: {e}")
            return {}
    
    async def initialize_full_dataset(self, market: str = "btctwd") -> bool:
        """初始化完整數據集（首次使用時調用）"""
        try:
            logger.info(f"🚀 開始初始化完整數據集: {market}")
            
            # 按優先級順序初始化
            timeframes = ['1h', '5m', '1m']  # 從長期到短期
            
            for timeframe in timeframes:
                logger.info(f"📊 初始化 {timeframe} 數據...")
                success = await self._update_timeframe_data(market, timeframe)
                
                if not success:
                    logger.error(f"❌ 初始化 {timeframe} 數據失敗")
                    return False
                
                # 短暫延遲避免API限制
                await asyncio.sleep(1)
            
            logger.info("✅ 完整數據集初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 初始化完整數據集失敗: {e}")
            return False
    
    def cleanup_old_data(self, market: str = "btctwd", days_to_keep: int = 30):
        """清理舊數據"""
        try:
            cutoff_timestamp = int((datetime.now() - timedelta(days=days_to_keep)).timestamp())
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 刪除舊數據
                cursor.execute('''
                    DELETE FROM klines 
                    WHERE market = ? AND timestamp < ?
                ''', (market, cutoff_timestamp))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"🗑️ 清理了 {deleted_count} 條舊數據")
                
                # 優化數據庫
                cursor.execute('VACUUM')
                
        except Exception as e:
            logger.error(f"❌ 清理舊數據失敗: {e}")
    
    async def close(self):
        """關閉連接"""
        try:
            await self.max_client.close()
            logger.info("✅ 歷史數據管理器已關閉")
        except Exception as e:
            logger.error(f"❌ 關閉歷史數據管理器失敗: {e}")


# 創建全局歷史數據管理器實例
def create_historical_manager(db_path: str = "data/market_history.db") -> HistoricalDataManager:
    """創建歷史數據管理器實例"""
    return HistoricalDataManager(db_path)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_historical_manager():
        """測試歷史數據管理器"""
        print("🧪 測試歷史數據管理器...")
        
        manager = create_historical_manager()
        
        try:
            # 檢查並確保數據完整性
            print("🔍 檢查數據完整性...")
            results = await manager.ensure_historical_data("btctwd", ['1m', '5m', '1h'])
            
            for timeframe, success in results.items():
                print(f"   {timeframe}: {'✅ 成功' if success else '❌ 失敗'}")
            
            # 獲取歷史數據
            print("\n📊 獲取歷史數據...")
            data = manager.get_multiple_timeframes("btctwd", {'1m': 50, '5m': 30, '1h': 12})
            
            for timeframe, df in data.items():
                print(f"   {timeframe}: {len(df)} 條記錄")
            
            # 顯示統計信息
            print("\n📈 數據統計:")
            stats = manager.get_data_statistics("btctwd")
            
            for timeframe, info in stats.get('timeframe_stats', {}).items():
                print(f"   {timeframe}: {info['count']} 條記錄，覆蓋 {info['coverage_hours']:.1f} 小時")
            
            print(f"\n💾 數據庫大小: {stats.get('database_size_mb', 0):.2f} MB")
            
        finally:
            await manager.close()
    
    # 運行測試
    asyncio.run(test_historical_manager())