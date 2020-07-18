from __future__ import annotations
from sqlalchemy.sql import select, insert, delete, update, join, distinct
from sqlalchemy.exc import IntegrityError
from application.auth.account import account
from sqlalchemy.engine import Connection
#see documentation for queries 
from .data import utcnow
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .data import data
def delete_user(self:data, conn: Connection,  user_id:int) -> None:
    """deletes user with the given id. Check db if delete cascades or not (currently doesnt)

    Arguments:
        user_id {[int]} -- [id]
    """
    sql = self.account.delete().where(self.account.c.id == user_id)
    with conn.begin():
        conn.execute(sql) 

def check_user(self:data, conn: Connection,  username:str) -> bool:
    """check if given username is free

    Arguments:
        username {str} -- [username]

    Returns:
        [bool] -- [true if username is free]
    """

    sql = select([self.account.c.id]).where(self.account.c.username==username)
    with conn.begin():
        result_set = conn.execute(sql)
        row = result_set.fetchone()
        result_set.close()
        if row is None:
            return True
        else:
            return False

def update_user(self:data, conn: Connection, user_id:int, username:str=None, first_name=None, last_name=None) -> None:
    """Update the username for given id to match param

    Arguments:
        new_username {str} -- [new username]
        user_id {int} -- [id]
    """
    if first_name==None==username==last_name:
        self.logger.info("All params null for user update")
        return 
    
    sql = self.account.update().where(self.account.c.id == user_id)
    if username:
        sql=sql.values(username=username)
    if first_name:
        sql=sql.values(first_name=first_name)
    if last_name:
        sql=sql.values(last_name=last_name)

    with conn.begin() as trans:
        self.logger.info("Updating username for %s", user_id)
        try:
            conn.execute(sql)
            self.logger.info("Update success!")
        except IntegrityError as r:
            self.logger.info("Username taken")
            trans.rollback()
            raise r

def get_user_by_id(self:data, conn: Connection,  user_id: int) -> account:
    """Get all details of user matching given id

    Arguments:
        user_id {int} -- [id]

    Returns:
        account -- [returns mtaching account object, None in case user not found]
    """
    self.logger.info("fetching user: %s", user_id)
    join_clause = self.account.join(self.role)
    sql = select([self.role.c.name, self.account.c.username, self.account.c.first_name, self.account.c.last_name]).select_from(join_clause).where(self.account.c.id==user_id)
    with conn.begin():
        result_set = conn.execute(sql)
        row = result_set.fetchone()
        
        result_set.close()       
        if row is not None:
            return account(user_id,row[self.account.c.username], row[self.role.c.name], row[self.account.c.first_name], row[self.account.c.last_name] )
        else:
            return None
        




