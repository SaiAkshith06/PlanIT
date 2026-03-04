// Removed Google Maps specific global variables
let map;
let routeLine; // To hold the polyline

// Initialize Leaflet Map
document.addEventListener("DOMContentLoaded", () => {
    initMap();
    setupAutocomplete('source');
    setupAutocomplete('destination');
});

// Autocomplete Logic using Nominatim
function setupAutocomplete(inputId) {
    const input = document.getElementById(inputId);
    const wrapper = document.getElementById(`${inputId}-wrapper`);
    let timeout = null;

    input.addEventListener("input", function () {
        clearTimeout(timeout);
        closeAllLists();
        const query = this.value;
        if (!query || query.length < 3) return false;

        // Fetch after 300ms debounce
        timeout = setTimeout(async () => {
            try {
                // Nominatim API call for OpenStreetMap search
                const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&addressdetails=1&limit=5`, {
                    headers: { 'Accept-Language': 'en' }
                });
                const data = await res.json();

                if (data && data.length > 0) {
                    const dropdown = document.createElement("div");
                    dropdown.setAttribute("class", "autocomplete-items");

                    data.forEach(item => {
                        const option = document.createElement("div");
                        option.innerHTML = `<strong>${item.display_name.substring(0, query.length)}</strong>${item.display_name.substring(query.length)}`;
                        option.addEventListener("click", function () {
                            input.value = item.display_name;
                            closeAllLists();
                        });
                        dropdown.appendChild(option);
                    });

                    wrapper.appendChild(dropdown);
                }
            } catch (err) {
                console.error("Geocoding fetch error:", err);
            }
        }, 300);
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", function (e) {
        if (e.target !== input) closeAllLists();
    });

    function closeAllLists() {
        const items = document.getElementsByClassName("autocomplete-items");
        for (let i = 0; i < items.length; i++) {
            items[i].parentNode.removeChild(items[i]);
        }
    }
}

function initMap() {
    // Basic map initialization centered roughly on US
    map = L.map('map', {
        zoomControl: false // Custom position later if needed
    }).setView([39.8283, -98.5795], 4);

    // Add Zoom Control at bottom right
    L.control.zoom({
        position: 'bottomright'
    }).addTo(map);

    // Add Dark Theme Tiles (CartoDB Dark Matter)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);
}

// Handle Form Submission
document.getElementById('plan-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const source = document.getElementById('source').value;
    const destination = document.getElementById('destination').value;
    const priority = document.getElementById('priority').value;

    const btnBtn = document.getElementById('submit-btn');
    const originalText = btnBtn.innerHTML;
    btnBtn.innerHTML = '<span class="loader" style="display:block; margin: 0 auto;"></span>';
    btnBtn.disabled = true;

    try {
        const response = await fetch('/api/plan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ source, destination, priority })
        });

        const data = await response.json();

        if (response.ok) {
            displayResults(data.best_route, data.all_routes);
            drawRouteOnMap(data.best_route.geometry);
        } else {
            alert("Error: " + data.error);
        }
    } catch (err) {
        console.error("API Error:", err);
        alert("Failed to connect to the planning server.");
    } finally {
        btnBtn.innerHTML = originalText;
        btnBtn.disabled = false;
    }
});

// Render the Results UI
function displayResults(bestRoute, allRoutes) {
    const resultsContainer = document.getElementById('results-container');
    const bestRouteContainer = document.getElementById('best-route-card');
    const altRoutesContainer = document.getElementById('alt-routes-container');

    // Show container
    resultsContainer.classList.remove('hidden');

    // Render Best Route
    bestRouteContainer.innerHTML = createRouteCardHTML(bestRoute, true);

    // Render Alternative Routes
    altRoutesContainer.innerHTML = '';
    const alternatives = allRoutes.filter(r => r.mode !== bestRoute.mode);

    if (alternatives.length > 0) {
        alternatives.forEach(route => {
            const el = document.createElement('div');
            el.className = 'result-card';
            el.innerHTML = createRouteCardHTML(route, false);
            altRoutesContainer.appendChild(el);
        });
    } else {
        altRoutesContainer.innerHTML = '<p style="color: var(--text-secondary); font-size: 0.85rem;">No viable alternatives found.</p>';
    }
}

// Helper to generate HTML for a route card
function createRouteCardHTML(route, isBest) {
    const distanceKm = (route.distance_meters / 1000).toFixed(1);

    // Convert seconds to human readable time
    const mins = Math.round(route.time_seconds / 60);
    const hrs = Math.floor(mins / 60);
    const remainingMins = mins % 60;
    const timeStr = hrs > 0 ? `${hrs}h ${remainingMins}m` : `${mins}m`;

    return `
        <div class="card-header">
            <span class="mode-badge ${isBest ? 'highlight' : ''}">${route.mode}</span>
            ${!route.feasible ? '<span style="color: #ef4444; font-size: 0.75rem;">(Infeasible)</span>' : ''}
        </div>
        <p class="route-desc">${route.route}</p>
        <div class="metrics">
            <div class="metric">
                <span class="metric-label">Distance</span>
                <span class="metric-value">${distanceKm} km</span>
            </div>
            <div class="metric">
                <span class="metric-label">Est. Time</span>
                <span class="metric-value">${timeStr}</span>
            </div>
            <div class="metric mt-4">
                <span class="metric-label">Est. Cost</span>
                <span class="metric-value">${route.cost === 0 ? 'Free' : '₹' + route.cost.toLocaleString('en-IN')}</span>
            </div>
        </div>
    `;
}

// Visually trace the route using OSRM geometry
function drawRouteOnMap(routeGeometry) {
    if (!map) return;

    // Remove previous route if exists
    if (routeLine) {
        map.removeLayer(routeLine);
    }

    // Draw new route
    if (routeGeometry) {
        // OSRM returns geometry in GeoJSON format or encoded polyline
        // We'll assume the backend sends a decoded array of [lat, lng] or GeoJSON
        try {
            // Leaflet polyline expects [lat, lng]
            let coordinates = [];

            if (routeGeometry.type === "LineString") {
                // GeoJSON uses [lng, lat], Leaflet wants [lat, lng]
                coordinates = routeGeometry.coordinates.map(coord => [coord[1], coord[0]]);
            } else {
                // Fallback assuming array of [lat, lng]
                coordinates = routeGeometry;
            }

            routeLine = L.polyline(coordinates, {
                color: '#3b82f6',
                weight: 5,
                opacity: 0.8
            }).addTo(map);

            // Adjust map view to fit the route
            map.fitBounds(routeLine.getBounds(), { padding: [50, 50] });

        } catch (e) {
            console.error("Error drawing route line:", e);
        }
    }
}

// Removed Google Maps specific styling
