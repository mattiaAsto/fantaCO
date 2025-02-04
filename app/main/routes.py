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
def format_number(number):
    formatted_integer_part = "{:,}".format(int(number)).replace(",", "'")
    return f"{formatted_integer_part}.-"

#with this route a single variable is accesible everywhere and caching routes
@main.context_processor
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
        "format_number": format_number,
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
    
def get_league_transaction_table(id):
    return create_dynamic_league_transaction(id)



#routes

#base template for shared html between templates
@main.route("/base")
def base():
    return render_template("base.html")


#Home page, currently displays nothing
@main.route("/")
def home():
    all_articles = Article.query.order_by(Article.date_posted.desc()).all()

    articles = []
    for article in all_articles:
        article_date = datetime.replace(article.date_posted, tzinfo=timezone.utc)
        article_age = (datetime.now(timezone.utc) - article_date).seconds
        if article_age > 2592000:
           db.session.delete(article)
           db.session.commit()
        elif article_age >= 86400:
            article_age = f"{article_age // 86400} giorni fa"
        elif article_age >= 7200:
            article_age = f"{article_age // 3600} ore fa"
        elif article_age >= 3600:
            article_age = f"{article_age // 3600} ora fa"
        elif article_age > 60:
            article_age = f"{article_age // 60} minuti fa"
        else:
            article_age = "pochi secondi fa"
        
        article_info = {
            "id": article.id,
            "title": article.title,
            "content": article.content,
            "author": article.author,
            "author_username": article.author_username,
            "date": article_age
        }
        articles.append(article_info)


    return render_template("home.html", articles=articles, active_page="home")


#market page, displays 16 runners at a time, every hour the older goes and a new one comes
@main.route("/market", methods=["GET", "POST"])
@login_required
def market():


    filters=["Categoria", "Punti", "Società", "Prezzo"]
    filter = ""

    id = get_user_league_id()
        
    market_table=get_market_table(id)
    user_runner_table=get_user_runner_table(id)
    league_data_table = get_league_data_table(get_user_league_id())
    if get_user_league_id() is not 0:
        transaction_table = create_dynamic_league_transaction(get_user_league_id())


    if request.method == 'POST':

        form_id=request.form.get("form_id")

        if form_id == "filter":
            filter=request.form.get("filter")
        
        elif form_id == "remove_runner_offer":
            runner_name = request.form.get("runner_name")

            is_from_market = request.form.get("is_from_market")

            if is_from_market == "True":
                market_runner = market_table.query.filter_by(runner_name=runner_name).first()
            else:
                market_runner = user_runner_table.query.filter_by(runner_name=runner_name).first()

            market_runner.offer = 0
            market_runner.buyer = None
            db.session.commit()

        elif form_id == "add_runner_offer":
            if current_user.active_league == "global":
                runner_name = request.form.get("runner_name")
                offer_amount = request.form.get("offer_amount")

                if int(offer_amount) >= Runner.query.filter_by(name=runner_name).first().price and UserRunner.query.filter_by(user_username=current_user.username, runner_name=runner_name).first() is None:
                    new_relation = UserRunner(user_username=current_user.username, runner_name=runner_name)
                    db.session.add(new_relation)

                    current_user.league_data.balance -= int(offer_amount)
                    db.session.commit()
                else:
                    return jsonify({"errore": "GIocatore già in squadra o offerta troppo bassa"}), 400
            else:
                offer_amount = request.form.get("offer_amount")
                offer_amount = int(offer_amount) if offer_amount else 0
                min_price = request.form.get("min_price")
                runner_name = request.form.get("runner_name")

                is_from_market = request.form.get("is_from_market")

                if is_from_market == "True":
                    market_runner = market_table.query.filter_by(runner_name=runner_name).first()
                else:
                    market_runner = user_runner_table.query.filter_by(runner_name=runner_name).first()


                if int(market_runner.offer) < offer_amount and offer_amount >= int(min_price):
                    market_runner.offer = offer_amount
                    market_runner.buyer = current_user.username
                    db.session.commit()
                else:
                    print("offer less")   
        
        elif form_id == "remove_sell_runner":
            runner_name = request.form.get("runner_name")
            runner_info = user_runner_table.query.filter_by(runner_name=runner_name).first()
            runner_info.selling = 0
            runner_info.offer = 0
            runner_info.buyer = None
            db.session.commit()

        elif form_id == "accept_sell_offer":
            buyer = request.form.get("buyer_username")
            seller = current_user.username
            runner_name = request.form.get("runner_name")
            offer = int(request.form.get("offer"))


            if buyer == "FantaCO":

                user_league_data = league_data_table.query.filter_by(user_username=current_user.username).first()
                user_league_data.balance += offer

                user_runner = db.session.query(user_runner_table).filter_by(user_username=current_user.username, runner_name=runner_name).first()

                transaction_table = create_dynamic_league_transaction(id)
                new_transaction_info = transaction_table(
                    buyer_username = buyer,
                    seller_username = seller,
                    runner_name = runner_name,
                    amount = offer,
                )

                db.session.add(new_transaction_info)
                db.session.delete(user_runner)

            else:
                user_runner = user_runner_table.query.filter_by(user_username=current_user.username, runner_name=runner_name).first()
                db.session.delete(user_runner)
                user_league_data = league_data_table.query.filter_by(user_username=current_user.username).first()
                user_league_data.balance += offer

                buyer_league_data = league_data_table.query.filter_by(user_username=buyer).first()
                buyer_league_data.balance -= offer
                new_relation = user_runner_table(user_username=buyer, runner_name=runner_name)
                db.session.add(new_relation)

                transaction_table = create_dynamic_league_transaction(id)
                new_transaction_info = transaction_table(
                    buyer_username = buyer,
                    seller_username = seller,
                    runner_name = runner_name,
                    amount = offer,
                )

                db.session.add(new_transaction_info)
            db.session.commit()
                

    if filter == "":
        selected_runners=db.session.query(market_table).all()
    elif filter == "Categoria":
        selected_runners = market_table.query.join(Runner).order_by(Runner.category.asc()).all()
    elif filter == "Punti":
        selected_runners = market_table.query.join(Runner).order_by(Runner.points.desc()).all()
    elif filter == "Società":
        selected_runners = market_table.query.join(Runner).order_by(Runner.society.asc()).all()
    elif filter == "Prezzo":
        selected_runners = market_table.query.join(Runner).order_by(Runner.price.desc()).all()

    owned_runners=db.session.query(user_runner_table).filter_by(user_username=current_user.username).all()

    all_owned_runners=db.session.query(user_runner_table).all()


    row_count=db.session.query(market_table).count()
    
    runners_database=[]

    for runner in all_owned_runners:
        if runner.selling:
            full_details=runner.runner
            selling_runner={
                "name": full_details.name,
                "society": full_details.society,
                "category": full_details.category,
                "points": full_details.points,
                "price": full_details.price,
                "timestamp": "none",
                "seller": runner.user.nickname,
                "is_from_market": False,
                "buyer": runner.buyer,
                "offer": runner.offer
            }
            runners_database.append(selling_runner)

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
            "timestamp": time_remaining,
            "seller": "FantaCO",
            "is_from_market": True,
            "buyer": runner.buyer,
            "offer": runner.offer
        }
        runners_database.append(append_runner)

    #runners for the selling popup
    sellable_runners = []
    for runner in owned_runners:
        full_details=runner.runner
        sellable_runner={
            "name": full_details.name,
            "society": full_details.society,
            "category": full_details.category,
            "points": full_details.points,
            "price": full_details.price,
            "timestamp": time_remaining,
            "selling": runner.selling,
        }
        sellable_runners.append(sellable_runner)

    #runners in the sell slide of market
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
                "timestamp": time_remaining,
                "offer": runner.offer,
                "buyer": runner.buyer,
                "buyer_nickname": runner.user.nickname,
            }
            selling_runners.append(selling_runner)
    
    transactions = []
    if transaction_table:
        all_transactions = transaction_table.query.all()
        for transaction in all_transactions:
            transaction_dict ={
                "buyer": transaction.buyer_username,
                "seller": transaction.seller_username,
                "runner": transaction.runner_name,
                "amount": int(transaction.amount),
            }
            transactions.append(transaction_dict)

    return render_template(
        'market.html', 
        filters=filters, 
        runners_database=runners_database, 
        sellable_runners=sellable_runners, 
        selling_runners=selling_runners,
        transactions=transactions,
        active_page="market"
        )


