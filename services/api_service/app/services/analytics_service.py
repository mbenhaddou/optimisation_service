from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Job
from ..schemas import AnalyticsRecommendation, AnalyticsRoutesResponse, AnalyticsTrendPoint


def build_routes_analytics(db: Session, org_id: Optional[str]) -> AnalyticsRoutesResponse:
    base_query = db.query(Job).filter(Job.org_id == org_id)
    total_jobs = base_query.count()
    completed_jobs = base_query.filter(Job.status == "COMPLETED").count()
    failed_jobs = base_query.filter(Job.status == "FAILED").count()

    avg_nodes = db.query(func.avg(Job.node_count)).filter(Job.org_id == org_id).scalar()
    avg_units = db.query(func.avg(Job.usage_units)).filter(Job.org_id == org_id).scalar()

    last_30_days = datetime.utcnow() - timedelta(days=30)
    rows = (
        db.query(func.date(Job.created_at), func.count(Job.id))
        .filter(Job.org_id == org_id, Job.created_at >= last_30_days)
        .group_by(func.date(Job.created_at))
        .order_by(func.date(Job.created_at))
        .all()
    )
    trends: List[AnalyticsTrendPoint] = [
        AnalyticsTrendPoint(date=str(row[0]), value=float(row[1])) for row in rows
    ]

    infeasible_rate = 0.0
    if completed_jobs:
        infeasible_jobs = 0
        for job in base_query.filter(Job.status == "COMPLETED").all():
            result = job.result or {}
            solutions = result.get("solutions", [])
            dropped = 0
            for solution in solutions:
                dropped += len(solution.get("dropped", []))
            if dropped > 0:
                infeasible_jobs += 1
        infeasible_rate = round(infeasible_jobs / max(1, completed_jobs), 3)

    demand_forecast = None
    capacity_recommendation = None
    if trends:
        avg_daily = sum(point.value for point in trends) / max(1, len(trends))
        demand_forecast = round(avg_daily * 7, 2)
        capacity_recommendation = (
            "Increase fleet capacity next week"
            if demand_forecast > avg_daily * 7 * 1.1
            else "Current fleet capacity is sufficient"
        )

    recommendations = []
    if infeasible_rate > 0.2:
        recommendations.append(
            AnalyticsRecommendation(
                type="infeasible_rate_high",
                message="High infeasible rate detected. Review constraints or increase fleet capacity.",
            )
        )

    return AnalyticsRoutesResponse(
        total_jobs=total_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        infeasible_rate=infeasible_rate,
        average_nodes=float(avg_nodes) if avg_nodes else None,
        average_usage_units=float(avg_units) if avg_units else None,
        demand_forecast_next_7d=demand_forecast,
        capacity_recommendation=capacity_recommendation,
        trends=trends or None,
        recommendations=recommendations or None,
    )
