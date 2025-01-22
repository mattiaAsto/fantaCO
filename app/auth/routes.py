from flask import render_template, request, redirect, url_for, session, current_app, flash, jsonify
from flask_mail import Message
from flask_login import login_user, logout_user
from . import auth
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



#common variables

#functions
def check_username_unique(username):
    user=User.query.filter_by(username=username).first()
    if user:
        return False
    else:
        return True

def check_password(password): #returns "Okay" if all yes_... are satisfied, else it returns a string with an error
    numbers="0123456789"
    yes_numbers=any((c in numbers)for c in password)

    specials="@#_-%&"
    yes_specials=any((c in specials)for c in password)

    yes_upper=any(c.isupper() for c in password)

    check_only_wanted=[c for c in password if c not in specials]
    check_only_wanted=[c for c in check_only_wanted if c not in numbers]
    check_only_wanted="".join(check_only_wanted)
    check_only_wanted=check_only_wanted.isalpha()
    
    
    message=""
    if not yes_numbers:
        message="deve contenere numeri"
    elif not yes_specials:
        message=f"Deve contenere almeno uno di questi caratteri speciali: {specials}"
    elif not yes_upper:
        message="Deve contenere almeno una maiuscola"
    elif not check_only_wanted:
        message=f"I caratteri speciali consentiti sono: {specials}"
    else:
        message="Okay"
    #return message
    return "Okay"
    
def create_team(user):

    random_runners = db.session.query(Runner).order_by(func.random()).limit(12).all()

    for runner in random_runners:
        user_runner_new_relation=UserRunner(user_username=user.username, runner_name=runner.name)
        db.session.add(user_runner_new_relation)
    
    db.session.commit()
        
        


@auth.route("/prova/<password>")
def prova(password):
    print(password)
    return str(check_password(password))
    


#routes
@auth.route("/login", methods=['GET', 'POST']) #database reloaded
def login():

    login_error_message=""

    if request.method== "POST":
        username=request.form["username"]
        password=request.form["password"]

        user=User.query.filter_by(username=username).first()

        if user and not user.is_validated:
            login_error_message="Prima di accedere devi verificare il tuo account"
        elif user and  bcrypt.checkpw(password.encode('utf-8'), user.password):
            login_user(user)
            return redirect(url_for("main.home"))
        else:
            login_error_message="Nome utente o password non corretti"

    
    return render_template("login.html", login_error_message=login_error_message) 



@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))



@auth.route("/register", methods=['GET', 'POST']) #database reloaded
def register():

    login_error_message=""
    
    if request.method== "POST":
        print("post")

        name=request.form["name"]
        surname=request.form["surname"]
        username=request.form["username"]
        nickname=request.form["nickname"]
        password=request.form["password"]
        password2=request.form["password2"]

        hashed_password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user=User(
            name=name,
            surname=surname,
            username=username,
            nickname=nickname,
            password=hashed_password,
        )
        db.session.add(new_user)

        new_league_data = LeagueData(
            user_username=username, 
            balance=10000000, 
            points=0
            )
        db.session.add(new_league_data)

        db.session.commit()

        return redirect(url_for("auth.send_email", address=username, name=name))
    
    return render_template("register.html", login_error_message=login_error_message) 


@auth.route("/validate_registration", methods=['POST'])
def validate_registration():
    print("validation")
    new_username = request.form.get("username")

    password = request.form.get("password1")
    password2 = request.form.get("password2")

    password_checked=False
    if check_password(password) == "Okay":
        password_checked=True

    if not check_username_unique(new_username):
        return jsonify({"error": "Nome utente già esistente"}), 400
     
    elif password != password2:
        return jsonify({"error":"Le due password non corrispondono"}), 400

    elif not password_checked:
        return jsonify({"error": check_password(password)}), 400
    
    return jsonify({"success": "Nome utente e password verificati"}), 200




@auth.route("/send_verification_email/<address>/<name>")
def send_email(address, name):
    serializer = current_app.url_serializer
    token = serializer.dumps(address, salt="email-confirmation")
    verify_url = url_for("auth.verify_email", token=token, _external=True)

    msg = Message('Verifica il tuo account', recipients=[address])
    msg.body = f'Clicca sul link per verificare il tuo account: {verify_url}'

    msg = Message(
        subject="Verifica il tuo account",
        recipients=[address],
        body=f"Ciao {name} ci sei quasi, utilizza il link che trovi di seguito per verificare il tuo indiizzo E-Mail e completare la creazione del tuo account su FantaCO \n Link: {verify_url} \n Per domande e informazioni o in caso di mancato funzionamento del link ti preghiamo di scrivere a: ____"
    )
    try:
        mail.send(msg)
    except Exception as e:
        print(e)
        print('Errore durante l’invio dell’email. Riprova più tardi.', 'danger')
    return redirect(url_for("auth.auth_interaction", case="wait_verification"))



@auth.route("/auth_interaction/<case>")
def auth_interaction(case):
    if case == "wait_verification":
        message="Apri il link nella tua casella di posta per verificare la tua E-Mail"
        return render_template("auth_interaction.html", data=message)
    elif case == "redirect_post_verification":
        message="Il tuo account è stato verificato con successo, ritorna alla pagina di login"
        link=url_for('auth.login')
        data2="Vai al login"
        return render_template("auth_interaction.html", data=message, data2=data2, link=link)


@auth.route("/verify/<token>")
def verify_email(token):
    serializer=current_app.url_serializer
    email = serializer.loads(token, salt='email-confirmation', max_age=3600)

    verification_succesful=False

    if email:
        user = User.query.filter_by(username=email).first()
        if user:
            if user.is_validated:
                print("gia verificato")
            else:
                user.is_validated=True
                db.session.commit()
                print("verificata con successo")
        else:
            print("utente non trovato")
    else:
        print("Token di verifica invalido o scaduto")

    create_team(user)
    return redirect(url_for("auth.auth_interaction", case="redirect_post_verification"))
    