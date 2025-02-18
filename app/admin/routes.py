from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for
from flask_login import current_user
from wtforms import BooleanField

class AdminOnlyView(ModelView):
    form_overrides = {
        'is_validated': BooleanField,
        'light_theme': BooleanField
    }
    form_choices = {
        'is_validated': [(True, 'Yes'), (False, 'No')],
        'light_theme': [(True, 'Light Theme'), (False, 'Dark Theme')]
    }
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == "admin"

    def inaccessible_callback(self, name, **kwargs):
        """Se l'utente non è admin, viene reindirizzato alla pagina di login"""
        return redirect(url_for('auth.login'))
