"""
RELIEFOS Lite — Data Source Registry & Provider Architecture
Standardized states:
LIVE, LAST_KNOWN, STALE, UNAVAILABLE, MANUAL, ESTIMATED, SIMULATED, UNVERIFIED
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import threading


class DataSourceState(str, Enum):
    LIVE = "LIVE"
    LAST_KNOWN = "LAST_KNOWN"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"
    MANUAL = "MANUAL"
    ESTIMATED = "ESTIMATED"
    SIMULATED = "SIMULATED"
    UNVERIFIED = "UNVERIFIED"


class DataSourceMetadata:
    def __init__(
        self,
        provider_id: str,
        name: str,
        authority: str,
        state: DataSourceState,
        endpoint: str,
        license_info: str,
        cadence: str,
        coverage: str,
        last_retrieval: Optional[str] = None,
        observation_time: Optional[str] = None,
        health_pct: float = 100.0,
        error_message: Optional[str] = None,
        is_live: bool = False
    ):
        self.provider_id = provider_id
        self.name = name
        self.authority = authority
        self.state = state
        self.endpoint = endpoint
        self.license_info = license_info
        self.cadence = cadence
        self.coverage = coverage
        self.last_retrieval = last_retrieval or datetime.now(timezone.utc).isoformat()
        self.observation_time = observation_time or datetime.now(timezone.utc).isoformat()
        self.health_pct = health_pct
        self.error_message = error_message
        self.is_live = is_live

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "code": self.provider_id,
            "name": self.name,
            "authority": self.authority,
            "state": self.state.value if isinstance(self.state, DataSourceState) else str(self.state),
            "class_type": self.state.value if isinstance(self.state, DataSourceState) else str(self.state),
            "endpoint": self.endpoint,
            "license": self.license_info,
            "protocol": "REST / JSON (HTTPS)",
            "cadence": self.cadence,
            "coverage": self.coverage,
            "last_retrieval": self.last_retrieval,
            "last_ingest": self.last_retrieval,
            "observation_time": self.observation_time,
            "health_pct": self.health_pct,
            "status": "HEALTHY" if self.health_pct >= 90.0 else "DEGRADED" if self.health_pct >= 50.0 else "UNAVAILABLE",
            "error_message": self.error_message,
            "is_live": self.is_live
        }


class DataSourceRegistry:
    """Thread-safe central registry managing all external and internal data providers."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DataSourceRegistry, cls).__new__(cls)
                cls._instance._providers: Dict[str, DataSourceMetadata] = {}
                cls._instance._cache: Dict[str, Any] = {}
                cls._instance._init_default_entries()
            return cls._instance

    def _init_default_entries(self):
        """Initializes canonical provider records with grounded metadata."""
        defaults = [
            DataSourceMetadata(
                provider_id="MET-OPENMETEO-01",
                name="Open-Meteo Global Meteorological Forecast & Precipitation",
                authority="Open-Meteo & DWD / ECMWF Open Data",
                state=DataSourceState.LIVE,
                endpoint="https://api.open-meteo.com/v1/forecast",
                license_info="CC-BY 4.0 Open License (No API Key Required)",
                cadence="Hourly NWP Assimilation (15-min Client Cache)",
                coverage="Kamrup Metropolitan (26.1445° N, 91.7362° E)",
                health_pct=100.0,
                is_live=True
            ),
            DataSourceMetadata(
                provider_id="ROU-OSRM-02",
                name="OpenStreetMap / OSRM Real Road Network Routing",
                authority="Project OSRM & OpenStreetMap Contributors",
                state=DataSourceState.LIVE,
                endpoint="https://router.project-osrm.org/route/v1/driving",
                license_info="ODbL 1.0 Open Database License (Public Tile/Route Policy)",
                cadence="On-Demand Dynamic Shortest Path",
                coverage="Guwahati Arterial & Highway Network",
                health_pct=100.0,
                is_live=True
            ),
            DataSourceMetadata(
                provider_id="CWC-PANDU-03",
                name="CWC Brahmaputra River Stage & Discharge Gauge",
                authority="Central Water Commission (CWC) - Pandu Ghat Station",
                state=DataSourceState.LAST_KNOWN,
                endpoint="https://cwc.gov.in/telemetry (Simulated Stub with Certified Baseline)",
                license_info="Government Open Data License - India (GODL)",
                cadence="Hourly Gauge Reading (Manual / Telemetric)",
                coverage="Pandu Ghat & DC Court Stations (Brahmaputra Basin)",
                health_pct=95.0,
                is_live=False
            ),
            DataSourceMetadata(
                provider_id="ASDMA-ALERTS-04",
                name="ASDMA District Emergency Operations Center Situation Reports",
                authority="Assam State Disaster Management Authority (ASDMA)",
                state=DataSourceState.MANUAL,
                endpoint="Internal EOC Incident Management Bus",
                license_info="Official Emergency Management Use Only",
                cadence="Event-driven / Shift handover",
                coverage="Kamrup Metro District (Guwahati EOC)",
                health_pct=100.0,
                is_live=False
            ),
            DataSourceMetadata(
                provider_id="PWD-CLOSURES-05",
                name="PWD Road Infrastructure Inundation & Closure Registry",
                authority="PWD Roads Assam & Guwahati Traffic Police",
                state=DataSourceState.MANUAL,
                endpoint="Local Database-Backed Chokepoint Ledger",
                license_info="State Emergency Transport Directive",
                cadence="Continuous Monitoring during Spate",
                coverage="Guwahati Arterial Bridges and Sluice Crossings",
                health_pct=100.0,
                is_live=False
            ),
            DataSourceMetadata(
                provider_id="DDMA-SHELTERS-06",
                name="Verified Relief Camps & Evacuation Shelters Ledger",
                authority="District Disaster Management Authority (DDMA) Kamrup Metro",
                state=DataSourceState.MANUAL,
                endpoint="Database-Backed Operational Registry",
                license_info="Official District Disaster Management Plan 2024",
                cadence="Daily Camp Headcount Verification",
                coverage="5 Monitored Sectors (Sarusajai, Dispur, Bharalu, Uzan, Basistha)",
                health_pct=100.0,
                is_live=False
            ),
            DataSourceMetadata(
                provider_id="SIM-DRILL-07",
                name="Synthetic Stress-Test & Academic Drill Generator",
                authority="RELIEFOS Academic Decision-Support Core",
                state=DataSourceState.SIMULATED,
                endpoint="In-Memory Isolated Simulation Sandbox",
                license_info="Academic Research & Verification Use Only",
                cadence="Deterministic Scenario Invocation (Scenarios A-J)",
                coverage="Simulated Guwahati Urban Agglomeration",
                health_pct=100.0,
                is_live=False
            )
        ]
        for meta in defaults:
            self._providers[meta.provider_id] = meta

    def update_provider_status(
        self,
        provider_id: str,
        state: DataSourceState,
        health_pct: float,
        observation_time: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        with self._lock:
            if provider_id in self._providers:
                meta = self._providers[provider_id]
                meta.state = state
                meta.health_pct = health_pct
                meta.last_retrieval = datetime.now(timezone.utc).isoformat()
                if observation_time:
                    meta.observation_time = observation_time
                meta.error_message = error_message
                meta.is_live = (state == DataSourceState.LIVE)

    def get_all_providers(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [meta.to_dict() for meta in self._providers.values()]

    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            meta = self._providers.get(provider_id)
            return meta.to_dict() if meta else None


registry = DataSourceRegistry()
