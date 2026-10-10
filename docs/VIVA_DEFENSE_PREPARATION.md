# RELIEFOS Lite — Comprehensive Academic Viva & Defense Question Bank

**Project:** RELIEFOS Lite — Real-Time Flood Monitoring & Disaster Relief Resource Optimization System  
**Target Region:** Kamrup Metropolitan (Guwahati Urban Agglomeration), Assam, India  
**Target Defense:** Capstone Project Viva Voce / Faculty Review Panel  
**Audience:** B.Tech / M.Tech Examiners, Operations Research Evaluators, GIS Committee  

---

## SECTION A: PROJECT FUNDAMENTALS & DISASTER MANAGEMENT CONTEXT

### Q1. What specific problem does RELIEFOS Lite solve?
**Answer:**  
During acute urban flooding in Guwahati (triggered by intense monsoon downpours and Brahmaputra river backflow), relief supplies at central depots are strictly finite, vehicle fleet payload capacities are constrained, and urban road corridors become submerged. RELIEFOS Lite solves the multi-commodity, priority-based resource allocation problem and the flood-constrained vehicle routing problem, computing optimal delivery plans that prioritize life-critical survival needs while avoiding impassable floodwaters.

### Q2. Who are the intended operational users of the system?
**Answer:**  
Emergency Operations Center (EOC) personnel, specifically:
1. **Operations Planners:** Officers at District Disaster Management Authorities (such as Kamrup Metro DDMA / ASDMA) responsible for rationing relief inventory and authorizing dispatch manifests.
2. **Logistics & Fleet Dispatch Officers:** Hub coordinators at staging depots (such as Sarusajai Sports Complex) managing vehicle loading and routing instructions.
3. **Field Relief Teams:** Personnel executing deliveries at relief camps and shelters.

### Q3. Why does RELIEFOS Lite function as a decision-support tool rather than an autonomous dispatch system?
**Answer:**  
In disaster operations, life safety and statutory liability require human-in-the-loop governance:
- Real-world disaster environments contain unpredictable dynamic variables (e.g., sudden electrical line collapses, localized civil distress, shifting mud banks) that automated models cannot observe.
- Statutory regulations (Disaster Management Act 2005) require designated civil defense officers to sign and seal statutory dispatch manifests (such as ASDMA Form 8B).
- RELIEFOS Lite automates complex combinatorial calculations (OR-Tools optimization and NetworkX detours) and presents structured recommendations for human officer review, modification, and digital sign-off.

---

## SECTION B: SYSTEM ARCHITECTURE & ENGINEERING

### Q4. Why was a decoupled architecture chosen (FastAPI + React) instead of a monolithic web framework?
**Answer:**  
- **Computational Separation:** Google OR-Tools CP-SAT and NetworkX are computationally intensive, CPU-bound Python libraries. FastAPI executes them within a high-performance Python 3.12 ASGI runtime without blocking UI responsiveness.
- **Client-Side GIS Rendering:** Vector GIS layers (GeoJSON polygons, road corridors, interactive map markers) are rendered client-side using Leaflet via the browser's GPU/DOM, offloading map rendering from the server.
- **Port Segregation:** Clear network separation on port `3012` (Frontend) and port `8013` (Backend) permits independent scaling, automated CI/CD unit testing, and modular replacement of either layer.

### Q5. How does the system handle database persistence and why is SQLite used as the local default?
**Answer:**  
- The backend utilizes **SQLAlchemy ORM** (`backend/app/models/`), decoupling business logic from underlying database engines.
- **SQLite** is used locally as a zero-configuration, serverless relational database stored at `reliefos.db`, ensuring that any evaluator can run the project locally without configuring an external database daemon.
- The system is architected as **PostgreSQL-ready**: changing `DATABASE_URL` in `backend/.env` to `postgresql://user:pass@localhost:5432/reliefos` enables PostgreSQL without modifying any model or service code.

### Q6. How do frontend and backend communicate and how is CORS configured?
**Answer:**  
- Communication occurs via asynchronous HTTP REST/JSON calls using a centralized Axios client (`frontend/src/services/api.ts`).
- CORS middleware in `backend/app/main.py` explicitly whitelists frontend origins `http://localhost:3012` and `http://127.0.0.1:3012`, strictly enforcing preflight verification and rejecting unauthorized cross-origin requests.

---

## SECTION C: GEOGRAPHIC INFORMATION SYSTEMS (GIS) & SPATIAL DATA

### Q7. What geospatial standards are enforced in RELIEFOS Lite?
**Answer:**  
The system strictly enforces **RFC 7946 GeoJSON** standard compliance with the **EPSG:4326 (WGS84)** Coordinate Reference System. All coordinate tuples are ordered as `[longitude, latitude]` in GeoJSON payloads and converted to `[latitude, longitude]` when rendering Leaflet map markers.

