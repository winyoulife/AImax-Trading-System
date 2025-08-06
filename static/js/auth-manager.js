/**
 * AImax 安全認證管理器
 * 專屬帳號: lovejk1314 / Ichen5978
 */

class AuthManager {
    constructor() {
        this.isAuthenticated = false;
        this.username = '';
        this.sessionExpiry = null;
        this.init();
    }
    
    init() {
        this.checkAuthStatus();
    }
    
    // 檢查認證狀態
    checkAuthStatus() {
        const auth = localStorage.getItem('aimax_authenticated');
        const expiry = localStorage.getItem('aimax_session_expiry');
        const username = localStorage.getItem('aimax_username');
        
        if (auth === 'true' && expiry && username) {
            const expiryDate = new Date(expiry);
            const now = new Date();
            
            if (now < expiryDate) {
                this.isAuthenticated = true;
                this.username = username;
                this.sessionExpiry = expiryDate;
                return true;
            } else {
                this.logout();
                return false;
            }
        }
        
        return false;
    }
    
    // 設置認證狀態
    setAuthStatus(username) {
        this.isAuthenticated = true;
        this.username = username;
        
        // 設置24小時過期
        const expiry = new Date();
        expiry.setHours(expiry.getHours() + 24);
        this.sessionExpiry = expiry;
        
        localStorage.setItem('aimax_authenticated', 'true');
        localStorage.setItem('aimax_username', username);
        localStorage.setItem('aimax_session_expiry', expiry.toISOString());
        localStorage.setItem('aimax_login_time', new Date().toISOString());
    }
    
    // 登出
    logout() {
        this.isAuthenticated = false;
        this.username = '';
        this.sessionExpiry = null;
        
        localStorage.removeItem('aimax_authenticated');
        localStorage.removeItem('aimax_username');
        localStorage.removeItem('aimax_session_expiry');
        localStorage.removeItem('aimax_login_time');
    }
    
    // 檢查頁面訪問權限
    requireAuth() {
        const currentPath = window.location.pathname;
        const isLoginPage = currentPath.includes('secure-login.html') || currentPath.endsWith('/');
        
        if (isLoginPage) {
            return true; // 登入頁面不需要檢查
        }
        
        if (!this.checkAuthStatus()) {
            console.log('🔐 未授權訪問，重定向到登入頁面');
            window.location.href = './secure-login.html';
            return false;
        }
        return true;
    }
    
    // 獲取用戶信息
    getUserInfo() {
        if (!this.isAuthenticated) return null;
        
        return {
            username: this.username,
            loginTime: localStorage.getItem('aimax_login_time'),
            sessionExpiry: this.sessionExpiry
        };
    }
    
    // 延長會話
    extendSession() {
        if (this.isAuthenticated) {
            const newExpiry = new Date();
            newExpiry.setHours(newExpiry.getHours() + 24);
            this.sessionExpiry = newExpiry;
            localStorage.setItem('aimax_session_expiry', newExpiry.toISOString());
        }
    }
}

// 全局認證管理器實例
window.authManager = new AuthManager();

// 頁面載入時自動檢查認證
document.addEventListener('DOMContentLoaded', function() {
    // 如果不是登入頁面，則檢查認證
    const currentPath = window.location.pathname;
    const isLoginPage = currentPath.includes('secure-login.html') || currentPath.endsWith('index.html');
    
    if (!isLoginPage) {
        window.authManager.requireAuth();
    }
});