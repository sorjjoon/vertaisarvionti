from sqlalchemy.sql import Select, between, delete, desc, distinct, insert, join, select, update, func
from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Connection

from application.auth.account import account
from application.domain.comment import Comment
from datetime import datetime

from typing import List


def insert_comment(self, conn: Connection,  user_id:int, text:str, submit_id:int=None, task_id:int=None, assignment_id:int=None, answer_id:int=None, visible:bool=True) -> int:
    """[Insert given comment]

    Args:
        self (data): [description]
        user_id (int): [description]
        text (str): [description]
        submit_id (int, optional): [description]. Defaults to None.
        task_id (int, optional): [description]. Defaults to None.
        assignment_id (int, optional): [description]. Defaults to None.
        answer_id (int, optional): [description]. Defaults to None.
        visible (bool, optional): [description]. Defaults to True.

    Raises:
        ValueError: [In case all arguments null]

    Returns:
        int: [description]
    """
    sql = self.comment.insert().values(user_id=user_id, visible=visible, text=text)

    if submit_id is not None:
        sql=sql.values(submit_id=submit_id)
        self.logger.info("Inserting comment for user %s for submit %s",user_id, submit_id)
    elif answer_id is not None:
        sql=sql.values(answer_id=answer_id)
        self.logger.info("Inserting comment for user %s for answer %s",user_id, answer_id)
    elif task_id is not None:
        sql=sql.values(task_id=task_id)
        self.logger.info("Inserting comment for user %s for task %s",user_id, task_id)
    elif assignment_id is not None:
        sql = sql.values(assignment_id=assignment_id)
        self.logger.info("Inserting comment for user %s for assignment %s",user_id, assignment_id)
    else:
        raise ValueError("all arguments null")

    with conn.begin():
        rs = conn.execute(sql)
        id = rs.inserted_primary_key[0]

        return id


def insert_comment_dict(self, conn: Connection,  comment_dict):
    sql = self.comment.insert().values(comment_dict)
    with conn.begin():
        conn.execute(sql)



def delete_comment(self, conn: Connection,  comment_id:int, user_id:int):
    sql = self.comment.delete().where(id=comment_id, user_id=user_id)
    self.logger.info("Deleting comment %s for user %s ", comment_id, user_id)
    with conn.begin():
        rs = conn.execute(sql)
        self.logger.info("Deletion successful, deleted %s comments", rs.rowcount)
        if rs.rowcount != 1:
            self.logger.warning("Incorrect number of rows deleted")

def select_comments(self, conn: Connection,  user_id:int, submit_id:int=None, task_id:int=None, assignment_id:int=None, answer_id:int=None) -> List[Comment]:
    """Select comments matching param. Makes sure user has rights to view the comment, by checking that they are the owner, or the comment is visible

    Args:
        user_id (int): [description]
        submit_id (int, optional): [description]. Defaults to None.
        task_id (int, optional): [description]. Defaults to None.
        assignment_id (int, optional): [description]. Defaults to None.
        answer_id (int, optional): [description]. Defaults to None.

    Raises:
        ValueError: [in case all given args are null]

    Returns:
        [list]: [list of comments]
    """
    
    j = self.comment.join(self.account).join(self.role)
    sql = select([self.comment, self.account.c.last_name, self.account.c.first_name, self.role.c.name]).where((self.comment.c.user_id==user_id) | (self.comment.c.visible == True)).select_from(j).order_by(desc(func.coalesce(self.comment.c.modified, self.comment.c.timestamp)))
    if submit_id is not None:
        sql=sql.where(self.comment.c.submit_id==submit_id)
        self.logger.info("Selecting comments for user %s from submit %s",user_id, submit_id)
    elif answer_id is not None:
        sql=sql.where(self.comment.c.answer_id==answer_id)
        self.logger.info("Selecting comments for user %s from answer %s",user_id, answer_id)
    elif task_id is not None:
        sql=sql.where(self.comment.c.task_id==task_id)
        self.logger.info("Selecting comments for user %s from task %s",user_id, task_id)
    elif assignment_id is not None:
        sql = sql.where(self.comment.c.assignment_id==assignment_id)
        self.logger.info("Selecting comments for user %s from assignment %s",user_id, assignment_id)
    else:
        raise ValueError("all arguments null")

    self.logger.info("")
    with conn.begin():
        rs=conn.execute(sql)
        comments=[]
        for row in rs:
            owner_str=row[self.account.c.last_name]+", "+row[self.account.c.first_name]
            if row[self.role.c.name] == "TEACHER":
                owner_str+="  (opettaja)"
            c = Comment(row[self.comment.c.id], row[self.comment.c.user_id], row[self.comment.c.text], row[self.comment.c.visible], row[self.comment.c.timestamp], row[self.comment.c.modified], owner_str=owner_str)
            
            comments.append(c)
        
        return comments


def update_comment(self, conn: Connection,  comment_id:int, user_id:int, text:str=None, visible:bool=None):
    """No update in case text and visible left null

    Args:
        self (data): [description]
        comment_id (int): [description]
        user_id (int): [description]
        text (str, optional): [description]. Defaults to None.
        visible (bool, optional): [description]. Defaults to None.
    """
    self.logger.info("Updating comment %s for user %s", comment_id, user_id)
    if text==None==visible:
        self.logger.info("no update, text and visible None")
        return
    sql = self.comment.update().where((self.comment.c.id==comment_id) & (self.comment.c.user_id==user_id)).values(modified=func.now())
    if text is not None:
        self.logger.info("Updating text")
        sql = sql.values(text=text)
    if visible is not None:
        self.logger.info("Updating visibility")
        sql = sql.values(visible=visible)
    with conn.begin():
        rs = conn.execute(sql)
        self.logger.info("Comment update success. %s rows changed", rs.rowcount)
        if rs.rowcount!=1:
            self.logger.warning("Row update failure, too many/few rows changed")


