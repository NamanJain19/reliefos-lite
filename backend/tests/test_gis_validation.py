"""
Automated GIS & Geospatial Data Validation Test Suite for RELIEFOS Lite.
Validates RFC 7946 GeoJSON compliance, EPSG:4326 coordinate reference system,
Guwahati/Kamrup Metro bounding box enforcement, closed polygon rings, and routing geometry continuity.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.services.gis.gis_validator import validate_geojson_payload, validate_position, validate_linear_ring
from app.services.gis.gis_service import get_zones_geojson, get_infrastructure_geojson, get_routes_geojson, run_full_gis_audit
from app.core.database import SessionLocal
from app.models.domain import ShelterModel

client = TestClient(app)


def test_gis_zones_geojson_endpoint():
    """Verify operational zones GeoJSON FeatureCollection conforms strictly to RFC 7946 and EPSG:4326."""
    response = client.get("/api/gis/zones.geojson")
    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "FeatureCollection"
    assert "crs" in data
    assert len(data["features"]) == 5

    zone_codes = {f["properties"]["code"] for f in data["features"]}
    assert zone_codes == {"ZONE 01", "ZONE 02", "ZONE 03", "ZONE 04", "ZONE 05"}

    for feat in data["features"]:
        assert feat["type"] == "Feature"
        geom = feat["geometry"]
        assert geom["type"] == "Polygon"
        rings = geom["coordinates"]
        assert len(rings) >= 1

        ext_ring = rings[0]
        # Minimum 4 positions (triangle + closing point)
        assert len(ext_ring) >= 4

        # Closed ring check
        first_pt = ext_ring[0]
        last_pt = ext_ring[-1]
        assert abs(first_pt[0] - last_pt[0]) < 1e-6, f"Polygon ring not closed for {feat['properties']['code']}"
        assert abs(first_pt[1] - last_pt[1]) < 1e-6, f"Polygon ring not closed for {feat['properties']['code']}"

        # Coordinate ordering: [longitude, latitude] in Kamrup Metropolitan bounds
        for pt in ext_ring:
            lng, lat = pt[0], pt[1]
            assert 91.50 <= lng <= 91.95, f"Longitude {lng} out of Guwahati bounds"
            assert 25.95 <= lat <= 26.35, f"Latitude {lat} out of Guwahati bounds"

        # Properties check
        props = feat["properties"]
        assert "risk_tier" in props
        assert "risk_score" in props
        assert "total_demand_kg" in props
        assert "data_classification" in props
        assert "EPSG:4326" in props["coordinate_system"]


def test_gis_infrastructure_geojson_endpoint():
    """Verify disaster relief infrastructure features (Depot, Shelters, River Gauges, Vehicles)."""
    response = client.get("/api/gis/infrastructure.geojson")
    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) >= 8

    entity_types = {f["properties"]["entity_type"] for f in data["features"]}
    assert "DEPOT" in entity_types
    assert "SHELTER" in entity_types
    assert "HYDRO_GAUGE" in entity_types
    assert "ROAD_CHOKEPOINT" in entity_types
    assert "RELIEF_VEHICLE" in entity_types

    for feat in data["features"]:
        geom = feat["geometry"]
        assert geom["type"] == "Point"
        lng, lat = geom["coordinates"][0], geom["coordinates"][1]
        # Longitude first, latitude second
        assert 91.50 <= lng <= 91.95, f"Infrastructure asset {feat['id']} longitude {lng} out of range"
        assert 25.95 <= lat <= 26.35, f"Infrastructure asset {feat['id']} latitude {lat} out of range"

        # Check transponders have classification
        if feat["properties"]["entity_type"] == "RELIEF_VEHICLE":
            assert feat["properties"]["classification"] == "SIMULATED GPS TRANSPONDER"


def test_gis_routes_geojson_endpoint():
    """Verify fleet convoy routes with LineString geometry, round-trip return, and flood evasion."""
    response = client.get("/api/gis/routes.geojson")
    assert response.status_code == 200
    data = response.json()

    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 3

    for feat in data["features"]:
        geom = feat["geometry"]
        assert geom["type"] == "LineString"
        coords = geom["coordinates"]
        assert len(coords) >= 4, "Route line must have multiple intermediate waypoints"

        # Roundtrip verification: Depot departure and arrival
        depot_lng, depot_lat = 91.758, 26.115
        start_pt = coords[0]
        end_pt = coords[-1]
        assert abs(start_pt[0] - depot_lng) < 1e-3 and abs(start_pt[1] - depot_lat) < 1e-3, "Route must start at Sarusajai Depot"
        assert abs(end_pt[0] - depot_lng) < 1e-3 and abs(end_pt[1] - depot_lat) < 1e-3, "Route must return to Sarusajai Depot"

        props = feat["properties"]
        assert props["roundtrip"] is True
        assert props["total_distance_km"] > 10.0

    # Specifically verify VH-02 detour
    vh02 = next(f for f in data["features"] if f["properties"]["vehicle_code"] == "VH-02")
    assert vh02["properties"]["flood_detour_applied"] is True
    assert "Arya Nagar" in vh02["properties"]["detour_reason"]


def test_gis_validation_report_endpoint():
    """Verify automated full GIS spatial audit report returns PASS with 0 fatal errors."""
    response = client.get("/api/gis/validation-report")
    assert response.status_code == 200
    data = response.json()

    assert data["overall_status"] == "PASS"
    assert data["coordinate_reference_system"] == "EPSG:4326 (WGS84)"
    assert data["fatal_errors"] == 0
    assert data["total_spatial_features"] >= 15
    assert len(data["provenance_summary"]) == 3


def test_custom_geojson_validator_logic():
    """Test validator detection of malformed geometries, unclosed rings, and inverted coordinates."""
    # 1. Valid Polygon
    valid_poly = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "TEST-01",
                "properties": {"name": "Test Polygon"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[91.72, 26.15], [91.74, 26.15], [91.74, 26.17], [91.72, 26.17], [91.72, 26.15]]
                    ]
                }
            }
        ]
    }
    res_valid = validate_geojson_payload(valid_poly, "Valid Poly Test")
    assert res_valid["is_valid"] is True
    assert res_valid["fatal_errors_count"] == 0

    # 2. Unclosed Polygon Ring
    unclosed_poly = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "TEST-UNCLOSED",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[91.72, 26.15], [91.74, 26.15], [91.74, 26.17], [91.72, 26.17]]  # Missing closing point
                    ]
                }
            }
        ]
    }
    res_unclosed = validate_geojson_payload(unclosed_poly, "Unclosed Test")
    assert res_unclosed["is_valid"] is False
    assert any("not closed" in f["issue"] for f in res_unclosed["findings"])

    # 3. Inverted Coordinates ([lat, lng] instead of [lng, lat])
    inverted_poly = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "TEST-INVERTED",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[26.15, 91.72], [26.15, 91.74], [26.17, 91.74], [26.17, 91.72], [26.15, 91.72]]
                    ]
                }
            }
        ]
    }
    res_inverted = validate_geojson_payload(inverted_poly, "Inverted Test")
    assert res_inverted["is_valid"] is False
    assert any("Inverted coordinate order" in f["issue"] for f in res_inverted["findings"])


def test_database_shelters_persistence():
    """Verify that ShelterModel is persisted with valid coordinates in the database."""
    db = SessionLocal()
    try:
        shelters = db.query(ShelterModel).all()
        assert len(shelters) >= 2
        for s in shelters:
            assert 26.0 <= s.latitude <= 26.3
            assert 91.6 <= s.longitude <= 91.9
            assert s.capacity > 0
    finally:
        db.close()


def test_router_waypoints_have_coordinates():
    """Verify that router.py returns waypoints with explicit lat/lng coordinates and polyline."""
    from app.services.routing.router import compute_fleet_optimized_routes
    routes_data = compute_fleet_optimized_routes()
    for route in routes_data["routes"]:
        assert "polyline_latlng" in route
        assert len(route["polyline_latlng"]) >= 4
        assert "geometry_geojson" in route
        assert route["geometry_geojson"]["type"] == "LineString"

        for wp in route["waypoints"]:
            assert "lat" in wp
            assert "lng" in wp
            assert 26.0 <= wp["lat"] <= 26.3
            assert 91.6 <= wp["lng"] <= 91.9
