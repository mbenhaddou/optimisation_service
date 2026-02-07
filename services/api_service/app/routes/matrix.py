from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import get_api_key, get_db
from ..schemas import MatrixRequest, MatrixResponse
from ..services.matrix_service import build_matrix
from ..services.rate_limit import enforce_rate_limit


router = APIRouter(prefix="/v1", tags=["matrix"])


@router.post("/matrix", response_model=MatrixResponse)
async def matrix(
    request: Request,
    payload: MatrixRequest = Body(...),
    db: Session = Depends(get_db),
):
    api_key_id = get_api_key(request, db, required_scopes={"solve:write"})
    identifier = api_key_id or f"anon:{request.client.host if request.client else 'unknown'}"
    enforce_rate_limit(identifier)

    if len(payload.locations) < 2:
        raise HTTPException(status_code=400, detail="locations must contain at least 2 entries")

    method = payload.distance_matrix_method or "haversine"
    routing_engine_url = payload.routing_engine_url or settings.mapping_service_url
    if routing_engine_url:
        method = "osrm" if method == "haversine" else method

    coords_latlon = [[loc.lat, loc.lng] for loc in payload.locations]
    result = build_matrix(
        coords_latlon,
        method=method,
        driving_speed_kmh=payload.driving_speed_kmh,
        routing_engine_url=routing_engine_url,
    )

    return MatrixResponse(
        distances_m=result["distances"],
        durations_s=result["durations"],
    )
