from typing import List, Dict, Any

ZONES_DATA: List[Dict[str, Any]] = [
    {
        "id": "zone-01",
        "code": "ZONE 01",
        "name": "North Guwahati (Riverfront)",
        "latitude": 26.208,
        "longitude": 91.732,
        "population": 2850,
        "risk_tier": "CRITICAL",
        "risk_score": 8.8,
        "food_demand_kg": 1200,
        "water_demand_kg": 900,
        "total_demand_kg": 2100,
        "severity_weight": 10.0,
        "is_accessible": True,
        "inundation_area_ha": 24.1,
        "avg_flood_depth_m": 1.10,
        "key_road_status": "MONITORED",
        "recommended_interventions": [
            "Pre-position NDRF Inflatable Zodiac Unit VH-01 at Sonaram Field.",
            "Deploy levee monitoring team at ch 3+400."
        ]
    },
    {
        "id": "zone-02",
        "code": "ZONE 02",
        "name": "Bharalumukh Sluice Basin",
        "latitude": 26.172,
        "longitude": 91.735,
        "population": 4120,
        "risk_tier": "CRITICAL",
        "risk_score": 9.2,
        "food_demand_kg": 1000,
        "water_demand_kg": 700,
        "total_demand_kg": 1700,
        "severity_weight": 10.0,
        "is_accessible": True,
        "inundation_area_ha": 38.4,
        "avg_flood_depth_m": 1.85,
        "key_road_status": "RESTRICTED (MG Road Severed)",
        "recommended_interventions": [
            "Deploy 2x 500 GPM high-discharge diesel pumps to Santipur culvert junction.",
            "Enforce detour via AT Road Arterial Bypass (Arya Nagar flyover).",
            "Trigger targeted SMS evacuation advisories to 420 riverbank households."
        ]
    },
    {
        "id": "zone-03",
        "code": "ZONE 03",
        "name": "Uzan Bazar Ghat",
        "latitude": 26.195,
        "longitude": 91.758,
        "population": 3400,
        "risk_tier": "HIGH",
        "risk_score": 7.1,
        "food_demand_kg": 800,
        "water_demand_kg": 600,
        "total_demand_kg": 1400,
        "severity_weight": 5.0,
        "is_accessible": True,
        "inundation_area_ha": 19.7,
        "avg_flood_depth_m": 0.85,
        "key_road_status": "OPEN",
        "recommended_interventions": [
            "Maintain sandbag reinforcement at Old City Waterfront.",
            "Stage 1 boat and 1 pump at Ghat float station."
        ]
    },
    {
        "id": "zone-04",
        "code": "ZONE 04",
        "name": "Basistha Stream Corridor",
        "latitude": 26.118,
        "longitude": 91.785,
        "population": 1920,
        "risk_tier": "MODERATE",
        "risk_score": 5.2,
        "food_demand_kg": 700,
        "water_demand_kg": 500,
        "total_demand_kg": 1200,
        "severity_weight": 2.0,
        "is_accessible": True,
        "inundation_area_ha": 12.5,
        "avg_flood_depth_m": 0.45,
        "key_road_status": "OPEN",
        "recommended_interventions": [
            "Monitor culvert clearance along Southern NH-27 Foothills.",
            "Maintain alert level for flash hill runoff."
        ]
    },
    {
        "id": "zone-05",
        "code": "ZONE 05",
        "name": "Dispur Secretariat Lowlands",
        "latitude": 26.142,
        "longitude": 91.792,
        "population": 850,
        "risk_tier": "LOW",
        "risk_score": 3.0,
        "food_demand_kg": 500,
        "water_demand_kg": 300,
        "total_demand_kg": 800,
        "severity_weight": 1.0,
        "is_accessible": True,
        "inundation_area_ha": 4.2,
        "avg_flood_depth_m": 0.10,
        "key_road_status": "OPEN",
        "recommended_interventions": [
            "Storm drains flowing freely; standard administrative readiness."
        ]
    }
]

