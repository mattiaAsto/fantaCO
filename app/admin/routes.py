from flask_admin.contrib.sqla import ModelView
from wtforms import BooleanField
from flask_login import current_user
from flask import redirect, url_for

class AdminOnlyView(ModelView):
    form_overrides = {
        'is_validated': BooleanField,
        'light_theme': BooleanField
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.username == "admin"

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

    def on_model_change(self, form, model, is_created):
        # Quando l'utente seleziona il checkbox, vogliamo che il valore sia la stringa 'True'
        if form.is_validated.data:  # Se il checkbox è selezionato
            model.is_validated = 'True'  # Impostiamo la stringa 'True'
        else:  # Se il checkbox non è selezionato
            model.is_validated = 'False'  # Impostiamo la stringa 'False'

        if form.light_theme.data:  # Per il checkbox light_theme
            model.light_theme = 'True'  # Impostiamo la stringa 'True'
        else:
            model.light_theme = 'False'  # Impostiamo la stringa 'False'

        return super(AdminOnlyView, self).on_model_change(form, model, is_created)
