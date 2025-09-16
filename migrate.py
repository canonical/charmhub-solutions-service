from flask_migrate import upgrade
from snaprecommend import app

if __name__ == "__main__":
    with app.app_context():
        upgrade()
