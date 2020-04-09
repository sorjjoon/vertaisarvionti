from sqlalchemy.sql import select, insert, delete, update

from application.auth.account import account

from hashlib import scrypt
from secrets import token_hex

# see documentation for queries / param explanations


def get_user(self, username: str, password: str):

    hashed = self.hash_password(password, username=username)
    sql = select([self.account]).where(self.account.c.username ==
                                       username).where(self.account.c.password == hashed)
    print(self.hash_password(password, username=username))
    with self.engine.connect() as conn:
        result_set = conn.execute(sql)
        row = result_set.fetchone()
        result_set.close()
        if row is not None:
            print("Login for "+username+" success")
            return account(row[self.account.c.id], row[self.account.c.username], row[self.account.c.password], row[self.account.c.first_name])
        else:
            print("Login for "+username+" failed")
            return None


def get_role_id(self, role):
    sql = select([self.role.c.id]).where(self.role.c.name == role)
    with self.engine.connect() as conn:
        rs = conn.execute(sql)
        return rs.fetchone()[self.role.c.id]


def insert_user(self, username: str, password: str, first_name:str, last_name:str, role="USER"):
    print("Adding new user "+username)
    salt = generate_new_salt()

    hashed = hash_password_salt(password, salt)
    role_id = self.get_role_id(role)
    sql = self.account.insert().values(
        username=username, password=hashed, salt=salt, role_id=role_id, first_name=first_name, last_name=last_name)
    with self.engine.connect() as conn:
        conn.execute(sql)


def hash_password(self, password, username=None, user_id=None):
    sql = select([self.account.c.salt])
    if username:
        sql = sql.where(self.account.c.username == username)
    elif user_id:
        sql = sql.where(self.account.c.id == user_id)
    else:
        return None
    with self.engine.connect() as conn:
        result_set = conn.execute(sql)
        row = result_set.fetchone()
        if row is None:
            return None

        salt = row[self.account.c.salt]
        result_set.close()
        return hash_password_salt(password, salt)


def update_password(self, user_id: int, new_password: str):
    print("updating password for "+str(user_id))
    new_hash = self.hash_password(new_password, user_id=user_id)
    sql = update(self.account).values(
        password=new_hash).where(self.account.c.id == user_id)
    with self.engine.connect() as conn:
        conn.execute(sql)


def generate_new_salt():
    return token_hex(32)


def hash_password_salt(password, salt):  # n, r chosen to be fast to compute
    hashed_bytes = scrypt(bytes(password, "utf-8"), n=16384, r=8,
                          p=1, salt=bytes(salt, "utf-8"))  # scrypt returns bytes
    return hashed_bytes.hex()
