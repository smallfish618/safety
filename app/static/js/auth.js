/**
 * 用于增强登录页面安全性和用户体验的脚本
 */
document.addEventListener('DOMContentLoaded', function() {
    // 获取登录表单元素
    const loginForm = document.querySelector('form[action*="login"]');
    
    if (loginForm) {
        // 表单提交前进行验证
        loginForm.addEventListener('submit', function(e) {
            // 检查CSRF令牌是否存在
            const csrfToken = loginForm.querySelector('input[name="csrf_token"]');
            if (!csrfToken || !csrfToken.value) {
                e.preventDefault();
                showAlert('登录失败', 'CSRF令牌缺失，请刷新页面重试。', 'danger');
                return false;
            }
            
            // 获取用户名和密码字段
            const username = loginForm.querySelector('#username');
            const password = loginForm.querySelector('#password');
            
            // 基本前端验证
            if (!username.value.trim()) {
                e.preventDefault();
                showAlert('登录失败', '请输入用户名', 'danger');
                username.focus();
                return false;
            }
            
            if (!password.value) {
                e.preventDefault();
                showAlert('登录失败', '请输入密码', 'danger');
                password.focus();
                return false;
            }
            
            // 禁用提交按钮防止重复提交
            const submitButton = loginForm.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 登录中...';
            }
            
            // 允许表单提交
            return true;
        });
    }
    
    // 显示警告信息的函数
    function showAlert(title, message, type = 'info') {
        // 创建警告元素
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.setAttribute('role', 'alert');
        
        // 设置警告内容
        alertDiv.innerHTML = `
            <strong>${title}</strong> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="关闭"></button>
        `;
        
        // 插入到表单前面
        if (loginForm) {
            loginForm.parentNode.insertBefore(alertDiv, loginForm);
        } else {
            // 如果找不到表单，插入到body开始
            document.body.insertBefore(alertDiv, document.body.firstChild);
        }
        
        // 自动关闭警告
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alertDiv);
                bsAlert.close();
            } catch (error) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    // 在登录页面引入这个脚本
    const loginPageScript = document.createElement('script');
    loginPageScript.src = '/static/js/auth.js';
    document.body.appendChild(loginPageScript);
});
