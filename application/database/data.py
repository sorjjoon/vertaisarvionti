from datetime import date as pydate
from random import choice
import os

from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Index,
                        Integer, LargeBinary, MetaData, String, Table,
                        UniqueConstraint, engine)
from sqlalchemy.engine import Engine
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update)
from sqlalchemy.types import VARBINARY, Date, DateTime, Text, Time, LargeBinary
from sqlalchemy.sql import func


class data:
    def __init__(self, used_engine: engine):
        if not os.environ.get("HEROKU"):
            # sqlite doesn't enforce foreign keys by default, turning them on to enforce cascade
            def _fk_pragma_on_connect(dbapi_con, con_record):
                dbapi_con.execute('pragma foreign_keys=ON')

            from sqlalchemy import event
            event.listen(used_engine, 'connect', _fk_pragma_on_connect)

        metadata = MetaData(used_engine)

        self.account = Table('account', metadata,
                             Column("id", Integer, primary_key=True),
                             Column("role_id", Integer,  ForeignKey(
                                 "role.id", onupdate="CASCADE"), nullable=False),
                             Column("creation date", DateTime, nullable=False,
                                    server_default=func.now()),
                             Column("username", String(144), nullable=False),
                             Column("salt", String(144), nullable=False),
                             Column("password", String(144), nullable=False),
                             Column("first_name", String(144), nullable=False),
                             Column("last_name", String(144), nullable=False),
                             UniqueConstraint(
                                 'username', name='username_unique')
                             )
        self.role = Table("role", metadata,
                          Column("id", Integer, primary_key=True),
                          Column("name", String(20)),
                          UniqueConstraint('name', name='role_unique'
                                           ))

        self.course = Table("course", metadata,
                            Column("id", Integer, primary_key=True),
                            Column("teacher_id", Integer, ForeignKey(
                                "account.id", onupdate="CASCADE"), index=True),
                            Column("name", String(144), nullable=False),
                            Column("description", String(144)),
                            Column("code", String(8), nullable=False),
                            Column("end_date", Date, nullable=False),
                            Column("creation_date", DateTime, nullable=False,
                                   server_default=func.now())
                            )
        self.course_student = Table("course_student", metadata,
                                    Column("student_id", Integer, ForeignKey(
                                        "account.id", onupdate="CASCADE"), primary_key=True),
                                    Column("course_id", Integer, ForeignKey(
                                        "course.id", onupdate="CASCADE"), primary_key=True)
                                    )

        self.assignment = Table("assignment", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(500)),
        Column("course_id", Integer, ForeignKey(
                                        "course.id", onupdate="CASCADE"), nullable=False),
        Column("reveal", DateTime,
                                   server_default=func.now(), nullable=False),
        Column("deadline", DateTime)
        )

        self.task = Table("task", metadata,
        Column("id", Integer, primary_key=True),
        Column("points", Integer, nullable=False),
        Column("description", String(500)),
        Column("assignment_id", Integer, ForeignKey(
                                        "assignment.id", onupdate="CASCADE"))
                                    )

        self.file = Table("file", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(), nullable=False),
        Column("owner", Integer, ForeignKey(
                                "account.id", onupdate="CASCADE"), index=True),
        Column("upload_date", DateTime, nullable=False,
                                   server_default=func.now()),
        Column("binary_file", LargeBinary()),
        Column("submit_id", Integer, ForeignKey(
                                        "submit.id", onupdate="CASCADE"), index=True),
        Column("task_id", Integer, ForeignKey(
                                        "task.id", onupdate="CASCADE"), index=True),
        Column("assignment_id", Integer, ForeignKey(
                                        "assignment.id", onupdate="CASCADE"), index=True)
        )

        self.answer = Table("answer", metadata,
        Column("id", Integer, primary_key=True),
        Column("task_id", Integer, ForeignKey(
                                        "task.id", onupdate="CASCADE"), index=True),
                                        Column("reveal", DateTime))

        self.submit = Table("submit", metadata,
        Column("id", Integer, primary_key=True),
        Column("description", String(500)),
        Column("task_id", Integer, ForeignKey("task.id", onupdate="CASCADE"), index=True),
        
        Column("last_update", DateTime, nullable=False, server_default=func.now()), 
        Column("owner_id", Integer, ForeignKey("account.id", onupdate="CASCADE"), index=True))
                            
        

        self.engine=used_engine
        metadata.create_all()  # checks if table exsists first

        # insert 1 admin user, and roles "USER" and "ADMIN to the database (if they don't exsist)"

        with self.engine.connect() as conn:
            sql=self.role.insert().values(name = "USER", id = 1)

            # catches unqiue contraint fail
            try:

                conn.execute(sql)
                print("user role inserted")
            except:
                pass
            sql=self.role.insert().values(name = "ADMIN", id = 2)
            try:
                conn.execute(sql)
                print("admin role inserted")

            except:
                pass

            sql=self.role.insert().values(name = "TEACHER", id = 3)
            try:
                conn.execute(sql)
                print("admin role inserted")

            except:
                pass

    from ._user_service import delete_user, get_user_by_id, check_user, update_username
    from ._user_auth import get_user, hash_password, insert_user, update_password, get_role_id
    from ._course_service import insert_course, select_courses_teacher, select_courses_student, enlist_student, select_students, select_course_details, set_assignments
    from ._assignment_service import insert_assignment, insert_task, select_assignment, set_submits
    from ._file_service import select_file_details, get_file
