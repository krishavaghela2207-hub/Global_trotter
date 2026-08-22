/**
 * GlobeTrotter - Comprehensive Single-Page Application Client Engine
 * Empowering Personalized Travel Planning (Odoo Hackathon)
 */

// Global State
const state = {
  currentUser: null,
  activeScreen: 'dashboard',
  cities: [],
  activities: [],
  categories: [],
  regions: [],
  trips: [],
  currentTripDetail: null,
  currentTripBudget: null,
  calendarDate: new Date(),
  charts: {},
  currency: 'USD',
  currencyRates: {
    'USD': { symbol: '$', rate: 1.0 },
    'EUR': { symbol: '€', rate: 0.92 },
    'GBP': { symbol: '£', rate: 0.79 },
    'JPY': { symbol: '¥', rate: 154.5 },
    'INR': { symbol: '₹', rate: 83.5 },
    'AUD': { symbol: 'A$', rate: 1.52 },
    'AED': { symbol: 'AED', rate: 3.67 },
    'CHF': { symbol: 'CHF', rate: 0.90 }
  },
  leafletMap: null,
  selectedAiPersona: 'luxury_gourmet',
  generatedAiTrip: null
};

// Multi-Currency Converter Helper
function formatMoney(amountInUsd) {
  const curr = state.currency || 'USD';
  const info = state.currencyRates[curr] || { symbol: '$', rate: 1.0 };
  const val = (parseFloat(amountInUsd) || 0) * info.rate;
  if (curr === 'JPY') {
    return `${info.symbol}${Math.round(val).toLocaleString()}`;
  }
  return `${info.symbol}${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function changeGlobalCurrency(code) {
  state.currency = code;
  showToast(`Switched currency to ${code}`);
  // Refresh active screen to update all displayed prices
  navigateTo(state.activeScreen);
}

// --- CSRF & API Helpers --- //
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');

async function apiFetch(url, options = {}) {
  options.headers = options.headers || {};
  if (!options.headers['Content-Type'] && !(options.body instanceof FormData)) {
    options.headers['Content-Type'] = 'application/json';
  }
  if (csrftoken) {
    options.headers['X-CSRFToken'] = csrftoken;
  }
  try {
    const res = await fetch(url, options);
    const data = await res.json();
    return data;
  } catch (err) {
    console.error('API Fetch Error:', err);
    showToast('Network error or server unavailable', 'error');
    throw err;
  }
}

// Toast Notifications
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  const icon = type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ');
  toast.innerHTML = `
    <span style="font-weight: bold; color: ${type === 'success' ? '#10B981' : (type === 'error' ? '#EF4444' : '#6366F1')}">${icon}</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// --- Router & Screen Navigation --- //
function navigateTo(screenId, params = {}) {
  // Hide all screens
  document.querySelectorAll('.screen-section').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));

  // Normalize screenId
  let targetId = screenId;
  if (targetId.startsWith('#')) targetId = targetId.substring(1);
  if (targetId.includes('?')) targetId = targetId.split('?')[0];

  const targetEl = document.getElementById(`screen-${targetId}`);
  if (targetEl) {
    targetEl.classList.add('active');
    state.activeScreen = targetId;

    // Update active nav link
    const navLink = document.querySelector(`.nav-link[data-screen="${targetId}"]`);
    if (navLink) navLink.classList.add('active');

    // Trigger screen-specific loaders
    if (targetId === 'dashboard') loadDashboard();
    else if (targetId === 'ai-concierge') loadAiConcierge();
    else if (targetId === 'route-map') loadRouteMap();
    else if (targetId === 'my-trips') loadMyTrips();
    else if (targetId === 'create-trip') initCreateTrip();
    else if (targetId === 'city-search') loadCitySearch();
    else if (targetId === 'activity-search') loadActivitySearch();
    else if (targetId === 'community') loadCommunity();
    else if (targetId === 'calendar') loadCalendar();
    else if (targetId === 'profile') loadUserProfile();
    else if (targetId === 'admin-analytics') loadAdminAnalytics();
    else if (targetId === 'itinerary') {
      if (params.tripId) loadItineraryView(params.tripId);
    } else if (targetId === 'builder') {
      if (params.tripId) loadItineraryBuilder(params.tripId);
    } else if (targetId === 'budget-view') {
      if (params.tripId) loadBudgetScreen(params.tripId);
    } else if (targetId === 'packing') {
      if (params.tripId) loadPackingScreen(params.tripId);
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else {
    // Fallback to dashboard
    navigateTo('dashboard');
  }
}

// Global Router Hash Listener
window.addEventListener('hashchange', () => {
  const hash = window.location.hash.substring(1);
  if (!hash) {
    navigateTo('dashboard');
    return;
  }
  if (hash.startsWith('itinerary-')) {
    const id = hash.replace('itinerary-', '');
    navigateTo('itinerary', { tripId: id });
  } else if (hash.startsWith('builder-')) {
    const id = hash.replace('builder-', '');
    navigateTo('builder', { tripId: id });
  } else if (hash.startsWith('budget-')) {
    const id = hash.replace('budget-', '');
    navigateTo('budget-view', { tripId: id });
  } else if (hash.startsWith('packing-')) {
    const id = hash.replace('packing-', '');
    navigateTo('packing', { tripId: id });
  } else {
    navigateTo(hash);
  }
});
    navigateTo(hash);
  }
});

// --- Initial App Initialization --- //
document.addEventListener('DOMContentLoaded', async () => {
  await checkAuth();
  await loadGlobalCatalogs();

  // Setup Event Listeners
  setupNavigationEvents();
  setupAuthModalEvents();
  setupFilterBars();
  setupThemeToggle();

  // Check initial hash
  const initialHash = window.location.hash.substring(1);
  if (initialHash) {
    window.dispatchEvent(new Event('hashchange'));
  } else {
    navigateTo('dashboard');
  }
});

async function checkAuth() {
  const res = await apiFetch('/api/auth/me/');
  if (res && res.authenticated) {
    state.currentUser = res.user;
    updateUserNavUI(res.user);
  } else {
    state.currentUser = null;
    updateUserNavUI(null);
  }
}

function updateUserNavUI(user) {
  const userActions = document.getElementById('nav-user-actions');
  if (!userActions) return;

  if (user) {
    userActions.innerHTML = `
      <div class="user-menu-btn" onclick="navigateTo('profile')">
        <img class="user-avatar" src="${user.avatar_url || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=300&auto=format&fit=crop&q=80'}" alt="${user.username}" />
        <span style="font-size:0.9rem; font-weight:600;">${user.first_name || user.username}</span>
      </div>
      <button class="btn btn-primary btn-sm" onclick="navigateTo('create-trip')">
        <span>+ Plan a Trip</span>
      </button>
      <button class="btn btn-outline btn-sm" onclick="handleLogout()" title="Logout">
        <span>🚪</span>
      </button>
    `;
  } else {
    userActions.innerHTML = `
      <button class="btn btn-outline btn-sm" onclick="openAuthModal('login')">Log In</button>
      <button class="btn btn-primary btn-sm" onclick="openAuthModal('signup')">Sign Up</button>
      <button class="btn btn-emerald btn-sm" onclick="navigateTo('create-trip')">
        <span>+ Plan Trip</span>
      </button>
    `;
  }
}

async function loadGlobalCatalogs() {
  const [citiesRes, regionsRes, catsRes] = await Promise.all([
    apiFetch('/api/cities/'),
    apiFetch('/api/regions/'),
    apiFetch('/api/activities/')
  ]);
  if (citiesRes) state.cities = citiesRes.cities || [];
  if (regionsRes) state.regions = regionsRes.regions || [];
  if (catsRes) {
    state.activities = catsRes.activities || [];
    state.categories = catsRes.categories || [];
  }
}

function setupNavigationEvents() {
  document.querySelectorAll('[data-nav]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const target = btn.getAttribute('data-nav');
      window.location.hash = target;
    });
  });
}

function setupThemeToggle() {
  const toggleBtn = document.getElementById('theme-toggle-btn');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      document.body.classList.toggle('light-theme');
      const isLight = document.body.classList.contains('light-theme');
      toggleBtn.innerHTML = isLight ? '🌙' : '☀️';
    });
  }
}

// --- Auth Modal & Handling (Screen 1 & 2) --- //
function openAuthModal(mode = 'login') {
  const modal = document.getElementById('auth-modal');
  if (!modal) return;
  modal.classList.add('active');
  switchAuthTab(mode);
}

function closeAuthModal() {
  const modal = document.getElementById('auth-modal');
  if (modal) modal.classList.remove('active');
}

function switchAuthTab(tab) {
  const loginForm = document.getElementById('auth-login-form');
  const signupForm = document.getElementById('auth-signup-form');
  const tabBtns = document.querySelectorAll('.auth-tab-btn');

  tabBtns.forEach(btn => btn.classList.remove('active'));
  if (tab === 'login') {
    loginForm.style.display = 'block';
    signupForm.style.display = 'none';
    const btn = document.querySelector('.auth-tab-btn[data-tab="login"]');
    if (btn) btn.classList.add('active');
  } else {
    loginForm.style.display = 'none';
    signupForm.style.display = 'block';
    const btn = document.querySelector('.auth-tab-btn[data-tab="signup"]');
    if (btn) btn.classList.add('active');
  }
}

function setupAuthModalEvents() {
  const loginForm = document.getElementById('auth-login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = loginForm.querySelector('#login-username').value;
      const password = loginForm.querySelector('#login-password').value;
      const res = await apiFetch('/api/auth/login/', {
        method: 'POST',
        body: JSON.stringify({ username, password })
      });
      if (res && res.success) {
        showToast('Logged in successfully!');
        closeAuthModal();
        await checkAuth();
        navigateTo('dashboard');
      } else {
        showToast(res.error || 'Login failed', 'error');
      }
    });
  }

  const signupForm = document.getElementById('auth-signup-form');
  if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        username: signupForm.querySelector('#signup-username').value,
        email: signupForm.querySelector('#signup-email').value,
        password: signupForm.querySelector('#signup-password').value,
        first_name: signupForm.querySelector('#signup-firstname').value,
        last_name: signupForm.querySelector('#signup-lastname').value,
        phone_number: signupForm.querySelector('#signup-phone').value,
        city: signupForm.querySelector('#signup-city').value,
        country: signupForm.querySelector('#signup-country').value,
        bio: signupForm.querySelector('#signup-bio').value,
        avatar_url: signupForm.querySelector('#signup-avatar').value,
      };
      const res = await apiFetch('/api/auth/register/', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      if (res && res.success) {
        showToast('Account created successfully!');
        closeAuthModal();
        await checkAuth();
        navigateTo('dashboard');
      } else {
        showToast(res.error || 'Signup failed', 'error');
      }
    });
  }
}

async function handleLogout() {
  await apiFetch('/api/auth/logout/', { method: 'POST' });
  showToast('Logged out');
  await checkAuth();
  navigateTo('dashboard');
}

// --- Screen 3: Dashboard / Home Screen --- //
async function loadDashboard() {
  const container = document.getElementById('dashboard-container');
  if (!container) return;

  // Load user trips and top destinations
  const [tripsRes, citiesRes] = await Promise.all([
    apiFetch('/api/trips/'),
    apiFetch('/api/cities/?sort=popularity')
  ]);

  const trips = (tripsRes && tripsRes.trips) || [];
  const topCities = (citiesRes && citiesRes.cities) ? citiesRes.cities.slice(0, 4) : [];

  // Recent/Ongoing trips
  const ongoingTrips = trips.filter(t => t.status === 'ongoing');
  const upcomingTrips = trips.filter(t => t.status === 'upcoming');
  const displayTrips = ongoingTrips.length > 0 ? ongoingTrips : upcomingTrips;

  container.innerHTML = `
    <!-- Hero Banner -->
    <div class="hero-banner">
      <img class="hero-banner-bg" src="https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=1600&auto=format&fit=crop&q=80" alt="GlobeTrotter Banner" />
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <div class="hero-badge">
          <span>✨</span> Empowering Personalized Travel Planning
        </div>
        <h1 class="hero-title">Dream, Design & Explore <span>Without Limits</span></h1>
        <p class="hero-subtitle">Organize multi-city stops, balance budgets with precision, discover hidden gems, and share unforgettable itineraries with a global community.</p>
        <div style="display:flex; gap:1rem; flex-wrap:wrap;">
          <button class="btn btn-primary btn-lg" onclick="navigateTo('create-trip')">
            <span>🚀 Start Planning New Trip</span>
          </button>
          <button class="btn btn-secondary btn-lg" onclick="navigateTo('city-search')">
            <span>🌍 Explore 16+ Global Cities</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Wireframe Toolbar (Search, Filter, Group, Sort) -->
    <div class="filter-search-toolbar">
      <div class="search-input-group">
        <span>🔍</span>
        <input type="text" id="dash-quick-search" placeholder="Search cities, activities, or trips..." onkeyup="handleDashboardSearch(this.value)" />
      </div>
      <div class="toolbar-select-group">
        <select class="custom-select" id="dash-region-filter" onchange="filterDashboardCities(this.value)">
          <option value="all">Group by: All Regions</option>
          ${state.regions.map(r => `<option value="${r.id}">${r.name}</option>`).join('')}
        </select>
        <select class="custom-select" id="dash-cost-filter" onchange="filterDashboardCitiesByCost(this.value)">
          <option value="all">Filter: Any Budget ($ - $$$)</option>
          <option value="$">Budget ($)</option>
          <option value="$$">Moderate ($$)</option>
          <option value="$$$">Luxury ($$$)</option>
        </select>
        <button class="btn btn-primary btn-sm" onclick="navigateTo('create-trip')">+ Plan a Trip</button>
      </div>
    </div>

    <!-- Top Regional Selections (Screen 3 Wireframe) -->
    <div class="section-header-row">
      <div class="section-title-group">
        <h2><span>🌟</span> Top Regional Selections</h2>
        <p class="section-subtitle">Curated world-class destinations with live budget indexes and activity hubs</p>
      </div>
      <button class="btn btn-outline btn-sm" onclick="navigateTo('city-search')">View All Destinations →</button>
    </div>

    <div class="cards-grid-4" id="dashboard-cities-grid">
      ${topCities.map(city => renderCityCard(city)).join('')}
    </div>

    <!-- Active & Upcoming Trips Section (Screen 3 Wireframe) -->
    <div class="section-header-row">
      <div class="section-title-group">
        <h2><span>✈️</span> Your Journey Dashboard</h2>
        <p class="section-subtitle">Active, upcoming, and recent multi-city itineraries</p>
      </div>
      <button class="btn btn-outline btn-sm" onclick="navigateTo('my-trips')">Go to My Trips (${trips.length}) →</button>
    </div>

    ${trips.length === 0 ? `
      <div class="glass-panel" style="padding: 3rem; text-align: center; margin-bottom: 2.5rem;">
        <h3>Ready for your next adventure?</h3>
        <p style="color:var(--text-secondary); margin: 0.75rem 0 1.5rem;">You haven't created any trips yet. Start building your dream itinerary now!</p>
        <button class="btn btn-primary" onclick="navigateTo('create-trip')">+ Create Your First Trip</button>
      </div>
    ` : `
      <div class="trips-grid-3">
        ${trips.slice(0, 3).map(trip => renderTripCard(trip)).join('')}
      </div>
    `}
  `;
}

