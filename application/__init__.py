from flask import Flask
import os
from application.database.data import data

#from model import db as database

from flask_sqlalchemy_core import FlaskSQLAlchemy

if os.environ.get("DATABASE_URL"):
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
else:
    DATABASE_URL = "sqlite:///vertais_data.db"
    
print(DATABASE_URL)
database = FlaskSQLAlchemy(DATABASE_URL)
db = data(database.get_engine(), create=True)
def create_app(config):    
    print("creating app")
    app = Flask(__name__)

    #db

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    

    
    #db.init_app(app) 
    
        
    

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

    with app.app_context():
        from application import views as views1, forms as forms1
        from application.teacher_views import tasks
        from application.auth import views, forms
        from application.teacher_views import overview

    return app