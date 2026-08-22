# 🌍 GlobeTrotter – Next-Gen Personalized Travel Planning & Interactive Global Mapping Platform

**GlobeTrotter** is a comprehensive, production-ready travel planning web application built for the **Odoo LD Hackathon**. It empowers global explorers and roadtrippers to craft multi-city itineraries, visualize sequential GPS routes on interactive multi-layer Leaflet maps, manage travel budgets with real-time currency conversion (INR `₹`, USD `$`, EUR `€`), schedule activities on full-featured calendars, and share journeys with a live travel community.

---

## 📸 Core Features & Highlights

### 1. 🗺️ Real-Time Interactive Global Mapping System (`/map/`)
- **Multi-Tile Switcher**: Switch dynamically between **CartoDB Voyager (Streets)**, **OpenStreetMap Standard**, and **Esri World Imagery (High-Res Satellite / Terrain)** without reloading.
- **Custom Pulsing SVG Marker Pins**: Sequence-numbered markers (`1, 2, 3...`) with glowing radar aura animations and custom route color coding per journey.
- **Sequential Route Polylines**: Auto-drawn dashed route lines connecting consecutive stops of each journey with hover tooltips and interactive click handlers.
- **Browser Geolocation API ("My Location")**: Instant GPS location finder with a pulsing blue beacon and smooth animated map fly-to.
- **Live Search & Filter Overlay**: Real-time filtering by travel status (`Planning`, `In Progress`, `Completed`), journey selector dropdown, "My Trips Only" toggle, and keyword search.
- **Slide-Over Detail Drawer**: Interactive sidebar displaying destination cover photos, arrival/departure dates, hotel stays, transit modes, expense breakdowns, and scheduled activity timelines.

### 2. 🧳 Multi-City Itinerary Builder & Visual Timeline
- **Sequential Stop Management**: Define destination sequences with arrival and departure dates, hotel accommodations, transit modes (Flights, Vande Bharat Trains, Buses, Cabs, Shikaras), and costs.
- **Scheduled Activities**: Add activities per stop with start times, duration in minutes, locations, entry fees, notes, and completion toggles.
- **Interactive Stop Pills**: Quick-jump stop pills (`[1] Srinagar`, `[2] Gulmarg`, `[3] Manali`) that pan the Leaflet map and trigger popup cards.
- **Export & Print**: Integrated PDF export and print-friendly itinerary formatting.

### 3. 💰 Dynamic Financial Snapshot & Budget Engine (`/trips/<id>/budget/`)
- **Real-Time Cost Categorization**: Automated calculation of stays, transportation, sightseeing activities, meals, shopping, and miscellaneous expenses.
- **Interactive Donut Chart**: Rendered with **Chart.js** with localized currency formatting (`₹`, `$`, `€`).
- **Expense Receipt Logger**: Form-validated receipt entries with instant budget impact calculation and CSRF-protected receipt deletion.

### 4. 🗓️ FullCalendar Schedule Visualizer (`/trips/<id>/calendar/`)
- Interactive **FullCalendar 6** day/week/month timeline with color-coded event chips for city stays, sightseeing tours, and culinary experiences.
- Bootstrap modal popup displaying event names, categories, and scheduled timestamps on click.

### 5. 🏔️ Destination & Experience Catalog (`/cities/` & `/activities/`)
- Curated Indian destinations (Kashmir Valleys, Himachal Passes, Vibrant Gujarat, Royal Rajasthan) and international capitals.
- **City Detail Interactive Map**: Pinned city centers and categorized nearby sights (Trekking, Heritage, Food, Lakes, Culture).
- **Interactive Bucket List / Wishlist**: One-click async toggle API with heart animations.

### 6. 👥 Live Community, Social Sharing & 1-Click Itinerary Cloning
- **Public Share Permalinks**: Unique share URLs (`/trips/share/<slug>/`) with social sharing buttons for WhatsApp and X (Twitter).
- **1-Click Itinerary Cloning**: Clone any public itinerary into your account with automatic 14-day date recalculation.
- **Live Community Stream (`/community/`)**: Real-time polling activity feed, ratings, reviews, and discussion threads.

### 7. 🛡️ Administrator Command Center (`/admin-dashboard/`)
- Superuser analytics, platform-wide revenue graphs, total active trips, destination counts, and recent activity monitoring.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Backend Framework** | Python 3.13 / Django 5.x (MTV Architecture) |
| **Database** | SQLite3 (Pre-seeded with 22+ trips, cities, activities, and expenses) |
| **Frontend Styling** | Vanilla CSS Theme System (`static/css/style.css`), Bootstrap 5.3, FontAwesome 6 |
| **Typography** | Google Fonts (**Outfit** for Headings, **Plus Jakarta Sans** for Body) |
| **Interactive Mapping** | Leaflet.js 1.9.4 (CartoDB, OpenStreetMap, Esri Satellite, Geolocation API) |
| **Data Visualizations** | Chart.js 4.x (Dynamic Donut & Analytics Charts) |
| **Calendar Engine** | FullCalendar 6.1.15 |

---

## 📂 Project Directory Structure

