from flask.blueprints import Blueprint
from sqlalchemy.sql import text

from event_horizon.polaris.db import db_session as polaris_db_session
from event_horizon.vela.db import db_session as vela_db_session

healthz_bp = Blueprint("healthz", __name__)


@healthz_bp.route("/livez", methods=["GET"])
def livez() -> dict:
    return {}


@healthz_bp.route("/readyz", methods=["GET"])
def readyz() -> tuple[dict, int]:
    payload = {}
    status_code = 200
    db_errors = []

    try:
        polaris_db_session.execute(text("SELECT 1"))
    except Exception as ex:
        db_errors.append(f"failed to connect to polaris database due to error: {ex!r}")

    try:
        vela_db_session.execute(text("SELECT 1"))
    except Exception as ex:
        db_errors.append(f"failed to connect to vela database due to error: {ex!r}")

    if db_errors:
        payload = {"postgres": db_errors}
        status_code = 500

    # deepcode ignore ServerInformationExposure: this is an internal endpoint
    return payload, status_code
