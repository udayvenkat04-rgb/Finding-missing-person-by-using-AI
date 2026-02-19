// Check if user is logged in
function isLoggedIn() {
    return !!getToken();
}

// Check if user is admin
function isAdmin() {
    const user = getUser();
    return user && user.is_admin === true;
}

// Update UI based on auth state
function updateAuthUI() {
    const loginBtn = document.querySelector('.btn-login');
    const registerBtn = document.querySelector('.btn-register');
    const logoutBtn = document.getElementById('logout-btn');
    const dashboardLink = document.getElementById('dashboard-link');
    const adminLink = document.getElementById('admin-link');
    
    if (isLoggedIn()) {
        loginBtn.style.display = 'none';
        registerBtn.style.display = 'none';
        logoutBtn.style.display = 'block';
        dashboardLink.style.display = 'inline';
        
        if (isAdmin()) {
            adminLink.style.display = 'inline';
        } else {
            adminLink.style.display = 'none';
        }
    } else {
        loginBtn.style.display = 'block';
        registerBtn.style.display = 'block';
        logoutBtn.style.display = 'none';
        dashboardLink.style.display = 'none';
        adminLink.style.display = 'none';
    }
}

// Handle login
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const data = await login({ email, password });
        alert('Login successful!');
        closeLoginModal();
        updateAuthUI();
        
        // Redirect based on user type
        if (data.user.is_admin) {
            window.location.href = '/admin.html';
        } else {
            window.location.href = '/dashboard.html';
        }
    } catch (error) {
        alert(error.message);
    }
}

// Handle admin login
async function handleAdminLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('admin-email').value;
    const password = document.getElementById('admin-password').value;
    
    try {
        const data = await adminLogin({ email, password });
        alert('Admin login successful!');
        updateAuthUI();
        window.location.href = '/admin.html';
    } catch (error) {
        alert(error.message);
    }
}

// Handle register
async function handleRegister(event) {
    event.preventDefault();
    
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    
    if (password !== confirmPassword) {
        alert('Passwords do not match!');
        return;
    }
    
    try {
        await register({ name, email, password });
        alert('Registration successful! Please login.');
        closeRegisterModal();
        showLoginModal();
    } catch (error) {
        alert(error.message);
    }
}

// Logout
function logout() {
    removeToken();
    removeUser();
    updateAuthUI();
    window.location.href = '/';
}

// Modal functions
function showLoginModal() {
    document.getElementById('login-modal').classList.add('active');
}

function closeLoginModal() {
    document.getElementById('login-modal').classList.remove('active');
}

function showRegisterModal() {
    document.getElementById('register-modal').classList.add('active');
}

function closeRegisterModal() {
    document.getElementById('register-modal').classList.remove('active');
}

// Initialize auth state on page load
document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();
    
    // Check if on admin page and user is not admin
    if (window.location.pathname.includes('admin.html') && !isAdmin()) {
        window.location.href = '/';
    }
    
    // Check if on dashboard page and user is not logged in
    if (window.location.pathname.includes('dashboard.html') && !isLoggedIn()) {
        window.location.href = '/';
    }
});