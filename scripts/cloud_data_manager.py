#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雲端數據管理器
解決GitHub Actions無法持久化數據的問題
使用GitHub Issues或Gist作為數據存儲
"""

import os
import json
import requests
import base64
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class CloudDataManager:
    """雲端數據管理器"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = 'winyoulife'
        self.repo_name = 'AImax-Trading-System'
        self.data_branch = 'trading-data'  # 專用數據分支
        
        # 初始化設定
        self.initial_balance = 100000.0  # 10萬台幣
        self.current_balance = self.initial_balance
        self.positions = {}
        self.trade_history = []
        
    def get_headers(self):
        """獲取GitHub API請求頭"""
        return {
            'Authorization': f'token {self.github_token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
    
    def load_portfolio_state(self) -> Dict:
        """從GitHub載入投資組合狀態"""
        try:
            if not self.github_token:
                logger.warning("⚠️ GitHub Token未設定，使用本地數據")
                return self.load_local_state()
            
            # 嘗試從GitHub獲取數據
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/data/simulation/portfolio_state.json"
            
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                file_data = response.json()
                content = base64.b64decode(file_data['content']).decode('utf-8')
                state = json.loads(content)
                
                self.current_balance = state.get('balance', self.initial_balance)
                self.positions = state.get('positions', {})
                
                logger.info(f"✅ 從GitHub載入投資組合狀態: 餘額 {self.current_balance:,.0f} TWD")
                return state
                
            elif response.status_code == 404:
                logger.info("📝 GitHub上無投資組合數據，創建初始狀態")
                return self.create_initial_state()
            else:
                logger.error(f"❌ 載入GitHub數據失敗: {response.status_code}")
                return self.load_local_state()
                
        except Exception as e:
            logger.error(f"❌ 載入投資組合狀態失敗: {e}")
            return self.load_local_state()
    
    def save_portfolio_state(self, state: Dict) -> bool:
        """保存投資組合狀態到GitHub"""
        try:
            if not self.github_token:
                logger.warning("⚠️ GitHub Token未設定，僅保存到本地")
                return self.save_local_state(state)
            
            # 準備數據
            content = json.dumps(state, indent=2, ensure_ascii=False)
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            
            # 檢查文件是否存在
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/data/simulation/portfolio_state.json"
            
            get_response = requests.get(url, headers=self.get_headers())
            
            data = {
                'message': f'更新投資組合狀態 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                'content': encoded_content,
                'branch': 'main'
            }
            
            # 如果文件存在，需要提供SHA
            if get_response.status_code == 200:
                data['sha'] = get_response.json()['sha']
            
            # 提交更新
            response = requests.put(url, headers=self.get_headers(), json=data)
            
            if response.status_code in [200, 201]:
                logger.info("✅ 投資組合狀態已保存到GitHub")
                return True
            else:
                logger.error(f"❌ 保存到GitHub失敗: {response.status_code}")
                return self.save_local_state(state)
                
        except Exception as e:
            logger.error(f"❌ 保存投資組合狀態失敗: {e}")
            return self.save_local_state(state)
    
    def save_trade_record(self, trade: Dict) -> bool:
        """保存交易記錄"""
        try:
            # 本地保存
            os.makedirs('data/simulation', exist_ok=True)
            with open('data/simulation/trades.jsonl', 'a', encoding='utf-8') as f:
                f.write(json.dumps(trade, ensure_ascii=False) + '\n')
            
            # 如果有GitHub Token，也保存到雲端
            if self.github_token:
                return self.append_trade_to_github(trade)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存交易記錄失敗: {e}")
            return False
    
    def append_trade_to_github(self, trade: Dict) -> bool:
        """將交易記錄追加到GitHub"""
        try:
            # 獲取現有交易記錄
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/data/simulation/trades.jsonl"
            
            response = requests.get(url, headers=self.get_headers())
            
            if response.status_code == 200:
                # 文件存在，追加內容
                file_data = response.json()
                existing_content = base64.b64decode(file_data['content']).decode('utf-8')
                new_content = existing_content + json.dumps(trade, ensure_ascii=False) + '\n'
                
                encoded_content = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')
                
                data = {
                    'message': f'新增交易記錄 - {trade.get("action", "unknown")} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    'content': encoded_content,
                    'sha': file_data['sha'],
                    'branch': 'main'
                }
                
            else:
                # 文件不存在，創建新文件
                content = json.dumps(trade, ensure_ascii=False) + '\n'
                encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                
                data = {
                    'message': f'創建交易記錄文件 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    'content': encoded_content,
                    'branch': 'main'
                }
            
            # 提交更新
            response = requests.put(url, headers=self.get_headers(), json=data)
            
            if response.status_code in [200, 201]:
                logger.info("✅ 交易記錄已保存到GitHub")
                return True
            else:
                logger.error(f"❌ 保存交易記錄到GitHub失敗: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 保存交易記錄到GitHub失敗: {e}")
            return False
    
    def load_local_state(self) -> Dict:
        """載入本地狀態"""
        try:
            if os.path.exists('data/simulation/portfolio_state.json'):
                with open('data/simulation/portfolio_state.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self.create_initial_state()
        except Exception as e:
            logger.error(f"❌ 載入本地狀態失敗: {e}")
            return self.create_initial_state()
    
    def save_local_state(self, state: Dict) -> bool:
        """保存本地狀態"""
        try:
            os.makedirs('data/simulation', exist_ok=True)
            with open('data/simulation/portfolio_state.json', 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"❌ 保存本地狀態失敗: {e}")
            return False
    
    def create_initial_state(self) -> Dict:
        """創建初始狀態"""
        state = {
            'balance': self.initial_balance,
            'positions': {},
            'last_update': datetime.now().isoformat(),
            'total_trades': 0,
            'initial_balance': self.initial_balance,
            'currency': 'TWD',
            'exchange': 'MAX',
            'strategy_version': 'v1.0-smart-balanced'
        }
        
        # 保存初始狀態
        self.save_portfolio_state(state)
        return state
    
    def get_trading_summary(self) -> Dict:
        """獲取交易摘要"""
        try:
            # 載入投資組合狀態
            state = self.load_portfolio_state()
            
            # 載入交易記錄
            trades = []
            if os.path.exists('data/simulation/trades.jsonl'):
                with open('data/simulation/trades.jsonl', 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            trades.append(json.loads(line.strip()))
            
            # 計算統計
            total_trades = len(trades)
            buy_trades = len([t for t in trades if t.get('action') == 'buy'])
            sell_trades = len([t for t in trades if t.get('action') == 'sell'])
            
            # 計算總價值 (現金 + 持倉價值)
            current_balance = state.get('balance', self.initial_balance)
            positions = state.get('positions', {})
            
            # 估算持倉價值 (使用固定價格)
            estimated_btc_price = 95000.0
            position_value = sum(qty * estimated_btc_price for qty in positions.values())
            total_value = current_balance + position_value
            
            total_return = total_value - self.initial_balance
            return_pct = (total_return / self.initial_balance) * 100
            
            return {
                'initial_balance': self.initial_balance,
                'current_balance': current_balance,
                'positions': positions,
                'position_value': position_value,
                'total_value': total_value,
                'total_return': total_return,
                'return_percentage': return_pct,
                'total_trades': total_trades,
                'buy_trades': buy_trades,
                'sell_trades': sell_trades,
                'last_update': state.get('last_update', datetime.now().isoformat())
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取交易摘要失敗: {e}")
            return {}

def main():
    """測試雲端數據管理器"""
    print("🧪 測試雲端數據管理器")
    
    manager = CloudDataManager()
    
    # 載入狀態
    state = manager.load_portfolio_state()
    print(f"📊 當前狀態: {json.dumps(state, indent=2, ensure_ascii=False)}")
    
    # 獲取摘要
    summary = manager.get_trading_summary()
    print(f"📈 交易摘要: {json.dumps(summary, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    main()