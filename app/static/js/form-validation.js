/**
 * 处理表单验证的辅助脚本
 */
document.addEventListener('DOMContentLoaded', function() {
    // 验证所有有效期规则表单（添加和编辑）
    validateExpiryRuleForms();
    
    // 为所有关闭按钮添加事件处理
    setupModalCloseEvents();
});

/**
 * 验证所有有效期规则表单
 */
function validateExpiryRuleForms() {
    // 获取所有有效期规则表单（添加和编辑）
    const expiryForms = document.querySelectorAll('#addExpiryRuleModal form, .edit-expiry-form');
    
    expiryForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            let valid = true;
            
            // 检查必填字段
            const requiredFields = ['item_category', 'item_name', 'normal_expiry'];
            for (const fieldName of requiredFields) {
                const input = this.querySelector(`[name="${fieldName}"]`);
                
                if (!input || !input.value.trim()) {
                    // 显示错误
                    if (input) {
                        input.classList.add('is-invalid');
                        
                        // 如果还没有错误信息就创建一个
                        let errorDiv = input.nextElementSibling;
                        if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                            errorDiv = document.createElement('div');
                            errorDiv.className = 'invalid-feedback';
                            errorDiv.textContent = '此字段不能为空';
                            input.after(errorDiv);
                        }
                    }
                    valid = false;
                } else {
                    // 移除错误
                    input.classList.remove('is-invalid');
                    const errorDiv = input.nextElementSibling;
                    if (errorDiv && errorDiv.classList.contains('invalid-feedback')) {
                        errorDiv.remove();
                    }
                }
            }
            
            if (!valid) {
                e.preventDefault();
            }
        });
    });
}

/**
 * 设置模态框关闭事件
 */
function setupModalCloseEvents() {
    const closeButtons = document.querySelectorAll('.modal .close, .modal .btn-close');
    
    closeButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                const forms = modal.querySelectorAll('form');
                forms.forEach(function(form) {
                    form.reset();
                    const invalidFeedbacks = form.querySelectorAll('.invalid-feedback');
                    invalidFeedbacks.forEach(function(feedback) {
                        feedback.remove();
                    });
                    const invalidInputs = form.querySelectorAll('.is-invalid');
                    invalidInputs.forEach(function(input) {
                        input.classList.remove('is-invalid');
                    });
                });
            }
        });
    });
}
