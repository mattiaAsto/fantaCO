from app import create_app, db
from datetime import datetime, timezone
from livereload import Server
import os
import logging
import json
from app.models import *
from z_unused_scripts.asti_webscraper import RUNNERS_DATABASE_PATH as runners_path
from z_unused_scripts.asti_webscraper import LEAGUE_DATABASE_PATH as league_path
from z_unused_scripts.points_webscraper import POINTS_PATH
from datetime import datetime, timedelta, timezone
from sqlalchemy import MetaData
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import time
import os
import bcrypt





app = create_app()

# Leggi i dati dal file JSON
with open(runners_path, 'r') as file:
    data = json.load(file)

with open(league_path, 'r') as file:
    market = json.load(file)

with open(POINTS_PATH, 'r') as file:
    points_table = json.load(file)

migrate=True
if migrate:
    with app.app_context():

        load_dotenv()
        
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
        current_time=datetime.now(ZoneInfo("Europe/Zurich"))
        for runner in all_market_runners:
            timestamp=current_time + timedelta(hours=i)
            new_market_runner = MarketTable(
                runner_name=runner,
                timestamp=timestamp
            )
            db.session.add(new_market_runner)

            i+=1

        admin_password = str(os.getenv("ADMIN_PASSWORD", "1"))            
        hashed_password=bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
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

        admin2_password = str(os.getenv("ADMIN2_PASSWORD", "1"))            
        hashed_password=bcrypt.hashpw(admin2_password.encode('utf-8'), bcrypt.gensalt())
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

        global__password = str(os.getenv("GLOBAL__PASSWORD", "1"))            
        hashed_password=bcrypt.hashpw(global__password.encode('utf-8'), bcrypt.gensalt())
        global_=User(
            name="FantaCO",
            surname="FantaCO",
            username="FantaCO",
            nickname="FantaCO",
            password=hashed_password,
            is_validated=True
        )
        db.session.add(global_)
        league_data = LeagueData(user_username="FantaCO")
        db.session.add(league_data)


        db.session.commit()

        all_points_runner = list(points_table.keys())
        for point_runner in all_points_runner:
            all_points_dict = points_table[point_runner]
            all_points_dict_rows = len(list(all_points_dict.keys()))-2
            all_indexes = [f"{number}.TMO" for number in range(1, all_points_dict_rows+1)]
            for index in all_indexes:
                new_points = RunnerPoints(
                    runner_name = point_runner,
                    race = index,
                    season = all_points_dict["season"],
                    points = all_points_dict[index],
                )
                db.session.add(new_points)
        db.session.commit()
        print("Dati migrati con successo!")

skip_scheduler = os.getenv("NEED_SKIP_SCHEDULER", False)

if not skip_scheduler:
    #lazy import to avoid circular imports
    from app.scheduler import start_scheduler
    start_scheduler()
else:
    print("skipped scheduler")
    

system=1

host = os.getenv("HOST", "127.0.0.1")
port = int(os.getenv("PORT", 8000))

if __name__ == '__main__':
    print("Refreshed...")

    
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
