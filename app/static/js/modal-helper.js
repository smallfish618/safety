/**
 * 模态框管理辅助脚本 - 修复模态框不显示但背景变暗的问题
 */
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        // 用于追踪模态框状态
        let activeModals = [];
        let hangingBackdrops = 0;
        
        // 检测每个模态框事件
        document.querySelectorAll('.modal').forEach(modal => {
            // 监听模态框显示事件
            modal.addEventListener('show.bs.modal', function() {
                console.log('模态框正在打开:', this.id);
                activeModals.push(this.id);
            });
            
            // 监听模态框隐藏事件
            modal.addEventListener('hidden.bs.modal', function() {
                console.log('模态框已关闭:', this.id);
                activeModals = activeModals.filter(id => id !== this.id);
                
                // 强制清理模态框遗留样式
                forceCleanupModal(this);
                
                // 定期清理遗留的背景层
                setTimeout(cleanupBackdrops, 50);
                setTimeout(cleanupBackdrops, 300);
            });
            
            // 监听模态框出错事件
            modal.addEventListener('hidePrevented.bs.modal', function() {
                console.warn('模态框关闭被阻止:', this.id);
            });
        });
        
        // 监听添加有效期规则按钮，确保它正确工作
        const addRuleBtn = document.querySelector('button[data-bs-target="#addExpiryRuleModal"]');
        if (addRuleBtn) {
            addRuleBtn.addEventListener('click', function(e) {
                e.preventDefault();  // 阻止默认操作
                
                // 先确保所有遗留模态框已清理
                cleanupAllModals();
                
                // 尝试直接通过JavaScript打开模态框
                try {
                    const modalId = this.getAttribute('data-bs-target').substring(1); // 去掉#号
                    const modalElement = document.getElementById(modalId);
                    if (modalElement) {
                        const modal = new bootstrap.Modal(modalElement);
                        modal.show();
                    } else {
                        console.error('找不到模态框元素:', modalId);
                    }
                } catch (err) {
                    console.error('打开模态框出错:', err);
                    // 备用方法：直接操作DOM
                    emergencyOpenModal('addExpiryRuleModal');
                }
            });
        }
        
        // 定期检查是否有悬挂的模态框背景
        setInterval(function() {
            const backdrops = document.querySelectorAll('.modal-backdrop');
            if (backdrops.length > 0 && activeModals.length === 0) {
                console.warn('检测到悬挂的模态框背景:', backdrops.length);
                cleanupBackdrops();
                hangingBackdrops++;
                
                if (hangingBackdrops > 3) {
                    console.warn('多次检测到悬挂背景，执行完全页面刷新');
                    // 可以选择重载页面或重置所有模态框
                    resetModalSystem();
                    hangingBackdrops = 0;
                }
            } else {
                hangingBackdrops = 0;
            }
        }, 2000);
        
        // 监听ESC键，防止键盘事件被模态框吞噬
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && document.querySelectorAll('.modal-backdrop').length > 0) {
                console.log('检测到ESC键，尝试关闭所有模态框');
                cleanupAllModals();
            }
        });
    });
    
    // 强制清理模态框方法
    function forceCleanupModal(modalElement) {
        // 移除可能添加的内联样式
        modalElement.style.display = '';
        modalElement.style.paddingRight = '';
        modalElement.classList.remove('show');
        modalElement.setAttribute('aria-hidden', 'true');
        modalElement.removeAttribute('aria-modal');
        modalElement.removeAttribute('role');
        
        // 确保模态框隐藏
        if (window.getComputedStyle(modalElement).display !== 'none') {
            modalElement.style.display = 'none';
        }
    }
    
    // 清理所有模态框背景层
    function cleanupBackdrops() {
        document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
            backdrop.remove();
        });
        
        // 清理body上的样式
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }
    
    // 清理所有模态框
    function cleanupAllModals() {
        // 隐藏所有模态框
        document.querySelectorAll('.modal').forEach(modal => {
            forceCleanupModal(modal);
        });
        
        // 清理遗留背景
        cleanupBackdrops();
    }
    
    // 紧急打开模态框 - 使用DOM直接操作
    function emergencyOpenModal(modalId) {
        cleanupAllModals(); // 首先清理现有模态框
        
        const modalElement = document.getElementById(modalId);
        if (!modalElement) return;
        
        // 添加模态框背景
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        document.body.appendChild(backdrop);
        
        // 显示模态框
        modalElement.style.display = 'block';
        modalElement.classList.add('show');
        modalElement.setAttribute('aria-modal', 'true');
        modalElement.setAttribute('role', 'dialog');
        modalElement.removeAttribute('aria-hidden');
        
        // 设置body样式
        document.body.classList.add('modal-open');
        document.body.style.overflow = 'hidden';
        document.body.style.paddingRight = '17px';
        
        // 添加关闭按钮事件
        const closeButtons = modalElement.querySelectorAll('[data-bs-dismiss="modal"]');
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                cleanupAllModals();
            });
        });
    }
    
    // 完全重置模态框系统 - 最后的手段
    function resetModalSystem() {
        cleanupAllModals();
        console.info('模态框系统已重置');
        
        // 可选：重新初始化所有模态框
        document.querySelectorAll('.modal').forEach(modal => {
            try {
                if (bootstrap && bootstrap.Modal) {
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) modalInstance.dispose();
                    // 不要立即重新初始化，让Bootstrap在下次点击时处理
                }
            } catch (e) {
                console.warn('重置模态框时出错:', e);
            }
        });
    }
})();

