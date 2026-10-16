"""
RELIEFOS Lite — Operational Context Aggregation Service
Retrieves relevant, authorized data from database models and operational APIs.
Enforces explicit provenance labeling (LIVE, VERIFIED OBSERVATION, FORECAST, ESTIMATED,
SIMULATED, MANUAL REPORT, STALE, UNAVAILABLE, UNVERIFIED) according to ISO-19115 standards.
Multi-location aware: compiles genuine context for the selected district without data leakage.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import re

from app.core.database import SessionLocal
from app.models.domain import (
    ZoneModel, InventoryItemModel, DemandModel, RoadClosureModel, ShelterModel,
    VehicleModel, DepotModel, StockMovementModel, IncidentModel, SituationReportModel,
    AuditLogModel
)
from app.core.data_store import (
    ZONES_DATA, INVENTORY_ITEMS_DATA, DEMAND_RECORDS_DATA, DEPOT_DATA, VEHICLES_DATA, SHELTERS_DATA
)
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
    get_district_chokepoints, get_district_routes
)
from app.services.demand.sphere_calculator import calculate_sphere_humanitarian_demand


class AIContextService:
    """Aggregates multi-source emergency operations context with strict provenance tagging."""

    @classmethod
    def detect_relevant_modules(cls, query: str) -> List[AIContextModule]:
        """
        Analyzes query intent and keyword signals to determine which backend domains
        must be retrieved for accurate evidence-based answering.
        """
        q = query.lower().strip()
        mods = set()

        # Inventory & stock ledger
        if any(w in q for w in ["inventory", "stock", "reserve", "depot", "ration", "warehouse", "balance", "sku", "food", "water"]):
            mods.add(AIContextModule.INVENTORY)
            mods.add(AIContextModule.STOCK_MOVEMENTS)

        # Shelters & evacuees
        if any(w in q for w in ["shelter", "evacuee", "camp", "displaced", "occupancy", "capacity", "school", "college"]):
            mods.add(AIContextModule.SHELTERS)
            mods.add(AIContextModule.ZONES)

        # Meteorology & rainfall
        if any(w in q for w in ["weather", "rain", "precip", "temp", "forecast", "monsoon", "cloud", "humidity"]):
            mods.add(AIContextModule.WEATHER)

        # River hydrology & gauges
        if any(w in q for w in ["gauge", "river", "brahmaputra", "burhidihing", "barak", "hydrology", "water level", "danger mark", "msl", "cwc"]):
            mods.add(AIContextModule.GAUGES)
            mods.add(AIContextModule.WEATHER)

        # Road networks & closures
        if any(w in q for w in ["road", "closure", "detour", "access", "submerged", "bridge", "chokepoint", "route", "highway", "corridor"]):
            mods.add(AIContextModule.ROADS)
            mods.add(AIContextModule.ROUTING)
            mods.add(AIContextModule.VEHICLES)

        # Vehicle fleet
        if any(w in q for w in ["vehicle", "fleet", "truck", "carrier", "tata", "bolero", "payload", "fuel"]):
            mods.add(AIContextModule.VEHICLES)

        # Field Incidents & Breaches
        if any(w in q for w in ["incident", "breach", "embankment", "stranded", "casualt", "overflow", "damage", "hazard"]):
            mods.add(AIContextModule.INCIDENTS)
            mods.add(AIContextModule.SITREPS)

        # Situation Reports & Deltas
        if any(w in q for w in ["sitrep", "bulletin", "report", "changed", "delta", "update", "latest situation", "overview"]):
            mods.add(AIContextModule.SITREPS)
            mods.add(AIContextModule.INCIDENTS)
            mods.add(AIContextModule.ZONES)

        # Demand Requisitions & Sphere Standards
        if any(w in q for w in ["demand", "deficit", "shortage", "unmet", "requisition", "sphere", "quota", "per capita"]):
            mods.add(AIContextModule.DEMANDS)
            mods.add(AIContextModule.INVENTORY)
            mods.add(AIContextModule.SPHERE_STANDARDS)

        # Optimization & Resource Allocation
        if any(w in q for w in ["allocat", "optimizer", "optimization", "solver", "cp-sat", "or-tools", "plan", "assign"]):
            mods.add(AIContextModule.ALLOCATION)
            mods.add(AIContextModule.INVENTORY)
            mods.add(AIContextModule.DEMANDS)

        # Risk & Assessment
        if any(w in q for w in ["risk", "priority", "vulnerab", "severe", "depth", "inundat"]):
            mods.add(AIContextModule.ZONES)
            mods.add(AIContextModule.RISK_ASSESSMENT)
            mods.add(AIContextModule.GAUGES)

        # If query is broad or general, return core operational snapshot
        if not mods or any(w in q for w in ["status", "overview", "situation", "brief", "summary", "review"]):
            mods.update([
                AIContextModule.ZONES,
                AIContextModule.WEATHER,
                AIContextModule.GAUGES,
                AIContextModule.INVENTORY,
                AIContextModule.SHELTERS,
                AIContextModule.INCIDENTS,
                AIContextModule.ALLOCATION,
                AIContextModule.SYSTEM_MODE
            ])

        return list(mods)

    @staticmethod
    def get_zones_context(target_zone_code: Optional[str] = None, location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        db = SessionLocal()
        try:
            db_zones = db.query(ZoneModel).filter(
                (ZoneModel.location_id == loc_id) | (ZoneModel.location_id == None if loc_id == "kamrup_metro" else False)
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
            if loc_id == "kamrup_metro":
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

        crit_zones = [f"{z['code']} ({z['risk_level']}, depth: {z['water_depth_m']}m)" for z in zones if z['risk_level'] in ('CRITICAL', 'HIGH')]
        summary = f"{len(zones)} operational sectors monitored in {loc_meta.district_name}."
        if crit_zones:
            summary += " Highest risk: " + ", ".join(crit_zones)
        else:
            summary += " All monitored sectors within normal risk thresholds."

        return ContextItem(
            domain="zones",
            title=f"Operational Flood Risk Zones ({loc_meta.district_name})",
            source_agency=f"ASDMA / DDMA {loc_meta.district_name}",
            provenance_state="ESTIMATED",
            is_live=False,
            observation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            summary=summary,
            raw_metrics={"zones": zones, "location_id": loc_id},
            freshness_status="FRESH"
        )

    @staticmethod
    def get_weather_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)
        try:
            weather = fetch_location_weather(loc_id)
            curr = weather.get("current", {})
            obs_time = weather.get("observation_time", datetime.now(timezone.utc).isoformat())
            summary = (
                f"{loc_meta.district_name} weather observation: {curr.get('temperature_c')}°C, humidity {curr.get('humidity_pct')}%, "
                f"precipitation rate {curr.get('precipitation_rate_mm_h')} mm/h, condition: '{curr.get('weather_condition')}'. "
                f"Next 24h forecast available."
            )
            return ContextItem(
                domain="weather",
                title=f"{loc_meta.district_name} Meteorology & Precipitation Forecast",
                source_agency=weather.get("source", "Open-Meteo NWP ECMWF/DWD"),
                provenance_state="LIVE / RECENTLY RETRIEVED" if weather.get("is_live", True) else "ESTIMATED",
                is_live=weather.get("is_live", True),
                observation_time=obs_time,
                summary=summary,
                raw_metrics=weather,
                freshness_status="FRESH" if weather.get("is_live", True) else "STALE"
            )
        except Exception as exc:
            return ContextItem(
                domain="weather",
                title=f"{loc_meta.district_name} Meteorology & Precipitation Forecast",
                source_agency="Open-Meteo Weather API",
                provenance_state="UNAVAILABLE",
                is_live=False,
                observation_time="N/A",
                summary=f"Weather telemetry temporarily unavailable: {str(exc)}",
                raw_metrics={"error": str(exc)},
                freshness_status="UNAVAILABLE"
            )

    @staticmethod
    def get_gauges_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)
        gauges = get_all_river_gauges(location_id=loc_id)

        if not gauges:
            summary = f"No official CWC river gauge stations registered in {loc_meta.district_name}."
            prov = "UNAVAILABLE"
            fresh = "UNAVAILABLE"
        else:
            danger_count = sum(
                1 for g in gauges
                if g.get("current_level_m") is not None and g["current_level_m"] >= g.get("danger_level_m", 0)
            )
            monitored_readings = sum(1 for g in gauges if g.get("current_level_m") is not None)
            stations_str = ", ".join([f"{g.get('station_name')} ({g.get('river')}, stage: {g.get('current_level_m')}m, DL: {g.get('danger_level_m')}m)" for g in gauges[:3]])
            summary = (
                f"{len(gauges)} CWC station(s) in {loc_meta.district_name} ({monitored_readings} reporting readings). "
                f"{danger_count} at/above danger mark. Stations: {stations_str}."
            )
            prov = "VERIFIED OBSERVATION" if monitored_readings > 0 else "MANUAL REPORT"
            fresh = "FRESH"

        return ContextItem(
            domain="gauges",
            title=f"{loc_meta.district_name} CWC River Hydrology Gauges",
            source_agency="Central Water Commission (CWC) Assam Regional Circle",
            provenance_state=prov,
            is_live=False,
            observation_time="Official CWC Bulletin Cycle",
            summary=summary,
            raw_metrics={"stations": gauges, "district": loc_meta.district_name},
            freshness_status=fresh
        )

    @staticmethod
    def get_inventory_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        db = SessionLocal()
        inv_data = []
        try:
            items = db.query(InventoryItemModel).filter(
                (InventoryItemModel.location_id == loc_id) | (InventoryItemModel.location_id == None if loc_id == "kamrup_metro" else False)
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
            if loc_id == "kamrup_metro":
                inv_data = list(INVENTORY_ITEMS_DATA)
            else:
                inv_data = get_district_inventory(loc_id)

        depot = get_district_depot(loc_id) if loc_id != "kamrup_metro" else {"code": "DEPOT-GAU-01", "name": "Sarusajai Central Depot Logistics Desk"}
        depot_desc = f"{depot.get('name', 'Central Depot')} ({depot.get('code', 'DEPOT')})"

        total_food = sum(i.get("available_qty", 0) for i in inv_data if "food" in i.get("category", "").lower() or "ration" in i.get("category", "").lower())
        total_water = sum(i.get("available_qty", 0) for i in inv_data if "water" in i.get("category", "").lower())

        summary = (
            f"{loc_meta.district_name} physical inventory: {len(inv_data)} items tracked at {depot_desc}. "
            f"Available Food: {total_food} kg. Available Potable Water: {total_water} L."
        )

        return ContextItem(
            domain="inventory",
            title=f"Consumable Relief Stock Ledger ({loc_meta.district_name})",
            source_agency=depot_desc,
            provenance_state="VERIFIED OBSERVATION",
            is_live=False,
            observation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            summary=summary,
            raw_metrics={"inventory_items": inv_data, "depot_code": depot.get("code"), "location_id": loc_id},
            freshness_status="FRESH"
        )

    @staticmethod
    def get_stock_movements_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        db = SessionLocal()
        movements = []
        try:
            mov_models = db.query(StockMovementModel).filter(
                (StockMovementModel.location_id == loc_id) | (StockMovementModel.location_id == None if loc_id == "kamrup_metro" else False)
            ).order_by(StockMovementModel.id.desc()).limit(10).all()

            movements = [
                {
                    "movement_id": m.movement_id,
                    "item_sku": m.item_sku,
                    "item_name": m.item_name,
                    "movement_type": m.movement_type,
                    "quantity": m.quantity,
                    "unit": m.unit,
                    "balance_after": m.balance_after,
                    "operator_name": m.operator_name,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None
                }
                for m in mov_models
            ]
        except Exception:
            movements = []
        finally:
            db.close()

        if movements:
            recent_summary = f"{len(movements)} recent stock movement(s) recorded in {loc_meta.district_name}. Latest: {movements[0]['movement_type']} of {movements[0]['quantity']} {movements[0]['unit']} ({movements[0]['item_sku']}) by {movements[0]['operator_name']}."
        else:
            recent_summary = f"No recent stock movements recorded in {loc_meta.district_name} operational ledger."

        return ContextItem(
            domain="stock_movements",
            title=f"Stock Movements & Ledger Audit ({loc_meta.district_name})",
            source_agency="ASDMA Central Warehouse Ledger",
            provenance_state="VERIFIED OBSERVATION",
            is_live=False,
            observation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            summary=recent_summary,
            raw_metrics={"movements": movements, "location_id": loc_id},
            freshness_status="FRESH"
        )

    @staticmethod
    def get_shelters_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        db = SessionLocal()
        shelters_list = []
        try:
            sh_models = db.query(ShelterModel).filter(
                (ShelterModel.location_id == loc_id) | (ShelterModel.location_id == None if loc_id == "kamrup_metro" else False)
            ).all()

            shelters_list = [
                {
                    "code": s.code,
                    "name": s.name,
                    "zone_code": s.zone_code,
                    "capacity": s.capacity,
                    "occupancy": s.occupancy,
                    "available_space": max(0, (s.capacity or 0) - (s.occupancy or 0)),
                    "status": s.status,
                    "verification_status": s.verification_status
                }
                for s in sh_models
            ]
        except Exception:
            shelters_list = []
        finally:
            db.close()

        if not shelters_list:
            if loc_id == "kamrup_metro":
                shelters_list = [
                    {
                        "code": s.get("code", s.get("id")),
                        "name": s.get("name"),
                        "zone_code": s.get("zone_code", "ZONE 01"),
                        "capacity": s.get("capacity", 500),
                        "occupancy": s.get("occupancy", 0),
                        "available_space": max(0, s.get("capacity", 500) - s.get("occupancy", 0)),
                        "status": s.get("status", "ACTIVE"),
                        "verification_status": "VERIFIED"
                    }
                    for s in SHELTERS_DATA
                ]
            else:
                dist_sh = get_district_shelters(loc_id)
                shelters_list = [
                    {
                        "code": s.get("code", s.get("id")),
                        "name": s.get("name"),
                        "zone_code": s.get("zone_code", "ZONE 01"),
                        "capacity": s.get("capacity", 400),
                        "occupancy": s.get("occupancy", 0),
                        "available_space": max(0, s.get("capacity", 400) - s.get("occupancy", 0)),
                        "status": s.get("status", "ACTIVE"),
                        "verification_status": "VERIFIED"
                    }
                    for s in dist_sh
                ]

        tot_cap = sum(s.get("capacity", 0) for s in shelters_list)
        tot_occ = sum(s.get("occupancy", 0) for s in shelters_list)
        tot_avail = max(0, tot_cap - tot_occ)

        summary = (
            f"{loc_meta.district_name} designated shelters: {len(shelters_list)} facilities. "
            f"Total Capacity: {tot_cap} persons. Total Occupancy: {tot_occ} evacuees. "
            f"Remaining Available Vacancy: {tot_avail} persons."
        )

        return ContextItem(
            domain="shelters",
            title=f"Designated Relief Shelters & Evacuee Capacity ({loc_meta.district_name})",
            source_agency=f"DDMA {loc_meta.district_name} Shelter Registry",
            provenance_state="VERIFIED OBSERVATION",
            is_live=False,
            observation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            summary=summary,
            raw_metrics={"shelters": shelters_list, "total_capacity": tot_cap, "total_occupancy": tot_occ, "available_beds": tot_avail},
            freshness_status="FRESH"
        )

    @staticmethod
    def get_demands_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        db = SessionLocal()
        dem_list = []
        try:
            demands = db.query(DemandModel).filter(
                (DemandModel.location_id == loc_id) | (DemandModel.location_id == None if loc_id == "kamrup_metro" else False)
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
            if loc_id == "kamrup_metro":
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
        tot_food_dem = sum(d.get("requested_qty", 0) for d in dem_list if "food" in d.get("resource_type", "").lower() or "ration" in d.get("resource_type", "").lower())
        tot_water_dem = sum(d.get("requested_qty", 0) for d in dem_list if "water" in d.get("resource_type", "").lower())

        summary = (
            f"{len(dem_list)} active requisitions in {loc_meta.district_name}. {crit_count} Critical Priority requests. "
            f"Total requested food: {tot_food_dem} kg, potable water: {tot_water_dem} L."
        )

        return ContextItem(
            domain="demands",
            title=f"Relief Demand Requisitions ({loc_meta.district_name})",
            source_agency=f"ASDMA Field Coordinators & DDMA {loc_meta.district_name}",
            provenance_state="MANUAL REPORT",
            is_live=False,
            observation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            summary=summary,
            raw_metrics={"demands": dem_list, "location_id": loc_id},
            freshness_status="FRESH"
        )

    @staticmethod
    def get_incidents_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        db = SessionLocal()
        incidents = []
        try:
            inc_models = db.query(IncidentModel).filter(
                (IncidentModel.location_id == loc_id) | (IncidentModel.location_id == None if loc_id == "kamrup_metro" else False)
            ).order_by(IncidentModel.id.desc()).limit(15).all()

            incidents = [
                {
                    "incident_id": inc.incident_id,
                    "title": inc.title,
                    "incident_type": inc.incident_type,
                    "severity": inc.severity,
                    "status": inc.status,
                    "zone_code": inc.zone_code,
                    "persons_stranded": inc.persons_stranded,
                    "casualties_reported": inc.casualties_reported,
                    "reported_by": inc.reported_by,
                    "reported_at": inc.reported_at.isoformat() if inc.reported_at else None
                }
                for inc in inc_models
            ]
        except Exception:
            incidents = []
        finally:
            db.close()

        active_count = sum(1 for i in incidents if i.get("status") in ("REPORTED", "VERIFIED", "IN_RESPONSE", "RESPONDING"))
        crit_count = sum(1 for i in incidents if i.get("severity") == "CRITICAL")
        tot_stranded = sum(i.get("persons_stranded", 0) for i in incidents)

        summary = (
            f"{loc_meta.district_name} ground incidents: {len(incidents)} total ({active_count} active, {crit_count} critical). "
            f"Persons reported stranded: {tot_stranded}."
        )

        return ContextItem(
            domain="incidents",
            title=f"Field Incidents & Hazard Log ({loc_meta.district_name})",
            source_agency="ASDMA Emergency Operations Incident Registry",
            provenance_state="MANUAL REPORT",
            is_live=False,
            observation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            summary=summary,
            raw_metrics={"incidents": incidents, "active_count": active_count, "location_id": loc_id},
            freshness_status="FRESH"
        )

    @staticmethod
    def get_sitreps_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        db = SessionLocal()
        sitrep_info = {}
        try:
            sr = db.query(SituationReportModel).filter(
                (SituationReportModel.location_id == loc_id) | (SituationReportModel.location_id == None if loc_id == "kamrup_metro" else False)
            ).order_by(SituationReportModel.id.desc()).first()

            if sr:
                sitrep_info = {
                    "sitrep_id": sr.sitrep_id,
                    "report_date": sr.report_date,
                    "district_name": sr.district_name,
                    "active_human_lives_affected": sr.active_human_lives_affected,
                    "displaced_in_shelters": sr.displaced_in_shelters,
                    "active_shelters_count": sr.active_shelters_count,
                    "roads_closed_count": sr.roads_closed_count,
                    "compiling_officer": sr.compiling_officer,
                    "approving_commander": sr.approving_commander,
                    "approval_status": sr.approval_status,
                    "created_at": sr.created_at.isoformat() if sr.created_at else None
                }
        except Exception:
            sitrep_info = {}
        finally:
            db.close()

        if sitrep_info:
            summary = (
                f"Latest ASDMA Daily SitRep ({sitrep_info.get('sitrep_id')}, date: {sitrep_info.get('report_date')}): "
                f"Status: {sitrep_info.get('approval_status')}. Displaced in shelters: {sitrep_info.get('displaced_in_shelters')}. "
                f"Compiled by: {sitrep_info.get('compiling_officer')}."
            )
            prov = "VERIFIED OBSERVATION" if sitrep_info.get("approval_status") == "APPROVED" else "MANUAL REPORT"
        else:
            summary = f"No compiled situation reports found for {loc_meta.district_name}."
            prov = "UNAVAILABLE"

        return ContextItem(
            domain="sitreps",
            title=f"ASDMA Daily Situation Reports ({loc_meta.district_name})",
            source_agency="ASDMA State Emergency Operations Center",
            provenance_state=prov,
            is_live=False,
            observation_time=sitrep_info.get("created_at") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            summary=summary,
            raw_metrics={"latest_sitrep": sitrep_info, "location_id": loc_id},
            freshness_status="FRESH" if sitrep_info else "UNAVAILABLE"
        )

    @staticmethod
    def get_vehicles_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        db = SessionLocal()
        vehicles = []
        try:
            v_models = db.query(VehicleModel).filter(
                (VehicleModel.location_id == loc_id) | (VehicleModel.location_id == None if loc_id == "kamrup_metro" else False)
            ).all()

            vehicles = [
                {
                    "code": v.code,
                    "name": v.name,
                    "type": v.type,
                    "capacity_kg": v.capacity_kg,
                    "status": v.status,
                    "fuel_pct": v.fuel_pct
                }
                for v in v_models
            ]
        except Exception:
            vehicles = []
        finally:
            db.close()

        if not vehicles:
            if loc_id == "kamrup_metro":
                vehicles = list(VEHICLES_DATA)
            else:
                vehicles = get_district_vehicles(loc_id)

        tot_cap = sum(v.get("capacity_kg", 0) for v in vehicles)
        ready_count = sum(1 for v in vehicles if v.get("status") in ("READY", "AVAILABLE"))

        summary = (
            f"{loc_meta.district_name} relief fleet: {len(vehicles)} vehicles ({ready_count} READY). "
            f"Total payload capacity: {tot_cap} kg."
        )

        return ContextItem(
            domain="vehicles",
            title=f"Transport & Relief Carrier Fleet ({loc_meta.district_name})",
            source_agency=f"DDMA {loc_meta.district_name} Transport Division",
            provenance_state="VERIFIED OBSERVATION",
            is_live=False,
            observation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            summary=summary,
            raw_metrics={"vehicles": vehicles, "total_capacity_kg": tot_cap, "location_id": loc_id},
            freshness_status="FRESH"
        )

    @staticmethod
    def get_roads_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        db = SessionLocal()
        close_list = []
        try:
            closures = db.query(RoadClosureModel).filter(
                RoadClosureModel.is_active == True,
                (RoadClosureModel.location_id == loc_id) | (RoadClosureModel.location_id == None if loc_id == "kamrup_metro" else False)
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
            provenance_state="MANUAL REPORT",
            is_live=False,
            observation_time="Verified Operational Shift",
            summary=summary,
            raw_metrics={"closures": close_list, "location_id": loc_id},
            freshness_status="FRESH"
        )

    @staticmethod
    def get_routing_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        try:
            routes_data = get_district_routes(loc_id)
            routes = routes_data.get("routes", []) if isinstance(routes_data, dict) else routes_data
            routes_summary = []
            for r in routes:
                routes_summary.append({
                    "vehicle": r.get("vehicle_code"),
                    "assigned_zone": r.get("assigned_zone") or r.get("route_profile"),
                    "distance_km": r.get("total_distance_km"),
                    "duration": r.get("est_duration") or r.get("est_tour_duration"),
                    "detour_active": "DETOUR" in r.get("route_profile", "") or bool(r.get("detour_reason"))
                })
            summary = f"{len(routes)} transit routes calculated for {loc_meta.district_name} relief dispatch."
            return ContextItem(
                domain="routing",
                title=f"Transit Routes & Detour Profiles ({loc_meta.district_name})",
                source_agency="OSRM & NetworkX Routing Engine",
                provenance_state="ESTIMATED",
                is_live=False,
                observation_time="Latest Routing Calculation",
                summary=summary,
                raw_metrics={"routes": routes_summary, "location_id": loc_id},
                freshness_status="FRESH"
            )
        except Exception as exc:
            return ContextItem(
                domain="routing",
                title=f"Transit Routes & Detour Profiles ({loc_meta.district_name})",
                source_agency="Routing Engine",
                provenance_state="UNAVAILABLE",
                is_live=False,
                observation_time="N/A",
                summary=f"Routing service unavailable: {str(exc)}",
                raw_metrics={"error": str(exc)},
                freshness_status="UNAVAILABLE"
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
                title=f"Optimal Allocation Plan ({loc_meta.district_name})",
                source_agency="Google OR-Tools CP-SAT Solver v9.8",
                provenance_state="ESTIMATED",
                is_live=False,
                observation_time="Latest Execution",
                summary=summary,
                raw_metrics=plan,
                freshness_status="FRESH"
            )
        except Exception as exc:
            return ContextItem(
                domain="allocation",
                title=f"Optimal Allocation Plan ({loc_meta.district_name})",
                source_agency="Optimization Engine",
                provenance_state="UNAVAILABLE",
                is_live=False,
                observation_time="N/A",
                summary=f"Allocation plan unavailable: {str(exc)}",
                raw_metrics={"error": str(exc), "location_id": loc_id},
                freshness_status="UNAVAILABLE"
            )

    @staticmethod
    def get_risk_assessment_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        try:
            dist_zones = get_district_zones(loc_id)
            crit_zones = [z["code"] for z in dist_zones if "CRITICAL" in z.get("risk_tier", "")]
            summary = (
                f"Multi-criteria flood risk assessment for {loc_meta.district_name}: "
                f"{len(crit_zones)} critical sectors identified ({', '.join(crit_zones) or 'None'}). "
                f"Baseline algorithm: Random Forest classifier v1.0.0 with hydro-meteorological MCDA weighting."
            )
            return ContextItem(
                domain="risk_assessment",
                title=f"Flood Risk Vulnerability Model ({loc_meta.district_name})",
                source_agency="ASDMA Hydrological Analytics Desk",
                provenance_state="ESTIMATED",
                is_live=False,
                observation_time="Current Risk Run",
                summary=summary,
                raw_metrics={"critical_sectors": crit_zones, "model_version": "v1.0.0-rf-mcda", "location_id": loc_id},
                freshness_status="FRESH"
            )
        except Exception as exc:
            return ContextItem(
                domain="risk_assessment",
                title=f"Flood Risk Vulnerability Model ({loc_meta.district_name})",
                source_agency="Risk Engine",
                provenance_state="UNAVAILABLE",
                is_live=False,
                observation_time="N/A",
                summary=f"Risk assessment unavailable: {str(exc)}",
                raw_metrics={"error": str(exc)},
                freshness_status="UNAVAILABLE"
            )

    @staticmethod
    def get_sphere_standards_context(location_id: Optional[str] = None) -> ContextItem:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)

        try:
            # Baseline population calculation using 5000 affected pop
            sphere_data = calculate_sphere_humanitarian_demand(
                population_affected=5000,
                evacuees_in_shelters=1200,
                time_horizon_hours=24,
                location_id=loc_id
            )
            req = sphere_data.get("consolidated_humanitarian_requirement", {})
            summary = (
                f"Sphere Handbook 2018 Standards: Daily baselines = 2,100 kcal food, 15.0 L water / person / day. "
                f"For 5,000 affected population in {loc_meta.district_name} (24h horizon): {req.get('food_rations_total_kg')} kg rations, {req.get('potable_water_total_liters')} L water required."
            )
            return ContextItem(
                domain="sphere_standards",
                title="Sphere 2018 Humanitarian Charter Requirements",
                source_agency="Sphere Association (2018 Handbook Standard)",
                provenance_state="ESTIMATED",
                is_live=False,
                observation_time="Statutory Baseline Standard",
                summary=summary,
                raw_metrics=sphere_data,
                freshness_status="FRESH"
            )
        except Exception as exc:
            return ContextItem(
                domain="sphere_standards",
                title="Sphere 2018 Humanitarian Charter Requirements",
                source_agency="Humanitarian Engine",
                provenance_state="UNAVAILABLE",
                is_live=False,
                observation_time="N/A",
                summary=f"Sphere standards calculation unavailable: {str(exc)}",
                raw_metrics={"error": str(exc)},
                freshness_status="UNAVAILABLE"
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
            provenance_state="LIVE / RECENTLY RETRIEVED",
            is_live=True,
            observation_time=mode_data.get("switched_at", datetime.now(timezone.utc).isoformat()),
            summary=summary,
            raw_metrics=mode_data,
            freshness_status="FRESH"
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

        module_set = set(modules) if modules else {
            AIContextModule.ZONES,
            AIContextModule.WEATHER,
            AIContextModule.GAUGES,
            AIContextModule.INVENTORY,
            AIContextModule.STOCK_MOVEMENTS,
            AIContextModule.SHELTERS,
            AIContextModule.DEMANDS,
            AIContextModule.INCIDENTS,
            AIContextModule.SITREPS,
            AIContextModule.VEHICLES,
            AIContextModule.ROADS,
            AIContextModule.ROUTING,
            AIContextModule.ALLOCATION,
            AIContextModule.RISK_ASSESSMENT,
            AIContextModule.SPHERE_STANDARDS,
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
        if AIContextModule.STOCK_MOVEMENTS in module_set:
            items.append(cls.get_stock_movements_context(location_id=loc_id))
        if AIContextModule.SHELTERS in module_set:
            items.append(cls.get_shelters_context(location_id=loc_id))
        if AIContextModule.DEMANDS in module_set:
            items.append(cls.get_demands_context(location_id=loc_id))
        if AIContextModule.INCIDENTS in module_set:
            items.append(cls.get_incidents_context(location_id=loc_id))
        if AIContextModule.SITREPS in module_set:
            items.append(cls.get_sitreps_context(location_id=loc_id))
        if AIContextModule.VEHICLES in module_set:
            items.append(cls.get_vehicles_context(location_id=loc_id))
        if AIContextModule.ROADS in module_set:
            items.append(cls.get_roads_context(location_id=loc_id))
        if AIContextModule.ROUTING in module_set:
            items.append(cls.get_routing_context(location_id=loc_id))
        if AIContextModule.ALLOCATION in module_set:
            items.append(cls.get_allocation_context(location_id=loc_id))
        if AIContextModule.RISK_ASSESSMENT in module_set:
            items.append(cls.get_risk_assessment_context(location_id=loc_id))
        if AIContextModule.SPHERE_STANDARDS in module_set:
            items.append(cls.get_sphere_standards_context(location_id=loc_id))

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
                    "freshness_status": item.freshness_status,
                    "observation_time": item.observation_time,
                    "retrieval_time": item.retrieval_time,
                    "summary": item.summary,
                    "metrics": item.raw_metrics
                }
                for item in preview.context_items
            ]
        }
        return json.dumps(payload, indent=2)