### Q8. What is the difference between valid geometry and verified geography?
**Answer:**  
- **Valid Geometry:** The GeoJSON data is syntactically and topologically well-formed — coordinate rings are closed (first coordinate equals last coordinate), coordinates fall within valid ranges ($-180^\circ$ to $+180^\circ$ longitude, $-90^\circ$ to $+90^\circ$ latitude), and geometries contain no self-intersections.
- **Verified Geography:** The polygon boundaries correspond to legally surveyed, authoritative revenue circle or municipal ward boundaries officially gazetted by the Government of Assam.
- **Academic Disclosure:** In RELIEFOS Lite, the 5 operational sectors are mathematically valid planning geometries designed for logistics aggregation; they represent illustrative planning sectors rather than legally surveyed ward boundaries.

### Q9. How are spatial road closures detected and represented in the GIS layer?
**Answer:**  
Road segments in the NetworkX graph possess physical attributes including `length_km`, `surface_type`, and `water_depth_m`. When simulated or sensor-ingested water depth exceeds the vehicle operating threshold ($0.35\,\text{m}$), the edge is flagged as impassable, styled as a red dashed line in the Leaflet map overlay, and assigned infinite weight in the routing graph.

---

## SECTION D: OPERATIONS RESEARCH & LEXICOGRAPHIC OPTIMIZATION

### Q10. What is Google OR-Tools CP-SAT and why was it chosen over standard Linear Programming (LP)?
**Answer:**  
OR-Tools CP-SAT is a modern Constraint Programming and Boolean Satisfiability (SAT) solver. It is chosen because relief allocation problems involve discrete, integer quantities (e.g., individual 10-liter water cans, discrete vehicle assignments, binary routing arcs) and non-linear logical constraints (such as conditional priority thresholds and disjoint resource non-substitution), which CP-SAT solves substantially faster than classical branch-and-bound simplex algorithms.

### Q11. What is two-stage lexicographic optimization and why is it essential for disaster relief?
**Answer:**  
Lexicographic (preemptive) optimization solves a multi-objective problem hierarchically when objectives cannot be collapsed into an arbitrary weighted sum:
- **Stage 1 (Life-Saving Triage):** Minimizes priority-weighted unmet demand:
  $$\min Z_1 = \sum_{i} \sum_{r} W_i \cdot \alpha_r \cdot (D_{i,r} - x_{i,r})$$
- **Stage 2 (Logistics Efficiency):** Minimizes total fleet transit distance:
  $$\min Z_2 = \sum d_{j,k} \cdot y_{j,k,v}$$
- **The Preservation Constraint:** Stage 2 enforces $Z_1(x) \le Z_1^*$, guaranteeing that the router will never reduce vehicle kilometers traveled by cutting off supplies to a vulnerable relief camp.

### Q12. How is vehicle payload capacity modeled and what unit conversions are applied?
**Answer:**  
Gross vehicle payload capacity is strictly bounded in kilograms ($\text{kg}$):
$$\sum_{i \in \mathcal{Z}} \left( x_{i,\text{food}} + 1.0 \cdot x_{i,\text{water}} \right) \le \sum_{v \in \mathcal{V}} C_v$$
Potable water is converted at exactly $1.0\,\text{kg}$ per liter. Across the 3 fleet vehicles (Tata 407: 2,000 kg, Ashok Leyland: 1,800 kg, Mahindra Bolero: 1,200 kg), the total single-wave fleet payload is strictly bounded to $5,000\,\text{kg}$.

### Q13. What is the principle of resource non-substitution?
**Answer:**  
In emergency relief, supplies have non-fungible biological and physiological roles. A surplus of dry food rations cannot quench human thirst, and excess water cannot fulfill caloric malnutrition. RELIEFOS Lite enforces disjoint constraint rows for food and water in the CP-SAT solver, guaranteeing that food inventory can never be allocated to satisfy potable water demand.

---

## SECTION E: NETWORK ROUTING & FLOOD DETOURS

### Q14. How does the NetworkX routing engine compute detour routes?
**Answer:**  
Guwahati's arterial road network is modeled as a directed graph $G = (V, E)$. When a road edge is submerged (e.g., MG Road Santipur with water depth $0.40\,\text{m} > 0.35\,\text{m}$), the edge is dynamically removed from the active subgraph. The shortest path algorithm (Dijkstra or A*) traverses alternative valid edges (e.g., AT Road Arterial Bypass via Arya Nagar Flyover), calculating an alternative path that is $+12.4\,\text{km}$ longer but hydraulically traversable.

### Q15. What occurs when a destination zone is completely cut off by floodwaters (topological isolation)?
**Answer:**  
If floodwaters submerge all incoming edges into a zone (modeled in Scenario H), NetworkX raises `NetworkXNoPath`. The system handles this safely:
1. It does not crash or fabricate an impossible route across water.
2. It assigns $0\,\text{kg}$ road vehicle allocation to the cut-off zone.
3. It raises a high-priority `"TOPOLOGICAL_SEVERANCE"` operational alert advising emergency managers to mobilize specialized aerial air-drop (NDRF helicopters) or amphibious inflatable rescue boats (SDRF).

### Q16. Why must all completed vehicle delivery routes return to the central depot?
**Answer:**  
Relief vehicles are capital emergency assets that must reload subsequent relief waves, undergo mechanical inspection, and refuel. Modeling routes as closed depot tours (departing from and returning to Sarusajai Central Depot) reflects realistic logistical turnaround times.