function renderCityCard(city) {
  return `
    <div class="city-card" onclick="openCityModal(${city.id})">
      <img class="city-card-bg" src="${city.image_url}" alt="${city.name}" loading="lazy" />
      <div class="city-card-overlay"></div>
      <div class="city-card-content">
        <div class="city-badges-row">
          <span class="badge badge-cost">${city.cost_index_display || city.cost_index}</span>
          <span class="badge badge-pop">★ ${city.popularity_score}</span>
        </div>
        <h3 class="city-title">${city.flag_emoji || '🌍'} ${city.name}</h3>
        <p class="city-meta-text">
          <span>${city.country}</span> • <span>~${formatMoney(city.avg_daily_cost)}/day</span>
        </p>
      </div>
    </div>
  `;
}

function renderTripCard(trip) {
  const statusClass = `badge-status-${trip.status}`;
  return `
    <div class="trip-card">
      <div class="trip-card-cover">
        <img src="${trip.cover_image}" alt="${trip.title}" loading="lazy" />
        <div class="trip-cover-badges">
          <span class="badge ${statusClass}">${trip.status_display || trip.status}</span>
          <span class="badge" style="background:rgba(0,0,0,0.6); color:#FFF;">${trip.duration_days} Days</span>
        </div>
      </div>
      <div class="trip-card-body">
        <h3 class="trip-card-title">${trip.title}</h3>
        <div class="trip-route-badge">
          <span>📍</span> ${trip.destinations_summary || 'Multi-City Route'}
        </div>
        <p class="trip-description-snippet">${trip.description || 'Custom curated travel itinerary.'}</p>
        
        <div class="trip-stats-bar">
          <div class="stat-item">
            <span class="stat-item-label">Budget</span>
            <span class="stat-item-val" style="color:var(--emerald);">${formatMoney(trip.total_budget)}</span>
          </div>
          <div class="stat-item">
            <span class="stat-item-label">Stops</span>
            <span class="stat-item-val">${trip.destinations_count || 0} Cities</span>
          </div>
          <div class="stat-item">
            <span class="stat-item-label">Activities</span>
            <span class="stat-item-val">${trip.activities_count || 0}</span>
          </div>
        </div>

        <div class="trip-card-footer">
          <div style="display:flex; gap:0.35rem; flex-wrap:wrap;">
            <button class="btn btn-primary btn-sm" onclick="window.location.hash='itinerary-${trip.id}'">View</button>
            <button class="btn btn-secondary btn-sm" onclick="window.location.hash='builder-${trip.id}'">Stops</button>
            <button class="btn btn-outline btn-sm" onclick="openBoardingPassModal(${trip.id})" title="Luxury Boarding Pass">🎫 Pass</button>
            <button class="btn btn-outline btn-sm" onclick="openEcoScoreModal(${trip.id})" title="Carbon Eco Score">🌱 Eco</button>
            <button class="btn btn-outline btn-sm" onclick="window.location.hash='packing-${trip.id}'" title="Packing List">🎒 Pack</button>
          </div>
          <button class="btn btn-icon" onclick="openShareModal(${trip.id})" title="Share Trip">🔗</button>
        </div>
      </div>
    </div>
  `;
}

