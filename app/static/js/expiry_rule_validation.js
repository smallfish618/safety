document.addEventListener('DOMContentLoaded', function() {
    // 获取表单元素
    const addForm = document.querySelector('form[action*="add_expiry_rule"]');
    const editForms = document.querySelectorAll('form[action*="edit_expiry_rule"]');
    
    // 添加验证函数到添加表单
    if (addForm) {
        setupValidation(addForm);
    }
    
    // 添加验证函数到所有编辑表单
    if (editForms.length > 0) {
        editForms.forEach(form => {
            setupValidation(form);
        });
    }
    
    // 设置表单验证
    function setupValidation(form) {
        const itemNameInput = form.querySelector('input[name="item_name"]');
        const submitButton = form.querySelector('button[type="submit"]');
        
        // 如果没有找到必要元素，直接返回
        if (!itemNameInput || !submitButton) {
            console.warn("验证设置失败: 未找到物品名称输入框或提交按钮");
            return;
        }
        
        // 获取规则ID（如果是编辑表单）
        let ruleId = null;
        if (form.action.includes('edit_expiry_rule')) {
            const match = form.action.match(/edit_expiry_rule\/(\d+)/);
            if (match && match[1]) {
                ruleId = match[1];
            }
        }
        
        // 设置延迟验证
        let timeout = null;
        
        // 输入时验证
        itemNameInput.addEventListener('input', function() {
            // 清除原有验证信息
            clearValidationMessage(itemNameInput);
            
            // 设置延迟验证，避免频繁请求
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                validateItemName(itemNameInput.value, ruleId, itemNameInput, submitButton);
            }, 500);
        });
        
        // 表单提交前验证
        form.addEventListener('submit', function(e) {
            // 先执行同步验证
            if (!itemNameInput.value.trim()) {
                e.preventDefault();
                showError(itemNameInput, "物品名称不能为空");
                return;
            }
            
            // 检查是否正在验证中
            if (itemNameInput.dataset.validating === "true") {
                e.preventDefault();
                return;
            }
            
            // 检查是否已验证为无效
            if (itemNameInput.dataset.valid === "false") {
                e.preventDefault();
            }
        });
    }
    
    // 验证物品名称是否重复
    function validateItemName(name, ruleId, inputElement, submitButton) {
        // 如果为空，不验证
        if (!name.trim()) {
            return;
        }
        
        // 标记正在验证中
        inputElement.dataset.validating = "true";
        
        // 构建请求URL
        let url = `/admin/api/check_item_name?item_name=${encodeURIComponent(name)}`;
        if (ruleId) {
            url += `&rule_id=${ruleId}`;
        }
        
        // 发送AJAX请求检查名称
        fetch(url)
            .then(response => response.json())
            .then(data => {
                inputElement.dataset.validating = "false";
                
                if (data.exists) {
                    // 名称已存在
                    showError(inputElement, "此物品名称已存在，请使用其他名称");
                    submitButton.disabled = true;
                    inputElement.dataset.valid = "false";
                } else {
                    // 名称可用
                    showSuccess(inputElement, "物品名称可用");
                    submitButton.disabled = false;
                    inputElement.dataset.valid = "true";
                }
            })
            .catch(error => {
                inputElement.dataset.validating = "false";
                console.error("验证出错:", error);
                // 出错时允许提交，服务器会再次验证
                submitButton.disabled = false;
                inputElement.dataset.valid = "true";
            });
    }
    
    // 显示错误信息
    function showError(inputElement, message) {
        clearValidationMessage(inputElement);
        inputElement.classList.add('is-invalid');
        inputElement.classList.remove('is-valid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        
        inputElement.parentNode.appendChild(errorDiv);
    }
    
    // 显示成功信息
    function showSuccess(inputElement, message) {
        clearValidationMessage(inputElement);
        inputElement.classList.add('is-valid');
        inputElement.classList.remove('is-invalid');
        
        const successDiv = document.createElement('div');
        successDiv.className = 'valid-feedback';
        successDiv.textContent = message;
        
        inputElement.parentNode.appendChild(successDiv);
    }
    
    // 清除验证信息
    function clearValidationMessage(inputElement) {
        const parent = inputElement.parentNode;
        const feedback = parent.querySelector('.invalid-feedback, .valid-feedback');
        if (feedback) {
            parent.removeChild(feedback);
        }
    }
});