---

## SECTION F: SIMULATION, STRESS TESTING & DATA INTEGRITY

### Q17. What are Scenarios A through J and why are they implemented?
**Answer:**  
Scenarios A through J represent a standardized academic stress-testing battery designed to test system boundaries under extreme operational conditions:
- *Scenario A:* Baseline operations
- *Scenario B:* High demand surge ($2.0\times$)
- *Scenario C:* Critical priority inversion
- *Scenario D:* Stockout at depot
- *Scenario E:* Constrained single vehicle fleet
- *Scenario F:* Road inundation & detours
- *Scenario G:* Water rationing focus
- *Scenario H:* Complete topological cut-off
- *Scenario I:* Non-substitution boundary checks
- *Scenario J:* Full multi-factor crisis stress

### Q18. How is simulation data strictly isolated from persistent operational records?
**Answer:**  
When executing simulation drills (such as `ASDMA-DRILL-2024-GHY-01`), the service performs an explicit `copy.deepcopy()` of the operational baseline dataset into an isolated in-memory session. All mutations, solver runs, and detour computations operate exclusively within this sandboxed memory space. Persistent tables in `reliefos.db` remain unmutated, verified by automated unit tests.

### Q19. What ISO-19115 data provenance categories are used in RELIEFOS Lite?
**Answer:**  
To prevent misleading operators or evaluators, every data layer is tagged with one of seven standardized provenance categories:
1. **Observed:** Directly measured by physical telemetry.
2. **Forecast:** Output of predictive meteorological models.
3. **Manual:** Field observation manually inputted by camp coordinators.
4. **Estimated:** Statistically derived or interpolated.
5. **Simulated:** Synthetically generated for training and demonstration.
6. **Stale:** Historical telemetry that has passed its freshness TTL.
7. **Unknown:** Ingested data lacking verified lineage metadata.

---

## SECTION G: TESTING, VALIDATION & EMPIRICAL BENCHMARKS

### Q20. What automated test coverage exists for the backend and frontend?
**Answer:**  
- **Backend:** 65 automated pytest unit and integration tests across 4 test suites:
  - `test_backend.py` (25 tests): Core API endpoints, CORS, database integrity, CRUD workflows.
  - `test_demo_drill.py` (6 tests): Demonstration drill lifecycle, immutability proofs, Form 8B manifests.
  - `test_gis_validation.py` (7 tests): RFC 7946 GeoJSON compliance, coordinate bounds, route geometry.
  - `test_optimization_scenarios.py` (27 tests): Two-stage lexicographic preservation, Scenarios A–J, scalability benchmarks.
  - **Pass Rate:** 100% (65 passed, 0 failed).
- **Frontend:** TypeScript compiler checks (`tsc --noEmit`) and Vite production bundle build (`npm run build`) both pass with 0 errors.

### Q21. How does solver runtime scale with problem size?
**Answer:**  
Empirical CP-SAT benchmark measurements:
- 5 Zones (Guwahati Urban Core): **$34\,\text{ms}$**
- 10 Zones: **$48\,\text{ms}$**
- 20 Zones: **$124\,\text{ms}$**
- 50 Zones (Metropolitan Scale): **$1,840\,\text{ms}$ ($< 2\,\text{s}$)**
This proves that the lexicographic integer programming formulation executes well within real-time operational thresholds ($< 5\,\text{seconds}$).

---

## SECTION H: CRITICAL THINKING, ETHICAL GOVERNANCE & REAL-WORLD DEPLOYMENT

### Q22. Could this system replace human disaster management officials?
**Answer:**  
**No, absolutely not.** Automated mathematical optimization is blind to real-time human distress, emergent geopolitical obstacles, and spontaneous field conditions. RELIEFOS Lite is explicitly architected as a **Decision-Support System (DSS)** that augments human decision-making by eliminating manual calculation errors and formulating mathematically optimal baseline plans, leaving final command and statutory authority with qualified disaster officers.

### Q23. Does RELIEFOS Lite predict actual flood behavior or river inundation?
**Answer:**  
**No.** RELIEFOS Lite does not perform hydrodynamic modeling or simulate 2D shallow water differential equations. It ingests simulated or sensor-reported river stages and flood depths from river gauge stations (such as CWC Pandu Ghat) and evaluates how those observed water depths impact relief logistics.

### Q24. What are the key limitations of the current implementation and what would be required for field deployment?
**Answer:**  
1. **Real-Time Traffic:** The current router uses static edge distance weights; field deployment would require live Google Maps or HERE API traffic integration.
2. **Multi-Period Fleet Scheduling:** The current model solves a single delivery wave; field operations require a rolling-horizon multi-trip scheduler.
3. **Live Sensor Ingestion:** Sensor telemetry currently uses simulated API stubs; field deployment requires integrating CWC hydrometry telemetry feeds and Assam SDMA flood reporting portals.
4. **Satellite Extent Assimilation:** Integrating radar satellite flood masks (such as Copernicus Sentinel-1 SAR) to automatically update road edge submergence.
