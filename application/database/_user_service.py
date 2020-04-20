
from sqlalchemy.sql import select, insert, delete, update, join, distinct

from application.auth.account import account

#see documentation for queries 


def delete_user(self, user_id: int):
    """[summary]
    
    Arguments:
        user_id {int} -- [description]
    """    
    sql = self.account.delete().where(self.account.c.id == user_id)
    with self.engine.connect() as conn:
        conn.execute(sql) #delete cascades

def check_user(self, username: str) -> bool:
    """[summary]
    
    Arguments:
        username {str} -- [description]
    
    Returns:
        bool -- [description]
    """        
    sql = select([self.account.c.id]).where(self.account.c.username==username)
    with self.engine.connect() as conn:
        result_set = conn.execute(sql)
        row = result_set.fetchone()
        result_set.close()
        if row is None:
            return True
        else:
            return False

def update_username(self, new_username:str, user_id:int):
    """[summary]
    
    Arguments:
        new_username {str} -- [description]
        user_id {int} -- [description]
    """        
    sql = self.account.update().values(username=new_username).where(self.account.c.id == user_id)
    with self.engine.connect() as conn:
        conn.execute(sql)

def get_user_by_id(self, user_id: int) -> account:
    """[summary]
    
    Arguments:
        user_id {int} -- [description]
    
    Returns:
        account -- [description]
    """        
    join_clause = self.account.join(self.role)
    sql = select([self.role.c.name, self.account.c.username, self.account.c.first_name]).select_from(join_clause).where(self.account.c.id==user_id)
    with self.engine.connect() as conn:
        result_set = conn.execute(sql)
        row = result_set.fetchone()
        
        result_set.close()       
        if row is not None:
            return account(user_id,row[self.account.c.username], row[self.role.c.name], row[self.account.c.first_name])
        else:
            return None
        




