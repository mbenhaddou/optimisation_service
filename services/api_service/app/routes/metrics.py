from fastapi import APIRouter

from ..observability import metrics

router = APIRouter()


@router.get("/metrics")
def get_metrics():
    return metrics.snapshot()
