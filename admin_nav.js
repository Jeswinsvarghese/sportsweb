document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;

    document.querySelectorAll('.sidebar-nav li').forEach(item => {
        item.classList.remove('active');
    });

    if (path.includes('/admin/dashboard')) {
        document.getElementById('nav-feedback')?.classList.add('active');
    } else if (path.includes('/admin/api-management')) {
        document.getElementById('nav-api-management')?.classList.add('active');
    } else if (path.includes('/admin/api-usage')) {
        document.getElementById('nav-api-usage')?.classList.add('active');
    }
}); 