# RELIEFOS Lite — Academic Capstone Presentation Outline

**Project Title:** RELIEFOS Lite: Real-Time Flood Monitoring & Disaster Relief Resource Optimization System  
**Presentation Target:** Final B.Tech / M.Tech / Capstone Defense Committee  
**Total Duration:** 15–20 Minutes (including live demonstration and viva)  
**Slide Count:** 16 Academic Slides  

---

### Slide 1: Title & Candidacy
- **Title:** RELIEFOS Lite: Real-Time Flood Monitoring & Disaster Relief Resource Optimization System
- **Subtitle:** A Decoupled Geospatial Decision-Support Architecture for Constrained Logistics during Extreme Inundation Events
- **Geographic Context:** Kamrup Metropolitan (Guwahati Urban Agglomeration), Assam, India
- **Presenters:** Student Candidate / Capstone Project Team
- **Advisors / Department:** Department of Computer Science & Engineering / GIS & Operations Research Laboratory
- **Academic Disclaimer:** Human-in-the-loop decision-support system; all live telemetry layers displayed during testing utilize verified synthetic simulation sandboxes.

---

### Slide 2: Problem Statement & Local Geography
- **Urban Hydrology of Guwahati:**
  - Bowl-shaped topography bounded by the Brahmaputra River to the north and Meghalaya hills to the south.
  - Sluice gate backflow: When Brahmaputra stage exceeds Danger Level (49.68 m MSL at Pandu Ghat), city drainage channels (Bharalu, Mora Bharalu, Basistha) cannot discharge gravity flow.
- **Relief Logistics Crisis:**
  - Inundated road networks cut off low-lying communities (Bharalumukh, Santipur, Kumarpara).
  - Relief resources (food, potable water) are strictly finite at central hubs (Sarusajai Sports Complex).
  - Traditional dispatch relies on manual ad-hoc spreadsheets, resulting in stockouts in critical areas and vehicle overloading.

---

### Slide 3: Project Motivation & Research Objectives
- **Core Research Questions:**
  1. How can priority-weighted relief rationing be mathematically guaranteed when demand exceeds single-wave fleet capacity?
  2. How can topological road closures be dynamically integrated with route planning to prevent relief trucks from stalling in deep water?
  3. How can simulation drills be safely executed without risking corruption of live operational databases?
- **Primary Objectives:**
  - Build a high-performance web-based GIS operations console.
  - Formulate and solve a two-stage lexicographic optimization model using integer programming.
  - Implement hydraulic edge filtering in graph routing ($> 0.35\,\text{m}$ water cutoff).
  - Guarantee zero-mutation memory sandboxing for training drills.

---

### Slide 4: Proposed Solution & System Scope
- **The RELIEFOS Lite Framework:**
  - Decoupled GIS command center uniting flood monitoring with operations research.
  - Real-time conversion of spatial flood depth into actionable vehicle route detours.
- **System Scope & Non-Goals:**
  - **In Scope:** Decision support, allocation triage, detour navigation, dispatch manifest drafting, simulation stress testing.
  - **Out of Scope (Explicit Governance Guardrails):**
    - *No Autonomous Dispatch:* Vehicles are not dispatched without human officer sign-off.
    - *No Public Alert Dissemination:* Emergency broadcast requires statutory authority approval.
    - *No Hydrological Forecasting:* Water levels are ingested from sensor stubs, not computed via hydrodynamic partial differential equations.

---

### Slide 5: System Architecture & Data Flow
- **Two-Tier Decoupled Architecture:**
  - **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Leaflet (Port 3012).
  - **Backend API:** FastAPI (Python 3.12), SQLAlchemy, Uvicorn (Port 8013).
- **Service Segregation:**
  - *Optimization Service:* Google OR-Tools CP-SAT v9.8+.
  - *Network Routing Service:* NetworkX v3.0+ directed graph.
  - *GIS Geospatial Service:* RFC 7946 GeoJSON parser & validator.
  - *Drill Controller:* Sandboxed memory session with SHA-256 digital signing.

---

