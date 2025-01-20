from flask import render_template, request, redirect, url_for, session, flash, jsonify
from . import main
from app.models import * #import everytinh from app.models
from app import db, cache
from werkzeug.security import check_password_hash
from flask_login import login_required, login_manager, current_user
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import os
import json
import asti_webscraper
import time
import random

#common variables
RUNNERS_DATABASE_PATH = asti_webscraper.RUNNERS_DATABASE_PATH
PLAYERS_DATABASE_PATH = asti_webscraper.PLAYERS_DATABASE_PATH
LEAGUE_DATABASE_PATH = asti_webscraper.LEAGUE_DATABASE_PATH
CATEGORIES = asti_webscraper.LIST_OF_CATEGORIES

#functions

#old function for json based database
def load_database(path):
    try:
        with open(path) as f:
            database = json.load(f)
            return database
    except:
        return{}
    
#old function for json based database
def upload_database(path, database):
    with open(path, "w") as f:
        json.dump(database, f)
        return 

#old function for json based database
def uploading_time_span(last_ulpoading_time):
    waiting_belay=3600
    current_time=time.time()
    if last_ulpoading_time+waiting_belay<=current_time:
        return "current"
    else:
        return "must upload"

#old function for old market managment system
def run_market_creation():
    all_runners=db.session.query(Runner).all()
    all_market_runners=db.session.query(MarketTable).all()
    uploading_interval=3600
    actual_time=time.time()

    all_runners_name=[runner.name for runner in all_runners]
    all_market_runners_name=[runner.runner_name for runner in all_market_runners]
    
    free_runners=[runner for runner in all_runners_name if runner not in all_market_runners_name]

    to_delete=[]
    to_add=[]

    counter=0

    for runner in all_market_runners:
        if runner.timestamp <= actual_time-uploading_interval:
            to_delete.append(runner)
            if free_runners:
                new_runner_name=random.choice(free_runners)
                free_runners.remove(new_runner_name)
                new_timestamp=(uploading_interval*len(all_market_runners)+all_market_runners[0].timestamp+counter)
                new_market_runner=MarketTable(
                    runner_name=new_runner_name,
                    timestamp=new_timestamp
                )
                to_add.append(new_market_runner)
                counter+=uploading_interval

    for runner in to_delete:
        db.session.delete(runner)

    for new_runner in to_add:
        db.session.add(new_runner)
    
    db.session.commit()

#with this route a single variable is accesible everywhere and caching routes
@main.context_processor
def global_injection_dictionary():
    if current_user.is_authenticated:
        active_league = current_user.active_league
        if active_league != "global":
            league_id = League.query.filter_by(name=active_league).first().id

        all_user_leagues_rows = UserLeague.query.filter_by(user_username=current_user.username).all()
        all_leagues=[row.league_name for row in all_user_leagues_rows]
    else:
        all_leagues=["Effettua il login per vedere le leghe"]


    return {
        "is_logged": current_user.is_authenticated, #is_logged is used to chose between login and logout in navbar buttons
        "user": current_user,
        "leagues": all_leagues,
    }


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




#routes

#base template for shared html between templates
@main.route("/base")
def base():
    return render_template("base.html")


#Home page, currently displays nothing
@main.route("/")
def home():

    return render_template("home.html")


#market page, displays 16 runners at a time, every hour the older goes and a new one comes
@main.route("/market", methods=["GET", "POST"])
@login_required
def market():


    filters=["Categoria", "Punti", "Società", "Prezzo"]
    filter = ""

    if current_user.active_league == "global":
        id = 0
    else:
        league=current_user.active_league
        id = db.session.query(League).filter_by(name=league).first().id
        
    user_runner_table=get_market_table(id)
    owned_runners=db.session.query(get_user_runner_table(id)).all()
    

    if request.method == 'POST':

        form_id=request.form.get("form_id")

        if form_id == "filter":
            filter=request.form.get("filter")
    
    if filter == "":
        selected_runners=db.session.query(user_runner_table).all()
    elif filter == "Categoria":
        selected_runners = user_runner_table.query.join(Runner).order_by(Runner.category.asc()).all()
    elif filter == "Punti":
        selected_runners = user_runner_table.query.join(Runner).order_by(Runner.points.desc()).all()
    elif filter == "Società":
        selected_runners = user_runner_table.query.join(Runner).order_by(Runner.society.asc()).all()
    elif filter == "Prezzo":
        selected_runners = user_runner_table.query.join(Runner).order_by(Runner.price.desc()).all()


    row_count=db.session.query(user_runner_table).count()
    
    runners_database_list=[]

    for runner in selected_runners:
        current_time=(datetime.now(ZoneInfo("Europe/Zurich")))
        runner_timestamp=runner.timestamp.replace(tzinfo=ZoneInfo("Europe/Zurich"))


        time_since_post=(current_time - runner_timestamp)
        time_remaining=(timedelta(hours=row_count) - time_since_post).seconds  #remaining time in the market in seconds
        if time_remaining >= 7200:
            time_remaining//=3600
            time_remaining=f"{time_remaining} h"
        elif 3600 < time_remaining < 7200:
            time_remaining//=3600
            time_remaining=f"{time_remaining} h"
        else:
            time_remaining//=60
            time_remaining=f"{time_remaining} min"

        full_details=runner.runner
        append_runner={
            "name": full_details.name,
            "society": full_details.society,
            "category": full_details.category,
            "points": full_details.points,
            "price": full_details.price,
            "timestamp": time_remaining
        }
        runners_database_list.append(append_runner)


    sellable_runners = []
    for runner in owned_runners:
        full_details=runner.runner
        sellable_runner={
            "name": full_details.name,
            "society": full_details.society,
            "category": full_details.category,
            "points": full_details.points,
            "price": full_details.price,
            "timestamp": time_remaining
        }
        sellable_runners.append(sellable_runner)

    selling_runners = []
    for runner in owned_runners:
        if runner.selling:
            full_details=runner.runner
            selling_runner={
                "name": full_details.name,
                "society": full_details.society,
                "category": full_details.category,
                "points": full_details.points,
                "price": full_details.price,
                "timestamp": time_remaining
            }
            selling_runners.append(selling_runner)
    

    return render_template('market.html', runners_database=runners_database_list, filters=filters, sellable_runners=sellable_runners, selling_runners=selling_runners)


