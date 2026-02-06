import json
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from solution_routing.solution_routing_CRUD import solution_routing_crud
from solution_routing.solution_routing_model import SolutionRouting
from solution_routing.solution_routing_schema import SolutionRoutingCreate, SolutionRoutingStatus
from optimise import api
from optimise.routing.constants import translate

import logging

logger = logging.getLogger("app")


class SolutionRoutingService:
    def create_routing_solution(self, db_session: Session, obj_in: SolutionRoutingCreate) -> SolutionRouting:
        return solution_routing_crud.create(db_session, obj_in)

    def get_one(self, db_session: Session, uuid: UUID, include_request: bool = False,include_parameters:bool =False,error_language:str='en' ) -> SolutionRouting:
        """
                        Get item by id.
                        """
        item = solution_routing_crud.get(db_session, uuid, include_request,include_parameters)
        if item is None:
            error_msg = translate("solution_routing_not_found",error_language).format(uuid)
            logger.error(error_msg)
            raise HTTPException(
                status_code=404,
                detail=error_msg,
            )

        return item

    def get_multi(self, db_session: Session, skip: int = 0, limit: int = 100, status: List[str] = None,
                  from_date: str = None,
                  to_date: str = None, include_request: bool = False,include_parameters:bool =False,error_language:str='en') -> List[SolutionRouting]:
        """
                        Get items.
                        """
        items = solution_routing_crud.get_multi(db_session, skip, limit, status, from_date, to_date, include_request,include_parameters)
        return items

    def delete(self, db_session: Session, uuid: UUID,error_language:str='en') -> SolutionRouting:
        """
                             Delete item.
                              """
        item = solution_routing_crud.get(db_session, uuid)

        if item is None:
            error_msg = translate("solution_routing_not_found",error_language).format(uuid)
            logger.error(error_msg)
            raise HTTPException(
                status_code=404,
                detail=error_msg,
            )
        if item.status not in ["FINISHED", "FAILED"]:
            error_msg =  translate("delete_solution_routing_not_allowed", error_language).format(uuid)
            logger.error(error_msg)
            raise HTTPException(
                status_code=404,
                detail=error_msg,
            )

        return solution_routing_crud.remove(db_session, uuid)

    def delete_multi(self, db_session: Session, status: List[str] = None,
                     from_date: str = None,
                     to_date: str = None) -> int:
        """
                        Delete items.
                        """
        count = solution_routing_crud.remove_multi(db_session, status, from_date, to_date)
        return count

    def start_optimization(self,  solution_routing: SolutionRouting):
        solution_routing.status = SolutionRoutingStatus.running.value
        json_request = json.loads(solution_routing.optimization_request)
        solution_routing.status_msg = translate("optimization_has_started", json_request.get("language"))
        solution_routing_crud.update(solution_routing)
        try:
            results = api.get_optimal_routes(solution_routing)
            solution_routing.optimization_response = json.dumps(results)
            solution_routing.status = SolutionRoutingStatus.finished.value
            solution_routing.status_msg =translate("optimization_has_finished", json_request.get("language"))
        except Exception as ex:
            solution_routing.status = SolutionRoutingStatus.failed.value
            solution_routing.status_msg = repr(ex)
        finally:
            solution_routing_crud.update(solution_routing)
            logger.info("Optimization has finished in Thread")



solution_routing_service = SolutionRoutingService()
