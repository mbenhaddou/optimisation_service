import json
import logging
import os
import random
import string
import threading
import time
from contextlib import asynccontextmanager
from threading import Thread
from typing import List, Optional
from uuid import UUID

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.logger import logger
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse

from config import defaults as config
from db.init_db import init_db
from db.migrate_db import migrate
from db.session import SessionLocal, db_session
from optimise import api
from solution_routing import solution_routing_service
from solution_routing.solution_routing_schema import SolutionRoutingCreate, SolutionRouting, SolutionRoutingStatus, \
    SolutionRoutingResponse
from solution_routing.solution_routing_service import solution_routing_service
from optimise.routing.constants import translate

# setup loggers
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
# get root logger
logger = logging.getLogger("app")
logger.debug('Starting SOA API')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_db(db_session)
    await migrate()
    yield


app = FastAPI(lifespan=lifespan, title="scheduling optimization",
              docs_url="/soa/docs", redoc_url="/soa/redoc", openapi_url="/soa/openapi.json")


def log_threads():
    while True:
        time.sleep(10)  # Sleep for 10 seconds
        current_threads = threading.enumerate()
        thread_info = [f"Thread Name: {thread.name}, Thread ID: {thread.ident}" for thread in current_threads]
        logger.info("-----------------------------------------------")
        logger.info("Current Threads:\n%s", "\n".join(thread_info))
        logger.info("-----------------------------------------------")


# Start the background thread
background_thread = Thread(target=log_threads, daemon=True)
background_thread.start()


@app.middleware('http')
async def db_session_middleware(request: Request, call_next):
    request.state.db = Session()
    response = await call_next(request)
    request.state.db.close()
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response


# THREADING
def _sync_run(*args, **kwargs):
    target = kwargs.pop("__target")
    try:
        target(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in {_sync_run.__name__}: {e}")


def run_in_thread(target, *args, **kwargs):
    kwargs["__target"] = target
    thread = Thread(target=_sync_run, args=args, kwargs=kwargs, daemon=True)
    thread.setName(f"{target.__name__} thread - {args[0].uuid}")
    thread.start()


## SCHEDULING

@app.post("/soa/scheduling", response_model=dict, include_in_schema=False, tags=["hidden"])
async def get_schedule(schedule_request: dict):
    try:
        result = api.get_schedule(schedule_request)
        return result
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400, detail=str(e)
        )


@app.post("/soa/scheduling/string", include_in_schema=False, tags=["hidden"])
async def get_schedule_str(schedule_request: dict):
    try:
        return api.get_schedule_str(schedule_request)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400, detail=str(e)
        )


@app.post("/soa/scheduling/download", include_in_schema=False, tags=["hidden"])
def get_optimal_routes_html(schedule_request: dict):
    try:
        api.get_schedule_str(schedule_request)
        return FileResponse("optimise/scheduling/solutions/solution.html", media_type="text/html")
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400, detail=str(e)
        )


## ROUTING

@app.post("/soa/routing", response_model=SolutionRoutingResponse)
def optimize_routes(routes_request: dict, db: Session = Depends(get_db)):
    """
      Start routing optimization. \n
      The method is asynchronous, \n
      returns an id that can be used to request the status and the result of the optimization.
      """

    try:

        s_routing_in = SolutionRoutingCreate(optimization_request=json.dumps(routes_request),parameters=json.dumps({'version':get_current_version()}))
        s_routing_out = solution_routing_service.create_routing_solution(db, s_routing_in)
        db.expunge_all()
        run_in_thread(solution_routing_service.start_optimization, s_routing_out)
        return SolutionRoutingResponse(solution_routing_id=s_routing_out.uuid)
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400, detail=str(e)
        )


@app.get("/soa/solution/routing/{solution_routing_id}", response_model=SolutionRouting)
def read_routing_solution_by_id(
        solution_routing_id: UUID,
        include_request: bool = Query(False, description=config.SOLUTION_ROUTING_INCLUDE_REQUEST_DESC),
        include_parameters: bool = Query(False, description=config.SOLUTION_ROUTING_INCLUDE_PARAMETERS_DESC),
        language: Optional[str] = Query("en", description="Language for the error messages"),
        db: Session = Depends(get_db),
):
    """
    Get a routing solution by id.
    """

    solution_routing = solution_routing_service.get_one(db, solution_routing_id, include_request,include_parameters,language)
    if include_request and include_parameters:
        return solution_routing
    elif include_request:
        return JSONResponse(jsonable_encoder(custom_encoder(solution_routing,include=['optimization_request']), exclude={'parameters'}))
    elif include_parameters:
        return JSONResponse(jsonable_encoder(custom_encoder(solution_routing,include=['parameters']), exclude={'optimization_request'}))
    else:
        return JSONResponse(jsonable_encoder(custom_encoder(solution_routing), exclude={'optimization_request', 'parameters'}))


