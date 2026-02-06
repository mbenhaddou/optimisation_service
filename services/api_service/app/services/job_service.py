from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Job, UsageRecord


class JobService:
    @staticmethod
    def create_job(
        db: Session,
        payload: Dict[str, Any],
        node_count: Optional[int] = None,
        usage_units: Optional[int] = None,
        api_key_id: Optional[str] = None,
    ) -> Job:
        job = Job(
            status="PENDING",
            request=payload,
            node_count=node_count,
            usage_units=usage_units,
            api_key_id=api_key_id,
        )
        db.add(job)
        db.flush()
        usage_record = UsageRecord(
            api_key_id=api_key_id,
            job_id=job.id,
            node_count=node_count,
            usage_units=usage_units,
        )
        db.add(usage_record)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def list_jobs(
        db: Session,
        limit: int = 20,
        offset: int = 0,
        api_key_id: Optional[str] = None,
    ) -> Tuple[List[Job], int]:
        stmt = select(Job).order_by(Job.created_at.desc())
        if api_key_id is None:
            stmt = stmt.where(Job.api_key_id.is_(None))
        else:
            stmt = stmt.where(Job.api_key_id == api_key_id)
        stmt = stmt.limit(limit).offset(offset)
        items = list(db.execute(stmt).scalars().all())
        total_stmt = select(func.count()).select_from(Job)
        if api_key_id is None:
            total_stmt = total_stmt.where(Job.api_key_id.is_(None))
        else:
            total_stmt = total_stmt.where(Job.api_key_id == api_key_id)
        total = db.execute(total_stmt).scalar_one()
        return items, total

    @staticmethod
    def get_job(db: Session, job_id: str, api_key_id: Optional[str] = None) -> Optional[Job]:
        stmt = select(Job).where(Job.id == job_id)
        if api_key_id is None:
            stmt = stmt.where(Job.api_key_id.is_(None))
        else:
            stmt = stmt.where(Job.api_key_id == api_key_id)
        return db.execute(stmt).scalar_one_or_none()
