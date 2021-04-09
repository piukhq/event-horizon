from authlib.integrations.flask_client import OAuth
from flask import Flask, Response

from app.polaris.views.admin import polaris_admin
from app.settings import OAUTH_SERVER_METADATA_URL

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

    app = Flask(__name__)
    app.config.from_object(config_name)
    app.response_class = RelativeLocationHeaderResponse

    oauth.init_app(app)
    polaris_admin.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(healthz_bp)
    return app