/**
 * 模态框功能辅助脚本
 * 用于确保所有模态框可以正常工作
 */
document.addEventListener('DOMContentLoaded', function() {
    // 1. 确保所有模态框触发按钮正常工作
    document.querySelectorAll('[data-bs-toggle="modal"]').forEach(function(button) {
        button.addEventListener('click', function(e) {
            // 获取目标模态框
            const targetSelector = this.getAttribute('data-bs-target');
            const modalElement = document.querySelector(targetSelector);
            
            if (modalElement) {
                // 确保先移除可能残留的背景遮罩
                document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
                    backdrop.remove();
                });
                
                try {
                    // 尝试使用Bootstrap API打开模态框
                    const modal = new bootstrap.Modal(modalElement);
                    modal.show();
                } catch (error) {
                    console.warn('使用Bootstrap API打开模态框失败，使用备用方法', error);
                    
                    // 备用方法：手动添加必要的类和样式
                    modalElement.classList.add('show');
                    modalElement.style.display = 'block';
                    modalElement.setAttribute('aria-modal', 'true');
                    modalElement.setAttribute('role', 'dialog');
                    document.body.classList.add('modal-open');
                    
                    // 添加背景遮罩
                    const backdrop = document.createElement('div');
                    backdrop.className = 'modal-backdrop fade show';
                    document.body.appendChild(backdrop);
                }
            } else {
                console.error('找不到目标模态框:', targetSelector);
            }
        });
    });
    
    // 2. 为所有模态框添加关闭事件处理
    document.querySelectorAll('.modal').forEach(function(modal) {
        // 处理关闭按钮点击
        modal.querySelectorAll('[data-bs-dismiss="modal"]').forEach(function(closeBtn) {
            closeBtn.addEventListener('click', function() {
                hideModal(modal);
            });
        });
        
        // 处理点击背景关闭
        modal.addEventListener('click', function(e) {
            // 如果点击的是模态框本身而不是内容
            if (e.target === modal) {
                hideModal(modal);
            }
        });
        
        // 监听ESC键
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.classList.contains('show')) {
                hideModal(modal);
            }
        });
    });
    
    // 关闭模态框的函数
    function hideModal(modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
        modal.removeAttribute('aria-modal');
        modal.setAttribute('aria-hidden', 'true');
        
        // 移除背景遮罩
        document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
            backdrop.remove();
        });
        
        // 如果没有其他打开的模态框，恢复body样式
        if (!document.querySelector('.modal.show')) {
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        }
        
        // 如果是表单模态框，重置表单
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
    }
    
    // 特别处理编辑按钮
    document.querySelectorAll('[data-bs-target^="#editModal"]').forEach(function(editButton) {
        editButton.addEventListener('click', function(e) {
            // 获取物资ID，用于获取对应的编辑模态框
            const targetModal = this.getAttribute('data-bs-target');
            const modalElement = document.querySelector(targetModal);
            
            if (!modalElement) {
                console.error('找不到编辑模态框:', targetModal);
                return;
            }
            
            // 确保模态框能正常打开
            try {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            } catch (error) {
                console.error('打开编辑模态框失败:', error);
                
                // 备用方案：手动添加必要的类和样式
                modalElement.classList.add('show');
                modalElement.style.display = 'block';
                modalElement.setAttribute('aria-modal', 'true');
                modalElement.removeAttribute('aria-hidden');
                document.body.classList.add('modal-open');
                
                // 添加背景遮罩
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                document.body.appendChild(backdrop);
            }
        });
    });
    
    // 处理日期格式化问题
    document.querySelectorAll('input[type="date"]').forEach(function(dateInput) {
        // 如果日期input为空，但属性值不为空，将其格式化
        if (!dateInput.value && dateInput.getAttribute('value')) {
            try {
                const dateValue = dateInput.getAttribute('value');
                const date = new Date(dateValue);
                const formattedDate = date.toISOString().split('T')[0]; // YYYY-MM-DD
                dateInput.value = formattedDate;
            } catch (e) {
                console.warn('日期格式化失败:', e);
            }
        }
    });
    
    // 添加模态框之间切换的辅助函数
    window.switchModal = function(fromModalId, toModalId) {
        // 获取两个模态框元素
        const fromModal = document.getElementById(fromModalId);
        const toModal = document.getElementById(toModalId);
        
        if (!fromModal || !toModal) {
            console.error('模态框切换失败：无法找到指定的模态框');
            return;
        }
        
        // 隐藏第一个模态框
        try {
            const fromBsModal = bootstrap.Modal.getInstance(fromModal);
            if (fromBsModal) {
                fromBsModal.hide();
            } else {
                fromModal.classList.remove('show');
                fromModal.style.display = 'none';
            }
        } catch (e) {
            console.warn('隐藏源模态框失败', e);
            // 强制关闭模态框
            fromModal.classList.remove('show');
            fromModal.style.display = 'none';
        }
        
        // 等待第一个模态框隐藏动画完成
        setTimeout(function() {
            // 移除可能残留的背景遮罩
            document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
                backdrop.remove();
            });
            
            // 显示第二个模态框
            try {
                const modal = new bootstrap.Modal(toModal);
                modal.show();
            } catch (e) {
                console.warn('使用Bootstrap API显示目标模态框失败', e);
                
                // 手动显示模态框
                toModal.classList.add('show');
                toModal.style.display = 'block';
                toModal.setAttribute('aria-modal', 'true');
                toModal.removeAttribute('aria-hidden');
                document.body.classList.add('modal-open');
                
                // 添加背景遮罩
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                document.body.appendChild(backdrop);
            }
        }, 300);
    };
    
    // 为所有编辑转换按钮添加事件处理
    document.querySelectorAll('[data-detail-to-edit]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const stationId = this.getAttribute('data-station-id');
            if (!stationId) {
                console.error('缺少物资ID，无法打开编辑模态框');
                return;
            }
            
            // 关闭详情模态框，打开编辑模态框
            switchModal(`detailModal-${stationId}`, `editModal-${stationId}`);
        });
    });
});

