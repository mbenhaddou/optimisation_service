import importlib
from pathlib import Path

import pytest


def _reload_api_modules():
    from services.api_service.app import config, db, models, main

    importlib.reload(config)
    importlib.reload(db)
    importlib.reload(models)
    importlib.reload(main)
    return main


@pytest.fixture()
def app(monkeypatch, tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "api_service.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("ALLOW_ANON", "true")
    monkeypatch.setenv("AUTO_CREATE_DB", "true")
    monkeypatch.setenv("SYNC_EXECUTION", "true")
    monkeypatch.setenv("ENABLE_RATE_LIMITING", "false")
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin")
    monkeypatch.setenv("ADMIN_KEY_HEADER", "X-Admin-Key")
    monkeypatch.setenv("API_KEY_HEADER", "X-API-Key")

    main = _reload_api_modules()
    return main.create_app()


@pytest.fixture()
def client(app):
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    from services.api_service.app.db import Base, engine
    from services.api_service.app import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
