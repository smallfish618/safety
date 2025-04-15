// 创建统一的筛选功能逻辑

document.addEventListener('DOMContentLoaded', function() {
    // 高级筛选区域控制
    const advancedFilters = document.getElementById('advancedFilters');
    const filterToggleBtn = document.querySelector('[data-bs-target="#advancedFilters"]');
    
    // 从URL获取筛选参数
    const urlParams = new URLSearchParams(window.location.search);
    const hasAdvancedFilters = (
        urlParams.has('filter_category') || 
        urlParams.has('filter_item') || 
        urlParams.has('filter_area') || 
        urlParams.has('filter_manufacturer')
    );
    
    // 检查是否有筛选条件，决定是否展开筛选区域
    if (hasAdvancedFilters && advancedFilters) {
        // 确保高级筛选区域展开
        advancedFilters.classList.add('show');
        
        // 更新按钮状态
        if (filterToggleBtn) {
            filterToggleBtn.setAttribute('aria-expanded', 'true');
        }
    }
    
    // 类别和物品名称联动
    const categorySelect = document.getElementById('filter_category');
    const itemSelect = document.getElementById('filter_item');
    
    if (categorySelect && itemSelect) {
        // 保存所有原始选项用于筛选
        const originalOptions = Array.from(itemSelect.options).map(opt => ({
            value: opt.value,
            text: opt.textContent,
            category: opt.dataset.category
        }));
        
        // 当类别选择变更时
        categorySelect.addEventListener('change', function() {
            const selectedCategory = this.value;
            const currentItemValue = itemSelect.value;
            
            // 先清除所有选项，然后添加"全部"选项
            itemSelect.innerHTML = '<option value="">-- 全部 --</option>';
            
            // 如果选择了特定类别，只显示该类别的物品
            // 否则显示所有物品
            if (selectedCategory) {
                // 找出属于所选类别的物品
                const filteredOptions = originalOptions.filter(opt => 
                    !opt.category || opt.category === selectedCategory || opt.value === '');
                
                // 添加过滤后的选项
                filteredOptions.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.value;
                    option.textContent = opt.text;
                    if (opt.category) {
                        option.dataset.category = opt.category;
                    }
                    itemSelect.appendChild(option);
                });
            } else {
                // 添加所有选项
                originalOptions.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.value;
                    option.textContent = opt.text;
                    if (opt.category) {
                        option.dataset.category = opt.category;
                    }
                    itemSelect.appendChild(option);
                });
            }
            
            // 尝试恢复之前选中的值
            if (currentItemValue) {
                // 检查当前值是否在新选项中
                const optionExists = Array.from(itemSelect.options).some(opt => opt.value === currentItemValue);
                if (optionExists) {
                    itemSelect.value = currentItemValue;
                }
            }
        });
    }
    
    // 监听表单提交，确保正确传递参数
    const searchForm = document.querySelector('form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            // 检查表单字段
            const emptyFields = [];
            
            // 收集所有空白字段，后续可能需要移除它们
            Array.from(this.elements).forEach(el => {
                if ((el.nodeName === 'INPUT' || el.nodeName === 'SELECT') && 
                    el.type !== 'submit' && el.type !== 'button' && 
                    !el.value.trim() && el.name) {
                    emptyFields.push(el.name);
                }
            });
        });
    }
    
    // 监听模态框事件，确保正确处理遮罩和body样式
    document.querySelectorAll('.modal').forEach(function(modalElement) {
        modalElement.addEventListener('hidden.bs.modal', function() {
            // 移除所有可能残留的backdrop
            document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
                backdrop.remove();
            });
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        });
    });
});
