from __future__ import annotations

import sys
import time
from os import getenv

import httpx


def main() -> None:
    base_url = getenv("DRIFT_SMOKE_BASE_URL", "http://127.0.0.1:8080")
    deadline = time.time() + 20
    last_error = ""

    while time.time() < deadline:
        try:
            response = httpx.get(f"{base_url}/health/live", timeout=2.0)
            if response.status_code == 200:
                dashboard = httpx.get(base_url, timeout=2.0)
                dashboard.raise_for_status()
                if "System Drift Engine" not in dashboard.text:
                    raise RuntimeError("dashboard title missing")
                return
        except Exception as error:
            last_error = str(error)
            time.sleep(1)

    print(f"API smoke check failed: {last_error}", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
