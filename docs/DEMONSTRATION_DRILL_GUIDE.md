# RELIEFOS Lite — Demonstration Drill Guide

**Scenario Designation:** Guwahati Urban Flood Emergency — Relief Operations Drill  
**Official Incident Code:** `ASDMA-DRILL-2024-GHY-01`  
**Target Operational Area:** Kamrup Metropolitan (Guwahati Urban Agglomeration), Assam, India  
**Target Audience:** Academic Capstone Review Committee, External Examiners, Disaster Operations Specialists  

---

## 1. Drill Context & Scenario Background

This simulated emergency drill models a severe monsoon hydrometeorological crisis across the Guwahati urban basin:
- **Rainfall:** 210 mm accumulated precipitation over 48 hours.
- **River Gauge:** Brahmaputra at Pandu Ghat reaches Danger Level (49.68 m MSL).
- **Critical Infrastructure Severance:** Sluice gates backflow-choked; MG Road Santipur culvert submerged under 0.40 m water (exceeding the 0.35 m safe vehicle operating threshold).
- **Relief Mission:** Deliver life-critical food rations and potable drinking water from the Sarusajai Central Relief Depot to five flood-affected sectors.
- **Fleet Constraints:** 3 relief transport vehicles with a combined single-wave payload capacity of strictly 5,000 kg.
- **Relief Supply Gap:** Total sector demand of 6,500 kg against a 5,000 kg fleet wave limit, requiring lexicographic priority triage.

> [!NOTE]
> All hydrometric readings, casualty numbers, and damage levels used in this drill are synthetically generated for academic demonstration and decision-support verification. They do not represent real-time observations or authoritative emergency alerts.

---

## 2. Environment Startup & Verification

Verify the system is running locally on the verified ports:

### A. Backend Startup
```powershell
cd "d:\projects\Disaster Relief Planning & Resource Optimization System\backend"
.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8013 --reload
```
*Health Check:* Open `http://127.0.0.1:8013/api/health` — response must indicate `"status": "healthy"`.

### B. Frontend Startup
```powershell
cd "d:\projects\Disaster Relief Planning & Resource Optimization System\frontend"
npm.cmd run dev -- --port 3012
```
*Access:* Open `http://localhost:3012` in any modern web browser (Google Chrome or Microsoft Edge recommended).

---

## 3. End-to-End 10-Page Operator Demonstration Workflow

Follow this precise sequence to demonstrate complete operational functionality to the examination panel:

### Step 1: Operations Overview (`/dashboard`)
- **Action:** Navigate to `http://localhost:3012/dashboard`.
- **Observations:**
  - Notice the KPI cards: 5 Operational Zones, 3 Fleet Vehicles, 1 Central Depot.
  - Review the Brahmaputra River Stage gauge at 49.68 m MSL (highlighted in orange/red warning tier).
  - Inspect the Demand vs. Supply bar chart showing current relief inventory distribution.
  - Review Tactical Alerts list showing the MG Road Santipur culvert submergence alert.
  - Note the **"SIMULATED DATA (DEMO READY)"** badge on the top navigation bar.

### Step 2: Live Flood Map (`/flood-map`)
- **Action:** Click "Live Flood Map" in the sidebar navigation or browse to `/flood-map`.
- **Observations:**
  - The Leaflet interactive map renders the Guwahati urban basin centered on Kamrup Metropolitan.
  - Five distinct operational zones render with color-coded risk shading (Red = Critical, Amber = High, Yellow = Moderate, Blue/Green = Low).
  - Depot marker is positioned at Sarusajai Sports Complex (`26.1158° N, 91.7584° E`).
  - Shelter markers show active occupancy numbers.
  - Layer toggles in the top-right allow switching between Zone Boundaries, Inundation Heatmaps, and Relief Corridors.

### Step 3: Zones & Vulnerability Risk (`/zones`)
- **Action:** Navigate to `/zones`.
- **Observations:**
  - Inspect the 5 operational sectors:
    - **Zone 01:** Bharalumukh (Critical Risk — Sluice backflow)
    - **Zone 02:** Panbazar (Critical Risk — Riverfront seepage)
    - **Zone 03:** Dispur Supermarket (High Risk — Lowland drainage overflow)
    - **Zone 04:** Basistha (Moderate Risk — Canal runoff)
    - **Zone 05:** Jalukbari (Low Risk — Elevated bypass hub)
  - Confirm that Zone Priority (tactical dispatch rank) and Zone Risk (inundation severity) are distinctly modeled and displayed.

### Step 4: Resource Inventory (`/inventory`)
- **Action:** Navigate to `/inventory`.
- **Observations:**
  - Available stock at Sarusajai Central Depot: 2,500 kg Food Rations, 3,000 L Potable Water Cans.
  - Inspect the 3 fleet transport vehicles:
    - **VH-01 (Tata 407 4x4 Medium):** 2,000 kg capacity
    - **VH-02 (Ashok Leyland Heavy Cargo):** 1,800 kg capacity
    - **VH-03 (Mahindra Bolero Pickup):** 1,200 kg capacity
  - Gross fleet payload capacity reconciles to exactly:
    $$2,000 + 1,800 + 1,200 = 5,000\,\text{kg}$$
  - Note the explicit conversion notice: Potable water is modeled at $1.0\,\text{kg}/\text{L}$ for vehicle axle payload calculations.

### Step 5: Demand Intake & Management (`/demand`)
- **Action:** Navigate to `/demand`.
- **Observations:**
  - Total incoming demands across all 5 zones: Food 2,500 kg, Water 4,000 L (Total 6,500 kg payload).
  - Note the single-wave fleet deficit:
    $$6,500\,\text{kg (Demand)} - 5,000\,\text{kg (Fleet Limit)} = 1,500\,\text{kg (Unmet Deficit)}$$
  - Test validation: Attempting to submit a negative quantity is blocked with an explicit input validation error.

