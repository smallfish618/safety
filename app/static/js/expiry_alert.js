// 首先添加自我检查功能，验证JS是否正确加载
console.log("==== expiry_alert.js 文件已加载 ====");

// 将这些函数提升到全局作用域以便所有代码都能访问
// 为每个负责人生成邮件内容片段
function generateResponsibleSection(responsible, items) {
    let html = `
        <div style="margin-top: 20px;">
            <h3 style="margin-bottom: 10px; border-bottom: 1px solid #dee2e6; padding-bottom: 5px;">
                负责人：${responsible}
            </h3>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #f8f9fa;">
                        <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">物品名称</th>
                        <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">型号</th>
                        <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">区域</th>
                        <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">位置</th>
                        <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">到期日期</th>
                        <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">状态</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    // 为每个物品生成行
    items.forEach(item => {
        let statusText, statusColor;
        
        if (item.days_remaining < 0) {
            statusText = "已到期";
            statusColor = "#dc3545"; // 红色
        } else if (item.days_remaining <= 30) {
            statusText = "30天内到期";
            statusColor = "#ffc107"; // 黄色
        } else if (item.days_remaining <= 60) {
            statusText = "60天内到期";
            statusColor = "#17a2b8"; // 青色
        } else {
            statusText = "90天内到期";
            statusColor = "#007bff"; // 蓝色
        }
        
        html += `
            <tr>
                <td style="border: 1px solid #dee2e6; padding: 8px;">${item.name || ''}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px;">${item.model || ''}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px;">${item.area_name || ''}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px;">${item.location || ''}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px;">${item.expiry_date || ''}</td>
                <td style="border: 1px solid #dee2e6; padding: 8px; color: ${statusColor}; font-weight: bold;">
                    ${statusText}
                </td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    return html;
}

// 创建邮件内容HTML - 移至全局作用域
function createEmailContent(filteredItems, emailContentElement, emailRecipientsElement) {
    // 按负责人分组
    const itemsByResponsible = {};
    filteredItems.forEach(item => {
        if (!item.responsible_person) return;
        
        if (!itemsByResponsible[item.responsible_person]) {
            itemsByResponsible[item.responsible_person] = [];
        }
        itemsByResponsible[item.responsible_person].push(item);
    });
    
    // 生成收件人列表
    const recipients = new Set();
    filteredItems.forEach(item => {
        if (item.responsible_person) {
            recipients.add(item.responsible_person);
        }
    });
    // 修复错误 - 使用传入的参数而不是未定义的变量
    emailRecipientsElement.innerHTML = Array.from(recipients).join(', ');
    
    // 生成邮件正文HTML
    let html = `
        <div style="font-family: Arial, sans-serif;">
            <h2 style="color: #dc3545;">消防安全管理系统 - 物资有效期预警通知</h2>
            <p>尊敬的负责人：</p>
            <p>您负责的以下物资即将到期或已经到期，请及时处理：</p>
    `;
    
    // 为每个负责人生成表格内容
    Object.keys(itemsByResponsible).forEach(responsible => {
        const items = itemsByResponsible[responsible];
        html += generateResponsibleSection(responsible, items);
    });
    
    // 添加结尾和签名
    html += `
        <p>请及时对已到期和即将到期的物资进行更换或维护，确保消防安全。</p>
        <p>谢谢您的配合！</p>
        <p style="margin-top: 20px; color: #6c757d; font-size: 0.9em;">
            消防安全管理系统<br>
            发送时间：${new Date().toLocaleString()}
        </p>
    </div>`;
    
    emailContentElement.innerHTML = html;
}

