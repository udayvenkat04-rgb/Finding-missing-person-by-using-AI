// Load stats on homepage
async function loadStats() {
    try {
        const reports = await getAllReports();
        const total = reports.length;
        const resolved = reports.filter(r => r.status === 'resolved').length;
        const active = reports.filter(r => r.status === 'approved').length;
        
        document.getElementById('total-cases').textContent = total;
        document.getElementById('resolved-cases').textContent = resolved;
        document.getElementById('active-cases').textContent = active;
        document.getElementById('reunited').textContent = resolved;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load recent cases
async function loadRecentCases() {
    try {
        const reports = await getAllReports();
        const approvedReports = reports.filter(r => r.status === 'approved').slice(0, 6);
        
        const grid = document.getElementById('cases-grid');
        grid.innerHTML = '';
        
        approvedReports.forEach(report => {
            const card = createCaseCard(report);
            grid.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading cases:', error);
    }
}

// Create case card element
function createCaseCard(report) {
    const card = document.createElement('div');
    card.className = 'case-card';
    
    const imageUrl = report.images && report.images.length > 0 
        ? report.images[0] 
        : 'https://via.placeholder.com/300x200';
    
    const lastSeenDate = new Date(report.last_seen_date).toLocaleDateString();
    
    card.innerHTML = `
        <img src="${imageUrl}" alt="${report.name}" class="case-image">
        <div class="case-info">
            <h3>${report.name}, ${report.age}</h3>
            <p><i class="fas fa-map-marker-alt"></i> Last seen: ${report.last_seen_location}</p>
            <p><i class="fas fa-calendar"></i> Date: ${lastSeenDate}</p>
            <p><i class="fas fa-info-circle"></i> ${report.description.substring(0, 100)}...</p>
            ${report.match_found ? 
                '<p class="match-highlight"><i class="fas fa-check-circle"></i> Potential match found!</p>' : 
                ''}
        </div>
    `;
    
    return card;
}

// Search missing persons
async function searchMissing() {
    const searchTerm = document.getElementById('search-input').value;
    
    try {
        const results = await searchMissingPersons({ name: searchTerm, location: searchTerm });
        displaySearchResults(results);
    } catch (error) {
        console.error('Error searching:', error);
    }
}

// Display search results
function displaySearchResults(results) {
    const grid = document.getElementById('cases-grid');
    grid.innerHTML = '';
    
    if (results.length === 0) {
        grid.innerHTML = '<p style="text-align: center; grid-column: 1/-1;">No results found</p>';
        return;
    }
    
    results.forEach(report => {
        const card = createCaseCard(report);
        grid.appendChild(card);
    });
}

// Initialize homepage
if (window.location.pathname === '/' || window.location.pathname.includes('index.html')) {
    document.addEventListener('DOMContentLoaded', () => {
        loadStats();
        loadRecentCases();
    });
}