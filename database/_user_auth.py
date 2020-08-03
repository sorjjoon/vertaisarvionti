from __future__ import annotations
from hashlib import scrypt
from secrets import token_hex
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import delete, insert, join, select, update
from sqlalchemy.engine import Connection
from application.domain.account import Account
from .data import utcnow
# see documentation for queries / param explanations
from typing import List, TYPE_CHECKING
import pytz
if TYPE_CHECKING:
    from .data import data

from .exceptions import AccountLockedError



def get_user(self:data, conn: Connection,  username: str, password: str) -> Account:
    """Get the Account object for given username and password (function handles salting)

    Arguments:
        username {str} -- [username]
        password {str} -- [password]

    Returns:
        Account -- [matching user Account, None in case username/password invalid]
    """

    hashed = self.hash_password(conn, password, username=username)
    j = self.account.join(self.role)
    sql = select([self.account, self.role.c.name]).where(self.account.c.username ==
                                       username).select_from(j)
    
    with conn.begin():
        result_set = conn.execute(sql)
        row = result_set.first()
        if row is None:
            self.logger.info("Login for "+username+" failed, invalid username")
            return None

        user_id = row[self.account.c.id]
        locked_until = row[self.account.c.locked_until]
        
        
        if locked_until is not None and locked_until>datetime.utcnow():
            self.logger.warning("Attempted login for locked user %s", user_id)
            raise AccountLockedError("Account is locked", locked_until)

        if hashed == row[self.account.c.password]:
                
            self.logger.info("Login for "+username+" success")
            sql = self.account.update().where(self.account.c.id==user_id).values(locked_until=None, failed_attempts=0)
            conn.execute(sql)
            return Account(user_id, row[self.account.c.username], row[self.role.c.name], row[self.account.c.first_name], row[self.account.c.last_name], 0, None)
            
                
        failed_attempts = row[self.account.c.failed_attempts]+1
        sql = self.account.update().where(self.account.c.id==user_id).values(failed_attempts=self.account.c.failed_attempts+1)
        self.logger.info("Login for "+username+" failed, invalid password, failed_attempts %s", failed_attempts)
        if failed_attempts > 1 and not failed_attempts%5:
            self.logger.warning("locking Account %s due to failed login attempts", user_id)
            lock_time = timedelta(hours=1)*(failed_attempts//5)
            new_time=datetime.utcnow()+lock_time
            
            sql = sql.values(locked_until=new_time)
        conn.execute(sql)
        return None

def get_role_id(self:data, conn: Connection,  role:str) -> id:
    """[Return the role_id for given role name. ]

    Arguments:
        role {str} -- [role name ]

    Returns:
        id -- [role id, None in case invalid name]
    """
    sql = select([self.role.c.id]).where(self.role.c.name == role)
    with conn.begin():
        rs = conn.execute(sql)
        return rs.fetchone()[self.role.c.id]


def insert_user(self:data, conn: Connection,  username: str, password: str, first_name:str, last_name:str, role:str="USER") -> None:
    """Insert the given user in the database (also generates new salt) Raises Integrity error in case duplicate username

    Arguments:
        username {str} -- [username]
        password {str} -- [pswd]
        first_name {str} -- [name]
        last_name {str} -- [name]

    Keyword Arguments:
        role {str} -- [user role name] (default: {"USER"})
    """
    self.logger.info("Adding new user "+username)
    salt = generate_new_salt()

    hashed = hash_password_salt(password, salt)
    role_id = self.get_role_id(conn, role)
    sql = self.account.insert().values(
        username=username, password=hashed, salt=salt, role_id=role_id, first_name=first_name, last_name=last_name)
    with conn.begin():
        try:
            conn.execute(sql)
            self.logger.info("Insertion success!")
        except IntegrityError as r:
            self.logger.info("duplicate username")
            raise r


def hash_password(self:data, conn: Connection,  password:str, username:str=None, user_id:int=None) -> str:
    """Get the password for the given password, fetches salt matching username or user_id
        if both are null, returns None
    Arguments:
        password {[str]} -- [unhashed password]

    Keyword Arguments:
        username {[str]} -- [username] (default: {None})
        user_id {[id]} -- [id] (default: {None})

    Returns:
        [str] -- [return the hashed password]
    """
    if username is None and user_id is None:
        return None
    sql = select([self.account.c.salt])
    if username:
        sql = sql.where(self.account.c.username == username)
    elif user_id:
        sql = sql.where(self.account.c.id == user_id)
    else:
        return None
    with conn.begin():
        result_set = conn.execute(sql)
        row = result_set.fetchone()
        if row is None:
            return None

        salt = row[self.account.c.salt]
        result_set.close()
        return hash_password_salt(password, salt)


def update_password(self:data, conn: Connection,  user_id: int, new_password: str):
    """ update users id to match the given (plain text password) to match users salt hash. Users authroity to do this should be checked outside this function

    Arguments:
        user_id {int} -- [id]
        new_password {str} -- [new_password]
    """
    self.logger.info("updating password for "+str(user_id))
    new_hash = self.hash_password(conn, new_password, user_id=user_id)
    sql = update(self.account).values(
        password=new_hash).where(self.account.c.id == user_id)
    with conn.begin():
        conn.execute(sql)


def generate_new_salt() -> str:
    """[return the hex string for 32 randomly generated secure bytes]

    Returns:
        str -- [random hex]
    """
    return token_hex(32)


def hash_password_salt(password:str, salt:str) -> str:  # n, r chosen to be fast to compute
    """hashes the given password/salt combination


    Arguments:
        password {str} -- [plain text password]
        salt {str} -- [string form of random bytes (generate new salt with generate_new_salt)]

    Returns:
        str -- [hashed password]
    """
    hashed_bytes = scrypt(bytes(password, "utf-8"), n=16384, r=8,
                          p=1, salt=bytes(salt, "utf-8"))  # scrypt returns bytes
    return hashed_bytes.hex()