
import os as os
from flask import Flask

    
app = Flask(__name__)

#db
from flask_sqlalchemy import SQLAlchemy
from application.database.data import data

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
if os.environ.get("HEROKU"):
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
    app.config["SQLALCHEMY_ECHO"] = True
database = SQLAlchemy(app)
db = data(database.engine)

# login
from flask_login import LoginManager

app.config["SECRET_KEY"] = os.urandom(32)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login_auth"
login_manager.login_message = "Please login to use this functionality."

from application.auth import account

#upload
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), "files")


@login_manager.user_loader
def load_user(user_id):
    return db.get_user_by_id(user_id)

from application import views as views1, forms as forms1
from application.teacher_views import tasks
from application.auth import views, forms
