from flask import Flask
from config import Config
from app.extensions import db, migrate
from app.public.api import public_bp
from app.publisher.api import publisher_bp
from app.dashboard.routes import dashboard_bp
from app.sso import init_sso


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config)

    init_sso(app)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        app.register_blueprint(dashboard_bp, url_prefix="/")
        app.register_blueprint(public_bp, url_prefix="/api")
        app.register_blueprint(publisher_bp, url_prefix="/api/publisher")

    return app


app = create_app()
