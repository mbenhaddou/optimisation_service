from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    password: str
    organization: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OrganizationResponse(BaseModel):
    id: str
    name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    id: str
    email: str
    role: str
    org_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: List[UserProfileResponse]
    total: int


class UserRoleUpdate(BaseModel):
    role: str


class ApiKeyCreate(BaseModel):
    name: Optional[str] = None
    scopes: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class ApiKeyRotateRequest(BaseModel):
    name: Optional[str] = None
    scopes: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    id: str
    key: str
    name: Optional[str] = None
    scopes: Optional[List[str]] = None
    active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    last_used_ip: Optional[str] = None
    rotated_from_id: Optional[str] = None
    revoked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    org_id: Optional[str] = None
    created_by_user_id: Optional[str] = None

    class Config:
        from_attributes = True


class ApiKeyListResponse(BaseModel):
    items: List[ApiKeyResponse]
    total: int


class WebhookCreate(BaseModel):
    name: str
    url: str
    events: List[str] = Field(default_factory=list)
    secret: Optional[str] = None
    active: Optional[bool] = True


class WebhookResponse(BaseModel):
    id: str
    name: str
    url: str
    events: List[str]
    active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    items: List[WebhookResponse]
    total: int


class AuditLogResponse(BaseModel):
    id: str
    org_id: Optional[str] = None
    actor_user_id: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int


class AnalyticsTrendPoint(BaseModel):
    date: str
    value: float


class AnalyticsRecommendation(BaseModel):
    type: str
    message: str


class AnalyticsRoutesResponse(BaseModel):
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    infeasible_rate: float
    average_nodes: Optional[float] = None
    average_usage_units: Optional[float] = None
    demand_forecast_next_7d: Optional[float] = None
    capacity_recommendation: Optional[str] = None
    trends: Optional[List[AnalyticsTrendPoint]] = None
    recommendations: Optional[List[AnalyticsRecommendation]] = None


class BillingSummaryResponse(BaseModel):
    plan_name: str
    status: str
    used_units: int
    free_tier_units: int
    overage_units: int


class BillingCheckoutResponse(BaseModel):
    url: str


class BillingPortalResponse(BaseModel):
    url: str


class ReportScheduleCreate(BaseModel):
    name: str
    schedule: str
    format: str = "csv"
    active: bool = True


class ReportScheduleResponse(BaseModel):
    id: str
    name: str
    schedule: str
    format: str
    active: bool
    created_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportScheduleListResponse(BaseModel):
    items: List[ReportScheduleResponse]
    total: int


class JobResponse(BaseModel):
    id: str
    status: str
    node_count: Optional[int] = None
    usage_units: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    items: List[JobResponse]
    total: int


class Location(BaseModel):
    lat: float
    lng: float
    address: Optional[str] = None


class TimeWindow(BaseModel):
    start: datetime
    end: datetime


class BreakWindow(BaseModel):
    earliest: datetime
    latest: datetime


class Break(BaseModel):
    duration_minutes: int
    time_window: BreakWindow


class VehicleCapacity(BaseModel):
    weight: Optional[float] = None
    volume: Optional[float] = None
    units: Optional[float] = None


class Vehicle(BaseModel):
    id: str
    start_location: Location
    end_location: Optional[Location] = None
    capacity: Optional[VehicleCapacity] = None
    available_time_windows: List[TimeWindow] = Field(default_factory=list)
    breaks: List[Break] = Field(default_factory=list)
    max_tasks: Optional[int] = None
    skills: Optional[List[str]] = None
    depot_id: Optional[str] = None
    team_id: Optional[str] = None
    range_km: Optional[float] = None


class TaskDemand(BaseModel):
    weight: Optional[float] = None
    volume: Optional[float] = None
    units: Optional[float] = None


class Task(BaseModel):
    id: str
    type: Optional[str] = "delivery"
    location: Location
    service_duration_minutes: int
    time_windows: List[TimeWindow] = Field(default_factory=list)
    preferred_time_windows: List[TimeWindow] = Field(default_factory=list)
    soft_time_window_penalty: Optional[float] = None
    demand: Optional[TaskDemand] = None
    priority: Optional[int] = None
    required_skills: Optional[List[str]] = None


class ObjectivesWeights(BaseModel):
    duration: Optional[float] = None
    distance: Optional[float] = None
    cost: Optional[float] = None
    vehicle_balance: Optional[float] = None


class Objectives(BaseModel):
    primary: str
    secondary: Optional[str] = None
    weights: Optional[ObjectivesWeights] = None
    minimize_vehicles: Optional[bool] = None


class OptimizeConstraints(BaseModel):
    max_route_duration_minutes: Optional[int] = None
    max_route_distance_km: Optional[float] = None
    balance_routes: Optional[bool] = None
    allow_overtime: Optional[bool] = None
    required_task_assignments: Optional[List[str]] = None
    task_dependencies: Optional[List[Dict[str, Any]]] = None
    zone_restrictions: Optional[List[Dict[str, Any]]] = None


