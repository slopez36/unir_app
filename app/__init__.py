from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config_by_name

db = SQLAlchemy()

def create_app(config_name='dev'):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)

    from .routes.main import main_bp
    from .routes.subjects import subjects_bp
    from .routes.resources import resources_bp
    from .routes.activities import activities_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(activities_bp)

    return app