DEPOT_DATA = {
    "id": "depot-01",
    "code": "DEPOT-GAU-01",
    "name": "Sarusajai Central Logistics Hub",
    "latitude": 26.115,
    "longitude": 91.758,
    "total_capacity_kg": 15000,
    "available_food_kg": 2500,
    "available_water_kg": 3000,
    "reserved_food_kg": 700,
    "reserved_water_kg": 500
}

SHELTERS_DATA: List[Dict[str, Any]] = [
    {
        "id": "shelter-01",
        "name": "Kamrup Girls High School Relief Camp",
        "zone_code": "ZONE 02",
        "location_desc": "Bharalumukh West",
        "latitude": 26.170,
        "longitude": 91.732,
        "capacity": 350,
        "occupancy": 140,
        "status": "ACTIVE"
    },
    {
        "id": "shelter-02",
        "name": "Dispur High School Relief Shelter",
        "zone_code": "ZONE 05",
        "location_desc": "Dispur Secretariat Lowlands",
        "latitude": 26.145,
        "longitude": 91.795,
        "capacity": 500,
        "occupancy": 95,
        "status": "STANDBY"
    }
]

VEHICLES_DATA: List[Dict[str, Any]] = [
    {
        "id": "vh-01",
        "code": "VH-01",
        "name": "Tata 407 (4x4)",
        "vehicle_type": "High-Clearance 4x4 Truck",
        "max_capacity_kg": 2000,
        "status": "AVAILABLE",
        "assigned_route": "North Ghy (Saraighat Bridge)",
        "current_lat": 26.195,
        "current_lng": 91.710,
        "location_classification": "SIMULATED GPS TRANSPONDER",
        "payload_allocated_kg": 1800,
        "utilization_pct": 90.0
    },
    {
        "id": "vh-02",
        "code": "VH-02",
        "name": "Ashok Leyland 4x4",
        "vehicle_type": "Heavy Rescue Transport",
        "max_capacity_kg": 1800,
        "status": "AVAILABLE",
        "assigned_route": "Bharalumukh (AT Road Bypass)",
        "current_lat": 26.168,
        "current_lng": 91.740,
        "location_classification": "SIMULATED GPS TRANSPONDER",
        "payload_allocated_kg": 1750,
        "utilization_pct": 97.2
    },
    {
        "id": "vh-03",
        "code": "VH-03",
        "name": "Mahindra Bolero Camper",
        "vehicle_type": "Rapid Dispatch 4WD",
        "max_capacity_kg": 1200,
        "status": "AVAILABLE",
        "assigned_route": "Basistha / Dispur Corridor",
        "current_lat": 26.128,
        "current_lng": 91.775,
        "location_classification": "SIMULATED GPS TRANSPONDER",
        "payload_allocated_kg": 1200,
        "utilization_pct": 100.0
    }
]

