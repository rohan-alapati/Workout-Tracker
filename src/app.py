# src/app.py
import os
from flask import Flask
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

load_dotenv()


def create_app():
    # — Set up instance folder for SQLite —
    base_dir = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(base_dir, "instance")
    os.makedirs(instance_dir, exist_ok=True)

    # — Initialize Flask —
    app = Flask(__name__, instance_relative_config=True, instance_path=instance_dir)

    from flasgger import Swagger

    # ... inside create_app(), after app = Flask(...)
    template = {
        "swagger": "2.0",
        "info": {"title": "Workout Tracker API", "version": "1.0.0"},
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT: Bearer <token>",
            }
        },
    }
    Swagger(app, template=template)

    # — Config —
    db_file = os.path.join(instance_dir, "workout.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", f"sqlite:///{db_file}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET", "change-me")

    # — Extensions —
    from src.model import db

    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)

    # — Blueprints —
    from src.auth import auth_bp

    app.register_blueprint(auth_bp)

    from src.workout import workouts_bp

    app.register_blueprint(workouts_bp)

    from src.reports import reports_bp

    app.register_blueprint(reports_bp)

    from src.ui import ui_bp

    app.register_blueprint(ui_bp)

    @app.route("/")
    def home():
        return "🏋️‍♂️ Workout Tracker API is live!"

    return app
