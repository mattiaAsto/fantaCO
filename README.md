# fantaCO

FantaCO is flask-based web-service that works as a sport game.

It is like a fantacalcio but for Orienteering.

Currently it is still a work in progress, all the database and info of runners come from the local chanmpionship in Ticino, CH.

## Geting started

Use:
```bash
pip install -r requirements.txt
```
to install all the packages needed to run the project.

## Environement variables
The file "variables.env.exapmle" is the blueprint for all the .env variables needed to run the program.

### Database variables

If you already have a postgresql database set your .env variables accordigly to the .env.exapmle file and make sure to remove the "DB_COMPLETE_URL" variable from your file.

If you plan to use a MySql database please provide the full url to your database in the variable "DB_COMPLETE_URL" and leave empty the other "DB_" variables.

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
Giunicor feature will soon be added !

## Support, feedback, suggestions and debugging
I created this project with zero experience in programing and also almost zero classroom learning.

Al my knowledge is based on yt videos and the help of chatGPT so please accept my newbie mistakes and don't be afraid to point them out and provide a solution.

Contact me at astorimattia05@gmail.com if you have some suggestions or debugging solutions, i'm open to learning !!