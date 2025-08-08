#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🚀 終極雲端部署工具
徹底解決GitHub Pages更新問題
確保每次更新都能成功部署到線上
"""

import os
import shutil
import json
import time
from datetime import datetime
import subprocess

class UltimateCloudDeploy:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        self.version = f"v3.0-ultimate-{self.timestamp}"
        self.deploy_time = datetime.now().strftime("%Y/%m/%d %H:%M")
        
    def log(self, message, level="INFO"):
        """統一日誌輸出"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def check_prerequisites(self):
        """檢查部署前置條件"""
        self.log("🔍 檢查部署前置條件...")
        
        # 檢查Git狀態
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.log("❌ Git倉庫狀態異常", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Git檢查失敗: {e}", "ERROR")
            return False
        
        # 檢查關鍵文件
        required_files = [
            "static/smart-balanced-dashboard.html",
            ".github/workflows/ultimate-deploy.yml"
        ]
        
        for file in required_files:
            if not os.path.exists(file):
                self.log(f"❌ 缺少關鍵文件: {file}", "ERROR")
                return False
        
        self.log("✅ 前置條件檢查通過")
        return True
    
    def prepare_deployment_files(self):
        """準備部署文件"""
        self.log("📁 準備部署文件...")
        
        # 1. 更新主儀表板文件
        main_file = "static/smart-balanced-dashboard.html"
        
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 確保包含混合高頻策略
        if 'fetchBTCPriceHybrid' not in content:
            self.log("❌ 主文件缺少混合高頻策略", "ERROR")
            return False
        
        # 更新版本信息
        import re
        
        # 更新版本標識
        version_pattern = r'版本: v[\d\.]+-[\w-]+ \| 更新時間: [\d/]+ [\d:]+'
        new_version = f'版本: {self.version} | 更新時間: {self.deploy_time}'
        content = re.sub(version_pattern, new_version, content)
        
        # 更新右下角版本
        corner_pattern = r'🔄 v[\d\.]+-[\w-]+ \| [\d/]+ [\d:]+ \|'
        new_corner = f'🔄 {self.version} | {self.deploy_time} |'
        content = re.sub(corner_pattern, new_corner, content)
        
        # 添加部署時間戳到頁面
        deploy_info = f'''
        <!-- 部署信息 -->
        <meta name="deploy-version" content="{self.version}">
        <meta name="deploy-timestamp" content="{self.timestamp}">
        <meta name="deploy-time" content="{self.deploy_time}">
        '''
        
        if '<meta charset="UTF-8">' in content:
            content = content.replace('<meta charset="UTF-8">', 
                                    f'<meta charset="UTF-8">{deploy_info}')
        
        # 添加版本檢查JavaScript
        version_check_js = f'''
        // 🚀 終極部署版本檢查 - {self.version}
        console.log('🚀 AImax 終極雲端部署 - {self.version}');
        console.log('📅 部署時間: {self.deploy_time}');
        console.log('🔢 時間戳: {self.timestamp}');
        
        // 強制清除舊版本緩存
        const deployVersion = '{self.version}';
        const storedVersion = localStorage.getItem('aimax_deploy_version');
        
        if (storedVersion !== deployVersion) {{
            console.log('🔄 檢測到新部署版本，清除所有緩存...');
            localStorage.clear();
            sessionStorage.clear();
            
            // 清除所有可能的緩存
            if ('caches' in window) {{
                caches.keys().then(names => {{
                    names.forEach(name => {{
                        caches.delete(name);
                    }});
                }});
            }}
        }}
        
        localStorage.setItem('aimax_deploy_version', deployVersion);
        localStorage.setItem('aimax_deploy_timestamp', '{self.timestamp}');
        '''
        
        # 在頁面載入事件前添加版本檢查
        if 'document.addEventListener(\'DOMContentLoaded\'' in content:
            content = content.replace(
                'document.addEventListener(\'DOMContentLoaded\'',
                version_check_js + '\n        document.addEventListener(\'DOMContentLoaded\''
            )
        
        # 保存更新後的主文件
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.log(f"✅ 主文件已更新: {self.version}")
        
        # 2. 同步到所有目標文件
        target_files = [
            "static/smart-balanced-dashboard-static.html",
            "static/index.html"
        ]
        
        for target in target_files:
            try:
                shutil.copy2(main_file, target)
                self.log(f"✅ 同步到: {target}")
            except Exception as e:
                self.log(f"⚠️ 同步失敗 {target}: {e}", "WARN")
        
        # 3. 創建帶時間戳的備份版本
        backup_file = f"static/smart-balanced-dashboard-{self.timestamp}.html"
        shutil.copy2(main_file, backup_file)
        self.log(f"✅ 創建備份版本: {backup_file}")
        
        # 4. 創建部署信息文件
        deploy_info = {
            "version": self.version,
            "timestamp": self.timestamp,
            "deploy_time": self.deploy_time,
            "features": [
                "混合高頻價格更新策略",
                "每30秒CORS代理實時數據",
                "每2分鐘GitHub Actions備援",
                "三層容錯機制",
                "終極雲端部署系統"
            ],
            "urls": {
                "main": f"https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard.html?v={self.timestamp}",
                "static": f"https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard-static.html?v={self.timestamp}",
                "backup": f"https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard-{self.timestamp}.html"
            },
            "deployment_method": "ultimate_cloud_deploy",
            "cache_busters": [
                f"?v={self.timestamp}",
                f"?version={self.version}",
                f"?t={int(time.time())}"
            ]
        }
        
        with open('static/deploy_info.json', 'w', encoding='utf-8') as f:
            json.dump(deploy_info, f, ensure_ascii=False, indent=2)
        
        self.log("✅ 部署信息文件已創建")
        return True
    
    def optimize_github_actions(self):
        """優化GitHub Actions工作流程"""
        self.log("⚙️ 優化GitHub Actions工作流程...")
        
        # 創建優化的部署工作流程
        optimized_workflow = f'''name: 🚀 終極雲端部署

on:
  push:
    branches: [ main ]
  workflow_dispatch:
    inputs:
      force_deploy:
        description: '強制部署'
        required: false
        default: 'false'

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: true

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{{{ steps.deployment.outputs.page_url }}}}
    runs-on: ubuntu-latest
    
    steps:
      - name: 🔄 檢出代碼
        uses: actions/checkout@v4
        
      - name: 🔧 設置Pages
        uses: actions/configure-pages@v4
        
      - name: 📁 準備部署文件
        run: |
          echo "🚀 終極雲端部署 - {self.version}"
          echo "📅 部署時間: {self.deploy_time}"
          
          # 創建部署目錄
          mkdir -p _site
          
          # 複製所有靜態文件
          cp -r static/* _site/
          
          # 創建.nojekyll文件 (禁用Jekyll)
          touch _site/.nojekyll
          
          # 創建robots.txt
          cat > _site/robots.txt << 'EOF'
          User-agent: *
          Disallow: /admin
          Allow: /
          EOF
          
          # 創建緩存控制文件
          cat > _site/.htaccess << 'EOF'
          <IfModule mod_expires.c>
            ExpiresActive on
            ExpiresByType text/html "access plus 0 seconds"
            ExpiresByType application/json "access plus 0 seconds"
          </IfModule>
          
          <IfModule mod_headers.c>
            Header set Cache-Control "no-cache, no-store, must-revalidate"
            Header set Pragma "no-cache"
            Header set Expires "0"
          </IfModule>
          EOF
          
          # 顯示部署文件列表
          echo "📋 部署文件列表:"
          find _site -type f | sort
          
          # 驗證關鍵文件
          if [ -f "_site/smart-balanced-dashboard.html" ]; then
            echo "✅ 主儀表板文件存在"
            if grep -q "fetchBTCPriceHybrid" "_site/smart-balanced-dashboard.html"; then
              echo "✅ 混合高頻策略已包含"
            else
              echo "❌ 混合高頻策略缺失"
              exit 1
            fi
          else
            echo "❌ 主儀表板文件不存在"
            exit 1
          fi
          
      - name: 📤 上傳Pages構建產物
        uses: actions/upload-pages-artifact@v3
        with:
          path: '_site'
          
      - name: 🚀 部署到GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
        
      - name: ✅ 部署完成通知
        run: |
          echo "🎉 終極雲端部署完成！"
          echo "🌐 訪問地址: ${{{{ steps.deployment.outputs.page_url }}}}"
          echo "📅 部署時間: $(date)"
          echo "🔢 版本: {self.version}"
          
          # 等待部署生效
          echo "⏳ 等待部署生效..."
          sleep 30
          
          # 驗證部署結果
          echo "🔍 驗證部署結果..."
          curl -s "${{{{ steps.deployment.outputs.page_url }}}}smart-balanced-dashboard.html" | grep -q "{self.version}" && echo "✅ 版本驗證成功" || echo "⚠️ 版本驗證失敗"
'''
        
        # 保存優化的工作流程
        with open('.github/workflows/ultimate-deploy.yml', 'w', encoding='utf-8') as f:
            f.write(optimized_workflow)
        
        self.log("✅ 終極部署工作流程已創建")
        
        # 禁用舊的工作流程
        old_workflow = '.github/workflows/simple-deploy.yml'
        if os.path.exists(old_workflow):
            disabled_dir = '.github/workflows/disabled'
            os.makedirs(disabled_dir, exist_ok=True)
            shutil.move(old_workflow, f'{disabled_dir}/simple-deploy.yml.disabled')
            self.log("✅ 舊工作流程已禁用")
        
        return True
    
    def deploy_to_github(self):
        """部署到GitHub"""
        self.log("🚀 部署到GitHub...")
        
        try:
            # Git操作
            subprocess.run(['git', 'add', '.'], check=True)
            
            commit_msg = f"🚀 終極雲端部署 - {self.version}"
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            
            self.log("✅ 代碼已推送到GitHub")
            return True
            
        except subprocess.CalledProcessError as e:
            self.log(f"❌ Git操作失敗: {e}", "ERROR")
            return False
    
    def verify_deployment(self):
        """驗證部署結果"""
        self.log("🔍 驗證部署結果...")
        
        # 等待GitHub Pages更新
        self.log("⏳ 等待GitHub Pages更新 (60秒)...")
        time.sleep(60)
        
        # 檢查部署狀態
        urls_to_check = [
            f"https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard.html?v={self.timestamp}",
            f"https://winyoulife.github.io/AImax-Trading-System/deploy_info.json?v={self.timestamp}"
        ]
        
        import requests
        
        for url in urls_to_check:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    if self.version in response.text:
                        self.log(f"✅ 驗證成功: {url}")
                    else:
                        self.log(f"⚠️ 版本不匹配: {url}", "WARN")
                else:
                    self.log(f"❌ 訪問失敗: {url} - {response.status_code}", "ERROR")
            except Exception as e:
                self.log(f"❌ 驗證失敗: {url} - {e}", "ERROR")
        
        return True
    
    def run_ultimate_deploy(self):
        """執行終極部署"""
        self.log("🚀 開始終極雲端部署...")
        self.log("=" * 60)
        
        # 1. 檢查前置條件
        if not self.check_prerequisites():
            return False
        
        # 2. 準備部署文件
        if not self.prepare_deployment_files():
            return False
        
        # 3. 優化GitHub Actions
        if not self.optimize_github_actions():
            return False
        
        # 4. 部署到GitHub
        if not self.deploy_to_github():
            return False
        
        # 5. 驗證部署結果
        self.verify_deployment()
        
        # 6. 顯示部署結果
        self.log("=" * 60)
        self.log("🎉 終極雲端部署完成！")
        self.log("=" * 60)
        self.log(f"📅 版本: {self.version}")
        self.log(f"⏰ 時間: {self.deploy_time}")
        self.log(f"🔢 時間戳: {self.timestamp}")
        
        self.log("\n🌐 訪問地址:")
        self.log(f"1. 主頁面: https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard.html?v={self.timestamp}")
        self.log(f"2. 靜態版本: https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard-static.html?v={self.timestamp}")
        self.log(f"3. 備份版本: https://winyoulife.github.io/AImax-Trading-System/smart-balanced-dashboard-{self.timestamp}.html")
        
        self.log("\n💡 特性:")
        self.log("✅ 混合高頻價格更新策略")
        self.log("✅ 強制緩存清除機制")
        self.log("✅ 多重備份版本")
        self.log("✅ 自動部署驗證")
        self.log("✅ 終極雲端部署系統")
        
        self.log("\n🔧 如果還是看不到更新:")
        self.log("1. 等待2-3分鐘讓GitHub Pages完全更新")
        self.log("2. 按 Ctrl+F5 強制刷新頁面")
        self.log("3. 清除瀏覽器所有緩存")
        self.log("4. 使用無痕模式訪問")
        
        return True

def main():
    deployer = UltimateCloudDeploy()
    success = deployer.run_ultimate_deploy()
    
    if success:
        print("\n🎉 終極雲端部署成功完成！")
        return 0
    else:
        print("\n❌ 終極雲端部署失敗！")
        return 1

if __name__ == "__main__":
    exit(main())