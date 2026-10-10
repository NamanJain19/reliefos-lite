from datetime import datetime

def get_current_ist_timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

__all__ = ["get_current_ist_timestamp"]
