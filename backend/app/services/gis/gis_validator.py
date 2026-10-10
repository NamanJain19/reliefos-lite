"""
GIS Validation Engine for RELIEFOS Lite.
Performs RFC 7946 GeoJSON structural validation, EPSG:4326 WGS84 coordinate verification,
closed-ring polygon checks, and Kamrup Metropolitan / Guwahati bounding box validation.
"""

from typing import Dict, Any, List, Optional, Tuple
import math

# Bounding box for Kamrup Metropolitan, Guwahati, Assam
# Longitudes: ~91.50°E to ~91.95°E
# Latitudes: ~25.95°N to ~26.35°N
GUWAHATI_BOUNDS = {
    "min_lng": 91.50,
    "max_lng": 91.95,
    "min_lat": 25.95,
    "max_lat": 26.35
}


class GeoJsonValidationError:
    def __init__(self, dataset: str, feature_id: Optional[str], geometry_type: str,
                 status: str, issue: str, recommended_correction: str):
        self.dataset = dataset
        self.feature_id = feature_id
        self.geometry_type = geometry_type
        self.status = status  # PASS, WARNING, FAIL
        self.issue = issue
        self.recommended_correction = recommended_correction

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset": self.dataset,
            "feature_id": self.feature_id,
            "geometry_type": self.geometry_type,
            "status": self.status,
            "issue": self.issue,
            "recommended_correction": self.recommended_correction
        }


def validate_position(pos: Any, dataset: str, feature_id: Optional[str],
                      check_guwahati_bounds: bool = True) -> List[GeoJsonValidationError]:
    """Validates an individual [longitude, latitude, (elevation)] coordinate position."""
    errors = []
    if not isinstance(pos, (list, tuple)) or len(pos) < 2:
        errors.append(GeoJsonValidationError(
            dataset=dataset,
            feature_id=feature_id,
            geometry_type="Position",
            status="FAIL",
            issue=f"Position must be an array of at least 2 numbers, got: {pos}",
            recommended_correction="Ensure position is [longitude, latitude] or [longitude, latitude, elevation]."
        ))
        return errors

    lng, lat = pos[0], pos[1]

    # Type check
    if not isinstance(lng, (int, float)) or not isinstance(lat, (int, float)):
        errors.append(GeoJsonValidationError(
            dataset=dataset,
            feature_id=feature_id,
            geometry_type="Position",
            status="FAIL",
            issue=f"Coordinates must be numeric, got: ({type(lng).__name__}, {type(lat).__name__})",
            recommended_correction="Convert coordinate values to standard floating point numbers."
        ))
        return errors

    if math.isnan(lng) or math.isnan(lat):
        errors.append(GeoJsonValidationError(
            dataset=dataset,
            feature_id=feature_id,
            geometry_type="Position",
            status="FAIL",
            issue="Coordinate contains NaN (Not a Number)",
            recommended_correction="Provide valid finite numeric coordinate values."
        ))
        return errors

    # Check for inverted lat/lng (e.g. [26.18, 91.75] instead of [91.75, 26.18])
    if 25.0 <= lng <= 28.0 and 90.0 <= lat <= 93.0:
        errors.append(GeoJsonValidationError(
            dataset=dataset,
            feature_id=feature_id,
            geometry_type="Position",
            status="FAIL",
            issue=f"Inverted coordinate order detected: [{lng}, {lat}]. Latitude was passed first.",
            recommended_correction="Invert array elements to RFC 7946 order: [longitude, latitude]."
        ))
        return errors

    # Standard WGS84 range
    if not (-180.0 <= lng <= 180.0):
        errors.append(GeoJsonValidationError(
            dataset=dataset,
            feature_id=feature_id,
            geometry_type="Position",
            status="FAIL",
            issue=f"Longitude {lng} out of valid range [-180.0, 180.0]",
            recommended_correction="Provide valid longitude between -180 and +180 degrees."
        ))
    if not (-90.0 <= lat <= 90.0):
        errors.append(GeoJsonValidationError(
            dataset=dataset,
            feature_id=feature_id,
            geometry_type="Position",
            status="FAIL",
            issue=f"Latitude {lat} out of valid range [-90.0, 90.0]",
            recommended_correction="Provide valid latitude between -90 and +90 degrees."
        ))

    # Kamrup Metropolitan Regional Bounds
    if check_guwahati_bounds and not errors:
        b = GUWAHATI_BOUNDS
        if not (b["min_lng"] <= lng <= b["max_lng"] and b["min_lat"] <= lat <= b["max_lat"]):
            errors.append(GeoJsonValidationError(
                dataset=dataset,
                feature_id=feature_id,
                geometry_type="Position",
                status="WARNING",
                issue=f"Coordinate [{lng}, {lat}] is outside Kamrup Metropolitan operational bounds ({b['min_lng']}-{b['max_lng']}°E, {b['min_lat']}-{b['max_lat']}°N)",
                recommended_correction="Verify whether this asset or zone belongs within the Guwahati command area."
            ))

    return errors


