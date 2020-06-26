from sqlalchemy.sql import Select, between, delete, desc, distinct, insert, join, select, update, func
from sqlalchemy import nullslast
from sqlalchemy.exc import IntegrityError
from string import ascii_uppercase
from random import choice
from application.domain.course import Course
from application.auth.account import account
from application.domain.assignment import Assignment, Task
from datetime import datetime




from sqlalchemy.sql import Select, between, delete, desc, distinct, insert, join, select, update, func
from sqlalchemy import nullslast
from sqlalchemy.exc import IntegrityError


from application.auth.account import account
from application.domain.assignment import Comment
from datetime import datetime

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .data import data

def insert_feedback(self, user_id:int, submit_id:int=None, visible:bool=False, text:str="") -> int:
    """Insert feedback

    Args:
        user_id (int): [description]
        submit_id (int, optional): [description]. Defaults to None.
        visible (bool, optional): [description]. Defaults to False.
        text (str, optional): [description]. Defaults to "".

    Returns:
        int: [description]
    """

    sql = self.feedback.insert().values(owner_id=user_id, visible=visible, text=text, submit_id=submit_id)
    self.logger.info("Inserting feedback for submit %s for user %s ", submit_id, user_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]
        return id


def delete_feedback(self, feedback_id:int, user_id:int):
    sql = self.feedback.delete().where(id=feedback_id, owner_id=user_id)
    self.logger.info("Deleting feedback %s for user %s ", feedback_id, user_id)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        self.logger.info("Deletion successful, deleted %s feedback", rs.rowcount)
        if rs.rowcount != 1:
            self.logger.warning("Incorrect number of rows deleted")




def update_feedback(self, feedback_id:int, user_id:int, text:str=None, visible:bool=None):
    """No update in case text and visible left null

    Args:
        self (data): [description]
        comment_id (int): [description]
        user_id (int): [description]
        text (str, optional): [description]. Defaults to None.
        visible (bool, optional): [description]. Defaults to None.
    """
    self.logger.info("Updating feedback %s for user %s", comment_id, user_id)
    if text==None==visible:
        self.logger.info("no update, text and visible None")
        return
    sql = self.feedback.update().where((self.feedback.c.id==feedback_id) & (self.feedback.c.owner_id==user_id)).values(modified=func.now())
    if text is not None:
        self.logger.info("Updating text")
        sql = sql.values(text=text)
    if visible is not None:
        self.logger.info("Updating visibility")
        sql = sql.values(visible=visible)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        self.logger.info("feedback update success. %s rows changed", rs.rowcount)
        if rs.rowcount!=1:
            self.logger.warning("Row update failure, too many/few rows changed")


