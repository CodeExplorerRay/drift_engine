from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from drift_engine.api.dependencies import request_engine as get_engine
from drift_engine.api.security import Scopes, require_scope
from drift_engine.core.engine import DriftEngine

router = APIRouter(prefix="/audit", tags=["audit"])
ENGINE_DEP = Depends(get_engine)
AUDIT_READ = Depends(require_scope(Scopes.AUDIT_READ))


@router.get("", dependencies=[AUDIT_READ])
async def list_audit_events(
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    engine: DriftEngine = ENGINE_DEP,
) -> list[dict[str, object]]:
    if engine.audit_repository is None:
        raise HTTPException(status_code=501, detail="audit repository is not configured")
    events = await engine.audit_repository.list(limit=limit, offset=offset)
    return [event.to_document() for event in events]
