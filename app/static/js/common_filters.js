// 创建通用的筛选功能JS，确保所有页面行为一致

document.addEventListener('DOMContentLoaded', function() {
    // 处理高级筛选区域的展开/折叠
    function setupAdvancedFilters() {
        const advancedFilters = document.getElementById('advancedFilters');
        if (!advancedFilters) return;
        
        // 检查URL参数
        const urlParams = new URLSearchParams(window.location.search);
        const hasAdvancedFilters = urlParams.has('filter_area') || 
                                  urlParams.has('filter_category') ||
                                  urlParams.has('filter_item') ||
                                  urlParams.has('filter_manufacturer');
        
        // 根据筛选状态设置显示
        if (hasAdvancedFilters) {
            // 有筛选条件，确保展开
            advancedFilters.classList.add('show');
            
            // 更新按钮状态
            const filterButton = document.querySelector('[data-bs-target="#advancedFilters"]');
            if (filterButton) {
                filterButton.setAttribute('aria-expanded', 'true');
                
                // 添加"已筛选"标记
                if (!filterButton.querySelector('.badge')) {
                    const badge = document.createElement('span');
                    badge.className = 'badge bg-primary ms-1';
                    badge.textContent = '已筛选';
                    filterButton.appendChild(badge);
                }
            }
        } else {
            // 无筛选条件，确保折叠
            advancedFilters.classList.remove('show');
            
            // 更新按钮状态
            const filterButton = document.querySelector('[data-bs-target="#advancedFilters"]');
            if (filterButton) {
                filterButton.setAttribute('aria-expanded', 'false');
                
                // 移除"已筛选"标记
                const badge = filterButton.querySelector('.badge');
                if (badge) {
                    badge.remove();
                }
            }
        }
    }
    
    // 监听表单提交
    function setupFormSubmission() {
        const searchForm = document.querySelector('form');
        if (!searchForm) return;
        
        searchForm.addEventListener('submit', function(e) {
            // 获取所有筛选字段
            const searchInput = this.querySelector('input[name="search"]');
            const filterAreaSelect = this.querySelector('select[name="filter_area"]');
            const filterCategorySelect = this.querySelector('select[name="filter_category"]');
            const filterItemSelect = this.querySelector('select[name="filter_item"]');
            const filterManufacturerSelect = this.querySelector('select[name="filter_manufacturer"]');
            
            // 检查是否有高级筛选
            const hasAdvancedFilter = 
                (filterAreaSelect && filterAreaSelect.value) || 
                (filterCategorySelect && filterCategorySelect.value) || 
                (filterItemSelect && filterItemSelect.value) || 
                (filterManufacturerSelect && filterManufacturerSelect.value);
            
            // 如果没有高级筛选，确保高级筛选区域折叠
            if (!hasAdvancedFilter) {
                const advancedFilters = document.getElementById('advancedFilters');
                if (advancedFilters) {
                    advancedFilters.classList.remove('show');
                }
            }
        });
    }
    
    // 执行初始化
    setupAdvancedFilters();
    setupFormSubmission();
    
    // 处理下拉菜单的联动效果
    const categorySelect = document.getElementById('filter_category');
    const itemSelect = document.getElementById('filter_item');
    
    if (categorySelect && itemSelect) {
        // 保存所有原始选项以便过滤
        const allItems = Array.from(itemSelect.options).map(option => {
            return {
                value: option.value,
                text: option.text,
                category: option.dataset.category || ''
            };
        });
        
        categorySelect.addEventListener('change', function() {
            const selectedCategory = this.value;
            
            // 清空当前选项
            itemSelect.innerHTML = '<option value="">-- 全部 --</option>';
            
            // 添加符合所选类别的选项或所有选项
            allItems.forEach(item => {
                if (!selectedCategory || item.category === selectedCategory) {
                    const option = document.createElement('option');
                    option.value = item.value;
                    option.text = item.text;
                    if (item.category) {
                        option.dataset.category = item.category;
                    }
                    itemSelect.appendChild(option);
                }
            });
        });
    }
});
