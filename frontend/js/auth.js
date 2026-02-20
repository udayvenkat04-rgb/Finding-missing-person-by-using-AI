// Update UI based on auth state
function updateAuthUI() {
    const loginBtn = document.querySelector('.btn-login');
    const registerBtn = document.querySelector('.btn-register');
    const logoutBtn = document.querySelector('.btn-logout');
    const dashboardLink = document.getElementById('dashboard-link');
    const adminLink = document.getElementById('admin-link');
    
    if (isLoggedIn()) {
        if (loginBtn) loginBtn.style.display = 'none';
        if (registerBtn) registerBtn.style.display = 'none';
        if (logoutBtn) logoutBtn.style.display = 'block';
        if (dashboardLink) dashboardLink.style.display = 'inline';
        
        if (isAdmin()) {
            if (adminLink) adminLink.style.display = 'inline';
        } else {
            if (adminLink) adminLink.style.display = 'none';
        }
    } else {
        if (loginBtn) loginBtn.style.display = 'block';
        if (registerBtn) registerBtn.style.display = 'block';
        if (logoutBtn) logoutBtn.style.display = 'none';
        if (dashboardLink) dashboardLink.style.display = 'none';
        if (adminLink) adminLink.style.display = 'none';
    }
}

// Check authentication on page load
document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();
    
    // Protect routes
    const currentPath = window.location.pathname;
    
    if (currentPath.includes('dashboard.html') && !isLoggedIn()) {
        window.location.href = '/login.html';
    }
    
    if (currentPath.includes('admin.html') && !isAdmin()) {
        window.location.href = '/';
    }
    
    if (currentPath.includes('report.html') && !isLoggedIn()) {
        window.location.href = '/login.html';
    }
});