INVENTORY_ITEMS_DATA: List[Dict[str, Any]] = [
    {
        "sku": "FOOD-001",
        "name": "Masoor Dal & Rice Grain Packs",
        "description": "Standard 50kg double-seal moisture resistant sacks",
        "category": "Food Supplies",
        "available_qty": 1300,
        "reserved_qty": 700,
        "total_buffer": 2000,
        "unit": "kg",
        "status": "In Stock",
        "verified_at": "14:30 IST"
    },
    {
        "sku": "FOOD-002",
        "name": "Ready-to-Eat Thermal Meal Kits",
        "description": "NDRF Spec self-heating MRE packs (1,800 kcal)",
        "category": "Packaged Food",
        "available_qty": 650,
        "reserved_qty": 350,
        "total_buffer": 1000,
        "unit": "kg",
        "status": "In Stock",
        "verified_at": "14:15 IST"
    },
    {
        "sku": "FOOD-003",
        "name": "Fortified High-Calorie Dry Biscuits",
        "description": "Emergency dry ration boxes with glucose enrich",
        "category": "Dry Rations",
        "available_qty": 550,
        "reserved_qty": 150,
        "total_buffer": 700,
        "unit": "kg",
        "status": "In Stock",
        "verified_at": "13:50 IST"
    },
    {
        "sku": "WATR-001",
        "name": "20L Potable Treated Water Cans",
        "description": "PHED lab-certified mobile water canister containers",
        "category": "Drinking Water",
        "available_qty": 1500,
        "reserved_qty": 900,
        "total_buffer": 2400,
        "unit": "L",
        "status": "In Stock",
        "verified_at": "14:38 IST"
    },
    {
        "sku": "WATR-002",
        "name": "Bottled Mineral Water (1L Cartons)",
        "description": "12-bottle crates for infant/elderly triage distribution",
        "category": "Drinking Water",
        "available_qty": 900,
        "reserved_qty": 300,
        "total_buffer": 1200,
        "unit": "L",
        "status": "In Stock",
        "verified_at": "14:05 IST"
    },
    {
        "sku": "MED-001",
        "name": "Chlorine & Water Purification Tabs",
        "description": "Aquatabs 67mg strips (1 tablet per 20L)",
        "category": "Medical",
        "available_qty": 8500,
        "reserved_qty": 1500,
        "total_buffer": 10000,
        "unit": "boxes",
        "status": "In Stock",
        "verified_at": "12:45 IST"
    },
    {
        "sku": "MED-002",
        "name": "Emergency ORS Sachets (WHO Spec)",
        "description": "Zinc + Oral Rehydration Salt packets for dehydration",
        "category": "Medical",
        "available_qty": 4200,
        "reserved_qty": 800,
        "total_buffer": 5000,
        "unit": "boxes",
        "status": "In Stock",
        "verified_at": "12:30 IST"
    },
    {
        "sku": "MED-003",
        "name": "Infant Nutritional Powder Formula",
        "description": "Stage 1 & 2 hypoallergenic fortified milk powder",
        "category": "Medical",
        "available_qty": 45,
        "reserved_qty": 55,
        "total_buffer": 100,
        "unit": "kg",
        "status": "Low Stock",
        "verified_at": "11:20 IST"
    }
]

