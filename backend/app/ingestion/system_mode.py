"""
RELIEFOS Lite — System Operational Mode Manager
Manages strict separation between:
1. OPERATIONAL_LIVE: Real-world weather, real road network, database-backed stock & verified demands.
2. HISTORICAL_EVENT: Authentic archived flood disasters with explicit observation bounds.
3. SIMULATION_DRILL: Sandboxed what-if drills isolated from live database stores.
"""

from typing import Dict, Any
from datetime import datetime, timezone
import threading

from app.core.database import SessionLocal
from app.models.domain import AuditLogModel

class SystemModeType:
    OPERATIONAL_LIVE = "OPERATIONAL_LIVE"
    HISTORICAL_EVENT = "HISTORICAL_EVENT"
    SIMULATION_DRILL = "SIMULATION_DRILL"

_CURRENT_MODE: str = SystemModeType.OPERATIONAL_LIVE
_MODE_SWITCHED_AT: str = datetime.now(timezone.utc).isoformat()
_ACTIVE_HISTORICAL_EVENT: str = "HIST-2022-GHY-MONSOON"
_MODE_LOCK = threading.Lock()


def get_system_mode_status() -> Dict[str, Any]:
    """Retrieves active system operating mode and isolation guarantees."""
    with _MODE_LOCK:
        return {
            "mode": _CURRENT_MODE,
            "switched_at": _MODE_SWITCHED_AT,
            "is_operational": (_CURRENT_MODE == SystemModeType.OPERATIONAL_LIVE),
            "is_historical": (_CURRENT_MODE == SystemModeType.HISTORICAL_EVENT),
            "is_simulation": (_CURRENT_MODE == SystemModeType.SIMULATION_DRILL),
            "active_historical_event": _ACTIVE_HISTORICAL_EVENT if _CURRENT_MODE == SystemModeType.HISTORICAL_EVENT else None,
            "isolation_guarantee": (
                "ZERO_MUTATION_TO_OPERATIONAL_STORE" if _CURRENT_MODE == SystemModeType.SIMULATION_DRILL
                else "PERSISTENT_DATABASE_TRANSACTIONS_ACTIVE"
            ),
            "mode_descriptions": {
                "OPERATIONAL_LIVE": "Real-time decision support with live Open-Meteo weather, OSRM road graph, database inventory, and verified shelter registries.",
                "HISTORICAL_EVENT": "Replay and analysis of verified past disaster records (Guwahati June 2022 / July 2024) with disclosed sensor gaps.",
                "SIMULATION_DRILL": "In-memory sandboxed emergency exercises (ASDMA-DRILL-2024-GHY-01) with deep-copy isolation."
            }
        }


def switch_system_mode(
    new_mode: str,
    operator_name: str = "Insp. S. Sharma (Operations Planner)",
    historical_event_id: str = "HIST-2022-GHY-MONSOON",
    notes: str = ""
) -> Dict[str, Any]:
    """
    Transitions the system mode with strict validation and audit logging.
    """
    global _CURRENT_MODE, _MODE_SWITCHED_AT, _ACTIVE_HISTORICAL_EVENT

    valid_modes = [
        SystemModeType.OPERATIONAL_LIVE,
        SystemModeType.HISTORICAL_EVENT,
        SystemModeType.SIMULATION_DRILL
    ]

    target = new_mode.strip().upper()
    if target not in valid_modes:
        raise ValueError(f"Invalid system mode '{new_mode}'. Must be one of: {', '.join(valid_modes)}")

    with _MODE_LOCK:
        old_mode = _CURRENT_MODE
        _CURRENT_MODE = target
        _MODE_SWITCHED_AT = datetime.now(timezone.utc).isoformat()
        if target == SystemModeType.HISTORICAL_EVENT:
            _ACTIVE_HISTORICAL_EVENT = historical_event_id

    # Record persistent audit entry
    db = SessionLocal()
    try:
        log_entry = AuditLogModel(
            operator_name=operator_name,
            entity_type="SYSTEM_MODE",
            entity_id=f"MODE-{target}",
            action="SWITCH_MODE",
            old_value=old_mode,
            new_value=target,
            notes=notes or f"Operator initiated system mode transition from {old_mode} to {target}"
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    return get_system_mode_status()
