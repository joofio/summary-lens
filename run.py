import logging
import os
from logging.handlers import RotatingFileHandler


from lens_app import app
from lens_app.customJsonify import FhirJSONProvider

if not app.debug:
    # if app.debug:
    if not os.path.exists("logs"):
        try:
            os.mkdir("logs")
        except FileExistsError:
            print("The 'logs' directory already exists.")
    file_handler = RotatingFileHandler(
        "logs/lens-summary.log", maxBytes=10240 * 1024, backupCount=10
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    
    app.json = FhirJSONProvider(app)

if __name__ == "__main__":
    # print("runnn")
    app.run(debug=True, host="0.0.0.0", port=5005)
