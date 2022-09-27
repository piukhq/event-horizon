from typing import Any

from flask.blueprints import Blueprint
from sqlalchemy.sql import text

from event_horizon.polaris.db import db_session as polaris_db_session
from event_horizon.vela.db import db_session as vela_db_session

healthz_bp = Blueprint("healthz", __name__)


@healthz_bp.route("/livez", methods=["GET"])
def livez() -> Any:
    return {}


@healthz_bp.route("/readyz", methods=["GET"])
def readyz() -> Any:
    payload = {}
    status_code = 200
    db_errors = []

    try:
        polaris_db_session.execute(text("SELECT 1"))
    except Exception as e:
        db_errors.append(f"failed to connect to polaris database due to error: {repr(e)}")

    try:
        vela_db_session.execute(text("SELECT 1"))
    except Exception as e:
        db_errors.append(f"failed to connect to vela database due to error: {repr(e)}")

    if db_errors:
        payload = {"postgres": db_errors}
        status_code = 500

    return payload, status_code
