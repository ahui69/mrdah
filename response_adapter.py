"""
Response adapter for API responses
"""
from typing import Any, Dict

def adapt(data: Any) -> Dict[str, Any]:
    """Adapt response data to standard format"""
    if isinstance(data, dict):
        return data
    return {"data": data}

def _wrap_for_ui(data: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap data for UI consumption"""
    return {
        "ok": True,
        "timestamp": __import__("time").time(),
        **data
    }