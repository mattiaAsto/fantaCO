from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import UserMixin, LoginManager, login_user
from flask_caching import Cache
from itsdangerous import URLSafeTimedSerializer
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from distutils.util import strtobool
import atexit
import os
from pathlib import Path


db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
cache = Cache()


def create_app():

    app=Flask(__name__)

    load_dotenv()

    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_hostname = os.getenv("DB_HOSTNAME")
    db_name = os.getenv("DB_NAME")

    db_complete_url = os.getenv("DB_COMPLETE_URL")

    mail_server = str(os.getenv("MAIL_SERVER"))
    mail_port = int(os.getenv("MAIL_PORT"))
    mail_use_tls = True
    mail_use_ssl = False
    mail_username = str(os.getenv("MAIL_USERNAME"))
    mail_password = str(os.getenv("MAIL_PASSWORD"))
    mail_default_sender = str(os.getenv("MAIL_DEFAULT_SENDER"))

    secret_key = os.getenv("SECRET_KEY")

    cache_type = os.getenv("CACHE_TYPE")
    cache_default_timeout = int(os.getenv("CACHE_DEFAULT_TIMEOUT"))


    #config of app, as database url
    if db_complete_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_complete_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_hostname}.oregon-postgres.render.com/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    #Flask-Mail configs
    app.config['MAIL_SERVER'] = mail_server   # Server SMTP (es. Gmail: smtp.gmail.com)
    app.config['MAIL_PORT'] = mail_port                    # Porta del server SMTP (587 per TLS, 465 per SSL)
    app.config['MAIL_USE_TLS'] = mail_use_tls               # Utilizzare TLS (True/False)
    app.config['MAIL_USE_SSL'] = mail_use_ssl               # Utilizzare SSL (True/False)
    app.config['MAIL_USERNAME'] = mail_username  # Email per l'autenticazione
    app.config['MAIL_PASSWORD'] = mail_password         # Password per l'autenticazione
    app.config['MAIL_DEFAULT_SENDER'] = mail_default_sender  # Mittente predefinito (opzionale)

    app.config['SECRET_KEY'] = secret_key

    app.url_serializer=URLSafeTimedSerializer(app.config['SECRET_KEY'])

    app.config['CACHE_TYPE'] = cache_type
    app.config['CACHE_DEFAULT_TIMEOUT'] = cache_default_timeout


    #init Flask-Mail
    mail.init_app(app)

    #init SQLAlchemy 
    db.init_app(app)

    #init Flas-Login
    login_manager.init_app(app)

    #init Flasc-Cache
    cache.init_app(app)



    #register blueprints
    from app.main import main as main_blueprint
    from app.auth import auth as auth_blueprint
    from app.leagues import leagues as leagues_blueprint
    app.register_blueprint(main_blueprint, url_prefix='/')
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(leagues_blueprint, url_prefix='/leagues')

    with app.app_context():
        db.create_all()

    login_manager.login_view="auth.login"

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    
        



    return app
