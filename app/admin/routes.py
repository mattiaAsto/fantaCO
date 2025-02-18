from flask import render_template, request, redirect, url_for, session, current_app, flash, jsonify
from flask_mail import Message
from flask_login import login_user, logout_user, login_required, current_user
from . import admin
from app.models import *
from app import db, mail
from werkzeug.security import check_password_hash
from sqlalchemy import func
import os
import json
import asti_webscraper
import bcrypt
import time
import random

@admin.route("/")
@login_required
def admin_home():
    if not current_user.username == "admin":
        return redirect(url_for("main.home"))