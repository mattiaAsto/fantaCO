import requests
from app import db
from bs4 import BeautifulSoup

LIST_OF_CATEGORIES=["H10","H12","H14","H16","H18","HAL","HAM","HAK","H40","H50","H60","H70","D10","D12","D14","D16","D18","DAL","DAK","D40","D50","D60"]
BASE_URL="https://www.asti-ticino.ch/co/index.php?folder=tmo&main=classifica&cat="

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0',
}

all_url = [BASE_URL+category for category in LIST_OF_CATEGORIES]

for url in all_url:

    response = requests.get(url, headers=headers)
    data = BeautifulSoup(response.text, 'html.parser')

    table=data.find("table", class_="class tabella_uff")
    rows = table.find_all("tr")

    table_header = rows[0]
    

