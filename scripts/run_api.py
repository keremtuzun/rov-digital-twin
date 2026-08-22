from __future__ import annotations

try:
    import uvicorn
except ImportError as exc:
    raise SystemExit("Install with: pip install -e '.[api]'") from exc


if __name__ == "__main__":
    uvicorn.run("oceansense.api:app", host="127.0.0.1", port=8000, reload=False)
