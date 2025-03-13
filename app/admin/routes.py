from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, flash, abort
from flask_login import current_user
from wtforms import PasswordField
from wtforms.validators import Optional
from flask_admin.form import SecureForm
import bcrypt


class AdminHomeView(AdminIndexView):
    """Questa classe protegge l'intero pannello admin."""
    
    def is_accessible(self):
        # Controlla se l'utente è loggato e ha accesso all'admin
        return current_user.is_authenticated and current_user.username == "admin"

    def inaccessible_callback(self, name, **kwargs):
        """Se l'utente non è admin, reindirizza alla pagina di login."""
        return abort(404)

class AdminOnlyView(ModelView):
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))
    
class RunnerOnlyView(ModelView):

    column_list = ["name", "society", "category" ]
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

class UserOnlyView(ModelView):
    form_extra_fields = {
        'password': PasswordField('Password', validators=[Optional()])
    }

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            for _ in range(10):
                print("ciao")
            model.password = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt())
        
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))
    
class ArticleView(AdminOnlyView):
    column_list = ["id", "title", "content", "author", "author_username", "date_posted"]

class RunnerPointsView(AdminOnlyView):
    column_list = ["id", "runner_name", "race", "season", "points"]

class UserRunnerView(AdminOnlyView):
    column_list = ["user_username", "runner_name", "lineup", "selling"]

class LeagueView(AdminOnlyView):
    column_list = ["id", "name", "max_managers"]

class LeagueDataView(AdminOnlyView):
    column_list = ["user_username", "points", "balance"]

class UserLeagueView(AdminOnlyView):
    column_list = ["league_name", "user_username"]
    

""" class ArticleView(AdminOnlyView):
    column_list = [c.name for c in Article.__table__.columns]

class RunnerPointsView(AdminOnlyView):
    column_list = [c.name for c in RunnerPoints.__table__.columns]

class UserRunnerView(AdminOnlyView):
    column_list = [c.name for c in UserRunner.__table__.columns]

class LeagueView(AdminOnlyView):
    column_list = [c.name for c in League.__table__.columns]

class LeagueDataView(AdminOnlyView):
    column_list = [c.name for c in LeagueData.__table__.columns]

class UserLeagueView(AdminOnlyView):
    column_list = [c.name for c in UserLeague.__table__.columns] """

