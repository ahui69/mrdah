from fastapi import APIRouter, Depends
from core.licensing import require_license_dep
from core.pricing import suggest_price

router = APIRouter(prefix="/vinted", tags=["vinted"], dependencies=[Depends(require_license_dep("pro"))])

def _title_variants(brand, category, size, color):
    base = f"{brand} {category} {size} {color}".strip()
    t1 = f"{base} • top stan • oryginał"
    t2 = f"{brand} {category} {size} • {color} • premium quality"
    t3 = f"{category} {brand} • {color} • {size} • jak nowe"
    return [t1, t2, t3]

def _shotlist(category):
    return [
        "front na płasko, dobre światło",
        "tył i metka składu",
        "zbliżenie logo/haftu",
        "zbliżenie faktury materiału",
        "ew. wada z bliska (uczciwość podnosi konwersję)"
    ]

@router.post("/listing")
def make_listing(payload: dict):
    brand   = payload.get("brand","")
    category= payload.get("category","")
    size    = payload.get("size","")
    color   = payload.get("color","")
    material= payload.get("material","")
    condition = payload.get("condition","dobry")
    defects = payload.get("defects","brak")
    measures= payload.get("measurements",{})  # dict: chest/length/waist/inseam...
    orig    = float(payload.get("original_price",0) or 0)
    comps   = (float(payload.get("comps_avg")) if payload.get("comps_avg") else None)
    demand  = float(payload.get("demand",0.6))

    pricing = suggest_price(brand, condition, orig, comps, demand)
    titles = _title_variants(brand, category, size, color)

    dims = []
    for k in ["chest","waist","length","inseam","sleeve"]:
        if k in measures: dims.append(f"{k}: {measures[k]} cm")

    desc = (
        f"{brand} {category} – {color}\n"
        f"• Stan: {condition}\n"
        + (f"• Materiał: {material}\n" if material else "")
        + (f"• Wymiary: {', '.join(dims)}\n" if dims else "")
        + (f"• Wady: {defects}\n" if defects and defects!='brak' else "• Wady: brak\n")
        + "• Dom bez dymu i zwierząt\n"
        + "• Pakuję solidnie, wysyłka 24h\n\n"
        "Dlaczego warto: dobra marka, sensowna cena wyjściowa i pełne wymiary → mniej zwrotów, szybciej sprzedane."
    )

    tags = [brand, category, color, size, "premium", "oryginał", "jak_nowe"]
    strategy = {
        "pricing": pricing,
        "offers_rule": f"Auto-akceptacja >= {pricing['min']} PLN, zakres negocjacji: {int(pricing['min'])}-{int(pricing['start'])} PLN.",
        "bundle": "Rabat 10% przy 2+ sztukach – informacja w opisie i wiadomości automatycznej.",
        "refresh": "Jeśli brak ruchu 48h: zmiana tytułu (wariant B/C) + -5 PLN; po 5 dniach wróć do anchor i ponów cykl."
    }

    return {
        "titles": titles,
        "description": desc,
        "price": pricing,
        "hashtags": [t.lower().replace(" ","_") for t in tags],
        "photo_shotlist": _shotlist(category),
        "strategy": strategy
    }
