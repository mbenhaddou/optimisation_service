from db.base_class import Base
from db.session import engine
from solution_routing.solution_routing_CRUD import solution_routing_crud
from solution_routing.solution_routing_schema import SolutionRoutingStatus

import logging

logger = logging.getLogger("app")


async def init_db(db_session):
    Base.metadata.create_all(bind=engine)
    # Update async actions that were interrupted and set status to fail
    try:
        routing_solutions = solution_routing_crud.get_multi(db_session, status=["RUNNING", "CREATED"], limit=-1)
        for s in routing_solutions:
            try:
                s.status = SolutionRoutingStatus.failed.value
                s.status_msg = "The API has been shut down before completing the optimization"
                solution_routing_crud.update(s)
            except Exception as err:
                logger.error(err)
    except Exception as err:
        logger.error(err)
    finally:
        db_session.close()

