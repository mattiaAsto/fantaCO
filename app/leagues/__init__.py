from flask import Blueprint

leagues = Blueprint(
    "leagues", __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="leagues/static"
    )

from . import routes
#this file initiates the blueprint "leagues"