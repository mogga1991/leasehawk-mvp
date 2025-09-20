// Use relative URL for API calls (works in both dev and production)
const API_URL = window.location.origin;

// Map instance
let map;
let markers = [];
let selectedOpportunity = null;
let opportunities = [];
let propertyMatches = {};

// Initialize map on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    loadOpportunities();
});

function initializeMap() {
    // Initialize Leaflet map centered on USA
    map = L.map('map').setView([39.8283, -98.5795], 4);
    
    // Add tile layer (using OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
}

async function loadOpportunities() {
    try {
        const response = await fetch(`${API_URL}/opportunities/`);
        opportunities = await response.json();
        
        // Update opportunity count
        document.getElementById('opportunityCount').textContent = 
            `${opportunities.length} GSA opportunities in pipeline`;
        
        // Render opportunities list
        renderOpportunities(opportunities);
        
        // Load matches for each opportunity
        for (let opp of opportunities) {
            await loadMatchesForOpportunity(opp.prospectus.id);
        }
    } catch (error) {
        console.error('Error loading opportunities:', error);
    }
}

function renderOpportunities(opps) {
    const listHTML = opps.map(opp => {
        const matchCount = propertyMatches[opp.prospectus.id]?.length || 0;
        const matchClass = matchCount > 5 ? '' : matchCount > 0 ? 'low' : 'none';
        const matchText = matchCount > 0 ? `${matchCount} matches` : 'No matches';
        
        return `
            <div class="opportunity-card" onclick="selectOpportunity(${opp.prospectus.id})" 
                 id="opp-${opp.prospectus.id}">
                <div class="opportunity-header">
                    <div class="agency-info">
                        <h3>${opp.prospectus.agency}</h3>
                        <div class="location">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>${opp.prospectus.location}</span>
                        </div>
                    </div>
                    <span class="match-badge ${matchClass}">${matchText}</span>
                </div>
                
                <div class="opportunity-metrics">
                    <div class="metric-item">
                        <i class="fas fa-building"></i>
                        <div>
                            <div class="metric-label">Space Required</div>
                            <div class="metric-value">
                                ${(opp.prospectus.estimated_nusf || 0).toLocaleString()} sqft
                            </div>
                        </div>
                    </div>
                    <div class="metric-item">
                        <i class="fas fa-calendar"></i>
                        <div>
                            <div class="metric-label">Lease Term</div>
                            <div class="metric-value">
                                ${opp.prospectus.lease_term || '10'} years
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="opportunity-footer">
                    <div class="annual-value">
                        $${((opp.prospectus.estimated_annual_cost || 0) / 1000).toFixed(0)}K/year
                    </div>
                    <button class="action-btn" onclick="event.stopPropagation(); findMatches(${opp.prospectus.id})">
                        View Matches
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    document.getElementById('opportunitiesList').innerHTML = listHTML;
}

async function loadMatchesForOpportunity(prospectusId) {
    try {
        const response = await fetch(`${API_URL}/match-properties/${prospectusId}`, {
            method: 'POST'
        });
        const result = await response.json();
        propertyMatches[prospectusId] = result.top_matches || [];
    } catch (error) {
        console.error(`Error loading matches for prospectus ${prospectusId}:`, error);
        propertyMatches[prospectusId] = [];
    }
}

function selectOpportunity(prospectusId) {
    // Update selected state in UI
    document.querySelectorAll('.opportunity-card').forEach(card => {
        card.classList.remove('selected');
    });
    document.getElementById(`opp-${prospectusId}`).classList.add('selected');
    
    selectedOpportunity = prospectusId;
    
    // Show matches on map
    showMatchesOnMap(prospectusId);
}

function showMatchesOnMap(prospectusId) {
    // Clear existing markers
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
    
    const matches = propertyMatches[prospectusId] || [];
    
    if (matches.length === 0) {
        return;
    }
    
    const bounds = [];
    
    matches.forEach((match, index) => {
        if (match.property.latitude && match.property.longitude) {
            const lat = match.property.latitude;
            const lng = match.property.longitude;
            
            // Create custom div icon with score
            const icon = L.divIcon({
                className: 'property-marker',
                html: `$${Math.round(match.property.asking_rent_per_sqft || 25)}/sf`,
                iconSize: [60, 30],
                iconAnchor: [30, 15]
            });
            
            const marker = L.marker([lat, lng], { icon })
                .addTo(map)
                .bindPopup(createPopupContent(match));
            
            marker.on('click', () => showPropertyDetails(match));
            
            markers.push(marker);
            bounds.push([lat, lng]);
        }
    });
    
    // Fit map to show all markers
    if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50] });
    }
}

function createPopupContent(match) {
    const score = Math.round(match.scores?.total_score || 0);
    const scoreClass = score > 80 ? 'high-score' : score > 60 ? 'medium-score' : 'low-score';
    
    return `
        <div style="min-width: 200px;">
            <h4 style="margin: 0 0 8px 0;">${match.property.address}</h4>
            <div style="margin-bottom: 8px;">
                <span class="match-score ${scoreClass}" style="padding: 2px 6px; border-radius: 3px;">
                    Score: ${score}%
                </span>
            </div>
            <div style="font-size: 13px; color: #64748b;">
                <div>Available: ${(match.property.available_sqft || 0).toLocaleString()} sqft</div>
                <div>Asking: $${match.property.asking_rent_per_sqft || 0}/sqft</div>
            </div>
        </div>
    `;
}

function showPropertyDetails(match) {
    const popup = document.getElementById('propertyPopup');
    const content = document.getElementById('popupContent');
    
    content.innerHTML = `
        <h3>${match.property.address}</h3>
        <div class="property-details-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-top: 16px;">
            <div>
                <label style="font-size: 12px; color: #64748b;">Match Score</label>
                <div style="font-size: 24px; font-weight: bold; color: ${match.scores.total_score > 80 ? '#10b981' : '#f59e0b'};">
                    ${Math.round(match.scores.total_score)}%
                </div>
            </div>
            <div>
                <label style="font-size: 12px; color: #64748b;">Available Space</label>
                <div style="font-size: 18px; font-weight: 600;">
                    ${(match.property.available_sqft || 0).toLocaleString()} sqft
                </div>
            </div>
            <div>
                <label style="font-size: 12px; color: #64748b;">Asking Rent</label>
                <div style="font-size: 18px; font-weight: 600;">
                    $${match.property.asking_rent_per_sqft || 0}/sqft
                </div>
            </div>
            <div>
                <label style="font-size: 12px; color: #64748b;">Total Annual Cost</label>
                <div style="font-size: 18px; font-weight: 600;">
                    $${((match.property.available_sqft || 0) * (match.property.asking_rent_per_sqft || 0)).toLocaleString()}
                </div>
            </div>
        </div>
        
        <div style="margin-top: 20px;">
            <h4>Score Breakdown</h4>
            <div style="margin-top: 10px;">
                <div style="margin-bottom: 8px;">
                    <span style="color: #64748b;">Location Score:</span>
                    <strong>${Math.round(match.scores.location_score)}%</strong>
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="color: #64748b;">Size Match:</span>
                    <strong>${Math.round(match.scores.size_score)}%</strong>
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="color: #64748b;">Price Competitiveness:</span>
                    <strong>${Math.round(match.scores.price_score)}%</strong>
                </div>
            </div>
        </div>
    `;
    
    popup.style.display = 'block';
}

function closePropertyPopup() {
    document.getElementById('propertyPopup').style.display = 'none';
}

// Search and Filter Functions
function toggleFilters() {
    const panel = document.getElementById('filterPanel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

function applyFilters() {
    const minSize = document.getElementById('minSize').value;
    const maxSize = document.getElementById('maxSize').value;
    const minValue = document.getElementById('minValue').value;
    
    let filtered = opportunities.filter(opp => {
        if (minSize && opp.prospectus.estimated_nusf < parseInt(minSize)) return false;
        if (maxSize && opp.prospectus.estimated_nusf > parseInt(maxSize)) return false;
        if (minValue && opp.prospectus.estimated_annual_cost < parseInt(minValue)) return false;
        return true;
    });
    
    renderOpportunities(filtered);
    toggleFilters();
}

function sortBy(criteria) {
    document.querySelectorAll('.sort-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    let sorted = [...opportunities];
    
    switch(criteria) {
        case 'value':
            sorted.sort((a, b) => (b.prospectus.estimated_annual_cost || 0) - (a.prospectus.estimated_annual_cost || 0));
            break;
        case 'size':
            sorted.sort((a, b) => (b.prospectus.estimated_nusf || 0) - (a.prospectus.estimated_nusf || 0));
            break;
        case 'matches':
            sorted.sort((a, b) => (propertyMatches[b.prospectus.id]?.length || 0) - (propertyMatches[a.prospectus.id]?.length || 0));
            break;
        default: // date
            sorted.sort((a, b) => new Date(b.prospectus.created_at) - new Date(a.prospectus.created_at));
    }
    
    renderOpportunities(sorted);
}

// Upload Functions
function toggleUploadModal() {
    const modal = document.getElementById('uploadModal');
    modal.style.display = modal.style.display === 'none' ? 'flex' : 'none';
}

function handleFileSelect(event) {
    const fileName = event.target.files[0]?.name;
    if (fileName) {
        document.querySelector('.upload-area p').textContent = `Selected: ${fileName}`;
    }
}

async function uploadProspectus() {
    const fileInput = document.getElementById('prospectusFile');
    const file = fileInput.files[0];
    
    if (!file) {
        alert('Please select a file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${API_URL}/parse-prospectus/`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        document.getElementById('uploadResult').innerHTML = `
            <div style="color: #10b981; margin-top: 16px;">
                ✅ Prospectus parsed successfully!
            </div>
        `;
        
        // Reload opportunities after upload
        setTimeout(() => {
            toggleUploadModal();
            loadOpportunities();
        }, 1500);
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('uploadResult').innerHTML = `
            <div style="color: #ef4444; margin-top: 16px;">
                ❌ Error parsing prospectus
            </div>
        `;
    }
}

async function findMatches(prospectusId) {
    await loadMatchesForOpportunity(prospectusId);
    selectOpportunity(prospectusId);
}

// Map control functions
function toggleMapView() {
    // Toggle between street and satellite view
    // Implementation depends on your tile provider
}

function zoomToFit() {
    if (markers.length > 0) {
        const group = new L.featureGroup(markers);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

// Search functionality
document.getElementById('searchInput')?.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    
    const filtered = opportunities.filter(opp => {
        return opp.prospectus.agency.toLowerCase().includes(searchTerm) ||
               opp.prospectus.location.toLowerCase().includes(searchTerm);
    });
    
    renderOpportunities(filtered);
});


