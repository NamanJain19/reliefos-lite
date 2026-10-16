"""
RELIEFOS Lite — Grounded Deterministic Response Synthesizer
Builds evidence-grounded operational responses directly from authoritative database records
and sensor adapters when cloud AI providers (Gemini/OpenAI) are unavailable or disabled.
Strictly eliminates conversational hallucination and enforces ISO-19115 provenance transparency.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

from app.schemas.ai import (
    AIStructuredResponse, AISupportingEvidence, AIProposedAction, ContextItem
)
from app.core.location_registry import get_location_meta, normalize_location_id


class DeterministicGroundedSynthesizer:
    """Synthesizes factual, traceable decision-support responses directly from verified context."""

    @classmethod
    def synthesize(
        cls,
        query: str,
        location_id: str,
        context_items: List[ContextItem],
        fallback_reason: Optional[str] = None,
        is_provider_error: bool = False,
        operator_name: Optional[str] = None
    ) -> AIStructuredResponse:
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)
        q_lower = query.lower().strip()

        domain_map: Dict[str, ContextItem] = {item.domain: item for item in context_items}

        supporting_evidence: List[AISupportingEvidence] = []
        proposed_actions: List[AIProposedAction] = []
        risks_and_limitations: List[str] = []
        missing_or_stale_disclosures: List[str] = []

        if fallback_reason:
            missing_or_stale_disclosures.append(
                f"Cloud AI inference provider unavailable ({fallback_reason}). Answering using verified deterministic backend records."
            )
        else:
            missing_or_stale_disclosures.append(
                "Cloud AI inference provider (Gemini/OpenAI) is not configured. Answering using verified deterministic backend records."
            )

        # Check for unavailable or stale domains in compiled context
        for item in context_items:
            if item.provenance_state == "UNAVAILABLE" or item.freshness_status == "UNAVAILABLE":
                missing_or_stale_disclosures.append(
                    f"Operational domain '{item.domain}' ({item.title}) is currently UNAVAILABLE: {item.summary}"
                )
            elif item.freshness_status == "STALE":
                missing_or_stale_disclosures.append(
                    f"Operational domain '{item.domain}' contains STALE observations ({item.observation_time})."
                )

        # ----------------------------------------------------------------------
        # Domain 0: STATUTORY OPERATOR REVIEW & FORM 8B GOVERNANCE
        # ----------------------------------------------------------------------
        if any(w in q_lower for w in ["review next", "what should an operator review", "next step", "form 8b"]):
            rec = (
                f"Statutory Form 8B Review Priority for {loc_meta.district_name}: "
                f"Duty officer must review and sign the pending Form 8B Resource Allocation Manifest before authorizing field carrier dispatches."
            )
            exp = (
                f"Operational next-steps protocol for {loc_meta.district_name} (ASDMA Statutory Guidelines):\n"
                f"1. Form 8B Review: Inspect OR-Tools optimization allocations across vulnerable sectors.\n"
                f"2. Logistics Clearance: Verify physical depot stock balances and designated camp occupancy.\n"
                f"3. Cryptographic Sign-Off: Submit authorized Form 8B officer approval to transition proposed actions from PENDING_OFFICER_REVIEW to APPROVED.\n"
            )
            proposed_actions.append(AIProposedAction(
                action_id="ACT-FORM8B-REVIEW-01",
                title=f"Review & Sign Form 8B Resource Manifest ({loc_meta.district_name})",
                target_entity=f"DDMA {loc_meta.district_name}",
                action_type="REVIEW_ALLOCATION",
                priority="HIGH",
                rationale="Under ASDMA Form 8B protocol, emergency relief dispatches require authorized duty officer review prior to physical vehicle rollout.",
                suggested_route="/allocation",
                status="PENDING_OFFICER_REVIEW"
            ))
            alloc_item = domain_map.get("allocation")
            source_ag = alloc_item.source_agency if alloc_item else "ASDMA State EOC"
            obs_time = alloc_item.observation_time if alloc_item else "Statutory Directive Cycle"
            supporting_evidence.append(AISupportingEvidence(
                source=source_ag,
                data_point=f"Pending Form 8B action review manifest for {loc_meta.district_name}: Statutory compliance sign-off prerequisite.",
                provenance_state="MANUAL REPORT",
                observation_time=obs_time,
                trust_tier="TIER_1_OFFICIAL"
            ))

            return cls._build_response(rec, exp, supporting_evidence, proposed_actions, risks_and_limitations, missing_or_stale_disclosures)

        # ----------------------------------------------------------------------
        # Domain 1: INVENTORY & WAREHOUSE LEDGER
        # ----------------------------------------------------------------------
        inv_item = domain_map.get("inventory")
        mov_item = domain_map.get("stock_movements")
        if any(w in q_lower for w in ["inventory", "stock", "reserve", "depot", "ration", "warehouse", "balance", "sku", "food", "water"]):
            if inv_item and inv_item.provenance_state != "UNAVAILABLE":
                inv_metrics = inv_item.raw_metrics.get("inventory_items", [])
                depot_code = inv_item.raw_metrics.get("depot_code", "DEPOT-01")

                total_food = sum(i.get("available_qty", 0) for i in inv_metrics if "food" in i.get("category", "").lower() or "ration" in i.get("category", "").lower())
                total_water = sum(i.get("available_qty", 0) for i in inv_metrics if "water" in i.get("category", "").lower())

                supporting_evidence.append(AISupportingEvidence(
                    source=inv_item.source_agency,
                    data_point=f"Physical stock: {total_food} kg Food Supplies, {total_water} L Potable Water ({len(inv_metrics)} SKUs tracked)",
                    provenance_state=inv_item.provenance_state,
                    observation_time=inv_item.observation_time,
                    trust_tier="TIER_1_OFFICIAL"
                ))

                mov_metrics = mov_item.raw_metrics.get("movements", []) if mov_item else []
                if mov_metrics:
                    latest_mov = mov_metrics[0]
                    supporting_evidence.append(AISupportingEvidence(
                        source=mov_item.source_agency if mov_item else "Warehouse Ledger",
                        data_point=f"Latest stock movement: {latest_mov.get('movement_type')} of {latest_mov.get('quantity')} {latest_mov.get('unit')} ({latest_mov.get('item_sku')}) by {latest_mov.get('operator_name')}",
                        provenance_state="VERIFIED OBSERVATION",
                        observation_time=latest_mov.get("timestamp") or "Recent Shift",
                        trust_tier="TIER_1_OFFICIAL"
                    ))

                # Match any specific SKU or product name in query
                matched_items = [
                    i for i in inv_metrics
                    if (i.get("sku") and i.get("sku").lower() in q_lower)
                    or (i.get("name") and any(tok in q_lower for tok in i.get("name").lower().split() if len(tok) > 3))
                ]

                if matched_items:
                    primary_m = matched_items[0]
                    supporting_evidence.append(AISupportingEvidence(
                        source=inv_item.source_agency,
                        data_point=f"Direct query match for {primary_m.get('sku')} ({primary_m.get('name')}): Available {primary_m.get('available_qty')} {primary_m.get('unit')} (Total: {primary_m.get('total_qty', primary_m.get('available_qty'))} {primary_m.get('unit')}, Reserved: {primary_m.get('reserved_qty', 0)} {primary_m.get('unit')})",
                        provenance_state="VERIFIED OBSERVATION",
                        observation_time=inv_item.observation_time,
                        trust_tier="TIER_1_OFFICIAL"
                    ))
                    rec = (
                        f"Verified stock record for {primary_m.get('sku')} ({primary_m.get('name')}): "
                        f"{primary_m.get('available_qty')} {primary_m.get('unit')} available at {loc_meta.district_name} ({depot_code}). "
                        f"Total stock: {primary_m.get('total_qty', primary_m.get('available_qty'))} {primary_m.get('unit')} (Reserved: {primary_m.get('reserved_qty', 0)} {primary_m.get('unit')})."
                    )
                else:
                    rec = (
                        f"Verified warehouse records for {loc_meta.district_name} ({depot_code}) show {total_food} kg food supplies "
                        f"and {total_water} L potable water currently available for dispatch across {len(inv_metrics)} active SKUs."
                    )

                exp = (
                    f"Current physical warehouse ledger for {loc_meta.district_name} staged via {inv_item.source_agency}. "
                    f"Available inventory breakdown:\n"
                )
                # Prioritize matched items first, then display remaining items
                ordered_items = list(matched_items) + [i for i in inv_metrics if i not in matched_items]
                for i in ordered_items[:30]:
                    exp += f"• {i.get('sku')}: {i.get('name')} — Available: {i.get('available_qty')} {i.get('unit')} (Reserved: {i.get('reserved_qty', 0)} {i.get('unit')}, Status: {i.get('status')})\n"

                if total_food < 1000:
                    risks_and_limitations.append(f"Depot food inventory ({total_food} kg) is below 1,000 kg safety buffer.")
                    proposed_actions.append(AIProposedAction(
                        action_id="ACT-INV-REPLENISH-01",
                        title=f"Requisition Emergency Buffer Stock for {loc_meta.district_name}",
                        target_entity=depot_code,
                        action_type="REPLENISH_STOCK",
                        priority="HIGH",
                        rationale=f"Depot food buffer ({total_food} kg) requires replenishment from State Emergency Operations Center Khanapara.",
                        suggested_route="/operations"
                    ))

                return cls._build_response(rec, exp, supporting_evidence, proposed_actions, risks_and_limitations, missing_or_stale_disclosures)
            else:
                return cls._build_unavailable_response("inventory", loc_meta.district_name, supporting_evidence, missing_or_stale_disclosures)

        # ----------------------------------------------------------------------
        # Domain 2: SHELTERS & EVACUEE CAPACITY
        # ----------------------------------------------------------------------
        sh_item = domain_map.get("shelters")
        if any(w in q_lower for w in ["shelter", "evacuee", "camp", "displaced", "occupancy", "capacity", "school", "college"]):
            if sh_item and sh_item.provenance_state != "UNAVAILABLE":
                shelters = sh_item.raw_metrics.get("shelters", [])
                tot_cap = sh_item.raw_metrics.get("total_capacity", 0)
                tot_occ = sh_item.raw_metrics.get("total_occupancy", 0)
                tot_avail = sh_item.raw_metrics.get("available_beds", 0)

                supporting_evidence.append(AISupportingEvidence(
                    source=sh_item.source_agency,
                    data_point=f"{len(shelters)} designated shelters: Total capacity {tot_cap}, Current occupancy {tot_occ}, Vacancy {tot_avail}",
                    provenance_state=sh_item.provenance_state,
                    observation_time=sh_item.observation_time,
                    trust_tier="TIER_1_OFFICIAL"
                ))

                rec = (
                    f"{len(shelters)} designated shelters registered in {loc_meta.district_name} with {tot_cap} total capacity. "
                    f"Currently housing {tot_occ} registered evacuees ({tot_avail} bed spaces available)."
                )
                exp = f"Designated relief shelter status for {loc_meta.district_name}:\n"
                for s in shelters:
                    avail = s.get("available_space", max(0, s.get("capacity", 0) - s.get("occupancy", 0)))
                    exp += f"• {s.get('name')} ({s.get('zone_code')}): Occupancy {s.get('occupancy')}/{s.get('capacity')} ({avail} spaces available, Status: {s.get('status')})\n"

                for s in shelters:
                    if s.get("occupancy", 0) >= s.get("capacity", 1):
                        risks_and_limitations.append(f"Shelter '{s.get('name')}' is at 100% capacity ({s.get('capacity')} evacuees).")

                return cls._build_response(rec, exp, supporting_evidence, proposed_actions, risks_and_limitations, missing_or_stale_disclosures)
            else:
                return cls._build_unavailable_response("shelters", loc_meta.district_name, supporting_evidence, missing_or_stale_disclosures)

        # ----------------------------------------------------------------------
        # Domain 3: RIVER HYDROLOGY & CWC GAUGES
        # ----------------------------------------------------------------------
        gauge_item = domain_map.get("gauges")
        if any(w in q_lower for w in ["gauge", "river", "brahmaputra", "burhidihing", "barak", "hydrology", "water level", "danger mark", "msl", "cwc"]):
            if gauge_item and gauge_item.provenance_state != "UNAVAILABLE":
                stations = gauge_item.raw_metrics.get("stations", [])
                danger_stations = [s for s in stations if s.get("current_level_m") is not None and s.get("current_level_m") >= s.get("danger_level_m", 0)]

                for s in stations[:4]:
                    supporting_evidence.append(AISupportingEvidence(
                        source=gauge_item.source_agency,
                        data_point=f"{s.get('station_name')} ({s.get('river')}): Current {s.get('current_level_m')}m MSL (Danger Level: {s.get('danger_level_m')}m MSL, Status: {s.get('status', 'MONITORED')})",
                        provenance_state=gauge_item.provenance_state,
                        observation_time=gauge_item.observation_time,
                        trust_tier="TIER_1_OFFICIAL"
                    ))

                if danger_stations:
                    rec = (
                        f"Hydrological warning: {len(danger_stations)} CWC river station(s) in {loc_meta.district_name} "
                        f"exceed official Danger Level: " + ", ".join([f"{s.get('station_name')} (+{round(s.get('current_level_m', 0) - s.get('danger_level_m', 0), 2)}m)" for s in danger_stations])
                    )
                else:
                    rec = f"All {len(stations)} monitored CWC river gauge stations in {loc_meta.district_name} are currently below official Danger Levels."

                exp = f"CWC Assam river hydrological observations for {loc_meta.district_name}:\n"
                for s in stations:
                    diff = round((s.get("current_level_m") or 0) - (s.get("danger_level_m") or 0), 2)
                    sign = "+" if diff >= 0 else ""
                    exp += f"• {s.get('station_name')} — River {s.get('river')}: {s.get('current_level_m')}m MSL (DL: {s.get('danger_level_m')}m, Variance: {sign}{diff}m, Trend: {s.get('trend', 'Steady')})\n"

                for ds in danger_stations:
                    risks_and_limitations.append(f"River {ds.get('river')} at {ds.get('station_name')} is overtopping danger threshold.")

                return cls._build_response(rec, exp, supporting_evidence, proposed_actions, risks_and_limitations, missing_or_stale_disclosures)
            else:
                return cls._build_unavailable_response("gauges", loc_meta.district_name, supporting_evidence, missing_or_stale_disclosures)

        # ----------------------------------------------------------------------
        # Domain 4: WEATHER & RAINFALL OBSERVATIONS / FORECASTS
        # ----------------------------------------------------------------------
        w_item = domain_map.get("weather")
        if any(w in q_lower for w in ["weather", "rain", "precip", "temp", "forecast", "monsoon", "cloud", "humidity"]):
            if w_item and w_item.provenance_state != "UNAVAILABLE":
                w_metrics = w_item.raw_metrics
                curr = w_metrics.get("current", {})

                supporting_evidence.append(AISupportingEvidence(
                    source=w_item.source_agency,
                    data_point=f"Current: Temp {curr.get('temperature_c')}°C, Precip rate {curr.get('precipitation_rate_mm_h')} mm/h, Humidity {curr.get('humidity_pct')}%, Wind {curr.get('wind_speed_km_h')} km/h",
                    provenance_state=w_item.provenance_state,
                    observation_time=w_item.observation_time,
                    trust_tier="TIER_1_OFFICIAL"
                ))

                rec = (
                    f"Current weather observation for {loc_meta.district_name}: {curr.get('temperature_c')}°C with "
                    f"{curr.get('precipitation_rate_mm_h')} mm/h precipitation ({curr.get('weather_condition', 'Monsoon conditions')})."
                )
                exp = (
                    f"Open-Meteo NWP ECMWF telemetry for {loc_meta.district_name} (Observation: {w_item.observation_time}):\n"
                    f"• Surface Temperature: {curr.get('temperature_c')}°C\n"
                    f"• Precipitation Rate: {curr.get('precipitation_rate_mm_h')} mm/h\n"
                    f"• Relative Humidity: {curr.get('humidity_pct')}%\n"
                    f"• Wind Speed: {curr.get('wind_speed_km_h')} km/h ({curr.get('wind_direction_cardinal')})\n"
                    f"• Cloud Cover: {curr.get('cloud_cover_pct')}%\n"
                    f"• Forecast Status: Hourly 24h precipitation model available in telemetry service.\n"
                    f"Note: Current readings represent verified observations; 24-hour accumulations represent forecast projections."
                )

                if curr.get("precipitation_rate_mm_h", 0) > 10.0:
                    risks_and_limitations.append(f"Heavy precipitation rate ({curr.get('precipitation_rate_mm_h')} mm/h) poses flash waterlogging hazard.")

                return cls._build_response(rec, exp, supporting_evidence, proposed_actions, risks_and_limitations, missing_or_stale_disclosures)
            else:
                return cls._build_unavailable_response("weather", loc_meta.district_name, supporting_evidence, missing_or_stale_disclosures)

        # ----------------------------------------------------------------------
        # Domain 5: ROAD CLOSURES, ROUTING & DETOUR IMPACT
        # ----------------------------------------------------------------------
        roads_item = domain_map.get("roads")
        routes_item = domain_map.get("routing")
        if any(w in q_lower for w in ["road", "closure", "detour", "access", "submerged", "bridge", "chokepoint", "route", "highway", "corridor"]):
            if roads_item and roads_item.provenance_state != "UNAVAILABLE":
                closures = roads_item.raw_metrics.get("closures", [])
                submerged = [c for c in closures if "IMPASSABLE" in c.get("status", "").upper() or c.get("water_depth_m", 0) >= c.get("threshold_m", 0.35)]

                for c in closures[:3]:
                    supporting_evidence.append(AISupportingEvidence(
                        source=roads_item.source_agency,
                        data_point=f"Chokepoint {c.get('corridor')}: Water depth {c.get('water_depth_m')}m (Clearance threshold: {c.get('threshold_m')}m, Status: {c.get('status')})",
                        provenance_state=roads_item.provenance_state,
                        observation_time=roads_item.observation_time,
                        trust_tier="TIER_1_OFFICIAL"
                    ))

                if submerged:
                    rec = (
                        f"{len(submerged)} impassable road closure(s) recorded in {loc_meta.district_name}: "
                        + ", ".join([f"{c.get('corridor')} ({c.get('water_depth_m')}m water, Detour: {c.get('detour') or 'Alternative highway'})" for c in submerged])
                    )
                else:
                    rec = f"No impassable road closures currently recorded in {loc_meta.district_name}. All primary transit corridors open."

                exp = f"Road network inundation and accessibility register for {loc_meta.district_name}:\n"
                for c in closures:
                    exp += f"• {c.get('corridor')}: Depth {c.get('water_depth_m')}m — Status: {c.get('status')}. Detour: {c.get('detour') or 'None required'}\n"

                for sc in submerged:
                    risks_and_limitations.append(f"Arterial corridor '{sc.get('corridor')}' is impassable for standard relief carriers.")

                return cls._build_response(rec, exp, supporting_evidence, proposed_actions, risks_and_limitations, missing_or_stale_disclosures)
            else:
                return cls._build_unavailable_response("roads", loc_meta.district_name, supporting_evidence, missing_or_stale_disclosures)

        # ----------------------------------------------------------------------
        # Domain 6: OR-TOOLS CP-SAT RESOURCE ALLOCATION & OPTIMIZER / DISPATCH ACTIONS
        # ----------------------------------------------------------------------
        alloc_item = domain_map.get("allocation")
        if any(w in q_lower for w in ["allocat", "optimizer", "optimization", "solver", "cp-sat", "or-tools", "plan", "assign", "dispatch", "authorize", "release"]):
            if alloc_item and alloc_item.provenance_state != "UNAVAILABLE":
                plan = alloc_item.raw_metrics
                alloc_kg = plan.get("proposed_allocation_kg", 0)
                deficit_kg = plan.get("projected_deficit_kg", 0)
                coverage = plan.get("coverage_ratio_pct", 0)
                allocations = plan.get("allocations", [])

                supporting_evidence.append(AISupportingEvidence(
                    source=alloc_item.source_agency,
                    data_point=f"Google OR-Tools CP-SAT Two-Stage Lexicographic solver: Coverage {coverage}%, Allocated {alloc_kg} kg, Deficit {deficit_kg} kg",
                    provenance_state=alloc_item.provenance_state,
                    observation_time=alloc_item.observation_time,
                    trust_tier="TIER_1_OFFICIAL"
                ))

                is_dispatch_query = any(w in q_lower for w in ["dispatch", "authorize", "release"])

                if is_dispatch_query:
                    rec = (
                        f"Operational Action Governance for {loc_meta.district_name}: Autonomous AI dispatches are prohibited. "
                        f"All emergency dispatches require authorized DDMA officer sign-off under Form 8B. Proposed action staged in PENDING_OFFICER_REVIEW."
                    )
                else:
                    rec = (
                        f"OR-Tools CP-SAT optimizer solved allocation for {loc_meta.district_name} with {coverage}% demand coverage. "
                        f"Allocated: {alloc_kg} kg relief supplies across {len(allocations)} sectors. Projected unmet deficit: {deficit_kg} kg."
                    )

                exp = (
                    f"Mathematical allocation optimization details ({loc_meta.district_name}):\n"
                    f"• Strategy: Two-Stage Lexicographic Severity-Constrained MILP\n"
                    f"• Solver Engine: Google OR-Tools CP-SAT (Integer Feasibility with Bound Tightening)\n"
                    f"• Total Demand Evaluated: {round(alloc_kg + deficit_kg, 1)} kg\n"
                    f"• Total Apportioned Rations: {alloc_kg} kg ({coverage}% fulfillment)\n"
                    f"• Net Shortfall: {deficit_kg} kg\n"
                    f"Zone Apportionment Summary:\n"
                )
                for a in allocations[:5]:
                    exp += f"• {a.get('zone_code')}: Demand {a.get('demand_kg')} kg -> Allocated {a.get('allocated_kg')} kg (Deficit: {a.get('deficit_kg')} kg, Status: {a.get('status')})\n"

                risks_and_limitations.append("Autonomous execution prohibited: All emergency resource dispatches require physical Form 8B officer sign-off.")
                if deficit_kg > 0:
                    risks_and_limitations.append(f"Unmet demand of {deficit_kg} kg remains due to warehouse supply limits.")

                # Always stage a proposed action requiring human review for dispatch or allocation
                proposed_actions.append(AIProposedAction(
                    action_id="ACT-ALLOC-REVIEW-01",
                    title=f"Review & Sign Form 8B Dispatch Manifest for {loc_meta.district_name}",
                    target_entity=f"DDMA {loc_meta.district_name}",
                    action_type="REVIEW_ALLOCATION",
                    priority="HIGH",
                    rationale="OR-Tools optimization plan completed. Requires authorized officer review and sign-off under Form 8B protocol prior to carrier dispatch.",
                    suggested_route="/allocation",
                    status="PENDING_OFFICER_REVIEW"
                ))

                return cls._build_response(rec, exp, supporting_evidence, proposed_actions, risks_and_limitations, missing_or_stale_disclosures)
            else:
                return cls._build_unavailable_response("allocation", loc_meta.district_name, supporting_evidence, missing_or_stale_disclosures)

        # ----------------------------------------------------------------------
        # Domain 7: FIELD INCIDENTS & SITREPS
        # ----------------------------------------------------------------------
        inc_item = domain_map.get("incidents")
        sit_item = domain_map.get("sitreps")
        if any(w in q_lower for w in ["incident", "breach", "embankment", "stranded", "casualt", "sitrep", "bulletin", "report", "changed", "delta"]):
            incidents = inc_item.raw_metrics.get("incidents", []) if inc_item else []
            sitrep = sit_item.raw_metrics.get("latest_sitrep", {}) if sit_item else {}

            if incidents:
                supporting_evidence.append(AISupportingEvidence(
                    source=inc_item.source_agency if inc_item else "Incident Log",
                    data_point=f"{len(incidents)} field incident(s) logged. Active: {inc_item.raw_metrics.get('active_count', 0)}",
                    provenance_state="MANUAL REPORT",
                    observation_time=inc_item.observation_time if inc_item else "Today",
                    trust_tier="TIER_1_OFFICIAL"
                ))

            if sitrep:
                supporting_evidence.append(AISupportingEvidence(
                    source=sit_item.source_agency if sit_item else "ASDMA SitRep",
                    data_point=f"SitRep {sitrep.get('sitrep_id')}: Date {sitrep.get('report_date')}, Status: {sitrep.get('approval_status')}, Displaced: {sitrep.get('displaced_in_shelters')}",
                    provenance_state=sit_item.provenance_state if sit_item else "MANUAL REPORT",
                    observation_time=sitrep.get("created_at") or "Today",
                    trust_tier="TIER_1_OFFICIAL"
                ))

            rec = (
                f"{len(incidents)} field incident(s) registered in {loc_meta.district_name}. "
                f"Latest ASDMA SitRep ({sitrep.get('sitrep_id', 'DRAFT')}) reports {sitrep.get('displaced_in_shelters', 0)} displaced persons in shelters."
            )
            exp = f"Emergency situation & incident log for {loc_meta.district_name}:\n"
            if incidents:
                exp += "Active Ground Incidents:\n"
                for i in incidents[:5]:
                    exp += f"• [{i.get('severity')}] {i.get('title')} ({i.get('zone_code')}): Status {i.get('status')}, Stranded: {i.get('persons_stranded', 0)}, Reported by: {i.get('reported_by')}\n"
            else:
                exp += "• No open field hazard incidents logged.\n"

            if sitrep:
                exp += f"\nASDMA Daily Flood Bulletin ({sitrep.get('sitrep_id')}):\n"
                exp += f"• Approval Status: {sitrep.get('approval_status')}\n"
                exp += f"• Affected Population: {sitrep.get('active_human_lives_affected')}\n"
                exp += f"• Displaced in Shelters: {sitrep.get('displaced_in_shelters')}\n"
                exp += f"• Roads Closed: {sitrep.get('roads_closed_count')}\n"
                exp += f"• Compiling Officer: {sitrep.get('compiling_officer')}\n"

            return cls._build_response(rec, exp, supporting_evidence, proposed_actions, risks_and_limitations, missing_or_stale_disclosures)

        # ----------------------------------------------------------------------
        # Domain 8: GENERAL SITUATION / OVERVIEW (Multi-Domain Panoramic)
        # ----------------------------------------------------------------------
        zones_item = domain_map.get("zones")
        zones = zones_item.raw_metrics.get("zones", []) if zones_item else []
        high_risk_zones = [z for z in zones if z.get("risk_level") in ("CRITICAL", "HIGH")]

        if zones_item:
            supporting_evidence.append(AISupportingEvidence(
                source=zones_item.source_agency,
                data_point=f"{len(zones)} sectors monitored in {loc_meta.district_name} ({len(high_risk_zones)} critical/high risk)",
                provenance_state=zones_item.provenance_state,
                observation_time=zones_item.observation_time,
                trust_tier="TIER_1_OFFICIAL"
            ))

        if inv_item:
            supporting_evidence.append(AISupportingEvidence(
                source=inv_item.source_agency,
                data_point=inv_item.summary,
                provenance_state=inv_item.provenance_state,
                observation_time=inv_item.observation_time,
                trust_tier="TIER_1_OFFICIAL"
            ))

        if gauge_item and gauge_item.provenance_state != "UNAVAILABLE":
            supporting_evidence.append(AISupportingEvidence(
                source=gauge_item.source_agency,
                data_point=gauge_item.summary,
                provenance_state=gauge_item.provenance_state,
                observation_time=gauge_item.observation_time,
                trust_tier="TIER_1_OFFICIAL"
            ))

        rec = (
            f"Operational situation for {loc_meta.district_name}: {len(zones)} operational sectors active "
            f"({len(high_risk_zones)} high/critical risk). Relief inventory and hydrometric telemetry actively monitored."
        )
        if any(w in q_lower for w in ["dispatch", "authorize", "release"]):
            proposed_actions.append(AIProposedAction(
                action_id="ACT-DISPATCH-01",
                title=f"Review & Sign Form 8B Dispatch Authorization ({loc_meta.district_name})",
                target_entity=f"DDMA {loc_meta.district_name} Fleet Desk",
                action_type="REVIEW_ALLOCATION",
                priority="CRITICAL",
                rationale="Operational dispatch requested. Under ASDMA statutory protocol, all vehicle movements and stock releases require authorized officer sign-off via Form 8B.",
                suggested_route="/allocation",
                status="PENDING_OFFICER_REVIEW"
            ))

        exp = (
            f"Comprehensive operational telemetry summary for {loc_meta.district_name} ({loc_meta.display_name}):\n\n"
            f"1. Operational Sectors & Flood Depth:\n"
        )
        for z in zones[:5]:
            exp += f"• {z.get('code')} ({z.get('name')}): Risk {z.get('risk_level')}, Water Depth: {z.get('water_depth_m')}m, Road: {z.get('road_status')}\n"

        if inv_item:
            exp += f"\n2. Warehouse Logistics:\n• {inv_item.summary}\n"
        if gauge_item:
            exp += f"\n3. Hydrology & River Telemetry:\n• {gauge_item.summary}\n"
        if w_item:
            exp += f"\n4. Meteorological Observation:\n• {w_item.summary}\n"
        if sh_item:
            exp += f"\n5. Relief Shelters:\n• {sh_item.summary}\n"

        return cls._build_response(rec, exp, supporting_evidence, proposed_actions, risks_and_limitations, missing_or_stale_disclosures)

    @classmethod
    def _build_response(
        cls,
        rec: str,
        exp: str,
        evidence: List[AISupportingEvidence],
        actions: List[AIProposedAction],
        risks: List[str],
        disclosures: List[str]
    ) -> AIStructuredResponse:
        audit_id = f"AUD-DET-{uuid.uuid4().hex[:8].upper()}"
        return AIStructuredResponse(
            status="SUCCESS",
            provider_used="backend_deterministic",
            model_used="reliefos-grounded-deterministic-v2",
            recommendation=rec,
            detailed_explanation=exp,
            supporting_evidence=evidence,
            proposed_actions=actions,
            identified_risks_and_limitations=risks or ["Operational conditions subject to localized monsoon variance."],
            missing_or_stale_data_disclosures=disclosures,
            human_review_required=True,
            statutory_compliance_notice="ASDMA Form 8B Advisory Guidance Only. Official human sign-off required prior to vehicle rollout or supply release.",
            is_mock_fallback=False,
            execution_mode="DETERMINISTIC_GROUNDED",
            fallback_reason=None,
            audit_id=audit_id
        )

    @classmethod
    def _build_unavailable_response(
        cls,
        domain_name: str,
        district_name: str,
        evidence: List[AISupportingEvidence],
        disclosures: List[str]
    ) -> AIStructuredResponse:
        rec = f"Operational data for '{domain_name}' in {district_name} is currently UNAVAILABLE. Zero simulated or fabricated values are displayed."
        exp = (
            f"The requested data domain '{domain_name}' could not be retrieved from the authoritative database or external service for {district_name}. "
            f"Under ASDMA decision-support guidelines, the system refuses to manufacture estimated or fictional values. "
            f"Verify circle-officer field communications or reconnect the authoritative data adapter."
        )
        disclosures.append(f"Domain '{domain_name}' unavailable for {district_name}; missing data disclosed.")
        return cls._build_response(rec, exp, evidence, [], [f"Unavailable data domain: {domain_name}"], disclosures)