def validate_linear_ring(ring: Any, dataset: str, feature_id: Optional[str],
                         check_guwahati_bounds: bool = True) -> List[GeoJsonValidationError]:
    """Validates a polygon linear ring (must have >= 4 coordinates, closed ring)."""
    errors = []
    if not isinstance(ring, list) or len(ring) < 4:
        errors.append(GeoJsonValidationError(
            dataset=dataset,
            feature_id=feature_id,
            geometry_type="LinearRing",
            status="FAIL",
            issue=f"Linear ring must contain at least 4 positions (triangle + closure), found {len(ring) if isinstance(ring, list) else 0}",
            recommended_correction="Provide at least 4 positions for a closed polygon ring."
        ))
        return errors

    # Validate each coordinate
    for pos in ring:
        errors.extend(validate_position(pos, dataset, feature_id, check_guwahati_bounds))

    # Check closure: first position equals last position
    first, last = ring[0], ring[-1]
    if isinstance(first, (list, tuple)) and isinstance(last, (list, tuple)):
        if len(first) >= 2 and len(last) >= 2:
            if abs(first[0] - last[0]) > 1e-7 or abs(first[1] - last[1]) > 1e-7:
                errors.append(GeoJsonValidationError(
                    dataset=dataset,
                    feature_id=feature_id,
                    geometry_type="LinearRing",
                    status="FAIL",
                    issue=f"Linear ring is not closed: first point [{first[0]}, {first[1]}] != last point [{last[0]}, {last[1]}]",
                    recommended_correction="Append the initial coordinate to the end of the ring array to seal the boundary."
                ))

    # Check non-zero enclosed area (Shoelace formula)
    area = 0.0
    for i in range(len(ring) - 1):
        p1, p2 = ring[i], ring[i + 1]
        if isinstance(p1, (list, tuple)) and isinstance(p2, (list, tuple)) and len(p1) >= 2 and len(p2) >= 2:
            area += (p1[0] * p2[1]) - (p2[0] * p1[1])
    area = abs(area) / 2.0
    if area < 1e-9:
        errors.append(GeoJsonValidationError(
            dataset=dataset,
            feature_id=feature_id,
            geometry_type="LinearRing",
            status="WARNING",
            issue=f"Polygon ring has near-zero planar area ({area:.2e}), suggesting collapsed or collinear vertices.",
            recommended_correction="Verify polygon vertices to ensure they define a valid 2D planar polygon."
        ))

    return errors


