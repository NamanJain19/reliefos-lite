"""
RELIEFOS Lite — Flood Risk Dataset Audit Service
Audits available datasets, their source, spatial/temporal coverage, observation timestamps,
missing value handling, sensor gaps, and data-quality trust tiers according to ISO-19115 standards.
"""

from datetime import datetime, timezone
from typing import List

from app.schemas.risk import DatasetAuditItem, DatasetAuditResponse


def get_dataset_audit() -> DatasetAuditResponse:
    """
    Returns an authoritative audit of all operational datasets feeding flood risk analysis.
    Explicitly documents observation frequency, gaps, missing data handling, and limitations.
    """
    datasets: List[DatasetAuditItem] = [
        DatasetAuditItem(
            dataset_name="Open-Meteo Numerical Weather Prediction (ECMWF / DWD)",
            source_agency="Open-Meteo Weather API / European Centre for Medium-Range Weather Forecasts",
            spatial_coverage="Kamrup Metropolitan Centroid (26.1445°N, 91.7362°E), 2-4 km grid resolution",
            observation_timestamps="Real-time assimilation; hourly forecast steps for 48 hours",
            update_frequency="15-minute in-memory cache TTL (respects fair-use CC-BY 4.0 policy)",
            missing_data_handling="Cached valid forecast carried forward on timeout; flagged as ESTIMATED_FORECAST",
            known_sensor_gaps="Local micro-topography convective cells in Khasi foothills may produce localized cloudbursts uncaptured by coarse grid NWP models.",
            provenance_classification="LIVE / ESTIMATED_FORECAST",
            quality_trust_tier="TIER_2_TELEMETRY",
            limitations="Provides precipitation rates and accumulated rain forecasts; does not model surface runoff accumulation or storm-sewer hydraulic capacity."
        ),
        DatasetAuditItem(
            dataset_name="CWC Brahmaputra Basin Hydrometric River Gauges",
            source_agency="Central Water Commission (CWC) Assam Regional Circle & Guwahati Municipal Corporation",
            spatial_coverage="4 Gauging Stations: Pandu Ghat (Main Stem), DC Court, Bharalumukh Sluice, Basistha Stream",
            observation_timestamps="Official bulletins issued at 08:00, 14:00, and 18:00 IST; physical gauge boards read by hydrographers",
            update_frequency="Twice daily official bulletin cycle; manual real-time entries supported with officer audit logs",
            missing_data_handling="Last verified official bulletin reading carried forward (LAST_KNOWN state); variance tracked against danger level",
            known_sensor_gaps="Tributary automated acoustic level sensors subject to siltation drift and electrical feeder outages during peak storm events (documented Bharalu 2022 outage).",
            provenance_classification="LAST_KNOWN / MANUAL",
            quality_trust_tier="TIER_1_OFFICIAL",
            limitations="River water stage indicates primary regional drainage boundary condition; does not represent localized street-level water depth in interior settlements."
        ),
        DatasetAuditItem(
            dataset_name="ASDMA Historical Guwahati Urban Flood Archive (2018–2024)",
            source_agency="Assam State Disaster Management Authority (ASDMA) & IMD Borjhar",
            spatial_coverage="5 Kamrup Metropolitan Operational Zones (Wards 01–31, North Guwahati to Dispur)",
            observation_timestamps="Archived daily post-disaster memos (June 2022 Monsoon, July 2024 Cloudburst, and 2018–2024 monsoon records)",
            update_frequency="Annual post-monsoon data consolidation by ASDMA GIS and Field Documentation Division",
            missing_data_handling="Incomplete shift entries filtered out; missing rainfall correlated with IMD Borjhar automated rain gauge",
            known_sensor_gaps="Sub-daily flood timing in informal urban settlements estimated from rescue log dispatch timestamps rather than continuous electronic loggers.",
            provenance_classification="LAST_KNOWN / HISTORICAL_GROUND_TRUTH",
            quality_trust_tier="TIER_1_OFFICIAL",
            limitations="Archived flood severity tiers reflect historical municipal and rescue deployment records; urbanization and land-use changes since 2018 may alter runoff patterns."
        ),
        DatasetAuditItem(
            dataset_name="Kamrup Metropolitan Operational Zones Cadastral GIS Grid",
            source_agency="ASDMA Pilot Scheme v2.4 & DDMA Kamrup Metropolitan",
            spatial_coverage="5 Operational Zones (ZONE 01 to ZONE 05) closed RFC 7946 polygons in EPSG:4326 (WGS84)",
            observation_timestamps="2024 EOC Administrative Revision; static spatial polygon topology",
            update_frequency="Updated on EOC boundary reapportionment or gazette notification",
            missing_data_handling="Deterministic spatial containment; points outside bounding box flagged as OUT_OF_BOUNDS",
            known_sensor_gaps="Polygons represent emergency operations triage sectors rather than high-resolution 1m bare-earth LiDAR digital elevation models (DEM).",
            provenance_classification="MANUAL / ADMINISTRATIVE_GRID",
            quality_trust_tier="TIER_1_OFFICIAL",
            limitations="Zonal boundaries are operational administrative units. Sub-zonal elevation variations (e.g. low-lying pocket vs hilltop) are averaged across the sector."
        ),
        DatasetAuditItem(
            dataset_name="PWD Roads Assam & Traffic Police Chokepoint Registry",
            source_agency="Public Works Department (PWD) Roads Assam & Guwahati Traffic Police (EOC Traffic Desk)",
            spatial_coverage="Guwahati Arterial Road Corridors (MG Road, GS Road, AT Road, Saraighat Bridge approach)",
            observation_timestamps="Shift-by-shift traffic control updates and physical road depth markers",
            update_frequency="Event-driven updates when roadway waterlogging exceeds the 0.35m truck clearance threshold",
            missing_data_handling="Inactive closures purged after water recedes below 0.15m and pavement safety inspection completes",
            known_sensor_gaps="Interior lane waterlogging relies on ward officer call-ins; arterial corridors have direct traffic police observation.",
            provenance_classification="MANUAL / EVENT_DRIVEN",
            quality_trust_tier="TIER_1_OFFICIAL",
            limitations="Documents road clearance thresholds and detour availability; not a full continuous hydrodynamic transit model."
        )
    ]

    return DatasetAuditResponse(
        audit_title="RELIEFOS Lite — Comprehensive Operational Dataset & Provenance Audit",
        audited_at=datetime.now(timezone.utc).isoformat(),
        total_datasets=len(datasets),
        datasets=datasets,
        governance_compliance="ISO-19115 Geospatial Metadata Standard & ASDMA Form 8B Decision Support Audit Protocol"
    )
