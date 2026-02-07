from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..db import get_session
from ..deps import get_current_user
from ..models import Job
from ..routes.optimize import _build_routes

router = APIRouter(prefix="/v1/exports", tags=["exports"])


def get_db() -> Session:
    yield from get_session()


def _job_routes(job: Job) -> List[Dict[str, Any]]:
    result = job.result or {}
    solutions = result.get("solutions", [])
    request_payload = job.request or {}
    orders = request_payload.get("orders", [])
    durations = {str(order.get("id")): int(order.get("work_hours", 0)) for order in orders}
    routes, _, _ = _build_routes(solutions, durations)
    return [route.model_dump() for route in routes]


@router.get("/jobs/{job_id}")
def export_job(
    request: Request,
    job_id: str,
    format: str = Query("json", pattern="^(json|csv|geojson)$"),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    job = (
        db.query(Job)
        .filter(Job.id == job_id, Job.org_id == user.org_id)
        .one_or_none()
    )
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "COMPLETED":
        raise HTTPException(status_code=409, detail="Job is not completed")

    routes = _job_routes(job)

    if format == "json":
        return {"job_id": job_id, "routes": routes}

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "vehicle_id",
                "sequence",
                "type",
                "task_id",
                "lat",
                "lng",
                "arrival_time",
                "departure_time",
                "distance_from_previous_km",
                "duration_from_previous_minutes",
            ]
        )
        for route in routes:
            for stop in route.get("stops", []):
                writer.writerow(
                    [
                        route.get("vehicle_id"),
                        stop.get("sequence"),
                        stop.get("type"),
                        stop.get("task_id"),
                        stop.get("location", {}).get("lat"),
                        stop.get("location", {}).get("lng"),
                        stop.get("arrival_time"),
                        stop.get("departure_time"),
                        stop.get("distance_from_previous_km"),
                        stop.get("duration_from_previous_minutes"),
                    ]
                )
        return {"content_type": "text/csv", "data": output.getvalue()}

    # geojson
    features = []
    for route in routes:
        coords = [
            [stop.get("location", {}).get("lng"), stop.get("location", {}).get("lat")]
            for stop in route.get("stops", [])
            if stop.get("location")
        ]
        features.append(
            {
                "type": "Feature",
                "properties": {"vehicle_id": route.get("vehicle_id")},
                "geometry": {"type": "LineString", "coordinates": coords},
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
    }
