"""
The Flask application package.
"""

import logging
import sys

from flask import Flask, request
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix


app = Flask(__name__)
app.config.from_object(Config)

# Trust the proxy headers sent by Azure App Service.
# This allows Flask to recognize the original HTTPS request and host.
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1
)

# Configure logging for Azure App Service Log Stream.
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

# Configure server-side sessions.
Session(app)

# Configure the database.
db = SQLAlchemy(app)

# Configure Flask-Login.
login = LoginManager(app)
login.login_view = "login"
login.login_message = "Please sign in to access this page."


@app.before_request
def log_proxy_information():
    """
    Log the effective scheme and forwarded headers.

    This helps verify that Azure App Service is forwarding the
    original HTTPS request correctly.
    """
    if request.path == "/login":
        app.logger.info(
            "Login request: scheme=%s, host=%s, "
            "X-Forwarded-Proto=%s, X-Forwarded-Host=%s",
            request.scheme,
            request.host,
            request.headers.get("X-Forwarded-Proto"),
            request.headers.get("X-Forwarded-Host")
        )


# Import routes after app, database and login manager initialization.
import FlaskWebProject.views