/**
 * Venom_Tracker - Main JavaScript
 * Client-side functionality for the application
 */

// Global configuration
const VENOM_TRACKER = {
    API_BASE: '/api/v1',
    NOTIFICATION_TIMEOUT: 3000,
    MAP_DEFAULT_ZOOM: 12,
    SEARCH_RADIUS: 50
};

/**
 * Display notification to user
 * @param {string} message - Notification message
 * @param {string} type - Type of notification (success, error, warning, info)
 */
function showNotification(message, type = 'info') {
    const alertClass = `alert-${type === 'error' ? 'danger' : type}`;
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertAdjacentElement('afterbegin', alertDiv);
        
        // Auto-dismiss after timeout
        setTimeout(() => {
            alertDiv.remove();
        }, VENOM_TRACKER.NOTIFICATION_TIMEOUT);
    }
}

/**
 * Get user's current location
 * @returns {Promise} - Promise with location data
 */
function getUserLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject('Geolocation is not supported');
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            position => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy
                });
            },
            error => {
                reject(`Error getting location: ${error.message}`);
            }
        );
    });
}

/**
 * Calculate distance between two coordinates using Haversine formula
 * @param {number} lat1 - Latitude 1
 * @param {number} lon1 - Longitude 1
 * @param {number} lat2 - Latitude 2
 * @param {number} lon2 - Longitude 2
 * @returns {number} - Distance in kilometers
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return Math.round(R * c * 100) / 100;
}

/**
 * Format date to readable format
 * @param {string|Date} date - Date to format
 * @returns {string} - Formatted date
 */
function formatDate(date) {
    if (typeof date === 'string') {
        date = new Date(date);
    }
    return date.toLocaleString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Get status badge class
 * @param {string} status - Status value
 * @returns {string} - Bootstrap color class
 */
function getStatusBadgeClass(status) {
    const statusMap = {
        'pending': 'warning',
        'accepted': 'info',
        'rejected': 'danger',
        'completed': 'success',
        'available': 'success',
        'low_stock': 'warning',
        'out_of_stock': 'danger',
        'good': 'success',
        'low': 'warning',
        'critical': 'danger',
        'mild': 'info',
        'moderate': 'warning',
        'severe': 'danger'
    };
    return statusMap[status] || 'secondary';
}

/**
 * Initialize map with Leaflet
 * @param {string} elementId - ID of map container
 * @param {number} lat - Initial latitude
 * @param {number} lng - Initial longitude
 * @param {number} zoom - Initial zoom level
 * @returns {Object} - Leaflet map object
 */
function initializeMap(elementId, lat = 20.5937, lng = 78.9629, zoom = 5) {
    const map = L.map(elementId).setView([lat, lng], zoom);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    return map;
}

/**
 * Add marker to map
 * @param {Object} map - Leaflet map object
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @param {string} title - Marker title
 * @param {string} color - Marker color (blue, red, green, orange)
 * @returns {Object} - Leaflet marker object
 */
function addMarker(map, lat, lng, title, color = 'blue') {
    const colorMap = {
        'blue': '#007bff',
        'red': '#dc3545',
        'green': '#28a745',
        'orange': '#fd7e14',
        'yellow': '#ffc107'
    };
    
    const marker = L.circleMarker([lat, lng], {
        radius: 8,
        fillColor: colorMap[color] || colorMap['blue'],
        color: '#fff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(map).bindPopup(title);
    
    return marker;
}

/**
 * Make API call
 * @param {string} endpoint - API endpoint
 * @param {string} method - HTTP method
 * @param {Object} data - Request data
 * @returns {Promise} - API response
 */
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`${VENOM_TRACKER.API_BASE}${endpoint}`, options);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || `HTTP ${response.status}`);
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Update location to server
 */
function updateLocationToServer() {
    getUserLocation()
        .then(location => {
            fetch('/user/update-location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(location)
            })
            .then(response => response.json())
            .catch(error => console.error('Error updating location:', error));
        })
        .catch(error => console.error('Error getting location:', error));
}

/**
 * Format phone number
 * @param {string} phone - Phone number
 * @returns {string} - Formatted phone number
 */
function formatPhoneNumber(phone) {
    return phone.replace(/(\d{3})(\d{3})(\d{4})/, '+91 $1 $2 $3');
}

/**
 * Validate email
 * @param {string} email - Email to validate
 * @returns {boolean} - Is valid email
 */
function validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Validate phone
 * @param {string} phone - Phone to validate
 * @returns {boolean} - Is valid phone
 */
function validatePhone(phone) {
    const regex = /^\d{10}$/;
    return regex.test(phone.replace(/\D/g, ''));
}

/**
 * Download file
 * @param {string} filename - Filename
 * @param {string} content - File content
 * @param {string} type - MIME type
 */
function downloadFile(filename, content, type = 'text/plain') {
    const element = document.createElement('a');
    element.setAttribute('href', `data:${type};charset=utf-8,${encodeURIComponent(content)}`);
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

/**
 * Initialize tooltips and popovers
 */
function initializeBootstrapComponents() {
    // Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Dark mode toggle
 */
function toggleDarkMode() {
    const currentTheme = document.body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

/**
 * Load theme preference
 */
function loadThemePreference() {
    const theme = localStorage.getItem('theme') || 'light';
    document.body.setAttribute('data-theme', theme);
}

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Load theme preference
    loadThemePreference();
    
    // Initialize Bootstrap components
    initializeBootstrapComponents();
    
    // Update location every 5 minutes
    updateLocationToServer();
    setInterval(updateLocationToServer, 5 * 60 * 1000);
    
    console.log('Venom_Tracker initialized');
});

// Export functions for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        showNotification,
        getUserLocation,
        calculateDistance,
        formatDate,
        getStatusBadgeClass,
        initializeMap,
        addMarker,
        apiCall,
        updateLocationToServer,
        formatPhoneNumber,
        validateEmail,
        validatePhone,
        downloadFile,
        toggleDarkMode,
        loadThemePreference
    };
}
