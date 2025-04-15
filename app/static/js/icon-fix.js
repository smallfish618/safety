/**
 * 专门用于修复Bootstrap图标显示问题的脚本
 * 处理图标加载失败的情况，尝试回退到CDN
 */
(function() {
    // 检测图标是否正常显示
    function checkIconsVisibility() {
        const icons = document.querySelectorAll('.bi');
        let hasVisibilityIssues = false;
        
        icons.forEach(icon => {
            // 检查计算样式
            const style = window.getComputedStyle(icon);
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                hasVisibilityIssues = true;
            }
            
            // 确保图标可见
            icon.style.visibility = 'visible';
            icon.style.display = 'inline-block';
            icon.style.opacity = '1';
        });
        
        // 如果发现问题，尝试加载CDN版本
        if (hasVisibilityIssues || icons.length === 0) {
            loadCdnIcons();
        }
    }
    
    // 加载CDN版本的图标
    function loadCdnIcons() {
        if (document.getElementById('bootstrap-icons-cdn')) {
            return; // 已经加载过了
        }
        
        const link = document.createElement('link');
        link.id = 'bootstrap-icons-cdn';
        link.rel = 'stylesheet';
        link.href = 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css';
        document.head.appendChild(link);
        
        console.log('Bootstrap Icons: 已加载CDN版本作为备用');
    }
    
    // 在DOM准备好时执行
    document.addEventListener('DOMContentLoaded', function() {
        console.log('正在应用图标修复...');
        
        // 确保所有bootstrap图标可见
        const allIcons = document.querySelectorAll('.bi, [class*="bi-"]');
        allIcons.forEach(icon => {
            icon.style.display = 'inline-block';
            icon.style.visibility = 'visible';
            icon.style.opacity = '1';
        });
        
        // 特殊处理导航栏图标
        const navIcons = document.querySelectorAll('.sidebar .nav-link i');
        navIcons.forEach(icon => {
            icon.style.cssText = 'display: inline-block !important; visibility: visible !important; opacity: 1 !important; color: inherit;';
        });
        
        setTimeout(checkIconsVisibility, 100); // 短暂延迟确保DOM已处理
    });
    
    // 在页面加载完成后再次检查并修复
    window.addEventListener('load', function() {
        // 延迟执行以确保所有动态内容已经加载
        setTimeout(function() {
            const allIcons = document.querySelectorAll('.bi, [class*="bi-"]');
            allIcons.forEach(icon => {
                if (getComputedStyle(icon).display === 'none' || 
                    getComputedStyle(icon).visibility === 'hidden') {
                    
                    console.log('修复了隐藏的图标:', icon);
                    icon.style.cssText = 'display: inline-block !important; visibility: visible !important; opacity: 1 !important;';
                }
            });
        }, 200);
        
        setTimeout(checkIconsVisibility, 500); // 页面加载完成后再次检查
    });
})();