// 邮件发送功能模块
document.addEventListener('DOMContentLoaded', function() {
    console.log("expiry_alert.js DOMContentLoaded 事件触发");
    
    // 验证全局 allItems 变量
    if (typeof window.allItems === 'undefined') {
        console.error("全局 allItems 变量未定义");
        window.allItems = [];
    } else {
        console.log("全局 allItems 变量已定义，包含", window.allItems.length, "项");
    }
    
    // 声明全局调试变量
    window.emailAlertDebug = {
        initialized: false,
        errors: [],
        elements: {},
        events: []
    };
    
    try {
        // 获取CSRF令牌
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        console.log("CSRF令牌已获取:", csrfToken ? "成功" : "失败", csrfToken);
        window.emailAlertDebug.csrfToken = csrfToken;
        
        if (!csrfToken) {
            console.error("警告: 找不到CSRF令牌，可能导致POST请求失败");
            window.emailAlertDebug.errors.push("找不到CSRF令牌");
        }
        
        // 获取发送预警邮件按钮
        const sendAlertEmailBtn = document.getElementById('sendAlertEmailBtn');
        window.emailAlertDebug.elements.sendAlertEmailBtn = sendAlertEmailBtn;
        
        console.log("获取发送预警邮件按钮:", sendAlertEmailBtn ? "成功" : "失败");
        
        if (sendAlertEmailBtn) {
            console.log("尝试绑定点击事件到发送预警邮件按钮");
            
            // 先移除可能存在的事件处理器，避免重复
            sendAlertEmailBtn.removeEventListener('click', handleSendAlertEmailClick);
            
            // 添加点击事件处理程序
            sendAlertEmailBtn.addEventListener('click', handleSendAlertEmailClick);
            console.log("成功绑定点击事件到发送预警邮件按钮");
            
            // 额外添加明确可见的点击处理器
            sendAlertEmailBtn.onclick = function() {
                console.log("发送预警邮件按钮被点击 (onclick方法)");
                handleSendAlertEmailClick();
            };
        } else {
            console.error("错误: 未找到发送预警邮件按钮 (ID: sendAlertEmailBtn)");
            window.emailAlertDebug.errors.push("找不到发送预警邮件按钮");
            
            // 尝试在整个文档中查找可能匹配的按钮
            console.log("尝试查找所有按钮元素");
            const allButtons = document.querySelectorAll('button');
            console.log("找到", allButtons.length, "个按钮元素");
            allButtons.forEach((btn, index) => {
                console.log(`按钮 ${index + 1}:`, btn.id, btn.className, btn.textContent.trim());
            });
        }
        
        // 查找并存储关键元素
        window.emailAlertDebug.elements.emailPreviewModal = document.getElementById('emailPreviewModal');
        window.emailAlertDebug.elements.refreshPreviewBtn = document.getElementById('refreshPreviewBtn');
        window.emailAlertDebug.elements.sendEmailBtn = document.getElementById('sendEmailBtn');
        window.emailAlertDebug.elements.emailContent = document.getElementById('emailContent');
        window.emailAlertDebug.elements.emailRecipients = document.getElementById('emailRecipients');
        
        console.log("关键元素检查:");
        console.log("- emailPreviewModal:", window.emailAlertDebug.elements.emailPreviewModal ? "已找到" : "未找到");
        console.log("- refreshPreviewBtn:", window.emailAlertDebug.elements.refreshPreviewBtn ? "已找到" : "未找到");
        console.log("- sendEmailBtn:", window.emailAlertDebug.elements.sendEmailBtn ? "已找到" : "未找到");
        console.log("- emailContent:", window.emailAlertDebug.elements.emailContent ? "已找到" : "未找到");
        console.log("- emailRecipients:", window.emailAlertDebug.elements.emailRecipients ? "已找到" : "未找到");
        
        // 验证bootstrap库是否可用
        if (typeof bootstrap === 'undefined') {
            console.error("错误: Bootstrap库未加载，模态框功能将无法使用");
            window.emailAlertDebug.errors.push("Bootstrap库未加载");
            
            // 尝试动态加载Bootstrap
            const script = document.createElement('script');
            script.src = "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js";
            script.integrity = "sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p";
            script.crossOrigin = "anonymous";
            script.onload = function() {
                console.log("已动态加载Bootstrap库");
                initOtherEventHandlers(); // 初始化其他事件处理程序
            };
            document.head.appendChild(script);
        } else {
            console.log("Bootstrap库已加载，版本:", bootstrap.Tooltip.VERSION);
            initOtherEventHandlers(); // 初始化其他事件处理程序
        }
        
        // 标记初始化完成
        window.emailAlertDebug.initialized = true;
        console.log("邮件预警模块初始化完成");
        
    } catch (error) {
        console.error("邮件预警模块初始化失败:", error);
        window.emailAlertDebug.errors.push(error.message);
    }
    
    // 发送预警邮件点击处理程序
    function handleSendAlertEmailClick(event) {
        console.log("发送预警邮件按钮点击处理开始", event);
        window.emailAlertDebug.events.push({
            type: 'click',
            element: 'sendAlertEmailBtn',
            timestamp: new Date().toISOString()
        });
        
        try {
            // 使用页面定义的函数或当前JS文件的函数
            if (typeof window.generateEmailPreview === 'function') {
                console.log("使用全局预览生成函数");
                window.generateEmailPreview();
            } else {
                console.log("使用本地预览生成函数");
                generateEmailPreview();
            }
            
            // 显示模态框
            const emailPreviewModal = document.getElementById('emailPreviewModal');
            if (emailPreviewModal) {
                console.log("找到模态框元素，尝试显示");
                try {
                    const modal = new bootstrap.Modal(emailPreviewModal);
                    console.log("模态框实例创建成功", modal);
                    modal.show();
                    console.log("模态框显示方法已调用");
                } catch (error) {
                    console.error("显示模态框时出错:", error);
                    
                    // 尝试使用jQuery方法作为备用（如果可用）
                    if (typeof $ !== 'undefined') {
                        console.log("尝试使用jQuery显示模态框");
                        try {
                            $(emailPreviewModal).modal('show');
                            console.log("已使用jQuery显示模态框");
                        } catch (jqError) {
                            console.error("使用jQuery显示模态框失败:", jqError);
                        }
                    }
                }
            } else {
                console.error("错误: 未找到模态框元素 (ID: emailPreviewModal)");
                alert("无法显示预警邮件预览，未找到模态框元素");
            }
        } catch (error) {
            console.error("处理发送预警邮件按钮点击时出错:", error);
            alert("处理发送预警邮件请求时出错: " + error.message);
        }
    }
    
    // 初始化其他事件处理程序
    function initOtherEventHandlers() {
        console.log("初始化其他事件处理程序");
        
        // 处理刷新预览按钮点击事件
        const refreshPreviewBtn = document.getElementById('refreshPreviewBtn');
        if (refreshPreviewBtn) {
            refreshPreviewBtn.addEventListener('click', function() {
                console.log("刷新预览按钮被点击");
                try {
                    if (typeof window.generateEmailPreview === 'function') {
                        window.generateEmailPreview();
                    } else {
                        generateEmailPreview();
                    }
                    console.log("邮件预览已刷新");
                } catch (error) {
                    console.error("刷新邮件预览时出错:", error);
                }
            });
        }
        
        // 处理选项变更事件
        document.querySelectorAll('#includeExpiredItems, #include30DaysItems, #include60DaysItems, #include90DaysItems')
            .forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    console.log("预警选项变更:", this.id, "值:", this.checked);
                    try {
                        if (typeof window.generateEmailPreview === 'function') {
                            window.generateEmailPreview();
                        } else {
                            generateEmailPreview();
                        }
                    } catch (error) {
                        console.error("选项变更后生成预览时出错:", error);
                    }
                });
            });
        
        // 处理发送邮件按钮点击事件
        const sendEmailBtn = document.getElementById('sendEmailBtn');
        if (sendEmailBtn) {
            sendEmailBtn.addEventListener('click', function() {
                console.log("发送邮件按钮被点击");
                try {
                    sendAlertEmails();
                } catch (error) {
                    console.error("调用sendAlertEmails时出错:", error);
                }
            });
        }
        
        console.log("所有事件处理程序初始化完成");
    }
    
    // 暴露函数到全局供调试使用
    window.debugEmailAlert = {
        generatePreview: function() {
            try {
                generateEmailPreview();
                return "预览生成成功";
            } catch (error) {
                console.error("生成预览出错:", error);
                return "预览生成失败: " + error.message;
            }
        },
        sendEmails: function() {
            try {
                sendAlertEmails();
                return "开始发送邮件";
            } catch (error) {
                console.error("发送邮件出错:", error);
                return "发送邮件失败: " + error.message;
            }
        },
        showModal: function() {
            const emailPreviewModal = document.getElementById('emailPreviewModal');
            if (emailPreviewModal) {
                try {
                    const modal = new bootstrap.Modal(emailPreviewModal);
                    modal.show();
                    return "模态框已显示";
                } catch (error) {
                    console.error("显示模态框出错:", error);
                    return "显示模态框失败: " + error.message;
                }
            } else {
                return "未找到模态框元素";
            }
        },
        status: function() {
            return {
                initialized: window.emailAlertDebug.initialized,
                errors: window.emailAlertDebug.errors,
                elements: Object.keys(window.emailAlertDebug.elements).reduce((obj, key) => {
                    obj[key] = !!window.emailAlertDebug.elements[key];
                    return obj;
                }, {}),
                events: window.emailAlertDebug.events,
                csrfToken: window.emailAlertDebug.csrfToken ? "存在" : "不存在"
            };
        }
    };
    
    // 其余的生成预览和发送邮件函数保持不变，只添加更多的日志

    // 生成邮件预览内容函数 - 使用window.allItems
    function generateEmailPreview() {
        console.log("生成邮件预览内容");
        const emailRecipients = document.getElementById('emailRecipients');
        const emailContent = document.getElementById('emailContent');
        const sendEmailBtn = document.getElementById('sendEmailBtn');
        
        if (!emailRecipients || !emailContent) {
            console.error("未找到邮件内容或收件人元素");
            return;
        }
        
        // 获取选项状态
        const includeExpired = document.getElementById('includeExpiredItems').checked;
        const include30Days = document.getElementById('include30DaysItems').checked;
        const include60Days = document.getElementById('include60DaysItems').checked;
        const include90Days = document.getElementById('include90DaysItems').checked;
        
        console.log("预警选项状态:", {
            includeExpired,
            include30Days,
            include60Days,
            include90Days
        });
        
        // 确认allItems全局变量存在
        if (typeof window.allItems === 'undefined' || !Array.isArray(window.allItems)) {
            console.error("错误: window.allItems 未定义或不是数组");
            emailContent.innerHTML = '<div class="alert alert-danger">数据加载错误，请刷新页面</div>';
            if (sendEmailBtn) sendEmailBtn.disabled = true;
            return;
        }
        
        console.log("allItems共有", window.allItems.length, "个物品");
        
        // 获取选中的负责人
        const selectedResponsibles = new Set();
        document.querySelectorAll('.responsible-checkbox:checked').forEach(checkbox => {
            selectedResponsibles.add(checkbox.value);
        });
        
        console.log(`已选中 ${selectedResponsibles.size} 个负责人`);
        
        // 根据条件筛选物品
        const filteredItems = [];
        
        window.allItems.forEach(item => {
            const daysRemaining = item.days_remaining;
            
            // 首先检查是否选中了该负责人
            if (!item.responsible_person || !selectedResponsibles.has(item.responsible_person)) {
                return; // 跳过未选中负责人的物品
            }
            
            if (daysRemaining < 0 && includeExpired) {
                filteredItems.push(item);
            } else if (daysRemaining >= 0 && daysRemaining <= 30 && include30Days) {
                filteredItems.push(item);
            } else if (daysRemaining > 30 && daysRemaining <= 60 && include60Days) {
                filteredItems.push(item);
            } else if (daysRemaining > 60 && daysRemaining <= 90 && include90Days) {
                filteredItems.push(item);
            }
        });
        
        console.log(`筛选后的物品数量: ${filteredItems.length}`);
        
        // 如果没有符合条件的物品，显示提示
        if (filteredItems.length === 0) {
            emailContent.innerHTML = '<div class="alert alert-info">没有符合条件的预警物品</div>';
            if (sendEmailBtn) sendEmailBtn.disabled = true;
            return;
        }
        
        // 创建邮件内容
        createEmailContent(filteredItems, emailContent, emailRecipients);
        
        // 启用发送按钮
        if (sendEmailBtn) sendEmailBtn.disabled = false;
    }
    
    // 发送邮件函数
    function sendAlertEmails() {
        console.log("准备发送预警邮件");
        
        // 获取邮件信息
        const emailSubject = document.getElementById('emailSubject').value;
        const emailContent = document.getElementById('emailContent').innerHTML;
        
        if (!emailContent) {
            console.error("邮件内容为空，无法发送");
            return;
        }
        
        // 获取选项状态
        const includeExpired = document.getElementById('includeExpiredItems').checked;
        const include30Days = document.getElementById('include30DaysItems').checked;
        const include60Days = document.getElementById('include60DaysItems').checked;
        const include90Days = document.getElementById('include90DaysItems').checked;
        
        // 获取选中的负责人
        const selectedResponsibles = [];
        document.querySelectorAll('.responsible-checkbox:checked').forEach(checkbox => {
            selectedResponsibles.push(checkbox.value);
        });
        
        // 显示发送状态
        const emailSendAlert = document.getElementById('emailSendAlert');
        const emailSendMessage = document.getElementById('emailSendMessage');
        const emailSendSpinner = document.getElementById('emailSendSpinner');
        const sendEmailBtn = document.getElementById('sendEmailBtn');
        
        if (!emailSendAlert || !emailSendMessage || !emailSendSpinner) {
            console.error("未找到邮件发送状态元素");
            return;
        }
        
        // 更新UI状态
        emailSendAlert.classList.remove('d-none', 'alert-danger', 'alert-success');
        emailSendAlert.classList.add('alert-info');
        emailSendMessage.textContent = '正在发送邮件...';
        emailSendSpinner.style.display = 'inline-block';
        
        if (sendEmailBtn) sendEmailBtn.disabled = true;
        
        // 获取筛选后的物品数据，用于后端重新生成个性化内容
        const filteredItems = [];
        
        // 只传递必要的属性以减少数据量
        if (window.allItems && Array.isArray(window.allItems)) {
            window.allItems.forEach(item => {
                if (item.responsible_person && selectedResponsibles.includes(item.responsible_person)) {
                    const daysRemaining = item.days_remaining;
                    
                    if ((daysRemaining < 0 && includeExpired) || 
                        (daysRemaining >= 0 && daysRemaining <= 30 && include30Days) ||
                        (daysRemaining > 30 && daysRemaining <= 60 && include60Days) ||
                        (daysRemaining > 60 && daysRemaining <= 90 && include90Days)) {
                        
                        filteredItems.push({
                            name: item.name,
                            model: item.model,
                            area_name: item.area_name,
                            location: item.location,
                            expiry_date: item.expiry_date,
                            days_remaining: item.days_remaining,
                            responsible_person: item.responsible_person
                        });
                    }
                }
            });
        }
        
        // 创建要发送的数据 - 添加 filteredItems
        const postData = {
            email_subject: emailSubject,
            email_content: emailContent,
            options: {
                include_expired: includeExpired,
                include_30days: include30Days,
                include_60days: include60Days,
                include_90days: include90Days
            },
            selected_responsibles: selectedResponsibles,
            items: filteredItems  // 添加筛选后的原始物品数据
        };
        
        console.log("发送AJAX请求到 /admin/send_expiry_alert_emails");
        
        // 获取CSRF令牌 - 尝试多种方法获取
        let csrfToken = null;
        
        // 方法1: 从meta标签获取
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            csrfToken = csrfMeta.getAttribute('content');
            console.log("从meta标签获取CSRF令牌:", csrfToken ? "成功" : "失败");
        }
        
        // 方法2: 从cookie获取
        if (!csrfToken) {
            const csrfCookie = document.cookie.split(';').find(c => c.trim().startsWith('csrf_token='));
            if (csrfCookie) {
                csrfToken = csrfCookie.split('=')[1];
                console.log("从cookie获取CSRF令牌:", csrfToken ? "成功" : "失败");
            }
        }
        
        // 方法3: 尝试从隐藏输入字段获取
        if (!csrfToken) {
            const csrfInput = document.querySelector('input[name="csrf_token"]');
            if (csrfInput) {
                csrfToken = csrfInput.value;
                console.log("从隐藏输入字段获取CSRF令牌:", csrfToken ? "成功" : "失败");
            }
        }
        
        if (!csrfToken) {
            console.error("无法获取CSRF令牌，请求可能会失败");
            emailSendAlert.classList.remove('alert-info');
            emailSendAlert.classList.add('alert-danger');
            emailSendAlert.classList.remove('d-none');
            emailSendMessage.textContent = "无法获取安全令牌(CSRF)，请刷新页面后重试";
            emailSendSpinner.style.display = 'none';
            if (sendEmailBtn) sendEmailBtn.disabled = false;
            return;
        }
        
        // 准备请求头
        const headers = {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest' // 添加这个头部标识AJAX请求
        };
        
        // 从cookie添加额外的CSRF令牌
        if (document.cookie.includes('csrf_token=')) {
            headers['X-CSRF-TOKEN'] = csrfToken;
        }
        
        console.log("请求头:", headers);
        console.log("CSRF令牌:", csrfToken);
        
        // 发送AJAX请求
        fetch('/admin/send_expiry_alert_emails', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(postData),
            credentials: 'same-origin' // 确保发送Cookie
        })
        .then(response => {
            console.log("收到服务器响应:", response.status);
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || `服务器返回错误状态码: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log("邮件发送结果:", data);
            
            // 更新UI状态
            emailSendSpinner.style.display = 'none';
            if (sendEmailBtn) sendEmailBtn.disabled = false;
            
            if (data.success) {
                // 发送成功
                emailSendAlert.classList.remove('alert-info');
                emailSendAlert.classList.add('alert-success');
                
                if (data.recipients_count > 0) {
                    emailSendMessage.textContent = `邮件发送成功！已发送给 ${data.recipients_count} 位接收者。`;
                } else {
                    emailSendMessage.textContent = '没有找到有效的收件人邮箱地址。请确保负责人信息中有正确的邮箱地址。';
                }
                
                // 3秒后自动关闭模态框
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('emailPreviewModal'));
                    if (modal) modal.hide();
                }, 3000);
            } else {
                // 发送失败
                emailSendAlert.classList.remove('alert-info');
                emailSendAlert.classList.add('alert-danger');
                emailSendMessage.textContent = `邮件发送失败：${data.error || '未知错误'}`;
            }
        })
        .catch(error => {
            console.error("邮件发送请求错误:", error);
            
            // 更新UI状态
            emailSendSpinner.style.display = 'none';
            if (sendEmailBtn) sendEmailBtn.disabled = false;
            emailSendAlert.classList.remove('alert-info');
            emailSendAlert.classList.add('alert-danger');
            emailSendMessage.textContent = `发生错误：${error.message}`;
        });
    }
});

// 同样修复页面内备份函数中的同样问题
window.generateEmailPreview = function() {
    console.log("使用页面内定义的generateEmailPreview函数");
    const emailRecipients = document.getElementById('emailRecipients');
    const emailContent = document.getElementById('emailContent');
    const sendEmailBtn = document.getElementById('sendEmailBtn');
    
    if (!emailRecipients || !emailContent) {
        console.error("未找到邮件内容或收件人元素");
        return;
    }
    
    // 获取选项状态 - 确保这些变量定义在这个作用域内
    const includeExpired = document.getElementById('includeExpiredItems').checked;
    const include30Days = document.getElementById('include30DaysItems').checked;
    const include60Days = document.getElementById('include60DaysItems').checked;
    const include90Days = document.getElementById('include90DaysItems').checked;
    
    console.log("预警选项状态:", {
        includeExpired,
        include30Days,
        include60Days,
        include90Days
    });
    
    // 确认allItems全局变量存在
    if (typeof window.allItems === 'undefined' || !Array.isArray(window.allItems)) {
        console.error("错误: window.allItems 未定义或不是数组");
        emailContent.innerHTML = '<div class="alert alert-danger">数据加载错误，请刷新页面</div>';
        if (sendEmailBtn) sendEmailBtn.disabled = true;
        return;
    }
    
    console.log("allItems共有", window.allItems.length, "个物品");
    
    // 获取选中的负责人
    const selectedResponsibles = new Set();
    document.querySelectorAll('.responsible-checkbox:checked').forEach(checkbox => {
        selectedResponsibles.add(checkbox.value);
    });
    
    console.log(`已选中 ${selectedResponsibles.size} 个负责人`);
    
    // 根据条件筛选物品 - 确保在这里定义filteredItems变量
    const filteredItems = [];
    
    window.allItems.forEach(item => {
        const daysRemaining = item.days_remaining;
        
        // 首先检查是否选中了该负责人
        if (!item.responsible_person || !selectedResponsibles.has(item.responsible_person)) {
            return; // 跳过未选中负责人的物品
        }
        
        // 在这里使用之前已经正确定义的变量
        if (daysRemaining < 0 && includeExpired) {
            filteredItems.push(item);
        } else if (daysRemaining >= 0 && daysRemaining <= 30 && include30Days) {
            filteredItems.push(item);
        } else if (daysRemaining > 30 && daysRemaining <= 60 && include60Days) {
            filteredItems.push(item);
        } else if (daysRemaining > 60 && daysRemaining <= 90 && include90Days) {
            filteredItems.push(item);
        }
    });
    
    console.log(`筛选后的物品数量: ${filteredItems.length}`);
    
    // 如果没有符合条件的物品，显示提示
    if (filteredItems.length === 0) {
        emailContent.innerHTML = '<div class="alert alert-info">没有符合条件的预警物品</div>';
        if (sendEmailBtn) sendEmailBtn.disabled = true;
        return;
    }
    
    // 创建邮件内容 - 使用定义好的filteredItems变量
    createEmailContent(filteredItems, emailContent, emailRecipients);
    
    // 启用发送按钮
    if (sendEmailBtn) sendEmailBtn.disabled = false;
};

// 在邮件预览模态框显示时初始化负责人选择列表
document.addEventListener('DOMContentLoaded', function() {
    // ...existing code...
    
    // 获取邮件预览模态框元素
    const emailPreviewModal = document.getElementById('emailPreviewModal');
    if (emailPreviewModal) {
        // 监听模态框显示事件
        emailPreviewModal.addEventListener('show.bs.modal', function() {
            console.log("邮件预览模态框正在显示");
            // 初始化负责人选择列表
            initResponsibleCheckboxes();
        });
    }
    
    // 添加全选和取消全选按钮事件
    const selectAllBtn = document.getElementById('selectAllResponsible');
    const deselectAllBtn = document.getElementById('deselectAllResponsible');
    
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('.responsible-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = true;
            });
            // 刷新预览
            if (typeof window.generateEmailPreview === 'function') {
                window.generateEmailPreview();
            } else {
                generateEmailPreview();
            }
        });
    }
    
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', function() {
            const checkboxes = document.querySelectorAll('.responsible-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = false;
            });
            // 刷新预览
            if (typeof window.generateEmailPreview === 'function') {
                window.generateEmailPreview();
            } else {
                generateEmailPreview();
            }
        });
    }
});

// 初始化负责人选择列表
function initResponsibleCheckboxes() {
    const container = document.getElementById('responsibleCheckboxes');
    if (!container) return;
    
    // 清空容器
    container.innerHTML = '';
    
    // 从allItems中提取唯一的负责人列表
    const responsiblePersons = new Set();
    
    if (window.allItems && window.allItems.length > 0) {
        window.allItems.forEach(item => {
            if (item.responsible_person) {
                responsiblePersons.add(item.responsible_person);
            }
        });
    }
    
    // 如果没有负责人，显示提示
    if (responsiblePersons.size === 0) {
        container.innerHTML = '<div class="text-center py-2 text-muted">没有找到负责人信息</div>';
        return;
    }
    
    // 将Set转换为排序后的数组
    const responsibleArray = Array.from(responsiblePersons).sort();
    
    // 为每个负责人创建一个复选框
    responsibleArray.forEach(person => {
        const div = document.createElement('div');
        div.className = 'form-check';
        
        const input = document.createElement('input');
        input.className = 'form-check-input responsible-checkbox';
        input.type = 'checkbox';
        input.id = `responsible-${person.replace(/\s+/g, '-')}`;
        input.value = person;
        input.checked = true; // 默认选中
        input.dataset.responsible = person;
        
        // 添加变更事件，当选中状态变化时重新生成预览
        input.addEventListener('change', function() {
            if (typeof window.generateEmailPreview === 'function') {
                window.generateEmailPreview();
            } else {
                generateEmailPreview();
            }
        });
        
        const label = document.createElement('label');
        label.className = 'form-check-label';
        label.htmlFor = input.id;
        label.textContent = person;
        
        div.appendChild(input);
        div.appendChild(label);
        container.appendChild(div);
    });
    
    console.log(`已加载 ${responsibleArray.length} 个负责人选项`);
}

// 修改generateEmailPreview函数，考虑选中的负责人
function generateEmailPreview() {
    // ...existing code...
    
    // 获取选中的负责人
    const selectedResponsibles = new Set();
    document.querySelectorAll('.responsible-checkbox:checked').forEach(checkbox => {
        selectedResponsibles.add(checkbox.value);
    });
    
    console.log(`已选中 ${selectedResponsibles.size} 个负责人`);
    
    // 修改筛选逻辑，只包含选中的负责人的物品
    const filteredItems = [];
    
    window.allItems.forEach(item => {
        const daysRemaining = item.days_remaining;
        
        // 首先检查是否选中了该负责人
        if (!item.responsible_person || !selectedResponsibles.has(item.responsible_person)) {
            return; // 跳过未选中负责人的物品
        }
        
        if (daysRemaining < 0 && includeExpired) {
            filteredItems.push(item);
        } else if (daysRemaining >= 0 && daysRemaining <= 30 && include30Days) {
            filteredItems.push(item);
        } else if (daysRemaining > 30 && daysRemaining <= 60 && include60Days) {
            filteredItems.push(item);
        } else if (daysRemaining > 60 && daysRemaining <= 90 && include90Days) {
            filteredItems.push(item);
        }
    });
    
    // ...existing code...
}

// 修改window.generateEmailPreview函数，考虑选中的负责人
window.generateEmailPreview = function() {
    console.log("使用页面内定义的generateEmailPreview函数");
    const emailRecipients = document.getElementById('emailRecipients');
    const emailContent = document.getElementById('emailContent');
    const sendEmailBtn = document.getElementById('sendEmailBtn');
    
    if (!emailRecipients || !emailContent) {
        console.error("未找到邮件内容或收件人元素");
        return;
    }
    
    // 获取选项状态 - 确保这些变量定义在这个作用域内
    const includeExpired = document.getElementById('includeExpiredItems').checked;
    const include30Days = document.getElementById('include30DaysItems').checked;
    const include60Days = document.getElementById('include60DaysItems').checked;
    const include90Days = document.getElementById('include90DaysItems').checked;
    
    console.log("预警选项状态:", {
        includeExpired,
        include30Days,
        include60Days,
        include90Days
    });
    
    // 确认allItems全局变量存在
    if (typeof window.allItems === 'undefined' || !Array.isArray(window.allItems)) {
        console.error("错误: window.allItems 未定义或不是数组");
        emailContent.innerHTML = '<div class="alert alert-danger">数据加载错误，请刷新页面</div>';
        if (sendEmailBtn) sendEmailBtn.disabled = true;
        return;
    }
    
    console.log("allItems共有", window.allItems.length, "个物品");
    
    // 获取选中的负责人
    const selectedResponsibles = new Set();
    document.querySelectorAll('.responsible-checkbox:checked').forEach(checkbox => {
        selectedResponsibles.add(checkbox.value);
    });
    
    console.log(`已选中 ${selectedResponsibles.size} 个负责人`);
    
    // 根据条件筛选物品 - 确保在这里定义filteredItems变量
    const filteredItems = [];
    
    window.allItems.forEach(item => {
        const daysRemaining = item.days_remaining;
        
        // 首先检查是否选中了该负责人
        if (!item.responsible_person || !selectedResponsibles.has(item.responsible_person)) {
            return; // 跳过未选中负责人的物品
        }
        
        // 在这里使用之前已经正确定义的变量
        if (daysRemaining < 0 && includeExpired) {
            filteredItems.push(item);
        } else if (daysRemaining >= 0 && daysRemaining <= 30 && include30Days) {
            filteredItems.push(item);
        } else if (daysRemaining > 30 && daysRemaining <= 60 && include60Days) {
            filteredItems.push(item);
        } else if (daysRemaining > 60 && daysRemaining <= 90 && include90Days) {
            filteredItems.push(item);
        }
    });
    
    console.log(`筛选后的物品数量: ${filteredItems.length}`);
    
    // 如果没有符合条件的物品，显示提示
    if (filteredItems.length === 0) {
        emailContent.innerHTML = '<div class="alert alert-info">没有符合条件的预警物品</div>';
        if (sendEmailBtn) sendEmailBtn.disabled = true;
        return;
    }
    
    // 创建邮件内容 - 使用定义好的filteredItems变量
    createEmailContent(filteredItems, emailContent, emailRecipients);
    
    // 启用发送按钮
    if (sendEmailBtn) sendEmailBtn.disabled = false;
};

// 修改sendAlertEmails函数，添加选中的负责人到请求数据中
function sendAlertEmails() {
    console.log("准备发送预警邮件");
        
    // 获取邮件信息
    const emailSubject = document.getElementById('emailSubject').value;
    const emailContent = document.getElementById('emailContent').innerHTML;
    
    if (!emailContent) {
        console.error("邮件内容为空，无法发送");
        return;
    }
    
    // 获取选项状态
    const includeExpired = document.getElementById('includeExpiredItems').checked;
    const include30Days = document.getElementById('include30DaysItems').checked;
    const include60Days = document.getElementById('include60DaysItems').checked;
    const include90Days = document.getElementById('include90DaysItems').checked;
    
    // 获取选中的负责人
    const selectedResponsibles = [];
    document.querySelectorAll('.responsible-checkbox:checked').forEach(checkbox => {
        selectedResponsibles.push(checkbox.value);
    });
    
    // 显示发送状态
    const emailSendAlert = document.getElementById('emailSendAlert');
    const emailSendMessage = document.getElementById('emailSendMessage');
    const emailSendSpinner = document.getElementById('emailSendSpinner');
    const sendEmailBtn = document.getElementById('sendEmailBtn');
    
    if (!emailSendAlert || !emailSendMessage || !emailSendSpinner) {
        console.error("未找到邮件发送状态元素");
        return;
    }
    
    // 更新UI状态
    emailSendAlert.classList.remove('d-none', 'alert-danger', 'alert-success');
    emailSendAlert.classList.add('alert-info');
    emailSendMessage.textContent = '正在发送邮件...';
    emailSendSpinner.style.display = 'inline-block';
    
    if (sendEmailBtn) sendEmailBtn.disabled = true;
    
    // 获取筛选后的物品数据，用于后端重新生成个性化内容
    const filteredItems = [];
    
    // 只传递必要的属性以减少数据量
    if (window.allItems && Array.isArray(window.allItems)) {
        window.allItems.forEach(item => {
            if (item.responsible_person && selectedResponsibles.includes(item.responsible_person)) {
                const daysRemaining = item.days_remaining;
                
                if ((daysRemaining < 0 && includeExpired) || 
                    (daysRemaining >= 0 && daysRemaining <= 30 && include30Days) ||
                    (daysRemaining > 30 && daysRemaining <= 60 && include60Days) ||
                    (daysRemaining > 60 && daysRemaining <= 90 && include90Days)) {
                    
                    filteredItems.push({
                        name: item.name,
                        model: item.model,
                        area_name: item.area_name,
                        location: item.location,
                        expiry_date: item.expiry_date,
                        days_remaining: item.days_remaining,
                        responsible_person: item.responsible_person
                    });
                }
            }
        });
    }
    
    // 创建要发送的数据 - 添加 filteredItems
    const postData = {
        email_subject: emailSubject,
        email_content: emailContent,
        options: {
            include_expired: includeExpired,
            include_30days: include30Days,
            include_60days: include60Days,
            include_90days: include90Days
        },
        selected_responsibles: selectedResponsibles,
        items: filteredItems  // 添加筛选后的原始物品数据
    };
    
    console.log("发送AJAX请求到 /admin/send_expiry_alert_emails");
    
    // 获取CSRF令牌 - 尝试多种方法获取
    let csrfToken = null;
    
    // 方法1: 从meta标签获取
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    if (csrfMeta) {
        csrfToken = csrfMeta.getAttribute('content');
        console.log("从meta标签获取CSRF令牌:", csrfToken ? "成功" : "失败");
    }
    
    // 方法2: 从cookie获取
    if (!csrfToken) {
        const csrfCookie = document.cookie.split(';').find(c => c.trim().startsWith('csrf_token='));
        if (csrfCookie) {
            csrfToken = csrfCookie.split('=')[1];
            console.log("从cookie获取CSRF令牌:", csrfToken ? "成功" : "失败");
        }
    }
    
    // 方法3: 尝试从隐藏输入字段获取
    if (!csrfToken) {
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        if (csrfInput) {
            csrfToken = csrfInput.value;
            console.log("从隐藏输入字段获取CSRF令牌:", csrfToken ? "成功" : "失败");
        }
    }
    
    if (!csrfToken) {
        console.error("无法获取CSRF令牌，请求可能会失败");
        emailSendAlert.classList.remove('alert-info');
        emailSendAlert.classList.add('alert-danger');
        emailSendAlert.classList.remove('d-none');
        emailSendMessage.textContent = "无法获取安全令牌(CSRF)，请刷新页面后重试";
        emailSendSpinner.style.display = 'none';
        if (sendEmailBtn) sendEmailBtn.disabled = false;
        return;
    }
    
    // 准备请求头
    const headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
        'X-Requested-With': 'XMLHttpRequest' // 添加这个头部标识AJAX请求
    };
    
    // 从cookie添加额外的CSRF令牌
    if (document.cookie.includes('csrf_token=')) {
        headers['X-CSRF-TOKEN'] = csrfToken;
    }
    
    console.log("请求头:", headers);
    console.log("CSRF令牌:", csrfToken);
    
    // 发送AJAX请求
    fetch('/admin/send_expiry_alert_emails', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(postData),
        credentials: 'same-origin' // 确保发送Cookie
    })
    .then(response => {
        console.log("收到服务器响应:", response.status);
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `服务器返回错误状态码: ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log("邮件发送结果:", data);
        
        // 更新UI状态
        emailSendSpinner.style.display = 'none';
        if (sendEmailBtn) sendEmailBtn.disabled = false;
        
        if (data.success) {
            // 发送成功
            emailSendAlert.classList.remove('alert-info');
            emailSendAlert.classList.add('alert-success');
            
            if (data.recipients_count > 0) {
                emailSendMessage.textContent = `邮件发送成功！已发送给 ${data.recipients_count} 位接收者。`;
            } else {
                emailSendMessage.textContent = '没有找到有效的收件人邮箱地址。请确保负责人信息中有正确的邮箱地址。';
            }
            
            // 3秒后自动关闭模态框
            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('emailPreviewModal'));
                if (modal) modal.hide();
            }, 3000);
        } else {
            // 发送失败
            emailSendAlert.classList.remove('alert-info');
            emailSendAlert.classList.add('alert-danger');
            emailSendMessage.textContent = `邮件发送失败：${data.error || '未知错误'}`;
        }
    })
    .catch(error => {
        console.error("邮件发送请求错误:", error);
        
        // 更新UI状态
        emailSendSpinner.style.display = 'none';
        if (sendEmailBtn) sendEmailBtn.disabled = false;
        emailSendAlert.classList.remove('alert-info');
        emailSendAlert.classList.add('alert-danger');
        emailSendMessage.textContent = `发生错误：${error.message}`;
    });
}

// 同样更新页面内备份的sendAlertEmails函数
window.sendAlertEmails = function() {
    console.log("使用页面内定义的sendAlertEmails函数");
    // 直接调用主函数
    sendAlertEmails();
};
