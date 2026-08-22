/* ==========================================================================
   GlobeTrotter - Next-Gen Interactive Dynamic Route & Destination Map Engine
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function () {
  // ------------------------------------------------------------------------
  // 1. Multi-City Trip Itinerary Route Map
  // ------------------------------------------------------------------------
  const mapContainer = document.getElementById('itinerary-map');
  if (mapContainer && window.routePoints && window.routePoints.length > 0) {
    initItineraryRouteMap(mapContainer, window.routePoints);
  }

  // ------------------------------------------------------------------------
  // 2. Single City & Activity Exploration Map
  // ------------------------------------------------------------------------
  const cityMapContainer = document.getElementById('city-overview-map');
  if (cityMapContainer && window.cityMapData) {
    initCityOverviewMap(cityMapContainer, window.cityMapData, window.activityPoints || []);
  }
});

/**
 * Calculates great-circle distance between two points in kilometers
 */
function calculateDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

/**
 * Initializes the full multi-stop itinerary route map
 */
function initItineraryRouteMap(container, points) {
  // Wrap map in relative container for toolbar if not already present
  if (!container.parentElement.classList.contains('map-wrapper')) {
    const wrapper = document.createElement('div');
    wrapper.className = 'map-wrapper position-relative';
    container.parentNode.insertBefore(wrapper, container);
    wrapper.appendChild(container);
  }
  const wrapper = container.parentElement;

  // Base Layers
  const streetsLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors, © CARTO'
  });

  const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: '© Esri, Maxar, Earthstar Geographics'
  });

  const darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors, © CARTO'
  });

  const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
  });

  const firstPt = points[0];
  const map = L.map(container.id, {
    center: [firstPt.lat, firstPt.lng],
    zoom: 5,
    layers: [streetsLayer],
    zoomControl: false
  });

  // Custom Zoom Control at bottom right
  L.control.zoom({ position: 'bottomright' }).addTo(map);

  // Floating Control Toolbar
  const toolbar = document.createElement('div');
  toolbar.className = 'gt-map-toolbar';
  toolbar.innerHTML = `
    <button type="button" class="gt-map-btn active" id="btn-map-streets"><i class="fas fa-map"></i> <span class="d-none d-sm-inline">Streets</span></button>
    <button type="button" class="gt-map-btn" id="btn-map-satellite"><i class="fas fa-satellite"></i> <span class="d-none d-sm-inline">Satellite</span></button>
    <button type="button" class="gt-map-btn" id="btn-map-dark"><i class="fas fa-moon"></i> <span class="d-none d-sm-inline">Dark</span></button>
    <button type="button" class="gt-map-btn text-primary fw-bold" id="btn-map-fit" title="Fit Entire Route"><i class="fas fa-expand"></i> <span class="d-none d-sm-inline">Fit</span></button>
  `;
  wrapper.appendChild(toolbar);

  // Toolbar layer toggle handlers
  const btnStreets = toolbar.querySelector('#btn-map-streets');
  const btnSatellite = toolbar.querySelector('#btn-map-satellite');
  const btnDark = toolbar.querySelector('#btn-map-dark');
  const btnFit = toolbar.querySelector('#btn-map-fit');

  function setActiveBtn(activeBtn) {
    [btnStreets, btnSatellite, btnDark].forEach(b => b.classList.remove('active'));
    activeBtn.classList.add('active');
  }

  btnStreets.addEventListener('click', () => {
    map.removeLayer(satelliteLayer);
    map.removeLayer(darkLayer);
    map.addLayer(streetsLayer);
    setActiveBtn(btnStreets);
  });

  btnSatellite.addEventListener('click', () => {
    map.removeLayer(streetsLayer);
    map.removeLayer(darkLayer);
    map.addLayer(satelliteLayer);
    setActiveBtn(btnSatellite);
  });

  btnDark.addEventListener('click', () => {
    map.removeLayer(streetsLayer);
    map.removeLayer(satelliteLayer);
    map.addLayer(darkLayer);
    setActiveBtn(btnDark);
  });

  const markers = [];
  const latlngs = [];
  let totalDistanceKm = 0;

  points.forEach((pt, index) => {
    const coord = [pt.lat, pt.lng];
    latlngs.push(coord);

    if (index > 0) {
      totalDistanceKm += calculateDistanceKm(points[index - 1].lat, points[index - 1].lng, pt.lat, pt.lng);
    }

    const orderNum = pt.order || (index + 1);

    // Glowing sequence pin with pulsing effect
    const customIcon = L.divIcon({
      className: 'custom-map-pin',
      html: `
        <div class="gt-svg-pin-wrapper" style="--pin-color: #4f46e5;">
          <div class="gt-pin-pulse"></div>
          <div class="gt-pin-head">
            <span>${orderNum}</span>
          </div>
          <div class="gt-pin-label">${pt.name}</div>
        </div>
      `,
      iconSize: [44, 44],
      iconAnchor: [22, 22],
      popupAnchor: [0, -24]
    });

    const marker = L.marker(coord, { icon: customIcon }).addTo(map);
    markers.push({ order: orderNum, marker, coord, name: pt.name });

    const popupHtml = `
      <div class="gt-popup-card">
        ${pt.image_url ? `
          <div class="position-relative mb-2 rounded-3 overflow-hidden" style="height: 110px;">
            <img src="${pt.image_url}" alt="${pt.name}" style="width: 100%; height: 100%; object-fit: cover;">
            <span class="gt-popup-badge bg-primary text-white position-absolute top-0 end-0 m-2">Stop ${orderNum}</span>
          </div>
        ` : `
          <div class="d-flex justify-content-between align-items-center mb-2">
            <span class="gt-popup-badge bg-primary text-white">Stop ${orderNum}</span>
            <span class="text-muted fs-8"><i class="fas fa-location-dot text-danger me-1"></i>${pt.country}</span>
          </div>
        `}
        <h6 class="fw-bold text-dark mb-1 fs-6">${pt.name}</h6>
        ${pt.arrival ? `<div class="text-muted fs-8 mb-1"><i class="fas fa-calendar-alt text-primary me-1"></i>${pt.arrival} ${pt.departure ? '&ndash; ' + pt.departure : ''} (${pt.nights || 1}N)</div>` : ''}
        ${pt.stay ? `<div class="text-primary small mb-1"><i class="fas fa-hotel me-1"></i>${pt.stay}</div>` : ''}
        ${pt.transport ? `<div class="text-info fs-8 mb-2"><i class="fas fa-plane-arrival me-1"></i>Arrival via ${pt.transport}</div>` : ''}
        <div class="d-flex gap-1 mt-2">
          <button type="button" class="btn btn-sm btn-primary py-1 px-2 fs-8 fw-semibold w-100" onclick="focusTimelineDay(${orderNum})">
            <i class="fas fa-timeline me-1"></i> View Day Plan
          </button>
        </div>
      </div>
    `;
    marker.bindPopup(popupHtml);
  });

  // Polyline for Route
  let polyline = null;
  if (latlngs.length > 1) {
    polyline = L.polyline(latlngs, {
      color: '#4f46e5',
      weight: 4,
      opacity: 0.85,
      dashArray: '10, 10',
      lineCap: 'round',
      lineJoin: 'round'
    }).addTo(map);

    map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
  } else {
    map.setView(latlngs[0], 7);
  }

  btnFit.addEventListener('click', () => {
    if (polyline) {
      map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
    } else if (latlngs.length > 0) {
      map.setView(latlngs[0], 7);
    }
  });

  // Global helper to focus a stop on the map from timeline cards
  window.focusMapStop = function (stopOrder) {
    const target = markers.find(m => m.order === stopOrder);
    if (target) {
      map.flyTo(target.coord, 11, { duration: 1.2 });
      setTimeout(() => {
        target.marker.openPopup();
      }, 1250);
    }
  };

  // Global helper to scroll to day card
  window.focusTimelineDay = function (dayNum) {
    const dayEl = document.getElementById(`timeline-day-${dayNum}`);
    if (dayEl) {
      dayEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      dayEl.classList.add('shadow-lg', 'border-primary');
      setTimeout(() => {
        dayEl.classList.remove('shadow-lg', 'border-primary');
      }, 2500);
    }
  };
}

