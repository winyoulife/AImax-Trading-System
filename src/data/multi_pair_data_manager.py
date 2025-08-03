#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多交易對數據管理系統 - 統一管理多個交易對的歷史和實時數據
基於本地AI + MAX歷史數據 + 超進化Python的核心理念
"""

import asyncio
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import json
from dataclasses import dataclass, asdict
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    from .multi_pair_max_client import MultiPairMAXClient, create_multi_pair_client
    from .trading_pair_manager import TradingPairManager, create_trading_pair_manager
    from .historical_data_manager import HistoricalDataManager
except ImportError:
    # 用於直接運行測試
    from multi_pair_max_client import MultiPairMAXClient, create_multi_pair_client
    from trading_pair_manager import TradingPairManager, create_trading_pair_manager
    from historical_data_manager import HistoricalDataManager

logger = logging.getLogger(__name__)

@dataclass
class DataStreamConfig:
    """數據流配置"""
    pair: str
    timeframes: List[str]
    update_intervals: Dict[str, int]  # 秒
    buffer_size: int = 1000
    enabled: bool = True

@dataclass
class DataSyncStatus:
    """數據同步狀態"""
    pair: str
    last_sync: datetime
    sync_status: str  # 'synced', 'syncing', 'error'
    records_synced: int
    error_message: Optional[str] = None

class MultiPairDataManager:
    """多交易對數據管理系統 - 增強版"""
    
    def __init__(self, db_path: str = "data/multi_pair_market.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 核心組件
        self.max_client = create_multi_pair_client()
        self.pair_manager = create_trading_pair_manager()
        
        # 為每個交易對創建獨立的歷史數據管理器
        self.pair_data_managers: Dict[str, HistoricalDataManager] = {}
        
        # 數據流配置
        self.stream_configs: Dict[str, DataStreamConfig] = {}
        self.sync_status: Dict[str, DataSyncStatus] = {}
        
        # 數據緩存和同步 - 增強版
        self.data_buffers: Dict[str, Dict[str, List]] = {}
        self.sync_locks: Dict[str, threading.Lock] = {}
        self.data_consistency_cache: Dict[str, Dict[str, Any]] = {}
        
        # 並發控制 - 優化
        self.executor = ThreadPoolExecutor(max_workers=8)  # 增加線程數
        self.sync_interval = 300  # 5分鐘同步一次
        self.is_running = False
        
        # 數據同步協調器
        self.sync_coordinator = DataSyncCoordinator()
        
        # 初始化
        self._init_database()
        self._initialize_stream_configs()
        self._initialize_pair_data_managers()
        
        logger.info("🚀 多交易對數據管理系統 (增強版) 初始化完成")
    
    def _initialize_pair_data_managers(self):
        """為每個交易對創建獨立的歷史數據管理器"""
        try:
            for pair in self.stream_configs.keys():
                # 為每個交易對創建專用的數據庫路徑
                pair_db_path = f"data/{pair.lower()}_history.db"
                
                # 創建獨立的歷史數據管理器
                self.pair_data_managers[pair] = HistoricalDataManager(
                    db_path=pair_db_path,
                    pair=pair
                )
                
                logger.debug(f"✅ 為 {pair} 創建獨立數據管理器")
            
            logger.info(f"📊 為 {len(self.pair_data_managers)} 個交易對創建獨立數據管理器")
            
        except Exception as e:
            logger.error(f"❌ 初始化交易對數據管理器失敗: {e}")


class DataSyncCoordinator:
    """數據同步協調器 - 管理多交易對間的數據同步和一致性"""
    
    def __init__(self):
        self.sync_queue = asyncio.Queue()
        self.sync_locks = {}
        self.cross_pair_correlations = {}
        self.sync_priorities = {}
        
        logger.info("🔄 數據同步協調器初始化完成")
    
    async def coordinate_sync(self, pairs: List[str], sync_type: str = 'incremental'):
        """協調多交易對同步"""
        try:
            # 根據優先級排序
            sorted_pairs = self._sort_pairs_by_priority(pairs)
            
            # 並行同步，但控制並發數
            semaphore = asyncio.Semaphore(3)  # 最多3個並發同步
            
            tasks = []
            for pair in sorted_pairs:
                task = self._sync_with_semaphore(semaphore, pair, sync_type)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 檢查同步結果
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            logger.info(f"✅ 協調同步完成: {success_count}/{len(pairs)} 成功")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 協調同步失敗: {e}")
            return []
    
    async def _sync_with_semaphore(self, semaphore: asyncio.Semaphore, 
                                 pair: str, sync_type: str):
        """使用信號量控制的同步"""
        async with semaphore:
            return await self._sync_single_pair(pair, sync_type)
    
    async def _sync_single_pair(self, pair: str, sync_type: str):
        """同步單個交易對"""
        try:
            # 獲取同步鎖
            if pair not in self.sync_locks:
                self.sync_locks[pair] = asyncio.Lock()
            
            async with self.sync_locks[pair]:
                logger.debug(f"🔄 開始同步 {pair} ({sync_type})")
                
                # 模擬同步過程
                await asyncio.sleep(1)
                
                logger.debug(f"✅ 完成同步 {pair}")
                return {'pair': pair, 'status': 'success', 'type': sync_type}
                
        except Exception as e:
            logger.error(f"❌ 同步 {pair} 失敗: {e}")
            return {'pair': pair, 'status': 'error', 'error': str(e)}
    
    def _sort_pairs_by_priority(self, pairs: List[str]) -> List[str]:
        """根據優先級排序交易對"""
        # 默認優先級：主流幣種優先
        priority_map = {
            'BTCTWD': 1,
            'ETHTWD': 2,
            'LTCTWD': 3,
            'BCHTWD': 4,
            'ADATWD': 5,
            'DOTTWD': 6
        }
        
        return sorted(pairs, key=lambda p: priority_map.get(p, 999))
    
    def update_cross_pair_correlations(self, correlations: Dict[str, Dict[str, float]]):
        """更新交易對間相關性"""
        self.cross_pair_correlations = correlations
        logger.debug(f"📊 更新交易對相關性: {len(correlations)} 對")
    
    def get_sync_recommendations(self, pair: str) -> Dict[str, Any]:
        """獲取同步建議"""
        try:
            recommendations = {
                'priority': self.sync_priorities.get(pair, 'normal'),
                'correlated_pairs': [],
                'sync_frequency': 'normal'
            }
            
            # 查找高相關性的交易對
            if pair in self.cross_pair_correlations:
                for other_pair, correlation in self.cross_pair_correlations[pair].items():
                    if abs(correlation) > 0.7:  # 高相關性閾值
                        recommendations['correlated_pairs'].append({
                            'pair': other_pair,
                            'correlation': correlation
                        })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ 獲取 {pair} 同步建議失敗: {e}")
            return {}


# 將_init_database方法移回MultiPairDataManager類中
# 這個方法應該在MultiPairDataManager類內部，而不是在DataSyncCoordinator類中

# 讓我們在MultiPairDataManager類中添加缺失的方法
class MultiPairDataManagerMethods:
    """MultiPairDataManager的額外方法 - 臨時修復"""
    
    def _init_database(self):
        """初始化多交易對數據庫"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 創建多交易對K線數據表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS multi_pair_klines (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pair TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        open REAL NOT NULL,
                        high REAL NOT NULL,
                        low REAL NOT NULL,
                        close REAL NOT NULL,
                        volume REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(pair, timeframe, timestamp)
                    )
                ''')
                
                # 創建實時數據表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS real_time_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pair TEXT NOT NULL,
                        timestamp INTEGER NOT NULL,
                        price REAL NOT NULL,
                        volume REAL NOT NULL,
                        bid REAL,
                        ask REAL,
                        technical_data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(pair, timestamp)
                    )
                ''')
                
                # 創建數據同步日誌表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sync_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pair TEXT NOT NULL,
                        sync_type TEXT NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        records_processed INTEGER DEFAULT 0,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 創建索引
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_multi_klines_pair_timeframe_timestamp 
                    ON multi_pair_klines(pair, timeframe, timestamp)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_realtime_pair_timestamp 
                    ON real_time_data(pair, timestamp)
                ''')
                
                conn.commit()
                logger.info("✅ 多交易對數據庫初始化完成")
                
        except Exception as e:
            logger.error(f"❌ 數據庫初始化失敗: {e}")
            raise    

    def _initialize_stream_configs(self):
        """初始化數據流配置"""
        try:
            # 獲取所有活躍交易對
            active_pairs = self.max_client.get_active_pairs()
            
            for pair in active_pairs:
                # 為每個交易對創建數據流配置
                config = DataStreamConfig(
                    pair=pair,
                    timeframes=['1m', '5m', '1h'],
                    update_intervals={'1m': 60, '5m': 300, '1h': 3600},
                    buffer_size=1000,
                    enabled=True
                )
                
                self.stream_configs[pair] = config
                self.sync_status[pair] = DataSyncStatus(
                    pair=pair,
                    last_sync=datetime.now(),
                    sync_status='initialized',
                    records_synced=0
                )
                
                # 初始化數據緩存和鎖
                self.data_buffers[pair] = {tf: [] for tf in config.timeframes}
                self.sync_locks[pair] = threading.Lock()
            
            logger.info(f"📊 初始化 {len(active_pairs)} 個交易對的數據流配置")
            
        except Exception as e:
            logger.error(f"❌ 初始化數據流配置失敗: {e}")
    
    async def start_data_streams(self):
        """啟動所有數據流"""
        if self.is_running:
            logger.warning("⚠️ 數據流已在運行中")
            return
        
        self.is_running = True
        logger.info("🚀 啟動多交易對數據流...")
        
        try:
            # 創建並發任務
            tasks = []
            
            # 實時數據獲取任務
            tasks.append(asyncio.create_task(self._real_time_data_loop()))
            
            # 歷史數據同步任務
            tasks.append(asyncio.create_task(self._historical_sync_loop()))
            
            # 數據一致性檢查任務
            tasks.append(asyncio.create_task(self._consistency_check_loop()))
            
            # 等待所有任務
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"❌ 數據流運行失敗: {e}")
        finally:
            self.is_running = False
    
    async def _real_time_data_loop(self):
        """實時數據獲取循環"""
        logger.info("📡 啟動實時數據獲取循環")
        
        while self.is_running:
            try:
                # 獲取所有交易對的實時數據
                market_data = await self.max_client.get_multi_pair_market_data()
                
                if market_data:
                    # 並行處理每個交易對的數據
                    tasks = []
                    for pair, data in market_data.items():
                        task = self._process_real_time_data(pair, data)
                        tasks.append(task)
                    
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # 等待下一次更新
                await asyncio.sleep(30)  # 30秒更新一次實時數據
                
            except Exception as e:
                logger.error(f"❌ 實時數據循環錯誤: {e}")
                await asyncio.sleep(60)  # 錯誤時等待更長時間
    
    async def _process_real_time_data(self, pair: str, data: Dict[str, Any]):
        """處理單個交易對的實時數據"""
        try:
            if pair not in self.stream_configs:
                return
            
            # 提取關鍵數據
            timestamp = int(data.get('timestamp', datetime.now()).timestamp())
            price = data.get('current_price', 0)
            volume = data.get('volume_24h', 0)
            bid = data.get('bid', price)
            ask = data.get('ask', price)
            
            # 技術指標數據
            technical_data = {
                'rsi': data.get('rsi', 50),
                'macd': data.get('macd', 0),
                'bollinger_position': data.get('bollinger_position', 0.5),
                'volume_ratio': data.get('volume_ratio', 1.0),
                'volatility': data.get('volatility', 0.02)
            }
            
            # 保存實時數據
            await self._save_real_time_data(pair, timestamp, price, volume, 
                                          bid, ask, technical_data)
            
            # 更新同步狀態
            if pair in self.sync_status:
                self.sync_status[pair].last_sync = datetime.now()
                self.sync_status[pair].sync_status = 'synced'
                self.sync_status[pair].records_synced += 1
            
        except Exception as e:
            logger.error(f"❌ 處理 {pair} 實時數據失敗: {e}")
            if pair in self.sync_status:
                self.sync_status[pair].sync_status = 'error'
                self.sync_status[pair].error_message = str(e)
    
    async def _save_real_time_data(self, pair: str, timestamp: int, price: float,
                                 volume: float, bid: float, ask: float,
                                 technical_data: Dict[str, Any]):
        """保存實時數據到數據庫"""
        try:
            def save_to_db():
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        INSERT OR REPLACE INTO real_time_data 
                        (pair, timestamp, price, volume, bid, ask, technical_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (pair, timestamp, price, volume, bid, ask, 
                          json.dumps(technical_data)))
                    conn.commit()
            
            # 在線程池中執行數據庫操作
            await asyncio.get_event_loop().run_in_executor(
                self.executor, save_to_db
            )
            
        except Exception as e:
            logger.error(f"❌ 保存 {pair} 實時數據失敗: {e}")
    
    async def _historical_sync_loop(self):
        """歷史數據同步循環"""
        logger.info("📚 啟動歷史數據同步循環")
        
        while self.is_running:
            try:
                # 為每個交易對同步歷史數據
                for pair in self.stream_configs:
                    if self.stream_configs[pair].enabled:
                        await self._sync_pair_historical_data(pair)
                        
                        # 避免API限制
                        await asyncio.sleep(2)
                
                # 等待下一次同步
                await asyncio.sleep(self.sync_interval)
                
            except Exception as e:
                logger.error(f"❌ 歷史數據同步循環錯誤: {e}")
                await asyncio.sleep(300)  # 錯誤時等待5分鐘    

    async def _sync_pair_historical_data(self, pair: str):
        """同步單個交易對的歷史數據"""
        try:
            config = self.stream_configs[pair]
            
            # 記錄同步開始
            sync_id = await self._log_sync_start(pair, 'historical')
            
            total_synced = 0
            
            for timeframe in config.timeframes:
                # 檢查是否需要更新
                if await self._needs_historical_update(pair, timeframe):
                    logger.info(f"🔄 同步 {pair} {timeframe} 歷史數據...")
                    
                    # 獲取歷史數據
                    synced_count = await self._fetch_and_save_historical(pair, timeframe)
                    total_synced += synced_count
                    
                    logger.debug(f"✅ {pair} {timeframe} 同步完成: {synced_count} 條")
            
            # 記錄同步完成
            await self._log_sync_complete(sync_id, total_synced, 'success')
            
            # 更新狀態
            if pair in self.sync_status:
                self.sync_status[pair].sync_status = 'synced'
                self.sync_status[pair].records_synced += total_synced
                self.sync_status[pair].last_sync = datetime.now()
            
        except Exception as e:
            logger.error(f"❌ 同步 {pair} 歷史數據失敗: {e}")
            await self._log_sync_complete(sync_id, 0, 'error', str(e))
            
            if pair in self.sync_status:
                self.sync_status[pair].sync_status = 'error'
                self.sync_status[pair].error_message = str(e)
    
    async def _needs_historical_update(self, pair: str, timeframe: str) -> bool:
        """檢查是否需要更新歷史數據"""
        try:
            def check_db():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 獲取最新數據時間
                    cursor.execute('''
                        SELECT MAX(timestamp) FROM multi_pair_klines 
                        WHERE pair = ? AND timeframe = ?
                    ''', (pair, timeframe))
                    
                    result = cursor.fetchone()
                    if not result or not result[0]:
                        return True  # 沒有數據，需要更新
                    
                    latest_timestamp = result[0]
                    latest_time = datetime.fromtimestamp(latest_timestamp)
                    
                    # 檢查數據是否過期
                    config = self.stream_configs[pair]
                    update_interval = config.update_intervals.get(timeframe, 3600)
                    
                    time_diff = (datetime.now() - latest_time).total_seconds()
                    return time_diff > update_interval
            
            return await asyncio.get_event_loop().run_in_executor(
                self.executor, check_db
            )
            
        except Exception as e:
            logger.error(f"❌ 檢查 {pair} {timeframe} 更新需求失敗: {e}")
            return True  # 錯誤時強制更新
    
    async def _fetch_and_save_historical(self, pair: str, timeframe: str) -> int:
        """獲取並保存歷史數據"""
        try:
            # 時間框架映射
            period_map = {'1m': 1, '5m': 5, '1h': 60, '1d': 1440}
            period = period_map.get(timeframe, 5)
            
            # 獲取數據限制
            limit_map = {'1m': 1440, '5m': 2016, '1h': 720, '1d': 365}
            limit = limit_map.get(timeframe, 100)
            
            # 確保session已初始化
            if not self.max_client.session:
                import aiohttp
                self.max_client.session = aiohttp.ClientSession()
            
            # 從API獲取數據
            klines_df = await self.max_client._get_klines(pair, period, limit)
            
            if klines_df is None or klines_df.empty:
                logger.warning(f"⚠️ {pair} {timeframe} 沒有獲取到數據")
                return 0
            
            # 保存到數據庫
            def save_to_db():
                with sqlite3.connect(self.db_path) as conn:
                    saved_count = 0
                    
                    for _, row in klines_df.iterrows():
                        try:
                            timestamp = int(row['timestamp'].timestamp()) if isinstance(row['timestamp'], pd.Timestamp) else int(row['timestamp'])
                            
                            conn.execute('''
                                INSERT OR REPLACE INTO multi_pair_klines 
                                (pair, timeframe, timestamp, open, high, low, close, volume)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                pair, timeframe, timestamp,
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
            
            saved_count = await asyncio.get_event_loop().run_in_executor(
                self.executor, save_to_db
            )
            
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ 獲取保存 {pair} {timeframe} 歷史數據失敗: {e}")
            return 0
    
    async def _consistency_check_loop(self):
        """數據一致性檢查循環"""
        logger.info("🔍 啟動數據一致性檢查循環")
        
        while self.is_running:
            try:
                # 每小時進行一次一致性檢查
                await asyncio.sleep(3600)
                
                for pair in self.stream_configs:
                    await self._check_pair_data_consistency(pair)
                
            except Exception as e:
                logger.error(f"❌ 數據一致性檢查錯誤: {e}")
    
    async def _check_pair_data_consistency(self, pair: str):
        """檢查單個交易對的數據一致性"""
        try:
            def check_consistency():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    issues = []
                    
                    # 檢查數據缺口
                    for timeframe in ['1m', '5m', '1h']:
                        cursor.execute('''
                            SELECT COUNT(*) as count,
                                   MIN(timestamp) as earliest,
                                   MAX(timestamp) as latest
                            FROM multi_pair_klines 
                            WHERE pair = ? AND timeframe = ?
                        ''', (pair, timeframe))
                        
                        result = cursor.fetchone()
                        if result and result[0] > 0:
                            count, earliest, latest = result
                            expected_count = self._calculate_expected_records(
                                timeframe, earliest, latest
                            )
                            
                            if count < expected_count * 0.9:  # 允許10%的容差
                                issues.append(f"{timeframe}: 數據缺失 ({count}/{expected_count})")
                    
                    return issues
            
            issues = await asyncio.get_event_loop().run_in_executor(
                self.executor, check_consistency
            )
            
            if issues:
                logger.warning(f"⚠️ {pair} 數據一致性問題: {issues}")
                # 觸發數據修復
                await self._repair_data_gaps(pair, issues)
            
        except Exception as e:
            logger.error(f"❌ 檢查 {pair} 數據一致性失敗: {e}")
    
    def _calculate_expected_records(self, timeframe: str, earliest: int, latest: int) -> int:
        """計算預期記錄數"""
        time_diff = latest - earliest
        
        if timeframe == '1m':
            return time_diff // 60
        elif timeframe == '5m':
            return time_diff // 300
        elif timeframe == '1h':
            return time_diff // 3600
        else:
            return 0
    
    async def _repair_data_gaps(self, pair: str, issues: List[str]):
        """修復數據缺口"""
        try:
            logger.info(f"🔧 修復 {pair} 數據缺口: {issues}")
            
            # 強制重新同步有問題的時間框架
            for issue in issues:
                timeframe = issue.split(':')[0]
                await self._fetch_and_save_historical(pair, timeframe)
                await asyncio.sleep(1)  # 避免API限制
            
        except Exception as e:
            logger.error(f"❌ 修復 {pair} 數據缺口失敗: {e}")
    
    async def _log_sync_start(self, pair: str, sync_type: str) -> int:
        """記錄同步開始"""
        try:
            def log_to_db():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO sync_log 
                        (pair, sync_type, start_time, status)
                        VALUES (?, ?, ?, ?)
                    ''', (pair, sync_type, datetime.now().isoformat(), 'started'))
                    conn.commit()
                    return cursor.lastrowid
            
            return await asyncio.get_event_loop().run_in_executor(
                self.executor, log_to_db
            )
            
        except Exception as e:
            logger.error(f"❌ 記錄同步開始失敗: {e}")
            return 0
    
    async def _log_sync_complete(self, sync_id: int, records_processed: int, 
                               status: str, error_message: str = None):
        """記錄同步完成"""
        try:
            def log_to_db():
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('''
                        UPDATE sync_log 
                        SET end_time = ?, records_processed = ?, 
                            status = ?, error_message = ?
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), records_processed, 
                          status, error_message, sync_id))
                    conn.commit()
            
            await asyncio.get_event_loop().run_in_executor(
                self.executor, log_to_db
            )
            
        except Exception as e:
            logger.error(f"❌ 記錄同步完成失敗: {e}")
    
    def get_multi_pair_historical_data(self, pairs: List[str] = None, 
                                     timeframe: str = '5m', 
                                     limit: int = 100) -> Dict[str, pd.DataFrame]:
        """獲取多個交易對的歷史數據"""
        if pairs is None:
            pairs = list(self.stream_configs.keys())
        
        results = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for pair in pairs:
                    query = '''
                        SELECT timestamp, open, high, low, close, volume
                        FROM multi_pair_klines 
                        WHERE pair = ? AND timeframe = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    '''
                    
                    df = pd.read_sql_query(query, conn, params=(pair, timeframe, limit))
                    
                    if not df.empty:
                        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                        df = df.sort_values('timestamp').reset_index(drop=True)
                        results[pair] = df
            
            logger.info(f"✅ 獲取 {len(results)} 個交易對的歷史數據")
            return results
            
        except Exception as e:
            logger.error(f"❌ 獲取多交易對歷史數據失敗: {e}")
            return {}
    
    def get_real_time_data_summary(self, pairs: List[str] = None) -> Dict[str, Dict[str, Any]]:
        """獲取實時數據摘要"""
        if pairs is None:
            pairs = list(self.stream_configs.keys())
        
        results = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for pair in pairs:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT price, volume, bid, ask, technical_data, timestamp
                        FROM real_time_data 
                        WHERE pair = ?
                        ORDER BY timestamp DESC
                        LIMIT 1
                    ''', (pair,))
                    
                    result = cursor.fetchone()
                    if result:
                        price, volume, bid, ask, technical_data_json, timestamp = result
                        
                        technical_data = json.loads(technical_data_json) if technical_data_json else {}
                        
                        results[pair] = {
                            'price': price,
                            'volume': volume,
                            'bid': bid,
                            'ask': ask,
                            'spread': ask - bid,
                            'timestamp': datetime.fromtimestamp(timestamp),
                            'technical_indicators': technical_data
                        }
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 獲取實時數據摘要失敗: {e}")
            return {}
    
    def get_sync_status_summary(self) -> Dict[str, Any]:
        """獲取同步狀態摘要"""
        try:
            active_pairs = []
            syncing_pairs = []
            error_pairs = []
            
            for pair, status in self.sync_status.items():
                if status.sync_status == 'synced':
                    active_pairs.append(pair)
                elif status.sync_status == 'syncing':
                    syncing_pairs.append(pair)
                elif status.sync_status == 'error':
                    error_pairs.append(pair)
            
            return {
                'total_pairs': len(self.sync_status),
                'active_pairs': active_pairs,
                'syncing_pairs': syncing_pairs,
                'error_pairs': error_pairs,
                'active_count': len(active_pairs),
                'syncing_count': len(syncing_pairs),
                'error_count': len(error_pairs),
                'is_running': self.is_running,
                'database_path': str(self.db_path)
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取同步狀態摘要失敗: {e}")
            return {}
    
    async def stop_data_streams(self):
        """停止所有數據流"""
        logger.info("🛑 停止多交易對數據流...")
        self.is_running = False
        
        # 等待所有任務完成
        await asyncio.sleep(2)
        
        # 關閉線程池
        self.executor.shutdown(wait=True)
        
        logger.info("✅ 數據流已停止")
    
    async def close(self):
        """關閉數據管理系統"""
        try:
            await self.stop_data_streams()
            await self.max_client.close()
            logger.info("✅ 多交易對數據管理系統已關閉")
        except Exception as e:
            logger.error(f"❌ 關閉數據管理系統失敗: {e}")


# 創建全局多交易對數據管理器實例
def create_multi_pair_data_manager() -> MultiPairDataManager:
    """創建多交易對數據管理器實例"""
    return MultiPairDataManager()


# 測試代碼
if __name__ == "__main__":
    async def test_multi_pair_data_manager():
        """測試多交易對數據管理器"""
        print("🧪 測試多交易對數據管理器...")
        
        manager = create_multi_pair_data_manager()
        
        try:
            # 獲取同步狀態
            status = manager.get_sync_status_summary()
            print(f"📊 同步狀態: {status}")
            
            # 測試歷史數據獲取
            print("📚 測試歷史數據獲取...")
            historical_data = manager.get_multi_pair_historical_data(
                pairs=['BTCTWD', 'ETHTWD'], 
                timeframe='5m', 
                limit=10
            )
            
            for pair, df in historical_data.items():
                print(f"   {pair}: {len(df)} 條歷史記錄")
            
            # 測試實時數據摘要
            print("📡 測試實時數據摘要...")
            real_time_summary = manager.get_real_time_data_summary()
            
            for pair, data in real_time_summary.items():
                print(f"   {pair}: {data['price']:.0f} TWD")
            
            print("✅ 多交易對數據管理器測試完成")
            
        finally:
            await manager.close()
    
    # 運行測試
    asyncio.run(test_multi_pair_data_manager())