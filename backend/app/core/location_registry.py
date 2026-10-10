"""
RELIEFOS Lite — Authoritative Backend Location Registry
Central registry of all 9 monitored districts across Assam with verified centroids,
bounding boxes, operational tiers, and ISO-compliant data availability flags.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from fastapi import Header, Query, HTTPException, status


class LocationMeta(BaseModel):
    id: str
    display_name: str
    short_name: str
    district_name: str
    state: str = "Assam"
    latitude: float
    longitude: float
    bounds: List[List[float]]
    operational_tier: str  # FULL_OPERATIONAL, TELEMETRY_MONITORED, BASELINE_REFERENCE
    tier_badge: str
    primary_river: str
    cwc_gauge_count: int
    data_availability: Dict[str, bool]


SUPPORTED_LOCATIONS: Dict[str, LocationMeta] = {
    "kamrup_metro": LocationMeta(
        id="kamrup_metro",
        display_name="Kamrup Metropolitan, Assam",
        short_name="Kamrup Metro",
        district_name="Kamrup Metropolitan",
        latitude=26.160,
        longitude=91.750,
        bounds=[[26.050, 91.600], [26.250, 91.900]],
        operational_tier="FULL_OPERATIONAL",
        tier_badge="FULL EOC GRID",
        primary_river="Brahmaputra Mainstem & Bharalu Tributary",
        cwc_gauge_count=4,
        data_availability={
            "zones": True,
            "shelters_depots": True,
            "fleet_routes": True,
            "cwc_gauges": True,
            "nwp_weather": True,
            "demands": True,
            "road_closures": True,
            "simulations": True
        }
    ),
    "kamrup_rural": LocationMeta(
        id="kamrup_rural",
        display_name="Kamrup Rural, Assam",
        short_name="Kamrup Rural",
        district_name="Kamrup Rural",
        latitude=26.3467,
        longitude=91.6458,
        bounds=[[25.950, 91.250], [26.650, 91.950]],
        operational_tier="CONTINGENCY_OPERATIONAL",
        tier_badge="DISTRICT EOC",
        primary_river="Puthimari River",
        cwc_gauge_count=1,
        data_availability={
            "zones": True,
            "shelters_depots": True,
            "fleet_routes": True,
            "cwc_gauges": True,
            "nwp_weather": True,
            "demands": True,
            "road_closures": True,
            "simulations": True
        }
    ),
    "barpeta": LocationMeta(
        id="barpeta",
        display_name="Barpeta, Assam",
        short_name="Barpeta",
        district_name="Barpeta",
        latitude=26.3216,
        longitude=90.9865,
        bounds=[[26.080, 90.750], [26.600, 91.300]],
        operational_tier="CONTINGENCY_OPERATIONAL",
        tier_badge="DISTRICT EOC",
        primary_river="Beki River (Manas Tributary)",
        cwc_gauge_count=1,
        data_availability={
            "zones": True,
            "shelters_depots": True,
            "fleet_routes": True,
            "cwc_gauges": True,
            "nwp_weather": True,
            "demands": True,
            "road_closures": True,
            "simulations": True
        }
    ),
    "nalbari": LocationMeta(
        id="nalbari",
        display_name="Nalbari, Assam",
        short_name="Nalbari",
        district_name="Nalbari",
        latitude=26.4494,
        longitude=91.4600,
        bounds=[[26.200, 91.250], [26.650, 91.650]],
        operational_tier="CONTINGENCY_OPERATIONAL",
        tier_badge="DISTRICT EOC",
        primary_river="Pagladiya River",
        cwc_gauge_count=1,
        data_availability={
            "zones": True,
            "shelters_depots": True,
            "fleet_routes": True,
            "cwc_gauges": True,
            "nwp_weather": True,
            "demands": True,
            "road_closures": True,
            "simulations": True
        }
    ),
    "darrang": LocationMeta(
        id="darrang",
        display_name="Darrang, Assam",
        short_name="Darrang",
        district_name="Darrang",
        latitude=26.4350,
        longitude=92.0350,
        bounds=[[26.150, 91.750], [26.750, 92.350]],
        operational_tier="CONTINGENCY_OPERATIONAL",
        tier_badge="DISTRICT EOC",
        primary_river="Nonoi River / Brahmaputra",
        cwc_gauge_count=1,
        data_availability={
            "zones": True,
            "shelters_depots": True,
            "fleet_routes": True,
            "cwc_gauges": True,
            "nwp_weather": True,
            "demands": True,
            "road_closures": True,
            "simulations": True
        }
    ),
    "morigaon": LocationMeta(
        id="morigaon",
        display_name="Morigaon, Assam",
        short_name="Morigaon",
        district_name="Morigaon",
        latitude=26.1642,
        longitude=92.3500,
        bounds=[[26.000, 92.050], [26.450, 92.650]],
        operational_tier="CONTINGENCY_OPERATIONAL",
        tier_badge="DISTRICT EOC",
        primary_river="Kopili River",
        cwc_gauge_count=1,
        data_availability={
            "zones": True,
            "shelters_depots": True,
            "fleet_routes": True,
            "cwc_gauges": True,
            "nwp_weather": True,
            "demands": True,
            "road_closures": True,
            "simulations": True
        }
    ),
    "goalpara": LocationMeta(
        id="goalpara",
        display_name="Goalpara, Assam",
        short_name="Goalpara",
        district_name="Goalpara",
        latitude=26.1782,
        longitude=90.6272,
        bounds=[[25.900, 90.200], [26.350, 90.950]],
        operational_tier="CONTINGENCY_OPERATIONAL",
        tier_badge="DISTRICT EOC",
        primary_river="Brahmaputra River Mainstem",
        cwc_gauge_count=1,
        data_availability={
            "zones": True,
            "shelters_depots": True,
            "fleet_routes": True,
            "cwc_gauges": True,
            "nwp_weather": True,
            "demands": True,
            "road_closures": True,
            "simulations": True
        }
    ),
    "nagaon": LocationMeta(
        id="nagaon",
        display_name="Nagaon, Assam",
        short_name="Nagaon",
        district_name="Nagaon",
        latitude=26.1531,
        longitude=92.6564,
        bounds=[[25.800, 92.300], [26.700, 93.150]],
        operational_tier="CONTINGENCY_OPERATIONAL",
        tier_badge="DISTRICT EOC",
        primary_river="Kopili River & Kolong",
        cwc_gauge_count=1,
        data_availability={
            "zones": True,
            "shelters_depots": True,
            "fleet_routes": True,
            "cwc_gauges": True,
            "nwp_weather": True,
            "demands": True,
            "road_closures": True,
            "simulations": True
        }
    ),
    "cachar": LocationMeta(
        id="cachar",
        display_name="Cachar, Assam",
        short_name="Cachar",
        district_name="Cachar",
        latitude=24.8319,
        longitude=92.7961,
        bounds=[[24.400, 92.400], [25.150, 93.200]],
        operational_tier="CONTINGENCY_OPERATIONAL",
        tier_badge="BARAK REGIONAL EOC",
        primary_river="Barak River Mainstem",
        cwc_gauge_count=1,
        data_availability={
            "zones": True,
            "shelters_depots": True,
            "fleet_routes": True,
            "cwc_gauges": True,
            "nwp_weather": True,
            "demands": True,
            "road_closures": True,
            "simulations": True
        }
    )
}

DEFAULT_LOCATION_ID = "kamrup_metro"


def normalize_location_id(raw_id: Optional[str]) -> str:
    """Normalizes string inputs to a canonical location_id."""
    if not raw_id:
        return DEFAULT_LOCATION_ID
    clean = raw_id.strip().lower().replace(" ", "_").replace("-", "_")
    # Common aliases
    aliases = {
        "kamrup": "kamrup_metro",
        "kamrup_metropolitan": "kamrup_metro",
        "guwahati": "kamrup_metro",
        "ghy": "kamrup_metro",
        "silchar": "cachar",
    }
    if clean in aliases:
        return aliases[clean]
    if clean in SUPPORTED_LOCATIONS:
        return clean
    # Fuzzy match on district name
    for loc_id, meta in SUPPORTED_LOCATIONS.items():
        if clean in meta.district_name.lower():
            return loc_id
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported location ID '{raw_id}'. Supported locations: {list(SUPPORTED_LOCATIONS.keys())}"
    )


def get_location_meta(location_id: Optional[str] = None) -> LocationMeta:
    canonical = normalize_location_id(location_id)
    return SUPPORTED_LOCATIONS[canonical]


def resolve_location(
    x_location_id: Optional[str] = Header(None, alias="X-Location-ID"),
    location_id: Optional[str] = Query(None, description="Operational location ID (e.g. 'kamrup_metro', 'barpeta')")
) -> str:
    """
    FastAPI dependency that resolves the target location from either query parameter
    or the X-Location-ID HTTP request header, defaulting safely to kamrup_metro.
    """
    candidate = location_id or x_location_id or DEFAULT_LOCATION_ID
    return normalize_location_id(candidate)
