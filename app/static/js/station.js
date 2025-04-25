/**
 * 微型消防站模块的专用JavaScript
 */
$(document).ready(function() {
    console.log('站点JS已加载，初始化事件处理...');
    
    // 添加全局标志表示初始化完成
    window.stationInitialized = true;
    
    // 查看按钮点击事件
    $(document).on('click', '.btn-view', function(e) {
        e.preventDefault();
        e.stopPropagation(); // 阻止事件冒泡
        const itemId = $(this).data('id');
        console.log('查看按钮被点击，ID:', itemId);
        
        // 直接使用jQuery方法显示模态框
        $('#viewModal').modal('show');
        
        // 获取详细数据
        $.ajax({
            url: `/station/details/${itemId}`,
            type: 'GET',
            success: function(response) {
                // ...填充模态框数据...
                $('#viewItemId').text(response.id);
                $('#viewAreaName').text(response.area_name);
                $('#viewItemName').text(response.item_name);
                $('#viewModel').text(response.model || '未指定');
                $('#viewQuantity').text(response.quantity);
                $('#viewManufacturer').text(response.manufacturer || '未指定');
                $('#viewProductionDate').text(response.production_date || '未指定');
                $('#viewRemark').text(response.remark || '无');
            },
            error: function(xhr) {
                console.error('获取物资详情错误:', xhr.responseText);
                $('#viewItemName').text('加载数据失败，请重试');
            }
        });
    });
    
    // 编辑按钮点击事件
    $(document).on('click', '.btn-edit', function(e) {
        e.preventDefault();
        e.stopPropagation(); // 阻止事件冒泡
        const itemId = $(this).data('id');
        console.log('编辑按钮被点击，ID:', itemId);
        
        // 直接使用jQuery方法显示模态框
        $('#editModal').modal('show');
        
        // 获取物资数据填充表单
        $.ajax({
            url: `/station/details/${itemId}`,
            type: 'GET',
            success: function(response) {
                $('#editId').val(response.id);
                $('#editItemName').val(response.item_name);
                $('#editModel').val(response.model || '');
                $('#editQuantity').val(response.quantity);
                $('#editManufacturer').val(response.manufacturer || '');
                $('#editProductionDate').val(response.production_date || '');
                $('#editRemark').val(response.remark || '');
            },
            error: function(xhr) {
                console.error('获取编辑数据错误:', xhr.responseText);
                alert('获取物资数据失败，请重试');
                $('#editModal').modal('hide');
            }
        });
    });
    
    // 删除按钮点击事件
    $(document).on('click', '.btn-delete', function(e) {
        e.preventDefault();
        e.stopPropagation(); // 阻止事件冒泡
        const itemId = $(this).data('id');
        const itemName = $(this).data('name') || '此物资';
        console.log('删除按钮被点击，ID:', itemId, '名称:', itemName);
        
        // 设置删除表单的ID和显示确认消息
        $('#deleteId').val(itemId);
        $('#deleteItemName').text(itemName);
        
        // 直接使用jQuery方法显示模态框
        $('#deleteModal').modal('show');
    });
    
    // 添加按钮点击事件
    $(document).on('click', '#addItemButton', function(e) {
        e.preventDefault();
        e.stopPropagation(); // 阻止事件冒泡
        console.log('添加按钮被点击');
        
        // 重置添加表单
        if ($('#addItemForm').length) {
            $('#addItemForm')[0].reset();
        }
        
        // 直接使用jQuery方法显示模态框
        $('#addModal').modal('show');
    });
    
    // 确保所有模态框都已被初始化
    $('.modal').each(function() {
        try {
            new bootstrap.Modal(this);
            console.log(`模态框 ${this.id} 初始化成功`);
        } catch(e) {
            console.error(`初始化模态框 ${this.id} 失败:`, e);
        }
    });
    
    console.log('站点JS初始化完成，已监听所有按钮事件');
});
