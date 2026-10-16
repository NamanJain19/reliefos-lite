import urllib.request
import json

def get_json(url):
    req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

print("=== 1. PROVIDERS & INTEGRATIONS HEALTH ===")
provs = get_json("http://127.0.0.1:8013/api/health/providers")
print(f"Total providers registered: {provs.get('total_providers')}")
for p in provs.get("providers", []):
    print(f"  * {p.get('provider_id')}: {p.get('provider_name')}")
    print(f"    State: {p.get('state')}, Authority: {p.get('authority')}")
    print(f"    Latency: {p.get('latency_ms')}ms, Observation Time: {p.get('observation_time')}")

print("\n=== 2. WEATHER TELEMETRY ACROSS DISTRICTS ===")
for dist in ["kamrup_metro", "barpeta", "nalbari", "cachar"]:
    w = get_json(f"http://127.0.0.1:8013/api/weather/current?location_id={dist}")
    print(f"  * District: {dist} ({w.get('target_location')})")
    print(f"    Source: {w.get('source')}")
    print(f"    State: {w.get('state')}, is_live: {w.get('is_live')}")
    print(f"    Obs Time: {w.get('observation_time')}, Retrieved: {w.get('retrieved_at')}")
    curr = w.get("current", {})
    print(f"    Current: Temp {curr.get('temperature_c')}C, Humidity {curr.get('humidity_pct')}%, Precip {curr.get('precipitation_rate_mm_h')} mm/h, Condition: {curr.get('weather_condition')}")
    fc = w.get("forecast_24h", [])
    print(f"    Forecast points: {len(fc)} hourly intervals")

print("\n=== 3. FLOOD HYDROLOGY TELEMETRY ===")
flood = get_json("http://127.0.0.1:8013/api/flood")
print(f"River basin: {flood.get('river_basin')}")
for g in flood.get("gauges", []):
    print(f"  * Gauge: {g.get('station_name')} ({g.get('station_id')})")
    print(f"    River: {g.get('river')}, District: {g.get('district')}")
    print(f"    Stage: {g.get('current_level_m')}m (Warning: {g.get('warning_level_m')}m, Danger: {g.get('danger_level_m')}m, Variance: {g.get('variance_m')}m)")
    print(f"    Provenance State: {g.get('provenance_state')}, is_live: {g.get('is_live_telemetry')}")
    print(f"    Obs Time: {g.get('observation_time')}, Source Date: {g.get('source_date')}")
