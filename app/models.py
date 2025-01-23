from app import db
from datetime import datetime, timezone, timedelta
from flask_login import UserMixin, login_manager
from sqlalchemy.types import LargeBinary
from sqlalchemy import inspect, func
import random


class User(UserMixin, db.Model):
    __tablename__="user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    surname = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(120), unique=True, nullable=False)
    nickname = db.Column(db.String(80), nullable=False)
    password = db.Column(LargeBinary, nullable=False)


    is_validated = db.Column(db.Boolean, nullable=False, default=False)
    active_league = db.Column(db.String(30), nullable=False, default="global")


    runners = db.relationship("UserRunner", back_populates="user", cascade="all, delete")
    market = db.relationship("MarketTable", back_populates="user", cascade="all, delete")

    user_league = db.relationship('UserLeague', back_populates='user')
    
    league_data = db.relationship('LeagueData', back_populates='user', uselist=False, cascade="all, delete")


    @classmethod
    def get_by_username(username):
        return User.query.get(username)
    



class Runner(db.Model):
    __tablename__="runner"
    #id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, primary_key=True)
    society = db.Column(db.String(20), unique=False, nullable=False)
    category = db.Column(db.String(4), unique=False, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)

    plus_minus = db.Column(db.Integer, default=0)

    users = db.relationship("UserRunner", back_populates="runner", cascade="all, delete")
    market = db.relationship("MarketTable", back_populates="runner")




class UserRunner(db.Model):
    __tablename__="userRunner"
    user_username = db.Column(db.String(50), db.ForeignKey("user.username"), nullable=False, primary_key=True)
    runner_name = db.Column(db.String(50), db.ForeignKey("runner.name"), nullable=False, primary_key=True)
    lineup = db.Column(db.Integer, default=0)
    selling = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship('User', back_populates='runners')
    runner = db.relationship('Runner', back_populates='users')


class MarketTable(db.Model):
    __tablename__="markettable"
    id = db.Column(db.Integer, primary_key=True)
    runner_name = db.Column(db.String(50), db.ForeignKey("runner.name"), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    offer = db.Column(db.Integer, default=0)
    buyer = db.Column(db.String(30), db.ForeignKey("user.username"))

    user = db.relationship('User', back_populates='market')
    runner = db.relationship("Runner", back_populates="market")

class LeagueData(db.Model):
    __tablename__="leagueData"
    user_username = db.Column(db.String(50), db.ForeignKey("user.username"), nullable=False, primary_key=True)
    points = db.Column(db.Integer, default=0)
    balance = db.Column(db.Integer, default=10000000)

    user = db.relationship('User', back_populates='league_data')

class League(db.Model):
    __tablename__="leagues"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    user_league = db.relationship("UserLeague", back_populates="league")


class UserLeague(db.Model):
    __tablename__="userLeague"
    league_name = db.Column(db.String(50), db.ForeignKey("leagues.name"), nullable=False, primary_key=True)
    user_username = db.Column(db.String(50), db.ForeignKey("user.username"), nullable=False, primary_key=True)

    league = db.relationship('League', back_populates='user_league')
    user = db.relationship('User', back_populates='user_league')


def create_dynamic_market_model(league_id):
    # Nome dinamico per la classe
    class_name = f"LeagueMarket_{league_id}"
    table_name = f"league_{league_id}_market"

    # Verifica se la classe è già stata definita
    if class_name in globals():
        return globals()[class_name]

    # Definizione dinamica della classe
    model = type(
        class_name,  # Nome dinamico della classe
        (db.Model,),  # Classe base (eredita da db.Model)
        {
            "__tablename__": table_name,  # Nome della tabella
            "id": db.Column(db.Integer, primary_key=True),
            "runner_name": db.Column(db.String(50), db.ForeignKey("runner.name"), nullable=False),
            "timestamp": db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False),
            "offer": db.Column(db.Integer, default=0),
            "buyer": db.Column(db.String(30), db.ForeignKey("user.username")),
            # Relazioni
            "runner": db.relationship(
                "Runner",
                backref=db.backref(f"{table_name}_runner", cascade="all, delete"),
                foreign_keys=lambda: [model.runner_name],  # Riferimento corretto alla colonna
            ),
            "user": db.relationship(
                "User",
                backref=db.backref(f"{table_name}_market", cascade="all, delete"),
                foreign_keys=lambda: [model.buyer],  # Riferimento corretto alla colonna
            ),
        },
    )

    # Salva la classe in globals per riutilizzarla
    globals()[class_name] = model
    return model