DEMAND_RECORDS_DATA: List[Dict[str, Any]] = [
    {
        "id": "DEM-2024-001",
        "zone_code": "ZONE 01",
        "zone_name": "North Guwahati (Riverfront)",
        "resource_type": "Food Supplies",
        "requested_qty": 1200,
        "unit": "kg",
        "priority": "CRITICAL",
        "status": "APPROVED",
        "request_source": "Field Audit (ASDMA Circle Officer)",
        "created_at": "Today, 13:45 IST"
    },
    {
        "id": "DEM-2024-002",
        "zone_code": "ZONE 01",
        "zone_name": "North Guwahati (Riverfront)",
        "resource_type": "Potable Water",
        "requested_qty": 900,
        "unit": "L",
        "priority": "CRITICAL",
        "status": "APPROVED",
        "request_source": "Field Audit",
        "created_at": "Today, 13:45 IST"
    },
    {
        "id": "DEM-2024-003",
        "zone_code": "ZONE 02",
        "zone_name": "Bharalumukh Sluice Basin",
        "resource_type": "Food Supplies",
        "requested_qty": 1000,
        "unit": "kg",
        "priority": "CRITICAL",
        "status": "APPROVED",
        "request_source": "Observed Population Census",
        "created_at": "Today, 13:50 IST"
    },
    {
        "id": "DEM-2024-004",
        "zone_code": "ZONE 02",
        "zone_name": "Bharalumukh Sluice Basin",
        "resource_type": "Potable Water",
        "requested_qty": 700,
        "unit": "L",
        "priority": "CRITICAL",
        "status": "APPROVED",
        "request_source": "Observed Population Census",
        "created_at": "Today, 13:50 IST"
    },
    {
        "id": "DEM-2024-005",
        "zone_code": "ZONE 03",
        "zone_name": "Uzan Bazar Ghat",
        "resource_type": "Food Supplies",
        "requested_qty": 800,
        "unit": "kg",
        "priority": "HIGH",
        "status": "APPROVED",
        "request_source": "Community Liaison",
        "created_at": "Today, 14:00 IST"
    },
    {
        "id": "DEM-2024-006",
        "zone_code": "ZONE 03",
        "zone_name": "Uzan Bazar Ghat",
        "resource_type": "Potable Water",
        "requested_qty": 600,
        "unit": "L",
        "priority": "HIGH",
        "status": "APPROVED",
        "request_source": "Community Liaison",
        "created_at": "Today, 14:00 IST"
    },
    {
        "id": "DEM-2024-007",
        "zone_code": "ZONE 04",
        "zone_name": "Basistha Stream Corridor",
        "resource_type": "Food Supplies",
        "requested_qty": 700,
        "unit": "kg",
        "priority": "MEDIUM",
        "status": "PENDING",
        "request_source": "Estimated Demand Model",
        "created_at": "Today, 14:10 IST"
    },
    {
        "id": "DEM-2024-008",
        "zone_code": "ZONE 04",
        "zone_name": "Basistha Stream Corridor",
        "resource_type": "Potable Water",
        "requested_qty": 500,
        "unit": "L",
        "priority": "MEDIUM",
        "status": "PENDING",
        "request_source": "Estimated Demand Model",
        "created_at": "Today, 14:10 IST"
    },
    {
        "id": "DEM-2024-009",
        "zone_code": "ZONE 05",
        "zone_name": "Dispur Secretariat Lowlands",
        "resource_type": "Food Supplies",
        "requested_qty": 500,
        "unit": "kg",
        "priority": "LOW",
        "status": "PENDING",
        "request_source": "Estimated Demand Model",
        "created_at": "Today, 14:15 IST"
    },
    {
        "id": "DEM-2024-010",
        "zone_code": "ZONE 05",
        "zone_name": "Dispur Secretariat Lowlands",
        "resource_type": "Potable Water",
        "requested_qty": 300,
        "unit": "L",
        "priority": "LOW",
        "status": "PENDING",
        "request_source": "Estimated Demand Model",
        "created_at": "Today, 14:15 IST"
    }
]

FLOOD_OBSERVATIONS_DATA: List[Dict[str, Any]] = [
    {
        "station_id": "CWC-GAU-01",
        "station_name": "DC Court Station (Brahmaputra)",
        "river": "Brahmaputra River",
        "latitude": 26.191,
        "longitude": 91.745,
        "station_classification": "OBSERVED TELEMETRY (CWC)",
        "current_level_m": 49.68,
        "warning_level_m": 49.26,
        "danger_level_m": 49.50,
        "variance_m": 0.42,
        "alert_tier": "ABOVE DANGER",
        "discharge_cumecs": 38200.0,
        "observed_at": "14:40 IST (CWC Gauges)"
    },
    {
        "station_id": "CWC-GAU-02",
        "station_name": "Bharalu Sluice Gate",
        "river": "Bharalu Tributary",
        "latitude": 26.172,
        "longitude": 91.735,
        "station_classification": "OBSERVED TELEMETRY (CWC)",
        "current_level_m": 48.15,
        "warning_level_m": 47.50,
        "danger_level_m": 48.00,
        "variance_m": 0.15,
        "alert_tier": "ALERT",
        "discharge_cumecs": 142.0,
        "observed_at": "14:41 IST"
    },
    {
        "station_id": "CWC-GAU-03",
        "station_name": "Basistha Bridge Sensor",
        "river": "Basistha River",
        "latitude": 26.118,
        "longitude": 91.785,
        "station_classification": "OBSERVED TELEMETRY (CWC)",
        "current_level_m": 52.10,
        "warning_level_m": 53.25,
        "danger_level_m": 54.00,
        "variance_m": -1.15,
        "alert_tier": "NOMINAL",
        "discharge_cumecs": 45.0,
        "observed_at": "14:38 IST"
    }
]

