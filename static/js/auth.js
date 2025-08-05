
// AImax 專屬認證系統
const AUTH_CONFIG = {
    username: "lovejk1314",
    passwordHash: "898535a8764bb8b3ccfebd1c2ac92163adafb69300370881a7beaa2dda7af4ae",
    sessionTimeout: 3600000, // 1小時 (毫秒)
    maxLoginAttempts: 5,
    lockoutDuration: 300000   // 5分鐘 (毫秒)
};

class AuthManager {
    constructor() {
        this.loginAttempts = parseInt(localStorage.getItem('loginAttempts') || '0');
        this.lastAttempt = parseInt(localStorage.getItem('lastAttempt') || '0');
        this.sessionStart = parseInt(localStorage.getItem('sessionStart') || '0');
    }
    
    hashPassword(password) {
        // 使用Web Crypto API進行SHA-256哈希
        return crypto.subtle.digest('SHA-256', new TextEncoder().encode(password))
            .then(hashBuffer => {
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            });
    }
    
    async authenticate(username, password) {
        // 檢查是否被鎖定
        if (this.isLockedOut()) {
            throw new Error('帳號已被鎖定，請稍後再試');
        }
        
        // 驗證用戶名
        if (username !== AUTH_CONFIG.username) {
            this.recordFailedAttempt();
            throw new Error('帳號或密碼錯誤');
        }
        
        // 驗證密碼哈希
        const passwordHash = await this.hashPassword(password);
        if (passwordHash !== AUTH_CONFIG.passwordHash) {
            this.recordFailedAttempt();
            throw new Error('帳號或密碼錯誤');
        }
        
        // 認證成功
        this.clearFailedAttempts();
        this.startSession();
        return true;
    }
    
    isLockedOut() {
        if (this.loginAttempts >= AUTH_CONFIG.maxLoginAttempts) {
            const timeSinceLastAttempt = Date.now() - this.lastAttempt;
            return timeSinceLastAttempt < AUTH_CONFIG.lockoutDuration;
        }
        return false;
    }
    
    recordFailedAttempt() {
        this.loginAttempts++;
        this.lastAttempt = Date.now();
        localStorage.setItem('loginAttempts', this.loginAttempts.toString());
        localStorage.setItem('lastAttempt', this.lastAttempt.toString());
    }
    
    clearFailedAttempts() {
        this.loginAttempts = 0;
        localStorage.removeItem('loginAttempts');
        localStorage.removeItem('lastAttempt');
    }
    
    startSession() {
        this.sessionStart = Date.now();
        localStorage.setItem('sessionStart', this.sessionStart.toString());
        localStorage.setItem('authenticated', 'true');
    }
    
    isAuthenticated() {
        const authenticated = localStorage.getItem('authenticated') === 'true';
        if (!authenticated) return false;
        
        const sessionAge = Date.now() - this.sessionStart;
        if (sessionAge > AUTH_CONFIG.sessionTimeout) {
            this.logout();
            return false;
        }
        
        return true;
    }
    
    logout() {
        localStorage.removeItem('authenticated');
        localStorage.removeItem('sessionStart');
        window.location.reload();
    }
    
    getRemainingLockoutTime() {
        if (!this.isLockedOut()) return 0;
        const elapsed = Date.now() - this.lastAttempt;
        return Math.max(0, AUTH_CONFIG.lockoutDuration - elapsed);
    }
}

// 全局認證管理器
window.authManager = new AuthManager();
