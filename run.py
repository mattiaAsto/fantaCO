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
