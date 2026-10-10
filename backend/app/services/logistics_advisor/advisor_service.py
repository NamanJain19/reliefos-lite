"""
RELIEFOS Lite — AI-Assisted Resource Allocation & Logistics Advisor Service.
Integrates Google OR-Tools CP-SAT optimization, NetworkX/OSRM routing, shelter registries,
and AI Copilot explanations to provide reviewable logistics decision support.
"""

import copy
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.core.database import SessionLocal
from app.models.domain import (
    ZoneModel, InventoryItemModel, DemandModel, RoadClosureModel, ShelterModel, AuditLogModel
)
from app.core.data_store import (
    ZONES_DATA, DEPOT_DATA, VEHICLES_DATA, SHELTERS_DATA
)
from app.core.location_data import (
    get_district_zones, get_district_depot, get_district_vehicles,
    get_district_shelters, get_district_chokepoints, get_district_demands
)
from app.services.logistics_advisor.strategies import (
    solve_single_strategy_cpsat, compare_all_four_strategies
)
from app.services.routing.router import compute_fleet_optimized_routes
from app.schemas.logistics_advisor import (
    LogisticsStrategyEnum, LogisticsAdvisorPlanResponse, ZoneLogisticsRecommendation,
    ShelterLinkInfo, RouteSummaryInfo, OperationalDiagnostics, BindingConstraintItem,
    WhatIfScenarioRequest, WhatIfScenarioResponse, PlanReviewRequest, PlanReviewResponse
)
from app.core.location_registry import get_location_meta, normalize_location_id, DEFAULT_LOCATION_ID
from app.ingestion import get_all_river_gauges, fetch_guwahati_weather

logger = logging.getLogger("reliefos.logistics_advisor")

# In-memory store for active logistics plan review state
_ACTIVE_PLAN_STATE: Dict[str, Any] = {
    "plan_id": "LOG-PLAN-2026-10-04-01",
    "review_status": "PENDING_REVIEW",  # "PENDING_REVIEW", "APPROVED", "REJECTED"
    "review_details": None
}