### Slide 6: Technology Stack & Architectural Justification
| Layer | Technology | Engineering Rationale |
| :--- | :--- | :--- |
| **Frontend UI** | React 18 + TypeScript | Type safety, reactive UI state across 10 command pages |
| **Styling** | Tailwind CSS | Google Stitch dark command-center aesthetic, responsive layouts |
| **Mapping Engine** | Leaflet / React-Leaflet | Lightweight WGS84 tile rendering, custom GeoJSON layer overlays |
| **Backend REST** | FastAPI (Python 3.12) | High throughput async ASGI, automatic OpenAPI/Swagger generation |
| **Optimization** | Google OR-Tools CP-SAT | State-of-the-art constraint programming & SAT solver for discrete NP-hard models |
| **Network Graph** | NetworkX | Efficient Dijkstra/A* shortest path algorithms with dynamic edge weight filtering |

---

### Slide 7: GIS & Spatial Inundation Interface
- **Geospatial Standards:**
  - GeoJSON standard: RFC 7946 compliance with EPSG:4326 (WGS84) latitude/longitude coordinate ordering.
  - Strict polygon ring closure and bounding-box validation ($26.0^\circ - 26.3^\circ\,\text{N}$, $91.6^\circ - 91.9^\circ\,\text{E}$).
- **Command-Center Map Features:**
  - Color-coded zone polygons based on real-time vulnerability index.
  - Depot coordinates (Sarusajai: `26.1158° N, 91.7584° E`).
  - Active shelter locations and occupancy ratios.
  - Dynamic overlay of submerged road corridors.

---

### Slide 8: Demand & Resource Inventory Reconciliation
- **Resource Differentiation & Units:**
  - **Food Supplies:** Packaged dry rations measured in kilograms ($\text{kg}$).
  - **Potable Water:** Sealed drinking water containers measured in liters ($\text{L}$).
- **Axle Payload Conversion:**
  - Water volume is converted at $1.0\,\text{kg}/\text{L}$ to enforce physical gross vehicle weight limits.
- **Strict Resource Non-Substitution:**
  - Food mass and water volume occupy independent constraint rows in the solver.
  - A food surplus cannot mathematically fulfill a potable water deficit.

---

### Slide 9: Mathematical Formulation — Two-Stage Lexicographic CP-SAT
- **Stage 1: Priority-Weighted Deficit Minimization**
  $$\min Z_1 = \sum_{i \in \mathcal{Z}} \sum_{r \in \mathcal{R}} W_i \cdot \alpha_r \cdot (D_{i,r} - x_{i,r})$$
  - Subject to: $0 \le x_{i,r} \le D_{i,r}$, $\sum x_{i,r} \le S_r$, $\sum \sum x_{i,r} \le \text{FleetCapacity}$.
  - Weights: Critical = 10, High = 5, Moderate = 2, Low = 1.
- **Stage 2: Travel Distance Minimization with Preservation**
  $$\min Z_2 = \sum_{v \in \mathcal{V}} \sum_{j} \sum_{k} d_{j,k} \cdot y_{j,k,v} \quad \text{s.t.} \quad Z_1(x) \le Z_1^*$$
  - MTZ subtour elimination constraints guarantee depot round-trip tours.
  - Preserves Stage 1 life-saving triage optimality ($Z_1^*$).

---

### Slide 10: Topological Routing & Hydraulic Road Closures
- **Road Inundation Cutoff:**
  - Maximum safe vehicle wading depth: $0.35\,\text{m}$.
- **Empirical Demonstration Case:**
  - MG Road Santipur section submerged under $0.40\,\text{m}$ water ($> 0.35\,\text{m}$).
  - Edge dynamically pruned from graph traversal.
  - Router diverts transport via elevated AT Road Arterial Bypass & Arya Nagar Flyover.
  - Detour cost: $+12.4\,\text{km}$ additional transit distance, avoiding vehicle stall.
- **Topological Severance (Scenario H):**
  - If a zone has no valid dry access path, solver assigns $0\,\text{kg}$ road allocation and triggers a `"TOPOLOGICAL_SEVERANCE"` emergency airlift alert.

---

