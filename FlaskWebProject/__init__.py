"""
The flask application package.
"""

import logging
import sys

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session


app = Flask(__name__)
app.config.from_object(Config)

# Configure application logging for Azure App Service
app.logger.setLevel(logging.INFO)

log_formatter = logging.Formatter(
    "%(asctime)s %(levelname)s: %(message)s"
)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(log_formatter)

app.logger.handlers.clear()
app.logger.addHandler(stream_handler)
app.logger.propagate = False

Session(app)

db = SQLAlchemy(app)

login = LoginManager(app)
login.login_view = "login"
login.login_message = "Please sign in to access this page."

import FlaskWebProject.views