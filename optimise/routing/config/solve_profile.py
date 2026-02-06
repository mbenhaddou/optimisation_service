from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SolveProfile:
    """
    Encapsulates OR-Tools search parameters and solver configuration.
    """

    first_solution_strategy: Optional[str] = None
    local_search_metaheuristic: Optional[str] = None
    time_limit_seconds: Optional[int] = None
    log_search: bool = False
    search_workers: Optional[int] = None
    solution_limit: Optional[int] = None

    @staticmethod
    def from_solver_input(input_obj) -> "SolveProfile":
        return SolveProfile(
            first_solution_strategy=input_obj.first_solution_strategy,
            local_search_metaheuristic=input_obj.local_search_metaheuristic,
            time_limit_seconds=input_obj.time_limit_seconds,
        )
