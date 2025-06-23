import os
from flask import Flask
from application.database import db  # Import database

app = None

def create_app():
    app = Flask(__name__)
    app.secret_key = "super_secret_key_123"
    app.debug = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking.sqlite3"
    db.init_app(app)
    app.app_context().push()  # Ensures everything runs within Flask context
    app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")
    return app

app = create_app()
from application.controller import *

if __name__ == "__main__":
    app.run()
