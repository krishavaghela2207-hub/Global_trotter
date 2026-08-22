/* ==========================================================================
   GlobeTrotter - Real-Time Interactive Global Travel Mapping Engine
   ========================================================================== */

(function () {
  'use strict';

  let map = null;
  let currentLayer = null;
  let baseLayers = {};
  let allTripsData = [];
  let currentMarkers = [];
  let currentPolylines = [];
  let userLocationMarker = null;
  let activeStopData = null;

  // DOM Elements
  let mapContainer = null;
  let searchInput = null;
  let statusFilterGroup = null;
  let tripSelectDropdown = null;
  let myTripsCheckbox = null;
  let btnMyLocation = null;
  let btnFitAll = null;
  let drawer = null;
  let drawerContent = null;
  let drawerCloseBtn = null;
  let tripsCountBadge = null;
  let stopsCountBadge = null;
  let activeFilterStatus = '';

  document.addEventListener('DOMContentLoaded', function () {
    mapContainer = document.getElementById('global-travel-map');
    if (!mapContainer) return;

    initDOMElements();
    initLeafletMap();
    setupEventListeners();
    fetchAndRenderTripLocations();
  });

  function initDOMElements() {
    searchInput = document.getElementById('map-search-input');
    statusFilterGroup = document.getElementById('map-status-filters');
    tripSelectDropdown = document.getElementById('map-trip-select');
    myTripsCheckbox = document.getElementById('map-my-trips-toggle');
    btnMyLocation = document.getElementById('btn-my-location');
    btnFitAll = document.getElementById('btn-fit-all');
    drawer = document.getElementById('map-stop-drawer');
    drawerContent = document.getElementById('drawer-body-content');
    drawerCloseBtn = document.getElementById('btn-close-drawer');
    tripsCountBadge = document.getElementById('stat-trips-count');
    stopsCountBadge = document.getElementById('stat-stops-count');
  }

  function initLeafletMap() {
    // 1. Tile Base Layers
    const voyagerLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors, © CARTO'
    });

    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap contributors'
    });

    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: '© Esri, Maxar, Earthstar Geographics'
    });

    baseLayers = {
      voyager: voyagerLayer,
      osm: osmLayer,
      satellite: satelliteLayer
    };

    // Default center: India / Asia hub (latitude: 22.0, longitude: 79.0)
    map = L.map('global-travel-map', {
      center: [23.5, 78.5],
      zoom: 5,
      layers: [voyagerLayer],
      zoomControl: false
    });

    currentLayer = voyagerLayer;

    // Place zoom control at bottom-right
    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Layer switch buttons
    const btnLayerVoyager = document.getElementById('layer-voyager');
    const btnLayerOSM = document.getElementById('layer-osm');
    const btnLayerSatellite = document.getElementById('layer-satellite');

    function setActiveLayerBtn(btn) {
      [btnLayerVoyager, btnLayerOSM, btnLayerSatellite].forEach(b => {
        if (b) b.classList.remove('active');
      });
      if (btn) btn.classList.add('active');
    }

    if (btnLayerVoyager) {
      btnLayerVoyager.addEventListener('click', () => {
        switchBaseLayer(voyagerLayer);
        setActiveLayerBtn(btnLayerVoyager);
      });
    }

    if (btnLayerOSM) {
      btnLayerOSM.addEventListener('click', () => {
        switchBaseLayer(osmLayer);
        setActiveLayerBtn(btnLayerOSM);
      });
    }

    if (btnLayerSatellite) {
      btnLayerSatellite.addEventListener('click', () => {
        switchBaseLayer(satelliteLayer);
        setActiveLayerBtn(btnLayerSatellite);
      });
    }
  }

  function switchBaseLayer(newLayer) {
    if (currentLayer && map.hasLayer(currentLayer)) {
      map.removeLayer(currentLayer);
    }
    map.addLayer(newLayer);
    currentLayer = newLayer;
  }

  function setupEventListeners() {
    // Search input with debounce
    let searchTimeout = null;
    if (searchInput) {
      searchInput.addEventListener('input', function () {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          fetchAndRenderTripLocations();
        }, 300);
      });
    }

    // Status filter buttons (All, Planning, Ongoing, Completed)
    if (statusFilterGroup) {
      const statusButtons = statusFilterGroup.querySelectorAll('[data-status]');
      statusButtons.forEach(btn => {
        btn.addEventListener('click', function () {
          statusButtons.forEach(b => b.classList.remove('active', 'btn-primary'));
          statusButtons.forEach(b => b.classList.add('btn-light', 'text-dark'));
          
          this.classList.remove('btn-light', 'text-dark');
          this.classList.add('active', 'btn-primary');
          
          activeFilterStatus = this.getAttribute('data-status') || '';
          fetchAndRenderTripLocations();
        });
      });
    }

    // Trip selector dropdown
    if (tripSelectDropdown) {
      tripSelectDropdown.addEventListener('change', function () {
        fetchAndRenderTripLocations();
      });
    }

    // My trips toggle
    if (myTripsCheckbox) {
      myTripsCheckbox.addEventListener('change', function () {
        fetchAndRenderTripLocations();
      });
    }

    // Geolocation "My Location" Button
    if (btnMyLocation) {
      btnMyLocation.addEventListener('click', handleUserGeolocation);
    }

    // Fit All Routes
    if (btnFitAll) {
      btnFitAll.addEventListener('click', fitAllRouteBounds);
    }

    // Drawer close
    if (drawerCloseBtn) {
      drawerCloseBtn.addEventListener('click', closeDrawer);
    }

    // Close drawer when clicking map outside
    map.on('click', function (e) {
      if (e.originalEvent && e.originalEvent.target && e.originalEvent.target.closest('#map-stop-drawer')) {
        return;
      }
    });
  }

  /**
   * Fetches real trip GPS data from the backend JSON API: /trips/api/locations/
   */
  async function fetchAndRenderTripLocations() {
    const params = new URLSearchParams();

    if (searchInput && searchInput.value.trim()) {
      params.append('q', searchInput.value.trim());
    }

    if (activeFilterStatus) {
      params.append('status', activeFilterStatus);
    }

    if (tripSelectDropdown && tripSelectDropdown.value) {
      params.append('trip_id', tripSelectDropdown.value);
    }

    if (myTripsCheckbox && myTripsCheckbox.checked) {
      params.append('my_trips', '1');
    }

    try {
      showLoadingIndicator(true);
      const res = await fetch(`/trips/api/locations/?${params.toString()}`);
      if (!res.ok) throw new Error(`API error HTTP ${res.status}`);
      const data = await res.json();
      
      allTripsData = data.trips || [];
      renderTripsOnMap(allTripsData);

      if (tripsCountBadge) tripsCountBadge.textContent = data.count || 0;
      if (stopsCountBadge) stopsCountBadge.textContent = data.total_stops || 0;
    } catch (err) {
      console.error('Failed to fetch trip locations:', err);
    } finally {
      showLoadingIndicator(false);
    }
  }

  /**
   * Renders trips, pulsing SVG markers, and connecting dashed route polylines
   */
  function renderTripsOnMap(trips) {
    // Clear old markers and lines
    clearMapLayers();

    const allCoordinates = [];

    trips.forEach((trip, tripIndex) => {
      const tripColor = trip.color || '#4f46e5';
      const tripLatLngs = [];

      trip.stops.forEach((stop, stopIndex) => {
        const coord = [stop.latitude, stop.longitude];
        tripLatLngs.push(coord);
        allCoordinates.push(coord);

        // Generate Custom Pulsing SVG Marker Pin
        const markerIcon = createPulsingSVGMarker(stop.sequence, tripColor, stop.city_name);

        const marker = L.marker(coord, {
          icon: markerIcon,
          riseOnHover: true,
          title: `Stop ${stop.sequence}: ${stop.city_name} (${trip.title})`
        }).addTo(map);

        // Rich interactive Leaflet popup
        const popupHtml = `
          <div class="gt-map-popup-card">
            <div class="position-relative overflow-hidden rounded-top" style="height: 100px;">
              <img src="${stop.image_url}" alt="${stop.city_name}" style="width: 100%; height: 100%; object-fit: cover;">
              <span class="badge position-absolute top-0 end-0 m-2 text-white" style="background: ${tripColor}; font-weight: 700;">
                Stop ${stop.sequence}
              </span>
              <span class="badge bg-dark bg-opacity-75 position-absolute bottom-0 start-0 m-2 text-white fs-8">
                ${trip.travel_style_display}
              </span>
            </div>
            <div class="p-3">
              <div class="d-flex justify-content-between align-items-center mb-1">
                <h6 class="fw-bold text-dark mb-0">${stop.city_name}</h6>
                <span class="text-muted fs-8">${stop.country_name}</span>
              </div>
              <p class="text-secondary fs-8 mb-2"><i class="fas fa-route me-1" style="color: ${tripColor};"></i> <strong>${trip.title}</strong></p>
              
              <div class="d-flex justify-content-between text-muted fs-8 mb-2 pb-2 border-bottom">
                <span><i class="fas fa-calendar-alt text-primary me-1"></i> ${stop.arrival_date}</span>
                <span><i class="fas fa-moon text-info me-1"></i> ${stop.duration_nights} Nights</span>
              </div>

              <div class="d-flex gap-2">
                <button type="button" class="btn btn-sm btn-primary w-100 fs-8 fw-bold" onclick="window.GlobeTrotterMap.openStopDrawer(${trip.id}, ${stop.stop_id})">
                  <i class="fas fa-circle-info me-1"></i> Full Details
                </button>
                <a href="${trip.view_url}" class="btn btn-sm btn-outline-secondary fs-8" title="Open Timeline">
                  <i class="fas fa-arrow-up-right-from-square"></i>
                </a>
              </div>
            </div>
          </div>
        `;

        marker.bindPopup(popupHtml, {
          maxWidth: 280,
          className: 'gt-custom-leaflet-popup'
        });

        // Click marker to open drawer
        marker.on('click', function () {
          openStopDrawer(trip, stop);
        });

        currentMarkers.push(marker);
      });

      // Draw dashed connecting polyline for trip stops
      if (tripLatLngs.length > 1) {
        const polyline = L.polyline(tripLatLngs, {
          color: tripColor,
          weight: 4,
          opacity: 0.85,
          dashArray: '8, 12',
          lineCap: 'round',
          lineJoin: 'round'
        }).addTo(map);

        // Tooltip showing trip details when hovering on line
        polyline.bindTooltip(
          `<strong>${trip.title}</strong><br><span class="fs-8">${trip.stops.length} Stops · ${trip.duration_days} Days</span>`,
          { sticky: true, opacity: 0.9 }
        );

        polyline.on('click', function () {
          if (trip.stops.length > 0) {
            openStopDrawer(trip, trip.stops[0]);
          }
        });

        currentPolylines.push(polyline);
      }
    });

    // Auto-fit bounds if we have coordinates
    if (allCoordinates.length > 0) {
      map.fitBounds(allCoordinates, { padding: [60, 60], maxZoom: 12 });
    }
  }

  /**
   * Generates custom pulsing SVG marker icon
   */
  function createPulsingSVGMarker(sequenceNumber, color, cityName) {
    const svgHtml = `
      <div class="gt-svg-pin-wrapper" style="--pin-color: ${color};">
        <div class="gt-pin-pulse"></div>
        <div class="gt-pin-head">
          <span>${sequenceNumber}</span>
        </div>
        <div class="gt-pin-label">${cityName}</div>
      </div>
    `;

    return L.divIcon({
      className: 'gt-pulsing-marker-pin',
      html: svgHtml,
      iconSize: [44, 44],
      iconAnchor: [22, 22],
      popupAnchor: [0, -24]
    });
  }

  function clearMapLayers() {
    currentMarkers.forEach(m => map.removeLayer(m));
    currentMarkers = [];
    currentPolylines.forEach(p => map.removeLayer(p));
    currentPolylines = [];
  }

  function fitAllRouteBounds() {
    if (currentMarkers.length === 0) return;
    const group = L.featureGroup(currentMarkers);
    map.fitBounds(group.getBounds(), { padding: [50, 50] });
  }

  /**
   * Browser Geolocation API: finds user's real GPS position
   */
  function handleUserGeolocation() {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser.');
      return;
    }

    if (btnMyLocation) {
      btnMyLocation.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Locating...';
      btnMyLocation.disabled = true;
    }

    navigator.geolocation.getCurrentPosition(
      function (pos) {
        const userLat = pos.coords.latitude;
        const userLng = pos.coords.longitude;

        if (userLocationMarker) {
          map.removeLayer(userLocationMarker);
        }

        const userBeaconIcon = L.divIcon({
          className: 'gt-user-beacon-pin',
          html: `
            <div class="gt-user-beacon-core">
              <div class="gt-user-beacon-ring"></div>
              <div class="gt-user-beacon-dot"></div>
            </div>
          `,
          iconSize: [36, 36],
          iconAnchor: [18, 18]
        });

        userLocationMarker = L.marker([userLat, userLng], { icon: userBeaconIcon }).addTo(map);
        userLocationMarker.bindPopup(`
          <div class="p-2 text-center">
            <span class="badge bg-primary mb-1">Your Location</span>
            <div class="fw-bold text-dark small">Lat: ${userLat.toFixed(4)}, Lng: ${userLng.toFixed(4)}</div>
            <p class="text-muted fs-8 mb-0">GPS accuracy within ${Math.round(pos.coords.accuracy)}m</p>
          </div>
        `).openPopup();

        map.flyTo([userLat, userLng], 10, { duration: 1.5 });

        if (btnMyLocation) {
          btnMyLocation.innerHTML = '<i class="fas fa-location-crosshairs text-success me-1"></i> Located!';
          setTimeout(() => {
            btnMyLocation.innerHTML = '<i class="fas fa-location-crosshairs me-1"></i> My Location';
            btnMyLocation.disabled = false;
          }, 3000);
        }
      },
      function (err) {
        console.warn('Geolocation failed:', err.message);
        alert('Could not access your location: ' + err.message);
        if (btnMyLocation) {
          btnMyLocation.innerHTML = '<i class="fas fa-location-crosshairs me-1"></i> My Location';
          btnMyLocation.disabled = false;
        }
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  }

  /**
   * Floating Drawer with place photo, dates, stay, expenses, and scheduled activities
   */
  function openStopDrawer(trip, stop) {
    if (!drawer || !drawerContent) return;

    activeStopData = { trip, stop };

    let activitiesHtml = '';
    if (stop.activities && stop.activities.length > 0) {
      activitiesHtml = stop.activities.map(act => `
        <div class="p-2 bg-light rounded-3 border mb-2 d-flex justify-content-between align-items-center">
          <div>
            <div class="d-flex align-items-center gap-1">
              <span class="badge bg-white text-dark border fs-8">${act.category_display}</span>
              <strong class="fs-8 text-dark">${act.title}</strong>
            </div>
            <div class="text-muted fs-8 mt-1">
              ${act.scheduled_date ? `<i class="fas fa-calendar-day text-primary me-1"></i>${act.scheduled_date}` : ''}
              ${act.start_time ? ` · <i class="fas fa-clock text-info me-1"></i>${act.start_time}` : ''}
              ${act.duration_minutes ? ` (${act.duration_minutes}m)` : ''}
            </div>
          </div>
          <span class="fw-bold text-dark fs-8">${trip.currency_symbol}${act.cost.toFixed(0)}</span>
        </div>
      `).join('');
    } else {
      activitiesHtml = '<div class="p-3 bg-light rounded-3 text-muted fs-8 fst-italic text-center">No scheduled activities logged for this stop.</div>';
    }

    drawerContent.innerHTML = `
      <div class="position-relative">
        <img src="${stop.image_url}" alt="${stop.city_name}" class="w-100 rounded-4 shadow-sm" style="height: 190px; object-fit: cover;">
        <div class="position-absolute top-0 end-0 m-3">
          <span class="badge text-white px-3 py-2 fs-7" style="background: ${trip.color}; font-weight: 700; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
            Stop ${stop.sequence}
          </span>
        </div>
        <div class="position-absolute bottom-0 start-0 m-3">
          <span class="badge bg-dark bg-opacity-85 text-white px-2 py-1 fs-8">
            ${trip.travel_style_display}
          </span>
        </div>
      </div>

      <div class="mt-3">
        <div class="d-flex justify-content-between align-items-start mb-1">
          <div>
            <h4 class="fw-bold text-dark mb-0">${stop.city_name}</h4>
            <span class="text-muted small">${stop.full_location}</span>
          </div>
          <span class="badge bg-success-subtle text-success border border-success-subtle px-2 py-1">
            ${trip.status_display}
          </span>
        </div>

        <div class="p-3 bg-light rounded-4 border my-3">
          <div class="d-flex align-items-center gap-2 mb-2">
            <i class="fas fa-route text-primary"></i>
            <span class="fw-bold text-dark fs-7">${trip.title}</span>
          </div>
          <div class="text-muted fs-8 mb-2">Planned by <strong>${trip.author}</strong> · ${trip.duration_days} Days total</div>

          <div class="row g-2 pt-2 border-top text-center">
            <div class="col-6">
              <span class="text-muted fs-9 d-block">Arrival Date</span>
              <strong class="fs-8 text-dark">${stop.arrival_date}</strong>
            </div>
            <div class="col-6">
              <span class="text-muted fs-9 d-block">Departure Date</span>
              <strong class="fs-8 text-dark">${stop.departure_date}</strong>
            </div>
          </div>
        </div>

        <!-- Accommodation & Transit -->
        <h6 class="fw-bold text-dark mb-2 fs-7"><i class="fas fa-hotel text-primary me-2"></i> Stay & Transit</h6>
        <div class="p-3 bg-white border rounded-4 shadow-xs mb-3">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="text-muted fs-8">Hotel / Resort</span>
            <span class="fw-semibold text-dark fs-8">${stop.accommodation_name || 'Standard Boutique Stay'}</span>
          </div>
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="text-muted fs-8">Stay Cost</span>
            <span class="fw-bold text-primary fs-8">${trip.currency_symbol}${stop.stay_cost.toFixed(0)}</span>
          </div>
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="text-muted fs-8">Transit Mode</span>
            <span class="badge bg-info-subtle text-info border fs-8">${stop.transport_type_display}</span>
          </div>
          <div class="d-flex justify-content-between align-items-center pt-2 border-top">
            <span class="text-muted fs-8">Transit Cost</span>
            <span class="fw-bold text-info fs-8">${trip.currency_symbol}${stop.transport_cost.toFixed(0)}</span>
          </div>
        </div>

        <!-- Scheduled Activities -->
        <div class="d-flex justify-content-between align-items-center mb-2">
          <h6 class="fw-bold text-dark mb-0 fs-7"><i class="fas fa-list-check text-success me-2"></i> Scheduled Activities</h6>
          <span class="badge bg-light text-dark border fs-8">${stop.activities_count} Items</span>
        </div>
        <div class="mb-4">
          ${activitiesHtml}
        </div>

        <!-- Action Links -->
        <div class="d-flex flex-column gap-2 pt-2 border-top">
          <a href="${trip.view_url}" class="btn btn-primary btn-sm fw-bold py-2">
            <i class="fas fa-eye me-1"></i> View Visual Timeline
          </a>
          ${trip.is_owner ? `
            <a href="${trip.builder_url}" class="btn btn-outline-primary btn-sm fw-semibold">
              <i class="fas fa-sliders me-1"></i> Open Itinerary Builder
            </a>
          ` : `
            <a href="${trip.share_url}" class="btn btn-outline-secondary btn-sm fw-semibold" target="_blank">
              <i class="fas fa-share-nodes me-1"></i> Public Shared Link
            </a>
          `}
        </div>
      </div>
    `;

    drawer.classList.add('open');
  }

  function closeDrawer() {
    if (drawer) drawer.classList.remove('open');
  }

  function showLoadingIndicator(show) {
    const loader = document.getElementById('map-loading-indicator');
    if (loader) {
      loader.style.display = show ? 'flex' : 'none';
    }
  }

  // Global scope helper for popup buttons
  window.GlobeTrotterMap = {
    openStopDrawer: function (tripId, stopId) {
      const trip = allTripsData.find(t => t.id === tripId);
      if (trip) {
        const stop = trip.stops.find(s => s.stop_id === stopId);
        if (stop) {
          openStopDrawer(trip, stop);
        }
      }
    }
  };

})();
