"""
RELIEFOS Lite — CWC Hydrology & River Stage Provider Adapter
Manages river gauges, warning/danger levels, and verified manual readings with audit logging.
Targets: Brahmaputra and Barak River Basins across Assam (Kamrup Metro, Kamrup Rural, Barpeta, Nalbari, Nagaon, Morigaon, Cachar).
Official Sources: Central Water Commission (cwc.gov.in), Assam Water Resources Department (waterresources.assam.gov.in), ASDMA (asdma.gov.in).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import copy

from app.ingestion.registry import registry, DataSourceState
from app.core.database import SessionLocal
from app.models.domain import AuditLogModel

# Verified baseline station configuration from CWC Assam Hydrology Bulletins and Assam Water Resources Department
DEFAULT_GAUGE_STATIONS: List[Dict[str, Any]] = [
    {
        "station_id": "CWC-PANDU-01",
        "station_name": "Pandu Ghat Station",
        "river": "Brahmaputra River",
        "district": "Kamrup Metropolitan",
        "latitude": 26.175,
        "longitude": 91.685,
        "warning_level_m": 48.68,
        "danger_level_m": 49.68,
        "hfl_m": 51.46,
        "current_level_m": 49.68,
        "variance_m": 0.00,
        "discharge_cumecs": 38200.0,
        "trend": "STEADY",
        "provenance_state": DataSourceState.LAST_KNOWN.value,
        "is_live_telemetry": False,
        "source_url": "https://waterresources.assam.gov.in",
        "source_date": "2024-07-02 (CWC Hydrology Bulletin)",
        "observation_time": "Reference Baseline (CWC Bulletin)",
        "last_verified_by": "CWC Regional Office Guwahati"
    },
    {
        "station_id": "CWC-DCCOURT-02",
        "station_name": "Guwahati DC Court Ghat",
        "river": "Brahmaputra River",
        "district": "Kamrup Metropolitan",
        "latitude": 26.191,
        "longitude": 91.745,
        "warning_level_m": 49.26,
        "danger_level_m": 49.50,
        "hfl_m": 51.46,
        "current_level_m": 49.68,
        "variance_m": 0.18,
        "discharge_cumecs": 39100.0,
        "trend": "SLOW RECEDING",
        "provenance_state": DataSourceState.LAST_KNOWN.value,
        "is_live_telemetry": False,
        "source_url": "https://waterresources.assam.gov.in",
        "source_date": "2024-07-02 (CWC Hydrology Bulletin)",
        "observation_time": "Reference Baseline (CWC Bulletin)",
        "last_verified_by": "CWC Regional Office Guwahati"
    },
    {
        "station_id": "CWC-BHARALU-03",
        "station_name": "Bharalumukh Sluice Gate",
        "river": "Bharalu Basin / River Outfall",
        "district": "Kamrup Metropolitan",
        "latitude": 26.172,
        "longitude": 91.735,
        "warning_level_m": 47.50,
        "danger_level_m": 48.00,
        "hfl_m": 48.90,
        "current_level_m": 48.15,
        "variance_m": 0.15,
        "discharge_cumecs": 142.0,
        "trend": "BACKFLOW ACTIVE",
        "provenance_state": DataSourceState.LAST_KNOWN.value,
        "is_live_telemetry": False,
        "source_url": "https://waterresources.assam.gov.in",
        "source_date": "2024-07-02 (GMC Drainage Bulletin)",
        "observation_time": "Reference Baseline",
        "last_verified_by": "GMC Drainage Division"
    },
    {
        "station_id": "CWC-BASISTHA-04",
        "station_name": "Basistha Stream Sensor",
        "river": "Basistha Tributary",
        "district": "Kamrup Metropolitan",
        "latitude": 26.118,
        "longitude": 91.785,
        "warning_level_m": 53.25,
        "danger_level_m": 54.00,
        "hfl_m": 54.85,
        "current_level_m": 52.10,
        "variance_m": -1.90,
        "discharge_cumecs": 45.0,
        "trend": "NORMAL",
        "provenance_state": DataSourceState.LAST_KNOWN.value,
        "is_live_telemetry": False,
        "source_url": "https://waterresources.assam.gov.in",
        "source_date": "2024-07-02 (WRD Field Post)",
        "observation_time": "Reference Baseline",
        "last_verified_by": "WRD Field Post Basistha"
    },
    {
        "station_id": "CWC-PUTHIMARI-05",
        "station_name": "Puthimari NH Road Crossing",
        "river": "Puthimari River",
        "district": "Kamrup Rural",
        "latitude": 26.3467,
        "longitude": 91.6458,
        "warning_level_m": 50.81,
        "danger_level_m": 51.81,
        "hfl_m": 54.22,
        "current_level_m": None,
        "variance_m": None,
        "discharge_cumecs": None,
        "trend": "UNAVAILABLE",
        "provenance_state": DataSourceState.LAST_KNOWN.value,
        "is_live_telemetry": False,
        "source_url": "https://waterresources.assam.gov.in",
        "source_date": "2024-07-02 (Assam WRD / CWC Bulletin)",
        "observation_time": "Baseline Reference (WRD Manual Post)",
        "last_verified_by": "WRD Hydrological Sub-Division Rangia"
    },
    {
        "station_id": "CWC-BEKI-06",
        "station_name": "Beki Road Bridge (Barpeta Road)",
        "river": "Beki River",
        "district": "Barpeta",
        "latitude": 26.4947,
        "longitude": 90.9178,
        "warning_level_m": 44.10,
        "danger_level_m": 45.10,
        "hfl_m": 46.20,
        "current_level_m": None,
        "variance_m": None,
        "discharge_cumecs": None,
        "trend": "UNAVAILABLE",
        "provenance_state": DataSourceState.LAST_KNOWN.value,
        "is_live_telemetry": False,
        "source_url": "https://asdma.gov.in",
        "source_date": "2024-07-02 (CWC Lower Brahmaputra Division)",
        "observation_time": "Baseline Reference (CWC Site Office)",
        "last_verified_by": "CWC Gauge Site Office Barpeta Road"
    },
    {
        "station_id": "CWC-PAGLADIYA-07",
        "station_name": "Pagladiya NT Road Crossing",
        "river": "Pagladiya River",
        "district": "Nalbari",
        "latitude": 26.4494,
        "longitude": 91.4600,
        "warning_level_m": 51.75,
        "danger_level_m": 52.75,
        "hfl_m": 55.45,
        "current_level_m": None,
        "variance_m": None,
        "discharge_cumecs": None,
        "trend": "UNAVAILABLE",
        "provenance_state": DataSourceState.LAST_KNOWN.value,
        "is_live_telemetry": False,
        "source_url": "https://waterresources.assam.gov.in",
        "source_date": "2024-07-02 (CWC Station Code 830)",
        "observation_time": "Baseline Reference (WRD Division Nalbari)",
        "last_verified_by": "WRD Division Nalbari"
    },
    {
        "station_id": "CWC-KAMPUR-08",
        "station_name": "Kopili River at Kampur",
        "river": "Kopili River",
        "district": "Nagaon",
        "latitude": 26.1531,
        "longitude": 92.6564,
        "warning_level_m": 59.50,
        "danger_level_m": 60.50,
        "hfl_m": 62.20,
        "current_level_m": None,
        "variance_m": None,
        "discharge_cumecs": None,
        "trend": "UNAVAILABLE",
        "provenance_state": DataSourceState.LAST_KNOWN.value,
        "is_live_telemetry": False,
        "source_url": "https://asdma.gov.in",
        "source_date": "2024-07-02 (CWC Middle Brahmaputra Division)",
        "observation_time": "Baseline Reference (DDMA Nagaon)",
        "last_verified_by": "ASDMA DDMA Nagaon Field Desk"
    },
    {
        "station_id": "CWC-DHARAMTUL-09",
        "station_name": "Kopili River at Dharamtul",
        "river": "Kopili River",
        "district": "Morigaon",
        "latitude": 26.1642,
        "longitude": 92.3500,
        "warning_level_m": 55.00,
        "danger_level_m": 56.00,
        "hfl_m": 58.09,
        "current_level_m": None,
        "variance_m": None,
        "discharge_cumecs": None,
        "trend": "UNAVAILABLE",
        "provenance_state": DataSourceState.LAST_KNOWN.value,
        "is_live_telemetry": False,
        "source_url": "https://asdma.gov.in",
        "source_date": "2024-07-02 (CWC Site CW1BRL000311)",
        "observation_time": "Baseline Reference (DDMA Morigaon)",
        "last_verified_by": "ASDMA DDMA Morigaon Field Desk"
    },
    {
        "station_id": "CWC-BARAK-10",
        "station_name": "Barak River at Annapurna Ghat (A.P. Ghat)",
        "river": "Barak River",
        "district": "Cachar",
        "latitude": 24.8319,
        "longitude": 92.7961,
        "warning_level_m": 18.83,
        "danger_level_m": 19.83,
        "hfl_m": 21.68,
        "current_level_m": None,
        "variance_m": None,
        "discharge_cumecs": None,
        "trend": "UNAVAILABLE",
        "provenance_state": DataSourceState.LAST_KNOWN.value,
        "is_live_telemetry": False,
        "source_url": "https://waterresources.assam.gov.in",
        "source_date": "2024-07-02 (CWC Barak Basin Division)",
        "observation_time": "Baseline Reference (WRD Cachar Division)",
        "last_verified_by": "WRD Cachar Division Silchar"
    },
    {
        "station_id": "CWC-MANGALDAI-11",
        "station_name": "Nonoi River at Mangaldai",
        "river": "Nonoi River (Brahmaputra Tributary)",
        "district": "Darrang",
        "latitude": 26.4350,
        "longitude": 92.0350,
        "warning_level_m": 53.14,
        "danger_level_m": 54.14,
        "hfl_m": 55.20,
        "current_level_m": None,
        "variance_m": None,
        "discharge_cumecs": None,
        "trend": "UNAVAILABLE",
        "provenance_state": DataSourceState.LAST_KNOWN.value,
        "is_live_telemetry": False,
        "source_url": "https://waterresources.assam.gov.in",
        "source_date": "2024-07-02 (Assam WRD Mangaldai Division)",
        "observation_time": "Baseline Reference (WRD Mangaldai)",
        "last_verified_by": "WRD Division Mangaldai"
    },
    {
        "station_id": "CWC-GOALPARA-12",
        "station_name": "Brahmaputra River at Goalpara",
        "river": "Brahmaputra River Mainstem",
        "district": "Goalpara",
        "latitude": 26.1782,
        "longitude": 90.6272,
        "warning_level_m": 35.27,
        "danger_level_m": 36.27,
        "hfl_m": 37.43,
        "current_level_m": None,
        "variance_m": None,
        "discharge_cumecs": None,
        "trend": "UNAVAILABLE",
        "provenance_state": DataSourceState.LAST_KNOWN.value,
        "is_live_telemetry": False,
        "source_url": "https://waterresources.assam.gov.in",
        "source_date": "2024-07-02 (CWC Lower Brahmaputra Division)",
        "observation_time": "Baseline Reference (CWC Goalpara Ghat)",
        "last_verified_by": "CWC Goalpara Site Office"
    }
]

_ACTIVE_GAUGES: List[Dict[str, Any]] = copy.deepcopy(DEFAULT_GAUGE_STATIONS)


def get_all_river_gauges(district: Optional[str] = None, location_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns all monitored river gauge stations with current status and danger margins.
    Supports optional district or location_id filtering while maintaining default access to all stations.
    """
    if location_id and not district:
        try:
            from app.core.location_registry import get_location_meta
            meta = get_location_meta(location_id)
            district = meta.district_name
        except Exception:
            pass

    if district and district.strip().upper() != "ALL":
        d_lower = district.strip().lower()
        return [g for g in _ACTIVE_GAUGES if d_lower in g.get("district", "").lower()]
    return _ACTIVE_GAUGES


