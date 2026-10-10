"""
RELIEFOS Lite — Flood Risk Analysis Master Orchestrator
Coordinates live data ingestion, baseline scoring, ML inference with graceful fallback,
citywide aggregation, and historical disaster comparison.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid

from app.schemas.risk import (
    FloodRiskTier, RiskEngineMethod, RiskEngineWeights,
    ZoneRiskAssessment, FloodRiskAnalysisResponse, HistoricalComparisonItem
)
from app.core.database import SessionLocal
from app.models.domain import ZoneModel, RoadClosureModel
from app.core.location_registry import get_location_meta, normalize_location_id, DEFAULT_LOCATION_ID
from app.ingestion import (
    fetch_location_weather, fetch_guwahati_weather, get_all_river_gauges, get_system_mode_status
)
from app.services.risk.baseline import TransparentBaselineRiskEngine
from app.services.risk.ml_model import FloodRiskMLService
from app.ingestion.historical_provider import get_historical_disaster_catalog
from app.core.location_data import get_district_zones, get_district_chokepoints


class FloodRiskAnalysisService:
    """Master service for comprehensive flood risk evaluation across Kamrup Metropolitan and Assam sectors."""

    @classmethod
    def get_historical_comparisons(
        cls,
        current_precip_rate: float,
        current_pandu_stage: float
    ) -> List[HistoricalComparisonItem]:
        """Compares current live situation with certified historical Guwahati flood events."""
        catalog = get_historical_disaster_catalog()
        comparisons: List[HistoricalComparisonItem] = []

        for ev in catalog:
            summary = ev.get("meteorological_summary", {})
            hist_24h = float(summary.get("peak_24h_rainfall_mm", 0.0))
            hist_pandu = float(summary.get("peak_gauge_stage_pandu_m", 0.0))
            extent = float(summary.get("inundation_extent_sq_km", 0.0))
            displaced = int(summary.get("displaced_population_est", 0))

            delta_stage = current_pandu_stage - hist_pandu
            comparison_note = (
                f"Current river stage ({current_pandu_stage:.2f}m) is {abs(delta_stage):.2f}m "
                f"{'above' if delta_stage >= 0 else 'below'} peak stage recorded during {ev['title']}."
            )

            comparisons.append(
                HistoricalComparisonItem(
                    event_id=ev["event_id"],
                    event_title=ev["title"],
                    event_period=ev["period"],
                    rainfall_24h_mm=hist_24h,
                    peak_pandu_stage_m=hist_pandu,
                    inundation_extent_sq_km=extent,
                    displaced_population=displaced,
                    comparison_notes=comparison_note
                )
            )

        return comparisons

    @classmethod
    def run_analysis(
        cls,
        weights: Optional[RiskEngineWeights] = None,
        force_baseline: bool = False,
        target_zone_code: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> FloodRiskAnalysisResponse:
        """
        Executes full flood risk analysis pipeline for Kamrup Metropolitan or monitored Assam districts.
        - Uses ML model if available and force_baseline is False
        - Automatically falls back to transparent baseline MCDA when required
        - Never fabricates hydrodynamic flood depth or exact wave timing
        - Cleanly returns 0 cadastral zones for unconfigured districts while serving live telemetry
        """
        loc_id = normalize_location_id(location_id)
        loc_meta = get_location_meta(loc_id)
        mode_data = get_system_mode_status()

        # 1. Fetch live telemetry for target location
        weather_data = fetch_location_weather(loc_id)
        gauges = get_all_river_gauges(location_id=loc_id)

        # 2. Fetch database zones or authentic district revenue circles
        if loc_id == "kamrup_metro":
            db = SessionLocal()
            try:
                db_zones = db.query(ZoneModel).filter(
                    (ZoneModel.location_id == "kamrup_metro") | (ZoneModel.location_id == None)
                ).all()
                zones_list = [
                    {
                        "code": z.code,
                        "name": z.name,
                        "population": z.affected_population,
                        "inundation_area_ha": z.inundation_area_ha,
                        "avg_flood_depth_m": z.water_depth_m,
                        "key_road_status": z.road_status
                    }
                    for z in db_zones
                ]
                db_closures = db.query(RoadClosureModel).filter(
                    RoadClosureModel.is_active == True,
                    (RoadClosureModel.location_id == "kamrup_metro") | (RoadClosureModel.location_id == None)
                ).all()
                closures_list = [
                    {
                        "corridor": c.corridor_name,
                        "location": c.location_desc,
                        "water_depth_m": c.water_depth_m,
                        "status": c.status
                    }
                    for c in db_closures
                ]
            except Exception:
                zones_list = []
                closures_list = []
            finally:
                db.close()

            if not zones_list:
                zones_list = list(ZONES_DATA)
        else:
            zones_list = get_district_zones(loc_id)
            chokepoints = get_district_chokepoints(loc_id)
            closures_list = [
                {
                    "corridor": ch.get("name") or ch.get("corridor_name", "Arterial Corridor"),
                    "location": ch.get("location_desc", ""),
                    "water_depth_m": ch.get("depth_m", ch.get("water_depth_m", 0.40)),
                    "status": ch.get("status", "IMPASSABLE / SUBMERGED")
                }
                for ch in chokepoints
            ]

        if target_zone_code:
            norm = target_zone_code.strip().upper()
            filtered = [z for z in zones_list if norm in z["code"].upper() or norm in z.get("name", "").upper()]
            if filtered:
                zones_list = filtered

        # 3. Initialize ML engine if needed
        if not force_baseline:
            try:
                FloodRiskMLService.initialize()
            except Exception:
                force_baseline = True

        # 4. Evaluate each zone
        assessments: List[ZoneRiskAssessment] = []
        for z in zones_list:
            if force_baseline:
                assessment = TransparentBaselineRiskEngine.assess_zone_risk(
                    zone_dict=z,
                    weather_data=weather_data,
                    gauges=gauges,
                    closures=closures_list,
                    weights=weights
                )
            else:
                assessment = FloodRiskMLService.predict_zone_risk(
                    zone_dict=z,
                    weather_data=weather_data,
                    gauges=gauges,
                    closures=closures_list
                )
            assessments.append(assessment)

        # 5. Compile citywide summary metrics
        total_zones = len(assessments)
        crit_count = sum(1 for a in assessments if a.risk_tier == FloodRiskTier.CRITICAL)
        high_count = sum(1 for a in assessments if a.risk_tier == FloodRiskTier.HIGH)
        mod_count = sum(1 for a in assessments if a.risk_tier == FloodRiskTier.MODERATE)
        low_count = sum(1 for a in assessments if a.risk_tier == FloodRiskTier.LOW)

        max_risk = max((a.risk_score for a in assessments), default=0.0)
        avg_risk = round(sum(a.risk_score for a in assessments) / max(1, total_zones), 2)
        highest_zone = next((a for a in assessments if a.risk_score == max_risk), assessments[0] if assessments else None)

        controlling_gauge = next((g for g in gauges if "pandu" in g.get("station_name", "").lower()), gauges[0] if gauges else {})
        curr_gauge = float(controlling_gauge.get("current_level_m") or controlling_gauge.get("danger_level_m") or 49.68)
        danger_gauge = float(controlling_gauge.get("danger_level_m") or 49.68)
        curr_precip = float(weather_data.get("current", {}).get("precipitation_rate_mm_h", 0.0) or 0.0)

        citywide_summary = {
            "total_monitored_sectors": total_zones,
            "critical_risk_sectors": crit_count,
            "high_risk_sectors": high_count,
            "moderate_risk_sectors": mod_count,
            "low_risk_sectors": low_count,
            "citywide_max_risk_score": max_risk,
            "citywide_average_risk_score": avg_risk,
            "highest_priority_sector": {
                "code": highest_zone.zone_code if highest_zone else "ZONE 01",
                "name": highest_zone.zone_name if highest_zone else f"{loc_meta.district_name} Sector",
                "risk_tier": highest_zone.risk_tier.value if highest_zone else "CRITICAL",
                "score": highest_zone.risk_score if highest_zone else 8.5
            },
            "hydrometeorological_drivers": {
                "controlling_gauge": controlling_gauge.get("station_name", "Regional CWC Station"),
                "current_river_stage_m": curr_gauge,
                "danger_level_m": danger_gauge,
                "stage_margin_m": round(curr_gauge - danger_gauge, 2),
                "river_trend": controlling_gauge.get("trend", "STEADY"),
                "precipitation_rate_mm_h": curr_precip,
                "weather_condition": weather_data.get("current", {}).get("weather_condition", "Overcast")
            }
        }

        # 6. Historical comparisons
        hist_comps = cls.get_historical_comparisons(curr_precip, curr_gauge)

        # 7. Active method descriptor
        if force_baseline:
            active_method = RiskEngineMethod.RULE_BASED_BASELINE
            model_ver = None
        else:
            any_fallback = any(a.fallback_applied for a in assessments)
            active_method = RiskEngineMethod.FALLBACK_BASELINE if any_fallback else RiskEngineMethod.ML_RANDOM_FOREST
            model_ver = FloodRiskMLService.get_metadata().model_version

        w_applied = weights or RiskEngineWeights()

        return FloodRiskAnalysisResponse(
            analysis_id=f"RISK-EVAL-{uuid.uuid4().hex[:8].upper()}",
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            system_mode=mode_data.get("mode", "OPERATIONAL_LIVE"),
            active_method=active_method,
            model_version=model_ver,
            citywide_summary=citywide_summary,
            zone_assessments=assessments,
            weights_applied=w_applied,
            historical_comparisons=hist_comps,
            governance_notice=(
                f"ASDMA Decision Support System — Relative flood risk index for {loc_meta.district_name}. "
                "Official Form 8B physical review required before operational mobilization. "
                "Does not constitute an autonomous public alert."
            )
        )
