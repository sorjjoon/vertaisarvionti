from __future__ import annotations
from sqlalchemy.sql import Select, between, delete, desc, distinct, insert, join, select, update, func
from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Connection

from application.auth.account import account
from application.domain.comment import Comment
from application.domain.assignment import File
from datetime import datetime
import pytz
from typing import List, TYPE_CHECKING
from .data import utcnow

if TYPE_CHECKING:
    from .data import data

def insert_comment(self:data, conn: Connection,  user_id:int, text:str, submit_id:int=None, task_id:int=None, assignment_id:int=None, answer_id:int=None, reveal:datetime=None, course_id:int=None, files:list=[]) -> int:
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
    sql = self.comment.insert().values(user_id=user_id, text=text)
    if reveal is None:
        sql = sql.values(reveal=utcnow())
    else:
        sql = sql.values(reveal=reveal)
    if submit_id is not None:
        sql=sql.values(submit_id=submit_id)
        self.logger.info("Inserting comment for user %s for submit %s",user_id, submit_id)
    if course_id is not None:
        sql=sql.values(course_id=course_id)
        self.logger.info("Inserting comment for user %s for course %s",user_id, course_id)
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
        if files:
            self.insert_files(conn, user_id, files, comment_id=id)

        return id


def insert_comment_dict(self:data, conn: Connection,  comment_dict):
    sql = self.comment.insert().values(comment_dict)
    with conn.begin():
        rs = conn.execute(sql)
        
        



def delete_comment(self:data, conn: Connection,  comment_id:int, user_id:int):
    sql = self.comment.delete().where(id=comment_id, user_id=user_id)
    self.logger.info("Deleting comment %s for user %s ", comment_id, user_id)
    with conn.begin():
        rs = conn.execute(sql)
        self.logger.info("Deletion successful, deleted %s comments", rs.rowcount)
        if rs.rowcount != 1:
            self.logger.warning("Incorrect number of rows deleted")

def select_comments(self:data, conn: Connection,  user_id:int, submit_id:int=None, task_id:int=None, assignment_id:int=None, answer_id:int=None, course_id:int=None) -> List[Comment]:
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
    
    j = self.comment.join(self.account).join(self.role).outerjoin(self.file, (self.file.c.comment_id==self.comment.c.id) )
    sql = select([self.comment, self.account.c.last_name, self.account.c.first_name, self.role.c.name, self.file.c.id, self.file.c.name, self.file.c.upload_date]).where((self.comment.c.user_id==user_id) | (self.comment.c.reveal < utcnow() )).select_from(j).order_by(desc(self.comment.c.reveal))
    if submit_id is not None:
        sql=sql.where(self.comment.c.submit_id==submit_id)
        self.logger.info("Selecting comments for user %s from submit %s",user_id, submit_id)
    elif course_id is not None:
        sql = sql.where(self.comment.c.course_id == course_id)
        self.logger.info("Selecting comments for user %s from course %s",user_id, course_id)
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
        self.logger.error("select_comments called with all null values")
        raise ValueError("all arguments null")

    
    with conn.begin():
        rs=conn.execute(sql)
        
        seen_comments = {}
        for row in rs:
            owner_str=row[self.account.c.last_name]+", "+row[self.account.c.first_name]
            if row[self.role.c.name] == "TEACHER":
                owner_str+="  (opettaja)"
            comment_id = row[self.comment.c.id]
            if not seen_comments.get(comment_id):
                c = Comment(comment_id, row[self.comment.c.user_id], row[self.comment.c.text], row[self.comment.c.reveal], row[self.comment.c.timestamp], row[self.comment.c.modified], owner_str=owner_str, files=[])
                seen_comments[comment_id] = c
            if row[self.file.c.id] is not None:
                seen_comments[comment_id].files.append(File(row[self.file.c.id], row[self.file.c.name], row[self.file.c.upload_date]))
        
    return list(seen_comments.values())


def update_comment(self:data, conn: Connection,  comment_id:int, user_id:int, text:str=None, reveal:datetime=None, new_files:list=[], delete_old_files:list = []):
    """No update in case text and visible left null

    Args:
        self (data): [description]
        comment_id (int): [description]
        user_id (int): [description]
        text (str, optional): [description]. Defaults to None.
        visible (bool, optional): [description]. Defaults to None.
    """
    self.logger.info("Updating comment %s for user %s", comment_id, user_id)
    if text==None==reveal:
        self.logger.info("no update, text and visible None")
        return
    sql = self.comment.update().where((self.comment.c.id==comment_id) & (self.comment.c.user_id==user_id)).values(modified=utcnow())
    if text is not None:
        self.logger.info("Updating text")
        sql = sql.values(text=text)
    if reveal is not None:
        self.logger.info("Updating reveal")
        sql = sql.values(reveal=reveal)
    with conn.begin():
        rs = conn.execute(sql)
        self.logger.info("Comment update success. %s rows changed", rs.rowcount)
        if rs.rowcount!=1:
            self.logger.warning("Row update failure, too many/few rows changed")
        self.update_file(conn, user_id, new_files, comment_id=comment_id, files_to_delete=delete_old_files)


