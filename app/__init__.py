from flask import Flask

from app.admin import admin
from app.auth import oauth


def create_app(config_name: str = "settings") -> Flask:
    from app.auth import auth_bl

    app = Flask(__name__)
    app.config.from_object(config_name)

    admin.init_app(app)
    oauth.init_app(app)

    app.register_blueprint(auth_bl)
    return app
