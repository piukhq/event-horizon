from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest
import wtforms

from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from event_horizon.admin.model_views import AuthorisedModelView
from event_horizon.app import create_app
from event_horizon.polaris.db.session import db_session as SyncSessionMaker


@pytest.fixture()
def mock_form() -> mock.MagicMock:
    return mock.MagicMock(spec=wtforms.Form)


@pytest.fixture()
def mock_field() -> mock.MagicMock:
    return mock.MagicMock(spec=wtforms.Field)


@pytest.fixture(scope="session")
def app() -> Flask:
    app = create_app()
    # deepcode ignore DisablesCSRFProtection/test: this is a test as suggested by it being a pytest fixture
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["ENV"] = "development"
    return app


@pytest.fixture(scope="function")
def test_client(app: Flask) -> Generator["FlaskClient", None, None]:
    with (
        app.app_context(),
        app.test_request_context(),
        mock.patch.object(
            AuthorisedModelView,
            "user_info",
            {
                "name": "Test User",
                "roles": {"Admin"},
                "exp": (datetime.now(tz=timezone.utc) + timedelta(days=1)).timestamp(),
            },
        ),
    ):
        yield app.test_client()


@pytest.fixture(scope="session")
def main_db_session() -> Generator["Session", None, None]:
    with SyncSessionMaker() as session:
        yield session


@pytest.fixture(scope="function")
def db_session(main_db_session: "Session") -> Generator["Session", None, None]:
    yield main_db_session
    main_db_session.rollback()
    main_db_session.expunge_all()
