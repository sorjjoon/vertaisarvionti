from datetime import date as pydate
from random import choice
import os
from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Index,
                        Integer, LargeBinary, MetaData, String, Table,
                        UniqueConstraint, engine)
from sqlalchemy.engine import Engine
from sqlalchemy.sql import (Select, between, delete, desc, distinct, insert,
                            join, select, update)
from sqlalchemy.sql import func


class data:
    def __init__(self, used_engine: engine, create= True):
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
                          Column("name", String(20), nullable=False),
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
                                        "account.id", onupdate="CASCADE"),nullable=False, primary_key=True),
                                    Column("course_id", Integer, ForeignKey(
                                        "course.id", onupdate="CASCADE"),nullable=False, primary_key=True)
                                    )

        self.assignment = Table("assignment", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(500), nullable=False),
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
                                        "assignment.id", onupdate="CASCADE"), nullable=False)
                                    )

        self.file = Table("file", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(), nullable=False),
        Column("owner_id", Integer,  ForeignKey("account.id", onupdate="CASCADE"),nullable=False, index=True),
        Column("upload_date", DateTime, nullable=False, server_default=func.now()),
        Column("binary_file", LargeBinary()),
        Column("submit_id", Integer, ForeignKey(
                                        "submit.id", onupdate="CASCADE"), index=True),
        Column("answer_id", Integer, ForeignKey(
                                        "answer.id", onupdate="CASCADE"), index=True),
        Column("task_id", Integer, ForeignKey(
                                        "task.id", onupdate="CASCADE"), index=True),
        Column("assignment_id", Integer, ForeignKey(
                                        "assignment.id", onupdate="CASCADE"), index=True))
        

        self.answer = Table("answer", metadata,
        Column("id", Integer, primary_key=True),
        Column("reveal", DateTime,
                                   server_default=func.now(), nullable=False),
        Column("description", String(500)),                           
        Column("task_id", Integer, ForeignKey(
                                        "task.id", onupdate="CASCADE"), index=True,nullable=False),
                                        Column("reveal", DateTime,nullable=False))

        self.submit = Table("submit", metadata,
        Column("id", Integer, primary_key=True),
        Column("description", String(500)),
        Column("task_id", Integer, ForeignKey("task.id", onupdate="CASCADE"), index=True,nullable=False),
        
        Column("last_update", DateTime, nullable=False, server_default=func.now()), 
        Column("points", Integer),
        Column("owner_id", Integer, ForeignKey("account.id", onupdate="CASCADE"), index=True,nullable=False))
                            
        
        self.peer = Table("peer", metadata,
        Column("submit_id", Integer, ForeignKey("submit.id", onupdate="CASCADE"), index=True,nullable=False),
        
        Column("reciever_id", Integer, ForeignKey("account.id", onupdate="CASCADE"), index=True,nullable=False),
        Column("reviewer_id", Integer, ForeignKey("account.id", onupdate="CASCADE"), index=True,nullable=False),
        Column("review", String(500), nullable=False),
        Column("deadline", DateTime, nullable=False),
        Column("teacher_check", Boolean, default = False)
        
        
        )
        

        self.engine=used_engine
        if create:
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
    from ._file_service import select_file_details, get_file, update_file
    from ._submit_service import update_submit
    from ._teacher_stats import count_students
    from ._task_service import set_task_answer, update_answer