### Slide 11: Comprehensive Stress Testing (Scenarios A–J)
- **10 Deterministic Test Scenarios Executed:**
  - *A:* Normal Operations Baseline
  - *B:* High Demand Surge ($2.0\times$ demand)
  - *C:* Critical Priority Inversion
  - *D:* Low Depot Inventory
  - *E:* Severely Constrained Fleet ($1$ truck)
  - *F:* Road Closures & Flood Detours
  - *G:* Water Rationing Focus ($\alpha_w = 1.5$)
  - *H:* Isolated Severed Zone
  - *I:* Non-Substitution Stress
  - *J:* Full Multi-Factor Stress
- **Key Verification:** All 10 scenarios solve deterministically with 100% solver feasibility and no state leaks.

---

### Slide 12: Empirical Performance & Scalability Benchmarks
- **Measured Solver Execution Times:**
  - 5 Operational Zones (Guwahati Baseline): **$< 35\,\text{ms}$**
  - 10 Zones Benchmark: **$48\,\text{ms}$**
  - 20 Zones Regional Grid: **$124\,\text{ms}$**
  - 50 Zones Large-Scale Emergency: **$1,840\,\text{ms}$ ($< 2.0\,\text{s}$)**
- **Memory Footprint & Concurrency:**
  - Backend memory usage under active CP-SAT solve: $< 140\,\text{MB}$.
  - Async FastAPI event loop handles concurrent operator inspection while solver executes.

---

### Slide 13: Demonstration Mode & Operational Store Isolation
- **Sandboxed Simulation Architecture:**
  - Deep-copy isolation (`copy.deepcopy`) creates an isolated in-memory simulation instance.
  - Drill operations do not write to `reliefos.db` or operational memory tables.
- **Audited Immutability Proof:**
  - Automated test `test_demo_drill_database_immutability` confirms operational stock and demands are 100% identical before and after executing the drill.
- **Statutory Audit Dossier:**
  - Generates ASDMA Form 8B dispatch manifests with SHA-256 digital verification hashes for evidentiary logging.

---

### Slide 14: Quality Assurance & Automated Test Evidence
- **Backend Test Suite Results:**
  - `test_backend.py`: 25 Tests PASSED (API endpoints, CORS, database integrity)
  - `test_demo_drill.py`: 6 Tests PASSED (Drill lifecycle, immutability, Form 8B export)
  - `test_gis_validation.py`: 7 Tests PASSED (RFC 7946 GeoJSON, bounding boxes, waypoints)
  - `test_optimization_scenarios.py`: 27 Tests PASSED (Scenarios A–J, CP-SAT constraints)
  - **Total Backend Tests: 65 PASSED, 0 FAILED (100% Pass Rate)**
- **Frontend Validation:**
  - TypeScript compilation (`tsc --noEmit`): 0 Errors
  - Vite production bundle build: SUCCESSFUL (`dist/` generated)

---

### Slide 15: System Limitations & Future Research
- **Technical Limitations Disclosed:**
  - *Static Road Graph:* Graph weights are fixed distance values; dynamic real-time Google Maps/HERE traffic congestion is not currently integrated.
  - *Single-Wave Scheduling:* Fleet trips are modeled as single round-trips; multi-period vehicle re-dispatch requires rolling-horizon extensions.
  - *Water Density Assumption:* Water modeled at exactly $1.0\,\text{kg}/\text{L}$ (neglects container packaging tare weight).
- **Future Research Directions:**
  - Integrating Sentinel-1 SAR satellite flood extent rasters into automated GeoJSON polygon extraction.
  - Multi-depot collaborative replenishment across neighboring districts.

---

### Slide 16: Summary, Live Demonstration & Viva Defense
- **Capstone Contributions:**
  1. Delivered a complete, verified, 10-page GIS decision-support command center.
  2. Implemented a mathematically rigorous two-stage lexicographic CP-SAT optimization model.
  3. Integrated hydraulic edge-depth graph routing with automated flood detours.
  4. Built a fully isolated, reproducible demonstration drill environment (`ASDMA-DRILL-2024-GHY-01`).
- **Live System Verification:**
  - Frontend operational at `http://localhost:3012`
  - Backend REST API operational at `http://127.0.0.1:8013`
- **Thank you! We now welcome questions from the examination committee.**
