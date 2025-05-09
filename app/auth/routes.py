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
from z_unused_scripts import asti_webscraper
import bcrypt
import time
import random



#common variables
SOCIETIES = ["ASCO", "CO AGET", "CO UTOE", "GOLD", "GOV", "O-92", "SCOM", "UNITAS"]

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
    return message
    #return "Okay"
    
    


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
            next_url=request.args.get("next")
            return redirect(next_url or url_for("main.home"))
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

        name=request.form["name"]
        surname=request.form["surname"]
        username=request.form["username"]
        nickname=request.form["nickname"]
        password=request.form["password"]
        password2=request.form["password2"]
        society=request.form["society"]

        hashed_password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user=User(
            name=name,
            surname=surname,
            username=username,
            nickname=nickname,
            password=hashed_password,
            society=society,
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
    
    return render_template("register.html", login_error_message=login_error_message, societies=SOCIETIES) 


@auth.route("/validate_registration", methods=['POST'])
def validate_registration():
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




@auth.route("/send_verification_email/<address>/<name>", methods=["GET", "POST"])
def send_email(address, name):
    #if not name:
    #    name = "caro orientista," IT IS ALREADY IN THE HTML TEMPLATE
    if request.method == "POST":
        address = request.form.get("correct-address")
        print(address)
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
    return redirect(url_for("auth.auth_interaction", case="wait_verification", address=address))



@auth.route("/auth_interaction/<case>/<address>")
def auth_interaction(case, address):
    if not address:
        address=""

    if case == "wait_verification":
        
        return render_template("auth_interaction.html", case=1, address=address)
    
    elif case == "redirect_post_verification":

        return render_template("auth_interaction.html", case=2)

    elif case == "recover_address":

        return render_template("")

@auth.route("/verify/<token>")
def verify_email(token):
    serializer=current_app.url_serializer
    email = serializer.loads(token, salt='email-confirmation', max_age=3600)

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

    create_default_team(0, email)
    return redirect(url_for("auth.auth_interaction", case="redirect_post_verification", address="not_needed"))
    

@auth.route("/recover_email/<address>")
def recover_email(address):
    return render_template("recover.html", address=address)



@auth.route("/todo")
def todo():
    return f"Non ancora completato, arriverà a breve"