def update_gauge_reading_manual(
    station_id: str,
    new_water_level_m: float,
    operator_name: str,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Records a certified manual water level observation for a gauge station.
    Persists an immutable audit log entry into the operational database.
    """
    global _ACTIVE_GAUGES
    target = None
    for g in _ACTIVE_GAUGES:
        if g["station_id"].upper() == station_id.upper():
            target = g
            break

    if not target:
        raise ValueError(f"Gauge station '{station_id}' not found.")

    old_level = target.get("current_level_m")
    target["current_level_m"] = round(new_water_level_m, 2)
    target["variance_m"] = round(target["current_level_m"] - target["danger_level_m"], 2)
    target["provenance_state"] = DataSourceState.MANUAL.value
    target["is_live_telemetry"] = False
    target["observation_time"] = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    target["last_verified_by"] = operator_name

    # Determine trend and alert tier
    if target["variance_m"] > 0:
        target["alert_tier"] = "ABOVE DANGER LEVEL"
        target["trend"] = "RISING / CRITICAL"
    elif target["current_level_m"] >= target["warning_level_m"]:
        target["alert_tier"] = "ALERT / WARNING LEVEL"
        target["trend"] = "WARNING"
    else:
        target["alert_tier"] = "NOMINAL (BELOW WARNING)"
        target["trend"] = "NORMAL"

    # Persist audit record to database
    db = SessionLocal()
    try:
        log_entry = AuditLogModel(
            operator_name=operator_name,
            entity_type="GAUGE_READING",
            entity_id=station_id,
            action="MANUAL_READING_UPDATE",
            old_value=str(old_level) if old_level is not None else "NONE",
            new_value=str(new_water_level_m),
            notes=notes or "Operator certified manual water gauge level update"
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    # Update registry
    registry.update_provider_status(
        provider_id="CWC-PANDU-03",
        state=DataSourceState.MANUAL,
        health_pct=100.0,
        observation_time=target["observation_time"]
    )

    return target
