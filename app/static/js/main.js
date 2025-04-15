// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('消防安全管理系统已加载');
    
    // 获取当前URL路径
    const currentPath = window.location.pathname;
    
    // 为导航栏项目添加激活状态
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        
        // 检查链接是否匹配当前路径
        if (href && currentPath.includes(href.replace(/\?.*$/, ''))) {
            link.classList.add('active');
            
            // 确保图标和文本可见
            const icon = link.querySelector('i');
            const text = link.querySelector('span');
            
            if (icon) {
                icon.style.color = '#fff';
                icon.style.visibility = 'visible';
                icon.style.display = 'inline-block';
            }
            
            if (text) {
                text.style.color = '#fff';
                text.style.visibility = 'visible';
                text.style.display = 'inline-block';
            }
        } else {
            link.classList.remove('active');
        }
    });
});