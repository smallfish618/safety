/**
 * 控制高级筛选区域的显示/隐藏
 */
// 立即执行函数，不等待DOM加载完成
(function() {
    // 立即隐藏所有高级筛选区域，防止闪现
    document.addEventListener('DOMContentLoaded', function() {
        const advancedFilters = document.getElementById('advancedFilters');
        if (!advancedFilters) return;

        // 检查URL参数
        const urlParams = new URLSearchParams(window.location.search);
        const hasAdvancedParam = checkAdvancedFilters(urlParams);
        
        // 直接操作类，立即设置状态
        if (!hasAdvancedParam) {
            advancedFilters.classList.remove('show');
            advancedFilters.setAttribute('aria-expanded', 'false');
            advancedFilters.style.height = '0';
        }
        
        // 禁用Bootstrap Collapse事件默认处理
        const advFilterToggle = document.querySelector('[data-bs-target="#advancedFilters"]');
        if (advFilterToggle) {
            // 阻止事件的默认行为
            advFilterToggle.addEventListener('click', function(e) {
                // 不阻止默认行为，我们需要Bootstrap的折叠功能
            });
        }
        
        // 处理表单提交
        const filterForm = document.querySelector('form');
        if (filterForm) {
            filterForm.addEventListener('submit', function(e) {
                const hasAdvParams = hasAdvancedFormParams(this);
                if (!hasAdvParams) {
                    // 确保高级筛选区域在提交时折叠
                    advancedFilters.classList.remove('show');
                }
            });
        }
    });

    // 检查URL是否包含高级筛选参数
    function checkAdvancedFilters(urlParams) {
        const commonFilters = [
            'filter_area', 'filter_item', 'filter_manufacturer', 
            'filter_category', 'filter_status'
        ];
        
        for (const param of commonFilters) {
            if (urlParams.get(param)) return true;
        }
        return false;
    }

    // 检查表单中是否包含高级筛选参数
    function hasAdvancedFormParams(form) {
        const filterInputs = form.querySelectorAll('[name^="filter_"]');
        for (const input of filterInputs) {
            if (input.value) return true;
        }
        return false;
    }
})();
