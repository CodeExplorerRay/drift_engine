# ruff: noqa: E501

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response

router = APIRouter(tags=["ui"])

DASHBOARD_DIR = Path(__file__).resolve().parents[1] / "static" / "dashboard"
DASHBOARD_INDEX = DASHBOARD_DIR / "index.html"
ASSET_REFERENCE_PATTERN = re.compile(r'/assets/([^"\']+)')
HASHED_ASSET_PATTERN = re.compile(
    r"^(?P<base>.+)-[A-Za-z0-9_-]{6,}\.(?P<ext>css|js)(?P<map>\.map)?$"
)

FAVICON_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#0f172a"/>
  <path d="M16 39 L27 28 L36 35 L49 21" fill="none" stroke="#38bdf8"
        stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M16 46 H50" fill="none" stroke="#64748b" stroke-width="4"
        stroke-linecap="round"/>
  <circle cx="16" cy="39" r="4" fill="#22c55e"/>
  <circle cx="27" cy="28" r="4" fill="#f59e0b"/>
  <circle cx="36" cy="35" r="4" fill="#38bdf8"/>
  <circle cx="49" cy="21" r="4" fill="#ef4444"/>
</svg>
"""

FALLBACK_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>System Drift Engine</title>
  <link rel="icon" href="/favicon.ico" type="image/svg+xml" />
  <style>
    body {
      margin: 0;
      min-height: 100vh;
      background: #f8fafc;
      color: #0f172a;
      font-family: Aptos, "Segoe UI Variable Text", "Segoe UI", sans-serif;
    }
    main {
      display: grid;
      min-height: 100vh;
      place-items: center;
      padding: 24px;
    }
    section {
      max-width: 760px;
      border: 1px solid #dbe3ef;
      border-radius: 24px;
      background: #ffffff;
      box-shadow: 0 18px 48px rgba(15, 23, 42, 0.06);
      padding: 32px;
    }
    p {
      color: #64748b;
      line-height: 1.7;
    }
    code {
      border-radius: 8px;
      background: #f1f5f9;
      padding: 2px 6px;
    }
  </style>
</head>
<body>
  <main>
    <section>
      <p>Operator Console</p>
      <h1>System Drift Engine</h1>
      <p>
        The React dashboard build was not found. Run <code>npm install</code> and
        <code>npm run build</code> in <code>frontend/</code>, or rebuild the Docker image.
      </p>
      <p>
        Available modules: Findings, Report history, Remediation queue, Baselines,
        Create job, Integrations, Audit trail, Approve action, Execute approved.
      </p>
    </section>
  </main>
</body>
</html>
"""


def _candidate_asset_path(asset_path: str) -> Path | None:
    assets_dir = (DASHBOARD_DIR / "assets").resolve()
    requested_asset = (assets_dir / asset_path).resolve()
    try:
        requested_asset.relative_to(assets_dir)
    except ValueError:
        return None
    if requested_asset.is_file():
        return requested_asset

    filename = Path(asset_path).name
    match = HASHED_ASSET_PATTERN.match(filename)
    if match is None:
        return None

    suffix = f".{match.group('ext')}{match.group('map') or ''}"
    pattern = f"{match.group('base')}-*{suffix}"
    candidates = sorted(
        path
        for path in assets_dir.glob(pattern)
        if path.is_file() and path.name.endswith(suffix)
    )
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate.stat().st_mtime_ns)


def _dashboard_build_is_usable() -> bool:
    if not DASHBOARD_INDEX.exists():
        return False
    dashboard_html = DASHBOARD_INDEX.read_text(encoding="utf-8")
    asset_matches = ASSET_REFERENCE_PATTERN.findall(dashboard_html)
    if not asset_matches:
        return False
    return all(_candidate_asset_path(asset_path) is not None for asset_path in asset_matches)


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    if _dashboard_build_is_usable():
        return HTMLResponse(DASHBOARD_INDEX.read_text(encoding="utf-8"))
    return HTMLResponse(FALLBACK_HTML)


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(FAVICON_SVG, media_type="image/svg+xml")


@router.get("/assets/{asset_path:path}", include_in_schema=False)
async def dashboard_asset(asset_path: str) -> FileResponse:
    requested_asset = _candidate_asset_path(asset_path)
    if requested_asset is None:
        raise HTTPException(status_code=404, detail="asset not found")
    return FileResponse(requested_asset)
