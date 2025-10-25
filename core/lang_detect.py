
import os

_DET = None
_FASTTEXT = None

def _load_fasttext(model_path: str):
    global _FASTTEXT
    try:
        import fasttext  # type: ignore
        _FASTTEXT = fasttext.load_model(model_path)
        return True
    except Exception:
        return False

def _load_cld3():
    global _DET
    try:
        import cld3  # type: ignore
        _DET = cld3
        return True
    except Exception:
        return False

def detect_lang(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "und"
    # 1) CLD3 if available
    if _DET or _load_cld3():
        try:
            r = _DET.get_language(t)  # type: ignore
            if r and r.is_reliable and r.language:
                return r.language
        except Exception:
            pass
    # 2) fastText if configured via ENV
    model_path = os.getenv("FASTTEXT_LID_MODEL","")
    if model_path and (_FASTTEXT or _load_fasttext(model_path)):
        try:
            # fastText returns labels like '__label__pl'
            lab, prob = _FASTTEXT.predict(t.replace("\n"," "))  # type: ignore
            if lab and len(lab)>0:
                code = str(lab[0]).split("__")[-1]
                return code
        except Exception:
            pass
    # 3) fallback heuristic (pl vs en)
    import re
    low = t.lower()
    if re.search(r"[ąćęłńóśźż]", low):
        return "pl"
    if re.search(r"\b(the|and|you|are|is|this|that)\b", low):
        return "en"
    return "pl" if sum(c in 'ąćęłńóśźż' for c in low) > 0 else "en"
