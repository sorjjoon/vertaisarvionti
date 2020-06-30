from flask import Flask
import os
from application.database.data import data

#from model import db as database

#from flask_sqlalchemy_core import FlaskSQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask import Response

class LaxResponse(Response):
    #Just adding samesite lax, in case it's not set
    def set_cookie(self, *args, **kwargs):
        if 'samesite' not in kwargs or ('samesite' in kwargs and kwargs['samesite'] is None):
            kwargs['samesite']="Lax"
        super().set_cookie(*args, **kwargs)
        


def create_app(config):  
      
    print("creating app")
    import logging.config
    
    
    app = Flask(__name__)
    sql_alchemy_db = SQLAlchemy()
    global db
    if os.environ.get("SECRET_KEY"):
        app.config["SECRET_KEY"]=os.environ["SECRET_KEY"]
        app.logger.info("secret key found")
    else:
        app.logger.info("secret key not found, using random")
        app.config["SECRET_KEY"] = os.urandom(32)
    #db
    app.logger.info("configuring sqlalchemy")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if os.environ.get("UNIT_TEST"):
        app.logger.info("unit test detected, echoing sql")
        app.config["SQLALCHEMY_ECHO"] = False
    else:
        app.config["SQLALCHEMY_ECHO"] = False
    
    if config =="NET_TEST":
        app.logger.info("network test detected, using in memory")
        DATABASE_URL = "sqlite://"
    elif os.environ.get("DATABASE_URL"):
        DATABASE_URL = os.environ.get("DATABASE_URL")
        app.logger.info("database url found")
        app.logger.info(DATABASE_URL)
    
    else:
        
        DATABASE_URL = "sqlite:///vertais_data.db"
        app.logger.info("database url not found, using "+DATABASE_URL)

    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    sql_alchemy_db.init_app(app)
    with app.app_context():

        if config=="DATA_TEST":
            data.drop_all(sql_alchemy_db.get_engine())

        logging.getLogger("sqlalchemy").setLevel(logging.DEBUG)
        logging.getLogger("sqlalchemy").propagate = False

        sql_handler = logging.FileHandler("sql_log.log","w")
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s - %(process)d: %(message)s")
        sql_handler.setFormatter(formatter)
        sql_handler.setLevel(logging.INFO)
        logging.getLogger("sqlalchemy").addHandler(sql_handler)
        
        db = data(sql_alchemy_db.get_engine(), create=True)
    app.logger.info("Database configuration success!")
    # session
    
    app.logger.info("configuring session")
    
    #configuring custom response class, to make make same site lax the default
    app.response_class = LaxResponse

    app.config["SESSION_TYPE"] = "sqlalchemy"
    app.config["PERMANENT_SESSION_LIFETIME"] = 60 *60 * 24 * 7 # 1 week lifetime
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_SQLALCHEMY"] = sql_alchemy_db
    with app.app_context():
        sess = Session(app)
    #sess.init_app(app)
    
        sess.app.session_interface.db.create_all()
    # login
    from flask_login import LoginManager
    

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

    app.logger.info("Importing views")
    with app.app_context():
        import application.views.common
        import application.views.utils

        import application.auth.views
        import application.auth.forms

        import application.views.teacher.course  as t
        import application.views.teacher.teacher_views.grade 
        import application.views.teacher.teacher_views.overview 
        import application.views.teacher.teacher_views.tasks 


        import application.views.student.course  
        import application.views.student.assignment  
        import application.views.student.task 
    app.logger.info("app creation success!")
    return app