import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "POSTGRESQL_DB_CONNECT_STRING", "sqlite:///solutions.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv(
        "FLASK_SECRET_KEY", "dev-secret-key"
    )
    OPENID_LAUNCHPAD_TEAM = os.getenv(
        "OPENID_LAUNCHPAD_TEAM", "charmhub-solution-reviewers"
    )
