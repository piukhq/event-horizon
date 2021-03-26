from typing import Any

from flask.blueprints import Blueprint
from sqlalchemy.sql import text

from app.polaris.db import SessionMaker as PolarisSessionMaker

healthz_bp = Blueprint("healthz", __name__)


@healthz_bp.route("/livez", methods=["GET"])
def livez() -> Any:
    return {}


@healthz_bp.route("/readyz", methods=["GET"])
def readyz() -> Any:
    payload = {}
    status_code = 200
    try:
        with PolarisSessionMaker() as session:
            session.execute(text("SELECT 1"))
    except Exception as e:
        payload = {"postgres": f"failed to connect to polaris database due to error: {repr(e)}"}
        status_code = 500

    return payload, status_code
