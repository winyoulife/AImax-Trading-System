#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI決策可視化組件 - 顯示AI決策過程和歷史追蹤
"""

import sys
import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import sqlite3

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
        QTabWidget, QGroupBox, QProgressBar, QScrollArea,
        QFrame, QSplitter, QComboBox, QDateTimeEdit, QCheckBox
    )
    from PyQt6.QtCore import QTimer, Qt, QDateTime
    from PyQt6.QtGui import QFont, QColor, QPalette
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("⚠️ PyQt6 未安裝，AI決策可視化將使用文本模式")

logger = logging.getLogger(__name__)

class DecisionCard(QFrame if PYQT_AVAILABLE else object):
    """單個AI決策卡片"""
    
    def __init__(self, decision_data: Dict[str, Any], parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        self.decision_data = decision_data
        self.setup_ui()
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 標題行
        title_layout = QHBoxLayout()
        
        # AI模型名稱
        model_name = QLabel(self.decision_data.get('model_name', 'Unknown AI'))
        model_name.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_layout.addWidget(model_name)
        
        title_layout.addStretch()
        
        # 決策結果
        decision = self.decision_data.get('decision', 'HOLD')
        decision_label = QLabel(decision)
        decision_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        # 根據決策類型設置顏色
        if decision == 'BUY':
            decision_label.setStyleSheet("color: #28a745;")
        elif decision == 'SELL':
            decision_label.setStyleSheet("color: #dc3545;")
        else:
            decision_label.setStyleSheet("color: #ffc107;")
        
        title_layout.addWidget(decision_label)
        layout.addLayout(title_layout)    
    
        # 信心度進度條
        confidence_layout = QHBoxLayout()
        confidence_layout.addWidget(QLabel("信心度:"))
        
        confidence = self.decision_data.get('confidence', 0.0)
        confidence_bar = QProgressBar()
        confidence_bar.setRange(0, 100)
        confidence_bar.setValue(int(confidence * 100))
        confidence_layout.addWidget(confidence_bar)
        
        confidence_layout.addWidget(QLabel(f"{confidence:.1%}"))
        layout.addLayout(confidence_layout)
        
        # 決策理由
        reasoning = self.decision_data.get('reasoning', '無詳細說明')
        reasoning_label = QLabel(f"決策理由: {reasoning}")
        reasoning_label.setWordWrap(True)
        reasoning_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(reasoning_label)
        
        # 技術指標
        indicators = self.decision_data.get('technical_indicators', {})
        if indicators:
            indicators_text = "技術指標: " + ", ".join([
                f"{k}: {v}" for k, v in indicators.items()
            ])
            indicators_label = QLabel(indicators_text)
            indicators_label.setWordWrap(True)
            indicators_label.setStyleSheet("color: #495057; font-size: 9px;")
            layout.addWidget(indicators_label)
        
        # 時間戳
        timestamp = self.decision_data.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        time_label = QLabel(f"時間: {timestamp.strftime('%H:%M:%S')}")
        time_label.setStyleSheet("color: #6c757d; font-size: 8px;")
        layout.addWidget(time_label)

class AIDecisionVisualization(QWidget if PYQT_AVAILABLE else object):
    """AI決策可視化主組件"""
    
    def __init__(self, parent=None):
        if PYQT_AVAILABLE:
            super().__init__(parent)
        
        self.ai_manager = None
        self.decision_history = []
        self.db_path = "AImax/data/decision_history.db"
        
        self.setup_ui()
        self.setup_database()
        
        # 定時更新決策
        if PYQT_AVAILABLE:
            self.decision_timer = QTimer()
            self.decision_timer.timeout.connect(self.update_decisions)
            self.decision_timer.start(15000)  # 每15秒更新
    
    def setup_ui(self):
        """設置UI"""
        if not PYQT_AVAILABLE:
            return
            
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("🧠 AI決策可視化")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 創建標籤頁
        self.tab_widget = QTabWidget()
        
        # 實時決策標籤頁
        self.realtime_tab = self.create_realtime_tab()
        self.tab_widget.addTab(self.realtime_tab, "🔴 實時決策")
        
        # 歷史追蹤標籤頁
        self.history_tab = self.create_history_tab()
        self.tab_widget.addTab(self.history_tab, "📊 歷史追蹤")
        
        # 決策分析標籤頁
        self.analysis_tab = self.create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "📈 決策分析")
        
        layout.addWidget(self.tab_widget)
    
    def create_realtime_tab(self) -> QWidget:
        """創建實時決策標籤頁"""
        if not PYQT_AVAILABLE:
            return None
            
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        # 交易對選擇
        control_layout.addWidget(QLabel("交易對:"))
        self.pair_combo = QComboBox()
        self.pair_combo.addItems(["BTCTWD", "ETHTWD", "LTCTWD", "BCHTWD"])
        control_layout.addWidget(self.pair_combo)
        
        # 自動更新開關
        self.auto_update_checkbox = QCheckBox("自動更新")
        self.auto_update_checkbox.setChecked(True)
        self.auto_update_checkbox.stateChanged.connect(self.toggle_auto_update)
        control_layout.addWidget(self.auto_update_checkbox)
        
        # 手動刷新按鈕
        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.clicked.connect(self.update_decisions)
        control_layout.addWidget(refresh_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 決策卡片顯示區域
        self.decision_scroll = QScrollArea()
        self.decision_widget = QWidget()
        self.decision_layout = QVBoxLayout(self.decision_widget)
        
        self.decision_scroll.setWidget(self.decision_widget)
        self.decision_scroll.setWidgetResizable(True)
        layout.addWidget(self.decision_scroll)
        
        return tab    

    def create_history_tab(self) -> QWidget:
        """創建歷史追蹤標籤頁"""
        if not PYQT_AVAILABLE:
            return None
            
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 篩選控制
        filter_layout = QHBoxLayout()
        
        # 時間範圍
        filter_layout.addWidget(QLabel("時間範圍:"))
        self.start_datetime = QDateTimeEdit()
        self.start_datetime.setDateTime(QDateTime.currentDateTime().addDays(-1))
        filter_layout.addWidget(self.start_datetime)
        
        filter_layout.addWidget(QLabel("到"))
        self.end_datetime = QDateTimeEdit()
        self.end_datetime.setDateTime(QDateTime.currentDateTime())
        filter_layout.addWidget(self.end_datetime)
        
        # 決策類型篩選
        filter_layout.addWidget(QLabel("決策類型:"))
        self.decision_filter = QComboBox()
        self.decision_filter.addItems(["全部", "BUY", "SELL", "HOLD"])
        filter_layout.addWidget(self.decision_filter)
        
        # 應用篩選按鈕
        apply_filter_btn = QPushButton("🔍 應用篩選")
        apply_filter_btn.clicked.connect(self.apply_history_filter)
        filter_layout.addWidget(apply_filter_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # 歷史決策表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "時間", "AI模型", "決策", "信心度", "理由", "技術指標", "結果"
        ])
        
        # 調整列寬
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        layout.addWidget(self.history_table)
        
        return tab
    
    def create_analysis_tab(self) -> QWidget:
        """創建決策分析標籤頁"""
        if not PYQT_AVAILABLE:
            return None
            
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 分析統計
        stats_group = QGroupBox("決策統計")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        stats_layout.addWidget(self.stats_text)
        
        layout.addWidget(stats_group)
        
        # 模型性能比較
        performance_group = QGroupBox("模型性能比較")
        performance_layout = QVBoxLayout(performance_group)
        
        self.performance_table = QTableWidget()
        self.performance_table.setColumnCount(5)
        self.performance_table.setHorizontalHeaderLabels([
            "AI模型", "決策數量", "準確率", "平均信心度", "最後決策"
        ])
        performance_layout.addWidget(self.performance_table)
        
        layout.addWidget(performance_group)
        
        # 更新分析按鈕
        update_analysis_btn = QPushButton("📊 更新分析")
        update_analysis_btn.clicked.connect(self.update_analysis)
        layout.addWidget(update_analysis_btn)
        
        return tab
    
    def setup_database(self):
        """設置數據庫"""
        try:
            # 確保數據目錄存在
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 創建決策歷史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decision_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    trading_pair TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT,
                    technical_indicators TEXT,
                    result TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("✅ 決策歷史數據庫初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 數據庫初始化失敗: {e}")
    
    def set_ai_manager(self, ai_manager):
        """設置AI管理器"""
        self.ai_manager = ai_manager
        self.update_decisions()
    
    def toggle_auto_update(self, state):
        """切換自動更新"""
        if not PYQT_AVAILABLE:
            return
            
        if state == Qt.CheckState.Checked.value:
            self.decision_timer.start(15000)
            logger.info("✅ 自動更新已啟用")
        else:
            self.decision_timer.stop()
            logger.info("⏸️ 自動更新已停用")
    
    def update_decisions(self):
        """更新決策顯示"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            # 獲取當前交易對
            current_pair = self.pair_combo.currentText()
            
            # 生成模擬決策數據
            decisions = self.generate_mock_decisions(current_pair)
            
            # 清空現有決策卡片
            for i in reversed(range(self.decision_layout.count())):
                child = self.decision_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            # 添加新的決策卡片
            for decision in decisions:
                card = DecisionCard(decision)
                self.decision_layout.addWidget(card)
                
                # 保存到歷史記錄
                self.save_decision_to_history(decision)
            
            self.decision_layout.addStretch()
            
            logger.info(f"✅ 更新了 {len(decisions)} 個AI決策")
            
        except Exception as e:
            logger.error(f"❌ 更新決策失敗: {e}")
    
    def generate_mock_decisions(self, trading_pair: str) -> List[Dict[str, Any]]:
        """生成模擬決策數據"""
        import random
        
        ai_models = [
            {"name": "🚀 市場掃描員", "type": "scanner"},
            {"name": "🔍 深度分析師", "type": "analyst"},
            {"name": "📈 趨勢分析師", "type": "trend"},
            {"name": "⚠️ 風險評估AI", "type": "risk"},
            {"name": "🧠 最終決策者", "type": "decision"}
        ]
        
        decisions = []
        current_time = datetime.now()
        
        for i, model in enumerate(ai_models):
            # 生成隨機決策
            decision_types = ["BUY", "SELL", "HOLD"]
            decision = random.choice(decision_types)
            confidence = random.uniform(0.6, 0.95)
            
            # 生成決策理由
            reasons = {
                "BUY": [
                    "技術指標顯示強烈買入信號",
                    "突破關鍵阻力位，成交量放大",
                    "RSI指標顯示超賣狀態，預期反彈"
                ],
                "SELL": [
                    "技術指標顯示賣出信號",
                    "跌破重要支撐位，趨勢轉弱",
                    "RSI指標顯示超買狀態，預期回調"
                ],
                "HOLD": [
                    "市場橫盤整理，等待明確信號",
                    "技術指標中性，建議觀望",
                    "波動率較低，缺乏明確方向"
                ]
            }
            
            reasoning = random.choice(reasons[decision])
            
            # 生成技術指標
            indicators = {
                "RSI": f"{random.randint(20, 80)}",
                "MACD": f"{random.uniform(-0.5, 0.5):.3f}",
                "MA20": f"{random.randint(1480000, 1520000):,}",
                "Volume": f"{random.randint(800, 1200)}M"
            }
            
            decisions.append({
                "model_name": model["name"],
                "model_type": model["type"],
                "trading_pair": trading_pair,
                "decision": decision,
                "confidence": confidence,
                "reasoning": reasoning,
                "technical_indicators": indicators,
                "timestamp": current_time - timedelta(seconds=i*30)
            })
        
        return decisions 
   
    def save_decision_to_history(self, decision: Dict[str, Any]):
        """保存決策到歷史記錄"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO decision_history 
                (timestamp, model_name, trading_pair, decision, confidence, reasoning, technical_indicators)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                decision['timestamp'].isoformat(),
                decision['model_name'],
                decision['trading_pair'],
                decision['decision'],
                decision['confidence'],
                decision['reasoning'],
                json.dumps(decision['technical_indicators'])
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ 保存決策歷史失敗: {e}")
    
    def apply_history_filter(self):
        """應用歷史篩選"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            start_time = self.start_datetime.dateTime().toPython()
            end_time = self.end_datetime.dateTime().toPython()
            decision_filter = self.decision_filter.currentText()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 構建查詢
            query = '''
                SELECT timestamp, model_name, decision, confidence, reasoning, technical_indicators, result
                FROM decision_history 
                WHERE timestamp BETWEEN ? AND ?
            '''
            params = [start_time.isoformat(), end_time.isoformat()]
            
            if decision_filter != "全部":
                query += " AND decision = ?"
                params.append(decision_filter)
            
            query += " ORDER BY timestamp DESC LIMIT 100"
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # 更新表格
            self.history_table.setRowCount(len(results))
            
            for row, result in enumerate(results):
                timestamp, model_name, decision, confidence, reasoning, indicators, result_status = result
                
                # 格式化時間戳
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%m-%d %H:%M:%S")
                
                self.history_table.setItem(row, 0, QTableWidgetItem(time_str))
                self.history_table.setItem(row, 1, QTableWidgetItem(model_name))
                
                # 決策項目帶顏色
                decision_item = QTableWidgetItem(decision)
                if decision == "BUY":
                    decision_item.setBackground(QColor(144, 238, 144))
                elif decision == "SELL":
                    decision_item.setBackground(QColor(255, 182, 193))
                else:
                    decision_item.setBackground(QColor(255, 255, 224))
                
                self.history_table.setItem(row, 2, decision_item)
                self.history_table.setItem(row, 3, QTableWidgetItem(f"{confidence:.1%}"))
                self.history_table.setItem(row, 4, QTableWidgetItem(reasoning))
                
                # 格式化技術指標
                try:
                    indicators_dict = json.loads(indicators) if indicators else {}
                    indicators_str = ", ".join([f"{k}:{v}" for k, v in indicators_dict.items()])
                except:
                    indicators_str = indicators or ""
                
                self.history_table.setItem(row, 5, QTableWidgetItem(indicators_str))
                self.history_table.setItem(row, 6, QTableWidgetItem(result_status or "待確認"))
            
            conn.close()
            
            logger.info(f"✅ 載入了 {len(results)} 條歷史決策記錄")
            
        except Exception as e:
            logger.error(f"❌ 載入歷史記錄失敗: {e}")
    
    def update_analysis(self):
        """更新決策分析"""
        if not PYQT_AVAILABLE:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 獲取統計數據
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_decisions,
                    COUNT(CASE WHEN decision = 'BUY' THEN 1 END) as buy_count,
                    COUNT(CASE WHEN decision = 'SELL' THEN 1 END) as sell_count,
                    COUNT(CASE WHEN decision = 'HOLD' THEN 1 END) as hold_count,
                    AVG(confidence) as avg_confidence
                FROM decision_history 
                WHERE timestamp >= datetime('now', '-24 hours')
            ''')
            
            stats = cursor.fetchone()
            
            if stats and stats[0] > 0:
                total, buy, sell, hold, avg_conf = stats
                
                stats_text = f"""
📊 過去24小時決策統計:
• 總決策數: {total}
• 買入決策: {buy} ({buy/total:.1%})
• 賣出決策: {sell} ({sell/total:.1%})
• 持有決策: {hold} ({hold/total:.1%})
• 平均信心度: {avg_conf:.1%}
                """.strip()
                
                self.stats_text.setPlainText(stats_text)
            
            # 獲取模型性能數據
            cursor.execute('''
                SELECT 
                    model_name,
                    COUNT(*) as decision_count,
                    AVG(confidence) as avg_confidence,
                    MAX(timestamp) as last_decision
                FROM decision_history 
                WHERE timestamp >= datetime('now', '-24 hours')
                GROUP BY model_name
                ORDER BY decision_count DESC
            ''')
            
            model_stats = cursor.fetchall()
            
            self.performance_table.setRowCount(len(model_stats))
            
            for row, (model_name, count, avg_conf, last_time) in enumerate(model_stats):
                self.performance_table.setItem(row, 0, QTableWidgetItem(model_name))
                self.performance_table.setItem(row, 1, QTableWidgetItem(str(count)))
                self.performance_table.setItem(row, 2, QTableWidgetItem("N/A"))  # 準確率需要實際結果
                self.performance_table.setItem(row, 3, QTableWidgetItem(f"{avg_conf:.1%}"))
                
                # 格式化最後決策時間
                last_dt = datetime.fromisoformat(last_time)
                last_str = last_dt.strftime("%H:%M:%S")
                self.performance_table.setItem(row, 4, QTableWidgetItem(last_str))
            
            conn.close()
            
            logger.info("✅ 決策分析更新完成")
            
        except Exception as e:
            logger.error(f"❌ 更新決策分析失敗: {e}")

def create_ai_decision_visualization():
    """創建AI決策可視化組件實例"""
    return AIDecisionVisualization()

# 測試函數
def main():
    """測試主函數"""
    if PYQT_AVAILABLE:
        from PyQt6.QtWidgets import QApplication
        import sys
        
        app = QApplication(sys.argv)
        
        # 創建測試窗口
        widget = AIDecisionVisualization()
        widget.setWindowTitle("AI決策可視化測試")
        widget.resize(1000, 700)
        widget.show()
        
        # 模擬更新決策
        widget.update_decisions()
        
        sys.exit(app.exec())
    else:
        print("🖥️ PyQt6未安裝，無法運行GUI測試")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()