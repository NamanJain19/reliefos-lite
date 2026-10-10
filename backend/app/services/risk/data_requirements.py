"""
RELIEFOS Lite — Hydrodynamic Data Requirements & Modeling Roadmap
Documents the exact sensory, topographic, and bathymetric data required to advance from
relative risk classification to full 2D hydrodynamic inundation and depth modeling.
Complies with Central Water Commission (CWC) and National Disaster Management Authority (NDMA) specifications.
"""

from typing import Dict, Any, List


HYDRODYNAMIC_DATA_REQUIREMENTS: List[Dict[str, Any]] = [
    {
        "category": "High-Resolution Terrain & Topography",
        "required_specification": "1m to 2m Bare-Earth LiDAR Digital Elevation Model (DEM) with vertical accuracy <= 0.15m",
        "current_status": "PARTIALLY_AVAILABLE (Coarse zone-level centroids and elevation classes)",
        "gap_impact": "Prevents micro-topographic ponding simulation in interior gullies and street-by-street depression storage calculations.",
        "authorizing_agency": "Survey of India (SOI) & Assam Remote Sensing Application Centre (ARSAC)"
    },
    {
        "category": "River & Sluice Channel Bathymetry",
        "required_specification": "Sonar cross-sectional riverbed geometry surveyed every 250m along Brahmaputra main stem and Bharalu basin outfall",
        "current_status": "UNAVAILABLE (Only surface water stage meters monitored at Pandu and DC Court)",
        "gap_impact": "Channel cross-section flow velocity and sediment deposition cannot be dynamically modeled in 1D/2D Saint-Venant hydraulic equations.",
        "authorizing_agency": "Inland Waterways Authority of India (IWAI) & Water Resources Department (WRD) Assam"
    },
    {
        "category": "Storm Sewer & Sub-Surface Conduit Network",
        "required_specification": "Full GIS attribute shapefiles of municipal drainage conduits, invert levels, culvert dimensions, and pump discharge capacities",
        "current_status": "MANUAL / CHOKEPOINT ONLY (Specific severed locations logged in PWD registry)",
        "gap_impact": "Sub-surface drainage backflow and storm sewer surcharge times cannot be calculated deterministically.",
        "authorizing_agency": "Guwahati Municipal Corporation (GMC) Drainage & Sewerage Division"
    },
    {
        "category": "Continuous Antecedent Soil Moisture & Infiltration",
        "required_specification": "Time-series Antecedent Moisture Condition (AMC) from in-situ TDR soil probes or high-res Sentinel-1 SAR soil moisture products",
        "current_status": "ESTIMATED (Assumed saturated during active monsoon months)",
        "gap_impact": "Soil infiltration rate (Horton / Green-Ampt) assumed constant rather than dynamically decaying with storm duration.",
        "authorizing_agency": "Assam Agricultural University & NESAC (North Eastern Space Applications Centre)"
    },
    {
        "category": "High-Density Urban Rain Gauge Telemetry",
        "required_specification": "Automated tipping-bucket rain gauges spaced <= 2 km apart with 5-minute telemetry intervals",
        "current_status": "COARSE_REGIONAL (Open-Meteo 4km NWP grid & IMD Borjhar airport single station)",
        "gap_impact": "Local convective cloudbursts confined to single hill watersheds may be delayed or underestimated in regional models.",
        "authorizing_agency": "India Meteorological Department (IMD) Regional Meteorological Centre Borjhar"
    }
]


def get_hydrodynamic_data_requirements() -> List[Dict[str, Any]]:
    """Returns the statutory data requirements roadmap for hydrodynamic modeling."""
    return HYDRODYNAMIC_DATA_REQUIREMENTS
