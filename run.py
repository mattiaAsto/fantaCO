from app import create_app
from datetime import datetime, timezone
from livereload import Server
import os
import logging




app = create_app()

system=1


if __name__ == '__main__':
    print("Refreshed...")

    #lazy import to avoid circular imports
    from app.scheduler import start_scheduler
    start_scheduler()
    
    if system == 1:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        app.run(debug=True, port='8000')
    else:
        server = Server(app)
        # Aggiungi qui i file o directory che vuoi monitorare
        server.watch('app/main/static/*.css')  # Monitora i file CSS nella cartella static/css
        server.watch('app/main/templates/*.html')  # Monitora i file HTML nei templates
        server.serve(debug=True, port=8000)