// --- Screen 4: Create Trip Screen (Odoo Wireframe Screen 4) --- //
function initCreateTrip() {
  const container = document.getElementById('create-trip-container');
  if (!container) return;

  // Set default dates
  const today = new Date();
  const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
  const startStr = today.toISOString().split('T')[0];
  const endStr = nextWeek.toISOString().split('T')[0];

  const suggestedCities = state.cities.slice(0, 6);

  container.innerHTML = `
    <div class="form-card-container">
      <div style="margin-bottom: 2rem;">
        <h1 style="font-size:2rem; margin-bottom:0.4rem;">Plan a New Trip</h1>
        <p style="color:var(--text-secondary);">Set your travel timeline, budget, and pick starting destinations with automatic activity suggestions.</p>
      </div>

      <form id="create-trip-form">
        <div class="form-group">
          <label class="form-label"><span>🏷️</span> Trip Name</label>
          <input type="text" class="form-control" id="new-trip-title" placeholder="e.g. Mediterranean Coastline & Historic Rome" required />
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label"><span>📅</span> Start Date</label>
            <input type="date" class="form-control" id="new-trip-start" value="${startStr}" required />
          </div>
          <div class="form-group">
            <label class="form-label"><span>📅</span> End Date</label>
            <input type="date" class="form-control" id="new-trip-end" value="${endStr}" required />
          </div>
        </div>

        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label"><span>💰</span> Total Estimated Budget (USD)</label>
            <input type="number" class="form-control" id="new-trip-budget" value="2500" min="100" step="50" required />
          </div>
          <div class="form-group">
            <label class="form-label"><span>📍</span> Initial City / Stop</label>
            <select class="form-control" id="new-trip-city">
              <option value="">-- Choose Starting City --</option>
              ${state.cities.map(c => `<option value="${c.id}">${c.flag_emoji || '🌍'} ${c.name}, ${c.country}</option>`).join('')}
            </select>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label"><span>📝</span> Trip Description & Goals</label>
          <textarea class="form-control" id="new-trip-desc" placeholder="What are your main travel goals, food cravings, and must-see sights for this trip?"></textarea>
        </div>

        <div class="form-group">
          <label class="form-label"><span>🖼️</span> Cover Photo URL (Optional)</label>
          <input type="url" class="form-control" id="new-trip-cover" placeholder="https://images.unsplash.com/..." />
        </div>

        <!-- Wireframe Screen 4: Suggestions for Places to Visit / Activities to Perform -->
        <div class="suggestions-panel">
          <h3 style="font-size:1.15rem; display:flex; align-items:center; gap:0.5rem;">
            <span>💡</span> Suggestions for Places to Visit & Activities to Perform
          </h3>
          <p style="font-size:0.85rem; color:var(--text-secondary); margin-top:0.25rem;">Click any popular destination to automatically prefill your starting stop</p>
          
          <div class="suggestions-grid">
            ${suggestedCities.map(c => `
              <div class="suggestion-card" onclick="selectSuggestionCity(${c.id}, '${c.name}')">
                <img src="${c.image_url}" alt="${c.name}" />
                <div class="suggestion-card-info">
                  <div class="suggestion-card-title">${c.flag_emoji} ${c.name}</div>
                  <div class="suggestion-card-cost">~$${c.avg_daily_cost}/day • ★ ${c.popularity_score}</div>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <div style="display:flex; justify-content:flex-end; gap:1rem; margin-top:2.5rem;">
          <button type="button" class="btn btn-secondary" onclick="navigateTo('dashboard')">Cancel</button>
          <button type="submit" class="btn btn-primary btn-lg">
            <span>✨ Create Trip & Build Itinerary</span>
          </button>
        </div>
      </form>
    </div>
  `;

  document.getElementById('create-trip-form').addEventListener('submit', handleCreateTripSubmit);
}

function selectSuggestionCity(cityId, cityName) {
  const citySelect = document.getElementById('new-trip-city');
  if (citySelect) {
    citySelect.value = cityId;
    showToast(`Selected ${cityName} as starting stop!`);
  }
}

async function handleCreateTripSubmit(e) {
  e.preventDefault();
  const title = document.getElementById('new-trip-title').value.trim();
  const start_date = document.getElementById('new-trip-start').value;
  const end_date = document.getElementById('new-trip-end').value;
  const total_budget = document.getElementById('new-trip-budget').value;
  const city_id = document.getElementById('new-trip-city').value;
  const description = document.getElementById('new-trip-desc').value.trim();
  const cover_image = document.getElementById('new-trip-cover').value.trim();

  const stops = [];
  if (city_id) {
    stops.push({
      city_id: parseInt(city_id),
      arrival_date: start_date,
      departure_date: end_date,
      allocated_budget: total_budget
    });
  }

  const res = await apiFetch('/api/trips/create/', {
    method: 'POST',
    body: JSON.stringify({
      title,
      start_date,
      end_date,
      total_budget,
      description,
      cover_image,
      is_public: true,
      stops
    })
  });

  if (res && res.success) {
    showToast('Trip created successfully!');
    window.location.hash = `builder-${res.trip.id}`;
  } else {
    showToast(res.error || 'Failed to create trip', 'error');
  }
}

// --- Screen 5: Itinerary Builder Screen (Odoo Wireframe Screen 5) --- //
async function loadItineraryBuilder(tripId) {
  const container = document.getElementById('builder-container');
  if (!container) return;

  const trip = await apiFetch(`/api/trips/${tripId}/`);
  if (!trip || trip.error) {
    showToast('Failed to load trip', 'error');
    navigateTo('my-trips');
    return;
  }
  state.currentTripDetail = trip;

  container.innerHTML = `
    <div style="max-width: 1080px; margin: 0 auto;">
      <!-- Header -->
      <div class="glass-panel" style="padding: 1.75rem; margin-bottom: 2rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
        <div>
          <button class="btn btn-outline btn-sm" onclick="window.location.hash='my-trips'" style="margin-bottom:0.5rem;">← Back to Trips</button>
          <h1 style="font-size:2rem;">Build Itinerary: ${trip.title}</h1>
          <p style="color:var(--text-secondary); font-size:0.92rem;">
            📅 ${trip.start_date} to ${trip.end_date} (${trip.duration_days} Days) • Total Budget: <b style="color:var(--emerald);">$${trip.total_budget}</b>
          </p>
        </div>
        <div style="display:flex; gap:0.5rem;">
          <button class="btn btn-outline" onclick="window.location.hash='itinerary-${trip.id}'">👁️ View Final Plan</button>
          <button class="btn btn-primary" onclick="openAddStopModal(${trip.id})">+ Add Another Stop / Section</button>
        </div>
      </div>

      <!-- Multi-Section / Multi-Stop List (Wireframe Screen 5: Section 1, Section 2, Section 3...) -->
      <div class="stops-builder-container" id="builder-stops-list">
        ${trip.stops.length === 0 ? `
          <div class="glass-panel" style="padding:3rem; text-align:center;">
            <h3>No Stops Added Yet</h3>
            <p style="color:var(--text-secondary); margin:0.5rem 0 1.5rem;">Add your first destination city to start scheduling daily activities and section budgets.</p>
            <button class="btn btn-primary" onclick="openAddStopModal(${trip.id})">+ Add Section 1</button>
          </div>
        ` : trip.stops.map((stop, idx) => renderBuilderStopSection(stop, idx + 1, trip.id)).join('')}
      </div>

      <!-- Add Another Section Wireframe Button -->
      <div style="text-align:center; margin: 2.5rem 0;">
        <button class="btn btn-secondary btn-lg" onclick="openAddStopModal(${trip.id})" style="border: 2px dashed var(--border-highlight); padding: 1.2rem 3rem;">
          <span style="font-size:1.2rem;">＋</span> Add another Section / Stop
        </button>
      </div>
    </div>
  `;
}

function renderBuilderStopSection(stop, sectionNum, tripId) {
  return `
    <div class="stop-section-block">
      <div class="stop-section-header">
        <div class="stop-section-title">
          <span style="background:var(--grad-primary); width:28px; height:28px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; color:#FFF; font-size:0.85rem;">${sectionNum}</span>
          <span>Section ${sectionNum}: ${stop.flag_emoji || '📍'} ${stop.city_name}, ${stop.country_name}</span>
        </div>
        <div style="display:flex; align-items:center; gap:0.5rem;">
          <span class="badge badge-cost">Allocated: $${stop.allocated_budget}</span>
          <button class="btn btn-icon" onclick="deleteStop(${stop.id})" title="Delete Section" style="color:var(--rose);">🗑️</button>
        </div>
      </div>

      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1rem; font-size:0.88rem; color:var(--text-secondary); margin-bottom:1rem;">
        <div><b>Date Range:</b> ${stop.arrival_date} to ${stop.departure_date} (${stop.duration_days} Days)</div>
        <div><b>Budget of this section:</b> $${stop.allocated_budget}</div>
      </div>

      ${stop.notes ? `<p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1rem; font-style:italic;">Notes: ${stop.notes}</p>` : ''}

      <!-- Activities inside this stop -->
      <div style="margin-top:1.25rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem;">
          <span style="font-weight:600; font-size:0.92rem;">Assigned Activities & Schedule (${stop.items.length})</span>
          <button class="btn btn-outline btn-sm" onclick="openAddActivityModal(${stop.id}, ${stop.city_id})">+ Assign Activity</button>
        </div>

        <div class="stop-activities-list">
          ${stop.items.length === 0 ? `
            <div style="padding:1rem; text-align:center; color:var(--text-muted); font-size:0.85rem; background:var(--bg-surface); border-radius:var(--radius-md);">
              No activities assigned yet. Click "+ Assign Activity" to select from curated catalog.
            </div>
          ` : stop.items.map(item => `
            <div class="stop-activity-row">
              <div style="display:flex; align-items:center; gap:0.75rem;">
                <span class="badge badge-category">Day ${item.day_number}</span>
                <span style="font-weight:600;">${item.title}</span>
                <span style="font-size:0.8rem; color:var(--text-muted);">(${item.start_time} - ${item.end_time})</span>
              </div>
              <div style="display:flex; align-items:center; gap:0.75rem;">
                <span style="color:var(--emerald); font-weight:700;">$${item.cost}</span>
                <button class="btn btn-icon" onclick="deleteItineraryItem(${item.id})" style="width:30px; height:30px; font-size:0.8rem;" title="Remove">✕</button>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;
}

// Modal for Adding a Stop / Section
function openAddStopModal(tripId) {
  const modal = document.getElementById('generic-modal');
  if (!modal) return;

  const trip = state.currentTripDetail;
  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Add Stop / Section to Trip</h3>
        <span class="modal-close-btn" onclick="closeGenericModal()">✕</span>
      </div>
      <form id="add-stop-form">
        <div class="form-group">
          <label class="form-label">Select City / Destination</label>
          <select class="form-control" id="modal-stop-city" required>
            <option value="">-- Choose City --</option>
            ${state.cities.map(c => `<option value="${c.id}">${c.flag_emoji} ${c.name}, ${c.country} (~$${c.avg_daily_cost}/day)</option>`).join('')}
          </select>
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">Arrival Date</label>
            <input type="date" class="form-control" id="modal-stop-arr" value="${trip ? trip.start_date : ''}" required />
          </div>
          <div class="form-group">
            <label class="form-label">Departure Date</label>
            <input type="date" class="form-control" id="modal-stop-dep" value="${trip ? trip.end_date : ''}" required />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Section Allocated Budget ($)</label>
          <input type="number" class="form-control" id="modal-stop-budget" value="800" min="50" required />
        </div>
        <div class="form-group">
          <label class="form-label">Section Notes / Accommodations</label>
          <textarea class="form-control" id="modal-stop-notes" placeholder="Hotel name, flight details, or key priorities..."></textarea>
        </div>
        <div style="display:flex; justify-content:flex-end; gap:1rem; margin-top:1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeGenericModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">+ Add Section</button>
        </div>
      </form>
    </div>
  `;
  modal.classList.add('active');

  document.getElementById('add-stop-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const city_id = document.getElementById('modal-stop-city').value;
    const arrival_date = document.getElementById('modal-stop-arr').value;
    const departure_date = document.getElementById('modal-stop-dep').value;
    const allocated_budget = document.getElementById('modal-stop-budget').value;
    const notes = document.getElementById('modal-stop-notes').value.trim();

    const res = await apiFetch(`/api/trips/${tripId}/stops/add/`, {
      method: 'POST',
      body: JSON.stringify({ city_id, arrival_date, departure_date, allocated_budget, notes })
    });

    if (res && res.success) {
      showToast(res.message);
      closeGenericModal();
      loadItineraryBuilder(tripId);
    }
  });
}

// Modal for Adding Activity to Stop
async function openAddActivityModal(stopId, cityId) {
  const modal = document.getElementById('generic-modal');
  if (!modal) return;

  // Fetch activities for this city
  const cityActivities = state.activities.filter(a => a.city_id === cityId);

  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Assign Activity to Stop</h3>
        <span class="modal-close-btn" onclick="closeGenericModal()">✕</span>
      </div>
      <form id="add-activity-form">
        <div class="form-group">
          <label class="form-label">Select from Curated City Activities</label>
          <select class="form-control" id="modal-act-select" onchange="handleActivitySelectChange(this.value)">
            <option value="">-- Custom Activity / Pick Curated --</option>
            ${cityActivities.map(a => `<option value="${a.id}" data-cost="${a.estimated_cost}" data-title="${a.title}">★ ${a.rating} - ${a.title} ($${a.estimated_cost})</option>`).join('')}
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Activity Title</label>
          <input type="text" class="form-control" id="modal-act-title" placeholder="e.g. Sunset Boat Tour" required />
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">Day Number (1, 2, 3...)</label>
            <input type="number" class="form-control" id="modal-act-day" value="1" min="1" required />
          </div>
          <div class="form-group">
            <label class="form-label">Estimated Cost ($)</label>
            <input type="number" class="form-control" id="modal-act-cost" value="45" min="0" step="5" required />
          </div>
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">Start Time</label>
            <input type="text" class="form-control" id="modal-act-start" value="10:00 AM" required />
          </div>
          <div class="form-group">
            <label class="form-label">End Time</label>
            <input type="text" class="form-control" id="modal-act-end" value="12:30 PM" required />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Category</label>
          <select class="form-control" id="modal-act-cat">
            <option value="activity">Activity / Sightseeing</option>
            <option value="meal">Food & Dining</option>
            <option value="transport">Transportation</option>
            <option value="stay">Accommodation</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div style="display:flex; justify-content:flex-end; gap:1rem; margin-top:1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeGenericModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">+ Assign to Schedule</button>
        </div>
      </form>
    </div>
  `;
  modal.classList.add('active');

  document.getElementById('add-activity-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const activity_id = document.getElementById('modal-act-select').value || null;
    const title = document.getElementById('modal-act-title').value.trim();
    const day_number = document.getElementById('modal-act-day').value;
    const cost = document.getElementById('modal-act-cost').value;
    const start_time = document.getElementById('modal-act-start').value;
    const end_time = document.getElementById('modal-act-end').value;
    const category = document.getElementById('modal-act-cat').value;

    const res = await apiFetch(`/api/stops/${stopId}/items/add/`, {
      method: 'POST',
      body: JSON.stringify({ activity_id, title, day_number, cost, start_time, end_time, category })
    });

    if (res && res.success) {
      showToast('Activity added!');
      closeGenericModal();
      loadItineraryBuilder(res.trip.id);
    }
  });
}

function handleActivitySelectChange(actId) {
  if (!actId) return;
  const act = state.activities.find(a => a.id == actId);
  if (act) {
    document.getElementById('modal-act-title').value = act.title;
    document.getElementById('modal-act-cost').value = act.estimated_cost;
  }
}

async function deleteStop(stopId) {
  if (!confirm('Are you sure you want to delete this entire section/stop?')) return;
  const res = await apiFetch(`/api/stops/${stopId}/delete/`, { method: 'POST' });
  if (res && res.success) {
    showToast('Stop removed');
    loadItineraryBuilder(res.trip.id);
  }
}

async function deleteItineraryItem(itemId) {
  const res = await apiFetch(`/api/items/${itemId}/delete/`, { method: 'POST' });
  if (res && res.success) {
    showToast('Activity removed');
    loadItineraryBuilder(res.trip.id);
  }
}

function closeGenericModal() {
  const modal = document.getElementById('generic-modal');
  if (modal) modal.classList.remove('active');
}

// --- Screen 6: User Trip Listing (My Trips - Odoo Wireframe Screen 6) --- //
async function loadMyTrips(filterStatus = 'all') {
  const container = document.getElementById('my-trips-container');
  if (!container) return;

  const res = await apiFetch(`/api/trips/?status=${filterStatus}`);
  const trips = (res && res.trips) || [];
  const counts = (res && res.counts) || { all: 0, ongoing: 0, upcoming: 0, completed: 0 };

  container.innerHTML = `
    <!-- Top Filter Bar -->
    <div class="filter-search-toolbar">
      <div class="search-input-group">
        <span>🔍</span>
        <input type="text" placeholder="Search my trips..." onkeyup="handleMyTripsSearch(this.value)" />
      </div>
      <div class="toolbar-select-group">
        <select class="custom-select" onchange="sortMyTrips(this.value)">
          <option value="start_date">Sort by: Travel Date</option>
          <option value="created_at">Sort by: Recently Created</option>
          <option value="budget">Sort by: Highest Budget</option>
        </select>
        <button class="btn btn-primary btn-sm" onclick="navigateTo('create-trip')">+ Plan a Trip</button>
      </div>
    </div>

    <!-- Tabs Nav (Ongoing, Up-coming, Completed) -->
    <div class="trip-tabs-nav">
      <button class="trip-tab-btn ${filterStatus === 'all' ? 'active' : ''}" onclick="loadMyTrips('all')">
        All Trips <span class="tab-badge-count">${counts.all}</span>
      </button>
      <button class="trip-tab-btn ${filterStatus === 'ongoing' ? 'active' : ''}" onclick="loadMyTrips('ongoing')">
        Ongoing <span class="tab-badge-count">${counts.ongoing}</span>
      </button>
      <button class="trip-tab-btn ${filterStatus === 'upcoming' ? 'active' : ''}" onclick="loadMyTrips('upcoming')">
        Up-coming <span class="tab-badge-count">${counts.upcoming}</span>
      </button>
      <button class="trip-tab-btn ${filterStatus === 'completed' ? 'active' : ''}" onclick="loadMyTrips('completed')">
        Completed <span class="tab-badge-count">${counts.completed}</span>
      </button>
    </div>

    <!-- Trips List View (Odoo Wireframe Screen 6) -->
    <div id="my-trips-list">
      ${trips.length === 0 ? `
        <div class="glass-panel" style="padding:4rem; text-align:center;">
          <h3>No Trips Found</h3>
          <p style="color:var(--text-secondary); margin:0.75rem 0 1.5rem;">Start designing your personalized itinerary today!</p>
          <button class="btn btn-primary" onclick="navigateTo('create-trip')">+ Create New Trip</button>
        </div>
      ` : trips.map(trip => renderMyTripRow(trip)).join('')}
    </div>
  `;
}

function renderMyTripRow(trip) {
  return `
    <div class="trip-list-row">
      <img class="trip-list-img" src="${trip.cover_image}" alt="${trip.title}" />
      <div>
        <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
          <span class="badge badge-status-${trip.status}">${trip.status_display}</span>
          <span style="font-size:0.85rem; color:var(--text-muted);">${trip.start_date} → ${trip.end_date} (${trip.duration_days} Days)</span>
        </div>
        <h3 style="font-size:1.3rem; margin-bottom:0.35rem;">${trip.title}</h3>
        <p style="font-size:0.88rem; color:var(--primary); font-weight:600; margin-bottom:0.5rem;">
          📍 ${trip.destinations_summary}
        </p>
        <p style="font-size:0.85rem; color:var(--text-secondary); display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">
          ${trip.description}
        </p>
      </div>

      <div style="display:flex; flex-direction:column; align-items:flex-end; gap:0.75rem;">
        <div style="text-align:right;">
          <div style="font-size:0.75rem; color:var(--text-muted); text-transform:uppercase;">Allocated Budget</div>
          <div style="font-size:1.25rem; font-weight:800; color:var(--emerald);">${formatMoney(trip.total_budget)}</div>
        </div>
        <div style="display:flex; gap:0.35rem; flex-wrap:wrap;">
          <button class="btn btn-primary btn-sm" onclick="window.location.hash='itinerary-${trip.id}'">View</button>
          <button class="btn btn-secondary btn-sm" onclick="window.location.hash='builder-${trip.id}'">Stops</button>
          <button class="btn btn-outline btn-sm" onclick="openBoardingPassModal(${trip.id})" title="Luxury Boarding Pass">🎫 Pass</button>
          <button class="btn btn-outline btn-sm" onclick="openEcoScoreModal(${trip.id})" title="Carbon Eco Score">🌱 Eco</button>
          <button class="btn btn-outline btn-sm" onclick="window.location.hash='packing-${trip.id}'" title="Packing List">🎒 Pack</button>
          <button class="btn btn-icon" onclick="openShareModal(${trip.id})" title="Share">🔗</button>
          <button class="btn btn-icon" onclick="deleteTrip(${trip.id})" style="color:var(--rose);" title="Delete">🗑️</button>
        </div>
      </div>
    </div>
  `;
}

async function deleteTrip(tripId) {
  if (!confirm('Are you sure you want to delete this trip and all its itinerary data?')) return;
  const res = await apiFetch(`/api/trips/${tripId}/delete/`, { method: 'POST' });
  if (res && res.success) {
    showToast('Trip deleted');
    loadMyTrips();
  }
}

// --- Screen 7: User Profile Screen (Odoo Wireframe Screen 7) --- //
async function loadUserProfile() {
  const container = document.getElementById('profile-container');
  if (!container) return;

  const authRes = await apiFetch('/api/auth/me/');
  if (!authRes || !authRes.authenticated) {
    openAuthModal('login');
    return;
  }
  const user = authRes.user;

  const [tripsRes, savedRes] = await Promise.all([
    apiFetch('/api/trips/'),
    apiFetch('/api/destinations/saved/')
  ]);

  const trips = (tripsRes && tripsRes.trips) || [];
  const preplannedTrips = trips.filter(t => t.status === 'upcoming' || t.status === 'ongoing');
  const previousTrips = trips.filter(t => t.status === 'completed');
  const savedDestinations = (savedRes && savedRes.saved_destinations) || [];

  container.innerHTML = `
    <div style="max-width:1080px; margin:0 auto;">
      <!-- Profile Header Card (Wireframe Screen 7) -->
      <div class="glass-panel" style="padding:2.5rem; margin-bottom:2.5rem; display:grid; grid-template-columns:140px 1fr auto; gap:2rem; align-items:center;">
        <img src="${user.avatar_url}" alt="${user.username}" style="width:130px; height:130px; border-radius:50%; object-fit:cover; border:3px solid var(--primary);" />
        <div>
          <h1 style="font-size:2.2rem; margin-bottom:0.25rem;">${user.first_name} ${user.last_name}</h1>
          <p style="color:var(--primary); font-weight:600; font-size:0.95rem; margin-bottom:0.5rem;">@${user.username} • 📍 ${user.city || 'Global Traveler'}, ${user.country || 'Earth'}</p>
          <p style="color:var(--text-secondary); font-size:0.92rem; max-width:650px;">${user.bio || 'Wanderer exploring global wonders.'}</p>
        </div>
        <button class="btn btn-secondary" onclick="openEditProfileModal()">✏️ Edit Profile</button>
      </div>

      <!-- Preplanned Trips (Wireframe Screen 7) -->
      <div class="section-header-row">
        <div class="section-title-group">
          <h2><span>🗺️</span> Preplanned Trips</h2>
          <p class="section-subtitle">Upcoming and active adventures ready to embark</p>
        </div>
        <button class="btn btn-primary btn-sm" onclick="navigateTo('create-trip')">+ Plan New Trip</button>
      </div>
      <div class="trips-grid-3" style="margin-bottom:3rem;">
        ${preplannedTrips.length === 0 ? `
          <div style="grid-column:1/-1; padding:2rem; text-align:center; color:var(--text-secondary);" class="glass-panel">
            No upcoming trips planned. Click "+ Plan New Trip" to get started.
          </div>
        ` : preplannedTrips.map(t => renderTripCard(t)).join('')}
      </div>

      <!-- Previous Trips (Wireframe Screen 7) -->
      <div class="section-header-row">
        <div class="section-title-group">
          <h2><span>📜</span> Previous Trips</h2>
          <p class="section-subtitle">Completed memories and past itineraries</p>
        </div>
      </div>
      <div class="trips-grid-3" style="margin-bottom:3rem;">
        ${previousTrips.length === 0 ? `
          <div style="grid-column:1/-1; padding:2rem; text-align:center; color:var(--text-secondary);" class="glass-panel">
            No completed trips yet.
          </div>
        ` : previousTrips.map(t => renderTripCard(t)).join('')}
      </div>

      <!-- Wishlist / Saved Destinations -->
      <div class="section-header-row">
        <div class="section-title-group">
          <h2><span>❤️</span> Saved Destinations Wishlist</h2>
          <p class="section-subtitle">Cities and regions saved for future exploration</p>
        </div>
      </div>
      <div class="cards-grid-4">
        ${savedDestinations.map(c => renderCityCard(c)).join('')}
      </div>
    </div>
  `;
}

function openEditProfileModal() {
  const modal = document.getElementById('generic-modal');
  if (!modal) return;
  const user = state.currentUser;

  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Edit Profile Information</h3>
        <span class="modal-close-btn" onclick="closeGenericModal()">✕</span>
      </div>
      <form id="edit-profile-form">
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">First Name</label>
            <input type="text" class="form-control" id="prof-firstname" value="${user.first_name || ''}" />
          </div>
          <div class="form-group">
            <label class="form-label">Last Name</label>
            <input type="text" class="form-control" id="prof-lastname" value="${user.last_name || ''}" />
          </div>
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">City</label>
            <input type="text" class="form-control" id="prof-city" value="${user.city || ''}" />
          </div>
          <div class="form-group">
            <label class="form-label">Country</label>
            <input type="text" class="form-control" id="prof-country" value="${user.country || ''}" />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Phone Number</label>
          <input type="text" class="form-control" id="prof-phone" value="${user.phone_number || ''}" />
        </div>
        <div class="form-group">
          <label class="form-label">Avatar Image URL</label>
          <input type="url" class="form-control" id="prof-avatar" value="${user.avatar_url || ''}" />
        </div>
        <div class="form-group">
          <label class="form-label">Bio / Additional Details</label>
          <textarea class="form-control" id="prof-bio">${user.bio || ''}</textarea>
        </div>
        <div style="display:flex; justify-content:flex-end; gap:1rem; margin-top:1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeGenericModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Save Changes</button>
        </div>
      </form>
    </div>
  `;
  modal.classList.add('active');

  document.getElementById('edit-profile-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      first_name: document.getElementById('prof-firstname').value.trim(),
      last_name: document.getElementById('prof-lastname').value.trim(),
      city: document.getElementById('prof-city').value.trim(),
      country: document.getElementById('prof-country').value.trim(),
      phone_number: document.getElementById('prof-phone').value.trim(),
      avatar_url: document.getElementById('prof-avatar').value.trim(),
      bio: document.getElementById('prof-bio').value.trim(),
    };

    const res = await apiFetch('/api/auth/profile/update/', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res && res.success) {
      showToast('Profile updated!');
      closeGenericModal();
      await checkAuth();
      loadUserProfile();
    }
  });
}

