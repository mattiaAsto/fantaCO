from app.models import User, Runner, MarketTable, UserRunner
from app import db
from sqlalchemy.sql.expression import func
from run import app as global_app
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import time, random
import atexit


def check_obsolete_db():
    with global_app.app_context():
        current_time = datetime.now(ZoneInfo("Europe/Zurich"))

        last = MarketTable.query.order_by(MarketTable.id.desc()).first()
        last_created_time = last.timestamp

        if last_created_time.tzinfo is None:
                last_created_time = last_created_time.replace(tzinfo=ZoneInfo("Europe/Zurich"))

        if last_created_time + timedelta(hours=1) < current_time:
            return True
        else:
            return False
    
def renovate_obsolete_db(): #if db is obsolete update it
    with global_app.app_context():
        row_count = db.session.query(MarketTable).count()
        if row_count == 0:
            print("No rows to renovate.")
            return
        
        current_time = datetime.now(ZoneInfo("Europe/Zurich"))
        try:
            for i in range(row_count): #update every row of db one by one
                first = MarketTable.query.order_by(MarketTable.id.asc()).first()
                last = MarketTable.query.order_by(MarketTable.id.desc()).first()

                last_created_time = last.timestamp.replace(tzinfo=ZoneInfo("Europe/Zurich"))

                #if it is the first iteration the timestamp must be current time but older by the number of rows
                #this way all the new record will be more recent util the last is created at current time
                new_timestamp = current_time - timedelta(hours=row_count - 1) if i == 0 else last_created_time + timedelta(hours=1)
                
                subquery = db.session.query(MarketTable.runner_name)
                new_runner = Runner.query.filter(~Runner.name.in_(subquery)).order_by(func.random()).first()
                if new_runner:
                    new_market_runner = MarketTable(
                        runner_name=new_runner.name,
                        timestamp=new_timestamp
                    )
                    db.session.add(new_market_runner)
                
                #remove the first row of db
                if first:
                    db.session.delete(first)
                # must commit, this way the next iteration uses the right first and last rows
                db.session.commit()

            print("Database renovation completed.")
        except Exception as e:
            db.session.rollback()
            print(f"Error renovating database: {e}")

def refresh_market():
    with global_app.app_context():
        current_time = datetime.now(ZoneInfo("Europe/Zurich"))

        first = MarketTable.query.order_by(MarketTable.id.asc()).first()
        last = MarketTable.query.order_by(MarketTable.id.desc()).first()

        created_time = first.timestamp
        last_created_time = last.timestamp

        if created_time.tzinfo is None:
            created_time = created_time.replace(tzinfo=ZoneInfo("Europe/Zurich"))
        if last_created_time.tzinfo is None:
            last_created_time = last_created_time.replace(tzinfo=ZoneInfo("Europe/Zurich"))

        row_count = db.session.query(MarketTable).count()

        if created_time < current_time - timedelta(hours=1 * row_count):
            
            new_timestamp = last_created_time + timedelta(hours=1)

            subquery = db.session.query(MarketTable.runner_name)
            new_runner = Runner.query.filter(~Runner.name.in_(subquery)).order_by(func.random()).first()
            if new_runner:
                new_market_runner = MarketTable(
                    runner_name=new_runner.name,
                    timestamp=new_timestamp
                )
                db.session.add(new_market_runner)

            removable_runner = MarketTable.query.first()
            if removable_runner:
                db.session.delete(removable_runner)

            db.session.commit()
            print("Refresh completato.")
        else:
            print(f"No refresh")

def price_calculations():
    with global_app.app_context():
        
        users_number=db.session.query(User).count()
        runners=Runner.query.all()

        for runner in runners:
            price=runner.price
            plus_minus=runner.plus_minus

            reduction_factor=0.2
            variation_factor=plus_minus/users_number #calculate the percentage of users buying the runner

            effective_variation_factor=(variation_factor*reduction_factor)+1 #reduce te percentage with the reduction factor and then scale it ut to 1+ to make it a percentage greater than 100%

            price=price*effective_variation_factor #calculate new price

            runner.price=price
            runner.plus_minus=0

            db.session.commit()


def start_scheduler():
    
    #check if the db is obsolete, in case upload it, this should just happen once in production, when the program is launched
    if check_obsolete_db():
        renovate_obsolete_db()

    #scheduler for market refreshing
    scheduler = BackgroundScheduler()
    from .scheduler import refresh_market
    scheduler.add_job(refresh_market, "interval", hours=1)
    scheduler.add_job(price_calculations, "interval", minutes=20)
    scheduler.start()


    atexit.register(lambda: scheduler.shutdown()) 