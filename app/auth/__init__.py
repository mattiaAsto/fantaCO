from flask import Blueprint

auth = Blueprint(
    "auth", __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="views/static"
    )

from . import routes
#this file initiates the blueprint "views"