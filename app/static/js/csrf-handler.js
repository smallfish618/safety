/**
 * CSRF令牌处理器
 * 确保所有AJAX请求包含正确的CSRF令牌
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("CSRF令牌处理器已加载");
    
    // 获取CSRF令牌函数 - 改进版：更全面地检查可能的令牌源
    function getCsrfToken() {
        // 检查meta标签
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            const token = metaToken.getAttribute('content');
            if (token) {
                return token;
            }
        }
        
        // 检查数据属性
        const dataToken = document.querySelector('[data-csrf-token]');
        if (dataToken) {
            const token = dataToken.getAttribute('data-csrf-token');
            if (token) {
                return token;
            }
        }
        
        // 检查表单中的隐藏输入
        const formToken = document.querySelector('input[name="csrf_token"]');
        if (formToken) {
            const token = formToken.value;
            if (token) {
                return token;
            }
        }
        
        console.warn("未找到有效的CSRF令牌");
        return null;
    }
    
    // 确保页面上始终有CSRF令牌元标签
    function ensureMetaToken() {
        let token = getCsrfToken();
        if (!token) {
            console.warn("页面中没有CSRF令牌，尝试添加");
            
            // 尝试从Flask生成的表单中获取令牌
            const hiddenInput = document.querySelector('input[name="csrf_token"]');
            if (hiddenInput && hiddenInput.value) {
                token = hiddenInput.value;
                
                // 创建meta标签
                const meta = document.createElement('meta');
                meta.setAttribute('name', 'csrf-token');
                meta.setAttribute('content', token);
                document.head.appendChild(meta);
                console.log("已从表单添加CSRF令牌到meta标签");
            }
        }
        return token;
    }
    
    // 确保页面有CSRF令牌meta标签
    ensureMetaToken();
    
    // 添加事件监听器，修复动态加载内容后的CSRF问题
    document.addEventListener('DOMNodeInserted', function(e) {
        // 检查是否加载了模态框
        if (e.target.classList && e.target.classList.contains('modal')) {
            setTimeout(() => {
                const token = getCsrfToken();
                if (token) {
                    // 确保模态框中的表单有CSRF令牌
                    const forms = e.target.querySelectorAll('form');
                    forms.forEach(form => {
                        if (!form.querySelector('input[name="csrf_token"]')) {
                            const input = document.createElement('input');
                            input.setAttribute('type', 'hidden');
                            input.setAttribute('name', 'csrf_token');
                            input.setAttribute('value', token);
                            form.appendChild(input);
                        }
                    });
                }
            }, 100);
        }
    });
    
    // 为所有fetch请求添加CSRF令牌
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // 仅处理修改数据的请求方法
        if (!options.method || options.method.toUpperCase() === 'GET') {
            return originalFetch(url, options);
        }
        
        // 创建新的选项对象，避免修改原始对象
        const newOptions = {...options};
        
        // 确保headers存在
        newOptions.headers = {...(newOptions.headers || {})};
        
        // 添加CSRF令牌如果不存在 - 每次请求前重新获取最新的令牌
        const token = getCsrfToken();
        if (token) {
            // 确保使用两种可能的头名称，增加兼容性
            if (!newOptions.headers['X-CSRFToken'] && !newOptions.headers['X-CSRF-TOKEN']) {
                newOptions.headers['X-CSRFToken'] = token;
                newOptions.headers['X-CSRF-TOKEN'] = token;
            }
        } else {
            console.error(`无法获取CSRF令牌用于请求: ${url}`);
        }
        
        // 确保请求包含凭证
        if (!newOptions.credentials) {
            newOptions.credentials = 'same-origin';
        }
        
        // 调用原始的fetch方法，并添加错误处理
        return originalFetch(url, newOptions)
            .then(response => {
                // 检查是否为CSRF相关错误
                if (response.status === 400) {
                    // 克隆响应以便可以多次读取
                    return response.clone().text().then(text => {
                        // 检查是否包含CSRF错误信息
                        if ((text && text.includes('CSRF')) || text.includes('csrf')) {
                            console.error("CSRF验证失败");
                            throw new Error('CSRF令牌验证失败，请刷新页面后重试');
                        }
                        return response;
                    });
                }
                return response;
            });
    };
    
    // 显示当前CSRF令牌状态
    const token = getCsrfToken();
    if (token) {
        console.log("CSRF令牌已获取: " + token.substring(0, 5) + '...');
    } else {
        console.error("CSRF令牌缺失！可能会导致表单提交或AJAX请求被拒绝");
    }
});
