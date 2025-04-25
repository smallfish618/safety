/**
 * 负责处理邮件发送的JS模块
 */

// 邮件发送处理函数
function sendPrewarningEmails(options) {
    // 显示加载状态
    const sendButton = document.getElementById('sendEmailBtn');
    const originalBtnText = sendButton.innerHTML;
    sendButton.disabled = true;
    sendButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 发送中...';
    
    // 获取CSRF令牌，确保请求安全有效
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    console.log('准备发送预警邮件，收集数据中...');
    
    // 获取邮件内容和主题
    const emailContent = document.getElementById('emailPreview').innerHTML;
    const emailSubject = document.getElementById('emailSubject').value || '【重要】物资有效期预警通知';
    
    // 收集所有选中的负责人
    const selectedResponsibles = [];
    document.querySelectorAll('.responsible-checkbox:checked').forEach(checkbox => {
        selectedResponsibles.push(checkbox.value);
    });
    
    // 获取所有表格数据，用于生成个性化邮件
    const tableRows = document.querySelectorAll('#expiry-table tbody tr');
    const items = [];
    
    tableRows.forEach(row => {
        items.push({
            name: row.querySelector('td:nth-child(1)').textContent.trim(),
            model: row.querySelector('td:nth-child(2)').textContent.trim(),
            area_name: row.querySelector('td:nth-child(3)').textContent.trim(),
            location: row.querySelector('td:nth-child(4)').textContent.trim(),
            expiry_date: row.querySelector('td:nth-child(5)').textContent.trim(),
            days_remaining: parseInt(row.querySelector('td:nth-child(6)').getAttribute('data-days') || '0'),
            type: row.querySelector('td:nth-child(7)').textContent.trim(),
            responsible_person: row.querySelector('td:nth-child(8)').textContent.trim()
        });
    });
    
    // 构建请求数据
    const requestData = {
        email_content: emailContent,
        email_subject: emailSubject,
        selected_responsibles: selectedResponsibles,
        items: items,
        options: options || {}
    };
    
    console.log('发送请求数据:', requestData);
    
    // 发送AJAX请求 - 增强错误处理
    fetch('/admin/send_expiry_alert_emails', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'Accept': 'application/json'  // 明确指定期望JSON响应
        },
        body: JSON.stringify(requestData),
        credentials: 'same-origin'  // 确保发送凭证
    })
    .then(response => {
        // 增强错误处理，特别处理HTML响应
        if (!response.ok) {
            console.error('服务器响应错误:', response.status, response.statusText);
            
            // 检查内容类型是否为HTML
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('text/html')) {
                return response.text().then(html => {
                    console.error('服务器返回HTML而非JSON，可能是会话过期或CSRF问题');
                    throw new Error('会话可能已过期，请刷新页面后重试');
                });
            }
            
            // 尝试读取错误信息
            return response.text().then(text => {
                try {
                    return JSON.parse(text);  // 尝试解析JSON
                } catch (e) {
                    console.error('无效JSON响应:', text);
                    throw new Error('服务器返回了非预期格式的响应');
                }
            });
        }
        
        // 正确响应，返回JSON数据
        return response.json();
    })
    .then(data => {
        console.log('邮件发送结果:', data);
        
        // 恢复按钮状态
        sendButton.disabled = false;
        sendButton.innerHTML = originalBtnText;
        
        // 显示结果信息
        if (data.success) {
            showAlert('success', `成功发送邮件给 ${data.recipients_count} 个收件人！${data.message || ''}`);
            
            // 成功后关闭模态框
            setTimeout(() => {
                const sendModal = bootstrap.Modal.getInstance(document.getElementById('sendEmailModal'));
                if (sendModal) sendModal.hide();
            }, 2000);
        } else {
            showAlert('danger', `发送邮件失败: ${data.error || '未知错误'}`);
        }
    })
    .catch(error => {
        console.error('邮件发送请求出错:', error);
        
        // 恢复按钮状态
        sendButton.disabled = false;
        sendButton.innerHTML = originalBtnText;
        
        // 显示友好的错误消息
        showAlert('danger', `发送邮件时出错: ${error.message}`);
    });
}

// 工具函数：显示提示消息
function showAlert(type, message) {
    // 创建提示元素
    const alertBox = document.createElement('div');
    alertBox.className = `alert alert-${type} alert-dismissible fade show`;
    alertBox.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // 插入到页面中
    const container = document.querySelector('.alert-container');
    if (container) {
        container.appendChild(alertBox);
    } else {
        // 如果没有专用容器，插入到模态框或页面顶部
        const modalBody = document.querySelector('.modal-body');
        if (modalBody) {
            modalBody.insertBefore(alertBox, modalBody.firstChild);
        } else {
            document.querySelector('.container').insertBefore(alertBox, document.querySelector('.container').firstChild);
        }
    }
    
    // 5秒后自动关闭
    setTimeout(() => {
        alertBox.classList.remove('show');
        setTimeout(() => alertBox.remove(), 150);
    }, 5000);
}

// 页面加载完成后初始化事件监听
document.addEventListener('DOMContentLoaded', function() {
    console.log('邮件发送模块已加载');
    
    // 绑定发送按钮事件
    const sendBtn = document.getElementById('sendEmailBtn');
    if (sendBtn) {
        sendBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('发送按钮被点击');
            
            // 验证是否选择了收件人
            const checkedResponsibles = document.querySelectorAll('.responsible-checkbox:checked');
            if (checkedResponsibles.length === 0) {
                showAlert('warning', '请至少选择一位收件人');
                return;
            }
            
            // 确认发送
            if (confirm('确定要发送预警邮件吗？')) {
                sendPrewarningEmails();
            }
        });
    }
    
    // 添加全选功能
    const selectAllBtn = document.getElementById('selectAllResponsibles');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const isSelectMode = this.textContent.includes('全选');
            
            // 切换所有复选框状态
            document.querySelectorAll('.responsible-checkbox').forEach(checkbox => {
                checkbox.checked = isSelectMode;
            });
            
            // 更新按钮文本
            this.textContent = isSelectMode ? '取消全选' : '全选';
        });
    }
});
