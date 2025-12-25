from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config_by_name

db = SQLAlchemy()

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)

    # Trust proxy headers (needed for HTTPS behind Nginx Proxy Manager)
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    from .routes.main import main_bp
    from .routes.subjects import subjects_bp
    from .routes.resources import resources_bp
    from .routes.activities import activities_bp
    
    from app.routes.auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(subjects_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(activities_bp)
    app.register_blueprint(auth_bp)

    from flask import session, redirect, url_for, request

    @app.before_request
    def require_login():
        allowed_routes = ['auth.login', 'auth.callback', 'static']
        if request.endpoint and request.endpoint not in allowed_routes and 'user_email' not in session:
             # Basic check: if it acts like a static asset or public route, skip
             if not request.endpoint.startswith('static'):
                 return redirect(url_for('auth.login'))

    return app
