
from typing import Any, Dict, List, Optional, Union

def _norm_source(s: Union[str, Dict[str, str]]) -> Dict[str, str]:
    if isinstance(s, str):
        return {"title": s, "url": s}
    if isinstance(s, dict):
        title = s.get("title") or s.get("name") or s.get("label") or s.get("url") or "źródło"
        url = s.get("url") or s.get("href") or s.get("link") or ""
        return {"title": title, "url": url}
    return {"title": "źródło", "url": ""}

def adapt(obj: Any, *, text_field_candidates: Optional[List[str]] = None, sources_field_candidates: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Normalize heterogeneous endpoint payloads to {text, sources[]} for the WebUI.
    - If obj is str -> {"text": obj, "sources": []}
    - If obj is dict -> pick the first present from text_field_candidates, and sources from sources_field_candidates.
    - Else -> str(obj)
    """
    text_field_candidates = text_field_candidates or ["text", "message", "summary", "result", "content", "output"]
    sources_field_candidates = sources_field_candidates or ["sources", "citations", "refs", "links"]
    # simple cases
    if obj is None:
        return {"text": "", "sources": []}
    if isinstance(obj, str):
        return {"text": obj, "sources": []}
    if isinstance(obj, (int, float, bool)):
        return {"text": str(obj), "sources": []}
    if isinstance(obj, list):
        # join list of strings as text, pass any url-like into sources
        items = [str(x) for x in obj]
        return {"text": "\n".join(items), "sources": []}
    if isinstance(obj, dict):
        text_val = None
        for k in text_field_candidates:
            if k in obj and obj[k]:
                text_val = obj[k]
                break
        # fallback: stringify
        if text_val is None:
            text_val = obj.get("error") or obj.get("detail") or str(obj)
        sources: List[Dict[str, str]] = []
        for k in sources_field_candidates:
            if k in obj and obj[k]:
                raw = obj[k]
                if isinstance(raw, (list, tuple)):
                    sources = [_norm_source(x) for x in raw][:12]
                elif isinstance(raw, (str, dict)):
                    sources = [_norm_source(raw)]
                break
        return {"text": text_val, "sources": sources}
    # default
    return {"text": str(obj), "sources": []}
