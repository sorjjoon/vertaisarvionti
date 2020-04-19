
from sqlalchemy.sql import select, insert, delete, update, join, distinct

from application.auth.account import account

#see documentation for queries 


def delete_user(self, user_id):
    sql = self.account.delete().where(self.account.c.id == user_id)
    with self.engine.connect() as conn:
        conn.execute(sql) #delete cascades

def check_user(self, username):
    sql = select([self.account.c.id]).where(self.account.c.username==username)
    with self.engine.connect() as conn:
        result_set = conn.execute(sql)
        row = result_set.fetchone()
        result_set.close()
        if row is None:
            return True
        else:
            return False

def update_username(self, new_username, user_id):
    sql = self.account.update().values(username=new_username).where(self.account.c.id == user_id)
    with self.engine.connect() as conn:
        conn.execute(sql)

def get_user_by_id(self, user_id: int):
    join_clause = self.account.join(self.role)
    sql = select([self.role.c.name, self.account.c.username, self.account.c.first_name, self.account.c.last_name]).select_from(join_clause).where(self.account.c.id==user_id)
    with self.engine.connect() as conn:
        result_set = conn.execute(sql)
        row = result_set.fetchone()
        
        result_set.close()       
        if row is not None:
            return account(user_id,row[self.account.c.username], row[self.role.c.name], row[self.account.c.first_name], row[self.account.c.last_name] )
        else:
            return None
        




