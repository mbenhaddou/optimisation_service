import builtins
import importlib
import os

import optimise.routing.distance_matrix as distance_matrix


def test_distance_matrix_fallback_uses_env(monkeypatch):
    monkeypatch.setenv("ROUTING_ENGINE", "http://example.com:5000")
    monkeypatch.setenv("ORS_API_KEYS", "")
    monkeypatch.setenv("MAPBOX_OSRM_API_KEYS", "")
    monkeypatch.setenv("GRAPHHOPPER_API_KEYS", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.startswith("config"):
            raise ModuleNotFoundError("Forced config import failure for test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    importlib.reload(distance_matrix)

    assert distance_matrix.ROUTING_ENGINE == os.getenv(
        "ROUTING_ENGINE", "http://localhost:5000"
    )
