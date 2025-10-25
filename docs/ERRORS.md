# Standard błędów API

Zawsze zwracamy JSON w formacie:

```json
{
  "error": "http_error|validation_error|internal_error|rate_limit|...",
  "code": 400,
  "detail": "... lub obiekt/array ...",
  "request_id": "UUID lub n/a"
}
```

- `error` – stały kod błędu do obsługi w kliencie.
- `code` – HTTP status.
- `detail` – komunikat lub lista błędów (np. z walidacji).
- `request_id` – wartość `X-Request-ID` (ułatwia śledzenie w logach).

Typowe kody:
- 401/403 – auth required/forbidden
- 404 – not found
- 422 – validation_error (Pydantic)
- 429 – rate_limit (middleware)
- 500 – internal_error
