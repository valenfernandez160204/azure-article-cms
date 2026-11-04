import os
from urllib.parse import quote_plus


basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Azure Blob Storage
    BLOB_ACCOUNT = os.environ.get("BLOB_ACCOUNT")
    BLOB_STORAGE_KEY = os.environ.get("BLOB_STORAGE_KEY")
    BLOB_CONTAINER = os.environ.get("BLOB_CONTAINER")

    # Azure SQL Database
    SQL_SERVER = os.environ.get("SQL_SERVER")
    SQL_DATABASE = os.environ.get("SQL_DATABASE")
    SQL_USER_NAME = os.environ.get("SQL_USER_NAME")
    SQL_PASSWORD = os.environ.get("SQL_PASSWORD")

    ODBC_CONNECTION_STRING = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER=tcp:{SQL_SERVER},1433;"
        f"DATABASE={SQL_DATABASE};"
        f"UID={SQL_USER_NAME};"
        f"PWD={SQL_PASSWORD};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    SQLALCHEMY_DATABASE_URI = (
        "mssql+pyodbc:///?odbc_connect="
        + quote_plus(ODBC_CONNECTION_STRING)
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Microsoft authentication
    CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
    CLIENT_ID = os.environ.get("CLIENT_ID")

    AUTHORITY = "https://login.microsoftonline.com/common"
    REDIRECT_PATH = "/getAToken"
    SCOPE = ["User.Read"]

    # Token cache stored in the server-side session
    SESSION_TYPE = "filesystem"