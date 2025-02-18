from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for
from flask_login import current_user
from wtforms import BooleanField

class AdminOnlyView(ModelView):
    form_overrides = {
        'is_validated': BooleanField,
        'light_theme': BooleanField
    }

    def on_model_change(self, form, model, is_created):
        # Converte i valori 'y' e 'n' in True e False
        if form.is_validated.data == 'y':
            model.is_validated = True
        elif form.is_validated.data == 'n':
            model.is_validated = False

        if form.light_theme.data == 'y':
            model.light_theme = True
        elif form.light_theme.data == 'n':
            model.light_theme = False

        # Chiamare il metodo della classe base per assicurarsi che il cambiamento venga applicato
        return super(AdminOnlyView, self).on_model_change(form, model, is_created)
    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == "admin"

    def inaccessible_callback(self, name, **kwargs):
        """Se l'utente non è admin, viene reindirizzato alla pagina di login"""
        return redirect(url_for('auth.login'))
