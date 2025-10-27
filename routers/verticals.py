from fastapi import APIRouter, Depends
from core.licensing import require_license_dep

router = APIRouter(prefix="/verticals", tags=["verticals"], dependencies=[Depends(require_license_dep("pro"))])

@router.post("/hvac/offer")
def hvac_offer(customer: dict):
    name = customer.get("name","Klient")
    rooms = int(customer.get("rooms", 3))
    kw = float(customer.get("kw", 3.5))
    total = round(2999 + rooms*700 + kw*420, 2)
    return {
        "title": f"Oferta klimatyzacji dla {name}",
        "items": [
            {"name":"Jednostka split premium", "qty": rooms, "unit_price": 2199},
            {"name":"Montaż + materiały", "qty": rooms, "unit_price": 700},
            {"name":"Uruchomienie i testy", "qty": 1, "unit_price": 420},
        ],
        "total_estimate": total,
        "notes": "Ceny orientacyjne. Finalizacja po wizji lokalnej."
    }

@router.post("/content/post")
def content_post(topic: dict):
    brand = topic.get("brand","Mordzix")
    subject = topic.get("subject","AI automations")
    return {
        "h1": f"{brand}: {subject} – 3 szybkie pomysły",
        "bullets": [
            f"Automatyzuj powtarzalne procesy {brand} bez dotykania kodu.",
            f"Zaimplementuj analitykę i A/B testy w 24h.",
            f"Bezpieczny dostęp (RBAC/SSO) i logi audytowe."
        ]
    }
