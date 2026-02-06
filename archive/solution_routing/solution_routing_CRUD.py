from typing import Optional, List
from uuid import UUID

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_
from sqlalchemy.orm import Session, defer

from db.session import db_session
from solution_routing.solution_routing_model import SolutionRouting
from solution_routing.solution_routing_schema import SolutionRoutingCreate

import logging

logger = logging.getLogger("app")
class SolutionRoutingCRUD:

    def get(self, db_session: Session, uuid: UUID, include_request: bool = False,include_parameters:bool =False) -> Optional[SolutionRouting]:
        query = db_session.query(SolutionRouting)

        # Conditionally include the "optimization_request" column
        if not include_request:
            query = query.options(defer(SolutionRouting.optimization_request, raiseload=True))
        # Conditionally include the "parameters" column
        if not include_parameters:
            query = query.options(defer(SolutionRouting.parameters, raiseload=True))
        query = query.filter(SolutionRouting.uuid == uuid)

        return query.first()

    def get_multi(self, db_session: Session, skip: int = 0, limit: int = 100, status: List[str] = None,
                  from_date: str = None,
                  to_date: str = None, include_request: bool = False,include_parameters:bool =False) -> List[SolutionRouting]:
        query = db_session.query(SolutionRouting)
        if status:
            search_args = [getattr(SolutionRouting, "status") == v for v in status]
            query = query.filter(or_(*search_args))
        if from_date:
            query = query.filter(SolutionRouting.creation_date >= from_date)
        if to_date:
            query = query.filter(SolutionRouting.creation_date <= to_date)
        query = query.offset(skip)
        if limit > 0:
            query = query.limit(limit)
        # Conditionally include the "optimization_request" column
        if not include_request:
            query = query.options(defer(SolutionRouting.optimization_request, raiseload=True))
        # Conditionally include the "parameters" column
        if not include_parameters:
            query = query.options(defer(SolutionRouting.parameters, raiseload=True))
        try:
            return query.all()
        except Exception as e:
            logger.error(e)
            raise HTTPException(
                status_code=400, detail=f"Invalid query options, status: {status}, from_date: {from_date}, to_date: {to_date}, include_request: {include_request}"
            )

    def create(self, db_session: Session, obj_in: SolutionRoutingCreate) -> SolutionRouting:
        db_obj = SolutionRouting(**jsonable_encoder(obj_in))
        db_session.add(db_obj)
        db_session.commit()
        db_session.refresh(db_obj)
        return db_obj

    def update(
            self,  db_obj: SolutionRouting
    ) -> SolutionRouting:
        session = db_session()
        try:
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


    def remove(self, db_session: Session, id: UUID) -> SolutionRouting:
        obj = db_session.query(SolutionRouting).options(
            defer(SolutionRouting.optimization_request, raiseload=True)).get(id)
        db_session.delete(obj)
        db_session.commit()
        return obj

    def remove_multi(self, db_session: Session, status: List[str] = None,
                     from_date: str = None, to_date: str = None):
        query = db_session.query(SolutionRouting).options(defer(SolutionRouting.optimization_request, raiseload=True))
        if status:
            search_args = [getattr(SolutionRouting, "status") == v for v in status]
            query = query.filter(or_(*search_args))
        else:
            query = query.filter(SolutionRouting.status.in_(["FINISHED", "FAILED"]))
        if from_date:
            query = query.filter(SolutionRouting.creation_date >= from_date)
        if to_date:
            query = query.filter(SolutionRouting.creation_date <= to_date)

        try:
            count = query.delete(synchronize_session=False)
            db_session.commit()

            return count
        except Exception as e:
            db_session.rollback()
            logger.error(e)
            raise HTTPException(
                status_code=400,
                detail=f"Invalid query options, status: {status}, from_date: {from_date}, to_date: {to_date}"
            )


solution_routing_crud = SolutionRoutingCRUD()
