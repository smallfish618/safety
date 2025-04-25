/**
 * 有效期预警邮件发送功能
 * 确保不重复发送和不遗漏收件人
 */

// 初始化全局变量
let isSubmitting = false; // 用于防止重复提交
let allResponsibles = []; // 所有负责人
let selectedResponsibles = []; // 选中的负责人
let filteredItems = []; // 预警物品列表

// 添加初始化函数，只有当显式调用时才执行
function initEmailAlertModule() {
    // 检查是否已初始化，防止重复初始化
    if (window.emailAlertInitialized) {
        console.warn('邮件预警模块已初始化，跳过');
        return;
    }
    
    window.emailAlertInitialized = true;
    console.log('邮件预警模块初始化开始');

    // 在DOM加载完成后执行
    document.addEventListener('DOMContentLoaded', function() {
        console.log('邮件发送JS已加载');
        
        // 初始化收件人列表
        initializeResponsiblesList();
        
        // 单选按钮切换事件
        document.querySelectorAll('input[name="recipientType"]').forEach(radio => {
            radio.addEventListener('change', toggleRecipientSelector);
        });
        
        // 全选/取消全选按钮
        document.getElementById('selectAllBtn')?.addEventListener('click', selectAllResponsibles);
        document.getElementById('deselectAllBtn')?.addEventListener('click', deselectAllResponsibles);
        
        // 确认发送按钮
        document.getElementById('confirmSendBtn')?.addEventListener('click', sendEmails);
    });

    // 初始化收件人列表
    function initializeResponsiblesList() {
        // 收集页面中所有负责人
        const checkboxes = document.querySelectorAll('.responsible-checkbox');
        allResponsibles = Array.from(checkboxes).map(cb => cb.value);
        
        console.log(`已加载 ${allResponsibles.length} 位负责人`);
        
        // 收集页面中的预警物品
        try {
            filteredItems = JSON.parse(document.getElementById('filtered-items-data')?.value || '[]');
            console.log(`已加载 ${filteredItems.length} 个预警物品`);
        } catch (error) {
            console.error('解析预警物品数据出错:', error);
            filteredItems = [];
        }
    }

    // 切换收件人选择器显示
    function toggleRecipientSelector() {
        const selectorDiv = document.getElementById('responsibleSelector');
        const selectedValue = document.querySelector('input[name="recipientType"]:checked').value;
        
        if (selectedValue === 'select') {
            selectorDiv.style.display = 'block';
        } else {
            selectorDiv.style.display = 'none';
        }
    }

    // 全选负责人
    function selectAllResponsibles() {
        document.querySelectorAll('.responsible-checkbox').forEach(cb => {
            cb.checked = true;
        });
    }

    // 取消全选负责人
    function deselectAllResponsibles() {
        document.querySelectorAll('.responsible-checkbox').forEach(cb => {
            cb.checked = false;
        });
    }

    // 确认发送前更新模态框内容
    document.getElementById('sendEmailBtn')?.addEventListener('click', function() {
        updateConfirmModalContent();
    });

    // 更新确认模态框内容
    function updateConfirmModalContent() {
        const recipientType = document.querySelector('input[name="recipientType"]:checked').value;
        const summaryDiv = document.getElementById('recipientSummary');
        
        // 获取选中的负责人列表
        selectedResponsibles = [];
        if (recipientType === 'all') {
            selectedResponsibles = [...allResponsibles];
        } else {
            document.querySelectorAll('.responsible-checkbox:checked').forEach(cb => {
                selectedResponsibles.push(cb.value);
            });
        }
        
        // 没有选择收件人时显示警告
        if (selectedResponsibles.length === 0) {
            summaryDiv.innerHTML = '<div class="alert alert-danger">未选择任何收件人，请选择后再发送</div>';
            document.getElementById('confirmSendBtn').disabled = true;
            return;
        }
        
        // 启用发送按钮
        document.getElementById('confirmSendBtn').disabled = false;
        
        // 显示收件人摘要
        let html = `<p>邮件将发送给以下 <strong>${selectedResponsibles.length}</strong> 位负责人:</p>`;
        html += '<ul class="list-group">';
        
        // 如果负责人过多，只显示部分
        const displayLimit = 10;
        const displayCount = Math.min(selectedResponsibles.length, displayLimit);
        
        for (let i = 0; i < displayCount; i++) {
            html += `<li class="list-group-item">${selectedResponsibles[i]}</li>`;
        }
        
        if (selectedResponsibles.length > displayLimit) {
            html += `<li class="list-group-item">...还有 ${selectedResponsibles.length - displayLimit} 位</li>`;
        }
        
        html += '</ul>';
        summaryDiv.innerHTML = html;
    }

    // 修改sendEmails函数，添加防重复发送逻辑
    function sendEmails() {
        // 防止重复提交
        if (isSubmitting || window.sendEmailInProgress) {
            console.warn('发送请求已在处理中，请勿重复提交');
            return;
        }
        
        // 如果没有选择收件人，显示错误并返回
        if (selectedResponsibles.length === 0) {
            showResult('error', '未选择任何收件人，请选择后再发送');
            return;
        }
        
        // 设置正在提交标志 - 本地和全局都设置
        isSubmitting = true;
        window.sendEmailInProgress = true;
        
        // 更新界面状态
        const confirmSendBtn = document.getElementById('confirmSendBtn');
        const originalButtonText = confirmSendBtn.innerHTML;
        confirmSendBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 发送中...';
        confirmSendBtn.disabled = true;
        
        // 获取邮件主题
        const emailSubject = document.getElementById('emailSubject').value || '【重要】物资有效期预警通知';
        
        // 获取CSRF令牌
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (!csrfToken) {
            showResult('error', 'CSRF令牌缺失，无法发送请求，请刷新页面后重试');
            resetSubmitStatus(confirmSendBtn, originalButtonText);
            return;
        }
        
        // 准备发送的数据
        const sendData = {
            email_subject: emailSubject,
            email_content: generateEmailHTML(), // 生成邮件HTML内容
            selected_responsibles: selectedResponsibles, // 选中的负责人列表
            items: filteredItems, // 预警物品数据
            options: {
                send_to_selected_only: true
            }
        };
        
        // 发送AJAX请求
        fetch('/admin/send_expiry_alert_emails', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(sendData),
            credentials: 'same-origin'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP错误：${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // 处理成功响应
            console.log('发送结果:', data);
            
            // 隐藏确认模态框，显示结果模态框
            const confirmModal = bootstrap.Modal.getInstance(document.getElementById('confirmSendModal'));
            confirmModal.hide();
            
            // 显示发送结果
            if (data.success) {
                showResult('success', `邮件发送成功！共发送给 ${data.recipients_count} 位接收者。${data.message || ''}`);
            } else {
                showResult('error', `邮件发送失败：${data.error || '未知错误'}`);
            }
        })
        .catch(error => {
            console.error('发送邮件时出错:', error);
            showResult('error', `发送邮件时出错: ${error.message}`);
        })
        .finally(() => {
            // 恢复按钮状态和提交标志 - 本地和全局都重置
            resetSubmitStatus(confirmSendBtn, originalButtonText);
            isSubmitting = false;
            window.sendEmailInProgress = false;
        });
    }

    // 重置提交状态
    function resetSubmitStatus(button, originalText) {
        button.innerHTML = originalText;
        button.disabled = false;
        isSubmitting = false;
    }

    // 生成邮件HTML内容
    function generateEmailHTML() {
        // 获取表格内容或使用其他方式生成HTML
        const tableContent = document.getElementById('expiryItemsTable')?.outerHTML || '';
        
        // 添加邮件正文，包含表格
        return `
        <div style="font-family: Arial, sans-serif;">
            <h2 style="color: #dc3545;">消防安全管理系统 - 物资有效期预警通知</h2>
            <p>尊敬的负责人：</p>
            <p>您负责的以下物资即将到期或已经到期，请及时处理：</p>
            ${tableContent}
            <p>请及时对已到期和即将到期的物资进行更换或维护，确保消防安全。</p>
            <p>谢谢您的配合！</p>
            <p style="margin-top: 20px; color: #6c757d; font-size: 0.9em;">
                消防安全管理系统<br>
                发送时间：${new Date().toLocaleString('zh-CN')}
            </p>
        </div>
        `;
    }

    // 显示发送结果
    function showResult(type, message) {
        const resultDiv = document.getElementById('sendResultMessage');
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const icon = type === 'success' ? 'bi-check-circle' : 'bi-exclamation-triangle';
        
        resultDiv.innerHTML = `
        <div class="alert ${alertClass}">
            <i class="${icon} me-2"></i> ${message}
        </div>
        `;
        
        // 显示结果模态框
        const resultModal = new bootstrap.Modal(document.getElementById('sendResultModal'));
        resultModal.show();
    }
}

// 检测URL参数，如果没有noSend=true，则自动初始化
if (!window.location.href.includes('noSend=true') && 
    !window.location.href.includes('noInit=true')) {
    document.addEventListener('DOMContentLoaded', initEmailAlertModule);
}

// 全局暴露初始化函数，供HTML调用
window.initEmailAlertModule = initEmailAlertModule;