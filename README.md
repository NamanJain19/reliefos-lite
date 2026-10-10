# RELIEFOS Lite — Real-Time Flood Monitoring & Disaster Relief Resource Optimization System

[![Backend Test Suite](https://img.shields.io/badge/pytest-72%20passed%20(100%25)-brightgreen.svg)]()
[![Frontend Build](https://img.shields.io/badge/typescript-0%20errors-brightgreen.svg)]()
[![Optimization Engine](https://img.shields.io/badge/OR--Tools-CP--SAT%20v9.8+-blue.svg)]()
[![GIS Compliance](https://img.shields.io/badge/GeoJSON-RFC%207946%20%2F%20EPSG%3A4326-blue.svg)]()
[![Basemap Provider](https://img.shields.io/badge/Basemap-OpenStreetMap%20(ODbL)-green.svg)]()
[![Weather API](https://img.shields.io/badge/Weather-Open--Meteo%20(CC--BY%204.0)-green.svg)]()

**Target Region:** Kamrup Metropolitan (Guwahati Urban Agglomeration), Assam, India  
**Designation:** Real-World-Data-Driven Disaster Relief Decision-Support System (Human-in-the-Loop)  

RELIEFOS Lite is a decision-support platform designed to assist emergency operations centers (such as the Assam State Disaster Management Authority — ASDMA) in monitoring real-world flood telemetry, predicting inundation risks, and solving multi-trip vehicle routing and priority relief allocation challenges across Guwahati, Assam.

---

## 🚀 Port & Network Architecture

| Tier | Service | Port | Local URL | Primary Technologies |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | GIS Tactical Command Center | **3012** | `http://localhost:3012` | React 18, Vite 5, TypeScript 5, Tailwind CSS, Leaflet |
| **Backend** | Operations Research REST API | **8013** | `http://127.0.0.1:8013` | Python 3.12, FastAPI, OR-Tools CP-SAT, NetworkX, SQLAlchemy |
| **Swagger UI** | Interactive OpenAPI Explorer | **8013** | `http://127.0.0.1:8013/docs` | OpenAPI 3.0 / Swagger |
| **ReDoc** | Academic API Specification | **8013** | `http://127.0.0.1:8013/redoc` | OpenAPI 3.0 / ReDoc |

---

## 🛠️ Quick Start & Startup Instructions

### 1. Backend Setup (`http://127.0.0.1:8013`)
```powershell
# Navigate to backend directory
cd "d:\projects\Disaster Relief Planning & Resource Optimization System\backend"

# Activate virtual environment
.\.venv\Scripts\activate   # Windows PowerShell
# (or 'source .venv/bin/activate' on Linux/macOS)

# Install dependencies if required
pip install -r requirements.txt

# Start backend ASGI server
uvicorn app.main:app --host 127.0.0.1 --port 8013 --reload
```
*Health verification:* Visit `http://127.0.0.1:8013/api/health` — response must indicate `"status": "healthy"`, `"active_mode": "OPERATIONAL_LIVE"`.

### 2. Frontend Setup (`http://localhost:3012`)
```powershell
# In a new terminal, navigate to frontend directory
cd "d:\projects\Disaster Relief Planning & Resource Optimization System\frontend"

# Start Vite dev server on strict port 3012
npm.cmd run dev -- --port 3012
```
*Access UI:* Open `http://localhost:3012` in your web browser.

### 3. Run Automated Quality Assurance Suites
```powershell
# Backend Test Suite (All 72 tests across 5 test suites)
cd "d:\projects\Disaster Relief Planning & Resource Optimization System\backend"
.\.venv\Scripts\pytest.exe -v

# Frontend Production Compilation & Type Check
cd "d:\projects\Disaster Relief Planning & Resource Optimization System\frontend"
npm.cmd run build
```

---

## 🌊 Phase 5 Demonstration Drill: Guwahati Flood Emergency

The system includes a fully reproducible, sandboxed emergency drill:
- **Drill Code:** `ASDMA-DRILL-2024-GHY-01`
- **Hydrology:** Brahmaputra River stage reaches Danger Level (49.68 m MSL at Pandu Ghat).
- **Physical Road Cutoff:** MG Road Santipur culvert submerged under 0.40 m water ($> 0.35\,\text{m}$ clearance limit).
- **Relief Mission:** Deliver 2,500 kg food and 4,000 L water (6,500 kg total payload demand) using 3 transport vehicles with a 5,000 kg single-wave fleet limit.
- **Topological Reaction:** Vehicle VH-02 is automatically diverted via elevated AT Road / Arya Nagar Flyover (+12.4 km detour).
- **Data Isolation Guarantee:** Deep-copy memory sandboxing guarantees 0 persistent mutations to `reliefos.db` operational tables.

### Quick Demonstration via Topbar:
1. Click the **"SIMULATED DATA (DEMO READY)"** button on the top navigation bar.
2. Click **"1. Load Emergency Drill Scenario"** $\rightarrow$ Badge updates to **"DEMO DRILL ACTIVE"**.
3. Click **"2. Execute Lexicographic Solver"** $\rightarrow$ Views real-time CP-SAT allocation and NetworkX detour metrics.
4. Click **"Export ASDMA Form 8B Dossier"** $\rightarrow$ Downloads signed JSON manifest with a 64-character SHA-256 integrity hash.
5. Click **"Reset to Operational Baseline"** $\rightarrow$ Restores baseline without modifying live records.

---

## 📑 10 Operational Application Pages

1. **Operations Overview (`/dashboard`)**: Central metrics dashboard, Brahmaputra river stage telemetry, inventory breakdown, and tactical emergency alerts.
2. **Live Flood Map (`/flood-map`)**: Interactive Leaflet map with RFC 7946 GeoJSON layers, colored risk sectors, depot marker, and submerged road overlays.
3. **Zones & Vulnerability Risk (`/zones`)**: 5-sector vulnerability index for Kamrup Metro (Bharalumukh, Panbazar, Dispur, Basistha, Jalukbari).
4. **Resource Inventory (`/inventory`)**: Stock ledger for Sarusajai Central Depot, vehicle fleet capacities, and water $1.0\,\text{kg}/\text{L}$ payload conversions.
5. **Demand Management (`/demand`)**: Priority-ranked relief demands with strict input validation preventing negative or malformed submissions.
6. **Relief Allocation (`/allocation`)**: Google OR-Tools CP-SAT two-stage lexicographic solver execution with Stage 1 preservation verification.
7. **Route Optimization (`/routes`)**: NetworkX directed road graph with automated hydraulic edge filtering and depot round-trip tours.
8. **Simulation & Stress Reports (`/simulation`)**: Catalog of Scenarios A through J and scalable grid benchmarks up to 50 zones ($< 2.0\,\text{s}$).
9. **Data Sources (`/data-sources`)**: Pipeline status and ISO-19115 data provenance badges (Simulated, Observed, Manual, Estimated, Stale).
10. **Settings (`/settings`)**: Solver hyperparameters, water weighting ratios, and Role-Based Access Control (RBAC) testing profiles.

---

## 🔬 Mathematical & Algorithmic Foundations

### 1. Two-Stage Lexicographic Optimization (OR-Tools CP-SAT)
- **Stage 1 (Life-Saving Triage):** Minimizes priority-weighted unmet demand:
  $$\min Z_1 = \sum_{i \in \mathcal{Z}} \sum_{r \in \mathcal{R}} W_i \cdot \alpha_r \cdot (D_{i,r} - x_{i,r})$$
  *(Where $W_i$ is zone priority: Critical = 10, High = 5, Moderate = 2, Low = 1; $\alpha_{\text{water}} = 1.2$)*.
- **Stage 2 (Logistical Efficiency):** Minimizes vehicle travel distance:
  $$\min Z_2 = \sum_{v \in \mathcal{V}} \sum_{j} \sum_{k} d_{j,k} \cdot y_{j,k,v} \quad \text{subject to } Z_1(x) \le Z_1^*$$
  *(Guarantees that route shortening never compromises relief fulfillment)*.
- **Resource Non-Substitution:** Food mass (kg) and water volume (L) occupy independent constraint rows.

### 2. Topological Hydraulic Routing (NetworkX)
- Edge traversal cost set to $\infty$ when water depth $> 0.35\,\text{m}$.
- Submerged corridors automatically trigger shortest alternative graph traversal (Dijkstra / A*).
- Completely severed zones trigger topological severance warnings advising aerial drop or boat dispatch.

---

## 🗺️ Real-World Data Ingestion & OpenStreetMap Basemap

### 1. OpenStreetMap Tile Integration (No CARTO Credentials Required)
- **Standard OSM Endpoint:** `https://tile.openstreetmap.org/{z}/{x}/{y}.png`
- **Configurable:** via `VITE_MAP_TILE_URL` and `VITE_MAP_ATTRIBUTION`.
- **Tile Policy Adherence:** Visible attribution `&copy; OpenStreetMap contributors`, zoom limits (`minZoom=10`, `maxZoom=19`), `useMap` resize handling, and non-intrusive `tileerror` fallback alert.
- **Tactical Dark Mode Canvas:** Preserved via `.dark-map-tiles` CSS luminance invert filter without altering cartographic geometry.

### 2. Connected Real-World Providers
- **Weather & Rainfall:** Live **Open-Meteo API** (CC-BY 4.0) queried for Kamrup Metro ($26.1445^\circ\text{N}, 91.7362^\circ\text{E}$) with 15-minute fair-use caching.
- **Road Network Routing:** Live **OSRM Driving Engine** (ODbL) calculating real OpenStreetMap highway geometry and driving duration with NetworkX topological fallback.
- **River Gauges:** Central Water Commission (CWC) stations (Pandu, DC Court, Bharalu, Basistha) with authorized manual entry modal and SQLite audit logging.
- **Historical Disasters:** Archived Guwahati June 2022 & July 2024 flood events with documented sensor outage disclosures.

### 3. Data Source Registry & 8 Lifecycle States
Every layer clearly communicates provenance:
`LIVE`, `LAST_KNOWN`, `STALE`, `UNAVAILABLE`, `MANUAL`, `ESTIMATED`, `SIMULATED`, and `UNVERIFIED`.

---

## 📚 Technical Documentation Package

Detailed technical documentation is available in the [`docs/`](./docs) directory:
- [Real-World Data Integration Report (`docs/REAL_WORLD_DATA_INTEGRATION_REPORT.md`)](./docs/REAL_WORLD_DATA_INTEGRATION_REPORT.md): Comprehensive production-readiness report, live provider status, and audit evidence.
- [System Architecture Specification (`docs/ARCHITECTURE.md`)](./docs/ARCHITECTURE.md): Multi-tier architecture, Mermaid topology and sequence diagrams, mathematical model, and data isolation.
- [Demonstration Drill Guide (`docs/DEMONSTRATION_DRILL_GUIDE.md`)](./docs/DEMONSTRATION_DRILL_GUIDE.md): Step-by-step viva presentation script across all 10 pages with cURL commands.
- [Capstone Presentation Outline (`docs/CAPSTONE_PRESENTATION_OUTLINE.md`)](./docs/CAPSTONE_PRESENTATION_OUTLINE.md): 16-slide academic presentation structure.
- [Academic Viva Question Bank (`docs/VIVA_DEFENSE_PREPARATION.md`)](./docs/VIVA_DEFENSE_PREPARATION.md): Comprehensive viva defense question bank covering Sections A through H.

---

## ⚖️ Operational Safety & Ethical Governance Disclaimer

RELIEFOS Lite is an **academic decision-support system (DSS)** developed for research, disaster planning, and operational decision-support.

- **Human-in-the-Loop:** The system does not autonomously dispatch physical emergency vehicles or issue public alerts. All recommendations require authorized human officer verification and statutory sign-off.
- **Zero Fabricated Live Data:** Missing or unmonitored sensors are transparently labeled `UNAVAILABLE` or `MANUAL`; the platform never fabricates fake telemetry values.
- **Geographic Data Notice:** Monitored zone polygons are labeled as illustrative operational areas (ASDMA Pilot Scheme v2.4) in WGS84 EPSG:4326. Verified shelter and depot coordinates are tagged with official registry provenance.
