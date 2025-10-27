"""
Research policy and filtering
"""
from typing import List, Dict, Any


def filter_sources_tenant(sources: List[str], tenant_id: str = "default") -> List[str]:
    """Filter sources based on tenant configuration"""
    # Default implementation - allow all sources
    return sources


def filter_sources(sources: List[str]) -> List[str]:
    """Filter sources based on global configuration"""
    allowed_sources = ["duckduckgo", "wikipedia", "arxiv", "scholar"]
    return [s for s in sources if s in allowed_sources]


def is_allowed(source: str, tenant_id: str = "default") -> bool:
    """Check if source is allowed for tenant"""
    allowed_sources = ["duckduckgo", "wikipedia", "arxiv", "scholar"]
    return source in allowed_sources


def get_source_config(source: str) -> Dict[str, Any]:
    """Get configuration for specific source"""
    configs = {
        "duckduckgo": {"rate_limit": 10, "max_results": 20},
        "wikipedia": {"rate_limit": 20, "max_results": 10},
        "arxiv": {"rate_limit": 5, "max_results": 15},
        "scholar": {"rate_limit": 3, "max_results": 10}
    }
    return configs.get(source, {"rate_limit": 5, "max_results": 10})