class TrafficOptions(BaseModel):
    mode: Optional[str] = None
    departure_time: Optional[datetime] = None
    include_historical_patterns: Optional[bool] = None


class OptimizationSettings(BaseModel):
    max_computation_time_seconds: Optional[int] = None
    solution_quality: Optional[str] = None
    return_alternative_solutions: Optional[int] = None
    enable_ml_predictions: Optional[bool] = None


class OptimizeOptions(BaseModel):
    return_detailed_metrics: Optional[bool] = True
    include_route_geometry: Optional[bool] = False
    calculate_carbon_footprint: Optional[bool] = False
    eco_routing: Optional[bool] = False


class RoutingOptions(BaseModel):
    distance_matrix_method: Optional[str] = None
    routing_engine_url: Optional[str] = None


class PrecomputedMatrix(BaseModel):
    distances_m: List[List[float]]
    durations_s: List[List[float]]


class Depot(BaseModel):
    id: str
    location: Location
    time_windows: List[TimeWindow] = Field(default_factory=list)
    name: Optional[str] = None


class OptimizeRequest(BaseModel):
    problem_type: str
    objectives: Objectives
    vehicles: List[Vehicle]
    tasks: List[Task]
    depots: List[Depot] = Field(default_factory=list)
    matrix: Optional[PrecomputedMatrix] = None
    constraints: Optional[OptimizeConstraints] = None
    traffic: Optional[TrafficOptions] = None
    optimization: Optional[OptimizationSettings] = None
    options: Optional[OptimizeOptions] = None
    routing: Optional[RoutingOptions] = None


class StopLocation(BaseModel):
    lat: float
    lng: float


class RouteStop(BaseModel):
    sequence: int
    type: str
    task_id: Optional[str] = None
    location: StopLocation
    arrival_time: Optional[datetime] = None
    departure_time: Optional[datetime] = None
    service_duration_minutes: Optional[int] = None
    waiting_time_minutes: Optional[int] = None
    distance_from_previous_km: Optional[float] = None
    duration_from_previous_minutes: Optional[float] = None


class RouteResponse(BaseModel):
    vehicle_id: str
    total_distance_km: float
    total_duration_minutes: float
    total_service_time_minutes: Optional[float] = None
    total_cost: Optional[float] = None
    stops: List[RouteStop]
    route_geometry: Optional[List[StopLocation]] = None


class UnassignedTaskResponse(BaseModel):
    task_id: str
    reason: Optional[str] = None
    details: Optional[str] = None


class OptimizeMetrics(BaseModel):
    total_distance_km: Optional[float] = None
    total_duration_minutes: Optional[float] = None
    total_service_time_minutes: Optional[float] = None
    total_cost: Optional[float] = None
    average_vehicle_utilization: Optional[float] = None
    tasks_assigned: Optional[int] = None
    tasks_unassigned: Optional[int] = None
    carbon_kg: Optional[float] = None


class WarningMessage(BaseModel):
    type: str
    task_ids: Optional[List[str]] = None
    message: str


class AlternativeSolution(BaseModel):
    quality_score: Optional[float] = None
    routes: List[RouteResponse]
    metrics: Optional[OptimizeMetrics] = None


class OptimizeResponse(BaseModel):
    status: str
    computation_time_ms: int
    solution_quality_score: Optional[float] = None
    routes: List[RouteResponse]
    unassigned_tasks: List[UnassignedTaskResponse]
    metrics: Optional[OptimizeMetrics] = None
    warnings: Optional[List[WarningMessage]] = None
    alternative_solutions: Optional[List[AlternativeSolution]] = None


class MatrixRequest(BaseModel):
    locations: List[Location]
    distance_matrix_method: Optional[str] = None
    routing_engine_url: Optional[str] = None
    driving_speed_kmh: Optional[float] = None


class MatrixResponse(BaseModel):
    distances_m: List[List[float]]
    durations_s: List[List[float]]


class ReoptimizeChanges(BaseModel):
    added_tasks: Optional[List[Task]] = None
    removed_task_ids: Optional[List[str]] = None
    updated_tasks: Optional[List[Task]] = None
    added_vehicles: Optional[List[Vehicle]] = None
    removed_vehicle_ids: Optional[List[str]] = None
    updated_vehicles: Optional[List[Vehicle]] = None
    constraints: Optional[OptimizeConstraints] = None
    optimization: Optional[OptimizationSettings] = None
    options: Optional[OptimizeOptions] = None
    routing: Optional[RoutingOptions] = None
    minimize_changes: Optional[bool] = None


class ReoptimizeRequest(BaseModel):
    base_request: OptimizeRequest
    solution_id: Optional[str] = None
    changes: Optional[ReoptimizeChanges] = None