@app.get("/soa/solution/routing", response_model=List[SolutionRouting])
def read_routing_solutions(
        skip: int = 0,
        limit: int = 100,
        status: List[str] = Query(None,
                                  description=config.SOLUTION_ROUTING_STATUS_DESC + "['CREATED','RUNNING','FINISHED','FAILED']"),
        from_date: Optional[str] = Query(None, description=config.SOLUTION_ROUTING_FROM_DATE_DESC),
        to_date: Optional[str] = Query(None, description=config.SOLUTION_ROUTING_TO_DATE_DESC),
        include_request: bool = Query(False, description=config.SOLUTION_ROUTING_INCLUDE_REQUEST_DESC),
        include_parameters: bool = Query(False, description=config.SOLUTION_ROUTING_INCLUDE_PARAMETERS_DESC),
        language: Optional[str] = Query("en", description="Language for the error messages"),
        db: Session = Depends(get_db),
):
    """
    Get multiple routing solution.
    """

    solutions = solution_routing_service.get_multi(db, skip, limit, status, from_date, to_date, include_request,include_parameters,language)
    if include_request and include_parameters:
        return solutions
    elif include_request:
        return JSONResponse(
            [jsonable_encoder(custom_encoder(item,include=['optimization_request']), exclude={'parameters'}) for item in solutions])
    elif include_parameters:
        return JSONResponse(
            [jsonable_encoder(custom_encoder(item,include=['parameters']), exclude={'optimization_request'}) for item in solutions])
    else:
        return JSONResponse(
            [jsonable_encoder(custom_encoder(item), exclude={'optimization_request', 'parameters'}) for item in
             solutions])

@app.delete("/soa/solution/routing/{solution_routing_id}", response_model=SolutionRouting)
def delete_routing_solution_by_id(
        solution_routing_id: UUID,
        language: Optional[str] = Query("en", description="Language for the error messages"),
        db: Session = Depends(get_db),
):
    """
    Delete a routing solution by id.
    """

    solution = solution_routing_service.delete(db, solution_routing_id,language)
    return JSONResponse(jsonable_encoder(custom_encoder(solution), exclude={'optimization_request','parameters'}))


@app.delete("/soa/solution/routing", response_model=str)
def delete_routing_solutions(
        status: List[str] = Query(None, description=config.SOLUTION_ROUTING_STATUS_DESC + "['FINISHED','FAILED']"),
        from_date: Optional[str] = Query(None, description=config.SOLUTION_ROUTING_FROM_DATE_DESC),
        to_date: Optional[str] = Query(None, description=config.SOLUTION_ROUTING_TO_DATE_DESC),
        language: Optional[str] = Query("en", description="Language for the error messages"),
        db: Session = Depends(get_db),
):
    """
    Delete multiple routing solutions. \n
    IMPORTANT! \n
    If no parameters are given,
    the request will delete all routing solutions with status FINISHED or FAILED.
    """
    if status:
        invalid_statuses = [s for s in status if s not in ["FINISHED", "FAILED"]]
        if invalid_statuses:
            error_msg = translate("invalid_status_for_delete_routing_solution",language).format( ", ".join(invalid_statuses))
            logger.error(error_msg)
            raise HTTPException(
                status_code=404,
                detail=error_msg,
            )

    int = solution_routing_service.delete_multi(db, status, from_date, to_date)

    return translate("successfully_deleted_routing_solutions",language).format(int)


@app.get("/soa/solution/routing/{solution_routing_id}/download")
async def download_routing_solution(
        solution_routing_id: UUID,
        language: Optional[str] = Query("en", description="Language for the error messages"),
        db: Session = Depends(get_db),
):
    """
    Download a routing optimization solution.
    """

    solution = solution_routing_service.get_one(db, solution_routing_id)
    if solution.status != SolutionRoutingStatus.finished.value:
        error_msg = translate("invalid_status_for_download_routing_solution",language).format(solution.status)
        logger.error(error_msg)
        raise HTTPException(
            status_code=404,
            detail=error_msg,
        )
    f = open(f"routing_solution_{solution_routing_id}.txt", "w")
    try:
        results = solution.optimization_response
        f.write('\n'.join(list(results["message"].values())))
        return FileResponse(f"routing_solution_{solution_routing_id}.txt", media_type="text/plain")
    except Exception as e:
        logger.error(e)
    finally:
        f.close()


@app.post("/soa/routing/string", response_model=str, include_in_schema=False, tags=["hidden"])
def get_optimal_routes_str(routes_request: dict):
    try:
        results = api.get_optimal_routes(routes_request)
        return '\n'.join(list(results["message"].values()))
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=400, detail=str(e)
        )


## VERSION

@app.get("/soa/version")
def get_version():
    return get_current_version()


@app.get('/soa/release-notes')
def get_release_notes(version: str = Query(None, description="Version to fetch change logs for")):
    all_versions = read_all_change_logs()
    if version:
        matching_versions = [v for v in all_versions.keys() if version in v]
        if matching_versions:
            return {matching_version: all_versions[matching_version] for matching_version in matching_versions}
        else:
            raise HTTPException(status_code=404, detail=f"Version {version} not found")

    return all_versions


# Read all change logs from the file
def read_all_change_logs():
    all_versions = {}
    with open("versions/changelog.txt", "r") as file:
        lines = file.readlines()
        current_version = None
        change_logs = []
        for line in lines:
            if line.startswith("Version "):
                if current_version:
                    all_versions[current_version] = change_logs
                current_version = line.strip()
                change_logs = []
            elif current_version:
                change_logs.append(line.strip())
    if current_version:
        all_versions[current_version] = change_logs
    return all_versions


def remove_file(path: str) -> None:
    os.unlink(path)


def custom_encoder(item, include=[]):
    if hasattr(item, 'optimization_response') and item.optimization_response is not None and item.optimization_response.strip() != '':
        item.optimization_response = json.loads(item.optimization_response)
    if 'optimization_request' in include  and hasattr(item, 'optimization_request') and item.optimization_request is not None and item.optimization_request.strip() != '':
        item.optimization_request = json.loads(item.optimization_request)
    if 'parameters' in include  and hasattr(item, 'parameters') and item.parameters is not None and item.parameters.strip() != '':
        item.parameters = json.loads(item.parameters)

    return item

def get_current_version():
    f = open("versions/version.txt", "r")
    try:
        version = f.read().strip()
        return version
    except Exception as e:
        logger.error(e)
    finally:
        f.close()


