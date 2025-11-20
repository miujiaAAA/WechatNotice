// 全局JavaScript函数

// CSRF保护
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

// AJAX全局设置
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
        }
    }
});

// 通用错误处理
$(document).ajaxError(function(event, xhr, settings) {
    if (xhr.status === 401) {
        // 未授权，跳转到登录页
        window.location.href = '/auth/login';
    } else if (xhr.status === 403) {
        // 禁止访问
        alert('访问被拒绝');
    } else if (xhr.status >= 500) {
        // 服务器错误
        alert('服务器错误，请稍后重试');
    }
});

// 格式化时间
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 格式化耗时
function formatResponseTime(ms) {
    if (ms === null || ms === undefined) return '-';
    return ms.toFixed(2) + ' ms';
}

// 导出为CSV
function exportToCSV(data, filename) {
    const csvContent = "data:text/csv;charset=utf-8,\uFEFF" + data.map(row => 
        Object.values(row).map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')
    ).join('\n');
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