DATA_SOURCES_DATA: List[Dict[str, Any]] = [
    {
        "code": "CWC-HYD-01",
        "name": "Brahmaputra River Gauges (DC Court & Pandu)",
        "authority": "Central Water Commission (CWC)",
        "class_type": "OBSERVED",
        "protocol": "MQTT / GeoJSON",
        "cadence": "Every 15 min",
        "last_ingest": "14:40 IST (2m ago)",
        "health_pct": 99.9,
        "status": "HEALTHY"
    },
    {
        "code": "MET-RAD-02",
        "name": "IMD Doppler Radar & Open-Meteo GFS",
        "authority": "IMD RMC Borjhar / Open-Meteo",
        "class_type": "FORECAST",
        "protocol": "REST / NetCDF-4",
        "cadence": "Hourly",
        "last_ingest": "14:00 IST (42m ago)",
        "health_pct": 98.4,
        "status": "HEALTHY"
    },
    {
        "code": "SAT-SAR-03",
        "name": "Copernicus Sentinel-1 SAR Extent",
        "authority": "ESA / NRSC Disaster Watch",
        "class_type": "ESTIMATED",
        "protocol": "WMS / GeoTIFF COG",
        "cadence": "6-Hour Orbit",
        "last_ingest": "10:30 IST (4h 12m ago • Replaced)",
        "health_pct": 88.5,
        "status": "DEGRADED"
    },
    {
        "code": "GIS-RDS-04",
        "name": "Kamrup Metro Road Network & Bridge Graph",
        "authority": "OSM Assam / PWD Roads",
        "class_type": "STATIC + SENSOR",
        "protocol": "gRPC / Protobuf",
        "cadence": "Continuous",
        "last_ingest": "14:38 IST (4m ago)",
        "health_pct": 100.0,
        "status": "HEALTHY"
    },
    {
        "code": "ERP-DPT-05",
        "name": "Sarusajai Depot Inventory Ledger",
        "authority": "ASDMA Logistics ERP",
        "class_type": "MANUAL AUDIT",
        "protocol": "SQL Webhook / JSON",
        "cadence": "Every 30 min",
        "last_ingest": "14:15 IST (27m ago)",
        "health_pct": 99.5,
        "status": "HEALTHY"
    },
    {
        "code": "FLD-OBS-06",
        "name": "Zonal SDRF 4th Bn Incident Stream",
        "authority": "SDRF Assam Quick Response",
        "class_type": "MANUAL OBSERVED",
        "protocol": "TETRA / Mobile App",
        "cadence": "Event-driven",
        "last_ingest": "14:28 IST (14m ago)",
        "health_pct": 96.0,
        "status": "HEALTHY"
    },
    {
        "code": "DEM-EST-07",
        "name": "Population Exposure & Demand Model",
        "authority": "Census / GIS Grid v2.4",
        "class_type": "SIMULATED",
        "protocol": "RPC / JSON",
        "cadence": "On-demand snap",
        "last_ingest": "14:30 IST Snapshot",
        "health_pct": 99.1,
        "status": "HEALTHY"
    },
    {
        "code": "GIS-ZON-08",
        "name": "Kamrup Operational Zones GeoJSON Layer",
        "authority": "ASDMA Pilot Scheme v2.4",
        "class_type": "ESTIMATED",
        "protocol": "REST / GeoJSON",
        "cadence": "Version Controlled",
        "last_ingest": "Active v2.4",
        "health_pct": 100.0,
        "status": "HEALTHY"
    }
]
