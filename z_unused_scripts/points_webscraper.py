import json
import requests
from bs4 import BeautifulSoup
import sqlite3

#global varibles

#common variables
LIST_OF_CATEGORIES=["H10","H12","H14","H16","H18","HAL","HAM","HAK","H40","H50","H60","H70","D10","D12","D14","D16","D18","DAL","DAK","D40","D50","D60"]
BASE_URL="https://www.asti-ticino.ch/co/resultate/archivio/2024/"
POINTS_PATH = "sources/points.json"

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
    

def scraping():
    upload_database(POINTS_PATH, {})
    
    all_url = [f"{BASE_URL}{category}.html" for category in LIST_OF_CATEGORIES]
    
    for url in all_url:
        print(url)
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find("table", class_="class")

        rows=table.find_all("tr")
        
        for index, row in enumerate(rows):
            db = load_database(POINTS_PATH)

            if index == 0:
                continue

            cols = row.find_all("td")

            races = len(cols)-5

            model = {"season": 2024, "average": 0,}
            average_total = 0
            average_counter = 0
        
            for i in range(len(cols)):
                if i == 0 or i == 1 or i == 2 or i == 3 or i == len(cols)-1:
                    continue
                else:
                    value = cols[i].text.strip()
                    if value == "-":
                        model[f"{str(i-3)}.TMO"] = None
                    else:
                        model[f"{str(i-3)}.TMO"] = int(value)
                        average_total += int(value)
                        average_counter += 1
            
            model["average"] = average_total/average_counter
                    
            db[cols[1].text.strip()]=model
            upload_database(POINTS_PATH, db)


                    

                    



if __name__ == "__main__":
   scraping()
    