// --- Screen 8: City Search & Activity Search Page (Odoo Wireframe Screen 8) --- //
async function loadCitySearch() {
  const container = document.getElementById('city-search-container');
  if (!container) return;

  const citiesRes = await apiFetch('/api/cities/');
  const cities = (citiesRes && citiesRes.cities) || [];

  container.innerHTML = `
    <!-- Search & Filter Bar -->
    <div class="filter-search-toolbar">
      <div class="search-input-group">
        <span>🔍</span>
        <input type="text" id="city-search-input" placeholder="Search cities, countries, or sights..." onkeyup="filterCitiesList()" />
      </div>
      <div class="toolbar-select-group">
        <select class="custom-select" id="city-region-filter" onchange="filterCitiesList()">
          <option value="all">Group by: All Regions</option>
          ${state.regions.map(r => `<option value="${r.id}">${r.name}</option>`).join('')}
        </select>
        <select class="custom-select" id="city-cost-filter" onchange="filterCitiesList()">
          <option value="all">Filter: Any Cost</option>
          <option value="$">Budget ($)</option>
          <option value="$$">Moderate ($$)</option>
          <option value="$$$">Luxury ($$$)</option>
        </select>
        <select class="custom-select" id="city-sort-filter" onchange="filterCitiesList()">
          <option value="popularity">Sort: Most Popular</option>
          <option value="cost_asc">Sort: Lowest Cost/Day</option>
          <option value="cost_desc">Sort: Highest Cost/Day</option>
          <option value="name">Sort: Alphabetical</option>
        </select>
      </div>
    </div>

    <!-- Cities Grid -->
    <div class="cards-grid-4" id="cities-explore-grid">
      ${cities.map(c => renderCityCard(c)).join('')}
    </div>
  `;
}

async function filterCitiesList() {
  const q = document.getElementById('city-search-input').value;
  const region = document.getElementById('city-region-filter').value;
  const cost = document.getElementById('city-cost-filter').value;
  const sort = document.getElementById('city-sort-filter').value;

  const res = await apiFetch(`/api/cities/?q=${encodeURIComponent(q)}&region=${region}&cost_index=${cost}&sort=${sort}`);
  const grid = document.getElementById('cities-explore-grid');
  if (grid && res && res.cities) {
    grid.innerHTML = res.cities.map(c => renderCityCard(c)).join('');
  }
}

async function openCityModal(cityId) {
  const modal = document.getElementById('generic-modal');
  if (!modal) return;

  const city = await apiFetch(`/api/cities/${cityId}/`);
  if (!city) return;

  modal.innerHTML = `
    <div class="modal-box" style="max-width:720px;">
      <div class="modal-header">
        <h2 class="modal-title">${city.flag_emoji} ${city.name}, ${city.country}</h2>
        <span class="modal-close-btn" onclick="closeGenericModal()">✕</span>
      </div>
      <img src="${city.image_url}" alt="${city.name}" style="width:100%; height:240px; border-radius:var(--radius-lg); object-fit:cover; margin-bottom:1.5rem;" />
      
      <div style="display:flex; gap:0.6rem; margin-bottom:1rem; flex-wrap:wrap;">
        <span class="badge badge-cost">Cost Index: ${city.cost_index}</span>
        <span class="badge badge-pop">★ ${city.popularity_score} Popularity</span>
        <span class="badge badge-category">Region: ${city.region}</span>
        <span class="badge" style="background:rgba(16,185,129,0.2); color:#34D399;">Avg. $${city.avg_daily_cost}/day</span>
      </div>

      <p style="color:var(--text-secondary); line-height:1.7; margin-bottom:1.5rem;">${city.description}</p>
      <div style="font-size:0.88rem; color:var(--text-muted); margin-bottom:1.5rem;">
        <b>Best Time to Visit:</b> ${city.best_time_to_visit} • <b>Climate:</b> ${city.climate_tag}
      </div>

      <h3 style="font-size:1.15rem; margin-bottom:0.75rem;">Top Curated Activities (${city.activities.length})</h3>
      <div style="display:flex; flex-direction:column; gap:0.75rem; max-height:220px; overflow-y:auto; margin-bottom:1.5rem;">
        ${city.activities.map(a => `
          <div style="display:flex; align-items:center; justify-content:space-between; padding:0.75rem 1rem; background:var(--bg-surface-elevated); border-radius:var(--radius-md);">
            <div>
              <div style="font-weight:600; font-size:0.9rem;">${a.title}</div>
              <div style="font-size:0.8rem; color:var(--text-muted);">${a.category} • ${a.duration_hours} hrs</div>
            </div>
            <div style="font-weight:700; color:var(--emerald);">$${a.estimated_cost}</div>
          </div>
        `).join('')}
      </div>

      <div style="display:flex; justify-content:flex-end; gap:1rem;">
        <button class="btn btn-outline" onclick="toggleSaveDestination(${city.id})">❤️ Save to Wishlist</button>
        <button class="btn btn-primary" onclick="closeGenericModal(); navigateTo('create-trip');">Plan Trip to ${city.name}</button>
      </div>
    </div>
  `;
  modal.classList.add('active');
}

async function toggleSaveDestination(cityId) {
  const res = await apiFetch('/api/destinations/toggle-save/', {
    method: 'POST',
    body: JSON.stringify({ city_id: cityId })
  });
  if (res && res.success) {
    showToast(res.message);
  }
}

// Activity Search Screen (Screen 8)
async function loadActivitySearch() {
  const container = document.getElementById('activity-search-container');
  if (!container) return;

  const res = await apiFetch('/api/activities/');
  const activities = (res && res.activities) || [];
  const categories = (res && res.categories) || [];

  container.innerHTML = `
    <!-- Top Filter Bar -->
    <div class="filter-search-toolbar">
      <div class="search-input-group">
        <span>🔍</span>
        <input type="text" id="act-search-input" placeholder="Search experiences, tours, or sports..." onkeyup="filterActivitiesList()" />
      </div>
      <div class="toolbar-select-group">
        <select class="custom-select" id="act-city-filter" onchange="filterActivitiesList()">
          <option value="all">Group by: All Cities</option>
          ${state.cities.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
        </select>
        <select class="custom-select" id="act-cat-filter" onchange="filterActivitiesList()">
          <option value="all">Filter: All Categories</option>
          ${categories.map(cat => `<option value="${cat.slug}">${cat.name}</option>`).join('')}
        </select>
        <select class="custom-select" id="act-sort-filter" onchange="filterActivitiesList()">
          <option value="rating">Sort: Top Rated</option>
          <option value="cost_asc">Sort: Price (Low to High)</option>
          <option value="cost_desc">Sort: Price (High to Low)</option>
        </select>
      </div>
    </div>

    <!-- Activities Grid -->
    <div class="cards-grid-4" id="activities-explore-grid">
      ${activities.map(a => renderActivityCard(a)).join('')}
    </div>
  `;
}

function renderActivityCard(act) {
  return `
    <div class="glass-panel glass-card-interactive" style="overflow:hidden; display:flex; flex-direction:column;">
      <div style="position:relative; height:180px;">
        <img src="${act.image_url}" alt="${act.title}" style="width:100%; height:100%; object-fit:cover;" />
        <span class="badge" style="position:absolute; top:1rem; left:1rem; background:rgba(0,0,0,0.6); color:#FFF;">
          ★ ${act.rating}
        </span>
        <span class="badge badge-category" style="position:absolute; top:1rem; right:1rem;">
          ${act.category_name}
        </span>
      </div>
      <div style="padding:1.25rem; display:flex; flex-direction:column; flex:1;">
        <div style="font-size:0.8rem; color:var(--primary); font-weight:600; margin-bottom:0.25rem;">📍 ${act.city_name}</div>
        <h3 style="font-size:1.15rem; margin-bottom:0.5rem;">${act.title}</h3>
        <p style="font-size:0.84rem; color:var(--text-secondary); margin-bottom:1rem; flex:1; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">
          ${act.description}
        </p>
        <div style="display:flex; align-items:center; justify-content:space-between; border-top:1px solid var(--border-subtle); padding-top:0.75rem;">
          <div>
            <span style="font-size:0.75rem; color:var(--text-muted);">Cost: </span>
            <span style="font-weight:700; color:var(--emerald); font-size:1.1rem;">$${act.estimated_cost}</span>
          </div>
          <button class="btn btn-primary btn-sm" onclick="openDirectAddActivityModal(${act.id})">+ Add to Trip</button>
        </div>
      </div>
    </div>
  `;
}

async function filterActivitiesList() {
  const q = document.getElementById('act-search-input').value;
  const city = document.getElementById('act-city-filter').value;
  const category = document.getElementById('act-cat-filter').value;
  const sort = document.getElementById('act-sort-filter').value;

  const res = await apiFetch(`/api/activities/?q=${encodeURIComponent(q)}&city=${city}&category=${category}&sort=${sort}`);
  const grid = document.getElementById('activities-explore-grid');
  if (grid && res && res.activities) {
    grid.innerHTML = res.activities.map(a => renderActivityCard(a)).join('');
  }
}

