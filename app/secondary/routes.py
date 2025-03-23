from flask import render_template, request, redirect, url_for, session, flash, jsonify, current_app
from . import secondary
from app.models import * #import everytinh from app.models
from app import db, cache
from werkzeug.security import check_password_hash
from flask_login import login_required, login_manager, current_user
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from sqlalchemy import text, MetaData
from rapidfuzz import process, fuzz
from sqlalchemy.orm import load_only
import os
import json
from z_unused_scripts import asti_webscraper
import time
import random


@secondary.context_processor
def global_injection_dictionary():
    if current_user.is_authenticated:
        active_league = current_user.active_league
        if active_league != "global":
            league_id = League.query.filter_by(name=active_league).first().id

        all_user_leagues_rows = UserLeague.query.filter_by(user_username=current_user.username).all()
        all_leagues=[row.league_name for row in all_user_leagues_rows]

        light_theme = current_user.light_theme
    else:
        all_leagues=["Effettua il login per vedere le leghe"]

        light_theme = False

    balance = get_league_data_table(get_user_league_id()).query.filter_by(user_username=current_user.username).first().balance if current_user.is_authenticated else 0




    return {
        "is_logged": current_user.is_authenticated, #is_logged is used to chose between login and logout in navbar buttons
        "user": current_user,
        "leagues": all_leagues,
        "balance": balance,
        "light_theme": light_theme,
    }

def get_user_league_id():
    if current_user.active_league == "global":
        return 0
    else:
        return League.query.filter_by(name=current_user.active_league).first().id


def get_market_table(id):

    if id == 0:
        return MarketTable
    else:
        return create_dynamic_market_model(id)
    

def get_user_runner_table(id):

    if id == 0:
        return UserRunner
    else:
        return create_dynamic_user_runner_model(id)


def get_league_data_table(id):

    if id == 0:
        return LeagueData
    else:
        return create_dynamic_league_data_model(id)





@secondary.route('/')
def main():
    return "secondary-main"

@secondary.route('/add_vs_create', methods=['GET', 'POST'])
def add_vs_create():
    return render_template('add_vs_create.html')

@secondary.route('/profile', methods=["GET", "POST"])
@login_required
def profile():

    if request.method == "POST":
        name = request.form.get("name")
        surname = request.form.get("surname")
        nickname = request.form.get("nickname")
        username = request.form.get("username")
        theme =str( request.form.get("theme"))
        if name:
            current_user.name = name
        if surname:
            current_user.surname = surname
        if username:
            current_user.username = username
        if nickname:
            current_user.nickname = nickname
        if theme == "True":
            current_user.light_theme = True
        else:
            current_user.light_theme = False
        db.session.commit()
        return redirect(url_for("main.home"))

    
    return render_template("profile.html")


@secondary.route('/upload_image')
def upload_image():
    all_runner_names = [runner.name for runner in Runner.query.all()]
    return render_template("add_picture.html", names=all_runner_names)
    #return "upload image --non ancora implementato, arriverà a breve"

@secondary.route("/create_new_league", methods=["GET", "POST"])
def create_new_league():
    user_username=current_user.username

    if request.method == "POST":
        league_name = request.form.get("league-name")
        max_managers = int(request.form.get("max-managers")) if request.form.get("max-managers") != "" else 0
        all_legue_names = [league.name for league in League.query.all()]
        if league_name in all_legue_names or league_name == "":
            return render_template('create_new_league.html', error="Nome lega già esistente o vuoto")
        elif max_managers < 2:
            return render_template('create_new_league.html', error="Inserisci un numero di manager maggiore di 1")
        else:
            new_league = League(name=league_name, max_managers=max_managers)
            db.session.add(new_league)

            new_user_league = UserLeague(league_name=league_name, user_username=user_username)
            db.session.add(new_user_league)

            db.session.commit()

            create_dynamic_tables(new_league.id, user_username)
            populate_market(new_league.id)
            create_default_team(new_league.id, user_username)

            league_data = create_dynamic_league_data_model(new_league.id)

            new_user_data = league_data(user_username=user_username)
            db.session.add(new_user_data)  

            current_user.active_league=league_name

            db.session.commit()


            return redirect(url_for('main.home')) 
    
    return render_template('create_new_league.html', error="Inserisci nome e numero di manager")


@secondary.route("/swap_league", methods=["POST"])
def swap_league():
    current_user.active_league=request.form.get("league-name")
    db.session.commit()
    return jsonify({'message': 'Form inviato con successo!'})


