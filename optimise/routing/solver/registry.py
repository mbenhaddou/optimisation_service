from typing import Dict, Type


class SolverRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, Type] = {}

    def register(self, name: str, solver_cls: Type) -> None:
        self._registry[name] = solver_cls

    def get(self, name: str) -> Type:
        if name not in self._registry:
            raise KeyError(f"Solver '{name}' is not registered")
        return self._registry[name]

    def list(self) -> Dict[str, Type]:
        return dict(self._registry)


registry = SolverRegistry()
