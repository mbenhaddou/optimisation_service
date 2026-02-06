from optimise.routing.core.functions import get_optimizer_strategy
from optimise.routing.defaults import FAST_FIRST_SOLUTIONS, FAST_METAHEURISTIC_SEARCH


def test_get_optimizer_strategy_deterministic_advances_history():
    strategy1, history = get_optimizer_strategy(
        "fast", history=None, deterministic=True
    )
    strategy2, history = get_optimizer_strategy(
        "fast", history=history, deterministic=True
    )

    assert strategy1["first_solution_strategy"] in FAST_FIRST_SOLUTIONS
    assert strategy1["local_search_metaheuristic"] in FAST_METAHEURISTIC_SEARCH

    # If there is more than one combo, deterministic strategy should advance.
    if len(FAST_FIRST_SOLUTIONS) * len(FAST_METAHEURISTIC_SEARCH) > 1:
        assert strategy1 != strategy2
