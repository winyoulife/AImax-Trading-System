#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多時間週期獨立確認MACD交易信號檢測系統
1小時使用MACD金叉/死叉，其他時間週期使用動態追蹤價格邏輯
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging
import numpy as np

logger = logging.getLogger(__name__)

class MultiTimeframePositionTracker:
    """多時間週期策略持倉狀態追蹤器"""
    
    def __init__(self):
        self.reset_all_states()
        
    def reset_all_states(self):
        """重置所有狀態"""
        self.current_position = 0  # 0=空倉, 1=持倉
        self.trade_sequence = 0    # 當前交易序號
        self.buy_count = 0         # 總買進次數
        self.sell_count = 0        # 總賣出次數
        self.trade_pairs = []      # 完整交易對
        self.open_trades = []      # 未平倉交易
        self.trade_history = []    # 完整交易歷史
        
        # 多時間週期策略相關
        self.hourly_signal = None  # 1小時MACD信號
        self.waiting_for_confirmation = False  # 是否等待短時間週期確認
        self.confirmation_start_time = None    # 確認開始時間
        self.confirmation_timeout_hours = 2    # 確認超時時間（小時）
        self.pending_signal_type = None        # 待確認的信號類型
        self.pending_signal_price = None       # 待確認的信號價格
        
        # 動態追蹤相關（用於30分、15分、5分）
        self.dynamic_buy_price = None          # 動態買進基準價
        self.dynamic_sell_price = None         # 動態賣出基準價
        self.is_observing = False              # 是否在觀察期
        
        # 條件顯示邏輯追蹤
        self.hourly_trigger_time = None        # 1小時觸發時間
        self.short_timeframe_display_status = {
            '30m': {'active': False, 'start_time': None, 'confirmed': False},
            '15m': {'active': False, 'start_time': None, 'confirmed': False},
            '5m': {'active': False, 'start_time': None, 'confirmed': False}
        }
        
    def can_buy(self) -> bool:
        """檢查是否可以買進"""
        return self.current_position == 0
    
    def can_sell(self) -> bool:
        """檢查是否可以賣出"""
        return self.current_position == 1
    
    def set_reference_point(self, signal_type: str, price: float, hourly_signal: str, trigger_time: datetime):
        """設置1小時基準點（不影響持倉狀態）"""
        self.waiting_for_confirmation = True
        self.confirmation_start_time = datetime.now()
        self.pending_signal_type = signal_type
        self.pending_signal_price = price  # 這是1小時基準點
        self.hourly_signal = hourly_signal
        self.hourly_trigger_time = trigger_time
        
        # 初始化30分鐘追蹤價格（用於顯示追蹤過程）
        if signal_type == 'buy':
            self.dynamic_buy_price = price  # 從基準點開始追蹤最低點
            self.dynamic_sell_price = None
        else:
            self.dynamic_sell_price = price  # 從基準點開始追蹤最高點
            self.dynamic_buy_price = None
        
        self.is_observing = True
        
        logger.info(f"🎯 設置1小時{signal_type}基準點: {price:,.0f} TWD")
        logger.info(f"   觸發時間: {trigger_time}")
        logger.info(f"   30分鐘開始根據基準點進行買賣判斷")
    
    def update_tracking_price(self, current_price: float, signal_type: str):
        """更新追蹤價格（最低點/最高點）- 供所有時間框架使用"""
        if signal_type == 'buy':
            # 買進：持續更新最低點
            if self.dynamic_buy_price is None or current_price < self.dynamic_buy_price:
                self.dynamic_buy_price = current_price
                logger.debug(f"更新追蹤最低點: {current_price:,.0f}")
        else:
            # 賣出：持續更新最高點
            if self.dynamic_sell_price is None or current_price > self.dynamic_sell_price:
                self.dynamic_sell_price = current_price
                logger.debug(f"更新追蹤最高點: {current_price:,.0f}")
    
    def get_current_tracking_price(self, signal_type: str) -> Optional[float]:
        """獲取當前追蹤價格"""
        if signal_type == 'buy':
            return self.dynamic_buy_price
        else:
            return self.dynamic_sell_price
    
    def check_30m_trigger(self, current_price: float, signal_type: str) -> bool:
        """檢查30分鐘觸發條件 - 使用1小時基準點比較法"""
        if not self.is_observing or self.pending_signal_price is None:
            logger.debug(f"未在觀察期或無基準價格，跳過觸發檢查: is_observing={self.is_observing}, pending_signal_price={self.pending_signal_price}")
            return False
        
        if signal_type == 'buy':
            # 買進：30分鐘價格 > 1小時基準點就立即買入
            if current_price > self.pending_signal_price:
                logger.info(f"🎯 30分買進觸發: 當前價格 {current_price:,.0f} > 1小時基準點 {self.pending_signal_price:,.0f}")
                return True
            else:
                logger.debug(f"30分買進未觸發: 當前價格 {current_price:,.0f} <= 1小時基準點 {self.pending_signal_price:,.0f}")
        else:
            # 賣出：30分鐘價格 < 1小時基準點就立即賣出
            if current_price < self.pending_signal_price:
                logger.info(f"🎯 30分賣出觸發: 當前價格 {current_price:,.0f} < 1小時基準點 {self.pending_signal_price:,.0f}")
                return True
            else:
                logger.debug(f"30分賣出未觸發: 當前價格 {current_price:,.0f} >= 1小時基準點 {self.pending_signal_price:,.0f}")
        
        return False
    
    def is_confirmation_timeout(self) -> bool:
        """檢查確認是否超時"""
        if not self.waiting_for_confirmation or self.confirmation_start_time is None:
            return False
        
        elapsed = datetime.now() - self.confirmation_start_time
        return elapsed.total_seconds() / 3600 >= self.confirmation_timeout_hours
    
    def execute_30m_buy(self, timestamp: datetime, price: float) -> int:
        """執行30分鐘買進交易（獨立於1小時持倉狀態）"""
        # 30分鐘買進只需要檢查當前是否空倉
        if self.current_position == 1:
            logger.warning("無法買進：當前已有持倉")
            return 0
        
        self.trade_sequence += 1
        self.current_position = 1  # 30分鐘買進後設置為持倉
        self.buy_count += 1
        
        trade = {
            'sequence': self.trade_sequence,
            'type': 'buy',
            'timestamp': timestamp,
            'price': price,
            'timeframe': '30m',
            'reference_price': self.pending_signal_price,  # 記錄1小時基準點
            'hourly_signal': self.hourly_signal
        }
        
        self.open_trades.append(trade)
        self.trade_history.append(trade)
        
        # 注意：不清除基準點狀態，因為每個基準點獨立處理
        
        logger.info(f"✅ 30分鐘買進交易 #{self.trade_sequence}: 價格 {price:,.0f}")
        return self.trade_sequence
    
    def execute_30m_sell(self, timestamp: datetime, price: float) -> int:
        """執行30分鐘賣出交易（獨立於1小時持倉狀態）"""
        # 30分鐘賣出只需要檢查當前是否持倉
        if self.current_position == 0:
            logger.warning("無法賣出：當前無持倉")
            return 0
        
        self.trade_sequence += 1
        self.current_position = 0  # 30分鐘賣出後設置為空倉
        self.sell_count += 1
        
        # 找到對應的買進交易
        buy_trade = None
        profit = 0  # 初始化profit變量
        
        for trade in self.open_trades:
            if trade['type'] == 'buy':
                buy_trade = trade
                break
        
        if buy_trade:
            self.open_trades.remove(buy_trade)
            
            # 計算利潤
            profit = price - buy_trade['price']
            
            # 創建交易對
            trade_pair = {
                'buy_sequence': buy_trade['sequence'],
                'sell_sequence': self.trade_sequence,
                'buy_price': buy_trade['price'],
                'sell_price': price,
                'profit': profit,
                'buy_time': buy_trade['timestamp'],
                'sell_time': timestamp,
                'buy_timeframe': '30m',
                'sell_timeframe': '30m',
                'hourly_signal': buy_trade['hourly_signal']
            }
            
            self.trade_pairs.append(trade_pair)
        
        trade = {
            'sequence': self.trade_sequence,
            'type': 'sell',
            'timestamp': timestamp,
            'price': price,
            'timeframe': '30m',
            'reference_price': self.pending_signal_price,  # 記錄1小時基準點
            'hourly_signal': self.hourly_signal
        }
        
        self.trade_history.append(trade)
        
        # 注意：不清除基準點狀態，因為每個基準點獨立處理
        
        logger.info(f"✅ 30分鐘賣出交易 #{self.trade_sequence}: 價格 {price:,.0f}, 利潤 {profit:,.0f}")
        return self.trade_sequence
    
    def get_status(self) -> Dict:
        """獲取當前狀態"""
        return {
            'current_position': self.current_position,
            'trade_sequence': self.trade_sequence,
            'buy_count': self.buy_count,
            'sell_count': self.sell_count,
            'waiting_for_confirmation': self.waiting_for_confirmation,
            'pending_signal_type': self.pending_signal_type,
            'pending_signal_price': self.pending_signal_price,
            'is_observing': self.is_observing,
            'dynamic_buy_price': self.dynamic_buy_price,
            'dynamic_sell_price': self.dynamic_sell_price,
            'hourly_signal': self.hourly_signal
        }
    
    def confirm_short_timeframe_trade(self, timeframe: str, confirm_time: datetime = None):
        """確認短時間框架交易完成，停止該時間框架的數據顯示"""
        if timeframe in self.short_timeframe_display_status:
            self.short_timeframe_display_status[timeframe]['confirmed'] = True
            self.short_timeframe_display_status[timeframe]['active'] = False
            self.short_timeframe_display_status[timeframe]['confirm_time'] = confirm_time  # 記錄確認時間
            logger.info(f"✅ {timeframe}時間框架交易完成，停止數據顯示，確認時間: {confirm_time}")
            
            # 注意：不需要等待所有時間框架都完成
            # 任何一個時間框架確認交易後，該時間框架就停止顯示
            # 其他時間框架繼續等待確認，直到有其他時間框架觸發或超時
    
    def should_display_timeframe_data(self, timeframe: str, data_time: datetime) -> bool:
        """
        判斷是否應該顯示指定時間框架的數據
        
        條件顯示邏輯：
        - 當1小時觸發買入/賣出信號時：短時間框架開始顯示數據
        - 當短時間框架確認交易完成時：該時間框架停止顯示數據
        - 等待下一個1小時觸發信號
        
        Args:
            timeframe: 時間框架 ('30m', '15m', '5m')
            data_time: 數據時間戳
        
        Returns:
            bool: 是否應該顯示該數據
        """
        # 顯示所有數據，就像1小時表格一樣
        return True
        
        if timeframe not in self.short_timeframe_display_status:
            logger.debug(f"{timeframe}: 不在短時間框架列表中")
            return False
        
        status = self.short_timeframe_display_status[timeframe]
        
        # 如果該時間框架未激活，不顯示
        if not status['active']:
            logger.debug(f"{timeframe}: 未激活 (active=False)")
            return False
        
        # 如果該時間框架已確認交易完成，不顯示
        if status['confirmed']:
            logger.debug(f"{timeframe}: 已確認交易完成 (confirmed=True)")
            return False
        
        # 如果沒有開始時間，不顯示
        if status['start_time'] is None:
            logger.debug(f"{timeframe}: 沒有開始時間 (start_time=None)")
            return False
        
        # 只顯示從1小時觸發時間點開始的數據
        should_show = data_time >= status['start_time']
        
        if not should_show:
            logger.debug(f"{timeframe}: 數據時間 {data_time} < 開始時間 {status['start_time']}")
        else:
            logger.debug(f"{timeframe}: 顯示數據 {data_time} (>= {status['start_time']})")
        
        return should_show

