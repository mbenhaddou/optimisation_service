from optimise.routing.solver.ortools_builder import OrtoolsSolver
from optimise.routing.solver.registry import registry

registry.register("ortools", OrtoolsSolver)

__all__ = ["OrtoolsSolver", "registry"]
