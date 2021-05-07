from typing import Any, Optional

import sentry_sdk

from authlib.integrations.flask_client import OAuth
from flask import Flask, Response
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.polaris.db.session import db_session
from app.polaris.views.admin import polaris_admin
from app.settings import OAUTH_SERVER_METADATA_URL, SENTRY_DSN, SENTRY_ENV
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
    from app.polaris.views.auth import auth_bp
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

    oauth.init_app(app)
    polaris_admin.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(healthz_bp)

    @app.teardown_appcontext
    def remove_session(exception: Optional[Exception] = None) -> Any:
        db_session.remove()

    return app
