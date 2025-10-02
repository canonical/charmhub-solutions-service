from flask_migrate import upgrade
from app import app

if __name__ == "__main__":
    with app.app_context():
        upgrade()
