from typing import Any, Optional

import sentry_sdk

from authlib.integrations.flask_client import OAuth
from flask import Flask, Response
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.admin import event_horizon_admin
from app.polaris.db import db_session as polaris_db_session
from app.polaris.db.models import Base as PolarisModelBase
from app.polaris.db.session import engine as polaris_engine
from app.settings import OAUTH_SERVER_METADATA_URL, SENTRY_DSN, SENTRY_ENV
from app.vela.db import db_session as vela_db_session
from app.vela.db.models import Base as VelaModelBase
from app.vela.db.session import engine as vela_engine
from app.version import __version__

oauth = OAuth()
oauth.register(
    "event_horizon",
    server_metadata_url=OAUTH_SERVER_METADATA_URL,
    client_kwargs={"scope": "openid profile email"},
)


class RelativeLocationHeaderResponse(Response):
    # Below setting allows relative location headers, allowing us to redirect
    # without having to hardcode the Azure Front Door host to all redirects
    autocorrect_location_header = False


def create_app(config_name: str = "app.settings") -> Flask:
    PolarisModelBase.prepare(polaris_engine, reflect=True)
    VelaModelBase.prepare(vela_engine, reflect=True)

    from app import events  # noqa: F401 initialise events
    from app.polaris import register_polaris_admin
    from app.vela import register_vela_admin
    from app.views.auth import auth_bp
    from app.views.healthz import healthz_bp

    if SENTRY_DSN is not None:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FlaskIntegration(), SqlalchemyIntegration()],
            environment=SENTRY_ENV,
            release=__version__,
            traces_sample_rate=0.0,
        )

    app = Flask(__name__)
    app.config.from_object(config_name)
    app.response_class = RelativeLocationHeaderResponse

    register_polaris_admin(event_horizon_admin)
    register_vela_admin(event_horizon_admin)

    event_horizon_admin.init_app(app)
    oauth.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(healthz_bp)

    @app.teardown_appcontext
    def remove_session(exception: Optional[Exception] = None) -> Any:
        polaris_db_session.remove()
        vela_db_session.remove()

    return app