def validate_geometry(geom: Any, dataset: str, feature_id: Optional[str],
                      check_guwahati_bounds: bool = True) -> List[GeoJsonValidationError]:
    """Validates GeoJSON Geometry objects (Point, LineString, Polygon, MultiPolygon)."""
    errors = []
    if not isinstance(geom, dict):
        errors.append(GeoJsonValidationError(
            dataset=dataset,
            feature_id=feature_id,
            geometry_type="Geometry",
            status="FAIL",
            issue=f"Geometry must be a dictionary object, got: {type(geom).__name__}",
            recommended_correction="Provide a valid GeoJSON Geometry object with 'type' and 'coordinates'."
        ))
        return errors

    geom_type = geom.get("type")
    coords = geom.get("coordinates")

    if not geom_type:
        errors.append(GeoJsonValidationError(
            dataset=dataset,
            feature_id=feature_id,
            geometry_type="Geometry",
            status="FAIL",
            issue="Missing required 'type' field in geometry",
            recommended_correction="Specify geometry type (e.g. Point, LineString, Polygon, MultiPolygon)."
        ))
        return errors

    if coords is None:
        errors.append(GeoJsonValidationError(
            dataset=dataset,
            feature_id=feature_id,
            geometry_type=geom_type,
            status="FAIL",
            issue="Missing required 'coordinates' field in geometry",
            recommended_correction="Provide non-null coordinates array for the geometry."
        ))
        return errors

    if geom_type == "Point":
        errors.extend(validate_position(coords, dataset, feature_id, check_guwahati_bounds))

    elif geom_type == "LineString":
        if not isinstance(coords, list) or len(coords) < 2:
            errors.append(GeoJsonValidationError(
                dataset=dataset,
                feature_id=feature_id,
                geometry_type="LineString",
                status="FAIL",
                issue=f"LineString must contain at least 2 positions, got {len(coords) if isinstance(coords, list) else 0}",
                recommended_correction="Provide at least 2 valid coordinate points along the route line."
            ))
        else:
            for pt in coords:
                errors.extend(validate_position(pt, dataset, feature_id, check_guwahati_bounds))

    elif geom_type == "Polygon":
        if not isinstance(coords, list) or len(coords) < 1:
            errors.append(GeoJsonValidationError(
                dataset=dataset,
                feature_id=feature_id,
                geometry_type="Polygon",
                status="FAIL",
                issue="Polygon must contain at least an exterior linear ring array",
                recommended_correction="Provide array of rings, where coords[0] is the exterior boundary ring."
            ))
        else:
            for ring in coords:
                errors.extend(validate_linear_ring(ring, dataset, feature_id, check_guwahati_bounds))

    elif geom_type == "MultiPolygon":
        if not isinstance(coords, list) or len(coords) < 1:
            errors.append(GeoJsonValidationError(
                dataset=dataset,
                feature_id=feature_id,
                geometry_type="MultiPolygon",
                status="FAIL",
                issue="MultiPolygon must contain at least one polygon coordinates array",
                recommended_correction="Provide an array of polygon rings."
            ))
        else:
            for poly in coords:
                if not isinstance(poly, list):
                    errors.append(GeoJsonValidationError(
                        dataset=dataset,
                        feature_id=feature_id,
                        geometry_type="MultiPolygon",
                        status="FAIL",
                        issue="Malformed polygon in MultiPolygon",
                        recommended_correction="Ensure MultiPolygon contains an array of polygon ring arrays."
                    ))
                else:
                    for ring in poly:
                        errors.extend(validate_linear_ring(ring, dataset, feature_id, check_guwahati_bounds))

    else:
        errors.append(GeoJsonValidationError(
            dataset=dataset,
            feature_id=feature_id,
            geometry_type=geom_type,
            status="WARNING",
            issue=f"Geometry type '{geom_type}' is not actively processed by RELIEFOS Lite core layers",
            recommended_correction="Ensure geometry is Point, LineString, Polygon, or MultiPolygon."
        ))

    return errors


