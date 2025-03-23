import json
import requests
from bs4 import BeautifulSoup
import sqlite3

#global varibles
global MAX_PRICE, MIN_PRICE
MAX_PRICE=850000
MIN_PRICE=60000

#common variables
LIST_OF_CATEGORIES=["H10","H12","H14","H16","H18","HAL","HAM","HAK","H40","H50","H60","H70","D10","D12","D14","D16","D18","DAL","DAK","D40","D50","D60"]
BASE_URL="https://www.asti-ticino.ch/co/index.php?folder=tmo&main=classifica&cat="
RUNNERS_DATABASE_PATH = "sources/runners_database.json"
PLAYERS_DATABASE_PATH = "sources/players_database.json"
LEAGUE_DATABASE_PATH = "sources/league_database.json"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
}

#functions
def load_database(path):
    try:
        with open(path) as f:
            database = json.load(f)
            return database
    except:
        return{}
    
def upload_database(path, database):
    with open(path, "w") as f:
        json.dump(database, f)
        return 
    
def calculate_price(points, total):
    max_limit=0.90*total
    min_limit=0.15*total
    points=int(points)
    if points>max_limit:
        return 850000
    elif points<min_limit:
        return 60000
    else:
        price=MIN_PRICE+((points-min_limit)/(max_limit-min_limit)*(MAX_PRICE-MIN_PRICE))
        return round(price)

def first_scraping():
    upload_database(RUNNERS_DATABASE_PATH, {})
    all_names=[]
    all_prices=[]

    for category in LIST_OF_CATEGORIES:
        #print(category)

        url=BASE_URL+category
        
        request=requests.get(url, headers=headers)
        soup = BeautifulSoup(request.text, 'html.parser')

        table=soup.find("table", class_="class tabella_uff")

        rows=table.find_all("tr")

        for index, row in enumerate(rows):
            if index == 0:  # Salta l'intestazione
                continue
            cols = row.find_all("td")
            if len(cols) > 0:

                runners_database=load_database(RUNNERS_DATABASE_PATH)

                second_column_data=cols[1].text.strip()
                fourth_column_data=cols[3].text.strip()
                last_column_data=cols[len(cols)-1].text.strip()

                all_names.append(second_column_data)
                if all_names.count(second_column_data)!=1:

                    double_runner_info=runners_database[second_column_data]
                    if int(double_runner_info["points"])>int(last_column_data):
                        continue

                new_runner_name=second_column_data
                new_runner_data={
                    "name":second_column_data,
                    "society":fourth_column_data,
                    "category":category,
                    "points":last_column_data,
                    "price":calculate_price(last_column_data, 8000)
                }
                all_prices.append(calculate_price(last_column_data, 8000))
                

                runners_database[new_runner_name]=new_runner_data
                upload_database(RUNNERS_DATABASE_PATH, runners_database)