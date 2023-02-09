import logging

from typing import Any

import sentry_sdk

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, Flask, Response
from flask_wtf.csrf import CSRFProtect
from retry_tasks_lib.admin.views import register_tasks_admin
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from event_horizon.admin import event_horizon_admin
from event_horizon.admin.model_views import BaseModelView
from event_horizon.carina import CARINA_MENU_TITLE
from event_horizon.carina.db import db_session as carina_db_session
from event_horizon.carina.db.models import Base as CarinaModelBase
from event_horizon.carina.db.session import engine as carina_engine
from event_horizon.hubble.db import db_session as hubble_db_session
from event_horizon.hubble.db.models import Base as HubbleModelBase
from event_horizon.hubble.db.session import engine as hubble_engine
from event_horizon.polaris import POLARIS_MENU_TITLE
from event_horizon.polaris.db import db_session as polaris_db_session
from event_horizon.polaris.db.models import Base as PolarisModelBase
from event_horizon.polaris.db.session import engine as polaris_engine
from event_horizon.settings import OAUTH_SERVER_METADATA_URL, QUERY_LOG_LEVEL, ROUTE_BASE, SENTRY_DSN, SENTRY_ENV, redis
from event_horizon.vela import VELA_MENU_TITLE
from event_horizon.vela.db import db_session as vela_db_session
from event_horizon.vela.db.models import Base as VelaModelBase
from event_horizon.vela.db.session import engine as vela_engine
from event_horizon.version import __version__

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


# pylint: disable=import-outside-toplevel
def create_app(config_name: str = "event_horizon.settings") -> Flask:
    CarinaModelBase.prepare(carina_engine, reflect=True)
    PolarisModelBase.prepare(polaris_engine, reflect=True)
    VelaModelBase.prepare(vela_engine, reflect=True)
    HubbleModelBase.prepare(hubble_engine, reflect=True)

    from event_horizon.carina import register_carina_admin
    from event_horizon.hubble import register_hubble_admin
    from event_horizon.polaris import register_polaris_admin
    from event_horizon.vela import register_vela_admin
    from event_horizon.views.auth import auth_bp
    from event_horizon.views.healthz import healthz_bp

    query_log_level = getattr(logging, QUERY_LOG_LEVEL.upper())
    sqla_logger = logging.getLogger("sqlalchemy.engine")
    sqla_logger.setLevel(query_log_level)
    sqla_handler = logging.StreamHandler()
    sqla_handler.setLevel(level=query_log_level)
    sqla_logger.addHandler(sqla_handler)

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
    register_tasks_admin(
        admin=event_horizon_admin,
        scoped_db_session=polaris_db_session,
        redis=redis,
        admin_base_classes=(BaseModelView,),
        url_prefix="polaris",
        endpoint_prefix="polaris",
        menu_title=POLARIS_MENU_TITLE,
    )
    register_vela_admin(event_horizon_admin)
    register_tasks_admin(
        admin=event_horizon_admin,
        scoped_db_session=vela_db_session,
        redis=redis,
        admin_base_classes=(BaseModelView,),
        url_prefix="vela",
        endpoint_prefix="vela",
        menu_title=VELA_MENU_TITLE,
    )
    register_carina_admin(event_horizon_admin)
    register_tasks_admin(
        admin=event_horizon_admin,
        scoped_db_session=carina_db_session,
        redis=redis,
        admin_base_classes=(BaseModelView,),
        url_prefix="carina",
        endpoint_prefix="carina",
        menu_title=CARINA_MENU_TITLE,
    )
    register_hubble_admin(event_horizon_admin)

    event_horizon_admin.init_app(app)
    oauth.init_app(app)
    CSRFProtect(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(healthz_bp)

    eh_bp = Blueprint("eh", __name__, static_url_path=f"{ROUTE_BASE}/eh/static", static_folder="static")
    app.register_blueprint(eh_bp)

    @app.teardown_appcontext
    def remove_session(exception: BaseException | None = None) -> Any:  # pylint: disable=unused-argument
        carina_db_session.remove()
        polaris_db_session.remove()
        vela_db_session.remove()
        hubble_db_session.remove()

    return app