def validate_geojson_payload(geojson: Any, dataset_name: str = "Unknown Dataset",
                             check_guwahati_bounds: bool = True) -> Dict[str, Any]:
    """
    Validates a complete GeoJSON object against RFC 7946 specifications and
    domain-specific disaster management spatial requirements.
    """
    findings: List[GeoJsonValidationError] = []

    if not isinstance(geojson, dict):
        return {
            "dataset_name": dataset_name,
            "is_valid": False,
            "crs": "UNKNOWN",
            "total_features": 0,
            "valid_features": 0,
            "invalid_features": 0,
            "warnings_count": 0,
            "findings": [{
                "dataset": dataset_name,
                "feature_id": None,
                "geometry_type": "Root",
                "status": "FAIL",
                "issue": f"Root GeoJSON must be a JSON object (dictionary), got {type(geojson).__name__}",
                "recommended_correction": "Provide a valid GeoJSON FeatureCollection or Feature object."
            }]
        }

    root_type = geojson.get("type")
    if not root_type:
        findings.append(GeoJsonValidationError(
            dataset=dataset_name,
            feature_id=None,
            geometry_type="Root",
            status="FAIL",
            issue="Missing 'type' property at root level",
            recommended_correction="Specify 'type': 'FeatureCollection' or 'type': 'Feature'."
        ))

    crs_info = "EPSG:4326 (WGS84 Default)"
    if "crs" in geojson:
        crs_dict = geojson["crs"]
        if isinstance(crs_dict, dict) and "properties" in crs_dict:
            crs_name = crs_dict["properties"].get("name", "Custom CRS")
            crs_info = f"Declared: {crs_name}"
            if "CRS84" not in crs_name and "4326" not in crs_name:
                findings.append(GeoJsonValidationError(
                    dataset=dataset_name,
                    feature_id=None,
                    geometry_type="Root",
                    status="WARNING",
                    issue=f"Non-WGS84 CRS declared: '{crs_name}'. Leaflet requires WGS84 EPSG:4326 coordinates.",
                    recommended_correction="Reproject spatial data to EPSG:4326 (WGS84) before client ingestion."
                ))

    total_features = 0
    valid_features = 0
    invalid_features = 0

    if root_type == "FeatureCollection":
        features = geojson.get("features")
        if not isinstance(features, list):
            findings.append(GeoJsonValidationError(
                dataset=dataset_name,
                feature_id=None,
                geometry_type="FeatureCollection",
                status="FAIL",
                issue="'features' member must be an array of Feature objects",
                recommended_correction="Provide an array in the 'features' attribute."
            ))
        else:
            total_features = len(features)
            for idx, feat in enumerate(features):
                feat_id = None
                feat_has_fatal = False

                if not isinstance(feat, dict):
                    findings.append(GeoJsonValidationError(
                        dataset=dataset_name,
                        feature_id=f"Index-{idx}",
                        geometry_type="Feature",
                        status="FAIL",
                        issue=f"Feature at index {idx} is not an object",
                        recommended_correction="Ensure all items in features array are Feature objects."
                    ))
                    invalid_features += 1
                    continue

                if feat.get("type") != "Feature":
                    findings.append(GeoJsonValidationError(
                        dataset=dataset_name,
                        feature_id=f"Index-{idx}",
                        geometry_type=str(feat.get("type")),
                        status="FAIL",
                        issue=f"Object in features array must have type 'Feature', found '{feat.get('type')}'",
                        recommended_correction="Add 'type': 'Feature' to the object."
                    ))
                    feat_has_fatal = True

                props = feat.get("properties") or {}
                feat_id = feat.get("id") or props.get("id") or props.get("code") or f"Feature-{idx+1}"

                geom = feat.get("geometry")
                if not geom:
                    findings.append(GeoJsonValidationError(
                        dataset=dataset_name,
                        feature_id=feat_id,
                        geometry_type="Feature",
                        status="WARNING",
                        issue="Feature has null or missing geometry",
                        recommended_correction="Provide geometry or remove unmapped feature."
                    ))
                else:
                    geom_errors = validate_geometry(geom, dataset_name, feat_id, check_guwahati_bounds)
                    findings.extend(geom_errors)
                    if any(e.status == "FAIL" for e in geom_errors):
                        feat_has_fatal = True

                if feat_has_fatal:
                    invalid_features += 1
                else:
                    valid_features += 1

    elif root_type == "Feature":
        total_features = 1
        props = geojson.get("properties") or {}
        feat_id = geojson.get("id") or props.get("code") or "Feature-Single"
        geom = geojson.get("geometry")
        if not geom:
            findings.append(GeoJsonValidationError(
                dataset=dataset_name,
                feature_id=feat_id,
                geometry_type="Feature",
                status="WARNING",
                issue="Single feature has null or missing geometry",
                recommended_correction="Provide geometry."
            ))
            invalid_features = 1
        else:
            geom_errors = validate_geometry(geom, dataset_name, feat_id, check_guwahati_bounds)
            findings.extend(geom_errors)
            if any(e.status == "FAIL" for e in geom_errors):
                invalid_features = 1
            else:
                valid_features = 1

    fatal_count = sum(1 for f in findings if f.status == "FAIL")
    warnings_count = sum(1 for f in findings if f.status == "WARNING")
    is_valid = (fatal_count == 0)

    return {
        "dataset_name": dataset_name,
        "is_valid": is_valid,
        "crs": crs_info,
        "total_features": total_features,
        "valid_features": valid_features,
        "invalid_features": invalid_features,
        "fatal_errors_count": fatal_count,
        "warnings_count": warnings_count,
        "findings": [f.to_dict() for f in findings]
    }
