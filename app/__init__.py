from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import UserMixin, LoginManager, login_user
from flask_caching import Cache
from itsdangerous import URLSafeTimedSerializer
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
cache = Cache()


def create_app():
    app=Flask(__name__)

    #config of app, as database url
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fantaCO.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://fantaco_database_user:OGA9m6oFLrf8N76afgUfmQjslNp1gw3J@dpg-cu51nd56l47c73dg0b80-a.oregon-postgres.render.com/fantaco_database'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    #Flask-Mail configs
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'   # Server SMTP (es. Gmail: smtp.gmail.com)
    app.config['MAIL_PORT'] = 587                    # Porta del server SMTP (587 per TLS, 465 per SSL)
    app.config['MAIL_USE_TLS'] = True                # Utilizzare TLS (True/False)
    app.config['MAIL_USE_SSL'] = False               # Utilizzare SSL (True/False)
    app.config['MAIL_USERNAME'] = 'fantaco.service@gmail.com'  # Email per l'autenticazione
    app.config['MAIL_PASSWORD'] = 'xyjr smyk zvww whak'          # Password per l'autenticazione
    app.config['MAIL_DEFAULT_SENDER'] = 'astorimattia05@gmail.com'  # Mittente predefinito (opzionale)

    app.config['SECRET_KEY'] = 'lamiachiavesegreta1221'

    app.url_serializer=URLSafeTimedSerializer(app.config['SECRET_KEY'])

    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 60


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
    app.register_blueprint(main_blueprint, url_prefix='/')
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    with app.app_context():
        db.create_all()

    login_manager.login_view="auth.login"

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    
        



    return app