class MultiTimeframeSignalValidator:
    """多時間週期策略信號驗證器"""
    
    @staticmethod
    def validate_hourly_buy_signal(current_row: pd.Series, previous_row: pd.Series) -> bool:
        """
        驗證1小時MACD買進信號（金叉）
        
        條件:
        1. MACD柱為負 (macd_hist < 0)
        2. MACD線突破信號線向上 (前一時點 macd <= signal，當前時點 macd > signal)
        3. MACD線為負 (macd < 0)
        4. 信號線為負 (signal < 0)
        """
        if previous_row is None:
            return False
        
        try:
            # 基本MACD條件
            basic_conditions = (
                previous_row['macd_hist'] < 0 and  # MACD柱為負
                previous_row['macd'] <= previous_row['macd_signal'] and  # 前一時點MACD <= 信號線
                current_row['macd'] > current_row['macd_signal']  # 當前MACD > 信號線
            )
            
            # 新增的負值條件
            negative_conditions = (
                current_row['macd'] < 0 and  # MACD線為負
                current_row['macd_signal'] < 0  # 信號線為負
            )
            
            result = basic_conditions and negative_conditions
            
            if result:
                logger.debug(f"1小時買進信號驗證通過: MACD={current_row['macd']:.1f}, 信號={current_row['macd_signal']:.1f}, 柱={current_row['macd_hist']:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"1小時買進信號驗證失敗: {e}")
            return False
    
    @staticmethod
    def validate_hourly_sell_signal(current_row: pd.Series, previous_row: pd.Series) -> bool:
        """
        驗證1小時MACD賣出信號（死叉）
        
        條件:
        1. MACD柱為正 (macd_hist > 0)
        2. 信號線突破MACD線向上 (前一時點 macd >= signal，當前時點 signal > macd)
        3. MACD線為正 (macd > 0)
        4. 信號線為正 (signal > 0)
        """
        if previous_row is None:
            return False
        
        try:
            # 基本MACD條件
            basic_conditions = (
                previous_row['macd_hist'] > 0 and  # MACD柱為正
                previous_row['macd'] >= previous_row['macd_signal'] and  # 前一時點MACD >= 信號線
                current_row['macd_signal'] > current_row['macd']  # 當前信號線 > MACD
            )
            
            # 新增的正值條件
            positive_conditions = (
                current_row['macd'] > 0 and  # MACD線為正
                current_row['macd_signal'] > 0  # 信號線為正
            )
            
            result = basic_conditions and positive_conditions
            
            if result:
                logger.debug(f"1小時賣出信號驗證通過: MACD={current_row['macd']:.1f}, 信號={current_row['macd_signal']:.1f}, 柱={current_row['macd_hist']:.1f}")
            
            return result
            
        except Exception as e:
            logger.error(f"1小時賣出信號驗證失敗: {e}")
            return False

class MultiTimeframeSignalDetectionEngine:
    """多時間週期策略信號檢測引擎"""
    
    def __init__(self, confirmation_timeout_hours: int = 2):
        self.tracker = MultiTimeframePositionTracker()
        self.tracker.confirmation_timeout_hours = confirmation_timeout_hours
        self.validator = MultiTimeframeSignalValidator()
        
        # 確保從乾淨的狀態開始
        self.tracker.reset_all_states()
        logger.info(f"初始化多時間框架信號檢測引擎，狀態已重置: waiting_for_confirmation={self.tracker.waiting_for_confirmation}")
        
    def detect_signals(self, hourly_df: pd.DataFrame, timeframe_dfs: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """檢測多時間週期策略信號"""
        logger.info(f"🎯 開始檢測多時間週期信號，1小時數據: {len(hourly_df)} 筆")
        signals = {
            '1h': [],
            '30m': [],
            '15m': [],
            '5m': []
        }
        
        # 處理1小時數據 - 需要順序處理每個信號
        hourly_signals_to_process = []
        
        # 重置tracker狀態，確保從乾淨狀態開始
        self.tracker.reset_all_states()
        
        # 首先收集所有有效的1小時信號（不被忽略的）
        for i, row in hourly_df.iterrows():
            previous_row = hourly_df.iloc[i-1] if i > 0 else None
            
            # 檢查1小時MACD買進信號
            if self.validator.validate_hourly_buy_signal(row, previous_row):
                # 檢查是否可以買進（不在持倉狀態）
                if self.tracker.can_buy():
                    hourly_signals_to_process.append({
                        'datetime': row['datetime'],
                        'close': row['close'],
                        'signal_type': 'buy',
                        'hourly_signal': f"1小時MACD金叉: {row['macd_hist']:.2f}",
                        'macd_hist': row['macd_hist'],
                        'macd': row['macd'],
                        'macd_signal': row['macd_signal']
                    })
                    # 模擬執行買進，更新持倉狀態
                    self.tracker.current_position = 1
                
            elif self.validator.validate_hourly_sell_signal(row, previous_row):
                # 檢查是否可以賣出（在持倉狀態）
                if self.tracker.can_sell():
                    hourly_signals_to_process.append({
                        'datetime': row['datetime'],
                        'close': row['close'],
                        'signal_type': 'sell',
                        'hourly_signal': f"1小時MACD死叉: {row['macd_hist']:.2f}",
                        'macd_hist': row['macd_hist'],
                        'macd': row['macd'],
                        'macd_signal': row['macd_signal']
                    })
                    # 模擬執行賣出，更新持倉狀態
                    self.tracker.current_position = 0
        
        logger.info(f"收集到 {len(hourly_signals_to_process)} 個1小時信號")
        
        # 按時間順序排序1小時信號
        hourly_signals_to_process.sort(key=lambda x: x['datetime'])
        
        # 順序處理每個1小時信號，買賣成對編號
        pair_sequence = 1  # 交易對序號從1開始
        
        for hourly_signal in hourly_signals_to_process:
            # 添加1小時信號到結果中
            signals['1h'].append({
                'datetime': hourly_signal['datetime'],
                'close': hourly_signal['close'],
                'signal_type': hourly_signal['signal_type'],
                'trade_sequence': 0,  # 1小時不直接執行交易
                'timeframe': '1h',
                'hourly_signal': hourly_signal['hourly_signal'],
                'macd_hist': hourly_signal['macd_hist'],
                'macd': hourly_signal['macd'],
                'macd_signal': hourly_signal['macd_signal']
            })
            
            # 不在這裡添加基準點信號，等到統一追蹤邏輯中找到真正觸發點時再添加
            # 只記錄序號信息供後續使用
            signal_type_text = '買' if hourly_signal['signal_type'] == 'buy' else '賣'
            
            # 買進信號：使用當前pair_sequence，然後遞增
            # 賣出信號：使用當前pair_sequence，不遞增（與前面的買進配對）
            if hourly_signal['signal_type'] == 'buy':
                current_sequence = pair_sequence
                pair_sequence += 1  # 買進後遞增，準備下一對
            else:
                current_sequence = pair_sequence - 1  # 賣出使用前一個序號（與買進配對）
            
            # 將序號信息添加到hourly_signal中，供統一追蹤邏輯使用
            hourly_signal['sequence'] = current_sequence
            
            logger.info(f"準備搜索1小時{signal_type_text}{current_sequence}基準點觸發時機")
            
            # 暫時不在這裡處理30分鐘追蹤，改為統一處理
        
        # 統一處理30分鐘追蹤邏輯
        try:
            logger.info(f"🚀 準備調用統一追蹤邏輯，timeframe_dfs keys: {list(timeframe_dfs.keys())}")
            self._process_30m_unified_tracking(timeframe_dfs, signals, hourly_signals_to_process)
            logger.info(f"✅ 統一追蹤邏輯執行完成")
        except Exception as e:
            logger.error(f"❌ 統一追蹤邏輯執行失敗: {e}")
            import traceback
            traceback.print_exc()
        
        # 處理15分鐘時間框架 - 使用30分鐘追蹤結果作為基準
        if '15m' in timeframe_dfs and not timeframe_dfs['15m'].empty:
            self._process_15m_with_30m_tracking(timeframe_dfs['15m'], signals, hourly_signals_to_process)
        
        # 處理5分鐘時間框架 - 完全獨立，複製30分鐘邏輯
        if '5m' in timeframe_dfs and not timeframe_dfs['5m'].empty:
            self._process_5m_independent_tracking(timeframe_dfs['5m'], signals, hourly_signals_to_process)
        
        # 轉換為DataFrame並返回
        result = {}
        for timeframe, signal_list in signals.items():
            result[timeframe] = pd.DataFrame(signal_list) if signal_list else pd.DataFrame()
        
        return result
    
    # 舊的追蹤方法已移除，使用統一追蹤邏輯
    
    def _process_30m_unified_tracking(self, timeframe_dfs: Dict[str, pd.DataFrame], signals: Dict[str, List], hourly_signals: List):
        """1小時MA動態判斷策略處理"""
        if '30m' not in timeframe_dfs or timeframe_dfs['30m'] is None or timeframe_dfs['30m'].empty:
            logger.warning("1小時MA數據為空，跳過MA策略處理")
            return
        
        df_1h_ma = timeframe_dfs['30m']  # 實際是1小時MA數據
        df_sorted = df_1h_ma.sort_values('datetime').reset_index(drop=True)
        
        # 為1小時MA策略創建獨立的持倉狀態
        ma_position = 0  # 0=空倉, 1=持倉
        ma_trade_sequence = 0
        
        logger.info(f"🔥 開始1小時MA動態判斷處理，共 {len(df_sorted)} 筆1小時數據")
        
        for i, row in df_sorted.iterrows():
            current_time = row['datetime']
            current_price = row['close']
            
            # 檢查是否有MA數據
            if 'ma9' not in row or pd.isna(row['ma9']) or pd.isna(row['ma25']) or pd.isna(row['ma99']):
                # 沒有MA數據，添加等待信號
                signals['30m'].append({
                    'datetime': current_time,
                    'close': current_price,
                    'signal_type': 'waiting',
                    'trade_sequence': 0,
                    'timeframe': '30m',
                    'hourly_signal': '⏳ 等待MA數據',
                    'macd_hist': 0,
                    'macd': 0,
                    'macd_signal': 0,
                    'is_waiting': True,
                    'ma9': 0,
                    'ma25': 0,
                    'ma99': 0
                })
                continue
            
            ma9 = row['ma9']
            ma25 = row['ma25']
            ma99 = row['ma99']
            
            # 1小時MA動態判斷邏輯
            trigger_result, tracking_signal, signal_type = self._process_1h_ma_strategy(
                current_time, current_price, ma9, ma25, ma99, i, df_sorted
            )
            
            # 處理交易信號 - 使用獨立的持倉狀態
            if trigger_result:
                if signal_type == 'buy' and ma_position == 0:
                    # 執行買進
                    ma_trade_sequence += 1
                    ma_position = 1  # 設置為持倉
                    signals['30m'].append({
                        'datetime': current_time,
                        'close': current_price,
                        'signal_type': 'buy',
                        'trade_sequence': ma_trade_sequence,
                        'timeframe': '30m',
                        'hourly_signal': f'🟢 1小時MA買{ma_trade_sequence}: {tracking_signal}',
                        'macd_hist': 0,
                        'macd': 0,
                        'macd_signal': 0,
                        'is_confirmed': True,
                        'ma9': ma9,
                        'ma25': ma25,
                        'ma99': ma99
                    })
                    logger.info(f"1小時MA買入交易完成: 買{ma_trade_sequence} - {tracking_signal}")
                    
                elif signal_type == 'sell' and ma_position == 1:
                    # 執行賣出 - 使用相同的序號（與買進配對）
                    ma_position = 0  # 設置為空倉
                    signals['30m'].append({
                        'datetime': current_time,
                        'close': current_price,
                        'signal_type': 'sell',
                        'trade_sequence': ma_trade_sequence,  # 使用當前序號（與買進配對）
                        'timeframe': '30m',
                        'hourly_signal': f'🔴 1小時MA賣{ma_trade_sequence}: {tracking_signal}',
                        'macd_hist': 0,
                        'macd': 0,
                        'macd_signal': 0,
                        'is_confirmed': True,
                        'ma9': ma9,
                        'ma25': ma25,
                        'ma99': ma99
                    })
                    logger.info(f"1小時MA賣出交易完成: 賣{ma_trade_sequence} - {tracking_signal}")
                    # 賣出後準備下一個交易對，但不在這裡遞增，等下次買進時再遞增
                else:
                    # 無法交易（已有持倉或空倉）
                    position_status = "已持倉" if ma_position == 1 else "已空倉"
                    next_sequence = ma_trade_sequence + 1 if signal_type == 'buy' else ma_trade_sequence
                    signal_text = f'買{next_sequence}' if signal_type == 'buy' else f'賣{ma_trade_sequence}'
                    signals['30m'].append({
                        'datetime': current_time,
                        'close': current_price,
                        'signal_type': 'blocked',
                        'trade_sequence': 0,
                        'timeframe': '30m',
                        'hourly_signal': f'❌ 1小時MA{signal_text}被阻擋 ({position_status}): {tracking_signal}',
                        'macd_hist': 0,
                        'macd': 0,
                        'macd_signal': 0,
                        'is_blocked': True,
                        'ma9': ma9,
                        'ma25': ma25,
                        'ma99': ma99
                    })
            else:
                # 添加追蹤信號
                signals['30m'].append({
                    'datetime': current_time,
                    'close': current_price,
                    'signal_type': signal_type,
                    'trade_sequence': 0,
                    'timeframe': '30m',
                    'hourly_signal': tracking_signal,
                    'macd_hist': 0,
                    'macd': 0,
                    'macd_signal': 0,
                    'is_tracking': True,
                    'ma9': ma9,
                    'ma25': ma25,
                    'ma99': ma99
                })
    
    def _process_1h_ma_strategy(self, current_time, current_price, ma9, ma25, ma99, current_index, df_sorted):
        """1小時MA動態判斷核心邏輯"""
        
        # 策略參數 - 大幅降低閾值以增加觸發機會
        CROSS_THRESHOLD = 100        # 穿越閾值（元）- 大幅降低閾值
        CONFIRM_PERIODS = 1          # 確認週期數 - 降低確認要求
        MA99_TREND_THRESHOLD = 0.001 # MA99趨勢閾值（0.1%）- 大幅降低閾值
        
        # 計算MA99趨勢（需要至少5期數據）
        ma99_trend = 0
        if current_index >= 5:
            ma99_5_ago = df_sorted.iloc[current_index - 5]['ma99']
            if not pd.isna(ma99_5_ago) and ma99_5_ago > 0:
                ma99_trend = (ma99 - ma99_5_ago) / ma99_5_ago
        
        # 獲取前一期數據（用於確認穿越）
        prev_ma9 = ma9
        prev_ma25 = ma25
        if current_index > 0:
            prev_row = df_sorted.iloc[current_index - 1]
            if 'ma9' in prev_row and not pd.isna(prev_row['ma9']):
                prev_ma9 = prev_row['ma9']
                prev_ma25 = prev_row['ma25']
        
        # 判斷當前市場狀態
        if ma9 < ma99 and ma25 < ma99:
            # 空頭市場（MA9和MA25都在MA99下方）
            market_state = "空頭市場"
            
            if ma9 > ma25 + CROSS_THRESHOLD and prev_ma9 <= prev_ma25:
                # 黃金交叉 - 簡化條件，不要求MA99趨勢
                return True, f'🟢 1小時MA買進: 黃金交叉({ma9:,.0f}>{ma25:,.0f}) 空頭反彈', 'buy'
            elif ma9 > ma25:
                return False, f'🔵 1小時MA觀察: 空頭市場MA9({ma9:,.0f})>MA25({ma25:,.0f}) 等待確認', 'observing_buy'
            else:
                return False, f'⚪ 1小時MA追蹤: {market_state} MA9:{ma9:,.0f} MA25:{ma25:,.0f} MA99:{ma99:,.0f}', 'tracking'
                
        elif ma9 > ma99 and ma25 > ma99:
            # 多頭市場（MA9和MA25都在MA99上方）
            market_state = "多頭市場"
            
            if ma9 < ma25 - CROSS_THRESHOLD and prev_ma9 >= prev_ma25:
                # 死亡交叉 - 簡化條件，不要求MA99趨勢
                return True, f'🔴 1小時MA賣出: 死亡交叉({ma9:,.0f}<{ma25:,.0f}) 多頭回調', 'sell'
            elif ma9 < ma25:
                return False, f'🟠 1小時MA觀察: 多頭市場MA9({ma9:,.0f})<MA25({ma25:,.0f}) 等待確認', 'observing_sell'
            else:
                return False, f'⚪ 1小時MA追蹤: {market_state} MA9:{ma9:,.0f} MA25:{ma25:,.0f} MA99:{ma99:,.0f}', 'tracking'
        else:
            # 震盪市場（MA9和MA25跨越MA99）
            return False, f'🟣 1小時MA震盪: 震盪市場 MA9:{ma9:,.0f} MA25:{ma25:,.0f} MA99:{ma99:,.0f}', 'sideways'
        
    def _process_15m_with_30m_tracking(self, df: pd.DataFrame, signals: Dict[str, List], hourly_signals: List):
        """處理15分鐘，使用搜索確認機制（複製30分鐘的搜索邏輯）"""
        if df is None or df.empty:
            print("15M: 數據為空，跳過處理")
            return
        
        df_sorted = df.sort_values('datetime').reset_index(drop=True)
        hourly_signals_sorted = sorted(hourly_signals, key=lambda x: x['datetime'])
        
        # 初始化信號列表
        if '15m' not in signals:
            signals['15m'] = []
        
        # 當前活躍的搜索狀態和追蹤狀態（複製30分鐘的搜索邏輯）
        searching_reference = None  # 正在搜索的1小時基準點
        current_reference = None    # 已找到並開始追蹤的基準點
        tracking_lowest = None      # 追蹤最低點（買入用）
        tracking_highest = None     # 追蹤最高點（賣出用）
        
        print(f"15M: 開始處理15分鐘，共 {len(df_sorted)} 筆數據")
        
        # 預先建立1小時基準點映射
        hourly_reference_map = {}
        for hourly_signal in hourly_signals_sorted:
            hourly_reference_map[hourly_signal['datetime']] = hourly_signal
            print(f"15M HOURLY MAP: {hourly_signal['datetime']} -> {hourly_signal['close']:,.0f} ({hourly_signal['signal_type']})")
        
        for i, row in df_sorted.iterrows():
            current_time = row['datetime']
            current_price = row['close']
            
            # 檢查是否有新的1小時基準點需要搜索
            if current_time in hourly_reference_map:
                hourly_signal = hourly_reference_map[current_time]
                
                # 從hourly_signal中獲取序號
                sequence_num = hourly_signal.get('sequence')
                
                # 開始搜索1小時真正觸發價格
                searching_reference = {
                    'target_price': hourly_signal['close'],  # 要搜索的目標價格
                    'type': hourly_signal['signal_type'],
                    'sequence': sequence_num,
                    'start_time': current_time,
                    'hourly_time': current_time
                }
                
                print(f"🔍 15M: 開始搜索1小時真正觸發價格 {hourly_signal['close']:,.0f} ({hourly_signal['signal_type']}{sequence_num})")
                
                # 不在這裡添加信號，等找到真正觸發點時再添加
            
            # 如果正在搜索，檢查是否找到目標價格
            if searching_reference and current_time > searching_reference['start_time']:
                target_price = searching_reference['target_price']
                
                # 檢查是否找到精確匹配的價格（允許小誤差）
                if abs(current_price - target_price) < 0.1:
                    # 找到了！設置為活躍的追蹤基準點
                    current_reference = {
                        'price': target_price,  # 使用1小時的目標價格
                        'type': searching_reference['type'],
                        'sequence': searching_reference['sequence'],
                        'time': current_time,  # 實際找到的時間
                        'hourly_time': searching_reference['hourly_time']  # 1小時觸發時間
                    }
                    
                    print(f"✅ 15M: 已找到1小時觸發點！時間: {current_time}, 價格: {target_price:,.0f}")
                    
                    # 先添加基準點信號（在找到觸發點的時間顯示）
                    signal_type_text = '買' if current_reference['type'] == 'buy' else '賣'
                    base_signal = f'🔵 15分{signal_type_text}{current_reference["sequence"]}基準點' if current_reference['type'] == 'buy' else f'🔴 15分{signal_type_text}{current_reference["sequence"]}基準點'
                    signal_type = 'buy_reference' if current_reference['type'] == 'buy' else 'sell_reference'
                    
                    signals['15m'].append({
                        'datetime': current_time,  # 在實際找到觸發點的時間顯示基準點
                        'close': target_price,
                        'signal_type': signal_type,
                        'trade_sequence': current_reference['sequence'],
                        'timeframe': '15m',
                        'hourly_signal': base_signal,
                        'macd_hist': 0,
                        'macd': 0,
                        'macd_signal': 0,
                        'is_reference': True,
                        'reference_sequence': current_reference['sequence']
                    })
                    
                    # 然後添加確認找到的信號
                    found_signal = f'✅ 已找到1小時{signal_type_text}{current_reference["sequence"]}觸發點，開始動態追蹤'
                    
                    signals['15m'].append({
                        'datetime': current_time,
                        'close': target_price,  # 使用目標價格而不是當前價格
                        'signal_type': f'{current_reference["type"]}_confirmed',
                        'trade_sequence': current_reference['sequence'],
                        'timeframe': '15m',
                        'hourly_signal': found_signal,
                        'macd_hist': row['macd_hist'],
                        'macd': row['macd'],
                        'macd_signal': row['macd_signal'],
                        'is_confirmed': True,
                        'target_price': target_price
                    })
                    
                    # 初始化追蹤價格
                    if current_reference['type'] == 'buy':
                        tracking_lowest = target_price
                        tracking_highest = None
                        print(f"   初始化15分買入追蹤最低點: {tracking_lowest:,.0f}")
                    else:
                        tracking_highest = target_price
                        tracking_lowest = None
                        print(f"   初始化15分賣出追蹤最高點: {tracking_highest:,.0f}")
                    
                    # 清除搜索狀態
                    searching_reference = None
            
            # 如果有活躍的基準點，進行追蹤（完全複製30分鐘邏輯）
            if current_reference and current_time > current_reference['time']:
                tracking_signal = '⚪ 追蹤中'
                
                if current_reference['type'] == 'buy':
                    # 買入：持續更新最低點
                    if tracking_lowest is None or current_price < tracking_lowest:
                        tracking_lowest = current_price
                    
                    # 動態判斷基準：使用追蹤到的最低點
                    dynamic_trigger_price = tracking_lowest
                    tracking_signal = f'⚪ 追蹤中 {current_price:,.0f} →判斷基準: {dynamic_trigger_price:,.0f} (1小時基準: {current_reference["price"]:,.0f})'
                    
                    # 觸發條件：當前價格 > 追蹤到的最低點
                    trigger_result = current_price > dynamic_trigger_price
                    
                else:
                    # 賣出：持續更新最高點
                    if tracking_highest is None or current_price > tracking_highest:
                        tracking_highest = current_price
                    
                    # 動態判斷基準：使用追蹤到的最高點
                    dynamic_trigger_price = tracking_highest
                    tracking_signal = f'⚪ 追蹤中 {current_price:,.0f} →判斷基準: {dynamic_trigger_price:,.0f} (1小時基準: {current_reference["price"]:,.0f})'
                    
                    # 觸發條件：當前價格 < 追蹤到的最高點
                    trigger_result = current_price < dynamic_trigger_price
                
                if trigger_result:
                    # 觸發交易
                    if current_reference['type'] == 'buy':
                        signals['15m'].append({
                            'datetime': current_time,
                            'close': current_price,
                            'signal_type': 'buy',
                            'trade_sequence': current_reference['sequence'],
                            'timeframe': '15m',
                            'hourly_signal': f'🟢 15分買{current_reference["sequence"]} (已超過最低點買入)',
                            'macd_hist': row['macd_hist'],
                            'macd': row['macd'],
                            'macd_signal': row['macd_signal'],
                            'is_confirmed': True,
                            'reference_sequence': current_reference['sequence'],
                            'tracking_lowest': tracking_lowest  # 記錄追蹤到的最低點
                        })
                        print(f"15M買入交易完成: 15分買{current_reference['sequence']}, 最低點: {tracking_lowest:,.0f}")
                        current_reference = None  # 清除活躍基準點
                        
                    else:
                        signals['15m'].append({
                            'datetime': current_time,
                            'close': current_price,
                            'signal_type': 'sell',
                            'trade_sequence': current_reference['sequence'],
                            'timeframe': '15m',
                            'hourly_signal': f'🔴 15分賣{current_reference["sequence"]} (已低於最高點賣出)',
                            'macd_hist': row['macd_hist'],
                            'macd': row['macd'],
                            'macd_signal': row['macd_signal'],
                            'is_confirmed': True,
                            'reference_sequence': current_reference['sequence'],
                            'tracking_highest': tracking_highest  # 記錄追蹤到的最高點
                        })
                        print(f"15M賣出交易完成: 15分賣{current_reference['sequence']}, 最高點: {tracking_highest:,.0f}")
                        current_reference = None  # 清除活躍基準點
                else:
                    # 沒有觸發，添加追蹤信號
                    signals['15m'].append({
                        'datetime': current_time,
                        'close': current_price,
                        'signal_type': 'tracking',
                        'trade_sequence': 0,
                        'timeframe': '15m',
                        'hourly_signal': tracking_signal,
                        'macd_hist': row['macd_hist'],
                        'macd': row['macd'],
                        'macd_signal': row['macd_signal'],
                        'is_tracking': True,
                        'reference_sequence': current_reference['sequence'],
                        'tracking_lowest': tracking_lowest,
                        'tracking_highest': tracking_highest
                    })
    
    def _process_5m_independent_tracking(self, df: pd.DataFrame, signals: Dict[str, List], hourly_signals: List):
        """處理5分鐘，完全複製30分鐘的搜索邏輯，完全獨立"""
        if df is None or df.empty:
            print("5M: 數據為空，跳過處理")
            return
        
        df_sorted = df.sort_values('datetime').reset_index(drop=True)
        hourly_signals_sorted = sorted(hourly_signals, key=lambda x: x['datetime'])
        
        # 初始化信號列表
        if '5m' not in signals:
            signals['5m'] = []
        
        # 當前活躍的搜索狀態和追蹤狀態（完全複製30分鐘的邏輯）
        searching_reference = None  # 正在搜索的1小時基準點
        current_reference = None    # 已找到並開始追蹤的基準點
        tracking_lowest = None      # 追蹤最低點（買入用）
        tracking_highest = None     # 追蹤最高點（賣出用）
        
        print(f"5M: 開始處理5分鐘，共 {len(df_sorted)} 筆數據")
        
        # 預先建立1小時基準點映射
        hourly_reference_map = {}
        for hourly_signal in hourly_signals_sorted:
            hourly_reference_map[hourly_signal['datetime']] = hourly_signal
        
        for i, row in df_sorted.iterrows():
            current_time = row['datetime']
            current_price = row['close']
            
            # 檢查是否有新的1小時基準點需要搜索
            if current_time in hourly_reference_map:
                hourly_signal = hourly_reference_map[current_time]
                sequence_num = hourly_signal.get('sequence')
                
                # 開始搜索1小時真正觸發價格
                searching_reference = {
                    'target_price': hourly_signal['close'],  # 要搜索的目標價格
                    'type': hourly_signal['signal_type'],
                    'sequence': sequence_num,
                    'start_time': current_time,
                    'hourly_time': current_time
                }
                
                print(f"🔍 5M: 開始搜索1小時真正觸發價格 {hourly_signal['close']:,.0f} ({hourly_signal['signal_type']}{sequence_num})")
            
            # 如果正在搜索，檢查是否找到目標價格
            if searching_reference and current_time > searching_reference['start_time']:
                target_price = searching_reference['target_price']
                
                # 檢查是否找到精確匹配的價格（允許小誤差）
                if abs(current_price - target_price) < 0.1:
                    # 找到了！設置為活躍的追蹤基準點
                    current_reference = {
                        'price': target_price,  # 使用1小時的目標價格
                        'type': searching_reference['type'],
                        'sequence': searching_reference['sequence'],
                        'time': current_time,  # 實際找到的時間
                        'hourly_time': searching_reference['hourly_time']  # 1小時觸發時間
                    }
                    
                    print(f"✅ 5M: 已找到1小時觸發點！時間: {current_time}, 價格: {target_price:,.0f}")
                    
                    # 先添加基準點信號（在找到觸發點的時間顯示）
                    signal_type_text = '買' if current_reference['type'] == 'buy' else '賣'
                    base_signal = f'🔵 5分{signal_type_text}{current_reference["sequence"]}基準點' if current_reference['type'] == 'buy' else f'🔴 5分{signal_type_text}{current_reference["sequence"]}基準點'
                    signal_type = 'buy_reference' if current_reference['type'] == 'buy' else 'sell_reference'
                    
                    signals['5m'].append({
                        'datetime': current_time,  # 在實際找到觸發點的時間顯示基準點
                        'close': target_price,
                        'signal_type': signal_type,
                        'trade_sequence': current_reference['sequence'],
                        'timeframe': '5m',
                        'hourly_signal': base_signal,
                        'macd_hist': 0,
                        'macd': 0,
                        'macd_signal': 0,
                        'is_reference': True,
                        'reference_sequence': current_reference['sequence']
                    })
                    
                    # 然後添加確認找到的信號
                    found_signal = f'✅ 已找到1小時{signal_type_text}{current_reference["sequence"]}觸發點，開始動態追蹤'
                    
                    signals['5m'].append({
                        'datetime': current_time,
                        'close': target_price,  # 使用目標價格而不是當前價格
                        'signal_type': f'{current_reference["type"]}_confirmed',
                        'trade_sequence': current_reference['sequence'],
                        'timeframe': '5m',
                        'hourly_signal': found_signal,
                        'macd_hist': row['macd_hist'],
                        'macd': row['macd'],
                        'macd_signal': row['macd_signal'],
                        'is_confirmed': True,
                        'target_price': target_price
                    })
                    
                    # 初始化追蹤價格
                    if current_reference['type'] == 'buy':
                        tracking_lowest = target_price
                        tracking_highest = None
                        print(f"   初始化5分買入追蹤最低點: {tracking_lowest:,.0f}")
                    else:
                        tracking_highest = target_price
                        tracking_lowest = None
                        print(f"   初始化5分賣出追蹤最高點: {tracking_highest:,.0f}")
                    
                    # 清除搜索狀態
                    searching_reference = None
            
            # 如果有活躍的基準點，進行追蹤（完全複製30分鐘邏輯）
            if current_reference and current_time > current_reference['time']:
                tracking_signal = '⚪ 追蹤中'
                
                if current_reference['type'] == 'buy':
                    # 買入：持續更新最低點
                    if tracking_lowest is None or current_price < tracking_lowest:
                        tracking_lowest = current_price
                    
                    # 動態判斷基準：使用追蹤到的最低點
                    dynamic_trigger_price = tracking_lowest
                    tracking_signal = f'⚪ 追蹤中 {current_price:,.0f} →判斷基準: {dynamic_trigger_price:,.0f} (1小時基準: {current_reference["price"]:,.0f})'
                    
                    # 觸發條件：當前價格 > 追蹤到的最低點
                    trigger_result = current_price > dynamic_trigger_price
                    
                else:
                    # 賣出：持續更新最高點
                    if tracking_highest is None or current_price > tracking_highest:
                        tracking_highest = current_price
                    
                    # 動態判斷基準：使用追蹤到的最高點
                    dynamic_trigger_price = tracking_highest
                    tracking_signal = f'⚪ 追蹤中 {current_price:,.0f} →判斷基準: {dynamic_trigger_price:,.0f} (1小時基準: {current_reference["price"]:,.0f})'
                    
                    # 觸發條件：當前價格 < 追蹤到的最高點
                    trigger_result = current_price < dynamic_trigger_price
                
                if trigger_result:
                    # 觸發交易
                    if current_reference['type'] == 'buy':
                        signals['5m'].append({
                            'datetime': current_time,
                            'close': current_price,
                            'signal_type': 'buy',
                            'trade_sequence': current_reference['sequence'],
                            'timeframe': '5m',
                            'hourly_signal': f'🟢 5分買{current_reference["sequence"]} (已超過最低點買入)',
                            'macd_hist': row['macd_hist'],
                            'macd': row['macd'],
                            'macd_signal': row['macd_signal'],
                            'is_confirmed': True,
                            'reference_sequence': current_reference['sequence'],
                            'tracking_lowest': tracking_lowest  # 記錄追蹤到的最低點
                        })
                        print(f"5M買入交易完成: 5分買{current_reference['sequence']}, 最低點: {tracking_lowest:,.0f}")
                        current_reference = None  # 清除活躍基準點
                        
                    else:
                        signals['5m'].append({
                            'datetime': current_time,
                            'close': current_price,
                            'signal_type': 'sell',
                            'trade_sequence': current_reference['sequence'],
                            'timeframe': '5m',
                            'hourly_signal': f'🔴 5分賣{current_reference["sequence"]} (已低於最高點賣出)',
                            'macd_hist': row['macd_hist'],
                            'macd': row['macd'],
                            'macd_signal': row['macd_signal'],
                            'is_confirmed': True,
                            'reference_sequence': current_reference['sequence'],
                            'tracking_highest': tracking_highest  # 記錄追蹤到的最高點
                        })
                        print(f"5M賣出交易完成: 5分賣{current_reference['sequence']}, 最高點: {tracking_highest:,.0f}")
                        current_reference = None  # 清除活躍基準點
                else:
                    # 沒有觸發，添加追蹤信號
                    signals['5m'].append({
                        'datetime': current_time,
                        'close': current_price,
                        'signal_type': 'tracking',
                        'trade_sequence': 0,
                        'timeframe': '5m',
                        'hourly_signal': tracking_signal,
                        'macd_hist': row['macd_hist'],
                        'macd': row['macd'],
                        'macd_signal': row['macd_signal'],
                        'is_tracking': True,
                        'reference_sequence': current_reference['sequence'],
                        'tracking_lowest': tracking_lowest,
                        'tracking_highest': tracking_highest
                    })

    
    def get_statistics(self) -> Dict:
        """獲取統計信息"""
        status = self.tracker.get_status()
        return {
            'total_signals': self.tracker.buy_count + self.tracker.sell_count,
            'total_trades': len(self.tracker.trade_pairs),
            'buy_count': self.tracker.buy_count,
            'sell_count': self.tracker.sell_count,
            'trade_pairs': self.tracker.trade_pairs,
            'current_status': status,
            'position_status': status.get('position_status', '空倉'),
            'complete_pairs': status.get('complete_pairs', 0),
            'open_positions': status.get('open_positions', 0),
            'next_trade_sequence': status.get('next_trade_sequence', 1)
        }

def detect_multi_timeframe_trading_signals(hourly_df: pd.DataFrame, timeframe_dfs: Dict[str, pd.DataFrame], 
                                          confirmation_timeout_hours: int = 2) -> Tuple[Dict[str, pd.DataFrame], Dict, object]:
    """
    檢測多時間週期策略交易信號
    
    Args:
        hourly_df: 1小時MACD數據
        timeframe_dfs: 短時間週期數據字典 {'30m': df, '15m': df, '5m': df}
        confirmation_timeout_hours: 確認超時時間（小時）
    
    Returns:
        (signals_dict, statistics, tracker)
    """
    engine = MultiTimeframeSignalDetectionEngine(confirmation_timeout_hours)
    signals_dict = engine.detect_smart_balanced_signals(hourly_df, timeframe_dfs)
    statistics = engine.get_statistics()
    
    return signals_dict, statistics, engine.tracker 