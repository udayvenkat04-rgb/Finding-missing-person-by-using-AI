// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Token management
function setToken(token) {
    localStorage.setItem('token', token);
}

function getToken() {
    return localStorage.getItem('token');
}

function removeToken() {
    localStorage.removeItem('token');
}

// User management
function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

function getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

function removeUser() {
    localStorage.removeItem('user');
}

// Check if user is logged in
function isLoggedIn() {
    return !!getToken();
}

// Check if user is admin
function isAdmin() {
    const user = getUser();
    return user && user.is_admin === true;
}

// Logout function
function logout() {
    removeToken();
    removeUser();
    window.location.href = '/';
}

// API call function with error handling
async function apiCall(endpoint, method = 'GET', data = null, isFormData = false) {
    const url = `${API_BASE_URL}${endpoint}`;
    console.log(`🌐 API Call: ${method} ${url}`);
    
    const headers = {};
    
    if (getToken()) {
        headers['Authorization'] = `Bearer ${getToken()}`;
    }
    
    if (!isFormData) {
        headers['Content-Type'] = 'application/json';
    }
    
    const config = {
        method,
        headers,
        mode: 'cors'
    };
    
    if (data) {
        config.body = isFormData ? data : JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, config);
        const responseData = await response.json();
        
        if (!response.ok) {
            throw new Error(responseData.error || `HTTP error! status: ${response.status}`);
        }
        
        return responseData;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Test connection
async function testConnection() {
    try {
        const data = await apiCall('/test');
        console.log('✅ Backend connected:', data);
        return true;
    } catch (error) {
        console.error('❌ Backend connection failed:', error);
        return false;
    }
}

// Auth APIs
async function register(userData) {
    return apiCall('/register', 'POST', userData);
}

async function login(credentials) {
    const data = await apiCall('/login', 'POST', credentials);
    if (data.token) {
        setToken(data.token);
        setUser(data.user);
    }
    return data;
}

async function adminLogin(credentials) {
    const data = await apiCall('/admin/login', 'POST', credentials);
    if (data.token) {
        setToken(data.token);
        setUser(data.user);
    }
    return data;
}

// Missing Person APIs
async function reportMissingPerson(formData) {
    return apiCall('/missing-person/report', 'POST', formData, true);
}

async function getMyReports() {
    return apiCall('/missing-person/my-reports');
}

async function getAllReports() {
    return apiCall('/missing-person/all');
}

async function getReportById(reportId) {
    return apiCall(`/missing-person/${reportId}`);
}

async function searchMissingPersons(params) {
    const queryString = new URLSearchParams(params).toString();
    return apiCall(`/search?${queryString}`);
}

// Admin APIs
async function updateMissingPersonStatus(personId, status) {
    return apiCall(`/admin/missing-person/${personId}/status`, 'PUT', { status });
}

async function uploadUnidentifiedPerson(formData) {
    return apiCall('/admin/unidentified/upload', 'POST', formData, true);
}

async function getAllUnidentified() {
    return apiCall('/admin/unidentified/all');
}

// Initialize connection test
testConnection();