@main.route("/sell-runner", methods=["POST"])
def sell_runner():
    if current_user.active_league == "global":
        user_runner = UserRunner.query.filter_by(user_username=current_user.username, runner_name=request.form.get("runner-name")).first()
        if user_runner:
            db.session.delete(user_runner)
            current_user.league_data.balance += user_runner.runner.price
            db.session.commit()
        else:
            return jsonify({"code": "errorr"}), 400
    else:
        user_runner_table = get_user_runner_table(get_user_league_id())

        user_runner = user_runner_table.query.filter_by(user_username=current_user.username, runner_name=request.form.get("runner-name")).first()
        if user_runner:
            user_runner.selling=True
            user_runner.offer=int(request.form.get("runner-price"))
            db.session.commit()
        else:
            return jsonify({"code": "errorr"}), 400
            
    return redirect(url_for('main.market'))


@main.route("/team", methods=['GET', 'POST'])
@login_required
def team():

    filters=["Categoria", "Punti", "Società", "Prezzo"]
    filter = ""

    id = get_user_league_id()


    user_runner_table=get_user_runner_table(id)
    owned_runners=db.session.query(user_runner_table).filter_by(user_username=current_user.username).all()


    if request.method=="POST":
        form_id = request.form.get("form_id")
        
        if form_id == "filter":
            filter = request.form.get("filter")
            

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


    if filter == "Categoria":
        runners_database_list = sorted(runners_database_list, key=lambda x: x["category"])    
    elif filter == "Punti":
        runners_database_list = sorted(runners_database_list, key=lambda x: x["points"])    
    elif filter == "Società":
        runners_database_list = sorted(runners_database_list, key=lambda x: x["society"])    
    elif filter == "Prezzo":
        runners_database_list = sorted(runners_database_list, key=lambda x: x["price"])    

    return render_template("team.html",
                           filters = filters, 
                           lineup_line1=lineup_line1, 
                           lineup_line2=lineup_line2, 
                           lineup_line3=lineup_line3, 
                           runners_database=runners_database_list,
                           active_page="team"
                           )


@main.route("/refresh-team", methods=["POST"])
def refresh_team():
    name = request.form.get("runner-name")
    number = request.form.get("number")

    user_runner_table = get_user_runner_table(get_user_league_id())
    
    old_runner = db.session.query(user_runner_table).filter(user_runner_table.user_username == current_user.username, user_runner_table.lineup == number).first()
    if old_runner: 
        old_runner.lineup = 0

    new_runner = db.session.query(user_runner_table).filter(user_runner_table.user_username == current_user.username, user_runner_table.runner_name == name).first()
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
