from flask import Flask
import os
from application.database.data import data

#from model import db as database

#from flask_sqlalchemy_core import FlaskSQLAlchemy
from flask_sqlalchemy import SQLAlchemy

    

sql_alchemy_db = SQLAlchemy()

def create_app(config):    
    print("creating app, given config "+str(config))
    app = Flask(__name__)
    global db
    #db

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if os.environ.get("UNIT_TEST"):
        print("unit test detected, echoing sql")
        app.config["SQLALCHEMY_ECHO"] = True
    else:
        app.config["SQLALCHEMY_ECHO"] = False
    
    if config =="NET_TEST":
        print("network test detected, using in memory")
        DATABASE_URL = "sqlite://"
    elif os.environ.get("DATABASE_URL"):
        DATABASE_URL = os.environ.get("DATABASE_URL")
        print("database url found")
        print(DATABASE_URL)
    
    else:
        
        DATABASE_URL = "sqlite:///vertais_data.db"
        print("database url not found, using "+DATABASE_URL)

    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    sql_alchemy_db.init_app(app)
    with app.app_context():

        if config=="DATA_TEST":
            data.drop_all(sql_alchemy_db.get_engine())

        db = data(sql_alchemy_db.get_engine(), create=True)

    # login
    from flask_login import LoginManager
    if os.environ.get("SECRET_KEY"):
        app.config["SECRET_KEY"]=os.environ["SECRET_KEY"]
        print("secret key found")
    else:
        print("secret key not found, using random")
        app.config["SECRET_KEY"] = os.urandom(32)

    login_manager = LoginManager()
    login_manager.init_app(app)

    login_manager.login_view = "login_auth"
    login_manager.login_message = "Sinun tulee kirjautua sisään"

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