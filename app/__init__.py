from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import UserMixin, LoginManager, login_user, current_user
from flask_caching import Cache
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from itsdangerous import URLSafeTimedSerializer
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from distutils.util import strtobool
from app.admin.routes import AdminHomeView
import atexit
import os
from pathlib import Path


db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
cache = Cache()
admin_panel = admin = Admin(name='FantaCO Admin', template_mode='bootstrap3', index_view=AdminHomeView())


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


    app.config['SQLALCHEMY_DATABASE_URI'] = db_complete_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_POOL_SIZE'] = 10
    app.config['SQLALCHEMY_POOL_TIMEOUT'] = 5  
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600 

    #Flask-Mail configs
    app.config['MAIL_SERVER'] = mail_server   # Server SMTP (es. Gmail: smtp.gmail.com)
    app.config['MAIL_PORT'] = mail_port                    # Porta del server SMTP (587 per TLS, 465 per SSL)
    app.config['MAIL_USE_TLS'] = mail_use_tls               # Utilizzare TLS (True/False)
    app.config['MAIL_USE_SSL'] = mail_use_ssl               # Utilizzare SSL (True/False)
    app.config['MAIL_USERNAME'] = mail_username  # Email per l'autenticazione
    app.config['MAIL_PASSWORD'] = mail_password         # Password per l'autenticazione
    app.config['MAIL_DEFAULT_SENDER'] = mail_default_sender  # Mittente predefinito (opzionale)

    app.config['SECRET_KEY'] = secret_key

    app.url_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

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

    admin_panel.init_app(app)

    from app.admin.routes import UserOnlyView, AdminOnlyView, RunnerOnlyView, ArticleView, RunnerPointsView, UserRunnerView, LeagueView, LeagueDataView, UserLeagueView
    from .models import Article, User, Runner, RunnerPoints, UserRunner, League, LeagueData, UserLeague

    admin_panel.add_view(ArticleView(Article, db.session))
    admin_panel.add_view(UserOnlyView(User, db.session))
    admin_panel.add_view(RunnerOnlyView(Runner, db.session))
    admin_panel.add_view(RunnerPointsView(RunnerPoints, db.session))
    admin_panel.add_view(UserRunnerView(UserRunner, db.session))
    admin_panel.add_view(LeagueView(League, db.session))
    admin_panel.add_view(LeagueDataView(LeagueData, db.session))
    admin_panel.add_view(UserLeagueView(UserLeague, db.session))



    #register blueprints
    from app.main import main as main_blueprint
    from app.auth import auth as auth_blueprint
    from app.secondary import secondary as secondary_blueprint
    app.register_blueprint(main_blueprint, url_prefix='/')
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(secondary_blueprint, url_prefix='/secondary')


    with app.app_context():
        db.create_all()

    login_manager.login_view="auth.login"

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    @app.errorhandler(500)
    def page_not_found(error):
        error ={
            "title": "500 internal error",
            "code": 500,
            "message": "Sembra che ci sia stato un errore interno al server, ricarica la pagina o riprova piu tardi a raggiungere la pagina richiesta.",
            "image": "internal",
        }
        return render_template("error.html", error=error), 500
    
    @app.errorhandler(405)
    def page_not_found(error):
        error ={
            "title": "405 bad request",
            "code": 405,
            "message": "Opss..., sembra che la richiesta invata non sia gestibile dal server",
            "image": "lost",
        }
        return render_template("error.html", error=error), 405
    
    @app.errorhandler(404)
    def page_not_found(error):
        error ={
            "title": "404 not found",
            "code": 404,
            "message": "Opss.. Sembra che la pagina che tu ti sia perso. La pagina che stai cercando non è qui.",
            "image": "lost",
        }
        return render_template("error.html", error=error), 404
    
    @app.errorhandler(403)
    def page_not_found(error):
        error ={
            "title": "403 error",
            "code": 403,
            "message": "Opss.. Sembra che tu non abbia le autorizzazioni necessarie ad accedere a questa pagina, nel caso di bisogno contatta l'assistenza.",
            "image": "auth_error",
        }
        return render_template("error.html", error=error), 403
    
    
        



    return app
