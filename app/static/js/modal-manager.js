/**
 * 增强型模态框管理器
 * 用于解决模态框不稳定、突然消失的问题
 */
(function() {
    // 存储当前激活的模态框
    let activeModal = null;
    let preventClose = false;
    
    document.addEventListener('DOMContentLoaded', function() {
        // 处理所有编辑模态框
        setupEditModals();
        
        // 增强所有模态框
        enhanceAllModals();
        
        // 处理ESC键和点击背景事件
        setupGlobalModalEvents();
    });
    
    /**
     * 设置编辑模态框的增强功能
     */
    function setupEditModals() {
        // 获取所有编辑按钮
        const editButtons = document.querySelectorAll('button[data-bs-target^="#editModal-"]');
        
        editButtons.forEach(button => {
            // 保存原始点击事件并替换
            const originalClick = button.onclick;
            button.onclick = null;
            
            // 添加新的点击事件处理
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // 获取目标模态框ID
                const modalId = this.getAttribute('data-bs-target').substring(1);
                const modal = document.getElementById(modalId);
                
                if (!modal) {
                    console.error('找不到编辑模态框:', modalId);
                    return;
                }
                
                // 移除任何现有的活跃模态框
                closeActiveModals();
                
                // 打开新的模态框，并设置为当前活跃模态框
                setTimeout(() => {
                    openModalSafely(modal);
                    activeModal = modal;
                    
                    // 阻止此模态框自动关闭
                    preventClose = true;
                    setTimeout(() => { preventClose = false; }, 300);
                    
                    console.log('编辑模态框已打开:', modalId);
                }, 50);
            });
        });
    }
    
    /**
     * 增强所有模态框
     */
    function enhanceAllModals() {
        const modals = document.querySelectorAll('.modal');
        
        modals.forEach(modal => {
            // 阻止点击内容区域导致关闭
            const modalContent = modal.querySelector('.modal-content');
            if (modalContent) {
                modalContent.addEventListener('click', function(e) {
                    e.stopPropagation();
                });
            }
            
            // 增强关闭按钮行为
            const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
            closeButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // 如果是活跃的编辑模态框且处于保护期，阻止关闭
                    if (modal === activeModal && preventClose) {
                        console.log('模态框处于保护期，阻止关闭');
                        return;
                    }
                    
                    closeModalSafely(modal);
                });
            });
            
            // 修复表单提交问题
            const form = modal.querySelector('form');
            if (form) {
                form.addEventListener('submit', function(e) {
                    // 表单提交前验证CSRF令牌是否存在
                    const csrfToken = form.querySelector('input[name="csrf_token"]');
                    if (!csrfToken || !csrfToken.value) {
                        e.preventDefault();
                        console.error('CSRF令牌缺失，无法提交表单');
                        alert('表单验证失败：CSRF令牌缺失');
                        return;
                    }
                    
                    // 禁用所有按钮防止重复提交
                    const buttons = form.querySelectorAll('button');
                    buttons.forEach(btn => btn.disabled = true);
                    
                    // 在表单提交后不要立即关闭模态框，等待服务器响应
                    modal.setAttribute('data-submitting', 'true');
                });
            }
            
            // 监听显示和隐藏事件
            modal.addEventListener('show.bs.modal', function() {
                activeModal = modal;
            });
            
            modal.addEventListener('hidden.bs.modal', function() {
                if (activeModal === modal) {
                    activeModal = null;
                }
            });
        });
    }
    
    /**
     * 设置全局模态框事件
     */
    function setupGlobalModalEvents() {
        // ESC键处理
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && activeModal) {
                // 如果模态框处于保护期，阻止关闭
                if (preventClose) {
                    e.preventDefault();
                    e.stopPropagation();
                    return;
                }
                
                // 表单正在提交中，阻止关闭
                if (activeModal.getAttribute('data-submitting') === 'true') {
                    e.preventDefault();
                    e.stopPropagation();
                    return;
                }
                
                closeModalSafely(activeModal);
            }
        });
        
        // 点击背景关闭
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('modal') && e.target === activeModal) {
                // 如果模态框处于保护期或正在提交，阻止关闭
                if (preventClose || e.target.getAttribute('data-submitting') === 'true') {
                    e.preventDefault();
                    e.stopPropagation();
                    return;
                }
                
                closeModalSafely(e.target);
            }
        });
    }
    
    /**
     * 安全地打开模态框
     */
    function openModalSafely(modal) {
        try {
            // 尝试使用Bootstrap API
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
        } catch (error) {
            console.warn('无法使用Bootstrap API打开模态框，降级使用DOM方法');
            
            // DOM降级方法
            modal.style.display = 'block';
            modal.classList.add('show');
            document.body.classList.add('modal-open');
            document.body.style.paddingRight = '17px'; // 滚动条宽度
            document.body.style.overflow = 'hidden';
            
            // 添加背景
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            document.body.appendChild(backdrop);
        }
    }
    
    /**
     * 安全地关闭模态框
     */
    function closeModalSafely(modal) {
        if (!modal) return;
        
        try {
            // 尝试使用Bootstrap API
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            } else {
                // DOM降级方法
                closeModalByDOM(modal);
            }
        } catch (error) {
            console.warn('无法使用Bootstrap API关闭模态框，降级使用DOM方法');
            closeModalByDOM(modal);
        }
    }
    
    /**
     * 通过DOM操作关闭模态框
     */
    function closeModalByDOM(modal) {
        modal.classList.remove('show');
        modal.style.display = 'none';
        
        // 移除背景
        document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
            backdrop.remove();
        });
        
        // 恢复body样式
        if (!document.querySelector('.modal.show')) {
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';
        }
    }
    
    /**
     * 关闭所有活跃的模态框
     */
    function closeActiveModals() {
        document.querySelectorAll('.modal.show').forEach(modal => {
            closeModalSafely(modal);
        });
        
        // 移除背景
        document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
            backdrop.remove();
        });
        
        // 重置活跃模态框
        activeModal = null;
    }
    
    // 暴露公共方法
    window.ModalManager = {
        open: openModalSafely,
        close: closeModalSafely,
        closeAll: closeActiveModals
    };
})();
