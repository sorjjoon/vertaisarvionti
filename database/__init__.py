from flask_sqlalchemy import SQLAlchemy

sql_alchemy_db = SQLAlchemy()
from .data import Data

db = Data(None)