from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request


BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def request(method: str, path: str, headers: dict[str, str] | None = None, body: dict | None = None):
    payload = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(BASE + path, data=payload, method=method, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def main() -> None:
    headers = {"X-Tenant-ID": "demo", "Idempotency-Key": "probe-catalog-v1"}
    print("health", request("GET", "/health"))
    print("catalog", request("POST", "/v1/jobs/catalog", headers))
    print("invalid review", request("PUT", "/v1/suggestions/not-a-uuid/review", {"X-Tenant-ID": "demo"}, {"decision": "approved"}))


if __name__ == "__main__":
    main()

