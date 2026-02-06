import json
from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import Optional, Any

from pydantic import BaseModel, validator


class SolutionRoutingStatus(str, Enum):
    created = 'CREATED'
    running = 'RUNNING'
    finished = 'FINISHED'
    failed = 'FAILED'


class SolutionRoutingBase(BaseModel):
    status: str = SolutionRoutingStatus.created.value
    status_msg: Optional[str]=""
    optimization_response: Optional[str]=""


class SolutionRoutingInDBBase(SolutionRoutingBase):
    uuid: UUID
    creation_date: Optional[datetime]
    update_date: Optional[datetime]

    class Config:
        orm_mode = True


class SolutionRoutingInDB(SolutionRoutingInDBBase):
    optimization_request: str
    parameters: str


class SolutionRoutingCreate(SolutionRoutingBase):
    optimization_request: str
    parameters: str


class SolutionRouting(SolutionRoutingInDBBase):
    optimization_request: Optional[dict] = None
    optimization_response: Optional[dict]=None
    parameters: Optional[dict]=None
    status_msg: Optional[str]=""

    @validator("optimization_response", "optimization_request", "parameters", pre=True)
    def str_to_dictionary(cls, v) -> Optional[dict]:
        if isinstance(v, str):
            if v.strip() == '':
                return None
            else:
                return json.loads(v)

class SolutionRoutingResponse(BaseModel):
    solution_routing_id: UUID
