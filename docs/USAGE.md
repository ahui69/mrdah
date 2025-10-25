# API – Kontrakt odpowiedzi (UI-friendly)

Standardowy kształt odpowiedzi, które WebUI czyta "jak GPT":

```json
{
  "text": "Twoja odpowiedź w czystym tekście lub markdown (może zawierać ```code```)",
  "sources": [
    {"title": "Artykuł A", "url": "https://…"},
    {"title": "Repo B", "url": "https://…"}
  ]
}
```

- Pole `text` jest renderowane w dymku, z obsługą bloków kodu (przycisk **Kopiuj**).
- Tablica `sources` (opcjonalna) renderuje się jako linki pod odpowiedzią.
- Jeśli endpoint zwróci co innego (np. surowy JSON) – WebUI nadal pokaże wynik, ale bez sekcji Źródła.

Dla **SSE** (`text/event-stream`): każdy token (linia `data:`) może być:
- zwykłym tekstem,
- lub krótkim JSON-em z polem `text` **albo** `delta`.


### Przykład realny
```json
{
  "text": "…",
  "sources": [
    {"title": "Artykuł A", "url": "https://…"},
    {"title": "Repo B", "url": "https://…"}
  ]
}
```
