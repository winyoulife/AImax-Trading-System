#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
訓練數據提取器 - 從歷史資料庫提取適合機器學習的訓練數據
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import sqlite3

from ..data.historical_data_manager import create_historical_manager
from ..data.technical_indicators import create_technical_calculator

logger = logging.getLogger(__name__)

class TrainingDataExtractor:
    """訓練數據提取器"""
    
    def __init__(self, db_path: str = "data/market_history.db"):
        """
        初始化訓練數據提取器
        
        Args:
            db_path: 歷史數據庫路徑
        """
        self.db_path = Path(db_path)
        self.historical_manager = create_historical_manager(str(db_path))
        self.technical_calculator = create_technical_calculator()
        
        # 特徵配置
        self.feature_config = {
            'price_features': ['open', 'high', 'low', 'close', 'volume'],
            'technical_features': [
                'rsi_14', 'rsi_7', 'rsi_21',
                'sma_5', 'sma_10', 'sma_20', 'sma_50',
                'ema_12', 'ema_26',
                'macd', 'macd_signal', 'macd_histogram',
                'bb_upper', 'bb_middle', 'bb_lower', 'bb_width',
                'volume_sma_20', 'volume_ratio'
            ],
            'derived_features': [
                'price_change_1', 'price_change_5', 'price_change_15',
                'volume_change_1', 'volume_change_5',
                'volatility_5', 'volatility_20',
                'momentum_5', 'momentum_10'
            ]
        }
        
        logger.info("🔧 訓練數據提取器初始化完成")
    
    async def extract_training_dataset(self, 
                                     market: str = "btctwd",
                                     days: int = 30,
                                     timeframe: str = "5m") -> Optional[pd.DataFrame]:
        """
        提取完整的訓練數據集
        
        Args:
            market: 交易對
            days: 提取天數
            timeframe: 時間框架
            
        Returns:
            包含特徵和標籤的完整數據集
        """
        try:
            logger.info(f"🚀 開始提取訓練數據集: {market}, {days}天, {timeframe}")
            
            # 步驟1: 確保歷史數據完整性
            await self.historical_manager.ensure_historical_data(market, [timeframe])
            
            # 步驟2: 獲取原始歷史數據
            raw_data = self._get_raw_historical_data(market, timeframe, days)
            if raw_data is None or raw_data.empty:
                logger.error("❌ 無法獲取原始歷史數據")
                return None
            
            # 步驟3: 計算技術指標
            enhanced_data = self._calculate_technical_features(raw_data)
            
            # 步驟4: 生成衍生特徵
            feature_data = self._generate_derived_features(enhanced_data)
            
            # 步驟5: 創建訓練標籤
            labeled_data = self._create_training_labels(feature_data)
            
            # 步驟6: 數據清洗和驗證
            clean_data = self._clean_and_validate_data(labeled_data)
            
            logger.info(f"✅ 訓練數據集提取完成: {len(clean_data)} 條記錄")
            return clean_data
            
        except Exception as e:
            logger.error(f"❌ 提取訓練數據集失敗: {e}")
            return None
    
    def _get_raw_historical_data(self, market: str, timeframe: str, days: int) -> Optional[pd.DataFrame]:
        """獲取原始歷史數據"""
        try:
            # 計算需要的數據量
            periods_per_day = {
                '1m': 1440,
                '5m': 288,
                '1h': 24,
                '1d': 1
            }
            
            limit = periods_per_day.get(timeframe, 288) * days
            
            # 從數據庫獲取數據
            df = self.historical_manager.get_historical_data(market, timeframe, limit)
            
            if df is None or df.empty:
                logger.warning(f"⚠️ 無法從數據庫獲取 {market} {timeframe} 數據")
                return None
            
            logger.info(f"📊 獲取原始數據: {len(df)} 條記錄")
            return df
            
        except Exception as e:
            logger.error(f"❌ 獲取原始歷史數據失敗: {e}")
            return None
    
    def _calculate_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """計算技術指標特徵"""
        try:
            logger.info("🔢 計算技術指標特徵...")
            
            enhanced_df = df.copy()
            
            # RSI指標
            for period in [7, 14, 21]:
                enhanced_df[f'rsi_{period}'] = self._calculate_rsi(df['close'], period)
            
            # 移動平均線
            for period in [5, 10, 20, 50]:
                enhanced_df[f'sma_{period}'] = df['close'].rolling(period).mean()
            
            # 指數移動平均線
            enhanced_df['ema_12'] = df['close'].ewm(span=12).mean()
            enhanced_df['ema_26'] = df['close'].ewm(span=26).mean()
            
            # MACD
            macd_line = enhanced_df['ema_12'] - enhanced_df['ema_26']
            macd_signal = macd_line.ewm(span=9).mean()
            enhanced_df['macd'] = macd_line
            enhanced_df['macd_signal'] = macd_signal
            enhanced_df['macd_histogram'] = macd_line - macd_signal
            
            # 布林帶
            sma_20 = enhanced_df['sma_20']
            std_20 = df['close'].rolling(20).std()
            enhanced_df['bb_upper'] = sma_20 + (std_20 * 2)
            enhanced_df['bb_middle'] = sma_20
            enhanced_df['bb_lower'] = sma_20 - (std_20 * 2)
            enhanced_df['bb_width'] = enhanced_df['bb_upper'] - enhanced_df['bb_lower']
            
            # 成交量指標
            enhanced_df['volume_sma_20'] = df['volume'].rolling(20).mean()
            enhanced_df['volume_ratio'] = df['volume'] / enhanced_df['volume_sma_20']
            
            logger.info(f"✅ 技術指標計算完成，新增 {len(enhanced_df.columns) - len(df.columns)} 個特徵")
            return enhanced_df
            
        except Exception as e:
            logger.error(f"❌ 計算技術指標失敗: {e}")
            return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """計算RSI指標"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            logger.error(f"❌ 計算RSI失敗: {e}")
            return pd.Series(index=prices.index, dtype=float)
    
    def _generate_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成衍生特徵"""
        try:
            logger.info("🔄 生成衍生特徵...")
            
            enhanced_df = df.copy()
            
            # 價格變化特徵
            for period in [1, 5, 15]:
                enhanced_df[f'price_change_{period}'] = df['close'].pct_change(period)
            
            # 成交量變化特徵
            for period in [1, 5]:
                enhanced_df[f'volume_change_{period}'] = df['volume'].pct_change(period)
            
            # 波動率特徵
            for period in [5, 20]:
                returns = df['close'].pct_change()
                enhanced_df[f'volatility_{period}'] = returns.rolling(period).std()
            
            # 動量特徵
            for period in [5, 10]:
                enhanced_df[f'momentum_{period}'] = df['close'] / df['close'].shift(period) - 1
            
            # 價格位置特徵
            enhanced_df['price_position_bb'] = (df['close'] - enhanced_df['bb_lower']) / (enhanced_df['bb_upper'] - enhanced_df['bb_lower'])
            enhanced_df['price_vs_sma20'] = df['close'] / enhanced_df['sma_20'] - 1
            
            # 時間特徵
            enhanced_df['hour'] = df['timestamp'].dt.hour
            enhanced_df['day_of_week'] = df['timestamp'].dt.dayofweek
            enhanced_df['is_weekend'] = (df['timestamp'].dt.dayofweek >= 5).astype(int)
            
            logger.info(f"✅ 衍生特徵生成完成，新增 {len(enhanced_df.columns) - len(df.columns)} 個特徵")
            return enhanced_df
            
        except Exception as e:
            logger.error(f"❌ 生成衍生特徵失敗: {e}")
            return df
    
    def _create_training_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """創建訓練標籤"""
        try:
            logger.info("🏷️ 創建訓練標籤...")
            
            labeled_df = df.copy()
            
            # 未來收益率（用於回歸）
            for horizon in [1, 3, 5, 10]:
                labeled_df[f'future_return_{horizon}'] = df['close'].shift(-horizon) / df['close'] - 1
            
            # 交易信號（用於分類）
            future_return_5 = labeled_df['future_return_5']
            
            # 三分類：買入(1)、持有(0)、賣出(-1)
            buy_threshold = 0.002   # 0.2%
            sell_threshold = -0.002 # -0.2%
            
            labeled_df['signal_3class'] = np.where(
                future_return_5 > buy_threshold, 1,
                np.where(future_return_5 < sell_threshold, -1, 0)
            )
            
            # 二分類：買入(1)、不買入(0)
            labeled_df['signal_binary'] = (future_return_5 > buy_threshold).astype(int)
            
            # 風險標籤
            volatility_5 = labeled_df['volatility_5']
            high_vol_threshold = volatility_5.quantile(0.8)
            labeled_df['high_risk'] = (volatility_5 > high_vol_threshold).astype(int)
            
            logger.info("✅ 訓練標籤創建完成")
            return labeled_df
            
        except Exception as e:
            logger.error(f"❌ 創建訓練標籤失敗: {e}")
            return df
    
    def _clean_and_validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """數據清洗和驗證"""
        try:
            logger.info("🧹 數據清洗和驗證...")
            
            # 移除無效數據
            clean_df = df.copy()
            
            # 移除包含未來數據的最後幾行
            clean_df = clean_df[:-10]
            
            # 移除無限值和NaN
            clean_df = clean_df.replace([np.inf, -np.inf], np.nan)
            
            # 記錄清洗前的數據量
            original_count = len(clean_df)
            
            # 移除包含NaN的行
            clean_df = clean_df.dropna()
            
            # 移除異常值（使用IQR方法）
            numeric_columns = clean_df.select_dtypes(include=[np.number]).columns
            for col in numeric_columns:
                if col not in ['signal_3class', 'signal_binary', 'high_risk', 'hour', 'day_of_week', 'is_weekend']:
                    Q1 = clean_df[col].quantile(0.01)
                    Q3 = clean_df[col].quantile(0.99)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    clean_df = clean_df[(clean_df[col] >= lower_bound) & (clean_df[col] <= upper_bound)]
            
            cleaned_count = len(clean_df)
            removed_count = original_count - cleaned_count
            
            logger.info(f"✅ 數據清洗完成: 移除 {removed_count} 條異常數據，保留 {cleaned_count} 條")
            
            # 數據質量報告
            self._generate_data_quality_report(clean_df)
            
            return clean_df
            
        except Exception as e:
            logger.error(f"❌ 數據清洗失敗: {e}")
            return df
    
    def _generate_data_quality_report(self, df: pd.DataFrame):
        """生成數據質量報告"""
        try:
            logger.info("📊 生成數據質量報告...")
            
            # 基本統計
            total_records = len(df)
            feature_count = len([col for col in df.columns if col not in ['timestamp']])
            
            # 標籤分佈
            if 'signal_3class' in df.columns:
                signal_dist = df['signal_3class'].value_counts()
                logger.info(f"信號分佈 - 買入: {signal_dist.get(1, 0)}, 持有: {signal_dist.get(0, 0)}, 賣出: {signal_dist.get(-1, 0)}")
            
            # 時間範圍
            if 'timestamp' in df.columns:
                start_time = df['timestamp'].min()
                end_time = df['timestamp'].max()
                logger.info(f"時間範圍: {start_time} 到 {end_time}")
            
            logger.info(f"📈 數據質量報告: {total_records} 條記錄, {feature_count} 個特徵")
            
        except Exception as e:
            logger.error(f"❌ 生成數據質量報告失敗: {e}")
    
    def get_feature_names(self) -> List[str]:
        """獲取所有特徵名稱"""
        all_features = []
        all_features.extend(self.feature_config['price_features'])
        all_features.extend(self.feature_config['technical_features'])
        all_features.extend(self.feature_config['derived_features'])
        
        # 添加額外的衍生特徵
        all_features.extend([
            'price_position_bb', 'price_vs_sma20',
            'hour', 'day_of_week', 'is_weekend'
        ])
        
        return all_features
    
    def save_training_data(self, df: pd.DataFrame, filename: str = None) -> str:
        """保存訓練數據"""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"training_data_{timestamp}.csv"
            
            output_path = Path("AImax/data") / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            df.to_csv(output_path, index=False)
            
            logger.info(f"💾 訓練數據已保存: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ 保存訓練數據失敗: {e}")
            return ""


# 創建全局實例
def create_training_data_extractor(db_path: str = "data/market_history.db") -> TrainingDataExtractor:
    """創建訓練數據提取器實例"""
    return TrainingDataExtractor(db_path)


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_training_data_extractor():
        """測試訓練數據提取器"""
        print("🧪 測試訓練數據提取器...")
        
        extractor = create_training_data_extractor()
        
        try:
            # 提取訓練數據
            training_data = await extractor.extract_training_dataset(
                market="btctwd",
                days=7,  # 測試用較少天數
                timeframe="5m"
            )
            
            if training_data is not None:
                print(f"✅ 訓練數據提取成功: {len(training_data)} 條記錄")
                print(f"📊 特徵數量: {len(training_data.columns)}")
                print(f"🏷️ 標籤列: {[col for col in training_data.columns if 'signal' in col or 'future' in col or 'risk' in col]}")
                
                # 保存數據
                saved_path = extractor.save_training_data(training_data, "test_training_data.csv")
                print(f"💾 數據已保存到: {saved_path}")
                
            else:
                print("❌ 訓練數據提取失敗")
                
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
    
    # 運行測試
    asyncio.run(test_training_data_extractor())