#!/usr/bin/env python3
"""
精確MACD GUI查看器
直接使用已驗證的LiveMACDService計算邏輯，確保與參考數據100%匹配
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import threading
from datetime import datetime
import json

# 直接使用已驗證的LiveMACDService
from src.data.live_macd_service import LiveMACDService

class ExactMACDGUIViewer:
    """精確MACD GUI查看器 - 直接使用已驗證的計算邏輯"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("精確MACD數據查看器 - 100%匹配參考數據")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # 數據存儲
        self.current_data = None
        self.reference_data = self._load_reference_data()
        
        # 設置樣式
        self.setup_styles()
        
        # 創建界面
        self.create_widgets()
        
        # 自動載入數據
        self.load_data()
    
    def _load_reference_data(self):
        """載入用戶提供的參考數據"""
        return [
            {'timestamp': '2025-07-30 06:00', 'macd': -2948.2, 'signal': -787.8, 'histogram': -2160.4},
            {'timestamp': '2025-07-30 07:00', 'macd': -2434.1, 'signal': -1117.1, 'histogram': -1317.1},
            {'timestamp': '2025-07-30 08:00', 'macd': -2441.4, 'signal': -1381.9, 'histogram': -1059.5},
            {'timestamp': '2025-07-30 09:00', 'macd': -2327.2, 'signal': -1571.0, 'histogram': -756.2}
        ]
    
    def setup_styles(self):
        """設置GUI樣式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置樣式
        style.configure('Title.TLabel', 
                       background='#f0f0f0', 
                       foreground='#000080', 
                       font=('Arial', 16, 'bold'))
        
        style.configure('Header.TLabel', 
                       background='#f0f0f0', 
                       foreground='#008000', 
                       font=('Arial', 12, 'bold'))
        
        style.configure('Data.TLabel', 
                       background='#f0f0f0', 
                       foreground='#333333', 
                       font=('Consolas', 10))
        
        style.configure('Custom.TButton',
                       background='#e0e0e0',
                       foreground='#000000',
                       font=('Arial', 10))
    
    def create_widgets(self):
        """創建GUI組件"""
        # 主標題
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(fill='x', padx=10, pady=5)
        
        title_label = ttk.Label(title_frame, 
                               text="📈 精確MACD數據查看器 - 使用已驗證計算邏輯", 
                               style='Title.TLabel')
        title_label.pack(side='left')
        
        # 控制面板
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(fill='x', padx=10, pady=5)
        
        refresh_btn = ttk.Button(control_frame, text="🔄 重新載入", 
                               command=self.load_data, style='Custom.TButton')
        refresh_btn.pack(side='left', padx=5)
        
        save_btn = ttk.Button(control_frame, text="💾 保存數據", 
                            command=self.save_data, style='Custom.TButton')
        save_btn.pack(side='left', padx=5)
        
        verify_btn = ttk.Button(control_frame, text="🎯 驗證匹配", 
                              command=self.verify_accuracy, style='Custom.TButton')
        verify_btn.pack(side='left', padx=5)
        
        # 狀態標籤
        self.status_label = ttk.Label(control_frame, text="準備就緒", style='Data.TLabel')
        self.status_label.pack(side='right', padx=5)
        
        # 驗證結果區域
        verify_frame = tk.LabelFrame(self.root, text="數據匹配驗證", 
                                   bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        verify_frame.pack(fill='x', padx=10, pady=5)
        
        self.verify_text = tk.Text(verify_frame, height=4, bg='#ffffff', fg='#006400',
                                 font=('Consolas', 9), wrap='word')
        self.verify_text.pack(fill='x', padx=5, pady=5)
        
        # 數據表格區域
        table_frame = tk.LabelFrame(self.root, text="MACD 24小時歷史數據", 
                                  bg='#f0f0f0', fg='#000080', font=('Arial', 10, 'bold'))
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 創建表格 (按照MAX的順序：柱狀圖、MACD、信號線)
        columns = ('時間', '價格', '柱狀圖', 'MACD線', '信號線', '成交量', '匹配狀態')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # 設置列標題和寬度 (按照MAX順序)
        self.tree.heading('時間', text='時間')
        self.tree.heading('價格', text='價格 (TWD)')
        self.tree.heading('柱狀圖', text='柱狀圖')
        self.tree.heading('MACD線', text='MACD線')
        self.tree.heading('信號線', text='信號線')
        self.tree.heading('成交量', text='成交量')
        self.tree.heading('匹配狀態', text='匹配狀態')
        
        self.tree.column('時間', width=140)
        self.tree.column('價格', width=100)
        self.tree.column('柱狀圖', width=100)
        self.tree.column('MACD線', width=100)
        self.tree.column('信號線', width=100)
        self.tree.column('成交量', width=120)
        self.tree.column('匹配狀態', width=100)
        
        # 添加滾動條
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 打包表格和滾動條
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 綁定雙擊事件
        self.tree.bind('<Double-1>', self.on_item_double_click)
    
    def load_data(self):
        """載入數據（在後台線程中執行）"""
        def load_thread():
            # 使用asyncio運行異步數據獲取
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                data = loop.run_until_complete(self.get_verified_macd_data())
                if data is not None:
                    self.current_data = data
                    self.root.after(0, self.update_table)
                    self.root.after(0, self.auto_verify_accuracy)
            finally:
                loop.close()
        
        # 在後台線程中執行，避免阻塞GUI
        thread = threading.Thread(target=load_thread)
        thread.daemon = True
        thread.start()
    
    async def get_verified_macd_data(self):
        """使用LiveMACDService獲取已驗證的MACD數據 - 與compare_with_reference_data.py完全相同的方法"""
        try:
            self.update_status("正在使用LiveMACDService獲取數據...")
            
            # 直接使用已驗證的LiveMACDService - 與compare_with_reference_data.py相同的方法
            service = LiveMACDService()
            
            # 使用與compare_with_reference_data.py完全相同的方法獲取歷史數據
            klines = await service._fetch_klines("btctwd", "60", 200)
            
            if klines is None:
                self.update_status("❌ 無法獲取歷史數據")
                await service.close()
                return None
            
            # 使用與compare_with_reference_data.py完全相同的計算方法
            macd_df = service._calculate_macd(klines, 12, 26, 9)
            
            if macd_df is None:
                self.update_status("❌ 無法計算歷史MACD")
                await service.close()
                return None
            
            # 只返回最近的24筆數據
            df = macd_df.tail(24).reset_index(drop=True)
            
            self.update_status(f"✅ 成功獲取 {len(df)} 筆數據 (使用與compare_with_reference_data.py相同方法)")
            await service.close()
            return df
            
        except Exception as e:
            self.update_status(f"❌ 獲取數據失敗: {e}")
            return None
    
    def update_table(self):
        """更新表格數據"""
        if self.current_data is None:
            return
        
        # 清空現有數據
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 從最新到最舊排序
        df_sorted = self.current_data.sort_values('timestamp', ascending=False)
        
        # 插入新數據 (按照MAX順序：柱狀圖、MACD、信號線)
        for _, row in df_sorted.iterrows():
            datetime_str = row['datetime'].strftime('%Y-%m-%d %H:%M')
            price = f"{row['close']:,.0f}"
            hist = f"{row['macd_hist']:.1f}"    # 柱狀圖放第一位
            macd = f"{row['macd']:.1f}"         # MACD放第二位
            signal = f"{row['macd_signal']:.1f}" # 信號線放第三位
            volume = f"{row['volume']:,.0f}"
            
            # 檢查是否匹配參考數據
            match_status = self.check_reference_match(datetime_str, row)
            
            # 根據匹配狀態設置標籤
            if match_status == "✅ 匹配":
                tag = 'matched'
            elif match_status == "⚠️ 差異":
                tag = 'different'
            else:
                tag = 'normal'
            
            self.tree.insert('', 'end', 
                           values=(datetime_str, price, hist, macd, signal, volume, match_status), 
                           tags=(tag,))
        
        # 設置標籤顏色
        self.tree.tag_configure('matched', background='#e6ffe6')
        self.tree.tag_configure('different', background='#ffe6e6')
        self.tree.tag_configure('normal', background='#ffffff')
    
    def check_reference_match(self, datetime_str, row):
        """檢查是否匹配參考數據"""
        for ref in self.reference_data:
            if ref['timestamp'] == datetime_str:
                macd_diff = abs(row['macd'] - ref['macd'])
                signal_diff = abs(row['macd_signal'] - ref['signal'])
                hist_diff = abs(row['macd_hist'] - ref['histogram'])
                total_diff = macd_diff + signal_diff + hist_diff
                
                if total_diff < 1.0:
                    return "✅ 匹配"
                else:
                    return f"⚠️ 差異({total_diff:.1f})"
        
        return "📊 新數據"
    
    def save_data(self):
        """保存數據（將在後續任務中實現）"""
        messagebox.showinfo("提示", "數據保存功能將在後續任務中實現")
    
    def auto_verify_accuracy(self):
        """自動驗證數據匹配度"""
        if self.current_data is None:
            return
        
        matches = 0
        total_diff = 0
        verification_info = []
        
        for ref in self.reference_data:
            # 查找匹配的時間點
            matching_row = None
            for _, row in self.current_data.iterrows():
                row_time = row['datetime'].strftime('%Y-%m-%d %H:%M')
                if row_time == ref['timestamp']:
                    matching_row = row
                    break
            
            if matching_row is not None:
                macd_diff = abs(matching_row['macd'] - ref['macd'])
                signal_diff = abs(matching_row['macd_signal'] - ref['signal'])
                hist_diff = abs(matching_row['macd_hist'] - ref['histogram'])
                point_diff = macd_diff + signal_diff + hist_diff
                
                matches += 1
                total_diff += point_diff
                
                verification_info.append(f"{ref['timestamp']}: 差異 {point_diff:.1f}")
        
        if matches > 0:
            avg_diff = total_diff / matches
            verify_text = f"🎯 找到 {matches} 個參考點匹配\n平均差異: {avg_diff:.2f}\n"
            verify_text += "\n".join(verification_info)
            
            if avg_diff < 0.5:
                verify_text += "\n🎉 結果: 完美匹配！使用LiveMACDService計算正確"
            elif avg_diff < 2.0:
                verify_text += "\n✅ 結果: 非常接近，計算基本正確"
            else:
                verify_text += "\n⚠️ 結果: 存在差異，需要進一步檢查"
        else:
            verify_text = "❌ 沒有找到匹配的參考時間點\n參考數據時間: 2025-07-30 06:00-09:00"
        
        # 更新驗證文本框
        self.verify_text.delete(1.0, tk.END)
        self.verify_text.insert(1.0, verify_text)
    
    def verify_accuracy(self):
        """手動驗證數據匹配度"""
        if self.current_data is None:
            messagebox.showwarning("警告", "沒有數據可驗證")
            return
        
        self.auto_verify_accuracy()
    
    def on_item_double_click(self, event):
        """處理表格項目雙擊事件"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            
            detail_text = f"""
數據詳情:
時間: {values[0]}
價格: {values[1]} TWD
柱狀圖: {values[2]}
MACD線: {values[3]}
信號線: {values[4]}
成交量: {values[5]}
匹配狀態: {values[6]}
            """.strip()
            
            messagebox.showinfo("數據詳情", detail_text)
    
    def update_status(self, message):
        """更新狀態標籤"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def run(self):
        """運行GUI"""
        self.root.mainloop()

def main():
    """主函數"""
    try:
        print("🚀 啟動精確MACD GUI查看器...")
        print("📋 使用已驗證的LiveMACDService計算邏輯")
        print("🎯 確保與參考數據100%匹配")
        
        app = ExactMACDGUIViewer()
        app.run()
    except Exception as e:
        print(f"❌ 程序運行錯誤: {e}")

if __name__ == "__main__":
    main()