@secondary.route("/leave_league", methods=["POST"])
def leave_league():

    league = request.form.get("league-name")
    user_username = current_user.username

    league_id = League.query.filter_by(name=league).first().id

    league_market = get_market_table(league_id)
    league_user_runner = get_user_runner_table(league_id)
    league_data = get_league_data_table(league_id)

    user_league = UserLeague.query.filter_by(league_name=league, user_username=user_username).first()
    db.session.delete(user_league)

    if (UserLeague.query.filter_by(league_name=league).count() == 0):
        league = League.query.filter_by(name=league).first()
        db.session.delete(league)

        db.session.commit()

        metadata = MetaData()
        metadata.reflect(bind=db.engine)

        league_market.__table__.metadata = metadata
        league_user_runner.__table__.metadata = metadata
        league_data.__table__.metadata = metadata

        metadata.drop_all(
            tables=[league_market.__table__, league_user_runner.__table__, league_data.__table__],
            bind=db.engine
        )
    
    else:
        user_data = league_data.query.filter_by(user_username=user_username).first()
        db.session.delete(user_data)

        league_user_runner = league_user_runner.query.filter_by(user_username=user_username).all()
        for user_runner in league_user_runner:
            db.session.delete(user_runner)

    current_user.active_league="global"


    db.session.commit()

    return redirect(url_for('main.home'))


@secondary.route("/share_league/<league_name>", methods=["GET","POST"])
def share_league(league_name):
    if league_name == "global":
        return jsonify({'error': 'Non puoi condividere la lega globale'})
    
    serializer = current_app.url_serializer
    token = serializer.dumps(league_name, salt="league-share")

    join_url = url_for("secondary.join_league", token=token, _external=True)

    return render_template("share_league.html", join_url=join_url)


@secondary.route("/join_league/<token>", methods=["GET","POST"])
def join_league(token):
    serializer = current_app.url_serializer
    league_name = serializer.loads(token, salt="league-share", max_age=3600)

    managers_already_in = UserLeague.query.filter_by(league_name=league_name).count()
    max_managers = League.query.filter_by(name=league_name).first().max_managers

    if current_user.is_authenticated:
        if UserLeague.query.filter_by(league_name=league_name, user_username=current_user.username).first() is None and managers_already_in < max_managers:
            user_username = current_user.username

            new_user_league = UserLeague(league_name=league_name, user_username=user_username)
            db.session.add(new_user_league)

            current_user.active_league=league_name

            league_data_table = get_league_data_table(League.query.filter_by(name=league_name).first().id)
            
            db.session.add(league_data_table(user_username=user_username))

            db.session.commit()

            create_default_team(League.query.filter_by(name=league_name).first().id, user_username)


            return redirect(url_for('main.home'))
        else:
            return jsonify({'error': 'Sei già nella lega oppure la lega è piena'})
    else:
        return redirect(url_for('auth.login'))
        

@secondary.route("/create_article" , methods=["GET", "POST"])
@login_required
def create_article():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        author = current_user.nickname
        author_username = current_user.username

        
        if content == "" and title == "":
            return render_template("create_article.html", error="Titolo o testo vuoto")
        elif Article.query.filter_by(title=title).first() != None:
            return render_template("create_article.html", error="Titolo già utilizzato in un altro articolo")
        else:
            new_article = Article(title=title, content=content, author=author, author_username=author_username)
            db.session.add(new_article)
            db.session.commit()

        return redirect(url_for('main.home'))

    return render_template("create_article.html", error="")

@secondary.route("/delete_article", methods=["POST"])
def delete_article():
    article_id = request.form.get("article-id")
    article = Article.query.filter_by(id=article_id).first()
    db.session.delete(article)
    db.session.commit()

    return redirect(url_for("main.home"))

@secondary.route("/search", methods=["GET", "POST"])
@login_required
def search():
    data = "Richiesta invalida"

    if request.method == "POST":
        data = request.form.get("search-bar")
    
    query = data

    users = User.query.options(load_only(User.username, User.name, User.nickname)).all()
    user_data = {user.username: user for user in users}
    user_data.update({user.name: user for user in users})
    user_data.update({user.nickname: user for user in users})

    # Recuperiamo tutti i runner (solo il nome)
    runners = Runner.query.options(load_only(Runner.name)).all()
    runner_data = {runner.name: runner for runner in runners}

    # Combiniamo i nomi utenti e runner in un unico dizionario con etichette
    all_names = {**user_data, **runner_data}

    # Troviamo la corrispondenza più simile
    best_match, score, _ = process.extractOne(query, all_names.keys(), scorer=fuzz.WRatio)

    if best_match and score > 70:  # Soglia minima di accuratezza
        matched_object = all_names[best_match]
        if isinstance(matched_object, User):
            return redirect(url_for("main.user", username=matched_object.username))
        elif isinstance(matched_object, Runner):
            return redirect(url_for("main.runner", runner=matched_object.name))

    return {"type": "none", "message": "Nessun risultato trovato"}

