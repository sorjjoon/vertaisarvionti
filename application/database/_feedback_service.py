from sqlalchemy.sql import Select, between, delete, desc, distinct, insert, join, select, update, func
from sqlalchemy import nullslast
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError
from string import ascii_uppercase
from random import choice
from application.domain.course import Course
from application.auth.account import account
from application.domain.assignment import Assignment, Task, Feedback
from datetime import datetime




from sqlalchemy.sql import Select, between, delete, desc, distinct, insert, join, select, update, func
from sqlalchemy import nullslast
from sqlalchemy.exc import IntegrityError


from application.auth.account import account

from datetime import datetime

from typing import TYPE_CHECKING

def select_feedback(self, conn: Connection,  user_id:int, submit_id=None):
    if submit_id is None:
        return None
    sql = select([self.feedback])

    if submit_id:
        sql = sql.where(self.feedback.c.submit_id== submit_id)
    else:
        raise ValueError("All params null")
    with conn.begin():
        row = conn.execute(sql).first()
        if row is None or row[self.feedback.c.id] is None:
            return None
        
        return Feedback(id=row[self.feedback.c.id], points=row[self.feedback.c.points], modified = row[self.feedback.c.modified], date=row[self.feedback.c.timestamp], submit_id=row[self.feedback.c.submit_id], owner_id = row[self.feedback.c.owner_id], visible = row[self.feedback.c.visible])


def grade_submit(self, conn: Connection,  user_id:int, submit_id, points, visible:bool=None):
    self.logger.info("grading submit %s for user %s", submit_id, user_id)
    sql = select([self.feedback.c.id]).where(self.feedback.c.submit_id== submit_id)
    with conn.begin():
        rs = conn.execute(sql)
        row = rs.first()
        if row is None:
            self.logger.info("no feedback found, creating new")
            self.insert_feedback(user_id, submit_id, points, visible=visible)
        else:
            id = row[self.feedback.c.id]
            self.logger.info("old feedback id: %s found, updating", id)
            self.update_feedback(conn, id, user_id, points=points, visible=visible)
        self.logger.info("success!")

def insert_feedback(self, conn: Connection,  user_id:int, submit_id, points, visible:bool=False) -> int:
    """Insert feedback

    Args:
        user_id (int): [description]
        submit_id (int).
        visible (bool, optional): [description]. Defaults to False.
        

    Returns:
        int: [description]
    """

    sql = self.feedback.insert().values(owner_id=user_id, visible=visible, points=points, submit_id=submit_id)
    self.logger.info("Inserting feedback for submit %s for user %s ", submit_id, user_id)
    with conn.begin():
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]
        return id


def delete_feedback(self, conn: Connection,  feedback_id:int, user_id:int):
    sql = self.feedback.delete().where(id=feedback_id, owner_id=user_id)
    self.logger.info("Deleting feedback %s for user %s ", feedback_id, user_id)
    with conn.begin():
        rs = conn.execute(sql)
        self.logger.info("Deletion successful, deleted %s feedback", rs.rowcount)
        if rs.rowcount != 1:
            self.logger.warning("Incorrect number of rows deleted")




def update_feedback(self, conn: Connection,  feedback_id:int, user_id:int, points=None, visible:bool=None):
    """No update in case points and visible left null

    Args:
        self (data): [description]
        comment_id (int): [description]
        user_id (int): [description]
       
        visible (bool, optional): [description]. Defaults to None.
    """
    self.logger.info("Updating feedback %s for user %s", feedback_id, user_id)
    if None==visible==points:
        self.logger.info("no update and visible None")
        return
    sql = self.feedback.update().where((self.feedback.c.id==feedback_id) & (self.feedback.c.owner_id==user_id)).values(modified=func.now())
    
    if visible is not None:
        self.logger.info("Updating visibility")
        sql = sql.values(visible=visible)
    if points is not None:
        self.logger.info("Updating points")
        sql = sql.values(points=points)
        
    with conn.begin():
        rs = conn.execute(sql)
        self.logger.info("feedback update success. %s rows changed", rs.rowcount)
        if rs.rowcount!=1:
            self.logger.warning("Row update failure, too many/few rows changed")


