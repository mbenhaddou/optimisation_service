def preprocess_request(*args, **kwargs):
    from optimise.routing.preprocessing.preprocess_request import (
        preprocess_request as _preprocess_request,
    )

    return _preprocess_request(*args, **kwargs)


def handle_orders(*args, **kwargs):
    from optimise.routing.preprocessing.handle_workorders import handle_orders as _handle

    return _handle(*args, **kwargs)


def handle_teams_and_workers(*args, **kwargs):
    from optimise.routing.preprocessing.handle_teams_and_workers import (
        handle_teams_and_workers as _handle,
    )

    return _handle(*args, **kwargs)


__all__ = ["preprocess_request", "handle_orders", "handle_teams_and_workers"]