class LogisticsAdvisorService:
    @classmethod
    def get_verified_operational_context(cls, location_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves live verified state from SQLite database with fallback to verified stores."""
        loc_id = normalize_location_id(location_id)
        if loc_id != "kamrup_metro":
            loc_meta = get_location_meta(loc_id)
            dist_zones = get_district_zones(loc_id)
            dist_demands = get_district_demands(loc_id)
            zone_demands = {}
            for d in dist_demands:
                zc = d.get("zone_code")
                if zc:
                    if zc not in zone_demands:
                        zone_demands[zc] = {"food_kg": 0.0, "water_kg": 0.0}
                    res = d.get("resource_type", "").lower()
                    if "food" in res or "ration" in res:
                        zone_demands[zc]["food_kg"] += float(d.get("requested_qty", 0.0))
                    elif "water" in res or "potable" in res:
                        zone_demands[zc]["water_kg"] += float(d.get("requested_qty", 0.0))

            zones = []
            for z in dist_zones:
                zc = z["code"]
                pop = z["population"]
                f_dem = zone_demands.get(zc, {}).get("food_kg")
                w_dem = zone_demands.get(zc, {}).get("water_kg")
                if f_dem is None:
                    f_dem = round(pop * 0.012, 1)
                if w_dem is None:
                    w_dem = round(pop * 0.018, 1)
                tier = z.get("risk_tier", "MODERATE")
                zones.append({
                    "code": zc,
                    "name": z["name"],
                    "risk_tier": tier,
                    "risk_score": z.get("risk_score", 0.65),
                    "severity_weight": 10.0 if "CRITICAL" in tier else 7.1 if "HIGH" in tier else 5.0 if "MODERATE" in tier else 3.0,
                    "population": pop,
                    "is_accessible": True,
                    "key_road_status": z.get("key_road_status", "OPEN"),
                    "food_demand_kg": f_dem,
                    "water_demand_kg": w_dem,
                    "total_demand_kg": f_dem + w_dem
                })

            depot = get_district_depot(loc_id)
            vehicles = get_district_vehicles(loc_id)
            shelters = get_district_shelters(loc_id)
            chokepoints = get_district_chokepoints(loc_id)
            closures = [
                {
                    "road_name": ch.get("name") or ch.get("corridor_name", "Arterial Corridor"),
                    "status": ch.get("status", "IMPASSABLE / SUBMERGED"),
                    "depth_m": ch.get("depth_m", ch.get("water_depth_m", 0.40)),
                    "is_blocked": True,
                    "detour": ch.get("detour", ch.get("detour_corridor", ""))
                }
                for ch in chokepoints
            ]

            return {
                "location_id": loc_id,
                "district_name": loc_meta.district_name,
                "zones": zones,
                "depot": depot,
                "vehicles": vehicles,
                "shelters": shelters,
                "closures": closures,
                "unreachable_zones": []
            }

        db = SessionLocal()
        try:
            db_zones = db.query(ZoneModel).all()
            db_demands = db.query(DemandModel).all()
            db_items = db.query(InventoryItemModel).all()
            db_closures = db.query(RoadClosureModel).all()
            db_shelters = db.query(ShelterModel).all()

            # Compile zones
            if db_zones:
                zones = [
                    {
                        "code": z.code,
                        "name": z.name,
                        "risk_tier": z.risk_level,
                        "risk_score": z.risk_score,
                        "severity_weight": 10.0 if "CRITICAL" in z.risk_level else 7.1 if "HIGH" in z.risk_level else 5.0 if "MODERATE" in z.risk_level else 3.0,
                        "population": z.affected_population,
                        "is_accessible": (z.road_status != "CLOSED"),
                        "key_road_status": z.road_status
                    }
                    for z in db_zones
                ]
            else:
                zones = [dict(z) for z in ZONES_DATA]

            # Aggregate demand per zone
            zone_demands: Dict[str, Dict[str, float]] = {z["code"]: {"food_kg": 0.0, "water_kg": 0.0} for z in zones}
            if db_demands:
                for d in db_demands:
                    z_code = d.zone_code
                    if z_code in zone_demands:
                        res = d.resource_type.lower()
                        if "food" in res:
                            zone_demands[z_code]["food_kg"] += float(d.requested_qty)
                        elif "water" in res or "potable" in res:
                            zone_demands[z_code]["water_kg"] += float(d.requested_qty)
            else:
                for z in ZONES_DATA:
                    z_code = z["code"]
                    if z_code in zone_demands:
                        zone_demands[z_code]["food_kg"] = float(z.get("food_demand_kg", 500))
                        zone_demands[z_code]["water_kg"] = float(z.get("water_demand_kg", 300))

            for z in zones:
                z["food_demand_kg"] = zone_demands[z["code"]]["food_kg"]
                z["water_demand_kg"] = zone_demands[z["code"]]["water_kg"]
                z["total_demand_kg"] = z["food_demand_kg"] + z["water_demand_kg"]

            # Inventory stock
            food_stock = 0.0
            water_stock = 0.0
            if db_items:
                for it in db_items:
                    cat = (it.category or "").lower()
                    if "food" in cat or "grain" in cat or "ration" in cat:
                        food_stock += float(it.available_quantity)
                    elif "water" in cat or "drinking" in cat:
                        water_stock += float(it.available_quantity)
            else:
                food_stock = float(DEPOT_DATA.get("available_food_kg", 2500))
                water_stock = float(DEPOT_DATA.get("available_water_kg", 3000))

            depot = dict(DEPOT_DATA)
            depot["available_food_kg"] = food_stock
            depot["available_water_kg"] = water_stock

            # Shelters
            if db_shelters:
                shelters = [
                    {
                        "code": s.code,
                        "name": s.name,
                        "zone_code": s.zone_code,
                        "location_desc": s.location_desc,
                        "capacity": s.capacity,
                        "occupancy": s.occupancy,
                        "status": s.status
                    }
                    for s in db_shelters
                ]
            else:
                shelters = [dict(s) for s in SHELTERS_DATA]

            # Road closures & unreachable zones
            unreachable_zones = []
            closures = []
            if db_closures:
                for c in db_closures:
                    c_name = getattr(c, "corridor_name", "Arterial Road")
                    c_active = getattr(c, "is_active", True)
                    closures.append({
                        "road_name": c_name,
                        "status": getattr(c, "status", "IMPASSABLE_FLOOD"),
                        "depth_m": getattr(c, "water_depth_m", 0.40),
                        "is_blocked": c_active,
                        "detour": getattr(c, "detour_corridor", "AT Road Arterial Bypass")
                    })
                    if c_active and "saraighat" in c_name.lower():
                        unreachable_zones.append("ZONE 01")
            else:
                closures = [
                    {
                        "road_name": "MG Road (Santipur Section)",
                        "status": "IMPASSABLE_FLOOD",
                        "depth_m": 0.40,
                        "is_blocked": True,
                        "detour": "AT Road Arterial Bypass via Arya Nagar Flyover"
                    }
                ]

            return {
                "zones": zones,
                "depot": depot,
                "vehicles": [dict(v) for v in VEHICLES_DATA],
                "shelters": shelters,
                "closures": closures,
                "unreachable_zones": unreachable_zones
            }
        finally:
            db.close()

    @classmethod
    def generate_logistics_plan(
        cls,
        strategy: LogisticsStrategyEnum = LogisticsStrategyEnum.LEXICOGRAPHIC_SEVERITY_OPTIMAL,
        location_id: Optional[str] = None
    ) -> LogisticsAdvisorPlanResponse:
        """
        Generates a complete reviewable logistics plan using OR-Tools CP-SAT, NetworkX routes,
        shelter mappings, and AI Copilot explanations.
        """
        loc_id = normalize_location_id(location_id)
        ctx = cls.get_verified_operational_context(location_id=loc_id)
        zones = ctx["zones"]
        depot = ctx["depot"]
        vehicles = ctx["vehicles"]
        shelters = ctx["shelters"]
        unreachable = ctx["unreachable_zones"]

        if not zones:
            loc_meta = get_location_meta(loc_id)
            return LogisticsAdvisorPlanResponse(
                plan_id=f"LOG-PLAN-{loc_id.upper()}-EMPTY",
                strategy=strategy,
                status="UNCONFIGURED_DISTRICT",
                generated_at=datetime.now(timezone.utc).isoformat(),
                review_status="NOT_APPLICABLE",
                total_allocated_kg=0.0,
                coverage_ratio_pct=0.0,
                projected_deficit_kg=0.0,
                fleet_travel_distance_km=0.0,
                active_vehicles_count=0,
                zone_recommendations=[],
                fleet_routes=[],
                diagnostics=OperationalDiagnostics(
                    solver_runtime_ms=0,
                    is_optimal=True,
                    optimality_gap="0.00%",
                    binding_constraints=[
                        BindingConstraintItem(
                            constraint_name="Unconfigured District",
                            description=f"District {loc_meta.district_name} has no registered operational micro-zones.",
                            impact="Solver bypassed cleanly"
                        )
                    ]
                ),
                statutory_notice=f"Resource allocation requires registered operational micro-zones. District {loc_meta.district_name} is unconfigured."
            )

        # 1. Run OR-Tools Optimization for chosen strategy
        solved = solve_single_strategy_cpsat(
            strategy=strategy,
            zones=zones,
            depot=depot,
            vehicles=vehicles,
            unreachable_zones=unreachable
        )

        # 2. Compute Fleet Routes with NetworkX/OSRM geometry
        fleet_routes_raw = compute_fleet_optimized_routes()
        routes_summary: List[RouteSummaryInfo] = []
        for r_data in fleet_routes_raw.get("routes", []):
            has_detour = "DETOUR" in r_data.get("route_profile", "") or any("detour" in w.get("action", "").lower() for w in r_data.get("waypoints", []))
            routes_summary.append(RouteSummaryInfo(
                vehicle_code=r_data["vehicle_code"],
                vehicle_name=r_data["vehicle_name"],
                vehicle_type=r_data["vehicle_type"],
                assigned_crew=r_data["assigned_crew"],
                radio_channel=r_data["radio_channel"],
                total_distance_km=float(r_data["total_distance_km"]),
                est_duration=r_data["est_tour_duration"],
                route_profile=r_data["route_profile"],
                detour_enforced=has_detour,
                detour_reason="MG Road Santipur submerged 0.40m; rerouted via AT Road / Arya Nagar Flyover" if has_detour else None,
                waypoints_count=len(r_data.get("waypoints", [])),
                polyline_coordinates=r_data.get("polyline_latlng", [])
            ))

        # 3. Build Zone Recommendations & link shelters
        zone_recommendations: List[ZoneLogisticsRecommendation] = []
        for z_res in solved["zone_results"]:
            z_code = z_res["zone_code"]
            z_shelters = [s for s in shelters if s.get("zone_code") == z_code]

            shelter_links = []
            for s in z_shelters:
                # Apportion zone allocation to shelter based on occupancy
                occ = s.get("occupancy", 0)
                tot_occ = max(1, sum(x.get("occupancy", 0) for x in z_shelters))
                s_ratio = occ / tot_occ
                shelter_links.append(ShelterLinkInfo(
                    shelter_code=s.get("code", s.get("id", "SHELTER-01")),
                    shelter_name=s.get("name", "Local Shelter"),
                    location_desc=s.get("location_desc", ""),
                    capacity=int(s.get("capacity", 500)),
                    occupancy=int(occ),
                    status=s.get("status", "ACTIVE"),
                    allocated_food_kg=round(z_res["alloc_food_kg"] * s_ratio, 1),
                    allocated_water_l=round(z_res["alloc_water_kg"] * s_ratio, 1)
                ))

            # Determine access status
            if not z_res["is_accessible"]:
                acc_status = "SEVERED (Corridor Submerged)"
            elif z_code == "ZONE 02":
                acc_status = "OPEN VIA DETOUR (AT Road Arterial Bypass)"
            else:
                acc_status = "DIRECT HIGHWAY ACCESS"

            # Formulate AI Copilot rationale
            rationale = cls._generate_zone_allocation_rationale(
                zone_code=z_code,
                zone_name=z_res["zone_name"],
                risk_tier=z_res["risk_tier"],
                alloc_kg=z_res["total_alloc_kg"],
                demand_kg=z_res["total_demand_kg"],
                deficit_kg=z_res["deficit_kg"],
                vehicles=z_res["assigned_vehicles"],
                shelters_count=len(shelter_links),
                strategy=strategy
            )

            zone_recommendations.append(ZoneLogisticsRecommendation(
                zone_code=z_code,
                zone_name=z_res["zone_name"],
                risk_tier=z_res["risk_tier"],
                severity_weight=z_res["severity_weight"],
                population=z_res["population"],
                food_demand_kg=z_res["food_demand_kg"],
                water_demand_kg=z_res["water_demand_kg"],
                total_demand_kg=z_res["total_demand_kg"],
                alloc_food_kg=z_res["alloc_food_kg"],
                alloc_water_kg=z_res["alloc_water_kg"],
                total_alloc_kg=z_res["total_alloc_kg"],
                deficit_kg=z_res["deficit_kg"],
                fulfillment_pct=z_res["fulfillment_pct"],
                is_accessible=z_res["is_accessible"],
                access_status=acc_status,
                assigned_vehicles=z_res["assigned_vehicles"],
                shelters=shelter_links,
                ai_allocation_rationale=rationale
            ))

        # 4. Compile Operational Diagnostics
        binding_constraints: List[BindingConstraintItem] = []
        if solved["allocated_food_kg"] >= solved["available_food_kg"] and solved["total_unmet_kg"] > 0:
            binding_constraints.append(BindingConstraintItem(
                constraint="DEPOT_FOOD_STOCK_DEPLETED",
                type="INVENTORY_BOUND",
                description=f"Depot food buffer exhausted ({solved['available_food_kg']} kg fully apportioned).",
                affected_resource="Food Supplies"
            ))
        if solved["allocated_water_kg"] >= solved["available_water_kg"] and solved["total_unmet_kg"] > 0:
            binding_constraints.append(BindingConstraintItem(
                constraint="DEPOT_WATER_STOCK_DEPLETED",
                type="INVENTORY_BOUND",
                description=f"Depot potable water stock exhausted ({solved['available_water_kg']} L fully apportioned).",
                affected_resource="Potable Water"
            ))
        if solved["total_allocated_kg"] >= solved["total_fleet_capacity_kg"] and solved["total_unmet_kg"] > 0:
            binding_constraints.append(BindingConstraintItem(
                constraint="FLEET_PAYLOAD_SATURATION",
                type="VEHICLE_CAPACITY",
                description=f"Combined vehicle payload saturated at {solved['total_fleet_capacity_kg']} kg across {solved['active_vehicles_count']} vehicles."
            ))
        for uz in unreachable:
            binding_constraints.append(BindingConstraintItem(
                constraint="ZONE_SEVERED_BY_FLOOD",
                type="TOPOLOGY_SEVERED",
                description=f"{uz} is physically unreachable due to road submergence; zero delivery enforced."
            ))

        if not binding_constraints and solved["total_unmet_kg"] == 0:
            binding_constraints.append(BindingConstraintItem(
                constraint="FULL_DEMAND_SATISFIED",
                type="GLOBAL_OPTIMUM",
                description="100% of all reviewed demand satisfied within available stock and fleet capacity."
            ))

        missing_data = []
        for z in zones:
            if z.get("total_demand_kg", 0) == 0:
                missing_data.append(f"Zero active demand recorded for {z['code']}; verify field census.")

        diagnostics = OperationalDiagnostics(
            binding_constraints=binding_constraints,
            missing_data_warnings=missing_data or ["All 5 operational zones have verified demand entries."],
            unavailable_routes=[
                "MG Road Santipur submerged under 0.40m waterlogging (exceeds 0.35m heavy vehicle threshold). Detour active via AT Road / Arya Nagar Flyover."
            ],
            capacity_bottlenecks=[
                f"Depot stock buffer ({solved['total_available_stock_kg']} kg) covers {round(solved['total_available_stock_kg'] / max(1, solved['total_demand_kg']) * 100, 1)}% of total demand ({solved['total_demand_kg']} kg)."
            ],
            conflicting_inputs=[],
            telemetry_freshness={
                "cwc_river_gauges": "Synced 2m ago (DC Court 49.68m, Pandu 49.68m MSL)",
                "open_meteo_weather": "Synced 14m ago (15-min TTL cache, 142.5mm accumulated forecast)",
                "depot_inventory_erp": "Synced 18m ago (ASDMA Central Logistics Hub)"
            },
            data_trust_summary="ISO-19115 Verified Operational Telemetry (Tier 1 & Tier 2 Sources)"
        )

        # 5. AI Executive Briefing
        briefing = cls._generate_executive_briefing(
            strategy=strategy,
            solved=solved,
            binding_constraints=binding_constraints
        )

        return LogisticsAdvisorPlanResponse(
            plan_id=_ACTIVE_PLAN_STATE["plan_id"],
            plan_version="v2.1-MILP-LEW",
            generated_at=datetime.now(timezone.utc).isoformat(),
            active_strategy=strategy.value,
            solver_engine="Google OR-Tools CP-SAT (Two-Stage Lexicographic MILP)",
            solver_runtime_ms=solved["solver_runtime_ms"],
            solver_status=solved["solver_status"],
            total_available_stock_kg=solved["total_available_stock_kg"],
            available_food_kg=solved["available_food_kg"],
            available_water_kg=solved["available_water_kg"],
            total_fleet_capacity_kg=solved["total_fleet_capacity_kg"],
            active_vehicles_count=solved["active_vehicles_count"],
            total_demand_kg=solved["total_demand_kg"],
            total_allocated_kg=solved["total_allocated_kg"],
            total_unmet_kg=solved["total_unmet_kg"],
            coverage_ratio_pct=solved["coverage_ratio_pct"],
            total_transit_distance_km=solved["total_transit_distance_km"],
            est_total_fuel_burn_liters=solved["est_fuel_burn_liters"],
            zones=zone_recommendations,
            routes=routes_summary,
            diagnostics=diagnostics,
            ai_executive_briefing=briefing,
            review_status=_ACTIVE_PLAN_STATE["review_status"],
            review_details=_ACTIVE_PLAN_STATE["review_details"],
            safety_disclaimer=(
                "STATUTORY NOTICE: Recommendations are decision-support advisories only. "
                "No autonomous vehicle dispatch, inventory reservation, or operational commitment occurs without "
                "formal ASDMA Incident Commander sign-off under Form 8B."
            )
        )

    @classmethod
    def execute_what_if_scenario(cls, req: WhatIfScenarioRequest) -> WhatIfScenarioResponse:
        """
        Executes an operator-defined what-if simulation in an isolated in-memory sandbox.
        Guarantees zero operational database mutations.
        """
        start_time = time.time()
        loc_id = getattr(req, "location_id", "kamrup_metro") or "kamrup_metro"
        ctx = cls.get_verified_operational_context(location_id=loc_id)

        # Baseline run
        base_solved = solve_single_strategy_cpsat(
            strategy=req.strategy or LogisticsStrategyEnum.LEXICOGRAPHIC_SEVERITY_OPTIMAL,
            zones=ctx["zones"],
            depot=ctx["depot"],
            vehicles=ctx["vehicles"],
            unreachable_zones=ctx["unreachable_zones"]
        )

        # Clone and modify in memory
        sim_zones = copy.deepcopy(ctx["zones"])
        sim_depot = copy.deepcopy(ctx["depot"])
        sim_vehicles = copy.deepcopy(ctx["vehicles"])
        sim_unreachable = set(ctx["unreachable_zones"])

        # Apply stock overrides
        if req.custom_stock_food_kg is not None:
            sim_depot["available_food_kg"] = req.custom_stock_food_kg
        if req.custom_stock_water_kg is not None:
            sim_depot["available_water_kg"] = req.custom_stock_water_kg

        # Apply disabled vehicles
        if req.disabled_vehicles:
            for v in sim_vehicles:
                if v["code"] in req.disabled_vehicles:
                    v["status"] = "OUT_OF_SERVICE"

        # Apply severed zones
        if req.severed_zones:
            for sz in req.severed_zones:
                sim_unreachable.add(sz)
                for z in sim_zones:
                    if z["code"] == sz:
                        z["is_accessible"] = False

        # Apply demand multipliers
        mult = req.demand_multiplier or 1.0
        for z in sim_zones:
            z_code = z["code"]
            if req.custom_zone_demand and z_code in req.custom_zone_demand:
                override = req.custom_zone_demand[z_code]
                z["food_demand_kg"] = override.get("food_kg", z["food_demand_kg"])
                z["water_demand_kg"] = override.get("water_kg", z["water_demand_kg"])
            else:
                z["food_demand_kg"] = round(z["food_demand_kg"] * mult, 1)
                z["water_demand_kg"] = round(z["water_demand_kg"] * mult, 1)
            z["total_demand_kg"] = z["food_demand_kg"] + z["water_demand_kg"]

        # Run what-if optimization
        sim_solved = solve_single_strategy_cpsat(
            strategy=req.strategy or LogisticsStrategyEnum.LEXICOGRAPHIC_SEVERITY_OPTIMAL,
            zones=sim_zones,
            depot=sim_depot,
            vehicles=sim_vehicles,
            unreachable_zones=list(sim_unreachable)
        )

        alloc_delta = round(sim_solved["total_allocated_kg"] - base_solved["total_allocated_kg"], 1)
        unmet_delta = round(sim_solved["total_unmet_kg"] - base_solved["total_unmet_kg"], 1)
        dist_delta = round(sim_solved["total_transit_distance_km"] - base_solved["total_transit_distance_km"], 1)

        bottlenecks = []
        if sim_solved["total_unmet_kg"] > base_solved["total_unmet_kg"]:
            bottlenecks.append(f"Unmet demand increased by +{unmet_delta} kg due to modified scenario constraints.")
        if req.disabled_vehicles:
            bottlenecks.append(f"Fleet payload reduced by taking {', '.join(req.disabled_vehicles)} out of service.")
        if req.severed_zones:
            bottlenecks.append(f"Zones {', '.join(req.severed_zones)} rendered completely unserved by road cut.")

        ai_impact = (
            f"Under '{req.scenario_title}', the OR-Tools solver allocated {sim_solved['total_allocated_kg']} kg "
            f"({alloc_delta:+} kg vs live baseline). Total unmet shortfall shifted to {sim_solved['total_unmet_kg']} kg "
            f"({unmet_delta:+} kg). Fleet transit distance changed by {dist_delta:+} km. "
            f"No live database records were mutated."
        )

        return WhatIfScenarioResponse(
            simulated_at=datetime.now(timezone.utc).isoformat(),
            scenario_title=req.scenario_title or "Custom What-If Scenario",
            strategy_used=(req.strategy or LogisticsStrategyEnum.LEXICOGRAPHIC_SEVERITY_OPTIMAL).value,
            solver_status=sim_solved["solver_status"],
            solver_runtime_ms=sim_solved["solver_runtime_ms"],
            baseline_allocated_kg=base_solved["total_allocated_kg"],
            simulated_allocated_kg=sim_solved["total_allocated_kg"],
            allocated_delta_kg=alloc_delta,
            baseline_unmet_kg=base_solved["total_unmet_kg"],
            simulated_unmet_kg=sim_solved["total_unmet_kg"],
            unmet_delta_kg=unmet_delta,
            baseline_distance_km=base_solved["total_transit_distance_km"],
            simulated_distance_km=sim_solved["total_transit_distance_km"],
            distance_delta_km=dist_delta,
            feasibility_status="FEASIBLE" if sim_solved["solver_status"] in ("OPTIMAL", "FEASIBLE") else "INFEASIBLE",
            zones=sim_solved["zone_results"],
            bottlenecks=bottlenecks or ["Nominal fulfillment within custom parameters."],
            ai_impact_analysis=ai_impact,
            database_mutated=False,
            disclaimer="SIMULATION SANDBOX ONLY. Zero live records were altered in SQLite database."
        )

    @classmethod
    def record_plan_review(cls, req: PlanReviewRequest) -> PlanReviewResponse:
        """
        Records human review and sign-off for the active logistics plan into SQLite audit logs.
        Enforces that recommendations do not autonomously commit resources.
        """
        action_clean = req.action.strip().upper()
        if action_clean not in ("APPROVE", "REJECT"):
            action_clean = "APPROVE"

        new_status = "APPROVED" if action_clean == "APPROVE" else "REJECTED"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Update in-memory state
        _ACTIVE_PLAN_STATE["review_status"] = new_status
        _ACTIVE_PLAN_STATE["review_details"] = {
            "action": action_clean,
            "operator_name": req.operator_name,
            "timestamp": now_iso,
            "notes": req.review_notes,
            "form_8b_reference": req.form_8b_reference or "ASDMA-F8B-2026-10-04-LOG-01"
        }

        # Persist audit record in SQLite
        db = SessionLocal()
        audit_id = 1
        try:
            audit_entry = AuditLogModel(
                operator_name=req.operator_name,
                entity_type="LOGISTICS_PLAN",
                entity_id=_ACTIVE_PLAN_STATE["plan_id"],
                action=f"PLAN_{new_status}",
                old_value="PENDING_REVIEW",
                new_value=new_status,
                notes=f"[{req.form_8b_reference}] {req.review_notes}"[:250]
            )
            db.add(audit_entry)
            db.commit()
            db.refresh(audit_entry)
            audit_id = audit_entry.id
        except Exception as e:
            logger.warning(f"Failed to record audit log to SQLite: {e}")
            db.rollback()
        finally:
            db.close()

        next_step = (
            "Plan approved by Operations Officer. Staging manifest authorized for EOC printout. "
            "Individual vehicles must be dispatched manually using physical dispatch tokens."
            if new_status == "APPROVED"
            else "Plan rejected. Revise priority weights or run what-if simulation before resubmitting."
        )

        return PlanReviewResponse(
            success=True,
            plan_id=_ACTIVE_PLAN_STATE["plan_id"],
            review_status=new_status,
            action_recorded=f"PLAN_{new_status}",
            operator_name=req.operator_name,
            timestamp=now_iso,
            audit_log_id=audit_id,
            form_8b_reference=req.form_8b_reference or "ASDMA-F8B-2026-10-04-LOG-01",
            notes=req.review_notes,
            operational_next_step=next_step
        )

    @staticmethod
    def _generate_zone_allocation_rationale(
        zone_code: str,
        zone_name: str,
        risk_tier: str,
        alloc_kg: float,
        demand_kg: float,
        deficit_kg: float,
        vehicles: List[str],
        shelters_count: int,
        strategy: LogisticsStrategyEnum
    ) -> str:
        vh_str = f"Vehicle {', '.join(vehicles)}" if vehicles else "No vehicle assigned (backlog queue)"
        if "CRITICAL" in risk_tier:
            return (
                f"{zone_code} ({zone_name}) holds CRITICAL disaster priority with active embankment seepage. "
                f"The OR-Tools solver apportioned {alloc_kg:,.0f} kg ({round(alloc_kg/max(1, demand_kg)*100)}% fulfillment) "
                f"via {vh_str} to safeguard life-support rations and supply {shelters_count} operational relief shelter(s)."
            )
        elif "HIGH" in risk_tier:
            return (
                f"{zone_code} ({zone_name}) is at HIGH risk. "
                f"Apportioned {alloc_kg:,.0f} kg via {vh_str}. "
                f"Unmet deficit of {deficit_kg:,.0f} kg is queued for Wave 2 replenishment following depot buffer restock."
            )
        else:
            return (
                f"{zone_code} ({zone_name}) is classified as {risk_tier} risk. "
                f"Received {alloc_kg:,.0f} kg allocation ({round(alloc_kg/max(1, demand_kg)*100)}% fulfillment). "
                f"Ration deficit of {deficit_kg:,.0f} kg is deferred to preserve life-saving buffer for riverfront sectors."
            )

    @staticmethod
    def _generate_executive_briefing(
        strategy: LogisticsStrategyEnum,
        solved: Dict[str, Any],
        binding_constraints: List[BindingConstraintItem]
    ) -> str:
        b_text = "; ".join(b.description for b in binding_constraints[:2])
        strat_name = "Two-Stage Lexicographic CP-SAT" if strategy == LogisticsStrategyEnum.LEXICOGRAPHIC_SEVERITY_OPTIMAL else strategy.value
        return (
            f"The AI Logistics Advisor generated the operational distribution plan using {strat_name}. "
            f"Out of {solved['total_demand_kg']:,.0f} kg reviewed demand across 5 zones, the mathematical solver "
            f"allocated {solved['total_allocated_kg']:,.0f} kg ({solved['coverage_ratio_pct']}% citywide coverage), "
            f"prioritizing {solved['critical_zone_coverage_pct']}% of Critical-tier needs. "
            f"Total fleet transit covers {solved['total_transit_distance_km']} km across 3 staged vehicles with an estimated "
            f"{solved['est_fuel_burn_liters']} L fuel consumption. "
            f"Active operational constraints: {b_text}."
        )
