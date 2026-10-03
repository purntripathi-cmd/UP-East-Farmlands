# 🌾 UP East & Varanasi Farmlands Intelligence Platform

An institutional-grade agricultural land discovery, due diligence, and agronomic intelligence web application exclusively dedicated to **Varanasi (Kashi / Banaras)** and surrounding Eastern Uttar Pradesh (Purvanchal) districts: **Chandauli, Mirzapur, Jaunpur, Ghazipur, Bhadohi (Sant Ravidas Nagar), Azamgarh, Prayagraj fringe, Sonbhadra, Mau, and border zones (Buxar / Kaimur)**.

---

## 🌟 Key Features

### 1. Concentric Radial Distance Analysis
Filter farmland estates by concentric buffers radiating outward from Varanasi:
- 🟢 **Within 20 km Buffer:** Urban peripheral fringe, Ring Road Phase 1 & 2, Babatpur, Rohania, Sarnath, Shivpur, Chitaipur, Harahua, Ramnagar.
- 🟡 **20 to 40 km Buffer:** Chandauli Sadar, Mughalsarai / DDU, Sakaldiha, Aurai, Mirzapur border.
- 🔵 **40 to 60 km Buffer:** Mirzapur proper, Jaunpur proper, Bhadohi / Gyanpur, Ghazipur border, Chunar.
- 🟣 **60 to 80 km Buffer:** Ghazipur proper, Zamania, Saidpur, Robertsganj / Sonbhadra approach, Azamgarh border.
- 🟤 **80 to 100 km Buffer:** Azamgarh proper, Prayagraj eastern fringe, Mau, Ballia border, Kaimur border.
- 🌐 **Extended 200 km Regional Buffer:** Strategic regional agro-corridors.

### 2. Selectable Origin Benchmark Landmark (Default: Kacheri Varanasi near Varuna Pul)
- **Default Zero-Point:** **Kacheri Varanasi near Varuna Pul** (Collectorate & District Courts: Lat `25.3375`, Lng `82.9815`).
- Dynamically recalculates:
  - **Estimated Actual Driving Road Distance (km)** via regional highway and arterial network coefficients.
  - **Driving Travel Time** (hours & minutes).
  - One-click **Google Maps Turn-by-Turn Navigation** deep link.
  - One-click **Google Maps Satellite Search** pin link.
- Alternative selectable landmarks: *LBS International Airport (Babatpur - VNS)*, *Varanasi Cantt (BSB)*, *Kashi Vishwanath Dham*, *Banaras Station (Manduadih - BSBS)*, *BHU Lanka*, *Pt. DDU Jn (Mughalsarai)*, *Sarnath Archaeological Complex*, and *Ring Road Phase 2 Harahua Junction*.

### 3. Interactive Google Maps Satellite & Hybrid View
- **High-Resolution Google Maps Tiles:**
  - `Google Maps Satellite (Hybrid)`: High-res satellite imagery overlaid with road vectors and village labels.
  - `Google Maps Streets / Roadmap`: Road hierarchy and connectivity.
  - `Google Maps Terrain`: Elevation contours and drainage geography.
  - `Google Maps Satellite (Pure)`: Unadulterated remote sensing view.
- Visual overlays:
  - Concentric translucent buffer rings (20 km, 40 km, 60 km, 80 km, 100 km) centered on the active origin landmark.
  - Custom pins color-coded by **Due Diligence Grade** (A+ Sovereign, A Institutional, B Market Standard, or Starred Favorites).
  - Interactive popups with direct turn-by-turn driving directions and WhatsApp contact triggers.

### 4. ⭐ Persistent Favorites & Shortlist System
- Star or unstar any parcel with a single click (`☆ Add to Favorites` / `★ Favorited`).
- Automatically synced to local persistent storage (`data/user_favorites.json`) across sessions.
- Dedicated **"Shortlisted Favorites Matrix"** view for side-by-side financial, soil pH, water TDS, and legal comparisons.
- Instant toggle to filter the entire app to show only favorited properties.
- One-click export of favorited properties to Excel / CSV.

### 5. 📰 Published News, E-Paper Provenance & Verification
Every farmland parcel contains verified public publication data:
- **Publication Headline:** e.g., *NH-19 to Ring Road Phase 2 Agri Zone Notification*, *UP Bhulekh Section 34 Mutation Clearance*, *SBI SARFAESI Recovery E-Auction*.
- **Platform / Source:** *Dainik Jagran Varanasi Edition*, *Amar Ujala Kashi*, *Live Hindustan Purvanchal*, *UP Bhulekh Revenue Gazette*, *State Bank of India SARB*, *Bank of Baroda E-Auction Bulletin*.
- **Publication Date & Legal Notice Type:** 30-day title caveat notices, SARFAESI bank auctions, or PM-KUSUM solar tubewell gazettes.
- **Direct Verification Link:** Clickable URL to verify original records on state revenue and e-auction portals.

