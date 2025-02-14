# fantaCO

FantaCO is flask-based web-service that works as a sport game.

It is like a fantacalcio but for Orienteering.

Currently it is still a work in progress, all the database and info of runners come from the local chanmpionship in Ticino, CH.

The idea is that this app is modular, this way everyone can create his own fanta-.... bay providing some base json data required for initalising athletes.

## Geting started

Use:
```bash
pip install -r requirements.txt
```
to install all the packages needed to run the project.

## Data imports
Currently the sources folder has 4 .json files:
"league_database": contains the first structure of the global market, requires 16 athletes names.
"runners_database": containes al the infos about athletes.
"players_database" currently uneuseful.
"runner_points": contains all the point made in the previous races of the season by athletes.

## Other customizations
In the file run.py check the part in:
```python
migrate = True
if migrate:
  ...
```
To customize the default users you need to create.
Currently admin, admin2 and fantaco are created, the first two needed for testing and the last to manage some buying and selling operations in the market.

!!! I WILL SOON ADD ADMIN PASSWORDS IN THE .ENV FILE !!!


## Environement variables
The file "variables.env.example" is the blueprint for all the .env variables needed to run the program.

### Database variables
Paster in the DB_COMPLETE_URL the url of your database, it must be a database supported by ```sqlalchemy```.

### Host and port
Without any "HOST" and "PORT" variables provided the page runs in 127.0.0.1:8000.

Add "HOST" and "PORT" to the .env file to control which host and port the page runs on.

### Flask-mail variables
All the MAIL_... varibles are needed to config Flask-mail module

### Cache variables
The program uses Flask-caching in some routes.

Set the cache-type and the default timeoute to your preference.

## Launch
To finally launch the program use the command:
```bash
python run.py
```
If you need production launch use:
```bash
gunicorn -b 0.0.0.0:5000 -w 1 run:app
```

## Support, feedback, suggestions and debugging
I created this project with zero experience in programing and also almost zero classroom learning.

Al my knowledge is based on yt videos and the help of chatGPT so please accept my newbie mistakes and don't be afraid to point them out and provide a solution.

Contact me at astorimattia05@gmail.com if you have some suggestions or debugging solutions, i'm open to learning !!
