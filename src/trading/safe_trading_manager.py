#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全交易管理器
包含風險控制、緊急停止、資金管理等功能
"""

import json
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import threading
import signal
import sys

logger = logging.getLogger(__name__)

class SafeTradingManager:
    """安全交易管理器"""
    
    def __init__(self, config_file: str = "trading_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.is_running = False
        self.emergency_stop = False
        self.current_position = None
        self.daily_loss = 0
        self.total_trades_today = 0
        self.last_reset_date = datetime.now().date()
        
        # 設置緊急停止信號處理 (僅在非Windows系統或主線程中設置)
        try:
            if hasattr(signal, 'SIGTERM'):
                signal.signal(signal.SIGTERM, self.emergency_stop_handler)
        except ValueError:
            pass  # 忽略在非主線程中設置信號處理器的錯誤
        
        # 創建狀態文件
        self.status_file = "trading_status.json"
        self.create_status_file()
    
    def load_config(self) -> Dict:
        """載入交易配置"""
        default_config = {
            "trading_amount": 50000,  # 每次交易金額 (TWD)
            "max_daily_loss": 5000,   # 每日最大虧損 (TWD)
            "max_daily_trades": 5,    # 每日最大交易次數
            "max_position_time": 24,  # 最大持倉時間 (小時)
            "emergency_stop_loss": 0.05,  # 緊急停損比例 (5%)
            "enable_trading": True,   # 是否啟用交易
            "notification_enabled": True,  # 是否啟用通知
            "telegram_chat_id": "",   # Telegram通知ID
            "dry_run": True,         # 是否為模擬交易
            "exchange": "max",       # 交易所
            "symbol": "BTCTWD"       # 交易對
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合併默認配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                logger.error(f"載入配置失敗: {e}")
                return default_config
        else:
            # 創建默認配置文件
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict = None):
        """保存配置"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存配置失敗: {e}")
    
    def create_status_file(self):
        """創建狀態文件"""
        status = {
            "is_running": False,
            "emergency_stop": False,
            "current_position": None,
            "daily_loss": 0,
            "total_trades_today": 0,
            "last_update": datetime.now().isoformat(),
            "last_signal": None,
            "system_status": "stopped"
        }
        
        try:
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"創建狀態文件失敗: {e}")
    
    def update_status(self, **kwargs):
        """更新狀態文件"""
        try:
            # 讀取現有狀態
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    status = json.load(f)
            else:
                status = {}
            
            # 更新狀態
            status.update(kwargs)
            status["last_update"] = datetime.now().isoformat()
            
            # 保存狀態
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"更新狀態失敗: {e}")
    
    def emergency_stop_handler(self, signum, frame):
        """緊急停止信號處理器"""
        logger.warning("收到緊急停止信號！")
        self.emergency_stop = True
        self.is_running = False
        self.update_status(
            emergency_stop=True,
            is_running=False,
            system_status="emergency_stopped"
        )
        print("\n🚨 緊急停止已啟動！系統將安全關閉...")
        sys.exit(0)
    
    def check_daily_limits(self) -> bool:
        """檢查每日限制"""
        today = datetime.now().date()
        
        # 如果是新的一天，重置計數器
        if today != self.last_reset_date:
            self.daily_loss = 0
            self.total_trades_today = 0
            self.last_reset_date = today
            logger.info("每日限制已重置")
        
        # 檢查每日虧損限制
        if self.daily_loss >= self.config["max_daily_loss"]:
            logger.warning(f"達到每日最大虧損限制: {self.daily_loss} TWD")
            return False
        
        # 檢查每日交易次數限制
        if self.total_trades_today >= self.config["max_daily_trades"]:
            logger.warning(f"達到每日最大交易次數限制: {self.total_trades_today}")
            return False
        
        return True
    
    def check_position_time(self) -> bool:
        """檢查持倉時間"""
        if self.current_position is None:
            return True
        
        position_time = datetime.now() - self.current_position["entry_time"]
        max_time = timedelta(hours=self.config["max_position_time"])
        
        if position_time > max_time:
            logger.warning(f"持倉時間過長: {position_time}")
            return False
        
        return True
    
    def check_emergency_stop_loss(self, current_price: float) -> bool:
        """檢查緊急停損"""
        if self.current_position is None:
            return True
        
        entry_price = self.current_position["entry_price"]
        if self.current_position["side"] == "buy":
            loss_ratio = (entry_price - current_price) / entry_price
        else:
            loss_ratio = (current_price - entry_price) / entry_price
        
        if loss_ratio >= self.config["emergency_stop_loss"]:
            logger.error(f"觸發緊急停損! 虧損比例: {loss_ratio:.2%}")
            return False
        
        return True
    
    def can_trade(self, current_price: float = None) -> tuple:
        """檢查是否可以交易"""
        # 檢查緊急停止
        if self.emergency_stop:
            return False, "系統緊急停止"
        
        # 檢查是否啟用交易
        if not self.config["enable_trading"]:
            return False, "交易已停用"
        
        # 檢查每日限制
        if not self.check_daily_limits():
            return False, "達到每日限制"
        
        # 檢查持倉時間
        if not self.check_position_time():
            return False, "持倉時間過長"
        
        # 檢查緊急停損
        if current_price and not self.check_emergency_stop_loss(current_price):
            return False, "觸發緊急停損"
        
        return True, "可以交易"
    
    def execute_trade(self, signal: Dict) -> Dict:
        """執行交易"""
        can_trade, reason = self.can_trade(signal.get("price"))
        
        if not can_trade:
            logger.warning(f"無法執行交易: {reason}")
            return {
                "success": False,
                "reason": reason,
                "signal": signal
            }
        
        # 模擬交易或實際交易
        if self.config["dry_run"]:
            result = self.simulate_trade(signal)
        else:
            result = self.real_trade(signal)
        
        # 更新統計
        if result["success"]:
            self.total_trades_today += 1
            if signal["signal_type"] == "sell" and "profit" in result:
                if result["profit"] < 0:
                    self.daily_loss += abs(result["profit"])
        
        # 更新狀態
        self.update_status(
            total_trades_today=self.total_trades_today,
            daily_loss=self.daily_loss,
            last_signal=signal,
            system_status="trading"
        )
        
        return result
    
    def simulate_trade(self, signal: Dict) -> Dict:
        """模擬交易"""
        logger.info(f"🔄 模擬交易: {signal['signal_type']} at {signal['close']:,.0f}")
        
        if signal["signal_type"] == "buy":
            self.current_position = {
                "side": "buy",
                "entry_price": signal["close"],
                "entry_time": datetime.now(),
                "amount": self.config["trading_amount"] / signal["close"]
            }
            return {
                "success": True,
                "type": "buy",
                "price": signal["close"],
                "amount": self.current_position["amount"],
                "message": f"模擬買入 {self.current_position['amount']:.6f} BTC"
            }
        
        elif signal["signal_type"] == "sell" and self.current_position:
            profit = (signal["close"] - self.current_position["entry_price"]) * self.current_position["amount"]
            profit_pct = (signal["close"] - self.current_position["entry_price"]) / self.current_position["entry_price"]
            
            result = {
                "success": True,
                "type": "sell",
                "price": signal["close"],
                "amount": self.current_position["amount"],
                "profit": profit,
                "profit_pct": profit_pct,
                "message": f"模擬賣出 {self.current_position['amount']:.6f} BTC, 獲利: {profit:,.0f} TWD ({profit_pct:.2%})"
            }
            
            self.current_position = None
            return result
        
        return {"success": False, "reason": "無效信號或無持倉"}
    
    def real_trade(self, signal: Dict) -> Dict:
        """實際交易 (需要接入交易所API)"""
        # 這裡需要實際的交易所API接入
        logger.warning("實際交易功能需要接入交易所API")
        return {"success": False, "reason": "實際交易功能未實現"}
    
    def start_monitoring(self):
        """開始監控"""
        self.is_running = True
        self.update_status(
            is_running=True,
            system_status="monitoring"
        )
        logger.info("🚀 安全交易管理器已啟動")
    
    def stop_monitoring(self):
        """停止監控"""
        self.is_running = False
        self.update_status(
            is_running=False,
            system_status="stopped"
        )
        logger.info("⏹️ 安全交易管理器已停止")
    
    def get_status(self) -> Dict:
        """獲取當前狀態"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"讀取狀態失敗: {e}")
        
        return {"error": "無法讀取狀態"}
    
    def create_emergency_stop_file(self):
        """創建緊急停止文件"""
        with open("EMERGENCY_STOP", 'w') as f:
            f.write(f"Emergency stop requested at {datetime.now()}")
        
        self.emergency_stop = True
        self.is_running = False
        logger.error("🚨 緊急停止文件已創建！")
    
    def check_emergency_stop_file(self) -> bool:
        """檢查緊急停止文件"""
        if os.path.exists("EMERGENCY_STOP"):
            self.emergency_stop = True
            self.is_running = False
            return True
        return False