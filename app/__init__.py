from flask import Flask
from config import Config
from app.extensions import db, migrate
from app.public.api import public_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.route("/")
    def index():
        return "Charmhub Solutions API - Copyright 2025 Canonical"

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        app.register_blueprint(public_bp, url_prefix="/api")

    return app


app = create_app()
