"""Flask app for starting server."""

from flask import Flask

app = Flask(__name__)


import lens_app.views
