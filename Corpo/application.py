import os
import secrets

from flask import Flask
from flask_cors import CORS

from database import close_db, init_database

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = os.environ.get(
    "FLASK_SECRET_KEY"
) or secrets.token_hex(32)

init_database()
app.teardown_appcontext(close_db)

import views