def create_dynamic_user_runner_model(group_id):
    # Nome dinamico per la classe
    class_name = f"LeagueUserRunner_{group_id}"
    table_name = f"league_{group_id}_userrunner"

    # Verifica se la classe è già stata definita
    if class_name in globals():
        return globals()[class_name]

    # Definizione dinamica della classe
    model = type(
        class_name,  # Nome dinamico della classe
        (db.Model,),  # Classe base (eredita da db.Model)
        {
            "__tablename__": table_name,  # Nome della tabella
            "user_username": db.Column(db.String(50), db.ForeignKey("user.username"), nullable=False, primary_key=True),
            "runner_name": db.Column(db.String(50), db.ForeignKey("runner.name"), nullable=False, primary_key=True),
            "lineup": db.Column(db.Integer, default=0),
            "selling": db.Column(db.Boolean, nullable=False, default=False),
            "offer": db.Column(db.Integer, default=0),
            "buyer": db.Column(db.String(30), db.ForeignKey("user.username")),
            # Relazioni
            "user": db.relationship(
                "User",
                backref=db.backref(f"{table_name}_user", cascade="all, delete"),
                foreign_keys=lambda: [model.user_username],  # Riferimento corretto alla colonna
            ),
            "runner": db.relationship(
                "Runner",
                backref=db.backref(f"{table_name}_runner", cascade="all, delete"),
                foreign_keys=lambda: [model.runner_name],  # Riferimento corretto alla colonna
            ),
        },
    )

    # Salva la classe in globals per riutilizzarla
    globals()[class_name] = model
    return model


def create_dynamic_league_data_model(group_id):
    # Nome dinamico per la classe
    class_name = f"LeagueData_{group_id}"
    table_name = f"league_{group_id}_data"

    # Verifica se la classe è già stata definita
    if class_name in globals():
        return globals()[class_name]

    # Definizione dinamica della classe
    model = type(
        class_name,  # Nome dinamico della classe
        (db.Model,),  # Classe base (eredita da db.Model)
        {
            "__tablename__": table_name,  # Nome della tabella
            "user_username": db.Column(db.String(50), db.ForeignKey("user.username"), nullable=False, primary_key=True),
            "points": db.Column(db.Integer, default=0),
            "balance": db.Column(db.Integer, default=10000000),

            # Relazioni
            "user": db.relationship(
                "User",
                backref=db.backref(f"{table_name}_user", cascade="all, delete"),
                foreign_keys=lambda: [model.user_username],  # Riferimento corretto alla colonna
            ),
        },
    )

    # Salva la classe in globals per riutilizzarla
    globals()[class_name] = model
    return model




def create_dynamic_tables(id, user_username):
    print(user_username)

    # Creazione tabella dinamica per il mercato
    market_model = create_dynamic_market_model(id)
    if not inspect(db.engine).has_table(market_model.__tablename__):
        market_model.__table__.create(db.engine)

    # Creazione tabella dinamica per la relazione User-Runner
    user_runner_model = create_dynamic_user_runner_model(id)
    if not inspect(db.engine).has_table(user_runner_model.__tablename__):
        user_runner_model.__table__.create(db.engine)

    league_data_model = create_dynamic_league_data_model(id)
    if not inspect(db.engine).has_table(league_data_model.__tablename__):
        league_data_model.__table__.create(db.engine)

    return

def populate_market(id):
    market_table = create_dynamic_market_model(id)
    all_market_runners = db.session.query(Runner).order_by(func.random()).limit(16).all()
    i=-14
    current_time=datetime.now(timezone.utc)
    for runner in all_market_runners:
        timestamp=current_time + timedelta(hours=i)
        new_market_runner = market_table(
            runner_name=runner.name,
            timestamp=timestamp
        )
        db.session.add(new_market_runner)

        i+=1
    db.session.commit()

def create_default_team(id, user_username):
    user_runner_table = create_dynamic_user_runner_model(id)
    market_table = create_dynamic_market_model(id)

    market_names_subquery = db.session.query(market_table.runner_name).subquery()

    # Estrai tutti i corridori non presenti nel mercato
    available_runners = (
        db.session.query(Runner)
        .filter(Runner.name.notin_(market_names_subquery))
        .all()
    )

    for _ in range(100000):
        random.shuffle(available_runners)
        selected_runners = random.sample(available_runners, 12)
        if 4900000 < sum(runner.price for runner in selected_runners) < 5100000:
            print(sum(runner.price for runner in selected_runners))
            break
    else:
        raise ValueError("Impossibile trovare una combinazione valida")

    for runner in selected_runners:
        new_relation = user_runner_table(
            user_username=user_username,
            runner_name=runner.name
        )
        db.session.add(new_relation)
    db.session.commit()




