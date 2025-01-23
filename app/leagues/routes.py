from flask import render_template, request, redirect, url_for, session, flash, jsonify, current_app
from . import leagues
from app.models import * #import everytinh from app.models
from app import db, cache
from werkzeug.security import check_password_hash
from flask_login import login_required, login_manager, current_user
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from sqlalchemy import text, MetaData
import os
import json
import asti_webscraper
import time
import random


@leagues.context_processor
def global_injection_dictionary():
    if current_user.is_authenticated:
        active_league = current_user.active_league
        if active_league != "global":
            league_id = League.query.filter_by(name=active_league).first().id

        all_user_leagues_rows = UserLeague.query.filter_by(user_username=current_user.username).all()
        all_leagues=[row.league_name for row in all_user_leagues_rows]
    else:
        all_leagues=["Effettua il login per vedere le leghe"]

    balance = get_league_data_table(get_user_league_id()).query.filter_by(user_username=current_user.username).first().balance if current_user.is_authenticated else 0



    return {
        "is_logged": current_user.is_authenticated, #is_logged is used to chose between login and logout in navbar buttons
        "user": current_user,
        "leagues": all_leagues,
        "balance": balance,
    }

def get_user_league_id():
    if current_user.active_league == "global":
        return 0
    else:
        return League.query.filter_by(name=current_user.active_league).first().id

@cache.memoize()
def get_market_table(id):

    if id == 0:
        return MarketTable
    else:
        return create_dynamic_market_model(id)
    
@cache.memoize()
def get_user_runner_table(id):

    if id == 0:
        return UserRunner
    else:
        return create_dynamic_user_runner_model(id)

@cache.memoize()
def get_league_data_table(id):

    if id == 0:
        return LeagueData
    else:
        return create_dynamic_league_data_model(id)





@leagues.route('/')
def main():
    return render_template('leagues.html')

@leagues.route('/add_vs_create', methods=['GET', 'POST'])
def add_vs_create():
    return render_template('add_vs_create.html')


@leagues.route("/create_new_league", methods=["GET", "POST"])
def create_new_league():
    user_username=current_user.username

    if request.method == "POST":
        league_name = request.form.get("league-name")
        all_legue_names = [league.name for league in League.query.all()]
        if league_name in all_legue_names:
            return render_template('create_new_league.html', error="Nome lega già esistente")
        else:
            new_league = League(name=league_name)
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
    
    return render_template('create_new_league.html')


@leagues.route("/swap_league", methods=["POST"])
def swap_league():
    current_user.active_league=request.form.get("league-name")
    db.session.commit()
    return jsonify({'message': 'Form inviato con successo!'})


@leagues.route("/leave_league", methods=["POST"])
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


@leagues.route("/share_league/<league_name>", methods=["GET","POST"])
def share_league(league_name):
    if league_name == "global":
        return jsonify({'error': 'Non puoi condividere la lega globale'})
    
    serializer = current_app.url_serializer
    token = serializer.dumps(league_name, salt="league-share")

    join_url = url_for("leagues.join_league", token=token, _external=True)

    return render_template("share_league.html", join_url=join_url)


@leagues.route("/join_league/<token>", methods=["GET","POST"])
def join_league(token):
    serializer = current_app.url_serializer
    league_name = serializer.loads(token, salt="league-share", max_age=3600)

    if current_user.is_authenticated:
        if UserLeague.query.filter_by(league_name=league_name, user_username=current_user.username).first() is None:
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
            return jsonify({'error': 'Sei già nella lega'})
    else:
        return redirect(url_for('auth.login'))
        



