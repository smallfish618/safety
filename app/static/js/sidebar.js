// 侧边栏和导航菜单功能

document.addEventListener('DOMContentLoaded', function() {
    console.log("sidebar.js 加载成功");

    // 侧边栏切换功能
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('d-md-block');
            sidebar.classList.toggle('d-none');
        });
    }
    
    // 初始化下拉菜单 - 特别处理物品分析下拉菜单
    const analysisDropdown = document.getElementById('analysisDropdown');
    if (analysisDropdown) {
        console.log("找到物品分析下拉菜单，添加事件处理");
        
        // 手动实现下拉菜单效果
        analysisDropdown.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // 找到对应的下拉菜单元素
            const dropdownMenu = this.nextElementSibling;
            if (dropdownMenu && dropdownMenu.classList.contains('dropdown-menu')) {
                // 切换显示状态
                dropdownMenu.classList.toggle('show');
                this.setAttribute('aria-expanded', dropdownMenu.classList.contains('show'));
                
                // 获取下拉菜单的高度
                const menuHeight = dropdownMenu.offsetHeight;
                
                // 找到所有下面的菜单项并动态调整它们的位置
                if (dropdownMenu.classList.contains('show')) {
                    // 当菜单展开时，找到之后的所有同级菜单项
                    let nextItem = dropdownMenu.parentNode.nextElementSibling;
                    while (nextItem) {
                        nextItem.style.transform = `translateY(${menuHeight}px)`;
                        nextItem.style.transition = 'transform 0.3s ease';
                        nextItem = nextItem.nextElementSibling;
                    }
                    
                    // 同时移动用户信息区域
                    const userInfo = document.querySelector('.sidebar .user-info');
                    if (userInfo) {
                        userInfo.style.transform = `translateY(${menuHeight}px)`;
                        userInfo.style.transition = 'transform 0.3s ease';
                    } else {
                        // 如果未登录，则移动登录按钮区域
                        const loginBox = document.querySelector('.sidebar .mt-4.p-3');
                        if (loginBox) {
                            loginBox.style.transform = `translateY(${menuHeight}px)`;
                            loginBox.style.transition = 'transform 0.3s ease';
                        }
                    }
                } else {
                    // 当菜单收起时，重置后面菜单项的位置
                    let nextItem = dropdownMenu.parentNode.nextElementSibling;
                    while (nextItem) {
                        nextItem.style.transform = 'translateY(0)';
                        nextItem = nextItem.nextElementSibling;
                    }
                    
                    // 同时重置用户信息区域
                    const userInfo = document.querySelector('.sidebar .user-info');
                    if (userInfo) {
                        userInfo.style.transform = 'translateY(0)';
                    } else {
                        const loginBox = document.querySelector('.sidebar .mt-4.p-3');
                        if (loginBox) {
                            loginBox.style.transform = 'translateY(0)';
                        }
                    }
                }
            }
        });
        
        // 点击其他区域关闭下拉菜单
        document.addEventListener('click', function(e) {
            if (!analysisDropdown.contains(e.target)) {
                const dropdownMenu = analysisDropdown.nextElementSibling;
                if (dropdownMenu && dropdownMenu.classList.contains('show')) {
                    dropdownMenu.classList.remove('show');
                    analysisDropdown.setAttribute('aria-expanded', 'false');
                    
                    // 重置下面菜单项的位置
                    let nextItem = dropdownMenu.parentNode.nextElementSibling;
                    while (nextItem) {
                        nextItem.style.transform = 'translateY(0)';
                        nextItem.style.transition = 'transform 0.3s ease';
                        nextItem = nextItem.nextElementSibling;
                    }
                    
                    // 同时重置用户信息区域
                    const userInfo = document.querySelector('.sidebar .user-info');
                    if (userInfo) {
                        userInfo.style.transform = 'translateY(0)';
                    } else {
                        const loginBox = document.querySelector('.sidebar .mt-4.p-3');
                        if (loginBox) {
                            loginBox.style.transform = 'translateY(0)';
                        }
                    }
                }
            }
        });
    }
    
    // 防止下拉菜单项点击立即关闭菜单
    const dropdownItems = document.querySelectorAll('.dropdown-menu .dropdown-item');
    dropdownItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
});