/**
 * 模态框辅助工具 - 确保模态框正常工作
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('模态框辅助工具已加载');
    
    // 定期清理可能的残留模态框backdrop
    function cleanupModalBackdrops() {
        // 检查是否有多余的backdrop
        const backdrops = document.querySelectorAll('.modal-backdrop');
        if (backdrops.length > 1) {
            console.warn(`发现${backdrops.length}个模态框背景，清理多余的`);
            // 只保留最后一个backdrop
            for (let i = 0; i < backdrops.length - 1; i++) {
                backdrops[i].remove();
            }
        }
        
        // 检查body是否有modal-open类但没有可见模态框
        const visibleModals = document.querySelectorAll('.modal.show');
        if (visibleModals.length === 0 && document.body.classList.contains('modal-open')) {
            console.warn('发现body有modal-open类但没有可见模态框，清理样式');
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
            
            // 同时移除所有backdrop
            backdrops.forEach(backdrop => backdrop.remove());
        }
    }
    
    // 每秒钟检查一次
    setInterval(cleanupModalBackdrops, 1000);
    
    // 为所有模态框添加额外的错误处理
    document.querySelectorAll('.modal').forEach(modalElement => {
        // 监听模态框关闭事件
        modalElement.addEventListener('hidden.bs.modal', function() {
            console.log(`模态框 ${this.id} 已关闭，执行清理`);
            cleanupModalBackdrops();
        });
        
        // 监听模态框打开事件
        modalElement.addEventListener('shown.bs.modal', function() {
            console.log(`模态框 ${this.id} 已打开`);
        });
        
        // 尝试为打开此模态框的按钮添加备份事件处理
        const modalId = modalElement.id;
        if (modalId) {
            document.querySelectorAll(`[data-bs-target="#${modalId}"], [data-target="#${modalId}"]`).forEach(trigger => {
                trigger.addEventListener('click', function(e) {
                    console.log(`模态框触发按钮被点击，目标: ${modalId}`);
                    try {
                        const modal = new bootstrap.Modal(document.getElementById(modalId));
                        modal.show();
                    } catch (error) {
                        console.error(`使用主方法无法打开模态框 ${modalId}:`, error);
                        try {
                            // 备用方法
                            $(`#${modalId}`).modal('show');
                        } catch (jqError) {
                            console.error(`使用备用jQuery方法也无法打开模态框:`, jqError);
                        }
                    }
                });
            });
        }
    });
    
    // 为所有需要打开模态框的按钮添加备用事件处理
    document.querySelectorAll('[data-bs-toggle="modal"]').forEach(button => {
        const targetModalId = button.getAttribute('data-bs-target') || button.getAttribute('data-target');
        if (targetModalId) {
            button.addEventListener('click', function(e) {
                console.log(`模态框按钮点击，目标: ${targetModalId}`);
            });
        }
    });
});
