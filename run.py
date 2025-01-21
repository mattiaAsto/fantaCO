from app import create_app, db
from datetime import datetime, timezone
from livereload import Server
import os
import logging

import json
from app.models import Runner, MarketTable, User
from asti_webscraper import RUNNERS_DATABASE_PATH as runners_path
from asti_webscraper import LEAGUE_DATABASE_PATH as league_path
from datetime import datetime, timedelta, timezone
from sqlalchemy import MetaData
import time
import os
import bcrypt





app = create_app()

# Leggi i dati dal file JSON
with open(runners_path, 'r') as file:
    data = json.load(file)

with open(league_path, 'r') as file:
    market = json.load(file)
    
with app.app_context():
    meta = MetaData()
    meta.reflect(bind=db.engine)
    meta.drop_all(bind=db.engine)

    db.create_all()

    # Aggiungi i runner al database
    all_runners=list(data.keys())
    for runner in all_runners:
        runner_data=data[runner]
        new_runner = Runner(
            name=runner_data['name'],
            society=runner_data["society"],
            category=runner_data["category"],
            points=runner_data["points"],
            price=runner_data["price"]    
        )
        db.session.add(new_runner)


    all_market_runners=market["market_runners"]
    i=-15
    current_time=datetime.now(timezone.utc)
    for runner in all_market_runners:
        timestamp=current_time + timedelta(hours=i)
        new_market_runner = MarketTable(
            runner_name=runner,
            timestamp=timestamp
        )
        db.session.add(new_market_runner)

        i+=1

    # Aggiungi gli utenti al database
    """ for user_data in data['users']:
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            team_id=user_data['team_id']
        )
        db.session.add(user) """

    hashed_password=bcrypt.hashpw("1".encode('utf-8'), bcrypt.gensalt())

    admin=User(
        name="Admin",
        surname="Admin",
        username="admin",
        nickname="ADMIN",
        password=hashed_password,
        points=0,
        balance=10000000,
        is_validated=True
    )

    db.session.add(admin)

    db.session.commit()
    print("Dati migrati con successo!")

system=1


if __name__ == '__main__':
    print("Refreshed...")

    #lazy import to avoid circular imports
    from app.scheduler import start_scheduler
    start_scheduler()
    
    if system == 1:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        app.run(host='0.0.0.0', debug=False)
    else:
        server = Server(app)
        # Aggiungi qui i file o directory che vuoi monitorare
        server.watch('app/main/static/*.css')  # Monitora i file CSS nella cartella static/css
        server.watch('app/main/templates/*.html')  # Monitora i file HTML nei templates
        server.serve(debug=True, port=8000)
