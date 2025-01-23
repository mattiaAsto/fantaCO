from app import create_app, db
from datetime import datetime, timezone
from livereload import Server
import os
import logging
import json
from app.models import *
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

migrate=False
if migrate:
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
        i=-14
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
            is_validated=True
        )

        db.session.add(admin)

        league_data = LeagueData(user_username="admin")

        db.session.add(league_data)


        hashed_password=bcrypt.hashpw("1".encode('utf-8'), bcrypt.gensalt())

        admin=User(
            name="Admin2",
            surname="Admin2",
            username="admin2",
            nickname="ADMIN2",
            password=hashed_password,
            is_validated=True
        )

        db.session.add(admin)

        league_data = LeagueData(user_username="admin2")

        db.session.add(league_data)

        db.session.commit()
        print("Dati migrati con successo!")

system=1

host = os.getenv("HOST", "127.0.0.1")
port = int(os.getenv("PORT", 8000))

if __name__ == '__main__':
    print("Refreshed...")

    #lazy import to avoid circular imports
    from app.scheduler import start_scheduler
    start_scheduler()
    
    if system == 1:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        app.run(host=host, port=port, debug=True)
    else:
        server = Server(app)
        # Aggiungi qui i file o directory che vuoi monitorare
        server.watch('app/main/static/*.css')  # Monitora i file CSS nella cartella static/css
        server.watch('app/main/templates/*.html')  # Monitora i file HTML nei templates
        server.serve(debug=True, port=8000)