```
d:\odoo_ld_hackthon\
├── accounts/                  # User Authentication, Profiles, Wishlists & Roles
│   ├── models.py              # UserProfile, WishlistItem models
│   ├── views.py               # Login, Register, Profile, Wishlist views
│   └── forms.py               # Auth & Profile forms with password validation
├── analytics/                 # Activity Logging & Admin Command Center
│   ├── models.py              # ActivityLog model
│   └── views.py               # Admin Dashboard & Live Feed API
├── destinations/              # Cities, Countries & Experience Catalog
│   ├── models.py              # Country, City (with GPS decimal lat/lng), Activity
│   └── views.py               # City search, City detail map, Activity catalog
├── globetrotter_core/         # Django Core Configuration & Root URLconf
│   ├── settings.py            # Settings, installed apps, static/media config
│   └── urls.py                # Main URL routing table
├── static/                    # Static Assets
│   ├── css/
│   │   └── style.css          # Next-Gen CSS Design System & Responsive Tokens
│   └── js/
│       ├── global_map.js      # Full-Screen Interactive Global Mapping Engine
│       ├── map_view.js        # Embedded Itinerary & City Route Map Engine
│       ├── budget_charts.js   # Chart.js Budget Donut & Breakdown Engine
│       └── live_feed.js       # Live Community Polling & Notification Engine
├── templates/                 # Modular Django HTML Templates
│   ├── base.html              # Core Layout, Sticky Navbar & Footer
│   ├── accounts/              # Login, Register, Profile, Wishlist templates
│   ├── dashboard/             # Home Dashboard template (home.html)
│   ├── destinations/          # City Explorer, City Detail Map, Activities templates
│   └── trips/                 # Global Map, Itinerary Builder, Timeline, Budget, Calendar
├── scratch/                   # Automated End-to-End Verification Test Suites
│   ├── verify_mapping_system.py # Test suite for Leaflet mapping & Locations API
│   └── verify_all_pages.py      # Full platform regression & form test suite
├── db.sqlite3                 # Seeded SQLite Database
├── manage.py                  # Django Management CLI
└── requirements.txt           # Python Dependencies
```

---

## 🚀 Step-by-Step: How to Run the Project

### 1. Open Terminal & Enter Directory
```powershell
cd d:\odoo_ld_hackthon
```

### 2. Install Required Python Packages
```powershell
pip install -r requirements.txt
```

### 3. Apply Migrations *(Optional / Already Configured)*
```powershell
python manage.py migrate
```

### 4. Start the Django Local Development Server
```powershell
python manage.py runserver
```

Open your browser and navigate to: **`http://127.0.0.1:8000/`**

---

## 🔑 Pre-Configured Demo Accounts

Log in at **`http://127.0.0.1:8000/login/`** using either of the following accounts:

| Role | Username / Email | Password | Permissions & Capabilities |
| :--- | :--- | :--- | :--- |
| **👑 Platform Admin** | `admin` / `admin@globetrotter.com` | `Admin@12345` | Full access to Admin Command Center (`/admin-dashboard/`), Django Admin (`/admin/`), and builder access across all platform trips. |
| **🎒 Active Traveler** | `traveler` / `traveler@globetrotter.com` | `Traveler@12345` | Personal Trip Builder, Wishlist, Budget Expense Logger, and Live Community reviews. |

*(A quick **"Fill Traveler"** shortcut button is also available directly on the login page for one-click login).*

---

## 🌐 Complete URL & Endpoint Directory

### 🗺️ Real-Time Mapping & Exploration
| Route | Method | Description |
| :--- | :--- | :--- |
| `/map/` or `/trips/map/` | `GET` | **Interactive Global Travel Map** with multi-tile switching, pulsing pins, Geolocation GPS, and slide-over destination drawer. |
| `/trips/api/locations/` | `GET` | **REST Locations API** returning sequential GPS stops, coordinates, cost estimates, and scheduled activities. |
| `/cities/` | `GET` | Multi-state and city explorer with budget, continent, and keyword filters. |
| `/cities/<slug>/` | `GET` | City guide with coordinates, weather, and interactive destination map. |
| `/activities/` | `GET` | Experience and activity catalog with category filtering. |

### 🧳 Trip Management & Planning
| Route | Method | Description |
| :--- | :--- | :--- |
| `/dashboard/` | `GET` | Central traveler dashboard with active trips, quick stats, and metrics. |
| `/trips/` | `GET` | My Trips itinerary management list. |
| `/trips/new/` | `GET, POST` | Create a new trip itinerary with form validation. |
| `/trips/<id>/builder/` | `GET` | Drag-and-drop itinerary builder with live budget ticker bar. |
| `/trips/<id>/view/` | `GET` | Chronological visual timeline with embedded multi-city route map. |
| `/trips/<id>/budget/` | `GET, POST` | Budget analytics, Chart.js donut chart, and receipt expense logger. |
| `/trips/<id>/calendar/` | `GET` | Interactive FullCalendar 6 schedule view with modal event popups. |
| `/trips/share/<slug>/` | `GET` | Public shared itinerary view with WhatsApp and X sharing. |
| `/trips/<id>/copy/` | `GET` | 1-click clone itinerary with 14-day date recalculation. |

### 👥 Community & Analytics
| Route | Method | Description |
| :--- | :--- | :--- |
| `/community/` | `GET` | Live community feed, reviews, ratings, and shared trips. |
| `/api/live-feed/` | `GET` | Real-time JSON activity feed stream for live polling. |
| `/api/wishlist/toggle/<id>/` | `POST` | Asynchronous bucket list toggle API. |
| `/trips/<id>/like/` | `POST` | Asynchronous trip like toggle API. |
| `/admin-dashboard/` | `GET` | Administrative analytics and platform management dashboard. |

---

## 🧪 Automated Testing & Verification

The codebase includes automated test suites covering all pages, permissions, GPS locations, and budget calculations:

```powershell
# 1. Run Interactive Global Mapping & Locations API Test Suite
python scratch/verify_mapping_system.py

# 2. Run Full Platform Regression Test Suite (All 22 Trips, Forms, APIs, & Dashboards)
python scratch/verify_all_pages.py
```

**Verification Results**: `100% PASS (0 Failures across all endpoints)`.

---

## 📄 License & Attribution
- Built for the **Odoo LD Hackathon 2026**.
- Open source under the **MIT License**.
