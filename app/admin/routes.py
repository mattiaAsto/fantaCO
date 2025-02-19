from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, flash
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
        return redirect(url_for('auth.login'))


class AdminOnlyView(ModelView):
    form_extra_fields = {
        'password': PasswordField('Password')
    }

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt())

    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))
