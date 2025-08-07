/**
 * GitHub Actions 監控模組
 * 獲取真實的交易系統運行狀態
 */

class GitHubActionsMonitor {
    constructor() {
        this.repoOwner = 'winyoulife';
        this.repoName = 'AImax-Trading-System';
        this.apiBase = 'https://api.github.com';
        this.lastUpdateTime = null;
        this.cache = new Map();
        this.cacheTimeout = 60000; // 1分鐘緩存
    }
    
    // 獲取工作流運行狀態
    async getWorkflowRuns(workflowName = null) {
        try {
            const cacheKey = `workflow_runs_${workflowName || 'all'}`;
            const cached = this.cache.get(cacheKey);
            
            if (cached && (Date.now() - cached.timestamp) < this.cacheTimeout) {
                return cached.data;
            }
            
            let url = `${this.apiBase}/repos/${this.repoOwner}/${this.repoName}/actions/runs`;
            if (workflowName) {
                url += `?workflow=${workflowName}`;
            }
            url += `${workflowName ? '&' : '?'}per_page=10&status=completed,in_progress,queued`;
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`GitHub API錯誤: ${response.status}`);
            }
            
            const data = await response.json();
            
            // 緩存結果
            this.cache.set(cacheKey, {
                data: data,
                timestamp: Date.now()
            });
            
            return data;
            
        } catch (error) {
            console.error('獲取工作流運行狀態失敗:', error);
            return { workflow_runs: [] };
        }
    }
    
    // 獲取智能平衡交易系統狀態
    async getHighFrequencyTradingStatus() {
        try {
            const data = await this.getWorkflowRuns('high-frequency-trading.yml');
            const runs = data.workflow_runs || [];
            
            if (runs.length === 0) {
                return {
                    status: 'unknown',
                    lastRun: null,
                    nextRun: null,
                    totalRuns: 0,
                    successRate: 0,
                    isRunning: false
                };
            }
            
            const latestRun = runs[0];
            const recentRuns = runs.slice(0, 10);
            const successfulRuns = recentRuns.filter(run => run.conclusion === 'success').length;
            const successRate = (successfulRuns / recentRuns.length) * 100;
            
            return {
                status: latestRun.status,
                conclusion: latestRun.conclusion,
                lastRun: new Date(latestRun.created_at),
                runId: latestRun.id,
                totalRuns: runs.length,
                successRate: successRate,
                isRunning: latestRun.status === 'in_progress' || latestRun.status === 'queued',
                workflowUrl: latestRun.html_url,
                recentRuns: recentRuns.map(run => ({
                    id: run.id,
                    status: run.status,
                    conclusion: run.conclusion,
                    createdAt: new Date(run.created_at),
                    duration: run.updated_at ? 
                        Math.round((new Date(run.updated_at) - new Date(run.created_at)) / 1000) : null
                }))
            };
            
        } catch (error) {
            console.error('獲取高頻交易狀態失敗:', error);
            return {
                status: 'error',
                error: error.message,
                isRunning: false
            };
        }
    }
    
    // 獲取所有交易相關工作流狀態
    async getAllTradingStatus() {
        try {
            const workflows = [
                'high-frequency-trading.yml',
                'main-trading.yml',
                'monitoring.yml',
                'data-management.yml',
                'telegram-notifications.yml'
            ];
            
            const results = await Promise.all(
                workflows.map(async (workflow) => {
                    const data = await this.getWorkflowRuns(workflow);
                    const runs = data.workflow_runs || [];
                    const latestRun = runs[0];
                    
                    return {
                        workflow: workflow.replace('.yml', ''),
                        status: latestRun ? latestRun.status : 'unknown',
                        conclusion: latestRun ? latestRun.conclusion : null,
                        lastRun: latestRun ? new Date(latestRun.created_at) : null,
                        isRunning: latestRun ? 
                            (latestRun.status === 'in_progress' || latestRun.status === 'queued') : false,
                        totalRuns: runs.length,
                        workflowUrl: latestRun ? latestRun.html_url : null
                    };
                })
            );
            
            return results;
            
        } catch (error) {
            console.error('獲取所有交易狀態失敗:', error);
            return [];
        }
    }
    
    // 獲取今日交易統計
    async getTodayTradingStats() {
        try {
            const data = await this.getWorkflowRuns('high-frequency-trading.yml');
            const runs = data.workflow_runs || [];
            
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            const todayRuns = runs.filter(run => {
                const runDate = new Date(run.created_at);
                return runDate >= today;
            });
            
            const successfulRuns = todayRuns.filter(run => run.conclusion === 'success');
            const failedRuns = todayRuns.filter(run => run.conclusion === 'failure');
            const runningRuns = todayRuns.filter(run => 
                run.status === 'in_progress' || run.status === 'queued'
            );
            
            return {
                totalExecutions: todayRuns.length,
                successfulExecutions: successfulRuns.length,
                failedExecutions: failedRuns.length,
                runningExecutions: runningRuns.length,
                successRate: todayRuns.length > 0 ? 
                    (successfulRuns.length / todayRuns.length) * 100 : 0,
                lastExecution: todayRuns.length > 0 ? 
                    new Date(todayRuns[0].created_at) : null,
                nextScheduledRun: this.calculateNextRun()
            };
            
        } catch (error) {
            console.error('獲取今日交易統計失敗:', error);
            return {
                totalExecutions: 0,
                successfulExecutions: 0,
                failedExecutions: 0,
                runningExecutions: 0,
                successRate: 0,
                lastExecution: null,
                nextScheduledRun: null,
                error: error.message
            };
        }
    }
    
    // 計算下次運行時間（基於cron表達式）
    calculateNextRun() {
        const now = new Date();
        const nextRun = new Date(now);
        
        // 簡化計算：假設高頻模式每5分鐘運行一次
        const minutesToAdd = 5 - (now.getMinutes() % 5);
        nextRun.setMinutes(now.getMinutes() + minutesToAdd);
        nextRun.setSeconds(0);
        nextRun.setMilliseconds(0);
        
        return nextRun;
    }
    
    // 格式化運行時間
    formatRunTime(date) {
        if (!date) return '未知';
        
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        
        if (days > 0) return `${days}天前`;
        if (hours > 0) return `${hours}小時前`;
        if (minutes > 0) return `${minutes}分鐘前`;
        return '剛剛';
    }
    
    // 格式化持續時間
    formatDuration(seconds) {
        if (!seconds) return '未知';
        
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        
        if (minutes > 0) {
            return `${minutes}分${remainingSeconds}秒`;
        }
        return `${seconds}秒`;
    }
    
    // 獲取狀態顏色
    getStatusColor(status, conclusion) {
        if (status === 'in_progress' || status === 'queued') return '#f39c12';
        if (conclusion === 'success') return '#00b894';
        if (conclusion === 'failure') return '#e17055';
        return '#666';
    }
    
    // 獲取狀態圖標
    getStatusIcon(status, conclusion) {
        if (status === 'in_progress') return '🔄';
        if (status === 'queued') return '⏳';
        if (conclusion === 'success') return '✅';
        if (conclusion === 'failure') return '❌';
        return '❓';
    }
}

// 全局實例
window.githubMonitor = new GitHubActionsMonitor();