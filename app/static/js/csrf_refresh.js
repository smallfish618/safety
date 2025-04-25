document.addEventListener('DOMContentLoaded', function() {
    // 在页面加载时检查CSRF令牌
    console.log("检查CSRF令牌...");
    
    // 检查表单中是否存在CSRF令牌
    const csrfTokenInput = document.querySelector('input[name="csrf_token"]');
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    
    if (!csrfTokenInput || !csrfTokenInput.value || csrfTokenInput.value === "None") {
        console.warn("CSRF令牌缺失或无效，尝试刷新令牌");
        
        // 获取新令牌
        fetch('/admin/get_csrf_token')
            .then(response => response.json())
            .then(data => {
                console.log("获取到新的CSRF令牌");
                
                // 更新表单中的CSRF令牌
                if (csrfTokenInput) {
                    csrfTokenInput.value = data.token;
                    console.log("已更新表单中的CSRF令牌");
                } else {
                    console.warn("找不到表单中的CSRF令牌输入字段");
                }
                
                // 更新或创建meta标签
                if (csrfMeta) {
                    csrfMeta.content = data.token;
                } else {
                    const meta = document.createElement('meta');
                    meta.name = 'csrf-token';
                    meta.content = data.token;
                    document.head.appendChild(meta);
                    console.log("已添加CSRF令牌meta标签");
                }
            })
            .catch(error => {
                console.error("获取CSRF令牌时发生错误:", error);
            });
    } else {
        console.log("CSRF令牌有效");
    }
    
    // 为登录表单添加提交前事件处理，确保CSRF令牌存在
    const loginForm = document.querySelector('form[action*="login"]');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const token = document.querySelector('input[name="csrf_token"]').value;
            if (!token || token === "None") {
                e.preventDefault();
                alert("安全令牌缺失，请刷新页面后重试");
                console.error("尝试提交表单时CSRF令牌缺失");
                return false;
            }
        });
    }
});
