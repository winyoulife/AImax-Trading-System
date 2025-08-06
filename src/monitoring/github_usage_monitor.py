#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AImax GitHub Actions使用量監控 - 任務10實現
專門監控GitHub Actions使用量，確保在免費額度內運行
"""

import sys
import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

@dataclass
class WorkflowRun:
    """工作流運行記錄"""
    id: int
    name: str
    status: str
    conclusion: str
    created_at: datetime
    updated_at: datetime
    duration_minutes: float
    billable_minutes: int
    workflow_name: str

@dataclass
class GitHubQuota:
    """GitHub配額信息"""
    total_minutes: int
    used_minutes: int
    remaining_minutes: int
    usage_percentage: float
    reset_date: datetime
    included_minutes: int
    paid_minutes: int

class GitHubUsageMonitor:
    """GitHub Actions使用量監控器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.workflow_runs: List[WorkflowRun] = []
        self.quota_history: List[GitHubQuota] = []
        
        # GitHub配置
        self.github_config = {
            'api_base': 'https://api.github.com',
            'token': os.environ.get('GITHUB_TOKEN'),
            'owner': os.environ.get('GITHUB_REPOSITORY_OWNER'),
            'repo': os.environ.get('GITHUB_REPOSITORY', '').split('/')[-1] if os.environ.get('GITHUB_REPOSITORY') else None
        }
        
        # 免費額度限制
        self.free_tier_limits = {
            'monthly_minutes': 2000,  # GitHub免費用戶每月2000分鐘
            'storage_gb': 0.5,        # 500MB存儲空間
            'concurrent_jobs': 20,    # 最多20個並發作業
            'job_timeout_hours': 6    # 單個作業最長6小時
        }
        
        # 警告閾值
        self.alert_thresholds = {
            'usage_warning': 75.0,    # 75%使用量警告
            'usage_critical': 90.0,   # 90%使用量危險
            'daily_limit': 100,       # 每日使用限制（分鐘）
            'workflow_duration': 30   # 單個工作流超時警告（分鐘）
        }
        
        self.setup_github_config()
    
    def setup_github_config(self):
        """設置GitHub配置"""
        # 嘗試從git配置獲取倉庫信息
        try:
            import subprocess
            result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                remote_url = result.stdout.strip()
                if 'github.com' in remote_url:
                    # 解析GitHub倉庫信息
                    if remote_url.endswith('.git'):
                        remote_url = remote_url[:-4]
                    
                    if 'github.com/' in remote_url:
                        repo_part = remote_url.split('github.com/')[-1]
                        parts = repo_part.split('/')
                        if len(parts) >= 2:
                            self.github_config['owner'] = parts[0]
                            self.github_config['repo'] = parts[1]
        except Exception as e:
            logger.warning(f"無法獲取Git倉庫信息: {e}")
    
    def can_access_github_api(self) -> bool:
        """檢查是否可以訪問GitHub API"""
        return (self.github_config['token'] and 
                self.github_config['owner'] and 
                self.github_config['repo'])
    
    def get_current_quota(self) -> Optional[GitHubQuota]:
        """獲取當前GitHub Actions配額"""
        if not self.can_access_github_api():
            logger.warning("⚠️ 無法訪問GitHub API，請檢查配置")
            return None
        
        try:
            headers = {
                'Authorization': f"token {self.github_config['token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 獲取Actions計費信息
            billing_url = f"{self.github_config['api_base']}/repos/{self.github_config['owner']}/{self.github_config['repo']}/actions/billing"
            
            response = requests.get(billing_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                billing_data = response.json()
                
                total_minutes = billing_data.get('total_minutes_used', 0)
                included_minutes = billing_data.get('included_minutes', self.free_tier_limits['monthly_minutes'])
                paid_minutes = billing_data.get('total_paid_minutes_used', 0)
                
                remaining_minutes = max(0, included_minutes - total_minutes)
                usage_percentage = (total_minutes / included_minutes * 100) if included_minutes > 0 else 0
                
                # 計算重置日期（每月1號）
                now = datetime.now()
                if now.day == 1:
                    reset_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                else:
                    next_month = now.replace(day=1) + timedelta(days=32)
                    reset_date = next_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                
                quota = GitHubQuota(
                    total_minutes=total_minutes,
                    used_minutes=total_minutes,
                    remaining_minutes=remaining_minutes,
                    usage_percentage=usage_percentage,
                    reset_date=reset_date,
                    included_minutes=included_minutes,
                    paid_minutes=paid_minutes
                )
                
                self.quota_history.append(quota)
                return quota
            
            elif response.status_code == 403:
                logger.error("❌ GitHub API訪問被拒絕，請檢查token權限")
                return None
            else:
                logger.error(f"❌ GitHub API請求失敗: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 獲取GitHub配額失敗: {e}")
            return None
    
    def get_workflow_runs(self, days: int = 7) -> List[WorkflowRun]:
        """獲取工作流運行記錄"""
        if not self.can_access_github_api():
            return []
        
        try:
            headers = {
                'Authorization': f"token {self.github_config['token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # 獲取工作流運行記錄
            runs_url = f"{self.github_config['api_base']}/repos/{self.github_config['owner']}/{self.github_config['repo']}/actions/runs"
            
            # 設置查詢參數
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            params = {
                'per_page': 100,
                'created': f'>={since_date}'
            }
            
            response = requests.get(runs_url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                runs_data = response.json()
                workflow_runs = []
                
                for run in runs_data.get('workflow_runs', []):
                    created_at = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
                    updated_at = datetime.fromisoformat(run['updated_at'].replace('Z', '+00:00'))
                    
                    # 計算運行時間
                    duration_minutes = (updated_at - created_at).total_seconds() / 60
                    
                    # 估算計費分鐘數（簡化計算）
                    billable_minutes = max(1, int(duration_minutes)) if run['status'] == 'completed' else 0
                    
                    workflow_run = WorkflowRun(
                        id=run['id'],
                        name=run['name'],
                        status=run['status'],
                        conclusion=run['conclusion'] or 'unknown',
                        created_at=created_at,
                        updated_at=updated_at,
                        duration_minutes=duration_minutes,
                        billable_minutes=billable_minutes,
                        workflow_name=run['workflow_name'] if 'workflow_name' in run else run['name']
                    )
                    
                    workflow_runs.append(workflow_run)
                
                self.workflow_runs = workflow_runs
                return workflow_runs
            
            else:
                logger.error(f"❌ 獲取工作流運行記錄失敗: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 獲取工作流運行記錄失敗: {e}")
            return []
    
    def analyze_usage_patterns(self) -> Dict[str, Any]:
        """分析使用模式"""
        if not self.workflow_runs:
            return {'error': 'No workflow data available'}
        
        # 按工作流分組統計
        workflow_stats = {}
        total_duration = 0
        total_billable = 0
        
        for run in self.workflow_runs:
            workflow_name = run.workflow_name
            
            if workflow_name not in workflow_stats:
                workflow_stats[workflow_name] = {
                    'runs': 0,
                    'total_duration': 0,
                    'total_billable': 0,
                    'success_rate': 0,
                    'avg_duration': 0,
                    'statuses': {}
                }
            
            stats = workflow_stats[workflow_name]
            stats['runs'] += 1
            stats['total_duration'] += run.duration_minutes
            stats['total_billable'] += run.billable_minutes
            
            # 統計狀態
            status = run.conclusion if run.conclusion != 'unknown' else run.status
            stats['statuses'][status] = stats['statuses'].get(status, 0) + 1
            
            total_duration += run.duration_minutes
            total_billable += run.billable_minutes
        
        # 計算成功率和平均時間
        for workflow_name, stats in workflow_stats.items():
            successful_runs = stats['statuses'].get('success', 0)
            stats['success_rate'] = (successful_runs / stats['runs'] * 100) if stats['runs'] > 0 else 0
            stats['avg_duration'] = stats['total_duration'] / stats['runs'] if stats['runs'] > 0 else 0
        
        # 按使用量排序
        sorted_workflows = sorted(
            workflow_stats.items(), 
            key=lambda x: x[1]['total_billable'], 
            reverse=True
        )
        
        return {
            'total_runs': len(self.workflow_runs),
            'total_duration_minutes': total_duration,
            'total_billable_minutes': total_billable,
            'avg_duration_per_run': total_duration / len(self.workflow_runs) if self.workflow_runs else 0,
            'workflow_stats': dict(sorted_workflows),
            'most_used_workflow': sorted_workflows[0][0] if sorted_workflows else None,
            'analysis_period_days': 7
        }
    
    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """獲取優化建議"""
        suggestions = []
        
        # 獲取當前配額
        quota = self.get_current_quota()
        if quota:
            # 使用量過高警告
            if quota.usage_percentage >= self.alert_thresholds['usage_critical']:
                suggestions.append({
                    'priority': 'critical',
                    'category': 'Usage Limit',
                    'issue': f"GitHub Actions使用量危險 ({quota.usage_percentage:.1f}%)",
                    'suggestion': '立即減少工作流執行頻率',
                    'actions': [
                        '暫停非關鍵工作流',
                        '增加工作流觸發條件',
                        '優化工作流執行時間',
                        '考慮使用條件執行'
                    ]
                })
            elif quota.usage_percentage >= self.alert_thresholds['usage_warning']:
                suggestions.append({
                    'priority': 'high',
                    'category': 'Usage Warning',
                    'issue': f"GitHub Actions使用量警告 ({quota.usage_percentage:.1f}%)",
                    'suggestion': '優化工作流以減少使用量',
                    'actions': [
                        '減少工作流觸發頻率',
                        '合併相似的工作流',
                        '使用更高效的Actions',
                        '添加路徑過濾條件'
                    ]
                })
        
        # 分析工作流使用模式
        usage_analysis = self.analyze_usage_patterns()
        
        if 'workflow_stats' in usage_analysis:
            # 找出耗時最長的工作流
            longest_workflows = sorted(
                usage_analysis['workflow_stats'].items(),
                key=lambda x: x[1]['avg_duration'],
                reverse=True
            )[:3]
            
            for workflow_name, stats in longest_workflows:
                if stats['avg_duration'] > self.alert_thresholds['workflow_duration']:
                    suggestions.append({
                        'priority': 'medium',
                        'category': 'Workflow Optimization',
                        'issue': f"工作流 '{workflow_name}' 平均執行時間過長 ({stats['avg_duration']:.1f}分鐘)",
                        'suggestion': '優化工作流執行效率',
                        'actions': [
                            '並行化獨立的作業',
                            '使用緩存減少重複操作',
                            '優化依賴安裝過程',
                            '移除不必要的步驟'
                        ]
                    })
            
            # 找出失敗率高的工作流
            for workflow_name, stats in usage_analysis['workflow_stats'].items():
                if stats['success_rate'] < 80 and stats['runs'] >= 5:
                    suggestions.append({
                        'priority': 'medium',
                        'category': 'Reliability',
                        'issue': f"工作流 '{workflow_name}' 成功率較低 ({stats['success_rate']:.1f}%)",
                        'suggestion': '提高工作流穩定性',
                        'actions': [
                            '添加重試機制',
                            '改善錯誤處理',
                            '檢查依賴項穩定性',
                            '增加超時設置'
                        ]
                    })
        
        return suggestions
    
    def generate_usage_report(self) -> str:
        """生成使用量報告"""
        quota = self.get_current_quota()
        usage_analysis = self.analyze_usage_patterns()
        suggestions = self.get_optimization_suggestions()
        
        report = f"""
🚀 AImax GitHub Actions使用量報告
{'='*60}

📊 當前配額狀態:
"""
        
        if quota:
            report += f"""   總配額: {quota.included_minutes} 分鐘/月
   已使用: {quota.used_minutes} 分鐘 ({quota.usage_percentage:.1f}%)
   剩餘: {quota.remaining_minutes} 分鐘
   付費分鐘: {quota.paid_minutes} 分鐘
   配額重置: {quota.reset_date.strftime('%Y-%m-%d')}
"""
        else:
            report += "   ⚠️ 無法獲取配額信息，請檢查GitHub API配置\n"
        
        if 'error' not in usage_analysis:
            report += f"""
📈 使用統計 (最近7天):
   工作流運行次數: {usage_analysis['total_runs']}
   總執行時間: {usage_analysis['total_duration_minutes']:.1f} 分鐘
   總計費時間: {usage_analysis['total_billable_minutes']} 分鐘
   平均執行時間: {usage_analysis['avg_duration_per_run']:.1f} 分鐘/次
   最常用工作流: {usage_analysis['most_used_workflow'] or 'N/A'}

🔧 工作流詳細統計:
"""
            
            for workflow_name, stats in list(usage_analysis['workflow_stats'].items())[:5]:
                report += f"""   {workflow_name}:
     運行次數: {stats['runs']}
     總時間: {stats['total_duration']:.1f} 分鐘
     平均時間: {stats['avg_duration']:.1f} 分鐘
     成功率: {stats['success_rate']:.1f}%
     計費時間: {stats['total_billable']} 分鐘
"""
        
        # 添加優化建議
        if suggestions:
            report += f"\n💡 優化建議:\n"
            for i, suggestion in enumerate(suggestions, 1):
                priority_emoji = {
                    'critical': '🚨',
                    'high': '⚠️',
                    'medium': '💡',
                    'low': 'ℹ️'
                }.get(suggestion['priority'], '💡')
                
                report += f"\n{i}. {priority_emoji} {suggestion['category']} - {suggestion['priority'].upper()}\n"
                report += f"   問題: {suggestion['issue']}\n"
                report += f"   建議: {suggestion['suggestion']}\n"
                report += f"   行動:\n"
                for action in suggestion['actions']:
                    report += f"     • {action}\n"
        
        report += f"\n{'='*60}\n"
        report += f"報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return report
    
    def check_usage_alerts(self) -> List[Dict[str, Any]]:
        """檢查使用量警告"""
        alerts = []
        
        quota = self.get_current_quota()
        if quota:
            if quota.usage_percentage >= self.alert_thresholds['usage_critical']:
                alerts.append({
                    'level': 'critical',
                    'message': f"🚨 GitHub Actions使用量危險: {quota.usage_percentage:.1f}%",
                    'remaining_minutes': quota.remaining_minutes,
                    'action_required': True
                })
            elif quota.usage_percentage >= self.alert_thresholds['usage_warning']:
                alerts.append({
                    'level': 'warning',
                    'message': f"⚠️ GitHub Actions使用量警告: {quota.usage_percentage:.1f}%",
                    'remaining_minutes': quota.remaining_minutes,
                    'action_required': False
                })
        
        # 檢查每日使用量
        today_runs = [
            run for run in self.workflow_runs 
            if run.created_at.date() == datetime.now().date()
        ]
        
        today_minutes = sum(run.billable_minutes for run in today_runs)
        
        if today_minutes > self.alert_thresholds['daily_limit']:
            alerts.append({
                'level': 'warning',
                'message': f"⚠️ 今日使用量過高: {today_minutes} 分鐘",
                'daily_usage': today_minutes,
                'action_required': False
            })
        
        return alerts
    
    def save_usage_data(self) -> Path:
        """保存使用量數據"""
        reports_dir = self.project_root / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # 保存詳細數據
        data_file = reports_dir / f"github_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        usage_data = {
            'timestamp': datetime.now().isoformat(),
            'quota': {
                'total_minutes': self.quota_history[-1].total_minutes if self.quota_history else 0,
                'used_minutes': self.quota_history[-1].used_minutes if self.quota_history else 0,
                'usage_percentage': self.quota_history[-1].usage_percentage if self.quota_history else 0,
                'remaining_minutes': self.quota_history[-1].remaining_minutes if self.quota_history else 0
            },
            'workflow_runs': [
                {
                    'id': run.id,
                    'name': run.name,
                    'status': run.status,
                    'conclusion': run.conclusion,
                    'created_at': run.created_at.isoformat(),
                    'duration_minutes': run.duration_minutes,
                    'billable_minutes': run.billable_minutes,
                    'workflow_name': run.workflow_name
                }
                for run in self.workflow_runs
            ],
            'usage_analysis': self.analyze_usage_patterns(),
            'optimization_suggestions': self.get_optimization_suggestions(),
            'alerts': self.check_usage_alerts()
        }
        
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(usage_data, f, indent=2, ensure_ascii=False)
        
        # 保存報告
        report_file = reports_dir / f"github_usage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_usage_report())
        
        logger.info(f"📄 GitHub使用量數據已保存: {data_file}")
        logger.info(f"📄 GitHub使用量報告已保存: {report_file}")
        
        return data_file

# 全局GitHub使用量監控器實例
github_usage_monitor = GitHubUsageMonitor()

# 便捷函數
def get_github_quota() -> Optional[GitHubQuota]:
    """獲取GitHub配額"""
    return github_usage_monitor.get_current_quota()

def check_github_usage_alerts() -> List[Dict[str, Any]]:
    """檢查GitHub使用量警告"""
    return github_usage_monitor.check_usage_alerts()

def get_github_optimization_suggestions() -> List[Dict[str, Any]]:
    """獲取GitHub優化建議"""
    return github_usage_monitor.get_optimization_suggestions()