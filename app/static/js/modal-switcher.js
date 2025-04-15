/**
 * 模态框切换工具 - 专门处理模态框之间的平滑切换
 */
(function() {
    // 存储可能的活动模态框
    var activeModal = null;
    var nextModalId = null;
    var isTransitioning = false;

    // 初始化
    document.addEventListener('DOMContentLoaded', function() {
        // 为详情模态框中的编辑按钮添加事件处理
        document.querySelectorAll('.modal .btn-warning[data-station-id]').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                // 防止事件冒泡和默认行为
                e.preventDefault();
                e.stopPropagation();
                
                // 获取当前模态框和目标模态框
                const stationId = this.getAttribute('data-station-id');
                const currentModalId = `detailModal-${stationId}`;
                const targetModalId = `editModal-${stationId}`;
                
                // 通过自定义方法切换模态框
                safeModalTransition(currentModalId, targetModalId);
            });
        });
        
        // 监听所有模态框的隐藏事件
        document.querySelectorAll('.modal').forEach(function(modal) {
            modal.addEventListener('hidden.bs.modal', function() {
                console.log('模态框隐藏事件触发:', modal.id);
                
                // 仅在正在进行过渡时执行下一步
                if (isTransitioning && nextModalId) {
                    const targetModal = document.getElementById(nextModalId);
                    if (targetModal) {
                        console.log('打开下一个模态框:', nextModalId);
                        setTimeout(function() {
                            showModalSafely(targetModal);
                            isTransitioning = false;
                            nextModalId = null;
                        }, 200);  // 延迟200ms以确保前一个模态框完全关闭
                    }
                }
                
                // 清理残留背景遮罩
                document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
                    backdrop.remove();
                });
                
                // 如果没有其他模态框打开，重置body
                if (!document.querySelector('.modal.show')) {
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                }
            });
        });
    });
    
    /**
     * 安全地在两个模态框之间切换，确保平稳过渡
     */
    window.safeModalTransition = function(fromModalId, toModalId) {
        isTransitioning = true;
        nextModalId = toModalId;
        
        // 关闭当前模态框
        const currentModal = document.getElementById(fromModalId);
        if (!currentModal) {
            console.error('找不到当前模态框:', fromModalId);
            isTransitioning = false;
            return;
        }
        
        try {
            // 使用Bootstrap API关闭模态框
            const bsModal = bootstrap.Modal.getInstance(currentModal);
            if (bsModal) {
                console.log('关闭当前模态框:', fromModalId);
                bsModal.hide();
                // 下一步将由hidden.bs.modal事件触发
            } else {
                // 回退到手动关闭
                currentModal.classList.remove('show');
                currentModal.style.display = 'none';
                
                // 手动触发下一步
                setTimeout(function() {
                    const nextModal = document.getElementById(toModalId);
                    if (nextModal) {
                        showModalSafely(nextModal);
                    }
                    isTransitioning = false;
                }, 200);
            }
        } catch (e) {
            console.error('关闭模态框时发生错误:', e);
            // 强制手动关闭
            currentModal.classList.remove('show');
            currentModal.style.display = 'none';
            document.body.classList.remove('modal-open');
            
            // 清理所有背景遮罩
            document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
                backdrop.remove();
            });
            
            // 延迟后开启目标模态框
            setTimeout(function() {
                const nextModal = document.getElementById(toModalId);
                if (nextModal) {
                    showModalSafely(nextModal);
                }
                isTransitioning = false;
            }, 300);
        }
    };
    
    /**
     * 安全地显示模态框，确保正确设置所有必要的类和属性
     */
    function showModalSafely(modal) {
        // 1. 确保body有正确的类
        document.body.classList.add('modal-open');
        
        // 2. 显示模态框
        modal.style.display = 'block';
        modal.classList.add('show');
        modal.setAttribute('aria-modal', 'true');
        modal.removeAttribute('aria-hidden');
        
        // 3. 添加背景遮罩
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        document.body.appendChild(backdrop);
        
        // 4. 存储当前活动模态框
        activeModal = modal;
        
        // 5. 尝试使用Bootstrap API（可选的后备方法）
        try {
            // 只有在前面的方法失败时才尝试使用Bootstrap API
            if (!modal.classList.contains('show')) {
                const bsModal = new bootstrap.Modal(modal);
                bsModal.show();
            }
        } catch (e) {
            console.warn('Bootstrap API调用失败，但模态框已手动显示');
        }
    }
})();
