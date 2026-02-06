from optimise.routing.solver import OrtoolsSolver, registry


def test_solver_registry_has_ortools():
    solver_cls = registry.get("ortools")
    assert solver_cls is OrtoolsSolver
