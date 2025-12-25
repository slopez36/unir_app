import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-unir-app'
    # Use database in instance folder
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'unir_app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Auth settings
    ALLOWED_EMAILS = ["slopezgoikolea@gmail.com"]

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig
}