""" @main.route("/buy-runner", methods=["POST"])
def buy_runner():
    print("ciao")
 """

@main.route("/sell-runner", methods=["POST"])
def sell_runner():
    user=current_user
    runner_name = request.form.get("name")

    user_runner = next((ur for ur in user.runners if ur.runner.name == runner_name), None)

    if user_runner:
        print(f"to remove: {user_runner}")
        #user.balance=user.balance+user_runner.runner.price
        #user_runner.runner.plus_minus-=1
        #db.session.delete(user_runner)
        user_runner.selling=True
        db.session.commit()
    else:
        print("Runner non trovato per questo utente.")
    
    return jsonify({"code": "okay"}), 200


@main.route("/team", methods=['GET', 'POST'])
@login_required
def team():
    user=current_user
    player_balance=user.balance

    if current_user.active_league == "global":
        id = 0
    else:
        league=current_user.active_league
        id = db.session.query(League).filter_by(name=league).first().id
        
    user_runner_table=get_market_table(id)
    owned_runners=db.session.query(get_user_runner_table(id)).all()

    if request.method=="POST":
        print("post")
            

    player_runners=sorted(owned_runners, key=lambda runner: runner.lineup)
    
    runners_database_list=[]
    for runner in player_runners:
        full_details=runner.runner
        append_runner={
            "name": full_details.name,
            "society": full_details.society,
            "category": full_details.category,
            "points": full_details.points,
            "price": full_details.price,
            "lineup": runner.lineup
        }
        runners_database_list.append(append_runner)


    lineup_positions = [None] * 12

    for runner in runners_database_list:
        position = runner["lineup"] - 1
        if 0 <= position < len(lineup_positions):
            lineup_positions[position] = runner

    lineup_line1 = lineup_positions[0:4]  
    lineup_line2 = lineup_positions[4:8]  
    lineup_line3 = lineup_positions[8:12]

    return render_template("team.html", balance=player_balance, lineup_line1=lineup_line1, lineup_line2=lineup_line2, lineup_line3=lineup_line3, runners_database=runners_database_list)


@main.route("/refresh-team", methods=["POST"])
def refresh_team():
    name = request.form.get("name")
    number = request.form.get("number")

    
    old_runner = db.session.query(UserRunner).filter(UserRunner.user_username == current_user.username, UserRunner.lineup == number).first()
    if old_runner: 
        old_runner.lineup = 0

    new_runner = db.session.query(UserRunner).filter(UserRunner.user_username == current_user.username, UserRunner.runner_name == name).first()
    new_runner.lineup = number
    db.session.commit()

    
    return jsonify({"code": "okay"}), 200
    



@main.route("runner", methods=['GET'])
def runner():
    url_parameters=request.args.get("runner", False)
    if not url_parameters:
        return "Il giocatore cercato non esiste oppure non è disponibile"
    if url_parameters:
        name=url_parameters
    full_details = Runner.query.filter_by(name=name).first()
    runner={
                "name": full_details.name,
                "society": full_details.society,
                "category": full_details.category,
                "points": full_details.points,
                "price": full_details.price
            }
    
    return render_template("runner.html", runner=runner)

@main.route("/create_new_league", methods=["GET", "POST"])
def create_new_league():
    user_username=current_user.username

    league_name="pincopallino"
    new_league = League(name=league_name)
    db.session.add(new_league)
    new_user_league = UserLeague(league_name=league_name, user_username=user_username)
    db.session.add(new_user_league)
    db.session.commit()
    create_dynamic_tables(new_league.id, user_username)
    return jsonify({'message': f"Lega '{league_name}' creata con successo!"})

@main.route("/test")
def test():
    all_user_leagues_rows = UserLeague.query.filter_by(user_username=current_user.username).all()
    all_leagues=[row.league_name for row in all_user_leagues_rows]
    return all_leagues

@main.route("/swap_league", methods=["POST"])
def swap_league():
    current_user.active_league=request.form.get("league-name")
    db.session.commit()
    return jsonify({'message': 'Form inviato con successo!'})