/**
 * Initializes single City Overview map with tourist activity pins
 */
function initCityOverviewMap(container, cityData, activities) {
  const streetsLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    attribution: '© CARTO, © OpenStreetMap contributors'
  });

  const map = L.map(container.id, {
    center: [cityData.lat, cityData.lng],
    zoom: 12,
    layers: [streetsLayer]
  });

  // City Center marker
  const cityPin = L.divIcon({
    className: 'custom-map-pin',
    html: `
      <div style="background: linear-gradient(135deg, #ea580c, #f97316); color: white; width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; border: 3px solid white; box-shadow: 0 4px 15px rgba(234, 88, 12, 0.5);">
        <i class="fas fa-city"></i>
      </div>
    `,
    iconSize: [42, 42],
    iconAnchor: [21, 21]
  });

  L.marker([cityData.lat, cityData.lng], { icon: cityPin })
    .addTo(map)
    .bindPopup(`
      <div class="p-2">
        <h6 class="fw-bold mb-1">${cityData.name}</h6>
        <p class="text-muted small mb-0">${cityData.country}</p>
      </div>
    `);

  // Activity pins
  const categoryColors = {
    'SIGHTSEEING': '#3b82f6',
    'ADVENTURE': '#10b981',
    'CULTURE': '#8b5cf6',
    'FOOD': '#f59e0b',
    'SHOPPING': '#ec4899',
    'RELAXATION': '#06b6d4',
    'SPIRITUAL': '#f97316'
  };

  activities.forEach(act => {
    if (act.lat && act.lng) {
      const color = categoryColors[act.category] || '#4f46e5';
      const actPin = L.divIcon({
        className: 'custom-map-pin',
        html: `
          <div class="gt-activity-pin" style="background: ${color};" title="${act.name}">
            <i class="fas fa-location-dot"></i>
          </div>
        `,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
      });

      L.marker([act.lat, act.lng], { icon: actPin })
        .addTo(map)
        .bindPopup(`
          <div class="p-2">
            <span class="badge bg-light text-dark border mb-1">${act.category}</span>
            <h6 class="fw-bold mb-1 small">${act.name}</h6>
            <div class="text-primary small fw-semibold">${act.cost ? '₹' + act.cost : 'Free'} · ${act.duration || '2 hrs'}</div>
          </div>
        `);
    }
  });
}