function openDirectAddActivityModal(actId) {
  const modal = document.getElementById('generic-modal');
  if (!modal) return;
  const act = state.activities.find(a => a.id == actId);
  if (!act) return;

  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Add "${act.title}" to a Trip</h3>
        <span class="modal-close-btn" onclick="closeGenericModal()">✕</span>
      </div>
      <p style="color:var(--text-secondary); margin-bottom:1.5rem;">Select which of your ongoing or upcoming trips you'd like to assign this activity to.</p>
      
      <div style="display:flex; flex-direction:column; gap:0.75rem;">
        <button class="btn btn-primary" onclick="closeGenericModal(); navigateTo('create-trip');">
          + Start a New Trip for ${act.city_name}
        </button>
        <button class="btn btn-secondary" onclick="closeGenericModal(); navigateTo('my-trips');">
          Browse Existing Trips to Assign
        </button>
      </div>
    </div>
  `;
  modal.classList.add('active');
}

// --- Screen 9: Itinerary View Screen with Budget Section (Odoo Wireframe Screen 9) --- //
async function loadItineraryView(tripId) {
  const container = document.getElementById('itinerary-view-container');
  if (!container) return;

  const trip = await apiFetch(`/api/trips/${tripId}/`);
  if (!trip || trip.error) {
    showToast('Failed to load itinerary', 'error');
    navigateTo('my-trips');
    return;
  }
  state.currentTripDetail = trip;

  // Flatten days across all stops
  const dayGroups = {};
  for (let d = 1; d <= trip.duration_days; d++) {
    dayGroups[d] = {
      day: d,
      city: 'Travel Day',
      items: [],
      totalExpense: 0
    };
  }

  trip.stops.forEach(stop => {
    stop.items.forEach(item => {
      if (dayGroups[item.day_number]) {
        dayGroups[item.day_number].city = stop.city_name;
        dayGroups[item.day_number].items.push(item);
        dayGroups[item.day_number].totalExpense += item.cost;
      }
    });
  });

  container.innerHTML = `
    <div style="max-width:1080px; margin:0 auto;">
      <!-- Hero Header -->
      <div class="itinerary-view-header">
        <div class="itinerary-hero-info">
          <div style="display:flex; gap:0.5rem; margin-bottom:0.5rem;">
            <span class="badge badge-status-${trip.status}">${trip.status_display}</span>
            <span class="badge" style="background:rgba(99,102,241,0.2); color:#A5B4FC;">${trip.destinations_count} Stops</span>
          </div>
          <h1>${trip.title}</h1>
          <p style="color:var(--primary); font-weight:600; font-size:1.1rem; margin-bottom:0.5rem;">
            📍 ${trip.destinations_summary}
          </p>
          <p style="color:var(--text-secondary); max-width:650px;">${trip.description}</p>
        </div>

        <div style="display:flex; flex-direction:column; align-items:flex-end; gap:0.75rem;">
          <div style="text-align:right;">
            <div style="font-size:0.8rem; color:var(--text-muted);">TOTAL SPENT / BUDGET</div>
            <div style="font-size:1.65rem; font-weight:800; color:var(--emerald);">
              ${formatMoney(trip.total_spent)} <span style="font-size:1rem; color:var(--text-muted);">/ ${formatMoney(trip.total_budget)}</span>
            </div>
          </div>
          <div style="display:flex; gap:0.4rem; flex-wrap:wrap;">
            <button class="btn btn-outline btn-sm" onclick="openBoardingPassModal(${trip.id})">🎫 Boarding Pass</button>
            <button class="btn btn-outline btn-sm" onclick="openEcoScoreModal(${trip.id})">🌱 Eco Score</button>
            <button class="btn btn-outline btn-sm" onclick="window.location.hash='packing-${trip.id}'">🎒 Packing List</button>
            <button class="btn btn-outline btn-sm" onclick="window.location.hash='budget-${trip.id}'">💰 Financial View</button>
            <button class="btn btn-secondary btn-sm" onclick="window.location.hash='builder-${trip.id}'">✏️ Edit Builder</button>
            <button class="btn btn-primary btn-sm" onclick="openShareModal(${trip.id})">🔗 Share</button>
          </div>
        </div>
      </div>

      <!-- Wireframe Screen 9: Day 1, Day 2 Physical Activity Flow with Expense -->
      <div class="section-header-row">
        <div class="section-title-group">
          <h2><span>🗓️</span> Day-by-Day Activity Schedule & Expenses</h2>
          <p class="section-subtitle">Interactive schedule flow with live completion check-offs</p>
        </div>
      </div>

      <div class="day-timeline-container">
        ${Object.values(dayGroups).map(g => renderDayBlock(g, trip.id)).join('')}
      </div>
    </div>
  `;
}

function renderDayBlock(dayGroup, tripId) {
  return `
    <div class="day-block-card">
      <div class="day-block-header">
        <div class="day-title-badge">
          <span style="background:var(--primary); color:#FFF; padding:0.25rem 0.75rem; border-radius:var(--radius-full); font-size:0.85rem;">Day ${dayGroup.day}</span>
          <span>${dayGroup.city}</span>
        </div>
        <div style="font-weight:700; color:var(--emerald);">
          Day Cost: $${dayGroup.totalExpense.toFixed(2)}
        </div>
      </div>

      <div class="day-activities-timeline">
        ${dayGroup.items.length === 0 ? `
          <div style="padding:1.5rem; text-align:center; color:var(--text-muted); font-size:0.9rem;">
            Free exploration / Travel day. No scheduled activities.
          </div>
        ` : dayGroup.items.map(item => `
          <div class="timeline-activity-node">
            <input type="checkbox" class="node-checkbox" ${item.is_completed ? 'checked' : ''} onchange="toggleItemCompletion(${item.id}, this)" title="Mark completed" />
            <div class="node-time-box">${item.start_time} - ${item.end_time}</div>
            <div class="node-content-box">
              <div class="node-title ${item.is_completed ? 'completed' : ''}">${item.title}</div>
              ${item.notes ? `<div style="font-size:0.82rem; color:var(--text-muted);">${item.notes}</div>` : ''}
            </div>
            <div class="node-expense-box">$${item.cost}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

async function toggleItemCompletion(itemId, checkbox) {
  const res = await apiFetch(`/api/items/${itemId}/toggle/`, { method: 'POST' });
  if (res && res.success) {
    const parentNode = checkbox.closest('.timeline-activity-node');
    if (parentNode) {
      const titleEl = parentNode.querySelector('.node-title');
      if (titleEl) {
        if (res.is_completed) titleEl.classList.add('completed');
        else titleEl.classList.remove('completed');
      }
    }
  }
}

// --- Screen 9 (Cont.): Trip Budget & Cost Breakdown Screen --- //
async function loadBudgetScreen(tripId) {
  const container = document.getElementById('budget-container');
  if (!container) return;

  const budget = await apiFetch(`/api/trips/${tripId}/budget/`);
  if (!budget) return;
  state.currentTripBudget = budget;

  container.innerHTML = `
    <div style="max-width:1080px; margin:0 auto;">
      <!-- Header -->
      <div class="glass-panel" style="padding:1.75rem; margin-bottom:2rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
        <div>
          <button class="btn btn-outline btn-sm" onclick="window.location.hash='itinerary-${tripId}'" style="margin-bottom:0.5rem;">← Back to Itinerary</button>
          <h1 style="font-size:2rem;">Financial Breakdown: ${budget.trip_title}</h1>
          <p style="color:var(--text-secondary); font-size:0.92rem;">Comprehensive expense allocation, pie charts, and daily averages</p>
        </div>
        <button class="btn btn-primary" onclick="openAddExpenseModal(${tripId})">+ Log Direct Expense</button>
      </div>

      <!-- KPI Summary Cards -->
      <div class="kpi-metrics-grid">
        <div class="kpi-card">
          <div class="kpi-icon-box" style="background:rgba(99,102,241,0.2); color:#818CF8;">💰</div>
          <div class="kpi-info">
            <span class="kpi-value">$${budget.total_budget}</span>
            <span class="kpi-label">Total Allocated Budget</span>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon-box" style="background:rgba(16,185,129,0.2); color:#34D399;">💳</div>
          <div class="kpi-info">
            <span class="kpi-value">$${budget.total_spent}</span>
            <span class="kpi-label">Actual Spent (${budget.percent_used}%)</span>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon-box" style="background:rgba(245,158,11,0.2); color:#FBBF24;">📊</div>
          <div class="kpi-info">
            <span class="kpi-value">$${budget.avg_cost_per_day}</span>
            <span class="kpi-label">Average Daily Cost</span>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon-box" style="background:${budget.remaining_budget >= 0 ? 'rgba(16,185,129,0.2)' : 'rgba(244,63,94,0.2)'}; color:${budget.remaining_budget >= 0 ? '#34D399' : '#FB7185'};">
            ${budget.remaining_budget >= 0 ? '🛡️' : '⚠️'}
          </div>
          <div class="kpi-info">
            <span class="kpi-value">$${budget.remaining_budget}</span>
            <span class="kpi-label">${budget.remaining_budget >= 0 ? 'Remaining Balance' : 'Over Budget!'}</span>
          </div>
        </div>
      </div>

      <!-- Charts Section (Pie & Bar) -->
      <div class="analytics-charts-grid">
        <div class="chart-card">
          <div class="chart-card-header">
            <h3>Expense Breakdown by Category</h3>
          </div>
          <div class="chart-canvas-wrapper">
            <canvas id="budget-pie-chart"></canvas>
          </div>
        </div>
        <div class="chart-card">
          <div class="chart-card-header">
            <h3>Daily Cost Distribution</h3>
          </div>
          <div class="chart-canvas-wrapper">
            <canvas id="budget-bar-chart"></canvas>
          </div>
        </div>
      </div>

      <!-- Direct Expenses Table -->
      <div class="data-table-container">
        <div class="table-header">
          <h3 style="font-size:1.15rem;">Logged Expenses List (${budget.expenses_list.length})</h3>
          <button class="btn btn-primary btn-sm" onclick="openAddExpenseModal(${tripId})">+ Add Expense</button>
        </div>
        <table class="custom-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Category</th>
              <th>Description</th>
              <th>Amount</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            ${budget.expenses_list.length === 0 ? `
              <tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding:2rem;">No direct expenses logged yet.</td></tr>
            ` : budget.expenses_list.map(exp => `
              <tr>
                <td>${exp.date || 'N/A'}</td>
                <td><span class="badge badge-category">${exp.category_display}</span></td>
                <td>${exp.description}</td>
                <td style="font-weight:700; color:var(--emerald);">$${exp.amount}</td>
                <td><button class="btn btn-icon" onclick="deleteExpense(${exp.id}, ${tripId})" style="width:28px; height:28px; color:var(--rose);">🗑️</button></td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;

  renderBudgetCharts(budget);
}

function renderBudgetCharts(budget) {
  if (typeof Chart === 'undefined') return;

  // Pie Chart
  const pieCtx = document.getElementById('budget-pie-chart');
  if (pieCtx) {
    if (state.charts.budgetPie) state.charts.budgetPie.destroy();
    state.charts.budgetPie = new Chart(pieCtx, {
      type: 'doughnut',
      data: {
        labels: ['Transport', 'Stay / Hotels', 'Activities', 'Meals & Dining', 'Other'],
        datasets: [{
          data: [
            budget.categories.transport,
            budget.categories.stay,
            budget.categories.activities,
            budget.categories.meals,
            budget.categories.other
          ],
          backgroundColor: ['#6366F1', '#10B981', '#F59E0B', '#EC4899', '#8B5CF6'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { color: '#D1D5DB' } }
        }
      }
    });
  }

  // Bar Chart
  const barCtx = document.getElementById('budget-bar-chart');
  if (barCtx) {
    const days = Object.keys(budget.day_costs);
    const costs = Object.values(budget.day_costs);
    if (state.charts.budgetBar) state.charts.budgetBar.destroy();
    state.charts.budgetBar = new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: days.map(d => `Day ${d}`),
        datasets: [{
          label: 'Spent ($)',
          data: costs,
          backgroundColor: '#6366F1',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: '#9CA3AF' }, grid: { display: false } },
          y: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }
}

function openAddExpenseModal(tripId) {
  const modal = document.getElementById('generic-modal');
  if (!modal) return;

  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Log Direct Expense</h3>
        <span class="modal-close-btn" onclick="closeGenericModal()">✕</span>
      </div>
      <form id="add-expense-form">
        <div class="form-group">
          <label class="form-label">Category</label>
          <select class="form-control" id="modal-exp-cat">
            <option value="transport">Transport (Flights, Train, Taxi)</option>
            <option value="stay">Stay / Accommodation</option>
            <option value="activities">Activities & Sightseeing</option>
            <option value="meals">Meals & Food</option>
            <option value="other">Miscellaneous</option>
          </select>
        </div>
        <div class="form-grid-2">
          <div class="form-group">
            <label class="form-label">Amount ($)</label>
            <input type="number" class="form-control" id="modal-exp-amt" value="50" min="1" step="1" required />
          </div>
          <div class="form-group">
            <label class="form-label">Date</label>
            <input type="date" class="form-control" id="modal-exp-date" value="${new Date().toISOString().split('T')[0]}" required />
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Description</label>
          <input type="text" class="form-control" id="modal-exp-desc" placeholder="e.g. Airport Taxi to Montmartre Hotel" required />
        </div>
        <div style="display:flex; justify-content:flex-end; gap:1rem; margin-top:1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeGenericModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Save Expense</button>
        </div>
      </form>
    </div>
  `;
  modal.classList.add('active');

  document.getElementById('add-expense-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const category = document.getElementById('modal-exp-cat').value;
    const amount = document.getElementById('modal-exp-amt').value;
    const date = document.getElementById('modal-exp-date').value;
    const description = document.getElementById('modal-exp-desc').value.trim();

    const res = await apiFetch(`/api/trips/${tripId}/expenses/add/`, {
      method: 'POST',
      body: JSON.stringify({ category, amount, date, description })
    });

    if (res && res.success) {
      showToast('Expense logged!');
      closeGenericModal();
      loadBudgetScreen(tripId);
    }
  });
}

async function deleteExpense(expenseId, tripId) {
  await apiFetch(`/api/expenses/${expenseId}/delete/`, { method: 'POST' });
  showToast('Expense deleted');
  loadBudgetScreen(tripId);
}

// --- Screen 10: Community Tab Screen (Odoo Wireframe Screen 10) --- //
async function loadCommunity() {
  const container = document.getElementById('community-container');
  if (!container) return;

  const res = await apiFetch('/api/community/trips/');
  const trips = (res && res.trips) || [];

  container.innerHTML = `
    <!-- Top Filter Bar -->
    <div class="filter-search-toolbar">
      <div class="search-input-group">
        <span>🔍</span>
        <input type="text" id="community-search-input" placeholder="Search community itineraries, destinations, or authors..." onkeyup="filterCommunityTrips()" />
      </div>
      <div class="toolbar-select-group">
        <select class="custom-select" id="community-sort-filter" onchange="filterCommunityTrips()">
          <option value="popular">Sort: Most Liked & Cloned</option>
          <option value="latest">Sort: Recently Published</option>
          <option value="budget_asc">Sort: Budget (Low to High)</option>
        </select>
      </div>
    </div>

    <!-- Community Header -->
    <div class="section-header-row">
      <div class="section-title-group">
        <h2><span>🌐</span> Global Traveler Community</h2>
        <p class="section-subtitle">Get inspired, read reviews, and clone tested multi-city trips into your account with 1-click</p>
      </div>
    </div>

    <!-- Community Feed Grid (Wireframe Screen 10) -->
    <div class="community-feed-grid" id="community-feed-list">
      ${trips.map(trip => renderCommunityTripCard(trip)).join('')}
    </div>
  `;
}

function renderCommunityTripCard(trip) {
  return `
    <div class="glass-panel" style="overflow:hidden; display:flex; flex-direction:column;">
      <div style="position:relative; height:200px;">
        <img src="${trip.cover_image}" alt="${trip.title}" style="width:100%; height:100%; object-fit:cover;" />
        <div style="position:absolute; top:1rem; left:1rem; right:1rem; display:flex; justify-content:space-between;">
          <span class="badge" style="background:rgba(0,0,0,0.6); color:#FFF;">${trip.duration_days} Days</span>
          <span class="badge badge-cost">$${trip.total_budget} Budget</span>
        </div>
      </div>

      <div style="padding:1.5rem; display:flex; flex-direction:column; flex:1;">
        <div style="display:flex; align-items:center; gap:0.65rem; margin-bottom:0.75rem;">
          <img src="${trip.user.avatar_url}" alt="${trip.user.username}" style="width:28px; height:28px; border-radius:50%; object-fit:cover;" />
          <span style="font-size:0.85rem; font-weight:600; color:var(--text-secondary);">${trip.user.full_name}</span>
        </div>

        <h3 style="font-size:1.3rem; margin-bottom:0.35rem;">${trip.title}</h3>
        <div style="color:var(--primary); font-weight:600; font-size:0.88rem; margin-bottom:0.75rem;">
          📍 ${trip.destinations_summary}
        </div>
        <p style="color:var(--text-secondary); font-size:0.88rem; margin-bottom:1.25rem; flex:1; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden;">
          ${trip.description}
        </p>

        <!-- Social Action Footer (Likes, Comments, Copy Trip) -->
        <div style="display:flex; align-items:center; justify-content:space-between; border-top:1px solid var(--border-subtle); padding-top:1rem;">
          <div style="display:flex; align-items:center; gap:0.75rem;">
            <button class="btn btn-outline btn-sm" onclick="toggleTripLike(${trip.id}, this)">
              ${trip.is_liked ? '❤️' : '🤍'} <span class="like-count">${trip.likes_count}</span>
            </button>
            <button class="btn btn-outline btn-sm" onclick="openTripCommentsModal(${trip.id})">
              💬 ${trip.comments_count || 0}
            </button>
          </div>
          
          <!-- Copy Trip Button (Wireframe Screen 10 / Screen 11) -->
          <button class="btn btn-emerald btn-sm" onclick="cloneTripToMyAccount(${trip.id})">
            <span>📋 Copy Trip</span>
          </button>
        </div>
      </div>
    </div>
  `;
}

async function filterCommunityTrips() {
  const q = document.getElementById('community-search-input').value;
  const sort = document.getElementById('community-sort-filter').value;
  const res = await apiFetch(`/api/community/trips/?q=${encodeURIComponent(q)}&sort=${sort}`);
  const feed = document.getElementById('community-feed-list');
  if (feed && res && res.trips) {
    feed.innerHTML = res.trips.map(t => renderCommunityTripCard(t)).join('');
  }
}

async function toggleTripLike(tripId, btn) {
  const res = await apiFetch(`/api/community/trips/${tripId}/like/`, { method: 'POST' });
  if (res && res.success) {
    btn.innerHTML = `${res.is_liked ? '❤️' : '🤍'} <span class="like-count">${res.likes_count}</span>`;
  }
}

async function cloneTripToMyAccount(tripId) {
  const res = await apiFetch(`/api/trips/${tripId}/clone/`, { method: 'POST' });
  if (res && res.success) {
    showToast('Trip cloned to your My Trips!');
    window.location.hash = `builder-${res.trip.id}`;
  } else {
    showToast(res.error || 'Failed to copy trip', 'error');
  }
}

async function openTripCommentsModal(tripId) {
  const modal = document.getElementById('generic-modal');
  if (!modal) return;

  const res = await apiFetch(`/api/community/trips/${tripId}/comments/`);
  const comments = (res && res.comments) || [];

  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Community Discussions</h3>
        <span class="modal-close-btn" onclick="closeGenericModal()">✕</span>
      </div>

      <div style="display:flex; flex-direction:column; gap:1rem; max-height:280px; overflow-y:auto; margin-bottom:1.5rem;" id="modal-comments-list">
        ${comments.length === 0 ? `
          <div style="text-align:center; color:var(--text-muted); padding:1rem;">Be the first to share your thoughts on this itinerary!</div>
        ` : comments.map(c => `
          <div style="background:var(--bg-surface-elevated); padding:0.85rem 1rem; border-radius:var(--radius-md);">
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.35rem;">
              <img src="${c.user.avatar_url}" alt="${c.user.username}" style="width:22px; height:22px; border-radius:50%;" />
              <span style="font-weight:600; font-size:0.85rem;">${c.user.full_name}</span>
              <span style="font-size:0.75rem; color:var(--text-muted);">${c.created_at}</span>
            </div>
            <p style="font-size:0.88rem; color:var(--text-primary);">${c.comment}</p>
          </div>
        `).join('')}
      </div>

      <form id="add-comment-form">
        <div style="display:flex; gap:0.5rem;">
          <input type="text" class="form-control" id="modal-comment-input" placeholder="Write a comment or tip..." required />
          <button type="submit" class="btn btn-primary">Post</button>
        </div>
      </form>
    </div>
  `;
  modal.classList.add('active');

  document.getElementById('add-comment-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const comment = document.getElementById('modal-comment-input').value.trim();
    if (!comment) return;
    const postRes = await apiFetch(`/api/community/trips/${tripId}/comments/add/`, {
      method: 'POST',
      body: JSON.stringify({ comment })
    });
    if (postRes && postRes.success) {
      document.getElementById('modal-comment-input').value = '';
      openTripCommentsModal(tripId);
    }
  });
}

// --- Screen 11: Calendar View Screen (Odoo Wireframe Screen 11) --- //
async function loadCalendar() {
  const container = document.getElementById('calendar-container');
  if (!container) return;

  const res = await apiFetch('/api/calendar/events/');
  const trips = (res && res.trips) || [];
  const activities = (res && res.activities) || [];

  const currentYear = state.calendarDate.getFullYear();
  const currentMonth = state.calendarDate.getMonth();
  const monthName = state.calendarDate.toLocaleString('default', { month: 'long', year: 'numeric' });

  // Compute days for month grid
  const firstDay = new Date(currentYear, currentMonth, 1).getDay();
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

  let daysHtml = '';
  // Empty offset cells
  for (let i = 0; i < firstDay; i++) {
    daysHtml += `<div class="calendar-cell other-month"></div>`;
  }

  // Days of current month
  for (let day = 1; day <= daysInMonth; day++) {
    const dayStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    
    // Find matching trips and activities for this day
    const dayTrips = trips.filter(t => t.start <= dayStr && t.end >= dayStr);
    const dayActs = activities.filter(a => a.date === dayStr);

    daysHtml += `
      <div class="calendar-cell" onclick="openCalendarDayDetails('${dayStr}', ${JSON.stringify(dayTrips).replace(/"/g, '&quot;')}, ${JSON.stringify(dayActs).replace(/"/g, '&quot;')})">
        <div class="calendar-cell-date">${day}</div>
        ${dayTrips.map(t => `<div class="calendar-event-pill" style="background:${t.color};">${t.title}</div>`).join('')}
        ${dayActs.map(a => `<div class="calendar-event-pill" style="background:rgba(255,255,255,0.1); border-left:3px solid ${a.color};">${a.title}</div>`).join('')}
      </div>
    `;
  }

  container.innerHTML = `
    <div style="max-width:1080px; margin:0 auto;">
      <div class="calendar-wrapper">
        <div class="calendar-header-controls">
          <button class="btn btn-outline btn-sm" onclick="changeCalendarMonth(-1)">← Previous</button>
          <h2 style="font-size:1.75rem;">${monthName}</h2>
          <button class="btn btn-outline btn-sm" onclick="changeCalendarMonth(1)">Next →</button>
        </div>

        <div class="calendar-grid">
          <div class="calendar-day-label">Sun</div>
          <div class="calendar-day-label">Mon</div>
          <div class="calendar-day-label">Tue</div>
          <div class="calendar-day-label">Wed</div>
          <div class="calendar-day-label">Thu</div>
          <div class="calendar-day-label">Fri</div>
          <div class="calendar-day-label">Sat</div>
          ${daysHtml}
        </div>
      </div>
    </div>
  `;
}

function changeCalendarMonth(delta) {
  state.calendarDate.setMonth(state.calendarDate.getMonth() + delta);
  loadCalendar();
}

function openCalendarDayDetails(dayStr, dayTrips, dayActs) {
  const modal = document.getElementById('generic-modal');
  if (!modal) return;

  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Schedule for ${dayStr}</h3>
        <span class="modal-close-btn" onclick="closeGenericModal()">✕</span>
      </div>
      
      <div style="margin-bottom:1.5rem;">
        <h4 style="font-size:1rem; color:var(--primary); margin-bottom:0.5rem;">Active Trips:</h4>
        ${dayTrips.length === 0 ? '<p style="color:var(--text-muted); font-size:0.85rem;">No active trips on this date.</p>' : dayTrips.map(t => `
          <div style="padding:0.75rem; background:var(--bg-surface-elevated); border-radius:var(--radius-md); margin-bottom:0.5rem; display:flex; justify-content:space-between; align-items:center;">
            <b>${t.title}</b>
            <button class="btn btn-primary btn-sm" onclick="closeGenericModal(); window.location.hash='itinerary-${t.trip_id}';">Open Itinerary</button>
          </div>
        `).join('')}
      </div>

      <div>
        <h4 style="font-size:1rem; color:var(--emerald); margin-bottom:0.5rem;">Scheduled Activities & Times:</h4>
        ${dayActs.length === 0 ? '<p style="color:var(--text-muted); font-size:0.85rem;">No activities scheduled on this day.</p>' : dayActs.map(a => `
          <div style="padding:0.75rem; background:var(--bg-surface); border-radius:var(--radius-md); margin-bottom:0.5rem; display:flex; justify-content:space-between;">
            <div>
              <div style="font-weight:600;">${a.title}</div>
              <div style="font-size:0.8rem; color:var(--text-muted);">${a.start_time} - ${a.end_time}</div>
            </div>
            <div style="font-weight:700; color:var(--emerald);">$${a.cost}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
  modal.classList.add('active');
}

// --- Screen 12: Admin & Analytics Panel (Odoo Wireframe Screen 12) --- //
async function loadAdminAnalytics() {
  const container = document.getElementById('analytics-container');
  if (!container) return;

  const res = await apiFetch('/api/admin/analytics/');
  if (!res) return;
  const m = res.metrics;

  container.innerHTML = `
    <div style="max-width:1180px; margin:0 auto;">
      <!-- Header -->
      <div class="section-header-row">
        <div class="section-title-group">
          <h2><span>📊</span> Admin Insights & Travel Analytics</h2>
          <p class="section-subtitle">Platform adoption metrics, destination trends, and budget volume distribution</p>
        </div>
        <button class="btn btn-primary btn-sm" onclick="loadAdminAnalytics()">🔄 Refresh Metrics</button>
      </div>

      <!-- KPI Metrics Row -->
      <div class="kpi-metrics-grid">
        <div class="kpi-card">
          <div class="kpi-icon-box" style="background:rgba(99,102,241,0.2); color:#818CF8;">👥</div>
          <div class="kpi-info">
            <span class="kpi-value">${m.total_users}</span>
            <span class="kpi-label">Registered Travelers</span>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon-box" style="background:rgba(16,185,129,0.2); color:#34D399;">🗺️</div>
          <div class="kpi-info">
            <span class="kpi-value">${m.total_trips}</span>
            <span class="kpi-label">Total Itineraries Created</span>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon-box" style="background:rgba(245,158,11,0.2); color:#FBBF24;">📍</div>
          <div class="kpi-info">
            <span class="kpi-value">${m.total_stops}</span>
            <span class="kpi-label">Destination Stops</span>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon-box" style="background:rgba(236,72,153,0.2); color:#F472B6;">💵</div>
          <div class="kpi-info">
            <span class="kpi-value">$${m.total_budget_volume.toLocaleString()}</span>
            <span class="kpi-label">Budget Volume Planned</span>
          </div>
        </div>
      </div>

      <!-- Analytics Charts (Wireframe Screen 12: Pie, Line, Bar) -->
      <div class="analytics-charts-grid">
        <div class="chart-card">
          <div class="chart-card-header">
            <h3>Trip Status Breakdown</h3>
          </div>
          <div class="chart-canvas-wrapper">
            <canvas id="admin-status-chart"></canvas>
          </div>
        </div>
        <div class="chart-card">
          <div class="chart-card-header">
            <h3>Platform Category Spending Volume</h3>
          </div>
          <div class="chart-canvas-wrapper">
            <canvas id="admin-category-chart"></canvas>
          </div>
        </div>
      </div>

      <!-- Top Cities & Recent Travelers Table -->
      <div class="data-table-container">
        <div class="table-header">
          <h3 style="font-size:1.15rem;">Top Visited Cities in Itineraries</h3>
        </div>
        <table class="custom-table">
          <thead>
            <tr>
              <th>City</th>
              <th>Country</th>
              <th>Itinerary Inclusion Count</th>
              <th>Avg. Daily Cost</th>
            </tr>
          </thead>
          <tbody>
            ${res.top_cities.map(c => `
              <tr>
                <td><b>${c.flag_emoji} ${c.name}</b></td>
                <td>${c.country}</td>
                <td><span class="badge badge-pop">${c.visits} Itineraries</span></td>
                <td style="font-weight:700; color:var(--emerald);">$${c.avg_daily_cost}/day</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;

  renderAdminCharts(res);
}

function renderAdminCharts(data) {
  if (typeof Chart === 'undefined') return;

  const statusCtx = document.getElementById('admin-status-chart');
  if (statusCtx) {
    if (state.charts.adminStatus) state.charts.adminStatus.destroy();
    state.charts.adminStatus = new Chart(statusCtx, {
      type: 'doughnut',
      data: {
        labels: ['Ongoing', 'Upcoming', 'Completed', 'Draft'],
        datasets: [{
          data: [
            data.status_counts.ongoing,
            data.status_counts.upcoming,
            data.status_counts.completed,
            data.status_counts.draft
          ],
          backgroundColor: ['#10B981', '#6366F1', '#9CA3AF', '#F59E0B'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { color: '#D1D5DB' } } }
      }
    });
  }

  const catCtx = document.getElementById('admin-category-chart');
  if (catCtx) {
    if (state.charts.adminCategory) state.charts.adminCategory.destroy();
    state.charts.adminCategory = new Chart(catCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(data.category_totals),
        datasets: [{
          label: 'Total Volume ($)',
          data: Object.values(data.category_totals),
          backgroundColor: '#8B5CF6',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { ticks: { color: '#9CA3AF' }, grid: { display: false } },
          y: { ticks: { color: '#9CA3AF' }, grid: { color: 'rgba(255,255,255,0.05)' } }
        },
        plugins: { legend: { display: false } }
      }
    });
  }
}

// --- Screen 13: Share Modal --- //
function openShareModal(tripId) {
  const modal = document.getElementById('generic-modal');
  if (!modal) return;

  const shareUrl = `${window.location.origin}/trip/share/${tripId}/`;

  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Share Public Itinerary</h3>
        <span class="modal-close-btn" onclick="closeGenericModal()">✕</span>
      </div>
      <p style="color:var(--text-secondary); margin-bottom:1.5rem;">
        Anyone with this link can view the read-only itinerary schedule and copy it to their personal GlobeTrotter account.
      </p>
      
      <div class="form-group">
        <label class="form-label">Shareable Link</label>
        <div style="display:flex; gap:0.5rem;">
          <input type="text" class="form-control" value="${shareUrl}" id="share-link-input" readonly />
          <button class="btn btn-primary" onclick="copyShareLink()">Copy</button>
        </div>
      </div>

      <div style="margin-top:2rem; padding-top:1.5rem; border-top:1px solid var(--border-subtle); display:flex; justify-content:space-between; align-items:center;">
        <span style="font-size:0.85rem; color:var(--text-muted);">Share on social channels:</span>
        <div style="display:flex; gap:0.5rem;">
          <a href="https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}&text=Check%20out%20my%20travel%20itinerary!" target="_blank" class="btn btn-outline btn-sm">Twitter / X</a>
          <a href="https://api.whatsapp.com/send?text=${encodeURIComponent('Check out my itinerary: ' + shareUrl)}" target="_blank" class="btn btn-outline btn-sm">WhatsApp</a>
        </div>
      </div>
    </div>
  `;
  modal.classList.add('active');
}

function copyShareLink() {
  const input = document.getElementById('share-link-input');
  if (input) {
    input.select();
    navigator.clipboard.writeText(input.value);
    showToast('Link copied to clipboard!');
  }
}

// ==========================================================================
// High-Class Innovation 1: AI Smart Travel Concierge & Generator
// ==========================================================================
function loadAiConcierge() {
  const container = document.getElementById('ai-concierge-container');
  if (!container) return;

  const personas = [
    { id: 'luxury_gourmet', icon: '🍷', title: 'Luxury Gourmet', desc: 'Michelin-starred dining, private sommelier tastings, and 5-star heritage suites.' },
    { id: 'romantic', icon: '✨', title: 'Romantic Getaway', desc: 'Sunset caldera cruises, candlelit dinners, and secluded scenic viewpoints.' },
    { id: 'adventure', icon: '⛰️', title: 'Extreme Adventure', desc: 'Sunrise volcano treks, high-altitude alpine trails, and coastal safari expeditions.' },
    { id: 'cultural', icon: '⛩️', title: 'Culture & Heritage', desc: 'Ancient Buddhist shrines, classical tea ceremonies, and VIP museum access.' },
    { id: 'budget_explorer', icon: '🎒', title: 'Backpacker Trek', desc: 'Authentic street food stalls, scenic trains, and hidden cultural hubs.' },
    { id: 'family', icon: '🎡', title: 'Family Magic', desc: 'Interactive theme parks, seaside promenades, and kid-friendly discoveries.' }
  ];

  container.innerHTML = `
    <div style="max-width:1120px; margin:0 auto;">
      <!-- Hero Header -->
      <div class="glass-panel" style="padding:2.5rem; margin-bottom:2.5rem; background:linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(139,92,246,0.1) 100%);">
        <div style="display:inline-flex; align-items:center; gap:0.5rem; padding:0.35rem 0.85rem; border-radius:var(--radius-full); background:rgba(139,92,246,0.2); border:1px solid rgba(139,92,246,0.4); color:#C4B5FD; font-size:0.85rem; font-weight:700; margin-bottom:1rem;">
          <span>⚡</span> Intelligent Travel AI Concierge
        </div>
        <h1 style="font-size:2.6rem; margin-bottom:0.75rem;">Design Your Ultimate Itinerary in Seconds</h1>
        <p style="color:var(--text-secondary); font-size:1.05rem; max-width:750px;">
          Choose your travel persona and preferences. Our AI Concierge automatically optimizes city stops, day-by-day activities, estimated expenses, and transit connections.
        </p>
      </div>

      <!-- Step 1: Traveler Persona Selection -->
      <div class="section-header-row">
        <div class="section-title-group">
          <h2><span>🎭</span> Step 1: Select Traveler Persona</h2>
        </div>
      </div>
      <div class="persona-cards-grid">
        ${personas.map(p => `
          <div class="persona-card ${state.selectedAiPersona === p.id ? 'selected' : ''}" onclick="selectAiPersona('${p.id}', this)">
            <div class="persona-icon">${p.icon}</div>
            <div class="persona-title">${p.title}</div>
            <div class="persona-desc">${p.desc}</div>
          </div>
        `).join('')}
      </div>

      <!-- Step 2: Trip Parameters -->
      <div class="glass-panel" style="padding:2rem; margin-bottom:2.5rem;">
        <h3 style="font-size:1.25rem; margin-bottom:1.5rem;"><span>⚙️</span> Step 2: Configure Journey Parameters</h3>
        <form id="ai-generator-form">
          <div class="form-grid-2">
            <div class="form-group">
              <label class="form-label">Preferred Region</label>
              <select class="form-control" id="ai-region-select">
                <option value="all">Any Region (Global Highlights)</option>
                ${state.regions.map(r => `<option value="${r.id}">${r.name}</option>`).join('')}
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Budget Tier</label>
              <select class="form-control" id="ai-budget-level">
                <option value="luxury">Luxury & VIP ($350/day)</option>
                <option value="moderate" selected>Comfort & Style ($160/day)</option>
                <option value="budget">Smart Backpacker ($80/day)</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" style="display:flex; justify-content:space-between;">
              <span>Trip Duration (Days): <b id="ai-days-label" style="color:var(--primary);">7 Days</b></span>
            </label>
            <input type="range" id="ai-days-range" min="3" max="14" value="7" style="width:100%; accent-color:var(--primary);" oninput="document.getElementById('ai-days-label').innerText = this.value + ' Days'" />
          </div>

          <div style="display:flex; justify-content:flex-end; margin-top:2rem;">
            <button type="submit" class="btn btn-primary btn-lg" id="btn-generate-ai">
              <span>✨ Generate AI Itinerary</span>
            </button>
          </div>
        </form>
      </div>

      <!-- Step 3: Live Generation Result Container -->
      <div id="ai-result-panel" style="display:none;"></div>
    </div>
  `;

  document.getElementById('ai-generator-form').addEventListener('submit', handleAiGenerate);
}

function selectAiPersona(personaId, card) {
  state.selectedAiPersona = personaId;
  document.querySelectorAll('.persona-card').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
}

async function handleAiGenerate(e) {
  e.preventDefault();
  const btn = document.getElementById('btn-generate-ai');
  btn.innerHTML = '<span>⚡ Analyzing Global Routes & Generating...</span>';
  btn.disabled = true;

  const payload = {
    persona: state.selectedAiPersona,
    region_id: document.getElementById('ai-region-select').value,
    budget_level: document.getElementById('ai-budget-level').value,
    days: parseInt(document.getElementById('ai-days-range').value),
    auto_save: false
  };

  const res = await apiFetch('/api/ai/generate-itinerary/', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  btn.innerHTML = '<span>✨ Generate AI Itinerary</span>';
  btn.disabled = false;

  if (res && res.success) {
    state.generatedAiTrip = res;
    renderAiGeneratedResult(res);
  }
}

function renderAiGeneratedResult(trip) {
  const panel = document.getElementById('ai-result-panel');
  if (!panel) return;
  panel.style.display = 'block';

  panel.innerHTML = `
    <div class="glass-panel" style="padding:2.5rem; margin-bottom:3rem; border:2px solid var(--border-highlight);">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1.5rem; margin-bottom:2rem;">
        <div>
          <span class="badge" style="background:var(--grad-primary); color:#FFF; margin-bottom:0.5rem;">AI Generated Blueprint</span>
          <h2 style="font-size:2.2rem;">${trip.title}</h2>
          <p style="color:var(--text-secondary); font-size:1rem; margin-top:0.4rem;">
            📅 ${trip.days} Days • Total Estimated Budget: <b style="color:var(--emerald); font-size:1.2rem;">${formatMoney(trip.total_budget)}</b>
          </p>
        </div>
        <button class="btn btn-emerald btn-lg" onclick="saveAiTripToAccount()" id="btn-save-ai-trip">
          <span>💾 1-Click Save to My Trips</span>
        </button>
      </div>

      <!-- Stops & Day-by-Day Schedule -->
      <div class="stops-builder-container">
        ${trip.stops.map((stop, s_idx) => `
          <div class="stop-section-block">
            <div class="stop-section-header">
              <div class="stop-section-title">
                <span>${stop.flag_emoji} Stop #${s_idx + 1}: ${stop.city_name}, ${stop.country_name} (${stop.duration_days} Days)</span>
              </div>
              <span class="badge badge-cost">Allocated: ${formatMoney(stop.allocated_budget)}</span>
            </div>

            <div class="stop-activities-list">
              ${stop.items.map(item => `
                <div class="stop-activity-row">
                  <div style="display:flex; align-items:center; gap:0.75rem;">
                    <span class="badge badge-category">Day ${item.day_number}</span>
                    <span style="font-weight:600;">${item.title}</span>
                    <span style="font-size:0.8rem; color:var(--text-muted);">(${item.start_time} - ${item.end_time})</span>
                  </div>
                  <span style="font-weight:700; color:var(--emerald);">${formatMoney(item.cost)}</span>
                </div>
              `).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  panel.scrollIntoView({ behavior: 'smooth' });
}

async function saveAiTripToAccount() {
  if (!state.generatedAiTrip) return;
  const btn = document.getElementById('btn-save-ai-trip');
  if (btn) btn.disabled = true;

  const payload = {
    persona: state.selectedAiPersona,
    region_id: document.getElementById('ai-region-select').value,
    budget_level: document.getElementById('ai-budget-level').value,
    days: state.generatedAiTrip.days,
    auto_save: true
  };

  const res = await apiFetch('/api/ai/generate-itinerary/', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  if (res && res.saved_trip_id) {
    showToast('AI Itinerary saved to My Trips!');
    window.location.hash = `itinerary-${res.saved_trip_id}`;
  } else {
    showToast('Failed to save trip', 'error');
  }
}

// ==========================================================================
// High-Class Innovation 2: Interactive Live World Map (Leaflet)
// ==========================================================================
async function loadRouteMap() {
  const container = document.getElementById('route-map-container');
  if (!container) return;

  const [citiesRes, tripsRes] = await Promise.all([
    apiFetch('/api/cities/'),
    apiFetch('/api/trips/')
  ]);

  const cities = (citiesRes && citiesRes.cities) || [];
  const trips = (tripsRes && tripsRes.trips) || [];

  container.innerHTML = `
    <div style="max-width:1200px; margin:0 auto;">
      <div class="section-header-row">
        <div class="section-title-group">
          <h2><span>🗺️</span> Global Geospatial Route Explorer</h2>
          <p class="section-subtitle">Interactive 3D Dark Map with animated flight trajectories and city hubs</p>
        </div>
        <div style="display:flex; gap:0.5rem;">
          <select class="custom-select" id="map-trip-select" onchange="highlightTripOnMap(this.value)">
            <option value="all">Show All 16+ Global Hubs</option>
            ${trips.map(t => `<option value="${t.id}">✈️ Trajectory: ${t.title}</option>`).join('')}
          </select>
        </div>
      </div>

      <!-- Map Container -->
      <div class="map-panel-container">
        <div id="leaflet-world-map"></div>
      </div>
    </div>
  `;

  // Initialize Leaflet
  setTimeout(() => {
    if (typeof L === 'undefined') return;
    
    if (state.leafletMap) {
      state.leafletMap.remove();
      state.leafletMap = null;
    }

    const map = L.map('leaflet-world-map', {
      center: [25.0, 10.0],
      zoom: 2.5,
      minZoom: 2,
      maxZoom: 18
    });

    // Dark Basemap CartoDB
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19
    }).addTo(map);

    state.leafletMap = map;
    state.mapMarkers = [];
    state.mapPolylines = [];

    // Add glowing circular pins for cities
    cities.forEach(city => {
      if (city.latitude || city.longitude) {
        const marker = L.circleMarker([city.latitude || 48.8566, city.longitude || 2.3522], {
          radius: 8,
          fillColor: '#6366F1',
          color: '#A5B4FC',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8
        }).addTo(map);

        marker.bindPopup(`
          <div style="text-align:center; min-width:180px;">
            <img src="${city.image_url}" style="width:100%; height:90px; object-fit:cover; border-radius:6px; margin-bottom:0.5rem;" />
            <h4 style="font-size:1.05rem; margin-bottom:0.2rem;">${city.flag_emoji || '📍'} ${city.name}</h4>
            <div style="font-size:0.8rem; color:#A5B4FC; margin-bottom:0.5rem;">${city.country} • ~${formatMoney(city.avg_daily_cost)}/day</div>
            <button class="btn btn-primary btn-sm" style="width:100%; font-size:0.75rem;" onclick="openCityModal(${city.id})">Explore Details</button>
          </div>
        `);

        state.mapMarkers.push({ cityId: city.id, marker });
      }
    });

    // Draw active flight routes for existing trips
    trips.forEach(t => {
      if (t.stops && t.stops.length > 1) {
        const latlngs = [];
        t.stops.forEach(s => {
          const c = cities.find(ci => ci.id === s.city_id);
          if (c && c.latitude) latlngs.push([c.latitude, c.longitude]);
        });
        if (latlngs.length > 1) {
          const polyline = L.polyline(latlngs, {
            color: '#10B981',
            weight: 3,
            dashArray: '6, 8',
            opacity: 0.7
          }).addTo(map);
          state.mapPolylines.push({ tripId: t.id, polyline });
        }
      }
    });
  }, 100);
}

function highlightTripOnMap(tripId) {
  if (!state.leafletMap) return;
  if (tripId === 'all') {
    state.leafletMap.setView([25.0, 10.0], 2.5);
  } else {
    const found = state.mapPolylines.find(p => p.tripId == tripId);
    if (found) {
      state.leafletMap.fitBounds(found.polyline.getBounds(), { padding: [50, 50] });
    }
  }
}

// ==========================================================================
// High-Class Innovation 3: Carbon Footprint & Eco Scorecard
// ==========================================================================
async function openEcoScoreModal(tripId) {
  const modal = document.getElementById('generic-modal');
  if (!modal) return;

  const res = await apiFetch(`/api/trips/${tripId}/eco/`);
  if (!res) return;

  modal.innerHTML = `
    <div class="modal-box" style="max-width:680px;">
      <div class="modal-header">
        <h3 class="modal-title">🌱 GreenTrotter Sustainability Scorecard</h3>
        <span class="modal-close-btn" onclick="closeGenericModal()">✕</span>
      </div>

      <div style="background:var(--bg-surface-elevated); border-radius:var(--radius-lg); padding:1.75rem; text-align:center; margin-bottom:1.5rem;">
        <div style="font-size:3.5rem; font-weight:900; color:${res.eco_color}; font-family:var(--font-heading);">
          ${res.eco_score}
        </div>
        <div style="font-size:1.1rem; font-weight:700; color:${res.eco_color};">${res.eco_label}</div>
        <p style="color:var(--text-secondary); font-size:0.88rem; margin-top:0.35rem;">
          Total Route Distance: <b>${res.total_distance_km} km</b> (${res.total_distance_miles} miles)
        </p>
      </div>

      <div class="kpi-metrics-grid" style="grid-template-columns:1fr 1fr; margin-bottom:1.5rem;">
        <div class="kpi-card" style="padding:1rem;">
          <div class="kpi-icon-box" style="background:rgba(239,68,68,0.2); color:#F87171;">💨</div>
          <div class="kpi-info">
            <span class="kpi-value" style="font-size:1.35rem;">${res.total_co2_kg} kg</span>
            <span class="kpi-label">CO2 Carbon Emission</span>
          </div>
        </div>
        <div class="kpi-card" style="padding:1rem;">
          <div class="kpi-icon-box" style="background:rgba(16,185,129,0.2); color:#34D399;">🌲</div>
          <div class="kpi-info">
            <span class="kpi-value" style="font-size:1.35rem;">${res.trees_offset_required} Trees</span>
            <span class="kpi-label">Annual Offset Required</span>
          </div>
        </div>
      </div>

      <h4 style="font-size:1rem; margin-bottom:0.5rem;">Eco-Friendly Travel Recommendations:</h4>
      <ul style="padding-left:1.25rem; font-size:0.88rem; color:var(--text-secondary); line-height:1.7; margin-bottom:1.5rem;">
        ${res.green_tips.map(tip => `<li>${tip}</li>`).join('')}
      </ul>

      <div style="display:flex; justify-content:flex-end;">
        <button class="btn btn-primary" onclick="closeGenericModal()">Done</button>
      </div>
    </div>
  `;
  modal.classList.add('active');
}

// ==========================================================================
// High-Class Innovation 4: Smart Packing Assistant
// ==========================================================================
async function loadPackingScreen(tripId) {
  const container = document.getElementById('packing-container');
  if (!container) return;

  const res = await apiFetch(`/api/trips/${tripId}/packing/`);
  if (!res) return;

  container.innerHTML = `
    <div style="max-width:960px; margin:0 auto;">
      <div class="glass-panel" style="padding:2rem; margin-bottom:2rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
        <div>
          <button class="btn btn-outline btn-sm" onclick="window.location.hash='itinerary-${tripId}'" style="margin-bottom:0.5rem;">← Back to Itinerary</button>
          <h1 style="font-size:2.2rem;">🎒 Smart Packing Assistant</h1>
          <p style="color:var(--text-secondary); font-size:0.92rem;">Climate-adaptive checklist dynamically compiled for your trip's weather and activities</p>
        </div>
        <button class="btn btn-primary" onclick="openAddPackingItemModal(${tripId})">+ Add Custom Item</button>
      </div>

      <!-- Packing Progress -->
      <div class="glass-panel" style="padding:1.5rem; margin-bottom:2rem;">
        <div style="display:flex; justify-content:space-between; font-weight:700; font-size:0.95rem;">
          <span>Packing Completion</span>
          <span style="color:var(--emerald);">${res.packed_count} / ${res.total_count} Packed (${res.percent_packed}%)</span>
        </div>
        <div class="packing-progress-bar">
          <div class="packing-progress-fill" style="width:${res.percent_packed}%;"></div>
        </div>
      </div>

      <!-- Categories Accordion -->
      <div>
        ${Object.values(res.categories).map(cat => `
          <div class="packing-category-group">
            <h3 style="font-size:1.15rem; margin-bottom:0.75rem; color:var(--primary);">
              ${cat.title} (${cat.items.filter(i => i.is_packed).length}/${cat.items.length})
            </h3>
            <div>
              ${cat.items.map(item => `
                <div class="packing-item-row">
                  <label class="packing-item-label ${item.is_packed ? 'packed' : ''}">
                    <input type="checkbox" class="node-checkbox" ${item.is_packed ? 'checked' : ''} onchange="togglePackingItem(${item.id}, ${tripId})" />
                    <span>${item.name}</span>
                  </label>
                  <button class="btn btn-icon" onclick="deletePackingItem(${item.id}, ${tripId})" style="width:28px; height:28px; font-size:0.75rem; color:var(--rose);">✕</button>
                </div>
              `).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

async function togglePackingItem(itemId, tripId) {
  await apiFetch(`/api/packing/${itemId}/toggle/`, { method: 'POST' });
  loadPackingScreen(tripId);
}

async function deletePackingItem(itemId, tripId) {
  await apiFetch(`/api/packing/${itemId}/delete/`, { method: 'POST' });
  loadPackingScreen(tripId);
}

function openAddPackingItemModal(tripId) {
  const modal = document.getElementById('generic-modal');
  if (!modal) return;

  modal.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3 class="modal-title">Add Item to Packing List</h3>
        <span class="modal-close-btn" onclick="closeGenericModal()">✕</span>
      </div>
      <form id="add-pack-form">
        <div class="form-group">
          <label class="form-label">Category</label>
          <select class="form-control" id="modal-pack-cat">
            <option value="clothing">Clothing & Apparel</option>
            <option value="electronics">Tech & Electronics</option>
            <option value="documents">Travel Documents & Money</option>
            <option value="toiletries">Health & Toiletries</option>
            <option value="activity_gear">Activity & Adventure Gear</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">Item Name</label>
          <input type="text" class="form-control" id="modal-pack-name" placeholder="e.g. Scuba Goggles or Travel Journal" required />
        </div>
        <div style="display:flex; justify-content:flex-end; gap:1rem; margin-top:1.5rem;">
          <button type="button" class="btn btn-secondary" onclick="closeGenericModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Add Item</button>
        </div>
      </form>
    </div>
  `;
  modal.classList.add('active');

  document.getElementById('add-pack-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('modal-pack-name').value.trim();
    const category = document.getElementById('modal-pack-cat').value;
    const res = await apiFetch(`/api/trips/${tripId}/packing/add/`, {
      method: 'POST',
      body: JSON.stringify({ name, category })
    });
    if (res && res.success) {
      showToast('Item added');
      closeGenericModal();
      loadPackingScreen(tripId);
    }
  });
}

// ==========================================================================
// High-Class Innovation 5: Luxury Digital Boarding Pass & Travel Pass
// ==========================================================================
async function openBoardingPassModal(tripId) {
  const modal = document.getElementById('generic-modal');
  if (!modal) return;

  const trip = await apiFetch(`/api/trips/${tripId}/`);
  if (!trip) return;

  modal.innerHTML = `
    <div class="modal-box" style="max-width:760px; background:transparent; border:none; box-shadow:none; padding:0;">
      <div style="display:flex; justify-content:flex-end; margin-bottom:1rem;">
        <span class="modal-close-btn" onclick="closeGenericModal()" style="background:rgba(0,0,0,0.6); width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center;">✕</span>
      </div>

      <div class="boarding-pass-card">
        <div class="boarding-pass-header">
          <div style="display:flex; align-items:center; gap:0.75rem;">
            <span style="font-size:1.5rem;">✈️</span>
            <div>
              <div style="font-weight:900; letter-spacing:0.1em; font-size:1.15rem;">GLOBETROTTER LUXURY PASS</div>
              <div style="font-size:0.75rem; opacity:0.8;">OFFICIAL TRAVEL ITINERARY & BOARDING CREDENTIAL</div>
            </div>
          </div>
          <span class="badge" style="background:rgba(255,255,255,0.2); color:#FFF; font-size:0.85rem;">PASSENGER: ${trip.user.full_name.toUpperCase()}</span>
        </div>

        <div class="boarding-pass-body">
          <div>
            <div style="font-size:0.75rem; color:#A5B4FC; text-transform:uppercase; letter-spacing:0.05em;">JOURNEY ROUTE</div>
            <div style="font-size:1.6rem; font-weight:800; margin-bottom:1rem; font-family:var(--font-heading);">
              ${trip.destinations_summary}
            </div>

            <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:1rem; margin-bottom:1.5rem;">
              <div>
                <div style="font-size:0.7rem; color:#9CA3AF; text-transform:uppercase;">DEPARTURE</div>
                <div style="font-weight:700;">${trip.start_date}</div>
              </div>
              <div>
                <div style="font-size:0.7rem; color:#9CA3AF; text-transform:uppercase;">RETURN</div>
                <div style="font-weight:700;">${trip.end_date}</div>
              </div>
              <div>
                <div style="font-size:0.7rem; color:#9CA3AF; text-transform:uppercase;">DURATION</div>
                <div style="font-weight:700; color:var(--emerald);">${trip.duration_days} Days</div>
              </div>
            </div>

            <div style="font-size:0.75rem; color:#A5B4FC; text-transform:uppercase; margin-bottom:0.4rem;">STOPS & SCHEDULED HIGHLIGHTS</div>
            <div style="display:flex; flex-direction:column; gap:0.4rem; font-size:0.85rem;">
              ${trip.stops.map(s => `
                <div style="display:flex; justify-content:space-between; padding:0.4rem 0.6rem; background:rgba(255,255,255,0.05); border-radius:4px;">
                  <span><b>${s.flag_emoji} ${s.city_name}</b> (${s.duration_days}d)</span>
                  <span style="color:#A5B4FC;">${s.items_count} activities scheduled</span>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Barcode & QR Stamp Visual -->
          <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; border-left:1px solid rgba(255,255,255,0.15); padding-left:1.5rem; text-align:center;">
            <div style="width:110px; height:110px; background:#FFF; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#000; font-weight:900; font-size:0.8rem; box-shadow:0 4px 12px rgba(0,0,0,0.5);">
              [QR CODE]
            </div>
            <div style="font-size:0.75rem; font-family:monospace; margin-top:0.75rem; letter-spacing:0.1em; color:#A5B4FC;">
              GT-${trip.id}-2026
            </div>
          </div>
        </div>

        <div class="boarding-pass-perforation"></div>

        <div style="padding: 0 2rem 1.5rem; display:flex; justify-content:space-between; align-items:center;">
          <div style="font-size:0.8rem; color:#9CA3AF;">Total Budget: <b style="color:var(--emerald);">${formatMoney(trip.total_budget)}</b></div>
          <button class="btn btn-primary btn-sm" onclick="window.print()">🖨️ Print Luxury Travel Pass</button>
        </div>
      </div>
    </div>
  `;
  modal.classList.add('active');
}

