// 为物资管理页面的表单添加通用验证功能

document.addEventListener('DOMContentLoaded', function() {
    // 验证添加物资表单
    function setupFormValidation(formSelector) {
        const forms = document.querySelectorAll(formSelector);
        
        forms.forEach(function(form) {
            form.addEventListener('submit', function(event) {
                let isValid = true;
                
                // 检查所有必填字段
                const requiredFields = form.querySelectorAll('[required]');
                requiredFields.forEach(function(field) {
                    if (!field.value.trim()) {
                        field.classList.add('is-invalid');
                        isValid = false;
                        
                        // 添加错误提示
                        let feedback = field.nextElementSibling;
                        if (!feedback || !feedback.classList.contains('invalid-feedback')) {
                            feedback = document.createElement('div');
                            feedback.className = 'invalid-feedback';
                            feedback.textContent = '此字段为必填项';
                            field.parentNode.insertBefore(feedback, field.nextSibling);
                        }
                    } else {
                        field.classList.remove('is-invalid');
                        const feedback = field.nextElementSibling;
                        if (feedback && feedback.classList.contains('invalid-feedback')) {
                            feedback.remove();
                        }
                    }
                });
                
                // 验证日期字段格式
                const dateFields = form.querySelectorAll('input[type="date"]');
                dateFields.forEach(function(field) {
                    if (field.value && !isValidDate(field.value)) {
                        field.classList.add('is-invalid');
                        isValid = false;
                        
                        // 添加错误提示
                        let feedback = field.nextElementSibling;
                        if (!feedback || !feedback.classList.contains('invalid-feedback')) {
                            feedback = document.createElement('div');
                            feedback.className = 'invalid-feedback';
                            feedback.textContent = '请输入有效的日期格式 (YYYY-MM-DD)';
                            field.parentNode.insertBefore(feedback, field.nextSibling);
                        }
                    }
                });
                
                // 如果表单无效，阻止提交
                if (!isValid) {
                    event.preventDefault();
                    
                    // 滚动到第一个错误字段
                    const firstInvalidField = form.querySelector('.is-invalid');
                    if (firstInvalidField) {
                        firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        firstInvalidField.focus();
                    }
                }
            });
            
            // 为字段添加实时验证
            const fields = form.querySelectorAll('input, select, textarea');
            fields.forEach(function(field) {
                field.addEventListener('blur', function() {
                    if (field.hasAttribute('required') && !field.value.trim()) {
                        field.classList.add('is-invalid');
                        
                        // 添加错误提示
                        let feedback = field.nextElementSibling;
                        if (!feedback || !feedback.classList.contains('invalid-feedback')) {
                            feedback = document.createElement('div');
                            feedback.className = 'invalid-feedback';
                            feedback.textContent = '此字段为必填项';
                            field.parentNode.insertBefore(feedback, field.nextSibling);
                        }
                    } else {
                        field.classList.remove('is-invalid');
                        const feedback = field.nextElementSibling;
                        if (feedback && feedback.classList.contains('invalid-feedback')) {
                            feedback.remove();
                        }
                    }
                });
            });
        });
    }
    
    // 验证日期格式
    function isValidDate(dateString) {
        const regex = /^\d{4}-\d{2}-\d{2}$/;
        if (!regex.test(dateString)) return false;
        
        const date = new Date(dateString);
        return !isNaN(date.getTime());
    }
    
    // 监听模态框显示事件，确保清除以前的验证样式
    const modals = document.querySelectorAll('.modal');
    modals.forEach(function(modal) {
        modal.addEventListener('shown.bs.modal', function() {
            const form = this.querySelector('form');
            if (form) {
                const invalidFields = form.querySelectorAll('.is-invalid');
                invalidFields.forEach(function(field) {
                    field.classList.remove('is-invalid');
                });
                
                const feedbacks = form.querySelectorAll('.invalid-feedback');
                feedbacks.forEach(function(feedback) {
                    feedback.remove();
                });
            }
        });
    });
    
    // 设置表单验证
    setupFormValidation('#addStationModal form');
    setupFormValidation('[id^="editModal-"] form');
});
