from flask import Blueprint

main = Blueprint(
    "main", __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="main/static"
    )

from . import routes
#this file initiates the blueprint "views"