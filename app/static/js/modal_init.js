// 更新模态框初始化逻辑，确保支持所有页面的模态框

document.addEventListener('DOMContentLoaded', function() {
    // 修复模态框不显示的问题 - 扩展选择器以包含所有编辑按钮
    const editButtons = document.querySelectorAll('button[data-bs-toggle="modal"][data-bs-target^="#editModal-"]');
    
    // 为所有编辑按钮添加点击事件处理
    editButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            // 阻止默认行为，手动控制模态框
            event.preventDefault();
            
            // 获取目标模态框ID
            const targetModalId = this.getAttribute('data-bs-target');
            const modalElement = document.querySelector(targetModalId);
            
            if (!modalElement) {
                console.error('找不到模态框元素:', targetModalId);
                return;
            }
            
            // 清理可能存在的任何模态框状态
            cleanupModalState();
            
            // 使用Bootstrap API显示模态框
            try {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                console.log('已显示编辑模态框:', targetModalId);
            } catch (error) {
                console.error('无法显示模态框:', error);
                
                // 降级方案：直接操作DOM
                modalElement.classList.add('show');
                modalElement.style.display = 'block';
                document.body.classList.add('modal-open');
                
                // 添加背景遮罩
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                document.body.appendChild(backdrop);
            }
        });
    });
    
    // 同样为详情按钮添加事件处理
    const detailButtons = document.querySelectorAll('button[data-bs-toggle="modal"][data-bs-target^="#detailModal-"]');
    detailButtons.forEach(function(button) {
        button.addEventListener('click', handleModalButton);
    });
    
    // 为删除按钮添加事件处理
    const deleteButtons = document.querySelectorAll('button[data-bs-toggle="modal"][data-bs-target="#deleteModal"]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', handleModalButton);
    });
    
    // 通用模态框按钮处理函数
    function handleModalButton(event) {
        event.preventDefault();
        const targetModalId = this.getAttribute('data-bs-target');
        const modalElement = document.querySelector(targetModalId);
        
        if (!modalElement) {
            console.error('找不到模态框元素:', targetModalId);
            return;
        }
        
        cleanupModalState();
        
        try {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        } catch (error) {
            console.error('无法显示模态框:', error);
            modalElement.classList.add('show');
            modalElement.style.display = 'block';
            document.body.classList.add('modal-open');
            
            const backdrop = document.createElement('div');
            backdrop.className = 'modal-backdrop fade show';
            document.body.appendChild(backdrop);
        }
    }
    
    // 清理模态框状态
    function cleanupModalState() {
        // 移除所有可能的模态框背景
        document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
            backdrop.remove();
        });
        
        // 重置body样式
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        // 隐藏所有显示的模态框
        document.querySelectorAll('.modal.show').forEach(modal => {
            modal.classList.remove('show');
            modal.style.display = 'none';
        });
    }
    
    // 监听所有关闭按钮
    document.querySelectorAll('[data-bs-dismiss="modal"]').forEach(button => {
        button.addEventListener('click', function() {
            const modalElement = this.closest('.modal');
            if (modalElement) {
                try {
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    if (modal) {
                        modal.hide();
                    } else {
                        modalElement.classList.remove('show');
                        modalElement.style.display = 'none';
                        cleanupModalState();
                    }
                } catch (error) {
                    modalElement.classList.remove('show');
                    modalElement.style.display = 'none';
                    cleanupModalState();
                }
            }
        });
    });
    
    // 确保模态框事件处理正确
    document.querySelectorAll('.modal').forEach(modal => {
        // 当模态框完全隐藏时
        modal.addEventListener('hidden.bs.modal', function() {
            cleanupModalState();
        });
        
        // 当点击模态框背景时
        modal.addEventListener('click', function(event) {
            // 只有点击到模态框外部时才关闭
            if (event.target === this) {
                try {
                    const modalInstance = bootstrap.Modal.getInstance(this);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                } catch (error) {
                    this.classList.remove('show');
                    this.style.display = 'none';
                    cleanupModalState();
                }
            }
        });
    });
});
