"""
RELIEFOS Lite — Operational Context Aggregation Service
Retrieves relevant, authorized data from database models and operational APIs.
Enforces explicit provenance labeling (LIVE, LAST_KNOWN, MANUAL, ESTIMATED, SIMULATED)
and data-quality classifications according to ISO-19115 standards.
Multi-location aware: compiles genuine context for the selected district without data leakage.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json

from app.core.database import SessionLocal
from app.models.domain import (
    ZoneModel, InventoryItemModel, DemandModel, RoadClosureModel, ShelterModel
)
from app.core.data_store import ZONES_DATA, INVENTORY_ITEMS_DATA, DEMAND_RECORDS_DATA, DEPOT_DATA
from app.core.location_registry import (
    get_location_meta, normalize_location_id, DEFAULT_LOCATION_ID
)
from app.ingestion import (
    fetch_location_weather, get_all_river_gauges, get_system_mode_status, DataSourceState
)
from app.services.optimization.solver import run_lexicographic_optimization
from app.schemas.ai import AIContextModule, ContextItem, AIContextPreviewResponse
from app.core.location_data import (
    get_district_zones, get_district_depot, get_district_shelters,
    get_district_vehicles, get_district_inventory, get_district_demands,
    get_district_chokepoints
)


class AIContextService:
    """Aggregates multi-source emergency operations context with strict provenance tagging."""

    @staticmethod
    def get_zones_context(target_zone_code: Optional[str] = None, location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        if loc_id == "kamrup_metro":
            db = SessionLocal()
            try:
                db_zones = db.query(ZoneModel).filter(
                    (ZoneModel.location_id == "kamrup_metro") | (ZoneModel.location_id == None)
                ).all()
                zones = [
                    {
                        "code": z.code,
                        "name": z.name,
                        "risk_level": z.risk_level,
                        "risk_score": z.risk_score,
                        "affected_population": z.affected_population,
                        "inundation_area_ha": z.inundation_area_ha,
                        "water_depth_m": z.water_depth_m,
                        "road_status": z.road_status
                    }
                    for z in db_zones
                ]
            except Exception:
                zones = []
            finally:
                db.close()

            if not zones:
                zones = [
                    {
                        "code": z["code"],
                        "name": z["name"],
                        "risk_level": z["risk_tier"],
                        "risk_score": z["risk_score"],
                        "affected_population": z["population"],
                        "inundation_area_ha": z["inundation_area_ha"],
                        "water_depth_m": z["avg_flood_depth_m"],
                        "road_status": z["key_road_status"]
                    }
                    for z in ZONES_DATA
                ]
        else:
            dist_zones = get_district_zones(loc_id)
            zones = [
                {
                    "code": z["code"],
                    "name": z["name"],
                    "risk_level": z["risk_tier"],
                    "risk_score": z["risk_score"],
                    "affected_population": z["population"],
                    "inundation_area_ha": z["inundation_area_ha"],
                    "water_depth_m": z["avg_flood_depth_m"],
                    "road_status": z["key_road_status"]
                }
                for z in dist_zones
            ]

        if target_zone_code:
            norm = target_zone_code.strip().upper()
            filtered = [z for z in zones if norm in z["code"].upper() or norm in z["name"].upper()]
            if filtered:
                zones = filtered

        summary = f"{len(zones)} operational sectors monitored in {loc_meta.district_name}. Highest risk: " + ", ".join(
            [f"{z['code']} ({z['risk_level']}, depth: {z['water_depth_m']}m)" for z in zones if z['risk_level'] in ('CRITICAL', 'HIGH')]
        )

        return ContextItem(
            domain="zones",
            title=f"Operational Flood Risk Zones ({loc_meta.district_name})",
            source_agency=f"ASDMA / DDMA {loc_meta.district_name}",
            provenance_state=DataSourceState.ESTIMATED.value,
            is_live=False,
            observation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            summary=summary,
            raw_metrics={"zones": zones, "location_id": loc_id}
        )

    @staticmethod
    def get_weather_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)
        try:
            weather = fetch_location_weather(loc_id)
            curr = weather.get("current", {})
            summary = (
                f"{loc_meta.district_name} current temp {curr.get('temperature_c')}°C, humidity {curr.get('humidity_pct')}%, "
                f"precip rate {curr.get('precipitation_rate_mm_h')} mm/h, condition: '{curr.get('weather_condition')}'. "
                f"Next 24h precip trend: {len(weather.get('forecast_24h', []))} hourly steps available."
            )
            return ContextItem(
                domain="weather",
                title=f"{loc_meta.district_name} Meteorology & Precipitation Forecast",
                source_agency=weather.get("source", "Open-Meteo NWP ECMWF/DWD"),
                provenance_state=weather.get("state", DataSourceState.LIVE.value),
                is_live=weather.get("is_live", True),
                observation_time=weather.get("observation_time", datetime.now(timezone.utc).isoformat()),
                summary=summary,
                raw_metrics=weather
            )
        except Exception as exc:
            return ContextItem(
                domain="weather",
                title=f"{loc_meta.district_name} Meteorology & Precipitation Forecast",
                source_agency="Open-Meteo Weather API",
                provenance_state=DataSourceState.UNAVAILABLE.value,
                is_live=False,
                observation_time="N/A",
                summary=f"Weather telemetry temporarily unavailable: {str(exc)}",
                raw_metrics={"error": str(exc)}
            )

    @staticmethod
    def get_gauges_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)
        gauges = get_all_river_gauges(location_id=loc_id)

        if not gauges:
            summary = f"No official CWC river gauge stations registered in {loc_meta.district_name}."
            prov = DataSourceState.UNAVAILABLE.value
        else:
            danger_count = sum(
                1 for g in gauges
                if g.get("current_level_m") is not None and g["current_level_m"] >= g.get("danger_level_m", 0)
            )
            monitored_readings = sum(1 for g in gauges if g.get("current_level_m") is not None)
            stations_str = ", ".join([f"{g.get('station_name')} ({g.get('river')})" for g in gauges[:2]])
            summary = (
                f"{len(gauges)} monitored CWC station(s) in {loc_meta.district_name} ({monitored_readings} with active telemetry, "
                f"{len(gauges) - monitored_readings} baseline reference posts). {danger_count} at or above danger mark. Stations: {stations_str}."
            )
            prov = DataSourceState.LAST_KNOWN.value if monitored_readings > 0 else DataSourceState.MANUAL.value

        return ContextItem(
            domain="gauges",
            title=f"{loc_meta.district_name} CWC River Hydrology Gauges",
            source_agency="Central Water Commission (CWC) Assam Regional Circle",
            provenance_state=prov,
            is_live=False,
            observation_time="Official CWC Bulletin Cycle",
            summary=summary,
            raw_metrics={"stations": gauges, "district": loc_meta.district_name}
        )

    @staticmethod
    def get_inventory_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        if loc_id == "kamrup_metro":
            db = SessionLocal()
            try:
                items = db.query(InventoryItemModel).filter(
                    (InventoryItemModel.location_id == "kamrup_metro") | (InventoryItemModel.location_id == None)
                ).all()
                inv_data = [
                    {
                        "sku": i.sku,
                        "name": i.name,
                        "category": i.category,
                        "available_qty": i.available_quantity,
                        "reserved_qty": i.reserved_quantity,
                        "total_qty": i.total_quantity,
                        "unit": i.unit,
                        "status": i.status
                    }
                    for i in items
                ]
            except Exception:
                inv_data = []
            finally:
                db.close()

            if not inv_data:
                inv_data = list(INVENTORY_ITEMS_DATA)
            depot_code = "DEPOT-GAU-01"
            depot_desc = "Sarusajai Central Depot Logistics Desk (DEPOT-GAU-01)"
            prov_state = DataSourceState.MANUAL.value
        else:
            inv_data = get_district_inventory(loc_id)
            depot = get_district_depot(loc_id)
            depot_code = depot["code"]
            depot_desc = f"{depot['name']} ({depot_code})"
            prov_state = DataSourceState.ESTIMATED.value

        total_food = sum(i.get("available_qty", 0) for i in inv_data if "food" in i.get("category", "").lower() or "ration" in i.get("category", "").lower())
        total_water = sum(i.get("available_qty", 0) for i in inv_data if "water" in i.get("category", "").lower())

        summary = (
            f"{loc_meta.district_name} active items: {len(inv_data)}. Available Food: {total_food} kg. "
            f"Available Potable Water: {total_water} L. Staged via {depot_desc}."
        )

        return ContextItem(
            domain="inventory",
            title=f"Consumable Relief Stock Ledger ({loc_meta.district_name})",
            source_agency=depot_desc,
            provenance_state=prov_state,
            is_live=False,
            observation_time="Current Shift Ledger",
            summary=summary,
            raw_metrics={"inventory_items": inv_data, "depot_code": depot_code, "location_id": loc_id}
        )

    @staticmethod
    def get_demands_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        if loc_id == "kamrup_metro":
            db = SessionLocal()
            try:
                demands = db.query(DemandModel).filter(
                    (DemandModel.location_id == "kamrup_metro") | (DemandModel.location_id == None)
                ).all()
                dem_list = [
                    {
                        "req_id": d.req_id,
                        "zone_code": d.zone_code,
                        "resource_type": d.resource_type,
                        "requested_qty": d.requested_qty,
                        "unit": d.unit,
                        "priority": d.priority,
                        "status": d.status,
                        "lifecycle_status": d.lifecycle_status
                    }
                    for d in demands
                ]
            except Exception:
                dem_list = []
            finally:
                db.close()

            if not dem_list:
                dem_list = list(DEMAND_RECORDS_DATA)
        else:
            dist_demands = get_district_demands(loc_id)
            dem_list = [
                {
                    "req_id": d["id"],
                    "zone_code": d["zone_code"],
                    "resource_type": d["resource_type"],
                    "requested_qty": d["requested_qty"],
                    "unit": d["unit"],
                    "priority": d["priority"],
                    "status": d["status"],
                    "lifecycle_status": "QUEUED"
                }
                for d in dist_demands
            ]

        crit_count = sum(1 for d in dem_list if d.get("priority") == "CRITICAL")
        summary = f"{len(dem_list)} active requisitions in {loc_meta.district_name}. {crit_count} Critical Priority requests requiring Stage 1 optimization."

        return ContextItem(
            domain="demands",
            title=f"Verified Relief Demand Requisitions ({loc_meta.district_name})",
            source_agency=f"ASDMA Field Coordinators & DDMA {loc_meta.district_name}",
            provenance_state=DataSourceState.MANUAL.value,
            is_live=False,
            observation_time="Current Operations Cycle",
            summary=summary,
            raw_metrics={"demands": dem_list, "location_id": loc_id}
        )

    @staticmethod
    def get_roads_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        db = SessionLocal()
        try:
            closures = db.query(RoadClosureModel).filter(
                RoadClosureModel.is_active == True,
                RoadClosureModel.location_id == loc_id
            ).all()
            close_list = [
                {
                    "corridor": c.corridor_name,
                    "location": c.location_desc,
                    "water_depth_m": c.water_depth_m,
                    "threshold_m": c.clearance_threshold_m,
                    "status": c.status,
                    "detour": c.detour_corridor
                }
                for c in closures
            ]
        except Exception:
            close_list = []
        finally:
            db.close()

        if not close_list:
            chokepoints = get_district_chokepoints(loc_id)
            close_list = [
                {
                    "corridor": ch.get("name") or ch.get("corridor_name", "Arterial Road"),
                    "location": ch.get("location_desc", f"{loc_meta.district_name} Corridor"),
                    "water_depth_m": ch.get("depth_m", ch.get("water_depth_m", 0.40)),
                    "threshold_m": ch.get("clearance_threshold_m", 0.35),
                    "status": ch.get("status", "IMPASSABLE / SUBMERGED"),
                    "detour": ch.get("detour", ch.get("detour_corridor", ""))
                }
                for ch in chokepoints
            ]

        if close_list:
            top = close_list[0]
            summary = (
                f"{len(close_list)} active road closures recorded in {loc_meta.district_name}. Major chokepoint: {top['corridor']} "
                f"under {top['water_depth_m']}m water. Detour: {top.get('detour') or 'Alternative arterial'}."
            )
        else:
            summary = f"No active impassable road closures recorded in {loc_meta.district_name}."

        return ContextItem(
            domain="roads",
            title=f"Road Inundation & Chokepoint Registry ({loc_meta.district_name})",
            source_agency=f"PWD Roads Assam & {loc_meta.district_name} Administration",
            provenance_state=DataSourceState.MANUAL.value,
            is_live=False,
            observation_time="Verified Operational Shift",
            summary=summary,
            raw_metrics={"closures": close_list, "location_id": loc_id}
        )

    @staticmethod
    def get_allocation_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        try:
            if loc_id == "kamrup_metro":
                plan = run_lexicographic_optimization()
            else:
                zones = get_district_zones(loc_id)
                depot = get_district_depot(loc_id)
                vehicles = get_district_vehicles(loc_id)
                plan = run_lexicographic_optimization(zones=zones, depot=depot, vehicles=vehicles)

            summary = (
                f"Google OR-Tools CP-SAT ({loc_meta.district_name}): Coverage {plan.get('coverage_ratio_pct', 0)}%, "
                f"Proposed Allocation: {plan.get('proposed_allocation_kg', 0)} kg, "
                f"Projected Unmet Deficit: {plan.get('projected_deficit_kg', 0)} kg across {len(plan.get('allocations', []))} zones."
            )
            return ContextItem(
                domain="allocation",
                title=f"Current Optimal Allocation Plan ({loc_meta.district_name})",
                source_agency="Google OR-Tools CP-SAT Solver v9.8",
                provenance_state=DataSourceState.ESTIMATED.value,
                is_live=False,
                observation_time="Latest Execution",
                summary=summary,
                raw_metrics=plan
            )
        except Exception as exc:
            return ContextItem(
                domain="allocation",
                title=f"Current Optimal Allocation Plan ({loc_meta.district_name})",
                source_agency="Optimization Engine",
                provenance_state=DataSourceState.UNAVAILABLE.value,
                is_live=False,
                observation_time="N/A",
                summary=f"Allocation plan unavailable: {str(exc)}",
                raw_metrics={"error": str(exc), "location_id": loc_id}
            )

    @staticmethod
    def get_system_mode_context() -> ContextItem:
        mode_data = get_system_mode_status()
        summary = (
            f"Active Operating Mode: {mode_data.get('mode')}. "
            f"Isolation Guarantee: {mode_data.get('isolation_guarantee')}."
        )
        return ContextItem(
            domain="system_mode",
            title="System Operational Mode & Isolation",
            source_agency="RELIEFOS Lite Mode Controller",
            provenance_state=DataSourceState.LIVE.value,
            is_live=True,
            observation_time=mode_data.get("switched_at", datetime.now(timezone.utc).isoformat()),
            summary=summary,
            raw_metrics=mode_data
        )

    @classmethod
    def compile_full_context(
        cls,
        modules: Optional[List[AIContextModule]] = None,
        target_zone_code: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> AIContextPreviewResponse:
        """Compiles specified or all operational context items into a structured context bundle."""
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        module_set = set(modules) if modules else {
            AIContextModule.ZONES,
            AIContextModule.WEATHER,
            AIContextModule.GAUGES,
            AIContextModule.INVENTORY,
            AIContextModule.DEMANDS,
            AIContextModule.ROADS,
            AIContextModule.ALLOCATION,
            AIContextModule.SYSTEM_MODE,
        }

        items: List[ContextItem] = []

        if AIContextModule.SYSTEM_MODE in module_set:
            items.append(cls.get_system_mode_context())
        if AIContextModule.ZONES in module_set:
            items.append(cls.get_zones_context(target_zone_code, location_id=loc_id))
        if AIContextModule.WEATHER in module_set:
            items.append(cls.get_weather_context(location_id=loc_id))
        if AIContextModule.GAUGES in module_set:
            items.append(cls.get_gauges_context(location_id=loc_id))
        if AIContextModule.INVENTORY in module_set:
            items.append(cls.get_inventory_context(location_id=loc_id))
        if AIContextModule.DEMANDS in module_set:
            items.append(cls.get_demands_context(location_id=loc_id))
        if AIContextModule.ROADS in module_set:
            items.append(cls.get_roads_context(location_id=loc_id))
        if AIContextModule.ALLOCATION in module_set:
            items.append(cls.get_allocation_context(location_id=loc_id))

        prov_dist: Dict[str, int] = {}
        for it in items:
            prov_dist[it.provenance_state] = prov_dist.get(it.provenance_state, 0) + 1

        mode_status = get_system_mode_status()

        return AIContextPreviewResponse(
            system_mode=mode_status.get("mode", "OPERATIONAL_LIVE"),
            compiled_at=datetime.now(timezone.utc).isoformat(),
            total_domains_compiled=len(items),
            provenance_distribution=prov_dist,
            context_items=items
        )

    @classmethod
    def serialize_context_for_prompt(
        cls,
        modules: Optional[List[AIContextModule]] = None,
        target_zone_code: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> str:
        """Serializes compiled context into clean JSON for the LLM prompt enclosure."""
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)
        preview = cls.compile_full_context(modules, target_zone_code, location_id=loc_id)

        payload = {
            "selected_location": {
                "location_id": loc_id,
                "district_name": loc_meta.district_name,
                "operational_tier": loc_meta.operational_tier,
                "tier_badge": loc_meta.tier_badge,
                "data_availability": loc_meta.data_availability
            },
            "system_mode": preview.system_mode,
            "compiled_at": preview.compiled_at,
            "operational_domains": [
                {
                    "domain": item.domain,
                    "title": item.title,
                    "source": item.source_agency,
                    "provenance_state": item.provenance_state,
                    "observation_time": item.observation_time,
                    "summary": item.summary,
                    "metrics": item.raw_metrics
                }
                for item in preview.context_items
            ]
        }
        return json.dumps(payload, indent=2)
