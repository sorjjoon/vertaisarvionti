

from flask import Flask
import os
    
app = Flask(__name__)



# login
from flask_login import LoginManager

app.config["SECRET_KEY"] = os.urandom(32)

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login_auth"
login_manager.login_message = "Please login to use this functionality."


from app import views