### Step 6: Relief Allocation Optimization (`/allocation`)
- **Action:** Navigate to `/allocation`.
- **Execution:** Click the **"Run Lexicographic Solver"** button.
- **Observations:**
  - The CP-SAT solver completes execution in under 50 ms with status **OPTIMAL**.
  - **Stage 1 Verification:** Critical Zones 01 and 02 receive 100% fulfillment of life-saving supplies (0 unmet penalty).
  - **Resource Non-Substitution:** Food allocations and water allocations are computed in disjoint constraint rows (food stock never substitutes for potable water).
  - **Stage 2 Verification:** Confirms Stage 1 optimum $Z_1^*$ is mathematically preserved while selecting the most compact distribution configuration.

### Step 7: Route Optimization & Detour Audit (`/routes`)
- **Action:** Navigate to `/routes`.
- **Observations:**
  - Routes are drawn connecting Sarusajai Depot to all delivered sector waypoints.
  - **Hydraulic Edge Cutoff:** MG Road Santipur section is marked with a red dashed line indicating **"IMPASSABLE (0.40m Water Depth > 0.35m Limit)"**.
  - **Detour Verified:** Vehicle VH-02 is automatically diverted via the elevated AT Road Arterial Bypass and Arya Nagar Flyover (+12.4 km additional detour distance).
  - Every completed vehicle route departs from and returns to Sarusajai Central Depot.

### Step 8: Scenario Stress Testing (`/simulation`)
- **Action:** Navigate to `/simulation`.
- **Observations:**
  - The catalog displays 10 standard stress scenarios (Scenarios A through J):
    - *Scenario A:* Normal Operations Baseline
    - *Scenario B:* High Demand Surge (2.0x Multiplier)
    - *Scenario C:* Critical Zone Priority Inversion
    - *Scenario D:* Severely Depleted Depot Stock
    - *Scenario E:* Constrained Single Vehicle Fleet
    - *Scenario F:* Flood Inundation Road Closures
    - *Scenario G:* Water Rationing Priority Mode
    - *Scenario H:* Isolated Severed Zone (Topological Cut)
    - *Scenario I:* Resource Non-Substitution Verification
    - *Scenario J:* Full Multi-Factor Crisis Stress
  - Click on "Scalability Benchmark" to review solver performance across synthetic networks up to 50 zones (all solving within $< 5.0$ seconds).

### Step 9: Data Sources & Provenance (`/data-sources`)
- **Action:** Navigate to `/data-sources`.
- **Observations:**
  - Every operational telemetry layer displays an explicit **ISO-19115 Data Provenance Badge**:
    - Central Water Commission River Gauge: `SIMULATED_API_STUB`
    - Road Inundation Sensors: `ESTIMATED_HYDRO_MODEL`
    - Shelter Capacity: `MANUAL_FIELD_ENTRY`
    - Geospatial Road Graph: `OSM_EXTRACT_EPSG4326`
  - Reassures the panel that no synthetic drill telemetry is misrepresented as genuine satellite or real-time IoT feeds.

### Step 10: Operator Settings & RBAC Sandbox (`/settings`)
- **Action:** Navigate to `/settings`.
- **Observations:**
  - Review tactical solver parameters (CP-SAT Time Limit, Water Priority Weight $\alpha_r = 1.2$).
  - Review Role-Based Access Control (RBAC) tiers:
    - *Operations Planner:* Authorized for Solver Dispatch & Manifest Review
    - *Field Dispatch Officer:* Manifest Execution View
    - *Administrator:* System Topology & Database Configuration

---

## 4. Live Demonstration Drill Controller Walkthrough

During the viva defense, demonstrate the drill management modal from the top navigation bar:

1. Click on the **"SIMULATED DATA (DEMO READY)"** button in the Topbar.
2. The **Disaster Relief Operations Drill Manager** modal opens.
3. Click **"1. Load Emergency Drill Scenario"**:
   - Staging status updates to **"DRILL STAGED"**.
   - Topbar badge dynamically transitions to **"DEMO DRILL ACTIVE"** with an amber/cyan alert glow.
4. Click **"2. Execute Lexicographic Solver"**:
   - The CP-SAT optimizer and NetworkX router run inside the sandbox.
   - Metrics card populates: Food Allocated = 2,500 kg, Water Allocated = 3,000 L, Fleet Utilization = 100%, Detour Distance = 12.4 km.
5. Click **"Export ASDMA Form 8B Dossier"**:
   - Downloads `ASDMA_DRILL_DOSSIER_<date>.json`.
   - Open the JSON file to show the committee the statutory Form 8B manifest, vehicle assignments, and the 64-character SHA-256 digital integrity hash.
6. Click **"Reset to Operational Baseline"**:
   - Status returns to **"IDLE / DEFAULT"**.
   - Topbar badge returns to **"SIMULATED DATA (DEMO READY)"**.
   - Demonstrates that persistent operational tables were untouched throughout the entire drill.

---

## 5. Verification Commands for Viva Examiners

Viva examiners may independently verify all claims by running the following copy-paste commands:

```bash
# 1. Inspect active drill status
curl -X GET http://127.0.0.1:8013/api/demo/drill/status

# 2. Stage the drill scenario
curl -X POST http://127.0.0.1:8013/api/demo/drill/load

# 3. Execute optimization and detour routing
curl -X POST http://127.0.0.1:8013/api/demo/drill/run

# 4. Export Form 8B dispatch manifest
curl -X GET http://127.0.0.1:8013/api/demo/drill/export

# 5. Reset drill environment
curl -X POST http://127.0.0.1:8013/api/demo/drill/reset
```