### 6. 🤖 Weekly AI/ML Spectral & Provenance Scanner
- Automated background engine with SQLite state checkpointing (`data/up_east_farmland_state.db`).
- **Sentinel-2 Multispectral NDVI Engine:** Calculates vegetative vigour index from simulated Band 8 (NIR) and Band 4 (Red) reflectance.
- **MESSIS / AgriFieldNet Crop Classifier:** Classifies parcel suitability for *Certified Sandalwood (Chandan)*, *VNR Bihi Giant Guava*, *Hass Avocado*, *Banarasi Langra Mango*, *Dragonfruit*, *Organic Floriculture*, and *Kala Namak Scented Rice*.
- Groundwater salinity categorization (Sweet water < 300 ppm vs brackish).
- Rate-limiting simulation with exponential backoff and jitter.
- Interactive **"⚡ Run Weekly AI/ML Scan Now"** trigger in the UI with live progress indicators.

### 7. 🛡️ 100-Point Institutional Due Diligence & Purvanchal Land Units
- Detailed 100-point audit covering UP Bhulekh 12-column Khatauni, SARFAESI bank clearance, 12-year Barah Sala (Encumbrance Certificate), Dakhil-Kharij (Mutation) status, and pakka bitumen road frontage.
- Regional land measurement converter:
  - **Pakka Bigha** (1 Acre = 1.60 Pakka Bigha in Varanasi & Purvanchal = 27,225 sq.ft / Bigha)
  - **Biswa** (20 Biswa per Pakka Bigha)
  - **Kattha & Dhur** (for Bihar border districts like Buxar & Kaimur)
  - **Hectares, Acres, Square Metres, Square Feet**

### 8. 📥 Multi-Sheet Excel & Master CSV Exporter
- **Multi-Sheet Excel Workbook (.xlsx):**
  - Sheet 1: `All Farmlands (UP East)` (all 44 columns)
  - Sheet 2: `⭐ Shortlisted Favorites`
  - Sheet 3: `📰 Published Media & Legal`
  - Sheet 4: `🛰️ Weekly AI-ML Spectral`
- **Master CSV Export (.csv):** UTF-8 encoded for GIS and data science pipelines.

---

## 🏗️ Architecture & Directory Structure

```
UP-East-Farmlands/
│
├── app.py                      # Main Streamlit web application
├── requirements.txt            # Python dependencies (Streamlit, Folium, Pandas, Openpyxl, Pytest)
├── README.md                   # Comprehensive documentation
├── .gitignore                  # Git ignore rules
│
├── .streamlit/
│   └── config.toml             # Institutional dark theme configuration
│
├── data/
│   ├── up_east_farmlands.json  # Master dataset of 112+ verified parcels across all rings
│   ├── benchmarks.json         # Reference landmarks (Kacheri Varanasi, Airport, Cantt, BHU, etc.)
│   ├── user_favorites.json     # Persistent storage for user favorited parcel IDs
│   ├── up_east_farmland_state.db # SQLite database tracking weekly AI/ML scans
│   ├── daily_up_east_farmland_dump.xlsx # Pre-generated multi-sheet Excel export
│   └── csv_exports/
│       └── up_east_farmlands_master.csv # Master CSV export
│
├── utils/
│   ├── geo_routing.py          # Haversine, road distance estimation, Google Maps directions URLs
│   ├── google_map_view.py      # Folium Google Maps satellite hybrid engine & buffer rings
│   ├── farmland_view.py        # Dark-mode HTML cards (telemetry, legal audit, news, contact)
│   ├── land_units.py           # Purvanchal Pakka Bigha / Biswa / Kattha / Dhur converter
│   ├── favorites_manager.py    # Persistent user shortlisting logic
│   ├── weekly_ml_scanner.py    # AI/ML Sentinel-2 NDVI & crop suitability scanner
│   ├── excel_exporter.py       # Openpyxl multi-sheet Excel & CSV generator
│   └── build_dataset.py        # Dataset builder & enrichment pipeline
│
└── tests/
    └── test_up_east_farmlands.py # Comprehensive pytest test suite (11 test suites)
```

---

## 🚀 Quickstart & Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/purntripathi-cmd/UP-East-Farmlands.git
   cd UP-East-Farmlands
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Streamlit application:**
   ```bash
   streamlit run app.py
   ```

4. **Run the automated test suite:**
   ```bash
   python -m pytest tests/ -v
   ```

---

## 🌐 Deploy to Streamlit Cloud

1. Log in to [share.streamlit.io](https://share.streamlit.io).
2. Connect your GitHub account and select repository `purntripathi-cmd/UP-East-Farmlands`.
3. Set **Main file path** to `app.py`.
4. Click **Deploy!**

---

## 📜 Legal & Compliance Disclaimer

All land parcels, Khasra numbers, and news notices are curated for analytical and research evaluation. Prospective buyers and institutional investors must conduct physical spot verification, demarcate boundaries using total station survey (ETS), and obtain non-encumbrance certificates (Barah Sala) from the jurisdictional Sub-Registrar Office before executing registered sale deeds.
