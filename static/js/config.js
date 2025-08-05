/**
 * AImax 私有交易系統配置
 * 注意: 此文件在部署時會自動注入環境變數
 */

// GitHub API配置 (部署時自動替換)
const CONFIG = {
    // GitHub API設置
    github: {
        token: '{{GITHUB_TOKEN}}', // 部署時自動替換
        owner: 'your-username', // 需要手動設置你的GitHub用戶名
        repo: 'AImax', // 倉庫名稱
        apiUrl: 'https://api.github.com'
    },
    
    // 系統設置
    system: {
        name: 'AImax 智能交易系統',
        version: '2.0',
        updateInterval: 10000, // 10秒更新一次
        maxRetries: 3,
        timeout: 15000 // 15秒超時
    },
    
    // 安全設置
    security: {
        sessionTimeout: 3600000, // 1小時
        maxLoginAttempts: 5,
        lockoutDuration: 300000, // 5分鐘
        encryptionKey: 'aimax-private-system-2025'
    },
    
    // 數據文件路徑
    dataFiles: {
        executionStatus: 'data/simulation/execution_status.json',
        trades: 'data/simulation/trades.jsonl',
        workflowFile: '.github/workflows/simple-trading.yml'
    },
    
    // UI設置
    ui: {
        theme: 'dark',
        language: 'zh-TW',
        dateFormat: 'YYYY-MM-DD HH:mm:ss',
        currency: 'USD',
        precision: 2
    }
};

// 防止配置被修改
Object.freeze(CONFIG);

// 導出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}